from __future__ import annotations

from ._runtime import *

COMPTES_CATEGORY_INFO: dict[str, dict[str, str]] = {
    "entretien_maintenance": {
        "label": "Entretien & maintenance",
        "icon": "tool",
        "account_family_label": "Entretien, maintenance et espaces communs",
    },
    "energie_fluides": {
        "label": "Energie & fluides",
        "icon": "drop",
        "account_family_label": "Eau, energie et fluides",
    },
    "prestations_service": {
        "label": "Prestations de service",
        "icon": "service",
        "account_family_label": "Prestataires et services courants",
    },
    "assurances": {
        "label": "Assurances",
        "icon": "shield",
        "account_family_label": "Assurances",
    },
    "taxes_impots": {
        "label": "Taxes & impots",
        "icon": "tax",
        "account_family_label": "Taxes et impots",
    },
    "honoraires": {
        "label": "Honoraires & honoraires tiers",
        "icon": "scale",
        "account_family_label": "Syndic, avocat, expert et comptable",
    },
    "controles_prioritaires": {
        "label": "Controles prioritaires",
        "icon": "alert",
        "account_family_label": "Controles comptables a justifier",
    },
    "autres_charges": {
        "label": "Autres charges",
        "icon": "box",
        "account_family_label": "Autres charges a qualifier",
    },
}

COMPTES_STATUS_LABELS = {
    "p1": "A traiter",
    "p2": "A confirmer",
    "ok": "Conforme avec preuve",
    "missing": "Piece a demander",
    "unknown": "A qualifier",
    "empty": "Aucun controle charge",
}

COMPTES_STATUS_TONES = {
    "p1": "danger",
    "p2": "warn",
    "ok": "ok",
    "missing": "warn",
    "unknown": "info",
    "empty": "info",
}


def _comptes_amount(value: object) -> float | None:
    return _amount_value(value)


def _comptes_amount_label(value: object, fallback: str = "Montant non charge") -> str:
    return _amount_label(value, fallback)


