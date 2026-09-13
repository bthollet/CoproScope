from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from ..core.common import read_csv, write_csv


SYNDIC_REQUEST_FIELDS = [
    "request_id",
    "origin_kind",
    "origin_ref",
    "channel",
    "created_at",
    "subject",
    "expected_piece",
    "due_at",
    "status",
    "last_follow_up_at",
    "expected_proof",
    "response_ref",
    "proof_ref",
    "priority",
    "notes",
]

OPEN_STATUSES = {"todo", "pending", "a_relancer", "answered"}
CLOSED_STATUSES = {"closed"}
ALL_STATUSES = OPEN_STATUSES | CLOSED_STATUSES
STATUS_ORDER = {"todo": 0, "pending": 1, "a_relancer": 2, "answered": 3, "closed": 4}

STATUS_ALIASES = {
    "": "todo",
    "TODO": "todo",
    "A_FAIRE": "todo",
    "A_DEMANDER": "todo",
    "ABSENT": "todo",
    "OBSOLETE": "todo",
    "A_CLASSER": "todo",
    "PENDING": "pending",
    "EN_ATTENTE": "pending",
    "EN_ATTENTE_REPONSE": "pending",
    "EN_COURS": "pending",
    "A_RELANCER": "a_relancer",
    "RELANCE": "a_relancer",
    "EN_RELANCE": "a_relancer",
    "ANSWERED": "answered",
    "REPONDU": "answered",
    "REPONSE_RECUE": "answered",
    "RESPONSE_RECEIVED": "answered",
    "CLOSED": "closed",
    "CLOTURE": "closed",
    "CLOTUREE": "closed",
    "PRESENT": "closed",
}

CHANNEL_ALIASES = {
    "": "a_definir",
    "A_DEFINIR": "a_definir",
    "EMAIL": "email",
    "MAIL": "email",
    "COURRIEL": "email",
    "EXTRANET": "extranet",
    "PORTAIL": "extranet",
    "PORTAL": "extranet",
    "COURRIER": "courrier",
    "LRAR": "courrier",
    "RECOMMANDE": "courrier",
    "TELEPHONE": "telephone",
    "TEL": "telephone",
    "PHONE": "telephone",
    "REUNION": "reunion",
    "AG": "reunion",
    "CS": "reunion",
    "DOCOPS": "docops",
}


