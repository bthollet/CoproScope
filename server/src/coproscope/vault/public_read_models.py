from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from ..core.common import InstanceConfig
from . import reconstruction
from .public_actions_read_model import (
    PUBLIC_ACTIONS_COLUMNS,
    PUBLIC_ACTIONS_SCHEMA_VERSION,
    PUBLIC_ACTIONS_VIEW,
    read_public_actions_v1,
)


PUBLIC_MISSING_PIECES_VIEW = "public_missing_pieces_v1"
PUBLIC_MISSING_PIECES_COLUMNS = (
    "item_id",
    "expected_piece",
    "rubric_label",
    "reason",
    "proof_expected_label",
    "criticality",
    "criticality_label",
    "status",
    "status_label",
    "source_label",
    "owner_label",
    "related_action_id",
    "related_request_id",
    "request_href",
    "deposit_href",
    "action_href",
    "action_label",
    "candidate_count",
    "diffusion_label",
    "next_step",
    "sort_key",
    "updated_at",
)

_REQUIRED_SOURCE_TABLES = {"expected_pieces", "actions", "requests"}
_PUBLIC_ID_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-")
_FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"payload_json", re.IGNORECASE),
    re.compile(r"event_path", re.IGNORECASE),
    re.compile(r"source_file", re.IGNORECASE),
    re.compile(r"source_path", re.IGNORECASE),
    re.compile(r"original_name", re.IGNORECASE),
    re.compile(r"original_path", re.IGNORECASE),
    re.compile(r"current_blob_id", re.IGNORECASE),
    re.compile(r"source_sha256", re.IGNORECASE),
    re.compile(r"locator_json", re.IGNORECASE),
    re.compile(r"message_draft", re.IGNORECASE),
    re.compile(r"\bchemin\b", re.IGNORECASE),
    re.compile(r"\braw\b", re.IGNORECASE),
    re.compile(r"\brestricted\b", re.IGNORECASE),
    re.compile(r"\blogs\b", re.IGNORECASE),
    re.compile(r"\bprivate\b", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"(?:^|[\\/\s\"'=])/(?:Users|home)/", re.IGNORECASE),
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"\\\\"),
    re.compile(r"(?:^|[?&\s])token=", re.IGNORECASE),
    re.compile(r"\bsecret\b", re.IGNORECASE),
)


class PublicReadModelUnavailable(RuntimeError):
    """Raised when the public projection cannot be read safely."""


def public_reconstruction_db_path(instance: InstanceConfig) -> Path | None:
    local_root = _public_vault_local_root(instance)
    if local_root is None:
        return None
    try:
        return reconstruction.resolve_reconstruction_db_path(local_root)
    except RuntimeError:
        return None


def read_public_missing_pieces_v1(db_path: Path, *, limit: int = 100) -> list[dict[str, object]]:
    path = Path(db_path).expanduser().resolve()
    if not path.exists():
        raise PublicReadModelUnavailable("public read model database is absent")

    connection = sqlite3.connect(str(path))
    try:
        connection.row_factory = sqlite3.Row
        _require_public_missing_pieces_source_tables(connection)
        rows = connection.execute(
            f"""
            SELECT
                item_id,
                expected_piece,
                rubric_label,
                reason,
                proof_expected_label,
                criticality,
                criticality_label,
                status,
                status_label,
                source_label,
                owner_label,
                related_action_id,
                related_request_id,
                request_href,
                deposit_href,
                action_href,
                action_label,
                candidate_count,
                diffusion_label,
                next_step,
                sort_key,
                updated_at
            FROM (
                {_public_missing_pieces_source_sql()}
            ) AS public_missing_pieces_v1
            ORDER BY sort_key, expected_piece, item_id
            LIMIT ?
            """,
            (max(1, int(limit)),),
        ).fetchall()
        return [_public_missing_piece_row(dict(row)) for row in rows]
    except sqlite3.Error as exc:
        raise PublicReadModelUnavailable(str(exc)) from exc
    finally:
        connection.close()


def build_public_missing_pieces_model(instance: InstanceConfig, year: int) -> dict[str, object]:
    db_path = public_reconstruction_db_path(instance)
    if db_path is None:
        raise PublicReadModelUnavailable("public reconstruction database is not configured")
    rows = read_public_missing_pieces_v1(db_path)
    return _missing_pieces_template_model(instance, year, rows)


def build_empty_public_missing_pieces_model(instance: InstanceConfig, year: int) -> dict[str, object]:
    return _missing_pieces_template_model(instance, year, [])


