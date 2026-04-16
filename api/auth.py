from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import UTC, datetime, timedelta


TOKEN_TTL_HOURS = 12


def get_shared_passcode() -> str:
    return os.getenv("WEB_UI_SHARED_PASSCODE", "").strip()


def _token_secret() -> str:
    return os.getenv("WEB_UI_TOKEN_SECRET", "dev-token-secret-change-me")


def create_access_token(user_label: str) -> tuple[str, str]:
    expires_at = datetime.now(UTC) + timedelta(hours=TOKEN_TTL_HOURS)
    payload = {
        "label": user_label.strip() or "Internal User",
        "exp": expires_at.isoformat(),
    }
    body = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    signature = hmac.new(_token_secret().encode("utf-8"), body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body}.{signature}", expires_at.isoformat()


def verify_access_token(token: str) -> str:
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("Malformed token") from exc

    expected_signature = hmac.new(_token_secret().encode("utf-8"), body.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid token signature")

    payload = json.loads(base64.urlsafe_b64decode(body.encode("ascii")).decode("utf-8"))
    expires_at = datetime.fromisoformat(payload["exp"])
    if expires_at < datetime.now(UTC):
        raise ValueError("Token expired")
    return str(payload.get("label", "Internal User"))

