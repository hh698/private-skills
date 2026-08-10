---
name: project-anchor-management
description: Use when a project has a named baseline, checkpoint, anchor, milestone, rollback point, or user-confirmed version and changes must preserve the agreed scope and avoid reverting unrelated work.
---

# Project Anchor Management

Treat a named anchor as a user-approved baseline, not as permission to discard later work.

## Create an anchor

When the user names an anchor such as `A` or `B`, record:

1. The exact scope and behavior the user approved.
2. The current branch, commit, and `git status --short` when available.
3. Important runtime facts: service ports, browser mode, login-state source, and test result.
4. Files or decisions explicitly outside the anchor.

Use a concise anchor note in the conversation. Create a Git tag or file only when the user asks for a persistent repository marker.

## Work after an anchor

Before changing code:

1. State which anchor the change starts from.
2. Separate requested changes from unrelated dirty-worktree changes.
3. Keep the anchor behavior intact unless the user explicitly changes it.
4. Add focused tests for the new behavior and preserve existing tests.

Do not assume that a new user request means revert to the anchor; it means modify the current state while using the anchor as a comparison point.

## Roll back safely

When the user asks to return to an anchor:

1. Confirm the anchor identifier and the intended rollback scope.
2. Compare the current tree with the recorded anchor state.
3. List files that would change and identify user changes made after the anchor.
4. Preserve unrelated user changes.
5. Ask for confirmation before deleting files, folders, large file sections, commits, or untracked artifacts.
6. Verify tests and runtime behavior after the rollback.

Never use `git reset --hard` or `git checkout --` as a shortcut. Prefer a targeted patch or a new branch or commit when history preservation matters.

## Anchor record template

```text
Anchor: B
Approved behavior: standalone PyCharm/PowerShell flow uses bb-browser controlled Chrome; startup does not open a browser; explicit button opens it.
Runtime: Web URL/port, collector URL/port, browser profile source.
Verification: command and result.
Change boundary: files or behavior intentionally excluded.
```

## Verification

At the end of anchor-related work, report the active anchor, what changed relative to it, what was preserved, and the verification result. Keep anchor notes short enough to reload in a future turn.
