from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from . import reconstruction


PUBLIC_ACTIONS_VIEW = "public_actions_v1"
PUBLIC_ACTIONS_SCHEMA_VERSION = "2026-05-23.public-actions-v1"
PUBLIC_ACTIONS_COLUMNS = (
    "id",
    "title",
    "source",
    "priority",
    "priority_label",
    "detail",
    "href",
    "status",
    "status_label",
    "domain",
    "domain_label",
    "owner",
    "next_step",
    "evidence",
    "channel",
    "diffusion_label",
    "related_piece_id",
    "related_request_id",
    "request_href",
    "proof_href",
    "sort_key",
    "updated_at",
    "read_model_version",
)

_REQUIRED_TABLES = {"projection_meta", "actions", "expected_pieces", "requests"}
_REQUIRED_COLUMNS = {
    "projection_meta": {"projector_id", "projector_version", "applied_count"},
    "actions": {"action_id", "title", "source_module", "domain", "owner_ref", "status", "priority", "due_at", "next_step", "proof_expected", "diffusion_status", "updated_at"},
    "expected_pieces": {"piece_id", "label", "linked_action_id", "linked_request_id", "status", "updated_at"},
    "requests": {"request_id", "recipient_label", "linked_action_id", "linked_piece_id", "updated_at"},
}
_PUBLIC_ID_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-")
_FORBIDDEN_PATTERNS = (
    re.compile(r"payload_json|event_path|source_file|source_path|original_name|original_path|current_blob_id|source_sha256|locator_json|message_draft", re.IGNORECASE),
    re.compile(r"\b(?:chemin|raw|restricted|logs|private|secret)\b", re.IGNORECASE),
    re.compile(r"file://|[A-Za-z]:\\|\\\\", re.IGNORECASE),
    re.compile(r"(?:^|[\\/\s\"'=])/(?:Users|home)/", re.IGNORECASE),
    re.compile(r"(?:^|[?&\s])token=", re.IGNORECASE),
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE),
)


class _ActionsReadModelUnavailable(RuntimeError):
    pass


def read_public_actions_v1(
    db_path: Path,
    *,
    priority: str = "",
    scope: str = "",
    status: str = "",
    limit: int = 100,
) -> list[dict[str, object]]:
    path = Path(db_path).expanduser().resolve()
    if not path.exists():
        return []
    try:
        connection = sqlite3.connect(str(path))
        connection.row_factory = sqlite3.Row
        try:
            _require_public_actions_projection(connection)
            rows = connection.execute(
                f"""
                SELECT
                    action_id, title, source, priority, detail, status, domain,
                    domain_label, owner, next_step, evidence, channel, recipient_label,
                    diffusion_label, related_piece_id, related_request_id,
                    sort_key, updated_at
                FROM ({_public_actions_source_sql()}) AS {PUBLIC_ACTIONS_VIEW}
                WHERE (? = '' OR priority = ?)
                  AND (? = '' OR status = ?)
                  AND (? = '' OR domain = ? OR channel = ?)
                ORDER BY sort_key, title, action_id
                LIMIT ?
                """,
                (
                    _filter_priority(priority),
                    _filter_priority(priority),
                    _filter_status(status),
                    _filter_status(status),
                    _filter_scope(scope),
                    _filter_scope(scope),
                    _filter_scope(scope),
                    max(1, min(int(limit), 500)),
                ),
            ).fetchall()
            return [_public_action_row(dict(row)) for row in rows]
        finally:
            connection.close()
    except (OSError, ValueError, sqlite3.Error, _ActionsReadModelUnavailable):
        return []


def _require_public_actions_projection(connection: sqlite3.Connection) -> None:
    tables = _table_names(connection)
    if not _REQUIRED_TABLES.issubset(tables):
        raise _ActionsReadModelUnavailable("public actions source tables are absent")
    for table, required in _REQUIRED_COLUMNS.items():
        if not required.issubset(_table_columns(connection, table)):
            raise _ActionsReadModelUnavailable(f"public actions source schema is incompatible: {table}")
    meta = connection.execute(
        """
        SELECT applied_count
        FROM projection_meta
        WHERE projector_id = ? AND projector_version = ?
        LIMIT 1
        """,
        (reconstruction.DEFAULT_PROJECTION_PROJECTOR_ID, reconstruction.DEFAULT_PROJECTION_PROJECTOR_VERSION),
    ).fetchone()
    if meta is None:
        raise _ActionsReadModelUnavailable("public actions projection version is absent")


