#!/usr/bin/env python3
"""Native package contracts for local-clone installation paths."""

import json
import pathlib
import filecmp
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class NativeHarnessPackages(unittest.TestCase):
    def test_generated_native_skill_trees_match_canonical_source(self):
        source = ROOT / "skills"
        for target in (
            ROOT / "plugins" / "job-hunt-agents" / "skills",
            ROOT / "adapters" / "antigravity" / "plugin" / "skills",
        ):
            comparison = filecmp.dircmp(source, target)
            self.assertFalse(comparison.left_only, comparison.left_only)
            self.assertFalse(comparison.right_only, comparison.right_only)
            self.assertFalse(comparison.diff_files, comparison.diff_files)

    def test_codex_marketplace_has_a_valid_local_plugin(self):
        marketplace = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text())
        plugin = json.loads((ROOT / "plugins/job-hunt-agents/.codex-plugin/plugin.json").read_text())
        self.assertEqual(marketplace["name"], "job-hunt-agents")
        self.assertEqual(marketplace["plugins"][0]["source"]["path"], "./plugins/job-hunt-agents")
        self.assertEqual(plugin["name"], "job-hunt-agents")
        self.assertTrue((ROOT / "plugins/job-hunt-agents/skills/job-scan/SKILL.md").is_file())

    def test_agy_plugin_declares_skills_and_mcp(self):
        plugin_root = ROOT / "adapters/antigravity/plugin"
        manifest = json.loads((plugin_root / "plugin.json").read_text())
        mcp = json.loads((plugin_root / "mcp_config.json").read_text())
        self.assertEqual(manifest["name"], "job-hunt-agents")
        self.assertIn("mcp-chrome", mcp["mcpServers"])
        self.assertTrue((plugin_root / "skills/job-scan/SKILL.md").is_file())

    def test_opencode_workspace_configures_mcp_chrome(self):
        config = json.loads((ROOT / "adapters/opencode/opencode.json").read_text())
        server = config["mcp"]["mcp-chrome"]
        self.assertEqual(server["type"], "remote")
        self.assertEqual(server["url"], "http://127.0.0.1:12306/mcp")

    def test_readme_uses_native_local_install_commands(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for command in ("cp -R \"$REPO/skills/.\"", "agy plugin install", "opencode mcp add", "mcp-chrome-bridge register"):
            self.assertIn(command, readme)
        self.assertIn("Which\nChrome profile should I use?", readme)
        self.assertNotIn("plugin marketplace add", readme)
        self.assertNotIn("bin/install-host.py", readme)
