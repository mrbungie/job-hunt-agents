# HTML-first PDF Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make local Chrome HTML/CSS the default PDF engine, retain XeLaTeX explicitly, and require ATS plus visual validation.

**Architecture:** `render.sh` selects an engine. HTML rendering writes an adjacent local preview and uses local headless Chrome; the existing Pandoc/XeLaTeX route stays behind `--engine latex`. The canonical skill makes mcp-chrome + vision verification mandatory and package synchronisation copies it to native harnesses.

**Tech Stack:** Bash, Pandoc, local Chrome/Chromium, HTML/CSS, XeLaTeX, Poppler, Python unittest.

**Spec:** `docs/superpowers/specs/2026-09-15-html-pdf-rendering-design.md`

## Global Constraints

- Default engine is `html`; `--engine latex` and `JOB_HUNT_PDF_ENGINE=latex` select XeLaTeX.
- HTML conversion is local only; no remote service or browser download.
- Both engines produce selectable-text PDFs.
- mcp-chrome provides preview and visual QA, not assumed programmatic PDF export.
- Skills must require ATS extraction and visual/vision review.
- Canonical changes must be synced to Codex, Agy and OpenCode packages.

---

### Task 1: Implement and test engine selection

**Files:**
- Create: `skills/cover-letter/resume-template.html`, `skills/cover-letter/letter-template.html`, `skills/cover-letter/document.css`
- Modify: `skills/cover-letter/render.sh`, `tests/test_core.py`

**Interfaces:** `render.sh [--engine html|latex] <input.md> <output.pdf> [letter]` writes `<output>.html` for HTML and always writes `<output>.pdf`.

- [ ] Add failing `RenderHtml` tests that execute `render.sh` with fake Pandoc/Chrome/XeLaTeX executables; assert default stderr says `engine: html`, the HTML preview exists, and `--engine latex` invokes the TeX route.
- [ ] Run `python3 -m unittest tests.test_core.RenderHtml -v`; confirm selector/assets are missing.
- [ ] Add templates/CSS and change `render.sh`: parse `--engine`, default to `JOB_HUNT_PDF_ENGINE` or `html`, render Markdown to a standalone HTML preview, discover Chrome/Chromium, and call `--headless --print-to-pdf="$OUT"`. Move current Pandoc/XeLaTeX path under `latex`; retain explicit plain emergency fallback and clear unknown-engine errors.
- [ ] Re-run `python3 -m unittest tests.test_core.RenderHtml -v`; confirm green.
- [ ] Commit: `feat: render application PDFs from HTML by default`.

### Task 2: Encode required agent QA in canonical docs

**Files:**
- Modify: `skills/cover-letter/SKILL.md`, `README.md`, `shared/prerequisites.md`, `skills/cover-letter/render-plain.py`, `tests/test_portability.py`

**Interfaces:** Canonical cover-letter skill consumes generated `.html`/`.pdf` and an available user-selected mcp-chrome profile; it directs agents to validate before form filling.

- [ ] Add a failing documentation test that requires `--engine latex`, `mcp-chrome`, `vision`, `pdftotext`, and `screenshot` in the canonical cover-letter skill.
- [ ] Run `python3 -m unittest tests.test_portability.CoverLetterRendering -v`; confirm it fails for absent requirements.
- [ ] Document default HTML commands, optional LaTeX commands, cross-platform Chrome prerequisite, ATS checks (`pdfinfo`, `pdftotext`), mcp-chrome profile selection, full-page screenshots and vision review, re-render-on-defect, and mandatory human save-dialog handoff. Update plain-renderer wording so it is not called nominal.
- [ ] Re-run the documentation test; confirm green.
- [ ] Commit: `docs: require visual and ATS PDF validation`.

### Task 3: Ship generated packages and verify

**Files:**
- Modify: generated copies under `plugins/job-hunt-agents/`, `adapters/antigravity/plugin/`, `adapters/opencode/`, `tests/test_native_harnesses.py`

**Interfaces:** `bin/sync-native-packages.py` copies canonical `skills`, `shared`, `templates` and runtime `bin` trees to Codex and Agy. OpenCode's install instructions copy the same skill assets.

- [ ] Add a failing native-package test requiring `document.css`, HTML templates and `vision` instructions in every host copy.
- [ ] Run `python3 -m unittest tests.test_native_harnesses.NativeHarnessPackages -v`; confirm it fails before synchronisation.
- [ ] Run `python3 bin/sync-native-packages.py`; update OpenCode installation copy lists if needed.
- [ ] Real smoke render representative Markdown into a temporary PDF through the available default engine; validate `%PDF`, `pdfinfo`, `pdftotext -layout` and retained HTML preview. If Chrome is unavailable, preserve its explicit prerequisite failure rather than counting fallback output as HTML success.
- [ ] Run `python3 -m unittest discover -s tests -v`; confirm all tests pass.
- [ ] Commit generated assets and push `main`.
