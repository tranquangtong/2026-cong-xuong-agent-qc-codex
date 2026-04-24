from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from core.content_sources import build_resolved_content_text
from core.llm import invoke_openai_transcription
from core.state import AgentState, ContentSource
from core.utils import log_communication


VIDEO_PATH_PATTERN = re.compile(
    r"['\"]([^'\"]+\.(?:mp4|mov|mkv|webm))['\"]|(?<![\w/.-])([~./\\\w :()-]+\.(?:mp4|mov|mkv|webm))(?![\w/.-])",
    re.IGNORECASE,
)
SRT_PATH_PATTERN = re.compile(
    r"['\"]([^'\"]+\.srt)['\"]|(?<![\w/.-])([~./\\\w :()-]+\.srt)(?![\w/.-])",
    re.IGNORECASE,
)
SEGMENT_HINT_PATTERN = re.compile(
    r"\b(?:from|between|segment|section|chapter|clip)\b.*?\b\d{1,2}[:.]\d{2}(?::\d{2})?\b",
    re.IGNORECASE,
)


def _extract_paths(pattern: re.Pattern[str], text: str) -> list[str]:
    values: list[str] = []
    for match in pattern.findall(text):
        values.extend(part.strip() for part in match if part and part.strip())
    return list(dict.fromkeys(values))


def _resolve_local_path(raw_path: str, project_root: Path) -> Path:
    candidate = Path(raw_path.strip()).expanduser()
    if candidate.exists():
        return candidate.resolve()
    if candidate.is_absolute():
        return candidate
    return (project_root / candidate).resolve()


def _safe_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _parse_srt_timestamp(raw_value: str) -> float:
    cleaned = raw_value.strip().replace(",", ".")
    hours, minutes, seconds = cleaned.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _format_seconds(value: float) -> str:
    total_ms = max(0, int(round(value * 1000)))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def _parse_srt_file(path: Path) -> list[dict[str, Any]]:
    raw_text = path.read_text(encoding="utf-8-sig")
    subtitles: list[dict[str, Any]] = []
    for block in re.split(r"\r?\n\r?\n+", raw_text.strip()):
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        if re.match(r"^\d+$", lines[0].strip()):
            cue_index = int(lines[0].strip())
            time_line = lines[1].strip()
            text_lines = lines[2:]
        else:
            cue_index = len(subtitles) + 1
            time_line = lines[0].strip()
            text_lines = lines[1:]
        if "-->" not in time_line:
            continue
        start_raw, end_raw = [part.strip() for part in time_line.split("-->", 1)]
        start_seconds = _parse_srt_timestamp(start_raw)
        end_seconds = _parse_srt_timestamp(end_raw)
        normalized_lines = [_normalize_whitespace(line) for line in text_lines if _normalize_whitespace(line)]
        text = "\n".join(normalized_lines).strip()
        subtitles.append(
            {
                "cue_index": cue_index,
                "start": start_seconds,
                "end": end_seconds,
                "duration": max(0.0, end_seconds - start_seconds),
                "start_timecode": _format_seconds(start_seconds),
                "end_timecode": _format_seconds(end_seconds),
                "text": text,
                "line_count": len(normalized_lines),
                "char_count": len(text.replace("\n", " ").strip()),
                "word_count": len(re.findall(r"\b\w+\b", text)),
                "source_cue": f"cue {cue_index}",
            }
        )
    return subtitles


def _run_command(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def _probe_video_manifest(video_path: Path) -> dict[str, Any]:
    result = _run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "ffprobe failed")
    payload = json.loads(result.stdout or "{}")
    streams = payload.get("streams", [])
    format_payload = payload.get("format", {})
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})
    duration_value = format_payload.get("duration") or video_stream.get("duration") or audio_stream.get("duration") or 0
    try:
        duration_seconds = float(duration_value)
    except (TypeError, ValueError):
        duration_seconds = 0.0
    return {
        "video_path": str(video_path),
        "duration_seconds": duration_seconds,
        "format_name": format_payload.get("format_name", ""),
        "size_bytes": int(format_payload.get("size", 0) or 0),
        "video_stream": {
            "codec_name": video_stream.get("codec_name", ""),
            "width": int(video_stream.get("width", 0) or 0),
            "height": int(video_stream.get("height", 0) or 0),
            "avg_frame_rate": video_stream.get("avg_frame_rate", ""),
        },
        "audio_stream": {
            "codec_name": audio_stream.get("codec_name", ""),
            "sample_rate": audio_stream.get("sample_rate", ""),
            "channels": int(audio_stream.get("channels", 0) or 0),
        },
        "raw": payload,
    }


