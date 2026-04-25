from __future__ import annotations

from pathlib import Path
from typing import Callable, TypedDict

from core.state import AgentState, QAFinding
from tools.text_tools import make_finding_id
from tools.wcag_contrast import ContrastAudit, audit_image_contrast


WCAG_BASELINE = "WCAG 2.2 AA"


class WCAGIssue(TypedDict):
    severity: str
    area: str
    criterion: str
    evidence: str
    impact: str
    recommended_fix: str


class WCAGAudit(TypedDict):
    issues: list[WCAGIssue]
    limitations: list[str]
    checked_images: list[str]


ContrastAuditor = Callable[[list[str]], ContrastAudit]


def _unique_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for raw_path in paths:
        path = str(raw_path).strip()
        if not path or path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def collect_wcag_image_paths(state: AgentState) -> list[str]:
    paths: list[str] = [*state.get("image_paths", [])]

    probe = state.get("browser_probe")
    if isinstance(probe, dict):
        if probe.get("screenshot_path"):
            paths.append(str(probe["screenshot_path"]))
        for visited_state in probe.get("visited_states", []):
            if isinstance(visited_state, dict) and visited_state.get("screenshot_path"):
                paths.append(str(visited_state["screenshot_path"]))

    for source in state.get("content_sources", []):
        paths.extend(str(path) for path in source.get("image_paths", []))

    return _unique_paths(paths)


def _contrast_issues(image_paths: list[str], contrast_auditor: ContrastAuditor) -> WCAGAudit:
    if not image_paths:
        return {"issues": [], "limitations": [], "checked_images": []}

    audit = contrast_auditor(image_paths)
    issues: list[WCAGIssue] = []
    for issue in audit.get("issues", []):
        image_name = Path(str(issue["image_path"])).name
        size_label = "large text" if issue["large_text"] else "normal text"
        issues.append(
            {
                "severity": "Major" if issue["threshold"] >= 4.5 else "Minor",
                "area": "WCAG Contrast Ratio",
                "criterion": "1.4.3 Contrast (Minimum)",
                "evidence": (
                    f"{image_name}: OCR sample '{issue['label']}' measured approximately "
                    f"{issue['ratio']:.2f}:1 against the local background "
                    f"({issue['foreground_hex']} on {issue['background_hex']}). "
                    f"This is below the WCAG AA threshold of {issue['threshold']:.1f}:1 for {size_label}."
                ),
                "impact": (
                    "Low text contrast can reduce readability, especially when the course is viewed at "
                    "normal playback size or on lower-quality displays."
                ),
                "recommended_fix": (
                    "Increase the luminance difference between the text and its immediate background, "
                    "or enlarge/promote the text so it meets the appropriate WCAG AA threshold."
                ),
            }
        )

    return {
        "issues": issues,
        "limitations": list(audit.get("limitations", [])),
        "checked_images": list(audit.get("checked_images", [])),
    }


def _browser_probe_issues(state: AgentState) -> list[WCAGIssue]:
    probe = state.get("browser_probe")
    if not isinstance(probe, dict):
        return []

    issues: list[WCAGIssue] = []
    for visited_state in probe.get("visited_states", []):
        if not isinstance(visited_state, dict):
            continue
        state_label = str(visited_state.get("step") or visited_state.get("title") or "browser state")
        for action in visited_state.get("actionables", []):
            if not isinstance(action, dict):
                continue
            role = str(action.get("role", "")).strip()
            tag = str(action.get("tag", "")).strip()
            name = str(action.get("name", "")).strip()
            if not role and tag not in {"button", "a", "input", "select", "textarea"}:
                continue
            if name:
                continue
            issues.append(
                {
                    "severity": "Major",
                    "area": "WCAG Accessible Name",
                    "criterion": "4.1.2 Name, Role, Value",
                    "evidence": (
                        f"{state_label}: detected an interactive control with role/tag "
                        f"'{role or tag}' but no accessible name in browser probe actionables."
                    ),
                    "impact": "Screen reader and voice-control users may not know what the control does.",
                    "recommended_fix": (
                        "Provide a visible label, aria-label, aria-labelledby, or equivalent programmatic "
                        "name that matches the learner-facing purpose of the control."
                    ),
                }
            )
    return issues


def audit_wcag_state(
    state: AgentState,
    *,
    contrast_auditor: ContrastAuditor = audit_image_contrast,
) -> WCAGAudit:
    image_audit = _contrast_issues(collect_wcag_image_paths(state), contrast_auditor)
    return {
        "issues": [*image_audit["issues"], *_browser_probe_issues(state)],
        "limitations": image_audit["limitations"],
        "checked_images": image_audit["checked_images"],
    }


def wcag_audit_to_findings(
    audit: WCAGAudit,
    *,
    prefix: str,
    source_agent: str,
    start_index: int = 1,
) -> list[QAFinding]:
    findings: list[QAFinding] = []
    index = start_index

    for issue in audit.get("issues", []):
        findings.append(
            {
                "id": make_finding_id(prefix, index),
                "severity": issue["severity"],  # type: ignore[typeddict-item]
                "area": issue["area"],
                "evidence": f"{WCAG_BASELINE} {issue['criterion']}: {issue['evidence']}",
                "impact": issue["impact"],
                "recommended_fix": issue["recommended_fix"],
                "source_agent": source_agent,
            }
        )
        index += 1

    for limitation in audit.get("limitations", []):
        findings.append(
            {
                "id": make_finding_id(prefix, index),
                "severity": "Info",
                "area": "WCAG Contrast Coverage",
                "evidence": limitation,
                "impact": "Deterministic WCAG coverage was limited for part of the supplied evidence.",
                "recommended_fix": (
                    "Install the missing OCR/image runtime dependencies, provide clearer rendered screenshots, "
                    "or rerun with browser/image evidence so the checker can measure local text contrast."
                ),
                "source_agent": source_agent,
            }
        )
        index += 1

    return findings


def build_wcag_findings(
    state: AgentState,
    *,
    prefix: str,
    source_agent: str,
    start_index: int = 1,
    contrast_auditor: ContrastAuditor = audit_image_contrast,
) -> list[QAFinding]:
    return wcag_audit_to_findings(
        audit_wcag_state(state, contrast_auditor=contrast_auditor),
        prefix=prefix,
        source_agent=source_agent,
        start_index=start_index,
    )
