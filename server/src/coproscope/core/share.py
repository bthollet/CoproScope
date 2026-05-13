from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from .common import load_structured_file


def _normalized(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def _matches_allowed(rel: str, allowed_paths: list[str]) -> bool:
    return any(rel == allowed_path.rstrip("/") or rel.startswith(allowed_path.rstrip("/") + "/") for allowed_path in allowed_paths)


def _matches_prefix(rel: str, prefixes: list[str]) -> bool:
    return any(rel == prefix.rstrip("/") or rel.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def _matches_pattern(rel: str, patterns: list[str]) -> bool:
    rel_lower = rel.lower()
    return any(pattern.lower() in rel_lower for pattern in patterns)


def audit_repo(repo_root: Path, config_path: Path) -> dict[str, list[str] | str]:
    config = load_structured_file(config_path)
    allowed = [str(item) for item in config.get("share_allowed_paths", [])]
    ignored_prefixes = [str(item).rstrip("/") + "/" for item in config.get("ignore_prefixes", [])]
    denied_prefixes = [str(item).rstrip("/") + "/" for item in config.get("never_share_prefixes", [])]
    denied_patterns = [str(item) for item in config.get("never_share_patterns", [])]

    shareable: list[str] = []
    blocked: list[str] = []
    ignored: list[str] = []

    for root, dirnames, filenames in os.walk(repo_root):
        root_path = Path(root)
        kept_dirs: list[str] = []

        for dirname in sorted(dirnames):
            dir_path = root_path / dirname
            rel_dir = _normalized(dir_path, repo_root)
            rel_dir_marker = rel_dir + "/"
            if _matches_prefix(rel_dir, ignored_prefixes):
                ignored.append(rel_dir_marker)
                continue
            if _matches_prefix(rel_dir, denied_prefixes) or _matches_pattern(rel_dir_marker, denied_patterns):
                blocked.append(rel_dir_marker)
                continue
            kept_dirs.append(dirname)

        dirnames[:] = kept_dirs

        for filename in sorted(filenames):
            path = root_path / filename
            rel = _normalized(path, repo_root)
            if _matches_prefix(rel, ignored_prefixes):
                ignored.append(rel)
                continue
            if _matches_prefix(rel, denied_prefixes) or _matches_pattern(rel, denied_patterns):
                blocked.append(rel)
                continue
            if _matches_allowed(rel, allowed):
                shareable.append(rel)
            else:
                ignored.append(rel)

    return {
        "repo_root": str(repo_root),
        "shareable": shareable,
        "blocked": blocked,
        "ignored": ignored,
        "public_repo_url": str(config.get("public_repo_url", "")),
    }


def export_shareable(repo_root: Path, config_path: Path, output_dir: Path, clean: bool = False) -> dict[str, object]:
    result = audit_repo(repo_root, config_path)
    destination = output_dir.resolve()
    repo_root = repo_root.resolve()

    if clean and destination.exists():
        if destination == repo_root or destination == repo_root.parent:
            raise ValueError(f"Refusing to clean unsafe destination: {destination}")
        shutil.rmtree(destination)

    destination.mkdir(parents=True, exist_ok=True)

    for rel in result["shareable"]:
        source = repo_root / str(rel)
        target = destination / str(rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    manifest = {
        "repo_root": result["repo_root"],
        "public_repo_url": result["public_repo_url"],
        "shareable": result["shareable"],
        "blocked": result["blocked"],
        "ignored": result["ignored"],
        "export_dir": str(destination),
        "exported_count": len(result["shareable"]),
    }
    manifest_path = destination / "share-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest
