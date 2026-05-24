from __future__ import annotations



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
