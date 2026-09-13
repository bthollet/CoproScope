from __future__ import annotations

from ._runtime import *

def _build_registre_model(
    instance: InstanceConfig,
    year: int,
    *,
    ux_items: list[dict[str, object]],
    decisions: dict[str, object],
    documents: dict[str, object],
) -> dict[str, object]:
    rows = decisions.get("rows") if isinstance(decisions.get("rows"), list) else []
    documents_index = _documents_by_id(documents)
    items = [
        _decision_register_item(row, index, documents_index)
        for index, row in enumerate(rows)
        if isinstance(row, dict)
    ]
    items = sorted(
        items,
        key=lambda item: (
            {"late": 0, "missing": 1, "planned": 2, "done": 9}.get(str(item.get("due_state")), 5),
            {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "OK": 9}.get(str(item.get("priority")), 5),
            str(item.get("due_on") or "9999-12-31"),
            str(item.get("resolution_ref", "")),
        ),
    )
    selected = next((item for item in items if item.get("status") != "clos"), items[0] if items else _empty_registre_selected())
    selected["is_selected"] = bool(selected.get("id"))
    selected["tabs"] = _register_tabs(selected)

    groups: list[dict[str, object]] = []
    grouped: dict[str, list[dict[str, object]]] = {}
    for item in items:
        grouped.setdefault(str(item.get("ag_id") or "AG-SANS-DATE"), []).append(item)
    for ag_id, group_items in sorted(grouped.items(), key=lambda pair: (pair[0],)):
        ag_date = str(group_items[0].get("ag_date") or "")
        groups.append(
            {
                "ag_id": ag_id,
                "label": _ag_label(ag_id, ag_date),
                "date": ag_date,
                "open_count": len([item for item in group_items if item.get("status") != "clos"]),
                "late_count": len([item for item in group_items if item.get("due_state") == "late"]),
                "is_expanded": any(item.get("id") == selected.get("id") for item in group_items),
                "href": _route_href("/actions", ag=ag_id),
                "items": [
                    {
                        "id": item.get("id", ""),
                        "resolution_ref": item.get("resolution_ref", ""),
                        "title": item.get("title", ""),
                        "subtitle": item.get("next_step", ""),
                        "status_label": item.get("status_label", ""),
                        "status_tone": item.get("status_tone", ""),
                        "priority_label": item.get("priority_label", ""),
                        "proof_state_label": item.get("proof_state_label", ""),
                        "owner_label": item.get("owner", ""),
                        "due_label": item.get("due_label", ""),
                        "is_selected": item.get("id") == selected.get("id"),
                        "href": item.get("href", _route_href("/actions")),
                    }
                    for item in group_items
                ],
            }
        )

    total_proofs = [
        proof
        for item in items
        for proof in (item.get("proofs", []) if isinstance(item.get("proofs"), list) else [])
        if isinstance(proof, dict)
    ]
    all_followups = [
        followup
        for item in items
        for followup in (item.get("followups", []) if isinstance(item.get("followups"), list) else [])
        if isinstance(followup, dict)
    ]
    share_blockers = len(
        [
            item
            for item in items
            if isinstance(item.get("diffusion"), dict)
            and item["diffusion"].get("status") in {"blocked", "after_redaction"}
        ]
    )
    summary_counts = {
        "total_resolutions": len(items),
        "open_actions": len([item for item in items if item.get("status") != "clos"]),
        "late_actions": len([item for item in items if item.get("due_state") == "late"]),
        "missing_proofs": len([item for item in items if item.get("proof_state") == "missing"]),
        "syndic_followups": len([followup for followup in all_followups if followup.get("status") != "closed"]),
        "verified_proofs": len([proof for proof in total_proofs if proof.get("status") == "verified"]),
        "share_blockers": share_blockers,
    }
    summary_hrefs = {
        "total_resolutions": _route_href("/actions"),
        "open_actions": _route_href("/actions", status="a_traiter"),
        "late_actions": _route_href("/actions", due_state="late"),
        "missing_proofs": _route_href("/actions", proof_state="missing"),
        "syndic_followups": _route_href("/actions", tab="relance"),
        "verified_proofs": _route_href("/actions", proof_state="verified"),
        "share_blockers": _route_href("/actions", diffusion="blocked"),
    }
    summary: dict[str, object] = {
        **summary_counts,
        **{f"{key}_href": href for key, href in summary_hrefs.items()},
        "last_updated_label": f"Situation {year}",
        "cards": [
            {"id": key, "label": label, "count": summary_counts[key], "href": summary_hrefs[key]}
            for key, label in [
                ("total_resolutions", "Resolutions"),
                ("open_actions", "Actions ouvertes"),
                ("late_actions", "En retard"),
                ("missing_proofs", "Preuves manquantes"),
                ("syndic_followups", "Relances syndic"),
                ("verified_proofs", "Preuves validees"),
                ("share_blockers", "A verifier avant partage"),
            ]
        ],
    }

    facets = {
        "ag": _facet_options("ag_id", items),
        "status": _facet_options("status", items),
        "owner": _facet_options("owner", items),
        "priority": _facet_options("priority", items, {"P0": "Critique", "P1": "Haute", "P2": "Moyenne", "P3": "Basse", "OK": "Cloturee"}),
        "proof_state": _facet_options("proof_state", items),
        "due_state": _facet_options("due_state", items),
        "scope": [{"value": "decisions", "label": "Decisions AG", "count": len(items), "href": _route_href("/actions", scope="decisions"), "is_active": True}],
    }
    filters = {
        "selected_ag": "",
        "selected_status": "",
        "selected_owner": "",
        "selected_priority": "",
        "selected_proof_state": "",
        "query": "",
        "selected_item_id": selected.get("id", ""),
    }
    empty_states = {
        "no_resolution": {
            "is_visible": not bool(items),
            "label": "Aucune decision AG chargee. Ajouter ou importer un PV / registre AG pour commencer.",
            "href": _route_href("/depot"),
        },
        "no_result": {
            "is_visible": False,
            "label": "Aucune resolution ne correspond a ce filtre. Retirer un filtre ou afficher toutes les AG.",
            "href": _route_href("/actions"),
        },
        "no_proof": {
            "is_visible": not bool(selected.get("proofs")),
            "label": "Aucune preuve validee pour cette action. Ajouter une piece, choisir une preuve existante ou preparer une demande au syndic.",
            "href": _route_href("/actions", selected_item_id=selected.get("id", ""), tab="preuves"),
        },
        "no_piece": {
            "is_visible": not bool(selected.get("pieces")),
            "label": "Aucune piece rattachee. Ajouter le PV, un devis, une facture, une reponse syndic ou une note de verification.",
            "href": _route_href("/pieces"),
        },
        "no_followup": {
            "is_visible": not bool(selected.get("followups")),
            "label": "Aucune relance tracee. Preparer un message copiable et noter le canal d'envoi.",
            "href": _route_href("/actions", selected_item_id=selected.get("id", ""), tab="relance"),
        },
        "no_history": {
            "is_visible": not bool(selected.get("history")),
            "label": "Aucune trace encore inscrite. La prochaine mise a jour creera le premier evenement.",
            "href": _route_href("/actions", selected_item_id=selected.get("id", ""), tab="historique"),
        },
        "export_blocked": {
            "is_visible": bool(share_blockers),
            "label": "Export non prepare car au moins un element demande une verification de diffusion.",
            "href": _route_href("/actions", diffusion="blocked"),
        },
    }
    export_status = "blocked" if share_blockers else "ready"
    return {
        "context": {
            "coffre_label": _public_text(instance.display_name, "Copropriete"),
            "sharing_mode_label": "Prive local",
            "sharing_mode_detail": "Aucune synchronisation externe lancee depuis cette page.",
            "role_label": "Conseil syndical",
            "as_of_label": f"Situation {year}",
        },
        "summary": summary,
        "facets": facets,
        "filters": filters,
        "ag_groups": groups,
        "items": items,
        "selected": selected,
        "tabs": selected.get("tabs", _register_tabs(selected)),
        "empty_states": empty_states,
        "export": {
            "status": export_status,
            "label": "Export a verifier avant diffusion" if share_blockers else "Export registre",
            "href": _route_href("/exports/actions.csv", scope="decisions"),
            "markdown_href": _route_href("/exports/actions.md", scope="decisions"),
            "notice": "Exporter le perimetre courant et verifier les pieces sensibles avant partage.",
        },
        "action_followup": selected.get("action_followup", {}),
        "linked_documents": selected.get("linked_documents", []),
        "proofs": selected.get("proofs", []),
        "syndic_followups": selected.get("syndic_followups", []),
        "history_events": selected.get("history_events", []),
        "work_items": ux_items,
    }


