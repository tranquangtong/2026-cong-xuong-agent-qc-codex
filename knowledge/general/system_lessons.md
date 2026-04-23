# System Lessons Learned (Self-Improvement Log)

This file is automatically updated by the @Reflection-Agent to improve future QC accuracy.

## Consolidated Historical Lessons
- Ensure automated QA fully traverses the requested learner scope, including lessons, chapters, interactives, revealed states, and knowledge-check paths.
- Verify that course content is fully available, directly resolvable, and accessible before treating a QA pass as complete.
- Investigate and resolve browser console errors and warnings when they suggest learner-facing instability or broken functionality.
- Keep QA tool dependencies and parsing/vision runtime prerequisites installed and working before relying on automated diagnostics.
- Require enough source artifacts and evidence for complete review, including direct content URLs, text/document sources, design links, and clear screenshots when relevant.
- Enforce content consistency across grammar, spelling, terminology, capitalization, and chosen language variant.
- Use high-quality visual evidence and manual visual review to assess spacing, hierarchy, readability, contrast, and WCAG 2.2 visual risks.
- Confirm that interactive features and feedback mechanisms accurately reflect learner actions and system state.

## Active System Emphases
- For content-heavy runs, prioritize elimination of redundant text, typo cleanup, terminology consistency, and clearer sentence structure when copy is complex.
- For learning-flow runs, verify that assessments and interactions support learner understanding without hiding downstream states or required actions.
