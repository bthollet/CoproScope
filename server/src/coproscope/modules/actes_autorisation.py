"""Facade du modele relationnel actes / depenses / liens.

Point d'entree unique du lot. Les modules `_actes_*` sont prives et decoupes par
responsabilite: `_actes_schema` declare, `_actes_vues` calcule, `_actes_requetes`
filtre, `_actes_store` ecrit et lit.

Ce lot ne fabrique **aucun** rattachement automatique. Il rend la structure qui
le permettra: un lien porte sa provenance, son motif et son doute, et plusieurs
liens concurrents coexistent sur la meme paire. Qui rapproche quoi, et sur quels
indices, est une autre question - le modele la designe comme fragile, et elle
vient apres.
"""

from __future__ import annotations

import sqlite3

from typing import Any, Sequence

from ._actes_requetes import (
    COUT_AGREGAT,
    COUT_DIRECT,
    COUT_JOINTURE,
    FILTRES,
    SQL_ACTES_DU_DOSSIER,
    FiltreInconnu,
    construire_requete,
    filtres_disponibles,
)
from ._actes_schema import (
    ATTRIBUTS_CONNUS,
    ETAT_CONSTATEE,
    ETAT_PROJETEE,
    EXIGENCES_LIEN,
    FORCE_ABSENT,
    FORCE_AFFIRME,
    FORCE_PIECE,
    CONFIANCES,
    CONFIANCE_FAIBLE,
    CONFIANCE_FORTE,
    CONFIANCE_MOYENNE,
    KINDS,
    NATURES,
    ORIGINE_CORRIGE,
    ORIGINE_EXTRAIT,
    PORTEES,
    MAJORITE_NON_ENONCEE,
    PROVENANCES,
    RELATIONS,
    RESULTATS,
    RESULTATS_AUTORISANTS,
    TVA_REGIMES,
    SOURCES_AFFIRMATION,
    TABLE_ACTES,
    TABLE_ATTRIBUTS,
    TABLE_DOSSIERS,
    TABLE_LIENS,
    TABLE_TRACES,
    acte_id_decision_cs,
    acte_id_resolution,
    acte_id_urgence,
    diffusable,
    lien_id,
    montant_nombre,
    montant_texte,
    resultat_valide,
)
# Un appelant qui ecrit un montant lu sur un document doit pouvoir attraper le
# refus par son nom, sans connaitre le module prive qui le leve.
from ._montants import MontantIllisible, montant_decimal  # noqa: F401
from ._actes_store import (
    GouvernanceStoreIndisponible,
    NOMS_VUES,
    SchemaDeGouvernanceDivergent,
    connexion,
    ecrire,
    lire_table,
    lire_vue,
    preparer,
    store_path,
)

__all__ = [
    "ATTRIBUTS_CONNUS", "COUT_AGREGAT", "COUT_DIRECT", "COUT_JOINTURE",
    "CONFIANCES", "CONFIANCE_FAIBLE", "CONFIANCE_FORTE",
    "CONFIANCE_MOYENNE", "ETAT_CONSTATEE", "ETAT_PROJETEE", "EXIGENCES_LIEN", "FILTRES",
    "FORCE_ABSENT", "FORCE_AFFIRME", "FORCE_PIECE", "FiltreInconnu",
    "GouvernanceStoreIndisponible", "KINDS", "NATURES", "ORIGINE_CORRIGE",
    "MAJORITE_NON_ENONCEE", "ORIGINE_EXTRAIT", "PORTEES", "PROVENANCES",
    "RELATIONS", "RESULTATS", "RESULTATS_AUTORISANTS", "TVA_REGIMES",
    "SOURCES_AFFIRMATION", "SQL_ACTES_DU_DOSSIER",
    "TABLE_ACTES", "TABLE_ATTRIBUTS", "TABLE_DOSSIERS", "TABLE_LIENS",
    "TABLE_TRACES",
    "acte_id_decision_cs", "acte_id_resolution", "acte_id_urgence",
    "actes_du_dossier", "connexion", "construire_requete", "constats",
    "cumul_delegations", "diffusable", "ecrire", "filtres_disponibles",
    "jours_entre", "lien_id", "lire_table", "lire_vue", "matrice",
    "MontantIllisible", "montant_decimal", "montant_nombre", "montant_texte",
    "preparer", "resultat_valide",
    "store_path",
]


def jours_entre(depuis: str, jusqu_a: str) -> int | None:
    """Nombre de jours entre deux dates ISO, ou `None` si l'une manque.

    Le calcul est **ici et pas dans une vue**. Une vue qui appellerait
    `date('now')` rendrait des tests non reproductibles et, pire, un age qui
    change sans que rien n'ait change. La vue enonce un fait date; l'age est une
    lecture, et l'appelant choisit sa date de reference.
    """
    from datetime import date

    if not depuis or not jusqu_a:
        return None
    try:
        a = date.fromisoformat(depuis)
        b = date.fromisoformat(jusqu_a)
    except ValueError:
        return None
    return (b - a).days


