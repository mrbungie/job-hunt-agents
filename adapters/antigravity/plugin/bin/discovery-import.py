#!/usr/bin/env python3
"""Persist JobSpy or mcp-chrome discovery JSONL into the job-pipeline ledger.

Rows are append-only `todo` discoveries. Existing rows — especially final
application outcomes — are never rewritten. Provenance lives in `Note` because
the established ledger schema deliberately has no separate source column.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile

def script_dir() -> str:
    """Find the sibling skill tree in a clone or a host package."""
    here = os.path.abspath(os.path.dirname(__file__))
    for root in (os.path.dirname(here), os.path.dirname(os.path.dirname(here))):
        candidate = os.path.join(root, "skills", "job-scan", "scripts")
        if os.path.isfile(os.path.join(candidate, "ledger.py")):
            return candidate
    raise RuntimeError("cannot locate skills/job-scan/scripts/ledger.py")


SCRIPT_DIR = script_dir()
sys.path.insert(0, SCRIPT_DIR)
import ledger  # noqa: E402  (loaded from the packaged job-scan utilities)


SOURCE = re.compile(r"^(?:jobspy|mcp-chrome):[a-z0-9_-]+$")
URL = re.compile(r"(?:^|[;\s])url=([^;\s|]+)")


def canonical_url(value: object) -> str:
    return str(value or "").strip().rstrip("/")


def identity(record: dict[str, object], source: str, url: str) -> str:
    given = str(record.get("ledger_id") or "").strip()
    if given:
        return given
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    return f"{source}:{digest}"


def read_records(path: str) -> list[dict[str, object]]:
    records = []
    try:
        with open(path, encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    ledger.die(f"{path}:{number}: invalid JSON: {error}")
                if not isinstance(record, dict):
                    ledger.die(f"{path}:{number}: expected one JSON object")
                records.append(record)
    except OSError as error:
        ledger.die(f"{path}: {error}")
    return records


def existing_urls(rows: list[dict[str, str]]) -> set[str]:
    urls = set()
    for row in rows:
        found = URL.search(row.get("Note", ""))
        if found:
            urls.add(canonical_url(found.group(1)))
    return urls


def imported_row(record: dict[str, object], source: str, url: str,
                 captured: str) -> dict[str, str]:
    return {
        "ID": identity(record, source, url),
        "Role": str(record.get("title") or "—"),
        "Company": str(record.get("company") or "—"),
        "Location / mode": str(record.get("location") or "—"),
        "Posted": str(record.get("date_posted") or "—"),
        "Match": str(record.get("match") or "—"),
        "Pay": str(record.get("pay") or "—"),
        "Status": "todo",
        "Note": f"origin={source}; captured={captured}; url={url}",
    }


def insert_before_log(text: str, rows: list[str]) -> str:
    if not rows:
        return text
    marker = re.search(r"^## (?!Ads)\S.*$", text, re.M)
    if not marker:
        ledger.die("ledger has no section after `## Ads`; refusing to guess where to insert")
    prefix = text[:marker.start()].rstrip("\n")
    suffix = text[marker.start():]
    return prefix + "\n" + "\n".join(rows) + "\n\n" + suffix


def write_atomic(path: str, text: str) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    descriptor, temporary = tempfile.mkstemp(prefix=".job-pipeline-", dir=directory,
                                             text=True)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", default=ledger.DEFAULT)
    parser.add_argument("--input", required=True, help="JSONL from JobSpy or mcp-chrome")
    args = parser.parse_args()

    text = ledger.read(args.file)
    columns, raw_rows = ledger.ads_table(text, args.file)
    required = {"ID", "Role", "Company", "Location / mode", "Posted", "Match", "Pay", "Status", "Note"}
    missing = sorted(required - set(columns))
    if missing:
        ledger.die(f"{args.file}: missing ledger columns: {', '.join(missing)}")
    rows = ledger.parsed(columns, raw_rows, args.file)
    ids = {row.get("ID", "") for row in rows}
    urls = existing_urls(rows)
    captured = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    additions = []
    added = skipped = 0

    for number, record in enumerate(read_records(args.input), 1):
        source = str(record.get("source") or "").strip().casefold()
        url = canonical_url(record.get("url"))
        if not SOURCE.fullmatch(source):
            ledger.die(f"{args.input}:{number}: source must be `jobspy:<site>` or `mcp-chrome:<board>`")
        if not url.startswith(("https://", "http://")):
            ledger.die(f"{args.input}:{number}: missing or invalid URL")
        values = imported_row(record, source, url, captured)
        if values["ID"] in ids or url in urls:
            skipped += 1
            continue
        additions.append(ledger.row(values, columns))
        ids.add(values["ID"])
        urls.add(url)
        added += 1

    if additions:
        write_atomic(args.file, insert_before_log(text, additions))
    print(json.dumps({"added": added, "duplicates": skipped, "file": args.file},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
