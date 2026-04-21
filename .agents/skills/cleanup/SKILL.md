---
name: cleanup
description: Clean project cache and temporary files safely. Use when Codex needs to run the repo's existing cleanup flow, remove Python cache artifacts, clear temp files, or tidy the workspace without deleting source files, `.venv`, or valid report bundle directories under `outputs/`.
---

# Cleanup

## Overview

Use this workflow to run the repo's built-in cleanup routine through the existing command path. Prefer the project utility over ad hoc deletion so the cleanup stays consistent and safe.

## Workflow

1. Confirm the request is about project cleanup rather than QA review.
2. Run the existing cleanup entrypoint from the project root: `python main.py --text "/cleanup"`.
3. Summarize what was removed, including the removed count and a short path preview when available.
4. State the safety boundary clearly if it matters: source files, `.venv`, `site-packages`, and valid output bundle directories must remain intact.

## When To Use

Use this skill for requests such as:

- "run cleanup"
- "clear the project cache"
- "delete temp files"
- "tidy the workspace before/after a QC run"

Do not route QA review requests here unless the user is explicitly asking to clean the workspace.

## Fallback

If the CLI entrypoint cannot run because of a shell or interpreter issue, call the same project utility from Python by importing `cleanup_project()` from `core.utils` and targeting the repo root. Keep the behaviour aligned with the built-in command rather than inventing a broader cleanup.

## Output Contract

Report:

- whether cleanup completed successfully
- how many items were removed
- a short preview of removed paths when present
- any limitation if the cleanup could not be executed

## Example Prompts

- `Use $cleanup to clear caches before the next QA pass.`
- `Use $cleanup to tidy the project workspace but keep reports.`
- `Use $cleanup to run the repo cleanup command and tell me what it removed.`
