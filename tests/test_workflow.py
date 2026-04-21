from __future__ import annotations

import os
import shutil
from subprocess import CompletedProcess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

from core.content_sources import resolve_content_sources
from core.config import AppConfig
from core.browser import _best_body_text, _best_title_text, _extract_articulate_asset_url
from core.graph import invoke_workflow
from core.knowledge import get_knowledge_context, maybe_consolidate
from core.reporting import generate_markdown_report
from core.state import merge_findings
from core.utils import cleanup_project, ensure_text_file, make_output_bundle_dir, upgit_project
from agents.id_agent import run_id_review
from main import auto_detect_agents, normalize_command


REPO_ROOT = Path(__file__).resolve().parent.parent


def _pdf_bytes_with_text(text: str) -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(f'BT\n/F1 12 Tf\n72 100 Td\n({text}) Tj\nET\n'.encode('latin-1'))} >>\nstream\nBT\n/F1 12 Tf\n72 100 Td\n({text}) Tj\nET\nendstream".encode(
            "latin-1"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    payload = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{index} 0 obj\n".encode("ascii"))
        payload.extend(obj)
        payload.extend(b"\nendobj\n")

    xref_start = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(f"trailer\n<< /Root 1 0 R /Size {len(objects) + 1} >>\n".encode("ascii"))
    payload.extend(f"startxref\n{xref_start}\n%%EOF".encode("ascii"))
    return bytes(payload)


def _write_minimal_docx(path: Path, paragraphs: list[str], table_rows: list[list[str]]) -> None:
    def _paragraph_xml(text: str) -> str:
        escaped = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        return f"<w:p><w:r><w:t xml:space=\"preserve\">{escaped}</w:t></w:r></w:p>"

    body_parts = [_paragraph_xml(text) for text in paragraphs]
    if table_rows:
        rows_xml = []
        for row in table_rows:
            cells_xml = "".join(
                f"<w:tc><w:p><w:r><w:t xml:space=\"preserve\">{cell}</w:t></w:r></w:p></w:tc>" for cell in row
            )
            rows_xml.append(f"<w:tr>{cells_xml}</w:tr>")
        body_parts.append(f"<w:tbl>{''.join(rows_xml)}</w:tbl>")

    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
 xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
 xmlns:v="urn:schemas-microsoft-com:vml"
 xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:w10="urn:schemas-microsoft-com:office:word"
 xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
 xmlns:w15="http://schemas.microsoft.com/office/word/2012/wordml"
 xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
 xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"
 xmlns:wne="http://schemas.microsoft.com/office/2006/wordml"
 xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
 mc:Ignorable="w14 w15 wp14">
  <w:body>
    {''.join(body_parts)}
    <w:sectPr><w:pgSz w:w="12240" w:h="15840" /><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0" /></w:sectPr>
  </w:body>
</w:document>
"""

    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
""",
        )
        archive.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
