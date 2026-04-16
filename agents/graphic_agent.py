from __future__ import annotations

import re

from core.knowledge import get_knowledge_context
from core.llm import invoke_multimodal_model, invoke_text_model, is_llm_enabled, parse_json_object
from core.state import AgentState, QAFinding
from core.utils import log_communication
from tools.text_tools import make_finding_id


FIGMA_PATTERN = re.compile(r"https?://(?:www\.)?figma\.com/\S+", re.IGNORECASE)


def _build_finding(index: int, severity: str, area: str, evidence: str, impact: str, fix: str) -> QAFinding:
    return {
        "id": make_finding_id("FG", index),
        "severity": severity,
        "area": area,
        "evidence": evidence,
        "impact": impact,
        "recommended_fix": fix,
        "source_agent": "graphic",
    }


def _fallback_graphic_review(state: AgentState) -> list[QAFinding]:
    findings: list[QAFinding] = []
    index = 1
    text = state.get("user_text", "")

    figma_links = FIGMA_PATTERN.findall(text)
    for link in figma_links:
        findings.append(
            _build_finding(
                index,
                "Info",
                "Figma Source",
                f"Detected Figma link: {link}",
                "The linked design should be reviewed for visual hierarchy, spacing, accessibility, and consistency.",
                "Open the linked Figma frame or export a screenshot, then review it against the graphic QA and WCAG 2.2 checklist.",
            )
        )
        index += 1

    for image_path in state.get("image_paths", []):
        findings.append(
            _build_finding(
                index,
                "Info",
                "Graphic Review",
                f"Image supplied for review: {image_path}",
                "The design can be checked for contrast, layout, readability, and interaction affordance.",
                "Review the supplied image against spacing, hierarchy, and WCAG 2.2 visual accessibility criteria.",
            )
        )
        index += 1

    if not findings:
        findings.append(
            _build_finding(
                index,
                "Info",
                "Graphic QA",
                "No Figma link or screenshot was supplied.",
                "Graphic QA requires a specific frame, node, or exported image to inspect.",
                "Provide a Figma link or screenshot for the target design.",
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
                str(item.get("area", "Graphic QA")),
                str(item.get("evidence", "Model-generated graphic QA finding.")),
                str(item.get("impact", "Potential impact on usability, accessibility, or visual consistency.")),
                str(item.get("recommended_fix", "Review and address the issue.")),
            )
        )
    return normalized


def run_graphic_review(state: AgentState) -> list[QAFinding]:
    config = state["config"]
    api_key = config.api_key_for_provider(config.graphic_provider)
    if not is_llm_enabled(config.graphic_provider, api_key):
        return _fallback_graphic_review(state)

    knowledge_context = get_knowledge_context(state["project_root"])
    figma_links = FIGMA_PATTERN.findall(state.get("user_text", ""))
    source_note = "\n".join(f"- {link}" for link in figma_links) if figma_links else "- No explicit Figma link detected."
    system_prompt = f"""
You are Graphic-Agent for e-learning QA.
Review the supplied design request and identify findings about:
- layout and spacing
- typography and readability
- contrast and accessibility
- WCAG 2.2-relevant visual issues
- visual hierarchy
- component consistency
- touch target and focus visibility risks

Shared project knowledge:
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
- Prefer concrete visual evidence.
- If only a Figma link is given and no screenshot is available, return at least one Info finding describing what should be inspected.
- Use WCAG 2.2 as the accessibility baseline.
""".strip()
    user_prompt = f"""Review this graphic QA request.

Request text:
{state.get('user_text', '').strip()}

Referenced Figma links:
{source_note}
"""

    try:
        if state.get("image_paths"):
            raw_response = invoke_multimodal_model(
                provider=config.graphic_provider,
                model=config.graphic_model,
                api_key=api_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                image_paths=state.get("image_paths", []),
            )
        else:
            raw_response = invoke_text_model(
                provider=config.graphic_provider,
                model=config.graphic_model,
                api_key=api_key,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        payload = parse_json_object(raw_response)
        findings = _normalize_llm_findings(payload.get("findings", []))
        return findings or _fallback_graphic_review(state)
    except Exception:
        return _fallback_graphic_review(state)


def graphic_node(state: AgentState) -> AgentState:
    findings = run_graphic_review(state)
    log_communication(
        state["project_root"],
        "Graphic Agent",
        "Workflow",
        f"Produced {len(findings)} finding(s) for graphic review.",
    )
    return {
        "messages": [],
        "findings": findings,
        "sender": "graphic",
        "next_agents": ["FINISH"],
        "routing_reason": state.get("routing_reason", ""),
    }
