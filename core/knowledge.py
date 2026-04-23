from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from core.state import AgentState, ContentSource, KnowledgeEntry, QAFinding
from core.utils import ensure_text_file


FILE_MAP = {
    "human_feedback": ("knowledge/general/human_feedback_lessons.md", "# Human QA Supervisor Lessons\n"),
    "system": (
        "knowledge/general/system_lessons.md",
        "# System Lessons Learned (Self-Improvement Log)\n\nThis file is automatically updated by the @Reflection-Agent to improve future QC accuracy.\n",
    ),
    "process_facts": (
        "knowledge/general/process_facts.md",
        "# Process Facts\n\nStable workflow and evidence facts learned across QA runs.\n",
    ),
    "procedure_candidates": (
        "knowledge/procedures/procedure_candidates.md",
        "# Procedure Candidates\n\nDraft procedural patterns that may later become repo-local skills or stronger standing rules.\n",
    ),
    "followups": (
        "knowledge/backlog/reflection_followups.md",
        "# Reflection Follow-ups\n\nDraft improvements that should be reviewed before changing prompts, collectors, reporting, or repo-local skills.\n",
    ),
}

ORDERED_CONTEXT_KEYS = ("human_feedback", "system", "process_facts", "procedure_candidates")
PROMOTION_THRESHOLD = 3
ENTRY_METADATA_FIELDS = (
    "id",
    "category",
    "tags",
    "source_agent",
    "first_seen_at",
    "last_seen_at",
    "seen_count",
    "confidence",
    "promoted",
    "promoted_by",
    "example_run_refs",
    "summary",
    "rationale",
    "recommended_action",
)
FIELD_LABELS = {
    "id": "id",
    "category": "category",
    "tags": "tags",
    "source_agent": "source_agent",
    "first_seen_at": "first_seen_at",
    "last_seen_at": "last_seen_at",
    "seen_count": "seen_count",
    "confidence": "confidence",
    "promoted": "promoted",
    "promoted_by": "promoted_by",
    "example_run_refs": "example_run_refs",
    "summary": "summary",
    "rationale": "rationale",
    "recommended_action": "recommended_action",
}
ARTICULATE_MARKERS = ("articulate", "rise", "storyline", "review 360", "#/lessons/")
FIGMA_MARKERS = ("figma.com", "frame", "node-id")
DOCUMENT_FORMATS = {"pdf", "csv", "docx"}
TAG_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
SNAPSHOT_PATTERN = re.compile(r"\bpage-\d{4}-\d{2}-\d{2}t\d{2}", re.IGNORECASE)
SCREENSHOT_PATTERN = re.compile(r"\.(?:png|jpg|jpeg|yml)\b", re.IGNORECASE)


@dataclass(slots=True)
class KnowledgeContextRequest:
    mode: str = ""
    flow_type: str = ""
    user_text: str = ""
    image_paths: list[str] | None = None
    content_sources: list[ContentSource] | None = None
    findings: list[QAFinding] | None = None
    browser_probe: object | None = None


def _path(project_root: Path, key: str) -> Path:
    return project_root / FILE_MAP[key][0]


def _ensure_file(project_root: Path, key: str) -> Path:
    path = _path(project_root, key)
    ensure_text_file(path, FILE_MAP[key][1])
    return path


def _split_sections(content: str) -> tuple[str, list[str]]:
    lines = content.splitlines()
    header_lines: list[str] = []
    sections: list[list[str]] = []
    current_section: list[str] | None = None
    seen_section = False

    for line in lines:
        if line.startswith("## "):
            seen_section = True
            if current_section:
                sections.append(current_section)
            current_section = [line]
            continue
        if not seen_section:
            header_lines.append(line)
            continue
        if current_section is None:
            current_section = [line]
        else:
            current_section.append(line)

    if current_section:
        sections.append(current_section)
    header = "\n".join(header_lines).rstrip()
    section_strings = ["\n".join(section).strip() for section in sections if any(item.strip() for item in section)]
    return header, section_strings