def _comptes_ratio_label(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "A calculer"
    return f"{round(100 * numerator / denominator)}%"


def _comptes_ratio_value(numerator: int, denominator: int) -> int:
    return round(100 * numerator / denominator) if denominator > 0 else 0


def _comptes_slug(value: object) -> str:
    normalized = str(value or "").strip().lower().replace("&", " et ")
    normalized = normalized.replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")
    normalized = normalized.replace("ç", "c").replace("î", "i").replace("ï", "i").replace("ô", "o")
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")


def _comptes_category_info(category_id: str) -> dict[str, str]:
    return COMPTES_CATEGORY_INFO.get(category_id, COMPTES_CATEGORY_INFO["autres_charges"])


def _comptes_category_id(row: dict[str, str]) -> str:
    explicit = _comptes_slug(
        _first_value(
            row,
            "famille_charge",
            "account_family",
            "account_family_label",
            "categorie",
            "category",
        )
    )
    aliases = {
        "entretien": "entretien_maintenance",
        "entretien_maintenance": "entretien_maintenance",
        "maintenance": "entretien_maintenance",
        "energie": "energie_fluides",
        "energie_fluides": "energie_fluides",
        "fluides": "energie_fluides",
        "prestations": "prestations_service",
        "prestations_service": "prestations_service",
        "services": "prestations_service",
        "assurance": "assurances",
        "assurances": "assurances",
        "taxes": "taxes_impots",
        "taxes_impots": "taxes_impots",
        "impots": "taxes_impots",
        "honoraires": "honoraires",
        "honoraire": "honoraires",
    }
    if explicit in aliases:
        return aliases[explicit]
    if explicit in COMPTES_CATEGORY_INFO:
        return explicit

    account = _first_value(row, "compte_propose", "compte_candidate", "account", "compte_debit")
    if account.startswith("615"):
        return "entretien_maintenance"
    if account.startswith("606"):
        return "energie_fluides"
    if account.startswith("616"):
        return "assurances"
    if account.startswith(("621", "622", "623")):
        return "honoraires"
    if account.startswith(("63", "635")):
        return "taxes_impots"

    haystack = " ".join(
        _first_value(row, field)
        for field in [
            "fournisseur",
            "supplier",
            "supplier_hint",
            "statement_label",
            "account_label",
            "label",
            "libelle_depense",
            "control",
            "evidence",
            "anomaly",
            "anomalies",
            "anomalies_facture",
            "justification",
            "match_reason",
            "motif",
            "next_action",
            "action",
        ]
    ).lower()
    if any(word in haystack for word in ["entretien", "maintenance", "jardin", "espaces verts", "travaux"]):
        return "entretien_maintenance"
    if any(word in haystack for word in ["eau", "electricite", "energie", "gaz", "fluide", "chauffage"]):
        return "energie_fluides"
    if any(word in haystack for word in ["assurance", "multirisque"]):
        return "assurances"
    if any(word in haystack for word in ["taxe", "impot", "foncier"]):
        return "taxes_impots"
    if any(word in haystack for word in ["honoraire", "syndic", "avocat", "expert", "comptable"]):
        return "honoraires"
    if any(word in haystack for word in ["service", "nettoyage", "gardien", "prestation"]):
        return "prestations_service"
    if _first_value(row, "control", "severity", "status"):
        return "controles_prioritaires"
    return "autres_charges"


def _comptes_priority(value: object, default: str = "P2") -> str:
    priority = str(value or default).strip().upper()
    if priority in {"P0", "P1"}:
        return "P1"
    if priority == "OK":
        return "OK"
    if priority == "INFO":
        return "info"
    return "P2"


def _comptes_priority_label(priority: object) -> str:
    normalized = _comptes_priority(priority, "P2")
    return {
        "P1": "A traiter",
        "P2": "A confirmer",
        "OK": "Conforme avec preuve",
        "info": "Information",
    }.get(normalized, "A confirmer")


def _comptes_tone_from_priority(priority: object) -> str:
    return {
        "P1": "danger",
        "P2": "warn",
        "OK": "ok",
        "info": "info",
    }.get(_comptes_priority(priority, "P2"), "warn")


def _comptes_match_state(row: dict[str, str]) -> str:
    status = _first_value(row, "match_status", "statut_rapprochement", "status").upper()
    priority = _comptes_priority(_first_value(row, "match_priority", "priorite"), "")
    if priority == "OK" or status in {"OK", "MATCH", "RAPPROCHE"} or status.startswith("MATCH"):
        return "matched"
    if "AMBIG" in status or "CANDIDAT" in status:
        return "ambiguous"
    if "SANS_ETAT" in status or "ETAT_DEPENSES" in status:
        return "missing_statement"
    if "MONTANT" in status or "ECART" in status:
        return "amount_to_check"
    if "FOURNISSEUR" in status or "ALIAS" in status:
        return "supplier_to_check"
    if "NON" in status or "ABSENT" in status or "MISSING" in status:
        return "not_matched"
    return "to_check"


def _comptes_match_state_label(match_state: str) -> str:
    return {
        "matched": "Facture rapprochee",
        "ambiguous": "Rapprochement candidat a confirmer",
        "missing_statement": "Etat des depenses a demander",
        "amount_to_check": "Montant a verifier",
        "supplier_to_check": "Fournisseur a confirmer",
        "not_matched": "Rapprochement manquant",
        "to_check": "A verifier",
    }.get(match_state, "A verifier")


def _comptes_proof_state(row: dict[str, str], priority: str) -> str:
    match_state = _comptes_match_state(row)
    if priority == "OK" or match_state == "matched":
        return "verified"
    if priority == "P1" or match_state in {"not_matched", "missing_statement"}:
        return "missing"
    if match_state in {"ambiguous", "amount_to_check", "supplier_to_check", "to_check"}:
        return "candidate"
    return "candidate"


def _comptes_proof_state_label(proof_state: str) -> str:
    return {
        "missing": "Piece ou preuve a demander",
        "candidate": "Preuve candidate a confirmer",
        "verified": "Preuve rattachee",
        "rejected": "Preuve refusee",
        "not_needed": "Aucune preuve supplementaire",
    }.get(proof_state, "Preuve a verifier")


def _comptes_alert_type(row: dict[str, str]) -> str:
    text = " ".join(str(value or "") for value in row.values()).lower()
    if "bon de commande" in text or "decision" in text:
        return "missing_order"
    if "piece jointe" in text or "justificatif" in text or "piece attendue" in text:
        return "missing_attachment"
    if "period" in text or "periodicite" in text:
        return "period_gap"
    if "montant" in text or "ecart" in text:
        return "amount_gap"
    if "fournisseur" in text or "alias" in text:
        return "supplier_gap"
    if "ambigu" in text or "candidate" in text:
        return "ambiguous_match"
    if "non" in text or "rapproch" in text or "etat des depenses" in text:
        return "non_match"
    return "unknown"


def _comptes_alert_type_label(alert_type: str) -> str:
    return {
        "missing_order": "Decision ou bon de commande a justifier",
        "missing_attachment": "Justificatif manquant",
        "period_gap": "Periodicite a verifier",
        "non_match": "Facture non rapprochee",
        "ambiguous_match": "Rapprochement ambigu",
        "amount_gap": "Ecart de montant",
        "supplier_gap": "Fournisseur a confirmer",
        "unknown": "Controle a qualifier",
    }.get(alert_type, "Controle a qualifier")


def _comptes_expected_proof(row: dict[str, str], priority: str) -> str:
    explicit = _first_value(row, "expected_proof", "evidence", "preuve_attendue")
    if explicit:
        return _public_text(explicit, "Piece ou justification attendue.")
    match_state = _comptes_match_state(row)
    if match_state == "missing_statement":
        return "Etat des depenses ou grand livre de l'exercice."
    if priority == "P1":
        return "Piece, decision ou ligne de grand livre permettant de justifier le point."
    if priority == "P2":
        return "Confirmation du rattachement comptable ou justificatif complementaire."
    return "Facture et ligne de depense rapprochees."


def _comptes_next_action(row: dict[str, str], priority: str) -> str:
    explicit = _first_value(row, "next_action", "prochaine_action", "action")
    if explicit:
        return _public_text(explicit, "Verifier le point avec le syndic.")
    if priority == "P1":
        return "Demander la piece ou la justification au syndic."
    if priority == "P2":
        return "Confirmer le rattachement avec le syndic ou une piece."
    return "Conserver la preuve rattachee."


def _comptes_merge_invoice(row: dict[str, str], invoices_by_doc: dict[str, dict[str, str]]) -> dict[str, str]:
    doc_id = _first_value(row, "doc_id", "source_doc_id")
    merged = dict(invoices_by_doc.get(doc_id, {}))
    for key, value in row.items():
        if value:
            merged[key] = value
    return merged


def _comptes_piece_actions(piece_id: str, doc_id: str, category_id: str) -> list[dict[str, str]]:
    return [
        {"id": "ouvrir", "label": "Ouvrir", "href": _route_href("/comptes", categorie=category_id, piece=piece_id)},
        {
            "id": "fiche_document",
            "label": "Fiche document",
            "href": _route_href("/documents", doc_id=doc_id) if doc_id else _route_href("/documents"),
        },
        {
            "id": "rattacher_preuve",
            "label": "Rattacher comme preuve",
            "href": _route_href("/comptes", categorie=category_id, piece=piece_id, action="rattacher-preuve"),
        },
        {
            "id": "demander_syndic",
            "label": "Demander au syndic",
            "href": _route_href("/comptes", categorie=category_id, piece=piece_id, tab="questions"),
        },
        {
            "id": "ajouter_rapport_ag",
            "label": "Ajouter au rapport AG",
            "href": _route_href("/comptes", categorie=category_id, piece=piece_id, tab="rapport-ag"),
        },
    ]


def _comptes_piece_from_row(
    row: dict[str, str],
    *,
    category_id: str,
    index: int,
    source: str,
    priority: str,
) -> dict[str, object]:
    doc_id = _public_text(_first_value(row, "doc_id", "piece_doc_id", "source_doc_id"), "")
    supplier = _public_text(_first_value(row, "fournisseur", "supplier", "supplier_hint"), "Fournisseur non renseigne")
    invoice_ref_raw = _public_text(_first_value(row, "numero_facture", "invoice_ref", "reference", "statement_reference"), "")
    invoice_ref = invoice_ref_raw or "Facture sans reference"
    match_state = _comptes_match_state(row)
    proof_state = _comptes_proof_state(row, priority)
    piece_id = _stable_action_id("PCE-COMP", index, doc_id, invoice_ref, supplier, source)
    label = (
        f"Facture {invoice_ref} - {supplier}"
        if invoice_ref_raw
        else _first_value(row, "statement_label", "label", "account_label", "control")
        or f"Piece {doc_id or index}"
    )
    return {
        "piece_id": piece_id,
        "doc_id": doc_id,
        "category_id": category_id,
        "label": _public_text(label, "Piece comptable"),
        "type_label": "facture" if invoice_ref_raw else "ligne depense",
        "supplier_label": supplier,
        "invoice_ref": invoice_ref,
        "invoice_date_label": _date_label(_first_value(row, "date_facture", "invoice_date", "date"), "Date non lue"),
        "amount_label": _comptes_amount_label(_first_value(row, "ttc", "statement_amount", "montant_depense", "amount", "debit")),
        "period_label": _public_text(_first_value(row, "periode", "period_label"), "Exercice"),
        "match_status": match_state,
        "match_status_label": _comptes_match_state_label(match_state),
        "proof_state": proof_state,
        "proof_state_label": _comptes_proof_state_label(proof_state),
        "role_label": "preuve locale" if proof_state == "verified" else "piece a verifier",
        "related_alert_ids": [],
        "question_ids": [],
        "diffusion_label": "Conseil syndical",
        "restriction_reason": "Relecture requise avant diffusion AG" if proof_state != "verified" else "",
        "href": _route_href("/comptes", categorie=category_id, piece=piece_id),
        "actions": _comptes_piece_actions(piece_id, doc_id, category_id),
    }


def _comptes_question_from_row(
    row: dict[str, str],
    *,
    category_id: str,
    alert_id: str,
    piece_id: str,
    index: int,
    year: int,
    source: str,
) -> dict[str, object]:
    if source == "control":
        question = _question_from_control(row)
        subject = row.get("control") or "Controle comptable a justifier"
    elif source == "anomaly":
        question = _question_from_anomaly(row)
        subject = question.get("title") or row.get("anomaly") or "Anomalie facture a clarifier"
    else:
        question = _question_from_non_match(row)
        subject = question.get("title") or row.get("fournisseur") or "Rapprochement a confirmer"
    priority = _comptes_priority(question.get("priority") or _priority_for(row, "P2"), "P2")
    question_text = _public_text(question.get("question"), "Pouvez-vous transmettre la piece ou la confirmation attendue ?")
    question_id = _stable_action_id("Q-COMP", index, category_id, alert_id, piece_id, question_text)
    expected_proof = _comptes_expected_proof(row, priority)
    context_label = _public_text(
        " - ".join(
            part
            for part in [
                _comptes_category_info(category_id)["label"],
                _first_value(row, "fournisseur", "supplier", "supplier_hint"),
                _first_value(row, "numero_facture", "doc_id"),
            ]
            if part
        ),
        _comptes_category_info(category_id)["label"],
    )
    copy_text = "\n".join(
        [
            f"Controle comptes {year} - {context_label}",
            "",
            question_text,
            "",
            f"Preuve attendue: {expected_proof}",
        ]
    )
    return {
        "question_id": question_id,
        "category_id": category_id,
        "alert_ids": [alert_id] if alert_id else [],
        "piece_ids": [piece_id] if piece_id else [],
        "priority": priority,
        "priority_label": _comptes_priority_label(priority),
        "status": "draft",
        "status_label": "Brouillon a relire",
        "subject": _public_text(subject, "Question syndic"),
        "short_label": _clip(question_text, 90),
        "question_text": question_text,
        "copy_text": _public_text(copy_text, question_text),
        "context_label": context_label,
        "expected_answer": "Confirmation ecrite ou piece rattachee au point de controle.",
        "expected_proof": expected_proof,
        "recipient_label": "Syndic",
        "channel_label": "Copie manuelle, aucun envoi automatique",
        "last_sent_label": "Non envoyee depuis CoproScope",
        "answer_summary": "",
        "related_request_id": "",
        "include_in_ag_report": priority in {"P1", "P2"},
        "diffusion_label": "Conseil syndical, a relire avant AG",
        "href": _route_href("/comptes", categorie=category_id, tab="questions", question=question_id),
    }


def _comptes_alert_from_row(
    row: dict[str, str],
    *,
    category_id: str,
    piece_id: str,
    question_id: str,
    index: int,
    priority: str,
    source: str,
) -> dict[str, object]:
    alert_type = _comptes_alert_type(row)
    invoice_ref = _public_text(_first_value(row, "numero_facture", "doc_id"), "Piece concernee")
    alert_id = _stable_action_id("AL-COMP", index, category_id, piece_id, alert_type, source)
    explanation = _public_text(
        _first_value(row, "match_reason", "motif", "reason", "status_label", "libelle_statut", "anomaly", "evidence", "action"),
        "Ce point demande une verification humaine avant validation.",
    )
    return {
        "alert_id": alert_id,
        "category_id": category_id,
        "priority": priority,
        "priority_label": _comptes_priority_label(priority),
        "tone": _comptes_tone_from_priority(priority),
        "type": alert_type,
        "label": _comptes_alert_type_label(alert_type),
        "count": 1,
        "explanation": explanation,
        "affected_piece_ids": [piece_id] if piece_id else [],
        "affected_invoice_refs": [invoice_ref] if invoice_ref else [],
        "expected_proof": _comptes_expected_proof(row, priority),
        "suggested_question_id": question_id,
        "next_action_label": _comptes_next_action(row, priority),
        "status": "question_ready" if question_id else "open",
        "href": _route_href("/comptes", categorie=category_id, alert=alert_id),
    }
