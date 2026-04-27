# Claude Project Guide

## What this repo is
Cong Xuong Agent QC is a Python multi-agent QA factory for e-learning review. It produces bilingual QA reports (`English` + `Vietnamese`) for:

- `id`: instructional design, browser flow, quiz logic, navigation, accessibility, on-screen text
- `content`: storyboard copy, subtitles, grammar, spelling, British English, terminology consistency
- `graphic`: Figma, screenshot, and rendered-artifact visual QA for layout, spacing, hierarchy, readability, and WCAG 2.2 visual risks
- `video`: local learning video QC for `video + .srt` artifacts, sampled frames, subtitle quality, and subtitle/audio sync
- `reflection`: writes reusable lessons back into the knowledge base

The repo has two entry surfaces:

- CLI: `main.py`
- FastAPI web API: `api/app.py`

There is also a static frontend in `web/`.

For Codex chat workflows, the repo also ships repo-local skills under `.agents/skills`:

- `cqc`
- `vqc`
- `id-qc`
- `fg-qc`
- `cg-qc`
- `qc-reflect`
- `cleanup`
- `checkgit`
- `upgit`

## High-level flow
- `main.py` supports `/id`, `/cg`, `/fg`, `/cqc`, `/vqc`, `/reflect`, `/cleanup`, and `/upgit`
- In Codex chat, the same cleanup utility can be invoked via `$cleanup`
- In Codex chat, the git freshness/device-swap status utility can be invoked via `$checkgit`
- In Codex chat, the git sync utility can be invoked via `$upgit`
- In Codex chat, collaborative course QC should use `$cqc` when the request is specifically about one Articulate/Rise course flow
- In Codex chat, local video QC should use `$vqc` when the request is about one local learning video plus subtitle artifact
- `/upgit` skips runtime/generated paths such as `docs/communication.md` and `outputs/` by default, and auto-generates a commit message when none is provided
- Requests may skip the router via explicit commands or auto-detect
- `core/graph.py` resolves content sources, prepares shared CQC browser evidence when `flow_type == "cqc"`, prepares shared VQC local-video evidence when `flow_type == "vqc"`, runs specialist agents, then runs reflection
- Every QA run writes a fresh bundle to `outputs/<timestamp>_<slug>_<id>/`
- `core/reporting.py` owns bilingual report generation for `id`, `content`, `graphic`, and `video`
- `report.md` and generated/copied artifacts should live in the same output bundle
- Reflection v2 can route learning into:
  - `knowledge/general/human_feedback_lessons.md`
  - `knowledge/general/system_lessons.md`
  - `knowledge/general/process_facts.md`
  - `knowledge/procedures/procedure_candidates.md`
  - `knowledge/backlog/reflection_followups.md`

## Key routing rules
- Local `.pdf`, `.csv`, `.docx` references route to `content`
- Figma links route to `graphic`, or `content + graphic` when the prompt is clearly about storyboard/copy/text
- Images, screenshots, rendered PDF previews, and exported design frames route to `graphic`
- Articulate, Rise, Storyline, and SCORM-style prompts route to `id`
- Explicit course-level collaborative review requests should route to `/cqc` or `$cqc`
- Explicit local-video review requests with a video path plus `.srt` should route to `/vqc` or `$vqc`
- If the router LLM is disabled, the repo falls back to heuristics

## Source handling rules
- Supported document ingestion for content QA: `.pdf`, `.csv`, `.docx`
- Raw Figma links are unresolved for content review unless content has already been pre-resolved into `content_sources`
- Graphic review can inspect screenshots directly; link-only Figma review is possible but weaker without rendered evidence
- If Figma MCP is rate-limited or unavailable, prefer exported screenshots or locally rendered artifacts over claiming direct frame inspection
- Web uploads are persisted under `.web-runtime/jobs/<job_id>/inputs/...`
- Final evidence and reports live under `outputs/...`
- `/vqc` keeps `report.md` plus sibling video artifacts in one output bundle under `outputs/...`

