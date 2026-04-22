from __future__ import annotations

import re
from pathlib import Path

from core.browser import BrowserProbeResult, run_playwright_probe
from core.knowledge import get_knowledge_context
from core.llm import invoke_text_model, is_llm_enabled, parse_json_object
from core.state import AgentState, ContentSource, QAFinding
from core.utils import log_communication
from tools.text_tools import check_british_english, extract_quoted_labels, make_finding_id


URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


def _build_finding(index: int, severity: str, area: str, evidence: str, impact: str, fix: str) -> QAFinding:
    return {
        "id": make_finding_id("ID", index),
        "severity": severity,
        "area": area,
        "evidence": evidence,
        "impact": impact,
        "recommended_fix": fix,
        "source_agent": "id",
    }


def _run_browser_probe(state: AgentState) -> BrowserProbeResult | None:
    cached_probe = state.get("browser_probe")
    if isinstance(cached_probe, dict):
        return cached_probe
    urls = URL_PATTERN.findall(state.get("user_text", ""))
    output_dir = state.get("output_dir", "")
    if not urls or not output_dir:
        return None
    try:
        return run_playwright_probe(urls[0], Path(output_dir), state.get("user_text", ""))
    except Exception as exc:
        return {
            "available": False,
            "status": "error",
            "url": urls[0],
            "warnings": [f"Playwright probe failed: {exc}"],
            "artifacts": [],
        }


def _probe_to_content_source(probe: BrowserProbeResult | None) -> ContentSource | None:
    if not probe:
        return None

    image_paths = [probe["screenshot_path"]] if probe.get("screenshot_path") else []
    extracted_parts = []
    if probe.get("title"):
        extracted_parts.append(f"Title: {probe['title']}")
    if probe.get("asset_url"):
        extracted_parts.append(f"Resolved asset URL: {probe['asset_url']}")
    if probe.get("lesson_url"):
        extracted_parts.append(f"Reached lesson URL: {probe['lesson_url']}")
    if probe.get("actions_attempted") is not None:
        extracted_parts.append(
            f"Traversal coverage: {probe.get('actions_attempted', 0)} action(s) attempted, {probe.get('actions_changed_state', 0)} state-changing action(s)."
        )
    if probe.get("body_text"):
        extracted_parts.append(f"Body text excerpt:\n{probe['body_text'][:4000]}")
    if probe.get("content_text"):
        extracted_parts.append(f"Main content excerpt:\n{probe['content_text'][:4000]}")
    elif probe.get("snapshot_text"):
        extracted_parts.append(f"Snapshot excerpt:\n{probe['snapshot_text'][:4000]}")
    visited_states = probe.get("visited_states", [])
    if visited_states:
        state_lines = []
        for state in visited_states:
            state_lines.append(
                (
                    f"- {state.get('step', 'state')}: {state.get('title', '')} @ {state.get('page_url', '')}"
                    f" | action: {state.get('matched_label', '')}"
                ).strip()
            )
        extracted_parts.append("Visited browser states:\n" + "\n".join(state_lines))

    return {
        "kind": "text",
        "uri": probe.get("url", ""),
        "display_name": "Playwright browser probe",
        "format": "browser",
        "extracted_text": "\n\n".join(extracted_parts),
        "image_paths": image_paths,
        "location_hints": ["browser probe", "live browser state", "lesson traversal evidence"],
        "extraction_mode": "playwright-lesson-traverse" if probe.get("lesson_reached") else "playwright-cli",
        "warnings": list(probe.get("warnings", [])),
    }


def _probe_has_lesson_evidence(probe: BrowserProbeResult | None) -> bool:
    if not probe:
        return False
    if probe.get("lesson_reached"):
        return True
    lesson_url = str(probe.get("lesson_url", ""))
    return "#/lessons/" in lesson_url


