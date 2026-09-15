#!/usr/bin/env python3
"""Regenerate host packages from the canonical repository content.

Native hosts require their own package layout.  This script deliberately keeps
those generated layouts byte-for-byte aligned with the source skills instead of
turning any adapter into a second hand-maintained implementation.
"""

from __future__ import annotations

import pathlib
import shutil


ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGETS = (
    ROOT / "plugins" / "job-hunt-agents",
    ROOT / "adapters" / "antigravity" / "plugin",
)
CONTENT = ("skills", "shared", "templates", "bin")
EXCLUDED_BIN = {"build-host.py", "install-host.py", "sync-native-packages.py"}


def copy_tree(source: pathlib.Path, destination: pathlib.Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def sync_target(target: pathlib.Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for name in CONTENT:
        source = ROOT / name
        destination = target / name
        copy_tree(source, destination)
    for name in EXCLUDED_BIN:
        candidate = target / "bin" / name
        if candidate.exists():
            candidate.unlink()


def main() -> None:
    for target in TARGETS:
        sync_target(target)
        print(f"synced {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
