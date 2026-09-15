#!/usr/bin/env python3
"""Read-only capability and workspace diagnostics shared by host adapters."""

import argparse
import importlib.util
import json
import pathlib
import shutil


ROOT = pathlib.Path(__file__).resolve().parents[1]


def _workspace_module(root):
    spec = importlib.util.spec_from_file_location("job_hunt_workspace", root / "bin" / "workspace-path.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect(root=ROOT, prefer=None):
    """Return JSON-safe diagnostics without creating files or contacting a network."""
    root = pathlib.Path(root).resolve()
    workspace = _workspace_module(root)
    path, _source, ask = workspace.resolve(prefer)
    if path:
        path = str(pathlib.Path(path).resolve())
    capabilities = {
        "python": "available",
        "pdf_renderer": "available" if shutil.which("pandoc") and shutil.which("xelatex") else "unavailable",
        "browser": "unknown",
        "logged_in_session": "unknown",
        "upload": "unknown",
    }
    issues = []
    if ask:
        issues.append({"code": "workspace-unconfigured", "message": ask})
    if capabilities["pdf_renderer"] == "unavailable":
        issues.append({"code": "pdf-renderer-unavailable", "message": "Markdown drafting remains available; PDF rendering is unavailable."})
    return {"workspace": path, "configured": bool(path), "capabilities": capabilities, "issues": issues}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefer")
    args = parser.parse_args(argv)
    print(json.dumps(collect(prefer=args.prefer), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
