from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from ..core.common import InstanceConfig, write_text


GITHUB_MARKER = "github.com"

INSTANCE_GITIGNORE_LINES = (
    "# CoproScope instance: local Git only. Do not push this repository to GitHub.",
    "",
    "# Secrets and local OAuth state",
    ".env",
    ".env.*",
    "!.env.example",
    ".env.local",
    "**/.env.local",
    ".secrets/",
    "**/.secrets/",
    ".oauth/",
    "**/.oauth/",
    "credentials.json",
    "client_secret*.json",
    "token.json",
    "**/oauth/*.json",
    "",
    "# Local runtimes and caches",
    ".venv/",
    "**/.venv/",
    "__pycache__/",
    "**/__pycache__/",
    ".pytest_cache/",
    "**/.pytest_cache/",
    ".mypy_cache/",
    "**/.mypy_cache/",
    ".ruff_cache/",
    "**/.ruff_cache/",
    ".cache/",
    "**/.cache/",
    "node_modules/",
    "**/node_modules/",
    "",
    "# Host and transient files",
    "desktop.ini",
    "Thumbs.db",
    ".DS_Store",
    "*.tmp",
    "*.log",
    "~$*",
    "",
    "# Generated local workspaces often placed next to the private instance",
    "coproscope/",
    "_worktrees/",
    "public-export/",
    "",
)


def ensure_local_git_repo(
    instance: InstanceConfig,
    *,
    update_gitignore: bool = True,
    force_nested: bool = False,
) -> dict[str, Any]:
    root = instance.instance_root.resolve()
    parent_repo = _parent_git_repo(root)
    if parent_repo is not None and parent_repo != root and not _is_git_repo(root) and not force_nested:
        return {
            "ok": False,
            "status": "blocked_parent_git_repo",
            "instance_root": str(root),
            "parent_git_root": str(parent_repo),
            "message": "Instance root is already inside another Git worktree; pass --force-nested only after review.",
        }

    initialized = False
    if not _is_git_repo(root):
        _git(root, "init")
        _git(root, "symbolic-ref", "HEAD", "refs/heads/main", allow_failure=True)
        initialized = True

    _git(root, "config", "--local", "pull.ff", "only")
    _git(root, "config", "--local", "push.default", "nothing")
    _git(root, "config", "--local", "advice.detachedHead", "false")

    gitignore_updated = False
    if update_gitignore:
        gitignore_updated = ensure_instance_gitignore(root)

    status = inspect_instance_git(instance)
    status.update(
        {
            "initialized": initialized,
            "gitignore_updated": gitignore_updated,
            "policy": "local_instance_git_no_github_remote",
        }
    )
    return status


def inspect_instance_git(instance: InstanceConfig) -> dict[str, Any]:
    root = instance.instance_root.resolve()
    if not _is_git_repo(root):
        return {
            "ok": False,
            "status": "not_initialized",
            "instance_root": str(root),
            "is_git_repo": False,
            "has_github_remote": False,
            "remotes": [],
        }

    top_level = _git(root, "rev-parse", "--show-toplevel").strip()
    branch = _git(root, "branch", "--show-current", allow_failure=True).strip()
    remote_lines = _git(root, "remote", "-v", allow_failure=True).splitlines()
    remotes = [line.strip() for line in remote_lines if line.strip()]
    github_remotes = [line for line in remotes if GITHUB_MARKER in line.lower()]
    short_status = _git(root, "status", "--short", allow_failure=True).splitlines()

    return {
        "ok": not github_remotes,
        "status": "ok" if not github_remotes else "blocked_github_remote",
        "instance_root": str(root),
        "git_top_level": str(Path(top_level).resolve()) if top_level else "",
        "branch": branch,
        "is_git_repo": True,
        "has_github_remote": bool(github_remotes),
        "remotes": remotes,
        "github_remotes": github_remotes,
        "dirty_count": len(short_status),
        "gitignore_present": (root / ".gitignore").exists(),
    }


def ensure_instance_gitignore(root: Path) -> bool:
    path = root / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if not existing.strip():
        write_text(path, "\n".join(INSTANCE_GITIGNORE_LINES))
        return True

    existing_lines = existing.splitlines()
    existing_set = set(existing_lines)
    additions = [line for line in INSTANCE_GITIGNORE_LINES if line and line not in existing_set]
    if not additions and path.exists():
        return False

    lines = list(existing_lines)
    if lines and lines[-1] != "":
        lines.append("")
    if additions:
        lines.extend(additions)
    if not lines or lines[-1] != "":
        lines.append("")
    write_text(path, "\n".join(lines))
    return True


def _is_git_repo(root: Path) -> bool:
    return (root / ".git").exists()


def _parent_git_repo(root: Path) -> Path | None:
    result = _run_git(root, "rev-parse", "--show-toplevel", allow_failure=True)
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    return Path(text).resolve() if text else None


def _git(root: Path, *args: str, allow_failure: bool = False) -> str:
    result = _run_git(root, *args, allow_failure=allow_failure)
    if result.returncode != 0 and not allow_failure:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} failed in {root}: {detail}")
    return result.stdout


def _run_git(root: Path, *args: str, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 and not allow_failure:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} failed in {root}: {detail}")
    return result