def _build_sample_points(
    subtitles: list[dict[str, Any]],
    duration_seconds: float,
    interval_seconds: int,
    max_midpoints: int,
) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    seen_keys: set[int] = set()

    for subtitle in subtitles[:max_midpoints]:
        duration = float(subtitle.get("duration", 0.0) or 0.0)
        timestamp = float(subtitle.get("start", 0.0) or 0.0) if duration <= 1.2 else (float(subtitle.get("start", 0.0)) + duration / 2)
        key = int(round(timestamp * 10))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        samples.append(
            {
                "timestamp": round(timestamp, 3),
                "timestamp_label": _format_seconds(timestamp),
                "cue_index": subtitle.get("cue_index"),
                "sample_type": "subtitle-start" if duration <= 1.2 else "subtitle-midpoint",
            }
        )

    if duration_seconds > 0 and interval_seconds > 0:
        current = 0.0
        while current < duration_seconds:
            key = int(round(current * 10))
            if key not in seen_keys:
                samples.append(
                    {
                        "timestamp": round(current, 3),
                        "timestamp_label": _format_seconds(current),
                        "cue_index": None,
                        "sample_type": "interval",
                    }
                )
                seen_keys.add(key)
            current += interval_seconds
    return sorted(samples, key=lambda item: float(item["timestamp"]))


def _extract_frame_samples(video_path: Path, frames_dir: Path, sample_points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[dict[str, Any]] = []
    for index, sample in enumerate(sample_points, start=1):
        filename = f"frame_{index:04d}_{str(sample['timestamp_label']).replace(':', '-').replace('.', '_')}.png"
        output_path = frames_dir / filename
        result = _run_command(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(sample["timestamp"]),
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                str(output_path),
            ]
        )
        record = dict(sample)
        record["image_path"] = str(output_path)
        record["status"] = "ok" if result.returncode == 0 and output_path.exists() else "failed"
        if result.returncode != 0:
            record["warning"] = result.stderr.strip() or result.stdout.strip() or "ffmpeg frame extraction failed"
        extracted.append(record)
    return extracted


def _extract_audio_track(video_path: Path, output_path: Path) -> tuple[bool, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = _run_command(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(output_path),
        ]
    )
    if result.returncode != 0 or not output_path.exists():
        return False, result.stderr.strip() or result.stdout.strip() or "ffmpeg audio extraction failed"
    return True, ""


def _subtitle_text_source(subtitle_path: Path, subtitles: list[dict[str, Any]]) -> ContentSource:
    return {
        "kind": "subtitle",
        "uri": str(subtitle_path),
        "display_name": subtitle_path.name,
        "format": "srt",
        "extracted_text": "\n".join(
            f"Cue {item['cue_index']} | {item['start_timecode']} -> {item['end_timecode']}: {item['text']}"
            for item in subtitles
            if item.get("text")
        ),
        "image_paths": [],
        "location_hints": [f"cue {item['cue_index']}" for item in subtitles[:50]],
        "extraction_mode": "vqc-srt-parser",
        "warnings": [],
        "metadata": {"cue_count": len(subtitles)},
    }


def _asr_text_source(video_path: Path, transcript: dict[str, Any], warnings: list[str]) -> ContentSource:
    segments = transcript.get("segments", []) if isinstance(transcript, dict) else []
    lines = []
    for index, segment in enumerate(segments, start=1):
        segment_text = _normalize_whitespace(str(segment.get("text", "")))
        if not segment_text:
            continue
        lines.append(
            f"ASR Segment {index} | {_format_seconds(float(segment.get('start', 0.0) or 0.0))} -> "
            f"{_format_seconds(float(segment.get('end', 0.0) or 0.0))}: {segment_text}"
        )
    return {
        "kind": "audio",
        "uri": str(video_path),
        "display_name": f"{video_path.name} ASR Transcript",
        "format": "asr",
        "extracted_text": "\n".join(lines),
        "image_paths": [],
        "location_hints": [f"segment {index}" for index, _segment in enumerate(segments[:50], start=1)],
        "extraction_mode": "openai-transcription",
        "warnings": warnings,
        "metadata": {"segment_count": len(segments)},
    }


