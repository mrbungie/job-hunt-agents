#!/usr/bin/env python3
"""Contracts for the HTML-first application-document renderer."""

import os
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RENDER = ROOT / "skills" / "cover-letter" / "render.sh"


class HtmlRendering(unittest.TestCase):
    def fake_toolchain(self, directory):
        tools = pathlib.Path(directory) / "tools"
        tools.mkdir()
        pandoc = tools / "pandoc"
        pandoc.write_text(
            "#!/usr/bin/env bash\n"
            "set -e\n"
            "for ((i=1; i <= $#; i++)); do\n"
            "  if [ \"${!i}\" = -o ]; then j=$((i+1)); out=${!j}; fi\n"
            "done\n"
            "case \"$out\" in\n"
            "  *.html) printf '<!doctype html><html><body>CV preview</body></html>' > \"$out\" ;;\n"
            "  *) printf '%%PDF-1.4 latex\\n' > \"$out\" ;;\n"
            "esac\n")
        chrome = tools / "google-chrome"
        chrome.write_text(
            "#!/usr/bin/env bash\n"
            "set -e\n"
            "for arg in \"$@\"; do\n"
            "  case \"$arg\" in --print-to-pdf=*) printf '%%PDF-1.4 html\\n' > \"${arg#--print-to-pdf=}\" ;; esac\n"
            "done\n")
        xelatex = tools / "xelatex"
        xelatex.write_text("#!/usr/bin/env bash\nexit 0\n")
        uname = tools / "uname"
        uname.write_text("#!/usr/bin/env bash\necho Darwin\n")
        opener = tools / "open"
        opener.write_text("#!/usr/bin/env bash\ntouch \"$RENDER_OPEN_MARKER\"\n")
        for path in (pandoc, chrome, xelatex, uname, opener):
            path.chmod(0o755)
        return tools

    def render(self, args):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = root / "resume.md"
            pdf = root / "resume.pdf"
            source.write_text("# Ada Lovelace\n\n## Experience\n", encoding="utf-8")
            tools = self.fake_toolchain(root)
            env = os.environ.copy()
            env["PATH"] = f"{tools}:{env['PATH']}"
            marker = root / "opened"
            env["RENDER_OPEN_MARKER"] = str(marker)
            env["RENDER_NO_OPEN"] = "1"
            result = subprocess.run(
                [str(RENDER), *args, str(source), str(pdf)], text=True,
                capture_output=True, env=env, check=False)
            return result, pdf.exists(), pdf.read_bytes() if pdf.exists() else b"", \
                pdf.with_suffix(".html").exists(), marker.exists()

    def test_default_engine_renders_html_preview_and_pdf(self):
        result, exists, content, preview, opened = self.render([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("engine: html", result.stderr)
        self.assertTrue(exists)
        self.assertTrue(preview)
        self.assertFalse(opened)
        self.assertTrue(content.startswith(b"%PDF-1.4 html"))

    def test_latex_is_an_explicit_engine(self):
        result, exists, content, preview, opened = self.render(["--engine", "latex"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("engine: latex", result.stderr)
        self.assertTrue(exists)
        self.assertFalse(preview)
        self.assertFalse(opened)
        self.assertTrue(content.startswith(b"%PDF-1.4 latex"))

    def test_rejects_unknown_engine_before_rendering(self):
        result, exists, _content, _preview, _opened = self.render(["--engine", "ink"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown PDF engine", result.stderr)
        self.assertFalse(exists)

    def test_native_html_is_printed_without_markdown_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = root / "resume.html"
            pdf = root / "resume.pdf"
            source.write_text("<!doctype html><html><body><h1>Native HTML</h1></body></html>")
            tools = self.fake_toolchain(root)
            env = os.environ.copy()
            env["PATH"] = f"{tools}:{env['PATH']}"
            env["RENDER_NO_OPEN"] = "1"
            result = subprocess.run([str(RENDER), str(source), str(pdf)], text=True, capture_output=True, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("engine: html", result.stderr)
            self.assertTrue(pdf.read_bytes().startswith(b"%PDF-1.4 html"))
            self.assertIn("Native HTML", source.read_text())
