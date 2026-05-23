from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


MAX_LINES = 600

SCOPED_ROOTS = ("server", "tools", ".github")
SCOPED_SUFFIXES = (
    ".py",
    ".pyfrag",
    ".html",
    ".css",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".ps1",
    ".psm1",
    ".psd1",
    ".toml",
    ".yml",
    ".yaml",
)
EXCLUDED_DIR_NAMES = frozenset(
    {
        ".cache",
        ".eggs",
        ".git",
        ".mypy_cache",
        ".nox",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".tmp-test",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
        "node_modules",
        "site-packages",
        "venv",
    }
)


@dataclass(frozen=True)
class LineLimitViolation:
    path: Path
    lines: int
    max_lines: int

    def format(self, repo_root: Path) -> str:
        relative = self.path.relative_to(repo_root).as_posix()
        return f"{relative}: {self.lines} lines (limit: {self.max_lines})"


def iter_scoped_code_files(repo_root: Path) -> Iterable[Path]:
    suffixes = {suffix.lower() for suffix in SCOPED_SUFFIXES}
    for root_name in SCOPED_ROOTS:
        scoped_root = repo_root / root_name
        if not scoped_root.exists():
            continue

        for directory, dirnames, filenames in os.walk(scoped_root, topdown=True):
            dirnames[:] = [name for name in dirnames if not _is_excluded_dir(name)]
            for filename in filenames:
                path = Path(directory) / filename
                if path.suffix.lower() in suffixes:
                    yield path


def find_violations(repo_root: Path, max_lines: int = MAX_LINES) -> list[LineLimitViolation]:
    violations: list[LineLimitViolation] = []
    for path in iter_scoped_code_files(repo_root):
        line_count = count_lines(path)
        if line_count > max_lines:
            violations.append(LineLimitViolation(path=path, lines=line_count, max_lines=max_lines))
    return sorted(violations, key=lambda violation: (-violation.lines, violation.path.as_posix()))


def count_lines(path: Path) -> int:
    lines = 0
    with path.open("rb") as file:
        for lines, _line in enumerate(file, 1):
            pass
    return lines


def scope_summary() -> str:
    roots = ", ".join(SCOPED_ROOTS)
    suffixes = ", ".join(SCOPED_SUFFIXES)
    excluded = ", ".join(sorted(EXCLUDED_DIR_NAMES))
    return (
        f"roots: {roots}; suffixes: {suffixes}; excluded directories: {excluded}. "
        "Docs, assets, binaries, examples, and generated caches are outside this guardrail."
    )


def format_violations(violations: Sequence[LineLimitViolation], repo_root: Path) -> str:
    return "\n".join(f"- {violation.format(repo_root)}" for violation in violations)


def _is_excluded_dir(name: str) -> bool:
    return name in EXCLUDED_DIR_NAMES or name.startswith(".tmp-")


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail when scoped code files exceed the CoproScope line-count cap."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=_default_repo_root(),
        help="Repository root to scan. Defaults to the parent of tools/.",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=MAX_LINES,
        help=f"Maximum allowed logical lines per scoped code file. Defaults to {MAX_LINES}.",
    )
    args = parser.parse_args(argv)

    repo_root = args.root.resolve()
    violations = find_violations(repo_root, max_lines=args.max_lines)
    if violations:
        print(f"Code line limit exceeded. Scope: {scope_summary()}", file=sys.stderr)
        print(format_violations(violations, repo_root), file=sys.stderr)
        return 1

    print(f"OK: no scoped code file exceeds {args.max_lines} lines. Scope: {scope_summary()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