def _require_public_missing_pieces_source_tables(connection: sqlite3.Connection) -> None:
    existing_tables = _table_names(connection)
    if not _REQUIRED_SOURCE_TABLES.issubset(existing_tables):
        missing = ", ".join(sorted(_REQUIRED_SOURCE_TABLES - existing_tables))
        raise PublicReadModelUnavailable(f"missing source tables: {missing}")


def _public_missing_pieces_source_sql() -> str:
    return """
        SELECT
            p.piece_id AS item_id,
            COALESCE(NULLIF(p.label, ''), 'Piece attendue') AS expected_piece,
            COALESCE(NULLIF(a.domain, ''), 'Piece attendue') AS rubric_label,
            COALESCE(NULLIF(p.reason, ''), NULLIF(a.next_step, ''), 'Piece necessaire pour avancer sans conclure sans preuve.') AS reason,
            COALESCE(NULLIF(a.proof_expected, ''), NULLIF(p.label, ''), 'Preuve attendue a preciser') AS proof_expected_label,
            COALESCE(NULLIF(p.priority, ''), NULLIF(a.priority, ''), 'P2') AS criticality,
            CASE UPPER(COALESCE(NULLIF(p.priority, ''), NULLIF(a.priority, ''), 'P2'))
                WHEN 'P0' THEN 'Urgent'
                WHEN 'P1' THEN 'A traiter maintenant'
                WHEN 'P2' THEN 'A confirmer'
                WHEN 'P3' THEN 'Suivi courant'
                ELSE 'A confirmer'
            END AS criticality_label,
            COALESCE(NULLIF(p.status, ''), 'open') AS status,
            CASE UPPER(COALESCE(NULLIF(p.status, ''), 'open'))
                WHEN 'OPEN' THEN 'A demander'
                WHEN 'WAITING' THEN 'A demander'
                WHEN 'A_DEMANDER' THEN 'A demander'
                WHEN 'PREUVE_A_DEMANDER' THEN 'A demander'
                ELSE 'A demander'
            END AS status_label,
            COALESCE(NULLIF(a.source_module, ''), 'Projection publique') AS source_label,
            COALESCE(NULLIF(a.owner_ref, ''), NULLIF(p.holder_label, ''), NULLIF(p.expected_from, ''), 'Syndic ou source a confirmer') AS owner_label,
            COALESCE(NULLIF(p.linked_action_id, ''), NULLIF(a.action_id, ''), '') AS related_action_id,
            COALESCE(
                NULLIF(p.linked_request_id, ''),
                (
                    SELECT rr.request_id
                    FROM requests rr
                    WHERE rr.linked_piece_id = p.piece_id
                       OR rr.linked_action_id = p.linked_action_id
                    ORDER BY rr.updated_at DESC, rr.request_id
                    LIMIT 1
                ),
                ''
            ) AS related_request_id,
            '' AS request_href,
            '' AS deposit_href,
            '' AS action_href,
            COALESCE(NULLIF(a.title, ''), 'Action a ouvrir') AS action_label,
            CASE
                WHEN p.received_doc_ids_json IS NULL THEN 0
                WHEN TRIM(p.received_doc_ids_json) = '' THEN 0
                WHEN TRIM(p.received_doc_ids_json) = '[]' THEN 0
                ELSE 1
            END AS candidate_count,
            CASE
                WHEN a.diffusion_status IS NULL OR TRIM(a.diffusion_status) = '' THEN 'Conseil syndical uniquement'
                ELSE a.diffusion_status
            END AS diffusion_label,
            COALESCE(NULLIF(a.next_step, ''), 'Demander ou rattacher la piece attendue.') AS next_step,
            CASE UPPER(COALESCE(NULLIF(p.priority, ''), NULLIF(a.priority, ''), 'P2'))
                WHEN 'P0' THEN '0'
                WHEN 'P1' THEN '1'
                WHEN 'P2' THEN '2'
                WHEN 'P3' THEN '3'
                ELSE '4'
            END || ':' || COALESCE(NULLIF(p.updated_at, ''), '') || ':' || COALESCE(NULLIF(p.piece_id, ''), '') AS sort_key,
            COALESCE(NULLIF(p.updated_at, ''), NULLIF(a.updated_at, ''), '') AS updated_at
        FROM expected_pieces p
        LEFT JOIN actions a ON a.action_id = p.linked_action_id
        WHERE UPPER(COALESCE(NULLIF(p.status, ''), 'open')) NOT IN (
            'PRESENT',
            'OK',
            'TRAITE',
            'CLOTURE',
            'CLOS',
            'SANS_SUITE',
            'CLOSED',
            'RATTACHEE'
        )
        """


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
        ).fetchall()
    }


