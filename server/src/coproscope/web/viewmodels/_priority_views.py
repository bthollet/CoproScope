from __future__ import annotations

from ._runtime import *

def _syndic_followup_view_item(action: dict[str, str], index: int) -> dict[str, object]:
    item_id = _public_text(action.get("id"), _stable_action_id("FOLLOWUP", index, action.get("title", "")))
    expected_proof = _public_text(action.get("evidence"), "Preuve attendue a preciser")
    title = _public_text(action.get("title"), "Demande au syndic")
    status = "ready_to_copy" if action.get("status") == "a_demander" else "draft"
    body = (
        f"Bonjour, pouvez-vous nous transmettre ou confirmer la piece suivante: {expected_proof} ? "
        "Merci de preciser la date, la source et le contexte de la reponse."
    )
    return {
        "id": _stable_action_id("RELANCE", index, item_id, expected_proof),
        "title": title,
        "related_action_id": item_id,
        "related_piece_id": _stable_action_id("MISSING-PIECE", index, item_id, expected_proof),
        "status": status,
        "status_label": "Pret a copier" if status == "ready_to_copy" else "Brouillon a relire",
        "priority": _public_text(action.get("priority"), "P2"),
        "priority_label": _priority_label(str(action.get("priority") or "P2")),
        "channel_label": "Email syndic ou canal a noter",
        "last_request_label": "Aucune demande tracee",
        "proposed_followup_label": "A envoyer hors CoproScope apres relecture",
        "expected_proof": expected_proof,
        "draft": {
            "subject": f"Demande de piece - {title}",
            "body": _public_text(body, "Message de relance a preparer."),
            "copy_warning": "CoproScope prepare le texte; l'envoi reste externe et doit etre confirme.",
        },
        "copy_action": {"label": "Copier le message", "disabled": False, "disabled_reason": ""},
        "mark_sent_action": {
            "label": "Noter l'envoi hors CoproScope apres copie",
            "requires_confirmation": True,
            "disabled": False,
            "disabled_reason": "",
        },
        "answer_href": _route_href("/depot", intent="syndic-answer", action=item_id),
        "memory_href": _public_href(action.get("href"), _route_href("/chantiers")),
        "href": _route_href("/demandes/relance", action_id=item_id),
    }


def _missing_piece_view_from_ux_piece(item: dict[str, object], index: int) -> dict[str, object]:
    expected_piece = _public_text(item.get("expected_piece"), "Piece attendue")
    related = item.get("related") if isinstance(item.get("related"), dict) else {}
    related_action_id = _public_text(related.get("action_id"), _stable_action_id("MISSING-PIECE", index, expected_piece))
    candidate_docs = _list_of_dicts(item.get("linked_documents")) if item.get("status") == "a_verifier" else []
    priority = _public_text(item.get("priority"), "P2")
    return {
        "id": _public_text(item.get("id"), _stable_action_id("MISSING-PIECE", index, related_action_id, expected_piece)),
        "expected_piece": expected_piece,
        "proof_expected_label": _public_text(item.get("proof_expected_label") or expected_piece, expected_piece),
        "rubric_label": _public_text(item.get("rubric_label"), "Piece"),
        "reason": _public_text(item.get("reason") or item.get("next_step"), "Necessaire pour avancer sans conclure sans preuve."),
        "proof_purpose": "Prouver ou confirmer le point rattache avant passation.",
        "criticality": priority,
        "criticality_label": _priority_label(priority),
        "status": _public_text(item.get("status"), "a_demander"),
        "status_label": _public_text(item.get("status_label"), "A demander"),
        "source_label": _public_text(item.get("source_label"), "Source a confirmer"),
        "owner_label": _public_text(item.get("owner_label"), "Syndic ou source a confirmer"),
        "related_action_id": related_action_id,
        "related_event_id": _public_text(related.get("event_id"), related_action_id),
        "request_href": _public_href(item.get("request_href"), _route_href("/demandes/relance", action_id=related_action_id)),
        "deposit_href": _public_href(item.get("deposit_href"), _route_href("/depot", intent="proof", missing_for=related_action_id)),
        "action_href": _public_href(item.get("action_href") or item.get("href"), _action_selected_href(related_action_id)),
        "action_label": _public_text(item.get("action_label") or item.get("point_label"), "Action a ouvrir"),
        "candidate_docs": [
            {
                "id": _public_text(document.get("id"), ""),
                "label": _public_text(document.get("label"), "Document lie"),
                "status_label": _public_text(document.get("status_label"), "Piece candidate a verifier"),
                "href": _public_href(document.get("href"), "/documents"),
            }
            for document in candidate_docs
        ],
        "diffusion_label": "Conseil syndical",
        "next_step": _public_text(item.get("next_step"), "Demander ou rattacher la piece attendue."),
    }


