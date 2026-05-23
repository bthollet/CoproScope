from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.event_types import (
    ACTION_CREATED,
    CLASSIFICATION_COMPLETED,
    COMMENT_ADDED,
    DIFFUSION_DECIDED,
    EXPORT_CREATED,
    OCR_COMPLETED,
    PASSATION_EXPORT_CREATED,
    PLUGIN_ACTIVATED,
    PLUGIN_RESULT_RECORDED,
    POINT_CREATED,
    REDACTION_COMPLETED,
    REQUEST_ACTION_RECORDED,
    REQUEST_CREATED,
)
from . import core


RECONSTRUCTION_DB_FILE = "vault_reconstruction.sqlite3"
DEFAULT_PROJECTION_PROJECTOR_ID = "coproscope.vault.reconstruction"
DEFAULT_PROJECTION_PROJECTOR_VERSION = "2026-05-22.incremental-v1"
CONFLICT_RESOLUTION_EVENTS = {"conflict_resolved", "status_conflict_resolved"}
DOCUMENT_EVENT_TYPES = {"document_added", "document_version_added"}
PLUGIN_RUN_EVENT_TYPES = {OCR_COMPLETED, PLUGIN_ACTIVATED, PLUGIN_RESULT_RECORDED}
EXPORT_EVENT_TYPES = {EXPORT_CREATED, PASSATION_EXPORT_CREATED}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _value_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return _canonical_json(value)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


@dataclass(frozen=True)
class ReconstructionEvent:
    event_id: str
    event_type: str
    object_id: str
    created_at: str
    author_key_id: str
    device_id: str
    sequence: int
    event_hash: str
    event_path: str
    payload: Mapping[str, Any]
    envelope: Mapping[str, Any]

    @classmethod
    def from_envelope(
        cls,
        envelope: Mapping[str, Any],
        payload: Mapping[str, Any],
        *,
        event_hash: str = "",
        event_path: str = "",
    ) -> "ReconstructionEvent":
        sequence = envelope.get("sequence", 0)
        try:
            sequence_int = int(sequence)
        except (TypeError, ValueError):
            sequence_int = 0
        envelope_dict = dict(envelope)
        payload_dict = dict(payload)
        return cls(
            event_id=str(envelope.get("event_id", "")),
            event_type=str(envelope.get("event_type", "")),
            object_id=str(envelope.get("object_id", "")),
            created_at=str(envelope.get("created_at", "")),
            author_key_id=str(envelope.get("author_key_id", "")),
            device_id=str(envelope.get("device_id", "")),
            sequence=sequence_int,
            event_hash=event_hash or _sha256_text(_canonical_json(envelope_dict)),
            event_path=event_path,
            payload=payload_dict,
            envelope=envelope_dict,
        )


def default_reconstruction_db_path(local_root: Path) -> Path:
    return Path(local_root).expanduser().resolve() / RECONSTRUCTION_DB_FILE


def resolve_reconstruction_db_path(local_root: Path, db_path: Path | None = None) -> Path:
    local = Path(local_root).expanduser().resolve()
    resolved = default_reconstruction_db_path(local) if db_path is None else Path(db_path).expanduser().resolve()
    if not _is_relative_to(resolved, local):
        raise RuntimeError(f"Reconstruction cache must stay under the local root: {resolved}")
    return resolved


def iter_event_paths(sync_root: Path) -> list[Path]:
    event_root = Path(sync_root).expanduser().resolve() / "events"
    if not event_root.exists():
        return []
    return sorted(path for path in event_root.glob("*/*.json") if path.is_file())


def load_key_records(sync_root: Path) -> list[dict[str, Any]]:
    key_root = Path(sync_root).expanduser().resolve() / "keys"
    if not key_root.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(key_root.glob("*.json")):
        payload = _read_json(path)
        if not isinstance(payload, dict):
            raise RuntimeError(f"Invalid public key record: {path}")
        payload.setdefault("key_path", str(path))
        records.append(payload)
    return records


def load_verified_events(
    local_root: Path,
    sync_root: Path,
    *,
    verify_result: Mapping[str, Any] | None = None,
) -> list[ReconstructionEvent]:
    local = Path(local_root).expanduser().resolve()
    sync = Path(sync_root).expanduser().resolve()
    verification = verify_result or core.vault_verify(local, sync)
    if not verification.get("valid", False):
        errors = verification.get("errors", [])
        detail = "; ".join(str(error) for error in errors[:5]) if isinstance(errors, Sequence) else str(errors)
        raise RuntimeError(f"Cannot reconstruct an invalid vault: {detail}")

    events: list[ReconstructionEvent] = []
    for path in iter_event_paths(sync):
        raw = path.read_bytes()
        envelope = json.loads(raw.decode("utf-8"))
        if not isinstance(envelope, dict):
            raise RuntimeError(f"Invalid event envelope: {path}")
        payload = core.vault_export_debug_payload(local, sync, path)
        events.append(
            ReconstructionEvent.from_envelope(
                envelope,
                payload,
                event_hash=_sha256_bytes(raw),
                event_path=str(path),
            )
        )
    return sorted(events, key=_event_sort_key)


