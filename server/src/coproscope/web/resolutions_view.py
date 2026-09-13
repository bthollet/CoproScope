"""Vue des resolutions d'assemblee, lue depuis le registre.

Trois regles d'affichage, tirees de defauts constates sur l'interface reelle:

- **jamais d'ecran vide silencieux.** Registre non declare, extraction non
  lancee, aucune resolution: chaque cas rend un etat explicite qui dit ce qui
  manque et comment le construire. Ailleurs dans le produit, une source absente
  rend une liste vide et laisse croire qu'il n'y a rien a faire;
- **l'ordre est celui du document.** Trier par confiance croissante mettrait les
  cas incomprehensibles en premier, alors que le lecteur se forme en lisant. Les
  anomalies sont marquees la ou elles sont, pas remontees en tete;
- **la qualite d'extraction est affichee, pas cachee.** Une numerotation deduite
  et une confiance faible se voient sur la ligne concernee.

Deux regles ajoutees le 2026-09-04, apres recette sur instance reelle:

- **une assemblee, une ligne.** Le registre peut contenir plusieurs lectures du
  meme proces-verbal - l'original, sa conversion texte, une recomposition a
  partir de documents scindes. Elles etaient rendues comme autant d'assemblees
  distinctes, dont une aux comptages faux, sans que rien ne dise laquelle
  faisait foi. Le regroupement et l'election sont dans
  `_resolutions_assemblees`; ici on ne fait qu'en tirer l'affichage. Aucune
  ligne n'est supprimee du registre: les versions ecartees sont nommees, avec
  leur motif;
- **jamais d'identifiant technique devant un lecteur.** Quand la date de
  l'assemblee n'a pas ete extraite du document, l'identifiant interne retombe
  sur la reference du fichier. L'afficher en guise de titre est un defaut de
  produit, pas un detail: le titre dit alors ce qui est su, et ce qui ne l'est
  pas.
"""

from __future__ import annotations

from typing import Any

from ..core.common import InstanceConfig
from ..vault.gouvernance_store import GouvernanceStoreIndisponible, lire, store_path
from ._resolutions_assemblees import (
    attestations_depuis,
    elire,
    formes_par_document,
    motif_ecart,
    regrouper,
)

REGISTRE_ABSENT = "registre_absent"
REGISTRE_VIDE = "registre_vide"
PRET = "pret"

# Une resolution votee dont l'adoption n'est pas enoncee, ou lue avec une
# confiance faible, appelle une relecture humaine. Les deux etats ou le
# proces-verbal conclut sans qu'on sache lire sa conclusion en font partie: ils
# ne sont pas un fait sur l'assemblee, ils sont une lecture a refaire.
RESULTATS_A_RELIRE = {
    "VOTE_SANS_FORMULE",
    "SANS_ISSUE_TRACEE",
    "ISSUE_NON_RECONNUE",
    "ISSUE_ENONCEE_NON_LUE",
}

# Le libelle est ce que le coproprietaire lit. Trois etats voisins se
# distinguent ici par une seule question, posee en clair: **le proces-verbal
# conclut-il ?**
#
#   SANS_ISSUE_TRACEE      il ne conclut pas - rien a relire, c'est le document
#                          qui est muet, et c'est un constat sur l'assemblee;
#   ISSUE_NON_RECONNUE     il conclut, avec des mots que le logiciel ne connait
#                          pas encore;
#   ISSUE_ENONCEE_NON_LUE  il conclut, et le logiciel n'a meme pas su reperer sa
#                          phrase de conclusion.
#
# Les deux derniers ne disent rien de l'assemblee: ils disent que la lecture
# reste a faire. Ecrire sur eux « issue non tracee » revenait a reprocher au
# document un silence qui etait le notre.
LIBELLES_RESULTAT = {
    "ADOPTEE": "Adoptée",
    "REJETEE": "Rejetée",
    "PAS_DE_VOTE": "Pas de vote",
    "VOTE_SANS_FORMULE": "Votée sans adoption énoncée",
    "SANS_ISSUE_TRACEE": "Le procès-verbal ne conclut pas",
    "ISSUE_NON_RECONNUE": "Conclusion écrite en mots inconnus, à relire",
    "ISSUE_ENONCEE_NON_LUE": "Conclusion écrite, non lue par le logiciel, à relire",
    "SANS_OBJET": "Sans objet",
    "REPORTEE": "Reportée",
    "PROJET": "Projet, non voté",
}

