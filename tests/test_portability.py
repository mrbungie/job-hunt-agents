#!/usr/bin/env python3
"""Regression coverage for host-neutral packaging and installation."""

import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / "bin" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortableLauncher(unittest.TestCase):
    def test_resolves_a_package_relative_script_and_rejects_escape(self):
        run = load("run")
        self.assertEqual(
            run.resolve_script(ROOT, "bin/workspace-path.py"),
            ROOT / "bin" / "workspace-path.py")
        with self.assertRaises(ValueError):
            run.resolve_script(ROOT, "../outside.py")
        with self.assertRaises(ValueError):
            run.resolve_script(ROOT, str(ROOT / "bin/workspace-path.py"))


class Preflight(unittest.TestCase):
    def test_reports_a_named_workspace_without_creating_it(self):
        preflight = load("preflight")
        with tempfile.TemporaryDirectory() as tmp:
            workspace = pathlib.Path(tmp) / "candidate data"
            report = preflight.collect(ROOT, prefer=str(workspace))
            self.assertEqual(report["workspace"], str(workspace.resolve()))
            self.assertTrue(report["configured"])
            self.assertFalse(workspace.exists())
            self.assertEqual(report["capabilities"]["python"], "available")


class BrowserHandoff(unittest.TestCase):
    def test_mcp_chrome_handoff_requires_profile_choice_and_human_gates(self):
        handoff = (ROOT / "shared" / "browser-handoff.md").read_text(encoding="utf-8")
        handoff = " ".join(handoff.split()).casefold()
        for required in ("mcp-chrome", "which chrome profile", "captcha", "two-factor", "human", "do not submit"):
            self.assertIn(required, handoff)

    def test_active_browser_skills_do_not_depend_on_claude_chrome_tools(self):
        for relative in (
            "skills/job-scan/SKILL.md",
            "skills/cover-letter/SKILL.md",
            "skills/board-request/SKILL.md",
            "skills/linkedin-profile/SKILL.md",
            "skills/linkedin-watch/SKILL.md",
            "shared/boards/linkedin.md",
            "shared/prerequisites.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8").casefold()
            self.assertNotIn("mcp__claude-in-chrome", text, relative)
            self.assertIn("mcp-chrome", text, relative)


class CoverLetterRendering(unittest.TestCase):
    def test_cover_letter_requires_html_default_and_visual_pdf_qa(self):
        text = (ROOT / "skills/cover-letter/SKILL.md").read_text(encoding="utf-8").casefold()
        for phrase in ("html", "--engine latex", "mcp-chrome", "vision", "pdftotext", "screenshot"):
            self.assertIn(phrase, text)


class CvTemplateSetup(unittest.TestCase):
    def test_setup_requires_a_visual_pdf_template_and_change_skill_exists(self):
        setup = (ROOT / "shared/setup.md").read_text(encoding="utf-8").casefold()
        for phrase in ("visual template", "template-source.pdf", "html or latex", "vision"):
            self.assertIn(phrase, setup)
        skill = ROOT / "skills/cv-template/SKILL.md"
        self.assertTrue(skill.is_file())
        text = skill.read_text(encoding="utf-8").casefold()
        self.assertIn("change", text)
        self.assertIn("template-source.pdf", text)
