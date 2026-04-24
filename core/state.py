from __future__ import annotations

import operator
from typing import Annotated, Any, List, Literal, Sequence, TypedDict


Severity = Literal["Critical", "Major", "Minor", "Suggestion", "Info"]


class BaseMessage(TypedDict, total=False):
    role: str
    content: str


class QAFinding(TypedDict):
    id: str
    severity: Severity
    area: str
    evidence: str
    impact: str
    recommended_fix: str
    source_agent: str


class ContentSource(TypedDict, total=False):
    kind: Literal["document", "figma", "text", "video", "subtitle", "audio"]
    uri: str
    display_name: str
    format: str
    extracted_text: str
    image_paths: list[str]
    location_hints: list[str]
    extraction_mode: str
    warnings: list[str]
    metadata: dict[str, Any]


class KnowledgeEntry(TypedDict, total=False):
    id: str
    title: str
    category: str
    tags: list[str]
    source_agent: str
    first_seen_at: str
    last_seen_at: str
    seen_count: int
    confidence: str
    promoted: bool
    promoted_by: str
    example_run_refs: list[str]
    summary: str
    rationale: str
    recommended_action: str
    storage_key: str
    legacy: bool


class FollowupItem(TypedDict, total=False):
    id: str
    summary: str
    rationale: str
    recommended_action: str
    tags: list[str]
    source_agent: str


class ReflectionRecord(TypedDict, total=False):
    storage_key: str
    entry: KnowledgeEntry
    discarded: bool
    reason: str


class RouteDecision(TypedDict):
    next: List[Literal["content", "id", "graphic", "video", "reflection", "FINISH"]]
    reasoning: str


def merge_findings(current: list[QAFinding], incoming: list[QAFinding]) -> list[QAFinding]:
    merged = list(current)
    existing_ids = {finding["id"] for finding in current}
    for finding in incoming:
        finding_id = finding["id"]
        if finding_id in existing_ids:
            prefix = finding_id.rsplit("-", 1)[0]
            sequence = sum(1 for item in merged if item["id"].startswith(prefix + "-")) + 1
            adjusted = dict(finding)
            adjusted["id"] = f"{prefix}-{sequence:03d}"
            merged.append(adjusted)
            existing_ids.add(adjusted["id"])
            continue
        merged.append(finding)
        existing_ids.add(finding_id)
    return merged


def pick_last(current: Any, incoming: Any) -> Any:
    return incoming if incoming not in (None, "", []) else current


def combine_agents(current: list[str], incoming: list[str]) -> list[str]:
    return list(dict.fromkeys([*(current or []), *(incoming or [])]))


class AgentState(TypedDict, total=False):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    findings: Annotated[List[QAFinding], merge_findings]
    sender: Annotated[str, pick_last]
    next_agents: Annotated[List[str], combine_agents]
    routing_reason: Annotated[str, pick_last]
    flow_type: str
    user_text: str
    raw_text: str
    image_paths: list[str]
    project_root: Any
    config: Any
    output_dir: str
    report_path: str
    reflection_summary: str
    content_sources: list[ContentSource]
    resolved_content_text: str
    browser_probe: Any
    video_probe: dict[str, Any]
    collector_summary: str
    requested_scope: dict[str, Any]
    coverage_map: dict[str, Any]
