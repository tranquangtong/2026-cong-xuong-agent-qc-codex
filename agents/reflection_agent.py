from __future__ import annotations

from collections import OrderedDict
from datetime import datetime

from core.knowledge import append_lesson_block, maybe_consolidate
from core.llm import invoke_text_model, is_llm_enabled, parse_json_object
from core.state import AgentState
from core.utils import log_communication


MIN_FINDINGS_FOR_AUTO_REFLECTION = 2


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _derive_lessons_from_findings(findings: list[dict]) -> list[str]:
    lessons: list[str] = []
    seen = OrderedDict()
    for finding in findings:
        area = finding["area"]
        impact = finding["impact"]
        key = f"{area}|{impact}"
        if key not in seen:
            seen[key] = f"Strengthen QA checks for {area.lower()}: {impact}"
    lessons.extend(seen.values())
    return lessons[:8]


def _llm_reflection_lessons(state: AgentState) -> list[str]:
    config = state["config"]
    api_key = config.api_key_for_provider(config.reflection_provider)
    if not is_llm_enabled(config.reflection_provider, api_key):
        return _derive_lessons_from_findings(state.get("findings", []))

    findings = state.get("findings", [])
    serialized_findings = "\n".join(
        f"- [{item['severity']}] {item['area']}: {item['evidence']} | Impact: {item['impact']} | Fix: {item['recommended_fix']}"
        for item in findings
    )
    system_prompt = """
You are Reflection-Agent for an e-learning QA factory.
Turn the latest QA findings into concise reusable system lessons.
Return strict JSON:
{"lessons":["lesson 1","lesson 2"]}

Rules:
- Write compact, reusable lessons.
- Avoid repeating near-duplicates.
- Maximum 8 lessons.
""".strip()
    user_prompt = f"Generate reusable QA lessons from these findings:\n{serialized_findings}"

    try:
        raw_response = invoke_text_model(
            provider=config.reflection_provider,
            model=config.reflection_model,
            api_key=api_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        payload = parse_json_object(raw_response)
        lessons = [str(item).strip() for item in payload.get("lessons", []) if str(item).strip()]
        return lessons[:8] or _derive_lessons_from_findings(findings)
    except Exception:
        return _derive_lessons_from_findings(findings)


def reflection_node(state: AgentState) -> AgentState:
    findings = state.get("findings", [])
    project_root = state["project_root"]

    if not findings and not state.get("sender"):
        bullet = state.get("user_text", "").strip() or "Review process feedback received."
        title = f"## Manual Feedback from {_timestamp()}"
        append_lesson_block(project_root, "human_feedback", title, [f"MANDATORY: {bullet}"])
        maybe_consolidate(project_root, "human_feedback")
        summary = "Stored manual feedback as a mandatory human QA lesson."
        log_communication(project_root, "Reflection Agent", "Knowledge", summary)
        return {
            "messages": [],
            "findings": [],
            "sender": "reflection",
            "next_agents": ["FINISH"],
            "routing_reason": state.get("routing_reason", ""),
            "reflection_summary": summary,
        }

    if len(findings) < MIN_FINDINGS_FOR_AUTO_REFLECTION:
        summary = "Skipped automatic reflection because fewer than 2 findings were produced."
        log_communication(project_root, "Reflection Agent", "Workflow", summary)
        return {
            "messages": [],
            "findings": [],
            "sender": "reflection",
            "next_agents": ["FINISH"],
            "routing_reason": state.get("routing_reason", ""),
            "reflection_summary": summary,
        }

    lessons = _llm_reflection_lessons(state)
    title = f"## Automatic Lessons from {_timestamp()}"
    append_lesson_block(project_root, "system", title, lessons)
    maybe_consolidate(project_root, "system")
    summary = f"Stored {len(lessons)} automatic lesson(s) from the latest QA run."
    log_communication(project_root, "Reflection Agent", "Knowledge", summary)
    return {
        "messages": [],
        "findings": [],
        "sender": "reflection",
        "next_agents": ["FINISH"],
        "routing_reason": state.get("routing_reason", ""),
        "reflection_summary": summary,
    }
