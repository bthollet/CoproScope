from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path
from typing import Any

from . import reconstruction


OBJECT_FOLLOWUPS_VIEW = "object_followups_v1"
OBJECT_FOLLOWUPS_SCHEMA_VERSION = "2026-05-27.object-followups-v1"
OBJECT_FOLLOWUPS_COLUMNS = (
    "parent_kind",
    "parent_id",
    "followup_kind",
    "followup_id",
    "effect",
    "summary",
    "status_after",
    "remaining_reason",
    "occurred_at",
    "visibility",
    "read_model_version",
)

_REQUIRED_TABLES = {"projection_meta", "object_followups"}
_PUBLIC_ID_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-")
_ALLOWED_EFFECTS = {"opens", "updates", "partially_resolves", "resolves", "keeps_open", "waives"}
_ALLOWED_KINDS = {
    "action",
    "expected_piece",
    "human_validation",
    "incident",
    "milestone",
    "object",
    "point",
    "proof",
    "reconciliation_cell",
    "reconciliation_line",
    "request",
    "request_action",
    "works_project",
}
_FORBIDDEN_PATTERNS = (
    re.compile(r"payload_json|event_path|source_file|source_path|original_name|original_path|current_blob_id|source_sha256|locator_json|message_draft", re.IGNORECASE),
    re.compile(r"\b(?:chemin|raw|restricted|logs|private|secret)\b", re.IGNORECASE),
    re.compile(r"file://|[A-Za-z]:\\|\\\\", re.IGNORECASE),
    re.compile(r"(?:^|[\\/\s\"'=])/(?:Users|home)/", re.IGNORECASE),
    re.compile(r"(?:^|[?&\s])token=", re.IGNORECASE),
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE),
)


class ObjectFollowupsReadModelUnavailable(RuntimeError):
    pass


def read_object_followups_v1(
    db_path: Path,
    *,
    parent_kind: str = "",
    parent_id: str = "",
    limit: int = 100,
) -> list[dict[str, object]]:
    path = Path(db_path).expanduser().resolve()
    if not path.exists():
        return []
    kind_filter = _filter_kind(parent_kind)
    id_filter = _public_filter_id(parent_id)
    if str(parent_kind or "").strip() and not kind_filter:
        return []
    if str(parent_id or "").strip() and not id_filter:
        return []
    try:
        connection = sqlite3.connect(str(path))
        connection.row_factory = sqlite3.Row
        try:
            _require_projection(connection)
            rows = connection.execute(
                """
                SELECT
                    parent_kind,
                    parent_id,
                    followup_kind,
                    followup_id,
                    effect,
                    summary,
                    status_after,
                    remaining_reason,
                    occurred_at,
                    visibility
                FROM object_followups
                WHERE (? = '' OR parent_kind = ?)
                  AND (? = '' OR parent_id = ?)
                ORDER BY occurred_at, event_id, row_id
                LIMIT ?
                """,
                (
                    kind_filter,
                    kind_filter,
                    id_filter,
                    id_filter,
                    max(1, min(int(limit), 500)),
                ),
            ).fetchall()
            return [_public_followup_row(dict(row)) for row in rows]
        finally:
            connection.close()
    except (OSError, ValueError, sqlite3.Error, ObjectFollowupsReadModelUnavailable):
        return []


def _require_projection(connection: sqlite3.Connection) -> None:
    tables = {
        str(row[0])
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')").fetchall()
    }
    if not _REQUIRED_TABLES.issubset(tables):
        raise ObjectFollowupsReadModelUnavailable("object followups source tables are absent")
    columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(object_followups)").fetchall()}
    if not set(OBJECT_FOLLOWUPS_COLUMNS[:-1]).issubset(columns):
        raise ObjectFollowupsReadModelUnavailable("object followups source schema is incompatible")
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
        raise ObjectFollowupsReadModelUnavailable("object followups projection version is absent")


def _public_followup_row(row: dict[str, Any]) -> dict[str, object]:
    parent_kind = _kind(row.get("parent_kind"))
    followup_kind = _kind(row.get("followup_kind"))
    effect = _effect(row.get("effect"))
    safe = {
        "parent_kind": parent_kind,
        "parent_id": _public_id(row.get("parent_id"), _prefix(parent_kind)),
        "followup_kind": followup_kind,
        "followup_id": _public_id(row.get("followup_id"), _prefix(followup_kind)),
        "effect": effect,
        "summary": _summary_text(effect, row.get("summary")),
        "status_after": _public_status(row.get("status_after"), effect),
        "remaining_reason": _public_text(row.get("remaining_reason"), ""),
        "occurred_at": _public_text(row.get("occurred_at"), ""),
        "visibility": _visibility(row.get("visibility")),
        "read_model_version": OBJECT_FOLLOWUPS_SCHEMA_VERSION,
    }
    return {key: safe[key] for key in OBJECT_FOLLOWUPS_COLUMNS}


def _kind(value: object) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return text if text in _ALLOWED_KINDS else "object"


def _filter_kind(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    kind = _kind(text)
    return "" if kind == "object" and text.lower() != "object" else kind


def _effect(value: object) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {"partial": "partially_resolves", "partial_resolve": "partially_resolves", "sans_suite": "waives"}
    text = aliases.get(text, text)
    return text if text in _ALLOWED_EFFECTS else "updates"


def _public_filter_id(value: object) -> str:
    text = str(value or "").strip()
    return text if text and not _contains_forbidden_value(text) else ""


def _public_id(value: object, prefix: str) -> str:
    text = " ".join(str(value or "").strip().split())[:140]
    if text and not _contains_forbidden_value(text) and all(char in _PUBLIC_ID_CHARS for char in text):
        return text
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:12].upper()
    return f"{prefix}-{digest or 'PUBLIC'}"


def _public_text(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").strip().split())[:220]
    return fallback if not text or _contains_forbidden_value(text) else text


def _summary_text(effect: str, value: object) -> str:
    label = _effect_label(effect)
    text = _public_text(value, "")
    return f"{label}: {text}" if text else label


def _public_status(value: object, effect: str) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if text and not _contains_forbidden_value(text):
        return text[:80]
    return {
        "opens": "open",
        "updates": "open",
        "partially_resolves": "partially_resolved",
        "resolves": "resolved",
        "keeps_open": "open",
        "waives": "sans_suite",
    }.get(effect, "open")


def _visibility(value: object) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    labels = {
        "cs_only": "conseil_syndical",
        "conseil_syndical": "conseil_syndical",
        "metadata_only": "metadata_only",
        "public_after_review": "public_after_review",
        "after_redaction": "after_redaction",
    }
    return labels.get(text, "conseil_syndical")


def _effect_label(effect: str) -> str:
    return {
        "opens": "suivi ouvert",
        "updates": "suivi mis a jour",
        "partially_resolves": "leve partiellement",
        "resolves": "leve",
        "keeps_open": "reste ouvert",
        "waives": "classe sans suite",
    }.get(effect, "suivi mis a jour")


def _prefix(kind: str) -> str:
    return {
        "action": "ACT",
        "expected_piece": "PCE",
        "human_validation": "VAL",
        "incident": "INC",
        "milestone": "MS",
        "point": "POINT",
        "proof": "PRF",
        "reconciliation_cell": "CELL",
        "reconciliation_line": "LINE",
        "request": "REQ",
        "request_action": "REQACT",
        "works_project": "WRK",
    }.get(kind, "OBJ")


def _contains_forbidden_value(value: str) -> bool:
    return any(pattern.search(value) for pattern in _FORBIDDEN_PATTERNS)
