# HTML-first PDF rendering

## Decision

CVs and cover letters remain authored as Markdown. The rendering contract becomes
HTML-first: the default engine renders Markdown into the project HTML/CSS template
and emits a PDF. XeLaTeX remains a supported explicit engine, not the default.
Every successful engine produces a PDF with selectable, correctly ordered text.

## Engines and interface

`skills/cover-letter/render.sh` accepts `--engine html|latex` before its existing
document arguments. Omitting it selects `html`. `JOB_HUNT_PDF_ENGINE=latex` is an
equivalent non-interactive override. The existing `letter` kind remains supported.

The HTML engine uses Pandoc to create a complete local HTML document and a dedicated
CSS template. It then uses a locally installed Chrome/Chromium executable in headless
print-to-PDF mode. The renderer probes known executable names and platform locations,
and reports the exact missing prerequisite. It must not download a browser or use a
remote conversion service.

The LaTeX engine preserves the current Pandoc + XeLaTeX templates and behavior under
`--engine latex`. The dependency-free `render-plain.py` route remains an explicitly
reported last-resort fallback, never the normal HTML result.

## Browser and human boundaries

The agent opens the generated local HTML in the user-selected `mcp-chrome` profile
when that connection is available. It takes a full-page screenshot and uses vision to
inspect hierarchy, clipping, overflow, page breaks, spacing, and accidental blank or
nearly empty pages. It does not call a PDF "looks good" merely because its text can
be extracted.

`mcp-chrome`'s documented tools provide navigation, screenshots, content and keyboard
interaction, but do not provide a programmatic PDF export operation. Therefore it is
the preferred preview/visual-QA route; the deterministic local Chrome headless command
creates the default PDF. If a host exposes a print-to-PDF operation in a future
mcp-chrome version, agents may use it only after the preview passes. If it opens the
native print dialog, saving is a mandatory human handoff; agents must never claim the
PDF was saved until the resulting file exists and passes validation.

## Required agent workflow

The cover-letter skill will state this sequence rather than leaving it implicit:

1. Render HTML-first to PDF (or honour an explicit LaTeX request).
2. Run ATS checks on the generated PDF: non-empty, `pdfinfo` page count and
   `pdftotext -layout` has expected name/contact, headings, titles and no mangled
   obvious text.
3. Open the matching generated HTML through mcp-chrome in the confirmed profile,
   capture every page/full-page view, and inspect it with vision. For a PDF that can
   be opened directly, inspect the rendered PDF too. Check for clipping, overlapping
   lines, bad page split, detached headings, illegible text, unexpected blank page and
   resume page-length target.
4. If either semantic/ATS or visual QA fails, revise and re-render. Report the engine,
   checks performed and any remaining limitation. Do not proceed to form filling with
   an unverified attachment.

This browser access inherits all existing profile-selection and human gates:
authentication, CAPTCHA, permission prompts, native print/save dialogs, and final
application submission remain human-controlled.

## Repository scope and tests

Source-of-truth files are the cover-letter renderer, HTML templates/CSS, the
cover-letter skill, README prerequisites and portability documentation. The native
Codex, Agy and OpenCode packages are generated from those sources and must be synced.

Tests will establish that the default invocation selects HTML, that `--engine latex`
selects the existing TeX path, that both paths create a valid selectable-text PDF using
test doubles for external executables, and that all host copies contain the mandatory
render-and-visual-QA instructions. A real local smoke test will render a representative
resume with the available engine and validate its PDF metadata/text; screenshot review
will be performed through mcp-chrome only when a connected user profile is available.
