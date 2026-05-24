from __future__ import annotations

from typing import Any

from ..core.common import InstanceConfig
from ..modules import requestops
from .requests_view import build_requests_view


def build_relance_syndic_view(
    instance: InstanceConfig,
    year: int = 2025,
    *,
    request_id: str = "",
    action_id: str = "",
    piece_id: str = "",
    piece_detail: str = "",
    sent: str = "",
    sent_id: str = "",
    dashboard_model: dict[str, object] | None = None,
) -> dict[str, Any]:
    requests = build_requests_view(instance, year)
    rows = _candidate_rows(requests.get("open_rows", []) or requests.get("rows", []))
    piece_row = _piece_context_row(instance, year, piece_detail or piece_id, dashboard_model=dashboard_model)
    selected = piece_row or _select_row(rows, request_id=request_id, action_id=action_id)
    linked_docs = _linked_documents(selected)
    subject = _safe(selected.get("subject"), "Demande au syndic")
    expected = _expected_label(selected)
    draft = _draft_message(subject=subject, expected=expected, selected=selected)
    latest_relance = _latest_relance_action(selected, sent_id=sent_id)
    sent_valid = bool(sent and request_id and latest_relance)
    return {
        "context": {
            "title": "Relancer le syndic",
            "subtitle": "Une reponse ou une piece manque pour terminer cette action.",
            "role_label": "Conseil syndical",
            "demo_label": "Mode local: aucun message n'est envoye par CoproScope",
        },
        "summary": {
            "total": len(rows),
            "selected_status": selected.get("status_label", "a verifier"),
            "delivery_status": "Brouillon non envoye par CoproScope",
            "sent": sent_valid,
            "sent_label": "Relance enregistree localement" if sent_valid else "",
            "sent_details": _safe(latest_relance.get("summary"), "") if sent_valid else "",
            "contextualized": bool(piece_row),
        },
        "selected": selected,
        "cards": [
            {
                "title": "Pourquoi on relance",
                "body": _why_label(selected),
            },
            {
                "title": "Ce qu'on attend",
                "body": expected,
            },
            {
                "title": "Ne pas joindre sans verifier",
                "body": _diffusion_guard(selected),
            },
        ],
        "draft": draft,
        "linked_docs": linked_docs,
        "actions": {
            "back_href": "/actions",
            "requests_href": "/demandes",
            "pieces_href": "/pieces?proof=missing",
            "depot_href": _depot_href(selected),
            "piece_href": selected.get("piece_href", ""),
        },
        "rows": rows,
        "empty_state": {
            "is_visible": not bool(selected),
            "title": "Aucune relance syndic a preparer",
            "body": "Les demandes ouvertes restent lisibles dans la boite de demandes.",
        },
    }


def _piece_context_row(
    instance: InstanceConfig,
    year: int,
    piece_ref: str,
    *,
    dashboard_model: dict[str, object] | None = None,
) -> dict[str, Any]:
    if not piece_ref:
        return {}
    from .piece_detail_view import build_piece_detail

    detail = build_piece_detail(instance, year, piece_ref, dashboard_model=dashboard_model)
    if detail.get("state") != "found":
        return {}
    piece = detail.get("piece") if isinstance(detail.get("piece"), dict) else {}
    proof = detail.get("proof") if isinstance(detail.get("proof"), dict) else {}
    linked = detail.get("linked") if isinstance(detail.get("linked"), dict) else {}
    diffusion = detail.get("diffusion") if isinstance(detail.get("diffusion"), dict) else {}
    action = linked.get("action") if isinstance(linked.get("action"), dict) else {}
    request = linked.get("request") if isinstance(linked.get("request"), dict) else {}
    deposit = linked.get("deposit") if isinstance(linked.get("deposit"), dict) else {}
    piece_id = _safe(piece.get("id"), piece_ref)
    return {
        "request_id": "",
        "subject": _safe(piece.get("label"), "Piece a demander"),
        "summary": _safe(piece.get("why_it_matters"), "Piece attendue pour prouver le point rattache."),
        "status": "a_demander",
        "status_label": _safe(piece.get("status_label"), "Piece ou preuve a demander"),
        "received_label": "depuis la fiche piece",
        "proof_label": _safe(proof.get("expected_label"), "Preuve attendue a preciser"),
        "source_label": piece_id,
        "next_action_label": _safe(piece.get("next_step"), "Demander la preuve au syndic."),
        "related_label": _safe(action.get("label"), "Point lie"),
        "related_action_id": piece_id,
        "visibility_label": _safe(diffusion.get("label"), "Diffusion a verifier"),
        "diffusion_warning": _safe(diffusion.get("detail"), "Ne pas joindre sans arbitrage de diffusion."),
        "holder_label": _safe(piece.get("holder_label"), "Syndic ou conseil syndical"),
        "piece_href": f"/pieces/{piece_id}",
        "request_href": _safe(request.get("href"), ""),
        "depot_href": _safe(deposit.get("href"), f"/depot?intent=syndic-answer&piece_detail={piece_id}&return=relance"),
        "journal": [],
        "journal_count": 0,
        "latest_action_label": "aucune relance enregistree",
    }


