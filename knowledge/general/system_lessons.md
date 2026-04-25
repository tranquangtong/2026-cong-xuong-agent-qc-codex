# System Lessons Learned (Self-Improvement Log)

This file is automatically updated by the @Reflection-Agent to improve future QC accuracy.

## Consolidated Historical Lessons

- id: legacy-system-001-01

- category: system_lesson

- tags:

- source_agent: reflection

- first_seen_at:

- last_seen_at:

- seen_count: 1

- confidence: medium

- promoted: true

- promoted_by: legacy

- example_run_refs:

- summary: Ensure automated QA fully traverses the requested learner scope, including lessons, chapters, interactives, revealed states, and knowledge-check paths.

- rationale:

- recommended_action:

## Consolidated Historical Lessons

- id: legacy-system-001-02

- category: system_lesson

- tags:

- source_agent: reflection

- first_seen_at:

- last_seen_at:

- seen_count: 1

- confidence: medium

- promoted: true

- promoted_by: legacy

- example_run_refs:

- summary: Verify that course content is fully available, directly resolvable, and accessible before treating a QA pass as complete.

- rationale:

- recommended_action:

## Consolidated Historical Lessons

- id: legacy-system-001-03

- category: system_lesson

- tags:

- source_agent: reflection

- first_seen_at:

- last_seen_at:

- seen_count: 1

- confidence: medium

- promoted: true

- promoted_by: legacy

- example_run_refs:

- summary: Investigate and resolve browser console errors and warnings when they suggest learner-facing instability or broken functionality.

- rationale:

- recommended_action:

## Consolidated Historical Lessons

- id: legacy-system-001-04

- category: system_lesson

- tags:

- source_agent: reflection

- first_seen_at:

- last_seen_at:

- seen_count: 1

- confidence: medium

- promoted: true

- promoted_by: legacy

- example_run_refs:

- summary: Keep QA tool dependencies and parsing/vision runtime prerequisites installed and working before relying on automated diagnostics.

- rationale:

- recommended_action:

## Consolidated Historical Lessons

- id: legacy-system-001-05

- category: system_lesson

- tags:

- source_agent: reflection

- first_seen_at:

- last_seen_at:

- seen_count: 1

- confidence: medium

- promoted: true

- promoted_by: legacy

- example_run_refs:

- summary: Require enough source artifacts and evidence for complete review, including direct content URLs, text/document sources, design links, and clear screenshots when relevant.

- rationale:

- recommended_action:

## Consolidated Historical Lessons

- id: legacy-system-001-06

- category: system_lesson

- tags:

- source_agent: reflection

- first_seen_at:

- last_seen_at:

- seen_count: 1

- confidence: medium

- promoted: true

- promoted_by: legacy

- example_run_refs:

- summary: Enforce content consistency across grammar, spelling, terminology, capitalization, and chosen language variant.

- rationale:

- recommended_action:

## Consolidated Historical Lessons

- id: legacy-system-001-07

- category: system_lesson

- tags:

- source_agent: reflection

- first_seen_at:

- last_seen_at:

- seen_count: 1

- confidence: medium

- promoted: true

- promoted_by: legacy

- example_run_refs:

- summary: Use high-quality visual evidence and manual visual review to assess spacing, hierarchy, readability, contrast, and WCAG 2.2 visual risks.

- rationale:

- recommended_action:

## Consolidated Historical Lessons

- id: legacy-system-001-08

- category: system_lesson

- tags:

- source_agent: reflection

- first_seen_at:

- last_seen_at:

- seen_count: 1

- confidence: medium

- promoted: true

- promoted_by: legacy

- example_run_refs:

- summary: Confirm that interactive features and feedback mechanisms accurately reflect learner actions and system state.

- rationale:

- recommended_action:

## Active System Emphases

- id: legacy-system-002-01

- category: system_lesson

- tags:

- source_agent: reflection

- first_seen_at:

- last_seen_at:

- seen_count: 1

- confidence: medium

- promoted: true

- promoted_by: legacy

- example_run_refs:

- summary: For content-heavy runs, prioritize elimination of redundant text, typo cleanup, terminology consistency, and clearer sentence structure when copy is complex.

- rationale:

- recommended_action:

## Active System Emphases

- id: legacy-system-002-02

- category: system_lesson

- tags:

- source_agent: reflection

- first_seen_at:

- last_seen_at:

- seen_count: 1

- confidence: medium

- promoted: true

- promoted_by: legacy

- example_run_refs:

