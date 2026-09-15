# Host compatibility

The portable core is Python 3.9+ and standard-library only. Native manifests
were validated locally on 2026-09-15; host runtimes and browser backends were
not live-tested by this change.

| Host | Package | Skills | Hooks | Browser/session/upload | Status |
| --- | --- | --- | --- | --- | --- |
| Claude Code | retained plugin manifest | upstream layout | none added | existing Claude integration only | package fixture-tested |
| Codex | Codex marketplace plugin | package `skills/` tree | none | mcp-chrome configured separately | manifest validated |
| Antigravity | local Agy plugin | package `skills/` tree | none | mcp-chrome in plugin configuration | CLI validated |
| OpenCode | project skills + config fragment | package `skills/` tree | none | mcp-chrome config fragment | schema fixture-tested |

Run a preflight from the clone before workflows that need local files or a
renderer:

```sh
python3 bin/preflight.py
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
