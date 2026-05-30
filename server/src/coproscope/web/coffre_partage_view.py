from typing import Any


def register_coffre_partage_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from fastapi import Request as FastAPIRequest

    @app.get("/coffre/partage", response_class=html_response)
    def coffre_partage(request: FastAPIRequest):
        require_token(request)
        view = build_coffre_partage_view(year)
        return templates.TemplateResponse(
            request=request,
            name="coffre_partage.html",
            context=context(request, "coffre_partage", model=view["shell_model"], coffre_partage=view),
        )


def build_coffre_partage_view(year: int = 2025) -> dict[str, Any]:
    """Return a synthetic, non-operational sharing view for the local UI."""
    rights = ["Lire", "Ajouter", "Valider", "Exporter", "Peut gerer les acces"]
    return {
        "title": "Coffre et partage",
        "notice": "Scenario FICTIF: aucun partage reel, aucune invitation envoyee.",
        "status": {
            "label": "Verification requise avant partage",
            "tone": "review",
            "summary": "Le coffre local peut etre relu, mais les invitations, exports et retraits restent bloques.",
            "cta": "Verifier avant partage",
        },
        "mental_model": [
            _model_item("Coffre local", "Reference de travail sur cet ordinateur, a verifier avant diffusion."),
            _model_item("Transport chiffre", "Le cloud transporte un paquet chiffre; il ne decide pas les droits."),
            _model_item("Personnes", "Chaque personne a des droits separes et limites."),
            _model_item("Ordinateurs reconnus", "Un nouvel ordinateur doit etre confirme avant d'acceder au coffre."),
            _model_item("Referent de secours", "Une recuperation demande une trace et une validation visible."),
        ],
        "before_share": [
            _gate("Droits relus", "A faire", "Confirmer qui peut lire, ajouter, valider, exporter ou gerer les acces."),
            _gate("Coffre verifie", "A faire", "Verifier qu'aucun conflit de version ne bloque le partage."),
            _gate("Ordinateur reconnu", "A faire", "Autoriser explicitement l'ordinateur avant toute invitation."),
            _gate("Diffusion prudente", "A faire", "Relire la forme partageable et les limites du retrait."),
        ],
        "members": [
            _member("CS-01", "Referente conseil syndical", ("Lire", "Ajouter", "Valider"), "Actif"),
            _member("CS-02", "Membre lecture seule", ("Lire",), "Actif"),
            _member("SECOURS-01", "Referent de secours", ("Lire",), "A confirmer"),
        ],
        "rights": rights,
        "actions": [
            _blocked_action("Preparer une invitation", "Coffre non verifie et ordinateur destinataire non confirme."),
            _blocked_action("Exporter un paquet chiffre", "Decision de diffusion et forme de sortie non relues."),
            _blocked_action("Retirer un acces", "Retirer l'acces n'efface pas les copies deja obtenues."),
            _blocked_action("Demander une recuperation", "Motif, referent de secours et validation humaine requis."),
            _blocked_action("Choisir la version de reference", "Deux versions du coffre existent; conflit a traiter avant partage."),
        ],
        "states": {
            "invitation": {
                "label": "Invitation bloquee",
                "detail": "Brouillon possible seulement apres relecture des droits et du destinataire.",
            },
            "revocation": {
                "label": "Retrait prudent",
                "detail": "La page rappelle que le retrait ne supprime pas les copies deja obtenues.",
            },
            "recovery": {
                "label": "Recuperation encadree",
                "detail": "Motif, referent et trace sont obligatoires; aucune recuperation solitaire.",
            },
            "conflict": {
                "label": "Deux versions du coffre existent",
                "detail": "Invitation et export bloques tant qu'une version de reference n'est pas choisie.",
            },
        },
        "audit_trail": [
            "Verification des droits a faire avant partage.",
            "Invitation et export bloques sur donnees fictives.",
            "Conflit de version a traiter avant diffusion.",
        ],
        "shell_model": _synthetic_shell_model(year),
    }


def _model_item(label: str, detail: str) -> dict[str, str]:
    return {"label": label, "detail": detail}


def _gate(label: str, status: str, detail: str) -> dict[str, str]:
    return {"label": label, "status": status, "detail": detail}


def _member(member_id: str, label: str, rights: tuple[str, ...], status: str) -> dict[str, Any]:
    return {"id": member_id, "label": label, "rights": list(rights), "status": status}


def _blocked_action(label: str, reason: str) -> dict[str, str]:
    return {"label": label, "enabled": "false", "reason": reason}


def _synthetic_shell_model(year: int) -> dict[str, Any]:
    return {
        "instance": {"id": "FICTIF", "name": "Copropriete FICTIVE", "root": "", "year": year},
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Coffre et partage",
                "active_page": "coffre_partage",
                "search_placeholder": "Rechercher une personne, un droit ou une trace fictive...",
                "notification_count": 0,
                "sharing_mode_label": "Lecture locale",
                "sharing_mode_status": "Aucun partage reel depuis cette page",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
