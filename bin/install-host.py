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


def _discovery_root(host):
    if host in ("codex", "antigravity"):
        return pathlib.Path(".agents") / "skills"
    if host == "opencode":
        return pathlib.Path(".opencode") / "skills"
    return None


def _links(host, project, destination, skills_root=None):
    discovery = _discovery_root(host)
    if discovery is None:
        return {}
    return {
        str(discovery / skill.name): os.path.relpath(destination / "skills" / skill.name, project / discovery)
        for skill in (skills_root or destination / "skills").iterdir() if skill.is_dir() and (skill / "SKILL.md").is_file()
    }


def _changed_links(project, links):
    changed = []
    for relative, target in links.items():
        path = project / relative
        if not path.is_symlink() or os.readlink(path) != target:
            changed.append(relative)
    return changed


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
        changed += _changed_links(project, previous.get("links", {}))
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
        for relative in previous.get("links", {}):
            target = project / relative
            if target.is_symlink():
                target.unlink()
                _remove_empty_parents(target.parent, project)
        (destination / MANIFEST).unlink(missing_ok=True)
        _remove_empty_parents(destination, project)
        return f"removed {destination}"
    with tempfile.TemporaryDirectory() as tmp:
        bundle = builder.build(host, pathlib.Path(tmp) / host, ROOT)
        manifest = {"host": host, "files": _files(bundle)}
        manifest["links"] = _links(host, project, destination, bundle / "skills")
        if dry_run:
            return f"would install {host} into {destination}"
        for relative, target in manifest["links"].items():
            link = project / relative
            if (link.exists() or link.is_symlink()) and (not link.is_symlink() or os.readlink(link) != target):
                raise RuntimeError(f"conflict: discovery path already exists: {relative}")
        destination.mkdir(parents=True, exist_ok=True)
        for relative in manifest["files"]:
            source, target = bundle / relative, destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for relative, target in manifest["links"].items():
            link = project / relative
            if not (link.exists() or link.is_symlink()):
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(target)
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
