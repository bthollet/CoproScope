from __future__ import annotations

from ._runtime import *

MEMOIRE_CATEGORY_INFO: dict[str, dict[str, str]] = {
    "ag": {"label": "AG", "tone": "green", "icon": "users"},
    "travaux": {"label": "Travaux", "tone": "blue", "icon": "tools"},
    "sinistres": {"label": "Sinistres", "tone": "orange", "icon": "alert"},
    "contrats": {"label": "Contrats", "tone": "green", "icon": "file-check"},
    "syndic": {"label": "Syndic", "tone": "blue", "icon": "building"},
    "documents": {"label": "Documents", "tone": "gray", "icon": "folder"},
    "comptes": {"label": "Comptes", "tone": "blue", "icon": "chart"},
    "demandes": {"label": "Demandes", "tone": "blue", "icon": "message"},
    "contentieux": {"label": "Contentieux", "tone": "red", "icon": "scale"},
}


def _memoire_category_from_document(row: dict[str, str]) -> str:
    text = " ".join(
        [
            row.get("lot", ""),
            row.get("document_type", ""),
            row.get("file_name", ""),
            row.get("notes", ""),
        ]
    ).lower()
    if any(word in text for word in ["contrat", "syndic", "fournisseur"]):
        return "contrats"
    if any(word in text for word in ["travaux", "devis", "chantier", "toiture"]):
        return "travaux"
    if any(word in text for word in ["ag", "pv", "convocation", "assemblee"]):
        return "ag"
    if any(word in text for word in ["compte", "budget", "facture", "comptable"]):
        return "comptes"
    if any(word in text for word in ["contentieux", "litige"]):
        return "contentieux"
    return "documents"


def _memoire_category_option(category_id: str) -> dict[str, str]:
    return MEMOIRE_CATEGORY_INFO.get(category_id, MEMOIRE_CATEGORY_INFO["documents"])


def _memoire_event_status(status: str, *, has_missing_proof: bool = False) -> dict[str, str]:
    normalized = (status or "").upper()
    if normalized in {"OK", "TRAITE", "CLOTURE", "CLOS", "TERMINE", "MATCH"}:
        return {"status": "clos", "label": "Clos", "risk": "low"}
    if has_missing_proof or normalized in {"PREUVE_A_DEMANDER", "ABSENT", "A_DEMANDER"}:
        return {"status": "ouvert", "label": "Ouvert", "risk": "high"}
    if normalized in {"A_ARBITRER", "A_REVOIR", "PREUVE_LOCALE_A_VERIFIER", "CANDIDAT_AVANT_AG"}:
        return {"status": "a_confirmer", "label": "A confirmer", "risk": "medium"}
    return {"status": "ouvert" if normalized else "a_confirmer", "label": "A confirmer", "risk": "medium"}


def _memoire_safe_refs(*values: object) -> list[str]:
    refs: list[str] = []
    for value in values:
        if isinstance(value, list):
            candidates = [str(item or "") for item in value]
        else:
            candidates = _split_piece_refs(str(value or ""))
        for candidate in candidates:
            safe = _public_text(candidate, "")
            if safe and safe not in refs:
                refs.append(safe)
    return refs


def _memoire_filter_options(
    rows: list[dict[str, object]],
    field: str,
    *,
    labels: dict[str, str] | None = None,
    route_field: str | None = None,
) -> list[dict[str, object]]:
    counts = Counter(str(row.get(field, "") or "non renseigne") for row in rows)
    options: list[dict[str, object]] = []
    for value, count in sorted(counts.items(), key=lambda item: (item[0] == "non renseigne", item[0])):
        options.append(
            {
                "id": value,
                "label": (labels or {}).get(value, value),
                "count": count,
                "is_active": False,
                "href": _route_href("/chantiers", **{route_field or field: value}),
            }
        )
    return options