def _build_priority_views(
    *,
    action_items: list[dict[str, str]],
    piece_workshop: dict[str, object],
    pieces_model: dict[str, object] | None = None,
) -> dict[str, object]:
    late_source = [
        action
        for action in action_items
        if action.get("priority", "").upper() in {"P0", "P1"} or action.get("status") in {"bloque", "a_demander"}
    ]
    late_items = [_priority_late_action_item(action, index) for index, action in enumerate(late_source[:30], start=1)]
    pieces_model = pieces_model if isinstance(pieces_model, dict) else {}
    merged_missing_source = _list_of_dicts(pieces_model.get("missing"))
    if merged_missing_source:
        missing_items = [
            _missing_piece_view_from_ux_piece(item, index)
            for index, item in enumerate(merged_missing_source[:30], start=1)
        ]
    else:
        missing_source = _list_of_dicts(piece_workshop.get("to_request"))
        missing_items = [_missing_piece_view_item(item, index) for index, item in enumerate(missing_source[:30], start=1)]
    syndic_source = [
        action
        for action in action_items
        if action.get("channel") == "syndic"
        or action.get("status") == "a_demander"
        or "syndic" in " ".join([action.get("owner", ""), action.get("title", ""), action.get("next_step", "")]).lower()
    ]
    followup_items = [_syndic_followup_view_item(action, index) for index, action in enumerate(syndic_source[:30], start=1)]
    missing_by_rubric = Counter(str(item.get("rubric_label", "Piece")) for item in missing_items)
    pieces_summary = pieces_model.get("summary") if isinstance(pieces_model.get("summary"), dict) else {}
    followup_tabs = [
        {"id": "a_preparer", "label": "A preparer", "count": len([item for item in followup_items if item.get("status") == "draft"]), "is_active": True},
        {"id": "pretes", "label": "Pretes a copier", "count": len([item for item in followup_items if item.get("status") == "ready_to_copy"]), "is_active": False},
        {"id": "reponses", "label": "Reponses a verifier", "count": 0, "is_active": False},
        {"id": "cloturees", "label": "Cloturees", "count": 0, "is_active": False},
    ]
    return {
        "late_actions": {
            "context": {
                "route": "/actions?view=retards",
                "title": "Toutes les actions en retard",
                "subtitle": "Ce qui depasse son echeance ou bloque une preuve attendue.",
            },
            "summary": {
                "total": len(late_items),
                "critical_count": len([item for item in late_items if item.get("priority") in {"P0", "P1"}]),
                "missing_proof_count": len([item for item in late_items if item.get("status") == "a_demander"]),
                "syndic_ready_count": len([item for item in followup_items if item.get("status") == "ready_to_copy"]),
                "oldest_delay_label": late_items[0]["delay_label"] if late_items else "Aucun retard",
            },
            "filters": {
                "priority_href": _route_href("/actions", priority="P1"),
                "syndic_href": _route_href("/actions", scope="syndic"),
                "to_request_href": _route_href("/actions", status="a_demander"),
            },
            "items": late_items,
            "selected": late_items[0] if late_items else {},
            "empty_state": {
                "is_visible": not bool(late_items),
                "label": "Aucune action en retard. Les prochaines echeances restent visibles dans la memoire.",
                "href": _route_href("/chantiers"),
            },
        },
        "missing_pieces": {
            "context": {
                "route": "/pieces?proof=missing",
                "title": "Pieces manquantes",
                "subtitle": "Les pieces a obtenir, verifier ou rattacher comme preuve.",
            },
            "summary": {
                "total": len(missing_items),
                "critical_count": len([item for item in missing_items if item.get("criticality") in {"P0", "P1"}]),
                "candidate_count": int(pieces_summary.get("to_verify_count") or len([item for item in missing_items if item.get("candidate_docs")])),
                "to_request_count": len([item for item in missing_items if item.get("status") == "a_demander"]),
                "completion_pct": int(pieces_summary.get("completion_pct") or 0)
                if pieces_summary
                else int(piece_workshop.get("summary", {}).get("with_local_proof", 0) or 0)
                if isinstance(piece_workshop.get("summary"), dict)
                else 0,
            },
            "groups": [
                {"id": _stable_action_id("RUBRIC", index, rubric), "label": rubric, "count": count}
                for index, (rubric, count) in enumerate(sorted(missing_by_rubric.items()), start=1)
            ],
            "items": missing_items,
            "selected": missing_items[0] if missing_items else {},
            "empty_state": {
                "is_visible": not bool(missing_items),
                "label": "Aucune piece manquante prioritaire n'est remontee.",
                "href": _route_href("/pieces"),
            },
        },
        "syndic_followups": {
            "context": {
                "route": "/demandes/relance",
                "title": "Relance syndic",
                "subtitle": "Brouillons, relances a envoyer et reponses a verifier.",
            },
            "summary": {
                "total_open": len(followup_items),
                "draft_count": len([item for item in followup_items if item.get("status") == "draft"]),
                "ready_count": len([item for item in followup_items if item.get("status") == "ready_to_copy"]),
                "sent_external_count": 0,
                "answers_to_verify_count": 0,
                "blocked_count": 0,
            },
            "tabs": followup_tabs,
            "items": followup_items,
            "selected": followup_items[0] if followup_items else {},
            "empty_state": {
                "is_visible": not bool(followup_items),
                "label": "Aucune relance syndic n'est en attente.",
                "href": _route_href("/actions"),
            },
        },
    }


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
