from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCheck:
    name: str
    kind: str
    available: bool
    version: str = ""
    path: str = ""
    note: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": self.kind,
            "available": self.available,
            "version": self.version,
            "path": self.path,
            "note": self.note,
        }


SYSTEM_TOOLS: dict[str, list[str]] = {
    "python": ["python", "--version"],
    "gh": ["gh", "--version"],
    "git": ["git", "--version"],
    "uv": ["uv", "--version"],
    "rg": ["rg", "--version"],
    "fd": ["fd", "--version"],
    "jq": ["jq", "--version"],
    "duckdb": ["duckdb", "--version"],
    "qpdf": ["qpdf", "--version"],
    "pdftotext": ["pdftotext", "-v"],
    "tesseract": ["tesseract", "--version"],
    "magick": ["magick", "--version"],
    "node": ["node", "--version"],
    "npm": ["npm.cmd", "--version"],
    "evidence": ["evidence.cmd", "--version"],
    "grist-ctl": ["grist-ctl", "--version"],
}

PYTHON_MODULES = [
    "duckdb",
    "pandas",
    "openpyxl",
    "pypdf",
    "fitz",
    "pdfplumber",
    "facturx",
    "docling",
    "rapidocr",
    "grist_api",
]


def _first_line(value: str) -> str:
    return value.replace("\r", "\n").split("\n", 1)[0].strip()


def _run_version(command: list[str]) -> tuple[str, str]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "", str(exc)
    output = completed.stdout.strip() or completed.stderr.strip()
    return _first_line(output), "" if completed.returncode == 0 else output


def system_tool_status() -> list[ToolCheck]:
    checks: list[ToolCheck] = []
    for name, command in SYSTEM_TOOLS.items():
        executable = shutil.which(command[0])
        if not executable:
            note = ""
            if name == "grist-ctl":
                note = "Non installe: binaire externe bloque par antivirus; utiliser Grist API Python."
            checks.append(ToolCheck(name=name, kind="system", available=False, note=note))
            continue
        version, error = _run_version([executable, *command[1:]])
        checks.append(
            ToolCheck(
                name=name,
                kind="system",
                available=True,
                version=version,
                path=executable,
                note=error,
            )
        )
    return checks


def python_module_status() -> list[ToolCheck]:
    checks: list[ToolCheck] = []
    for name in PYTHON_MODULES:
        spec = importlib.util.find_spec(name)
        checks.append(
            ToolCheck(
                name=name,
                kind="python",
                available=spec is not None,
                path=str(spec.origin) if spec and spec.origin else "",
                note="Optionnel" if name == "docling" and spec is None else "",
            )
        )
    return checks


def tools_status() -> dict[str, object]:
    checks = system_tool_status() + python_module_status()
    return {
        "python_runtime": sys.version.split()[0],
        "checks": [check.as_dict() for check in checks],
        "summary": {
            "available": sum(1 for check in checks if check.available),
            "missing": sum(1 for check in checks if not check.available),
        },
    }


def print_tools_status() -> None:
    print(json.dumps(tools_status(), indent=2, ensure_ascii=True))