def _probe_state_summary(probe: BrowserProbeResult | None) -> str:
    if not probe:
        return ""
    labels = []
    for state in probe.get("visited_states", []):
        step = state.get("step", "").strip()
        page_url = state.get("page_url", "").strip()
        matched_label = state.get("matched_label", "").strip()
        if step and page_url:
            if matched_label:
                labels.append(f"{step} ({matched_label}) -> {page_url}")
            else:
                labels.append(f"{step} -> {page_url}")
        elif step:
            labels.append(step)
    return "; ".join(labels[:6])


def _fallback_id_review(state: AgentState, probe: BrowserProbeResult | None = None) -> list[QAFinding]:
    text = state.get("user_text", "")
    findings: list[QAFinding] = []
    index = 1

    if probe:
        if _probe_has_lesson_evidence(probe):
            evidence = f"Playwright browser probe reached lesson state from {probe.get('url', 'the target URL')}."
            if probe.get("lesson_url"):
                evidence += f" Lesson URL: {probe['lesson_url']}."
            if probe.get("title"):
                evidence += f" Captured title: {probe['title']}."
            if probe.get("actions_attempted") is not None:
                evidence += (
                    f" Traversal attempted {probe.get('actions_attempted', 0)} action(s)"
                    f" and changed state {probe.get('actions_changed_state', 0)} time(s)."
                )
            state_summary = _probe_state_summary(probe)
            if state_summary:
                evidence += f" Traversed states: {state_summary}."
            findings.append(
                _build_finding(
                    index,
                    "Info",
                    "Browser Evidence",
                    evidence,
                    "The pass now has live lesson-level browser evidence, but interactive depth still depends on how many reveal states and question states were exercised.",
                    "Continue with section-by-section Playwright interaction steps and capture additional state notes or screenshots for each revealed state.",
                )
            )
            index += 1
        elif probe.get("status") in {"captured", "asset_captured"}:
            evidence = f"Playwright opened {probe.get('url', 'the target URL')}"
            if probe.get("asset_url"):
                evidence += f" and resolved the live Rise asset URL {probe['asset_url']}"
            evidence += ", but did not reach a lesson-level '#/lessons/...' page."
            state_summary = _probe_state_summary(probe)
            if state_summary:
                evidence += f" Captured states: {state_summary}."
            findings.append(
                _build_finding(
                    index,
                    "Info",
                    "Browser Coverage Limitation",
                    evidence,
                    "Any QA findings about lesson copy, chapter flow, knowledge checks, or navigation beyond the landing flow would be speculative.",
                    "Extend the Playwright traversal until a concrete lesson state is reached, then exercise every reveal and knowledge-check state within the requested chapter.",
                )
            )
            index += 1
        else:
            findings.append(
                _build_finding(
                    index,
                    "Info",
                    "Browser Probe",
                    f"Playwright browser probe did not complete for {probe.get('url', 'the target URL')}. {' '.join(probe.get('warnings', []))}".strip(),
                    "Without a successful live probe, the review cannot confirm interaction behavior from the actual page state.",
                    "Fix Playwright availability or provide tester notes/screenshots before treating the ID review as complete.",
                )
            )
            index += 1

    urls = URL_PATTERN.findall(text)
    for url in urls:
        findings.append(
            _build_finding(
                index,
                "Info",
                "Browser Coverage",
                f"Detected course URL: {url}",
                "The course should be tested with artifact-based browser notes to validate interactions end-to-end.",
                "Open the course with Playwright or capture tester notes before the next QA pass.",
            )
        )
        index += 1

    lowered = text.lower()
    if "knowledge check" in lowered or "quiz" in lowered:
        findings.append(
            _build_finding(
                index,
                "Info",
                "Assessment Coverage",
                "The request references a quiz or Knowledge Check flow.",
                "Incomplete quiz traversal can hide follow-up questions, feedback states, or broken continue actions.",
                "Answer every question sequentially, scroll after each one, and verify no further interactions remain.",
            )
        )
        index += 1

    if any(token in lowered for token in ("accordion", "click to reveal", "marker", "tab")):
        findings.append(
            _build_finding(
                index,
                "Info",
                "Interactive Coverage",
                "The request references interactive components that often require exhaustive clicking.",
                "Skipping one item can miss hidden content mismatches or dead interactions.",
                "Exercise every reveal item individually and record browser notes for each interaction.",
            )
        )
        index += 1

    for issue in check_british_english(text):
        findings.append(
            _build_finding(
                index,
                "Minor",
                "Grammar/Spelling",
                issue["evidence"],
                "Mixed English variants reduce consistency and can conflict with project style requirements.",
                issue["recommended_fix"],
            )
        )
        index += 1

    labels = extract_quoted_labels(text)
    for label in labels:
        if label.isalpha() and label.upper() != label:
            findings.append(
                _build_finding(
                    index,
                    "Suggestion",
                    "UI Labels",
                    f"Detected quoted control label '{label}' that is not ALL CAPS.",
                    "The project requirements specify ALL CAPS labels for buttons and controls.",
                    f"Confirm whether '{label}' is a button label and standardize it to '{label.upper()}'.",
                )
            )
            index += 1

    if not findings:
        findings.append(
            _build_finding(
                index,
                "Info",
                "ID Triage",
                "No explicit interaction defects were present in the request text.",
                "A live browser pass is still needed to validate navigation, quiz logic, and accessibility in context.",
                "Capture artifact-based notes or screenshots for a deeper ID review.",
            )
        )

    return findings


