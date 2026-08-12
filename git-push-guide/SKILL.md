---
name: git-push-guide
description: Use when publishing local project changes to GitHub, pushing a newly initialized repository, handling git push failures, avoiding sensitive file uploads, syncing code to a user-provided GitHub repo, or falling back to gh api when Git HTTPS/credentials/network push is unreliable.
---

# Git Push Guide

## Overview

Publish code to GitHub with a security-first push flow: audit what will be tracked, verify the local commit, try normal Git push, then use GitHub CLI/API fallback only when the Git transport fails.

Core principle: never trade speed for accidentally publishing private inputs, generated outputs, credentials, or large local artifacts.

## Trigger Examples

Use this skill for requests like:
- "Push this project to my GitHub repo"
- "Sync this code to the repository"
- "git push failed; fix it"
- "The repo is newly created; add README and push"
- "GitHub is open in the browser; connect and upload the code"

## Push Workflow

1. Read project instructions first, especially rules about deletion and sensitive files.
2. Inspect state:
   ```powershell
   git status --short
   git remote -v
   git ls-files
   ```
3. Audit tracked files before committing or pushing. Look for requirement docs, exports, archives, env files, credentials, large outputs, generated reports, browser captures, and local databases.
4. If sensitive files are staged or tracked, ask before removing from Git tracking. Prefer `git rm --cached` so local files remain untouched.
5. Update `.gitignore` for patterns that should never be published.
6. Commit intentionally. Avoid `git add -A` until after the audit.
7. Verify:
   ```powershell
   git status --short
   git log --oneline -1 --stat
   git ls-files | Select-String -Pattern 'output|\.xlsx$|\.docx$|\.env$|secret|token|credential'
   ```
8. Push normally:
   ```powershell
   git push -u origin main
   ```
9. If push fails, diagnose before retrying blindly.

## Failure Handling

| Symptom | Meaning | Action |
|---|---|---|
| `dubious ownership` | Git does not trust the repo path for the current OS user | Run `git config --global --add safe.directory '<absolute path>'`, then retry |
| `gh auth status` token invalid | GitHub CLI session is broken | Ask user to run `gh auth login -h github.com` |
| `Recv failure: Connection was reset` | Git HTTPS transport failed before auth/content exchange | Retry once, then test `gh repo view owner/repo` |
| `Could not connect to server` from `git ls-remote` | Git transport cannot reach GitHub | If `gh api` works, use API fallback script |
| GitHub API JSON parse errors from PowerShell temp files | JSON was written with an incompatible encoding | Write JSON with `System.Text.UTF8Encoding($false)` |
| Protected branch/non-fast-forward | Remote has newer history or branch rules | Fetch/compare or ask before force/overwrite |

## API Fallback

Use `scripts/publish_with_gh_api.ps1` only after:
- Local tracked file audit passes.
- Tests or project verification pass.
- `gh auth status` succeeds.
- Git push or `git ls-remote` fails because of transport/network issues.

Run from the project root:

```powershell
F:\codex\.codex\skills\git-push-guide\scripts\publish_with_gh_api.ps1 `
  -Repository "owner/repo" `
  -Branch "main" `
  -Message "feat: publish project"
```

The script publishes exactly `git ls-files`, creates blobs via `gh api`, builds one tree and one commit, then updates the branch as a fast-forward. It blocks common sensitive patterns by default.

## Dirty Worktree and Skill Files

Before staging, separate the requested publish scope from unrelated work:

1. Read `git status --short` and inspect every modified file that could be included.
2. Never use `git add -A` when the worktree contains user changes, local databases, generated reports, browser profiles, or skill staging files.
3. Stage an explicit allowlist of project files, then inspect `git diff --cached --stat` and `git diff --cached`.
4. Treat files under `F:\codex\.codex\skills` as Codex environment artifacts, not as project files. Publish them only when the user explicitly asks to publish the skill source and the target repository is intended to contain it.
5. Respect named project anchors. Confirm whether the commit should represent the current state or a specific anchor before preparing a rollback or snapshot.

## GitHub Connector Routing

Use the GitHub connector skill for repository, issue, PR, and review orientation. Use local `git` and `gh` for the current checkout, branch, staging, commit, push, and checks that the connector cannot perform reliably. Resolve the local remote and branch before describing the GitHub state; never infer that an open GitHub browser tab is an authenticated Git transport.

For a new repository, verify in this order:

```powershell
git remote -v
git branch --show-current
git ls-remote origin
gh auth status
gh repo view owner/repo --json defaultBranchRef,isPrivate,url
```

When the repository is public, re-audit PDFs, spreadsheets, Word documents, raw browser data, SQLite databases, `.local_browser_profile`, `.env` files, tokens, and generated HTML before committing.

## Safety Rules

- Never push user-provided PDFs, Word docs, spreadsheets, raw exports, generated output folders, `.env`, tokens, cookies, or browser session captures unless the user explicitly says those exact artifacts may be public.
- When a blocked push is followed by user approval, clarify the approved scope if it is ambiguous. If removing sensitive files from Git tracking is clearly allowed, use `git rm --cached`, not file deletion.
- Do not use `git reset --hard`, branch force updates, or destructive cleanup unless the user explicitly requests it.
- Do not use GitHub API fallback to bypass branch protection or overwrite remote work.
- If the repository is public, treat all committed contents as permanently public.

## Quick Commands

```powershell
# Auth and remote checks
gh auth status
gh repo view owner/repo --json defaultBranchRef,isPrivate,url
git remote -v
git ls-remote origin

# Safe tracking removal, local file preserved
git rm --cached path\to\file

# Trust repo path after dubious ownership
git config --global --add safe.directory '<absolute path>'

# Verify remote after publish
gh api repos/owner/repo/git/trees/main?recursive=1 --jq .tree[].path
gh api repos/owner/repo/commits/main --jq .html_url
```

## Common Mistakes

| Mistake | Fix |
|---|---|
| Pushing immediately after `git init` | Audit `git status` and `git ls-files` first |
| Assuming `.gitignore` removes already tracked files | Use `git rm --cached` after updating `.gitignore` |
| Treating API fallback as equivalent to local `git push` | Verify it created one remote commit and inspect the tree |
| Uploading requirements/design artifacts by accident | Block `output/`, office docs, PDFs, exports, credentials by default |
| Retrying a network-reset push repeatedly | Retry once, then switch to diagnosis/API fallback |

## Completion Checklist

Before saying the push is complete, report:
- Remote repository URL.
- Latest commit SHA or commit URL.
- Verification performed.
- Whether any files were intentionally excluded from the push.
- Any remaining local-only files or auth/network caveats.
