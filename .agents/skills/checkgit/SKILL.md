---
name: checkgit
description: Check whether the current project checkout is up to date with its GitHub upstream and summarize recent project implementation activity from git history and the repo communication log.
---

# Checkgit

## Overview

Use this workflow when switching between devices, especially Windows and macOS laptops, to verify whether the local project checkout is current with the connected GitHub repository.

This is a read-only status workflow. It should not commit, pull, merge, rebase, reset, or delete files.

## Workflow

1. Run the project utility entrypoint from the repo root:
   - `python main.py --text "/checkgit"`
2. Review the reported branch, upstream, fetch status, ahead/behind counts, local HEAD, upstream HEAD, and uncommitted changes.
3. Review the recent implementation log, which combines recent git commits and recent entries from `docs/communication.md`.
4. Tell the user whether the checkout appears up to date, behind GitHub, ahead of GitHub, diverged, or blocked by missing upstream/fetch failure.

## Behavior Contract

The `/checkgit` command should:

- fetch the configured upstream when available
- compare the current branch with its upstream
- show whether the local checkout is ahead, behind, diverged, or up to date
- show relevant uncommitted changes separately from runtime/generated changes such as `outputs/` and `docs/communication.md`
- show recent git commits
- show recent project implementation activity from `docs/communication.md`
- avoid changing the worktree or staging area

## Interpretation

- `up-to-date`: local branch matches upstream after fetch.
- `behind`: GitHub has commits this checkout does not have yet; pull before continuing work.
- `ahead`: this checkout has local commits not pushed yet; use `$upgit` or push intentionally.
- `diverged`: both local and upstream have unique commits; inspect before pulling or pushing.
- `no-upstream`: branch has no configured upstream; set one or compare manually.

## Example Prompts

- `Use $checkgit to see if this laptop is up to date with GitHub.`
- `Run /checkgit before I switch devices.`
- `Check whether this Mac checkout has the latest project updates and summarize recent implementation history.`
