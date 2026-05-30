from __future__ import annotations

from ._runtime import *

def _workstreams(decisions: dict[str, object], incidents: dict[str, object]) -> list[dict[str, object]]:
    decision_summary = decisions.get("summary") if isinstance(decisions.get("summary"), dict) else {}
    incident_summary = incidents.get("summary") if isinstance(incidents.get("summary"), dict) else {}
    decision_register = decisions.get("register")
    incident_register = incidents.get("register")
    decisions_total = int(decision_summary.get("total") or 0)
    missing_proofs = int(decision_summary.get("missing_proofs") or 0)
    open_incidents = int(incident_summary.get("open") or 0)
    incident_incomplete = int(incident_summary.get("incomplete") or 0)
    return [
        {
            "label": "Decisions AG",
            "status": _status(
                bool(decisions_total),
                bool(isinstance(decision_register, DataTable) and decision_register.exists),
            ),
            "detail": f"{decisions_total} decisions suivies, {missing_proofs} preuves manquantes.",
            "next": "Demander les preuves manquantes et confirmer les resolutions issues de convocations.",
            "items": decisions.get("items", [])[:5] if isinstance(decisions.get("items"), list) else [],
        },
        {
            "label": "Travaux suivis",
            "status": STATUS_WORKING,
            "detail": "Suivre devis, assurances, reception, garanties et ecarts travaux.",
            "next": "Ouvrir Travaux suivis pour verifier preuve manquante, blocage et partage possible.",
            "items": [],
        },
        {
            "label": "IncidentOps",
            "status": _status(
                bool(open_incidents),
                bool(isinstance(incident_register, DataTable) and incident_register.exists),
            ),
            "detail": f"{open_incidents} incidents ouverts, {incident_incomplete} fiches incompletes.",
            "next": "Relancer les responsables et obtenir une preuve de cloture.",
            "items": incidents.get("open_rows", [])[:5] if isinstance(incidents.get("open_rows"), list) else [],
        },
        {
            "label": "ContractOps",
            "status": STATUS_NOT_STARTED,
            "detail": "Mettre les contrats sous surveillance : echeance, obligations, clauses, attestations.",
            "next": "Extraire une fiche contrat depuis DocOps.",
            "items": [],
        },
        {
            "label": "CommsOps",
            "status": STATUS_PARTIAL,
            "detail": "Produire des syntheses diffusables, biffees ou agregees.",
            "next": "Brancher PrivacyOps et les rapports existants.",
            "items": [],
        },
        {
            "label": "Passation CS",
            "status": STATUS_NOT_STARTED,
            "detail": "Generer un dossier nouveau conseil syndical : sujets ouverts, risques, calendrier, acces.",
            "next": "Composer le pack depuis les priorites du cockpit.",
            "items": [],
        },
    ]


