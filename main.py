from __future__ import annotations

import argparse
from pathlib import Path

from core.config import AppConfig, ConfigError, get_project_root
from core.content_sources import extract_figma_links, has_document_source_hint
from core.graph import invoke_workflow
from core.utils import cleanup_project, ensure_runtime_directories, upgit_project


COMMAND_TO_AGENT = {
    "/id": ["id"],
    "/cg": ["content"],
    "/fg": ["graphic"],
    "/cqc": ["id", "content", "graphic"],
    "/reflect": ["reflection"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cong Xuong Agent QC CLI")
    parser.add_argument("--text", required=True, help="User request or command")
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        help="Optional image path. Can be passed multiple times.",
    )
    return parser.parse_args()


def normalize_command(raw_text: str) -> tuple[str, list[str]]:
    text = raw_text.strip()
    for command, agent_names in COMMAND_TO_AGENT.items():
        if text.lower().startswith(command):
            payload = text[len(command) :].strip()
            return payload or text, list(agent_names)
    return text, []


def detect_flow_type(raw_text: str) -> str:
    text = raw_text.strip().lower()
    if text.startswith("/cqc"):
        return "cqc"
    return ""


def auto_detect_agents(user_text: str, image_paths: list[str], project_root: Path) -> list[str]:
    lowered = user_text.lower()
    content_markers = ("subtitle", "grammar", "spelling", "copy", "content", "text", "storyboard")

    if has_document_source_hint(user_text, project_root):
        return ["content"]

    if image_paths:
        return ["graphic"]

    figma_links = extract_figma_links(user_text)
    if figma_links:
        if any(marker in lowered for marker in content_markers):
            return ["content", "graphic"]
        return ["graphic"]

    articulate_markers = ("articulate", "360.articulate", "rise", "storyline", ".story.html", "scorm")
    if any(marker in lowered for marker in articulate_markers):
        return ["id"]

    design_markers = ("screenshot", "design review", "check this design", "layout", "visual review")
    if any(marker in lowered for marker in design_markers):
        return ["graphic"]

    return []


def main() -> int:
    args = parse_args()
    project_root = get_project_root()
    ensure_runtime_directories(project_root)

    raw_text = args.text.strip()
    normalized_text, explicit_agents = normalize_command(raw_text)
    flow_type = detect_flow_type(raw_text)
    if raw_text.lower().startswith("/cleanup"):
        summary = cleanup_project(project_root)
        print(f"Cleanup complete: removed {summary['removed_count']} temp/cache item(s).")
        if summary["removed_paths"]:
            preview = summary["removed_paths"][:10]
            print("Removed:")
            for item in preview:
                print(f"- {item}")
            if len(summary["removed_paths"]) > len(preview):
                print(f"... and {len(summary['removed_paths']) - len(preview)} more")
        return 0
    if raw_text.lower().startswith("/upgit"):
        commit_message = raw_text[len("/upgit") :].strip() or None
        try:
            summary = upgit_project(project_root, commit_message=commit_message)
        except RuntimeError as exc:
            raise SystemExit(str(exc)) from exc

        cleanup_summary = summary["cleanup_summary"]
        print(f"Cleanup complete: removed {cleanup_summary['removed_count']} temp/cache item(s).")
        if cleanup_summary["removed_paths"]:
            preview = cleanup_summary["removed_paths"][:10]
            print("Removed:")
            for item in preview:
                print(f"- {item}")
            if len(cleanup_summary["removed_paths"]) > len(preview):
                print(f"... and {len(cleanup_summary['removed_paths']) - len(preview)} more")

        if summary["status"] == "no_changes":
            if summary["excluded_paths"]:
                print("Skipped runtime/generated paths:")
                for item in summary["excluded_paths"]:
                    print(f"- {item}")
                remaining = summary["excluded_path_count"] - len(summary["excluded_paths"])
                if remaining > 0:
                    print(f"... and {remaining} more")
            print("Git sync skipped: no staged or unpushed changes remained after cleanup.")
            return 0

        if summary["committed"]:
            print(f"Committed {summary['commit_sha']}: {summary['commit_message']}")
        else:
            print(f"No new commit created; pushing existing local commit(s) on {summary['branch']}.")
        if summary["excluded_paths"]:
            print("Skipped runtime/generated paths:")
            for item in summary["excluded_paths"]:
                print(f"- {item}")
            remaining = summary["excluded_path_count"] - len(summary["excluded_paths"])
            if remaining > 0:
                print(f"... and {remaining} more")
        if summary["staged_changes"]:
            print("Included changes:")
            for item in summary["staged_changes"]:
                print(f"- {item}")
            remaining = summary["staged_change_count"] - len(summary["staged_changes"])
            if remaining > 0:
                print(f"... and {remaining} more")
        print(f"Pushed to {summary['push_target']}.")
        return 0

    bypass_agents = explicit_agents or auto_detect_agents(normalized_text, args.image, project_root)

    try:
        config = AppConfig.load(project_root)
        config.validate_for_agents(bypass_agents)
    except ConfigError as exc:
        raise SystemExit(str(exc)) from exc

    result = invoke_workflow(
        user_text=normalized_text,
        raw_text=raw_text,
        image_paths=[str(Path(path)) for path in args.image],
        next_agents=bypass_agents,
        project_root=project_root,
        config=config,
        flow_type=flow_type,
    )

    print(f"Report generated: {result['report_path']}")
    print(f"Findings count: {len(result['findings'])}")
    if result.get("reflection_summary"):
        print(f"Reflection: {result['reflection_summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
