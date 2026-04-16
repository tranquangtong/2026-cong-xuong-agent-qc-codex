from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import markdown
from fastapi import UploadFile

from api.storage import JobStore
from core.config import AppConfig, get_project_root
from core.content_sources import summarize_content_sources
from core.graph import invoke_workflow


MODE_TO_COMMAND = {
    "id": "/id",
    "cg": "/cg",
    "fg": "/fg",
}

MODE_TO_AGENT = {
    "id": ["id"],
    "cg": ["content"],
    "fg": ["graphic"],
}

SEVERITY_ORDER = ("Critical", "Major", "Minor", "Suggestion", "Info")


class JobService:
    def __init__(self) -> None:
        self.project_root = get_project_root()
        self.runtime_root = self.project_root / ".web-runtime"
        self.jobs_root = self.runtime_root / "jobs"
        self.jobs_root.mkdir(parents=True, exist_ok=True)
        self.store = JobStore(self.runtime_root / "jobs.db")

    def create_job(
        self,
        *,
        mode: str,
        prompt_text: str,
        links: list[str],
        images: list[UploadFile],
        documents: list[UploadFile],
        created_by_label: str,
    ) -> dict[str, Any]:
        job_id = uuid4().hex[:12]
        job_dir = self.jobs_root / job_id
        inputs_dir = job_dir / "inputs"
        images_dir = inputs_dir / "images"
        documents_dir = inputs_dir / "documents"
        images_dir.mkdir(parents=True, exist_ok=True)
        documents_dir.mkdir(parents=True, exist_ok=True)

        image_paths = [self._persist_upload(upload, images_dir) for upload in images]
        document_paths = [self._persist_upload(upload, documents_dir) for upload in documents]
        full_prompt = self._build_prompt(prompt_text, links, document_paths)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        initial_record = {
            "job_id": job_id,
            "mode": mode,
            "status": "queued",
            "created_at": created_at,
            "created_by_label": created_by_label,
            "prompt_preview": self._prompt_preview(full_prompt),
            "prompt_text": full_prompt,
            "source_summary": [],
            "findings": [],
            "findings_count": 0,
            "severity_counts": {},
            "routing_reason": "",
            "reflection_summary": "",
            "report_markdown": "",
            "report_html": "",
            "artifact_manifest": self._artifact_manifest(job_id, image_paths + document_paths),
            "error_message": "",
        }
        self.store.create_job(initial_record)
        return initial_record

    def run_job(self, job_id: str) -> None:
        job = self.store.get_job(job_id)
        if not job:
            return

        self.store.update_job(job_id, {**job, "status": "running", "error_message": ""})

        try:
            config = AppConfig.load(self.project_root)
            config.validate_for_agents(MODE_TO_AGENT[job["mode"]])
            raw_text = f"{MODE_TO_COMMAND[job['mode']]} {job['prompt_text']}".strip()
            result = invoke_workflow(
                user_text=job["prompt_text"],
                raw_text=raw_text,
                image_paths=self._image_paths_from_manifest(job["artifact_manifest"]),
                next_agents=MODE_TO_AGENT[job["mode"]],
                project_root=self.project_root,
                config=config,
            )
            report_markdown = Path(result["report_path"]).read_text(encoding="utf-8")
            artifact_manifest = self._artifact_manifest_from_output(job_id, job["artifact_manifest"], result["report_path"])
            payload = {
                **job,
                "status": "completed",
                "source_summary": summarize_content_sources(result.get("content_sources", [])),
                "findings": result.get("findings", []),
                "findings_count": len(result.get("findings", [])),
                "severity_counts": self._severity_counts(result.get("findings", [])),
                "routing_reason": result.get("routing_reason", ""),
                "reflection_summary": result.get("reflection_summary", ""),
                "report_markdown": report_markdown,
                "report_html": markdown.markdown(report_markdown, extensions=["tables"]),
                "artifact_manifest": artifact_manifest,
                "error_message": "",
            }
            self.store.update_job(job_id, payload)
        except Exception as exc:
            self.store.update_job(
                job_id,
                {
                    **job,
                    "status": "failed",
                    "error_message": str(exc),
                },
            )

    def list_jobs(self) -> list[dict[str, Any]]:
        return self.store.list_jobs()

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self.store.get_job(job_id)

    def get_artifact_path(self, job_id: str, artifact_name: str) -> Path | None:
        job = self.get_job(job_id)
        if not job:
            return None
        for artifact in job.get("artifact_manifest", []):
            if artifact["name"] == artifact_name:
                path = Path(artifact["path"])
                if path.exists():
                    return path
        return None

    def _persist_upload(self, upload: UploadFile, target_dir: Path) -> str:
        safe_name = Path(upload.filename or "upload.bin").name
        target_path = target_dir / safe_name
        with target_path.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)
        return str(target_path.resolve())

    def _build_prompt(self, prompt_text: str, links: list[str], document_paths: list[str]) -> str:
        sections: list[str] = []
        if prompt_text.strip():
            sections.append(prompt_text.strip())
        if links:
            sections.append("Links:\n" + "\n".join(link.strip() for link in links if link.strip()))
        if document_paths:
            sections.append("Documents:\n" + "\n".join(f'"{path}"' for path in document_paths))
        return "\n\n".join(sections).strip() or "Run QC review."

    def _prompt_preview(self, prompt_text: str) -> str:
        compact = " ".join(prompt_text.split())
        return compact[:160]

    def _severity_counts(self, findings: list[dict[str, Any]]) -> dict[str, int]:
        counts = {severity: 0 for severity in SEVERITY_ORDER}
        for finding in findings:
            severity = str(finding.get("severity", "Info"))
            counts[severity] = counts.get(severity, 0) + 1
        return {key: value for key, value in counts.items() if value}

    def _artifact_manifest(self, job_id: str, paths: list[str]) -> list[dict[str, str]]:
        artifacts: list[dict[str, str]] = []
        for raw_path in paths:
            path = Path(raw_path)
            if not path.exists():
                continue
            artifacts.append(
                {
                    "name": path.name,
                    "path": str(path),
                    "url": f"/api/jobs/{job_id}/artifacts/{path.name}",
                }
            )
        return artifacts

    def _artifact_manifest_from_output(
        self,
        job_id: str,
        existing: list[dict[str, str]],
        report_path: str,
    ) -> list[dict[str, str]]:
        artifacts = list(existing)
        report_file = Path(report_path)
        artifacts.append(
            {
                "name": "report.md",
                "path": str(report_file),
                "url": f"/api/jobs/{job_id}/artifacts/report.md",
            }
        )
        artifacts_dir = report_file.parent / "artifacts"
        if artifacts_dir.exists():
            for path in sorted(artifacts_dir.iterdir()):
                if path.is_file():
                    artifacts.append(
                        {
                            "name": path.name,
                            "path": str(path),
                            "url": f"/api/jobs/{job_id}/artifacts/{path.name}",
                        }
                    )
        deduped: dict[str, dict[str, str]] = {}
        for item in artifacts:
            deduped[item["name"]] = item
        return list(deduped.values())

    def _image_paths_from_manifest(self, artifact_manifest: list[dict[str, str]]) -> list[str]:
        image_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
        return [
            item["path"]
            for item in artifact_manifest
            if Path(item["name"]).suffix.lower() in image_suffixes
        ]

