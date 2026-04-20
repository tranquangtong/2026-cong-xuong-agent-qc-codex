---
name: qc-reflect
description: Capture reusable QA lessons from findings or feedback. Use when Codex needs to store manual reviewer guidance, reflect on a completed QC pass, convert repeated defects into process lessons, or distinguish reusable learning from one-off noise.
---

# QC Reflect

## Overview

Use this workflow to turn feedback and findings into reusable lessons that improve future QC runs. Prefer concise operational lessons over long retrospectives.

## Workflow

1. Determine whether the input is manual feedback or a completed finding set.
2. Extract only the lessons that are reusable across future runs.
3. Avoid duplicating near-identical lessons or storing asset-specific noise.
4. Summarize what was learned and why it matters for future QC.

## Inputs

Expect one or more of:

- direct reviewer feedback
- a list of findings from a QC run
- a repeated QA miss that should become a standing rule
- a request to store or refine lessons for future passes

## Writing Behavior

Keep lessons short, reusable, and operational. Do not write long narrative summaries if a compact process rule will do.

Read [references/lesson-capture-rules.md](references/lesson-capture-rules.md) when deciding whether something is reusable enough to store.

## Output Contract

Produce lessons that:

- generalize beyond a single asset when possible
- improve future evidence gathering or QA judgment
- avoid duplication
- distinguish manual feedback from automatic reflection if that context matters

## Example Prompts

- `Use $qc-reflect to turn this QA feedback into reusable lessons for future runs.`
- `Use $qc-reflect to convert these repeated findings into concise system lessons.`
- `Use $qc-reflect to capture this reviewer correction as a standing QC rule.`

## Failure Modes

- If the feedback is too specific to one asset and teaches no broader rule, do not force it into a reusable lesson.
- If multiple lessons say the same thing, merge them into one stronger rule.
- If the input is weak or incomplete, summarize the limitation instead of inventing lessons.
