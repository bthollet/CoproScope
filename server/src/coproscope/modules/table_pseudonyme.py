"""La table pseudonymisee des documents: ce que l'IA lit, et rien d'autre.

**La commande.** Arbitrage de Brice du 2026-09-08, `RM-2026-0126`, verbatim au
depot dans `docs/arbitrage_brice_0126_verbatim_2026-09-08.md`:

    « on peut prevoir que le nom de fichier soit completement non-explicite, en
    correspondant [...] a un identifiant de base [...] et que, du coup, les
    champs qui ont ete trouves lors du typage, le type, le nom de fournisseur,
    les montants, etc., eh bien, tout ce qui est identifiant est remplace par
    le pseudonyme. »

**La contradiction que cette table resout.** Deux exigences justes se
contredisaient. `test_parcours_depot_retrouver` exige qu'un deposant retrouve sa
piece; le lot de biffage exige qu'un nom de fichier - ecrit par un tiers, donc
susceptible de porter un patronyme - ne traverse aucune page servie. Supprimer
l'un ou l'autre etait interdit.

Elles ne se contredisent que si `retrouver` veut dire `afficher le nom`. La
table les separe: le nom depose reste lisible **cote serveur** pour la
recherche, et ce qui SORT est l'identifiant plus des champs derives ou aliases.

**HYPOTHESE MONOUTILISATEUR, et elle est nommee parce qu'elle est fausse
demain.** CoproScope tourne aujourd'hui pour une seule personne sur son poste.
Trois simplifications en decoulent, et chacune tombe des qu'il y a deux
utilisateurs:

1. le deposant est l'utilisateur local: il n'y a personne d'autre a distinguer,
   donc `depose_par_utilisateur` porte une constante et non une identite gerie;
2. `l'accuse de depot montre le nom au deposant seul` se ramene a `pendant la
   redirection qui suit le depot`, parce que le seul lecteur possible est celui
   qui vient de deposer;
3. aucun controle de droits n'est ecrit: il n'y a qu'un college de lecture.

Ce qui casse au deuxieme utilisateur est decrit dans
`docs/cdc_pseudonymisation_multiutilisateur_2026-09-08.md`. Ce module ne
pretend pas le couvrir.

**Ou vit cette table, et le piege evite.** Magasin `gouvernance_store`, base
`gouvernance.sqlite3` sous `settings.vault.local_root`. Doctrine du 2026-09-03:
pas de nouveau registre CSV. Et surtout **pas** la base de reconstruction.

**Le motif exact, mesure le 2026-09-08 et non recopie.** Les consignes disent
qu'une table ajoutee a la base de reconstruction est effacee au rebuild suivant.
La mesure dit autre chose: `_reset_schema` est une LISTE EXPLICITE de
`DROP TABLE IF EXISTS`, et une table etrangere y survit - verifie sur deux
rebuilds consecutifs. Le danger reel n'est donc pas l'effacement, il est pire:
la table est OUBLIEE. Tout le reste de la base se refait depuis les evenements
pendant qu'elle garde ses lignes d'avant, ce qui donne une desynchronisation
muette au lieu d'une perte visible - et une disparition franche le jour ou
quelqu'un ajoute son nom a la liste de DROP.

Cette liste de DROP est d'ailleurs elle-meme une enumeration de modalites,
exactement le defaut que `RM-2026-0127` corrige ailleurs.

Rien de tout cela n'est suppose: `test_table_pseudonyme.py` reconstruit deux
fois et recompte.

**L'invariant de la table, et il est verifiable.** Aucune valeur de cette table
n'est du texte ecrit par un tiers. Chaque valeur est soit derivee par
CoproScope - un identifiant, un type d'un vocabulaire ferme, une date
normalisee - soit un alias produit par le sel d'instance. Le test l'asserte sur
TOUTES les colonnes, pas sur une liste: une colonne ajoutee demain qui porterait
du texte brut fait echouer la garde au lieu de fuir en silence.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from ..core.libelle_public import libelle_public_document
from ..vault import gouvernance_store
from .biffageops import load_corpus_salt, value_alias


TABLE = "documents_pseudonymes"

#: `origine` entre dans la cle: une ligne derivee par la machine et une ligne
#: corrigee par un humain decrivent le meme document sans s'ecraser. C'est la
#: regle du magasin partage, pas une invention locale.
CLES: tuple[str, ...] = ("doc_id", "origine")

COLONNES: tuple[str, ...] = (
    "doc_id",
    "origine",
    "type_document",
    "date_presumee",
    "libelle_public",
    "nom_depose_pseudo",
    "fournisseur_pseudo",
    "depose_par_pseudo",
    "depose_par_utilisateur",
    "depose_le",
)

#: **Hypothese monoutilisateur, rendue visible plutot que codee en dur partout.**
#: Brice, 2026-09-08: « c'est important de tracer quand meme qui a depose, donc
#: soit par son pseudo, soit par son nom d'utilisateur, son identifiant
#: d'utilisateur, je ne sais pas, peut-etre les deux ». On garde les DEUX
#: colonnes des maintenant - `depose_par_pseudo` et `depose_par_utilisateur` -
#: parce qu'ajouter une colonne a une table deja ecrite est le piege que
#: `_rattraper_colonnes` a du corriger le 2026-09-04.
UTILISATEUR_LOCAL = "local"


def pseudonymiser_valeur(sel: bytes, categorie: str, valeur: str) -> str:
    """Un alias stable pour une valeur identifiante, ou vide si la valeur l'est.

    On reutilise `value_alias` du corpus caviarde au lieu d'en deriver un
    second: deux mecanismes de pseudonymisation dans le meme produit
    reproduiraient le defaut numero un constate le 2026-09-02 - plusieurs
    comptages concurrents pour la meme notion - applique aux identites.
    """

    texte = (valeur or "").strip()
    if not texte:
        return ""
    return value_alias(sel, categorie, texte)


def ligne_pour_document(
    sel: bytes,
    row: dict[str, str],
    *,
    depose_le: str = "",
    depose_par: str = UTILISATEUR_LOCAL,
    origine: str = gouvernance_store.ORIGINE_EXTRAIT,
) -> dict[str, str]:
    """La ligne pseudonymisee d'un document du registre.

    **Le nom depose entre entier, jamais analyse.** On ne cherche pas un
    patronyme dedans: `libelle_public.py` a deja etabli que c'est mal pose -
    rien dans la forme d'un mot ne dit qu'il designe quelqu'un, et coder les
    formes vues chez un cabinet casse au suivant. Un nom de fichier est du
    texte de tiers dans son ensemble, donc il est aliase dans son ensemble.

    Consequence assumee: deux pieces nommees differemment par le meme syndic
    pour la meme personne recoivent deux alias distincts. Relier ces mentions
    est le travail de l'annuaire, decrit dans
    `docs/cdc_anonymisation_et_annuaire_2026-09-07.md`, pas celui de ce module.
    """

    doc_id = (row.get("doc_id") or "").strip()
    return {
        "doc_id": doc_id,
        "origine": origine,
        "type_document": (row.get("document_type") or "").strip(),
        "date_presumee": (row.get("suspected_date") or "").strip(),
        "libelle_public": libelle_public_document(row),
        "nom_depose_pseudo": pseudonymiser_valeur(
            sel, "NOMFICHIER", row.get("file_name") or ""
        ),
        "fournisseur_pseudo": pseudonymiser_valeur(
            sel, "FOURNISSEUR", row.get("emitter") or ""
        ),
        "depose_par_pseudo": pseudonymiser_valeur(sel, "DEPOSANT", depose_par),
        "depose_par_utilisateur": depose_par,
        "depose_le": (depose_le or row.get("first_seen") or "").strip(),
    }


def enregistrer(
    instance: Any,
    lignes: Iterable[dict[str, str]],
    doc_ids: Sequence[str],
) -> int:
    """Ecrit les lignes pseudonymisees et rend le nombre REELLEMENT stocke.

    Le remplacement epargne les lignes `CORRIGE_HUMAIN`: une re-extraction
    remplace ce qu'elle a produit et rien d'autre.
    """

    return gouvernance_store.remplacer_pour_documents(
        instance,
        COLONNES,
        list(lignes),
        list(doc_ids),
        table=TABLE,
        cles=CLES,
    )


def lire(instance: Any) -> list[dict[str, str]]:
    """La table telle que l'IA doit la lire. Base absente: liste vide."""

    return gouvernance_store.lire(instance, table=TABLE, ordre="doc_id")
