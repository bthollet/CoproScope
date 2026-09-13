from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from ..vault import gouvernance_store
from ..vault.gouvernance_store import (  # noqa: F401 - re-export volontaire
    ORIGINE_CORRIGE,
    ORIGINE_EXTRAIT,
    ORIGINES,
    GouvernanceStoreIndisponible,
    store_path,
)
from ._personnes_schema import (
    CANDIDAT_ETATS,
    DROITS,
    MASQUAGES,
    NATURES,
    RELATIONS_PERSONNES,
    SOURCES_ENTITE,
    TABLE_CANDIDATS,
    TABLE_LIENS_PERSONNES,
    TABLE_LOTS,
    TABLE_PERSONNES,
    TABLE_RATTACHEMENTS,
    TABLES,
)


"""Ecriture et lecture de la base des personnes, des lots et des rattachements.

Ce module ne decide rien: il garde. Les listes fermees du schema y sont
verifiees AVANT ecriture, parce qu'une valeur hors liste ne leve nulle part
ailleurs et fabrique un second objet pour un seul fait - c'est l'incident de
l'euro double, par une autre porte.
"""


#: Les colonnes dont la valeur appartient a une liste fermee, par table.
_LISTES_FERMEES: dict[str, dict[str, tuple[str, ...]]] = {
    TABLE_PERSONNES: {"nature": NATURES, "masquage": MASQUAGES, "source": SOURCES_ENTITE},
    TABLE_RATTACHEMENTS: {"droit": DROITS, "source": SOURCES_ENTITE},
    TABLE_LIENS_PERSONNES: {"relation": RELATIONS_PERSONNES},
    TABLE_CANDIDATS: {"etat": CANDIDAT_ETATS},
}


class ValeurHorsListe(ValueError):
    """Une colonne fermee a recu une valeur qui n'est pas declaree au schema."""


def _verifier_table(table: str) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    if table not in TABLES:
        raise KeyError(
            f"table inconnue du schema des personnes: {table!r}. "
            f"Tables declarees: {', '.join(sorted(TABLES))}."
        )
    return TABLES[table]


def _verifier_valeurs(table: str, lignes: list[dict[str, str]]) -> None:
    fermees = _LISTES_FERMEES.get(table, {})
    if not fermees:
        return
    for ligne in lignes:
        for colonne, autorisees in fermees.items():
            valeur = (ligne.get(colonne) or "").strip()
            if not valeur:
                continue
            if valeur not in autorisees:
                raise ValeurHorsListe(
                    f"{table}.{colonne} = {valeur!r} n'est pas une valeur declaree. "
                    f"Valeurs possibles: {', '.join(autorisees)}. "
                    "Une valeur nouvelle se declare au schema, jamais au point "
                    "d'appel: sans quoi elle fabrique un second objet pour un "
                    "seul fait, sans rien lever."
                )


def _verifier_origine(lignes: list[dict[str, str]]) -> None:
    for ligne in lignes:
        origine = (ligne.get("origine") or "").strip()
        if origine and origine not in ORIGINES:
            raise ValeurHorsListe(
                f"origine = {origine!r} inconnue. Valeurs possibles: {', '.join(ORIGINES)}. "
                "C'est cette colonne qui epargne les corrections humaines lors "
                "d'une re-extraction."
            )


def lire(instance: Any, table: str) -> list[dict[str, str]]:
    """Le contenu d'une table, ou liste vide si la base n'existe pas encore.

    Une base absente n'est pas une erreur: c'est une instance ou aucune liste
    nominative n'a encore ete lue. L'appelant doit le DIRE a l'utilisateur -
    un annuaire vide qui ne se voit pas est le defaut mesure le 2026-09-07.
    """

    _, _, ordre = _verifier_table(table)
    return gouvernance_store.lire(instance, table=table, ordre=ordre)


def remplacer_pour_documents(
    instance: Any,
    table: str,
    lignes: Iterable[dict[str, str]],
    doc_ids: Sequence[str],
    colonnes: Sequence[str] | None = None,
) -> int:
    """Remplace les lignes derivees des documents cites, et rend leur nombre.

    La garde qui protege les corrections humaines vit dans la couche partagee,
    dans la clause `DELETE ... AND origine <> 'CORRIGE_HUMAIN'`: une reponse
    donnee par un humain survit a toute re-extraction sans que l'appelant ait a
    y penser.
    """

    champs, cles, _ = _verifier_table(table)
    lignes = list(lignes)
    _verifier_valeurs(table, lignes)
    _verifier_origine(lignes)
    return gouvernance_store.remplacer_pour_documents(
        instance, colonnes or champs, lignes, doc_ids, table=table, cles=cles
    )


def personnes(instance: Any) -> list[dict[str, str]]:
    return lire(instance, TABLE_PERSONNES)


def lots(instance: Any) -> list[dict[str, str]]:
    return lire(instance, TABLE_LOTS)


def rattachements(instance: Any) -> list[dict[str, str]]:
    return lire(instance, TABLE_RATTACHEMENTS)


def candidats(instance: Any) -> list[dict[str, str]]:
    return lire(instance, TABLE_CANDIDATS)


def liens_personnes(instance: Any) -> list[dict[str, str]]:
    return lire(instance, TABLE_LIENS_PERSONNES)


def detenteurs_du_lot(instance: Any, lot_id: str, a_la_date: str = "") -> list[dict[str, str]]:
    """Qui detenait ce lot, et a quel titre, a la date demandee.

    **La date est le tout.** Le fichier des coproprietaires n'est jamais aligne
    sur l'etat de la copropriete a la date de l'assemblee traitee: un PV de 2019
    nomme le proprietaire de 2019. Sans date, on rend l'etat le plus recent
    connu, et l'appelant doit savoir que c'est ce qu'il obtient.

    Plusieurs detenteurs pour un meme lot est NORMAL, pas une anomalie: une
    indivision en compte plusieurs, un demembrement en compte deux. L'appelant
    ne doit jamais en choisir un seul de sa propre initiative.
    """

    retenus = [row for row in rattachements(instance) if row.get("lot_id") == lot_id]
    if a_la_date:
        retenus = [row for row in retenus if (row.get("date_piece") or "") <= a_la_date]
    if not retenus:
        return []
    plus_recente = max((row.get("date_piece") or "") for row in retenus)
    return [row for row in retenus if (row.get("date_piece") or "") == plus_recente]


def total_tantiemes(instance: Any, cle_repartition: str = "generale") -> int | None:
    """Le total des voix du syndicat sur une cle, ou None s'il est inconnu.

    **`None` n'est pas zero, et la distinction porte tout le sens.** Sans ce
    total, l'article 25 n'est pas calculable: le module de decompte rend
    `ASSIETTE_INDETERMINEE` plutot qu'un pourcentage faux. Rendre zero
    fabriquerait une division par zero ou, pire, un pourcentage inverse.
    """

    valeurs = [
        row.get("tantiemes", "")
        for row in lots(instance)
        if row.get("cle_repartition") == cle_repartition
    ]
    entiers = []
    for valeur in valeurs:
        texte = str(valeur or "").strip().replace(" ", "").replace(" ", "")
        if not texte.isdigit():
            continue
        entiers.append(int(texte))
    return sum(entiers) if entiers else None