def _public_missing_piece_row(row: dict[str, Any]) -> dict[str, object]:
    item_id = _public_id(row.get("item_id"), "PCE")
    action_id = _public_id(row.get("related_action_id"), "ACT") if row.get("related_action_id") else ""
    request_id = _public_id(row.get("related_request_id"), "REQ") if row.get("related_request_id") else ""
    candidate_count = _public_int(row.get("candidate_count"))
    status = "a_verifier" if candidate_count else _public_status(row.get("status"))
    safe_row: dict[str, object] = {
        "item_id": item_id,
        "expected_piece": _public_text(row.get("expected_piece"), "Piece attendue"),
        "rubric_label": _public_text(row.get("rubric_label"), "Piece attendue"),
        "reason": _public_text(row.get("reason"), "Piece necessaire pour avancer sans conclure sans preuve."),
        "proof_expected_label": _public_text(row.get("proof_expected_label"), "Preuve attendue a preciser"),
        "criticality": _public_priority(row.get("criticality")),
        "criticality_label": _priority_label(_public_priority(row.get("criticality"))),
        "status": status,
        "status_label": "Piece candidate a verifier" if status == "a_verifier" else "A demander",
        "source_label": _public_text(row.get("source_label"), "Projection publique"),
        "owner_label": _public_text(row.get("owner_label"), "Syndic ou source a confirmer"),
        "related_action_id": action_id,
        "related_request_id": request_id,
        "request_href": _request_href(item_id, action_id, request_id),
        "deposit_href": _route_href("/depot", intent="proof", missing_for=item_id, piece_detail=item_id),
        "action_href": _route_href("/actions", selected=action_id) if action_id else _route_href("/pieces", proof="missing"),
        "action_label": _public_text(row.get("action_label"), "Action a ouvrir"),
        "candidate_count": candidate_count,
        "diffusion_label": _public_diffusion_label(row.get("diffusion_label")),
        "next_step": _public_text(row.get("next_step"), "Demander ou rattacher la piece attendue."),
        "sort_key": _public_text(row.get("sort_key"), f"{_priority_rank(row.get('criticality'))}:{item_id}"),
        "updated_at": _public_text(row.get("updated_at"), ""),
    }
    return {key: safe_row[key] for key in PUBLIC_MISSING_PIECES_COLUMNS}


def _missing_pieces_template_model(
    instance: InstanceConfig,
    year: int,
    rows: list[dict[str, object]],
) -> dict[str, object]:
    items = [_template_missing_piece_item(row) for row in rows]
    critical_count = len([item for item in items if item.get("criticality") in {"P0", "P1"}])
    candidate_count = sum(int(item.get("candidate_count") or 0) for item in items)
    missing_view = {
        "context": {
            "route": "/pieces?proof=missing",
            "title": "Pieces manquantes",
            "subtitle": "Les pieces a obtenir, verifier ou rattacher comme preuve.",
        },
        "summary": {
            "total": len(items),
            "critical_count": critical_count,
            "candidate_count": candidate_count,
            "to_request_count": len([item for item in items if item.get("status") == "a_demander"]),
            "completion_pct": 0,
        },
        "groups": _groups_from_items(items),
        "items": items,
        "selected": items[0] if items else {},
        "empty_state": {
            "is_visible": not bool(items),
            "label": "Aucune piece manquante prioritaire n'est remontee.",
            "href": "/pieces",
        },
    }
    return {
        "instance": {
            "id": instance.instance_id,
            "name": instance.display_name,
            "root": "",
            "year": year,
        },
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Pieces manquantes",
                "active_page": "pieces",
                "search_placeholder": "Rechercher document, action, decision, fournisseur...",
                "notification_count": 0,
                "sharing_mode_label": "Mode prive local",
                "sharing_mode_status": "Aucune synchronisation externe lancee",
                "top_actions": [{"label": "Nouvelle demande", "href": "/demandes", "kind": "primary", "icon": "+"}],
            },
            "priority_views": {"missing_pieces": missing_view},
            "pieces": {
                "context": missing_view["context"],
                "summary": {
                    "total_actionable": len(items),
                    "missing_count": len([item for item in items if item.get("status") == "a_demander"]),
                    "to_deposit_count": 0,
                    "to_verify_count": candidate_count,
                    "linked_documents_count": 0,
                    "fictive_count": 0,
                    "completion_pct": 0,
                },
                "items": items,
                "missing": items,
                "to_verify": [],
                "selected": items[0] if items else {},
                "empty_state": missing_view["empty_state"],
            },
        },
        "piece_workshop": {
            "items": [],
            "to_request": [],
            "to_verify": [],
            "summary": {
                "total": len(items),
                "needs_action": len(items),
                "with_local_proof": 0,
                "without_local_proof": len(items),
                "by_source": {},
                "by_status": {},
            },
        },
        "accounting": {"guide": {"p1": [], "p2": [], "ok": []}},
        "action_summary": {
            "total": "",
            "accounting": "",
            "scope_counts": {"syndic": ""},
        },
        "kpis": {
            "actions": "",
            "doc_requests": len(items),
            "decisions": "",
            "privacy_reviews": "",
        },
        "public_read_model": PUBLIC_MISSING_PIECES_VIEW,
    }


