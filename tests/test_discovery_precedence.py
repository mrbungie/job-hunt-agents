#!/usr/bin/env python3
"""Contract for the broad job-discovery source cascade."""

import pathlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class DiscoveryPrecedence(unittest.TestCase):
    def test_broad_discovery_prefers_jobspy_then_browser_then_hiringcafe(self):
        path = ROOT / "shared" / "discovery-precedence.md"
        self.assertTrue(path.is_file(), "the discovery precedence policy is missing")
        policy = path.read_text(encoding="utf-8").casefold()
        jobspy = policy.index("1. jobspy")
        chrome = policy.index("2. mcp-chrome")
        hiringcafe = policy.index("3. hiringcafe")
        self.assertLess(jobspy, chrome)
        self.assertLess(chrome, hiringcafe)
        self.assertIn("jitter", policy)
        self.assertIn("challenge", policy)
        self.assertIn("human", policy)
        self.assertIn("do not use proxies", policy)

    def test_jobspy_rows_keep_the_upstream_site_and_stable_url_id(self):
        path = ROOT / "bin" / "jobspy.py"
        self.assertTrue(path.is_file(), "the JobSpy adapter is missing")
        spec = importlib.util.spec_from_file_location("jobspy_adapter", path)
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        rows = adapter.normalise_rows([{
            "site": "indeed",
            "job_url": "https://example.test/jobs/123",
            "title": "Platform Engineer",
            "company": "Example Ltd",
            "location": "Zurich",
        }])
        self.assertEqual(rows[0]["source"], "jobspy:indeed")
        self.assertEqual(rows[0]["ledger_id"], rows[0]["duplicate_key"])
        self.assertTrue(rows[0]["ledger_id"].startswith("jobspy:indeed:"))
        self.assertEqual(rows[0]["url"], "https://example.test/jobs/123")

    def test_importer_persists_jobspy_and_browser_provenance_without_duplicates(self):
        importer = ROOT / "bin" / "discovery-import.py"
        self.assertTrue(importer.is_file(), "the discovery importer is missing")
        ledger = """# Job pipeline\n\n## Ads\n\n| ID | Role | Company | Location / mode | Posted | Match | Pay | Status | Note |\n| :-- | :-- | :-- | :-- | :-- | --: | :-- | :-- | :-- |\n\n## Log\n"""
        records = [
            {"source": "jobspy:indeed", "url": "https://example.test/a",
             "title": "Engineer", "company": "Acme", "location": "Zurich"},
            {"source": "mcp-chrome:linkedin", "url": "https://example.test/b",
             "title": "Developer", "company": "Globex", "location": "Remote"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "job-pipeline.md"
            source = pathlib.Path(tmp) / "records.jsonl"
            path.write_text(ledger, encoding="utf-8")
            source.write_text("".join(json.dumps(row) + "\n" for row in records),
                              encoding="utf-8")
            command = [sys.executable, str(importer), "--file", str(path),
                       "--input", str(source)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            saved = path.read_text(encoding="utf-8")
            self.assertIn("origin=jobspy:indeed", saved)
            self.assertIn("origin=mcp-chrome:linkedin", saved)
            self.assertIn("url=https://example.test/a", saved)
            self.assertIn("| todo |", saved)
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(path.read_text(encoding="utf-8"), saved)
