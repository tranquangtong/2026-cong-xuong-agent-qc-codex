from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when required configuration is missing."""


def get_project_root() -> Path:
    override = os.getenv("AGENT_QC_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parent.parent


def _load_dotenv(project_root: Path) -> None:
    env_path = project_root / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(slots=True)
class AppConfig:
    openai_api_key: str
    google_api_key: str
    groq_api_key: str
    router_provider: str
    router_model: str
    content_provider: str
    content_model: str
    design_review_provider: str
    design_review_model: str
    graphic_provider: str
    graphic_model: str
    id_provider: str
    id_model: str
    reflection_provider: str
    reflection_model: str
    video_asr_provider: str
    video_asr_model: str
    video_frame_interval_seconds: int
    video_max_midpoint_frames_per_run: int

    def api_key_for_provider(self, provider: str) -> str:
        if provider == "openai":
            return self.openai_api_key
        if provider == "groq":
            return self.groq_api_key
        if provider == "google":
            return self.google_api_key
        return ""

    @classmethod
    def load(cls, project_root: Path) -> "AppConfig":
        _load_dotenv(project_root)
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            google_api_key=os.getenv("GOOGLE_API_KEY", ""),
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            router_provider=os.getenv("ROUTER_PROVIDER", "groq"),
            router_model=os.getenv("ROUTER_MODEL", "llama-3.3-70b-versatile"),
            content_provider=os.getenv("CONTENT_PROVIDER", "groq"),
            content_model=os.getenv("CONTENT_MODEL", "llama-3.3-70b-versatile"),
            design_review_provider=os.getenv("DESIGN_REVIEW_PROVIDER", os.getenv("VIDEO_PROVIDER", "groq")),
            design_review_model=os.getenv(
                "DESIGN_REVIEW_MODEL",
                os.getenv("VIDEO_VISUAL_MODEL", os.getenv("CONTENT_MODEL", "llama-3.2-90b-vision-preview")),
            ),
            graphic_provider=os.getenv("GRAPHIC_PROVIDER", os.getenv("DESIGN_REVIEW_PROVIDER", os.getenv("VIDEO_PROVIDER", "groq"))),
            graphic_model=os.getenv(
                "GRAPHIC_MODEL",
                os.getenv("DESIGN_REVIEW_MODEL", os.getenv("VIDEO_VISUAL_MODEL", "llama-3.2-90b-vision-preview")),
            ),
            id_provider=os.getenv("ID_PROVIDER", "groq"),
            id_model=os.getenv("ID_MODEL", "llama-3.3-70b-versatile"),
            reflection_provider=os.getenv("REFLECTION_PROVIDER", "google"),
            reflection_model=os.getenv("REFLECTION_MODEL", "gemini-2.5-flash"),
            video_asr_provider=os.getenv("VIDEO_ASR_PROVIDER", "openai"),
            video_asr_model=os.getenv("VIDEO_ASR_MODEL", "gpt-4o-mini-transcribe"),
            video_frame_interval_seconds=int(os.getenv("VIDEO_FRAME_INTERVAL_SECONDS", "2")),
            video_max_midpoint_frames_per_run=int(os.getenv("VIDEO_MAX_MIDPOINT_FRAMES_PER_RUN", "200")),
        )

    def validate_for_agents(self, next_agents: list[str]) -> None:
        required_keys: list[tuple[str, str]] = []

        def require_provider(provider: str) -> None:
            if provider == "groq":
                required_keys.append(("GROQ_API_KEY", self.groq_api_key))
            elif provider == "google":
                required_keys.append(("GOOGLE_API_KEY", self.google_api_key))
            elif provider == "openai":
                required_keys.append(("OPENAI_API_KEY", self.openai_api_key))

        if not next_agents:
            require_provider(self.router_provider)
            require_provider(self.id_provider)
            require_provider(self.content_provider)
            require_provider(self.reflection_provider)
        else:
            if "id" in next_agents:
                require_provider(self.id_provider)
            if "content" in next_agents:
                require_provider(self.content_provider)
            if "graphic" in next_agents:
                require_provider(self.graphic_provider)
            if "video" in next_agents:
                # Video analysis itself should still run without ASR credentials.
                pass
            if "reflection" in next_agents:
                require_provider(self.reflection_provider)

        missing = [name for name, value in required_keys if not value]
        if missing:
            raise ConfigError(f"Missing required environment variable(s): {', '.join(sorted(set(missing)))}")
