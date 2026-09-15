#!/usr/bin/env python3
"""Install one host bundle in a project without overwriting changed files."""

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ".job-hunt-manifest.json"


def _builder():
    spec = importlib.util.spec_from_file_location("build_host", ROOT / "bin" / "build-host.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _files(root):
    return {str(path.relative_to(root)): _digest(path) for path in root.rglob("*") if path.is_file() and path.name != MANIFEST}


def _load_manifest(destination):
    path = destination / MANIFEST
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _changed(destination, manifest):
    return [relative for relative, digest in manifest["files"].items() if not (destination / relative).is_file() or _digest(destination / relative) != digest]


def _remove_empty_parents(path, stop):
    while path != stop and path.exists() and not any(path.iterdir()):
        path.rmdir()
        path = path.parent


def install(host, project, dry_run=False, uninstall=False):
    builder = _builder()
    if host not in builder.HOSTS:
        raise ValueError(f"unsupported host: {host}")
    project = pathlib.Path(project).resolve()
    if not project.is_dir():
        raise ValueError(f"project is not a directory: {project}")
    destination = project / ".job-hunt-agents" / host
    previous = _load_manifest(destination) if destination.exists() else None
    if previous:
        changed = _changed(destination, previous)
        if changed:
            raise RuntimeError("conflict: changed owned files: " + ", ".join(changed))
    if uninstall:
        if not previous:
            return "nothing installed"
        if dry_run:
            return f"would remove {destination}"
        for relative in previous["files"]:
            target = destination / relative
            if target.exists():
                target.unlink()
                _remove_empty_parents(target.parent, destination)
        (destination / MANIFEST).unlink(missing_ok=True)
        _remove_empty_parents(destination, project)
        return f"removed {destination}"
    with tempfile.TemporaryDirectory() as tmp:
        bundle = builder.build(host, pathlib.Path(tmp) / host, ROOT)
        manifest = {"host": host, "files": _files(bundle)}
        if dry_run:
            return f"would install {host} into {destination}"
        destination.mkdir(parents=True, exist_ok=True)
        for relative in manifest["files"]:
            source, target = bundle / relative, destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        (destination / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return f"installed {host} into {destination}"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(install(args.host, args.project, args.dry_run, args.uninstall))
    except (ValueError, RuntimeError) as error:
        print(str(error), file=__import__("sys").stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
