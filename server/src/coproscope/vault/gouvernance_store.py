"""Magasin SQLite des donnees de gouvernance.

Arbitrage Brice du 2026-09-03: les donnees de gouvernance vont en SQLite, pas
dans un nouveau registre CSV. Motif: la table de liens `object_links` vit deja
en SQLite dans le coffre, et trois conversations qui ecriraient chacune dans un
magasin different reproduiraient le defaut numero un du produit - quatre
comptages concurrents pour la meme notion.

**Pourquoi une base dediee et non la base de reconstruction.**
`_reset_schema` est appele a chaque reconstruction, complete ou incrementale,
mais c'est une **liste explicite de `DROP TABLE IF EXISTS`** et la base n'est
jamais supprimee. Correction mesuree le 2026-09-08: une table ajoutee a la base
de reconstruction sans passer par le journal d'evenements n'y est donc PAS
effacee - elle survit a tous les rebuilds, desynchronisee, sans que rien le
signale. La conclusion ne bouge pas et la raison change: ce fichier-ci n'est pas
reconstruit, il est ecrit et relu tel quel.

**Destination.** La convergence avec la base de reconstruction est souhaitable,
mais elle suppose que les resolutions deviennent des objets evenementiels, avec
leur recorder et leur projection. Tant que ce chemin n'existe pas, ecrire
directement dans la base reconstruite serait une perte de donnees differee.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

GOUVERNANCE_DB_FILE = "gouvernance.sqlite3"

ORIGINE_EXTRAIT = "EXTRAIT"
ORIGINE_CORRIGE = "CORRIGE_HUMAIN"

#: **Liste fermee, et c'est le magasin partage qui la ferme.** `origine` n'est
#: pas une colonne comme une autre: elle dit si une ligne vient de la machine ou
#: d'un humain, elle entre dans la cle primaire des cinq tables d'actes comme
#: dans `CLES_RESOLUTIONS`, et c'est elle que la clause `DELETE ... AND origine
#: <> 'CORRIGE_HUMAIN'` interroge pour epargner une correction humaine.
#:
#: Tant qu'elle restait du texte libre, une troisieme valeur - `EXTRAIT_V2`,
#: une faute de frappe, un nom de version - fabriquait un SECOND acte pour un
#: seul fait, sans rien lever. Mesure du 2026-09-05: le meme acte ecrit sous
#: `EXTRAIT` puis sous `EXTRAIT_V2` rend deux lignes dans `v_actes`, deux dans
#: la matrice de gouvernance, et `montant_paye = 4000.0` pour une facture
#: unique de 2000.00. C'est l'euro double des constats bloquants du modele,
#: par une autre porte.
#:
#: Une valeur nouvelle est donc un ARBITRAGE - que signifie-t-elle pour la
#: garde des corrections humaines - et se declare ici, jamais au point d'appel.
ORIGINES = (ORIGINE_EXTRAIT, ORIGINE_CORRIGE)

# Toute table de ce magasin porte ces deux colonnes: le remplacement par
# document et la protection des corrections humaines en dependent.
COLONNES_REQUISES = ("doc_id", "origine")


class GouvernanceStoreIndisponible(RuntimeError):
    """Le coffre local n'est pas configure pour cette instance."""


class SchemaDeGouvernanceDivergent(RuntimeError):
    """La base locale ne porte plus le schema que le code declare.

    Levee, jamais avalee. Le defaut que cette classe existe pour rendre audible
    a ete mesure le 2026-09-04: apres un simple renommage de colonne, l'ecran
    des resolutions passait de deux assemblees a `registre_vide` alors que
    `select count(*)` rendait toujours 173 lignes - et le message propose a
    l'utilisateur l'envoyait verifier la qualite d'extraction d'un document
    parfaitement lisible.
    """


def _vault_local_root(instance: Any) -> Path | None:
    """Racine locale du coffre, avec les alias employes dans les instances."""
    settings = instance.settings()
    vault = settings.get("vault") or settings.get("coffre") or {}
    if not isinstance(vault, dict):
        return None
    local = vault.get("local_root") or vault.get("local") or vault.get("cache_root")
    if not local:
        return None
    return instance.resolve_path(str(local))