def _cell(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _first_value(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = _cell(row.get(name, ""))
        if value:
            return value
    return ""


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_value.casefold()).strip("_")


def _enum_key(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", _fold(value).upper()).strip("_")


def normalize_channel(value: str | None, default: str = "a_definir") -> str:
    key = _enum_key(value or "")
    if not key:
        key = _enum_key(default)
    return CHANNEL_ALIASES.get(key, _fold(value or default) or "a_definir")


def _infer_origin_kind(row: dict[str, str], default: str | None = None) -> str:
    explicit = _first_value(row, "origin_kind", "origine_kind", "source_kind", "source_module")
    if explicit:
        return _fold(explicit)
    if default:
        return _fold(default)
    if _first_value(row, "source_ref", "proof_id", "matched_doc_ids"):
        return "docops"
    if _first_value(row, "decision_action_id", "resolution_ref"):
        return "decisionops"
    if _first_value(row, "incident_id", "closure_proof_ref"):
        return "incidentops"
    return "manual"


def _normalize_date(value: str) -> str:
    parsed = _parse_date(value)
    return parsed.isoformat() if parsed else _cell(value)


def _parse_date(value: str) -> date | None:
    raw = _cell(value)
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    match = re.fullmatch(r"(20\d{2})[-_/ .]([01]?\d)", raw)
    if match:
        year, month = match.groups()
        try:
            return date(int(year), int(month), 1)
        except ValueError:
            return None
    return None


def _today(value: date | str | None) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        parsed = _parse_date(value)
        if parsed:
            return parsed
    return date.today()


def _is_overdue(due_at: str, today: date) -> bool:
    parsed = _parse_date(due_at)
    return bool(parsed and parsed < today)


def normalize_status(
    value: str | None,
    *,
    due_at: str = "",
    response_ref: str = "",
    proof_ref: str = "",
    today: date | str | None = None,
) -> str:
    requested = STATUS_ALIASES.get(_enum_key(value or ""), _fold(value or "") or "todo")
    if requested not in ALL_STATUSES:
        requested = "todo"

    has_response = bool(_cell(response_ref))
    has_proof = bool(_cell(proof_ref))
    reference_day = _today(today)

    if requested == "closed" and not has_proof:
        requested = "answered" if has_response else "todo"
    if requested == "answered" and not has_response:
        requested = "todo"
    if _is_overdue(due_at, reference_day) and not has_proof:
        return "a_relancer"
    if requested == "todo" and has_proof:
        return "closed"
    if requested == "todo" and has_response:
        return "answered"
    return requested


def _stable_request_id(row: dict[str, str]) -> str:
    source = "|".join([row.get("origin_kind", ""), row.get("origin_ref", ""), _fold(row.get("expected_piece", ""))])
    digest = hashlib.sha256((source or "syndicops").encode("utf-8")).hexdigest()
    return f"SYN-{digest[:10].upper()}"


def request_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        _fold(row.get("origin_kind", "")),
        _fold(row.get("origin_ref", "")),
        _fold(row.get("expected_piece", "")),
    )


def normalize_request(
    row: dict[str, str],
    *,
    today: date | str | None = None,
    default_channel: str = "a_definir",
    default_origin_kind: str | None = None,
) -> dict[str, str]:
    origin_kind = _infer_origin_kind(row, default_origin_kind)
    origin_ref = _first_value(
        row,
        "origin_ref",
        "origine_ref",
        "source_ref",
        "proof_id",
        "decision_action_id",
        "incident_id",
        "source_document",
        "request_id",
        "doc_id",
    )
    expected_piece = _first_value(
        row,
        "expected_piece",
        "expected_label",
        "piece_attendue",
        "document_attendu",
        "preuve_attendue",
        "expected_closure_proof",
        "document_type",
        "subject",
    )
    expected_proof = _first_value(
        row,
        "expected_proof",
        "preuve_attendue",
        "proof_expected",
        "expected_closure_proof",
        "expected_piece",
        "expected_label",
    )
    due_at = _normalize_date(_first_value(row, "due_at", "echeance", "response_due_date", "action_due_date", "date_echeance"))
    last_follow_up_at = _normalize_date(
        _first_value(row, "last_follow_up_at", "last_follow_up", "relance_at", "last_relance", "date_relance")
    )
    response_ref = _first_value(row, "response_ref", "reponse_ref", "response_document", "response_doc_ids", "response")
    proof_ref = _first_value(row, "proof_ref", "preuve_ref", "proof_doc_ids", "closure_proof_ref", "matched_doc_ids")
    notes = _join_unique(
        _first_value(row, "notes", "commentaire", "commentaires"),
        _first_value(row, "reason", "raison"),
        _first_value(row, "suggested_diligence", "diligence", "action"),
    )

    normalized = {field: "" for field in SYNDIC_REQUEST_FIELDS}
    normalized.update(
        {
            "request_id": _first_value(row, "request_id", "syndic_request_id"),
            "origin_kind": origin_kind,
            "origin_ref": origin_ref,
            "channel": normalize_channel(_first_value(row, "channel", "canal", "source_channel"), default_channel),
            "created_at": _normalize_date(_first_value(row, "created_at", "date", "date_demande")),
            "subject": _first_value(row, "subject", "objet", "action_attendue") or expected_piece,
            "expected_piece": expected_piece,
            "due_at": due_at,
            "last_follow_up_at": last_follow_up_at,
            "expected_proof": expected_proof or expected_piece,
            "response_ref": response_ref,
            "proof_ref": proof_ref,
            "priority": _first_value(row, "priority", "priorite", "criticality", "criticite") or "P2",
            "notes": notes,
        }
    )
    if not normalized["origin_ref"]:
        normalized["origin_ref"] = normalized["request_id"] or _stable_request_id(normalized)
    if not normalized["request_id"]:
        normalized["request_id"] = _stable_request_id(normalized)
    normalized["status"] = normalize_status(
        _first_value(row, "status", "statut"),
        due_at=normalized["due_at"],
        response_ref=response_ref,
        proof_ref=proof_ref,
        today=today,
    )
    return normalized


def _join_unique(*values: str) -> str:
    parts: list[str] = []
    seen: set[str] = set()
    for value in values:
        for part in re.split(r"\s*\|\s*", _cell(value)):
            if part and part not in seen:
                parts.append(part)
                seen.add(part)
    return " | ".join(parts)


def _date_sort_value(value: str, reverse_blank: bool = False) -> tuple[int, date]:
    parsed = _parse_date(value)
    if parsed:
        return (0, parsed)
    marker = date.max if reverse_blank else date.min
    return (1, marker)


def _earliest_date(left: str, right: str) -> str:
    left = _cell(left)
    right = _cell(right)
    if not left:
        return right
    if not right:
        return left
    left_date = _parse_date(left)
    right_date = _parse_date(right)
    if left_date and right_date:
        return left if left_date <= right_date else right
    if left_date:
        return left
    if right_date:
        return right
    return left


def _latest_date(left: str, right: str) -> str:
    left = _cell(left)
    right = _cell(right)
    if not left:
        return right
    if not right:
        return left
    left_date = _parse_date(left)
    right_date = _parse_date(right)
    if left_date and right_date:
        return left if left_date >= right_date else right
    if left_date:
        return left
    if right_date:
        return right
    return left


def _priority_rank(value: str) -> tuple[int, str]:
    match = re.search(r"\d+", value or "")
    if match:
        return (int(match.group(0)), value)
    return (99, value or "")


def _merge_request(left: dict[str, str], right: dict[str, str], today: date | str | None = None) -> dict[str, str]:
    merged = dict(left)
    for field in SYNDIC_REQUEST_FIELDS:
        if field in {"request_id", "status", "due_at", "last_follow_up_at", "priority", "notes"}:
            continue
        if not merged.get(field) and right.get(field):
            merged[field] = right[field]

    merged["due_at"] = _earliest_date(left.get("due_at", ""), right.get("due_at", ""))
    merged["last_follow_up_at"] = _latest_date(left.get("last_follow_up_at", ""), right.get("last_follow_up_at", ""))
    merged["priority"] = min([left.get("priority", ""), right.get("priority", "")], key=_priority_rank) or "P2"
    merged["notes"] = _join_unique(left.get("notes", ""), right.get("notes", ""))

    left_status = left.get("status", "todo")
    right_status = right.get("status", "todo")
    requested_status = max([left_status, right_status], key=lambda status: STATUS_ORDER.get(status, 0))
    merged["status"] = normalize_status(
        requested_status,
        due_at=merged.get("due_at", ""),
        response_ref=merged.get("response_ref", ""),
        proof_ref=merged.get("proof_ref", ""),
        today=today,
    )
    return merged


def normalize_requests(
    rows: Iterable[dict[str, str]],
    *,
    today: date | str | None = None,
    default_channel: str = "a_definir",
    default_origin_kind: str | None = None,
) -> list[dict[str, str]]:
    merged: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        normalized = normalize_request(
            row,
            today=today,
            default_channel=default_channel,
            default_origin_kind=default_origin_kind,
        )
        key = request_key(normalized)
        if key in merged:
            merged[key] = _merge_request(merged[key], normalized, today=today)
        else:
            merged[key] = normalized
    return sorted(
        merged.values(),
        key=lambda row: (
            _date_sort_value(row.get("due_at", ""), reverse_blank=True),
            STATUS_ORDER.get(row.get("status", ""), 0),
            row.get("origin_kind", ""),
            row.get("origin_ref", ""),
            row.get("expected_piece", ""),
        ),
    )


def read_syndic_requests(path: Path, *, today: date | str | None = None) -> list[dict[str, str]]:
    _, rows = read_csv(path)
    return normalize_requests(rows, today=today)


def write_syndic_requests(
    path: Path,
    rows: Iterable[dict[str, str]],
    *,
    today: date | str | None = None,
) -> Path:
    normalized = normalize_requests(rows, today=today)
    write_csv(path, SYNDIC_REQUEST_FIELDS, normalized)
    return path
