from __future__ import annotations

import os
from typing import Annotated

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api.contracts import ArtifactResponse, JobDetailResponse, JobSummaryResponse, ReportResponse
from api.service import JobService


app = FastAPI(title="Cong Xuong Agent QC Web API", version="0.1.0")

allowed_origins = [origin.strip() for origin in os.getenv("WEB_UI_ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _job_service() -> JobService:
    return JobService()


def _summary_payload(job: dict) -> JobSummaryResponse:
    return JobSummaryResponse(
        job_id=job["job_id"],
        mode=job["mode"],
        status=job["status"],
        created_at=job["created_at"],
        created_by_label=job["created_by_label"],
        prompt_preview=job["prompt_preview"],
        source_summary=job.get("source_summary", []),
        findings_count=job.get("findings_count", 0),
        severity_counts=job.get("severity_counts", {}),
        error_message=job.get("error_message", ""),
    )


def _detail_payload(job: dict) -> JobDetailResponse:
    artifacts = [
        ArtifactResponse(name=item["name"], url=item["url"])
        for item in job.get("artifact_manifest", [])
    ]
    return JobDetailResponse(
        **_summary_payload(job).model_dump(),
        routing_reason=job.get("routing_reason", ""),
        reflection_summary=job.get("reflection_summary", ""),
        findings=job.get("findings", []),
        report_markdown=job.get("report_markdown", ""),
        report_html=job.get("report_html", ""),
        artifact_urls=artifacts,
    )


@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/jobs", response_model=JobDetailResponse)
def create_job(
    background_tasks: BackgroundTasks,
    mode: Annotated[str, Form()],
    prompt_text: Annotated[str, Form()] = "",
    links: Annotated[list[str] | None, Form()] = None,
    images: Annotated[list[UploadFile] | None, File()] = None,
    documents: Annotated[list[UploadFile] | None, File()] = None,
    created_by_label: Annotated[str, Form()] = "Workspace User",
) -> JobDetailResponse:
    if mode not in {"id", "cg", "fg"}:
        raise HTTPException(status_code=400, detail="Unsupported mode")
    service = _job_service()
    job = service.create_job(
        mode=mode,
        prompt_text=prompt_text,
        links=links or [],
        images=images or [],
        documents=documents or [],
        created_by_label=created_by_label.strip() or "Workspace User",
    )
    background_tasks.add_task(service.run_job, job["job_id"])
    return _detail_payload(job)


@app.get("/api/jobs", response_model=list[JobSummaryResponse])
def list_jobs() -> list[JobSummaryResponse]:
    service = _job_service()
    return [_summary_payload(job) for job in service.list_jobs()]


@app.get("/api/jobs/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: str) -> JobDetailResponse:
    service = _job_service()
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _detail_payload(job)


@app.get("/api/jobs/{job_id}/report", response_model=ReportResponse)
def get_job_report(job_id: str) -> ReportResponse:
    service = _job_service()
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return ReportResponse(
        job_id=job_id,
        report_markdown=job.get("report_markdown", ""),
        report_html=job.get("report_html", ""),
    )


@app.get("/api/jobs/{job_id}/artifacts", response_model=list[ArtifactResponse])
def list_job_artifacts(job_id: str) -> list[ArtifactResponse]:
    service = _job_service()
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return [ArtifactResponse(name=item["name"], url=item["url"]) for item in job.get("artifact_manifest", [])]


@app.get("/api/jobs/{job_id}/artifacts/{artifact_name}")
def get_job_artifact(job_id: str, artifact_name: str) -> FileResponse:
    service = _job_service()
    path = service.get_artifact_path(job_id, artifact_name)
    if not path:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(path)
