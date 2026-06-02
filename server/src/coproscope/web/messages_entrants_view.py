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
    messages = [
        _message(
            "MSG-FICTIF-01",
            "Occupant fictif, sans nom",
            "Signalement fuite palier",
            "Risque dommage et delai court",
            "A traiter maintenant",
            "Resume prudent a preparer",
            "Conseil syndical seulement",
            "Photo masquee ou note a rattacher",
            "Preparer un lien vers un incident",
        ),
        _message(
            "MSG-FICTIF-02",
            "Coproprietaire fictif, sans nom",
            "Question charges",
            "Besoin de justificatif comptable",
            "A verifier",
            "A reformuler simplement",
            "Partage envisage, a valider",
            "Piece de compte a verifier",
            "Preparer une demande syndic",
        ),
        _message(
            "MSG-FICTIF-03",
            "Mandataire fictif, sans nom",
            "Piece travaux recue",
            "Document utile au suivi",
            "A ranger",
            "Original a garder local",
            "Conseil syndical seulement",
            "Reference de preuve a creer",
            "Preparer un lien vers le chantier travaux",
        ),
        _message(
            "MSG-FICTIF-04",
            "Role local fictif",
            "Question hors mandat",
            "Droit de reponse a confirmer",
            "Bloque",
            "Ne pas reformuler sans validation",
            "Partage bloque",
            "Mandat a confirmer",
            "Demander validation humaine",
        ),
    ]

    return {
        "title": "Messages entrants",
        "headline": "Messages recus a traiter",
        "notice": "Demonstration FICTIVE - FICTIF: aucun vrai message, aucune reponse, aucune publication.",
        "status": {
            "label": "Validation humaine obligatoire",
            "summary": "Chaque message est d'abord lu, reformule si besoin, relie a une preuve et partage seulement apres accord.",
            "cta": "Voir le tri a faire",
            "guardrail": "Qualifier maintenant signifie lire et classer: CoproScope ne repond pas et ne publie pas.",
        },
        "summary": [
            _metric("Messages a verifier", "4", "Entrees fictives avec une decision humaine manquante."),
            _metric("Messages sensibles", "2", "Synthese neutre requise avant diffusion."),
            _metric("Preuves a rattacher", "3", "Piece, note ou trace attendue avant cloture."),
        ],
        "definitions": [
            _entry("Message recu", "Information saisie localement pour demonstration."),
            _entry("Comprendre et classer", "Choisir la nature, l'urgence et la suite humaine."),
            _entry("Qui parle, sans nom", "Origine exprimee par un role fictif, sans identite personnelle."),
            _entry("Masquer ou reformuler", "Dire quoi garder local et quoi resumer prudemment."),
            _entry("Preuve attendue", "Piece ou trace qui montre ce qui a ete dit ou fait."),
            _entry("Qui peut lire", "Conseil syndical, coproprietaires, ou partage bloque."),
            _entry("Pourquoi on range", "Raison lisible avant de sortir le message de la file."),
        ],
        "messages": messages,
        "selected_message": messages[0],
        "decision_gates": [
            _entry("Lire sans envoyer", "Comprendre le sujet avant toute action visible."),
            _entry("Choisir qui peut lire", "Dire qui peut voir le resume et la preuve."),
            _entry("Verifier la preuve", "Relier une piece ou une trace avant rangement."),
            _entry("Noter la suite humaine", "Demande, action, classement ou validation humaine."),
        ],
        "actions": [
            _action("Lire le message", "A preparer ici", "Comprendre le sujet sans envoyer de reponse."),
            _action("Choisir qui peut lire", "A preparer ici", "Decider si le resume reste au conseil syndical ou doit etre bloque."),
            _action("Rattacher une preuve", "A preparer ici", "Nommer la piece ou la trace attendue."),
            _action("Noter la suite humaine", "A preparer ici", "Preparer une action ou un rangement, sans envoi officiel."),
            _action("Repondre automatiquement", "Bloquee", "Mandat et validation humaine requis."),
            _action("Publier aux coproprietaires", "Bloquee", "Partage non confirme."),
            _action("Ouvrir un compte exterieur", "Bloquee", "Aucun compte externe dans cette iteration."),
        ],
        "blocked_sources": [
            _entry("Original protege", "Ne pas montrer l'identite ni l'original avant validation."),
            _entry("Donnees fictives", "Aucune entree d'instance ni piece source n'est chargee."),
            _entry("Trace des verifications", "Toute suite doit garder motif, preuve et decision de partage."),
        ],
        "version_log": [
            "File creee sur donnees fictives.",
            "Aucune reponse automatique.",
            "Reponse et publication automatiques bloquees.",
            "Validation humaine obligatoire avant tout partage.",
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
    return {"label": label, "state": state, "reason": reason, "blocked": "true" if state == "Bloquee" else "false"}


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
