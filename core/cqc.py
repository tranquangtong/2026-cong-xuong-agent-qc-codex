from __future__ import annotations

import re
from pathlib import Path

from core.browser import BrowserProbeResult, run_playwright_probe
from core.content_sources import build_resolved_content_text
from core.state import AgentState, ContentSource
from core.utils import log_communication


URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


def _unique_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for item in paths:
        normalized = str(item).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def _probe_screenshot_paths(probe: BrowserProbeResult | None) -> list[str]:
    if not probe:
        return []

    paths: list[str] = []
    top_level = str(probe.get("screenshot_path", "")).strip()
    if top_level:
        paths.append(top_level)

    for state in probe.get("visited_states", []):
        screenshot_path = str(state.get("screenshot_path", "")).strip()
        if screenshot_path:
            paths.append(screenshot_path)
    return _unique_paths(paths)


def _probe_summary_source(probe: BrowserProbeResult) -> ContentSource:
    extracted_parts = [
        f"Browser probe status: {probe.get('status', 'unknown')}",
        f"Review URL: {probe.get('url', '')}",
    ]
    if probe.get("asset_url"):
        extracted_parts.append(f"Resolved asset URL: {probe['asset_url']}")
    if probe.get("lesson_url"):
        extracted_parts.append(f"Lesson URL reached: {probe['lesson_url']}")
    if probe.get("actions_attempted") is not None:
        extracted_parts.append(
            "Traversal coverage: "
            f"{probe.get('actions_attempted', 0)} action(s) attempted, "
            f"{probe.get('actions_changed_state', 0)} state-changing action(s)."
        )

    visited_states = probe.get("visited_states", [])
    if visited_states:
        extracted_parts.append(
            "Visited states:\n" + "\n".join(
                (
                    f"- {state.get('step', 'state')}: {state.get('title', '')} @ {state.get('page_url', '')}"
                    f" | action: {state.get('matched_label', '')}"
                ).strip()
                for state in visited_states
            )
        )

    if probe.get("warnings"):
        extracted_parts.append("Warnings:\n" + "\n".join(f"- {warning}" for warning in probe["warnings"]))

    return {
        "kind": "text",
        "uri": str(probe.get("url", "")),
        "display_name": "CQC Browser Collector Summary",
        "format": "browser",
        "extracted_text": "\n\n".join(part for part in extracted_parts if part.strip()),
        "image_paths": _probe_screenshot_paths(probe),
        "location_hints": ["course collector", "browser traversal", "shared CQC evidence"],
        "extraction_mode": "cqc-browser-collector",
        "warnings": list(probe.get("warnings", [])),
    }


def _probe_state_sources(probe: BrowserProbeResult) -> list[ContentSource]:
    sources: list[ContentSource] = []
    for index, state in enumerate(probe.get("visited_states", []), start=1):
        content_excerpt = str(state.get("content_excerpt", "")).strip()
        body_excerpt = str(state.get("body_excerpt", "")).strip()
        snapshot_excerpt = str(state.get("snapshot_excerpt", "")).strip()
        text_blocks = []

        if state.get("title"):
            text_blocks.append(f"Title: {state['title']}")
        if state.get("lesson_label"):
            text_blocks.append(f"Lesson label: {state['lesson_label']}")
        if state.get("progress_label"):
            text_blocks.append(f"Progress label: {state['progress_label']}")
        if state.get("matched_label"):
            text_blocks.append(f"Action that reached this state: {state['matched_label']}")
        if content_excerpt:
            text_blocks.append(f"Visible main content:\n{content_excerpt}")
        elif body_excerpt:
            text_blocks.append(f"Visible body content:\n{body_excerpt}")
        elif snapshot_excerpt:
            text_blocks.append(f"Snapshot excerpt:\n{snapshot_excerpt}")

        if not text_blocks and not state.get("screenshot_path"):
            continue

        hints = [str(state.get("step", "")).strip()]
        if state.get("lesson_label"):
            hints.append(str(state["lesson_label"]).strip())
        if state.get("matched_label"):
            hints.append(str(state["matched_label"]).strip())

        screenshot_path = str(state.get("screenshot_path", "")).strip()
        page_url = str(state.get("page_url", "")).strip() or str(probe.get("url", "")).strip()
        display_label = str(state.get("lesson_label", "")).strip() or str(state.get("title", "")).strip() or f"state-{index}"
        sources.append(
            {
                "kind": "text",
                "uri": f"{page_url}#state-{index}",
                "display_name": f"CQC State {index}: {display_label}",
                "format": "browser",
                "extracted_text": "\n\n".join(text_blocks).strip(),
                "image_paths": [screenshot_path] if screenshot_path else [],
                "location_hints": [hint for hint in hints if hint],
                "extraction_mode": "cqc-browser-state",
                "warnings": [],
            }
        )
    return sources


def prepare_cqc_state(state: AgentState) -> AgentState:
    urls = URL_PATTERN.findall(state.get("user_text", ""))
    output_dir = state.get("output_dir", "")
    if not urls or not output_dir:
        summary = "CQC collector skipped because no course URL or output directory was available."
        log_communication(state["project_root"], "CQC Collector", "Workflow", summary)
        return {
            "messages": [],
            "findings": [],
            "sender": "",
            "next_agents": state.get("next_agents", []),
            "routing_reason": state.get("routing_reason", ""),
            "collector_summary": summary,
        }

    probe = run_playwright_probe(urls[0], Path(output_dir), state.get("user_text", ""))
    content_sources = list(state.get("content_sources", []))
    content_sources.append(_probe_summary_source(probe))
    content_sources.extend(_probe_state_sources(probe))

    image_paths = _unique_paths([*state.get("image_paths", []), *_probe_screenshot_paths(probe)])
    resolved_content_text = build_resolved_content_text(content_sources, state.get("user_text", ""))

    summary = (
        "CQC collector gathered shared browser evidence: "
        f"status={probe.get('status', 'unknown')}, "
        f"visited_states={len(probe.get('visited_states', []))}, "
        f"shared_images={len(image_paths)}."
    )
    log_communication(state["project_root"], "CQC Collector", "Workflow", summary)

    return {
        "messages": [],
        "findings": [],
        "sender": "",
        "next_agents": state.get("next_agents", []),
        "routing_reason": state.get("routing_reason", ""),
        "content_sources": content_sources,
        "image_paths": image_paths,
        "resolved_content_text": resolved_content_text,
        "browser_probe": probe,
        "collector_summary": summary,
    }
