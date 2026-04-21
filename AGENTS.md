## Project Overview

This repository is a multi-agent QC factory for e-learning review. The working modes are:

- `id`: instructional design QA for browser-like course flows, interactions, quiz logic, navigation, accessibility, and learner-facing on-screen text
- `graphic`: visual QA for Figma links and screenshots, including layout, spacing, hierarchy, readability, and WCAG 2.2 visual risks
- `content`: content QA for storyboard copy, subtitles, grammar, spelling, British English, terminology, and learner-facing clarity
- `reflect`: lesson capture from feedback or findings so future QC passes improve over time

The runtime entrypoints in this repo are:

- CLI in `main.py`
- FastAPI backend in `api/app.py`
- Specialist agents in `agents/`
- Repo-local Codex workflows in `.agents/skills/`

Every QC run for `id`, `graphic`, or `content` must end in a bilingual `report.md` bundle under `outputs/`.

## Command And Mode Mapping

The canonical mode mapping is:

- `/id` -> `id`
- `/fg` -> `graphic`
- `/cg` -> `content`
- `/reflect` -> `reflect`

The project utility mapping is:

- `/cleanup` -> cleanup cache and temp files safely
- `/upgit` -> cleanup, commit current changes, and push to git remote

Default `/upgit` behavior:

- runs cleanup first
- skips runtime/generated paths such as `docs/communication.md` and `outputs/` by default
- auto-generates a commit message when none is provided
- pushes only the remaining relevant staged changes

When working in Codex chat, prefer the workflow skills:

- `$id-qc`
- `$fg-qc`
- `$cg-qc`
- `$qc-reflect`
- `$cleanup`
- `$upgit`

Use explicit workflow skills when the user clearly knows the target mode. If the request is ambiguous, reason from source type and stated intent before choosing a workflow.

The current repo-local skill folders are:

- `.agents/skills/id-qc`
- `.agents/skills/fg-qc`
- `.agents/skills/cg-qc`
- `.agents/skills/qc-reflect`
- `.agents/skills/cleanup`
- `.agents/skills/upgit`

## Routing Rules

Apply these routing rules consistently:

- Articulate, Rise, Storyline, SCORM, browser-flow, interaction, quiz, knowledge-check, navigation, and accessibility requests route to `id`
- Figma links and screenshots route to `graphic`
- Storyboard copy, subtitles, spelling, grammar, terminology, and document artifacts such as `pdf`, `csv`, and `docx` route to `content`
- Figma links that are explicitly about storyboard copy or text QA usually require both `graphic` and `content`, but `content` must only claim text coverage if the frame text is actually resolved
- Manual QA feedback and reusable process lessons route to `reflect`
- Cache, temp-file, or workspace cleanup requests route to the `cleanup` skill rather than a QA mode
- Git save, commit, push, or repository sync requests route to the `upgit` skill rather than a QA mode

If a request mixes multiple scopes, keep the boundaries explicit rather than collapsing everything into one vague review.

## Evidence Rules

Never pretend you inspected evidence that you did not actually access.

- If you used browser tooling such as Playwright, state what path or states were actually traversed
- If you used Figma tooling, state which frame, node, or screenshot evidence was actually reviewed
- If a Figma link is present but no text was resolved for content review, say so plainly
- If only prompt text is available, treat the output as a constrained QA pass and disclose the limitation
- If the user asks for section-level ID review, only claim completion when all visible interactives, revealed text, and reachable knowledge-check states within scope were exercised

When evidence is partial, report the missing coverage as part of the findings or summary.

## Reporting Rules

All reports and QC summaries should follow these expectations:

- Export a `report.md` file after every `id`, `graphic`, or `content` test pass, even when the review is partial or blocked
- Write the report under an `outputs/` bundle and mention the report path in the chat response when possible
- Keep findings actionable and grounded in evidence
- Use the supported severity levels: `Critical`, `Major`, `Minor`, `Suggestion`, `Info`
- Keep English and Vietnamese output together when generating project reports
- Use the shared reporting pipeline in `core/reporting.py` for bilingual output rather than hand-writing separate chat-only summaries
- Distinguish clearly between confirmed defects, review limitations, and follow-up suggestions
- Prefer honest coverage notes over overclaiming that a review is complete

For content and graphic QA, preserve source cues such as page, row, paragraph, frame, screenshot, or section when the evidence supports them.

If the review is limited by missing tooling, partial screenshots, unresolved Figma text, or blocked access, the report must still be exported and must say exactly what was not verified.

Translation behavior:

- The report layer attempts Vietnamese translation through configured live providers
- If LangChain provider adapters are missing in the current interpreter, the LLM layer falls back to direct HTTP calls for Groq and Gemini
- If no translation-capable provider is usable, the Vietnamese section must explicitly say translation was unavailable instead of silently reusing English text

## Tooling Guidance

This repo may be used in environments with or without plugins and MCP tools.

- If browser tooling is available, use it for `id` work that requires real interaction coverage
- If Figma tooling is available, use it for `
