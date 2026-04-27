## Project Overview

This repository is a multi-agent QC factory for e-learning review. The working modes are:

- `id`: instructional design QA for browser-like course flows, interactions, quiz logic, navigation, accessibility, and learner-facing on-screen text
- `graphic`: visual QA for Figma links, screenshots, and rendered design artifacts, including layout, spacing, hierarchy, readability, and WCAG 2.2 visual risks
- `content`: content QA for storyboard copy, subtitles, grammar, spelling, British English, terminology, and learner-facing clarity
- `video`: local learning video QA for `video + .srt` bundles, sampled frames, subtitle quality, and subtitle-to-audio sync
- `reflect`: lesson capture from feedback or findings so future QC passes improve over time

Reflection currently uses a `reflect v2` style durable-learning loop:

- manual feedback is stored as promoted human rules
- automatic reflection routes reusable learning into `system lessons`, `process facts`, `procedure candidates`, or `follow-up drafts`
- specialist agents receive scoped knowledge context rather than a full unfiltered knowledge dump

The runtime entrypoints in this repo are:

- CLI in `main.py`
- FastAPI backend in `api/app.py`
- Specialist agents in `agents/`
- Repo-local Codex workflows in `.agents/skills/`

Every QC run for `id`, `graphic`, `content`, or `video` must end in a bilingual `report.md` bundle under `outputs/`.

## Command And Mode Mapping

The canonical mode mapping is:

- `/id` -> `id`
- `/fg` -> `graphic`
- `/cg` -> `content`
- `/cqc` -> collaborative course QC flow using shared browser evidence for `id` + `content` + `graphic`
- `/vqc` -> local video QC flow using shared collector evidence for `content` + `graphic` + `video`
- `/reflect` -> `reflect`

The project utility mapping is:

- `/cleanup` -> cleanup cache and temp files safely
- `/checkgit` -> check whether the current checkout is up to date with the connected GitHub upstream and summarize recent project implementation activity
- `/upgit` -> cleanup, commit current changes, and push to git remote

Default `/upgit` behavior:

- runs cleanup first
- skips runtime/generated paths such as `docs/communication.md` and `outputs/` by default
- auto-generates a commit message when none is provided
- pushes only the remaining relevant staged changes

When working in Codex chat, prefer the workflow skills:

- `$cqc`
- `$vqc`
- `$id-qc`
- `$fg-qc`
- `$cg-qc`
- `$qc-reflect`
- `$cleanup`
- `$checkgit`
- `$upgit`

Use explicit workflow skills when the user clearly knows the target mode. If the request is ambiguous, reason from source type and stated intent before choosing a workflow.

The current repo-local skill folders are:

- `.agents/skills/cqc`
- `.agents/skills/vqc`
- `.agents/skills/id-qc`
- `.agents/skills/fg-qc`
- `.agents/skills/cg-qc`
- `.agents/skills/qc-reflect`
- `.agents/skills/cleanup`
- `.agents/skills/checkgit`
- `.agents/skills/upgit`
- `.agents/skills/wcag-qc`

The active knowledge files are:

- `knowledge/general/human_feedback_lessons.md`
- `knowledge/general/system_lessons.md`
- `knowledge/general/process_facts.md`
- `knowledge/general/wcag_global.md`
- `knowledge/procedures/procedure_candidates.md`
- `knowledge/backlog/reflection_followups.md`
- `knowledge/requirements/project_x_req.md`

## Routing Rules

Apply these routing rules consistently:

- Explicit `/cqc` requests route to the collaborative course QC flow rather than a single specialist mode
- Explicit `/vqc` requests route to the local video QC flow rather than a single specialist mode
- Articulate, Rise, Storyline, SCORM, browser-flow, interaction, quiz, knowledge-check, navigation, and accessibility requests route to `id`
- Figma links, screenshots, and rendered design artifacts such as poster exports or PDF previews route to `graphic`
- Storyboard copy, subtitles, spelling, grammar, terminology, and document artifacts such as `pdf`, `csv`, and `docx` route to `content`
- Local video requests with `.mp4`, `.mov`, `.mkv`, `.webm`, `.srt`, subtitle timing, or audio sync intent route to `video` plus supporting `content` and `graphic` review when `/vqc` is requested
- Figma links that are explicitly about storyboard copy or text QA usually require both `graphic` and `content`, but `content` must only claim text coverage if the frame text is actually resolved
- Manual QA feedback and reusable process lessons route to `reflect`
- Cache, temp-file, or workspace cleanup requests route to the `cleanup` skill rather than a QA mode
- Git freshness, branch sync, device-swap status, or project implementation log requests route to the `checkgit` skill rather than a QA mode
- Git save, commit, push, or repository sync requests route to the `upgit` skill rather than a QA mode

If a request mixes multiple scopes, keep the boundaries explicit rather than collapsing everything into one vague review.

