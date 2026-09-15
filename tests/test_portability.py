#!/usr/bin/env python3
"""Regression coverage for host-neutral packaging and installation."""

import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
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


class HostBundles(unittest.TestCase):
    def test_each_host_bundle_is_relocatable_and_has_one_skill_source(self):
        builder = load("build-host")
        with tempfile.TemporaryDirectory() as tmp:
            destination = pathlib.Path(tmp)
            for host in builder.HOSTS:
                bundle = builder.build(host, destination / host, ROOT)
                self.assertTrue((bundle / "skills" / "job-scan" / "SKILL.md").is_file())
                self.assertTrue((bundle / "bin" / "run.py").is_file())
                self.assertTrue((bundle / "HOST.md").is_file())
                self.assertEqual(len(list(bundle.rglob("job-scan/SKILL.md"))), 1)

    def test_unknown_host_is_refused(self):
        builder = load("build-host")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                builder.build("unknown", pathlib.Path(tmp), ROOT)


class ProjectInstallation(unittest.TestCase):
    def test_reinstall_is_idempotent_modified_file_is_preserved_and_uninstall_is_safe(self):
        installer = ROOT / "bin" / "install-host.py"
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp) / "project"
            project.mkdir()
            command = [sys.executable, str(installer), "--host", "codex", "--project", str(project)]
            self.assertEqual(subprocess.run(command, capture_output=True, text=True).returncode, 0)
            discovered = project / ".agents" / "skills" / "job-scan"
            self.assertTrue(discovered.is_symlink())
            self.assertEqual(discovered.resolve(), (project / ".job-hunt-agents" / "codex" / "skills" / "job-scan").resolve())
            self.assertEqual(subprocess.run(command, capture_output=True, text=True).returncode, 0)
            owned = project / ".job-hunt-agents" / "codex" / "HOST.md"
            owned.write_text("local edit\n", encoding="utf-8")
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("conflict", result.stderr.lower())
            self.assertEqual(owned.read_text(encoding="utf-8"), "local edit\n")
            result = subprocess.run(command + ["--uninstall"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertTrue(owned.exists())


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
