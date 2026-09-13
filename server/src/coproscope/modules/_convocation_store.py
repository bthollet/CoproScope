"""Tables SQLite du lot convocations, dans le coffre de gouvernance.

Arbitrage Brice du 2026-09-03, inscrit dans `CLAUDE.md`: les donnees de
gouvernance vont en SQLite, jamais dans un nouveau registre CSV. Les trois
tables du lot vivent donc dans le MEME fichier que les resolutions -
`gouvernance.sqlite3` sous `settings.vault.local_root` - plutot que dans un
magasin concurrent.

**Ce module est un appelant, pas une copie.** Le chemin, la connexion, le schema
et le remplacement viennent de `vault.gouvernance_store`, qui appartient a la
conversation resolutions. La raison est un defaut vecu: `with sqlite3.connect()`
gere la transaction et non la fermeture, et cette erreur avait ete ecrite des
deux cotes. Un defaut de couche basse ne doit pas vivre en deux exemplaires.

Ce qui reste ici est ce qui nous est propre: le nom des tables, leur cle, et
l'ordre de lecture attendu.

    convocations     une ligne par convocation lue, avec ses comptages
    devis_cites      une ligne par devis nomme par un projet de resolution
    declarations_ag  ce que la convocation declare d'une AUTRE assemblee
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from ..vault import gouvernance_store
from ..vault.gouvernance_store import (  # noqa: F401 - re-export volontaire
    GouvernanceStoreIndisponible,
    store_path,
)

# Cle primaire et ordre de lecture de chaque table. `origine` entre dans la cle
# partout: une correction humaine doit pouvoir coexister avec la lecture machine
# du meme objet, comme un projet coexiste avec son constat cote resolutions.
TABLES: dict[str, tuple[tuple[str, ...], str]] = {
    "convocations": (
        ("convocation_id", "origine"),
        "ag_date DESC, convocation_id",
    ),
    "devis_cites": (
        ("devis_cite_id", "origine"),
        "convocation_id, CAST(numero AS INTEGER), CAST(sous_numero AS INTEGER)",
    ),
    "declarations_ag": (
        ("declaration_id", "origine"),
        "convocation_id, declaration_id",
    ),
}


def _verifier(table: str) -> tuple[tuple[str, ...], str]:
    if table not in TABLES:
        raise ValueError(f"Table inconnue pour le lot convocations: {table}")
    return TABLES[table]


def lire(instance: Any, table: str) -> list[dict[str, str]]:
    """Le contenu d'une table, ou liste vide si la base n'existe pas encore.

    Une base absente n'est pas une erreur: c'est une instance ou aucune
    convocation n'a encore ete lue. L'appelant doit le dire a l'utilisateur au
    lieu d'afficher un ecran vide sans raison.
    """
    _, ordre = _verifier(table)
    return gouvernance_store.lire(instance, table=table, ordre=ordre)


def remplacer_pour_documents(
    instance: Any,
    table: str,
    colonnes: Sequence[str],
    lignes: Iterable[dict[str, str]],
    doc_ids: Sequence[str],
) -> int:
    """Remplace les lignes derivees des documents cites, et rend leur nombre.

    La garde qui protege les corrections humaines est dans la couche partagee,
    donc dans la clause `DELETE` elle-meme: les lignes d'origine
    `CORRIGE_HUMAIN` survivent a une re-extraction sans que l'appelant ait a y
    penser. C'est la decision back numero 2 de la strategie, rendue structurelle
    plutot que promise.
    """
    cles, _ = _verifier(table)
    return gouvernance_store.remplacer_pour_documents(
        instance, colonnes, lignes, doc_ids, table=table, cles=cles
    )
