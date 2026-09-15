# Codex adapter

Add this clone as a Codex marketplace with `codex plugin marketplace add .`,
then install `job-hunt-agents@job-hunt-agents`. Configure mcp-chrome with
`codex mcp add mcp-chrome --url http://127.0.0.1:12306/mcp`.

For browser work, configure the local `mcp-chrome` extension in the Chrome
profile the person selects at runtime. Its profile-selection and mandatory
human gates are in `shared/browser-handoff.md`.
