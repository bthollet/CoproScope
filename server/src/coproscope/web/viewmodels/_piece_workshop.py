from __future__ import annotations

from ._runtime import *

def _first_value(row: dict[str, str], *fields: str) -> str:
    for field in fields:
        value = row.get(field, "")
        if value:
            return value
    return ""


def _split_piece_refs(value: str) -> list[str]:
    refs: list[str] = []
    for chunk in (value or "").replace(";", ",").replace("|", ",").split(","):
        ref = chunk.strip()
        if not ref:
            continue
        refs.append(ref.split(":", 1)[0].strip())
    return [ref for ref in refs if ref]


def _first_document_for_piece(
    documents_by_id: dict[str, dict[str, str]],
    proof_ref: str,
) -> dict[str, str]:
    for ref in _split_piece_refs(proof_ref):
        if ref in documents_by_id:
            return documents_by_id[ref]
    return {}


def _piece_signature_badge(piece: str, row: dict[str, str] | None = None) -> str:
    haystack = " ".join(
        [
            piece or "",
            (row or {}).get("document_type", ""),
            (row or {}).get("expected_label", ""),
            (row or {}).get("notes", ""),
        ]
    ).lower()
    signature_markers = (" signe", " signee", "signature", "ordre de service", "devis vote")
    return "signature attendue" if any(marker in haystack for marker in signature_markers) else ""


def _workshop_tone(status: str, priority: str, has_local_proof: bool) -> str:
    normalized = (status or "").upper()
    if normalized in {"PRESENT", "OK", "TRAITE", "CLOTURE", "CLOS"}:
        return "ok"
    if has_local_proof and normalized in {"PREUVE_LOCALE_A_VERIFIER", "A_CLASSER", "A_VERIFIER_CLASSEMENT"}:
        return "p2"
    return (priority or "P2").lower()


def _workshop_requires_action(status: str) -> bool:
    normalized = (status or "").upper()
    return normalized not in {"", "PRESENT", "OK", "TRAITE", "CLOTURE", "CLOS", "SANS_SUITE"}


def _piece_workshop_item(
    *,
    source: str,
    point_type: str,
    point: str,
    piece: str,
    status: str,
    priority: str,
    action: str,
    next_step: str,
    proof_ref: str = "",
    point_id: str = "",
    request_id: str = "",
    href: str = "/pieces",
    privacy_badge: str = "",
    confidence_badge: str = "",
    signature_badge: str = "",
) -> dict[str, object]:
    has_local_proof = bool(proof_ref)
    requires_action = _workshop_requires_action(status)
    primary_action = next_step or action or "Qualifier le point puis rattacher la preuve."
    return {
        "source": source,
        "point_type": point_type,
        "point": point or "Point a qualifier",
        "point_id": point_id,
        "piece": piece or "Piece attendue",
        "status": status or "a_verifier",
        "priority": priority or "P2",
        "tone": _workshop_tone(status, priority, has_local_proof),
        "action": action or "Verifier la piece et son rattachement.",
        "next_step": primary_action,
        "primary_action": primary_action,
        "proof_ref": proof_ref,
        "proof_badge": "preuve locale" if has_local_proof else "preuve manquante",
        "privacy_badge": privacy_badge,
        "confidence_badge": confidence_badge,
        "signature_badge": signature_badge,
        "request_id": request_id,
        "href": href,
        "has_local_proof": has_local_proof,
        "requires_action": requires_action,
    }


def _piece_workshop_rank(item: dict[str, object]) -> tuple[int, int, str]:
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "OK": 9}
    status_rank = {
        "ABSENT": 0,
        "MISSING": 0,
        "A_DEMANDER": 0,
        "PREUVE_A_DEMANDER": 0,
        "EN_ATTENTE_PREUVE": 0,
        "OBSOLETE": 1,
        "A_CLASSER": 2,
        "A_VERIFIER_CLASSEMENT": 2,
        "PREUVE_LOCALE_A_VERIFIER": 2,
        "EN_COURS": 3,
        "PRESENT": 8,
        "OK": 9,
    }
    priority = str(item.get("priority", "P2")).upper()
    status = str(item.get("status", "")).upper()
    piece = str(item.get("piece", "")).lower()
    return (priority_rank.get(priority, 2), status_rank.get(status, 4), piece)