def _memoire_event_detail(event: dict[str, object]) -> dict[str, object]:
    if not event:
        return {}
    event_id = str(event.get("id") or "")
    document_refs = [str(ref) for ref in event.get("document_refs", []) if ref]
    action_refs = [str(ref) for ref in event.get("action_refs", []) if ref]
    decision_refs = [str(ref) for ref in event.get("decision_refs", []) if ref]
    can_export = bool(event.get("can_export"))
    event_status = _public_text(event.get("status"), "a_confirmer")
    proof_state = "verified" if event_status == "clos" and document_refs else "candidate" if document_refs else "missing"
    if event_status == "ouvert" and not document_refs:
        proof_state = "missing"
    documents = [
        {
            "id": ref,
            "label": ref,
            "type_label": "Document",
            "status_label": "Piece candidate a verifier" if proof_state != "verified" else "Preuve validee",
            "why_linked": "Explique ou documente cet evenement.",
            "href": _route_href("/documents", doc_id=ref),
            "diffusion_label": "Conseil syndical",
            "can_download": False,
            "blocked_reason": "Verifier la diffusion avant telechargement.",
        }
        for ref in document_refs[:6]
    ]
    missing_proofs = []
    if proof_state == "missing":
        missing_proofs.append(
            {
                "id": _stable_action_id("MISSING-EVT", 0, event_id, str(event.get("title", ""))),
                "label": "Preuve de cloture ou document explicatif",
                "why_needed": "Prouver ce qui s'est passe et ce qui reste a reprendre.",
                "request_href": _route_href("/actions", selected=action_refs[0] if action_refs else event_id, tab="relance"),
            }
        )
    return {
        "id": event_id,
        "title": _public_text(event.get("title"), "Evenement memoire"),
        "date_iso": _public_text(event.get("date_iso"), ""),
        "date_label": _public_text(event.get("date_label"), "Date a confirmer"),
        "category": _public_text(event.get("kind"), "memoire"),
        "category_label": _public_text(event.get("category_label"), "Memoire"),
        "status": event_status,
        "status_label": _public_text(event.get("status_label"), "A confirmer"),
        "summary": _public_text(event.get("subtitle"), "Evenement a relire."),
        "why_in_memory": "Sujet a reprendre tant qu'une action, une preuve ou une restriction reste ouverte.",
        "next_action": _public_text(event.get("next_action"), "Verifier le point et rattacher les preuves utiles."),
        "owner_label": "Conseil syndical",
        "proof_state": proof_state,
        "proof_state_label": _proof_state_label(proof_state),
        "documents": documents,
        "proofs": {
            "verified": documents if proof_state == "verified" else [],
            "candidates": documents if proof_state == "candidate" else [],
            "missing": missing_proofs,
        },
        "linked_actions": [
            {
                "id": ref,
                "label": "Action liee",
                "next_step": _public_text(event.get("next_action"), "Verifier la prochaine action."),
                "href": _route_href("/actions", selected=ref),
            }
            for ref in action_refs[:6]
        ],
        "linked_documents": [
            {"id": ref, "label": ref, "href": _route_href("/documents", doc_id=ref), "why_linked": "Piece rattachee a l'evenement."}
            for ref in document_refs[:6]
        ],
        "linked_decisions": [
            {"id": ref, "label": ref, "href": _route_href("/actions", selected=ref)}
            for ref in decision_refs[:6]
        ],
        "linked_requests": [],
        "passation_note": _public_text(event.get("passation_note"), "A conserver dans la memoire de passation."),
        "passation": {
            "include_in_handover": event_status != "clos" or proof_state != "missing",
            "note": _public_text(event.get("passation_note"), "A transmettre avec les limites de preuve et de diffusion."),
            "missing_for_handover": [item.get("label", "preuve attendue") for item in missing_proofs],
            "export_href": _route_href("/exports/passation", scope="event", selected=event_id),
        },
        "restriction": {
            "level": event.get("restriction_level", "conseil_syndical"),
            "label": event.get("restriction_label", "Diffusion a verifier"),
            "reason": "Verifier les pieces et ne partager que la preuve utile.",
            "review_href": _route_href("/confidentialite"),
        },
        "history": [
            {
                "date_label": event.get("date_label", "Date a confirmer"),
                "label": "Evenement projete depuis les donnees locales.",
                "detail": "Projection derivee des actions, documents ou incidents disponibles.",
            }
        ],
        "actions": {
            "primary": {"label": "Ouvrir les documents", "href": _route_href("/documents")},
            "secondary": [
                {"label": "Voir l'action liee", "href": _route_href("/actions", selected=action_refs[0])}
                if action_refs
                else {"label": "Voir les actions", "href": _route_href("/actions")}
            ],
            "export": {
                "label": "Exporter cette fiche",
                "href": _route_href("/exports/passation.txt", scope="event", selected=event_id),
                "requires_preview": True,
                "disabled": not can_export,
                "disabled_reason": "" if can_export else "Diffusion a verifier avant export.",
            },
        },
    }
