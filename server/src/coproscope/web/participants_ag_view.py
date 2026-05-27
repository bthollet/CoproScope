from typing import Any


def register_participants_ag_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from fastapi import Request as FastAPIRequest

    @app.get("/gouvernance/participants-ag", response_class=html_response)
    def participants_ag(request: FastAPIRequest):
        require_token(request)
        view = build_participants_ag_view(year)
        return templates.TemplateResponse(
            request=request,
            name="participants_ag.html",
            context=context(request, "participants_ag", model=view["shell_model"], participants_ag=view),
        )


def build_participants_ag_view(year: int = 2025) -> dict[str, Any]:
    """Return a synthetic AG participants and rights verification view."""
    return {
        "title": "Participants et droits AG",
        "notice": "Scenario FICTIF: liste de travail, aucun import reel, aucun vote officiel.",
        "status": {
            "label": "Verification humaine requise",
            "summary": "La liste aide a preparer l'AG, mais elle ne remplace pas le dossier officiel.",
            "cta": "Verifier les pouvoirs",
        },
        "summary": [
            _metric("Coproprietaires a verifier", "4", "Lignes fictives a relire avant toute convocation."),
            _metric("Pouvoirs recus", "2", "Mandats fictifs recus, dont un incomplet."),
            _metric("Votes incomplets", "3", "Presences, voix ou votes par correspondance a confirmer."),
        ],
        "boundaries": [
            _entry("Liste de travail", "Ne vaut pas dossier officiel de copropriete."),
            _entry("Aucun import reel", "Les donnees affichees sont synthetiques."),
            _entry("Aucune convocation", "La page ne prepare ni n'envoie de convocation."),
            _entry("Aucun vote officiel", "Les decisions d'AG restent hors de ce prototype."),
        ],
        "definitions": [
            _entry("Voix AG", "Nombre de voix utilise pour voter une resolution."),
            _entry("Pouvoir", "Document par lequel un coproprietaire confie son vote."),
            _entry("Mandataire", "Personne qui vote pour un coproprietaire absent."),
            _entry(
                "Feuille de presence",
                "Preuve de qui etait present, represente ou a vote par correspondance.",
            ),
        ],
        "participants": [
            _participant(
                "OWN-FICTIF-01",
                "LOT-A12",
                "Coproprietaire",
                "Vote direct",
                "Pouvoir absent",
                "120",
                "Presence a confirmer",
                "Verifier si la personne vient ou donne pouvoir.",
            ),
            _participant(
                "OWN-FICTIF-02",
                "LOT-B03",
                "Coproprietaire bailleur",
                "Pouvoir donne",
                "Mandataire a verifier",
                "80",
                "Pret pour revue",
                "Verifier que le mandataire peut porter ces voix.",
            ),
            _participant(
                "OWN-FICTIF-03",
                "LOT-C01 + LOT-C02",
                "Representant a nommer",
                "Vote bloque",
                "Pouvoir manquant",
                "160",
                "Bloquant",
                "Representant legal non confirme.",
            ),
            _participant(
                "OWN-FICTIF-04",
                "LOT-D07",
                "Indivision a clarifier",
                "Vote a verifier",
                "Pouvoir recu incomplet",
                "40",
                "A clarifier",
                "Verifier la personne qui peut voter pour ce lot.",
            ),
        ],
        "attendance": [
            _entry("Presents", "2 participants fictifs indiques comme presents ou attendus."),
            _entry("Representes", "1 pouvoir fictif a relire avant feuille de presence."),
            _entry("Correspondance", "1 vote par correspondance incomplet a verifier."),
        ],
        "resolutions": [
            _resolution("RES-FICTIF-01", "Budget travaux", "240 voix attendues", "Pieces et pouvoirs a relire."),
            _resolution("RES-FICTIF-02", "Election conseil", "120 voix incompletes", "Mandataire a confirmer."),
            _resolution("RES-FICTIF-03", "Question syndic", "40 voix bloquees", "Indivision a clarifier."),
        ],
        "checks": [
            _entry("Identite", "Nom, lot et role compris par un lecteur non specialiste."),
            _entry("Droit de vote", "Vote direct, pouvoir donne ou vote bloque visibles sans jargon."),
            _entry("Preuve attendue", "Chaque blocage indique la piece ou confirmation a demander."),
            _entry("Synthese derivee", "Un export futur devra marquer source_of_truth=false."),
        ],
        "blocked_sources": [
            _entry("Chemin local refuse", "Aucun dossier brut ne peut etre saisi comme source partageable."),
            _entry("Piece brute exclue", "Pouvoirs et feuille de presence restent en controle local."),
            _entry("Sortie large limitee", "Aucun annuaire ni feuille officielle ne sort de cette page."),
        ],
        "actions": [
            _action("Verifier les pouvoirs", "Disponible", "Relire les mandats avant toute AG."),
            _action("Demander confirmation au syndic", "Disponible", "Preparer une question, sans envoi automatique."),
            _action("Importer une liste reelle", "Bloquee", "Import reel absent de cette iteration."),
            _action("Exporter une feuille de presence", "Bloquee", "Aucun export officiel depuis cette page."),
            _action("Enregistrer un vote officiel", "Bloquee", "La page ne valide aucun vote d'AG."),
            _action("Envoyer une convocation", "Bloquee", "Toute convocation se prepare et s'envoie hors CoproScope."),
        ],
        "version_log": [
            "Liste creee sur donnees fictives.",
            "Pouvoirs et representants marques a verifier.",
            "Actions officielles bloquees avant toute integration metier.",
        ],
        "shell_model": _synthetic_shell_model(year),
    }


def _metric(label: str, value: str, detail: str) -> dict[str, str]:
    return {"label": label, "value": value, "detail": detail}


def _entry(label: str, detail: str) -> dict[str, str]:
    return {"label": label, "detail": detail}


def _participant(
    owner_id: str,
    lot: str,
    role: str,
    vote: str,
    power: str,
    ag_voices: str,
    status: str,
    caution: str,
) -> dict[str, str]:
    return {
        "owner_id": owner_id,
        "lot": lot,
        "role": role,
        "vote": vote,
        "power": power,
        "ag_voices": ag_voices,
        "status": status,
        "caution": caution,
    }


def _action(label: str, state: str, reason: str) -> dict[str, str]:
    return {"label": label, "state": state, "reason": reason, "enabled": "true" if state == "Disponible" else "false"}


def _resolution(resolution_id: str, title: str, voices: str, follow_up: str) -> dict[str, str]:
    return {"id": resolution_id, "title": title, "voices": voices, "follow_up": follow_up}


def _synthetic_shell_model(year: int) -> dict[str, Any]:
    return {
        "instance": {"id": "FICTIF", "name": "Copropriete FICTIVE", "root": "", "year": year},
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Participants et droits AG",
                "active_page": "participants_ag",
                "search_placeholder": "Rechercher un lot, un pouvoir ou une resolution fictive...",
                "notification_count": 0,
                "sharing_mode_label": "Interne local",
                "sharing_mode_status": "Aucun import reel ni export officiel",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