def _public_actions_source_sql() -> str:
    return """
        SELECT
            a.action_id AS action_id,
            COALESCE(NULLIF(a.title, ''), 'Action a traiter') AS title,
            COALESCE(NULLIF(a.source_module, ''), 'Projection publique') AS source,
            CASE UPPER(COALESCE(NULLIF(a.priority, ''), 'P2'))
                WHEN 'P0' THEN 'P0' WHEN 'P1' THEN 'P1' WHEN 'P3' THEN 'P3' WHEN 'OK' THEN 'OK' ELSE 'P2'
            END AS priority,
            COALESCE(NULLIF(a.next_step, ''), NULLIF(a.proof_expected, ''), 'Action a suivre sans conclure sans preuve.') AS detail,
            CASE LOWER(COALESCE(NULLIF(a.status, ''), 'open'))
                WHEN 'blocked' THEN 'bloque' WHEN 'bloque' THEN 'bloque'
                WHEN 'a_demander' THEN 'a_demander' WHEN 'waiting' THEN 'a_demander' WHEN 'preuve_a_demander' THEN 'a_demander'
                WHEN 'a_verifier' THEN 'a_verifier' WHEN 'candidate' THEN 'a_verifier'
                WHEN 'a_revoir' THEN 'a_revoir' WHEN 'review' THEN 'a_revoir'
                WHEN 'a_confirmer' THEN 'a_confirmer'
                WHEN 'clos' THEN 'clos' WHEN 'closed' THEN 'clos' WHEN 'done' THEN 'clos' WHEN 'ok' THEN 'clos'
                ELSE 'a_traiter'
            END AS status,
            COALESCE(NULLIF(a.domain, ''), 'general') AS domain,
            CASE LOWER(COALESCE(NULLIF(a.domain, ''), 'general'))
                WHEN 'comptes' THEN 'Comptes' WHEN 'confidentialite' THEN 'Confidentialite'
                WHEN 'documents' THEN 'Documents' WHEN 'decisions' THEN 'Decisions'
                WHEN 'incidents' THEN 'Incidents' ELSE 'Actions'
            END AS domain_label,
            COALESCE(NULLIF(a.owner_ref, ''), 'Conseil syndical') AS owner,
            COALESCE(NULLIF(a.next_step, ''), 'Verifier et noter la prochaine etape.') AS next_step,
            COALESCE(NULLIF(a.proof_expected, ''), NULLIF(p.label, ''), 'Preuve attendue a preciser') AS evidence,
            '' AS channel,
            COALESCE(NULLIF(r.recipient_label, ''), '') AS recipient_label,
            COALESCE(NULLIF(a.diffusion_status, ''), 'cs_only') AS diffusion_label,
            COALESCE(NULLIF(p.piece_id, ''), '') AS related_piece_id,
            COALESCE(NULLIF(p.linked_request_id, ''), NULLIF(r.request_id, ''), '') AS related_request_id,
            CASE UPPER(COALESCE(NULLIF(a.priority, ''), 'P2'))
                WHEN 'P0' THEN '0' WHEN 'P1' THEN '1' WHEN 'P2' THEN '2' WHEN 'P3' THEN '3' ELSE '4'
            END || ':' || COALESCE(NULLIF(a.updated_at, ''), '') || ':' || COALESCE(NULLIF(a.action_id, ''), '') AS sort_key,
            COALESCE(NULLIF(a.updated_at, ''), '') AS updated_at
        FROM actions a
        LEFT JOIN expected_pieces p ON p.piece_id = (
            SELECT pp.piece_id FROM expected_pieces pp
            WHERE pp.linked_action_id = a.action_id
            ORDER BY pp.updated_at DESC, pp.piece_id LIMIT 1
        )
        LEFT JOIN requests r ON r.request_id = (
            SELECT rr.request_id FROM requests rr
            WHERE rr.linked_action_id = a.action_id OR rr.linked_piece_id = p.piece_id
            ORDER BY rr.updated_at DESC, rr.request_id LIMIT 1
        )
        """