""",
        )
        archive.writestr(
            "docProps/core.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Test</dc:title>
</cp:coreProperties>
""",
        )
        archive.writestr(
            "docProps/app.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex Tests</Application>
</Properties>
""",
        )
        archive.writestr("word/document.xml", document_xml)


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="agent-qc-test-"))
        for relative in ("docs", "knowledge/general", "knowledge/requirements", "outputs"):
            (self.temp_dir / relative).mkdir(parents=True, exist_ok=True)

        communication_seed = REPO_ROOT / "docs" / "communication.md"
        if communication_seed.exists():
            shutil.copy(communication_seed, self.temp_dir / "docs" / "communication.md")
        else:
            ensure_text_file(
                self.temp_dir / "docs" / "communication.md",
                "| Timestamp | From | To | Message/Task |\n|---|---|---|---|\n",
            )
        shutil.copy(REPO_ROOT / "knowledge" / "general" / "human_feedback_lessons.md", self.temp_dir / "knowledge" / "general" / "human_feedback_lessons.md")
        shutil.copy(REPO_ROOT / "knowledge" / "general" / "system_lessons.md", self.temp_dir / "knowledge" / "general" / "system_lessons.md")
        shutil.copy(REPO_ROOT / "knowledge" / "general" / "wcag_global.md", self.temp_dir / "knowledge" / "general" / "wcag_global.md")
        shutil.copy(REPO_ROOT / "knowledge" / "requirements" / "project_x_req.md", self.temp_dir / "knowledge" / "requirements" / "project_x_req.md")

        self.fixture_dir = self.temp_dir / "fixtures"
        self.fixture_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.fixture_dir / "lesson content.csv"
        self.csv_path.write_text(
            "Screen,Copy\n1,User should organize color labels.\n2,Behaviour matters for every learner.\n",
            encoding="utf-8",
        )
        self.docx_path = self.fixture_dir / "lesson brief.docx"
        _write_minimal_docx(
            self.docx_path,
            ["The User should organize content carefully.", "Behaviour matters for every learner."],
            [["Button", "continue"], ["Status", "prioritize review"]],
        )
        self.pdf_path = self.fixture_dir / "lesson notes.pdf"
        self.pdf_path.write_bytes(_pdf_bytes_with_text("The User should organize color and behavior.")) 

        os.environ["AGENT_QC_ROOT"] = str(self.temp_dir)
        os.environ["GROQ_API_KEY"] = "test-groq"
        os.environ["GOOGLE_API_KEY"] = "test-google"
        self.config = AppConfig.load(self.temp_dir)

    def tearDown(self) -> None:
        os.environ.pop("AGENT_QC_ROOT", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_merge_findings_preserves_unique_ids(self) -> None:
        merged = merge_findings(
            [{"id": "ID-001", "severity": "Info", "area": "A", "evidence": "x", "impact": "y", "recommended_fix": "z", "source_agent": "id"}],
            [{"id": "ID-001", "severity": "Info", "area": "B", "evidence": "x", "impact": "y", "recommended_fix": "z", "source_agent": "id"}],
        )
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[1]["id"], "ID-002")

    def test_manual_reflection_updates_human_feedback(self) -> None:
        result = invoke_workflow(
            user_text="You missed Section 3 markers",
            raw_text="/reflect You missed Section 3 markers",
            image_paths=[],
            next_agents=["reflection"],
            project_root=self.temp_dir,
            config=self.config,
        )
        self.assertIn("Stored manual feedback", result["reflection_summary"])
        content = (self.temp_dir / "knowledge" / "general" / "human_feedback_lessons.md").read_text(encoding="utf-8")
        self.assertIn("Section 3 markers", content)

    def test_generate_markdown_report_reuses_supplied_output_dir(self) -> None:
        output_dir = make_output_bundle_dir(self.temp_dir, "graphic qa bundle")
        artifacts_dir = output_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        (artifacts_dir / "preview.png").write_text("placeholder", encoding="utf-8")

        report_path = generate_markdown_report(
            project_root=self.temp_dir,
            findings=[],
            routing_reason="Graphic QA test run.",
            request_text="/fg test",
            config=self.config,
            content_sources=[],
            output_dir=output_dir,
        )

        self.assertEqual(report_path.parent, output_dir)
        self.assertTrue((artifacts_dir / "preview.png").exists())
        output_bundles = [path for path in (self.temp_dir / "outputs").iterdir() if path.is_dir()]
        self.assertEqual(len(output_bundles), 1)

    def test_playwright_output_helpers_extract_clean_title_and_body(self) -> None:
        raw_title = """### Result
""
### Ran Playwright code
```js
await page.evaluate('() => (document.title)');
```
### Page
- Page URL: https://example.com
- Page Title: Example Title
"""
        raw_body = """### Result
"Chapter 1\\nStart course\\nKnowledge Check"
### Ran Playwright code
```js
await page.evaluate('() => (document.body ? document.body.innerText : '')');
```
### Page
- Page URL: https://example.com
- Page Title: Example Title
"""
        self.assertEqual(_best_title_text(raw_title), "Example Title")
        self.assertEqual(_best_body_text(raw_body), "Chapter 1\nStart course\nKnowledge Check")

    def test_playwright_output_helpers_extract_articulate_asset_url(self) -> None:
        raw_asset = """### Result
"https://articulateusercontent.com/review/uploads/demo123/abc456/index.html"
### Ran Playwright code
```js
await page.evaluate('() => (...)');
```
"""
        self.assertEqual(
            _extract_articulate_asset_url(raw_asset),
            "https://articulateusercontent.com/review/uploads/demo123/abc456/index.html",
        )

    def test_router_runs_both_specialists_for_generic_prompt(self) -> None:
        result = invoke_workflow(
            user_text="Review this e-learning course for navigation and content quality",
            raw_text="Review this e-learning course for navigation and content quality",
            image_paths=[],
            next_agents=[],
            project_root=self.temp_dir,
            config=self.config,
        )
        ids = {finding["source_agent"] for finding in result["findings"]}
        self.assertIn("id", ids)
        self.assertIn("content", ids)
        self.assertTrue(Path(result["report_path"]).exists())
        self.assertEqual(len(result["findings"]), len({finding["id"] for finding in result["findings"]}))
        self.assertEqual(Path(result["report_path"]).name, "report.md")
        self.assertEqual(Path(result["report_path"]).parents[1], self.temp_dir / "outputs")
        report_text = Path(result["report_path"]).read_text(encoding="utf-8")
        self.assertIn("## Bản Dịch Tiếng Việt", report_text)

    def test_cg_command_normalization(self) -> None:
        payload, agents = normalize_command("/cg review this storyboard")
        self.assertEqual(payload, "review this storyboard")
        self.assertEqual(agents, ["content"])

    def test_auto_detect_routes_document_paths_to_content(self) -> None:
        agents = auto_detect_agents(f"Please QC '{self.csv_path}'", [], self.temp_dir)
        self.assertEqual(agents, ["content"])

    def test_resolve_content_sources_extracts_csv(self) -> None:
        sources = resolve_content_sources(self.temp_dir, f"Review '{self.csv_path}'")
        self.assertEqual(sources[0]["format"], "csv")
        self.assertIn("Row 2:", sources[0]["extracted_text"])
        self.assertIn("row 2", sources[0]["location_hints"])

    def test_resolve_content_sources_extracts_docx(self) -> None:
        sources = resolve_content_sources(self.temp_dir, f"Review '{self.docx_path}'")
        self.assertEqual(sources[0]["format"], "docx")
        self.assertIn("Paragraph 1:", sources[0]["extracted_text"])
        self.assertIn("table 1 row 1", sources[0]["location_hints"])

    def test_resolve_content_sources_extracts_pdf(self) -> None:
        sources = resolve_content_sources(self.temp_dir, f"Review '{self.pdf_path}'")
        self.assertEqual(sources[0]["format"], "pdf")
        self.assertIn("Page 1:", sources[0]["extracted_text"])
        self.assertIn("page 1", sources[0]["location_hints"])

    def test_knowledge_context_ordering(self) -> None:
        context = get_knowledge_context(self.temp_dir)
        self.assertLess(context.index("Human QA Supervisor Lessons"), context.index("System Lessons Learned"))
        self.assertLess(context.index("System Lessons Learned"), context.index("WCAG Global Baseline"))
        self.assertLess(context.index("WCAG Global Baseline"), context.index("Project X Requirements"))

    def test_graphic_agent_runs_for_figma_link(self) -> None:
        result = invoke_workflow(
            user_text="Review this Figma frame https://www.figma.com/design/abc/MyFile?node-id=1-2",
            raw_text="/fg https://www.figma.com/design/abc/MyFile?node-id=1-2",
            image_paths=[],
            next_agents=["graphic"],
            project_root=self.temp_dir,
            config=self.config,
        )
        ids = {finding["source_agent"] for finding in result["findings"]}
        self.assertIn("graphic", ids)

    @patch("agents.id_agent.run_playwright_probe")
    def test_id_agent_adds_playwright_probe_evidence_when_available(self, mock_probe) -> None:
        mock_probe.return_value = {
            "available": True,
            "status": "lesson_captured",
            "url": "https://example.com/course",
            "asset_url": "https://cdn.example.com/index.html",
            "lesson_url": "https://cdn.example.com/index.html#/lessons/chapter-1",
            "lesson_reached": True,
            "title": "Sample Course",
            "body_text": "Chapter 1\nStart course\nKnowledge Check",
            "snapshot_text": "e1 link Start course",
            "artifacts": [],
            "warnings": [],
        }

        result = invoke_workflow(
            user_text="Review Chapter 1 at https://example.com/course",
            raw_text="/id Review Chapter 1 at https://example.com/course",
            image_paths=[],
            next_agents=["id"],
            project_root=self.temp_dir,
            config=self.config,
        )

        self.assertTrue(any(finding["area"] == "Browser Evidence" for finding in result["findings"]))
        self.assertTrue(any(source.get("format") == "browser" for source in result.get("content_sources", [])))
        report_text = Path(result["report_path"]).read_text(encoding="utf-8")
        self.assertIn("Playwright browser probe", report_text)

    @patch("agents.id_agent.invoke_text_model", side_effect=AssertionError("LLM should not be called for shell-only browser evidence"))
    @patch("agents.id_agent.is_llm_enabled", return_value=True)
    @patch("agents.id_agent.run_playwright_probe")
    def test_id_agent_skips_llm_when_probe_does_not_reach_lesson(self, mock_probe, _mock_llm_enabled, _mock_invoke) -> None:
        output_dir = make_output_bundle_dir(self.temp_dir, "id shell only")
        mock_probe.return_value = {
            "available": True,
            "status": "asset_captured",
            "url": "https://example.com/course",
            "asset_url": "https://cdn.example.com/index.html",
            "lesson_url": "",
            "lesson_reached": False,
            "title": "Sample Course",
            "body_text": "Review shell and intro only",
            "snapshot_text": "Current Version Feedback Sign In",
            "visited_states": [
                {"step": "review_shell", "page_url": "https://example.com/course"},
                {"step": "asset_landing", "page_url": "https://cdn.example.com/index.html"},
            ],
            "artifacts": [],
            "warnings": ["Playwright reached the Rise asset page but did not advance into a lesson-level '#/lessons/...' state."],
        }

        findings, content_sources = run_id_review(
            {
                "messages": [],
                "findings": [],
                "sender": "",
                "next_agents": ["id"],
                "routing_reason": "",
                "user_text": "Review Chapter 1 at https://example.com/course",
                "raw_text": "/id Review Chapter 1 at https://example.com/course",
                "image_paths": [],
                "project_root": self.temp_dir,
                "config": self.config,
                "output_dir": str(output_dir),
                "content_sources": [],
                "resolved_content_text": "",
            }
        )

        self.assertTrue(any(finding["area"] == "Browser Coverage Limitation" for finding in findings))
        self.assertTrue(any(source.get("format") == "browser" for source in content_sources))

    def test_content_agent_handles_raw_figma_link_as_unresolved_source(self) -> None:
        result = invoke_workflow(
            user_text="Review storyboard copy in https://www.figma.com/design/abc/MyFile?node-id=1-2",
            raw_text="/cg Review storyboard copy in https://www.figma.com/design/abc/MyFile?node-id=1-2",
            image_paths=[],
            next_agents=["content"],
            project_root=self.temp_dir,
            config=self.config,
        )
        self.assertTrue(any("Figma" in finding["evidence"] or "figma" in finding["evidence"].lower() for finding in result["findings"]))
        self.assertTrue(any(finding["area"] == "Content Source" for finding in result["findings"]))

    def test_content_agent_uses_pre_resolved_figma_source(self) -> None:
        result = invoke_workflow(
            user_text="Review this storyboard frame",
            raw_text="/cg Review this storyboard frame",
            image_paths=[],
            next_agents=["content"],
            project_root=self.temp_dir,
            config=self.config,
            content_sources=[
                {
                    "kind": "figma",
                    "uri": "https://www.figma.com/design/abc/MyFile?node-id=1-2",
                    "display_name": "Storyboard Frame",
                    "format": "figma",
                    "extracted_text": "The User should organize color labels for the learner.",
                    "image_paths": [],
                    "location_hints": ["frame text"],
                    "extraction_mode": "figma-plugin",
                    "warnings": [],
                }
            ],
        )
        self.assertTrue(any(finding["source_agent"] == "content" for finding in result["findings"]))
        self.assertFalse(any(finding["area"] == "Content Source" for finding in result["findings"]))

    def test_content_workflow_reads_supported_local_documents(self) -> None:
        for artifact_path in (self.csv_path, self.docx_path, self.pdf_path):
            result = invoke_workflow(
                user_text=f"Review '{artifact_path}' for grammar and terminology",
                raw_text=f"/cg Review '{artifact_path}' for grammar and terminology",
                image_paths=[],
                next_agents=["content"],
                project_root=self.temp_dir,
                config=self.config,
            )
            self.assertTrue(any(finding["source_agent"] == "content" for finding in result["findings"]))
            report_text = Path(result["report_path"]).read_text(encoding="utf-8")
            self.assertIn("## Source Summary", report_text)
            self.assertIn(artifact_path.name, report_text)

    def test_consolidation_keeps_latest_sections(self) -> None:
        path = self.temp_dir / "knowledge" / "general" / "system_lessons.md"
        path.write_text("# Header\n\n" + "\n\n".join(f"## Section {i}\n- lesson {i}" for i in range(12)), encoding="utf-8")
        changed = maybe_consolidate(self.temp_dir, "system")
        content = path.read_text(encoding="utf-8")
        self.assertTrue(changed)
        self.assertIn("## Consolidated Historical Lessons", content)
        self.assertIn("## Section 11", content)
        self.assertIn("## Section 10", content)
        self.assertIn("## Section 9", content)

    def test_cleanup_removes_project_caches_but_keeps_outputs_directories(self) -> None:
        cache_dir = self.temp_dir / "core" / "__pycache__"
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "temp.pyc").write_bytes(b"123")
        loose_output = self.temp_dir / "outputs" / "loose.png"
        loose_output.write_bytes(b"png")
        bundle_dir = self.temp_dir / "outputs" / "20260412_sample_bundle"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        (bundle_dir / "report.md").write_text("keep", encoding="utf-8")

        summary = cleanup_project(self.temp_dir)

        self.assertGreaterEqual(summary["removed_count"], 2)
        self.assertFalse(cache_dir.exists())
        self.assertFalse(loose_output.exists())
        self.assertTrue(bundle_dir.exists())
        self.assertTrue((bundle_dir / "report.md").exists())

    def test_upgit_runs_cleanup_commit_and_push(self) -> None:
        cache_dir = self.temp_dir / "core" / "__pycache__"
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "temp.pyc").write_bytes(b"123")

        commands: list[list[str]] = []

        def fake_run(cmd: list[str], cwd: Path, text: bool, capture_output: bool, check: bool) -> CompletedProcess[str]:
            commands.append(cmd)
            mapping = {
                ("git", "rev-parse", "--is-inside-work-tree"): CompletedProcess(cmd, 0, "true\n", ""),
                ("git", "branch", "--show-current"): CompletedProcess(cmd, 0, "main\n", ""),
                ("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"): CompletedProcess(cmd, 0, "origin/main\n", ""),
                ("git", "remote"): CompletedProcess(cmd, 0, "origin\n", ""),
                ("git", "add", "-A"): CompletedProcess(cmd, 0, "", ""),
                ("git", "diff", "--cached", "--name-status"): CompletedProcess(cmd, 0, "M\tmain.py\nM\tdocs/communication.md\nD\tcore/__pycache__/temp.pyc\n", ""),
                ("git", "restore", "--staged", "--", "docs/communication.md"): CompletedProcess(cmd, 0, "", ""),
                ("git", "commit", "-m", "feat: sync repo"): CompletedProcess(cmd, 0, "[main abc123] feat: sync repo\n", ""),
                ("git", "rev-parse", "--short", "HEAD"): CompletedProcess(cmd, 0, "abc123\n", ""),
                ("git", "rev-list", "--left-right", "--count", "origin/main...HEAD"): CompletedProcess(cmd, 0, "0 1\n", ""),
                ("git", "push"): CompletedProcess(cmd, 0, "Everything up-to-date\n", ""),
            }
            result = mapping.get(tuple(cmd))
            if result is None:
                raise AssertionError(f"Unexpected git command: {cmd}")
            return result

        with patch("core.utils.subprocess.run", side_effect=fake_run):
            summary = upgit_project(self.temp_dir, commit_message="feat: sync repo")

        self.assertEqual(summary["status"], "pushed")
        self.assertTrue(summary["committed"])
        self.assertTrue(summary["pushed"])
        self.assertEqual(summary["commit_sha"], "abc123")
        self.assertEqual(summary["commit_message"], "feat: sync repo")
        self.assertEqual(summary["push_target"], "origin/main")
        self.assertGreaterEqual(summary["cleanup_summary"]["removed_count"], 1)
        self.assertFalse(cache_dir.exists())
        self.assertEqual(summary["excluded_paths"], ["docs/communication.md"])
        self.assertIn(["git", "add", "-A"], commands)
        self.assertIn(["git", "restore", "--staged", "--", "docs/communication.md"], commands)
        self.assertIn(["git", "push"], commands)

    def test_upgit_returns_no_changes_when_branch_is_clean(self) -> None:
        def fake_run(cmd: list[str], cwd: Path, text: bool, capture_output: bool, check: bool) -> CompletedProcess[str]:
            mapping = {
                ("git", "rev-parse", "--is-inside-work-tree"): CompletedProcess(cmd, 0, "true\n", ""),
                ("git", "branch", "--show-current"): CompletedProcess(cmd, 0, "main\n", ""),
                ("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"): CompletedProcess(cmd, 0, "origin/main\n", ""),
                ("git", "remote"): CompletedProcess(cmd, 0, "origin\n", ""),
                ("git", "add", "-A"): CompletedProcess(cmd, 0, "", ""),
                ("git", "diff", "--cached", "--name-status"): CompletedProcess(cmd, 0, "", ""),
                ("git", "rev-list", "--left-right", "--count", "origin/main...HEAD"): CompletedProcess(cmd, 0, "0 0\n", ""),
            }
            result = mapping.get(tuple(cmd))
            if result is None:
                raise AssertionError(f"Unexpected git command: {cmd}")
            return result

        with patch("core.utils.subprocess.run", side_effect=fake_run):
            summary = upgit_project(self.temp_dir)

        self.assertEqual(summary["status"], "no_changes")
        self.assertFalse(summary["committed"])
        self.assertFalse(summary["pushed"])
        self.assertEqual(summary["staged_change_count"], 0)

    def test_upgit_autogenerates_meaningful_commit_message_and_skips_runtime_paths(self) -> None:
        state = {"restore_called": False}

        def fake_run(cmd: list[str], cwd: Path, text: bool, capture_output: bool, check: bool) -> CompletedProcess[str]:
            if tuple(cmd) == ("git", "rev-parse", "--is-inside-work-tree"):
                return CompletedProcess(cmd, 0, "true\n", "")
            if tuple(cmd) == ("git", "branch", "--show-current"):
                return CompletedProcess(cmd, 0, "main\n", "")
            if tuple(cmd) == ("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"):
                return CompletedProcess(cmd, 0, "origin/main\n", "")
            if tuple(cmd) == ("git", "remote"):
                return CompletedProcess(cmd, 0, "origin\n", "")
            if tuple(cmd) == ("git", "add", "-A"):
                return CompletedProcess(cmd, 0, "", "")
            if tuple(cmd) == ("git", "diff", "--cached", "--name-status"):
                if state["restore_called"]:
                    return CompletedProcess(cmd, 0, "M\tmain.py\nM\tcore/utils.py\nM\ttests/test_workflow.py\n", "")
                return CompletedProcess(cmd, 0, "M\tmain.py\nM\tcore/utils.py\nM\ttests/test_workflow.py\nM\tdocs/communication.md\nA\toutputs/sample/report.md\n", "")
            if tuple(cmd) == ("git", "restore", "--staged", "--", "docs/communication.md", "outputs/sample/report.md"):
                state["restore_called"] = True
                return CompletedProcess(cmd, 0, "", "")
            if tuple(cmd) == ("git", "commit", "-m", "feat: update CLI workflow handling"):
                return CompletedProcess(cmd, 0, "[main def456] feat: update CLI workflow handling\n", "")
            if tuple(cmd) == ("git", "rev-parse", "--short", "HEAD"):
                return CompletedProcess(cmd, 0, "def456\n", "")
            if tuple(cmd) == ("git", "rev-list", "--left-right", "--count", "origin/main...HEAD"):
                return CompletedProcess(cmd, 0, "0 1\n", "")
            if tuple(cmd) == ("git", "push"):
                return CompletedProcess(cmd, 0, "ok\n", "")
            raise AssertionError(f"Unexpected git command: {cmd}")

        with patch("core.utils.subprocess.run", side_effect=fake_run):
            summary = upgit_project(self.temp_dir)

        self.assertEqual(summary["commit_message"], "feat: update CLI workflow handling")
        self.assertEqual(summary["excluded_paths"], ["docs/communication.md", "outputs/sample/report.md"])
        self.assertEqual(summary["staged_changes"], ["M\tmain.py", "M\tcore/utils.py", "M\ttests/test_workflow.py"])


if __name__ == "__main__":
    unittest.main()
