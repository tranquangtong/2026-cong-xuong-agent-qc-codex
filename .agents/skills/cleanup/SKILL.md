---
name: cleanup
description: Clean project cache and temporary files safely. Use when Codex needs to run the repo's existing cleanup flow, remove Python cache artifacts, clear temp files, or tidy the workspace without deleting source files, `.venv`, or valid report bundle directories under `outputs/`.
---

# Cleanup

## Overview

Use this workflow to run the repo's built-in cleanup routine through the existing command path. Prefer the project utility over ad hoc deletion so the cleanup stays consistent and safe.

This skill can also tidy old local Codex conversation history after project cleanup. Because that deletes local user data, do not delete chat history silently; prepare the exact target list and ask for explicit confirmation immediately before deletion.

## Workflow

1. Confirm the request is about project cleanup rather than QA review.
2. Run the existing cleanup entrypoint from the project root: `python main.py --text "/cleanup"`.
3. Offer the Codex conversation-history cleanup target list and, if the user confirms, delete only the known local history paths listed below.
4. Summarize what was removed, including the removed count and a short path preview when available.
5. State the safety boundary clearly if it matters: source files, `.venv`, `site-packages`, valid output bundle directories, Codex auth/config, plugins, skills, and memories must remain intact.

## Optional Codex Conversation History Cleanup

When `$cleanup` is run in Codex chat, also check whether old Codex conversations should be cleared. Use these targets only:

- `%USERPROFILE%\.codex\sessions\*`
- `%USERPROFILE%\.codex\archived_sessions\*`
- `%USERPROFILE%\.codex\session_index.jsonl`

Safety rules:

- This is local data deletion, so ask for explicit confirmation right before deleting it, even if the cleanup request sounded broad.
- Do not delete `%USERPROFILE%\.codex\auth.json`, `config.toml`, `plugins\`, `skills\`, `memories\`, `mcp\`, `.sandbox*`, `sqlite\`, `logs_*.sqlite`, or `state_*.sqlite`.
- Use PowerShell native cmdlets end to end; do not pipe discovered paths into `cmd.exe` or another shell.
- Before recursive deletion, resolve the absolute paths and confirm they are under `%USERPROFILE%\.codex\sessions` or `%USERPROFILE%\.codex\archived_sessions`.
- If the user does not confirm, skip chat-history deletion and report that project cleanup completed while Codex history was left intact.

## When To Use

Use this skill for requests such as:

- "run cleanup"
- "clear the project cache"
- "delete temp files"
- "tidy the workspace before/after a QC run"
- "cleanup and clear old Codex conversations"

Do not route QA review requests here unless the user is explicitly asking to clean the workspace.

## Fallback

If the CLI entrypoint cannot run because of a shell or interpreter issue, call the same project utility from Python by importing `cleanup_project()` from `core.utils` and targeting the repo root. Keep the behaviour aligned with the built-in command rather than inventing a broader cleanup.

## Output Contract

Report:

- whether cleanup completed successfully
- how many items were removed
- a short preview of removed paths when present
- whether Codex conversation history was deleted, skipped, or left pending confirmation
- any limitation if the cleanup could not be executed

## Example Prompts

- `Use $cleanup to clear caches before the next QA pass.`
- `Use $cleanup to tidy the project workspace but keep reports.`
- `Use $cleanup to run the repo cleanup command and tell me what it removed.`
- `Use $cleanup and clear old Codex conversations after confirming the deletion target list.`
