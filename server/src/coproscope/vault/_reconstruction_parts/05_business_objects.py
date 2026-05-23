from __future__ import annotations



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
