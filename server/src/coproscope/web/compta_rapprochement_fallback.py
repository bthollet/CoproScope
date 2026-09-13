from __future__ import annotations

from typing import Any

from ._identite_coque import identite_coque

from ..modules.accounting import COMPTASCOPE_REVIEW_FIELDS


def fallback_rows(year: int) -> list[dict[str, str]]:
    rows = [
        {
            "review_id": f"REV-{year}-FICTIF-001",
            "exercice": str(year),
            "priorite": "P1",
            "fournisseur": "Ascenseur FICTIF",
            "numero_facture": "FAC-FICT-001",
            "doc_id": "DOC-FICT-001",
            "ttc": "1200.00",
            "niveau_preuve": "facture extraite",
            "statut_rapprochement": "NON_RAPPROCHE",
            "libelle_statut": "A traiter avant assemblee",
            "motif": "Aucun mouvement compatible n'est rattache.",
            "prochaine_action": "Demander mouvement bancaire et decision ou devis.",
            "question_syndic": "Pouvez-vous transmettre le mouvement bancaire et le devis associe ?",
            "bloc_copiable": "Brouillon a copier, aucun envoi automatique: merci de transmettre le mouvement et la justification.",
        },
        {
            "review_id": f"REV-{year}-FICTIF-002",
            "exercice": str(year),
            "priorite": "P2",
            "fournisseur": "Nettoyage FICTIF",
            "numero_facture": "FAC-FICT-002",
            "doc_id": "DOC-FICT-002",
            "ttc": "480.00",
            "niveau_preuve": "facture et ligne candidate",
            "ligne_depense_candidate": "DEP-FICT-002",
            "reference_depense": "REF-FICT-002",
            "libelle_depense": "Entretien parties communes",
            "montant_depense": "480.00",
            "statut_rapprochement": "CANDIDAT_MONTANT_FAMILLE",
            "libelle_statut": "A confirmer",
            "motif": "Montant exact mais libelle a relire.",
            "prochaine_action": "Confirmer le fournisseur avant conclusion.",
        },
    ]
    return [{field: row.get(field, "") for field in COMPTASCOPE_REVIEW_FIELDS} for row in rows]


def shell_model(year: int, instance: Any | None = None) -> dict[str, Any]:
    """La coque du controle des comptes.

    `instance` est optionnel et par defaut absent, pour ne casser aucun appelant
    - mais l'omettre affiche `Copropriete FICTIVE` a la place du nom reel. C'est
    le defaut mesure le 2026-09-05: la meme instance rendait « Residence Les
    Platanes » sur `/controle-gouvernance` et « Copropriete FICTIVE » ici.
    """
    return {
        "instance": identite_coque(instance, year),
        "ux": {
            "shell": {
                "app_title": "CoproScope",
                "page_title": "Controle des comptes",
                "active_page": "accounting",
                "search_placeholder": "Rechercher fournisseur, facture ou ligne comptable...",
                "notification_count": 0,
                "sharing_mode_label": "Validation locale",
                "sharing_mode_status": "Aucun envoi ni export automatique",
            }
        },
        "action_summary": {"total": "", "accounting": "", "scope_counts": {}},
        "kpis": {"actions": "", "doc_requests": "", "decisions": "", "privacy_reviews": ""},
    }
