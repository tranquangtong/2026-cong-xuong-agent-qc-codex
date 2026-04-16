from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from core.state import QAFinding


JobStatus = Literal["queued", "running", "completed", "failed"]
QCRunMode = Literal["id", "cg", "fg"]


class ArtifactResponse(BaseModel):
    name: str
    url: str


class JobSummaryResponse(BaseModel):
    job_id: str
    mode: QCRunMode
    status: JobStatus
    created_at: str
    created_by_label: str
    prompt_preview: str
    source_summary: list[str]
    findings_count: int
    severity_counts: dict[str, int]
    error_message: str = ""


class JobDetailResponse(JobSummaryResponse):
    routing_reason: str = ""
    reflection_summary: str = ""
    findings: list[QAFinding]
    report_markdown: str = ""
    report_html: str = ""
    artifact_urls: list[ArtifactResponse]


class ReportResponse(BaseModel):
    job_id: str
    report_markdown: str
    report_html: str
