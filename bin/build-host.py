#!/usr/bin/env python3
"""Build a self-contained distribution for exactly one supported host."""

import argparse
import pathlib
import shutil


ROOT = pathlib.Path(__file__).resolve().parents[1]
HOSTS = ("claude", "codex", "antigravity", "opencode")
COMMON = ("bin", "skills", "shared", "templates", "commands")


HOST_NOTES = {
    "claude": "Claude Code uses the retained .claude-plugin manifest. Run bin/preflight.py explicitly; no hook is installed.",
    "codex": "Install creates .agents/skills links to this bundle. Run bin/preflight.py explicitly; no hook is installed.",
    "antigravity": "Install creates .agents/skills links to this bundle. Run bin/preflight.py explicitly; no PreInvocation hook is installed.",
    "opencode": "Install creates .opencode/skills links to this bundle. Run bin/preflight.py explicitly; no plugin is installed.",
}


def build(host, output, source=ROOT):
    if host not in HOSTS:
        raise ValueError(f"unsupported host: {host}")
    source, output = pathlib.Path(source).resolve(), pathlib.Path(output).resolve()
    if output.exists():
        raise ValueError(f"output already exists: {output}")
    output.mkdir(parents=True)
    for name in COMMON:
        shutil.copytree(source / name, output / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("README.md", "LICENSE"):
        shutil.copy2(source / name, output / name)
    if host == "claude":
        shutil.copytree(source / ".claude-plugin", output / ".claude-plugin")
    adapter = source / "adapters" / host
    if adapter.exists():
        shutil.copytree(adapter, output / "adapter")
    (output / "HOST.md").write_text(
        f"# Portable Job Hunt — {host}\n\n{HOST_NOTES[host]}\n\n"
        "This bundle has one physical copy of every skill under `skills/`. Browser, authenticated-session and upload support depend on the selected host setup.\n",
        encoding="utf-8")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, choices=HOSTS)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    print(build(args.host, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
