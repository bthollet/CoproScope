from typing import Any


def register_roles_commissions_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from fastapi import Request as FastAPIRequest

    @app.get("/gouvernance/roles-commissions", response_class=html_response)
    def roles_commissions(request: FastAPIRequest):
        require_token(request)
        view = build_roles_commissions_view(year)
        return templates.TemplateResponse(
            request=request,
            name="roles_commissions.html",
            context=context(request, "roles_commissions", model=view["shell_model"], roles_commissions=view),
        )


def build_roles_commissions_view(year: int = 2025) -> dict[str, Any]:
    """Return a synthetic roles and commissions view without applying rights."""
    right_labels = ("Lire", "Ajouter", "Valider", "Diffuser", "Gerer acces")
    return {
        "title": "Roles et commissions",
        "notice": "Scenario FICTIF: profils synthetiques, aucun annuaire reel, aucun droit applique.",
        "status": {
            "label": "Validation humaine obligatoire",
            "summary": "La page aide a relire les roles, commissions et droits par ressource avant partage.",
            "cta": "Relire les droits par ressource",
        },
        "summary": [
            _metric("Profils synthetiques", "5", "Personnes fictives pour tester les consequences des droits."),
            _metric("Commissions", "3", "Travaux, finances et communication separes par responsabilite."),
            _metric("Ressources protegees", "6", "Chaque ressource a une diffusion et une preuve attendue."),
            _metric("Actions sensibles", "5", "Invitations, retraits et exports restent bloques."),
        ],
        "boundaries": [
            _entry("Aucun annuaire reel", "Les lignes ne viennent pas du fichier coproprietaires."),
            _entry("Aucun droit applique", "La matrice sert a relire; elle ne change aucun acces."),
            _entry("Aucune invitation", "Aucun message, partage ou cloud n'est declenche."),
            _entry("Aucune sortie large", "Les productions restent des syntheses a verifier."),
        ],
        "definitions": [
            _entry("Role", "Responsabilite lisible par un membre du conseil syndical."),
            _entry("Commission", "Petit groupe charge d'un sujet: travaux, finances ou communication."),
            _entry("Referent", "Personne qui prepare une verification, sans pouvoir automatique."),
            _entry("Ressource", "Ecran, dossier derive ou production dont l'acces doit etre limite."),
        ],
        "profiles": [
            _profile(
                "PROF-FICTIF-01",
                "Referente travaux",
                "Commission travaux",
                "Peut preparer les preuves chantier, sans diffuser seule.",
                "A confirmer",
            ),
            _profile(
                "PROF-FICTIF-02",
                "Tresorier CS",
                "Commission finances",
                "Peut relire charges et contrats, export bloque sans validation.",
                "Actif fictif",
            ),
            _profile(
                "PROF-FICTIF-03",
                "Relais communication",
                "Messages et courriers",
                "Prepare les reponses, aucun envoi automatique.",
                "A relire",
            ),
            _profile(
                "PROF-FICTIF-04",
                "Lecteur commission",
                "Lecture limitee",
                "Lit seulement les syntheses partageables de sa commission.",
                "Limite",
            ),
            _profile(
                "PROF-FICTIF-05",
                "Referent de secours",
                "Recuperation encadree",
                "Peut aider a recuperer un coffre seulement avec trace et validation.",
                "Bloque par defaut",
            ),
        ],
        "commissions": [
            _commission(
                "Commission travaux",
                "Referente travaux",
                "Preuves chantier, incidents, contrats de travaux.",
                "Compte rendu de suivi, non diffusable sans revue.",
            ),
            _commission(
                "Commission finances",
                "Tresorier CS",
                "Charges, contrats, budgets et indicateurs financiers.",
                "Synthese de controle, source_of_truth=false.",
            ),
            _commission(
                "Commission communication",
                "Relais communication",
                "Messages recus, courriers, demandes et reponses a preparer.",
                "Brouillon relu, aucun envoi automatique.",
            ),
        ],
        "right_labels": right_labels,
        "rights_matrix": [
            _rights_row("Coffre travaux", ("Lire", "Ajouter"), "Preuves chantier a relire avant diffusion."),
            _rights_row("Contrats", ("Lire", "Ajouter", "Valider"), "Echeances et attestations, sans alerte juridique auto."),
            _rights_row("Messages recus", ("Lire", "Ajouter"), "Qualification et moderation, aucune publication auto."),
            _rights_row("Courriers preuves", ("Lire", "Ajouter", "Valider"), "Brouillon et preuve, aucun envoi."),
            _rights_row("Participants AG", ("Lire",), "Droits AG et pouvoirs visibles en synthese seulement."),
            _rights_row("Exports derives", ("Lire", "Valider"), "Export marque derive et source_of_truth=false."),
        ],
        "production_gates": [
            _entry("Sujet nomme", "Chaque production indique commission, referent et ressource."),
            _entry("Preuve attendue", "La preuve ou la limite est visible avant partage."),
            _entry("Audience relue", "Coproprietaires, CS ou commission ne sont jamais confondus."),
            _entry("Trace locale", "Toute decision sensible reste a valider hors automatisme."),
        ],
        "actions": [
            _action("Inviter un membre", "Bloquee", "Invitation reelle absente de cette iteration."),
            _action("Changer un droit", "Bloquee", "La matrice n'applique aucun droit."),
            _action("Retirer un acces", "Bloquee", "Retrait reel et copies deja obtenues demandent une procedure separee."),
            _action("Exporter un annuaire", "Bloquee", "Aucun annuaire coproprietaire ne sort de cette page."),
            _action("Publier une production", "Bloquee", "Validation humaine et diffusion restent obligatoires."),
        ],
        "version_log": [
            "Vue creee sur profils FICTIFS.",
            "Droits par ressource limites a une matrice de relecture.",
            "Actions sensibles bloquees avant tout connecteur ou application de droit.",
        ],
        "shell_model": _synthetic_shell_model(year),
    }


def _metric(label: str, value: str, detail: str) -> dict[str, str]:
    return {"label": label, "value": value, "detail": detail}


def _entry(label: str, detail: str) -> dict[str, str]:
    return {"label": label, "detail": detail}


def _profile(profile_id: str, label: str, scope: str, responsibility: str, status: str) -> dict[str, str]:
    return {
        "id": profile_id,
        "label": label,
        "scope": scope,
        "responsibility": responsibility,
        "status": status,
    }


def _commission(label: str, referent: str, scope: str, production: str) -> dict[str, str]:
    return {"label": label, "referent": referent, "scope": scope, "production": production}


def _rights_row(resource: str, rights: tuple[str, ...], caution: str) -> dict[str, Any]:
    return {"resource": resource, "rights": list(rights), "caution": caution}


def _action(label: str, state: str, reason: str) -> dict[str, str]:
    return {"label": label, "state": state, "reason": reason, "enabled": "false"}


def _synthetic_shell_model(year: int) -> dict[str, Any]:
    return {
        "instance": {"id": "FICTIF", "name": "Copropriete FICTIVE", "root": "", "year": year},
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Roles et commissions",
                "active_page": "roles_commissions",
                "search_placeholder": "Rechercher un role, une commission ou une ressource fictive...",
                "notification_count": 0,
                "sharing_mode_label": "Droits a relire",
                "sharing_mode_status": "Aucun droit reel applique depuis cette page",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
