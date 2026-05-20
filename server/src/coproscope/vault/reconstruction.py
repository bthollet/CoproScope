from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import core


RECONSTRUCTION_DB_FILE = "vault_reconstruction.sqlite3"
CONFLICT_RESOLUTION_EVENTS = {"conflict_resolved", "status_conflict_resolved"}
DOCUMENT_EVENT_TYPES = {"document_added", "document_version_added"}


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
                observation = _record_status_event(connection, event)
                if observation is not None:
                    status_observations.append(observation)
                resolved_status_keys.update(_resolved_status_keys(event))

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
        }
    finally:
        read_connection.close()


def _event_sort_key(event: ReconstructionEvent) -> tuple[str, str, int, str]:
    return (event.created_at, event.device_id, event.sequence, event.event_id)


def _reset_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        DROP TABLE IF EXISTS conflicts;
        DROP TABLE IF EXISTS status_observations;
        DROP TABLE IF EXISTS document_versions;
        DROP TABLE IF EXISTS documents;
        DROP TABLE IF EXISTS identities;
        DROP TABLE IF EXISTS event_log;
        DROP TABLE IF EXISTS vault_meta;

        CREATE TABLE vault_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE event_log (
            event_order INTEGER PRIMARY KEY,
            event_hash TEXT NOT NULL UNIQUE,
            event_id TEXT NOT NULL UNIQUE,
            event_type TEXT NOT NULL,
            object_id TEXT NOT NULL,
            author_key_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            event_path TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL
        );

        CREATE TABLE identities (
            author_key_id TEXT PRIMARY KEY,
            public_key TEXT,
            key_type TEXT,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            devices_json TEXT NOT NULL,
            event_count INTEGER NOT NULL,
            revoked_at TEXT
        );

        CREATE TABLE documents (
            document_id TEXT PRIMARY KEY,
            original_name TEXT,
            source_sha256 TEXT,
            size_bytes INTEGER,
            current_blob_id TEXT,
            current_blob_sha256 TEXT,
            imported_at TEXT,
            latest_event_id TEXT NOT NULL,
            versions_count INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE document_versions (
            document_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            version_index INTEGER NOT NULL,
            blob_id TEXT,
            blob_sha256 TEXT,
            source_sha256 TEXT,
            size_bytes INTEGER,
            imported_at TEXT,
            created_at TEXT NOT NULL,
            PRIMARY KEY (document_id, event_id)
        );

        CREATE TABLE status_observations (
            observation_id TEXT PRIMARY KEY,
            object_id TEXT NOT NULL,
            field TEXT NOT NULL,
            value_json TEXT NOT NULL,
            value_text TEXT NOT NULL,
            event_id TEXT NOT NULL,
            author_key_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE conflicts (
            conflict_id TEXT PRIMARY KEY,
            object_id TEXT NOT NULL,
            field TEXT NOT NULL,
            conflict_type TEXT NOT NULL,
            status TEXT NOT NULL,
            event_ids_json TEXT NOT NULL,
            details_json TEXT NOT NULL,
            detected_at TEXT NOT NULL
        );

        CREATE INDEX idx_event_log_object ON event_log(object_id, created_at);
        CREATE INDEX idx_document_versions_document ON document_versions(document_id, version_index);
        CREATE INDEX idx_status_observations_object ON status_observations(object_id, field, created_at);
        CREATE INDEX idx_conflicts_object ON conflicts(object_id, status);
        """
    )


def _insert_meta(connection: sqlite3.Connection, *, vault_id: str, event_count: int) -> None:
    values = {
        "schema": "coproscope-vault-reconstruction-v1",
        "vault_id": vault_id,
        "event_count": str(event_count),
    }
    connection.executemany("INSERT INTO vault_meta(key, value) VALUES (?, ?)", sorted(values.items()))


def _seed_identities(connection: sqlite3.Connection, key_records: Iterable[Mapping[str, Any]]) -> None:
    for record in key_records:
        author_key_id = str(record.get("author_key_id", ""))
        if not author_key_id:
            continue
        created_at = str(record.get("created_at", ""))
        connection.execute(
            """
            INSERT OR IGNORE INTO identities(
                author_key_id, public_key, key_type, first_seen_at, last_seen_at, devices_json, event_count, revoked_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 0, NULL)
            """,
            (
                author_key_id,
                _optional_text(record.get("public_key")),
                _optional_text(record.get("key_type")),
                created_at,
                created_at,
                "[]",
            ),
        )


def _insert_event_log(connection: sqlite3.Connection, event_order: int, event: ReconstructionEvent) -> None:
    payload_json = _canonical_json(event.payload)
    connection.execute(
        """
        INSERT INTO event_log(
            event_order, event_hash, event_id, event_type, object_id, author_key_id, device_id,
            sequence, created_at, event_path, payload_json, payload_sha256
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_order,
            event.event_hash,
            event.event_id,
            event.event_type,
            event.object_id,
            event.author_key_id,
            event.device_id,
            event.sequence,
            event.created_at,
            event.event_path,
            payload_json,
            _sha256_text(payload_json),
        ),
    )


def _record_identity_event(connection: sqlite3.Connection, event: ReconstructionEvent) -> None:
    if not event.author_key_id:
        return
    row = connection.execute(
        "SELECT devices_json, first_seen_at, public_key, key_type, event_count FROM identities WHERE author_key_id = ?",
        (event.author_key_id,),
    ).fetchone()
    if row is None:
        devices = sorted({event.device_id} if event.device_id else set())
        connection.execute(
            """
            INSERT INTO identities(
                author_key_id, public_key, key_type, first_seen_at, last_seen_at, devices_json, event_count, revoked_at
            )
            VALUES (?, NULL, NULL, ?, ?, ?, 1, NULL)
            """,
            (event.author_key_id, event.created_at, event.created_at, _canonical_json(devices)),
        )
    else:
        devices = set(json.loads(row[0] or "[]"))
        if event.device_id:
            devices.add(event.device_id)
        first_seen = row[1] or event.created_at
        connection.execute(
            """
            UPDATE identities
            SET first_seen_at = ?, last_seen_at = ?, devices_json = ?, event_count = ?
            WHERE author_key_id = ?
            """,
            (first_seen, event.created_at, _canonical_json(sorted(devices)), int(row[4]) + 1, event.author_key_id),
        )

    revoked_author_key_id = _revoked_author_key_id(event)
    if revoked_author_key_id:
        connection.execute(
            "UPDATE identities SET revoked_at = ? WHERE author_key_id = ?",
            (event.created_at, revoked_author_key_id),
        )


def _revoked_author_key_id(event: ReconstructionEvent) -> str:
    if event.event_type != "member_revoked":
        return ""
    for key in ("author_key_id", "revoked_author_key_id", "member_author_key_id"):
        value = event.payload.get(key)
        if value:
            return str(value)
    return event.object_id


def _record_document_event(connection: sqlite3.Connection, event: ReconstructionEvent) -> None:
    if event.event_type not in DOCUMENT_EVENT_TYPES:
        return
    document_id = str(event.payload.get("document_id") or event.object_id)
    if not document_id:
        return

    existing = connection.execute("SELECT versions_count FROM documents WHERE document_id = ?", (document_id,)).fetchone()
    version_index = int(existing[0]) + 1 if existing is not None else 1
    blob_id = _optional_text(event.payload.get("blob_id"))
    blob_sha256 = _optional_text(event.payload.get("blob_sha256"))
    source_sha256 = _optional_text(event.payload.get("source_sha256"))
    size_bytes = _optional_int(event.payload.get("size_bytes"))
    imported_at = _optional_text(event.payload.get("imported_at")) or event.created_at

    connection.execute(
        """
        INSERT INTO document_versions(
            document_id, event_id, version_index, blob_id, blob_sha256, source_sha256,
            size_bytes, imported_at, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            document_id,
            event.event_id,
            version_index,
            blob_id,
            blob_sha256,
            source_sha256,
            size_bytes,
            imported_at,
            event.created_at,
        ),
    )

    if existing is None:
        connection.execute(
            """
            INSERT INTO documents(
                document_id, original_name, source_sha256, size_bytes, current_blob_id, current_blob_sha256,
                imported_at, latest_event_id, versions_count, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                document_id,
                _optional_text(event.payload.get("original_name")),
                source_sha256,
                size_bytes,
                blob_id,
                blob_sha256,
                imported_at,
                event.event_id,
                event.created_at,
            ),
        )
    else:
        connection.execute(
            """
            UPDATE documents
            SET original_name = COALESCE(?, original_name),
                source_sha256 = COALESCE(?, source_sha256),
                size_bytes = COALESCE(?, size_bytes),
                current_blob_id = COALESCE(?, current_blob_id),
                current_blob_sha256 = COALESCE(?, current_blob_sha256),
                imported_at = COALESCE(imported_at, ?),
                latest_event_id = ?,
                versions_count = ?,
                updated_at = ?
            WHERE document_id = ?
            """,
            (
                _optional_text(event.payload.get("original_name")),
                source_sha256,
                size_bytes,
                blob_id,
                blob_sha256,
                imported_at,
                event.event_id,
                version_index,
                event.created_at,
                document_id,
            ),
        )


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _record_status_event(connection: sqlite3.Connection, event: ReconstructionEvent) -> dict[str, Any] | None:
    if event.event_type != "status_changed":
        return None
    field = _status_field(event.payload)
    status_value = _status_value(event.payload)
    value_json = _canonical_json(status_value)
    observation_id = "obs_" + _sha256_text(f"{event.event_hash}:{event.object_id}:{field}")[:20]
    row = {
        "observation_id": observation_id,
        "object_id": event.object_id,
        "field": field,
        "value_json": value_json,
        "value_text": _value_text(status_value),
        "event_id": event.event_id,
        "author_key_id": event.author_key_id,
        "device_id": event.device_id,
        "created_at": event.created_at,
    }
    connection.execute(
        """
        INSERT INTO status_observations(
            observation_id, object_id, field, value_json, value_text, event_id,
            author_key_id, device_id, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["observation_id"],
            row["object_id"],
            row["field"],
            row["value_json"],
            row["value_text"],
            row["event_id"],
            row["author_key_id"],
            row["device_id"],
            row["created_at"],
        ),
    )
    return row


def _status_field(payload: Mapping[str, Any]) -> str:
    return str(payload.get("field") or payload.get("status_field") or payload.get("property") or "status")


def _status_value(payload: Mapping[str, Any]) -> Any:
    for key in ("status", "new_status", "value", "state"):
        if key in payload:
            return payload[key]
    return None


def _resolved_status_keys(event: ReconstructionEvent) -> set[tuple[str, str]]:
    if event.event_type not in CONFLICT_RESOLUTION_EVENTS:
        return set()
    object_id = str(event.payload.get("object_id") or event.payload.get("resolved_object_id") or event.object_id)
    field = _status_field(event.payload)
    return {(object_id, field)} if object_id else set()


def _detect_status_conflicts(
    observations: Iterable[Mapping[str, Any]],
    resolved_status_keys: set[tuple[str, str]],
) -> list[dict[str, Any]]:
    latest_by_key_device: dict[tuple[str, str], dict[str, Mapping[str, Any]]] = {}
    for observation in observations:
        object_id = str(observation["object_id"])
        field = str(observation["field"])
        device_id = str(observation["device_id"] or observation["author_key_id"])
        latest_by_key_device.setdefault((object_id, field), {})[device_id] = observation

    conflicts: list[dict[str, Any]] = []
    for key, observations_by_device in sorted(latest_by_key_device.items()):
        if key in resolved_status_keys:
            continue
        latest = list(observations_by_device.values())
        values = {str(observation["value_json"]) for observation in latest}
        if len(values) <= 1:
            continue
        event_ids = sorted(str(observation["event_id"]) for observation in latest)
        details = {
            "contenders": [
                {
                    "event_id": observation["event_id"],
                    "author_key_id": observation["author_key_id"],
                    "device_id": observation["device_id"],
                    "value": json.loads(str(observation["value_json"])),
                    "created_at": observation["created_at"],
                }
                for observation in sorted(latest, key=lambda item: str(item["event_id"]))
            ]
        }
        object_id, field = key
        conflict_id = "conf_" + _sha256_text(_canonical_json([object_id, field, event_ids]))[:20]
        conflicts.append(
            {
                "conflict_id": conflict_id,
                "object_id": object_id,
                "field": field,
                "conflict_type": "status_changed",
                "status": "open",
                "event_ids_json": _canonical_json(event_ids),
                "details_json": _canonical_json(details),
                "detected_at": max(str(observation["created_at"]) for observation in latest),
            }
        )
    return conflicts


def _insert_conflicts(connection: sqlite3.Connection, conflicts: Iterable[Mapping[str, Any]]) -> None:
    for conflict in conflicts:
        connection.execute(
            """
            INSERT INTO conflicts(
                conflict_id, object_id, field, conflict_type, status, event_ids_json, details_json, detected_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conflict["conflict_id"],
                conflict["object_id"],
                conflict["field"],
                conflict["conflict_type"],
                conflict["status"],
                conflict["event_ids_json"],
                conflict["details_json"],
                conflict["detected_at"],
            ),
        )


def _count_rows(connection: sqlite3.Connection, table: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row is not None else 0
