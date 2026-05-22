from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
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
        }
    finally:
        read_connection.close()


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


def _reset_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        DROP TABLE IF EXISTS source_import_map;
        DROP TABLE IF EXISTS object_links;
        DROP TABLE IF EXISTS object_event_sources;
        DROP TABLE IF EXISTS proof_capsules;
        DROP TABLE IF EXISTS privacy_reviews;
        DROP TABLE IF EXISTS exports;
        DROP TABLE IF EXISTS plugin_runs;
        DROP TABLE IF EXISTS request_actions;
        DROP TABLE IF EXISTS requests;
        DROP TABLE IF EXISTS comments;
        DROP TABLE IF EXISTS actions;
        DROP TABLE IF EXISTS expected_pieces;
        DROP TABLE IF EXISTS proofs;
        DROP TABLE IF EXISTS points;
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
            document_type TEXT,
            classification_status TEXT,
            privacy_status TEXT,
            diffusion_status TEXT,
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

        CREATE TABLE points (
            point_id TEXT PRIMARY KEY,
            title TEXT,
            category TEXT,
            severity TEXT,
            status TEXT NOT NULL,
            proof_ids_json TEXT NOT NULL,
            created_from_event_hash TEXT NOT NULL,
            updated_from_event_hash TEXT NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE proofs (
            proof_id TEXT PRIMARY KEY,
            source_document_id TEXT,
            source_version_id TEXT,
            locator_json TEXT NOT NULL,
            summary TEXT,
            confidence TEXT,
            status TEXT NOT NULL,
            created_from_event_hash TEXT NOT NULL,
            updated_from_event_hash TEXT NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE expected_pieces (
            piece_id TEXT PRIMARY KEY,
            label TEXT,
            reason TEXT,
            holder_label TEXT,
            expected_from TEXT,
            priority TEXT,
            status TEXT NOT NULL,
            linked_action_id TEXT,
            linked_request_id TEXT,
            received_doc_ids_json TEXT NOT NULL,
            proof_ids_json TEXT NOT NULL,
            created_from_event_hash TEXT NOT NULL,
            updated_from_event_hash TEXT NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE actions (
            action_id TEXT PRIMARY KEY,
            title TEXT,
            source_module TEXT,
            source_ref TEXT,
            domain TEXT,
            owner_ref TEXT,
            status TEXT NOT NULL,
            priority TEXT,
            due_at TEXT,
            next_step TEXT,
            proof_expected TEXT,
            diffusion_status TEXT,
            related_point_ids_json TEXT NOT NULL,
            proof_ids_json TEXT NOT NULL,
            created_from_event_hash TEXT NOT NULL,
            updated_from_event_hash TEXT NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE comments (
            comment_id TEXT PRIMARY KEY,
            target_object_id TEXT NOT NULL,
            body TEXT,
            visibility TEXT,
            proof_ids_json TEXT NOT NULL,
            created_from_event_hash TEXT NOT NULL,
            updated_from_event_hash TEXT NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE requests (
            request_id TEXT PRIMARY KEY,
            subject TEXT,
            recipient_label TEXT,
            channel TEXT,
            status TEXT NOT NULL,
            created_on TEXT,
            due_on TEXT,
            last_followup_on TEXT,
            message_draft TEXT,
            linked_action_id TEXT,
            linked_piece_id TEXT,
            local_record_status TEXT,
            created_from_event_hash TEXT NOT NULL,
            updated_from_event_hash TEXT NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE request_actions (
            journal_id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL,
            occurred_at TEXT,
            actor_role TEXT,
            action_type TEXT,
            summary TEXT,
            status_after TEXT,
            next_action TEXT,
            visibility TEXT,
            event_id TEXT NOT NULL UNIQUE,
            event_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES event_log(event_id) ON DELETE CASCADE
        );

        CREATE TABLE plugin_runs (
            plugin_run_id TEXT PRIMARY KEY,
            plugin_id TEXT,
            plugin_version TEXT,
            manifest_hash TEXT,
            status TEXT NOT NULL,
            input_hashes_json TEXT NOT NULL,
            output_hashes_json TEXT NOT NULL,
            created_from_event_hash TEXT NOT NULL,
            updated_from_event_hash TEXT NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE exports (
            export_id TEXT PRIMARY KEY,
            format TEXT,
            profile TEXT,
            status TEXT NOT NULL,
            export_blob_id TEXT,
            source_object_ids_json TEXT NOT NULL,
            source_of_truth INTEGER NOT NULL DEFAULT 0 CHECK(source_of_truth IN (0, 1)),
            created_from_event_hash TEXT NOT NULL,
            updated_from_event_hash TEXT NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE privacy_reviews (
            privacy_review_id TEXT PRIMARY KEY,
            target_object_id TEXT NOT NULL,
            diffusion_status TEXT,
            redaction_required INTEGER NOT NULL DEFAULT 0 CHECK(redaction_required IN (0, 1)),
            reason TEXT,
            created_from_event_hash TEXT NOT NULL,
            updated_from_event_hash TEXT NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE proof_capsules (
            proof_capsule_id TEXT PRIMARY KEY,
            source_proof_ids_json TEXT NOT NULL,
            redacted_blob_id TEXT,
            export_blob_id TEXT,
            diffusion_status TEXT,
            created_from_event_hash TEXT NOT NULL,
            updated_from_event_hash TEXT NOT NULL,
            source_event_ids_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE object_event_sources (
            object_kind TEXT NOT NULL,
            object_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            event_hash TEXT NOT NULL,
            event_type TEXT NOT NULL,
            source_module TEXT,
            created_at TEXT NOT NULL,
            PRIMARY KEY (object_kind, object_id, event_id),
            FOREIGN KEY (event_id) REFERENCES event_log(event_id) ON DELETE CASCADE
        );

        CREATE TABLE object_links (
            link_id TEXT PRIMARY KEY,
            source_kind TEXT NOT NULL,
            source_id TEXT NOT NULL,
            relation TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            target_id TEXT NOT NULL,
            event_id TEXT NOT NULL,
            event_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE (source_kind, source_id, relation, target_kind, target_id, event_id),
            FOREIGN KEY (event_id) REFERENCES event_log(event_id) ON DELETE CASCADE
        );

        CREATE TABLE source_import_map (
            source_kind TEXT NOT NULL,
            source_file TEXT NOT NULL,
            source_row_id TEXT NOT NULL,
            object_kind TEXT NOT NULL,
            object_id TEXT NOT NULL,
            import_run_id TEXT NOT NULL,
            source_sha256 TEXT,
            created_at TEXT NOT NULL,
            PRIMARY KEY (source_kind, source_file, source_row_id, object_kind)
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
        CREATE INDEX idx_points_status ON points(status, severity);
        CREATE INDEX idx_proofs_document ON proofs(source_document_id, status);
        CREATE INDEX idx_expected_pieces_status ON expected_pieces(status, priority);
        CREATE INDEX idx_expected_pieces_links ON expected_pieces(linked_action_id, linked_request_id);
        CREATE INDEX idx_actions_status ON actions(status, priority, due_at);
        CREATE INDEX idx_requests_status ON requests(status, due_on);
        CREATE INDEX idx_request_actions_request ON request_actions(request_id, occurred_at);
        CREATE INDEX idx_plugin_runs_plugin ON plugin_runs(plugin_id, status);
        CREATE INDEX idx_exports_status ON exports(status, profile);
        CREATE INDEX idx_privacy_reviews_target ON privacy_reviews(target_object_id, diffusion_status);
        CREATE INDEX idx_object_event_sources_object ON object_event_sources(object_kind, object_id, created_at);
        CREATE INDEX idx_object_links_source ON object_links(source_kind, source_id, relation);
        CREATE INDEX idx_object_links_target ON object_links(target_kind, target_id, relation);
        CREATE INDEX idx_source_import_map_object ON source_import_map(object_kind, object_id);
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


def _insert_event_log_if_missing(connection: sqlite3.Connection, event: ReconstructionEvent) -> None:
    existing = connection.execute("SELECT event_id FROM event_log WHERE event_id = ?", (event.event_id,)).fetchone()
    if existing is not None:
        return
    row = connection.execute("SELECT COALESCE(MAX(event_order), 0) + 1 FROM event_log").fetchone()
    next_order = int(row[0]) if row is not None else 1
    _insert_event_log(connection, next_order, event)


def _require_reconstruction_schema(connection: sqlite3.Connection) -> None:
    required = {"event_log", "points", "actions", "expected_pieces", "object_links", "source_import_map"}
    existing = {
        str(row[0])
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    missing = sorted(required - existing)
    if missing:
        raise RuntimeError(f"Reconstruction DB schema is missing tables: {', '.join(missing)}")


def _business_counts(connection: sqlite3.Connection) -> dict[str, int]:
    tables = ("points", "actions", "expected_pieces", "object_links", "source_import_map")
    return {table: _count_rows(connection, table) for table in tables}


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
                imported_at, document_type, classification_status, privacy_status, diffusion_status,
                latest_event_id, versions_count, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                document_id,
                _optional_text(event.payload.get("original_name")),
                source_sha256,
                size_bytes,
                blob_id,
                blob_sha256,
                imported_at,
                _optional_text(event.payload.get("document_type")),
                _optional_text(event.payload.get("classification_status")),
                _optional_text(event.payload.get("privacy_status")),
                _optional_text(event.payload.get("diffusion_status")),
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
                document_type = COALESCE(?, document_type),
                classification_status = COALESCE(?, classification_status),
                privacy_status = COALESCE(?, privacy_status),
                diffusion_status = COALESCE(?, diffusion_status),
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
                _optional_text(event.payload.get("document_type")),
                _optional_text(event.payload.get("classification_status")),
                _optional_text(event.payload.get("privacy_status")),
                _optional_text(event.payload.get("diffusion_status")),
                event.event_id,
                version_index,
                event.created_at,
                document_id,
            ),
        )
    _record_object_event_source(connection, "document", document_id, event)


def _record_business_object_event(connection: sqlite3.Connection, event: ReconstructionEvent) -> None:
    data = _event_data(event)

    if event.event_type == CLASSIFICATION_COMPLETED:
        _apply_classification_event(connection, event, data)
        return
    if event.event_type == POINT_CREATED:
        _upsert_point(connection, event, data)
        return
    if event.event_type == ACTION_CREATED:
        _upsert_action(connection, event, data)
        return
    if event.event_type == REQUEST_CREATED:
        _upsert_request(connection, event, data)
        return
    if event.event_type == REQUEST_ACTION_RECORDED:
        _insert_request_action(connection, event, data)
        return
    if event.event_type == COMMENT_ADDED:
        _insert_comment(connection, event, data)
        return
    if event.event_type == DIFFUSION_DECIDED:
        _upsert_privacy_review(connection, event, data)
        return
    if event.event_type == REDACTION_COMPLETED:
        _upsert_proof_capsule(connection, event, data)
        return
    if event.event_type in PLUGIN_RUN_EVENT_TYPES:
        _upsert_plugin_run(connection, event, data)
        return
    if event.event_type in EXPORT_EVENT_TYPES:
        _upsert_export(connection, event, data)


def _apply_classification_event(
    connection: sqlite3.Connection,
    event: ReconstructionEvent,
    data: Mapping[str, Any],
) -> None:
    document_id = _first_text(data, ("document_id", "target_object_id")) or event.object_id
    if not document_id:
        return
    connection.execute(
        """
        UPDATE documents
        SET document_type = COALESCE(?, document_type),
            classification_status = COALESCE(?, classification_status),
            updated_at = ?
        WHERE document_id = ?
        """,
        (
            _first_text(data, ("classification", "document_type", "type")),
            _first_text(data, ("status", "classification_status")) or "completed",
            event.created_at,
            document_id,
        ),
    )
    _record_object_event_source(connection, "document", document_id, event)


def _upsert_point(connection: sqlite3.Connection, event: ReconstructionEvent, data: Mapping[str, Any]) -> None:
    point_id = _first_text(data, ("point_id", "id")) or event.object_id
    if not point_id:
        return
    proof_ids = _json_list(_first_value(data, ("proof_ids", "proof_refs", "preuves")))
    _upsert_current_object(
        connection,
        table="points",
        id_column="point_id",
        object_id=point_id,
        event=event,
        insert_values={
            "title": _first_text(data, ("title", "titre", "summary")),
            "category": _first_text(data, ("category", "domain", "domaine")),
            "severity": _first_text(data, ("severity", "priority", "priorite")),
            "status": _first_text(data, ("status", "statut")) or "open",
            "proof_ids_json": proof_ids,
        },
        update_values={
            "title": _first_text(data, ("title", "titre", "summary")),
            "category": _first_text(data, ("category", "domain", "domaine")),
            "severity": _first_text(data, ("severity", "priority", "priorite")),
            "status": _first_text(data, ("status", "statut")),
            "proof_ids_json": proof_ids,
        },
    )
    _record_object_event_source(connection, "point", point_id, event)
    _record_standard_links(connection, event, "point", point_id, data)


def _upsert_action(connection: sqlite3.Connection, event: ReconstructionEvent, data: Mapping[str, Any]) -> None:
    action_id = _first_text(data, ("action_id", "id")) or event.object_id
    if not action_id:
        return
    related_point_ids = _json_list(_first_value(data, ("related_point_ids", "point_ids", "points")))
    proof_ids = _json_list(_first_value(data, ("proof_ids", "proof_refs", "preuves")))
    proof_expected = _first_text(data, ("proof_expected", "preuve_attendue", "expected_piece_label"))
    _upsert_current_object(
        connection,
        table="actions",
        id_column="action_id",
        object_id=action_id,
        event=event,
        insert_values={
            "title": _first_text(data, ("title", "titre", "action", "action_a_faire")),
            "source_module": _source_module(event, data),
            "source_ref": _first_text(data, ("source_ref", "source", "source_id")),
            "domain": _first_text(data, ("domain", "domaine", "category")),
            "owner_ref": _first_text(data, ("owner_ref", "responsable", "assignee")),
            "status": _first_text(data, ("status", "statut")) or "open",
            "priority": _first_text(data, ("priority", "priorite", "severity")),
            "due_at": _first_text(data, ("due_at", "due_on", "echeance")),
            "next_step": _first_text(data, ("next_step", "next_action", "prochaine_action")),
            "proof_expected": proof_expected,
            "diffusion_status": _first_text(data, ("diffusion_status", "visibility", "visibilite")),
            "related_point_ids_json": related_point_ids,
            "proof_ids_json": proof_ids,
        },
        update_values={
            "title": _first_text(data, ("title", "titre", "action", "action_a_faire")),
            "source_module": _source_module(event, data),
            "source_ref": _first_text(data, ("source_ref", "source", "source_id")),
            "domain": _first_text(data, ("domain", "domaine", "category")),
            "owner_ref": _first_text(data, ("owner_ref", "responsable", "assignee")),
            "status": _first_text(data, ("status", "statut")),
            "priority": _first_text(data, ("priority", "priorite", "severity")),
            "due_at": _first_text(data, ("due_at", "due_on", "echeance")),
            "next_step": _first_text(data, ("next_step", "next_action", "prochaine_action")),
            "proof_expected": proof_expected,
            "diffusion_status": _first_text(data, ("diffusion_status", "visibility", "visibilite")),
            "related_point_ids_json": related_point_ids,
            "proof_ids_json": proof_ids,
        },
    )
    _record_object_event_source(connection, "action", action_id, event, source_module=_source_module(event, data))
    _record_standard_links(connection, event, "action", action_id, data)
    _upsert_expected_piece_from_action(connection, event, action_id, data)


def _upsert_expected_piece_from_action(
    connection: sqlite3.Connection,
    event: ReconstructionEvent,
    action_id: str,
    data: Mapping[str, Any],
) -> None:
    label = _first_text(data, ("expected_piece_label", "proof_expected", "preuve_attendue", "piece_attendue"))
    explicit_piece_id = _first_text(data, ("expected_piece_id", "piece_id", "linked_piece_id"))
    if not label and not explicit_piece_id:
        return
    piece_id = explicit_piece_id or "PCE-" + _sha256_text(f"{action_id}:{label}")[:16].upper()
    _upsert_current_object(
        connection,
        table="expected_pieces",
        id_column="piece_id",
        object_id=piece_id,
        event=event,
        insert_values={
            "label": label,
            "reason": _first_text(data, ("reason", "raison", "why")),
            "holder_label": _first_text(data, ("holder_label", "expected_from", "detenteur")),
            "expected_from": _first_text(data, ("expected_from", "source_attendue")),
            "priority": _first_text(data, ("priority", "priorite", "severity")),
            "status": _first_text(data, ("piece_status", "status")) or "open",
            "linked_action_id": action_id,
            "linked_request_id": _first_text(data, ("linked_request_id", "request_id")),
            "received_doc_ids_json": _json_list(_first_value(data, ("received_doc_ids", "document_ids"))),
            "proof_ids_json": _json_list(_first_value(data, ("proof_ids", "proof_refs"))),
        },
        update_values={
            "label": label,
            "reason": _first_text(data, ("reason", "raison", "why")),
            "holder_label": _first_text(data, ("holder_label", "expected_from", "detenteur")),
            "expected_from": _first_text(data, ("expected_from", "source_attendue")),
            "priority": _first_text(data, ("priority", "priorite", "severity")),
            "status": _first_text(data, ("piece_status", "status")),
            "linked_action_id": action_id,
            "linked_request_id": _first_text(data, ("linked_request_id", "request_id")),
            "received_doc_ids_json": _json_list(_first_value(data, ("received_doc_ids", "document_ids"))),
            "proof_ids_json": _json_list(_first_value(data, ("proof_ids", "proof_refs"))),
        },
    )
    _record_object_event_source(connection, "expected_piece", piece_id, event, source_module=_source_module(event, data))
    _insert_object_link(connection, "action", action_id, "expects", "expected_piece", piece_id, event)


def _upsert_request(connection: sqlite3.Connection, event: ReconstructionEvent, data: Mapping[str, Any]) -> None:
    request_id = _first_text(data, ("request_id", "id")) or event.object_id
    if not request_id:
        return
    linked_action_id = _first_text(data, ("linked_action_id", "related_action_id", "action_id"))
    linked_piece_id = _first_text(data, ("linked_piece_id", "expected_piece_id", "piece_id"))
    _upsert_current_object(
        connection,
        table="requests",
        id_column="request_id",
        object_id=request_id,
        event=event,
        insert_values={
            "subject": _first_text(data, ("subject", "sujet", "title")),
            "recipient_label": _first_text(data, ("recipient_label", "recipient", "destinataire")),
            "channel": _first_text(data, ("channel", "canal")),
            "status": _first_text(data, ("status", "statut")) or "open",
            "created_on": _first_text(data, ("created_on", "created_at", "received_at")) or event.created_at,
            "due_on": _first_text(data, ("due_on", "response_due_date", "echeance")),
            "last_followup_on": _first_text(data, ("last_followup_on", "last_follow_up")),
            "message_draft": _first_text(data, ("message_draft", "draft")),
            "linked_action_id": linked_action_id,
            "linked_piece_id": linked_piece_id,
            "local_record_status": _first_text(data, ("local_record_status",)) or "local_draft",
        },
        update_values={
            "subject": _first_text(data, ("subject", "sujet", "title")),
            "recipient_label": _first_text(data, ("recipient_label", "recipient", "destinataire")),
            "channel": _first_text(data, ("channel", "canal")),
            "status": _first_text(data, ("status", "statut")),
            "due_on": _first_text(data, ("due_on", "response_due_date", "echeance")),
            "last_followup_on": _first_text(data, ("last_followup_on", "last_follow_up")),
            "message_draft": _first_text(data, ("message_draft", "draft")),
            "linked_action_id": linked_action_id,
            "linked_piece_id": linked_piece_id,
            "local_record_status": _first_text(data, ("local_record_status",)),
        },
    )
    _record_object_event_source(connection, "request", request_id, event, source_module=_source_module(event, data))
    if linked_action_id:
        _insert_object_link(connection, "request", request_id, "relates_to", "action", linked_action_id, event)
    if linked_piece_id:
        _insert_object_link(connection, "request", request_id, "asks_for", "expected_piece", linked_piece_id, event)


def _insert_request_action(connection: sqlite3.Connection, event: ReconstructionEvent, data: Mapping[str, Any]) -> None:
    journal_id = _first_text(data, ("journal_id", "request_action_id", "id")) or event.object_id
    request_id = _first_text(data, ("request_id", "demande_id"))
    if not journal_id or not request_id:
        return
    connection.execute(
        """
        INSERT OR IGNORE INTO request_actions(
            journal_id, request_id, occurred_at, actor_role, action_type, summary,
            status_after, next_action, visibility, event_id, event_hash, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            journal_id,
            request_id,
            _first_text(data, ("occurred_at", "date")) or event.created_at,
            _first_text(data, ("actor_role", "acteur")),
            _first_text(data, ("action_type", "type_action")) or "recorded_locally",
            _first_text(data, ("summary", "resume", "description")),
            _first_text(data, ("status_after", "statut_apres", "status")),
            _first_text(data, ("next_action", "prochaine_action")),
            _first_text(data, ("visibility", "visibilite")),
            event.event_id,
            event.event_hash,
            event.created_at,
        ),
    )
    _record_object_event_source(connection, "request_action", journal_id, event, source_module=_source_module(event, data))
    _insert_object_link(connection, "request_action", journal_id, "updates", "request", request_id, event)
    status_after = _first_text(data, ("status_after", "statut_apres", "status"))
    if status_after:
        connection.execute(
            """
            UPDATE requests
            SET status = ?, last_followup_on = ?, updated_from_event_hash = ?, updated_at = ?
            WHERE request_id = ?
            """,
            (status_after, _first_text(data, ("occurred_at", "date")) or event.created_at, event.event_hash, event.created_at, request_id),
        )


def _insert_comment(connection: sqlite3.Connection, event: ReconstructionEvent, data: Mapping[str, Any]) -> None:
    comment_id = _first_text(data, ("comment_id", "id")) or event.object_id
    target_object_id = _first_text(data, ("target_object_id", "target_id")) or event.object_id
    if not comment_id or not target_object_id:
        return
    proof_ids = _json_list(_first_value(data, ("proof_ids", "proof_refs")))
    _upsert_current_object(
        connection,
        table="comments",
        id_column="comment_id",
        object_id=comment_id,
        event=event,
        insert_values={
            "target_object_id": target_object_id,
            "body": _first_text(data, ("body", "comment", "summary")),
            "visibility": _first_text(data, ("visibility", "visibilite")),
            "proof_ids_json": proof_ids,
        },
        update_values={
            "body": _first_text(data, ("body", "comment", "summary")),
            "visibility": _first_text(data, ("visibility", "visibilite")),
            "proof_ids_json": proof_ids,
        },
    )
    _record_object_event_source(connection, "comment", comment_id, event, source_module=_source_module(event, data))
    _insert_object_link(connection, "comment", comment_id, "comments_on", "object", target_object_id, event)


def _upsert_privacy_review(connection: sqlite3.Connection, event: ReconstructionEvent, data: Mapping[str, Any]) -> None:
    target_object_id = _first_text(data, ("target_object_id", "object_id")) or event.object_id
    review_id = _first_text(data, ("privacy_review_id", "review_id", "id")) or "PRV-" + _sha256_text(f"{target_object_id}:{event.event_hash}")[:16].upper()
    if not target_object_id:
        return
    _upsert_current_object(
        connection,
        table="privacy_reviews",
        id_column="privacy_review_id",
        object_id=review_id,
        event=event,
        insert_values={
            "target_object_id": target_object_id,
            "diffusion_status": _first_text(data, ("diffusion_status", "status")),
            "redaction_required": 1 if _truthy(data.get("redaction_required")) else 0,
            "reason": _first_text(data, ("reason", "motif")),
        },
        update_values={
            "diffusion_status": _first_text(data, ("diffusion_status", "status")),
            "redaction_required": 1 if _truthy(data.get("redaction_required")) else None,
            "reason": _first_text(data, ("reason", "motif")),
        },
    )
    _record_object_event_source(connection, "privacy_review", review_id, event, source_module=_source_module(event, data))
    _insert_object_link(connection, "privacy_review", review_id, "reviews", "object", target_object_id, event)


def _upsert_proof_capsule(connection: sqlite3.Connection, event: ReconstructionEvent, data: Mapping[str, Any]) -> None:
    capsule_id = _first_text(data, ("proof_capsule_id", "capsule_id", "export_id", "id")) or event.object_id
    if not capsule_id:
        return
    _upsert_current_object(
        connection,
        table="proof_capsules",
        id_column="proof_capsule_id",
        object_id=capsule_id,
        event=event,
        insert_values={
            "source_proof_ids_json": _json_list(_first_value(data, ("source_proof_ids", "proof_ids"))),
            "redacted_blob_id": _first_text(data, ("redacted_blob_id",)),
            "export_blob_id": _first_text(data, ("export_blob_id",)),
            "diffusion_status": _first_text(data, ("diffusion_status", "status")),
        },
        update_values={
            "source_proof_ids_json": _json_list(_first_value(data, ("source_proof_ids", "proof_ids"))),
            "redacted_blob_id": _first_text(data, ("redacted_blob_id",)),
            "export_blob_id": _first_text(data, ("export_blob_id",)),
            "diffusion_status": _first_text(data, ("diffusion_status", "status")),
        },
    )
    _record_object_event_source(connection, "proof_capsule", capsule_id, event, source_module=_source_module(event, data))


def _upsert_plugin_run(connection: sqlite3.Connection, event: ReconstructionEvent, data: Mapping[str, Any]) -> None:
    plugin_run_id = _first_text(data, ("plugin_run_id", "run_id", "id")) or event.object_id
    if not plugin_run_id:
        return
    _upsert_current_object(
        connection,
        table="plugin_runs",
        id_column="plugin_run_id",
        object_id=plugin_run_id,
        event=event,
        insert_values={
            "plugin_id": _first_text(data, ("plugin_id",)),
            "plugin_version": _first_text(data, ("plugin_version", "version")),
            "manifest_hash": _first_text(data, ("manifest_hash",)),
            "status": _first_text(data, ("status", "statut")) or "recorded",
            "input_hashes_json": _json_list(_first_value(data, ("input_hashes", "inputs"))),
            "output_hashes_json": _json_list(_first_value(data, ("output_hashes", "outputs"))),
        },
        update_values={
            "plugin_id": _first_text(data, ("plugin_id",)),
            "plugin_version": _first_text(data, ("plugin_version", "version")),
            "manifest_hash": _first_text(data, ("manifest_hash",)),
            "status": _first_text(data, ("status", "statut")),
            "input_hashes_json": _json_list(_first_value(data, ("input_hashes", "inputs"))),
            "output_hashes_json": _json_list(_first_value(data, ("output_hashes", "outputs"))),
        },
    )
    _record_object_event_source(connection, "plugin_run", plugin_run_id, event, source_module=_source_module(event, data))


def _upsert_export(connection: sqlite3.Connection, event: ReconstructionEvent, data: Mapping[str, Any]) -> None:
    export_id = _first_text(data, ("export_id", "id")) or event.object_id
    if not export_id:
        return
    _upsert_current_object(
        connection,
        table="exports",
        id_column="export_id",
        object_id=export_id,
        event=event,
        insert_values={
            "format": _first_text(data, ("format",)),
            "profile": _first_text(data, ("profile", "audience")),
            "status": _first_text(data, ("status", "statut")) or "derived",
            "export_blob_id": _first_text(data, ("export_blob_id", "blob_id")),
            "source_object_ids_json": _json_list(_first_value(data, ("source_object_ids", "source_ids"))),
            "source_of_truth": 0,
        },
        update_values={
            "format": _first_text(data, ("format",)),
            "profile": _first_text(data, ("profile", "audience")),
            "status": _first_text(data, ("status", "statut")),
            "export_blob_id": _first_text(data, ("export_blob_id", "blob_id")),
            "source_object_ids_json": _json_list(_first_value(data, ("source_object_ids", "source_ids"))),
            "source_of_truth": 0,
        },
    )
    _record_object_event_source(connection, "export", export_id, event, source_module=_source_module(event, data))
    _record_standard_links(connection, event, "export", export_id, data)


def _audit360_normalized_row(
    row: Mapping[str, Any],
    *,
    index: int,
    default_source_kind: str,
    default_source_file: str,
) -> dict[str, str]:
    row_data = dict(row)
    source_kind = _first_text(row_data, ("source_kind", "source_type")) or default_source_kind
    source_file = _first_text(row_data, ("source_file", "file", "path")) or default_source_file
    source_row_id = (
        _first_text(row_data, ("source_row_id", "repository_id", "finding_id", "control_id"))
        or "row-" + _sha256_text(_canonical_json(row_data))[:16]
    )
    control_id = _first_text(row_data, ("control_id", "controle_id"))
    title = _first_text(row_data, ("point_de_controle", "title", "titre_source", "piece_ou_question"))
    action = _first_text(row_data, ("action_a_faire", "action", "actions_a_faire"))
    expected_piece = _first_text(row_data, ("preuve_attendue", "piece", "preuves_attendues"))
    constat = _first_text(row_data, ("constat", "fact"))
    risk = _first_text(row_data, ("risque_concret", "risk"))
    source_key = _canonical_json([source_kind, source_file, source_row_id, control_id or title or index])
    suffix = _sha256_text(source_key)[:16].upper()
    return {
        "source_kind": source_kind,
        "source_file": source_file,
        "source_row_id": source_row_id,
        "source_sha256": _sha256_text(_canonical_json(row_data)),
        "control_id": control_id,
        "point_id": _first_text(row_data, ("point_id",)) or f"POINT-AUD-{suffix}",
        "action_id": _first_text(row_data, ("action_id",)) or f"ACT-AUD-{suffix}",
        "piece_id": _first_text(row_data, ("piece_id", "expected_piece_id")) or f"PCE-AUD-{suffix}",
        "title": title or constat or action or expected_piece,
        "category": _first_text(row_data, ("scope_label", "category", "lot_modele", "lot", "bloc")),
        "severity": _first_text(row_data, ("priorite", "priority_hint", "priorite_max", "severity")) or "P2",
        "status": _first_text(row_data, ("statut_action", "status", "statut_global")) or "open",
        "constat": constat,
        "risk": risk,
        "action": action,
        "expected_piece": expected_piece,
        "holder_label": _first_text(row_data, ("acteur_ou_entreprise", "actor", "entreprises")),
        "reason": _first_text(row_data, ("pourquoi_ce_controle", "explication_simple", "appreciation", "appreciation_source")),
        "source_ref": control_id or source_row_id,
        "domain": _first_text(row_data, ("lot_concerne", "lot", "bloc_concerne", "bloc", "tags")),
    }


def _audit360_import_event(
    normalized: Mapping[str, str],
    *,
    import_run_id: str,
    imported_at: str,
) -> ReconstructionEvent:
    event_seed = _canonical_json(
        [
            normalized["source_kind"],
            normalized["source_file"],
            normalized["source_row_id"],
            normalized["source_sha256"],
        ]
    )
    event_hash = "audit360_" + _sha256_text(event_seed)
    event_id = "evt_audit360_" + _sha256_text(event_seed)[:24]
    payload = {
        "source_kind": normalized["source_kind"],
        "source_file": normalized["source_file"],
        "source_row_id": normalized["source_row_id"],
        "source_sha256": normalized["source_sha256"],
        "import_run_id": import_run_id,
        "point_id": normalized["point_id"],
        "action_id": normalized["action_id"],
        "piece_id": normalized["piece_id"],
    }
    return ReconstructionEvent(
        event_id=event_id,
        event_type="audit360_imported",
        object_id=normalized["source_row_id"],
        created_at=imported_at,
        author_key_id="audit360_import",
        device_id="local_db_import",
        sequence=0,
        event_hash=event_hash,
        event_path=normalized["source_file"],
        payload=payload,
        envelope={},
    )


def _import_audit360_objects(
    connection: sqlite3.Connection,
    event: ReconstructionEvent,
    normalized: Mapping[str, str],
    *,
    import_run_id: str,
    imported_at: str,
) -> None:
    point_id = normalized["point_id"]
    action_id = normalized["action_id"]
    piece_id = normalized["piece_id"]

    _upsert_current_object(
        connection,
        table="points",
        id_column="point_id",
        object_id=point_id,
        event=event,
        insert_values={
            "title": normalized["title"],
            "category": normalized["category"],
            "severity": normalized["severity"],
            "status": normalized["status"],
            "proof_ids_json": _canonical_json([]),
        },
        update_values={
            "title": normalized["title"],
            "category": normalized["category"],
            "severity": normalized["severity"],
            "status": normalized["status"],
        },
    )
    _record_object_event_source(connection, "point", point_id, event, source_module="audit360")
    _upsert_source_import_map(connection, normalized, "point", point_id, import_run_id, imported_at)

    if normalized["action"]:
        _upsert_current_object(
            connection,
            table="actions",
            id_column="action_id",
            object_id=action_id,
            event=event,
            insert_values={
                "title": normalized["action"],
                "source_module": "audit360",
                "source_ref": normalized["source_ref"],
                "domain": normalized["domain"],
                "owner_ref": normalized["holder_label"],
                "status": normalized["status"],
                "priority": normalized["severity"],
                "due_at": "",
                "next_step": normalized["action"],
                "proof_expected": normalized["expected_piece"],
                "diffusion_status": "",
                "related_point_ids_json": _canonical_json([point_id]),
                "proof_ids_json": _canonical_json([]),
            },
            update_values={
                "title": normalized["action"],
                "source_module": "audit360",
                "source_ref": normalized["source_ref"],
                "domain": normalized["domain"],
                "owner_ref": normalized["holder_label"],
                "status": normalized["status"],
                "priority": normalized["severity"],
                "next_step": normalized["action"],
                "proof_expected": normalized["expected_piece"],
                "related_point_ids_json": _canonical_json([point_id]),
            },
        )
        _record_object_event_source(connection, "action", action_id, event, source_module="audit360")
        _insert_object_link(connection, "action", action_id, "relates_to", "point", point_id, event)
        _upsert_source_import_map(connection, normalized, "action", action_id, import_run_id, imported_at)

    if normalized["expected_piece"]:
        _upsert_current_object(
            connection,
            table="expected_pieces",
            id_column="piece_id",
            object_id=piece_id,
            event=event,
            insert_values={
                "label": normalized["expected_piece"],
                "reason": normalized["reason"] or normalized["constat"] or normalized["risk"],
                "holder_label": normalized["holder_label"],
                "expected_from": normalized["holder_label"],
                "priority": normalized["severity"],
                "status": "open",
                "linked_action_id": action_id if normalized["action"] else "",
                "linked_request_id": "",
                "received_doc_ids_json": _canonical_json([]),
                "proof_ids_json": _canonical_json([]),
            },
            update_values={
                "label": normalized["expected_piece"],
                "reason": normalized["reason"] or normalized["constat"] or normalized["risk"],
                "holder_label": normalized["holder_label"],
                "expected_from": normalized["holder_label"],
                "priority": normalized["severity"],
                "status": "open",
                "linked_action_id": action_id if normalized["action"] else "",
            },
        )
        _record_object_event_source(connection, "expected_piece", piece_id, event, source_module="audit360")
        _insert_object_link(connection, "point", point_id, "expects", "expected_piece", piece_id, event)
        if normalized["action"]:
            _insert_object_link(connection, "action", action_id, "expects", "expected_piece", piece_id, event)
        _upsert_source_import_map(connection, normalized, "expected_piece", piece_id, import_run_id, imported_at)


def _upsert_source_import_map(
    connection: sqlite3.Connection,
    normalized: Mapping[str, str],
    object_kind: str,
    object_id: str,
    import_run_id: str,
    imported_at: str,
) -> None:
    connection.execute(
        """
        INSERT INTO source_import_map(
            source_kind, source_file, source_row_id, object_kind, object_id,
            import_run_id, source_sha256, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_kind, source_file, source_row_id, object_kind)
        DO UPDATE SET
            object_id = excluded.object_id,
            import_run_id = excluded.import_run_id,
            source_sha256 = excluded.source_sha256,
            created_at = excluded.created_at
        """,
        (
            normalized["source_kind"],
            normalized["source_file"],
            normalized["source_row_id"],
            object_kind,
            object_id,
            import_run_id,
            normalized["source_sha256"],
            imported_at,
        ),
    )


def _upsert_current_object(
    connection: sqlite3.Connection,
    *,
    table: str,
    id_column: str,
    object_id: str,
    event: ReconstructionEvent,
    insert_values: Mapping[str, Any],
    update_values: Mapping[str, Any],
) -> None:
    row = connection.execute(f"SELECT source_event_ids_json FROM {table} WHERE {id_column} = ?", (object_id,)).fetchone()
    if row is None:
        fields = [
            id_column,
            *insert_values.keys(),
            "created_from_event_hash",
            "updated_from_event_hash",
            "source_event_ids_json",
            "created_at",
            "updated_at",
        ]
        placeholders = ", ".join("?" for _ in fields)
        connection.execute(
            f"INSERT INTO {table}({', '.join(fields)}) VALUES ({placeholders})",
            (
                object_id,
                *insert_values.values(),
                event.event_hash,
                event.event_hash,
                _canonical_json([event.event_id]),
                event.created_at,
                event.created_at,
            ),
        )
        return

    next_source_events = _append_json_unique(row[0], event.event_id)
    set_parts = []
    values: list[Any] = []
    for field_name, value in update_values.items():
        if value is None:
            continue
        set_parts.append(f"{field_name} = ?")
        values.append(value)
    set_parts.extend(
        [
            "updated_from_event_hash = ?",
            "source_event_ids_json = ?",
            "updated_at = ?",
        ]
    )
    values.extend([event.event_hash, next_source_events, event.created_at, object_id])
    connection.execute(
        f"UPDATE {table} SET {', '.join(set_parts)} WHERE {id_column} = ?",
        tuple(values),
    )


def _record_object_event_source(
    connection: sqlite3.Connection,
    object_kind: str,
    object_id: str,
    event: ReconstructionEvent,
    *,
    source_module: str = "",
) -> None:
    if not object_kind or not object_id:
        return
    connection.execute(
        """
        INSERT OR IGNORE INTO object_event_sources(
            object_kind, object_id, event_id, event_hash, event_type, source_module, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            object_kind,
            object_id,
            event.event_id,
            event.event_hash,
            event.event_type,
            source_module,
            event.created_at,
        ),
    )


def _record_standard_links(
    connection: sqlite3.Connection,
    event: ReconstructionEvent,
    source_kind: str,
    source_id: str,
    data: Mapping[str, Any],
) -> None:
    for relation, raw_value in _event_links(event).items():
        for target_id in _as_text_list(raw_value):
            _insert_object_link(connection, source_kind, source_id, relation, _target_kind(relation), target_id, event)

    link_fields = (
        ("related_point_ids", "relates_to", "point"),
        ("point_ids", "relates_to", "point"),
        ("proof_ids", "has_proof", "proof"),
        ("proof_refs", "has_proof", "proof"),
        ("action_ids", "relates_to", "action"),
        ("linked_action_id", "relates_to", "action"),
        ("related_action_id", "relates_to", "action"),
        ("request_id", "relates_to", "request"),
        ("linked_request_id", "relates_to", "request"),
        ("source_document_id", "uses_source", "document"),
        ("document_id", "uses_source", "document"),
        ("source_object_ids", "derived_from", "object"),
    )
    for field_name, relation, target_kind in link_fields:
        for target_id in _as_text_list(data.get(field_name)):
            if target_id and target_id != source_id:
                _insert_object_link(connection, source_kind, source_id, relation, target_kind, target_id, event)


def _insert_object_link(
    connection: sqlite3.Connection,
    source_kind: str,
    source_id: str,
    relation: str,
    target_kind: str,
    target_id: str,
    event: ReconstructionEvent,
) -> None:
    if not source_id or not target_id:
        return
    link_id = "lnk_" + _sha256_text(_canonical_json([source_kind, source_id, relation, target_kind, target_id, event.event_id]))[:24]
    connection.execute(
        """
        INSERT OR IGNORE INTO object_links(
            link_id, source_kind, source_id, relation, target_kind, target_id,
            event_id, event_hash, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            link_id,
            source_kind,
            source_id,
            relation,
            target_kind,
            target_id,
            event.event_id,
            event.event_hash,
            event.created_at,
        ),
    )


def _event_data(event: ReconstructionEvent) -> Mapping[str, Any]:
    data = event.payload.get("data")
    return data if isinstance(data, Mapping) else event.payload


def _event_links(event: ReconstructionEvent) -> Mapping[str, Any]:
    links = event.payload.get("links")
    return links if isinstance(links, Mapping) else {}


def _source_module(event: ReconstructionEvent, data: Mapping[str, Any]) -> str:
    return _first_text(data, ("source_module", "module")) or _first_text(event.payload, ("source_module", "module")) or ""


def _first_value(mapping: Mapping[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        value = mapping.get(name)
        if value not in (None, ""):
            return value
    return None


def _first_text(mapping: Mapping[str, Any], names: tuple[str, ...]) -> str:
    value = _first_value(mapping, names)
    if value is None:
        return ""
    return str(value).strip()


def _json_list(value: Any) -> str:
    return _canonical_json(_as_text_list(value))


def _as_text_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        separator = ";" if ";" in value else ","
        if separator in value:
            return [item.strip() for item in value.split(separator) if item.strip()]
        return [value.strip()] if value.strip() else []
    if isinstance(value, Mapping):
        candidate = value.get("object_id") or value.get("id") or value.get("ref")
        return [str(candidate)] if candidate else []
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _append_json_unique(existing_json: Any, value: str) -> str:
    try:
        existing = json.loads(existing_json or "[]")
    except (TypeError, json.JSONDecodeError):
        existing = []
    values = [str(item) for item in existing if str(item)]
    if value and value not in values:
        values.append(value)
    return _canonical_json(values)


def _target_kind(relation: str) -> str:
    normalized = relation.lower()
    if "piece" in normalized:
        return "expected_piece"
    if "proof" in normalized or "preuve" in normalized:
        return "proof"
    if "document" in normalized or "doc" in normalized:
        return "document"
    if "request" in normalized or "demande" in normalized:
        return "request"
    if "action" in normalized:
        return "action"
    if "point" in normalized:
        return "point"
    if "export" in normalized:
        return "export"
    return "object"


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "oui", "y", "o"}


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
