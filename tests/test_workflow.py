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
from core.knowledge import get_knowledge_context, load_knowledge_entries, maybe_consolidate
from core.reporting import generate_markdown_report
from core.state import merge_findings
from core.utils import cleanup_project, ensure_text_file, make_output_bundle_dir, upgit_project
from core.wcag import build_wcag_findings
from agents.id_agent import run_id_review
from agents.video_agent import run_video_review
from main import auto_detect_agents, detect_flow_type, normalize_command
from tools.wcag_contrast import contrast_ratio


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
        for relative in ("docs", "knowledge/general", "knowledge/requirements", "knowledge/procedures", "knowledge/backlog", "outputs"):
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
        shutil.copy(REPO_ROOT / "knowledge" / "general" / "process_facts.md", self.temp_dir / "knowledge" / "general" / "process_facts.md")
        shutil.copy(REPO_ROOT / "knowledge" / "procedures" / "procedure_candidates.md", self.temp_dir / "knowledge" / "procedures" / "procedure_candidates.md")
        shutil.copy(REPO_ROOT / "knowledge" / "backlog" / "reflection_followups.md", self.temp_dir / "knowledge" / "backlog" / "reflection_followups.md")
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
        self.video_path = self.fixture_dir / "lesson clip.mp4"
        self.video_path.write_text("fake video placeholder", encoding="utf-8")
        self.srt_path = self.fixture_dir / "lesson clip.srt"
        self.srt_path.write_text(
            "1\n00:00:00,000 --> 00:00:01,000\nWelcome to this onboarding lesson.\n\n"
            "2\n00:00:01,100 --> 00:00:02,000\nThis subtitle line is intentionally very very very long for one short cue.\n",
            encoding="utf-8",
        )

        os.environ["AGENT_QC_ROOT"] = str(self.temp_dir)
        os.environ["OPENAI_API_KEY"] = "test-openai"
        os.environ["GROQ_API_KEY"] = "test-groq"
        os.environ["GOOGLE_API_KEY"] = "test-google"
        self.config = AppConfig.load(self.temp_dir)

    def tearDown(self) -> None:
        os.environ.pop("AGENT_QC_ROOT", None)
        os.environ.pop("OPENAI_API_KEY", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_merge_findings_preserves_unique_ids(self) -> None:
        merged = merge_findings(
            [{"id": "ID-001", "severity": "Info", "area": "A", "evidence": "x", "impact": "y", "recommended_fix": "z", "source_agent": "id"}],
            [{"id": "ID-001", "severity": "Info", "area": "B", "evidence": "x", "impact": "y", "recommended_fix": "z", "source_agent": "id"}],
        )
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[1]["id"], "ID-002")

    def test_contrast_ratio_matches_wcag_reference_values(self) -> None:
        self.assertAlmostEqual(contrast_ratio((0, 0, 0), (255, 255, 255)), 21.0, places=2)
        self.assertAlmostEqual(contrast_ratio((119, 119, 119), (255, 255, 255)), 4.48, places=2)

    def test_wcag_adapter_reports_browser_accessible_name_issue(self) -> None:
        findings = build_wcag_findings(
            {
                "messages": [],
                "findings": [],
                "sender": "",
                "next_agents": ["id"],
                "routing_reason": "",
                "user_text": "Review accessibility",
                "raw_text": "/id Review accessibility",
                "image_paths": [],
                "project_root": self.temp_dir,
                "config": self.config,
                "output_dir": str(self.temp_dir / "outputs"),
                "content_sources": [],
                "resolved_content_text": "",
                "browser_probe": {
                    "visited_states": [
                        {
                            "step": "quiz feedback",
                            "actionables": [
                                {"role": "button", "name": "", "tag": "button"},
                            ],
                        }
                    ]
                },
            },
            prefix="ID",
            source_agent="id",
        )

        self.assertTrue(any(finding["area"] == "WCAG Accessible Name" for finding in findings))
        self.assertTrue(any("4.1.2 Name, Role, Value" in finding["evidence"] for finding in findings))

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
        entries = load_knowledge_entries(self.temp_dir, "human_feedback")
        self.assertTrue(any(entry["promoted"] for entry in entries if "Section 3 markers" in entry["summary"]))

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

    def test_cqc_command_normalization(self) -> None:
        payload, agents = normalize_command("/cqc review this articulate lesson")
        self.assertEqual(payload, "review this articulate lesson")
        self.assertEqual(agents, ["id", "content", "graphic"])
        self.assertEqual(detect_flow_type("/cqc review this articulate lesson"), "cqc")

    def test_vqc_command_normalization(self) -> None:
        payload, agents = normalize_command("/vqc review this local video")
        self.assertEqual(payload, "review this local video")
        self.assertEqual(agents, ["content", "graphic", "video"])
        self.assertEqual(detect_flow_type("/vqc review this local video"), "vqc")

    def test_auto_detect_routes_document_paths_to_content(self) -> None:
        agents = auto_detect_agents(f"Please QC '{self.csv_path}'", [], self.temp_dir)
        self.assertEqual(agents, ["content"])

    @patch("core.vqc.shutil.which", side_effect=lambda name: None if name in {"ffmpeg", "ffprobe"} else "")
    def test_vqc_flow_exports_report_when_runtime_dependencies_are_missing(self, _mock_which) -> None:
        result = invoke_workflow(
            user_text=f"Review '{self.video_path}' with subtitles '{self.srt_path}'",
            raw_text=f"/vqc Review '{self.video_path}' with subtitles '{self.srt_path}'",
            image_paths=[],
            next_agents=["content", "graphic", "video"],
            project_root=self.temp_dir,
            config=self.config,
            flow_type="vqc",
        )

        self.assertTrue(Path(result["report_path"]).exists())
        report_text = Path(result["report_path"]).read_text(encoding="utf-8")
        self.assertIn("VQC Collector Summary", report_text)
        self.assertIn("ffmpeg is not available in PATH", report_text)
        self.assertTrue((Path(result["output_dir"]) / "artifacts" / "subtitles.json").exists())
        self.assertTrue((Path(result["output_dir"]) / "artifacts" / "video_manifest.json").exists())
        self.assertTrue((Path(result["output_dir"]) / "artifacts" / "asr_transcript.json").exists())

    @patch("core.vqc.invoke_openai_transcription")
    @patch("core.vqc._extract_frame_samples")
    @patch("core.vqc._extract_audio_track", return_value=(True, ""))
    @patch("core.vqc._probe_video_manifest")
    @patch("core.vqc.shutil.which", side_effect=lambda name: "C:/bin/tool.exe")
    def test_vqc_flow_collects_video_artifacts_and_alignment_findings(
        self,
        _mock_which,
        mock_manifest,
        _mock_audio,
        mock_frames,
        mock_transcription,
    ) -> None:
        frame_path = self.fixture_dir / "frame_0001.png"
        frame_path.write_text("frame", encoding="utf-8")
        mock_manifest.return_value = {
            "duration_seconds": 5.0,
            "format_name": "mp4",
            "size_bytes": 1234,
            "video_stream": {"width": 1280, "height": 720, "codec_name": "h264", "avg_frame_rate": "30/1"},
            "audio_stream": {"codec_name": "aac", "sample_rate": "48000", "channels": 2},
        }
        mock_frames.return_value = [
            {
                "timestamp": 0.5,
                "timestamp_label": "00:00:00.500",
                "cue_index": 1,
                "sample_type": "subtitle-start",
                "image_path": str(frame_path),
                "status": "ok",
            }
        ]
        mock_transcription.return_value = {
            "segments": [
                {"start": 0.0, "end": 1.0, "text": "Welcome to this compliance course."},
                {"start": 1.1, "end": 2.0, "text": "Short line."},
            ]
        }

        result = invoke_workflow(
            user_text=f"Review '{self.video_path}' with subtitles '{self.srt_path}'",
            raw_text=f"/vqc Review '{self.video_path}' with subtitles '{self.srt_path}'",
            image_paths=[],
            next_agents=["content", "graphic", "video"],
            project_root=self.temp_dir,
            config=self.config,
            flow_type="vqc",
        )

        source_agents = {finding["source_agent"] for finding in result["findings"]}
        self.assertIn("content", source_agents)
        self.assertIn("graphic", source_agents)
        self.assertIn("video", source_agents)
        self.assertTrue(any(finding["area"] == "Subtitle And Audio Mismatch" for finding in result["findings"]))
        self.assertTrue(any(finding["area"] == "Subtitle Readability" for finding in result["findings"]))
        self.assertIn(str(frame_path), result.get("image_paths", []))
        report_text = Path(result["report_path"]).read_text(encoding="utf-8")
        self.assertIn("asr_status=ok", report_text)
        self.assertIn(self.video_path.name, report_text)
        self.assertIn(self.srt_path.name, report_text)

    def test_video_agent_flags_uncaptioned_speech(self) -> None:
        findings = run_video_review(
            {
                "project_root": self.temp_dir,
                "video_probe": {
                    "warnings": [],
                    "asr_status": "ok",
                    "subtitles": [
                        {
                            "cue_index": 1,
                            "start": 0.0,
                            "end": 1.0,
                            "start_timecode": "00:00:00.000",
                            "end_timecode": "00:00:01.000",
                            "text": "Hello there",
                        }
                    ],
                    "asr_segments": [
                        {"start": 2.0, "end": 3.0, "text": "This speech is not captioned"}
                    ],
                },
            }
        )
        self.assertTrue(any(finding["area"] == "Uncaptioned Speech Segment" for finding in findings))

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

    def test_reflection_repeats_increment_seen_count_without_duplicate_entry(self) -> None:
        from agents.reflection_agent import reflection_node

        findings = [
            {
                "id": "ID-001",
                "severity": "Major",
                "area": "Knowledge Check State Leakage",
                "evidence": "Learner sees incorrect feedback before submit.",
                "impact": "Assessment validity is undermined.",
                "recommended_fix": "Hide feedback until submit.",
                "source_agent": "id",
            },
            {
                "id": "C-001",
                "severity": "Minor",
                "area": "Grammar/Spelling",
                "evidence": "Detected article error in learner-facing copy.",
                "impact": "Polish is reduced.",
                "recommended_fix": "Fix the article.",
                "source_agent": "content",
            },
        ]

        for turn in range(2):
            reflection_node(
                {
                    "findings": findings,
                    "project_root": self.temp_dir,
                    "config": self.config,
                    "raw_text": f"/cqc run {turn}",
                    "user_text": "Review chapter 1 knowledge check",
                    "flow_type": "cqc",
                }
            )

        entries = [entry for entry in load_knowledge_entries(self.temp_dir, "system") if "knowledge check state leakage" in entry["summary"].lower()]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["seen_count"], 2)

    def test_reflection_auto_promotes_after_third_repeat(self) -> None:
        from agents.reflection_agent import reflection_node

        findings = [
            {
                "id": "ID-001",
                "severity": "Major",
                "area": "Knowledge Check State Leakage",
                "evidence": "Learner sees incorrect feedback before submit.",
                "impact": "Assessment validity is undermined.",
                "recommended_fix": "Hide feedback until submit.",
                "source_agent": "id",
            },
            {
                "id": "C-001",
                "severity": "Minor",
                "area": "Grammar/Spelling",
                "evidence": "Detected article error in learner-facing copy.",
                "impact": "Polish is reduced.",
                "recommended_fix": "Fix the article.",
                "source_agent": "content",
            },
        ]

        for turn in range(3):
            reflection_node(
                {
                    "findings": findings,
                    "project_root": self.temp_dir,
                    "config": self.config,
                    "raw_text": f"/cqc repeat {turn}",
                    "user_text": "Review chapter 1 knowledge check",
                    "flow_type": "cqc",
                }
            )

        entries = [entry for entry in load_knowledge_entries(self.temp_dir, "system") if "knowledge check state leakage" in entry["summary"].lower()]
        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["promoted"])
        self.assertEqual(entries[0]["seen_count"], 3)

    def test_asset_specific_info_routes_to_followup_or_discard_not_system(self) -> None:
        from agents.reflection_agent import reflection_node

        findings = [
            {
                "id": "FG-001",
                "severity": "Info",
                "area": "Graphic Coverage Note",
                "evidence": "Used page-2026-04-23T07-13-40-434Z.png for one screenshot-only visual check.",
                "impact": "Only this asset state was visible.",
                "recommended_fix": "Capture more screenshots if broader visual scope is needed.",
                "source_agent": "graphic",
            },
            {
                "id": "ID-002",
                "severity": "Major",
                "area": "Knowledge Check State Leakage",
                "evidence": "Learner sees incorrect feedback before submit.",
                "impact": "Assessment validity is undermined.",
                "recommended_fix": "Hide feedback until submit.",
                "source_agent": "id",
            },
        ]

        reflection_node(
            {
                "findings": findings,
                "project_root": self.temp_dir,
                "config": self.config,
                "raw_text": "/cqc asset specific",
                "user_text": "Review chapter 1",
                "flow_type": "cqc",
            }
        )
        system_entries = load_knowledge_entries(self.temp_dir, "system")
        self.assertFalse(any("graphic coverage note" in entry["summary"].lower() for entry in system_entries))

    def test_scoped_knowledge_context_ignores_followups(self) -> None:
        from core.knowledge import append_or_update_entry

        append_or_update_entry(
            self.temp_dir,
            "process_facts",
            {
                "id": "process-fact-001",
                "title": "## Process Fact",
                "category": "process_fact",
                "tags": ["id", "articulate", "knowledge-check"],
                "source_agent": "id",
                "first_seen_at": "2026-04-23 10:00:00",
                "last_seen_at": "2026-04-23 10:00:00",
                "seen_count": 1,
                "confidence": "high",
                "promoted": False,
                "promoted_by": "",
                "example_run_refs": ["/cqc chapter 1"],
                "summary": "Capture direct asset evidence for articulate knowledge checks.",
                "rationale": "This improves evidence quality.",
                "recommended_action": "Resolve the asset URL before reviewing the quiz flow.",
            },
        )
        append_or_update_entry(
            self.temp_dir,
            "followups",
            {
                "id": "follow-up-001",
                "title": "## Follow-up",
                "category": "follow_up_item",
                "tags": ["id", "articulate", "knowledge-check"],
                "source_agent": "id",
                "first_seen_at": "2026-04-23 10:00:00",
                "last_seen_at": "2026-04-23 10:00:00",
                "seen_count": 1,
                "confidence": "medium",
                "promoted": False,
                "promoted_by": "",
                "example_run_refs": ["/cqc chapter 1"],
                "summary": "Improve collector heuristics for articulate quiz branching.",
                "rationale": "This is a code follow-up, not a prompt rule.",
                "recommended_action": "Adjust collector behavior.",
            },
        )

        context = get_knowledge_context(
            self.temp_dir,
            mode="id",
            state={
                "project_root": self.temp_dir,
                "user_text": "Review this Articulate knowledge check",
                "flow_type": "cqc",
                "browser_probe": {"status": "lesson_captured"},
                "content_sources": [],
                "image_paths": [],
            },
        )
        self.assertIn("Capture direct asset evidence for articulate knowledge checks.", context)
        self.assertNotIn("Improve collector heuristics for articulate quiz branching.", context)

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

    @patch(
        "agents.graphic_agent.audit_image_contrast",
        return_value={
            "issues": [
                {
                    "image_path": "/tmp/scene-1.png",
                    "label": "Continue",
                    "ratio": 2.84,
                    "threshold": 4.5,
                    "foreground_hex": "#777777",
                    "background_hex": "#FFFFFF",
                    "bbox": (10, 20, 120, 24),
                    "large_text": False,
                }
            ],
            "limitations": [],
            "checked_images": ["/tmp/scene-1.png"],
        },
    )
    @patch("agents.graphic_agent.is_llm_enabled", return_value=False)
    def test_graphic_agent_emits_deterministic_wcag_findings_when_available(self, _mock_llm_enabled, _mock_audit) -> None:
        image_path = self.fixture_dir / "scene-1.png"
        image_path.write_text("placeholder", encoding="utf-8")

        result = invoke_workflow(
            user_text="Review this screenshot for contrast",
            raw_text=f"/fg Review this screenshot for contrast {image_path}",
            image_paths=[str(image_path)],
            next_agents=["graphic"],
            project_root=self.temp_dir,
            config=self.config,
        )

        self.assertTrue(any(finding["area"] == "WCAG Contrast Ratio" for finding in result["findings"]))
        self.assertTrue(any("2.84:1" in finding["evidence"] for finding in result["findings"]))
        self.assertFalse(any(finding["area"] == "Graphic Review" for finding in result["findings"]))

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

    @patch("agents.id_agent.run_playwright_probe", side_effect=AssertionError("ID agent should reuse the collector probe in CQC flow"))
    @patch("agents.id_agent.is_llm_enabled", return_value=False)
    @patch("agents.content_agent.is_llm_enabled", return_value=False)
    @patch("agents.graphic_agent.is_llm_enabled", return_value=False)
    @patch("core.cqc.run_playwright_probe")
    def test_cqc_flow_collects_shared_evidence_once(
        self,
        mock_collector_probe,
        _graphic_llm_enabled,
        _content_llm_enabled,
        _id_llm_enabled,
        _id_probe,
    ) -> None:
        screenshot_one = str((self.temp_dir / "collector_state_1.png").resolve())
        screenshot_two = str((self.temp_dir / "collector_state_2.png").resolve())
        Path(screenshot_one).write_text("image-1", encoding="utf-8")
        Path(screenshot_two).write_text("image-2", encoding="utf-8")
        mock_collector_probe.return_value = {
            "available": True,
            "status": "lesson_captured",
            "url": "https://example.com/course",
            "asset_url": "https://cdn.example.com/index.html",
            "lesson_url": "https://cdn.example.com/index.html#/lessons/chapter-2",
            "lesson_reached": True,
            "title": "Sample Course",
            "body_text": "Color and behavior matter in this course.",
            "content_text": "The User should organize color labels and review behavior guidance.",
            "snapshot_text": "Start Course",
            "screenshot_path": screenshot_two,
            "visited_states": [
                {
                    "step": "asset_landing",
                    "page_url": "https://cdn.example.com/index.html",
                    "title": "Course landing",
                    "content_excerpt": "Start Course",
                    "screenshot_path": screenshot_one,
                    "lesson_label": "Course Introduction",
                    "matched_label": "",
                },
                {
                    "step": "state_1",
                    "page_url": "https://cdn.example.com/index.html#/lessons/chapter-2",
                    "title": "Lesson 1",
                    "content_excerpt": "The User should organize color labels and review behavior guidance.",
                    "screenshot_path": screenshot_two,
                    "lesson_label": "Chapter 2",
                    "matched_label": "Start Course",
                },
            ],
            "actions_attempted": 2,
            "actions_changed_state": 1,
            "artifacts": [],
            "warnings": [],
        }

        result = invoke_workflow(
            user_text="Review this articulate course for flow, grammar, and visuals: https://example.com/course",
            raw_text="/cqc Review this articulate course for flow, grammar, and visuals: https://example.com/course",
            image_paths=[],
            next_agents=["id", "content", "graphic"],
            project_root=self.temp_dir,
            config=self.config,
            flow_type="cqc",
        )

        source_agents = {finding["source_agent"] for finding in result["findings"]}
        self.assertIn("id", source_agents)
        self.assertIn("content", source_agents)
        self.assertIn("graphic", source_agents)
        self.assertEqual(mock_collector_probe.call_count, 1)
        self.assertTrue(any(source.get("display_name") == "CQC Browser Collector Summary" for source in result.get("content_sources", [])))
        self.assertGreaterEqual(len(result.get("content_sources", [])), 2)
        self.assertIn(screenshot_one, result.get("image_paths", []))
        self.assertIn(screenshot_two, result.get("image_paths", []))
        report_text = Path(result["report_path"]).read_text(encoding="utf-8")
        self.assertIn("CQC Browser Collector Summary", report_text)

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
