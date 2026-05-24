from __future__ import annotations



def _mark_event_applied(
    connection: sqlite3.Connection,
    event: ReconstructionEvent,
    *,
    projector_id: str = DEFAULT_PROJECTION_PROJECTOR_ID,
    projector_version: str = DEFAULT_PROJECTION_PROJECTOR_VERSION,
    applied_at: str | None = None,
) -> dict[str, Any]:
    if not projector_id or not projector_version:
        raise RuntimeError("Projector id and version are required")
    if not event.event_id or not event.event_hash:
        raise RuntimeError("Applied events require an event id and hash")

    existing = connection.execute(
        """
        SELECT event_hash
        FROM event_applied
        WHERE projector_id = ? AND projector_version = ? AND event_id = ?
        """,
        (projector_id, projector_version, event.event_id),
    ).fetchone()
    if existing is not None:
        if str(existing[0]) != event.event_hash:
            raise RuntimeError("Event id is already applied with a different hash")
        state = _refresh_projection_meta(connection, projector_id=projector_id, projector_version=projector_version)
        return {
            "ok": True,
            "projector_id": projector_id,
            "projector_version": projector_version,
            "event_id": event.event_id,
            "event_hash": event.event_hash,
            "applied": False,
            "already_applied": True,
            **state,
        }

    hash_owner = connection.execute(
        """
        SELECT event_id
        FROM event_applied
        WHERE projector_id = ? AND projector_version = ? AND event_hash = ?
        """,
        (projector_id, projector_version, event.event_hash),
    ).fetchone()
    if hash_owner is not None:
        raise RuntimeError(f"Event hash is already applied under another event id: {hash_owner[0]}")

    connection.execute(
        """
        INSERT INTO event_applied(
            projector_id, projector_version, event_id, event_hash, event_type, object_id,
            device_id, sequence, event_created_at, applied_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            projector_id,
            projector_version,
            event.event_id,
            event.event_hash,
            event.event_type,
            event.object_id,
            event.device_id,
            event.sequence,
            event.created_at,
            applied_at or event.created_at,
        ),
    )
    state = _refresh_projection_meta(connection, projector_id=projector_id, projector_version=projector_version)
    return {
        "ok": True,
        "projector_id": projector_id,
        "projector_version": projector_version,
        "event_id": event.event_id,
        "event_hash": event.event_hash,
        "applied": True,
        "already_applied": False,
        **state,
    }


def _refresh_projection_meta(
    connection: sqlite3.Connection,
    *,
    projector_id: str,
    projector_version: str,
) -> dict[str, Any]:
    rows = connection.execute(
        """
        SELECT event_id, event_hash, device_id, sequence, event_created_at, applied_at
        FROM event_applied
        WHERE projector_id = ? AND projector_version = ?
        ORDER BY device_id, sequence, event_created_at, event_id
        """,
        (projector_id, projector_version),
    ).fetchall()
    heads_by_device: dict[str, dict[str, Any]] = {}
    updated_at = ""
    for event_id, event_hash, device_id, sequence, event_created_at, applied_at in rows:
        device = str(device_id or "")
        heads_by_device[device] = {
            "device_id": device,
            "event_id": str(event_id),
            "event_hash": str(event_hash),
            "sequence": int(sequence),
            "created_at": str(event_created_at),
        }
        if str(applied_at) > updated_at:
            updated_at = str(applied_at)

    heads = [heads_by_device[device] for device in sorted(heads_by_device)]
    state = {
        "applied_count": len(rows),
        "heads": heads,
    }
    connection.execute(
        """
        INSERT INTO projection_meta(projector_id, projector_version, applied_count, heads_json, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(projector_id, projector_version)
        DO UPDATE SET
            applied_count = excluded.applied_count,
            heads_json = excluded.heads_json,
            updated_at = excluded.updated_at
        """,
        (projector_id, projector_version, len(rows), _canonical_json(heads), updated_at),
    )
    return state


def _event_already_applied(
    connection: sqlite3.Connection,
    event: ReconstructionEvent,
    *,
    projector_id: str,
    projector_version: str,
) -> bool:
    existing = connection.execute(
        """
        SELECT event_hash
        FROM event_applied
        WHERE projector_id = ? AND projector_version = ? AND event_id = ?
        """,
        (projector_id, projector_version, event.event_id),
    ).fetchone()
    if existing is not None:
        if str(existing[0]) != event.event_hash:
            raise RuntimeError("Event id is already applied with a different hash")
        return True

    hash_owner = connection.execute(
        """
        SELECT event_id
        FROM event_applied
        WHERE projector_id = ? AND projector_version = ? AND event_hash = ?
        """,
        (projector_id, projector_version, event.event_hash),
    ).fetchone()
    if hash_owner is not None:
        if str(hash_owner[0]) != event.event_id:
            raise RuntimeError(f"Event hash is already applied under another event id: {hash_owner[0]}")
        return True
    return False


def _ensure_reconstruction_schema(
    connection: sqlite3.Connection,
    *,
    vault_id: str,
    key_records: Iterable[Mapping[str, Any]],
) -> None:
    if "event_log" not in _table_names(connection):
        _reset_schema(connection)
        _insert_meta(connection, vault_id=vault_id, event_count=0)
    else:
        _ensure_projection_tracking_schema(connection)
        _require_reconstruction_schema(connection)
        if vault_id:
            connection.execute(
                """
                INSERT INTO vault_meta(key, value) VALUES ('vault_id', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (vault_id,),
            )
    _seed_identities(connection, key_records)


def _ensure_projection_tracking_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS projection_meta (
            projector_id TEXT NOT NULL,
            projector_version TEXT NOT NULL,
            applied_count INTEGER NOT NULL DEFAULT 0,
            heads_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (projector_id, projector_version)
        );

        CREATE TABLE IF NOT EXISTS event_applied (
            projector_id TEXT NOT NULL,
            projector_version TEXT NOT NULL,
            event_id TEXT NOT NULL,
            event_hash TEXT NOT NULL,
            event_type TEXT NOT NULL,
            object_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            event_created_at TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            PRIMARY KEY (projector_id, projector_version, event_id),
            UNIQUE (projector_id, projector_version, event_hash)
        );

        CREATE INDEX IF NOT EXISTS idx_event_applied_projector_order
            ON event_applied(projector_id, projector_version, device_id, sequence, event_created_at, event_id);
        CREATE INDEX IF NOT EXISTS idx_event_applied_type ON event_applied(event_type, event_created_at);
        """
    )


def _backfill_projection_events_from_event_log(
    connection: sqlite3.Connection,
    *,
    projector_id: str,
    projector_version: str,
) -> None:
    existing = connection.execute(
        """
        SELECT COUNT(*)
        FROM event_applied
        WHERE projector_id = ? AND projector_version = ?
        """,
        (projector_id, projector_version),
    ).fetchone()
    if existing is not None and int(existing[0]) > 0:
        return

    connection.execute(
        """
        INSERT OR IGNORE INTO event_applied(
            projector_id, projector_version, event_id, event_hash, event_type, object_id,
            device_id, sequence, event_created_at, applied_at
        )
        SELECT ?, ?, event_id, event_hash, event_type, object_id,
            device_id, sequence, created_at, created_at
        FROM event_log
        """,
        (projector_id, projector_version),
    )
    _refresh_projection_meta(connection, projector_id=projector_id, projector_version=projector_version)


def _refresh_status_conflicts(connection: sqlite3.Connection) -> None:
    connection.execute("DELETE FROM conflicts")
    _insert_conflicts(
        connection,
        _detect_status_conflicts(_status_observations_from_db(connection), _resolved_status_keys_from_event_log(connection)),
    )


def _status_observations_from_db(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT observation_id, object_id, field, value_json, value_text, event_id,
            author_key_id, device_id, created_at
        FROM status_observations
        ORDER BY created_at, event_id
        """
    ).fetchall()
    return [
        {
            "observation_id": observation_id,
            "object_id": object_id,
            "field": field,
            "value_json": value_json,
            "value_text": value_text,
            "event_id": event_id,
            "author_key_id": author_key_id,
            "device_id": device_id,
            "created_at": created_at,
        }
        for observation_id, object_id, field, value_json, value_text, event_id, author_key_id, device_id, created_at in rows
    ]


def _resolved_status_keys_from_event_log(connection: sqlite3.Connection) -> set[tuple[str, str]]:
    event_types = sorted(CONFLICT_RESOLUTION_EVENTS)
    placeholders = ", ".join("?" for _ in event_types)
    rows = connection.execute(
        f"SELECT object_id, payload_json FROM event_log WHERE event_type IN ({placeholders})",
        tuple(event_types),
    ).fetchall()
    resolved: set[tuple[str, str]] = set()
    for object_id, payload_json in rows:
        try:
            payload = json.loads(payload_json or "{}")
        except json.JSONDecodeError:
            payload = {}
        if not isinstance(payload, Mapping):
            payload = {}
        resolved_object_id = str(payload.get("object_id") or payload.get("resolved_object_id") or object_id)
        if resolved_object_id:
            resolved.add((resolved_object_id, _status_field(payload)))
    return resolved


def _require_reconstruction_schema(connection: sqlite3.Connection) -> None:
    _ensure_projection_tracking_schema(connection)
    required = {
        "event_log",
        "projection_meta",
        "event_applied",
        "points",
        "actions",
        "expected_pieces",
        "object_links",
        "source_import_map",
    }
    existing = {
        str(row[0])
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    missing = sorted(required - existing)
    if missing:
        raise RuntimeError(f"Reconstruction DB schema is missing tables: {', '.join(missing)}")


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }


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
