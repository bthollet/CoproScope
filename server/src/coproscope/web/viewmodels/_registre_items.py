from __future__ import annotations

from ._runtime import *

def _decision_register_item(
    row: dict[str, str],
    index: int,
    documents_by_id: dict[str, dict[str, str]],
) -> dict[str, object]:
    raw_id = row.get("decision_action_id") or _stable_action_id("DAP", index, row.get("ag_id", ""), row.get("resolution_ref", ""))
    item_id = _public_text(raw_id, _stable_action_id("DAP", index, row.get("ag_id", ""), row.get("resolution_ref", "")))
    proof_refs = _split_piece_refs(row.get("proof_doc_ids", ""))
    status_info = _decision_status(row.get("statut", ""), bool(proof_refs))
    status = status_info["status"]
    proof_state = _proof_state(row.get("statut", ""), proof_refs)
    due_state = _due_state(row.get("echeance", ""), status)
    ag_id = _public_text(row.get("ag_id"), "AG-SANS-DATE")
    ag_date = _ag_date(row)
    source_doc_id = _public_text(row.get("source_doc_id"), "")
    source_row = documents_by_id.get(row.get("source_doc_id", ""))

    proofs: list[dict[str, object]] = []
    if proof_refs:
        proof_status = "verified" if proof_state == "verified" else "candidate"
        for proof_ref in proof_refs:
            doc_row = documents_by_id.get(proof_ref)
            proofs.append(
                _proof_card(
                    item_id=item_id,
                    proof_ref=proof_ref,
                    label=_document_label(proof_ref, doc_row, row.get("preuve_attendue") or "Preuve candidate"),
                    type_label=_document_type_label(doc_row, row.get("proof_document_types") or "Preuve"),
                    status=proof_status,
                    source_doc_id=proof_ref,
                    source_label=_document_label(proof_ref, doc_row, "Piece locale"),
                )
            )
    else:
        proofs.append(
            _proof_card(
                item_id=item_id,
                proof_ref=f"{item_id}-missing-proof",
                label=row.get("preuve_attendue") or "Preuve a demander",
                type_label=row.get("proof_document_types") or "Preuve attendue",
                status="missing",
            )
        )

    pieces: list[dict[str, object]] = []
    if source_doc_id:
        pieces.append(
            _piece_card(
                item_id=item_id,
                doc_id=source_doc_id,
                label=_document_label(source_doc_id, source_row, row.get("source_file") or "Source du vote"),
                type_label=_document_type_label(source_row, "PV AG"),
                role_label="source du vote",
                proof_relation="none",
                doc_row=source_row,
            )
        )
    for proof_ref in proof_refs:
        doc_row = documents_by_id.get(proof_ref)
        pieces.append(
            _piece_card(
                item_id=item_id,
                doc_id=proof_ref,
                label=_document_label(proof_ref, doc_row, "Piece candidate"),
                type_label=_document_type_label(doc_row, row.get("proof_document_types") or "Preuve"),
                role_label="preuve validee" if proof_state == "verified" else "preuve candidate",
                proof_relation="verified" if proof_state == "verified" else "candidate",
                doc_row=doc_row,
            )
        )
    for ref in _split_piece_refs(row.get("related_invoice_refs", "")):
        doc_row = documents_by_id.get(ref)
        pieces.append(
            _piece_card(
                item_id=item_id,
                doc_id=ref,
                label=_document_label(ref, doc_row, "Facture liee"),
                type_label=_document_type_label(doc_row, "Facture"),
                role_label="facture",
                proof_relation="candidate",
                doc_row=doc_row,
            )
        )
    for ref in _split_piece_refs(row.get("related_work_refs", "")):
        doc_row = documents_by_id.get(ref)
        pieces.append(
            _piece_card(
                item_id=item_id,
                doc_id=ref,
                label=_document_label(ref, doc_row, "Devis ou travaux lies"),
                type_label=_document_type_label(doc_row, "Devis"),
                role_label="devis",
                proof_relation="candidate",
                doc_row=doc_row,
            )
        )

    followups: list[dict[str, object]] = []
    related_requests = _split_piece_refs(row.get("related_request_ids", ""))
    if related_requests:
        followup_status = "answered_to_check" if proof_refs else "sent_waiting"
        for request_id in related_requests:
            followups.append(
                _followup_card(
                    item_id=item_id,
                    row=row,
                    proof_expected=row.get("preuve_attendue", ""),
                    status=followup_status,
                    followup_id=request_id,
                )
            )
    elif proof_state == "missing":
        followups.append(_followup_card(item_id=item_id, row=row, proof_expected=row.get("preuve_attendue", ""), status="draft"))
    elif proof_state == "candidate":
        followups.append(
            _followup_card(item_id=item_id, row=row, proof_expected=row.get("preuve_attendue", ""), status="answered_to_check")
        )

    history = [
        _history_event(
            item_id=item_id,
            occurred_on=ag_date or row.get("echeance", ""),
            event_type="creation",
            type_label="Decision inscrite",
            summary=f"{row.get('resolution_ref') or 'Resolution'} ajoutee au registre.",
            piece_ids=[source_doc_id] if source_doc_id else [],
            memory_note="Conserver la decision et son action attendue pour la passation.",
        )
    ]
    if pieces:
        history.append(
            _history_event(
                item_id=item_id,
                occurred_on=row.get("echeance", ""),
                event_type="piece_linked",
                type_label="Piece liee",
                summary=f"{len(pieces)} piece(s) liee(s) a la decision.",
                piece_ids=[str(piece.get("doc_id", "")) for piece in pieces if piece.get("doc_id")],
                memory_note="Une piece liee n'est pas toujours une preuve validee.",
            )
        )
    if proofs:
        history.append(
            _history_event(
                item_id=item_id,
                occurred_on=row.get("echeance", ""),
                event_type="proof_added" if proof_state != "missing" else "update",
                type_label="Preuve suivie",
                summary=_proof_state_label(proof_state),
                proof_ids=[str(proof.get("proof_id", "")) for proof in proofs],
                is_evidence=proof_state == "verified",
                memory_note="Preuve validee seulement apres controle explicite.",
            )
        )
    if followups:
        history.append(
            _history_event(
                item_id=item_id,
                occurred_on=row.get("echeance", ""),
                event_type="followup_sent" if related_requests else "update",
                type_label="Relance syndic",
                summary=str(followups[0].get("status_label", "Relance a suivre")),
                followup_ids=[str(followup.get("followup_id", "")) for followup in followups],
                memory_note="Noter le canal d'envoi reel hors CoproScope.",
            )
        )
    history = sorted(history, key=lambda event: str(event.get("occurred_on") or "9999-12-31"))

    priority = (row.get("priorite") or "P2").upper()
    title = _public_text(row.get("decision_text"), row.get("resolution_ref") or "Decision AG")
    action_description = _public_text(row.get("action_attendue"), "Suivre la resolution jusqu'a sa preuve.")
    next_step = action_description
    if proof_state == "missing":
        next_step = "Ajouter une preuve ou preparer une relance syndic."
    elif proof_state == "candidate":
        next_step = "Verifier la piece candidate avant de cloturer."
    elif status == "clos":
        next_step = "Conserver la trace pour la memoire de copropriete."

    item = {
        "id": item_id,
        "ag_id": ag_id,
        "ag_label": _ag_label(ag_id, ag_date),
        "ag_date": ag_date,
        "resolution_ref": _public_text(row.get("resolution_ref"), "Resolution AG"),
        "source_doc_id": source_doc_id,
        "source_file_label": _document_label(source_doc_id, source_row, row.get("source_file") or "Source locale"),
        "title": title,
        "decision_summary": title,
        "decision_source_excerpt": _public_text(row.get("decision_text"), "Texte source a verifier dans le PV."),
        "majority_label": _public_text(row.get("majority") or row.get("majorite"), "Majorite a verifier"),
        "status": status,
        "status_label": status_info["label"],
        "status_detail": status_info["detail"],
        "status_tone": status_info["tone"],
        "priority": priority,
        "priority_label": _priority_label(priority),
        "priority_reason": _priority_reason(row, proof_state),
        "owner": _public_text(row.get("responsable"), "Conseil syndical / syndic"),
        "referent": "Conseil syndical",
        "due_on": _public_text(row.get("echeance"), ""),
        "due_label": _due_label(row.get("echeance", ""), due_state),
        "due_state": due_state,
        "progress_pct": 100 if status == "clos" else 60 if proof_state == "candidate" else 20,
        "next_step": next_step,
        "action_description": action_description,
        "proof_expected": _public_text(row.get("preuve_attendue"), "Preuve attendue a preciser"),
        "proof_state": proof_state,
        "proof_state_label": _proof_state_label(proof_state),
        "proofs": proofs,
        "pieces": pieces,
        "linked_documents": pieces,
        "followups": followups,
        "syndic_followups": followups,
        "history": history,
        "history_events": history,
        "diffusion": _diffusion_for_item(status, proof_state, pieces),
        "memory": {
            "handover_note": "Action a reprendre en passation tant qu'une preuve validee manque.",
            "timeline_ref": item_id,
            "open_risk": "preuve manquante" if proof_state == "missing" else "",
            "pack_section": "Decisions AG",
            "next_review_label": "Prochaine revue CS",
        },
        "href": _route_href("/actions", selected_item_id=item_id),
        "action_followup": {
            "label": "Suivi de l'action",
            "progress_pct": 100 if status == "clos" else 60 if proof_state == "candidate" else 20,
            "next_step": next_step,
            "href": _route_href("/actions", selected_item_id=item_id, tab="action"),
        },
        # Legacy work-item fields kept for templates that still consume the older UX shape.
        "kind": "decisions",
        "tone": status_info["tone"],
        "why": _public_text(row.get("notes"), status_info["detail"]),
        "proof": {"state": proof_state, "label": _public_text(row.get("preuve_attendue"), "Preuve attendue")},
        "action": {"label": next_step, "owner": _public_text(row.get("responsable"), "Conseil syndical / syndic")},
        "source": {"module": "DecisionOps", "object_id": item_id},
    }
    return item


