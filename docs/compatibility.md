# Host compatibility

The portable core is Python 3.9+ and standard-library only. Build and install
operations were fixture-tested locally on 2026-09-15; host runtimes and browser
backends were not live-tested by this change.

| Host | Package | Skills | Hooks | Browser/session/upload | Status |
| --- | --- | --- | --- | --- | --- |
| Claude Code | retained plugin manifest | upstream layout | none added | existing Claude integration only | package fixture-tested |
| Codex | project bundle | canonical `skills/` tree | explicit preflight only | unknown | package fixture-tested |
| Antigravity | project bundle | canonical `skills/` tree | explicit preflight only | unknown | package fixture-tested |
| OpenCode | project bundle | canonical `skills/` tree | explicit preflight only | unknown | package fixture-tested |

Run a preflight from an installed package before workflows that need local
files or a renderer:

```sh
python3 .job-hunt-agents/codex/bin/preflight.py
```

`browser`, `logged_in_session`, and `upload` deliberately remain `unknown`:
an executable on `PATH` is not evidence of an authenticated browser session.
For every host, [mcp-chrome](https://github.com/hangwin/mcp-chrome) is the
required backend when a workflow needs Chrome. The workflow asks the person to choose
their Chrome profile for each session and requires human takeover for CAPTCHA,
authentication, permissions, errors and every final submission; see
[`shared/browser-handoff.md`](../shared/browser-handoff.md).
Markdown drafting, scoring, the ledger, and HTTP/text work remain independently
available when browser or PDF support is absent.

No lifecycle hook is generated. A hook must be validated against that host's
actual event and output contract before it can be added; the explicit preflight
is read-only, has no network access, and is not required for core workflows.
