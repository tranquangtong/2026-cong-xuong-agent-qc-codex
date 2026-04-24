from __future__ import annotations

import re
from difflib import SequenceMatcher

from core.state import AgentState, QAFinding
from core.utils import log_communication
from tools.text_tools import make_finding_id


def _build_finding(index: int, severity: str, area: str, evidence: str, impact: str, fix: str) -> QAFinding:
    return {
        "id": make_finding_id("V", index),
        "severity": severity,
        "area": area,
        "evidence": evidence,
        "impact": impact,
        "recommended_fix": fix,
        "source_agent": "video",
    }


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, _normalize_text(left), _normalize_text(right)).ratio()


def _overlapping_segments(cue: dict, segments: list[dict], padding_seconds: float = 0.0) -> list[dict]:
    start = float(cue.get("start", 0.0) or 0.0) - padding_seconds
    end = float(cue.get("end", 0.0) or 0.0) + padding_seconds
    return [
        segment
        for segment in segments
        if float(segment.get("end", 0.0) or 0.0) >= start and float(segment.get("start", 0.0) or 0.0) <= end
    ]


def run_video_review(state: AgentState) -> list[QAFinding]:
    video_probe = state.get("video_probe", {})
    warnings = list(video_probe.get("warnings", []))
    subtitles = list(video_probe.get("subtitles", []))
    segments = list(video_probe.get("asr_segments", []))

    findings: list[QAFinding] = []
    index = 1

    for warning in warnings:
        findings.append(
            _build_finding(
                index,
                "Info",
                "Video Coverage Limitation",
                warning,
                "Video QC coverage is reduced for part of the requested checks.",
                "Review the limitation, provide the missing artifact or dependency, and rerun `/vqc` for fuller coverage.",
            )
        )
        index += 1

    if str(video_probe.get("asr_status", "")).strip() != "ok":
        return findings or [
            _build_finding(
                1,
                "Info",
                "Video QA",
                "No ASR transcript was available for subtitle-to-audio alignment checks.",
                "Subtitle/audio sync issues could not be verified in this run.",
                "Configure `OPENAI_API_KEY` and `ffmpeg`, then rerun `/vqc` to enable audio-sync review.",
            )
        ]

    if not subtitles or not segments:
        return findings or [
            _build_finding(
                1,
                "Info",
                "Video QA",
                "The collector did not produce both subtitle cues and ASR segments.",
                "Subtitle/audio alignment checks could not be completed reliably.",
                "Provide both a valid `.srt` file and a transcribable local video file before rerunning `/vqc`.",
            )
        ]

    for cue in subtitles:
        cue_text = str(cue.get("text", "")).strip()
        if not cue_text:
            continue
        overlapping = _overlapping_segments(cue, segments)
        nearby = _overlapping_segments(cue, segments, padding_seconds=0.75)
        overlapping_text = " ".join(str(segment.get("text", "")).strip() for segment in overlapping).strip()
        nearby_text = " ".join(str(segment.get("text", "")).strip() for segment in nearby).strip()

        if overlapping:
            similarity = _similarity(cue_text, overlapping_text)
            if similarity < 0.45:
                findings.append(
                    _build_finding(
                        index,
                        "Major" if similarity < 0.25 else "Minor",
                        "Subtitle And Audio Mismatch",
                        (
                            f"Cue {cue.get('cue_index')} at {cue.get('start_timecode')} -> {cue.get('end_timecode')} "
                            f"does not align closely with overlapping ASR speech. "
                            f"Subtitle: '{cue_text}'. ASR: '{overlapping_text or '[empty]'}'. Similarity={similarity:.2f}."
                        ),
                        "Learners may read text that materially differs from the spoken narration.",
                        "Compare the narration against the subtitle cue and correct either the subtitle wording or the cue timing.",
                    )
                )
                index += 1
            continue

        if nearby_text:
            findings.append(
                _build_finding(
                    index,
                    "Minor",
                    "Subtitle Timing Drift",
                    (
                        f"Cue {cue.get('cue_index')} at {cue.get('start_timecode')} -> {cue.get('end_timecode')} "
                        f"had no overlapping ASR segment, but nearby speech was detected: '{nearby_text}'."
                    ),
                    "The subtitle may appear too early, too late, or may not map cleanly to the spoken line.",
                    "Retime the subtitle cue so it overlaps the intended speech more closely.",
                )
            )
            index += 1

    for segment_index, segment in enumerate(segments, start=1):
        start = float(segment.get("start", 0.0) or 0.0)
        end = float(segment.get("end", 0.0) or 0.0)
        overlaps = [
            cue
            for cue in subtitles
            if float(cue.get("end", 0.0) or 0.0) >= start and float(cue.get("start", 0.0) or 0.0) <= end
        ]
        segment_text = str(segment.get("text", "")).strip()
        if segment_text and not overlaps:
            findings.append(
                _build_finding(
                    index,
                    "Minor",
                    "Uncaptioned Speech Segment",
                    (
                        f"ASR segment {segment_index} at {start:.2f}s -> {end:.2f}s contained speech without an overlapping subtitle: "
                        f"'{segment_text}'."
                    ),
                    "Learners may hear narration that is not represented in the subtitle track.",
                    "Add or retime a subtitle cue so this spoken content is covered.",
                )
            )
            index += 1

    return findings or [
        _build_finding(
            1,
            "Info",
            "Video Alignment",
            "Subtitle cues and ASR segments did not produce an obvious mismatch under the V1 heuristics.",
            "No clear subtitle/audio sync defect was confirmed from the available evidence.",
            "If deeper motion or narration review is needed, extend the evidence pipeline with denser sampling or manual spot checks.",
        )
    ]


def video_node(state: AgentState) -> AgentState:
    findings = run_video_review(state)
    log_communication(
        state["project_root"],
        "Video Agent",
        "Workflow",
        f"Produced {len(findings)} finding(s) for video alignment review.",
    )
    return {
        "messages": [],
        "findings": findings,
        "sender": "video",
        "next_agents": ["FINISH"],
        "routing_reason": state.get("routing_reason", ""),
    }
