from __future__ import annotations

from ._runtime import *

def _build_memoire_ux_model(
    instance: InstanceConfig,
    year: int,
    *,
    ux_items: list[dict[str, object]],
    accounting: dict[str, object],
    decisions: dict[str, object],
    incidents: dict[str, object],
    privacy: dict[str, object],
    documents: dict[str, object],
    piece_workshop: dict[str, object],
) -> dict[str, object]:
    decision_rows = decisions.get("rows") if isinstance(decisions.get("rows"), list) else []
    incident_rows = incidents.get("rows") if isinstance(incidents.get("rows"), list) else []
    document_table = documents.get("documents")
    document_rows = document_table.rows if isinstance(document_table, DataTable) else []
    document_actionable = documents.get("actionable") if isinstance(documents.get("actionable"), dict) else {}
    document_summary = document_actionable.get("summary") if isinstance(document_actionable.get("summary"), dict) else {}
    privacy_rows = privacy.get("review_rows") if isinstance(privacy.get("review_rows"), list) else []
    privacy_summary = privacy.get("review_summary") if isinstance(privacy.get("review_summary"), dict) else {}
    decision_summary = decisions.get("summary") if isinstance(decisions.get("summary"), dict) else {}
    incident_summary = incidents.get("summary") if isinstance(incidents.get("summary"), dict) else {}
    piece_summary = piece_workshop.get("summary") if isinstance(piece_workshop.get("summary"), dict) else {}
    accounting_before_ag = accounting.get("before_ag") if isinstance(accounting.get("before_ag"), dict) else {}

    timeline: list[dict[str, object]] = []

    for index, row in enumerate(decision_rows, start=1):
        if not isinstance(row, dict):
            continue
        category_id = "travaux" if row.get("related_work_refs") else "comptes" if row.get("related_invoice_refs") else "ag"
        category = _memoire_category_option(category_id)
        has_missing_proof = (row.get("statut") or "").upper() == "PREUVE_A_DEMANDER" or not row.get("proof_doc_ids")
        status = _memoire_event_status(row.get("statut", ""), has_missing_proof=has_missing_proof)
        date_iso = _ag_date(row) or _date_from_text(row.get("echeance", "")) or ""
        event_id = _stable_action_id(
            "MEM-DEC",
            index,
            row.get("decision_action_id", ""),
            row.get("ag_id", ""),
            row.get("resolution_ref", ""),
        )
        title = _public_text(row.get("decision_text"), row.get("resolution_ref") or "Decision AG")
        timeline.append(
            {
                "id": event_id,
                "date_iso": date_iso,
                "date_label": _date_label(date_iso, "Date a confirmer"),
                "year": int(date_iso[:4]) if date_iso[:4].isdigit() else year,
                "dot_tone": category["tone"],
                "icon": category["icon"],
                "title": title,
                "subtitle": _public_text(row.get("action_attendue") or row.get("preuve_attendue"), "Action ou preuve a reprendre."),
                "kind": category_id,
                "category_label": category["label"],
                "category_tone": category["tone"],
                "status": status["status"],
                "status_label": status["label"],
                "is_open_topic": status["status"] != "clos",
                "risk_level": status["risk"],
                "restriction_level": "conseil_syndical",
                "restriction_label": "Conseil syndical",
                "href": _route_href("/chantiers", selected=event_id),
                "detail_href": _route_href("/chantiers", selected=event_id),
                "document_refs": _memoire_safe_refs(row.get("source_doc_id"), row.get("proof_doc_ids")),
                "action_refs": _memoire_safe_refs(row.get("decision_action_id")),
                "decision_refs": _memoire_safe_refs(row.get("decision_action_id")),
                "next_action": _public_text(row.get("action_attendue"), "Rattacher la preuve attendue ou relancer le syndic."),
                "passation_note": "Decision a reprendre en passation tant que la preuve ou l'action reste ouverte.",
                "can_export": status["status"] == "clos",
            }
        )

    for index, row in enumerate(incident_rows, start=1):
        if not isinstance(row, dict):
            continue
        category = _memoire_category_option("sinistres")
        is_open = incidentops.is_open_incident(row)
        priority = (row.get("priority") or "P2").upper()
        date_iso = _date_from_text(row.get("date_signalement", "")) or _date_from_text(row.get("action_due_date", "")) or ""
        event_id = _stable_action_id("MEM-INC", index, row.get("incident_id", ""), row.get("date_signalement", ""))
        title_parts = [row.get("lieu", ""), row.get("incident_id", "")]
        title = _public_text(" - ".join(part for part in title_parts if part), "Incident a suivre")
        timeline.append(
            {
                "id": event_id,
                "date_iso": date_iso,
                "date_label": _date_label(date_iso, "Date a confirmer"),
                "year": int(date_iso[:4]) if date_iso[:4].isdigit() else year,
                "dot_tone": "red" if priority in {"P0", "P1"} else category["tone"],
                "icon": category["icon"],
                "title": title,
                "subtitle": _public_text(row.get("description") or row.get("next_action"), "Incident a documenter."),
                "kind": "sinistres",
                "category_label": category["label"],
                "category_tone": category["tone"],
                "status": "ouvert" if is_open else "clos",
                "status_label": "Ouvert" if is_open else "Clos",
                "is_open_topic": is_open,
                "risk_level": "high" if priority in {"P0", "P1"} else "medium" if is_open else "low",
                "restriction_level": "conseil_syndical",
                "restriction_label": "Diffusion limitee",
                "href": _route_href("/chantiers", selected=event_id),
                "detail_href": _route_href("/chantiers", selected=event_id),
                "document_refs": _memoire_safe_refs(row.get("doc_ids"), row.get("closure_proof_ref")),
                "action_refs": _memoire_safe_refs(row.get("incident_id")),
                "decision_refs": [],
                "next_action": _public_text(row.get("next_action"), "Obtenir la preuve de cloture."),
                "passation_note": "Ne pas clore la passation sans preuve de resolution ou prochaine action claire.",
                "can_export": not is_open,
            }
        )

    for index, row in enumerate(document_rows[:30], start=1):
        if not isinstance(row, dict):
            continue
        category_id = _memoire_category_from_document(row)
        category = _memoire_category_option(category_id)
        review_status = row.get("privacy_review_status") or row.get("review_required") or row.get("publication_form") or ""
        needs_review = str(review_status).upper() in {"YES", "A_ARBITRER", "BLOQUE"} or bool(row.get("required_transformations"))
        date_iso = _date_from_text(row.get("suspected_date", "")) or _date_from_text(row.get("last_modified", "")) or ""
        event_id = _stable_action_id("MEM-DOC", index, row.get("doc_id", ""), row.get("file_name", ""))
        timeline.append(
            {
                "id": event_id,
                "date_iso": date_iso,
                "date_label": _date_label(date_iso, "Date a confirmer"),
                "year": int(date_iso[:4]) if date_iso[:4].isdigit() else year,
                "dot_tone": "orange" if needs_review else category["tone"],
                "icon": category["icon"],
                "title": _document_label(row.get("doc_id", ""), row, "Document cle"),
                "subtitle": _document_type_label(row, "Document a transmettre"),
                "kind": category_id,
                "category_label": category["label"],
                "category_tone": category["tone"],
                "status": "a_confirmer" if needs_review else "clos",
                "status_label": "A verifier" if needs_review else "Clos",
                "is_open_topic": needs_review,
                "risk_level": "medium" if needs_review else "low",
                "restriction_level": "a_verifier" if needs_review else "coproprietaires",
                "restriction_label": "A verifier avant partage" if needs_review else "Transmissible apres controle",
                "href": _route_href("/chantiers", selected=event_id),
                "detail_href": _route_href("/chantiers", selected=event_id),
                "document_refs": _memoire_safe_refs(row.get("doc_id")),
                "action_refs": [],
                "decision_refs": [],
                "next_action": "Verifier la diffusion avant de transmettre." if needs_review else "Conserver dans les documents de passation.",
                "passation_note": "Document utile pour comprendre l'historique de la copropriete.",
                "can_export": not needs_review,
            }
        )

    accounting_open = int(accounting_before_ag.get("blocking") or 0) + int(accounting_before_ag.get("to_confirm") or 0)
    if accounting_open or int(accounting_before_ag.get("ok") or 0):
        category = _memoire_category_option("comptes")
        event_id = _stable_action_id("MEM-COMP", 0, str(year), str(accounting_open))
        timeline.append(
            {
                "id": event_id,
                "date_iso": f"{year}-12-31",
                "date_label": f"Exercice {year}",
                "year": year,
                "dot_tone": "orange" if accounting_open else category["tone"],
                "icon": category["icon"],
                "title": f"Controle des comptes {year}",
                "subtitle": "Points comptables a traiter avant AG." if accounting_open else "Rapprochements comptables disponibles.",
                "kind": "comptes",
                "category_label": category["label"],
                "category_tone": category["tone"],
                "status": "ouvert" if accounting_open else "clos",
                "status_label": "Ouvert" if accounting_open else "Clos",
                "is_open_topic": bool(accounting_open),
                "risk_level": "high" if int(accounting_before_ag.get("blocking") or 0) else "medium" if accounting_open else "low",
                "restriction_level": "conseil_syndical",
                "restriction_label": "Conseil syndical",
                "href": _route_href("/comptes"),
                "detail_href": _route_href("/comptes"),
                "document_refs": [],
                "action_refs": [],
                "decision_refs": [],
                "next_action": "Traiter les questions comptes et conserver les preuves utiles.",
                "passation_note": "Reprendre le statut des comptes dans le pack de passation.",
                "can_export": not accounting_open,
            }
        )

    timeline.sort(key=lambda event: str(event.get("date_iso") or "0000-00-00"), reverse=True)
    visible_timeline = timeline[:12]
    selected_event = _memoire_event_detail(visible_timeline[0]) if visible_timeline else {}
    selected_event_id = selected_event.get("id") if isinstance(selected_event, dict) else ""
    for event in visible_timeline:
        event["is_selected"] = bool(selected_event_id and event.get("id") == selected_event_id)
        event["aria_label"] = "Evenement selectionne" if event["is_selected"] else "Ouvrir le detail de cet evenement"
    open_topics = [event for event in timeline if event.get("is_open_topic")]
    restricted_count = len([event for event in timeline if event.get("restriction_level") in {"a_verifier", "conseil_syndical"} and not event.get("can_export")])
    missing_proof_count = int(decision_summary.get("missing_proofs") or 0) + int(piece_summary.get("without_local_proof") or 0)
    syndic_waiting = len([item for item in ux_items if item.get("lane") == "waiting_syndic"])
    document_missing = int(document_summary.get("to_request") or 0)
    privacy_attention = int(privacy_summary.get("to_arbitrate") or 0) + int(privacy_summary.get("blocked") or 0)
    open_incidents = int(incident_summary.get("open") or 0)
    open_works = len(
        [
            row
            for row in decision_rows
            if isinstance(row, dict)
            and row.get("related_work_refs")
            and row.get("statut") not in {"OK", "TRAITE", "CLOTURE", "CLOS", "TERMINE"}
        ]
    )
    contract_missing = len(
        [
            row
            for row in (document_actionable.get("to_request") if isinstance(document_actionable.get("to_request"), list) else [])
            if isinstance(row, dict)
            and "contrat" in " ".join([row.get("lot", ""), row.get("expected_piece", ""), row.get("expected_label", ""), row.get("subject", "")]).lower()
        ]
    )
    checklist_specs = [
        ("contrats", "Contrats en cours a suivre", contract_missing),
        ("travaux", "Travaux en cours ou a venir", open_works),
        ("sinistres", "Litiges et sinistres en cours", open_incidents),
        ("comptes", "Points de vigilance financiere", accounting_open),
        ("demandes", "Demandes en attente au syndic", syndic_waiting),
        ("documents", "Documents cles a transmettre", document_missing + privacy_attention),
    ]
    checklist = [
        {
            "id": item_id,
            "label": label,
            "is_done": count == 0,
            "needs_attention": count > 0,
            "alert_label": "A traiter" if count else "Pret",
            "count": count,
            "href": _route_href("/chantiers", categorie=item_id, statut="ouvert") if count else _route_href("/chantiers", categorie=item_id),
        }
        for item_id, label, count in checklist_specs
    ]
    completed_count = len([item for item in checklist if item["is_done"]])
    total_count = len(checklist)
    progress_pct = round(100 * completed_count / total_count) if total_count else 0

    transmit_items: list[dict[str, object]] = []
    for row in document_rows[:12]:
        if not isinstance(row, dict):
            continue
        doc_id = _public_text(row.get("doc_id"), "")
        review_status = str(row.get("privacy_review_status") or row.get("review_required") or "").upper()
        needs_review = review_status in {"YES", "A_ARBITRER", "BLOQUE"} or bool(row.get("required_transformations"))
        updated_on = _date_from_text(row.get("suspected_date", "")) or _date_from_text(row.get("last_modified", ""))
        transmit_items.append(
            {
                "id": doc_id or _stable_action_id("DOC-MEM", 0, row.get("file_name", "")),
                "title": _document_label(doc_id, row, "Document de passation"),
                "file_type": _public_text((row.get("extension") or "doc").upper(), "DOC"),
                "updated_label": f"Mis a jour le {_date_label(updated_on, 'date a confirmer')}",
                "icon": "file",
                "href": _route_href("/documents", doc_id=doc_id) if doc_id else _route_href("/documents"),
                "download_href": _route_href("/documents", doc_id=doc_id, download=1) if doc_id and not needs_review else "",
                "diffusion_label": "A verifier avant partage" if needs_review else "Transmissible apres controle",
                "restriction_label": "Diffusion a verifier" if needs_review else "",
                "can_download": bool(doc_id and not needs_review),
            }
        )

    last_event_label = str(visible_timeline[0].get("date_label", "Aucune date")) if visible_timeline else "Aucun evenement"
    summary = {
        "event_count": len(timeline),
        "visible_event_count": len(visible_timeline),
        "open_topics_count": len(open_topics),
        "handover_completed_count": completed_count,
        "handover_total_count": total_count,
        "handover_progress_pct": progress_pct,
        "transmit_count": len(transmit_items),
        "diffusion_limited_count": restricted_count,
        "missing_proof_count": missing_proof_count,
        "last_event_label": last_event_label,
    }
    category_labels = {key: value["label"] for key, value in MEMOIRE_CATEGORY_INFO.items()}
    export_status = "blocked" if privacy_attention else "warning" if restricted_count or open_topics else "ready"
    omissions = [
        {
            "id": _stable_action_id("OMIT-MEM", index, str(event.get("id", ""))),
            "label": event.get("title", "Element omis"),
            "reason": "Diffusion a verifier",
            "href": event.get("href", _route_href("/chantiers")),
        }
        for index, event in enumerate([event for event in timeline if not event.get("can_export")][:8], start=1)
    ]
    handover_checklist = [
        {"label": item["label"], "done": item["is_done"], "href": item["href"]}
        for item in checklist
    ]
    return {
        "context": {
            "route": "/chantiers",
            "visual_name": "Memoire de copropriete",
            "title": "Memoire de copropriete",
            "subtitle": "L'historique utile de l'immeuble, les sujets ouverts et les preuves a transmettre.",
            "active_nav_label": "Memoire copropriete",
            "coffre": _public_text(instance.display_name, "Copropriete"),
            "role": "Conseil syndical",
            "exercise": year,
            "as_of_label": f"Situation {year}",
            "default_period": "10ans",
        },
        "summary": summary,
        "toolbar": {
            "search_placeholder": "Rechercher un evenement, un contrat, un document...",
            "query": "",
            "active_period": "10ans",
            "period_options": [
                {"id": "5ans", "label": "5 ans", "href": _route_href("/chantiers", periode="5ans"), "is_active": False},
                {"id": "10ans", "label": "10 ans", "href": _route_href("/chantiers", periode="10ans"), "is_active": True},
                {"id": "tout", "label": "Tout", "href": _route_href("/chantiers", periode="tout"), "is_active": False},
            ],
            "active_filters_count": 0,
            "result_count": len(visible_timeline),
        },
        "filters": {
            "categories": _memoire_filter_options(timeline, "kind", labels=category_labels, route_field="categorie"),
            "statuses": _memoire_filter_options(timeline, "status", labels={"ouvert": "Ouvert", "clos": "Clos", "a_confirmer": "A confirmer"}, route_field="statut"),
            "diffusion": _memoire_filter_options(
                timeline,
                "restriction_level",
                labels={
                    "coproprietaires": "Transmissible",
                    "a_verifier": "A verifier",
                    "conseil_syndical": "Conseil syndical",
                },
                route_field="diffusion",
            ),
            "reset_href": _route_href("/chantiers"),
        },
        "timeline": visible_timeline,
        "selected_event": selected_event,
        "event_detail": selected_event,
        "passation": {
            "title": "Passation CS",
            "description": "Preparez la transmission des informations aux nouveaux membres du conseil syndical.",
            "completed_count": completed_count,
            "total_count": total_count,
            "progress_pct": progress_pct,
            "open_topics_count": len(open_topics),
            "detail_href": _route_href("/chantiers", panel="passation"),
            "checklist": checklist,
            "open_topics": [
                {
                    "id": event.get("id", ""),
                    "label": event.get("category_label", "Memoire"),
                    "title": event.get("title", "Sujet ouvert"),
                    "next_step": event.get("next_action", "Verifier la prochaine action."),
                    "severity": "P1" if event.get("risk_level") == "high" else "P2",
                    "href": event.get("href", _route_href("/chantiers")),
                }
                for event in open_topics[:8]
            ],
        },
        "transmit": {
            "title": "A transmettre",
            "count": len(transmit_items),
            "all_href": _route_href("/chantiers", panel="documents"),
            "items": transmit_items[:5],
        },
        "pack": {
            "id": f"passation-{year}",
            "title": "Pack passation",
            "scope": "Memoire de copropriete, sujets ouverts, preuves essentielles et restrictions de diffusion",
            "status": "partiel" if omissions else "pret",
            "status_label": "Pret avec omissions" if omissions else "Pret a relire",
            "generated_at_label": "Genere depuis les donnees locales",
            "source_of_truth": False,
            "watermark": "export derive, non source collaborative",
            "included_sections": ["Sujets ouverts", "Timeline", "Documents cles", "Restrictions", "Prochaines actions"],
            "omissions": omissions,
            "latest_export": {
                "json_href": _route_href("/exports/passation.json"),
                "text_href": _route_href("/exports/passation.txt"),
                "preview_href": _route_href("/chantiers", panel="export"),
            },
            "safety": {
                "has_local_path": False,
                "has_unreviewed_content": False,
                "blocked_reason": "Diffusion a arbitrer" if export_status == "blocked" else "",
            },
        },
        "export": {
            "title": "Exporter la passation",
            "watermark": "export derive, non source collaborative",
            "source_of_truth": False,
            "json_href": _route_href("/exports/passation.json"),
            "text_href": _route_href("/exports/passation.txt"),
            "preview_href": _route_href("/chantiers", panel="export"),
            "status": export_status,
            "disabled": export_status == "blocked",
            "disabled_reason": "Arbitrer la diffusion avant export." if export_status == "blocked" else "",
            "formats": [
                {"id": "json", "label": "Passation JSON", "href": _route_href("/exports/passation.json")},
                {"id": "text", "label": "Passation texte", "href": _route_href("/exports/passation.txt")},
                {"id": "preview", "label": "Apercu de passation", "href": _route_href("/chantiers", panel="export")},
            ],
            "omissions": omissions,
        },
        "empty_states": {
            "no_event": {
                "is_visible": not bool(timeline),
                "label": "Aucun evenement dans la memoire. Importer les registres ou rattacher des preuves pour commencer.",
                "href": _route_href("/depot"),
            },
            "event_not_found": {
                "is_visible": False,
                "label": "Evenement introuvable dans la projection courante.",
                "href": _route_href("/chantiers"),
            },
            "passation_empty": {
                "is_visible": not bool(open_topics) and completed_count == total_count,
                "label": "Passation a preparer: verifier les documents cles et les sujets ouverts.",
                "href": _route_href("/chantiers", panel="passation"),
            },
            "transmit_empty": {
                "is_visible": not bool(transmit_items),
                "label": "Aucun document transmissible charge pour la passation.",
                "href": _route_href("/documents"),
            },
            "export_blocked": {
                "is_visible": export_status == "blocked",
                "label": "Export bloque tant que la diffusion n'est pas arbitree.",
                "href": _route_href("/confidentialite"),
            },
        },
        "open_topics": open_topics[:12],
        "handover_checklist": handover_checklist,
    }
