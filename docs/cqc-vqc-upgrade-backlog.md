# CQC and VQC Upgrade Backlog

Generated from review of the current CQC and VQC reports and runtime code.

## Current Evidence Reviewed

- CQC report: `outputs/20260423_140610_cqc-focus-testing-tu-dau-cho-den-het-chapter-1_d8ff0d/report.md`
- VQC report: `outputs/20260425_103252_vqc-video-d-downloads-approving-rejecting-succes_2b64c5/report.md`
- Runtime files: `core/cqc.py`, `core/vqc.py`, `core/browser.py`, `core/wcag.py`, `agents/id_agent.py`, `agents/graphic_agent.py`, `agents/content_agent.py`, `agents/video_agent.py`

## High-Level Summary

CQC already has useful shared browser evidence and can catch course-state issues such as quiz feedback appearing too early. Its main gap is breadth and traceability: it needs stronger traversal coverage, clearer coverage maps, keyboard/focus testing, and deeper automated accessibility checks.

VQC currently has the right collector-first structure, but it depends heavily on local runtime tools. When `ffmpeg`, `ffprobe`, OCR dependencies, or ASR configuration are missing, the flow collapses into subtitle-text-only review and cannot meaningfully inspect frames, audio, or subtitle-to-audio sync.

## CQC Gaps

### 1. Browser Traversal Coverage Is Too Shallow

Current traversal is capped in `core/browser.py`:

- `max_states = 8`
- `max_depth = 3`
- `max_actions_per_state = 4`

This is often too small for Rise/Storyline lessons with tabs, accordions, flashcards, carousels, sorting activities, matching activities, and quiz branches.

Upgrade proposal:

- Make traversal limits configurable through environment variables or `AppConfig`.
- Add scope-aware traversal, for example chapter-only, section-only, quiz-only, or all-reveals.
- Track unclicked remaining actionables per state.
- Prefer exhaustive traversal for reveal components before moving to next lesson.

### 2. Missing Coverage Map

Reports currently describe coverage in prose, but they do not export a structured coverage map.

Upgrade proposal:

- Generate `coverage_map.json` in the output bundle.
- Include:
  - visited states
  - screenshots per state
  - clicked actions
  - unclicked actions
  - quiz questions discovered
  - correct/wrong paths attempted
  - blocked or skipped states
- Add a short coverage table to `report.md`.

### 3. Keyboard and Focus Testing Not Implemented

CQC currently relies on click-driven Playwright traversal. It does not verify keyboard-only operation, tab order, focus visibility, Enter/Space activation, or focus traps.

Upgrade proposal:

- Add a keyboard probe mode:
  - press `Tab` through visible controls
  - capture active element role/name
  - capture focus outline visibility where possible
  - test Enter/Space on focused controls
- Emit WCAG findings for focus order, focus visibility, inaccessible controls, and keyboard traps.

### 4. WCAG Automation Is Still Minimal

Current `core.wcag` covers:

- screenshot contrast through OCR/image sampling when dependencies are available
- missing accessible names from browser probe actionables

It does not yet run axe-core or ACT-style automated rule checks.

Upgrade proposal:

- Add an axe-core runner inside the Playwright probe.
- Save `axe_results.json` per visited state.
- Convert violations into findings with WCAG criterion, node target, impact, and source state.
- Keep axe `incomplete` results as `Info` or manual-review candidates.

### 5. Graphic Review in CQC Is Too Thin

The reviewed CQC report had many browser screenshots, but the graphic finding was only a coverage note. This means the graphic agent is not yet extracting enough value from rendered course evidence.

Upgrade proposal:

- Add screenshot-level visual checks:
  - tiny text risk
  - contrast risk
  - overflow or clipped content
  - crowded UI
  - weak visual hierarchy
  - inconsistent button/control styling
- Run desktop and mobile viewport variants when responsive behavior is in scope.
- Store visual findings with screenshot filename and state label.

### 6. Console Errors Are Collected But Not Interpreted Deeply

Browser probe captures console summaries, but findings only mention console output when it is surfaced by fallback logic.

Upgrade proposal:

- Parse console logs into categories:
  - asset load failures
  - JavaScript runtime errors
  - blocked resources
  - media errors
  - accessibility-related warnings
- Only raise findings when console issues map to learner-facing risk or broken functionality.

## VQC Gaps

### 1. Runtime Dependencies Block Full Review

The current VQC report shows:

- `ffmpeg` unavailable
- `ffprobe` unavailable
- `OPENAI_API_KEY` missing
- frame samples: `0`
- ASR segments: `0`

This prevents frame sampling, video metadata probing, audio extraction, and subtitle-to-audio sync review.

Upgrade proposal:

- Add a setup doctor command or helper:
  - check `ffmpeg`
  - check `ffprobe`
  - check `tesseract`
  - check Python image/OCR dependencies
  - check ASR provider configuration
- Report dependency status once in a dedicated Technical Limitations section rather than repeating it across agents.

### 2. Graphic-Agent Fallback Is Not VQC-Aware

When frame extraction fails, Graphic-Agent currently reports that no Figma link or screenshot was supplied. For VQC, this is misleading because the intended visual evidence is extracted video frames.

Upgrade proposal:

- Make Graphic-Agent detect `flow_type == "vqc"`.
- If no frames are available, emit a VQC-specific limitation:
  - "No video frame samples were available because frame extraction did not run."