def store_path(instance: Any) -> Path:
    """Chemin de la base de gouvernance, sous la racine locale du coffre."""
    racine = _vault_local_root(instance)
    if racine is None:
        raise GouvernanceStoreIndisponible(
            "Le coffre local n'est pas declare dans instance.yml (settings.vault.local_root)."
        )
    return Path(racine) / GOUVERNANCE_DB_FILE


def _connect(chemin: Path) -> sqlite3.Connection:
    """Connexion a la base, dossier cree au besoin.

    A ouvrir avec `closing(...)`: `with sqlite3.connect(...)` gere la
    transaction et NON la fermeture. Sous Windows le fichier reste alors
    verrouille, et l'erreur ne se voit pas la ou elle est causee - elle sort en
    `PermissionError [WinError 32]` au nettoyage d'un test suivant.
    """
    chemin.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(chemin))
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def connexion(instance: Any) -> Iterator[sqlite3.Connection]:
    """Connexion au coffre de gouvernance, fermee a coup sur.

    Point 1 du diff `gouvernance_store.PROPOSITION.patch`, applique le
    2026-09-04. Trois lots ont besoin d'une connexion au meme fichier, et
    `_connect` etait prive: sans point d'entree public, le quatrieme lot
    recopiait la fonction - et c'est exactement le defaut de fermeture non
    fermee qui a fait mutualiser cette couche le 2026-09-03.
    """
    with closing(_connect(store_path(instance))) as connection:
        yield connection


TABLE_RESOLUTIONS = "resolutions"
CLES_RESOLUTIONS = ("resolution_id", "etat", "origine")


