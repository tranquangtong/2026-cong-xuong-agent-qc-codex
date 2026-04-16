# Project X Requirements

## Content And Language Requirements
- Use British English consistently across learner-facing content.
- Prefer `Learner` instead of `User` in learner-facing copy unless the source material explicitly defines another term.
- Keep terminology, capitalization, and label style consistent within the same lesson or deliverable.
- Treat placeholder markers, bracketed drafting notes, and unfinished editorial comments as content defects unless the request explicitly says the asset is still in draft markup.

## Content-Agent MVP Source Rules
- `Content-Agent` may QC local `pdf`, `csv`, and `docx` artifacts after text extraction.
- `Content-Agent` may QC screenshot-based content when screenshots are supplied as evidence.
- Figma content QA is supported through a hybrid flow: the frame content should be pre-resolved by Codex/Figma tooling before the Python runtime performs content QA.
- If a source cannot be resolved or extracted, the report must state the limitation clearly instead of implying full review coverage.

## Reporting And Evidence Requirements
- Every QC pass must generate a dedicated `outputs/<bundle>/report.md`.
- If the QC request includes screenshots, those screenshot files must be stored in the same bundle under `outputs/<bundle>/artifacts/`.
- Artifacts should preserve enough evidence to reconstruct what source material was actually reviewed.