def constats(
    instance: Any,
    criteres: Sequence[tuple[str, str, Any]] = (),
    *,
    aujourd_hui: str = "",
    limite: int | None = None,
) -> list[dict[str, Any]]:
    """La file de travail: les ruptures nommees, datees et chiffrees.

    Ordre par defaut: le montant en jeu decroissant, comme le blueprint le
    demande (`tries par montant en jeu`). Un constat sans montant - une piece
    manquante, un proces-verbal sans date - passe apres, pas avant: il coute
    moins cher a la copropriete qu'un euro non couvert.

    `anciennete_jours` est ajoute a la lecture quand une date de reference est
    donnee. C'est le `il y a 287 jours` de la carte de file.
    """
    lignes = lire_vue(
        instance, "v_constats", criteres,
        ordre="montant_en_jeu IS NULL, montant_en_jeu DESC, code, sujet_id",
        limite=limite,
    )
    if aujourd_hui:
        for ligne in lignes:
            ligne["anciennete_jours"] = jours_entre(
                str(ligne.get("date_fait") or ""), aujourd_hui
            )
    return lignes


def matrice(
    instance: Any,
    criteres: Sequence[tuple[str, str, Any]] = (),
    *,
    limite: int | None = None,
) -> list[dict[str, Any]]:
    """Une ligne par acte, six colonnes de force probatoire.

    Chaque cellule vaut `PIECE_PRODUITE`, `AFFIRME_SANS_PIECE` ou `ABSENT`, ce
    qui se projette sur les trois statuts publics deja livres. Filtrer une
    colonne, c'est une egalite sur une colonne - jamais une recherche de mots.
    """
    return lire_vue(
        instance, "v_matrice_gouvernance", criteres,
        ordre="date_effet DESC, CAST(numero AS INTEGER), CAST(sous_numero AS INTEGER)",
        limite=limite,
    )


def cumul_delegations(
    instance: Any, criteres: Sequence[tuple[str, str, Any]] = ()
) -> list[dict[str, Any]]:
    """Le cumul des depenses deleguees contre le plafond, **sur la periode**.

    Article 21-2, et c'est le seul controle qui ne se voit pas ligne a ligne:
    chaque depense peut etre reguliere et le cumul depasser quand meme. La
    periode est celle de la delegation, pas l'exercice comptable - une
    delegation votee en 2023 couvre une depense de 2024, et rien dans cette
    requete ne connait la notion d'exercice.
    """
    return lire_vue(
        instance, "v_cumul_delegation", criteres,
        ordre="cumul DESC, delegation_id",
    )


def actes_du_dossier(instance: Any, dossier_id: str) -> list[dict[str, Any]]:
    """`Cet euro, qui l'a autorise ?` - la charniere des deux ecrans.

    Rend **toutes** les assertions vivantes, ordonnees par autorite de la
    provenance: ce qu'un humain a confirme d'abord, ce que CoproScope a calcule
    ensuite, ce que le syndic affirme en dernier. Plusieurs reponses concurrentes
    sont un resultat normal, pas une anomalie a reduire: c'est exactement ce que
    l'ecran doit montrer quand le syndic et le calcul ne disent pas la meme
    chose.

    Une liste vide n'est pas `pas d'autorisation`: c'est `aucune autorisation
    identifiee`. La difference se dit dans l'ecran, et le constat
    `EURO_SANS_ACTE` la porte.

    **UN `except Exception` NU A ETE RETIRE ICI le 2026-09-10, constat `C085`
    de l'axe B.** Il rendait une liste vide **quelle que soit la cause**: table
    absente, base abimee, fichier verrouille, colonne disparue, erreur de
    disque. L'ecran affichait alors *aucune autorisation identifiee* - une
    phrase qui, elle, affirme quelque chose sur la copropriete - la ou la verite
    etait *la question n'a pas pu etre posee*.

    **L'axe.** Ce qui varie, c'est la raison pour laquelle la lecture echoue. Ce
    qui reste invariant, c'est que **repondre et ne pas pouvoir repondre ne sont
    pas le meme etat**, et qu'un seul des deux se resume par une liste vide.

    Le module voisin portait deja cette doctrine: `_actes_store.lire_vue`
    distingue depuis le 2026-09-04 la table absente - une instance ou rien n'a
    encore ete verse - de tout le reste, apres qu'une colonne manquante eut
    rendu zero constat au lieu de 818, en silence. Cette fonction-ci etait
    restee en arriere; elle applique desormais la meme regle.
    """
    with connexion(instance) as cx:
        try:
            curseur = cx.execute(SQL_ACTES_DU_DOSSIER, (dossier_id,))
        except sqlite3.OperationalError as exc:
            # Le SEUL cas ou une liste vide dit la verite: rien n'a encore ete
            # verse dans ce coffre, donc la TABLE n'existe pas.
            #
            # **Une VUE absente n'est pas ce cas, et SQLite ne les distingue
            # pas:** il dit `no such table: v_actes` pour une vue manquante
            # comme pour une table manquante. Un premier jet de ce correctif,
            # le 2026-09-10, s'arretait a `no such table` - il aurait donc rendu
            # une liste vide sur une base dont la vue a disparu, c'est-a-dire
            # reproduit a l'identique le defaut que `lire_vue` avait corrige le
            # 2026-09-04, ou rendre `[]` affichait `aucun acte n'est encore
            # verse` sur une base qui en portait 173. Le nom manquant est donc
            # confronte a `NOMS_VUES`.
            manquant = str(exc).split("no such table:")[-1].strip()
            if "no such table" in str(exc) and manquant not in NOMS_VUES:
                return []
            raise SchemaDeGouvernanceDivergent(
                f"dossier '{dossier_id}': la lecture des actes a echoue sur "
                f"\"{exc}\". Une liste vide ici s'afficherait comme "
                "\"aucune autorisation identifiee\", ce qui affirmerait "
                "quelque chose sur la copropriete au lieu de dire que la "
                "question n'a pas pu etre posee."
            ) from exc
        return [dict(row) for row in curseur]