def ensure_schema(
    connection: sqlite3.Connection,
    colonnes: Sequence[str],
    *,
    table: str = TABLE_RESOLUTIONS,
    cles: Sequence[str] = CLES_RESOLUTIONS,
) -> None:
    """Cree la table si elle manque, avec les colonnes et la cle fournies.

    Le schema suit la liste de champs du module appelant plutot que de la
    dupliquer: une colonne ajoutee au modele apparait ici sans edition, et
    l'ecart entre les deux ne peut pas s'installer.

    `table` et `cles` sont parametres pour que les autres objets de gouvernance
    - convocations, devis cites, declarations - partagent cette couche au lieu
    d'en recopier une. Le defaut de fermeture de connexion signale le
    2026-09-03 existait deja en deux exemplaires: c'est ce que la mutualisation
    evite.
    """
    champs = ", ".join(f'"{nom}" TEXT' for nom in colonnes)
    cle = ", ".join(f'"{nom}"' for nom in cles)
    index = ""
    for colonne in ("doc_id", "ag_id"):
        if colonne in colonnes:
            index += (
                f'CREATE INDEX IF NOT EXISTS idx_{table}_{colonne} '
                f'ON "{table}"("{colonne}");\n'
            )
    connection.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS "{table}" ({champs},
            PRIMARY KEY ({cle})
        );
        {index}
        """
    )
    _rattraper_colonnes(connection, colonnes, table=table)
    _verifier_cle(connection, cles, table=table)


def _rattraper_colonnes(
    connection: sqlite3.Connection, colonnes: Sequence[str], *, table: str
) -> None:
    """Ajoute a une table deja creee les colonnes que le modele a gagnees.

    Point 2 du diff `gouvernance_store.PROPOSITION.patch`, applique le
    2026-09-04 **avant** le point 3 parce que l'ordre importe: le point 3
    transforme un silence en exception, et sans ce rattrapage il leverait sur
    toute base creee avant l'ajout d'une colonne citee dans un `ordre` de
    lecture.

    `CREATE TABLE IF NOT EXISTS` ne rattrape rien: une colonne ajoutee au
    modele apres qu'une base locale a ete ecrite n'existait jamais dans cette
    base. Le piege est differe - invisible sur une base neuve, donc invisible
    en test, et visible seulement chez quelqu'un qui met a jour le logiciel.
    """
    existantes = {
        row["name"] for row in connection.execute(f'PRAGMA table_info("{table}")')
    }
    for nom in colonnes:
        if nom not in existantes:
            connection.execute(f'ALTER TABLE "{table}" ADD COLUMN "{nom}" TEXT')


def _verifier_cle(
    connection: sqlite3.Connection, cles: Sequence[str], *, table: str
) -> None:
    """Refuse de travailler sur une table dont la cle primaire n'est plus celle
    du code.

    Trou mesure le 2026-09-04 et non couvert par le diff propose: elargir la
    cle primaire dans le code est **silencieusement sans effet** sur une base
    deja creee, puisque `CREATE TABLE IF NOT EXISTS` ne recree rien. Mesure:
    base creee avec ('id','origine'), puis ecriture avec ('id','etat','origine')
    de deux lignes ne differant que par `etat` -> une seule ligne subsiste, la
    seconde a ecrase la premiere, la DDL est inchangee.

    C'est exactement le defaut que la cle elargie existe pour empecher - le
    proces-verbal ecrasant le projet de resolution de la convocation - et il
    reviendrait sans un mot sur les bases anterieures. Une base dont la cle a
    derive doit le dire, pas ecraser.
    """
    reelle = tuple(
        row["name"]
        for row in sorted(
            (r for r in connection.execute(f'PRAGMA table_info("{table}")') if r["pk"]),
            key=lambda r: r["pk"],
        )
    )
    if reelle and reelle != tuple(cles):
        raise SchemaDeGouvernanceDivergent(
            f"table '{table}': la base porte la cle primaire {reelle}, le code "
            f"declare {tuple(cles)}. `CREATE TABLE IF NOT EXISTS` ne recree pas "
            "une table existante: ecrire malgre l'ecart ferait ecraser en "
            "silence des lignes que la cle du code distingue. Reconstruire la "
            "table ou revenir a la cle de la base."
        )


def collisions_de_cle(
    lignes: Iterable[dict[str, str]],
    cles: Sequence[str] = CLES_RESOLUTIONS,
) -> dict[tuple[str, ...], int]:
    """Les cles primaires revendiquees par plus d'une ligne soumise.

    **Une collision de cle n'est pas une erreur de la base: c'est une perte de
    donnee silencieuse.** `INSERT OR REPLACE` garde la derniere ligne et jette
    les precedentes sans rien lever. Mesure du 2026-09-04 sur une assemblee de
    fevrier 2026: un document produit neuf resolutions dont deux portent le
    numero 3 - une ligne parasite decrivant un lot, et le vote sur le
    non-renouvellement du mandat du syndic. Les deux fabriquent la meme cle, le
    journal ecrivait `resolutions: 9`, et le coffre en contenait huit. Sur un
    second corpus, `11.1` a `11.8` non lus comme sous-numeros rendaient six fois
    le meme identifiant, donc un acte pour six resolutions.

    Cette fonction ne tranche pas laquelle survit - ce n'est pas son role. Elle
    NOMME la cle en collision, et laisse l'appelant choisir sa politique: le
    registre des resolutions la rapporte, `_actes_store.ecrire` la refuse. Une
    detection, deux politiques - jamais deux detections qui deriveraient l'une
    de l'autre.
    """
    vues: dict[tuple[str, ...], int] = {}
    for ligne in lignes:
        cle = tuple(str(ligne.get(nom, "") or "") for nom in cles)
        vues[cle] = vues.get(cle, 0) + 1
    return {cle: n for cle, n in vues.items() if n > 1}


def remplacer_pour_documents(
    instance: Any,
    colonnes: Sequence[str],
    lignes: Iterable[dict[str, str]],
    doc_ids: Sequence[str],
    *,
    table: str = TABLE_RESOLUTIONS,
    cles: Sequence[str] = CLES_RESOLUTIONS,
) -> int:
    """Remplace les lignes derivees des documents cites, et rend leur nombre.

    **Le nombre rendu est celui qui a ete STOCKE, jamais celui qui a ete
    soumis.** L'appelant qui veut savoir CE qui a disparu appelle
    `collisions_de_cle` sur les memes lignes: le compte dit combien, elle dit
    lesquelles.

    Une re-extraction remplace ce qu'elle a produit et **rien d'autre**: les
    lignes d'origine `CORRIGE_HUMAIN` sont laissees intactes. C'est la decision
    back numero 2 de la strategie du lot, appliquee ici plutot que promise.

    **Prerequis**: la table appelante doit porter `doc_id` et `origine`. Le
    premier dit de quel document la ligne est derivee, le second si elle vient
    de la machine ou d'un humain - et sans lui, le remplacement effacerait les
    corrections humaines qu'il est justement charge d'epargner.

    Signale par la conversation convocations le 2026-09-03: sans cette
    verification, l'appelant recevait un `OperationalError: no such column`
    depuis les entrailles de SQLite, sans rapport lisible avec la cause.

    **Rend le nombre de lignes REELLEMENT stockees, pas le nombre soumis.**
    Corrige le 2026-09-04. `INSERT OR REPLACE` ecrase silencieusement deux
    lignes de meme cle, et rendre `len(lignes)` faisait rapporter au journal
    de traitement un nombre que le coffre ne portait pas. Cas mesure sur une
    assemblee reelle: neuf resolutions construites, dont deux portant le meme
    numero, huit lignes en base, et le journal ecrivant `resolutions: 9`. La
    ligne perdue etait l'un des deux votes en collision.
    """
    manquantes = [nom for nom in COLONNES_REQUISES if nom not in colonnes]
    if manquantes:
        raise ValueError(
            f"table '{table}': colonnes requises absentes {manquantes}. "
            "`doc_id` identifie le document d'origine, `origine` protege les "
            "lignes CORRIGE_HUMAIN du remplacement."
        )
    chemin = store_path(instance)
    lignes = list(lignes)
    with closing(_connect(chemin)) as connection, connection:
        ensure_schema(connection, colonnes, table=table, cles=cles)
        if doc_ids:
            marques = ",".join("?" for _ in doc_ids)
            connection.execute(
                f'DELETE FROM "{table}" WHERE doc_id IN ({marques}) AND origine <> ?',
                (*doc_ids, ORIGINE_CORRIGE),
            )
        if lignes:
            champs = ",".join(f'"{nom}"' for nom in colonnes)
            valeurs = ",".join("?" for _ in colonnes)
            connection.executemany(
                f'INSERT OR REPLACE INTO "{table}" ({champs}) VALUES ({valeurs})',
                [tuple(ligne.get(nom, "") for nom in colonnes) for ligne in lignes],
            )
    return len(lignes) - sum(n - 1 for n in collisions_de_cle(lignes, cles).values())


def lire(
    instance: Any,
    *,
    table: str = TABLE_RESOLUTIONS,
    ordre: str = "ag_id DESC, CAST(position AS INTEGER)",
) -> list[dict[str, str]]:
    """Toutes les resolutions, ou liste vide si la base n'existe pas encore.

    Une base absente n'est pas une erreur: c'est une instance ou aucun
    proces-verbal n'a encore ete lu. L'appelant doit le dire a l'utilisateur au
    lieu d'afficher un ecran vide.

    **Une table absente rend `[]`. Tout le reste leve.** Point 3 du diff
    propose, applique le 2026-09-04 apres le point 2 qui le rendait sur.
    Auparavant, `except sqlite3.OperationalError: return []` sans distinction
    du message confondait trois situations dans une seule valeur: rien n'a
    encore ete lu, la colonne du tri n'existe plus, la colonne demandee a ete
    renommee. Preuve de bout en bout mesuree sur une copie de la base reelle:
    apres un simple renommage de la colonne du tri par defaut, l'ecran passait
    de deux assemblees a `registre_vide` alors que `select count(*)` rendait
    toujours 173 lignes - et le message affiche envoyait l'utilisateur
    verifier la qualite d'extraction d'un document parfaitement lisible.

    Le module voisin `_actes_store.lire_vue` avait deja corrige exactement ce
    motif pour lui-meme; la couche partagee, que quatre appelants traversent,
    ne l'avait pas.
    """
    try:
        chemin = store_path(instance)
    except GouvernanceStoreIndisponible:
        return []
    if not chemin.exists():
        return []
    with closing(_connect(chemin)) as connection:
        try:
            curseur = connection.execute(f'SELECT * FROM "{table}" ORDER BY {ordre}')
        except sqlite3.OperationalError as exc:
            if "no such table" in str(exc):
                return []
            raise SchemaDeGouvernanceDivergent(
                f"table '{table}': la lecture a echoue sur \"{exc}\" alors que "
                f"la table existe. Tri demande: {ordre!r}. Une liste vide ici "
                "serait indiscernable d'un registre vide, et l'ecran "
                "accuserait la source au lieu du schema."
            ) from exc
        return [{cle: (row[cle] or "") for cle in row.keys()} for row in curseur]