def _extract_bullets(section: str) -> list[str]:
    bullets = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            bullets.append(stripped[2:].strip())
    return bullets


def _normalize_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _normalize_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def _normalize_entry(entry: KnowledgeEntry, *, storage_key: str = "") -> KnowledgeEntry:
    normalized = dict(entry)
    normalized.setdefault("id", "")
    normalized.setdefault("title", "## Knowledge Entry")
    normalized.setdefault("category", "")
    normalized.setdefault("tags", [])
    normalized.setdefault("source_agent", "reflection")
    normalized.setdefault("first_seen_at", "")
    normalized.setdefault("last_seen_at", "")
    normalized.setdefault("seen_count", 1)
    normalized.setdefault("confidence", "medium")
    normalized.setdefault("promoted", False)
    normalized.setdefault("promoted_by", "")
    normalized.setdefault("example_run_refs", [])
    normalized.setdefault("summary", "")
    normalized.setdefault("rationale", "")
    normalized.setdefault("recommended_action", "")
    normalized.setdefault("storage_key", storage_key or normalized.get("storage_key", ""))
    normalized.setdefault("legacy", False)
    normalized["tags"] = _normalize_list(normalized.get("tags", []))
    normalized["example_run_refs"] = _normalize_list(normalized.get("example_run_refs", []))
    normalized["seen_count"] = max(int(normalized.get("seen_count", 1) or 1), 1)
    normalized["promoted"] = bool(normalized.get("promoted", False))
    return normalized


def _entry_fingerprint(entry: KnowledgeEntry) -> str:
    text = f"{entry.get('category', '')}|{entry.get('summary', '')}".lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _legacy_category_for_key(key: str) -> str:
    mapping = {
        "human_feedback": "human_feedback",
        "system": "system_lesson",
        "process_facts": "process_fact",
        "procedure_candidates": "procedure_candidate",
        "followups": "follow_up_item",
    }
    return mapping.get(key, "system_lesson")


def _section_to_entry(section: str, *, storage_key: str, index: int) -> list[KnowledgeEntry]:
    lines = [line.rstrip() for line in section.splitlines() if line.strip()]
    if not lines:
        return []

    title = lines[0] if lines[0].startswith("## ") else f"## Legacy Entry {index}"
    metadata: dict[str, object] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        body = stripped[2:].strip()
        if ":" not in body:
            continue
        key, value = body.split(":", 1)
        normalized_key = key.strip()
        if normalized_key not in FIELD_LABELS.values():
            continue
        metadata[normalized_key] = value.strip()

    if metadata.get("id") and metadata.get("summary"):
        entry: KnowledgeEntry = {
            "id": str(metadata.get("id", "")),
            "title": title,
            "category": str(metadata.get("category", _legacy_category_for_key(storage_key))),
            "tags": _normalize_list(metadata.get("tags", "")),
            "source_agent": str(metadata.get("source_agent", "reflection")),
            "first_seen_at": str(metadata.get("first_seen_at", "")),
            "last_seen_at": str(metadata.get("last_seen_at", "")),
            "seen_count": int(str(metadata.get("seen_count", "1") or "1")),
            "confidence": str(metadata.get("confidence", "medium")),
            "promoted": _normalize_bool(metadata.get("promoted", False)),
            "promoted_by": str(metadata.get("promoted_by", "")),
            "example_run_refs": _normalize_list(metadata.get("example_run_refs", "")),
            "summary": str(metadata.get("summary", "")),
            "rationale": str(metadata.get("rationale", "")),
            "recommended_action": str(metadata.get("recommended_action", "")),
            "storage_key": storage_key,
            "legacy": False,
        }
        return [_normalize_entry(entry, storage_key=storage_key)]

    entries: list[KnowledgeEntry] = []
    for bullet_index, bullet in enumerate(_extract_bullets(section), start=1):
        entries.append(
            _normalize_entry(
                {
                    "id": f"legacy-{storage_key}-{index:03d}-{bullet_index:02d}",
                    "title": title,
                    "category": _legacy_category_for_key(storage_key),
                    "tags": [],
                    "source_agent": "reflection",
                    "summary": bullet,
                    "rationale": "",
                    "recommended_action": "",
                    "promoted": storage_key in {"human_feedback", "system"},
                    "promoted_by": "legacy",
                    "storage_key": storage_key,
                    "legacy": True,
                },
                storage_key=storage_key,
            )
        )
    return entries


