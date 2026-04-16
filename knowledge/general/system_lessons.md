# System Lessons Learned (Self-Improvement Log)

This file is automatically updated by the @Reflection-Agent to improve future QC accuracy.

## Consolidated Historical Lessons

- Implement a pre-run check to verify the availability and accessibility of all configured AI models before starting AI-dependent QC runs.

- Always verify subject-pronoun consistency, especially when 'We' is used as the subject.

- **Adherence to Style Guides and Consistency:** Maintain strict adherence to established style guides (e.g., for capitalization, formatting) across all content to ensure a professional and consistent user experience.

- **Thorough Functional Testing:** Implement comprehensive testing for all interactive elements and tracking mechanisms to ensure they accurately reflect user actions and system state, preventing misleading information or broken functionality.

- Maintain absolute consistency in all content elements, including capitalization, spelling, and chosen language variants.

- Ensure all interactive features and feedback mechanisms function correctly and accurately reflect user actions and progress.

- **Prioritize consistency in all aspects of content and presentation.** This includes stylistic elements like capitalization and language variants, as well as ensuring reliable content rendering.

- **Establish and strictly adhere to a comprehensive style guide.** A clear style guide helps prevent inconsistencies in grammar, spelling, and formatting across the platform.

## Automatic Lessons from 2026-04-12 15:55:43
- Strengthen QA checks for terminology: Project requirements explicitly require 'Learner' instead of 'User'.
- Strengthen QA checks for grammar/spelling: Mixed English variants weaken consistency and may violate the British English requirement.
- Strengthen QA checks for design/layout: A visual review should confirm alignment, spacing, contrast, and touch target sizing.

## Automatic Lessons from 2026-04-12 15:56:07
- Strengthen QA checks for terminology: Project requirements explicitly require 'Learner' instead of 'User'.
- Strengthen QA checks for grammar/spelling: Mixed English variants weaken consistency and may violate the British English requirement.
- Strengthen QA checks for design/layout: A visual review should confirm alignment, spacing, contrast, and touch target sizing.

## Automatic Lessons from 2026-04-12 16:03:36
- Strengthen QA checks for assessment coverage: Incomplete quiz traversal can hide follow-up questions, feedback states, or broken continue actions.
- Strengthen QA checks for content qa: A richer content sample is needed to verify grammar, terminology, and subtitle quality.


## Automatic Lessons from 2026-04-12 16:12:13
- Ensure all essential course materials are provided for comprehensive QA review.
- Provide detailed specifications and documentation for all interactive elements (e.g., quizzes, activities) for QA.
- All textual content must be available for review to ensure linguistic consistency and grammatical accuracy (e.g., specific English variants).
- All visual assets, including screenshots, must be provided for design and quality assurance review.


## Automatic Lessons from 2026-04-12 16:13:05
- To enable comprehensive QA, always provide detailed course materials, including outlines, lesson plans, and specific requirements.
- Clearly outline the expected navigation flow and any known issues to ensure thorough review of the learner experience.
- Specify criteria and areas of focus for content quality (e.g., grammar, consistency, engagement) to guide targeted assessment.
- Detail all interactive elements (quizzes, games, discussions) to allow for proper functionality and experience testing.
- Document all intended accessibility features (e.g., captions, screen reader support) for verification.
- Provide specific grammar and style guidelines (e.g., language consistency) to ensure adherence to standards.

## Automatic Lessons from 2026-04-14 16:45:00
- Every QC run should produce a report bundle in `outputs/` with `report.md` as the canonical deliverable.
- When a QC request includes screenshots, preserve those screenshot files inside the same bundle under `artifacts/`.
- Content QA should rely on explicit source resolution; if a Figma frame has not been pre-resolved or a document cannot be extracted, the report must name that limitation instead of implying full coverage.