def _candidate_rows(rows: object) -> list[dict[str, Any]]:
    candidates = [dict(row) for row in rows if isinstance(row, dict)]
    if not candidates:
        return []
    priority = {"relance": 0, "nouvelle": 1, "a_qualifier": 2, "en_attente": 3, "en_cours": 4}
    candidates.sort(key=lambda row: (priority.get(str(row.get("status") or ""), 5), str(row.get("received_at") or "")))
    return candidates


def _select_row(rows: list[dict[str, Any]], *, request_id: str, action_id: str) -> dict[str, Any]:
    for row in rows:
        if request_id and row.get("request_id") == request_id:
            return row
        if action_id and row.get("related_action_id") == action_id:
            return row
    return rows[0] if rows else {}


def _linked_documents(row: dict[str, Any]) -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    for key in ["proof_ref", "source_ref", "proof_label", "source_label", "origin_id"]:
        value = _safe(row.get(key), "")
        if value.startswith("DOC-") and value not in [item["id"] for item in docs]:
            docs.append({"id": value, "label": value, "href": f"/documents/{value}"})
    return docs


def _latest_relance_action(row: dict[str, Any], *, sent_id: str = "") -> dict[str, Any]:
    journal = row.get("journal") if isinstance(row.get("journal"), list) else []
    if sent_id:
        for action in journal:
            if isinstance(action, dict) and action.get("journal_id") == sent_id:
                return action
    for action in reversed(journal):
        if not isinstance(action, dict):
            continue
        if action.get("action_type") == "relance" or action.get("action_type_label") == "relance":
            return action
    return {}


def _expected_label(row: dict[str, Any]) -> str:
    proof = _safe(row.get("proof_label"), "")
    source = _safe(row.get("source_label"), "")
    if proof and proof != "preuve a rattacher":
        return proof
    if source and source != "source a noter":
        return source
    return "Une reponse ecrite du syndic ou une piece rattachee a la demande."


def _why_label(row: dict[str, Any]) -> str:
    status = _safe(row.get("status_label"), "a verifier")
    next_action = _safe(row.get("next_action_label"), "")
    if next_action:
        return f"La demande est {status}; prochaine action: {next_action}"
    return f"La demande est {status}; il faut clarifier la piece attendue avant de clore."


def _draft_message(*, subject: str, expected: str, selected: dict[str, Any]) -> dict[str, str]:
    request_id = _safe(selected.get("request_id"), "")
    next_action = _safe(selected.get("next_action_label"), "Merci de nous transmettre la piece attendue.")
    body = (
        "Bonjour,\n\n"
        f"Nous revenons vers vous au sujet de: {subject}.\n\n"
        f"Ce que nous attendons: {expected}.\n"
        f"Suite souhaitee: {next_action}\n\n"
        "Pouvez-vous nous confirmer la date de transmission, la source de la piece et le contexte de votre reponse ?\n\n"
        "Merci."
    )
    return {
        "request_id": request_id,
        "recipient": _safe(selected.get("holder_label"), "Syndic de la copropriete"),
        "subject": f"Relance - {subject}",
        "body": body,
        "deadline": "Sous 7 jours",
        "proof_expected": expected,
        "can_mark_sent": bool(request_id),
    }


def _diffusion_guard(selected: dict[str, Any]) -> str:
    warning = _safe(selected.get("diffusion_warning"), "")
    if warning:
        return warning
    return "Ne joignez pas de document restreint sans arbitrage de diffusion. La reponse recue restera candidate jusqu'a verification."


def _depot_href(selected: dict[str, Any]) -> str:
    href = _safe(selected.get("depot_href"), "")
    if href:
        return href
    request_id = _safe(selected.get("request_id"), "")
    return f"/depot?intent=syndic-answer&request_id={request_id}" if request_id else "/depot?intent=syndic-answer&return=relance"


def _safe(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    return requestops._privacy_safe_text(text)  # type: ignore[attr-defined]