def rebuild_local_cache(local_root: Path, sync_root: Path, db_path: Path | None = None) -> dict[str, Any]:
    local = Path(local_root).expanduser().resolve()
    sync = Path(sync_root).expanduser().resolve()
    resolved_db_path = resolve_reconstruction_db_path(local, db_path)
    verification = core.vault_verify(local, sync)
    if not verification.get("valid", False):
        errors = verification.get("errors", [])
        detail = "; ".join(str(error) for error in errors[:5]) if isinstance(errors, Sequence) else str(errors)
        raise RuntimeError(f"Cannot rebuild local cache from invalid vault: {detail}")

    vault_id = ""
    vault_json = sync / "vault.json"
    if vault_json.exists():
        vault_payload = _read_json(vault_json)
        if isinstance(vault_payload, dict):
            vault_id = str(vault_payload.get("vault_id", ""))

    events = load_verified_events(local, sync, verify_result=verification)
    return rebuild_cache_from_events(events, resolved_db_path, vault_id=vault_id, key_records=load_key_records(sync))


def rebuild_cache_from_events(
    events: Iterable[ReconstructionEvent],
    db_path: Path,
    *,
    vault_id: str = "",
    key_records: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    path = Path(db_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered_events = sorted(list(events), key=_event_sort_key)

    connection = sqlite3.connect(str(path))
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        _reset_schema(connection)
        with connection:
            _insert_meta(connection, vault_id=vault_id, event_count=len(ordered_events))
            _seed_identities(connection, key_records or [])
            status_observations: list[dict[str, Any]] = []
            resolved_status_keys: set[tuple[str, str]] = set()

            for event_order, event in enumerate(ordered_events, start=1):
                _insert_event_log(connection, event_order, event)
                _record_identity_event(connection, event)
                _record_document_event(connection, event)
                _record_business_object_event(connection, event)
                observation = _record_status_event(connection, event)
                if observation is not None:
                    status_observations.append(observation)
                resolved_status_keys.update(_resolved_status_keys(event))
                _mark_event_applied(connection, event)

            conflicts = _detect_status_conflicts(status_observations, resolved_status_keys)
            _insert_conflicts(connection, conflicts)
    finally:
        connection.close()

    read_connection = sqlite3.connect(str(path))
    try:
        return {
            "ok": True,
            "command": "vault reconstruct",
            "db_path": str(path),
            "vault_id": vault_id,
            "events": _count_rows(read_connection, "event_log"),
            "documents": _count_rows(read_connection, "documents"),
            "identities": _count_rows(read_connection, "identities"),
            "status_observations": _count_rows(read_connection, "status_observations"),
            "conflicts": _count_rows(read_connection, "conflicts"),
            "points": _count_rows(read_connection, "points"),
            "actions": _count_rows(read_connection, "actions"),
            "expected_pieces": _count_rows(read_connection, "expected_pieces"),
            "requests": _count_rows(read_connection, "requests"),
            "object_links": _count_rows(read_connection, "object_links"),
            "projection_events": _count_rows(read_connection, "event_applied"),
            "projection_meta": _count_rows(read_connection, "projection_meta"),
        }
    finally:
        read_connection.close()


def apply_incremental_events(
    events: Iterable[ReconstructionEvent],
    db_path: Path,
    *,
    vault_id: str = "",
    key_records: Iterable[Mapping[str, Any]] | None = None,
    projector_id: str = DEFAULT_PROJECTION_PROJECTOR_ID,
    projector_version: str = DEFAULT_PROJECTION_PROJECTOR_VERSION,
) -> dict[str, Any]:
    """Replay only events that have not already been applied by this projector."""

    path = Path(db_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered_events = sorted(list(events), key=_event_sort_key)
    applied_events = 0
    skipped_events = 0

    connection = sqlite3.connect(str(path))
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            _ensure_reconstruction_schema(
                connection,
                vault_id=vault_id,
                key_records=key_records or [],
            )
            _backfill_projection_events_from_event_log(
                connection,
                projector_id=projector_id,
                projector_version=projector_version,
            )
            for event in ordered_events:
                if _event_already_applied(
                    connection,
                    event,
                    projector_id=projector_id,
                    projector_version=projector_version,
                ):
                    skipped_events += 1
                    continue
                _insert_event_log_if_missing(connection, event)
                _apply_projection_event(connection, event)
                _mark_event_applied(
                    connection,
                    event,
                    projector_id=projector_id,
                    projector_version=projector_version,
                )
                applied_events += 1
            if applied_events:
                _refresh_status_conflicts(connection)
            projection_state = _refresh_projection_meta(
                connection,
                projector_id=projector_id,
                projector_version=projector_version,
            )
    finally:
        connection.close()

    read_connection = sqlite3.connect(str(path))
    try:
        return {
            "ok": True,
            "command": "vault project-incremental",
            "db_path": str(path),
            "vault_id": vault_id,
            "events": _count_rows(read_connection, "event_log"),
            "applied_events": applied_events,
            "skipped_events": skipped_events,
            "documents": _count_rows(read_connection, "documents"),
            "identities": _count_rows(read_connection, "identities"),
            "status_observations": _count_rows(read_connection, "status_observations"),
            "conflicts": _count_rows(read_connection, "conflicts"),
            "points": _count_rows(read_connection, "points"),
            "actions": _count_rows(read_connection, "actions"),
            "expected_pieces": _count_rows(read_connection, "expected_pieces"),
            "requests": _count_rows(read_connection, "requests"),
            "object_links": _count_rows(read_connection, "object_links"),
            "projection_events": _count_rows(read_connection, "event_applied"),
            "projection_meta": _count_rows(read_connection, "projection_meta"),
            **projection_state,
        }
    finally:
        read_connection.close()


def mark_event_applied(
    db_path: Path,
    event: ReconstructionEvent,
    *,
    projector_id: str = DEFAULT_PROJECTION_PROJECTOR_ID,
    projector_version: str = DEFAULT_PROJECTION_PROJECTOR_VERSION,
    applied_at: str | None = None,
) -> dict[str, Any]:
    """Record an event as already applied to a local projection without replaying it."""

    path = Path(db_path).expanduser().resolve()
    connection = sqlite3.connect(str(path))
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        _ensure_projection_tracking_schema(connection)
        _require_reconstruction_schema(connection)
        with connection:
            return _mark_event_applied(
                connection,
                event,
                projector_id=projector_id,
                projector_version=projector_version,
                applied_at=applied_at,
            )
    finally:
        connection.close()


def apply_event_once(
    db_path: Path,
    event: ReconstructionEvent,
    apply_callback: Callable[[sqlite3.Connection, ReconstructionEvent], Mapping[str, Any] | None],
    *,
    projector_id: str = DEFAULT_PROJECTION_PROJECTOR_ID,
    projector_version: str = DEFAULT_PROJECTION_PROJECTOR_VERSION,
    applied_at: str | None = None,
) -> dict[str, Any]:
    """Apply one event to a projection, skipping the callback if it was already applied."""

    path = Path(db_path).expanduser().resolve()
    connection = sqlite3.connect(str(path))
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        _require_reconstruction_schema(connection)
        with connection:
            if _event_already_applied(
                connection,
                event,
                projector_id=projector_id,
                projector_version=projector_version,
            ):
                result = _mark_event_applied(
                    connection,
                    event,
                    projector_id=projector_id,
                    projector_version=projector_version,
                    applied_at=applied_at,
                )
                return {**result, "callback_ran": False, "effect": {}}
            effect = apply_callback(connection, event) or {}
            result = _mark_event_applied(
                connection,
                event,
                projector_id=projector_id,
                projector_version=projector_version,
                applied_at=applied_at,
            )
            return {**result, "callback_ran": True, "effect": dict(effect)}
    finally:
        connection.close()


def import_audit360_rows(
    db_path: Path,
    rows: Iterable[Mapping[str, Any]],
    *,
    source_kind: str = "audit360",
    source_file: str = "",
    import_run_id: str = "manual",
    imported_at: str = "1970-01-01T00:00:00+00:00",
) -> dict[str, Any]:
    """Import normalized Audit360 rows into the reconstructed DB without wiring workers."""

    path = Path(db_path).expanduser().resolve()
    row_list = [dict(row) for row in rows]
    connection = sqlite3.connect(str(path))
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        _ensure_projection_tracking_schema(connection)
        _require_reconstruction_schema(connection)
        with connection:
            before = _business_counts(connection)
            imported_rows = 0
            skipped_rows = 0
            for index, row in enumerate(row_list, start=1):
                normalized = _audit360_normalized_row(
                    row,
                    index=index,
                    default_source_kind=source_kind,
                    default_source_file=source_file,
                )
                if not normalized["title"] and not normalized["action"] and not normalized["expected_piece"]:
                    skipped_rows += 1
                    continue
                event = _audit360_import_event(normalized, import_run_id=import_run_id, imported_at=imported_at)
                _insert_event_log_if_missing(connection, event)
                _import_audit360_objects(connection, event, normalized, import_run_id=import_run_id, imported_at=imported_at)
                _mark_event_applied(connection, event)
                imported_rows += 1
            after = _business_counts(connection)
    finally:
        connection.close()

    return {
        "ok": True,
        "command": "vault import-audit360-rows",
        "db_path": str(path),
        "rows": len(row_list),
        "imported_rows": imported_rows,
        "skipped_rows": skipped_rows,
        "points": after["points"],
        "actions": after["actions"],
        "expected_pieces": after["expected_pieces"],
        "object_links": after["object_links"],
        "source_import_map": after["source_import_map"],
        "created": {
            key: after[key] - before[key]
            for key in ("points", "actions", "expected_pieces", "object_links", "source_import_map")
        },
    }


def _event_sort_key(event: ReconstructionEvent) -> tuple[str, str, int, str]:
    return (event.created_at, event.device_id, event.sequence, event.event_id)
