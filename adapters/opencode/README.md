# OpenCode adapter

Install project-scoped with `python3 bin/install-host.py --host opencode
--project <project>`. Run `bin/preflight.py` explicitly. No JavaScript plugin
is emitted: there is no narrow, verified hook behavior that improves the core
workflow, and the workflow works without hooks.

For optional browser work, use `mcp-chrome` in the Chrome profile selected by
the person. `shared/browser-handoff.md` defines the required human handoffs.
