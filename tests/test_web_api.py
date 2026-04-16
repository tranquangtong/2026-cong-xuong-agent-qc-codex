from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.app import app


REPO_ROOT = Path(__file__).resolve().parent.parent


class WebApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="agent-qc-web-"))
        for relative in ("docs", "knowledge/general", "knowledge/requirements", "outputs"):
            (self.temp_dir / relative).mkdir(parents=True, exist_ok=True)

        for relative in (
            "knowledge/general/human_feedback_lessons.md",
            "knowledge/general/system_lessons.md",
            "knowledge/general/wcag_global.md",
            "knowledge/requirements/project_x_req.md",
            "docs/communication.md",
        ):
            shutil.copy(REPO_ROOT / relative, self.temp_dir / relative)

        os.environ["AGENT_QC_ROOT"] = str(self.temp_dir)
        os.environ["GROQ_API_KEY"] = "test-groq"
        os.environ["GOOGLE_API_KEY"] = "test-google"
        self.client = TestClient(app)

    def tearDown(self) -> None:
        for key in (
            "AGENT_QC_ROOT",
            "GROQ_API_KEY",
            "GOOGLE_API_KEY",
        ):
            os.environ.pop(key, None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_content_job_with_document(self) -> None:
        response = self.client.post(
            "/api/jobs",
            data={"mode": "cg", "prompt_text": "Check grammar", "links": "https://www.figma.com/design/abc/demo", "created_by_label": "Tong"},
            files={"documents": ("storyboard.csv", b"Screen,Copy\n1,Colour choice\n", "text/csv")},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mode"], "cg")
        self.assertEqual(payload["status"], "queued")
        detail = self.client.get(f"/api/jobs/{payload['job_id']}")
        self.assertEqual(detail.status_code, 200)
        detail_payload = detail.json()
        self.assertEqual(detail_payload["status"], "completed")
        self.assertGreaterEqual(detail_payload["findings_count"], 1)
        self.assertTrue(any("storyboard.csv" in item for item in detail_payload["source_summary"]))

    def test_create_graphic_job_with_image(self) -> None:
        response = self.client.post(
            "/api/jobs",
            data={"mode": "fg", "prompt_text": "Review this screen", "links": "https://www.figma.com/design/abc/frame", "created_by_label": "Tong"},
            files={"images": ("screen.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "queued")
        detail = self.client.get(f"/api/jobs/{payload['job_id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["status"], "completed")
        artifacts_response = self.client.get(f"/api/jobs/{payload['job_id']}/artifacts")
        self.assertEqual(artifacts_response.status_code, 200)
        self.assertTrue(any(item["name"] == "screen.png" for item in artifacts_response.json()))

    def test_list_jobs_is_public(self) -> None:
        response = self.client.get("/api/jobs")
        self.assertEqual(response.status_code, 200)
