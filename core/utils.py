from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
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
