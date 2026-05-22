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


def _upsert_member(
    connection: sqlite3.Connection,
    *,
    member_id: str | None,
    author_key_id: str | None,
    observed_at: str,
    status: str,
    display_name: str | None = None,
    email: str | None = None,
    role: str | None = None,
    public_key: str | None = None,
    key_type: str | None = None,
    revoked_at: str | None = None,
) -> str:
    normalized_author = _optional_text(author_key_id)
    normalized_member = _optional_text(member_id) or normalized_author
    if not normalized_member:
        return ""
    seen_at = observed_at or _now_iso()
    existing = connection.execute("SELECT * FROM members WHERE member_id = ?", (normalized_member,)).fetchone()
    if existing is None and normalized_author:
        existing = connection.execute("SELECT * FROM members WHERE author_key_id = ?", (normalized_author,)).fetchone()

    if existing is None:
        connection.execute(
            """
            INSERT INTO members(
                member_id, author_key_id, display_name, email, role, status,
                public_key, key_type, first_seen_at, last_seen_at, revoked_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized_member,
                normalized_author,
                display_name,
                email,
                role,
                status,
                public_key,
                key_type,
                seen_at,
                seen_at,
                revoked_at,
            ),
        )
        return normalized_member

    current_member = str(existing["member_id"])
    target_member = normalized_member
    if current_member != target_member:
        collision = connection.execute("SELECT member_id FROM members WHERE member_id = ?", (target_member,)).fetchone()
        if collision is None:
            connection.execute("UPDATE members SET member_id = ? WHERE member_id = ?", (target_member, current_member))
        else:
            target_member = current_member

    current_status = str(existing["status"])
    next_status = current_status if current_status == "revoked" and status == "active" else status
    connection.execute(
        """
        UPDATE members
        SET author_key_id = COALESCE(?, author_key_id),
            display_name = COALESCE(?, display_name),
            email = COALESCE(?, email),
            role = COALESCE(?, role),
            status = ?,
            public_key = COALESCE(?, public_key),
            key_type = COALESCE(?, key_type),
            first_seen_at = ?,
            last_seen_at = ?,
            revoked_at = COALESCE(?, revoked_at)
        WHERE member_id = ?
        """,
        (
            normalized_author,
            display_name,
            email,
            role,
            next_status,
            public_key,
            key_type,
            _earliest(existing["first_seen_at"], seen_at),
            _latest(existing["last_seen_at"], seen_at),
            revoked_at,
            target_member,
        ),
    )
    return target_member


def _upsert_device(
    connection: sqlite3.Connection,
    *,
    device_id: str | None,
    author_key_id: str | None,
    observed_at: str,
    sequence: int,
    event_id: str,
    status: str,
    member_id: str | None = None,
    increment_event_count: bool,
) -> None:
    normalized_device = _optional_text(device_id)
    if not normalized_device:
        return
    normalized_author = _optional_text(author_key_id)
    normalized_member = _optional_text(member_id) or _member_id_for_author(connection, normalized_author)
    seen_at = observed_at or _now_iso()
    existing = connection.execute("SELECT * FROM devices WHERE device_id = ?", (normalized_device,)).fetchone()
    increment = 1 if increment_event_count else 0
    if existing is None:
        connection.execute(
            """
            INSERT INTO devices(
                device_id, member_id, author_key_id, status, first_seen_at, last_seen_at,
                last_sequence, last_event_id, event_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                normalized_device,
                normalized_member,
                normalized_author,
                status,
                seen_at,
                seen_at,
                max(sequence, 0),
                event_id,
                increment,
            ),
        )
        return

    current_status = str(existing["status"])
    next_status = current_status if current_status == "revoked" and status == "active" else status
    connection.execute(
        """
        UPDATE devices
        SET member_id = COALESCE(?, member_id),
            author_key_id = COALESCE(?, author_key_id),
            status = ?,
            first_seen_at = ?,
            last_seen_at = ?,
            last_sequence = MAX(last_sequence, ?),
            last_event_id = COALESCE(?, last_event_id),
            event_count = event_count + ?
        WHERE device_id = ?
        """,
        (
            normalized_member,
            normalized_author,
            next_status,
            _earliest(existing["first_seen_at"], seen_at),
            _latest(existing["last_seen_at"], seen_at),
            max(sequence, 0),
            event_id,
            increment,
            normalized_device,
        ),
    )


def _write_sync_state(
    connection: sqlite3.Connection,
    *,
    events: Sequence[LocalVaultEvent],
    vault_id: str,
    local_root: Path | None,
    sync_root: Path | None,
    rebuilt_at: str,
) -> None:
    latest = events[-1] if events else None
    values = {
        "schema_version": SCHEMA_VERSION,
        "vault_id": vault_id,
        "event_count": str(len(events)),
        "last_event_id": latest.event_id if latest else "",
        "last_event_hash": latest.event_hash if latest else "",
        "last_event_created_at": latest.created_at if latest else "",
        "rebuilt_at": rebuilt_at,
        "source_local_root": str(local_root) if local_root is not None else "",
        "source_sync_root": str(sync_root) if sync_root is not None else "",
    }
    for key, value in sorted(values.items()):
        connection.execute("INSERT INTO sync_state(key, value, updated_at) VALUES (?, ?, ?)", (key, value, rebuilt_at))


