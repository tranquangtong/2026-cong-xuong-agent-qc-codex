# Course QC Multi-Agent Plan

## Goal

Design a dedicated QC flow for course products, especially Articulate Storyline and Rise, so one run can produce more complete findings by combining:

- `id` for navigation, interaction logic, knowledge checks, and learner-flow accessibility
- `content` for grammar, spelling, British English, terminology, and learner-facing clarity
- `graphic` for visual layout, readability, contrast, hierarchy, and visual accessibility

This plan is for `learning course` products.
It is separate from the future `learning video` flow.

## Why Change

The current repo already supports multiple specialist agents, but the practical behavior is still limited for course QC:

- agents are invoked in sequence, not true collaborative fan-out
- later agents do not reliably consume richer evidence produced by earlier agents in the same run
- `id` is the only agent with browser evidence collection
- `content` and `graphic` are strongest when they receive extracted text and screenshots, not just a raw Articulate link

For course QC, the best result should come from a shared evidence bundle collected once, then analyzed by multiple specialists.

## Proposed Product Split

Two main product lines:

1. `learning video`
   A future flow for transcript, subtitle, narration, frame sample, and visual-text alignment review.

2. `learning course`
   A dedicated flow for Articulate Storyline and Rise course QC, with shared browser evidence and specialist fan-out.

This document focuses only on `learning course`.

## Recommended Architecture

Recommended pattern:

`1 browser collector -> 3 specialist analyzers in parallel -> 1 merger/reporter -> reflection`

Do not let all 3 agents independently open and traverse the same Articulate link.

Reasons:

- one source of truth for coverage
- lower runtime and token cost
- fewer duplicated findings
- `content` and `graphic` receive the right evidence type
- easier report merging and limitation notes

## Proposed Flow

### Stage 1: Course Orchestrator

Responsibilities:

- detect that the request is a `course_qc_flow`
- parse product type and source
- normalize scope from the prompt
- create one output bundle for the entire run

Expected input examples:

- full course link
- chapter-only review request
- section-only review request
- emphasis such as `quiz logic`, `grammar`, `visual consistency`

Expected normalized scope:

- target course URL
- product type: `rise` or `storyline` when detectable
- target chapter(s)
- target section(s)
- emphasis areas

### Stage 2: Course Evidence Collector

Responsibilities:

- open Review 360 URL
- resolve the underlying asset URL
- reach lesson-level states where possible
- traverse only the requested scope
- capture screenshots for key states
- extract visible on-screen text after each reveal
- record which interactions and quiz branches were actually exercised

Expected outputs:

- `browser_evidence`
- `coverage_map`
- `screenshots`
- `resolved_text_blocks`
- `collector_limitations`

This is the most important new stage.
It should replace the current probe-only behavior for course review.

### Stage 3: Parallel Specialist Analysis

All three specialists analyze the same collected evidence.

#### ID Agent

Focus:

- navigation
- interaction logic
- reveal completeness
- quiz and knowledge-check behavior
- learner path blockers
- accessibility behavior in flow context

Input:

- coverage map
- visited states
- screenshots
- resolved text by state

#### Content Agent

Focus:

- grammar
- spelling
- British English
- terminology
- clarity of learner-facing text
- consistency across revealed states

Input:

- resolved text blocks extracted from browser states
- section and state labels for source cues
- screenshots only as fallback for OCR-like support if needed

#### Graphic Agent

Focus:

- spacing
- hierarchy
- readability
- overflow and clipping
- contrast
- visual accessibility risks
- consistency across course sections

Input:

- screenshots captured from collector
- section and state labels

### Stage 4: Merge And Report

Responsibilities:

- merge findings from all specialists
- deduplicate overlapping issues
- group findings by section or state when possible
- separate confirmed defects from limitations
- preserve source agent for each finding
- export one bilingual `report.md`

The final report should answer:

- what was actually traversed
- which sections are complete vs partial
- which issues are ID vs content vs graphic
- what needs follow-up retest

