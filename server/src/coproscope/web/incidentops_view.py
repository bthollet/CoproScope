from collections import Counter
from typing import Any

from ..modules import incidentops


STATUS_LABELS = {
    "NOUVEAU": "nouveau",
    "A_QUALIFIER": "a completer",
    "EN_COURS": "en cours",
    "EN_RELANCE": "en relance",
    "EN_ATTENTE_PREUVE": "preuve attendue",
    "A_CLOTURER": "a cloturer",
    "CLOTURE": "cloture",
    "SANS_SUITE": "sans suite",
}

PRIORITY_LABELS = {"P0": "urgence", "P1": "a traiter vite", "P2": "a suivre", "P3": "veille"}


def register_incidentops_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from fastapi import Request as FastAPIRequest

    @app.get("/incidents", response_class=html_response)
    def incidents(request: FastAPIRequest):
        require_token(request)
        view = build_incidentops_view(instance=getattr(app.state, "instance", None), year=year)
        return templates.TemplateResponse(
            request=request,
            name="incidents.html",
            context=context(request, "incidentops", model=view["shell_model"], incidents=view),
        )


def build_incidentops_view(instance: Any | None = None, year: int = 2025) -> dict[str, Any]:
    """Return a privacy-safe IncidentOps view from local rows or fictive examples."""
    if isinstance(instance, int) and year == 2025:
        year = instance
        instance = None
    rows = _incident_rows(instance, year)
    open_rows = [row for row in rows if row["is_open"]]
    status_counts = Counter(row["status"] for row in rows)
    priority_counts = Counter(row["priority"] for row in open_rows)
    guardrails = [
        _entry("Donnees minimales", "La page n'affiche pas les chemins ni les sources brutes."),
        _entry("Documents originaux non affiches", "Les pieces restent des rattachements a verifier, pas des fichiers servis."),
        _entry("Validation humaine", "Aucune declaration, relance ou diffusion n'est envoyee depuis cette page."),
    ]
    return {
        "title": "Incidents et sinistres",
        "headline": "Signalements et preuves de cloture",
        "notice": _notice(instance, rows),
        "status": {
            "label": "Suites a preparer",
            "summary": "CoproScope prepare les informations. Il n'envoie pas de declaration assurance ou syndic.",
            "cta": "Completer un signalement",
        },
        "summary": [
            _metric("A faire maintenant", str(priority_counts.get("P0", 0) + priority_counts.get("P1", 0)), "Urgence ou assurance a traiter."),
            _metric("Infos a completer", str(status_counts.get("A_QUALIFIER", 0)), "Lieu, assurance, preuve ou diffusion a preciser."),
            _metric("Preuves attendues", str(sum(1 for row in open_rows if row["expected_proof"])), "Photo ou document masque a verifier avant cloture."),
            _metric("Preuve recue", str(status_counts.get("CLOTURE", 0)), "Signalements clos avec preuve ou verification rattachee."),
        ],
        "definitions": [
            _entry("Signalement", "Fait remonte localement: lieu, date, dommage ou risque."),
            _entry("Sinistre", "Incident pouvant demander une assurance ou une expertise."),
            _entry("Assurance", "Dossier a verifier avec le syndic ou le contrat concerne."),
            _entry("Preuve de cloture", "Trace qui montre que le probleme est traite ou classe."),
            _entry("Photo ou document masque", "Copie relue avec les informations sensibles cachees avant partage."),
            _entry("Synthese neutre", "Texte court sans nom, chemin local ni piece sensible."),
            _entry("Diffusion", "Decision sur qui peut voir la synthese et la copie masquee."),
        ],
        "incidents": rows,
        "status_counts": _count_rows(status_counts, STATUS_LABELS),
        "priority_counts": _count_rows(priority_counts, PRIORITY_LABELS),
        "decision_gates": [
            _entry("Choisir le niveau d'urgence", "Distinguer securite, assurance, confort et simple suivi."),
            _entry("Nommer la preuve attendue", "Cloture impossible sans photo ou document masque lisible."),
            _entry("Choisir la diffusion", "Conseil syndical seulement par defaut; partage large a revoir."),
            _entry("Agir hors CoproScope", "Declaration, appel ou envoi restent humains et externes."),
        ],
        "actions": [
            _action("Voir les actions a faire", "Disponible", "Ouvrir la liste des actions liees aux incidents.", "/actions?scope=incidents"),
            _action("Joindre photo ou document masque", "Disponible", "Deposer une copie relue avec les informations sensibles cachees, jamais le fichier brut.", "/depot?intent=document&return=incidents"),
            _action("Voir les preuves attendues", "Disponible", "Retrouver les preuves a demander ou verifier.", "/pieces?proof=missing&group=sinistres"),
            _action("Declaration assurance externe", "Bloquee", "A faire hors CoproScope apres validation humaine.", ""),
            _action("Partager largement", "Bloquee", "Synthese et diffusion a confirmer avant partage.", ""),
            _action("Cloturer le dossier", "Bloquee", "Preuve de cloture et diffusion doivent etre confirmees.", ""),
        ],
        "boundaries": guardrails,
        "guardrails": guardrails,
        "version_log": [
            "Donnees FICTIVES si aucun registre local n'existe.",
            "Declaration, relance, partage et cloture restent hors CoproScope.",
            "Photos et documents bruts restent hors affichage.",
        ],
        "shell_model": _shell_model(year),
    }


def _incident_rows(instance: Any | None, year: int) -> list[dict[str, Any]]:
    if instance is not None:
        try:
            rows = incidentops.read_incident_register(instance)
        except (AttributeError, KeyError, OSError, TypeError, ValueError):
            rows = []
        if rows:
            return [_row_view(row, fictive=False) for row in rows]
    return [_row_view(row, fictive=True) for row in _fallback_rows(year)]