def _list_of_dicts(value: object) -> list[dict[str, object]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _action_selected_href(item_id: object, **params: object) -> str:
    return _route_href("/actions", selected=_public_text(item_id, ""), **params)


def _action_detail_model(registre: dict[str, object]) -> dict[str, object]:
    selected = registre.get("selected") if isinstance(registre.get("selected"), dict) else {}
    selected_id = _public_text(selected.get("id"), "")
    proofs = _list_of_dicts(selected.get("proofs"))
    pieces = _list_of_dicts(selected.get("pieces"))
    followups = _list_of_dicts(selected.get("followups"))
    history = _list_of_dicts(selected.get("history"))
    diffusion = selected.get("diffusion") if isinstance(selected.get("diffusion"), dict) else {}
    memory = selected.get("memory") if isinstance(selected.get("memory"), dict) else {}
    proof_state = _public_text(selected.get("proof_state"), "missing")
    expected_proof = _public_text(selected.get("proof_expected"), "Preuve attendue a preciser")
    verified_proofs = [proof for proof in proofs if proof.get("status") == "verified"]
    candidate_proofs = [proof for proof in proofs if proof.get("status") == "candidate"]
    linked_pieces = [piece for piece in pieces if piece.get("proof_relation") not in {"verified", "candidate"}]
    can_close = proof_state == "verified" and bool(verified_proofs)
    share_status = str(diffusion.get("status") or "")
    can_share = share_status == "copro_ok"
    memory_ref = _public_text(memory.get("timeline_ref") or selected_id, "")
    selected_title = _public_text(selected.get("title"), "Action a reprendre")
    selected_status = _public_text(selected.get("status"), "a_traiter")
    primary_label = "Rattacher une preuve"
    if followups or proof_state == "missing":
        primary_label = "Preparer la relance"
    if proof_state == "candidate":
        primary_label = "Verifier la piece candidate"
    if can_close:
        primary_label = "Conserver la preuve validee"

    missing_items: list[dict[str, object]] = []
    if proof_state in {"missing", "blocked"} or not verified_proofs:
        missing_items.append(
            {
                "id": _stable_action_id("MISSING", 0, selected_id, expected_proof),
                "label": expected_proof,
                "why_needed": "Prouver l'execution ou la decision avant cloture.",
                "request_href": _route_href("/demandes/relance", action_id=selected_id),
                "deposit_href": _route_href("/depot", intent="proof", action=selected_id),
            }
        )

    return {
        "context": {
            "route": "/actions",
            "selected_id": selected_id,
            "title": "Detail action",
            "visual_name": "Fiche action",
            "role_label": "Conseil syndical",
            "sharing_mode_label": "Prive local",
            "as_of_label": "Situation courante",
        },
        "navigation": {
            "back_href": _route_href("/actions"),
            "back_label": "Retour aux actions",
            "memory_href": _route_href("/chantiers", selected=memory_ref) if memory_ref else _route_href("/chantiers"),
            "memory_label": "Voir dans la memoire",
            "preserve_filters": True,
        },
        "selected": {
            "id": selected_id,
            "title": selected_title,
            "summary": _public_text(selected.get("decision_summary") or selected.get("status_detail"), "Action suivie par le conseil syndical."),
            "status": selected_status,
            "status_label": _public_text(selected.get("status_label"), _ux_status_label(selected_status)),
            "priority": _public_text(selected.get("priority"), "P2"),
            "priority_label": _public_text(selected.get("priority_label"), _priority_label(str(selected.get("priority") or "P2"))),
            "owner_label": _public_text(selected.get("owner"), "Conseil syndical"),
            "referent_label": _public_text(selected.get("referent"), "Conseil syndical"),
            "due_label": _public_text(selected.get("due_label"), "Echeance a fixer"),
            "next_step": _public_text(selected.get("next_step"), "Noter la prochaine action et la preuve attendue."),
        },
        "source": {
            "kind_label": "Decision ou demande source",
            "label": _public_text(selected.get("resolution_ref") or selected.get("source_file_label"), "Source a confirmer"),
            "summary": _public_text(selected.get("decision_source_excerpt"), "Source a relire avant cloture."),
            "source_href": _action_selected_href(selected_id, tab="historique") if selected_id else _route_href("/actions"),
            "certainty_label": "Preuve validee" if can_close else "A confirmer par piece ou justification.",
        },
        "status": {
            "delay_label": _public_text(selected.get("due_label"), "En attente"),
            "blocked_reason": "" if can_close else "Preuve ou justification attendue.",
            "can_close": can_close,
            "close_disabled_reason": "" if can_close else "La preuve attendue n'est pas encore validee.",
        },
        "proofs": {
            "expected_label": expected_proof,
            "state": proof_state,
            "state_label": _proof_state_label(proof_state),
            "verified": verified_proofs,
            "candidates": candidate_proofs,
            "linked_pieces": linked_pieces,
        },
        "missing": {
            "items": missing_items,
            "summary_label": "Aucun manque bloquant." if not missing_items else f"{len(missing_items)} piece ou preuve attendue.",
        },
        "linked": {
            "documents": [
                {
                    "id": piece.get("doc_id", ""),
                    "label": piece.get("label", "Document lie"),
                    "href": piece.get("href", _route_href("/documents")),
                    "why_linked": piece.get("role_label", "Piece utile au suivi."),
                }
                for piece in pieces[:8]
            ],
            "events": [
                {
                    "id": memory_ref or selected_id,
                    "label": _public_text(memory.get("pack_section"), "Memoire de copropriete"),
                    "href": _route_href("/chantiers", selected=memory_ref or selected_id),
                }
            ]
            if (memory_ref or selected_id)
            else [],
            "requests": [
                {
                    "id": followup.get("related_request_id", ""),
                    "label": followup.get("label", "Relance liee"),
                    "href": followup.get("href", _action_selected_href(selected_id, tab="relance")),
                }
                for followup in followups
                if followup.get("related_request_id")
            ],
            "decisions": [
                {
                    "id": selected_id,
                    "label": _public_text(selected.get("resolution_ref"), "Decision suivie"),
                    "href": _action_selected_href(selected_id),
                }
            ]
            if selected_id
            else [],
        },
        "followups": {
            "status_label": _public_text((followups[0].get("status_label") if followups else ""), "Brouillon a preparer"),
        "primary_href": _route_href("/demandes/relance", action_id=selected_id) if selected_id else _route_href("/demandes/relance"),
            "last_followup_label": _public_text((followups[0].get("label") if followups else ""), "Aucune relance tracee"),
            "items": followups,
        },
        "history": [
            {
                "date_label": _date_label(event.get("occurred_on"), "Date a noter"),
                "label": _public_text(event.get("type_label"), "Mise a jour"),
                "detail": _public_text(event.get("summary"), "Trace courte a completer."),
            }
            for event in history[:8]
        ],
        "share": {
            "level": _public_text(diffusion.get("status"), "conseil_syndical"),
            "label": _public_text(diffusion.get("label"), "Conseil syndical"),
            "can_share": can_share,
            "can_share_label": "Partage possible apres controle" if can_share else "Diffusion a verifier",
            "reason": _public_text(diffusion.get("reason"), "La preuve ou la piece peut contenir des informations a limiter."),
            "review_href": _route_href("/confidentialite", scope="action", selected=selected_id),
        },
        "handover": {
            "note": _public_text(memory.get("handover_note"), "Ne pas clore sans preuve ou justification ecrite."),
            "is_ready": can_close and can_share,
            "missing_for_handover": []
            if can_close and can_share
            else [
                label
                for label in ["preuve validee" if not can_close else "", "statut diffusion" if not can_share else ""]
                if label
            ],
        },
        "actions": {
            "primary": {"label": primary_label, "href": _route_href("/demandes/relance", action_id=selected_id) if primary_label == "Preparer la relance" else _action_selected_href(selected_id, tab="preuves")},
            "secondary": [
                {"label": "Rattacher une piece", "href": _route_href("/depot", intent="proof", action=selected_id)},
                {"label": "Voir dans la memoire", "href": _route_href("/chantiers", selected=memory_ref or selected_id)},
            ],
            "export": {
                "label": "Preparer un extrait",
                "href": _route_href("/exports/passation", scope="action", selected=selected_id),
                "requires_preview": True,
                "disabled": False,
            },
        },
        "empty_states": {
            "not_found": "Action introuvable. Revenir a la liste des actions.",
            "none_selected": "Selectionnez une action pour voir la preuve attendue, le suivi et la prochaine etape.",
            "no_proof": "Aucune preuve validee. Ajouter une piece, choisir un document candidat ou preparer une demande.",
            "no_followup": "Aucune relance tracee. Preparer un message copiable et noter le canal d'envoi.",
        },
    }
