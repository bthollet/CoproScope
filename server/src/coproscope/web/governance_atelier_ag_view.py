from typing import Any


def register_governance_atelier_ag_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from fastapi import Request as FastAPIRequest

    @app.get("/gouvernance/atelier-ag", response_class=html_response)
    def governance_atelier_ag(request: FastAPIRequest):
        require_token(request)
        view = build_governance_atelier_ag_view(year)
        return templates.TemplateResponse(
            request=request,
            name="governance_atelier_ag.html",
            context=context(
                request,
                "governance_atelier_ag",
                model=view["shell_model"],
                governance_atelier_ag=view,
            ),
        )


def build_governance_atelier_ag_view(year: int = 2025) -> dict[str, Any]:
    """Return a synthetic AG workshop view for CS preparation only."""
    return {
        "title": "Atelier AG",
        "notice": "Scenario FICTIF: Projet CS - non officiel, aucune convocation.",
        "status": {
            "label": "Version de travail",
            "summary": "La page aide a preparer questions et resolutions, sans publier ni voter.",
            "cta": "Verifier avant partage",
            "version": "Brouillon CS 0.1",
        },
        "summary": [
            _metric("Questions a preparer", "3", "Questions fictives a relire avec preuve attendue."),
            _metric("Resolutions en brouillon", "2", "Textes de travail, non soumis au vote."),
            _metric("Preuves a rattacher", "5", "Pieces ou sources a verifier avant partage."),
            _metric("Diffusions a verifier", "4", "Audience et forme a choisir avant export."),
        ],
        "boundaries": [
            _entry("Projet CS - non officiel", "Support de travail limite au conseil syndical."),
            _entry("Pas une convocation", "Aucun envoi officiel ni calendrier legal n'est declenche."),
            _entry("Pas un proces-verbal", "La page ne constate aucun vote et ne remplace aucun document officiel."),
            _entry("Validation humaine", "Chaque sortie demande une relecture et une decision de diffusion."),
        ],
        "agenda_items": [
            _agenda(
                "AG-FICTIF-Q01",
                "Question syndic",
                "Explication des devis manquants",
                "A formuler",
                "Liste des pieces attendues",
                "Preparer une question courte au syndic.",
            ),
            _agenda(
                "AG-FICTIF-R01",
                "Resolution brouillon",
                "Choix d'un prestataire travaux",
                "Preuve manquante",
                "Devis comparables et assurance",
                "Rattacher les pieces avant toute discussion.",
            ),
            _agenda(
                "AG-FICTIF-Q02",
                "Question comptes",
                "Ecart a expliquer avant approbation",
                "A verifier",
                "Ligne comptable et facture candidate",
                "Demander une reponse documentee.",
            ),
            _agenda(
                "AG-FICTIF-R02",
                "Resolution brouillon",
                "Mandat de suivi conseil syndical",
                "Reserve",
                "Projet de mandat a relire",
                "Controler la portee avant diffusion.",
            ),
        ],
        "review_steps": [
            _entry("Fait", "Sujet formule sans accusation ni certitude non prouvee."),
            _entry("Preuve", "Piece, decision ou source attendue nommee."),
            _entry("Regle", "Limite officielle visible: projet, pas convocation ni vote."),
            _entry("Action", "Prochaine diligence humaine claire et non automatique."),
        ],
        "diffusion": {
            "label": "Revue de diffusion avant export",
            "status": "A decider",
            "entries": [
                "Conseil syndical uniquement pour ce brouillon.",
                "Coproprietaires: attendre une version relue et diffusable.",
                "Syndic: question a envoyer hors CoproScope si le conseil le decide.",
                "Annexes: aucun brut ni chemin local dans une sortie partageable.",
            ],
        },
        "actions": [
            _action("Relire questions", "Disponible", "Verifier fait, preuve et formulation."),
            _action("Rattacher preuves", "Disponible", "Nommer les pieces attendues avant diffusion."),
            _action("Preparer export de travail", "Bloquee", "Diffusion et reserves restent a decider."),
            _action("Envoyer convocation", "Bloquee", "Action officielle hors CoproScope."),
            _action("Publier proces-verbal", "Bloquee", "Aucun document officiel n'est produit ici."),
            _action("Enregistrer vote", "Bloquee", "L'atelier ne valide aucun vote d'assemblee."),
        ],
        "version_log": [
            "Atelier cree sur donnees fictives.",
            "Questions et resolutions marquees comme brouillons.",
            "Diffusion bloquee avant controle humain.",
        ],
        "shell_model": _synthetic_shell_model(year),
    }


def _metric(label: str, value: str, detail: str) -> dict[str, str]:
    return {"label": label, "value": value, "detail": detail}


def _entry(label: str, detail: str) -> dict[str, str]:
    return {"label": label, "detail": detail}


def _agenda(
    item_id: str,
    item_type: str,
    title: str,
    status: str,
    proof: str,
    next_action: str,
) -> dict[str, str]:
    return {
        "id": item_id,
        "type": item_type,
        "title": title,
        "status": status,
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
                "page_title": "Atelier AG",
                "active_page": "governance_atelier_ag",
                "search_placeholder": "Rechercher une question, une preuve ou un brouillon fictif...",
                "notification_count": 0,
                "sharing_mode_label": "Interne local",
                "sharing_mode_status": "Projet CS non officiel",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