## Evidence Rules

Never pretend you inspected evidence that you did not actually access.

- If you used browser tooling such as Playwright, state what path or states were actually traversed
- If you used Figma tooling, state which frame, node, or screenshot evidence was actually reviewed
- If you used the video collector, state which local video file, subtitle file, sampled frames, and ASR status were actually available
- If a Figma link is present but no text was resolved for content review, say so plainly
- If only prompt text is available, treat the output as a constrained QA pass and disclose the limitation
- If the user asks for section-level ID review, only claim completion when all visible interactives, revealed text, and reachable knowledge-check states within scope were exercised
- For Articulate Storyline and Rise review, interact through all visible items on the page such as click-to-reveal, tabs, flashcards, markers, and similar reveal patterns before claiming the page is covered
- For course QA, `Content-Agent` should check learner-facing grammar, spelling, and British English consistency on the exercised states, while `ID-Agent` should judge whether the exercised content aligns with project intent and learning outcomes

When evidence is partial, report the missing coverage as part of the findings or summary.

## Reporting Rules

All reports and QC summaries should follow these expectations:

- Export a `report.md` file after every `id`, `graphic`, `content`, or `video` test pass, even when the review is partial or blocked
- Write the report under an `outputs/` bundle and mention the report path in the chat response when possible
- Keep findings actionable and grounded in evidence
- Use the supported severity levels: `Critical`, `Major`, `Minor`, `Suggestion`, `Info`
- Keep English and Vietnamese output together when generating project reports
- Use the shared reporting pipeline in `core/reporting.py` for bilingual output rather than hand-writing separate chat-only summaries
- Distinguish clearly between confirmed defects, review limitations, and follow-up suggestions
- Prefer honest coverage notes over overclaiming that a review is complete
- If a participating specialist finds no major issue, the specialist result should still say so explicitly rather than disappearing from the run summary
- Suggestions should remain clearly labeled as `Suggestion` rather than being mixed into confirmed defects

For content and graphic QA, preserve source cues such as page, row, paragraph, frame, screenshot, node, or section when the evidence supports them.

If the review is limited by missing tooling, partial screenshots, unresolved Figma text, blocked access, or rate-limited Figma MCP usage, the report must still be exported and must say exactly what was not verified.

Translation behavior:

- The report layer attempts Vietnamese translation through configured live providers
- If LangChain provider adapters are missing in the current interpreter, the LLM layer falls back to direct HTTP calls for Groq and Gemini
- If no translation-capable provider is usable, the Vietnamese section must explicitly say translation was unavailable instead of silently reusing English text

Artifact behavior:

- Every QC run should keep `report.md` and any generated or copied artifacts in the same output bundle
- Preferred structure is `outputs/<bundle>/report.md` plus `outputs/<bundle>/artifacts/...`
- Do not create a second output bundle for the same QC pass just because artifacts were prepared before report generation
- The coordinating flow or merger is responsible for synthesizing participating-agent outputs into the final `report.md`
- For `/vqc`, keep `video_manifest.json`, `subtitles.json`, `asr_transcript.json`, `frame_index.json`, and extracted frames in the same output bundle as `report.md`

## Tooling Guidance

This repo may be used in environments with or without plugins and MCP tools.

- If browser tooling is available, use it for `id` work that requires real interaction coverage
- For `video` QA, V1 uses local artifact collection with `ffmpeg`/`ffprobe`, subtitle parsing, sampled frames, and optional OpenAI ASR rather than browser playback or desktop automation
- If Figma tooling is available, use it for `graphic` work that needs live frame or node inspection
- If Figma MCP is unavailable, blocked, or rate-limited, fall back to exported screenshots, PDF renders, or other image artifacts rather than pretending the raw link was inspected successfully
- For `graphic` QA, rendered screenshots and exported frames are stronger evidence than a raw link alone
- For `content` QA, raw Figma links are unresolved unless text has already been pre-resolved into `content_sources`
- For document-based review, supported ingestion remains `pdf`, `csv`, and `docx`
- When screenshots or rendered previews are created during review, store them in the same output bundle as the final `report.md`
- For quiz review, prioritize correct-path and wrong-path learner outcomes, explanation quality, grammar/spelling, completeness, and post-quiz progression. Do not over-weight pre-submit states if they do not materially affect the learner experience.

## Implementation Discipline

Apply these rules when changing this repository:

- Prefer small, targeted edits that directly support the requested QC behavior
- Do not refactor unrelated agents, reporting, knowledge, or runtime artifact handling while fixing a narrow issue
- Before implementing larger changes, identify the expected verification artifact or test, such as `report.md`, a JSON artifact, a unit test, or a dependency check
- Avoid speculative abstractions; add shared helpers only when at least two agents or flows need the same behavior
- If local tooling prevents full verification, state the limitation rather than implying the change was fully tested
