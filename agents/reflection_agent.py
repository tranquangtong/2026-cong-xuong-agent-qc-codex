from __future__ import annotations

from datetime import datetime
import re

from core.knowledge import (
    PROMOTION_THRESHOLD,
    append_or_update_entry,
    mark_promoted,
)
from core.state import AgentState, KnowledgeEntry, QAFinding, ReflectionRecord
from core.utils import log_communication


MIN_FINDINGS_FOR_AUTO_REFLECTION = 2
ARTIFACT_PATTERN = re.compile(r"https?://\S+|page-\d{4}-\d{2}-\d{2}t\d{2}|(?:\.png|\.jpg|\.jpeg|\.yml)\b", re.IGNORECASE)
TAG_KEYWORDS = {
    "knowledge-check": ("knowledge check", "quiz", "assessment"),
    "coverage": ("coverage", "traverse", "exercise", "scope", "all visible"),
    "british-english": ("british english", "behaviour", "colour", "organisation"),
    "contrast": ("contrast", "wcag", "readability"),
    "unresolved-text": ("unresolved text", "pre-resolved", "resolved text"),
    "navigation": ("navigation", "continue", "next", "previous"),
    "collector": ("collector", "browser probe", "asset url", "review shell"),
    "artifacts": ("artifact", "screenshot", "evidence bundle"),
    "grammar": ("grammar", "spelling", "terminology"),
    "interaction": ("accordion", "tab", "marker", "click to reveal", "interactive"),
    "figma": ("figma",),
    "articulate": ("articulate", "rise", "storyline", "review 360", "#/lessons/"),
}


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized[:48] or "entry"


def _extract_tags(*texts: str, source_agent: str = "", flow_type: str = "") -> list[str]:
    lowered = " ".join(texts).lower()
    tags = set()
    for tag, markers in TAG_KEYWORDS.items():
        if any(marker in lowered for marker in markers):
            tags.add(tag)
    if source_agent:
        tags.add(source_agent)
    if flow_type:
        tags.add(flow_type)
    return sorted(tags)


def _entry_id(prefix: str, category: str, summary: str) -> str:
    return f"{prefix}-{category}-{_slug(summary)}"


def _finding_text(finding: QAFinding) -> str:
    return " ".join(
        str(finding.get(key, "")).strip()
        for key in ("area", "evidence", "impact", "recommended_fix", "source_agent")
    )


def _is_asset_specific(finding: QAFinding) -> bool:
    evidence = str(finding.get("evidence", ""))
    return bool(ARTIFACT_PATTERN.search(evidence))


def _is_followup_deficiency(finding: QAFinding) -> bool:
    text = _finding_text(finding).lower()
    return any(
        marker in text
        for marker in (
            "collector",
            "prompt",
            "routing",
            "report pipeline",
            "skill file",
            "logic agent",
            "logic gap",
            "tool dependency",
            "ocr",
            "parser",
            "browser probe",
        )
    )


def _is_process_fact(finding: QAFinding) -> bool:
    text = _finding_text(finding).lower()
    area = str(finding.get("area", "")).lower()
    return (
        any(marker in text for marker in ("artifact", "screenshot", "dependency", "provider", "unresolved text"))
        or "content source" in area
        or "coverage note" in area
    )


def _is_procedure_candidate(finding: QAFinding) -> bool:
    text = _finding_text(finding).lower()
    return any(
        marker in text
        for marker in (
            "click every",
            "exercise every",
            "traverse",
            "complete all",
            "reveal",
            "continue until",
            "scroll through",
            "coverage self-check",
        )
    )


def _should_discard_finding(finding: QAFinding) -> bool:
    if str(finding.get("severity", "")).lower() not in {"info", "suggestion"}:
        return False
    if _is_followup_deficiency(finding) or _is_process_fact(finding) or _is_procedure_candidate(finding):
        return False
    return _is_asset_specific(finding)


def _confidence_for_finding(finding: QAFinding, *, manual: bool = False) -> str:
    if manual:
        return "high"
    severity = str(finding.get("severity", "")).lower()
    if severity in {"critical", "major"}:
        return "high"
    if severity == "minor":
        return "medium"
    return "low"


def _build_entry(
    *,
    storage_key: str,
    category: str,
    summary: str,
    source_agent: str,
    rationale: str,
    recommended_action: str,
    tags: list[str],
    confidence: str,
    timestamp: str,
    run_ref: str,
    promoted: bool = False,
    promoted_by: str = "",
) -> KnowledgeEntry:
    return {
        "id": _entry_id(storage_key, category, summary),
        "title": f"## {summary[:80]}",
        "category": category,
        "tags": tags,
        "source_agent": source_agent,
        "first_seen_at": timestamp,
        "last_seen_at": timestamp,
        "seen_count": 1,
        "confidence": confidence,
        "promoted": promoted,
        "promoted_by": promoted_by,
        "example_run_refs": [run_ref] if run_ref else [],
        "summary": summary,
        "rationale": rationale,
        "recommended_action": recommended_action,
        "storage_key": storage_key,
    }


def _manual_feedback_entry(state: AgentState) -> KnowledgeEntry:
    timestamp = _timestamp()
    bullet = state.get("user_text", "").strip() or "Review process feedback received."
    flow_type = str(state.get("flow_type", ""))
    tags = _extract_tags(bullet, source_agent="human", flow_type=flow_type)
    summary = bullet if bullet.startswith("MANDATORY:") else f"MANDATORY: {bullet}"
    return _build_entry(
        storage_key="human_feedback",
        category="human_feedback",
        summary=summary,
        source_agent="human",
        rationale="Direct reviewer correction should become immediately available in future specialist prompts.",
        recommended_action="Inject this rule into future relevant QA runs as a standing mandatory instruction.",
        tags=tags,
        confidence="high",
        timestamp=timestamp,
        run_ref=str(state.get("raw_text", "")).strip(),
        promoted=True,
        promoted_by="manual_feedback",
    )


