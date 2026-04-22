# Graphic QC Visual Review Rubric

## Review Focus

Use this rubric for Figma and screenshot-based QA:

- layout and spacing
- alignment and grouping
- typography and readability
- contrast and accessibility
- hierarchy and emphasis
- component consistency
- focus visibility and touch-target risks when relevant

## Evidence Priorities

Preferred evidence, from strongest to weakest:

1. Screenshot or exported frame image
2. Figma frame or node inspected with tooling
3. Figma link without rendered evidence

If only a raw Figma link is available, provide a limited review plan or an `Info` finding that states what still needs visual inspection.

## Finding Quality Bar

Good graphic findings should:

- name the visual area precisely
- describe the observable issue, not generic design advice
- connect the issue to usability, readability, or consistency impact
- give a concrete fix direction

Example pattern:

- Evidence: "Body copy on the right card sits too close to the image edge and reads as cramped."
- Impact: "Tight spacing reduces scanability and weakens hierarchy."
- Fix: "Increase inner padding and align the text block to the same spacing system as the neighboring cards."

## Accessibility Baseline

Use WCAG 2.2 as the baseline for visual accessibility risks, especially for:

- low contrast text
- tiny text or dense copy blocks
- weak focus visibility
- ambiguous interactive affordances
- cramped targets on mobile-like screens

When tooling allows it, prefer measured contrast-ratio evidence over subjective statements like "this looks low contrast". If deterministic measurement is unavailable, say that the contrast call is heuristic rather than a confirmed WCAG ratio failure.
