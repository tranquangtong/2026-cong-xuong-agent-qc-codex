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
    kind: Literal["document", "figma", "text"]
    uri: str
    display_name: str
    format: str
    extracted_text: str
    image_paths: list[str]
    location_hints: list[str]
    extraction_mode: str
    warnings: list[str]


class RouteDecision(TypedDict):
    next: List[Literal["content", "id", "graphic", "reflection", "FINISH"]]
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
    collector_summary: str
