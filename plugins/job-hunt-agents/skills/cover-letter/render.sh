#!/usr/bin/env bash
# Render a document to a selectable-text PDF.
# Usage: render.sh [--engine html|latex] <input.html> <output.pdf> [letter]
set -euo pipefail

ENGINE="${JOB_HUNT_PDF_ENGINE:-html}"
if [ "${1:-}" = "--engine" ]; then
  [ -n "${2:-}" ] || { echo "ERROR: --engine needs html or latex" >&2; exit 2; }
  ENGINE="$2"
  shift 2
fi
case "$ENGINE" in html|latex) ;; *) echo "ERROR: unknown PDF engine: $ENGINE (use html or latex)" >&2; exit 2 ;; esac
[ $# -ge 2 ] && [ $# -le 3 ] || { echo "Usage: render.sh [--engine html|latex] <input.md> <output.pdf> [letter]" >&2; exit 2; }
IN="$1"; OUT="$2"; KIND="${3:-resume}"
DIR="$(cd "$(dirname "$0")" && pwd)"
[ -f "$IN" ] || { echo "ERROR: input does not exist: $IN" >&2; exit 2; }

open_pdf() {
  [ -n "${RENDER_NO_OPEN:-}" ] && return 0
  case "$(uname -s)" in
    Darwin) command -v open >/dev/null 2>&1 && open "$1" >/dev/null 2>&1 & ;;
    MINGW*|MSYS*|CYGWIN*) command -v cmd >/dev/null 2>&1 && cmd //c start "" "$1" >/dev/null 2>&1 & ;;
    *) command -v xdg-open >/dev/null 2>&1 && setsid xdg-open "$1" >/dev/null 2>&1 < /dev/null & ;;
  esac
}

plain_fallback() {
  echo "Falling back to render-plain.py — $1." >&2
  python3 "$DIR/render-plain.py" "$IN" "$OUT" --kind "$KIND" || true
  [ -s "$OUT" ] || { echo "ERROR: fallback wrote no PDF." >&2; exit 3; }
  echo "Wrote $OUT" >&2
  open_pdf "$OUT"
}

prepare_source() {
  TMPDIR_SRC="$(mktemp -d)"; trap 'rm -rf "$TMPDIR_SRC"' EXIT
  SRC="$TMPDIR_SRC/src.md"
  perl -CSD -pe 's/ ([:;!?])/\x{00A0}$1/g' "$IN" > "$SRC"
}

find_browser() {
  local candidate
  for candidate in google-chrome google-chrome-stable chromium chromium-browser chrome; do
    command -v "$candidate" >/dev/null 2>&1 && { command -v "$candidate"; return 0; }
  done
  for candidate in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" "/Applications/Chromium.app/Contents/MacOS/Chromium" "/c/Program Files/Google/Chrome/Application/chrome.exe"; do
    [ -x "$candidate" ] && { printf '%s\n' "$candidate"; return 0; }
  done
  return 1
}

render_html() {
  local browser template html css ws
  browser="$(find_browser)" || { plain_fallback "Chrome or Chromium is missing; install it for the HTML engine"; return; }
  if [[ "$IN" = *.html || "$IN" = *.htm ]]; then
    html="$IN"
    echo "engine: html (native source)" >&2
    "$browser" --headless=new --disable-gpu --allow-file-access-from-files --no-pdf-header-footer "--print-to-pdf=$OUT" "file://$html"
    [ -s "$OUT" ] || { echo "ERROR: Chrome did not write $OUT" >&2; exit 3; }
    echo "Wrote $OUT (HTML source: $html)" >&2
    open_pdf "$OUT"
    return
  fi
  command -v pandoc >/dev/null 2>&1 || { plain_fallback "pandoc is missing; install it for legacy Markdown input"; return; }
  ws="${JOB_HUNT_HOME:-}"
  if [ -z "$ws" ] && [ -x "$DIR/../../bin/workspace-path.py" ]; then
    ws="$(python3 "$DIR/../../bin/workspace-path.py" 2>/dev/null | tail -n 1 || true)"
  fi
  if [ -z "$ws" ] && [ -d "$HOME/Documents/job_applications" ]; then
    ws="$HOME/Documents/job_applications"
  fi

  template="$DIR/resume-template.html"
  [ "$KIND" = "letter" ] && template="$DIR/letter-template.html"
  if [ -n "$ws" ] && [ -d "$ws/profile/template" ]; then
    if [ "$KIND" = "letter" ] && [ -f "$ws/profile/template/letter-template.html" ]; then
      template="$ws/profile/template/letter-template.html"
    elif [ "$KIND" != "letter" ] && [ -f "$ws/profile/template/resume-template.html" ]; then
      template="$ws/profile/template/resume-template.html"
    fi
  fi

  css="$DIR/document.css"
  if [ -n "$ws" ] && [ -f "$ws/profile/template/document.css" ]; then
    css="$ws/profile/template/document.css"
  fi

  html="${OUT%.pdf}.html"
  prepare_source
  echo "engine: html" >&2
  pandoc "$SRC" --standalone --template="$template" --metadata "css=$css" -o "$html"
  "$browser" --headless=new --disable-gpu --allow-file-access-from-files --no-pdf-header-footer "--print-to-pdf=$OUT" "file://$html"
  [ -s "$OUT" ] || { echo "ERROR: Chrome did not write $OUT" >&2; exit 3; }
  echo "Wrote $OUT (HTML preview: $html)" >&2
  open_pdf "$OUT"
}

render_latex() {
  command -v pandoc >/dev/null 2>&1 || { plain_fallback "pandoc is missing"; return; }
  command -v xelatex >/dev/null 2>&1 || { plain_fallback "xelatex is missing"; return; }
  prepare_source
  local extra=() geometry fontsize
  if [ "$KIND" = "letter" ]; then
    geometry="top=2.4cm,bottom=2.4cm,left=2.2cm,right=2.2cm"; fontsize="11pt"; extra+=(--template="$DIR/letter-template.tex")
  else
    geometry="top=1.9cm,bottom=1.9cm,left=2cm,right=2cm"; fontsize="10pt"; extra+=(--template="$DIR/resume-template.tex" --shift-heading-level-by=-1)
  fi
  echo "engine: latex" >&2
  pandoc "$SRC" -o "$OUT" --pdf-engine=xelatex -V geometry:a4paper -V geometry:"$geometry" -V fontsize="$fontsize" -V colorlinks=true "${extra[@]}"
  [ -s "$OUT" ] || { echo "ERROR: XeLaTeX did not write $OUT" >&2; exit 3; }
  echo "Wrote $OUT" >&2
  open_pdf "$OUT"
}

if [ -n "${RENDER_PLAIN:-}" ]; then plain_fallback "RENDER_PLAIN was explicitly selected"
elif [ "$ENGINE" = "html" ]; then render_html
else render_latex
fi