- summary: For learning-flow runs, verify that assessments and interactions support learner understanding without hiding downstream states or required actions.

- rationale:

- recommended_action:

## Strengthen QA checks for subtitle reading speed: Subtitle pacing may be too fast

- id: system-system_lesson-strengthen-qa-checks-for-subtitle-reading-speed-

- category: system_lesson

- tags: content, interaction, vqc

- source_agent: content

- first_seen_at: 2026-04-25 10:32:56

- last_seen_at: 2026-04-25 10:32:56

- seen_count: 3

- confidence: high

- promoted: true

- promoted_by: auto_threshold

- example_run_refs: /vqc video: "D:\Downloads\Approving- Rejecting Successor Nominations-V2.mp4" subtitle: "D:\Downloads\Approving- Rejecting Successor Nominations-V2.srt"

- summary: Strengthen QA checks for subtitle reading speed: Subtitle pacing may be too fast for comfortable reading.

- rationale: Subtitle pacing may be too fast for comfortable reading.

- recommended_action: Reduce subtitle density or increase the cue duration so the reading speed comes down.

## Strengthen QA checks for grammar and spelling: Minor grammatical error may cause

- id: system-system_lesson-strengthen-qa-checks-for-grammar-and-spelling-mi

- category: system_lesson

- tags: content, grammar, vqc

- source_agent: content

- first_seen_at: 2026-04-25 10:32:56

- last_seen_at: 2026-04-25 10:32:56

- seen_count: 1

- confidence: medium

- promoted: false

- promoted_by:

- example_run_refs: /vqc video: "D:\Downloads\Approving- Rejecting Successor Nominations-V2.mp4" subtitle: "D:\Downloads\Approving- Rejecting Successor Nominations-V2.srt"

- summary: Strengthen QA checks for grammar and spelling: Minor grammatical error may cause slight confusion for learners

- rationale: Minor grammatical error may cause slight confusion for learners

- recommended_action: Correct the grammatical error to improve clarity

## Strengthen QA checks for consistency: Inconsistent terminology may cause confusi

- id: system-system_lesson-strengthen-qa-checks-for-consistency-inconsisten

- category: system_lesson

- tags: content, grammar, vqc

- source_agent: content

- first_seen_at: 2026-04-25 10:32:56

- last_seen_at: 2026-04-25 10:32:56

- seen_count: 1

- confidence: low

- promoted: false

- promoted_by:

- example_run_refs: /vqc video: "D:\Downloads\Approving- Rejecting Successor Nominations-V2.mp4" subtitle: "D:\Downloads\Approving- Rejecting Successor Nominations-V2.srt"

- summary: Strengthen QA checks for consistency: Inconsistent terminology may cause confusion for learners

- rationale: Inconsistent terminology may cause confusion for learners

- recommended_action: Use consistent terminology throughout the course

## Strengthen QA checks for clarity: Minor clarity issue may cause slight confusion

- id: system-system_lesson-strengthen-qa-checks-for-clarity-minor-clarity-i

- category: system_lesson

- tags: content, vqc

- source_agent: content

- first_seen_at: 2026-04-25 10:32:56

- last_seen_at: 2026-04-25 10:32:56

- seen_count: 1

- confidence: low

- promoted: false

- promoted_by:

- example_run_refs: /vqc video: "D:\Downloads\Approving- Rejecting Successor Nominations-V2.mp4" subtitle: "D:\Downloads\Approving- Rejecting Successor Nominations-V2.srt"

- summary: Strengthen QA checks for clarity: Minor clarity issue may cause slight confusion for learners

- rationale: Minor clarity issue may cause slight confusion for learners

- recommended_action: Consider rephrasing for improved clarity

## Strengthen QA checks for british english consistency: Inconsistent use of Britis

- id: system-system_lesson-strengthen-qa-checks-for-british-english-consist

- category: system_lesson

- tags: british-english, content, vqc

- source_agent: content

- first_seen_at: 2026-04-25 10:32:56

- last_seen_at: 2026-04-25 10:32:56

- seen_count: 1

- confidence: low

- promoted: false

- promoted_by:

- example_run_refs: /vqc video: "D:\Downloads\Approving- Rejecting Successor Nominations-V2.mp4" subtitle: "D:\Downloads\Approving- Rejecting Successor Nominations-V2.srt"

- summary: Strengthen QA checks for british english consistency: Inconsistent use of British English may cause confusion for learners

- rationale: Inconsistent use of British English may cause confusion for learners

- recommended_action: Ensure consistent use of British English throughout the course
