# Codex adapter

Install project-scoped with `python3 bin/install-host.py --host codex --project
<project>`. The bundle is self-contained and exposes its canonical `skills/`
tree; use the explicit `bin/preflight.py` diagnostic. No hook configuration is
generated because the local Codex hook contract was not live-validated here.

For browser work, configure the local `mcp-chrome` extension in the Chrome
profile the person selects at runtime. Its profile-selection and mandatory
human gates are in `shared/browser-handoff.md`.
