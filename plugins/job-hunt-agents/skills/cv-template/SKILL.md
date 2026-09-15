---
name: cv-template
description: Change or create the visual PDF template for generated CVs without changing the applicant's factual profile. Use when the user says "change my CV template", "use this PDF style", "make my CV look like this", "switch CV format", "pásalo a HTML", or "pásalo a LaTeX".
user-invocable: true
allowed-tools: Bash(*), Read, Write, Edit, AskUserQuestion
---

# Change the CV visual template

Ask for a PDF that is the **visual template**. It is not a source of facts:
never copy its name, employers, dates, skills or prose into the applicant's CV.

Resolve the workspace, ask the person to drop/select the PDF, validate it with
`file`, then copy it to `profile/template-source.pdf`. Render pages to PNG with
`pdftoppm -png -r 144`; use vision to inspect layout, hierarchy, font treatment,
margins, spacing, rules and page breaks. Ask whether they want **HTML** (default)
or **LaTeX**. Rebuild the visual format in `profile/template/`, preserving
single-column ATS reading order and selectable text. Render a neutral sample,
check it with `pdfinfo` and `pdftotext -layout`, then review screenshots with
vision. Report the chosen engine and source PDF. Changing the template never
edits `candidate.md`, `profile/.text/`, the ledger or prior applications.
