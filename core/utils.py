from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import subprocess
from uuid import uuid4


def ensure_runtime_directories(project_root: Path) -> None:
    for relative_path in ("agents", "core", "tools", "outputs", "tests"):
        (project_root / relative_path).mkdir(parents=True, exist_ok=True)


def ensure_text_file(path: Path, default_content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(default_content, encoding="utf-8")


def now_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def make_report_name() -> str:
    return "report.md"


def slugify(value: str, max_length: int = 48) -> str:
    normalized = re.sub(r"https?://\S+", " ", value.lower())
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    if not normalized:
        normalized = "qc-run"
    return normalized[:max_length].rstrip("-")


def make_output_bundle_dir(project_root: Path, request_text: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = slugify(request_text)
    output_dir = project_root / "outputs" / f"{timestamp}_{slug}_{uuid4().hex[:6]}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def log_communication(project_root: Path, source: str, target: str, message: str) -> None:
    communication_path = project_root / "docs" / "communication.md"
    ensure_text_file(
        communication_path,
        "| Timestamp | From | To | Message/Task |\n|---|---|---|---|\n",
    )
    timestamp = now_timestamp()
    sanitized = message.replace("\n", " ").strip()
    with communication_path.open("a", encoding="utf-8") as handle:
        handle.write(f"| {timestamp} | {source} | {target} | {sanitized} |\n")


def cleanup_project(project_root: Path) -> dict[str, object]:
    removed_paths: list[str] = []
    removed_count = 0

    removable_dir_names = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    removable_file_names = {".coverage"}
    removable_suffixes = {".pyc", ".pyo"}

    def should_skip(path: Path) -> bool:
        parts = {part.lower() for part in path.parts}
        return ".venv" in parts or "site-packages" in parts

    for path in project_root.rglob("*"):
        if should_skip(path):
            continue
        if path.is_dir() and path.name in removable_dir_names:
            shutil.rmtree(path, ignore_errors=True)
            removed_paths.append(str(path))
            removed_count += 1

    for path in project_root.rglob("*"):
        if should_skip(path):
            continue
        if path.is_file() and (path.name in removable_file_names or path.suffix in removable_suffixes):
            try:
                path.unlink()
                removed_paths.append(str(path))
                removed_count += 1
            except FileNotFoundError:
                pass

    outputs_dir = project_root / "outputs"
    if outputs_dir.exists():
        for path in outputs_dir.iterdir():
            if path.is_file():
                try:
                    path.unlink()
                    removed_paths.append(str(path))
                    removed_count += 1
                except FileNotFoundError:
                    pass

    return {
        "removed_count": removed_count,
        "removed_paths": removed_paths,
    }


def _run_git_command(project_root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=project_root,
        text=True,
        capture_output=True,
        check=check,
    )


def _git_error_message(result: subprocess.CompletedProcess[str]) -> str:
    return result.stderr.strip() or result.stdout.strip() or "Git command failed."


def _count_ahead_of_upstream(project_root: Path, upstream: str | None) -> int:
    if not upstream:
        return 0
    result = _run_git_command(project_root, ["rev-list", "--left-right", "--count", f"{upstream}...HEAD"], check=False)
    if result.returncode != 0:
        return 0
    counts = result.stdout.strip().split()
    if len(counts) != 2:
        return 0
    try:
        return int(counts[1])
    except ValueError:
        return 0


UPGIT_EXCLUDED_PATHS = {
    "docs/communication.md",
}

UPGIT_EXCLUDED_PREFIXES = (
    "outputs/",
    ".web-runtime/",
)


def _is_upgit_excluded(path: str) -> bool:
    normalized = path.strip()
    if not normalized:
        return False
    if normalized in UPGIT_EXCLUDED_PATHS:
        return True
    return any(normalized.startswith(prefix) for prefix in UPGIT_EXCLUDED_PREFIXES)


def _parse_name_status_lines(output: str) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        paths = [part for part in parts[1:] if part]
        primary_path = paths[-1] if paths else ""
        entries.append(
            {
                "status": status,
                "paths": paths,
                "path": primary_path,
                "display": line,
            }
        )
    return entries


def _collect_staged_changes(project_root: Path) -> list[dict[str, object]]:
    result = _run_git_command(project_root, ["diff", "--cached", "--name-status"], check=False)
    return _parse_name_status_lines(result.stdout)


def _derive_change_focus(paths: list[str]) -> list[str]:
    focus: list[str] = []

    def add(label: str) -> None:
        if label not in focus:
            focus.append(label)

    for path in paths:
        if "upgit" in path:
            add("upgit")
        elif "cleanup" in path:
            add("cleanup")
        elif path == "main.py":
            add("cli")
        elif path.startswith(".agents/skills/"):
            add("skills")
        elif path.startswith("tests/"):
            add("tests")
        elif path.startswith("docs/") or path in {"AGENTS.md", "claude.md", "README.md"}:
            add("docs")
        elif path.startswith("core/"):
            add("core")
        elif path.startswith("agents/"):
            add("agents")
        elif path.startswith("api/"):
            add("api")
        elif path.startswith("web/"):
            add("web")
        else:
            head = path.split("/", 1)[0] if "/" in path else path
            add(head.replace("_", "-"))

    return focus


def _generate_upgit_commit_message(staged_changes: list[dict[str, object]]) -> str:
    paths = [str(item["path"]) for item in staged_changes if item.get("path")]
    if not paths:
        return "chore: sync project updates"

    focus = _derive_change_focus(paths)
    path_set = set(paths)

    if "upgit" in focus and ("cli" in focus or "core" in focus):
        return "feat: refine upgit workflow"
    if "cleanup" in focus and ("cli" in focus or "core" in focus):
        return "feat: refine cleanup workflow"
    if focus[:2] == ["docs"] or set(focus) == {"docs"}:
        return "docs: update project guidance"
    if set(focus).issubset({"tests"}):
        return "test: update workflow coverage"
    if "skills" in focus and set(focus).issubset({"skills", "docs"}):
        skill_names = sorted({path.split("/")[2] for path in path_set if path.startswith(".agents/skills/") and len(path.split("/")) > 2})
        if len(skill_names) == 1:
            return f"feat: add {skill_names[0]} skill"
        if skill_names:
            return "feat: update repo skills"
    if {"cli", "core", "tests"}.issubset(set(focus)):
        return "feat: update CLI workflow handling"

    summary = ", ".join(focus[:3]) if focus else "project"
    return f"chore: update {summary}"


def upgit_project(project_root: Path, commit_message: str | None = None) -> dict[str, object]:
    cleanup_summary = cleanup_project(project_root)

    repo_probe = _run_git_command(project_root, ["rev-parse", "--is-inside-work-tree"], check=False)
    if repo_probe.returncode != 0 or repo_probe.stdout.strip() != "true":
        raise RuntimeError("`/upgit` requires the current project to be a git repository.")

    branch = _run_git_command(project_root, ["branch", "--show-current"], check=False).stdout.strip() or "HEAD"
    upstream_probe = _run_git_command(
        project_root,
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        check=False,
    )
    upstream = upstream_probe.stdout.strip() if upstream_probe.returncode == 0 else None
    remote_probe = _run_git_command(project_root, ["remote"], check=False)
    remotes = {line.strip() for line in remote_probe.stdout.splitlines() if line.strip()}

    _run_git_command(project_root, ["add", "-A"])
    initial_staged_changes = _collect_staged_changes(project_root)
    excluded_paths = sorted(
        {
            path
            for item in initial_staged_changes
            for path in item["paths"]
            if isinstance(path, str) and _is_upgit_excluded(path)
        }
    )
    if excluded_paths:
        _run_git_command(project_root, ["restore", "--staged", "--", *excluded_paths], check=False)
    staged_changes = _collect_staged_changes(project_root)

    committed = False
    commit_sha: str | None = None
    final_message = (commit_message or "").strip() or _generate_upgit_commit_message(staged_changes)

    if staged_changes:
        commit_result = _run_git_command(project_root, ["commit", "-m", final_message], check=False)
        if commit_result.returncode != 0:
            raise RuntimeError(f"Git commit failed: {_git_error_message(commit_result)}")
        committed = True
        commit_sha = _run_git_command(project_root, ["rev-parse", "--short", "HEAD"], check=False).stdout.strip() or None

    ahead_count = _count_ahead_of_upstream(project_root, upstream)
    if not committed and ahead_count == 0:
        return {
            "status": "no_changes",
            "cleanup_summary": cleanup_summary,
            "branch": branch,
            "upstream": upstream,
            "push_target": upstream,
            "committed": False,
            "pushed": False,
            "commit_message": None,
            "commit_sha": None,
            "staged_changes": [],
            "staged_change_count": 0,
            "excluded_paths": excluded_paths[:10],
            "excluded_path_count": len(excluded_paths),
            "ahead_count": 0,
        }

    push_target: str | None = upstream
    if upstream:
        push_args = ["push"]
    elif "origin" in remotes and branch != "HEAD":
        push_args = ["push", "-u", "origin", branch]
        push_target = f"origin/{branch}"
    else:
        if committed and commit_sha:
            raise RuntimeError(
                f"Created local commit {commit_sha}, but could not determine where to push it. Configure an upstream or add an `origin` remote."
            )
        raise RuntimeError("No git upstream is configured for this branch, and no `origin` remote is available for `/upgit`.")

    push_result = _run_git_command(project_root, push_args, check=False)
    if push_result.returncode != 0:
        if committed and commit_sha:
            raise RuntimeError(f"Created local commit {commit_sha}, but push failed: {_git_error_message(push_result)}")
        raise RuntimeError(f"Git push failed: {_git_error_message(push_result)}")

    return {
        "status": "pushed",
        "cleanup_summary": cleanup_summary,
        "branch": branch,
        "upstream": upstream,
        "push_target": push_target,
        "committed": committed,
        "pushed": True,
        "commit_message": final_message if committed else None,
        "commit_sha": commit_sha,
        "staged_changes": [str(item["display"]) for item in staged_changes[:10]],
        "staged_change_count": len(staged_changes),
        "excluded_paths": excluded_paths[:10],
        "excluded_path_count": len(excluded_paths),
        "ahead_count": _count_ahead_of_upstream(project_root, upstream),
    }
