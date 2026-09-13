from __future__ import annotations

import base64
import hashlib
import json
import re
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "coproscope-vault-local-reconstruction-v1"
LOCAL_STATE_FILE = "vault_local.json"
DEFAULT_DB_FILE = "vault_local_reconstruction.sqlite3"

DOCUMENT_EVENT_TYPES = {"document_added", "document_version_added"}
MEMBER_UPSERT_EVENT_TYPES = {"member_added", "member_invited", "member_updated"}
MEMBER_REVOKE_EVENT_TYPES = {"member_revoked"}
DEVICE_UPSERT_EVENT_TYPES = {"device_added", "device_registered"}
DEVICE_REVOKE_EVENT_TYPES = {"device_revoked"}
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_SYNC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


@dataclass(frozen=True)
class LocalVaultEvent:
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

    @classmethod
    def from_envelope(
        cls,
        envelope: Mapping[str, Any],
        payload: Mapping[str, Any],
        *,
        event_hash: str,
        event_path: str,
    ) -> "LocalVaultEvent":
        return cls(
            event_id=str(envelope.get("event_id", "")),
            event_type=str(envelope.get("event_type", "")),
            object_id=str(envelope.get("object_id", "")),
            created_at=str(envelope.get("created_at", "")),
            author_key_id=str(envelope.get("author_key_id", "")),
            device_id=str(envelope.get("device_id", "")),
            sequence=_optional_int(envelope.get("sequence")) or 0,
            event_hash=event_hash,
            event_path=event_path,
            payload=dict(payload),
        )


def default_db_path(local_root: Path) -> Path:
    return Path(local_root).expanduser().resolve() / DEFAULT_DB_FILE


def resolve_db_path(local_root: Path, db_path: Path | None = None) -> Path:
    local = Path(local_root).expanduser().resolve()
    resolved = default_db_path(local) if db_path is None else Path(db_path).expanduser().resolve()
    if not _is_relative_to(resolved, local):
        raise RuntimeError(f"Local reconstruction database must stay under local_root: {resolved}")
    return resolved


def load_valid_local_events(local_root: Path, sync_root: Path) -> list[LocalVaultEvent]:
    local = Path(local_root).expanduser().resolve()
    sync = Path(sync_root).expanduser().resolve()
    state = _load_state(local)
    errors: list[str] = []
    events: list[LocalVaultEvent] = []

    from .core import vault_verify

    verification = vault_verify(local, sync)
    if not verification.get("ok"):
        verify_errors = verification.get("errors")
        if isinstance(verify_errors, list) and verify_errors:
            errors.extend(str(error) for error in verify_errors)
        else:
            errors.append("vault verify failed")

    vault_file = sync / "vault.json"
    if not vault_file.exists():
        errors.append(f"Missing vault.json: {vault_file}")

    for device_id, paths in _event_paths_by_device(sync).items():
        expected_prev = ""
        expected_sequence = 1
        for path in paths:
            try:
                raw = path.read_bytes()
                file_hash = _sha256_bytes(raw)
                expected_file_hash = _expected_hash_from_filename(path)
                if expected_file_hash and file_hash != expected_file_hash:
                    errors.append(f"{path}: event hash does not match filename")

                envelope = json.loads(raw.decode("utf-8"))
                if not isinstance(envelope, dict):
                    raise RuntimeError("event envelope is not an object")
                if envelope.get("device_id") != device_id:
                    errors.append(f"{path}: device_id does not match directory")
                if envelope.get("sequence") != expected_sequence:
                    errors.append(f"{path}: expected sequence {expected_sequence}, got {envelope.get('sequence')}")
                if envelope.get("prev_device_event_hash") != expected_prev:
                    errors.append(f"{path}: invalid previous event hash")
                if state.get("vault_id") and envelope.get("vault_id") != state.get("vault_id"):
                    errors.append(f"{path}: event vault_id does not match local state")

                ciphertext = _unb64(str(envelope.get("encrypted_payload", "")))
                if _sha256_bytes(ciphertext) != envelope.get("encrypted_payload_hash"):
                    errors.append(f"{path}: invalid encrypted payload hash")
                _verify_signature(sync, envelope)
                payload = _decrypt_payload(state, envelope)
                _validate_document_blob(sync, envelope, payload, path, errors)
                events.append(
                    LocalVaultEvent.from_envelope(
                        envelope,
                        payload,
                        event_hash=file_hash,
                        event_path=str(path),
                    )
                )
                expected_prev = file_hash
                expected_sequence += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{path}: {exc}")

    if errors:
        raise RuntimeError(f"Cannot reconstruct invalid vault: {'; '.join(errors[:5])}")
    return sorted(events, key=_event_sort_key)


