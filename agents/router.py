from __future__ import annotations

from core.content_sources import extract_figma_links, summarize_content_sources
from core.llm import invoke_text_model, is_llm_enabled, parse_json_object
from core.state import AgentState, RouteDecision
from core.utils import log_communication


def _fallback_route_request(state: AgentState) -> RouteDecision:
    user_text = state.get("user_text", "").lower()
    image_paths = state.get("image_paths", [])
    content_sources = state.get("content_sources", [])

    if state.get("next_agents"):
        return {
            "next": state["next_agents"],
            "reasoning": "Routing bypassed because explicit command or auto-detect already selected agent(s).",
        }

    next_agents: list[str] = []
    if image_paths:
        next_agents.append("graphic")

    figma_links = extract_figma_links(state.get("user_text", ""))
    if figma_links:
        next_agents.append("graphic")

    has_document_source = any(source.get("format") in {"pdf", "csv", "docx"} for source in content_sources)
    has_resolved_figma_source = any(
        source.get("format") == "figma" and (source.get("extracted_text") or source.get("image_paths"))
        for source in content_sources
    )
    if has_document_source or has_resolved_figma_source:
        next_agents.append("content")

    id_markers = (
        "articulate",
        "storyline",
        "rise",
        "scorm",
        "quiz",
        "knowledge check",
        "navigation",
        "marker",
        "tab",
        "accordion",
    )
    if any(marker in user_text for marker in id_markers):
        next_agents.append("id")

    content_markers = (
        "subtitle",
        ".srt",
        "grammar",
        "spelling",
        "copy",
        "content",
        "text",
        "storyboard",
    )
    if any(marker in user_text for marker in content_markers):
        next_agents.append("content")

    graphic_markers = ("design", "figma", "frame", "screen", "visual", "graphic")
    if any(marker in user_text for marker in graphic_markers):
        next_agents.append("graphic")

    video_markers = (".mp4", ".mov", ".mkv", ".webm", "/vqc", "video qc", "subtitle timing", "audio sync")
    if any(marker in user_text for marker in video_markers):
        next_agents.extend(["content", "graphic", "video"])

    if not next_agents:
        next_agents = ["id", "content"]

    deduped = list(dict.fromkeys(next_agents))
    return {
        "next": deduped,
        "reasoning": f"Mapped the request to {', '.join(deduped)} based on detected QA intent.",
    }


def route_request(state: AgentState) -> RouteDecision:
    if state.get("next_agents"):
        return {
            "next": state["next_agents"],
            "reasoning": "Routing bypassed because explicit command or auto-detect already selected agent(s).",
        }

    config = state["config"]
    api_key = config.api_key_for_provider(config.router_provider)
    if not is_llm_enabled(config.router_provider, api_key):
        return _fallback_route_request(state)

    system_prompt = """
You are Router-Agent for an e-learning QA factory.
Choose which specialist agent(s) should handle the request.
Available agents:
- "id": instructional design, browser flow, quiz logic, navigation, accessibility, grammar on screen
- "content": content QA for storyboard copy, subtitles, grammar/spelling, terminology, and attached document artifacts such as pdf/csv/docx
- "graphic": Figma-linked or screenshot-based graphic QA, layout, hierarchy, spacing, and WCAG visual accessibility
- "video": local video QC, subtitle/audio alignment, frame sample review support, and timing mismatch detection

Return strict JSON with this shape:
{"next":["id","content","graphic"],"reasoning":"short explanation"}

Rules:
- If the request mentions screenshots, image review, Figma, frames, or visual design, include "graphic".
- If the request mentions Articulate, Rise, Storyline, SCORM, interactions, quiz, navigation, include "id".
- If the request mentions storyboard, copy, subtitles, spelling, grammar, text content, or attached document files like pdf/csv/docx, include "content".
- If the request includes a Figma frame for storyboard or copy review, include both "content" and "graphic".
- If uncertain, route to both agents.
- Never include any key other than next and reasoning.
""".strip()
    source_summary = summarize_content_sources(state.get("content_sources", []))
    rendered_sources = "\n".join(f"- {line}" for line in source_summary) if source_summary else "- No resolved sources."
    user_prompt = f"""User request:
{state.get('user_text', '').strip()}

Resolved sources:
{rendered_sources}
"""

    try:
        raw_response = invoke_text_model(
            provider=config.router_provider,
            model=config.router_model,
            api_key=api_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        payload = parse_json_object(raw_response)
        next_agents = [agent for agent in payload.get("next", []) if agent in {"id", "content", "graphic", "video"}]
        if not next_agents:
            return _fallback_route_request(state)
        return {
            "next": list(dict.fromkeys(next_agents)),
            "reasoning": str(payload.get("reasoning", "Model selected specialist agents.")),
        }
    except Exception:
        return _fallback_route_request(state)


def router_node(state: AgentState) -> AgentState:
    decision = route_request(state)
    log_communication(state["project_root"], "Router", "Workflow", decision["reasoning"])
    return {
        "messages": [],
        "findings": [],
        "sender": "router",
        "next_agents": decision["next"],
        "routing_reason": decision["reasoning"],
    }