def _normalize_llm_findings(raw_findings: list[dict]) -> list[QAFinding]:
    normalized: list[QAFinding] = []
    for index, item in enumerate(raw_findings, start=1):
        normalized.append(
            _build_finding(
                index,
                str(item.get("severity", "Info")),
                str(item.get("area", "Instructional Design")),
                str(item.get("evidence", "Model-generated review finding.")),
                str(item.get("impact", "Potential impact on learner experience or QA coverage.")),
                str(item.get("recommended_fix", "Review and address the issue.")),
            )
        )
    return normalized


def _is_generic_llm_finding(finding: QAFinding, probe: BrowserProbeResult | None) -> bool:
    evidence = finding.get("evidence", "")
    recommended_fix = finding.get("recommended_fix", "")
    area = finding.get("area", "")

    generic_evidence_prefixes = (
        "Browser body excerpt:",
        "Browser console summary:",
        "Browser title:",
        "WCAG 2.2 Baseline:",
    )
    generic_fix_prefixes = (
        "Verify that ",
        "Review the course",
        "Review the ",
        "Investigate and resolve browser console",
        "Ensure that ",
    )
    if evidence.startswith(generic_evidence_prefixes) and recommended_fix.startswith(generic_fix_prefixes):
        return True
    if area in {"Accessibility", "Content", "Language"} and recommended_fix.startswith(("Verify ", "Review ")):
        return True
    if probe and probe.get("lesson_reached") and "Lessons must be completed in order" in evidence and "This lesson is currently unavailable" in evidence:
        return True
    return False


def _sanitize_llm_findings(findings: list[QAFinding], probe: BrowserProbeResult | None) -> list[QAFinding]:
    sanitized = [finding for finding in findings if not _is_generic_llm_finding(finding, probe)]
    if sanitized:
        return sanitized
    return []


def _browser_prompt_block(probe: BrowserProbeResult | None) -> str:
    if not probe:
        return "No browser probe was available."

    lines = [f"Browser probe status: {probe.get('status', 'unknown')}"]
    if probe.get("url"):
        lines.append(f"Browser probe URL: {probe['url']}")
    if probe.get("asset_url"):
        lines.append(f"Resolved asset URL: {probe['asset_url']}")
    if probe.get("lesson_url"):
        lines.append(f"Lesson URL reached: {probe['lesson_url']}")
    if probe.get("actions_attempted") is not None:
        lines.append(
            "Traversal coverage: "
            f"{probe.get('actions_attempted', 0)} action(s) attempted, "
            f"{probe.get('actions_changed_state', 0)} state-changing action(s)"
        )
    if probe.get("title"):
        lines.append(f"Browser title: {probe['title']}")
    if probe.get("body_text"):
        lines.append(f"Browser body excerpt:\n{probe['body_text'][:4000]}")
    if probe.get("content_text"):
        lines.append(f"Main content excerpt:\n{probe['content_text'][:4000]}")
    elif probe.get("snapshot_text"):
        lines.append(f"Browser snapshot excerpt:\n{probe['snapshot_text'][:4000]}")
    visited_states = probe.get("visited_states", [])
    if visited_states:
        lines.append(
            "Visited browser states:\n- " + "\n- ".join(
                (
                    f"{state.get('step', 'state')}: {state.get('title', '')} @ {state.get('page_url', '')}"
                    f" | action: {state.get('matched_label', '')}"
                ).strip()
                for state in visited_states[:8]
            )
        )
    if probe.get("warnings"):
        lines.append("Browser warnings:\n- " + "\n- ".join(probe["warnings"]))
    return "\n".join(lines)


