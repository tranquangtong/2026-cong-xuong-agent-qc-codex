from __future__ import annotations

import re

from core.knowledge import get_knowledge_context
from core.llm import invoke_text_model, is_llm_enabled, parse_json_object
from core.state import AgentState, QAFinding
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


def _fallback_id_review(state: AgentState) -> list[QAFinding]:
    text = state.get("user_text", "")
    findings: list[QAFinding] = []
    index = 1

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


def run_id_review(state: AgentState) -> list[QAFinding]:
    config = state["config"]
    api_key = config.api_key_for_provider(config.id_provider)
    if not is_llm_enabled(config.id_provider, api_key):
        return _fallback_id_review(state)

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
""".strip()
    user_prompt = f"Review this request for instructional design QA:\n{state.get('user_text', '').strip()}"

    try:
        raw_response = invoke_text_model(
            provider=config.id_provider,
            model=config.id_model,
            api_key=api_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        payload = parse_json_object(raw_response)
        findings = _normalize_llm_findings(payload.get("findings", []))
        return findings or _fallback_id_review(state)
    except Exception:
        return _fallback_id_review(state)


def id_node(state: AgentState) -> AgentState:
    findings = run_id_review(state)
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
    }
