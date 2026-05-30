from typing import Any


def register_governance_cr_cs_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from fastapi import Request as FastAPIRequest

    @app.get("/gouvernance/compte-rendu-cs", response_class=html_response)
    def governance_cr_cs(request: FastAPIRequest):
        require_token(request)
        view = build_governance_cr_cs_view(year)
        return templates.TemplateResponse(
            request=request,
            name="governance_cr_cs.html",
            context=context(request, "governance_cr_cs", model=view["shell_model"], governance_cr_cs=view),
        )


def build_governance_cr_cs_view(year: int = 2025) -> dict[str, Any]:
    """Return a synthetic internal validation view for a CS meeting note."""
    return {
        "title": "Compte rendu du conseil syndical",
        "notice": "Scenario FICTIF: document interne, aucun envoi officiel.",
        "status": {
            "label": "Validation interne a preparer",
            "summary": "La version de travail peut etre relue, mais validation, export et partage restent bloques.",
            "cta": "Verifier avant partage",
            "version": "Version 0.3 - brouillon local",
        },
        "boundary": [
            _boundary("Document interne", "Ne vaut pas proces-verbal d'assemblee generale."),
            _boundary("Validation prudente", "Ne signe rien juridiquement et ne publie rien."),
            _boundary("Aucun envoi", "Un fichier prepare reste local tant qu'une personne ne l'envoie pas hors CoproScope."),
            _boundary("Correction tracee", "Toute correction apres validation cree une nouvelle version."),
        ],
        "meeting": {
            "date": "15 juin 2026",
            "place": "Reunion conseil syndical - exemple fictif",
            "attendees": ["Referente conseil syndical", "Membre travaux", "Membre comptes"],
            "missing": ["Syndic invite - reponse attendue"],
        },
        "decisions": [
            _decision(
                "Relancer les devis manquants",
                "A relire",
                "Demander au syndic les devis et l'autorisation de chantier.",
                "Document a verifier avant validation",
            ),
            _decision(
                "Reporter le partage externe",
                "Reserve",
                "Attendre la revue de diffusion avant tout export.",
                "Decision de diffusion absente",
            ),
            _decision(
                "Preparer la prochaine question comptes",
                "Brouillon",
                "Lister les pieces utiles et les questions a poser.",
                "Source comptable fictive",
            ),
        ],
        "actions": [
            _action("Demander relecture", "Disponible", "Faire relire le brouillon par les membres listes."),
            _action("Valider version interne", "Bloquee", "Preuves et diffusion ne sont pas confirmees."),
            _action("Verifier avant partage", "Prioritaire", "Choisir qui pourra voir le fichier prepare."),
            _action("Preparer revue diffusion", "Bloquee", "Audience, forme et reserves restent a renseigner."),
        ],
        "validation_steps": [
            _step("Presents relus", "A faire", "Confirmer qui etait present ou absent."),
            _step("Reserves individuelles notees", "A faire", "Ne pas transformer une reserve en position collective."),
            _step("Preuves acceptees", "Bloquant", "Une preuve a verifier bloque la validation interne."),
            _step("Diffusion relue", "Bloquant", "Aucun export tant que l'audience n'est pas claire."),
        ],
        "diffusion": {
            "label": "Qui pourra voir ce document",
            "status": "A verifier",
            "entries": [
                "Conseil syndical uniquement pour cette version.",
                "Coproprietaires exclus tant que la revue de diffusion n'est pas faite.",
                "Syndic a contacter hors CoproScope si le conseil le decide.",
            ],
        },
        "version_log": [
            "Brouillon cree sur donnees fictives.",
            "Preuves et diffusion marquees a verifier.",
            "Validation interne bloquee avant correction.",
        ],
        "shell_model": _synthetic_shell_model(year),
    }


def _boundary(label: str, detail: str) -> dict[str, str]:
    return {"label": label, "detail": detail}


def _decision(title: str, status: str, next_action: str, proof: str) -> dict[str, str]:
    return {"title": title, "status": status, "next_action": next_action, "proof": proof}


def _action(label: str, state: str, reason: str) -> dict[str, str]:
    return {"label": label, "state": state, "reason": reason, "enabled": "true" if state == "Disponible" else "false"}


def _step(label: str, status: str, detail: str) -> dict[str, str]:
    return {"label": label, "status": status, "detail": detail}


def _synthetic_shell_model(year: int) -> dict[str, Any]:
    return {
        "instance": {"id": "FICTIF", "name": "Copropriete FICTIVE", "root": "", "year": year},
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Compte rendu du conseil syndical",
                "active_page": "governance_cr_cs",
                "search_placeholder": "Rechercher une decision, une preuve ou une version fictive...",
                "notification_count": 0,
                "sharing_mode_label": "Interne local",
                "sharing_mode_status": "Aucun envoi officiel depuis cette page",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