def _collector_summary_source(video_probe: dict[str, Any]) -> ContentSource:
    summary_lines = [
        f"Video QC collector status: {video_probe.get('status', 'unknown')}",
        f"Video file: {video_probe.get('video_path', 'missing')}",
        f"Subtitle file: {video_probe.get('subtitle_path', 'missing')}",
        f"ASR status: {video_probe.get('asr_status', 'not_attempted')}",
        f"Frame extraction status: {video_probe.get('frame_extraction_status', 'not_attempted')}",
        f"Subtitle cues parsed: {len(video_probe.get('subtitles', []))}",
        f"ASR segments: {len(video_probe.get('asr_segments', []))}",
        f"Frame samples: {len(video_probe.get('frame_samples', []))}",
    ]
    warnings = list(video_probe.get("warnings", []))
    if warnings:
        summary_lines.append("Warnings:\n" + "\n".join(f"- {warning}" for warning in warnings))
    return {
        "kind": "video",
        "uri": str(video_probe.get("video_path", "")),
        "display_name": "VQC Collector Summary",
        "format": "video-bundle",
        "extracted_text": "\n".join(summary_lines),
        "image_paths": [item["image_path"] for item in video_probe.get("frame_samples", []) if item.get("status") == "ok"],
        "location_hints": ["video collector", "subtitle cues", "frame samples", "audio sync"],
        "extraction_mode": "vqc-collector",
        "warnings": warnings,
        "metadata": {
            "asr_status": video_probe.get("asr_status", ""),
            "frame_sample_count": len(video_probe.get("frame_samples", [])),
        },
    }