### Stage 5: Reflection

Responsibilities:

- run only after merged findings exist
- convert repeated problems into reusable QA lessons

## Proposed State Additions

Suggested shared state fields:

- `flow_type`
- `requested_scope`
- `collector_status`
- `browser_evidence`
- `coverage_map`
- `screenshots`
- `resolved_text_blocks`
- `collector_limitations`
- `merged_findings`
- `report_sections`

### Suggested State Definitions

`requested_scope`

- normalized review target
- chapter and section boundaries
- emphasis flags

`coverage_map`

- lessons visited
- states visited
- interactives exercised
- quiz branches exercised
- items still unverified

`resolved_text_blocks`

- extracted visible text
- grouped by lesson and state
- source cues such as section, heading, interaction label

`screenshots`

- file paths
- associated state id
- associated lesson or section

## Current Repo Gaps To Address

### 1. Current Workflow Is Not Truly Collaborative

`invoke_workflow()` currently builds a list of specialist updates from the same initial state.
That means the richer evidence produced by one specialist is not reliably reused by the next specialist in the same pass.

Implication:

- `content` and `graphic` do not benefit enough from `id` browser collection today

### 2. Browser Probe Is Too Shallow For Section-Level QC

Current `run_playwright_probe()` is still a heuristic probe with limits such as:

- small state cap
- shallow depth
- small action cap per state
- no strong scope targeting

Implication:

- suitable for evidence gathering
- not yet suitable for full section sign-off

### 3. Content Agent Needs Better Course Text Inputs

`content` is strong when it receives extracted text.
For Articulate course review, the new flow should feed it resolved text from the collector instead of expecting it to infer from a raw link.

### 4. Graphic Agent Needs Real Course Screenshots

`graphic` should analyze screenshots captured during traversal, not a raw Articulate URL by itself.

## Rollout Recommendation

### Phase 1: Introduce A New Course Flow Without Breaking Existing Skills

Implement a new dedicated path for course QC while keeping current `/id` behavior intact.

Goal:

- safe migration
- easy comparison with old reports

Suggested entry:

- internal `course_qc_flow`
- later exposed via skill or command once stable

### Phase 2: Build Collector-First Pipeline

Work items:

- add course collector node
- store browser evidence in shared state
- make `content` and `graphic` consume collector outputs

### Phase 3: Improve Scope Awareness

Work items:

- parse chapter and section constraints from request text
- map user scope to lesson ids where possible
- allow follow-up traversal only inside requested scope

### Phase 4: Improve Merge And Report Layer

Work items:

- add dedupe rules across agents
- improve section-based grouping
- improve limitation wording

## Suggested Implementation Order

1. Add new state fields and collector output contract.
2. Create a `course_evidence_collector` node.
3. Update workflow graph so collector runs before specialists.
4. Make `content` read `resolved_text_blocks`.
5. Make `graphic` read collector screenshots.
6. Add merge rules for overlapping findings.
7. Add tests for scope handling and merged reporting.

## Design Decisions To Approve

These decisions should be confirmed before implementation:

1. Should `course_qc_flow` be a new explicit mode, or should `/id` evolve to become collector-first for Articulate links?
2. Should the first release target `Rise` only, or support both `Rise` and `Storyline` together?
3. Should the collector aim for exhaustive traversal in one run, or support a phased pass with explicit coverage limits?
4. Should the final report keep findings grouped by source agent, by lesson section, or both?

## Recommendation

Recommended answer: proceed with the dedicated `learning course` flow.

Best first version:

- one shared collector
- three specialist analyzers on shared evidence
- one merged report

This is a better fit than letting `id`, `content`, and `graphic` independently open the same Articulate link.

## MVP Success Criteria

The new flow is successful if one Articulate review run can:

- state exactly which chapter or section was traversed
- provide screenshots and extracted text from the actual visited states
- produce `id`, `content`, and `graphic` findings from the same evidence bundle
- export one bilingual report with honest limitation notes
- reduce duplicate findings compared with the current approach
