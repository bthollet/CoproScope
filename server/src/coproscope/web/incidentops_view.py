from collections import Counter
from typing import Any

from ..modules import incidentops


STATUS_LABELS = {
    "NOUVEAU": "nouveau",
    "A_QUALIFIER": "a qualifier",
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
        _entry("References opaques", "Les pieces restent des rattachements a verifier, pas des fichiers servis."),
        _entry("Validation humaine", "Aucune declaration, relance ou diffusion n'est envoyee depuis cette page."),
    ]
    return {
        "title": "Incidents et sinistres",
        "headline": "Signalements et preuves de cloture",
        "notice": _notice(instance, rows),
        "status": {
            "label": "Signalements a qualifier",
            "summary": "Chaque incident garde une urgence, une preuve attendue et une cloture verifiable.",
            "cta": "Qualifier un signalement",
        },
        "summary": [
            _metric("Incidents ouverts", str(len(open_rows)), "Signalements qui demandent encore une suite humaine."),
            _metric("A qualifier", str(status_counts.get("A_QUALIFIER", 0)), "Lieu, assurance ou preuve attendue a preciser."),
            _metric("Preuves de cloture", str(sum(1 for row in open_rows if row["expected_proof"])), "Trace biffee, facture ou accord a obtenir."),
            _metric("Urgences", str(priority_counts.get("P0", 0) + priority_counts.get("P1", 0)), "Points a traiter avant simple suivi."),
        ],
        "definitions": [
            _entry("Signalement", "Fait remonte localement: lieu, date, dommage ou risque."),
            _entry("Sinistre", "Incident pouvant demander une assurance ou une expertise."),
            _entry("Assurance", "Dossier a verifier avec le syndic ou le contrat concerne."),
            _entry("Preuve de cloture", "Trace qui montre que le probleme est traite ou classe."),
            _entry("Synthese neutre", "Texte court sans nom, chemin local ni piece sensible."),
            _entry("Diffusion", "Decision sur qui peut voir la synthese et la preuve derivee."),
        ],
        "incidents": rows,
        "status_counts": _count_rows(status_counts, STATUS_LABELS),
        "priority_counts": _count_rows(priority_counts, PRIORITY_LABELS),
        "decision_gates": [
            _entry("Qualifier l'urgence", "Distinguer securite, assurance, confort et simple suivi."),
            _entry("Nommer la preuve attendue", "Cloture impossible sans trace lisible."),
            _entry("Choisir la diffusion", "CS seulement par defaut; partage large a revoir."),
            _entry("Agir hors CoproScope", "Declaration, appel ou envoi restent humains et externes."),
        ],
        "actions": [
            _action("Voir actions incidents", "Disponible", "Ouvrir la file des suites a donner.", "/actions?scope=incidents"),
            _action("Ajouter preuve locale", "Disponible", "Deposer une trace derivee ou biffee.", "/depot?intent=document&return=incidents"),
            _action("Voir pieces sinistres", "Disponible", "Retrouver les preuves attendues.", "/pieces?proof=missing&group=sinistres"),
            _action("Declaration assurance", "Bloquee", "A faire hors CoproScope apres validation humaine.", ""),
            _action("Partager aux coproprietaires", "Bloquee", "Synthese et diffusion a confirmer avant partage.", ""),
            _action("Marquer comme clos", "Bloquee", "Preuve de cloture et diffusion doivent etre confirmees.", ""),
        ],
        "boundaries": guardrails,
        "guardrails": guardrails,
        "version_log": [
            "Vue IncidentOps creee pour le suivi local fictif ou registre local.",
            "Exemples FICTIFS utilises si aucun registre incident n'existe.",
            "Actions externes, declarations et clotures bloquees dans cette iteration.",
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


def _notice(instance: Any | None, rows: list[dict[str, Any]]) -> str:
    if instance is not None and rows and any(row.get("source_label") == "Registre local" for row in rows):
        return "Registre local: synthese derivee, aucun original servi."
    return "Scenario FICTIF: signalements de demonstration, aucune declaration."


def _row_view(row: dict[str, str], *, fictive: bool) -> dict[str, Any]:
    normalized = incidentops.normalize_incident(row)
    status = incidentops.normalize_status(normalized.get("status"))
    priority = normalized.get("priority") or "P2"
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
        "is_open": incidentops.is_open_incident(normalized),
        "assurance": _assurance_label(normalized),
        "insurance": _assurance_label(normalized),
        "proof_state": _proof_state(normalized),
        "expected_proof": normalized.get("expected_closure_proof") or "preuve de cloture a definir",
        "next_action": normalized.get("next_action") or "Qualifier la suite humaine.",
        "due_at": normalized.get("action_due_date") or "echeance a fixer",
        "diffusion": "CS seulement",
        "link": _attachment_label(normalized),
        "source_label": "FICTIF" if fictive else "Registre local",
    }


def _summary_text(row: dict[str, str], *, fictive: bool) -> str:
    description = _clip(row.get("description", ""), 96)
    if description:
        return f"{description} ({'FICTIF' if fictive else 'synthese locale'})"
    return "Signalement a completer"


def _assurance_label(row: dict[str, str]) -> str:
    if row.get("contract_or_insurance_ref"):
        return "Assurance ou contrat a verifier"
    return "Assurance a qualifier"


def _proof_state(row: dict[str, str]) -> str:
    if row.get("closure_proof_ref"):
        return "Preuve de cloture rattachee"
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
            "expected_closure_proof": "Photo biffee apres intervention ou bon de passage.",
            "next_action": "Qualifier assurance, prestataire et preuve attendue.",
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
        return "Scenario FICTIF: suivi local, aucune transmission automatique."
    return "Registre local: references derivees seulement, pieces originales non affichees."


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
                "search_placeholder": "Rechercher un incident, une preuve ou une action...",
                "notification_count": 0,
                "sharing_mode_label": "Suivi local",
                "sharing_mode_status": "Aucune declaration depuis cette page",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
