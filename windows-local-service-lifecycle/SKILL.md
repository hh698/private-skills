---
name: windows-local-service-lifecycle
description: Use when developing or debugging a Windows local web tool that starts multiple services from PyCharm, PowerShell, or a Python entrypoint and must avoid stale processes, port reuse, orphan collectors, or incorrect shutdown behavior.
---

# Windows Local Service Lifecycle

Keep the Web service, collector service, browser daemon, and browser window as separate processes with explicit ownership.

## Startup contract

1. Read configured Web and collector hosts and ports.
2. Check whether the expected collector is healthy before starting another one.
3. If the default collector port belongs to an unknown or older process, choose an unused port and pass that endpoint to the new Web process.
4. Start the collector before declaring the Web page ready.
5. Do not open a browser during service startup. Browser launch belongs to an explicit user action.
6. Print the actual Web URL and collector endpoint used by this run.

## Process ownership

Record the `Popen` object for every child started by the project. On graceful shutdown:

1. Stop only recorded project-owned children.
2. Wait briefly for normal termination.
3. Force terminate only the child that did not exit.
4. Leave externally started services and browser processes alone.

Do not kill a process merely because it owns a port. First prove it is the project child or use a new port.

## Port diagnosis

Use PowerShell:

```powershell
Get-NetTCPConnection -LocalPort 8010,8011,8766,8767 -ErrorAction SilentlyContinue |
  Select-Object LocalPort,State,OwningProcess
netstat -ano | Select-String ':8010|:8011|:8766|:8767'
```

A `TIME_WAIT` entry is not a listening service. Only `LISTENING` blocks a new server. Confirm the process path before stopping it.

## PyCharm and PowerShell behavior

- Use the project `.venv\Scripts\python.exe`.
- Running `run.py` from a Python `>>>` prompt is a syntax error; run it from PowerShell or PyCharm.
- A child started with `Popen` can outlive the parent unless shutdown handling is registered.
- A force-stop from an IDE may skip graceful cleanup; use an owned-child registry and a fresh endpoint on the next run.

## Health and readiness

Define health as read-only. A health check may report `not ready`, `unauthorized`, or `collector unavailable`, but it must not start a browser or mutate login state. Keep readiness separate from authenticated platform availability.

## Verification checklist

Verify:

- first startup creates the expected Web and collector listeners;
- no browser window opens before a user action;
- restarting after a stale default port uses a fresh endpoint;
- normal PyCharm shutdown removes project-owned collector children;
- external collector processes are not terminated;
- the printed URL points to the current process, not an old tab or service.

Common failure: treating an old healthy HTTP response as proof that the current code is running. Add a service version or select a fresh endpoint when code identity matters.