def _piece_workshop_model(
    documents: dict[str, object],
    decisions: dict[str, object],
    incidents: dict[str, object],
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    documents_table = documents.get("documents")
    documents_by_id = (
        {
            row.get("doc_id", ""): row
            for row in documents_table.rows
            if isinstance(row, dict) and row.get("doc_id")
        }
        if isinstance(documents_table, DataTable)
        else {}
    )
    actionable = documents.get("actionable") if isinstance(documents.get("actionable"), dict) else {}
    matrix = actionable.get("matrix") if isinstance(actionable, dict) else None
    requests = actionable.get("to_request") if isinstance(actionable, dict) else []
    request_by_ref = {
        row.get("source_ref", ""): row
        for row in requests
        if isinstance(row, dict) and row.get("source_ref")
    }
    if isinstance(matrix, DataTable):
        for row in matrix.rows:
            proof_id = row.get("proof_id", "")
            request = request_by_ref.get(proof_id, {})
            status = request.get("status") or row.get("status", "")
            action = request.get("suggested_diligence") or row.get("action", "")
            proof_ref = _first_value(row, "evidence_paths", "matched_doc_ids")
            next_step = action
            if status == "PRESENT":
                next_step = "Rattacher cette preuve aux points ou actions qui la citent."
            elif proof_ref:
                next_step = "Verifier la piece locale puis confirmer son rattachement."
            document_row = _first_document_for_piece(documents_by_id, proof_ref)
            piece = row.get("expected_label") or row.get("document_type") or proof_id
            items.append(
                _piece_workshop_item(
                    source="DocOps",
                    point_type="Lot documentaire",
                    point=row.get("lot", ""),
                    point_id=proof_id,
                    piece=piece,
                    status=status,
                    priority=request.get("priority") or row.get("criticality", "P2"),
                    action=action,
                    next_step=next_step,
                    proof_ref=proof_ref,
                    request_id=request.get("request_id", ""),
                    href="/documents",
                    privacy_badge=document_row.get("privacy_review_status", ""),
                    confidence_badge=document_row.get("policy_confidence")
                    or document_row.get("classification_status", ""),
                    signature_badge=_piece_signature_badge(piece, document_row),
                )
            )

    decision_rows = decisions.get("open_rows")
    if isinstance(decision_rows, list):
        for row in decision_rows:
            if not isinstance(row, dict):
                continue
            point = " - ".join(
                part for part in [row.get("resolution_ref", ""), _clip(row.get("decision_text", ""), 120)] if part
            )
            status = row.get("statut", "")
            proof_ref = row.get("proof_doc_ids", "")
            next_step = row.get("action_attendue", "")
            if row.get("proof_doc_ids"):
                next_step = "Verifier la preuve locale et valider le suivi de decision."
            document_row = _first_document_for_piece(documents_by_id, proof_ref)
            piece = row.get("preuve_attendue") or row.get("proof_document_types") or "Preuve de decision"
            items.append(
                _piece_workshop_item(
                    source="DecisionOps",
                    point_type="Decision AG",
                    point=point,
                    point_id=row.get("decision_action_id", ""),
                    piece=piece,
                    status=status,
                    priority=row.get("priorite", "P2"),
                    action=row.get("action_attendue", ""),
                    next_step=next_step,
                    proof_ref=proof_ref,
                    href="/chantiers",
                    privacy_badge=document_row.get("privacy_review_status", ""),
                    confidence_badge=document_row.get("policy_confidence")
                    or document_row.get("classification_status", ""),
                    signature_badge=_piece_signature_badge(piece, document_row),
                )
            )

    incident_rows = incidents.get("open_rows")
    if isinstance(incident_rows, list):
        for row in incident_rows:
            if not isinstance(row, dict):
                continue
            status = incidentops.normalize_status(row.get("status"))
            point_parts = [row.get("incident_id", ""), row.get("lieu", ""), _clip(row.get("description", ""), 110)]
            proof_ref = row.get("closure_proof_ref", "")
            document_row = _first_document_for_piece(documents_by_id, proof_ref)
            piece = row.get("expected_closure_proof") or "Preuve de cloture"
            items.append(
                _piece_workshop_item(
                    source="IncidentOps",
                    point_type="Incident",
                    point=" - ".join(part for part in point_parts if part),
                    point_id=row.get("incident_id", ""),
                    piece=piece,
                    status=status,
                    priority=row.get("priority", "P2"),
                    action=row.get("next_action", ""),
                    next_step=row.get("next_action", ""),
                    proof_ref=proof_ref,
                    href="/chantiers",
                    privacy_badge=document_row.get("privacy_review_status", ""),
                    confidence_badge=document_row.get("policy_confidence")
                    or document_row.get("classification_status", ""),
                    signature_badge=_piece_signature_badge(piece, document_row),
                )
            )

    sorted_items = sorted(items, key=_piece_workshop_rank)
    by_source = _action_counter(
        [{"source": str(item.get("source", ""))} for item in sorted_items],
        "source",
    )
    by_status = _action_counter(
        [{"status": str(item.get("status", ""))} for item in sorted_items],
        "status",
    )
    return {
        "items": sorted_items[:80],
        "to_request": [item for item in sorted_items if item.get("requires_action") and not item.get("has_local_proof")][:30],
        "to_verify": [item for item in sorted_items if item.get("requires_action") and item.get("has_local_proof")][:30],
        "summary": {
            "total": len(sorted_items),
            "needs_action": len([item for item in sorted_items if item.get("requires_action")]),
            "with_local_proof": len([item for item in sorted_items if item.get("has_local_proof")]),
            "without_local_proof": len([item for item in sorted_items if not item.get("has_local_proof")]),
            "docops": by_source.get("DocOps", 0),
            "decisions": by_source.get("DecisionOps", 0),
            "incidents": by_source.get("IncidentOps", 0),
            "by_source": by_source,
            "by_status": by_status,
        },
    }