## Important files
- `core/config.py`: env loading and model/provider mapping
- `core/graph.py`: orchestration
- `core/content_sources.py`: document and Figma source resolution
- `core/reporting.py`: bilingual report generation and Vietnamese translation orchestration
- `core/llm.py`: provider invocation, multimodal handling, and HTTP fallback when LangChain adapters are missing
- `agents/`: router and specialist agents
- `api/service.py`: background job execution for web runs
- `tests/`: `unittest` coverage for workflow and web API
- `AGENTS.md`: canonical repo-level operating contract for Codex

## Runbook
- Install deps: `pip install -r requirements.txt`
- Create `.env` from `.env.example`
- Required live keys: `GROQ_API_KEY`, `GOOGLE_API_KEY`
- CLI example:
  - `python main.py --text "/cg Review 'C:/path/storyboard.csv' for grammar and terminology"`
- API local:
  - `uvicorn api.app:app --reload`
- Tests:
  - `python -m unittest discover -s tests`

## Model/config notes
- Default router/content/id provider: `groq`
- Default graphic provider: `groq` vision model
- Default reflection provider: `google`
- Default VQC ASR backend: OpenAI transcription via `gpt-4o-mini-transcribe`
- `test-*` and `fake-*` API keys intentionally disable live LLM calls and trigger fallback logic in tests
- If the current interpreter does not have `langchain-groq` or `langchain-google-genai` installed, `core/llm.py` falls back to direct HTTP calls for Groq and Gemini so live text/report translation can still run

## Working conventions
- Keep runtime web files only in `web/`; do not move frontend assets into `docs/`
- Reports must stay bilingual in a single `report.md`
- `id`, `cg`, `fg`, and `vqc` runs should always export `report.md`, even when the review is partial or blocked
- `report.md` and all generated/copied evidence for the same QC pass should stay in one output bundle
- `docs/communication.md` is an append-only runtime log; treat it as generated operational history
- Reflection/knowledge behavior now uses scoped retrieval. Knowledge load order is:
  1. `human_feedback_lessons.md`
  2. `system_lessons.md`
  3. `process_facts.md`
  4. `procedure_candidates.md`
  5. `wcag_global.md`
  6. `project_x_req.md`
- `reflection_followups.md` is draft/backlog memory and should not be injected into specialist prompts
- Human feedback should stay concise, reusable, and operational; avoid duplicating near-identical rules
- For Articulate/Rise page-level review, test all visible interactives on the page and inspect all newly revealed text before claiming coverage
- For quizzes, prioritize testing correct and incorrect answer paths, learner-facing explanations, grammar/spelling, and post-quiz flow; do not over-index on pre-submit states
- Every participating specialist should still contribute a result summary even when no major defect is found; the coordinating flow/report then merges that into the final `report.md`
- Save edited text files as UTF-8

## Coding agent behavior
- State assumptions before making non-trivial code changes, especially when scope, evidence, or runtime dependencies are ambiguous
- Prefer the smallest implementation that satisfies the requested QC behavior; avoid speculative abstractions or future-facing options unless the current task needs them
- Keep edits surgical: touch only files needed for the requested change, preserve existing style, and do not refactor adjacent code opportunistically
- Define verification before or during implementation; for bug fixes, prefer a reproducing test or artifact check, and for QC-flow changes, verify the expected report or JSON artifact output
- If a change cannot be fully verified because of missing local tooling, record the limitation explicitly

## Current caveats worth knowing
- The web API exposes `id`, `cg`, and `fg` modes directly; it does not expose the free router path as a user-facing mode
- Auth helpers exist in `api/auth.py`, but the current web UI is effectively running in no-auth mode
- Reflection skips automatic lesson generation when fewer than 2 findings are produced
- Reflection v2 uses metadata-backed entries internally, but legacy bullet-style knowledge files are still supported and may coexist during migration
- `cleanup_project()` removes cache/temp files but preserves valid output bundle directories
- Vietnamese report translation prefers live provider translation; if all translation-capable providers fail, the Vietnamese section should explicitly say translation was unavailable rather than silently repeating English
- The local shell interpreter can differ from the repo's intended environment; when that happens, missing optional packages may surface only in this shell even though `requirements.txt` is correct
- Figma MCP access depends on plan, seat, and quota. A public Figma link does not guarantee that the current runtime can inspect the frame live.