def rebuild_local_reconstruction(
    local_root: Path,
    sync_root: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    local = Path(local_root).expanduser().resolve()
    sync = Path(sync_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(local, db_path)
    events = load_valid_local_events(local, sync)
    state = _load_state(local)
    return rebuild_local_reconstruction_from_events(
        events,
        resolved_db_path,
        vault_id=_read_vault_id(sync) or str(state.get("vault_id", "")),
        key_records=_read_key_records(sync),
        local_root=local,
        sync_root=sync,
    )


def rebuild_local_reconstruction_from_events(
    events: Iterable[LocalVaultEvent],
    db_path: Path,
    *,
    vault_id: str = "",
    key_records: Iterable[Mapping[str, Any]] | None = None,
    local_root: Path | None = None,
    sync_root: Path | None = None,
) -> dict[str, Any]:
    path = Path(db_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered_events = sorted(list(events), key=_event_sort_key)
    rebuilt_at = _now_iso()

    connection = sqlite3.connect(str(path))
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        _reset_schema(connection)
        with connection:
            _seed_members_from_keys(connection, key_records or [])
            for event in ordered_events:
                _record_author_member(connection, event)
                _record_event_device(connection, event)
                _apply_member_event(connection, event)
                _apply_device_event(connection, event)
                _apply_document_event(connection, event)
            _write_sync_state(
                connection,
                events=ordered_events,
                vault_id=vault_id,
                local_root=local_root,
                sync_root=sync_root,
                rebuilt_at=rebuilt_at,
            )

        return {
            "ok": True,
            "command": "vault local-reconstruct",
            "schema_version": SCHEMA_VERSION,
            "db_path": str(path),
            "vault_id": vault_id,
            "events": len(ordered_events),
            "documents": _count_rows(connection, "documents"),
            "document_versions": _count_rows(connection, "document_versions"),
            "members": _count_rows(connection, "members"),
            "devices": _count_rows(connection, "devices"),
        }
    finally:
        connection.close()


def _reset_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        DROP TABLE IF EXISTS document_versions;
        DROP TABLE IF EXISTS documents;
        DROP TABLE IF EXISTS devices;
        DROP TABLE IF EXISTS members;
        DROP TABLE IF EXISTS sync_state;

        CREATE TABLE documents (
            document_id TEXT PRIMARY KEY,
            original_name TEXT,
            source_sha256 TEXT,
            size_bytes INTEGER,
            current_blob_id TEXT,
            current_blob_sha256 TEXT,
            imported_at TEXT,
            latest_event_id TEXT NOT NULL,
            latest_event_hash TEXT NOT NULL,
            versions_count INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE document_versions (
            document_id TEXT NOT NULL,
            version_index INTEGER NOT NULL,
            event_id TEXT NOT NULL UNIQUE,
            event_hash TEXT NOT NULL,
            blob_id TEXT,
            blob_sha256 TEXT,
            source_sha256 TEXT,
            size_bytes INTEGER,
            imported_at TEXT,
            created_at TEXT NOT NULL,
            PRIMARY KEY (document_id, version_index),
            FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
        );

        CREATE TABLE members (
            member_id TEXT PRIMARY KEY,
            author_key_id TEXT UNIQUE,
            display_name TEXT,
            email TEXT,
            role TEXT,
            status TEXT NOT NULL,
            public_key TEXT,
            key_type TEXT,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            revoked_at TEXT
        );

        CREATE TABLE devices (
            device_id TEXT PRIMARY KEY,
            member_id TEXT,
            author_key_id TEXT,
            status TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            last_sequence INTEGER NOT NULL,
            last_event_id TEXT NOT NULL,
            event_count INTEGER NOT NULL,
            FOREIGN KEY (member_id) REFERENCES members(member_id) ON UPDATE CASCADE
        );

        CREATE TABLE sync_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX idx_document_versions_document ON document_versions(document_id, version_index);
        CREATE INDEX idx_members_author_key ON members(author_key_id);
        CREATE INDEX idx_devices_author_key ON devices(author_key_id);
        """
    )


def _seed_members_from_keys(connection: sqlite3.Connection, key_records: Iterable[Mapping[str, Any]]) -> None:
    for record in key_records:
        author_key_id = _optional_text(record.get("author_key_id"))
        if not author_key_id:
            continue
        observed_at = _optional_text(record.get("created_at")) or ""
        _upsert_member(
            connection,
            member_id=author_key_id,
            author_key_id=author_key_id,
            observed_at=observed_at,
            public_key=_optional_text(record.get("public_key")),
            key_type=_optional_text(record.get("key_type")),
            status="active",
        )


def _record_author_member(connection: sqlite3.Connection, event: LocalVaultEvent) -> None:
    if event.author_key_id:
        _upsert_member(
            connection,
            member_id=event.author_key_id,
            author_key_id=event.author_key_id,
            observed_at=event.created_at,
            status="active",
        )


def _record_event_device(connection: sqlite3.Connection, event: LocalVaultEvent) -> None:
    if not event.device_id:
        return
    _upsert_device(
        connection,
        device_id=event.device_id,
        author_key_id=event.author_key_id,
        observed_at=event.created_at,
        sequence=event.sequence,
        event_id=event.event_id,
        status="active",
        increment_event_count=True,
    )


def _apply_member_event(connection: sqlite3.Connection, event: LocalVaultEvent) -> None:
    if event.event_type in MEMBER_UPSERT_EVENT_TYPES:
        member_id = _member_id_from_payload(event) or event.object_id
        author_key_id = _member_author_key_from_payload(event)
        status = _optional_text(event.payload.get("status")) or ("invited" if event.event_type == "member_invited" else "active")
        _upsert_member(
            connection,
            member_id=member_id or author_key_id,
            author_key_id=author_key_id,
            observed_at=event.created_at,
            display_name=_optional_text(event.payload.get("display_name") or event.payload.get("name")),
            email=_optional_text(event.payload.get("email")),
            role=_optional_text(event.payload.get("role")),
            status=status,
        )
        return

    if event.event_type in MEMBER_REVOKE_EVENT_TYPES:
        _upsert_member(
            connection,
            member_id=_member_id_from_payload(event) or event.object_id,
            author_key_id=_member_author_key_from_payload(event),
            observed_at=event.created_at,
            status="revoked",
            revoked_at=event.created_at,
        )


def _apply_device_event(connection: sqlite3.Connection, event: LocalVaultEvent) -> None:
    if event.event_type in DEVICE_UPSERT_EVENT_TYPES or event.event_type == "vault_initialized":
        device_id = _device_id_from_payload(event)
        if not device_id:
            return
        author_key_id = _optional_text(event.payload.get("author_key_id")) or event.author_key_id
        _upsert_device(
            connection,
            device_id=device_id,
            author_key_id=author_key_id,
            member_id=_optional_text(event.payload.get("member_id")) or _member_id_for_author(connection, author_key_id),
            observed_at=event.created_at,
            sequence=event.sequence if device_id == event.device_id else 0,
            event_id=event.event_id,
            status=_optional_text(event.payload.get("status")) or "active",
            increment_event_count=False,
        )
        return

    if event.event_type in DEVICE_REVOKE_EVENT_TYPES:
        device_id = _device_id_from_payload(event) or event.object_id
        if device_id:
            _upsert_device(
                connection,
                device_id=device_id,
                author_key_id=_optional_text(event.payload.get("author_key_id")),
                member_id=_optional_text(event.payload.get("member_id")),
                observed_at=event.created_at,
                sequence=0,
                event_id=event.event_id,
                status="revoked",
                increment_event_count=False,
            )


def _apply_document_event(connection: sqlite3.Connection, event: LocalVaultEvent) -> None:
    if event.event_type not in DOCUMENT_EVENT_TYPES:
        return
    document_id = _optional_text(event.payload.get("document_id")) or event.object_id
    if not document_id:
        return

    existing = connection.execute(
        "SELECT versions_count FROM documents WHERE document_id = ?",
        (document_id,),
    ).fetchone()
    if existing is None:
        connection.execute(
            """
            INSERT INTO documents(
                document_id, original_name, source_sha256, size_bytes, current_blob_id,
                current_blob_sha256, imported_at, latest_event_id, latest_event_hash,
                versions_count, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                document_id,
                _optional_text(event.payload.get("original_name")),
                _optional_text(event.payload.get("source_sha256")),
                _optional_int(event.payload.get("size_bytes")),
                _optional_text(event.payload.get("blob_id")),
                _optional_text(event.payload.get("blob_sha256")),
                _optional_text(event.payload.get("imported_at")) or event.created_at,
                event.event_id,
                event.event_hash,
                event.created_at,
            ),
        )
        version_index = 1
    else:
        version_index = int(existing["versions_count"]) + 1

    connection.execute(
        """
        INSERT INTO document_versions(
            document_id, version_index, event_id, event_hash, blob_id, blob_sha256,
            source_sha256, size_bytes, imported_at, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            document_id,
            version_index,
            event.event_id,
            event.event_hash,
            _optional_text(event.payload.get("blob_id")),
            _optional_text(event.payload.get("blob_sha256")),
            _optional_text(event.payload.get("source_sha256")),
            _optional_int(event.payload.get("size_bytes")),
            _optional_text(event.payload.get("imported_at")) or event.created_at,
            event.created_at,
        ),
    )
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
            latest_event_hash = ?,
            versions_count = ?,
            updated_at = ?
        WHERE document_id = ?
        """,
        (
            _optional_text(event.payload.get("original_name")),
            _optional_text(event.payload.get("source_sha256")),
            _optional_int(event.payload.get("size_bytes")),
            _optional_text(event.payload.get("blob_id")),
            _optional_text(event.payload.get("blob_sha256")),
            _optional_text(event.payload.get("imported_at")) or event.created_at,
            event.event_id,
            event.event_hash,
            version_index,
            event.created_at,
            document_id,
        ),
    )
