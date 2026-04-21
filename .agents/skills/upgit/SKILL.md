---
name: upgit
description: Clean the project, then save and push current changes to the connected GitHub repository. Use when Codex needs to run the repo's cleanup flow first, create a git commit for the current workspace, and push the active branch upstream safely.
---

# Upgit

## Overview

Use this workflow when the user wants one command that tidies the repo and then syncs the current branch to GitHub. Reuse the existing project command path instead of reconstructing the git steps manually unless the CLI path is unavailable.

## Workflow

1. Confirm the request is explicitly about saving and pushing the current workspace state.
2. Run the project utility entrypoint from the repo root: `python3 main.py --text "/upgit"`.
3. If the user provides a commit message, append it after the command, for example `python3 main.py --text "/upgit chore: update QC routing"`.
4. Summarize cleanup results, commit details, and push target honestly.

## Behavior Contract

The `/upgit` command should:

- run cleanup first
- avoid runtime/generated paths such as `docs/communication.md` and `outputs/` by default
- create a commit only from the remaining relevant workspace changes
- push to the current upstream when configured
- fall back to `origin/<branch>` only when no upstream exists and `origin` is available
- auto-generate a meaningful commit message when the user does not provide one
- report clearly when there is nothing new to commit or push

## Safety Notes

This workflow is narrower than a raw `git add -A`, but it is still repo-wide within the non-excluded paths. Do not describe it as a one-file or hand-curated commit unless the implementation actually supports that scope.

If push fails after commit creation, report that the commit exists locally and was not pushed successfully.

## Example Prompts

- `Use $upgit to clean and push the current repo state.`
- `Use $upgit to run cleanup, commit the current changes, and push them.`
- `Use $upgit with the message "chore: add upgit command".`