LIBELLES_QUALIFICATION = {
    "SEUIL_CONSULTATION_CS": "Seuil de consultation du conseil syndical",
    "SEUIL_MISE_EN_CONCURRENCE": "Seuil de mise en concurrence",
    "MISE_EN_CONCURRENCE_PRODUITE": "Plusieurs devis présentés",
    "DELEGATION_CS": "Délégation au conseil syndical",
    "MANDAT_SYNDIC": "Mandat d'exécution au syndic",
    "APPROBATION_COMPTES": "Approbation des comptes",
    "BUDGET_PREVISIONNEL": "Budget prévisionnel",
    "FONDS_TRAVAUX": "Fonds de travaux",
}


def _etat_vide(etat: str, message: str, action: str) -> dict[str, Any]:
    return {
        "disponible": False,
        "etat": etat,
        "message": message,
        "action": action,
        "assemblees": [],
        "total": 0,
    }


def _ligne(row: dict[str, str]) -> dict[str, Any]:
    resultat = row.get("resultat", "")
    confiance = row.get("confiance", "")
    qualifications = [q for q in (row.get("qualifications") or "").split(";") if q]
    return {
        "numero": row.get("numero", ""),
        "objet": row.get("objet", ""),
        "decision_actee": row.get("decision_actee", ""),
        "majorite": row.get("majorite_appliquee", ""),
        "majorite_annoncee": row.get("majorite_annoncee", ""),
        "passerelle": row.get("passerelle_utilisee") == "oui",
        "resultat": resultat,
        "resultat_libelle": LIBELLES_RESULTAT.get(resultat, resultat or "—"),
        "voix_pour": row.get("voix_pour", ""),
        "voix_contre": row.get("voix_contre", ""),
        "base_voix": row.get("base_voix", ""),
        "etat": row.get("etat", "CONSTATEE"),
        "origine": row.get("origine", "EXTRAIT"),
        "confiance": confiance,
        "numerotation": row.get("numerotation", "lue"),
        "qualifications": [
            LIBELLES_QUALIFICATION.get(q, q) for q in qualifications
        ],
        "duree_mois": row.get("duree_mois", ""),
        "valide_du": row.get("valide_du", ""),
        "valide_au": row.get("valide_au", ""),
        "a_relire": resultat in RESULTATS_A_RELIRE or confiance == "faible",
    }


def build_resolutions_view(instance: InstanceConfig) -> dict[str, Any]:
    """Modele d'affichage des resolutions, par assemblee."""
    try:
        store_path(instance)
    except GouvernanceStoreIndisponible:
        return _etat_vide(
            REGISTRE_ABSENT,
            "Le coffre local n'est pas configuré pour cette copropriété.",
            "Déclarez « settings.vault.local_root » dans instance.yml, "
            "puis redéposez un procès-verbal.",
        )

    rows = lire(instance)
    if not rows:
        return _etat_vide(
            REGISTRE_VIDE,
            "Le registre existe mais ne contient aucune résolution.",
            "Un procès-verbal a peut-être été déposé sans couche texte lisible. "
            "Vérifiez sa qualité d'extraction dans les documents.",
        )

    attestations = attestations_depuis(rows, formes_par_document(instance))
    assemblees = [_assemblee(groupe) for groupe in regrouper(attestations)]
    # Les assemblees datees d'abord, de la plus recente a la plus ancienne;
    # celles dont la date n'a pas ete lue ferment la liste plutot que de se
    # glisser au hasard de leur reference interne.
    assemblees.sort(key=lambda ag: (ag["date"] == "", _ordre_inverse(ag["date"])))

    return {
        "disponible": True,
        "etat": PRET,
        "message": "",
        "action": "",
        "assemblees": assemblees,
        "total": sum(ag["total"] for ag in assemblees),
        # **Le total DECLARE ce qu'il compte plusieurs fois** (`RM-2026-0077`).
        # La ligne ci-dessus somme les assemblees affichees; quand la meme
        # matiere figure sous deux d'entre elles, elle y entre deux fois, et un
        # nombre nu ne le laisse pas voir.
        "total_partage": _conservation(assemblees),
        "lignes_registre": len(rows),
        "versions_ecartees": sum(len(ag["versions_ecartees"]) for ag in assemblees),
    }


