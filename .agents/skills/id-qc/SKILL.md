---
name: id-qc
description: Run browser-style instructional design QA for e-learning experiences. Use when Codex needs to review Articulate, Rise, Storyline, SCORM, course URLs, interaction flows, quiz logic, navigation, accessibility, or learner-facing on-screen text, especially when the request expects real coverage rather than generic commentary.
---

# ID QC

## Overview

Use this workflow to run instructional design QA with an evidence-first mindset. Prioritize real traversal, honest coverage notes, and actionable findings over generic review language.

## Workflow

1. Identify the requested scope: course, lesson, section, interaction type, or knowledge check.
2. Gather the strongest evidence available.
3. Traverse the experience as deeply as the available tooling and evidence allow.
4. Record findings for navigation, interaction logic, accessibility, and on-screen text.
5. State any missing coverage explicitly.
6. Export the QC report as `report.md` under an `outputs/` bundle before closing the task.

## Inputs

Expect one or more of:

- a course URL or section URL
- a statement of scope such as "review section 3 only"
- screenshots, tester notes, or browser evidence
- emphasis areas such as navigation, quiz logic, accessibility, or grammar on screen

## Tooling Behavior

Prefer browser-capable tooling when available. If Playwright or an equivalent browser tool is present, use it for interaction coverage. If no browser tool is available, continue with the best evidence on hand and clearly label the result as limited.

Read [references/coverage-and-evidence.md](references/coverage-and-evidence.md) before finalizing a deep section-level review or when coverage completeness matters.

## Output Contract

Produce findings that are:

- grounded in the evidence you actually accessed
- explicit about missing interaction coverage
- clear about impact on learners
- specific about what should be fixed or retested

Always export a bilingual `report.md` after the pass. If the review is partial, the report must still be created and must include the limitation clearly.

Do not imply the course was fully validated if you only reviewed prompt text, screenshots, or a partial path.

## Example Prompts

- `Use $id-qc to review this Rise course for navigation, quiz logic, and accessibility.`
- `Use $id-qc to test section 4 of this Storyline course and report missing interaction coverage honestly.`
- `Use $id-qc to review this Articulate link for revealed text, knowledge checks, and learner-facing spelling issues.`

## Failure Modes

- If the user asks for end-to-end coverage but only a URL is provided and no browser access is possible, state that the pass is incomplete.
- If the section contains interactives that could not be exercised, call them out directly.
- If the request mixes `id` and `content` concerns, keep instructional design findings separate from pure copy-editing findings.