def _row_view(row: dict[str, str], *, fictive: bool) -> dict[str, Any]:
    normalized = incidentops.normalize_incident(row)
    status = incidentops.normalize_status(normalized.get("status"))
    priority = normalized.get("priority") or "P2"
    is_open = incidentops.is_open_incident(normalized)
    is_closed = not is_open and status == "CLOTURE"
    expected_proof = normalized.get("expected_closure_proof")
    next_action = normalized.get("next_action")
    return {
        "id": normalized.get("incident_id") or "INC-A-QUALIFIER",
        "date": normalized.get("date_signalement") or "date a preciser",
        "location": normalized.get("lieu") or "lieu a preciser",
        "subject": _clip(normalized.get("description", ""), 56) or "Signalement a completer",
        "summary": _summary_text(normalized, fictive=fictive),
        "status": status,
        "status_label": STATUS_LABELS.get(status, status.lower()),
        "priority": priority,
        "priority_label": PRIORITY_LABELS.get(priority, priority),
        "urgency": PRIORITY_LABELS.get(priority, priority),
        "is_open": is_open,
        "assurance": _assurance_label(normalized, closed=is_closed),
        "insurance": _assurance_label(normalized, closed=is_closed),
        "proof_state": _proof_state(normalized),
        "expected_proof": expected_proof or ("Preuve recue ou verification faite" if is_closed else "preuve de cloture a definir"),
        "next_action": next_action or ("Aucune action a preparer depuis cette page." if is_closed else "Preparer la prochaine action par une personne."),
        "due_at": normalized.get("action_due_date") or ("clos" if is_closed else "echeance a fixer"),
        "diffusion": "Conseil syndical seulement",
        "link": _attachment_label(normalized),
        "source_label": "FICTIF" if fictive else "Registre local",
    }


def _summary_text(row: dict[str, str], *, fictive: bool) -> str:
    description = _clip(row.get("description", ""), 96)
    if description:
        return f"{description} ({'FICTIF' if fictive else 'synthese locale'})"
    return "Signalement a completer"


def _assurance_label(row: dict[str, str], *, closed: bool = False) -> str:
    if closed and not row.get("contract_or_insurance_ref"):
        return "Verification faite"
    if row.get("contract_or_insurance_ref"):
        return "Assurance ou contrat a verifier"
    return "Assurance a verifier"


def _proof_state(row: dict[str, str]) -> str:
    if row.get("closure_proof_ref"):
        return "Preuve recue ou verification faite"
    if row.get("doc_ids") or row.get("piece_ref"):
        return "Piece candidate a verifier"
    return "Preuve a rattacher"


def _attachment_label(row: dict[str, str]) -> str:
    if row.get("contract_or_insurance_ref"):
        return "Contrat ou assurance a verifier"
    if row.get("piece_ref") or row.get("doc_ids"):
        return "Piece candidate a verifier"
    return "Rattachement a qualifier"


def _fallback_rows(year: int) -> list[dict[str, str]]:
    return [
        {
            "incident_id": "INC-FICTIF-01",
            "date_signalement": f"{year}-05-03",
            "lieu": "Parking niveau -1",
            "description": "Fuite persistante signalee dans une zone commune.",
            "status": "A_QUALIFIER",
            "priority": "P1",
            "expected_closure_proof": "Photo ou document masque apres intervention.",
            "next_action": "Verifier assurance, prestataire et preuve attendue.",
            "action_due_date": f"{year}-05-10",
        },
        {
            "incident_id": "INC-FICTIF-02",
            "date_signalement": f"{year}-04-18",
            "lieu": "Local technique",
            "description": "Panne recurrente a suivre avant cloture.",
            "status": "EN_ATTENTE_PREUVE",
            "priority": "P2",
            "expected_closure_proof": "Facture ou compte rendu d'intervention.",
            "next_action": "Demander la preuve de resolution au syndic.",
            "action_due_date": f"{year}-05-02",
        },
        {
            "incident_id": "INC-FICTIF-03",
            "date_signalement": f"{year}-03-28",
            "lieu": "Hall",
            "description": "Signalement classe apres verification locale.",
            "status": "CLOTURE",
            "priority": "P3",
            "closure_proof_ref": "PREUVE-FICTIVE-CLOTURE",
        },
    ]


def _metric(label: str, value: str, detail: str) -> dict[str, str]:
    return {"label": label, "value": value, "detail": detail}


def _entry(label: str, detail: str) -> dict[str, str]:
    return {"label": label, "detail": detail}


def _notice(instance: Any | None, rows: list[dict[str, Any]]) -> str:
    if instance is None or any(row.get("source_label") == "FICTIF" for row in rows):
        return "Scenario FICTIF: suivi de demonstration, aucune transmission automatique."
    return "Registre local: copies masquees seulement, documents originaux non affiches."


def _action(label: str, state: str, reason: str, href: str) -> dict[str, str]:
    return {"label": label, "state": state, "reason": reason, "href": href, "enabled": "true" if href else "false"}


def _count_rows(counts: Counter[str], labels: dict[str, str]) -> list[dict[str, Any]]:
    return [{"key": key, "label": labels.get(key, key), "count": count} for key, count in counts.items() if count]


def _clip(value: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}..."


def _shell_model(year: int) -> dict[str, Any]:
    return {
        "instance": {"id": "FICTIF", "name": "Copropriete FICTIVE", "root": "", "year": year},
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Incidents et sinistres",
                "active_page": "incidents",
                "search_placeholder": "Rechercher un document rattache ou une preuve...",
                "notification_count": 0,
                "sharing_mode_label": "Suivi local",
                "sharing_mode_status": "Aucune declaration assurance ou syndic envoyee",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
