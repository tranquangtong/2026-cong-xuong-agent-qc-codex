---
name: fg-qc
description: Run graphic QA for e-learning visuals. Use when Codex needs to review Figma links, Figma frames, screenshots, or design review requests focused on layout, spacing, hierarchy, readability, contrast, consistency, or WCAG 2.2 visual accessibility risks.
---

# Graphic QC

## Overview

Use this workflow for evidence-backed visual review. Prioritize observable design issues, accessibility risks, and clear fix guidance over generic aesthetic commentary.

## Workflow

1. Identify whether the evidence is a screenshot, a Figma frame, or only a raw Figma link.
2. Review the strongest available visual evidence first.
3. Evaluate layout, spacing, readability, contrast, hierarchy, and consistency.
4. Separate confirmed issues from limits caused by missing rendered evidence.
5. Export the QC report as `report.md` under an `outputs/` bundle before closing the task.

## Inputs

Expect one or more of:

- a Figma link or node
- screenshots or exported frames
- a stated review focus such as spacing, contrast, or component consistency
- a platform context such as desktop, mobile, or slide-like screen

## Tooling Behavior

Prefer rendered images or direct Figma inspection when tooling is available. If only a raw Figma link is available, do not overstate what was reviewed.

Read [references/visual-review-rubric.md](references/visual-review-rubric.md) when you need the full review rubric or when the line between confirmed issue and missing evidence matters.

## Output Contract

Produce findings that:

- describe the observed visual issue precisely
- explain the usability, readability, or accessibility impact
- recommend a concrete fix direction
- call out when the evidence is insufficient for a complete review

Always export a bilingual `report.md` after the pass. If the review is constrained by a raw Figma link, missing zoomed evidence, or tool access limits, the report must still be created and must document that limitation.

Keep text-only copy defects in `content` scope unless the issue is fundamentally about legibility or visual presentation.

## Example Prompts

- `Use $fg-qc to review this Figma frame for layout, contrast, and visual hierarchy.`
- `Use $fg-qc to review these screenshots for spacing, readability, and component consistency.`
- `Use $fg-qc to inspect this design for WCAG 2.2 visual accessibility risks.`

## Failure Modes

- If the request gives only a Figma URL with no rendered evidence and no Figma access, report a limitation instead of inventing detailed visual findings.
- If screenshots are partial, note what parts of the screen set remain unreviewed.
- If the user mixes visual QA with copy QA, keep the scope split cleanly.
