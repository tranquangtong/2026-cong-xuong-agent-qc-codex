---
name: cqc
description: Run collaborative course QC for Articulate Storyline and Rise links by collecting shared browser evidence first, then combining instructional design, content, and graphic review into one report.
---

# CQC

## Overview

Use this workflow for course products when one Articulate link should be reviewed through a shared-evidence pass across:

- instructional design QA
- content QA
- graphic QA

This workflow is intended for `learning course` products, not video products.

## Workflow

1. Identify the course scope from the user request.
2. Collect browser evidence once from the course link.
3. Reuse the same evidence for `id`, `content`, and `graphic` review.
4. Merge findings into one bilingual report.
5. Keep coverage limitations explicit when the collector does not exhaust every interaction path.

## Inputs

Expect one or more of:

- an Articulate Review 360 or asset URL
- a scope such as chapter or section range
- emphasis areas such as quiz logic, grammar, British English, or visual consistency

## Output Contract

Always produce one bilingual `report.md` under an `outputs/` bundle.

The report should:

- separate confirmed defects from evidence limitations
- preserve which evidence was actually traversed
- combine `id`, `content`, and `graphic` findings from the same collector pass

## Example Prompts

- `Use $cqc to review this Articulate lesson for chapter 2 sections 1 to 3.`
- `Use $cqc to run collaborative course QC on this Rise link for interactions, on-screen grammar, and visual readability.`
