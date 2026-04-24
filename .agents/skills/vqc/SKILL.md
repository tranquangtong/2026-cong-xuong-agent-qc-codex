---
name: vqc
description: Run local video QC for learning-video artifacts by collecting shared evidence from a local video file plus `.srt`, then combining content, graphic, and subtitle-to-audio alignment review into one bilingual report.
---

Use this workflow for `learning video` products when the request is about one local video file plus subtitle evidence.

Follow this order:
1. Confirm the request includes a local video path and, ideally, a local `.srt` path.
2. Run the collector-first `/vqc` flow so video metadata, subtitle cues, sampled frames, and optional ASR are gathered once.
3. Reuse the same evidence for `content`, `graphic`, and `video` review.
4. Export one bilingual `report.md` in the same output bundle as the video artifacts.

Evidence rules:
- Review only the video file, subtitle file, sampled frames, and ASR evidence that were actually collected.
- If `ffmpeg`, `ffprobe`, `OPENAI_API_KEY`, the video file, or the `.srt` file is missing, keep the run going and report the limitation plainly.
- V1 is full-file only. If the prompt asks for one segment, note that segment targeting is not implemented yet and the run still covers the whole file.

V1 coverage:
- subtitle grammar, spelling, British English, terminology, and readability heuristics
- sampled-frame visual review
- subtitle-to-audio sync checks when ASR succeeds

Non-goals in V1:
- browser playback
- Google Drive fetch
- desktop player automation
- full motion-analysis beyond deterministic frame sampling
