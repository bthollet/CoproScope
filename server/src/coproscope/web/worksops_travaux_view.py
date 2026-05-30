from typing import Any


def register_travaux_routes(app: Any, templates: Any, context: Any, year: int, require_token: Any, html_response: Any) -> None:
    from fastapi import Request as FastAPIRequest

    @app.get("/travaux", response_class=html_response)
    def travaux_suivis(request: FastAPIRequest):
        require_token(request)
        travaux = build_travaux_suivis_view(year)
        return templates.TemplateResponse(
            request=request,
            name="travaux.html",
            context=context(request, "travaux", model=travaux["shell_model"], travaux=travaux),
        )


def build_travaux_suivis_view(year: int = 2025) -> dict[str, Any]:
    """Return a fully synthetic works follow-up view for the local UI."""
    chantier = {
        "id": "TRV-FICTIF-001",
        "label": "Ravalement cour interieure - FICTIF",
        "status": "En attente d'une preuve avant etape suivante",
        "step": "3 sur 5",
        "owner": "Conseil syndical et syndic",
        "due": f"30/06/{year}",
        "share_status": "Partage possible seulement apres verification humaine",
    }
    pieces_confirmees = [
        _piece("PV-AG-FICTIF-2026-07", "Decision AG de principe", "Confirmee", "Cite la decision et le budget plafond."),
        _piece("DEV-FICTIF-ENT-A", "Devis entreprise A", "Confirmee", "Montant et lot de travaux lisibles."),
        _piece("ASS-FICTIF-ENT-A", "Attestation assurance entreprise", "Confirmee", "Reference courte disponible pour le suivi."),
    ]
    pieces_a_verifier = [
        _piece("DEV-FICTIF-ENT-B", "Devis entreprise B", "A verifier", "Verifier si la variante est comparable."),
        _piece("PLANNING-FICTIF-01", "Planning d'intervention", "A verifier", "Date de debut a confirmer avec le syndic."),
    ]
    pieces_manquantes = [
        _piece("AUT-FICTIF-VOIRIE", "Autorisation de pose d'echafaudage", "Manquante", "Necessaire avant commande ferme."),
        _piece("PHOTO-FICTIF-AVANT", "Photos avant travaux", "Manquante", "Preuve attendue pour comparer l'etat initial."),
    ]
    blockers = [
        {
            "label": "Autorisation non recue",
            "why": "Sans autorisation d'echafaudage, la date de debut ne peut pas etre confirmee.",
            "next": "Demander au syndic le numero ou la date de reception de l'autorisation d'echafaudage.",
        },
        {
            "label": "Comparaison devis incomplete",
            "why": "Une option du second devis n'est pas comparable au devis principal.",
            "next": "Faire preciser si la variante couvre le meme perimetre, les memes materiaux et la meme duree.",
        },
    ]
    actions = [
        {
            "label": "Preparer une demande",
            "href": "/demandes?from=travaux&preuve=autorisation-echafaudage",
            "detail": "Brouillon local: demander l'autorisation d'echafaudage et les photos avant travaux, sans envoi automatique.",
        },
        {
            "label": "Voir l'apercu avant partage",
            "href": "/travaux?view=apercu",
            "detail": "Relire le resume diffusable avant de le montrer hors conseil syndical.",
        },
    ]
    return {
        "title": "Travaux suivis",
        "notice": "Scenario FICTIF avec donnees synthetiques, sans document reel.",
        "chantier": chantier,
        "summary": {
            "confirmed": len(pieces_confirmees),
            "to_verify": len(pieces_a_verifier),
            "missing": len(pieces_manquantes),
            "blockers": len(blockers),
        },
        "progress": [
            {"label": "Decision reperee", "state": "fait", "detail": "Le point AG fictif est rattache au suivi."},
            {"label": "Devis principal lu", "state": "fait", "detail": "Le devis A est pret a etre compare."},
            {"label": "Preuve administrative", "state": "bloque", "detail": "L'autorisation d'echafaudage manque."},
            {
                "label": "Partage conseil",
                "state": "a verifier",
                "detail": "Preparer seulement une synthese pour le conseil syndical, puis relire avant diffusion.",
            },
            {"label": "Suivi apres travaux", "state": "a venir", "detail": "Photos et reserve de reception a preparer."},
        ],
        "blockers": blockers,
        "missing_proof": {
            "title": "Ce qui manque pour continuer",
            "items": pieces_manquantes,
            "next": "Obtenir une preuve courte et lisible avant de presenter la suite comme acquise.",
        },
        "pieces": {
            "confirmed": pieces_confirmees,
            "to_verify": pieces_a_verifier,
            "missing": pieces_manquantes,
        },
        "actions": actions,
        "share": {
            "status": "A verifier avant partage",
            "can_share": "Pas encore: une preuve manque et deux pieces doivent etre relues.",
            "allowed": [
                "Synthese courte du statut du chantier",
                "Liste des pieces deja confirmees",
                "Question a poser au syndic",
            ],
            "not_allowed": [
                "Presenter la date de demarrage comme certaine",
                "Joindre une piece non relue",
                "Dire qu'un controle juridique ou comptable est automatique",
            ],
        },
        "preview": {
            "title": "Apercu partageable a relire",
            "body": (
                "Le chantier fictif avance, mais le partage doit rester prudent: "
                "autorisation d'echafaudage attendue, variante de devis a comparer poste par poste, "
                "photos avant travaux manquantes."
            ),
        },
        "shell_model": _synthetic_shell_model(year),
    }


def _piece(ref: str, label: str, status: str, detail: str) -> dict[str, str]:
    return {"ref": ref, "label": label, "status": status, "detail": detail}


def _synthetic_shell_model(year: int) -> dict[str, Any]:
    return {
        "instance": {"id": "FICTIF", "name": "Copropriete FICTIVE", "root": "", "year": year},
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Travaux suivis",
                "active_page": "travaux",
                "search_placeholder": "Rechercher une piece fictive, une action ou un chantier...",
                "notification_count": 0,
                "sharing_mode_label": "Lecture locale",
                "sharing_mode_status": "Aucun partage lance depuis cette page",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