def _template_missing_piece_item(row: dict[str, object]) -> dict[str, object]:
    item = dict(row)
    item["id"] = row["item_id"]
    item["priority"] = row["criticality"]
    candidate_count = min(_public_int(row.get("candidate_count")), 9)
    item["candidate_docs"] = [{"label": "Piece candidate a verifier"} for _ in range(candidate_count)]
    item["related_event_id"] = row["related_action_id"] or row["item_id"]
    item["proof_purpose"] = "Prouver ou confirmer le point rattache avant passation."
    return item


def _groups_from_items(items: list[dict[str, object]]) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    for item in items:
        label = str(item.get("rubric_label") or "Piece attendue")
        counts[label] = counts.get(label, 0) + 1
    return [
        {"id": _public_id(label, "RUB"), "label": label, "count": count}
        for label, count in sorted(counts.items())
    ]


def _public_vault_local_root(instance: InstanceConfig) -> Path | None:
    settings = instance.settings()
    vault_settings = settings.get("vault") or settings.get("coffre") or {}
    if not isinstance(vault_settings, dict):
        return None
    local_value = vault_settings.get("local_root") or vault_settings.get("local") or vault_settings.get("cache_root")
    if not local_value:
        return None
    return instance.resolve_path(str(local_value))


def _public_id(value: object, prefix: str) -> str:
    text = " ".join(str(value or "").strip().split())[:140]
    if text and not _contains_forbidden_value(text) and all(char in _PUBLIC_ID_CHARS for char in text):
        return text
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:12].upper()
    return f"{prefix}-{digest or 'PUBLIC'}"


def _public_text(value: object, fallback: str = "") -> str:
    text = " ".join(str(value or "").strip().split())[:180]
    if not text:
        return fallback
    if _contains_forbidden_value(text):
        return fallback
    return text


def _public_diffusion_label(value: object) -> str:
    fallback = "Conseil syndical uniquement"
    text = _public_text(value, "")
    if not text:
        return fallback
    normalized = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    labels = {
        "cs_only": fallback,
        "conseil_syndical": fallback,
        "conseil_syndical_uniquement": fallback,
        "syndic_only": "Syndic uniquement",
        "after_redaction": "Apres biffage ou anonymisation",
        "diffusion_after_redaction": "Apres biffage ou anonymisation",
        "metadata_only": "Metadonnees uniquement",
        "public_after_review": "Diffusable apres controle",
        "diffusable_after_review": "Diffusable apres controle",
    }
    if normalized in labels:
        return labels[normalized]
    if "_" in text or text.islower():
        return fallback
    return text


def _public_int(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _contains_forbidden_value(value: str) -> bool:
    return any(pattern.search(value) for pattern in _FORBIDDEN_VALUE_PATTERNS)


def _public_priority(value: object) -> str:
    priority = str(value or "").strip().upper()
    return priority if priority in {"P0", "P1", "P2", "P3", "OK"} else "P2"


def _priority_label(priority: str) -> str:
    return {
        "P0": "Urgent",
        "P1": "A traiter maintenant",
        "P2": "A confirmer",
        "P3": "Suivi courant",
        "OK": "Cloturee",
    }.get(priority, "A confirmer")


def _priority_rank(priority: object) -> str:
    return {"P0": "0", "P1": "1", "P2": "2", "P3": "3"}.get(_public_priority(priority), "4")


def _public_status(value: object) -> str:
    status = str(value or "").strip().lower()
    if status in {"a_verifier", "candidate"}:
        return "a_verifier"
    return "a_demander"


def _request_href(item_id: str, action_id: str, request_id: str) -> str:
    query: dict[str, str] = {"piece_detail": item_id}
    if request_id:
        query["request_id"] = request_id
    elif action_id:
        query["action_id"] = action_id
    else:
        query["scope"] = "pieces"
    return f"/demandes/relance?{urlencode(query)}"


def _route_href(path: str, **params: object) -> str:
    query = {key: str(value) for key, value in params.items() if value not in ("", None)}
    return f"{path}?{urlencode(query)}" if query else path