def _validate_document_blob(
    sync_root: Path,
    envelope: Mapping[str, Any],
    payload: Mapping[str, Any],
    path: Path,
    errors: list[str],
) -> None:
    if envelope.get("event_type") not in DOCUMENT_EVENT_TYPES:
        return
    blob_id = _optional_text(payload.get("blob_id"))
    if not blob_id:
        return
    if not _is_sha256_hex(blob_id):
        errors.append(f"{path}: invalid blob id {blob_id}")
        return
    blob_path = _safe_sync_path(sync_root, "blobs", blob_id[:2], f"{blob_id}.blob")
    if not blob_path.exists():
        errors.append(f"{path}: missing blob {blob_id}")
        return
    expected = _optional_text(payload.get("blob_sha256"))
    if expected and _sha256_file(blob_path) != expected:
        errors.append(f"{path}: invalid blob hash {blob_id}")


def _verify_signature(sync_root: Path, event: Mapping[str, Any]) -> None:
    crypto = _require_crypto()
    signature = _unb64(str(event["signature"]))
    signed = dict(event)
    signed.pop("signature", None)
    author_key_id = str(event["author_key_id"])
    if not _is_safe_sync_id(author_key_id):
        raise RuntimeError(f"Invalid author_key_id: {author_key_id}")
    key_payload = _read_json(_safe_sync_path(sync_root, "keys", f"{author_key_id}.json"))
    public_key = crypto["ed25519"].Ed25519PublicKey.from_public_bytes(_unb64(str(key_payload["public_key"])))
    try:
        public_key.verify(signature, _canonical_bytes(signed))
    except crypto["InvalidSignature"] as exc:
        raise RuntimeError("Invalid event signature") from exc


def _decrypt_payload(state: Mapping[str, Any], event: Mapping[str, Any]) -> dict[str, Any]:
    crypto = _require_crypto()
    aesgcm = crypto["AESGCM"](_unb64(str(state["vault_key"])))
    plaintext = aesgcm.decrypt(
        _unb64(str(event["payload_nonce"])),
        _unb64(str(event["encrypted_payload"])),
        None,
    )
    payload = json.loads(plaintext.decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid decrypted payload for event {event.get('event_id')}")
    return payload


def _require_crypto() -> dict[str, Any]:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Local vault reconstruction requires the 'cryptography' package.") from exc
    return {"AESGCM": AESGCM, "InvalidSignature": InvalidSignature, "ed25519": ed25519}


def _load_state(local_root: Path) -> dict[str, Any]:
    path = local_root / LOCAL_STATE_FILE
    if not path.exists():
        raise RuntimeError(f"Vault local state not found: {path}")
    state = _read_json(path)
    if not isinstance(state, dict):
        raise RuntimeError(f"Invalid vault local state: {path}")
    return state


def _read_vault_id(sync_root: Path) -> str:
    vault_file = sync_root / "vault.json"
    if not vault_file.exists():
        return ""
    payload = _read_json(vault_file)
    return str(payload.get("vault_id", "")) if isinstance(payload, dict) else ""


def _read_key_records(sync_root: Path) -> list[dict[str, Any]]:
    key_root = sync_root / "keys"
    if not key_root.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(key_root.glob("*.json")):
        payload = _read_json(path)
        if not isinstance(payload, dict):
            raise RuntimeError(f"Invalid key record: {path}")
        records.append(payload)
    return records


def _event_paths_by_device(sync_root: Path) -> dict[str, list[Path]]:
    event_root = sync_root / "events"
    if not event_root.exists():
        return {}
    paths_by_device: dict[str, list[Path]] = {}
    for path in sorted(event_root.glob("*/*.json")):
        if path.is_file():
            paths_by_device.setdefault(path.parent.name, []).append(path)
    return {device_id: sorted(paths) for device_id, paths in sorted(paths_by_device.items())}


def _event_sort_key(event: LocalVaultEvent) -> tuple[str, str, int, str]:
    return (event.created_at, event.device_id, event.sequence, event.event_id)


def _member_id_from_payload(event: LocalVaultEvent) -> str:
    for key in ("member_id", "target_member_id", "revoked_member_id"):
        value = _optional_text(event.payload.get(key))
        if value:
            return value
    return ""


def _member_author_key_from_payload(event: LocalVaultEvent) -> str:
    for key in ("member_author_key_id", "target_author_key_id", "revoked_author_key_id", "author_key_id"):
        value = _optional_text(event.payload.get(key))
        if value:
            return value
    return ""


def _device_id_from_payload(event: LocalVaultEvent) -> str:
    for key in ("device_id", "target_device_id", "revoked_device_id"):
        value = _optional_text(event.payload.get(key))
        if value:
            return value
    return ""


def _member_id_for_author(connection: sqlite3.Connection, author_key_id: str | None) -> str | None:
    normalized_author = _optional_text(author_key_id)
    if not normalized_author:
        return None
    row = connection.execute("SELECT member_id FROM members WHERE author_key_id = ?", (normalized_author,)).fetchone()
    return str(row["member_id"]) if row is not None else normalized_author


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return bool(SHA256_HEX_RE.fullmatch(value))


def _is_safe_sync_id(value: str) -> bool:
    return bool(SAFE_SYNC_ID_RE.fullmatch(value))


def _safe_sync_path(sync_root: Path, *parts: str) -> Path:
    root = Path(sync_root).expanduser().resolve()
    path = root.joinpath(*parts).resolve()
    if not _is_relative_to(path, root):
        raise RuntimeError(f"Vault sync path escaped sync_root: {path}")
    return path


def _expected_hash_from_filename(path: Path) -> str:
    parts = path.stem.split("_", 1)
    return parts[1] if len(parts) == 2 else ""


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _earliest(left: Any, right: str) -> str:
    left_text = _optional_text(left)
    if not left_text:
        return right
    if not right:
        return left_text
    return min(left_text, right)


def _latest(left: Any, right: str) -> str:
    left_text = _optional_text(left)
    if not left_text:
        return right
    if not right:
        return left_text
    return max(left_text, right)


def _count_rows(connection: sqlite3.Connection, table: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row is not None else 0


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
