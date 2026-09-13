from typing import Any

from ._courriers_matiere import PRET, matiere_de_courriers
from ._identite_coque import identite_coque


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
        view = build_courriers_preuves_view(
            year, instance=getattr(app.state, "instance", None))
        return templates.TemplateResponse(
            request=request,
            name="courriers_preuves.html",
            context=context(request, "courriers_preuves", model=view["shell_model"], courriers_preuves=view),
        )


def build_courriers_preuves_view(
    year: int = 2025, *, instance: Any | None = None,
) -> dict[str, Any]:
    """Les courriers a ecrire, lus dans ce que la chaine a deja calcule.

    **Branche le 2026-09-11**, sur l'arbitrage de Brice - *« On branche les
    ecrans. »*

    **Le defaut corrige n'est pas celui qu'on attend.** Les trois brouillons
    inventes ne trompaient personne: leurs identifiants portaient `FICTIF`.
    **La page se contredisait elle-meme:** le bandeau annoncait *3 brouillons a
    valider* quand un seul portait ce statut, et *2 preuves* quand le tableau
    situe juste en dessous en comptait trois. Deux comptages ecrits a la main,
    pour la meme notion, a trois centimetres l'un de l'autre.

    Les compteurs comptent desormais la liste qu'ils annoncent, et rien
    d'autre.
    """
    matiere = matiere_de_courriers(instance)
    branche = matiere["etat"] == PRET
    preuves = matiere["preuves_attendues"]
    return {
        "title": "Courriers et preuves",
        "notice": (
            "Pièces à demander au syndic, calculées sur vos documents. "
            "Aucune transmission depuis CoproScope."
            if branche else
            "Scenario FICTIF: brouillons locaux, aucune transmission depuis CoproScope."
        ),
        "status": {
            "label": "Verification humaine requise",
            "summary": (matiere["message"] or
                        "CoproScope prepare le dossier, puis une personne agit hors application."),
            "cta": matiere["action"] or "Verifier avant envoi",
        },
        "etat_matiere": matiere["etat"],
        "summary": [
            _metric("Pièces à demander", str(matiere["compte"]),
                    "Courriers à écrire, calculés sur vos documents."),
            _metric("Dont priorité haute", str(matiere["haute_priorite"]),
                    "À traiter avant les autres."),
            _metric("Preuves d'envoi rattachées",
                    str(sum(p["rattaches"] for p in preuves)),
                    "Accusés de dépôt ou de réception reliés à une demande."),
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
        "drafts": matiere["brouillons"],
        "proofs": preuves,
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
        "shell_model": _synthetic_shell_model(year, instance),
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


def _synthetic_shell_model(
    year: int, instance: Any | None = None,
) -> dict[str, Any]:
    return {
        "instance": identite_coque(instance, year),
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
