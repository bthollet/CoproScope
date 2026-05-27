from __future__ import annotations


_FOLLOWUP_EFFECTS = frozenset({"opens", "updates", "partially_resolves", "resolves", "keeps_open", "waives"})
_BLOCKING_PARENT_KINDS = frozenset({"point", "incident", "reconciliation_cell", "reconciliation_line", "works_project", "milestone", "action"})


def _upsert_proof(connection: sqlite3.Connection, event: ReconstructionEvent, data: Mapping[str, Any]) -> None:
    proof_id = _first_text(data, ("proof_id", "preuve_id", "id")) or event.object_id
    if not proof_id:
        return
    effect = _normalize_followup_effect(
        _first_text(data, ("effect", "followup_effect", "resolution_effect", "proof_effect"))
        or "partially_resolves"
    )
    summary = _first_text(data, ("summary", "resume", "description", "label"))
    status_after = _first_text(data, ("status_after", "parent_status_after")) or _status_after_for_effect(effect)

    _upsert_current_object(
        connection,
        table="proofs",
        id_column="proof_id",
        object_id=proof_id,
        event=event,
        insert_values={
            "source_document_id": _first_text(data, ("source_document_id", "document_id", "doc_id")),
            "source_version_id": _first_text(data, ("source_version_id", "version_id")),
            "locator_json": _locator_json(_first_value(data, ("locator_json", "locator", "source_locator"))),
            "summary": summary,
            "confidence": _first_text(data, ("confidence", "confiance")),
            "status": _first_text(data, ("status", "statut")) or "recorded",
        },
        update_values={
            "source_document_id": _first_text(data, ("source_document_id", "document_id", "doc_id")),
            "source_version_id": _first_text(data, ("source_version_id", "version_id")),
            "locator_json": _locator_json(_first_value(data, ("locator_json", "locator", "source_locator"))),
            "summary": summary,
            "confidence": _first_text(data, ("confidence", "confiance")),
            "status": _first_text(data, ("status", "statut")),
        },
    )
    _record_object_event_source(connection, "proof", proof_id, event, source_module=_source_module(event, data))
    _record_standard_links(connection, event, "proof", proof_id, data)

    target_kind, target_id = _proof_target_ref(data)
    if target_kind and target_id:
        relation = "proven_by" if effect == "resolves" else "partially_proven_by"
        _insert_object_link(connection, target_kind, target_id, relation, "proof", proof_id, event)
        _insert_object_link(connection, "proof", proof_id, "proves", target_kind, target_id, event)
        if target_kind == "expected_piece":
            _update_expected_piece_from_proof(connection, event, data, piece_id=target_id, proof_id=proof_id, effect=effect)

    parents = _parents_for_followup_target(connection, data, target_kind, target_id)
    for parent_kind, parent_id in parents:
        _insert_object_followup(
            connection,
            event,
            parent_kind=parent_kind,
            parent_id=parent_id,
            followup_kind="proof",
            followup_id=proof_id,
            effect=effect,
            summary=summary,
            status_after=status_after,
            remaining_reason=_first_text(data, ("remaining_reason", "reste_a_traiter", "reserve")),
            visibility=_first_text(data, ("visibility", "visibilite")) or "cs_only",
            occurred_at=_first_text(data, ("occurred_at", "received_at", "date")) or event.created_at,
        )
        _insert_object_link(connection, parent_kind, parent_id, _proof_parent_relation(effect), "proof", proof_id, event)


def _insert_explicit_object_followup(
    connection: sqlite3.Connection,
    event: ReconstructionEvent,
    data: Mapping[str, Any],
) -> None:
    parent_kind = _first_text(data, ("parent_kind", "root_kind", "parent_object_kind"))
    parent_id = _first_text(data, ("parent_id", "root_id", "parent_object_id"))
    followup_kind = _first_text(data, ("followup_kind", "child_kind", "target_kind"))
    followup_id = _first_text(data, ("followup_id", "child_id", "target_id")) or event.object_id
    if not parent_kind or not parent_id or not followup_kind or not followup_id:
        return

    effect = _normalize_followup_effect(_first_text(data, ("effect", "followup_effect")) or "updates")
    relation = _first_text(data, ("relation", "link_relation")) or _relation_for_followup(followup_kind, effect)
    if _kind(parent_kind) == _kind(followup_kind) and parent_id == followup_id:
        return
    _insert_object_followup(
        connection,
        event,
        parent_kind=parent_kind,
        parent_id=parent_id,
        followup_kind=followup_kind,
        followup_id=followup_id,
        effect=effect,
        summary=_first_text(data, ("summary", "resume", "description")),
        status_after=_first_text(data, ("status_after", "statut_apres")) or _status_after_for_effect(effect),
        remaining_reason=_first_text(data, ("remaining_reason", "reste_a_traiter", "reserve")),
        visibility=_first_text(data, ("visibility", "visibilite")) or "cs_only",
        occurred_at=_first_text(data, ("occurred_at", "date")) or event.created_at,
    )
    _insert_object_link(connection, _kind(parent_kind), parent_id, relation, _kind(followup_kind), followup_id, event)