def _record_from_finding(state: AgentState, finding: QAFinding) -> ReflectionRecord:
    flow_type = str(state.get("flow_type", ""))
    source_agent = str(finding.get("source_agent", "reflection")).strip() or "reflection"
    text = _finding_text(finding)
    tags = _extract_tags(text, source_agent=source_agent, flow_type=flow_type)
    timestamp = _timestamp()
    run_ref = str(state.get("raw_text", state.get("user_text", ""))).strip()
    rationale = str(finding.get("impact", "")).strip() or "This pattern can improve future QA judgment."
    recommended_action = str(finding.get("recommended_fix", "")).strip() or "Review and refine the QA workflow."
    area = str(finding.get("area", "QA pattern")).strip()

    if _should_discard_finding(finding):
        return {"storage_key": "", "discarded": True, "reason": "asset-specific noise"}

    if _is_followup_deficiency(finding):
        summary = f"Follow-up candidate for {area.lower()}: {recommended_action}"
        entry = _build_entry(
            storage_key="followups",
            category="follow_up_item",
            summary=summary,
            source_agent=source_agent,
            rationale=rationale,
            recommended_action=recommended_action,
            tags=tags,
            confidence=_confidence_for_finding(finding),
            timestamp=timestamp,
            run_ref=run_ref,
        )
        return {"storage_key": "followups", "entry": entry, "discarded": False}

    if _is_process_fact(finding):
        summary = f"Stable process fact for {area.lower()}: {recommended_action}"
        entry = _build_entry(
            storage_key="process_facts",
            category="process_fact",
            summary=summary,
            source_agent=source_agent,
            rationale=rationale,
            recommended_action=recommended_action,
            tags=tags,
            confidence=_confidence_for_finding(finding),
            timestamp=timestamp,
            run_ref=run_ref,
        )
        return {"storage_key": "process_facts", "entry": entry, "discarded": False}

    if _is_procedure_candidate(finding):
        summary = f"Procedure candidate for {area.lower()}: {recommended_action}"
        entry = _build_entry(
            storage_key="procedure_candidates",
            category="procedure_candidate",
            summary=summary,
            source_agent=source_agent,
            rationale=rationale,
            recommended_action=recommended_action,
            tags=tags,
            confidence=_confidence_for_finding(finding),
            timestamp=timestamp,
            run_ref=run_ref,
        )
        return {"storage_key": "procedure_candidates", "entry": entry, "discarded": False}

    summary = f"Strengthen QA checks for {area.lower()}: {rationale}"
    entry = _build_entry(
        storage_key="system",
        category="system_lesson",
        summary=summary,
        source_agent=source_agent,
        rationale=rationale,
        recommended_action=recommended_action,
        tags=tags,
        confidence=_confidence_for_finding(finding),
        timestamp=timestamp,
        run_ref=run_ref,
    )
    return {"storage_key": "system", "entry": entry, "discarded": False}


def _should_promote_entry(storage_key: str, entry: KnowledgeEntry, *, manual: bool = False) -> bool:
    if storage_key == "human_feedback":
        return True
    if storage_key != "system":
        return False
    return manual or int(entry.get("seen_count", 1)) >= PROMOTION_THRESHOLD


def reflection_node(state: AgentState) -> AgentState:
    findings = state.get("findings", [])
    project_root = state["project_root"]

    if not findings and not state.get("sender"):
        entry = _manual_feedback_entry(state)
        stored = append_or_update_entry(project_root, "human_feedback", entry)
        summary = "Stored manual feedback as a promoted human QA lesson."
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

    stored_counts = {
        "system": 0,
        "process_facts": 0,
        "procedure_candidates": 0,
        "followups": 0,
        "discarded": 0,
        "promoted": 0,
    }
    for finding in findings:
        record = _record_from_finding(state, finding)
        if record.get("discarded"):
            stored_counts["discarded"] += 1
            continue
        storage_key = str(record.get("storage_key", "")).strip()
        entry = record.get("entry")
        if not storage_key or not entry:
            stored_counts["discarded"] += 1
            continue
        stored = append_or_update_entry(project_root, storage_key, entry)
        promoted_before = bool(stored.get("promoted", False))
        if _should_promote_entry(storage_key, stored) and not promoted_before:
            mark_promoted(project_root, storage_key, str(stored.get("id", "")), "auto_threshold")
            stored_counts["promoted"] += 1
        stored_counts[storage_key] += 1

    summary = (
        "Stored reflection outputs from the latest QA run: "
        f"system={stored_counts['system']}, "
        f"process_facts={stored_counts['process_facts']}, "
        f"procedures={stored_counts['procedure_candidates']}, "
        f"followups={stored_counts['followups']}, "
        f"discarded={stored_counts['discarded']}, "
        f"promoted={stored_counts['promoted']}."
    )
    log_communication(project_root, "Reflection Agent", "Knowledge", summary)
    return {
        "messages": [],
        "findings": [],
        "sender": "reflection",
        "next_agents": ["FINISH"],
        "routing_reason": state.get("routing_reason", ""),
        "reflection_summary": summary,
    }