def load_knowledge_entries(project_root: Path, key: str) -> list[KnowledgeEntry]:
    path = _ensure_file(project_root, key)
    _, sections = _split_sections(path.read_text(encoding="utf-8"))
    entries: list[KnowledgeEntry] = []
    for index, section in enumerate(sections, start=1):
        entries.extend(_section_to_entry(section, storage_key=key, index=index))
    return entries


def _write_entries(project_root: Path, key: str, entries: list[KnowledgeEntry]) -> None:
    path = _ensure_file(project_root, key)
    header = FILE_MAP[key][1].strip()
    parts = [header] if header else []

    for entry in entries:
        normalized = _normalize_entry(entry, storage_key=key)
        parts.append(normalized["title"])
        for field in ENTRY_METADATA_FIELDS:
            value = normalized.get(field)
            if field in {"tags", "example_run_refs"}:
                rendered = ", ".join(_normalize_list(value))
            elif field == "promoted":
                rendered = "true" if bool(value) else "false"
            else:
                rendered = str(value or "").strip()
            parts.append(f"- {FIELD_LABELS[field]}: {rendered}")

    path.write_text("\n\n".join(part.strip() for part in parts if part.strip()) + "\n", encoding="utf-8")


def _merge_entry(existing: KnowledgeEntry, incoming: KnowledgeEntry) -> KnowledgeEntry:
    merged = _normalize_entry(existing, storage_key=incoming.get("storage_key", existing.get("storage_key", "")))
    incoming = _normalize_entry(incoming, storage_key=merged.get("storage_key", ""))
    merged["last_seen_at"] = incoming.get("last_seen_at", "") or merged.get("last_seen_at", "")
    merged["first_seen_at"] = merged.get("first_seen_at", "") or incoming.get("first_seen_at", "")
    merged["seen_count"] = max(int(merged.get("seen_count", 1)), 1) + 1
    merged["confidence"] = incoming.get("confidence", "") or merged.get("confidence", "")
    merged["source_agent"] = incoming.get("source_agent", "") or merged.get("source_agent", "")
    merged["summary"] = incoming.get("summary", "") or merged.get("summary", "")
    merged["rationale"] = incoming.get("rationale", "") or merged.get("rationale", "")
    merged["recommended_action"] = incoming.get("recommended_action", "") or merged.get("recommended_action", "")
    merged["tags"] = sorted(set(_normalize_list(merged.get("tags", [])) + _normalize_list(incoming.get("tags", []))))
    example_run_refs = _normalize_list(merged.get("example_run_refs", []))
    for item in _normalize_list(incoming.get("example_run_refs", [])):
        if item not in example_run_refs:
            example_run_refs.append(item)
    merged["example_run_refs"] = example_run_refs[:6]
    if incoming.get("promoted"):
        merged["promoted"] = True
        merged["promoted_by"] = incoming.get("promoted_by", "") or merged.get("promoted_by", "")
    return merged


def append_or_update_entry(project_root: Path, key: str, entry: KnowledgeEntry) -> KnowledgeEntry:
    entries = load_knowledge_entries(project_root, key)
    normalized = _normalize_entry(entry, storage_key=key)
    fingerprint = _entry_fingerprint(normalized)
    for index, current in enumerate(entries):
        if current.get("id") == normalized.get("id") or _entry_fingerprint(current) == fingerprint:
            entries[index] = _merge_entry(current, normalized)
            _write_entries(project_root, key, entries)
            return entries[index]
    entries.append(normalized)
    _write_entries(project_root, key, entries)
    return normalized


