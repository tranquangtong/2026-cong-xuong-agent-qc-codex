from __future__ import annotations

from contextlib import closing
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class JobStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with closing(self._connect()) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    created_by_label TEXT NOT NULL,
                    prompt_preview TEXT NOT NULL,
                    prompt_text TEXT NOT NULL,
                    source_summary_json TEXT NOT NULL,
                    findings_json TEXT NOT NULL,
                    findings_count INTEGER NOT NULL,
                    severity_counts_json TEXT NOT NULL,
                    routing_reason TEXT NOT NULL,
                    reflection_summary TEXT NOT NULL,
                    report_markdown TEXT NOT NULL,
                    report_html TEXT NOT NULL,
                    artifact_manifest_json TEXT NOT NULL,
                    error_message TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def create_job(self, payload: dict[str, Any]) -> None:
        with self._lock, closing(self._connect()) as connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    job_id, mode, status, created_at, created_by_label,
                    prompt_preview, prompt_text, source_summary_json, findings_json,
                    findings_count, severity_counts_json, routing_reason,
                    reflection_summary, report_markdown, report_html,
                    artifact_manifest_json, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["job_id"],
                    payload["mode"],
                    payload["status"],
                    payload["created_at"],
                    payload["created_by_label"],
                    payload["prompt_preview"],
                    payload["prompt_text"],
                    json.dumps(payload.get("source_summary", [])),
                    json.dumps(payload.get("findings", [])),
                    int(payload.get("findings_count", 0)),
                    json.dumps(payload.get("severity_counts", {})),
                    payload.get("routing_reason", ""),
                    payload.get("reflection_summary", ""),
                    payload.get("report_markdown", ""),
                    payload.get("report_html", ""),
                    json.dumps(payload.get("artifact_manifest", [])),
                    payload.get("error_message", ""),
                ),
            )
            connection.commit()

    def update_job(self, job_id: str, payload: dict[str, Any]) -> None:
        fields = {
            "status": payload.get("status"),
            "source_summary_json": json.dumps(payload.get("source_summary", [])),
            "findings_json": json.dumps(payload.get("findings", [])),
            "findings_count": int(payload.get("findings_count", 0)),
            "severity_counts_json": json.dumps(payload.get("severity_counts", {})),
            "routing_reason": payload.get("routing_reason", ""),
            "reflection_summary": payload.get("reflection_summary", ""),
            "report_markdown": payload.get("report_markdown", ""),
            "report_html": payload.get("report_html", ""),
            "artifact_manifest_json": json.dumps(payload.get("artifact_manifest", [])),
            "error_message": payload.get("error_message", ""),
        }
        assignments = ", ".join(f"{column} = ?" for column in fields)
        values = list(fields.values()) + [job_id]
        with self._lock, closing(self._connect()) as connection:
            connection.execute(f"UPDATE jobs SET {assignments} WHERE job_id = ?", values)
            connection.commit()

    def list_jobs(self) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            rows = connection.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        return [self._deserialize(row) for row in rows]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            row = connection.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        return self._deserialize(row) if row else None

    def _deserialize(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "job_id": row["job_id"],
            "mode": row["mode"],
            "status": row["status"],
            "created_at": row["created_at"],
            "created_by_label": row["created_by_label"],
            "prompt_preview": row["prompt_preview"],
            "prompt_text": row["prompt_text"],
            "source_summary": json.loads(row["source_summary_json"]),
            "findings": json.loads(row["findings_json"]),
            "findings_count": row["findings_count"],
            "severity_counts": json.loads(row["severity_counts_json"]),
            "routing_reason": row["routing_reason"],
            "reflection_summary": row["reflection_summary"],
            "report_markdown": row["report_markdown"],
            "report_html": row["report_html"],
            "artifact_manifest": json.loads(row["artifact_manifest_json"]),
            "error_message": row["error_message"],
        }