def run_id_review(state: AgentState) -> tuple[list[QAFinding], list[ContentSource]]:
    probe = _run_browser_probe(state)
    content_sources = list(state.get("content_sources", []))
    probe_source = _probe_to_content_source(probe)
    if probe_source:
        content_sources.append(probe_source)

    if probe and not _probe_has_lesson_evidence(probe):
        return _fallback_id_review(state, probe), content_sources

    config = state["config"]
    api_key = config.api_key_for_provider(config.id_provider)
    if not is_llm_enabled(config.id_provider, api_key):
        return _fallback_id_review(state, probe), content_sources

    knowledge_context = get_knowledge_context(state["project_root"])
    system_prompt = f"""
You are InstructionalDesign-Agent for e-learning QA.
Review the request and extract actionable QA findings focused on:
- navigation
- interactions
- quiz / knowledge check logic
- accessibility / WCAG
- grammar and spelling on screen
- British English consistency

Project knowledge:
{knowledge_context}

Return strict JSON with this shape:
{{
  "findings": [
    {{
      "severity": "Critical|Major|Minor|Suggestion|Info",
      "area": "short area",
      "evidence": "specific evidence",
      "impact": "impact on learner",
      "recommended_fix": "clear fix"
    }}
  ]
}}

Rules:
- Use only supported severities.
- If the prompt is too vague, still return at least one Info finding describing what evidence is still needed.
- Focus on evidence grounded in the provided request.
- Assume section-level QC requires exhaustive coverage inside that section:
  - all visible interactives must be exercised
  - newly revealed text must be inspected, not skipped
  - knowledge checks should be traversed as far as the evidence allows
- If the evidence appears incomplete for a requested section, explicitly include an Info finding that names the missing coverage instead of pretending the QC pass was complete.
- Do not output checklist-style findings such as "verify content", "review accessibility", or "check language consistency".
- Do not treat generic Review 360 shell text, locked future lessons, or console summaries as defects unless the evidence shows learner-facing breakage in the tested scope.
- Prefer fewer, sharper findings over generic QA advice.
""".strip()
    user_prompt = (
        "Review this request for instructional design QA:\n"
        f"{state.get('user_text', '').strip()}\n\n"
        f"Available browser evidence:\n{_browser_prompt_block(probe)}"
    )

    try:
        raw_response = invoke_text_model(
            provider=config.id_provider,
            model=config.id_model,
            api_key=api_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        payload = parse_json_object(raw_response)
        findings = _sanitize_llm_findings(_normalize_llm_findings(payload.get("findings", [])), probe)
        return findings or _fallback_id_review(state, probe), content_sources
    except Exception:
        return _fallback_id_review(state, probe), content_sources


def id_node(state: AgentState) -> AgentState:
    findings, content_sources = run_id_review(state)
    log_communication(
        state["project_root"],
        "ID Agent",
        "Workflow",
        f"Produced {len(findings)} finding(s) for instructional design review.",
    )
    return {
        "messages": [],
        "findings": findings,
        "sender": "id",
        "next_agents": ["FINISH"],
        "routing_reason": state.get("routing_reason", ""),
        "content_sources": content_sources,
    }
