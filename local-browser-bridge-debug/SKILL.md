---
name: local-browser-bridge-debug
description: Use when a local web tool must open or reuse a browser session for authenticated collection, especially when bb-browser, Chrome CDP, ordinary Chrome/Edge, PyCharm, or Codex sandbox permissions are involved.
---

# Local Browser Bridge Debug

Diagnose browser bridges before changing application code. Keep browser control, local service access, and login-state ownership separate.

## Choose the connection path

| Need | Preferred path | Login state |
|---|---|---|
| Codex-only browser inspection | `chrome:control-chrome` / browser-client | Existing user Chrome session |
| Standalone PyCharm or PowerShell tool | `bb-browser` | bb-browser controlled profile |
| Existing CDP-enabled browser | Direct CDP on a known port | Profile attached to that port |

Treat `chrome:control-chrome` as a Codex connector, not a Python package.

## Preflight

1. Read project instructions and identify Web and collector port owners.
2. Run `where.exe bb-browser.cmd` and `bb-browser daemon status --json` as the same Windows user that runs the project.
3. Check candidate CDP ports (`9222`, `9333`, or configured ports) with `netstat -ano` and `/json/version`.
4. Check collector health without triggering a browser open.
5. Reproduce from external PowerShell or PyCharm if Codex returns `EPERM`; do not classify that as an application failure until the external run is tested.

## Application rules

- Project startup may prepare the collector service, but must not open a browser tab.
- Health checks are read-only and must never call `bb-browser open` as a fallback.
- Only an explicit user action such as `POST /open-login` may open the controlled browser.
- After opening, poll health or expose a recheck action; do not use page reload as detection.
- If an old collector occupies the default port, choose an unused endpoint for the new process instead of reusing unknown code.
- Track project-owned child processes and terminate only those children during graceful shutdown.

## Diagnose common failures

| Symptom | Check | Interpretation |
|---|---|---|
| `EPERM ... cdp-port` | Run the same command outside Codex | Sandbox or process isolation |
| `about:blank` opens at project start | Trace `daemon start` and `open` calls | Startup opens the browser too early |
| Refresh opens the platform page | Inspect health/eval fallback | Health contains an open fallback |
| Platform remains after browser close | Check live health, collector port, and profile state | Stale service, persistent login, or cached UI |
| External shell works but Codex fails | Compare process owner and profile path | Environment boundary |

## Verification

Verify that startup creates no browser window, `GET /health` calls no open command, the explicit open action calls `bb-browser open`, login makes a later health check queryable, and shutdown removes only project-owned child services.

Do not read, print, commit, or expose cookies, profile contents, or raw authentication headers.
