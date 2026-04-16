from __future__ import annotations

from pathlib import Path

from agents.content_agent import content_node
from agents.graphic_agent import graphic_node
from agents.id_agent import id_node
from agents.reflection_agent import reflection_node
from agents.router import router_node
from core.content_sources import build_resolved_content_text, resolve_content_sources
from core.reporting import generate_markdown_report
from core.state import AgentState, ContentSource, combine_agents, merge_findings, pick_last

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover
    END = "END"
    START = "START"
    StateGraph = None


def start_routing(state: AgentState) -> str:
    next_agents = state.get("next_agents", [])
    if "reflection" in next_agents:
        return "reflection"
    if next_agents:
        return "specialist"
    return "router"


def _merge_states(base: AgentState, updates: list[AgentState]) -> AgentState:
    merged = dict(base)
    current_findings = list(base.get("findings", []))
    current_agents = list(base.get("next_agents", []))
    current_sender = base.get("sender", "")
    current_reason = base.get("routing_reason", "")

    for update in updates:
        current_findings = merge_findings(current_findings, update.get("findings", []))
        current_agents = combine_agents(current_agents, update.get("next_agents", []))
        current_sender = pick_last(current_sender, update.get("sender", ""))
        current_reason = pick_last(current_reason, update.get("routing_reason", ""))

    merged["findings"] = current_findings
    merged["next_agents"] = current_agents
    merged["sender"] = current_sender
    merged["routing_reason"] = current_reason
    for update in updates:
        for key, value in update.items():
            if key not in {"findings", "next_agents", "sender", "routing_reason", "messages"} and value not in (None, ""):
                merged[key] = value
    return merged


def maybe_build_langgraph() -> StateGraph | None:
    if StateGraph is None:
        return None

    graph = StateGraph(AgentState)
    graph.add_node("router", router_node)
    graph.add_node("id", id_node)
    graph.add_node("content", content_node)
    graph.add_node("graphic", graphic_node)
    graph.add_node("reflection", reflection_node)
    graph.add_conditional_edges(START, start_routing, {"router": "router", "specialist": "id", "reflection": "reflection"})
    graph.add_edge("router", "id")
    graph.add_edge("id", "reflection")
    graph.add_edge("content", "reflection")
    graph.add_edge("graphic", "reflection")
    graph.add_edge("reflection", END)
    return graph


def invoke_workflow(
    user_text: str,
    raw_text: str,
    image_paths: list[str],
    next_agents: list[str],
    project_root: Path,
    config,
    content_sources: list[ContentSource] | None = None,
) -> AgentState:
    resolved_sources = resolve_content_sources(project_root, user_text, content_sources)
    state: AgentState = {
        "messages": [{"role": "user", "content": raw_text}],
        "findings": [],
        "sender": "",
        "next_agents": list(next_agents),
        "routing_reason": "",
        "user_text": user_text,
        "raw_text": raw_text,
        "image_paths": image_paths,
        "project_root": project_root,
        "config": config,
        "content_sources": resolved_sources,
        "resolved_content_text": build_resolved_content_text(resolved_sources, user_text),
    }

    route = start_routing(state)
    if route == "router":
        router_update = router_node(state)
        state = _merge_states(state, [router_update])
    elif route == "reflection":
        reflection_update = reflection_node(state)
        state = _merge_states(state, [reflection_update])
        report_path = generate_markdown_report(
            project_root,
            state["findings"],
            state.get("routing_reason", ""),
            state.get("raw_text", state.get("user_text", "")),
            state.get("config"),
            state.get("content_sources", []),
        )
        state["report_path"] = str(report_path)
        return state

    specialist_updates = []
    for agent_name in state.get("next_agents", []):
        if agent_name == "id":
            specialist_updates.append(id_node(state))
        elif agent_name == "content":
            specialist_updates.append(content_node(state))
        elif agent_name == "graphic":
            specialist_updates.append(graphic_node(state))

    if specialist_updates:
        state = _merge_states(state, specialist_updates)

    reflection_update = reflection_node(state)
    state = _merge_states(state, [reflection_update])
    report_path = generate_markdown_report(
        project_root,
        state["findings"],
        state.get("routing_reason", ""),
        state.get("raw_text", state.get("user_text", "")),
        state.get("config"),
        state.get("content_sources", []),
    )
    state["report_path"] = str(report_path)
    return state
