from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SERVER_ROOT = PACKAGE_ROOT.parents[2]

DEFAULT_DOCUMENT_FIELDS = [
    "doc_id",
    "instance_id",
    "entity_id",
    "scope",
    "sha256",
    "original_path",
    "file_name",
    "extension",
    "size_bytes",
    "last_modified",
    "first_seen",
    "source_zone",
    "source_kind",
    "lot",
    "document_type",
    "suspected_date",
    "emitter",
    "status_ocr",
    "classification_status",
    "text_path",
    "page_count",
    "text_char_count",
    "sensitivity",
    "notes",
]

REQUEST_FIELDS = [
    "request_id",
    "date",
    "subject",
    "expected_piece",
    "status",
    "last_follow_up",
    "priority",
    "response_due_date",
    "source_document",
    "related_doc_ids",
    "notes",
]

AG_FIELDS = [
    "ag_id",
    "doc_id",
    "file_name",
    "document_type",
    "detected_date",
    "resolution_count",
    "annex_hits",
    "majority_terms",
    "missing_annex_signals",
    "notes",
]

FINDING_FIELDS = [
    "finding_id",
    "category",
    "severity",
    "source_ref",
    "fact",
    "diligence",
    "status",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def safe_name(name: str, max_length: int = 150) -> str:
    cleaned = re.sub(r"[^\w.\- ]+", "_", name, flags=re.UNICODE).strip()
    return re.sub(r"\s+", "_", cleaned)[:max_length] or "document"


def append_note(existing: str, note: str) -> str:
    if not existing:
        return note
    if note in existing:
        return existing
    return f"{existing} | {note}"


def detect_date(value: str) -> str:
    match = re.search(r"(20\d{2})[-_. ]([01]\d)(?:[-_. ]([0-3]\d))?", value)
    if not match:
        return ""
    year, month, day = match.groups()
    if day:
        return f"{year}-{month}-{day}"
    return f"{year}-{month}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def resource_path(section: str, filename: str) -> Path:
    return PACKAGE_ROOT / section / filename


def load_structured_file(path: Path) -> Any:
    raw = path.read_text(encoding="utf-8-sig")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        if importlib.util.find_spec("yaml"):
            import yaml  # type: ignore

            return yaml.safe_load(raw)
        raise RuntimeError(
            f"Structured file {path} is not JSON-compatible YAML and PyYAML is not available."
        )


def load_template_csv(name: str) -> str:
    return resource_path("templates", name).read_text(encoding="utf-8")


def append_csv_row(path: Path, fieldnames: list[str], row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@dataclass
class InstanceConfig:
    path: Path
    payload: dict[str, Any]

    @property
    def instance_root(self) -> Path:
        return self.path.parent

    @property
    def instance_id(self) -> str:
        return str(self.payload["instance_id"])

    @property
    def display_name(self) -> str:
        return str(self.payload["display_name"])

    @property
    def scope(self) -> str:
        return str(self.payload.get("scope", "copro_simple"))

    @property
    def entity_id(self) -> str:
        return str(self.payload.get("entity_id", "main"))

    def resolve_path(self, value: str | None) -> Path | None:
        if not value:
            return None
        candidate = Path(value)
        if candidate.is_absolute():
            return candidate
        return (self.instance_root / candidate).resolve()

    def root(self, name: str) -> Path:
        value = self.payload.get("roots", {}).get(name)
        if value is None:
            raise KeyError(f"Missing root '{name}' in {self.path}")
        resolved = self.resolve_path(str(value))
        if resolved is None:
            raise KeyError(f"Unable to resolve root '{name}' in {self.path}")
        return resolved

    def root_list(self, name: str) -> list[Path]:
        values = self.payload.get("roots", {}).get(name, [])
        if isinstance(values, str):
            values = [values]
        return [self.resolve_path(str(item)) for item in values if self.resolve_path(str(item))]  # type: ignore[list-item]

    def register(self, name: str) -> Path:
        value = self.payload.get("registers", {}).get(name)
        if value is None:
            raise KeyError(f"Missing register '{name}' in {self.path}")
        resolved = self.resolve_path(str(value))
        if resolved is None:
            raise KeyError(f"Unable to resolve register '{name}' in {self.path}")
        return resolved

    def matrix(self, name: str) -> Path | None:
        value = self.payload.get("matrices", {}).get(name)
        return self.resolve_path(str(value)) if value else None

    def artifact(self, name: str) -> Path:
        value = self.payload.get("artifacts", {}).get(name)
        if value is None:
            fallback = self.root("staging") / name
            return fallback
        resolved = self.resolve_path(str(value))
        if resolved is None:
            raise KeyError(f"Unable to resolve artifact '{name}' in {self.path}")
        return resolved

    def env_files(self) -> list[Path]:
        values = self.payload.get("env", {}).get("files", [])
        if isinstance(values, str):
            values = [values]
        resolved: list[Path] = []
        for value in values:
            path = self.resolve_path(str(value))
            if path is not None:
                resolved.append(path)
        return resolved

    def required_env(self) -> list[str]:
        values = self.payload.get("env", {}).get("required", [])
        return [str(item) for item in values]

    def optional_env(self) -> list[str]:
        values = self.payload.get("env", {}).get("optional", [])
        return [str(item) for item in values]

    def settings(self) -> dict[str, Any]:
        return dict(self.payload.get("settings", {}))

    def classification_rules_path(self) -> Path:
        override = self.payload.get("config_overrides", {}).get("classification_rules")
        if override:
            resolved = self.resolve_path(str(override))
            if resolved is not None:
                return resolved
        return resource_path("configs", "taxonomy.default.yml")

    def completeness_rules_path(self) -> Path:
        override = self.payload.get("config_overrides", {}).get("document_completeness")
        if override:
            resolved = self.resolve_path(str(override))
            if resolved is not None:
                return resolved
        return resource_path("configs", "document_completeness.default.yml")

    def ag_rules_path(self) -> Path:
        override = self.payload.get("config_overrides", {}).get("ag_rules")
        if override:
            resolved = self.resolve_path(str(override))
            if resolved is not None:
                return resolved
        return resource_path("configs", "ag_rules.fr.yml")

    def sensitivity_rules_path(self) -> Path:
        override = self.payload.get("config_overrides", {}).get("sensitivity_rules")
        if override:
            resolved = self.resolve_path(str(override))
            if resolved is not None:
                return resolved
        return resource_path("configs", "sensitivity_rules.default.yml")


def load_instance(instance: str | None, instance_root: str | None) -> InstanceConfig:
    if instance:
        path = Path(instance)
        if path.is_dir():
            path = path / "instance.yml"
    elif instance_root:
        path = Path(instance_root) / "instance.yml"
    else:
        raise SystemExit("Provide --instance or --instance-root.")

    path = path.resolve()
    if not path.exists():
        raise SystemExit(f"Instance file not found: {path}")
    payload = load_structured_file(path)
    if not isinstance(payload, dict):
        raise SystemExit(f"Invalid instance payload in {path}")
    return InstanceConfig(path=path, payload=payload)


def relative_to(base: Path, target: Path) -> str:
    try:
        return str(target.relative_to(base))
    except ValueError:
        return str(target)


class RunContext:
    def __init__(self, instance: InstanceConfig, command: str) -> None:
        self.instance = instance
        self.command = command
        self.run_id = f"{slugify(command)}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        self.logs_dir = instance.root("logs")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.note(f"## {self.run_id}\n\n- command: `{command}`\n- instance: `{instance.instance_id}`\n")
        self.log_run("STARTED", "")

    def log_run(self, status: str, details: str) -> None:
        append_csv_row(
            self.logs_dir / "run_log.csv",
            ["timestamp", "run_id", "command", "status", "details"],
            {
                "timestamp": now_iso(),
                "run_id": self.run_id,
                "command": self.command,
                "status": status,
                "details": details,
            },
        )

    def log_action(self, action: str, target: Path, detail: str) -> None:
        append_csv_row(
            self.logs_dir / "action_log.csv",
            ["timestamp", "run_id", "action", "target", "detail"],
            {
                "timestamp": now_iso(),
                "run_id": self.run_id,
                "action": action,
                "target": str(target),
                "detail": detail,
            },
        )

    def log_error(self, error: str) -> None:
        append_csv_row(
            self.logs_dir / "error_log.csv",
            ["timestamp", "run_id", "command", "error"],
            {
                "timestamp": now_iso(),
                "run_id": self.run_id,
                "command": self.command,
                "error": error,
            },
        )

    def note(self, message: str) -> None:
        path = self.logs_dir / "agent_log.md"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(message.rstrip() + "\n\n")

    def finish(self, status: str = "OK", details: str = "") -> None:
        self.log_run(status, details)


def merge_category_rows(
    existing_rows: list[dict[str, str]],
    new_rows: list[dict[str, str]],
    category: str,
) -> list[dict[str, str]]:
    preserved = [row for row in existing_rows if row.get("category") != category]
    return preserved + new_rows


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def env_snapshot(instance: InstanceConfig) -> dict[str, str]:
    combined: dict[str, str] = {}
    for path in instance.env_files():
        combined.update(parse_env_file(path))
    for key in instance.required_env() + instance.optional_env():
        if os.environ.get(key):
            combined[key] = os.environ[key]
    return combined
