#!/usr/bin/env python3
"""Run JobSpy as the first broad-discovery source and emit portable JSONL.

JobSpy is optional: importing it happens only after CLI parsing so the plugin
itself stays standard-library-only. This utility intentionally exposes no proxy
option; a block is a source result, not something to evade.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from typing import Any, Iterable


def _value(row: dict[str, Any], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() and str(value) != "nan":
            return str(value).strip()
    return ""


def normalise_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Keep JobSpy provenance and make URL identity stable across runs."""
    result = []
    for row in rows:
        site = _value(row, "site", "SITE").casefold() or "unknown"
        url = _value(row, "job_url", "JOB_URL")
        if not url:
            continue
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        ledger_id = f"jobspy:{site}:{digest}"
        result.append({
            "ledger_id": ledger_id,
            "duplicate_key": ledger_id,
            "source": f"jobspy:{site}",
            "url": url,
            "title": _value(row, "title", "TITLE"),
            "company": _value(row, "company", "COMPANY"),
            "location": _value(row, "location", "LOCATION"),
            "description": _value(row, "description", "DESCRIPTION"),
            "date_posted": _value(row, "date_posted", "DATE_POSTED"),
        })
    return result


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument("--sites", default="indeed,linkedin,google",
                        help="comma-separated JobSpy sites selected by the user")
    parser.add_argument("--results", type=int, default=25)
    parser.add_argument("--country-indeed", default=None)
    parser.add_argument("--hours-old", type=int, default=None)
    parser.add_argument("--remote", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = arguments()
    if args.results < 1:
        print("[jobspy] --results must be positive", file=sys.stderr)
        return 2
    options: dict[str, Any] = {
        "site_name": [site.strip() for site in args.sites.split(",") if site.strip()],
        "search_term": args.query,
        "location": args.location,
        "results_wanted": args.results,
        "is_remote": args.remote,
        "verbose": 0,
    }
    if args.country_indeed:
        options["country_indeed"] = args.country_indeed
    if args.hours_old is not None:
        options["hours_old"] = args.hours_old
    runner = (
        "import json,sys\n"
        "from jobspy import scrape_jobs\n"
        "options=json.load(sys.stdin)\n"
        "print(scrape_jobs(**options).to_json(orient='records', date_format='iso'))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", runner], input=json.dumps(options), text=True,
        capture_output=True, check=False)
    if result.returncode:
        error = result.stderr.strip()
        if "No module named 'jobspy'" in error:
            print("[jobspy] python-jobspy is not installed. Install it with: "
                  "python3 -m pip install -U python-jobspy", file=sys.stderr)
            return 3
        print(f"[jobspy] source unavailable: {error}", file=sys.stderr)
        return 4
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("[jobspy] source returned invalid JSON", file=sys.stderr)
        return 4
    for row in normalise_rows(rows):
        print(json.dumps(row, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
