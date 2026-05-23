from __future__ import annotations

from ._runtime import *

def _build_ux_model(
    instance: InstanceConfig,
    year: int,
    *,
    action_items: list[dict[str, str]],
    action_summary: dict[str, object],
    evidence_summary: dict[str, object],
    cockpit_alerts: list[dict[str, object]],
    accounting: dict[str, object],
    decisions: dict[str, object],
    incidents: dict[str, object],
    privacy: dict[str, object],
    documents: dict[str, object],
    piece_workshop: dict[str, object],
    trust_summary: dict[str, object],
) -> dict[str, object]:
    ux_items = [_ux_work_item(action) for action in action_items]
    by_status = action_summary.get("by_status") if isinstance(action_summary.get("by_status"), dict) else {}
    by_priority = action_summary.get("by_priority") if isinstance(action_summary.get("by_priority"), dict) else {}
    scope_counts = action_summary.get("scope_counts") if isinstance(action_summary.get("scope_counts"), dict) else {}
    decision_summary = decisions.get("summary") if isinstance(decisions.get("summary"), dict) else {}
    incident_summary = incidents.get("summary") if isinstance(incidents.get("summary"), dict) else {}
    privacy_summary = privacy.get("review_summary") if isinstance(privacy.get("review_summary"), dict) else {}
    document_actionable = documents.get("actionable") if isinstance(documents.get("actionable"), dict) else {}
    document_summary = document_actionable.get("summary") if isinstance(document_actionable.get("summary"), dict) else {}
    piece_summary = piece_workshop.get("summary") if isinstance(piece_workshop.get("summary"), dict) else {}
    comptes_model = _build_comptes_ux_model(instance, year, accounting)
    pieces_model = _build_pieces_ux_model(
        piece_workshop=piece_workshop,
        documents=documents,
        action_items=action_items,
        comptes=comptes_model,
    )
    pieces_model_summary = pieces_model.get("summary") if isinstance(pieces_model.get("summary"), dict) else {}
    p1_count = int(by_priority.get("P0", 0) or 0) + int(by_priority.get("P1", 0) or 0)
    missing_pieces = int(pieces_model_summary.get("missing_count") or 0) + int(pieces_model_summary.get("to_deposit_count") or 0)
    syndic_count = int(scope_counts.get("syndic", 0) or by_status.get("a_demander", 0) or 0)
    ag_count = int(decision_summary.get("open") or decision_summary.get("missing_proofs") or 0)
    risk_count = len(cockpit_alerts) + int(privacy_summary.get("blocked") or 0)

    todo_cards = [
        {
            "id": "late-actions",
            "label": "Actions en retard",
            "count": p1_count,
            "subtitle": "Prioritaires ou bloquees",
            "tone": "danger" if p1_count else "ok",
            "icon": "!",
            "href": "/actions?priority=P1",
        },
        {
            "id": "missing-pieces",
            "label": "Pieces manquantes",
            "count": missing_pieces,
            "subtitle": "A demander ou rattacher",
            "tone": "warn" if missing_pieces else "ok",
            "icon": "doc",
            "href": "/pieces?proof=missing",
        },
        {
            "id": "syndic-followups",
            "label": "Demandes syndic",
            "count": syndic_count,
            "subtitle": "Relances et reponses attendues",
            "tone": "danger" if syndic_count else "ok",
            "icon": "msg",
            "href": "/actions?scope=syndic",
        },
        {
            "id": "ag-deadlines",
            "label": "Echeances AG",
            "count": ag_count,
            "subtitle": "Decisions et preuves avant AG",
            "tone": "info" if ag_count else "ok",
            "icon": "cal",
            "href": "/chantiers?section=ag",
        },
        {
            "id": "risk-alerts",
            "label": "Alertes et risques",
            "count": risk_count,
            "subtitle": "Diffusion, incident ou blocage",
            "tone": "danger" if risk_count else "ok",
            "icon": "risk",
            "href": "/actions?status=a_revoir",
        },
    ]

    total_doc_slots = max(
        int(document_summary.get("total") or 0),
        int(document_summary.get("present") or 0) + missing_pieces,
        1,
    )
    completion_pct = max(0, min(100, round(100 * (total_doc_slots - missing_pieces) / total_doc_slots)))
    missing_items = [
        item
        for item in pieces_model.get("missing", [])
        if isinstance(item, dict)
    ][:4]
    syndic_items = [item for item in ux_items if item.get("lane") == "waiting_syndic"][:4]
    risk_rows = []
    for alert in cockpit_alerts[:6]:
        risk_rows.append(
            {
                "level": alert.get("severity", "P2"),
                "label": alert.get("title", "A surveiller"),
                "tone": _ux_tone(str(alert.get("severity", "P2"))),
                "subject": _public_text(alert.get("title"), "Point a surveiller"),
                "detail": _public_text(alert.get("detail"), "Verifier le point avec les preuves disponibles."),
                "impact": "Action CS requise",
                "due_or_detected": "A traiter maintenant",
                "status_label": "Ouvert",
                "status_tone": "warn",
                "href": alert.get("href") or "/actions",
            }
        )
    if not risk_rows:
        risk_rows.append(
            {
                "level": "OK",
                "label": "Aucune alerte critique",
                "tone": "ok",
                "subject": "Surveillance courante",
                "detail": "Aucun blocage prioritaire detecte dans les registres charges.",
                "impact": "Continuer le suivi",
                "due_or_detected": "Aujourd'hui",
                "status_label": "OK",
                "status_tone": "ok",
                "href": "/actions",
            }
        )

    accounting_before_ag = accounting.get("before_ag") if isinstance(accounting.get("before_ag"), dict) else {}
    accounting_score = max(
        0,
        min(
            100,
            int(accounting_before_ag.get("ok") or 0) * 10
            + int(accounting_before_ag.get("to_confirm") or 0) * 3
            - int(accounting_before_ag.get("blocking") or 0) * 5,
        ),
    )
    decision_rows = decisions.get("open_rows") if isinstance(decisions.get("open_rows"), list) else []
    ag_deadlines = [
        {
            "day": (row.get("echeance") or "A fixer")[-2:] if isinstance(row, dict) else "A fixer",
            "month": (row.get("echeance") or "AG")[:7] if isinstance(row, dict) else "AG",
            "title": _public_text(row.get("resolution_ref") or row.get("decision_action_id"), "Decision AG a suivre") if isinstance(row, dict) else "Decision AG",
            "subtitle": _public_text(row.get("action_attendue") or row.get("preuve_attendue"), "Preuve ou action attendue") if isinstance(row, dict) else "Preuve attendue",
            "relative_label": "Avant prochaine AG",
            "href": "/chantiers?section=ag",
        }
        for row in decision_rows[:3]
        if isinstance(row, dict)
    ]
    if not ag_deadlines:
        ag_deadlines = [
            {
                "day": "AG",
                "month": str(year),
                "title": "Preparation AG",
                "subtitle": "Verifier les decisions ouvertes et les pieces attendues.",
                "relative_label": "A planifier",
                "href": "/chantiers?section=ag",
            }
        ]

    shell = {
        "app_title": "CoproScope",
        "page_title": "Cockpit Conseil Syndical",
        "active_page": "overview",
        "search_placeholder": "Rechercher document, action, decision, fournisseur...",
        "notification_count": len(cockpit_alerts),
        "sharing_mode_label": "Mode prive local",
        "sharing_mode_status": "Aucune synchronisation externe lancee",
        "top_actions": [{"label": "Nouvelle demande", "href": "/demandes", "kind": "primary", "icon": "+"}],
        "nav_sections": [
            {
                "label": "Travail du CS",
                "items": [
                    _ux_nav_item("Tableau de bord", "/", "overview", "overview", icon="home"),
                    _ux_nav_item("A traiter", "/actions", "actions", "overview", icon="check", count=action_summary.get("total", 0)),
                    _ux_nav_item("Pieces manquantes", "/pieces?proof=missing", "pieces", "overview", icon="doc", count=missing_pieces),
                    _ux_nav_item("Demandes syndic", "/actions?scope=syndic", "actions", "overview", icon="msg", count=syndic_count),
                    _ux_nav_item("AG", "/chantiers?section=ag", "workstreams", "overview", icon="cal", count=ag_count),
                ],
            },
            {
                "label": "Dossiers",
                "items": [
                    _ux_nav_item("Controle comptes", "/comptes", "accounting", "overview", icon="chart", count=scope_counts.get("comptes", 0)),
                    _ux_nav_item("Documents", "/documents", "documents", "overview", icon="folder"),
                    _ux_nav_item("Memoire copropriete", "/chantiers", "workstreams", "overview", icon="timeline"),
                    _ux_nav_item("Diffusion et masquage", "/confidentialite", "privacy", "overview", icon="lock", count=privacy_summary.get("blocked", 0)),
                ],
            },
            {
                "label": "Coffre",
                "items": [
                    _ux_nav_item("Droits et roles", "/gouvernance", "governance", "overview", icon="users"),
                    _ux_nav_item("Depot local", "/depot", "depot", "overview", icon="inbox"),
                ],
            },
        ],
    }
    registre_model = _build_registre_model(
        instance,
        year,
        ux_items=ux_items,
        decisions=decisions,
        documents=documents,
    )
    action_detail = _action_detail_model(registre_model)
    priority_views = _build_priority_views(action_items=action_items, piece_workshop=piece_workshop, pieces_model=pieces_model)
    memoire_model = _build_memoire_ux_model(
        instance,
        year,
        ux_items=ux_items,
        accounting=accounting,
        decisions=decisions,
        incidents=incidents,
        privacy=privacy,
        documents=documents,
        piece_workshop=piece_workshop,
    )
    passation_export = _build_passation_export_model(
        year=year,
        memoire=memoire_model,
        priority_views=priority_views,
        action_detail=action_detail,
    )
    # Mark active page in templates that pass a different `page` value by keeping the
    # page ids stable; the template recomputes `aria-current` from `page`.
    ux_model = {
        "schema_version": "coproscope.ux.v1",
        "context": {
            "coffre": _public_text(instance.display_name, "Copropriete"),
            "exercise": year,
            "role": "Conseil syndical",
            "sharing_mode": "local",
        },
        "facets": {
            "lanes": dict(Counter(str(item.get("lane", "")) for item in ux_items)),
            "statuses": dict(Counter(str(item.get("status", "")) for item in ux_items)),
            "priorities": dict(Counter(str(item.get("priority", "")) for item in ux_items)),
        },
        "shell": shell,
        "work_items": ux_items,
        "cockpit": {
            "as_of_label": f"Situation {year}",
            "intro_title": "Ce qui demande attention maintenant",
            "summary_cards": todo_cards,
            "now": ux_items[:5],
            "lanes": {
                "this_week": [item for item in ux_items if item.get("lane") == "this_week"][:4],
                "waiting_syndic": syndic_items,
                "proofs_to_verify": [item for item in ux_items if item.get("lane") == "proofs_to_verify"][:4],
                "diffusion_risk": [item for item in ux_items if item.get("lane") == "diffusion_risk"][:4],
                "before_ag": ag_deadlines,
            },
            "missing_documents": {
                "completion_pct": completion_pct,
                "top_missing": [
                    {
                        "label": _public_text(item.get("expected_piece") or item.get("piece"), "Piece attendue"),
                        "count": 1,
                        "href": item.get("href") or "/pieces",
                        "reason": _public_text(item.get("next_step"), "Demander ou rattacher la piece."),
                    }
                    for item in missing_items
                ],
                "detail_href": "/pieces?proof=missing",
            },
            "syndic_requests": {
                "tabs": [
                    {"id": "waiting", "label": "En attente", "count": syndic_count, "is_active": True},
                    {"id": "running", "label": "En cours", "count": int(by_status.get("a_traiter", 0) or 0), "is_active": False},
                    {"id": "done", "label": "Resolues", "count": int(by_status.get("clos", 0) or 0), "is_active": False},
                ],
                "items": syndic_items,
                "all_href": "/actions?scope=syndic",
            },
            "ag": {
                "deadlines": ag_deadlines,
                "calendar_href": "/chantiers?section=ag",
            },
            "accounting": {
                "score": accounting_score,
                "conformes_count": int(accounting_before_ag.get("ok") or 0),
                "watch_count": int(accounting_before_ag.get("to_confirm") or 0),
                "anomaly_count": int(accounting_before_ag.get("blocking") or 0),
                "watch_items": [item for item in ux_items if item.get("kind") == "comptes"][:3],
                "detail_href": "/comptes",
            },
            "risk_alerts": risk_rows,
            "trust": {
                "cards": trust_summary.get("cards", []),
                "label": "Coffre local",
                "sync_label": "Statut sync a verifier",
                "sync_detail": "Cette page reste locale: aucune synchronisation externe n'est lancee depuis le cockpit.",
            },
            "empty_state": {
                "is_visible": not bool(ux_items),
                "title": "Coffre pret a alimenter",
                "detail": "Ajoutez des pieces ou importez des registres pour faire apparaitre les premieres actions.",
                "primary_action": {"label": "Ajouter une piece", "href": "/depot", "kind": "deposit"},
                "secondary_action": {"label": "Voir les chantiers", "href": "/chantiers", "kind": "memory"},
            },
        },
        "registre": registre_model,
        "priority_views": priority_views,
        "pieces": pieces_model,
        "action_detail": action_detail,
        "comptes": comptes_model,
        "memoire": memoire_model,
        "event_detail": memoire_model.get("event_detail", {}),
        "passation_export": passation_export,
        "passation_export_preview": passation_export,
    }
    sanitized = _sanitize_ux_public(ux_model)
    if isinstance(sanitized, dict):
        cockpit = sanitized.get("cockpit")
        if isinstance(cockpit, dict) and isinstance(cockpit.get("syndic_requests"), dict):
            cockpit["syndic_requests"] = _JinjaItemsDict(cockpit["syndic_requests"])
    return sanitized
