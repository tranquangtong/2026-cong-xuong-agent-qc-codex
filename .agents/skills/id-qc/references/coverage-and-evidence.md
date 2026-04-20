# ID QC Coverage And Evidence

## Coverage Standard

Treat `id` review as evidence-driven traversal, not prompt-only commentary.

- Exercise all visible interactives inside the requested scope
- Read every newly revealed text state after each interaction
- Traverse quizzes and knowledge checks as far as the available evidence allows
- Note dead ends, blocked states, hidden states not reached, and scope boundaries

If the request names a specific section, do not claim that section is complete unless the section has been fully explored within the available tooling and time.

## Evidence Expectations

Preferred evidence, from strongest to weakest:

1. Browser interaction evidence with screenshots or state notes
2. Structured tester notes that describe the path taken
3. Prompt text describing observed behavior

When using browser tooling, capture or summarize:

- entry URL or shell state
- section names or interaction labels exercised
- answer paths used in knowledge checks
- major state changes after clicks, reveals, or submits

## Limitation Language

Use explicit limitation wording when coverage is incomplete. Good patterns:

- "This pass confirms the first two reveal states, but the remaining tabs were not exercised."
- "The quiz path was partially traversed; downstream feedback states remain unverified."
- "The request references a Rise lesson, but no live browser evidence was available for end-to-end interaction coverage."

Avoid language that implies full validation if you only inspected prompt text or a partial path.