def _conservation(assemblees: list[dict[str, Any]]) -> int:
    """Combien de lignes du total existent AUSSI sous une autre assemblee.

    **Ce que ce nombre dit, et ce qu'il ne dit pas.** Il ne dit pas *ce sont des
    doublons*: la raison du partage - un proces-verbal relu, un recueil qui
    reprend plusieurs assemblees, une resolution de seance qui revient chaque
    annee - reste ouverte, et `_resolutions_recouvrement` explique pourquoi la
    trancher demanderait de conclure sur une ressemblance. Il dit ce qui est
    vrai dans tous les cas: **un total obtenu par sommation compte ces lignes
    plusieurs fois.**

    **L'identite employee est l'ASSEMBLEE AFFICHEE, et c'est deliberé.** Le
    total somme ce que la page montre; la conservation doit donc porter sur
    cette population-la, et non sur les identifiants du registre, que la vue a
    parfois deja regroupes. Prendre l'identifiant amont ferait crier la garde
    sur un rapprochement que l'ecran a justement opere.

    Le calcul n'est pas refait ici: il est **delegue** au module qui le porte
    deja. Deux implantations d'une meme notion, c'est le defaut numero un du
    produit - plusieurs comptages concurrents pour la meme chose.
    """
    from ..modules._resolutions_assemblees import NATURE_RESOLUTION
    from ..modules._resolutions_recouvrement import conservation_du_total

    lignes: list[dict[str, Any]] = []
    for rang, assemblee in enumerate(assemblees):
        for ligne in assemblee["resolutions"]:
            lignes.append({
                "nature": NATURE_RESOLUTION,
                "ag_id": "affichee-%d" % rang,
                "numero": ligne.get("numero", ""),
                "sous_numero": ligne.get("sous_numero", ""),
                "objet": ligne.get("objet", ""),
            })
    return conservation_du_total(lignes)["actes_partages"]


def _ordre_inverse(date: str) -> str:
    """Cle de tri decroissante sur une date ISO, sans inverser toute la liste."""
    return "".join(chr(ord("9") - int(car)) if car.isdigit() else car for car in date)


COMPTES = {
    "adoptees": ("ADOPTEE",),
    "rejetees": ("REJETEE",),
    "sans_vote": ("PAS_DE_VOTE", "SANS_OBJET", "REPORTEE"),
}


def _comptages(lignes: list[dict[str, Any]]) -> dict[str, int]:
    """Trois comptages, plus le reste - pour que l'addition retombe juste.

    Les trois compteurs ne couvraient pas tous les resultats possibles: une
    resolution votee sans adoption enoncee, une issue non tracee ou un
    vocabulaire de cloture non reconnu n'entrait dans aucun d'eux. Un lecteur
    qui additionnait les trois chiffres ne retombait pas sur le total et n'avait
    aucun moyen de savoir pourquoi. `hors_comptage` porte cette difference.
    """
    comptages = {
        cle: sum(1 for l in lignes if l["resultat"] in valeurs)
        for cle, valeurs in COMPTES.items()
    }
    comptages["hors_comptage"] = len(lignes) - sum(comptages.values())
    return comptages


def _assemblee(groupe: list[Any]) -> dict[str, Any]:
    """Une assemblee affichable: la version qui fait foi, et ce qui est ecarte."""
    retenue, ecartees = elire(groupe)
    # L'ordre du document, pas un tri par confiance.
    lignes = [_ligne(row) for row in retenue.lignes]
    comptages = _comptages(lignes)
    date = retenue.date or next((a.date for a in ecartees if a.date), "")
    taille_serie = len({num for attestation in groupe for num in attestation.numeros})

    return {
        "date": date,
        # Un titre lisible, jamais une reference interne de fichier. Sans date
        # lue, le titre le dit; il ne le remplace pas par un identifiant.
        "titre": f"Assemblee du {date}" if date else "Assemblee dont la date n'a pas ete lue",
        "date_lue": bool(date),
        "total": len(lignes),
        **comptages,
        "a_relire": sum(1 for l in lignes if l["a_relire"]),
        "passerelles": sum(1 for l in lignes if l["passerelle"]),
        "numerotation": lignes[0]["numerotation"] if lignes else "lue",
        "resolutions": lignes,
        "versions_ecartees": [
            motif_ecart(
                ecartee,
                retenue,
                taille_serie=taille_serie,
                comptages_retenue=comptages,
                comptages_ecartee=_comptages([_ligne(row) for row in ecartee.lignes]),
            )
            for ecartee in ecartees
        ],
    }
