from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any


TIMELINE_FIELDS = [
    "timeline_id",
    "source",
    "source_id",
    "object_id",
    "occurred_at",
    "event_type",
    "status",
    "proof_ref",
    "comment",
    "summary",
]

OBJECT_REF_FIELDS = (
    "object_id",
    "doc_id",
    "document_id",
    "decision_action_id",
    "incident_id",
    "request_id",
    "ag_id",
    "lot_id",
    "action_id",
    "shortcut_id",
)
RELATED_REF_FIELDS = (
    *OBJECT_REF_FIELDS,
    "source_object_id",
    "target_object_id",
    "parent_object_id",
    "source_doc_id",
    "proof_doc_id",
    "proof_doc_ids",
    "proof_ref",
    "proof_refs",
    "doc_ids",
    "related_doc_ids",
    "related_request_ids",
    "related_invoice_refs",
    "related_work_refs",
)
DATE_FIELDS = (
    "occurred_at",
    "created_at",
    "timestamp",
    "updated_at",
    "date",
    "date_signalement",
    "echeance",
    "imported_at",
)
STATUS_FIELDS = (
    "status",
    "statut",
    "review_status",
    "privacy_review_status",
    "new_status",
    "state",
)
PROOF_FIELDS = (
    "proof_ref",
    "proof_refs",
    "proof_doc_id",
    "proof_doc_ids",
    "preuve",
    "preuve_attendue",
    "closure_proof_ref",
    "expected_closure_proof",
)
COMMENT_FIELDS = (
    "comment",
    "commentaire",
    "comments",
    "note",
    "notes",
    "detail",
    "message",
)
SUMMARY_FIELDS = (
    "summary",
    "title",
    "label",
    "subject",
    "description",
    "decision_text",
    "action_attendue",
    "detail",
    "message",
)

PRIVATE_PATH_FIELDS = {
    "path",
    "filepath",
    "file_path",
    "local_path",
    "absolute_path",
    "source_path",
    "original_path",
    "target_path",
    "shortcut_path",
    "link_path",
    "lnk_path",
    "chemin",
    "chemin_piece",
}
PRIVATE_PATH_MARKERS = (
    "c:\\users\\",
    "\\users\\",
    "/users/",
    "/home/",
    "onedrive",
    "restricted\\",
    "\\restricted\\",
    "restreint\\",
    "\\restreint\\",
    "c8_local\\",
    "local_only\\",
)


