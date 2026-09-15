#!/usr/bin/env python3
"""Run a package-relative script without depending on a host environment."""

import argparse
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]


def resolve_script(root, relative):
    """Return an existing file strictly below *root*.

    Absolute paths and ``..`` escapes are intentionally not a convenience
    feature: callers choose a script shipped by this package, never a command
    assembled from untrusted text.
    """
    root = pathlib.Path(root).resolve()
    candidate = pathlib.Path(relative)
    if candidate.is_absolute():
        raise ValueError("script path must be package-relative")
    resolved = (root / candidate).resolve()
    if root not in resolved.parents or not resolved.is_file():
        raise ValueError("script must name a file inside this package")
    return resolved


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", help="package-relative Python script")
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        script = resolve_script(ROOT, args.script)
    except ValueError as error:
        parser.error(str(error))
    if script.suffix != ".py":
        parser.error("only Python scripts are supported by this launcher")
    return subprocess.run([sys.executable, str(script), *args.arguments]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