- If frames are available, review them as sampled video frames, not generic screenshots or Figma frames.

### 3. Subtitle QC Needs More Deterministic Checks

Current subtitle checks cover reading speed and some basic line break heuristics.

Upgrade proposal:

- Add checks for:
  - overlapping cues
  - very short cue duration
  - very long cue duration
  - excessive gap between speech/subtitle blocks when ASR exists
  - max two-line rule
  - max characters per line
  - subtitle coverage percentage
  - missing terminal punctuation where style requires it
  - inconsistent speaker labels or bracketed sound cues
- Export a subtitle metrics summary to `subtitles_metrics.json`.

### 4. ASR Alignment Is Too Basic

Video-Agent currently compares overlapping subtitle cues with ASR segments using text similarity.

Upgrade proposal:

- Add alignment metrics:
  - cue start drift
  - cue end drift
  - nearest ASR segment distance
  - uncaptioned speech duration
  - captioned silence duration
  - confidence where ASR provider supports it
- Summarize alignment health before listing individual findings.

### 5. No Audio Quality Review

VQC does not currently check audio loudness, silence, clipping, channel count, or sample rate quality beyond metadata.

Upgrade proposal:

- Use `ffmpeg`/`ffprobe` to collect:
  - duration
  - codec
  - channel count
  - sample rate
  - integrated loudness if available
  - peak level/clipping risk
  - long silence segments
- Emit findings for missing audio, long silence where narration is expected, clipping, and unusual channel/sample-rate configuration.

### 6. Frame Sampling Needs More Intelligence

Current sampling is based on interval and subtitle midpoint logic.

Upgrade proposal:

- Sample:
  - first frame after intro
  - subtitle midpoint frames
  - slide/scene transition frames
  - frames around detected visual changes
  - final frame
- Add perceptual hash or image-difference detection to avoid many duplicate frames.
- Save a frame contact sheet for faster human review.

### 7. No OCR/Text Review From Video Frames

If a video contains UI text or slide text, VQC currently relies on subtitles and sampled-frame visual review, not OCR of on-screen text.

Upgrade proposal:

- Run OCR on sampled frames when `tesseract` is available.
- Add extracted frame text as `content_sources`.
- Let Content-Agent check on-screen text for spelling, grammar, terminology, and British English consistency.
- Include frame timestamp and frame filename in evidence.

### 8. No Motion or Cursor Usability Checks

VQC does not inspect whether cursor movement, clicks, zooms, or UI changes are understandable.

Upgrade proposal:

- Detect cursor visibility in frames if feasible.
- Add manual-review heuristics for:
  - cursor too small
  - action occurs before narration/subtitle explains it
  - screen changes too quickly
  - zoom level makes UI text unreadable
- Store these as visual/video review findings, not subtitle findings.

## Cross-Flow Gaps

### 1. Technical Limitations Are Repeated Too Often

Current reports can repeat the same missing dependency in Content-Agent, Graphic-Agent, and Video-Agent findings.

Upgrade proposal:

- Add a shared `limitations` field in `AgentState`.
- Render limitations in a dedicated report section.
- Specialists should reference limitations only when they materially affect their scope.

### 2. Reporting Translation Encoding Needs Attention

Some Vietnamese report output shows mojibake characters. This weakens the bilingual report requirement.

Upgrade proposal:

- Audit translation and report-writing encoding end to end.
- Add tests that assert Vietnamese diacritics survive in `report.md`.
- Ensure source strings in `core/reporting.py` are stored as UTF-8.

### 3. Findings Need Stronger Source Coordinates

Reports are better when every finding points to a concrete artifact.

Upgrade proposal:

- Standardize evidence coordinates:
  - CQC: state label, page URL, screenshot filename, snapshot filename
  - VQC: cue index, timestamp range, frame filename, ASR segment index
- Add optional machine-readable metadata to findings in a future schema version.

### 4. Agent Overlap Needs Deduplication

WCAG and dependency findings can be emitted by multiple agents.

Upgrade proposal:

- Add semantic deduplication before reporting.
- Prefer ownership rules:
  - ID owns interaction, quiz, keyboard, focus, accessible names
  - Graphic owns visual contrast, layout, frame readability
  - Content owns text/subtitle wording
  - Video owns timing, audio, frame/audio/video technical integrity

## Recommended Implementation Order

1. Add dependency/setup doctor for VQC and WCAG runtime tools.
2. Fix Vietnamese report encoding.
3. Make Graphic-Agent VQC-aware when frame extraction is unavailable.
4. Add CQC coverage map output.
5. Make CQC traversal limits configurable.
6. Add axe-core or equivalent automated accessibility scan for CQC.
7. Add keyboard/focus probe for CQC.
8. Expand deterministic subtitle metrics for VQC.
9. Add ASR alignment metrics beyond simple overlap similarity.
10. Add audio quality metrics from `ffmpeg`/`ffprobe`.
11. Add frame OCR and frame contact sheet for VQC.
12. Add cross-agent limitation handling and deduplication.

## Notes For Future Implementation

- Keep collector-first architecture. CQC and VQC should gather shared evidence once, then pass it to specialists.
- Do not let specialists claim evidence they did not access.
- Store all artifacts in the same output bundle as `report.md`.
- Prefer deterministic checks before LLM judgement.
- Keep suggestions clearly labeled as `Suggestion`, and keep technical limitations separate from confirmed learner-facing defects.