def _record_parent_followups(
    connection: sqlite3.Connection,
    event: ReconstructionEvent,
    data: Mapping[str, Any],
    *,
    followup_kind: str,
    followup_id: str,
    relation: str,
    default_effect: str,
    summary: str,
    status_after: str,
) -> None:
    effect = _normalize_followup_effect(_first_text(data, ("followup_effect", "effect")) or default_effect)
    for parent_kind, parent_id in _parent_refs_from_data(data):
        if _kind(parent_kind) == _kind(followup_kind) and parent_id == followup_id:
            continue
        _insert_object_followup(
            connection,
            event,
            parent_kind=parent_kind,
            parent_id=parent_id,
            followup_kind=followup_kind,
            followup_id=followup_id,
            effect=effect,
            summary=summary,
            status_after=status_after or _status_after_for_effect(effect),
            remaining_reason=_first_text(data, ("remaining_reason", "reste_a_traiter", "reserve")),
            visibility=_first_text(data, ("visibility", "visibilite", "diffusion_status")) or "cs_only",
            occurred_at=_first_text(data, ("occurred_at", "date")) or event.created_at,
        )
        _insert_object_link(connection, parent_kind, parent_id, relation, followup_kind, followup_id, event)


def _insert_object_followup(
    connection: sqlite3.Connection,
    event: ReconstructionEvent,
    *,
    parent_kind: str,
    parent_id: str,
    followup_kind: str,
    followup_id: str,
    effect: str,
    summary: str,
    status_after: str,
    remaining_reason: str,
    visibility: str,
    occurred_at: str,
) -> None:
    parent_kind = _kind(parent_kind)
    followup_kind = _kind(followup_kind)
    parent_id = str(parent_id or "").strip()
    followup_id = str(followup_id or "").strip()
    if not parent_kind or not parent_id or not followup_kind or not followup_id:
        return
    if parent_kind == followup_kind and parent_id == followup_id:
        return
    row_id = "fup_" + _sha256_text(
        _canonical_json([parent_kind, parent_id, followup_kind, followup_id, event.event_id])
    )[:24]
    connection.execute(
        """
        INSERT OR IGNORE INTO object_followups(
            row_id, parent_kind, parent_id, followup_kind, followup_id, effect,
            summary, status_after, remaining_reason, occurred_at, visibility,
            event_id, event_hash, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row_id,
            parent_kind,
            parent_id,
            followup_kind,
            followup_id,
            _normalize_followup_effect(effect),
            summary,
            status_after,
            remaining_reason,
            occurred_at or event.created_at,
            visibility or "cs_only",
            event.event_id,
            event.event_hash,
            event.created_at,
        ),
    )


def _parents_for_followup_target(
    connection: sqlite3.Connection,
    data: Mapping[str, Any],
    target_kind: str,
    target_id: str,
) -> list[tuple[str, str]]:
    refs = _parent_refs_from_data(data)
    if target_kind and target_id:
        refs.extend(
            (_kind(row[0]), str(row[1]))
            for row in connection.execute(
                """
                SELECT parent_kind, parent_id
                FROM object_followups
                WHERE followup_kind = ? AND followup_id = ?
                ORDER BY occurred_at, event_id, row_id
                """,
                (_kind(target_kind), target_id),
            ).fetchall()
        )
        refs.extend(
            (_kind(row[0]), str(row[1]))
            for row in connection.execute(
                """
                SELECT source_kind, source_id
                FROM object_links
                WHERE target_kind = ? AND target_id = ?
                ORDER BY created_at, event_id, link_id
                """,
                (_kind(target_kind), target_id),
            ).fetchall()
            if _kind(row[0]) in _BLOCKING_PARENT_KINDS
        )
    return _dedupe_refs(refs)


def _parent_refs_from_data(data: Mapping[str, Any]) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []
    for kind_field, id_field in (
        ("parent_kind", "parent_id"),
        ("root_kind", "root_id"),
        ("parent_object_kind", "parent_object_id"),
    ):
        kind = _first_text(data, (kind_field,))
        object_id = _first_text(data, (id_field,))
        if kind and object_id:
            refs.append((kind, object_id))

    refs.extend(("point", value) for value in _as_text_list(_first_value(data, ("related_point_ids", "point_ids", "points"))))
    refs.extend(("point", value) for value in _as_text_list(_first_value(data, ("point_id",))))
    refs.extend(("incident", value) for value in _as_text_list(_first_value(data, ("incident_ids", "incident_id"))))
    refs.extend(("reconciliation_cell", value) for value in _as_text_list(_first_value(data, ("reconciliation_cell_ids", "reconciliation_cell_id", "cell_id"))))
    refs.extend(("reconciliation_line", value) for value in _as_text_list(_first_value(data, ("reconciliation_line_id", "queue_line_id"))))
    refs.extend(("works_project", value) for value in _as_text_list(_first_value(data, ("works_project_id", "worksite_id", "chantier_id"))))
    refs.extend(("milestone", value) for value in _as_text_list(_first_value(data, ("milestone_id", "jalon_id"))))
    refs.extend(("action", value) for value in _as_text_list(_first_value(data, ("linked_action_id", "related_action_id"))))
    refs.extend(("expected_piece", value) for value in _as_text_list(_first_value(data, ("linked_piece_id",))))
    return _dedupe_refs(refs)


def _proof_target_ref(data: Mapping[str, Any]) -> tuple[str, str]:
    target_kind = _first_text(data, ("target_kind", "target_object_kind"))
    target_id = _first_text(data, ("target_id", "target_object_id"))
    if target_kind and target_id:
        return _kind(target_kind), target_id
    for kind, names in (
        ("expected_piece", ("expected_piece_id", "piece_id", "linked_piece_id")),
        ("reconciliation_cell", ("reconciliation_cell_id", "cell_id", "queue_cell_id")),
        ("reconciliation_line", ("reconciliation_line_id", "queue_line_id")),
        ("milestone", ("milestone_id", "jalon_id")),
        ("action", ("linked_action_id", "action_id")),
        ("request", ("request_id", "linked_request_id")),
        ("point", ("point_id",)),
        ("incident", ("incident_id",)),
    ):
        object_id = _first_text(data, names)
        if object_id:
            return kind, object_id
    return "", ""


def _update_expected_piece_from_proof(
    connection: sqlite3.Connection,
    event: ReconstructionEvent,
    data: Mapping[str, Any],
    *,
    piece_id: str,
    proof_id: str,
    effect: str,
) -> None:
    row = connection.execute(
        "SELECT proof_ids_json, status, source_event_ids_json FROM expected_pieces WHERE piece_id = ?",
        (piece_id,),
    ).fetchone()
    if row is None:
        return
    status = _first_text(data, ("target_status_after", "piece_status_after"))
    if not status:
        status = _piece_status_for_effect(effect, str(row[1] or "open"))
    connection.execute(
        """
        UPDATE expected_pieces
        SET proof_ids_json = ?, status = ?, updated_from_event_hash = ?,
            source_event_ids_json = ?, updated_at = ?
        WHERE piece_id = ?
        """,
        (
            _append_json_unique(row[0], proof_id),
            status,
            event.event_hash,
            _append_json_unique(row[2], event.event_id),
            event.created_at,
            piece_id,
        ),
    )


def _dedupe_refs(refs: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw_kind, raw_id in refs:
        kind = _kind(raw_kind)
        object_id = str(raw_id or "").strip()
        key = (kind, object_id)
        if kind and object_id and key not in seen:
            result.append(key)
            seen.add(key)
    return result


def _locator_json(value: Any) -> str:
    if value is None or value == "":
        return _canonical_json({})
    if isinstance(value, Mapping):
        return _canonical_json(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = {"label": value}
        return _canonical_json(parsed)
    return _canonical_json({"value": str(value)})


def _relation_for_followup(followup_kind: str, effect: str) -> str:
    kind = _kind(followup_kind)
    if kind == "action":
        return "followed_by"
    if kind == "expected_piece":
        return "expects"
    if kind == "proof":
        return _proof_parent_relation(effect)
    if kind == "request":
        return "requested_via"
    if kind in {"human_validation", "validation", "review"}:
        return "reviewed_by"
    return "updates"


def _proof_parent_relation(effect: str) -> str:
    return "proven_by" if _normalize_followup_effect(effect) == "resolves" else "partially_proven_by"


def _normalize_followup_effect(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "partial": "partially_resolves",
        "partially_resolved": "partially_resolves",
        "partial_resolve": "partially_resolves",
        "resolved": "resolves",
        "close": "resolves",
        "closed": "resolves",
        "sans_suite": "waives",
        "waived": "waives",
        "reserve": "keeps_open",
        "with_reserve": "keeps_open",
        "validated_with_reserve": "keeps_open",
    }
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in _FOLLOWUP_EFFECTS else "updates"


def _status_after_for_effect(effect: str) -> str:
    return {
        "opens": "open",
        "updates": "open",
        "partially_resolves": "partially_resolved",
        "resolves": "resolved",
        "keeps_open": "open",
        "waives": "sans_suite",
    }.get(_normalize_followup_effect(effect), "open")


def _piece_status_for_effect(effect: str, current_status: str) -> str:
    normalized = _normalize_followup_effect(effect)
    if normalized == "resolves":
        return "present"
    if normalized == "partially_resolves":
        return "partially_resolved"
    if normalized == "waives":
        return "sans_suite"
    return current_status or "open"


def _kind(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
