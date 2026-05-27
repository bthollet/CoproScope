from typing import Any


def register_messages_entrants_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from fastapi import Request as FastAPIRequest

    @app.get("/messages/entrants", response_class=html_response)
    def messages_entrants(request: FastAPIRequest):
        require_token(request)
        view = build_messages_entrants_view(year)
        return templates.TemplateResponse(
            request=request,
            name="messages_entrants.html",
            context=context(request, "messages_entrants", model=view["shell_model"], messages_entrants=view),
        )


def build_messages_entrants_view(year: int = 2025) -> dict[str, Any]:
    """Return a synthetic inbound-message qualification view."""
    return {
        "title": "Messages entrants",
        "headline": "Messages recus des coproprietaires",
        "notice": "Scenario FICTIF: saisie locale, aucun connecteur, aucune publication.",
        "status": {
            "label": "Decisions humaines requises",
            "summary": "Chaque message doit etre lu, classe, relie a une preuve et diffuse prudemment.",
            "cta": "Qualifier maintenant",
        },
        "summary": [
            _metric("Messages a qualifier", "4", "Entrees fictives avec une decision humaine manquante."),
            _metric("Messages sensibles", "2", "Synthese neutre requise avant diffusion."),
            _metric("Preuves a rattacher", "3", "Piece, note ou trace attendue avant cloture."),
        ],
        "definitions": [
            _entry("Message recu", "Information entree dans CoproScope par saisie locale."),
            _entry("Comprendre et classer", "Choisir la nature, l'urgence et la suite humaine."),
            _entry("Source rolee", "Origine exprimee par un role, sans identite personnelle."),
            _entry("Moderation", "Decision de masquer, reformuler ou garder local."),
            _entry("Preuve", "Piece qui peut servir a montrer ce qui a ete dit ou fait."),
            _entry("Diffusion", "Decision sur qui peut voir la synthese et la preuve."),
            _entry("Cloture", "Raison lisible avant de sortir le message de la file."),
        ],
        "messages": [
            _message(
                "MSG-FICTIF-01",
                "COPRO-FICTIF-01",
                "Signalement fuite palier",
                "Risque dommage et echeance courte",
                "A traiter maintenant",
                "Synthese neutre",
                "CS seulement",
                "Photo biffee a rattacher",
                "Lier a un incident",
            ),
            _message(
                "MSG-FICTIF-02",
                "COPRO-FICTIF-02",
                "Question charges",
                "Besoin de preuve comptable",
                "A qualifier",
                "Diffusable apres controle",
                "Synthese coproprietaires",
                "Piece compte a verifier",
                "Creer une demande syndic",
            ),
            _message(
                "MSG-FICTIF-03",
                "MAND-FICTIF-03",
                "Piece travaux recue",
                "Document utile au suivi",
                "A classer",
                "Original local",
                "CS seulement",
                "Reference preuve a creer",
                "Lier au chantier travaux",
            ),
            _message(
                "MSG-FICTIF-04",
                "LOC-FICTIF-04",
                "Question hors mandat",
                "Droit de reponse a verifier",
                "En attente",
                "Non diffusable en l'etat",
                "Bloquee",
                "Mandat a confirmer",
                "Demander validation humaine",
            ),
        ],
        "decision_gates": [
            _entry("Lire sans diffuser", "Comprendre le sujet avant toute action visible."),
            _entry("Choisir la visibilite", "Dire qui peut lire la synthese preparee."),
            _entry("Rattacher une preuve", "Relier une piece ou une trace avant cloture."),
            _entry("Decider la suite", "Demande, action, classement ou validation humaine."),
        ],
        "actions": [
            _action("Choisir la suite", "Disponible", "Qualifier nature, urgence, preuve et diffusion."),
            _action("Lier a un dossier", "Disponible", "Rattacher a action, incident, travaux, comptes ou AG."),
            _action("Preparer un brouillon", "Disponible", "Texte local a relire avant toute suite."),
            _action("Classer avec motif", "Disponible", "Cloture possible seulement avec raison lisible."),
            _action("Repondre automatiquement", "Bloquee", "Validation humaine et mandat requis."),
            _action("Publier aux coproprietaires", "Bloquee", "Diffusion non confirmee."),
            _action("Ouvrir un connecteur", "Bloquee", "Aucun compte externe dans cette iteration."),
        ],
        "blocked_sources": [
            _entry("Original protege", "Les messages sensibles restent en controle local."),
            _entry("Donnees fictives", "Aucune entree d'instance ni piece source n'est chargee."),
            _entry("Journal de diligence", "Toute suite doit garder motif, preuve et diffusion."),
        ],
        "version_log": [
            "File creee sur donnees fictives.",
            "Aucune reponse automatique.",
            "Reponse et publication automatiques bloquees.",
            "Qualification humaine obligatoire avant diffusion.",
        ],
        "shell_model": _synthetic_shell_model(year),
    }


def _metric(label: str, value: str, detail: str) -> dict[str, str]:
    return {"label": label, "value": value, "detail": detail}


def _entry(label: str, detail: str) -> dict[str, str]:
    return {"label": label, "detail": detail}


def _message(
    message_id: str,
    source: str,
    subject: str,
    attention: str,
    urgency: str,
    moderation: str,
    diffusion: str,
    proof: str,
    next_action: str,
) -> dict[str, str]:
    return {
        "id": message_id,
        "source": source,
        "subject": subject,
        "attention": attention,
        "urgency": urgency,
        "moderation": moderation,
        "diffusion": diffusion,
        "proof": proof,
        "next_action": next_action,
    }


def _action(label: str, state: str, reason: str) -> dict[str, str]:
    return {"label": label, "state": state, "reason": reason, "enabled": "true" if state == "Disponible" else "false"}


def _synthetic_shell_model(year: int) -> dict[str, Any]:
    return {
        "instance": {"id": "FICTIF", "name": "Copropriete FICTIVE", "root": "", "year": year},
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Messages entrants",
                "active_page": "messages_entrants",
                "search_placeholder": "Rechercher un message, une preuve ou une action fictive...",
                "notification_count": 0,
                "sharing_mode_label": "Qualification locale",
                "sharing_mode_status": "Aucune publication depuis cette page",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