def prepare_vqc_state(state: AgentState) -> AgentState:
    project_root = state["project_root"]
    output_dir_value = state.get("output_dir", "")
    output_dir = Path(output_dir_value) if output_dir_value else None
    if output_dir is None:
        summary = "VQC collector skipped because no output directory was available."
        log_communication(project_root, "VQC Collector", "Workflow", summary)
        return {
            "messages": [],
            "findings": [],
            "sender": "",
            "next_agents": state.get("next_agents", []),
            "routing_reason": summary,
            "collector_summary": summary,
        }

    artifacts_dir = output_dir / "artifacts"
    frames_dir = artifacts_dir / "frames"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    request_text = state.get("raw_text", "") or state.get("user_text", "")
    video_candidates = _extract_paths(VIDEO_PATH_PATTERN, request_text)
    subtitle_candidates = _extract_paths(SRT_PATH_PATTERN, request_text)
    video_path = _resolve_local_path(video_candidates[0], project_root) if video_candidates else None
    subtitle_path = _resolve_local_path(subtitle_candidates[0], project_root) if subtitle_candidates else None

    ffmpeg_available = shutil.which("ffmpeg") is not None
    ffprobe_available = shutil.which("ffprobe") is not None
    warnings: list[str] = []
    status = "ready"

    if SEGMENT_HINT_PATTERN.search(request_text):
        warnings.append("Segment targeting is not implemented in V1, so the collector still reviewed the whole file.")

    if not video_path:
        warnings.append("No local video path (.mp4/.mov/.mkv/.webm) was detected in the request.")
        status = "missing-video"
    elif not video_path.exists():
        warnings.append(f"Referenced local video file does not exist: {video_path}")
        status = "missing-video"

    if not subtitle_path:
        warnings.append("No local subtitle (.srt) file was detected in the request.")
        if status == "ready":
            status = "missing-subtitle"
    elif not subtitle_path.exists():
        warnings.append(f"Referenced local subtitle file does not exist: {subtitle_path}")
        if status == "ready":
            status = "missing-subtitle"

    if not ffmpeg_available:
        warnings.append("ffmpeg is not available in PATH, so audio extraction and frame sampling could not run.")
    if not ffprobe_available:
        warnings.append("ffprobe is not available in PATH, so video metadata probing could not run.")

    subtitles: list[dict[str, Any]] = []
    if subtitle_path and subtitle_path.exists():
        subtitles = _parse_srt_file(subtitle_path)

    manifest: dict[str, Any] = {
        "video_path": str(video_path) if video_path else "",
        "subtitle_path": str(subtitle_path) if subtitle_path else "",
        "ffmpeg_available": ffmpeg_available,
        "ffprobe_available": ffprobe_available,
        "status": status,
        "warnings": warnings,
    }
    if video_path and video_path.exists() and ffprobe_available:
        try:
            manifest = {**manifest, **_probe_video_manifest(video_path)}
        except Exception as exc:
            warnings.append(f"Video metadata probing failed: {exc}")
            manifest["probe_error"] = str(exc)

    frame_samples: list[dict[str, Any]] = []
    if video_path and video_path.exists() and ffmpeg_available:
        sample_points = _build_sample_points(
            subtitles=subtitles,
            duration_seconds=float(manifest.get("duration_seconds", 0.0) or 0.0),
            interval_seconds=max(1, int(state["config"].video_frame_interval_seconds)),
            max_midpoints=max(1, int(state["config"].video_max_midpoint_frames_per_run)),
        )
        frame_samples = _extract_frame_samples(video_path, frames_dir, sample_points)

    frame_extraction_status = "ok" if any(item.get("status") == "ok" for item in frame_samples) else "skipped"
    if frame_samples and all(item.get("status") != "ok" for item in frame_samples):
        frame_extraction_status = "failed"

    asr_transcript: dict[str, Any] = {"segments": []}
    asr_warnings: list[str] = []
    asr_status = "not_attempted"
    audio_artifact_path = artifacts_dir / "audio_track.wav"
    if not state["config"].openai_api_key:
        asr_status = "missing-openai-key"
        asr_warnings.append("OPENAI_API_KEY is not configured, so ASR-based subtitle/audio sync was skipped.")
    elif not video_path or not video_path.exists():
        asr_status = "missing-video"
    elif not ffmpeg_available:
        asr_status = "missing-ffmpeg"
    else:
        success, error_message = _extract_audio_track(video_path, audio_artifact_path)
        if not success:
            asr_status = "audio-extraction-failed"
            asr_warnings.append(error_message)
        else:
            try:
                asr_transcript = invoke_openai_transcription(
                    model=state["config"].video_asr_model,
                    api_key=state["config"].openai_api_key,
                    audio_path=audio_artifact_path,
                )
                asr_status = "ok"
            except Exception as exc:
                asr_status = "transcription-failed"
                asr_warnings.append(str(exc))

    warnings.extend(asr_warnings)

    _safe_write_json(artifacts_dir / "video_manifest.json", manifest)
    _safe_write_json(artifacts_dir / "subtitles.json", subtitles)
    _safe_write_json(artifacts_dir / "frame_index.json", frame_samples)
    _safe_write_json(
        artifacts_dir / "asr_transcript.json",
        {
            "status": asr_status,
            "warnings": asr_warnings,
            **(asr_transcript if isinstance(asr_transcript, dict) else {"raw": asr_transcript}),
        },
    )

    content_sources = list(state.get("content_sources", []))
    if subtitle_path and subtitle_path.exists():
        content_sources.append(_subtitle_text_source(subtitle_path, subtitles))
    if asr_status == "ok" and video_path:
        content_sources.append(_asr_text_source(video_path, asr_transcript, asr_warnings))

    video_probe = {
        "status": status,
        "video_path": str(video_path) if video_path else "",
        "subtitle_path": str(subtitle_path) if subtitle_path else "",
        "warnings": warnings,
        "manifest": manifest,
        "subtitles": subtitles,
        "frame_samples": frame_samples,
        "frame_extraction_status": frame_extraction_status,
        "asr_status": asr_status,
        "asr_segments": list(asr_transcript.get("segments", [])) if isinstance(asr_transcript, dict) else [],
        "artifacts": {
            "video_manifest": str(artifacts_dir / "video_manifest.json"),
            "subtitles": str(artifacts_dir / "subtitles.json"),
            "asr_transcript": str(artifacts_dir / "asr_transcript.json"),
            "frame_index": str(artifacts_dir / "frame_index.json"),
            "frames_dir": str(frames_dir),
        },
    }
    content_sources.append(_collector_summary_source(video_probe))

    image_paths = list(
        dict.fromkeys(
            [
                *state.get("image_paths", []),
                *[item["image_path"] for item in frame_samples if item.get("status") == "ok"],
            ]
        )
    )
    resolved_content_text = build_resolved_content_text(content_sources, state.get("user_text", ""))
    summary = (
        f"VQC collector prepared shared video evidence: status={status}, "
        f"subtitle_cues={len(subtitles)}, frame_samples={len(frame_samples)}, asr_status={asr_status}."
    )
    log_communication(project_root, "VQC Collector", "Workflow", summary)

    return {
        "messages": [],
        "findings": [],
        "sender": "",
        "next_agents": state.get("next_agents", []),
        "routing_reason": summary,
        "collector_summary": summary,
        "content_sources": content_sources,
        "image_paths": image_paths,
        "resolved_content_text": resolved_content_text,
        "video_probe": video_probe,
    }
