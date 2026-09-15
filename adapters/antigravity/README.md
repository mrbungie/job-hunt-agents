# Antigravity adapter

Install project-scoped with `python3 bin/install-host.py --host antigravity
--project <project>`. Run `bin/preflight.py` explicitly. In particular, this
package does not treat `PreInvocation` as a session-start event and installs no
repeated preflight hook.

Use `mcp-chrome` only in the Chrome profile selected by the person at runtime;
`shared/browser-handoff.md` defines the required human handoffs.