def _public_action_row(row: dict[str, Any]) -> dict[str, object]:
    action_id = _public_id(row.get("action_id"), "ACT")
    piece_id = _public_id(row.get("related_piece_id"), "PCE") if row.get("related_piece_id") else ""
    request_id = _public_id(row.get("related_request_id"), "REQ") if row.get("related_request_id") else ""
    priority = _public_priority(row.get("priority"))
    status = _public_status(row.get("status"))
    safe = {
        "id": action_id,
        "title": _public_text(row.get("title"), "Action a traiter"),
        "source": _public_text(row.get("source"), "Projection publique"),
        "priority": priority,
        "priority_label": _priority_label(priority),
        "detail": _public_text(row.get("detail"), "Action a suivre sans conclure sans preuve."),
        "href": _route_href("/actions", selected=action_id),
        "status": status,
        "status_label": _status_label(status),
        "domain": _filter_scope(row.get("domain")) or "general",
        "domain_label": _public_text(row.get("domain_label"), "Actions"),
        "owner": _public_text(row.get("owner"), "Conseil syndical"),
        "next_step": _public_text(row.get("next_step"), "Verifier et noter la prochaine etape."),
        "evidence": _public_text(row.get("evidence"), "Preuve attendue a preciser"),
        "channel": "syndic" if _is_syndic_channel(row) else "",
        "diffusion_label": _public_diffusion_label(row.get("diffusion_label")),
        "related_piece_id": piece_id,
        "related_request_id": request_id,
        "request_href": _request_href(action_id, request_id),
        "proof_href": _route_href("/depot", intent="proof", action_id=action_id, piece_detail=piece_id),
        "sort_key": _public_text(row.get("sort_key"), f"{_priority_rank(priority)}:{action_id}"),
        "updated_at": _public_text(row.get("updated_at"), ""),
        "read_model_version": PUBLIC_ACTIONS_SCHEMA_VERSION,
    }
    return {key: safe[key] for key in PUBLIC_ACTIONS_COLUMNS}


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')").fetchall()}


def _table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}


def _contains_forbidden_value(value: str) -> bool:
    return any(pattern.search(value) for pattern in _FORBIDDEN_PATTERNS)


def _public_id(value: object, prefix: str) -> str:
    text = " ".join(str(value or "").strip().split())[:140]
    if text and not _contains_forbidden_value(text) and all(char in _PUBLIC_ID_CHARS for char in text):
        return text
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:12].upper()
    return f"{prefix}-{digest or 'PUBLIC'}"


def _public_text(value: object, fallback: str = "") -> str:
    text = " ".join(str(value or "").strip().split())[:180]
    return fallback if not text or _contains_forbidden_value(text) else text


def _filter_priority(value: object) -> str:
    priority = str(value or "").strip().upper()
    return priority if priority in {"P0", "P1", "P2", "P3", "OK"} else ""


def _public_priority(value: object) -> str:
    return _filter_priority(value) or "P2"


def _filter_status(value: object) -> str:
    status = str(value or "").strip().lower()
    return status if status in {"bloque", "a_demander", "a_traiter", "a_revoir", "a_confirmer", "a_verifier", "clos"} else ""


def _public_status(value: object) -> str:
    return _filter_status(value) or "a_traiter"


def _is_syndic_channel(row: dict[str, Any]) -> bool:
    text = " ".join(str(row.get(key, "")) for key in ("channel", "owner", "next_step", "recipient_label")).lower()
    return "syndic" in text and not _contains_forbidden_value(text)


def _filter_scope(value: object) -> str:
    scope = str(value or "").strip().lower()
    return scope if scope in {"general", "comptes", "confidentialite", "documents", "decisions", "incidents", "syndic", "ag"} else ""


def _priority_label(priority: str) -> str:
    return {"P0": "Urgent", "P1": "A traiter maintenant", "P2": "A confirmer", "P3": "Suivi courant", "OK": "Cloturee"}.get(priority, "A confirmer")


def _priority_rank(priority: object) -> str:
    return {"P0": "0", "P1": "1", "P2": "2", "P3": "3"}.get(_public_priority(priority), "4")


def _status_label(status: str) -> str:
    return {
        "bloque": "Bloque",
        "a_demander": "A demander",
        "a_traiter": "A traiter",
        "a_revoir": "A arbitrer",
        "a_confirmer": "A confirmer",
        "a_verifier": "Preuve a verifier",
        "clos": "Termine",
    }.get(status, "A traiter")


def _public_diffusion_label(value: object) -> str:
    text = _public_text(value, "")
    normalized = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    labels = {
        "cs_only": "Conseil syndical uniquement",
        "conseil_syndical": "Conseil syndical uniquement",
        "syndic_only": "Syndic uniquement",
        "after_redaction": "Apres biffage ou anonymisation",
        "metadata_only": "Metadonnees uniquement",
        "public_after_review": "Diffusable apres controle",
    }
    return labels.get(normalized, text if text and "_" not in text and not text.islower() else "Conseil syndical uniquement")


def _request_href(action_id: str, request_id: str) -> str:
    query = {"action_id": action_id}
    if request_id:
        query["request_id"] = request_id
    return f"/demandes/relance?{urlencode(query)}"


def _route_href(path: str, **params: object) -> str:
    query = {key: str(value) for key, value in params.items() if value not in ("", None)}
    return f"{path}?{urlencode(query)}" if query else path
