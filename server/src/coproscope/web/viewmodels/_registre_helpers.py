from __future__ import annotations

from ._runtime import *

def _date_from_text(value: object) -> str:
    text = str(value or "")
    match = re.search(r"\b(20\d{2})[-_/]?([01]\d)[-_/]?([0-3]\d)\b", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    match = re.search(r"\b([0-3]\d)[-/]([01]\d)[-/](20\d{2})\b", text)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    return ""


def _ag_date(row: dict[str, str]) -> str:
    return _date_from_text(" ".join([row.get("ag_id", ""), row.get("source_file", ""), row.get("decision_text", "")]))


def _ag_label(ag_id: str, ag_date: str) -> str:
    if ag_date:
        return f"AG du {_date_label(ag_date)}"
    cleaned = _public_text((ag_id or "").replace("-", " "), "AG a renseigner")
    return cleaned if cleaned.upper().startswith("AG") else f"AG {cleaned}"


def _decision_status(statut: str, has_proof: bool) -> dict[str, str]:
    normalized = (statut or "").upper()
    if normalized in {"OK", "TRAITE", "CLOTURE", "CLOS", "TERMINE"}:
        return {
            "status": "clos",
            "label": "Terminee",
            "detail": "La decision dispose d'une trace de cloture.",
            "tone": "ok",
        }
    if normalized == "PREUVE_LOCALE_A_VERIFIER" or has_proof:
        return {
            "status": "a_verifier",
            "label": "Preuve a verifier",
            "detail": "Une piece locale existe, mais le conseil syndical doit confirmer ce qu'elle prouve.",
            "tone": "warn",
        }
    if normalized == "CANDIDAT_AVANT_AG":
        return {
            "status": "a_confirmer",
            "label": "Vote a confirmer",
            "detail": "La resolution vient d'une preparation ou convocation; le PV doit confirmer le vote.",
            "tone": "warn",
        }
    if normalized == "PREUVE_A_DEMANDER":
        return {
            "status": "a_demander",
            "label": "Preuve a demander",
            "detail": "La decision est suivie, mais la preuve d'execution manque encore.",
            "tone": "danger",
        }
    return {
        "status": "a_traiter",
        "label": _public_text(statut, "Action en cours"),
        "detail": "Le point demande une mise a jour lisible par le conseil syndical.",
        "tone": "info",
    }


def _proof_state(statut: str, proof_refs: list[str]) -> str:
    normalized = (statut or "").upper()
    if normalized in {"OK", "TRAITE", "CLOTURE", "CLOS", "TERMINE"}:
        return "verified"
    if normalized in {"BLOQUE", "A_REVOIR"}:
        return "blocked"
    if proof_refs:
        return "candidate"
    return "missing"


def _proof_state_label(state: str) -> str:
    return {
        "missing": "Preuve manquante",
        "candidate": "Preuve candidate",
        "verified": "Preuve validee",
        "rejected": "Preuve refusee",
        "blocked": "Verification bloquee",
    }.get(state, "Preuve a qualifier")


def _priority_label(priority: str) -> str:
    return {
        "P0": "Urgent",
        "P1": "A traiter maintenant",
        "P2": "A confirmer",
        "P3": "Suivi courant",
        "OK": "Cloturee",
    }.get((priority or "").upper(), _public_text(priority, "A confirmer"))


def _priority_reason(row: dict[str, str], proof_state: str) -> str:
    if proof_state == "missing":
        return "preuve manquante"
    if row.get("related_work_refs"):
        return "travaux"
    if row.get("related_invoice_refs"):
        return "budget"
    if (row.get("priorite") or "").upper() in {"P0", "P1"}:
        return "delai ou impact important"
    return "suivi courant"


def _due_state(due_on: str, status: str) -> str:
    if status == "clos":
        return "done"
    parsed = _parse_iso_date(due_on)
    if not parsed:
        return "missing"
    return "late" if parsed < date.today() else "planned"


def _due_label(due_on: str, due_state: str) -> str:
    parsed = _parse_iso_date(due_on)
    if due_state == "done":
        return "Cloturee"
    if due_state == "missing" or not parsed:
        return "Echeance a fixer"
    if due_state == "late":
        days = max(1, (date.today() - parsed).days)
        return f"En retard depuis {days} jours"
    return f"Echeance {_date_label(due_on)}"


def _documents_by_id(documents: dict[str, object]) -> dict[str, dict[str, str]]:
    documents_table = documents.get("documents")
    if not isinstance(documents_table, DataTable):
        return {}
    return {
        row.get("doc_id", ""): row
        for row in documents_table.rows
        if isinstance(row, dict) and row.get("doc_id")
    }


def _document_label(doc_id: str, row: dict[str, str] | None = None, fallback: str = "Piece locale") -> str:
    source = row or {}
    return _public_text(
        source.get("display_name") or source.get("file_name") or source.get("title") or doc_id,
        fallback,
    )


def _document_type_label(row: dict[str, str] | None, fallback: str = "Document") -> str:
    raw = (row or {}).get("document_type", "") or fallback
    return _public_text(raw.replace("_", " "), fallback)


def _diffusion_for_item(status: str, proof_state: str, pieces: list[dict[str, object]]) -> dict[str, object]:
    privacy_values = " ".join(str(piece.get("diffusion_label", "")) for piece in pieces).upper()
    if "BLOQUE" in privacy_values or "NE PAS DIFFUSER" in privacy_values:
        diffusion_status = "blocked"
    elif "BIFFER" in privacy_values or "ARBITRER" in privacy_values or proof_state in {"candidate", "blocked"}:
        diffusion_status = "after_redaction"
    elif status == "clos" and proof_state == "verified":
        diffusion_status = "copro_ok"
    else:
        diffusion_status = "cs_only"
    return {
        "status": diffusion_status,
        "label": {
            "local_only": "Prive local",
            "cs_only": "Conseil syndical seulement",
            "copro_ok": "Diffusion copro possible",
            "after_redaction": "A verifier avant partage",
            "blocked": "Export bloque",
        }.get(diffusion_status, "Conseil syndical seulement"),
        "reason": "Verifier les pieces et ne partager que la preuve utile.",
        "allowed_audience": "Conseil syndical" if diffusion_status != "copro_ok" else "Coproprietaires",
        "blocked_by": "verification diffusion" if diffusion_status in {"after_redaction", "blocked"} else "",
    }


def _piece_actions(doc_id: str, item_id: str) -> list[dict[str, str]]:
    return [
        {"id": "open", "label": "Ouvrir", "href": _route_href("/documents", doc_id=doc_id)},
        {"id": "attach-proof", "label": "Rattacher comme preuve", "href": _route_href("/actions", selected_item_id=item_id, tab="preuves")},
        {"id": "detach", "label": "Detacher", "href": _route_href("/actions", selected_item_id=item_id, tab="pieces")},
        {"id": "document-card", "label": "Voir la fiche document", "href": _route_href("/documents", doc_id=doc_id)},
        {"id": "redacted-copy", "label": "Preparer une version diffusable", "href": _route_href("/confidentialite", doc_id=doc_id)},
    ]


def _proof_card(
    *,
    item_id: str,
    proof_ref: str,
    label: str,
    type_label: str,
    status: str,
    source_doc_id: str = "",
    source_label: str = "",
    confirms: str = "execution",
) -> dict[str, object]:
    return {
        "proof_id": _public_text(proof_ref or _stable_action_id("PRV", 0, item_id, label), _stable_action_id("PRV", 0, item_id, label)),
        "label": _public_text(label, "Preuve attendue"),
        "type_label": _public_text(type_label, "Preuve"),
        "source_doc_id": _public_text(source_doc_id, ""),
        "source_label": _public_text(source_label or label, "A demander"),
        "captured_on": "",
        "verified_on": "",
        "status": status,
        "status_label": _proof_state_label(status),
        "confirms": confirms,
        "diffusion_label": "A verifier avant partage" if status != "verified" else "Diffusion possible apres controle",
        "restriction_reason": "" if status == "verified" else "Preuve non encore validee.",
        "href": _route_href("/actions", selected_item_id=item_id, tab="preuves"),
    }


def _piece_card(
    *,
    item_id: str,
    doc_id: str,
    label: str,
    type_label: str,
    role_label: str,
    proof_relation: str,
    doc_row: dict[str, str] | None = None,
) -> dict[str, object]:
    privacy = (doc_row or {}).get("privacy_status") or (doc_row or {}).get("privacy_review_status") or ""
    diffusion_label = {
        "DIFFUSABLE_BRUT": "Diffusion possible apres controle",
        "DIFFUSABLE_APRES_BIFFAGE": "A biffer avant partage",
        "A_BIFFER": "A biffer avant partage",
        "A_ARBITRER": "Diffusion a arbitrer",
        "BLOQUE": "Ne pas diffuser",
        "RESERVE_CS": "Conseil syndical seulement",
    }.get(privacy, "Diffusion a verifier")
    safe_doc_id = _public_text(doc_id, "")
    return {
        "doc_id": safe_doc_id,
        "label": _public_text(label, "Piece locale"),
        "type_label": _public_text(type_label, "Document"),
        "added_on": "",
        "role_label": _public_text(role_label, "annexe utile"),
        "proof_relation": proof_relation,
        "diffusion_label": diffusion_label,
        "href": _route_href("/documents", doc_id=safe_doc_id) if safe_doc_id else _route_href("/documents"),
        "download_href": _route_href("/documents", doc_id=safe_doc_id) if safe_doc_id else _route_href("/documents"),
        "actions": _piece_actions(safe_doc_id, item_id) if safe_doc_id else [],
    }


def _followup_card(
    *,
    item_id: str,
    row: dict[str, str],
    proof_expected: str,
    status: str,
    followup_id: str = "",
) -> dict[str, object]:
    resolution = _public_text(row.get("resolution_ref"), "cette decision")
    title = _public_text(row.get("decision_text"), "decision AG")
    expected = _public_text(proof_expected, "preuve attendue")
    copy_text = (
        f"Bonjour, pouvez-vous nous transmettre ou confirmer la preuve attendue pour {resolution} "
        f"({title}) : {expected} ? Merci d'indiquer la piece, la date et le contexte de la reponse."
    )
    return {
        "followup_id": _public_text(followup_id or _stable_action_id("REL", 0, item_id, expected), _stable_action_id("REL", 0, item_id, expected)),
        "label": "Preparer une relance syndic" if status in {"draft", "to_send"} else "Relance syndic a suivre",
        "status": status,
        "status_label": {
            "draft": "Brouillon a copier",
            "to_send": "A envoyer hors CoproScope",
            "sent_waiting": "Envoyee hors CoproScope, reponse attendue",
            "answered_to_check": "Reponse a verifier",
            "closed": "Relance close",
        }.get(status, "Relance a qualifier"),
        "sent_on": "",
        "channel_label": "Hors CoproScope, canal a noter",
        "recipient_label": _public_text(row.get("responsable"), "Syndic"),
        "message_excerpt": _clip(copy_text, 130),
        "expected_answer": expected,
        "answer_summary": "",
        "related_request_id": _public_text(row.get("related_request_ids"), ""),
        "copy_text": _public_text(copy_text, "Message de relance a preparer."),
        "href": _route_href("/actions", selected_item_id=item_id, tab="relance"),
    }


def _history_event(
    *,
    item_id: str,
    occurred_on: str,
    event_type: str,
    type_label: str,
    summary: str,
    actor_label: str = "CoproScope local",
    proof_ids: list[str] | None = None,
    piece_ids: list[str] | None = None,
    followup_ids: list[str] | None = None,
    is_evidence: bool = False,
    memory_note: str = "",
) -> dict[str, object]:
    event_id = _stable_action_id("EVT", 0, item_id, occurred_on, event_type, summary)
    return {
        "event_id": event_id,
        "occurred_on": occurred_on,
        "type": event_type,
        "type_label": type_label,
        "actor_label": actor_label,
        "summary": _public_text(summary, "Trace de suivi"),
        "proof_ids": proof_ids or [],
        "piece_ids": piece_ids or [],
        "followup_ids": followup_ids or [],
        "is_evidence": is_evidence,
        "memory_note": _public_text(memory_note, "A conserver pour la passation."),
    }