def _facet_options(field: str, rows: list[dict[str, object]], labels: dict[str, str] | None = None) -> list[dict[str, object]]:
    counts = Counter(str(row.get(field, "") or "non renseigne") for row in rows)
    options = []
    for value, count in sorted(counts.items(), key=lambda item: (item[0] == "non renseigne", item[0])):
        options.append(
            {
                "value": value,
                "label": (labels or {}).get(value, value),
                "count": count,
                "href": _route_href("/actions", **{field: value}),
                "is_active": False,
            }
        )
    return options


def _register_tabs(selected: dict[str, object]) -> list[dict[str, object]]:
    item_id = selected.get("id", "")
    counts = {
        "action": 1 if selected else 0,
        "preuves": len(selected.get("proofs", [])) if isinstance(selected.get("proofs"), list) else 0,
        "pieces": len(selected.get("pieces", [])) if isinstance(selected.get("pieces"), list) else 0,
        "relance": len(selected.get("followups", [])) if isinstance(selected.get("followups"), list) else 0,
        "historique": len(selected.get("history", [])) if isinstance(selected.get("history"), list) else 0,
    }
    labels = {
        "action": "Action",
        "preuves": "Preuves",
        "pieces": "Pieces liees",
        "relance": "Relance syndic",
        "historique": "Historique",
    }
    return [
        {
            "id": tab_id,
            "label": labels[tab_id],
            "count": counts[tab_id],
            "is_active": tab_id == "action",
            "href": _route_href("/actions", selected_item_id=item_id, tab=tab_id) if item_id else _route_href("/actions", tab=tab_id),
        }
        for tab_id in ["action", "preuves", "pieces", "relance", "historique"]
    ]


