---
name: wcag-qc
description: Run WCAG 2.2 accessibility checks for e-learning browser states, screenshots, rendered frames, and shared QC evidence, then return evidence-backed findings for the calling specialist agent.
---

# WCAG QC

## Overview

Use this workflow when a review asks for accessibility testing, WCAG 2.2 coverage, contrast checks, focus/keyboard risks, accessible names, or learner access barriers in course UI.

This skill is usually used inside another workflow:

- `$id-qc` for browser course flows, interaction states, keyboard/focus risks, and accessible names
- `$fg-qc` for screenshots, rendered Figma frames, contrast, readability, and visual accessibility
- `$cqc` for shared browser evidence reviewed by ID, content, and graphic agents

## Evidence Order

1. Prefer live browser evidence when testing course interactions.
2. Prefer rendered screenshots or exported frames when testing visual WCAG issues.
3. Use deterministic checks where available before model judgement:
   - text contrast from `core.wcag` and `tools.wcag_contrast`
   - browser-probe actionables for missing accessible names
4. Use model judgement only for issues that require context, such as ambiguous affordance, instructions, focus visibility risk, or color-only meaning.
5. Clearly report any missing coverage such as no browser probe, no screenshots, missing OCR runtime, or unresolved Figma text.

## Baseline

Use WCAG 2.2 AA as the default baseline unless the request specifies another level.

Prioritize:

- `1.4.3 Contrast (Minimum)` for normal and large text contrast
- `1.4.11 Non-text Contrast` for controls and meaningful graphical objects
- `1.4.1 Use of Color` when status or instruction is color-only
- `2.4.3 Focus Order` and `2.4.7 Focus Visible` for keyboard navigation
- `2.5.8 Target Size (Minimum)` for small or crowded interactive targets
- `3.3.2 Labels or Instructions` for form/task clarity
- `4.1.2 Name, Role, Value` for buttons, links, quiz controls, and custom interactions
- `4.1.3 Status Messages` for feedback/results that must be announced to assistive technology

## Runtime Integration

Agents should call the shared adapter instead of hand-writing separate WCAG logic:

```python
from core.wcag import build_wcag_findings

findings = build_wcag_findings(
    state,
    prefix="ID",
    source_agent="id",
)
```

Use `prefix="FG", source_agent="graphic"` for visual/screenshot review.

## Reporting Rules

Produce findings only when they are grounded in accessed evidence. If deterministic checks cannot run, add an `Info` limitation rather than claiming pass/fail.

Every finding should include:

- the WCAG criterion where known
- the exact screenshot, browser state, cue, component, or control involved
- learner impact
- a concrete retest/fix direction

Do not claim full WCAG conformance. Automated checks cover only part of WCAG and must be treated as evidence for targeted QA findings, not certification.
