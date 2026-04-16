from __future__ import annotations

import os
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api.auth import create_access_token, get_shared_passcode, verify_access_token
from api.contracts import ArtifactResponse, JobDetailResponse, JobSummaryResponse, LoginRequest, LoginResponse, ReportResponse
from api.service import JobService


app = FastAPI(title="Cong Xuong Agent QC Web API", version="0.1.0")

allowed_origins = [origin.strip() for origin in os.getenv("WEB_UI_ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,https://tranquangtong.github.io").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_user_label(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


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


@app.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    expected_passcode = get_shared_passcode()
    if not expected_passcode:
        raise HTTPException(status_code=500, detail="WEB_UI_SHARED_PASSCODE is not configured")
    if payload.passcode != expected_passcode:
        raise HTTPException(status_code=401, detail="Invalid passcode")
    access_token, expires_at = create_access_token(payload.label)
    return LoginResponse(access_token=access_token, expires_at=expires_at, user_label=payload.label)


@app.post("/api/jobs", response_model=JobDetailResponse)
def create_job(
    background_tasks: BackgroundTasks,
    mode: Annotated[str, Form()],
    prompt_text: Annotated[str, Form()] = "",
    links: Annotated[list[str] | None, Form()] = None,
    images: Annotated[list[UploadFile] | None, File()] = None,
    documents: Annotated[list[UploadFile] | None, File()] = None,
    user_label: str = Depends(_require_user_label),
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
        created_by_label=user_label,
    )
    background_tasks.add_task(service.run_job, job["job_id"])
    return _detail_payload(job)


@app.get("/api/jobs", response_model=list[JobSummaryResponse])
def list_jobs(user_label: str = Depends(_require_user_label)) -> list[JobSummaryResponse]:
    del user_label
    service = _job_service()
    return [_summary_payload(job) for job in service.list_jobs()]


@app.get("/api/jobs/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: str, user_label: str = Depends(_require_user_label)) -> JobDetailResponse:
    del user_label
    service = _job_service()
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _detail_payload(job)


@app.get("/api/jobs/{job_id}/report", response_model=ReportResponse)
def get_job_report(job_id: str, user_label: str = Depends(_require_user_label)) -> ReportResponse:
    del user_label
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
def list_job_artifacts(job_id: str, user_label: str = Depends(_require_user_label)) -> list[ArtifactResponse]:
    del user_label
    service = _job_service()
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return [ArtifactResponse(name=item["name"], url=item["url"]) for item in job.get("artifact_manifest", [])]


@app.get("/api/jobs/{job_id}/artifacts/{artifact_name}")
def get_job_artifact(job_id: str, artifact_name: str, user_label: str = Depends(_require_user_label)) -> FileResponse:
    del user_label
    service = _job_service()
    path = service.get_artifact_path(job_id, artifact_name)
    if not path:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(path)