def normalize_action_log_entries(entries: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for index, row in enumerate(entries):
        row_data = dict(row)
        occurred_at = _first_text(row_data, DATE_FIELDS)
        action = _cell(row_data.get("action"))
        event_type = _cell(row_data.get("event_type")) or "action_log_added"
        object_id = _object_id_from_row(row_data)
        target_ref = _safe_ref(row_data.get("target"))
        if not object_id and target_ref:
            object_id = target_ref

        source_id = _first_text(row_data, ("log_id", "event_id", "run_id", "action_id")) or f"action-log-{index + 1}"
        comment = _first_text(row_data, COMMENT_FIELDS)
        summary = _first_text(row_data, SUMMARY_FIELDS) or action or event_type
        normalized.append(
            {
                "timeline_id": _timeline_id("action_log", source_id, occurred_at, event_type, object_id, index),
                "source": "action_log",
                "source_id": source_id,
                "object_id": object_id,
                "occurred_at": occurred_at,
                "event_type": event_type,
                "action": action,
                "target_ref": target_ref,
                "status": _first_text(row_data, STATUS_FIELDS),
                "proof_ref": _first_text(row_data, PROOF_FIELDS),
                "comment": comment,
                "summary": summary,
            }
        )
    return normalized


def build_object_timeline(
    object_id: str,
    register_rows: Iterable[Mapping[str, Any]] | Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
    action_log_rows: Iterable[Mapping[str, Any]] | None = None,
    event_log_rows: Iterable[Mapping[str, Any]] | None = None,
) -> list[dict[str, str]]:
    wanted = _cell(object_id)
    if not wanted:
        raise ValueError("object_id is required")

    entries: list[dict[str, Any]] = []
    order = 0

    for source, row in _iter_register_rows(register_rows or []):
        entry = _register_timeline_entry(source, row, order)
        if _entry_matches_object(entry, wanted):
            entry["_order"] = order
            entries.append(entry)
        order += 1

    for entry in normalize_action_log_entries(action_log_rows or []):
        if _entry_matches_object(entry, wanted):
            entry["_order"] = order
            entries.append(entry)
        order += 1

    for row in event_log_rows or []:
        entry = _event_log_timeline_entry(row, order)
        if _entry_matches_object(entry, wanted):
            entry["_order"] = order
            entries.append(entry)
        order += 1

    entries.sort(key=lambda item: (_date_sort_key(_cell(item.get("occurred_at"))), int(item["_order"])))
    return [_public_timeline_entry(entry) for entry in entries]


def create_logical_shortcut(object_id: str, target_object_id: str, context_kind: str) -> dict[str, object]:
    source_ref = _required_logical_ref(object_id, "object_id")
    target_ref = _required_logical_ref(target_object_id, "target_object_id")
    context = _normalize_context_kind(context_kind)
    shortcut_id = "LSC-" + _sha256_text(json.dumps([source_ref, target_ref, context], separators=(",", ":")))[:16].upper()
    shortcut: dict[str, object] = {
        "shortcut_id": shortcut_id,
        "event_type": "shortcut_created",
        "object_id": source_ref,
        "target_object_id": target_ref,
        "context_kind": context,
        "relationship_type": "logical_shortcut",
        "storage_kind": "logical_reference",
        "reconstructible": True,
        "creates_windows_lnk": False,
        "target_retained_on_delete": True,
        "removes_target_on_delete": False,
        "delete_behavior": "shortcut_only",
    }
    validate_shortcut_no_private_path(shortcut)
    return shortcut


def validate_shortcut_no_private_path(shortcut: Mapping[str, Any]) -> bool:
    offenders: list[str] = []
    for key, value in shortcut.items():
        text = _cell(value)
        key_normalized = key.lower()
        if text and key_normalized in PRIVATE_PATH_FIELDS:
            offenders.append(key)
            continue
        if _looks_like_private_path(text):
            offenders.append(key)
    if offenders:
        unique = ", ".join(sorted(set(offenders)))
        raise ValueError(f"Logical shortcut must not contain private paths: {unique}")
    return True


def _register_timeline_entry(source: str, row: Mapping[str, Any], index: int) -> dict[str, str]:
    row_data = dict(row)
    occurred_at = _first_text(row_data, DATE_FIELDS)
    event_type = _first_text(row_data, ("event_type", "type", "kind")) or "register_row"
    source_id = _first_text(row_data, OBJECT_REF_FIELDS) or f"register-row-{index + 1}"
    object_id = _object_id_from_row(row_data)
    status = _first_text(row_data, STATUS_FIELDS)
    proof_ref = _first_text(row_data, PROOF_FIELDS)
    comment = _first_text(row_data, COMMENT_FIELDS)
    summary = _first_text(row_data, SUMMARY_FIELDS) or event_type
    return {
        "timeline_id": _timeline_id(source, source_id, occurred_at, event_type, object_id, index),
        "source": source,
        "source_id": source_id,
        "object_id": object_id,
        "occurred_at": occurred_at,
        "event_type": event_type,
        "status": status,
        "proof_ref": proof_ref,
        "comment": comment,
        "summary": summary,
        "_refs": ";".join(sorted(_object_refs_from_row(row_data))),
    }


def _event_log_timeline_entry(row: Mapping[str, Any], index: int) -> dict[str, str]:
    row_data = dict(row)
    payload = _payload_from_event(row_data)
    merged = dict(payload)
    merged.update({key: value for key, value in row_data.items() if key not in {"payload", "payload_json"}})

    occurred_at = _first_text(merged, DATE_FIELDS)
    event_type = _first_text(merged, ("event_type", "type", "kind")) or "event"
    source_id = _first_text(merged, ("event_id", "log_id")) or f"event-log-{index + 1}"
    object_id = _object_id_from_row(merged)
    status = _status_from_event(event_type, merged)
    proof_ref = _first_text(merged, PROOF_FIELDS)
    comment = _first_text(merged, COMMENT_FIELDS)
    summary = _first_text(merged, SUMMARY_FIELDS) or event_type
    return {
        "timeline_id": _timeline_id("event_log", source_id, occurred_at, event_type, object_id, index),
        "source": "event_log",
        "source_id": source_id,
        "object_id": object_id,
        "occurred_at": occurred_at,
        "event_type": event_type,
        "status": status,
        "proof_ref": proof_ref,
        "comment": comment,
        "summary": summary,
        "_refs": ";".join(sorted(_object_refs_from_row(merged))),
    }


def _iter_register_rows(
    register_rows: Iterable[Mapping[str, Any]] | Mapping[str, Iterable[Mapping[str, Any]]],
):
    if isinstance(register_rows, Mapping):
        for name, rows in register_rows.items():
            for row in rows:
                yield f"register:{name}", row
        return
    for row in register_rows:
        yield "register", row


def _payload_from_event(row: Mapping[str, Any]) -> dict[str, Any]:
    payload = row.get("payload")
    if isinstance(payload, Mapping):
        return dict(payload)
    payload_json = row.get("payload_json")
    if not payload_json:
        return {}
    try:
        parsed = json.loads(str(payload_json))
    except json.JSONDecodeError:
        return {}
    return dict(parsed) if isinstance(parsed, Mapping) else {}


def _status_from_event(event_type: str, row: Mapping[str, Any]) -> str:
    status = _first_text(row, STATUS_FIELDS)
    if status:
        return status
    if event_type == "status_changed":
        return _cell(row.get("value"))
    return ""


def _public_timeline_entry(entry: Mapping[str, Any]) -> dict[str, str]:
    return {field: _cell(entry.get(field)) for field in TIMELINE_FIELDS}


def _entry_matches_object(entry: Mapping[str, Any], object_id: str) -> bool:
    refs = set(_split_refs(entry.get("_refs", "")))
    refs.update(_split_refs(entry.get("object_id", "")))
    refs.update(_split_refs(entry.get("target_object_id", "")))
    refs.update(_split_refs(entry.get("proof_ref", "")))
    return object_id in refs


def _object_id_from_row(row: Mapping[str, Any]) -> str:
    return _first_text(row, OBJECT_REF_FIELDS)


def _object_refs_from_row(row: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for field in RELATED_REF_FIELDS:
        refs.update(_split_refs(row.get(field, "")))
    return {ref for ref in refs if ref and not _looks_like_private_path(ref)}


def _split_refs(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        refs: list[str] = []
        for item in value:
            refs.extend(_split_refs(item))
        return refs
    text = _cell(value)
    if not text:
        return []
    return [part for part in re.split(r"\s*[;,|]\s*", text) if part]


def _first_text(row: Mapping[str, Any], fields: Iterable[str]) -> str:
    for field in fields:
        value = _cell(row.get(field))
        if value:
            return value
    return ""


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True, ensure_ascii=True)
    return str(value).strip()


def _safe_ref(value: Any) -> str:
    text = _cell(value)
    if not text or _looks_like_private_path(text):
        return ""
    return text


def _required_logical_ref(value: str, field_name: str) -> str:
    text = _cell(value)
    if not text:
        raise ValueError(f"{field_name} is required")
    if _looks_like_private_path(text):
        raise ValueError(f"{field_name} must be an object id, not a private path")
    return text


def _normalize_context_kind(value: str) -> str:
    folded = unicodedata.normalize("NFKD", _cell(value)).encode("ascii", "ignore").decode("ascii")
    context = re.sub(r"[^a-zA-Z0-9]+", "_", folded).strip("_").lower()
    if not context:
        raise ValueError("context_kind is required")
    if _looks_like_private_path(context):
        raise ValueError("context_kind must not be a private path")
    return context


def _looks_like_private_path(value: str) -> bool:
    text = _cell(value)
    if not text:
        return False
    lowered = text.lower().replace("/", "\\")
    if text.lower().startswith("file://") or text.lower().endswith(".lnk"):
        return True
    if re.search(r"^[a-zA-Z]:\\", text) or text.startswith("\\\\"):
        return True
    if any(marker in lowered for marker in PRIVATE_PATH_MARKERS):
        return True
    if "\\" in text:
        return True
    if text.startswith("/") and "/" in text[1:]:
        return True
    return False


def _date_sort_key(value: str) -> tuple[int, datetime]:
    if not value:
        return (1, datetime.max.replace(tzinfo=timezone.utc))
    parsed = _parse_datetime(value)
    if parsed is None:
        return (0, datetime.max.replace(tzinfo=timezone.utc))
    return (0, parsed)


def _parse_datetime(value: str) -> datetime | None:
    text = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        text = f"{text}T00:00:00+00:00"
    elif text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _timeline_id(source: str, source_id: str, occurred_at: str, event_type: str, object_id: str, index: int) -> str:
    material = json.dumps(
        [source, source_id, occurred_at, event_type, object_id, index],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return "TL-" + _sha256_text(material)[:16].upper()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
