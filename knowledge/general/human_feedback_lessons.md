# Human QA Supervisor Lessons

## Consolidated Mandatory Rules
- MANDATORY: When a QC request targets a specific lesson or section, exhaustively click every visible interactive element inside scope before finalizing the report. This includes tabs, accordions, click-to-reveal items, flashcards, markers, buttons that reveal more copy, and knowledge-check transitions.
- MANDATORY: For Articulate Storyline and Rise review, interact through all visible items on the page and surface all newly revealed on-screen text before concluding coverage.
- MANDATORY: In Articulate Storyline and Rise review, `Content-Agent` must check learner-facing grammar, spelling, and British English consistency, while `ID-Agent` must verify whether the content aligns with the project intent and stated learning outcomes.
- MANDATORY: Complete every knowledge check as a learner. Answer sequentially, scroll after each question, interact with any `CONTINUE` or equivalent controls, and keep going until no further question, feedback, or revealed content appears.
- MANDATORY: For quiz review, prioritize post-answer learner experience over pre-submit states. Test both correct and incorrect answer paths, verify that the feedback and explanations are complete and aligned with lesson intent, check their grammar and spelling, and then confirm that the course flow progresses correctly after quiz completion.
- MANDATORY: Verify that knowledge-check feedback states are accurate and clearly mapped to the learner's answer path.
- MANDATORY: Perform a coverage self-check before closing a scoped QC pass: confirm all interactives were exercised, all revealed text was read, the deepest reachable knowledge-check path was traversed, and the report reflects the deepest evidence collected.
- MANDATORY: Preserve enough browser evidence to reconstruct coverage. For browser-assisted QC, keep the review-shell probe, a section/content probe, and at least one full-page screenshot of the tested state in the same output bundle.
- MANDATORY: If screenshots are supplied with the request, store them in the same `outputs/<bundle>/artifacts/` folder as the report.
- MANDATORY: If the public Review 360 shell blocks or hides the course body, resolve and document the direct asset URL, then continue QC on that asset while preserving evidence of the blocked public shell.
- MANDATORY: After testing, every participating specialist agent must produce its own report summary. If no bug is found, the agent must still state that no major issue was detected. Suggestions should be recorded under `Suggestion`, and the coordinating agent or flow must aggregate all participating-agent outputs into the final `report.md`.
- MANDATORY: Verify pronoun consistency and pronoun-antecedent agreement throughout learner-facing content.
- MANDATORY: Check language-variant consistency across the same learning item, especially British vs American English spelling.

## Specific Reminders Still Worth Keeping
- MANDATORY: In Section 2, every interactive element, specifically including Tab 2 and 3, must be clicked and its displayed content verified.
- MANDATORY: You missed checking Section 3 markers.
