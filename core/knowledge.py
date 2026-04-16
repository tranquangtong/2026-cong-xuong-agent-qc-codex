from __future__ import annotations

from pathlib import Path

from core.utils import ensure_text_file


FILE_MAP = {
    "human_feedback": ("knowledge/general/human_feedback_lessons.md", "# Human QA Supervisor Lessons\n"),
    "system": (
        "knowledge/general/system_lessons.md",
        "# System Lessons Learned (Self-Improvement Log)\n\nThis file is automatically updated by the @Reflection-Agent to improve future QC accuracy.\n",
    ),
}


def _path(project_root: Path, key: str) -> Path:
    return project_root / FILE_MAP[key][0]


def _ensure_file(project_root: Path, key: str) -> Path:
    path = _path(project_root, key)
    ensure_text_file(path, FILE_MAP[key][1])
    return path


def get_knowledge_context(project_root: Path) -> str:
    ordered_paths = [
        project_root / "knowledge/general/human_feedback_lessons.md",
        project_root / "knowledge/general/system_lessons.md",
        project_root / "knowledge/general/wcag_global.md",
        project_root / "knowledge/requirements/project_x_req.md",
    ]
    sections = []
    for path in ordered_paths:
        if path.exists():
            sections.append(path.read_text(encoding="utf-8").strip())
    return "\n\n".join(section for section in sections if section)


def append_lesson_block(project_root: Path, key: str, title: str, bullets: list[str]) -> None:
    path = _ensure_file(project_root, key)
    clean_bullets = [bullet.strip() for bullet in bullets if bullet.strip()]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n\n" + title + "\n")
        for bullet in clean_bullets:
            prefix = bullet if bullet.startswith(("-", "*")) else f"- {bullet}"
            handle.write(prefix + "\n")


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


def maybe_consolidate(project_root: Path, key: str) -> bool:
    path = _ensure_file(project_root, key)
    content = path.read_text(encoding="utf-8")
    header, sections = _split_sections(content)
    if len(sections) <= 10:
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