def mark_promoted(project_root: Path, key: str, entry_id: str, promoted_by: str) -> KnowledgeEntry | None:
    entries = load_knowledge_entries(project_root, key)
    for entry in entries:
        if entry.get("id") != entry_id:
            continue
        entry["promoted"] = True
        entry["promoted_by"] = promoted_by
        _write_entries(project_root, key, entries)
        return entry
    return None


def append_lesson_block(project_root: Path, key: str, title: str, bullets: list[str]) -> None:
    clean_bullets = [bullet.strip() for bullet in bullets if bullet.strip()]
    for index, bullet in enumerate(clean_bullets, start=1):
        append_or_update_entry(
            project_root,
            key,
            {
                "id": f"{key}-{index:03d}-{abs(hash((title, bullet))) % 100000:05d}",
                "title": title,
                "category": _legacy_category_for_key(key),
                "summary": bullet,
                "rationale": "",
                "recommended_action": "",
                "source_agent": "reflection",
                "promoted": key in {"human_feedback", "system"},
                "promoted_by": "legacy",
                "storage_key": key,
            },
        )


def maybe_consolidate(project_root: Path, key: str) -> bool:
    path = _ensure_file(project_root, key)
    content = path.read_text(encoding="utf-8")
    header, sections = _split_sections(content)
    if len(sections) <= 10:
        return False

    has_metadata = any("- id:" in section and "- summary:" in section for section in sections)
    if has_metadata:
        return False

    older_sections = sections[:-3]
    recent_sections = sections[-3:]
    summary_bullets: list[str] = []
    seen = set()
    for section in older_sections:
        for bullet in _extract_bullets(section):
            normalized = bullet.lower()
            if normalized not in seen:
                seen.add(normalized)
                summary_bullets.append(bullet)
            if len(summary_bullets) >= 8:
                break
        if len(summary_bullets) >= 8:
            break

    summary_title = "## Consolidated Historical Lessons"
    summary_body = [f"- {bullet}" for bullet in summary_bullets] or ["- Preserve recurring QA lessons from older runs."]

    rebuilt_parts = [header.strip()] if header.strip() else []
    rebuilt_parts.append(summary_title)
    rebuilt_parts.extend(summary_body)
    rebuilt_parts.extend(recent_sections)

    path.write_text("\n\n".join(part.strip() for part in rebuilt_parts if part.strip()) + "\n", encoding="utf-8")
    return True


def _source_types_from_request(request: KnowledgeContextRequest) -> set[str]:
    source_types: set[str] = set()
    user_text = request.user_text.lower()
    if request.flow_type == "cqc" or any(marker in user_text for marker in ARTICULATE_MARKERS) or request.browser_probe:
        source_types.add("articulate")
    if any(marker in user_text for marker in FIGMA_MARKERS):
        source_types.add("figma")
    if request.image_paths:
        source_types.add("screenshot")
    for source in request.content_sources or []:
        fmt = str(source.get("format", "")).lower()
        if fmt in DOCUMENT_FORMATS:
            source_types.add("document")
        if fmt == "figma":
            source_types.add("figma")
        if fmt == "browser":
            source_types.add("articulate")
    return source_types


def _tags_from_text(text: str) -> set[str]:
    lowered = text.lower()
    tag_map = {
        "knowledge-check": ("knowledge check", "quiz", "assessment"),
        "coverage": ("coverage", "traverse", "exercise", "complete all", "scope"),
        "british-english": ("british english", "behaviour", "colour", "organisation", "learner-facing spelling"),
        "contrast": ("contrast", "wcag", "readability"),
        "unresolved-text": ("unresolved", "text not resolved", "pre-resolved", "resolved text"),
        "navigation": ("navigation", "continue", "next", "previous"),
        "artifacts": ("artifact", "screenshot", "evidence bundle"),
        "grammar": ("grammar", "spelling", "terminology"),
        "interaction": ("accordion", "tab", "click to reveal", "marker", "interactive"),
    }
    tags = set()
    for tag, markers in tag_map.items():
        if any(marker in lowered for marker in markers):
            tags.add(tag)
    for token in TAG_PATTERN.findall(lowered):
        if token in {"id", "content", "graphic", "cqc", "figma", "articulate", "document", "screenshot"}:
            tags.add(token)
    return tags


