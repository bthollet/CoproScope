"""Ecriture et lecture du journal d'observation, sur la couche partagee.

**Ce module est un appelant, pas une copie.** Chemin, connexion, schema et
ecriture viennent de `vault.gouvernance_store`, exactement comme
`_actes_store` et `_convocation_store`. Le defaut de fermeture de connexion
SQLite constate le 2026-09-03 avait deja ete ecrit en deux exemplaires avant
d'etre mutualise: un troisieme serait une regression, pas une independance.

----------------------------------------------------------------------
Append-only, et comment on l'obtient sans nouvelle couche
----------------------------------------------------------------------

`gouvernance_store.remplacer_pour_documents` efface les lignes derivees des
documents cites avant de reecrire. Appele avec une liste de documents **vide**,
il n'efface rien - c'est le chemin que cette couche documente pour les lignes
qui ne derivent d'aucun document.

C'est exactement le besoin d'un journal: la ligne du 15 doit survivre a
l'ecriture du 22. Un journal qui se remplacerait lui-meme n'aurait aucune
valeur, puisque toute sa raison d'etre est la comparaison de deux dates.

La cle primaire porte `passage_id`: deux passages ne se marchent donc jamais
dessus, et reecrire le meme passage - reprise apres interruption - remplace ses
propres lignes sans toucher aux autres.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
from typing import Any, Iterator, Sequence

from ..vault import gouvernance_store
from ..vault.gouvernance_store import (  # noqa: F401 - re-export volontaire
    GouvernanceStoreIndisponible,
    store_path,
)
from ._extranet_schema import (
    CLOTURES,
    ETATS_RUBRIQUE,
    INDEX,
    ORIGINE_CORRIGE,
    TABLES,
)

TABLE_PASSAGES = "extranet_passages"
TABLE_RUBRIQUES = "extranet_rubriques"
TABLE_PIECES = "extranet_pieces"


@contextmanager
def connexion(instance: Any) -> Iterator[sqlite3.Connection]:
    """Connexion au coffre de gouvernance, fermee a coup sur."""
    chemin = gouvernance_store.store_path(instance)
    with closing(gouvernance_store._connect(chemin)) as cx:  # noqa: SLF001
        yield cx


def preparer(instance: Any) -> None:
    """Cree les trois tables et leurs index. Idempotent.

    Aucune vue: les constats du journal sont derives en Python par
    `_extranet_journal`, pas en SQL. Motif assume - la regle de retrait combine
    couverture, cloture et injectivite mesuree; l'ecrire en SQL la rendrait
    illisible pour qui doit la verifier, et c'est une regle qui doit pouvoir
    etre relue par un humain qui n'ecrit pas de SQL.
    """
    with connexion(instance) as cx, cx:
        for table, (colonnes, cles, _) in TABLES.items():
            gouvernance_store.ensure_schema(cx, colonnes, table=table, cles=cles)
        for table, nom, colonnes in INDEX:
            champs = ", ".join(f'"{c}"' for c in colonnes)
            cx.execute(f'CREATE INDEX IF NOT EXISTS {nom} ON "{table}" ({champs})')


def _ecrire(instance: Any, table: str, lignes: Sequence[dict[str, str]]) -> int:
    colonnes, cles, _ = TABLES[table]
    connues = set(colonnes)
    for ligne in lignes:
        inconnues = sorted(set(ligne) - connues)
        if inconnues:
            # La couche partagee ignore silencieusement une colonne non
            # declaree: la valeur serait ecrite nulle part et la perte ne se
            # verrait qu'a l'ecran, plus tard, sur un champ vide inexplicable.
            raise ValueError(
                f"table '{table}': colonnes inconnues {inconnues}. "
                "Un champ non declare serait perdu en silence."
            )
        # Meme raisonnement, applique aux VALEURS. Un etat hors enumeration ne
        # serait refuse par personne en aval: la comparaison le traiterait
        # comme *pas parcourue* - donc silencieusement plus prudente - ou, pire
        # selon l'ecriture, comme parcourue. Une enumeration declaree et non
        # gardee ne protege de rien.
        for champ, permis in (("etat", ETATS_RUBRIQUE), ("cloture", CLOTURES)):
            valeur = ligne.get(champ)
            if valeur is not None and valeur not in permis:
                raise ValueError(
                    f"table '{table}': valeur inconnue pour '{champ}': "
                    f"{valeur!r}. Valeurs declarees: {list(permis)}."
                )
    return gouvernance_store.remplacer_pour_documents(
        instance, colonnes, lignes, (), table=table, cles=cles
    )


def _existe(instance: Any, passage_id: str) -> bool:
    return any(
        p.get("passage_id") == passage_id for p in _lire(instance, TABLE_PASSAGES)
    )


def _effacer_passage(instance: Any, passage_id: str) -> None:
    """Retire les lignes machine d'un passage, en epargnant les corrections humaines.

    **L'axe de remplacement de la couche partagee est le document; le notre est
    le passage.** `remplacer_pour_documents` ne sait pas effacer par passage, et
    lui faire croire qu'un passage est un document serait un abus qui casserait
    a la premiere evolution. On ecrit donc la clause ici, avec exactement la
    meme protection: `origine <> CORRIGE_HUMAIN`.

    Sans cela, une reprise qui trouverait moins de pieces que la premiere
    laisserait les surnumeraires en base - des pieces fantomes qui
    deviendraient, au passage suivant, autant de faux retraits.
    """
    with connexion(instance) as cx, cx:
        for table in (TABLE_PIECES, TABLE_RUBRIQUES, TABLE_PASSAGES):
            try:
                cx.execute(
                    f'DELETE FROM "{table}" WHERE passage_id = ? AND origine <> ?',
                    (passage_id, ORIGINE_CORRIGE),
                )
            except sqlite3.OperationalError:
                # Table absente: instance neuve, rien a effacer.
                pass


def ecrire_passage(
    instance: Any,
    passage: dict[str, str],
    rubriques: Sequence[dict[str, str]],
    pieces: Sequence[dict[str, str]],
    *,
    remplacer: bool = False,
) -> dict[str, int]:
    """Enregistre un passage complet: son entete, sa couverture, ses pieces.

    Les trois ecritures vont ensemble et dans cet ordre. **La couverture n'est
    pas optionnelle**: un passage enregistre sans ses rubriques rendrait toute
    absence future inexploitable, puisque rien ne dirait ou l'on a regarde. Le
    refus est explicite plutot que differe a la lecture, ou il apparaitrait
    comme un `INDETERMINE` inexplicable des mois plus tard.
    """
    if not passage.get("passage_id"):
        raise ValueError("Un passage doit porter un `passage_id`.")
    if not passage.get("debut"):
        # Defaut trouve par le test de bout en bout, et garde comme regle: sans
        # horodatage, deux passages ne sont pas ordonnables, donc `les deux
        # plus recents` n'a pas de sens et la comparaison peut partir a
        # l'envers - en rendant un retrait pour un ajout. Un journal n'est rien
        # d'autre qu'un placement dans le temps: refuser ici, comme on refuse
        # un passage sans couverture.
        raise ValueError(
            "Un passage doit porter un `debut`. Sans horodatage, deux passages "
            "ne sont pas ordonnables et la comparaison peut s'inverser."
        )
    if not rubriques:
        raise ValueError(
            "Un passage sans couverture ne permet de conclure aucune absence. "
            "Declarer au moins une rubrique, meme NON_EXPLOREE."
        )
    preparer(instance)
    humaine = passage.get("origine") == ORIGINE_CORRIGE
    # Une correction humaine n'est pas une re-observation: elle annote un
    # passage existant et coexiste avec les lignes machine, `origine` faisant
    # partie de la cle primaire. Lui opposer la garde de reecriture rendrait
    # impossible le geste meme que le modele est fait pour accueillir.
    if _existe(instance, passage["passage_id"]) and not remplacer and not humaine:
        # Un journal ne s'ecrase pas par megarde. Le refus par defaut protege
        # l'historique; la reprise apres interruption reste possible, mais elle
        # doit etre demandee.
        raise ValueError(
            f"Le passage {passage['passage_id']!r} existe deja. "
            "Passer `remplacer=True` pour le reecrire - ses lignes machine "
            "seront remplacees, ses corrections humaines conservees."
        )
    if remplacer:
        _effacer_passage(instance, passage["passage_id"])
    return {
        "passages": _ecrire(instance, TABLE_PASSAGES, [passage]),
        "rubriques": _ecrire(instance, TABLE_RUBRIQUES, list(rubriques)),
        "pieces": _ecrire(instance, TABLE_PIECES, list(pieces)),
    }


def _lire(instance: Any, table: str) -> list[dict[str, str]]:
    _, _, ordre = TABLES[table]
    return gouvernance_store.lire(instance, table=table, ordre=ordre)


def lister_passages(instance: Any) -> list[dict[str, str]]:
    """Les passages enregistres, du plus recent au plus ancien."""
    return _lire(instance, TABLE_PASSAGES)


def lire_passage(instance: Any, passage_id: str) -> dict[str, Any]:
    """Un passage et tout ce qu'il porte, sous la forme attendue par `comparer`.

    Un passage inconnu rend une structure vide plutot qu'une erreur: sur une
    instance neuve, `aucun passage` est un etat normal du produit, pas une
    panne. L'appelant doit le dire a l'utilisateur au lieu d'afficher un ecran
    vide - c'est le defaut T10 du blueprint.
    """
    entetes = [p for p in _lire(instance, TABLE_PASSAGES) if p.get("passage_id") == passage_id]
    return {
        "passage": entetes[0] if entetes else {},
        "rubriques": [
            r for r in _lire(instance, TABLE_RUBRIQUES) if r.get("passage_id") == passage_id
        ],
        "pieces": [
            p for p in _lire(instance, TABLE_PIECES) if p.get("passage_id") == passage_id
        ],
    }


def deux_derniers(instance: Any) -> tuple[str, str]:
    """Les identifiants des deux passages les plus recents, ou des chaines vides.

    Rend `(avant, apres)`. Avec un seul passage enregistre, rend `("", id)`:
    **un premier passage ne produit aucun constat**, il constitue la reference.
    Le dire ici evite que l'ecran presente 115 pieces comme 115 ajouts.
    """
    passages = lister_passages(instance)
    if not passages:
        return "", ""
    if len(passages) == 1:
        return "", passages[0].get("passage_id", "")
    return passages[1].get("passage_id", ""), passages[0].get("passage_id", "")
