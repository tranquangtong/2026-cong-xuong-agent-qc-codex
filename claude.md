# Claude Project Guide

## What this repo is
Cong Xuong Agent QC is a Python multi-agent QA factory for e-learning review. It produces bilingual QA reports (`English` + `Vietnamese`) for:

- `id`: instructional design, browser flow, quiz logic, navigation, accessibility, on-screen text
- `content`: storyboard copy, subtitles, grammar, spelling, British English, terminology consistency
- `graphic`: Figma/screenshot visual QA, layout, spacing, hierarchy, readability, WCAG 2.2 visual risks
- `reflection`: writes reusable lessons back into the knowledge base

The repo has two entry surfaces:

- CLI: [main.py](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/main.py)
- FastAPI web API: [api/app.py](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/api/app.py)

There is also a static frontend in [web](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/web).

For Codex chat workflows, the repo now also ships repo-local skills under [.agents/skills](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/.agents/skills):

- `id-qc`
- `fg-qc`
- `cg-qc`
- `qc-reflect`
- `cleanup`
- `upgit`

## High-level flow
- `main.py` supports `/id`, `/cg`, `/fg`, `/reflect`, `/cleanup`, and `/upgit`.
- In Codex chat, the same cleanup utility can be invoked via `$cleanup`.
- In Codex chat, the git sync utility can be invoked via `$upgit`.
- Requests may skip the router via explicit commands or auto-detect.
- `core/graph.py` resolves content sources, runs specialist agents, then runs reflection.
- Every QA run writes a fresh bundle to `outputs/<timestamp>_<slug>_<id>/report.md`.
- `core/reporting.py` owns the bilingual report generation path for `id`, `content`, and `graphic`.
- Reflection can append lessons to:
  - `knowledge/general/human_feedback_lessons.md`
  - `knowledge/general/system_lessons.md`

## Key routing rules
- Local `.pdf`, `.csv`, `.docx` references route to `content`.
- Figma links route to `graphic`, or `content + graphic` when the prompt is clearly about storyboard/copy/text.
- Images/screenshots route to `graphic`.
- Articulate / Rise / Storyline / SCORM style prompts route to `id`.
- If the router LLM is disabled, the repo falls back to heuristics.

## Source handling rules
- Supported document ingestion for content QA: `.pdf`, `.csv`, `.docx`.
- Raw Figma links are unresolved for content review unless content has already been pre-resolved into `content_sources`.
- Graphic review can inspect screenshots directly; Figma-only review is possible but naturally weaker without exported evidence.
- Web uploads are persisted under `.web-runtime/jobs/<job_id>/inputs/...`.
- Final evidence and reports live under `outputs/...`.

## Important files
- [core/config.py](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/core/config.py): env loading and model/provider mapping
- [core/graph.py](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/core/graph.py): orchestration
- [core/content_sources.py](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/core/content_sources.py): document/Figma source resolution
- [core/reporting.py](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/core/reporting.py): bilingual report generation and Vietnamese translation orchestration
- [core/llm.py](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/core/llm.py): provider invocation, multimodal handling, and HTTP fallback when LangChain adapters are missing
- [agents](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/agents): router + specialist agents
- [api/service.py](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/api/service.py): background job execution for web runs
- [tests](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/tests): `unittest` coverage for workflow and web API
- [AGENTS.md](g:/My Drive/3- Projects & Learning/2026_cong xuong agent QC (codex)/AGENTS.md): canonical repo-level operating contract for Codex

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
- `test-*` and `fake-*` API keys intentionally disable live LLM calls and trigger fallback logic in tests
- If the current interpreter does not have `langchain-groq` or `langchain-google-genai` installed, `core/llm.py` now falls back to direct HTTP calls for Groq and Gemini so live text/report translation can still run

## Working conventions
- Keep runtime web files only in `web/`; do not move frontend assets into `docs/`.
- Reports must stay bilingual in a single `report.md`.
- `id`, `cg`, and `fg` runs should always export `report.md`, even when the review is partial or blocked.
- `docs/communication.md` is an append-only runtime log; treat it as generated operational history.
- Knowledge load order is:
  1. `human_feedback_lessons.md`
  2. `system_lessons.md`
  3. `wcag_global.md`
  4. `project_x_req.md`
- Save edited text files as UTF-8. Some existing docs/UI strings and older generated reports may still show mojibake from earlier revisions, so avoid introducing new encoding damage.

## Current caveats worth knowing
- The web API exposes `id`, `cg`, and `fg` modes directly; it does not expose the free router path as a user-facing mode.
- Auth helpers exist in `api/auth.py`, but the current web UI is effectively running in no-auth mode.
- Reflection skips automatic lesson generation when fewer than 2 findings are produced.
- `cleanup_project()` removes cache/temp files but preserves valid output bundle directories.
- Vietnamese report translation now prefers live provider translation. If all translation-capable providers fail, the Vietnamese section should explicitly say translation was unavailable rather than silently repeating English.
- The local shell interpreter can differ from the repo's intended environment; when that happens, missing optional packages may surface only in this shell even though `requirements.txt` is correct.
