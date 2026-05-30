from typing import Any


def register_courriers_preuves_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from fastapi import Request as FastAPIRequest

    @app.get("/courriers/preuves", response_class=html_response)
    def courriers_preuves(request: FastAPIRequest):
        require_token(request)
        view = build_courriers_preuves_view(year)
        return templates.TemplateResponse(
            request=request,
            name="courriers_preuves.html",
            context=context(request, "courriers_preuves", model=view["shell_model"], courriers_preuves=view),
        )


def build_courriers_preuves_view(year: int = 2025) -> dict[str, Any]:
    """Return a synthetic official communications evidence view."""
    return {
        "title": "Courriers et preuves",
        "notice": "Scenario FICTIF: brouillons locaux, aucune transmission depuis CoproScope.",
        "status": {
            "label": "Verification humaine requise",
            "summary": "CoproScope prepare le dossier, puis une personne agit hors application.",
            "cta": "Verifier avant envoi",
        },
        "summary": [
            _metric("Brouillons a valider", "3", "Textes locaux a relire avant toute suite."),
            _metric("Preuves a rattacher", "2", "Depot, reception ou refus a documenter par reference opaque."),
            _metric("Reponses recues", "1", "Retour fictif a relier a une action ou resolution."),
        ],
        "definitions": [
            _entry("Brouillon", "Texte prepare localement, pas encore transmis."),
            _entry("Mandat", "Raison qui autorise quelqu'un a agir ou ecrire."),
            _entry("Preuve de depot", "Trace que l'envoi a ete depose chez un service."),
            _entry(
                "Preuve de reception",
                "Trace que le destinataire ou son representant a recu ou refuse.",
            ),
        ],
        "boundaries": [
            _entry("Preparation seulement", "La page aide a relire; elle ne transmet rien."),
            _entry("Validation humaine", "Un brouillon engageant reste bloque sans approbation."),
            _entry("Preuve originale", "L'original reste conserve hors export large."),
            _entry("Synthese derivee", "Tout export futur devra marquer source_of_truth=false."),
        ],
        "drafts": [
            _draft(
                "DRAFT-FICTIF-01",
                "Demande de piece au syndic",
                "Action ACT-FICTIF-12",
                "SYNDIC-FICTIF",
                "A_VALIDER",
                "Mandat conseil a confirmer",
            ),
            _draft(
                "DRAFT-FICTIF-02",
                "Question avant resolution AG",
                "RES-FICTIF-03",
                "COPRO-FICTIF-01",
                "BROUILLON",
                "Verifier la base de mandat avant copie manuelle",
            ),
            _draft(
                "DRAFT-FICTIF-03",
                "Relance preuve travaux",
                "CHANTIER-FICTIF-02",
                "PREST-FICTIF",
                "PREUVE_A_RATTACHER",
                "Reference de depot attendue",
            ),
        ],
        "approval_steps": [
            _entry("Sujet compris", "Le lecteur sait pourquoi le brouillon existe."),
            _entry("Destinataire verifie", "Role fictif confirme, aucun carnet brut affiche."),
            _entry("Mandat relu", "La personne qui agit sait au nom de qui elle le fait."),
            _entry("Preuve attendue", "Depot, reception, refus ou reponse sont rattaches a une action."),
        ],
        "proofs": [
            _proof("PROOF-FICTIF-01", "Preuve de depot", "A rattacher", "Action ACT-FICTIF-12"),
            _proof("PROOF-FICTIF-02", "Preuve de reception", "A verifier", "Resolution RES-FICTIF-03"),
            _proof("REPLY-FICTIF-01", "Reponse recue", "A classer", "Demande DEM-FICTIF-04"),
        ],
        "actions": [
            _action("Verifier avant envoi", "Disponible", "Relire destinataire, mandat et preuve attendue."),
            _action("Copier le brouillon", "Disponible", "Copie manuelle pour agir hors CoproScope."),
            _action("Rattacher une preuve", "Disponible", "Ajouter une reference opaque apres action humaine."),
            _action("Annuler le brouillon", "Disponible", "Conserver la trace locale de l'abandon."),
            _action("Transmettre automatiquement", "Bloquee", "Aucun connecteur ni secret n'est configure."),
            _action("Exporter un courrier officiel", "Bloquee", "Sortie officielle hors de cette iteration."),
        ],
        "blocked_sources": [
            _entry("Secret exclu", "Aucun mot de passe, jeton ou compte externe dans cette vue."),
            _entry("Dossier brut refuse", "Les sources sensibles restent locales et non servies."),
            _entry("Original separe", "La preuve originale n'est pas incluse dans un export large."),
        ],
        "version_log": [
            "Brouillons crees sur donnees fictives.",
            "Transmission automatique bloquee.",
            "Preuves rattachees seulement par references opaques.",
        ],
        "shell_model": _synthetic_shell_model(year),
    }


def _metric(label: str, value: str, detail: str) -> dict[str, str]:
    return {"label": label, "value": value, "detail": detail}


def _entry(label: str, detail: str) -> dict[str, str]:
    return {"label": label, "detail": detail}


def _draft(
    draft_id: str,
    subject: str,
    source: str,
    recipient: str,
    status: str,
    mandate: str,
) -> dict[str, str]:
    return {
        "id": draft_id,
        "subject": subject,
        "source": source,
        "recipient": recipient,
        "status": status,
        "mandate": mandate,
    }


def _proof(proof_id: str, proof_type: str, status: str, link: str) -> dict[str, str]:
    return {"id": proof_id, "type": proof_type, "status": status, "link": link}


def _action(label: str, state: str, reason: str) -> dict[str, str]:
    return {"label": label, "state": state, "reason": reason, "enabled": "true" if state == "Disponible" else "false"}


def _synthetic_shell_model(year: int) -> dict[str, Any]:
    return {
        "instance": {"id": "FICTIF", "name": "Copropriete FICTIVE", "root": "", "year": year},
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Courriers et preuves",
                "active_page": "courriers_preuves",
                "search_placeholder": "Rechercher un brouillon, une preuve ou une action fictive...",
                "notification_count": 0,
                "sharing_mode_label": "Preparation locale",
                "sharing_mode_status": "Aucune transmission depuis cette page",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
