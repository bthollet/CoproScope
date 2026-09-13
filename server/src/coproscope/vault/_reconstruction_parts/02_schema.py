from __future__ import annotations



def _reset_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        DROP TABLE IF EXISTS source_import_map;
        DROP TABLE IF EXISTS object_followups;
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
        DROP TABLE IF EXISTS event_applied;
        DROP TABLE IF EXISTS projection_meta;
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

        CREATE TABLE projection_meta (
            projector_id TEXT NOT NULL,
            projector_version TEXT NOT NULL,
            applied_count INTEGER NOT NULL DEFAULT 0,
            heads_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (projector_id, projector_version)
        );

        CREATE TABLE event_applied (
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
        CREATE INDEX idx_event_applied_projector_order
            ON event_applied(projector_id, projector_version, device_id, sequence, event_created_at, event_id);
        CREATE INDEX idx_event_applied_type ON event_applied(event_type, event_created_at);
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
    _ensure_object_followups_schema(connection)


def _ensure_object_followups_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS object_followups (
            row_id TEXT PRIMARY KEY,
            parent_kind TEXT NOT NULL,
            parent_id TEXT NOT NULL,
            followup_kind TEXT NOT NULL,
            followup_id TEXT NOT NULL,
            effect TEXT NOT NULL,
            summary TEXT,
            status_after TEXT,
            remaining_reason TEXT,
            occurred_at TEXT NOT NULL,
            visibility TEXT,
            event_id TEXT NOT NULL,
            event_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE (parent_kind, parent_id, followup_kind, followup_id, event_id),
            FOREIGN KEY (event_id) REFERENCES event_log(event_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_object_followups_parent
            ON object_followups(parent_kind, parent_id, occurred_at, event_id);
        CREATE INDEX IF NOT EXISTS idx_object_followups_followup
            ON object_followups(followup_kind, followup_id);
        CREATE INDEX IF NOT EXISTS idx_object_followups_effect
            ON object_followups(effect, status_after);
        """
    )


def _insert_meta(connection: sqlite3.Connection, *, vault_id: str, event_count: int) -> None:
    values = {
        "schema": "coproscope-vault-reconstruction-v1",
        "vault_id": vault_id,
        "event_count": str(event_count),
    }
    connection.executemany("INSERT INTO vault_meta(key, value) VALUES (?, ?)", sorted(values.items()))
    _refresh_projection_meta(
        connection,
        projector_id=DEFAULT_PROJECTION_PROJECTOR_ID,
        projector_version=DEFAULT_PROJECTION_PROJECTOR_VERSION,
    )


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


def _insert_event_log_if_missing(connection: sqlite3.Connection, event: ReconstructionEvent) -> int:
    existing = connection.execute(
        "SELECT event_order, event_hash FROM event_log WHERE event_id = ?",
        (event.event_id,),
    ).fetchone()
    if existing is not None:
        if str(existing[1]) != event.event_hash:
            raise RuntimeError("Event id is already recorded with a different hash")
        return int(existing[0])

    hash_owner = connection.execute(
        "SELECT event_order, event_id FROM event_log WHERE event_hash = ?",
        (event.event_hash,),
    ).fetchone()
    if hash_owner is not None:
        raise RuntimeError(f"Event hash is already recorded under another event id: {hash_owner[1]}")

    row = connection.execute("SELECT COALESCE(MAX(event_order), 0) + 1 FROM event_log").fetchone()
    next_order = int(row[0]) if row is not None else 1
    _insert_event_log(connection, next_order, event)
    return next_order


def _apply_projection_event(connection: sqlite3.Connection, event: ReconstructionEvent) -> None:
    _record_identity_event(connection, event)
    _record_document_event(connection, event)
    _record_business_object_event(connection, event)
    _record_status_event(connection, event)