def _request_from_state(state: AgentState | None, mode: str = "") -> KnowledgeContextRequest:
    if not state:
        return KnowledgeContextRequest(mode=mode)
    return KnowledgeContextRequest(
        mode=mode,
        flow_type=str(state.get("flow_type", "")),
        user_text=str(state.get("user_text", "")),
        image_paths=list(state.get("image_paths", [])),
        content_sources=list(state.get("content_sources", [])),
        findings=list(state.get("findings", [])),
        browser_probe=state.get("browser_probe"),
    )


def _candidate_tags_for_request(request: KnowledgeContextRequest) -> set[str]:
    tags = _tags_from_text(request.user_text)
    for source_type in _source_types_from_request(request):
        tags.add(source_type)
    if request.mode:
        tags.add(request.mode)
    if request.flow_type:
        tags.add(request.flow_type)
    for finding in request.findings or []:
        tags.update(_tags_from_text(" ".join(str(finding.get(key, "")) for key in ("area", "evidence", "impact", "recommended_fix"))))
        source_agent = str(finding.get("source_agent", "")).strip()
        if source_agent:
            tags.add(source_agent)
    return tags


def _entry_matches_request(entry: KnowledgeEntry, request: KnowledgeContextRequest) -> bool:
    entry_tags = set(_normalize_list(entry.get("tags", [])))
    if not entry_tags:
        return True
    request_tags = _candidate_tags_for_request(request)
    if request.mode and request.mode in entry_tags:
        return True
    if request.flow_type and request.flow_type in entry_tags:
        return True
    if entry_tags & request_tags:
        return True
    return False


def _render_entries_section(header: str, entries: list[KnowledgeEntry]) -> str:
    if not entries:
        return ""
    lines = [header]
    for entry in entries:
        summary = str(entry.get("summary", "")).strip()
        if not summary:
            continue
        prefix = "MANDATORY: " if entry.get("category") == "human_feedback" and not summary.startswith("MANDATORY:") else ""
        lines.append(f"- {prefix}{summary}")
    return "\n".join(lines).strip()


def get_knowledge_context(project_root: Path, mode: str = "", state: AgentState | None = None) -> str:
    request = _request_from_state(state, mode=mode)
    sections: list[str] = []

    human_entries = load_knowledge_entries(project_root, "human_feedback")
    sections.append(_render_entries_section("# Human QA Supervisor Lessons", human_entries))

    system_entries = [
        entry for entry in load_knowledge_entries(project_root, "system")
        if entry.get("promoted") or entry.get("category") == "system_lesson"
    ]
    sections.append(_render_entries_section("# System Lessons Learned (Self-Improvement Log)", system_entries))

    process_entries = [
        entry for entry in load_knowledge_entries(project_root, "process_facts")
        if _entry_matches_request(entry, request)
    ]
    sections.append(_render_entries_section("# Process Facts", process_entries))

    procedure_entries = [
        entry for entry in load_knowledge_entries(project_root, "procedure_candidates")
        if _entry_matches_request(entry, request)
    ]
    sections.append(_render_entries_section("# Procedure Candidates", procedure_entries))

    for relative in ("knowledge/general/wcag_global.md", "knowledge/requirements/project_x_req.md"):
        path = project_root / relative
        if path.exists():
            sections.append(path.read_text(encoding="utf-8").strip())
    return "\n\n".join(section for section in sections if section.strip())
