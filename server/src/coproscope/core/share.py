from __future__ import annotations

from pathlib import Path

from .common import load_structured_file


def _normalized(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def audit_repo(repo_root: Path, config_path: Path) -> dict[str, list[str] | str]:
    config = load_structured_file(config_path)
    allowed = [str(item) for item in config.get("share_allowed_paths", [])]
    denied_prefixes = [str(item).rstrip("/") + "/" for item in config.get("never_share_prefixes", [])]
    denied_patterns = [str(item) for item in config.get("never_share_patterns", [])]

    shareable: list[str] = []
    blocked: list[str] = []
    ignored: list[str] = []

    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        rel = _normalized(path, repo_root)
        if any(rel.startswith(prefix) for prefix in denied_prefixes):
            blocked.append(rel)
            continue
        if any(pattern.lower() in rel.lower() for pattern in denied_patterns):
            blocked.append(rel)
            continue
        if any(rel == allowed_path.rstrip("/") or rel.startswith(allowed_path.rstrip("/") + "/") for allowed_path in allowed):
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
