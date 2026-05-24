from __future__ import annotations

from ._runtime import *

def _priority_late_action_item(action: dict[str, str], index: int) -> dict[str, object]:
    item_id = _public_text(action.get("id"), _stable_action_id("ACT", index, action.get("title", ""), action.get("source", "")))
    priority = _public_text(action.get("priority"), "P2")
    status = _public_text(action.get("status"), "a_traiter")
    expected_proof = _public_text(action.get("evidence"), "Preuve attendue a preciser")
    next_step = _public_text(action.get("next_step"), "Verifier le point et noter la prochaine action.")
    domain_label = _public_text(action.get("domain_label"), "Suivi CS")
    return {
        "id": item_id,
        "title": _public_text(action.get("title"), "Action a traiter"),
        "domain_label": domain_label,
        "priority": priority,
        "priority_label": _priority_label(priority),
        "status": status,
        "status_label": _ux_status_label(status),
        "due_date": "",
        "delay_label": "En retard ou prioritaire" if priority in {"P0", "P1"} else "A reprendre",
        "owner": _public_text(action.get("owner"), "Conseil syndical"),
        "expected_proof": expected_proof,
        "next_step": next_step,
        "href": _action_selected_href(item_id),
        "followup_href": _route_href("/demandes/relance", action_id=item_id),
        "piece_href": _route_href("/pieces", missing_for=item_id),
        "memory_href": _public_href(action.get("href"), _route_href("/chantiers")),
        "diffusion_label": "Conseil syndical",
        "can_close": status == "clos",
    }


def _missing_piece_view_item(item: dict[str, object], index: int) -> dict[str, object]:
    piece = _public_text(item.get("piece"), "Piece attendue")
    point_id = _public_text(item.get("point_id"), _stable_action_id("POINT", index, piece))
    proof_ref = _public_text(item.get("proof_ref"), "")
    status = "candidate" if proof_ref else "a_demander"
    return {
        "id": _stable_action_id("MISSING-PIECE", index, point_id, piece),
        "expected_piece": piece,
        "rubric_label": _public_text(item.get("point_type"), "Piece"),
        "reason": _public_text(item.get("action") or item.get("next_step"), "Necessaire pour avancer sans conclure sans preuve."),
        "proof_purpose": "Prouver ou confirmer le point rattache avant passation.",
        "criticality": _public_text(item.get("priority"), "P2"),
        "criticality_label": _priority_label(str(item.get("priority") or "P2")),
        "status": status,
        "status_label": "Piece candidate a verifier" if proof_ref else "A demander",
        "source_label": _public_text(item.get("source"), "Source a confirmer"),
        "related_action_id": point_id,
        "related_event_id": point_id,
        "request_href": _route_href("/demandes/relance", action_id=point_id),
        "deposit_href": _route_href("/depot", intent="proof", missing_for=point_id),
        "candidate_docs": [
            {
                "id": proof_ref,
                "label": proof_ref,
                "status_label": "Piece candidate a verifier",
                "href": _route_href("/documents", doc_id=proof_ref),
            }
        ]
        if proof_ref
        else [],
        "diffusion_label": "Conseil syndical",
        "next_step": _public_text(item.get("next_step"), "Demander ou rattacher la piece attendue."),
    }


def _ux_piece_status(item: dict[str, object]) -> str:
    status = str(item.get("status") or "").upper()
    has_local_proof = bool(item.get("has_local_proof"))
    requires_action = bool(item.get("requires_action", True))
    if has_local_proof and requires_action:
        return "a_verifier"
    if has_local_proof:
        return "rattachee"
    if status in {"ABSENT", "MISSING", "A_DEMANDER", "PREUVE_A_DEMANDER", "EN_ATTENTE_PREUVE"}:
        return "a_demander"
    return "a_deposer" if requires_action else "rattachee"


def _ux_piece_novice_status(status: str) -> dict[str, object]:
    labels = {
        "a_demander": (
            "Il faut demander ce document",
            "Aucune preuve locale n'est rattachee: preparez une relance, puis ajoutez la reponse au depot.",
            "danger",
        ),
        "a_deposer": (
            "A ajouter au depot",
            "Le point attend un fichier: ajoutez-le localement puis rattachez-le comme preuve.",
            "warn",
        ),
        "a_verifier": (
            "Un document local existe",
            "Relisez le document lie avant de dire que la preuve est validee.",
            "info",
        ),
        "rattachee": (
            "Document rattache",
            "La piece existe dans le coffre local; gardez le lien pour la passation.",
            "ok",
        ),
        "exemple": (
            "Exemple fictif",
            "Exemple de piece manquante pour guider l'ecran quand aucun registre n'est encore charge.",
            "muted",
        ),
    }
    label, detail, tone = labels.get(status, labels["a_demander"])
    return {"label": label, "detail": detail, "tone": tone}