def build_dashboard_model(instance: InstanceConfig, year: int = 2025) -> dict[str, object]:
    documents = _documents_model(instance)
    accounting = _accounting_model(instance, year)
    privacy = _privacy_model(instance)
    decisions = _decision_model(instance)
    incidents = _incident_model(instance)
    deposits = _deposits_model(instance)

    summary = accounting["summary"] if isinstance(accounting["summary"], dict) else {}
    non_matches = accounting["non_matches"]
    priority_controls = accounting["priority_controls"]
    controls_p1 = accounting["controls_p1"]
    review_rows = privacy["review_rows"]
    docops_actionable = documents.get("actionable") if isinstance(documents.get("actionable"), dict) else {}
    docops_summary = docops_actionable.get("summary") if isinstance(docops_actionable, dict) else {}
    decision_summary = decisions.get("summary") if isinstance(decisions.get("summary"), dict) else {}
    incident_summary = incidents.get("summary") if isinstance(incidents.get("summary"), dict) else {}
    priority_control_total = (
        priority_controls.count
        if isinstance(priority_controls, DataTable) and priority_controls.count
        else len(controls_p1) if isinstance(controls_p1, list) else 0
    )
    action_items = _build_action_items(documents, accounting, privacy, decisions, incidents)
    preview_actions = action_items[:13]
    action_summary = _action_summary(action_items, len(preview_actions))
    piece_workshop = _piece_workshop_model(documents, decisions, incidents)
    piece_workshop_summary = (
        piece_workshop["summary"] if isinstance(piece_workshop.get("summary"), dict) else {}
    )

    priorities: list[dict[str, str]] = []
    if isinstance(docops_summary, dict) and int(docops_summary.get("to_request") or 0):
        priorities.append(
            _priority(
                "Pieces documentaires a demander",
                "P2",
                f"{docops_summary.get('to_request')} pieces manquantes, obsoletes ou a classer sont transformees en actions.",
                "/actions?scope=documents",
            )
        )
    if isinstance(non_matches, DataTable) and non_matches.rows:
        priorities.append(
            _priority(
                "Factures a rapprocher",
                "P1",
                f"{len(non_matches.rows)} lignes demandent une clarification. Elles sont traitees comme actions de demande au syndic.",
                "/actions?scope=comptes",
            )
        )
    if isinstance(controls_p1, list) and controls_p1:
        priorities.append(
            _priority(
                "Controles comptables prioritaires",
                "P1",
                f"{priority_control_total} controles comptables prioritaires detectes ; {len(controls_p1)} sont affiches en apercu.",
                "/actions?scope=comptes",
            )
        )
    if isinstance(review_rows, list) and review_rows:
        priorities.append(
            _priority(
                "Confidentialite a revoir",
                "P2",
                f"{len(review_rows)} documents ou sorties demandent une revue.",
                "/actions?scope=confidentialite",
            )
        )
    if isinstance(decision_summary, dict) and int(decision_summary.get("missing_proofs") or 0):
        priorities.append(
            _priority(
                "Preuves de decisions a obtenir",
                "P1",
                f"{decision_summary.get('missing_proofs')} decisions AG n'ont pas encore de preuve rattachee.",
                "/actions?scope=decisions",
            )
        )
    if isinstance(incident_summary, dict) and int(incident_summary.get("open") or 0):
        priorities.append(
            _priority(
                "Incidents ouverts a suivre",
                "P1" if "P1" in incident_summary.get("priorities", {}) else "P2",
                f"{incident_summary.get('open')} incidents ouverts, {incident_summary.get('incomplete')} incomplets.",
                "/actions?scope=incidents",
            )
        )
    if not priorities:
        priorities.append(
            _priority(
                "Aucun blocage prioritaire detecte",
                "OK",
                "Les artefacts disponibles ne signalent pas de blocage immediat.",
                "/",
            )
        )

    cockpit_alerts = _cockpit_alerts(priorities, action_summary, privacy, piece_workshop)
    evidence_summary = _evidence_summary(action_items, piece_workshop, decisions, incidents)
    trust_summary = _trust_summary(instance, documents, privacy)
    ux_model = _build_ux_model(
        instance,
        year,
        action_items=action_items,
        action_summary=action_summary,
        evidence_summary=evidence_summary,
        cockpit_alerts=cockpit_alerts,
        accounting=accounting,
        decisions=decisions,
        incidents=incidents,
        privacy=privacy,
        documents=documents,
        piece_workshop=piece_workshop,
        trust_summary=trust_summary,
    )

    modules = [
        _module(
            "DocOps",
            _status(bool(documents["documents"].count), bool(documents["documents"].exists)),
            "Inventaire, hash, classement, completude.",
            "/documents",
        ),
        _module(
            "Atelier pieces",
            _status(
                bool(piece_workshop_summary.get("total")),
                bool(piece_workshop_summary.get("total")),
            ),
            "Pieces, points, actions attendues et preuves rattachees.",
            "/pieces",
        ),
        _module(
            "ComptaScope",
            _status(bool(summary), bool(accounting["paths"]["summary"].exists())),
            "Controle comptes guide et rapprochements.",
            "/comptes",
        ),
        _module(
            "PrivacyOps / BiffageOps",
            _status(bool(privacy["screening"].count), bool(privacy["screening"].exists)),
            "Screening, file de biffage, restrictions.",
            "/confidentialite",
        ),
        _module(
            "DecisionOps",
            _status(
                bool(decision_summary.get("total") if isinstance(decision_summary, dict) else 0),
                bool(decisions["register"].exists if isinstance(decisions.get("register"), DataTable) else False),
            ),
            "Decisions AG, echeances, preuves attendues.",
            "/chantiers",
        ),
        _module(
            "IncidentOps",
            _status(
                bool(incident_summary.get("total") if isinstance(incident_summary, dict) else 0),
                bool(incidents["register"].exists if isinstance(incidents.get("register"), DataTable) else False),
            ),
            "Incidents ouverts, prochaine action, preuve de cloture.",
            "/chantiers",
        ),
        _module(
            "Chantiers produit",
            STATUS_WORKING,
            "Travaux suivis, IncidentOps, CommsOps, passation.",
            "/chantiers",
        ),
        _module(
            "Depot & exports",
            _status(bool(deposits["count"]), bool(deposits["count"])),
            "Depot local, pipeline et pack local sur.",
            "/depot",
        ),
    ]
    ux_pieces_summary = (
        ux_model.get("pieces", {}).get("summary", {})
        if isinstance(ux_model.get("pieces"), dict)
        else {}
    )
    nav_missing_pieces = (
        int(ux_pieces_summary.get("missing_count") or 0)
        + int(ux_pieces_summary.get("to_deposit_count") or 0)
    )
    if not nav_missing_pieces and isinstance(docops_summary, dict):
        nav_missing_pieces = int(docops_summary.get("to_request") or 0)

    return {
        "instance": {
            "id": instance.instance_id,
            "name": instance.display_name,
            "root": str(instance.instance_root),
            "year": year,
        },
        "modules": modules,
        "priorities": priorities,
        "cockpit_alerts": cockpit_alerts,
        "evidence_summary": evidence_summary,
        "trust_summary": trust_summary,
        "actions": preview_actions,
        "action_items": action_items,
        "action_summary": action_summary,
        "piece_workshop": piece_workshop,
        "documents": documents,
        "accounting": accounting,
        "privacy": privacy,
        "decisions": decisions,
        "incidents": incidents,
        "deposits": deposits,
        "workstreams": _workstreams(decisions, incidents),
        "ux": ux_model,
        "kpis": {
            "documents": documents["documents"].count,
            "invoices": int(summary.get("invoice_count") or accounting["invoices"].count or 0),
            "controls": int(summary.get("control_count") or accounting["controls"].count or 0),
            "privacy_reviews": len(review_rows) if isinstance(review_rows, list) else 0,
            "decisions": int(decision_summary.get("total") or 0) if isinstance(decision_summary, dict) else 0,
            "open_incidents": int(incident_summary.get("open") or 0) if isinstance(incident_summary, dict) else 0,
            "doc_requests": nav_missing_pieces,
            "piece_workshop": int(piece_workshop_summary.get("total") or 0),
            "actions": len(action_items),
        },
    }