def _empty_registre_selected() -> dict[str, object]:
    return {
        "id": "",
        "ag_id": "",
        "resolution_ref": "",
        "source_doc_id": "",
        "source_file_label": "",
        "title": "Aucune decision selectionnee",
        "decision_summary": "",
        "decision_source_excerpt": "",
        "majority_label": "",
        "status": "empty",
        "status_label": "Aucune decision",
        "status_detail": "Importer ou ajouter un PV pour commencer le registre.",
        "status_tone": "info",
        "priority": "",
        "priority_label": "",
        "priority_reason": "",
        "owner": "",
        "referent": "",
        "due_on": "",
        "due_label": "",
        "due_state": "missing",
        "progress_pct": 0,
        "next_step": "Ajouter ou importer un PV / registre AG pour commencer.",
        "action_description": "",
        "proof_expected": "",
        "proof_state": "missing",
        "proof_state_label": "Preuve manquante",
        "proofs": [],
        "pieces": [],
        "linked_documents": [],
        "followups": [],
        "syndic_followups": [],
        "history": [],
        "history_events": [],
        "diffusion": {
            "status": "local_only",
            "label": "Prive local",
            "reason": "Aucun export prepare.",
            "allowed_audience": "Conseil syndical",
            "blocked_by": "",
        },
        "memory": {
            "handover_note": "",
            "timeline_ref": "",
            "open_risk": "",
            "pack_section": "Decisions AG",
            "next_review_label": "",
        },
        "href": _route_href("/actions"),
        "action_followup": {"label": "Suivi de l'action", "progress_pct": 0, "next_step": "", "href": _route_href("/actions")},
    }
