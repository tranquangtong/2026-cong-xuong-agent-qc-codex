---
name: cg-qc
description: Run content QA for e-learning text assets. Use when Codex needs to review storyboard copy, subtitles, grammar, spelling, British English, terminology, learner-facing clarity, or supported document inputs such as pdf, csv, docx, readable screenshots, or pre-resolved Figma text.
---

# Content QC

## Overview

Use this workflow to review learner-facing text with evidence-first discipline. Focus on real source text, source-aware findings, and explicit limitation handling when text is incomplete or unresolved.

## Workflow

1. Identify the source type and whether the text is actually readable or extracted.
2. Review grammar, spelling, British English, terminology, and learner-facing clarity.
3. Cite source cues such as page, row, paragraph, or frame when available.
4. Call out unresolved or partial sources instead of implying full content coverage.
5. Export the QC report as `report.md` under an `outputs/` bundle before closing the task.

## Inputs

Expect one or more of:

- a `pdf`, `csv`, or `docx`
- pasted storyboard or subtitle text
- a screenshot with readable text
- a pre-resolved Figma text source
- a request to check British English, terminology, grammar, or clarity

## Tooling Behavior

Review only text that is actually available. If a Figma link has not been resolved into readable text or image evidence, state the limitation and avoid pretending a full content pass occurred.

Read [references/content-review-rubric.md](references/content-review-rubric.md) when you need the detailed source-handling and style rubric.

## Output Contract

Produce findings that:

- point to concrete text or source cues
- distinguish hard errors from style or consistency suggestions
- recommend the corrected phrasing or change direction
- disclose missing source resolution when relevant

Always export a bilingual `report.md` after the pass. If the content source is unresolved, blurry, or only partially readable, the report must still be created and must state the missing coverage explicitly.

Keep pure layout or spacing findings in `graphic` scope unless they directly block text legibility.

## Example Prompts

- `Use $cg-qc to review this storyboard.csv for grammar, British English, and terminology consistency.`
- `Use $cg-qc to review this subtitle text for learner-facing clarity and spelling.`
- `Use $cg-qc to review this Figma-derived text source and call out any unresolved coverage honestly.`

## Failure Modes

- If the source is unresolved, say so instead of inferring unseen text.
- If the image text is too small or blurry to read safely, report that limitation.
- If the user mixes content and visual review, keep the findings separated by scope.