def _ux_piece_linked_documents(
    proof_ref: object,
    documents_by_id: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    linked: list[dict[str, object]] = []
    seen: set[str] = set()
    for doc_id in _split_piece_refs(str(proof_ref or "")):
        safe_doc_id = _public_text(doc_id, "")
        if not safe_doc_id or safe_doc_id in seen:
            continue
        seen.add(safe_doc_id)
        doc_row = documents_by_id.get(doc_id, {})
        linked.append(
            {
                "id": safe_doc_id,
                "label": _document_label(safe_doc_id, doc_row, "Document lie"),
                "type_label": _document_type_label(doc_row, "Document"),
                "status_label": "Document local a verifier",
                "href": _route_href("/documents", doc_id=safe_doc_id),
            }
        )
    return linked


def _ux_piece_contract_item(
    item: dict[str, object],
    index: int,
    documents_by_id: dict[str, dict[str, str]],
) -> dict[str, object]:
    expected_piece = _public_text(item.get("piece"), "Piece attendue")
    point_id = _public_text(item.get("point_id"), _stable_action_id("POINT", index, expected_piece))
    request_id = _public_text(item.get("request_id"), "")
    status = _ux_piece_status(item)
    novice_status = _ux_piece_novice_status(status)
    linked_documents = _ux_piece_linked_documents(item.get("proof_ref"), documents_by_id)
    relance_href = _route_href("/demandes/relance", action_id=point_id, request_id=request_id)
    deposit_href = _route_href("/depot", intent="proof", missing_for=point_id, request_id=request_id)
    documents_href = linked_documents[0]["href"] if linked_documents else _route_href("/documents", missing_for=point_id)
    if status == "a_verifier":
        primary_action = {"id": "verify-document", "label": "Verifier le document lie", "href": documents_href}
    elif status == "a_deposer":
        primary_action = {"id": "add-from-depot", "label": "Ajouter depuis le depot", "href": deposit_href}
    elif status == "rattachee":
        primary_action = {"id": "keep-link", "label": "Conserver le lien", "href": _route_href("/pieces", piece=point_id)}
    else:
        primary_action = {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href}
    return {
        "id": _stable_action_id("UX-PIECE", index, point_id, expected_piece),
        "expected_piece": expected_piece,
        "rubric_label": _public_text(item.get("point_type"), "Piece"),
        "point_label": _public_text(item.get("point"), "Point a rattacher"),
        "source_label": _public_text(item.get("source"), "Source a confirmer"),
        "status": status,
        "status_label": novice_status["label"],
        "novice_status": novice_status,
        "priority": _public_text(item.get("priority"), "P2"),
        "priority_label": _priority_label(str(item.get("priority") or "P2")),
        "reason": _public_text(item.get("action") or item.get("next_step"), "Piece necessaire pour avancer."),
        "next_step": _public_text(item.get("next_step"), "Demander, deposer ou verifier la piece attendue."),
        "proof_badge": _public_text(item.get("proof_badge"), "preuve manquante"),
        "signature_badge": _public_text(item.get("signature_badge"), ""),
        "privacy_badge": _public_text(item.get("privacy_badge"), ""),
        "confidence_badge": _public_text(item.get("confidence_badge"), ""),
        "is_fictive": False,
        "requires_real_validation": True,
        "related": {
            "action_id": point_id,
            "request_id": request_id,
            "event_id": point_id,
        },
        "linked_documents": linked_documents,
        "linked_documents_count": len(linked_documents),
        "request_href": relance_href,
        "deposit_href": deposit_href,
        "documents_href": documents_href,
        "href": _route_href("/pieces", piece=point_id),
        "primary_action": primary_action,
        "actions": [
            {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href},
            {"id": "add-from-depot", "label": "Ajouter depuis le depot", "href": deposit_href},
            {"id": "see-documents", "label": "Voir documents lies", "href": documents_href},
        ],
    }


def _ux_piece_from_comptes_piece(piece: dict[str, object], index: int) -> dict[str, object]:
    proof_state = str(piece.get("proof_state") or "")
    if proof_state == "verified":
        status = "rattachee"
    elif proof_state == "candidate":
        status = "a_verifier"
    else:
        status = "a_demander"
    piece_id = _public_text(piece.get("piece_id"), _stable_action_id("PCE-COMP", index, str(piece.get("label", ""))))
    label = _public_text(piece.get("label"), "Piece comptable attendue")
    category_id = _public_text(piece.get("category_id"), "")
    doc_id = _public_text(piece.get("doc_id"), "")
    relance_href = _route_href("/demandes/relance", source="comptes", piece_id=piece_id, categorie=category_id)
    deposit_href = _route_href("/depot", intent="proof", source="comptes", piece_id=piece_id, categorie=category_id)
    action_href = _public_href(piece.get("href"), _route_href("/comptes", proof_state="missing"))
    documents_href = _route_href("/documents", doc_id=doc_id) if doc_id else action_href
    novice_status = _ux_piece_novice_status(status)
    linked_documents = (
        [
            {
                "id": doc_id,
                "label": label,
                "type_label": _public_text(piece.get("type_label"), "Document comptable"),
                "status_label": "Document local a verifier",
                "href": documents_href,
            }
        ]
        if doc_id
        else []
    )
    primary_action = (
        {"id": "verify-document", "label": "Verifier le document lie", "href": documents_href}
        if status == "a_verifier"
        else {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href}
    )
    expected_piece = label if label.lower().startswith("justificatif") else f"Justificatif comptable - {label}"
    return {
        "id": _stable_action_id("UX-PIECE-COMP", index, piece_id, label),
        "expected_piece": expected_piece,
        "rubric_label": "Comptes et factures",
        "point_label": _public_text(piece.get("match_status_label"), "Controle comptable a justifier"),
        "source_label": "ComptaScope",
        "status": status,
        "status_label": novice_status["label"],
        "novice_status": novice_status,
        "priority": "P1" if status == "a_demander" else "P2",
        "priority_label": _priority_label("P1" if status == "a_demander" else "P2"),
        "reason": _public_text(piece.get("proof_state_label") or piece.get("match_status_label"), "Justificatif a demander ou rattacher."),
        "next_step": "Preparer une relance au syndic ou ajouter le justificatif depuis le depot.",
        "proof_badge": "preuve manquante" if status == "a_demander" else "preuve locale",
        "signature_badge": "",
        "privacy_badge": "",
        "confidence_badge": "",
        "is_fictive": False,
        "requires_real_validation": True,
        "related": {
            "action_id": piece_id,
            "request_id": "",
            "event_id": piece_id,
        },
        "linked_documents": linked_documents,
        "linked_documents_count": len(linked_documents),
        "request_href": relance_href,
        "deposit_href": deposit_href,
        "documents_href": documents_href,
        "href": action_href,
        "action_href": action_href,
        "action_label": "Controle comptes",
        "owner_label": "Syndic ou conseil syndical",
        "proof_expected_label": expected_piece,
        "primary_action": primary_action,
        "actions": [
            {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href},
            {"id": "add-from-depot", "label": "Ajouter depuis le depot", "href": deposit_href},
            {"id": "see-documents", "label": "Voir documents lies", "href": documents_href},
            {"id": "open-comptes", "label": "Voir dans les comptes", "href": action_href},
        ],
    }


def _ux_piece_from_action(action: dict[str, str], index: int) -> dict[str, object]:
    action_id = _public_text(action.get("id"), _stable_action_id("ACT", index, action.get("title", "")))
    expected_piece = _public_text(action.get("evidence"), "Preuve attendue a preciser")
    title = _public_text(action.get("title"), "Action a traiter")
    relance_href = _route_href("/demandes/relance", action_id=action_id)
    deposit_href = _route_href("/depot", intent="proof", action=action_id)
    action_href = _action_selected_href(action_id)
    novice_status = _ux_piece_novice_status("a_demander")
    return {
        "id": _stable_action_id("UX-PIECE-ACT", index, action_id, expected_piece),
        "expected_piece": expected_piece,
        "rubric_label": _public_text(action.get("domain_label"), "Action"),
        "point_label": title,
        "source_label": _public_text(action.get("source"), "Registre actions"),
        "status": "a_demander",
        "status_label": novice_status["label"],
        "novice_status": novice_status,
        "priority": _public_text(action.get("priority"), "P2"),
        "priority_label": _priority_label(str(action.get("priority") or "P2")),
        "reason": _public_text(action.get("detail") or action.get("next_step"), "Preuve attendue pour cloturer l'action."),
        "next_step": _public_text(action.get("next_step"), "Preparer une relance ou ajouter la preuve depuis le depot."),
        "proof_badge": "preuve manquante",
        "signature_badge": "",
        "privacy_badge": "",
        "confidence_badge": "",
        "is_fictive": False,
        "requires_real_validation": True,
        "related": {
            "action_id": action_id,
            "request_id": "",
            "event_id": action_id,
        },
        "linked_documents": [],
        "linked_documents_count": 0,
        "request_href": relance_href,
        "deposit_href": deposit_href,
        "documents_href": _route_href("/documents", action=action_id),
        "href": action_href,
        "action_href": action_href,
        "action_label": title,
        "owner_label": _public_text(action.get("owner"), "Syndic ou conseil syndical"),
        "proof_expected_label": expected_piece,
        "primary_action": {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href},
        "actions": [
            {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href},
            {"id": "add-from-depot", "label": "Ajouter depuis le depot", "href": deposit_href},
            {"id": "open-action", "label": "Voir action", "href": action_href},
        ],
    }


def _ux_piece_fictive_examples() -> list[dict[str, object]]:
    examples = [
        (
            "EXEMPLE-ASSURANCE",
            "Attestation assurance immeuble recente",
            "Assurance",
            "Demander l'attestation en cours de validite au syndic.",
        ),
        (
            "EXEMPLE-TRAVAUX",
            "Ordre de service signe",
            "Travaux",
            "Obtenir la version signee avant de clore la decision.",
        ),
    ]
    items: list[dict[str, object]] = []
    for index, (point_id, expected_piece, rubric, reason) in enumerate(examples, start=1):
        relance_href = _route_href("/demandes/relance", action_id=point_id)
        deposit_href = _route_href("/depot", intent="proof", missing_for=point_id)
        novice_status = _ux_piece_novice_status("exemple")
        items.append(
            {
                "id": _stable_action_id("UX-PIECE-EXEMPLE", index, point_id, expected_piece),
                "expected_piece": expected_piece,
                "rubric_label": rubric,
                "point_label": "Exemple de point a rattacher",
                "source_label": "Exemple local",
                "status": "exemple",
                "status_label": novice_status["label"],
                "novice_status": novice_status,
                "priority": "P2",
                "priority_label": _priority_label("P2"),
                "reason": reason,
                "next_step": "Remplacer cet exemple par une vraie piece issue du depot ou d'une relance.",
                "is_fictive": True,
                "requires_real_validation": True,
                "linked_documents": [],
                "linked_documents_count": 0,
                "request_href": relance_href,
                "deposit_href": deposit_href,
                "documents_href": _route_href("/documents"),
                "href": _route_href("/pieces", piece=point_id),
                "primary_action": {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href},
                "actions": [
                    {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href},
                    {"id": "add-from-depot", "label": "Ajouter depuis le depot", "href": deposit_href},
                ],
            }
        )
    return items


def _build_pieces_ux_model(
    *,
    piece_workshop: dict[str, object],
    documents: dict[str, object],
    action_items: list[dict[str, str]],
    comptes: dict[str, object],
) -> dict[str, object]:
    documents_by_id = _documents_by_id(documents)
    source_items = _list_of_dicts(piece_workshop.get("items"))
    actionable_source = [
        item
        for item in source_items
        if bool(item.get("requires_action", True))
    ]
    items = [
        _ux_piece_contract_item(item, index, documents_by_id)
        for index, item in enumerate(actionable_source[:80], start=1)
    ]
    comptes_pieces = comptes.get("pieces") if isinstance(comptes.get("pieces"), dict) else {}
    comptes_missing = _list_of_dicts(comptes_pieces.get("missing") if isinstance(comptes_pieces, dict) else [])
    comptes_candidate = _list_of_dicts(comptes_pieces.get("candidate") if isinstance(comptes_pieces, dict) else [])
    for index, piece in enumerate((comptes_missing + comptes_candidate)[:80], start=len(items) + 1):
        items.append(_ux_piece_from_comptes_piece(piece, index))
    represented_action_ids = {
        str((item.get("related") or {}).get("action_id") or "")
        for item in items
        if isinstance(item.get("related"), dict)
    }
    represented_piece_keys = {
        str(item.get("expected_piece") or "").strip().lower()
        for item in items
        if str(item.get("expected_piece") or "").strip()
    }
    for index, action in enumerate(action_items, start=len(items) + 1):
        if action.get("status") != "a_demander":
            continue
        if action.get("domain") == "comptes":
            continue
        action_id = _public_text(action.get("id"), "")
        if action_id and action_id in represented_action_ids:
            continue
        expected_piece_key = _public_text(action.get("evidence"), "").strip().lower()
        if expected_piece_key and expected_piece_key in represented_piece_keys:
            continue
        items.append(_ux_piece_from_action(action, index))
        if action_id:
            represented_action_ids.add(action_id)
        if expected_piece_key:
            represented_piece_keys.add(expected_piece_key)
    missing_items = [item for item in items if item.get("status") in {"a_demander", "a_deposer"}]
    verify_items = [item for item in items if item.get("status") == "a_verifier"]
    linked_documents_count = sum(int(item.get("linked_documents_count") or 0) for item in items)
    examples = _ux_piece_fictive_examples() if not items else []
    by_status = Counter(str(item.get("status", "")) for item in items)
    by_rubric = Counter(str(item.get("rubric_label", "Piece")) for item in items)
    piece_summary = piece_workshop.get("summary") if isinstance(piece_workshop.get("summary"), dict) else {}
    total_slots = max(int(piece_summary.get("total") or len(items) or len(examples) or 1), 1)
    completed = int(piece_summary.get("with_local_proof") or linked_documents_count or 0)
    completion_pct = max(0, min(100, round(100 * completed / total_slots)))
    return {
        "context": {
            "route": "/pieces?proof=missing",
            "title": "Pieces manquantes",
            "subtitle": "Demander, deposer ou verifier les pieces attendues avant de clore un point.",
            "role_label": "Conseil syndical",
        },
        "summary": {
            "total_actionable": len(items),
            "missing_count": len([item for item in items if item.get("status") == "a_demander"]),
            "to_deposit_count": len([item for item in items if item.get("status") == "a_deposer"]),
            "to_verify_count": len(verify_items),
            "linked_documents_count": linked_documents_count,
            "fictive_count": len(examples),
            "completion_pct": completion_pct,
        },
        "primary_actions": [
            {"id": "prepare-relance", "label": "Preparer une relance", "href": _route_href("/demandes/relance")},
            {"id": "add-from-depot", "label": "Ajouter depuis le depot", "href": _route_href("/depot", intent="proof")},
            {"id": "see-documents", "label": "Voir documents lies", "href": _route_href("/documents")},
        ],
        "status_legend": [
            {"status": key, **_ux_piece_novice_status(key)}
            for key in ["a_demander", "a_deposer", "a_verifier", "rattachee", "exemple"]
        ],
        "filters": {
            "status": [
                {
                    "value": status,
                    "label": _ux_piece_novice_status(status)["label"],
                    "count": count,
                    "href": _route_href("/pieces", proof=status),
                    "is_active": status in {"a_demander", "a_deposer"},
                }
                for status, count in sorted(by_status.items())
            ],
            "rubrics": [
                {
                    "value": rubric,
                    "label": rubric,
                    "count": count,
                    "href": _route_href("/pieces", rubrique=rubric),
                }
                for rubric, count in sorted(by_rubric.items())
            ],
        },
        "items": items,
        "missing": missing_items,
        "to_verify": verify_items,
        "linked_documents": [
            document
            for item in items
            for document in _list_of_dicts(item.get("linked_documents"))
        ][:20],
        "selected": items[0] if items else {},
        "empty_state": {
            "is_visible": not bool(items),
            "label": "Aucune piece manquante exploitable dans les registres charges.",
            "next_step": "Ajouter une piece au depot ou generer les rapports de completude documentaire.",
            "deposit_href": _route_href("/depot", intent="proof"),
            "relance_href": _route_href("/demandes/relance"),
            "examples": examples,
        },
    }
