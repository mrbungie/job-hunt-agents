#!/usr/bin/env python3
"""Contract for the broad job-discovery source cascade."""

import pathlib
import importlib.util
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
