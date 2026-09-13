"""Ecriture et lecture des tables d'actes, sur la couche partagee du coffre.

**Ce module est un appelant, pas une copie.** Le chemin, la connexion, le schema
et le remplacement viennent de `vault.gouvernance_store`, exactement comme
`_convocation_store`. Le motif est celui deja vecu le 2026-09-03: `with
sqlite3.connect()` gere la transaction et non la fermeture, et ce defaut avait
ete ecrit en deux exemplaires avant d'etre mutualise. Un troisieme exemplaire
serait une regression, pas une independance.

Ce qui reste ici est ce qui nous est propre: les vues, les index, la date de
lecture, et le fait qu'un constat se lit sans jamais s'ecrire.

**Migration.** Rien ne touche `resolutions`, `convocations`, `devis_cites` ni
`declarations_ag`. Les cinq tables de ce lot sont nouvelles, dans le meme
fichier, et `CREATE TABLE IF NOT EXISTS` les rend idempotentes. Une base
existante s'ouvre, gagne les tables vides et les vues, et rend exactement ce
qu'elle rendait avant.
"""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing, contextmanager
from typing import Any, Iterator, Sequence

from ..vault import gouvernance_store
from ..vault.gouvernance_store import (  # noqa: F401 - re-export volontaire
    GouvernanceStoreIndisponible,
    SchemaDeGouvernanceDivergent,
    store_path,
)
from . import _actes_requetes as requetes
from . import _actes_vocabulaire as vocabulaire
from ._actes_schema import (
    COLONNES_DATE,
    DateNonOrdonnable,
    INDEX,
    TABLE_ACTES,
    TABLE_DOSSIERS,
    TABLE_LIENS,
    TABLES,
    date_iso,
    montant_texte,
)
from ._montants import MontantIllisible, taux_normalise
from ._actes_vues import NOMS_VUES, VUES


@contextmanager
def connexion(instance: Any) -> Iterator[sqlite3.Connection]:
    """Connexion au coffre de gouvernance, fermee a coup sur.

    `gouvernance_store._connect` est prive; le diff propose au coordinateur
    l'expose sous le nom `connexion`. En attendant l'arbitrage, on emprunte la
    fonction plutot que d'en recopier une deuxieme - c'est precisement le defaut
    de fermeture non ferme qui a fait mutualiser cette couche.
    """
    chemin = gouvernance_store.store_path(instance)
    with closing(gouvernance_store._connect(chemin)) as cx:  # noqa: SLF001
        yield cx


def preparer(instance: Any) -> None:
    """Cree les tables, les index et les vues. Idempotent.

    Les vues sont **supprimees puis recreees** a chaque appel. Une vue porte du
    droit - l'echeance de l'article 21-5, le plafond de l'article 21-2 - et une
    base ouverte par une version plus recente du logiciel ne doit pas continuer
    a repondre avec la regle de la version precedente. Les tables, elles, ne
    sont jamais recreees: elles portent de la donnee.
    """
    with connexion(instance) as cx, cx:
        for table, (colonnes, cles, _) in TABLES.items():
            gouvernance_store.ensure_schema(cx, colonnes, table=table, cles=cles)
        for table, nom, colonnes in INDEX:
            champs = ", ".join(f'"{c}"' for c in colonnes)
            cx.execute(
                f'CREATE INDEX IF NOT EXISTS {nom} ON "{table}" ({champs})'
            )
        _recreer_vues(cx)


def _recreer_vues(cx: sqlite3.Connection) -> None:
    """Supprime puis recree les onze vues, dans une connexion deja ouverte."""
    for nom in NOMS_VUES:
        cx.execute(f"DROP VIEW IF EXISTS {nom}")
    for sql in VUES:
        cx.executescript(sql)


_ESPACES = re.compile(r"\s+")
#: `CREATE VIEW IF NOT EXISTS v_actes AS` d'un cote, `CREATE VIEW v_actes AS`
#: de l'autre: SQLite retire la clause `IF NOT EXISTS` avant de ranger le texte
#: dans `sqlite_master`. Les onze vues du module la portent.
_CREATION_DE_VUE = re.compile(
    r"^CREATE\s+VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?", re.IGNORECASE
)


def _forme_comparable(sql: str) -> str:
    """La definition d'une vue, reduite a ce qui la distingue d'une autre.

    **La clause `IF NOT EXISTS` est neutralisee avant comparaison, et c'est
    tout l'interet de la fonction.** Sans cette neutralisation, le texte du
    code et le texte range par SQLite different sur les onze vues, toujours:
    `vues_perimees` rendait donc `11 sur 11` sur une base fraichement preparee,
    et le realignement de `lire_vue` devenait une reconstruction
    inconditionnelle - mesure du 2026-09-05: 273 ms par appel a la matrice,
    `attempt to write a readonly database` sur une base en lecture seule, et
    `database is locked` derriere un verrou concurrent, sur deux chemins qui
    lisaient tres bien auparavant.

    Le mecanisme ne discriminait alors jamais rien: il rendait la bonne reponse
    pour la mauvaise raison - `on reconstruit toujours` est accidentellement
    correct sur une vue perimee. Le cas negatif - une base saine ne porte
    aucune vue perimee - est desormais tenu par un test.
    """
    aplati = _ESPACES.sub(" ", sql.strip().rstrip(";")).strip()
    return _CREATION_DE_VUE.sub("CREATE VIEW ", aplati, count=1)


def vues_perimees(cx: sqlite3.Connection) -> list[str]:
    """Les vues que la base porte differemment de ce que ce code declare.

    Une vue absente compte comme perimee: dans les deux cas la base repond
    avec une regle de droit qui n'est pas celle du logiciel qui l'interroge.

    **Pourquoi comparer et non se fier a l'exception.** Une vue absente leve
    `no such table` et tombait jusqu'ici dans le meme repli que l'absence de
    donnee - mesure le 2026-09-04: sur une base portant 173 actes, un
    `DROP VIEW v_matrice_gouvernance` faisait rendre zero ligne a la matrice et
    afficher a l'ecran `Aucun acte n'est encore verse dans le modele`, sans une
    exception. Mais le cas dangereux ne leve rien du tout: une vue restee dans
    la definition d'une version anterieure repond, et repond faux - meme base,
    157 points a instruire ramenes a 48, diagnostic toujours `pret`. Aucune
    exception ne peut l'attraper. Seule la comparaison du texte le voit.

    SQLite conserve le `CREATE VIEW` tel qu'il a ete soumis dans
    `sqlite_master.sql`: la comparaison porte sur ce texte, aux espaces pres.
    """
    attendues = {
        nom: _forme_comparable(sql) for nom, sql in zip(NOMS_VUES, VUES, strict=True)
    }
    presentes = {
        row["name"]: _forme_comparable(row["sql"] or "")
        for row in cx.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'view'"
        )
    }
    return [nom for nom, sql in attendues.items() if presentes.get(nom) != sql]


def rafraichir_vues(instance: Any) -> list[str]:
    """Realigne les vues de la base sur celles du code. Rend celles qui l'ont ete.

    C'est la reponse au second defaut mesure le 2026-09-04: `preparer()`
    n'etait appelee que depuis `ecrire()`, et comme rien n'ecrivait encore, la
    promesse de sa docstring - `une base ouverte par une version plus recente
    doit voir les vues de cette version` - n'avait aucun chemin d'execution.

    Seules les vues sont touchees. Les tables ne sont pas creees ici: une
    lecture ne doit pas faire passer une instance de `aucun proces-verbal
    depose` a `le modele n'a jamais ete alimente`.

    **Rien n'est ecrit quand rien n'a derive.** La transaction en ecriture
    n'est ouverte qu'apres avoir constate une divergence: c'est ce qui rend
    `lire_vue` a nouveau lisible sur une base en lecture seule ou tenue par un
    verrou concurrent. Le cas ordinaire - la base est a jour - ne touche pas
    au fichier.
    """
    with connexion(instance) as cx:
        perimees = vues_perimees(cx)
        if not perimees:
            return []
        with cx:
            _recreer_vues(cx)
    return perimees


#: Les colonnes dont la valeur porte du droit, et la liste fermee qui les
#: definit. Le pouvoir de controle du schema repose entierement sur des
#: egalites de chaines - `a.portee NOT IN (...)`, `JOIN exigences ON
#: e.nature = a.nature`. Une faute de frappe sur `portee` n'active donc pas
#: tous les controles: elle les desactive tous, et l'ecran affiche sereinement
#: "ne s'applique pas". Mesure du 2026-09-04: une ligne portant
#: nature='CE_QUE_JE_VEUX' et portee='PORTEE_INEXISTANTE' etait acceptee.
_VOCABULAIRES: dict[str, dict[str, tuple[str, ...]]] = {
    TABLE_ACTES: {
        "nature": vocabulaire.NATURES,
        "etat": vocabulaire.ETATS,
        "portee": vocabulaire.PORTEES,
        "resultat": vocabulaire.RESULTATS,
        # Le mot `haute`, qu'aucun extracteur n'ecrit, avait fini par vivre
        # dans les fixtures et dans l'ecran des seuils. Trois mots, ceux de
        # l'extracteur, et l'ecran lit les memes.
        "confiance": vocabulaire.CONFIANCES,
    },
    TABLE_LIENS: {
        "relation": vocabulaire.RELATIONS,
        "provenance": vocabulaire.PROVENANCES,
    },
}


def _valider_vocabulaire(table: str, ligne: dict[str, str]) -> None:
    """Refuse une valeur hors liste fermee, au point d'ecriture.

    Le vide est admis: une colonne non renseignee est un fait, pas une faute,
    et plusieurs actes n'ont legitimement ni resultat ni portee lisible.
    Ce qui est refuse est une valeur qui ressemble a du vocabulaire sans en
    etre - c'est elle qui eteint les controles en silence.
    """
    _valider_origine(table, ligne)
    attendus = _VOCABULAIRES.get(table)
    if not attendus:
        return
    for colonne, valeurs in attendus.items():
        valeur = (ligne.get(colonne) or "").strip()
        if valeur and valeur not in valeurs:
            raise ValueError(
                f"table '{table}': valeur inconnue pour '{colonne}': {valeur!r}. "
                f"Attendu l'une de {sorted(valeurs)}. Une valeur hors vocabulaire "
                "desactive silencieusement les controles qui s'appuient dessus."
            )


#: Les colonnes qui portent des euros, et celles qui portent un taux. Le
#: magasin stocke tout en TEXT: sans normalisation ici, `18 240,00 EUR` arrive
#: tel quel en base et la comparaison numerique en rend 18. Mesure du
#: 2026-09-04: le plafond de l'article 21-2 ne se declenchait jamais, sur aucune
#: delegation, sans une exception ni une trace. La defense existait deja
#: (`montant_texte`); ce qui manquait etait le point ou l'imposer.
_MONTANTS: dict[str, tuple[str, ...]] = {
    TABLE_ACTES: ("montant_autorise",),
    TABLE_LIENS: ("montant_impute",),
    TABLE_DOSSIERS: ("montant_ttc", "montant_ht", "tva_annoncee"),
}
_TAUX: dict[str, tuple[str, ...]] = {
    TABLE_DOSSIERS: ("taux_tva_annonce",),
}


def _normaliser_montants(table: str, ligne: dict[str, str]) -> dict[str, str]:
    """Rend la ligne avec ses euros en forme canonique, ou refuse en le disant.

    Normaliser a l'ecriture et non a la lecture est le choix qui compte: une
    base qui contient des chaines ambigues fait trebucher chaque nouveau
    lecteur, et un lecteur qui se trompe ne le sait pas. Ici, la faute a un
    seul endroit et un seul moment.

    Un montant qu'aucune regle ne sait lire n'est pas transforme en `0` ni en
    chaine vide: l'ecriture echoue avec le motif. L'appelant qui traite du
    texte de document - le pont - attrape `MontantIllisible` et ecrit
    `montant_source = ILLISIBLE`, qui est un fait affichable. Ce qu'on ne veut
    nulle part est un nombre plausible.
    """
    colonnes = _MONTANTS.get(table, ())
    taux = _TAUX.get(table, ())
    if not colonnes and not taux:
        return dict(ligne)
    sortie = dict(ligne)
    for colonne, lecture in (
        *((c, montant_texte) for c in colonnes),
        *((c, taux_normalise) for c in taux),
    ):
        if colonne not in sortie:
            continue
        try:
            sortie[colonne] = lecture(sortie[colonne])
        except MontantIllisible as exc:
            raise MontantIllisible(
                exc.valeur,
                f"table '{table}', colonne '{colonne}': {exc.motif}",
            ) from exc
    return sortie

def _valider_origine(table: str, ligne: dict[str, str]) -> None:
    """`origine` porte la cle primaire des cinq tables: elle n'est pas libre.

    Elle est traitee a part des autres colonnes de vocabulaire pour deux
    raisons, et les deux tiennent au fait qu'elle est une **cle**:

    - elle vaut pour les cinq tables et non pour deux, puisque les cinq la
      portent dans leur cle primaire au meme titre que `CLES_RESOLUTIONS`;
    - le vide y est refuse, alors qu'il est admis partout ailleurs. Un
      `resultat` non renseigne est un fait - le proces-verbal ne dit rien.
      Une `origine` vide n'est le fait de personne: la ligne n'est ni un
      extrait de la machine ni une correction humaine, et c'est precisement
      ce que la clause `DELETE ... AND origine <> 'CORRIGE_HUMAIN'` de la
      couche partagee interroge pour decider si elle a le droit de l'effacer.

    Mesure du 2026-09-05 sur le code d'avant: le meme acte ecrit une fois sous
    `EXTRAIT` et une fois sous `EXTRAIT_V2` produisait deux lignes dans
    `v_actes`, deux dans la matrice, et un montant paye de 4000.0 pour une
    facture unique de 2000.00 - sans exception, sans doublon visible a l'ecran.
    """
    valeur = (ligne.get("origine") or "").strip()
    if valeur in gouvernance_store.ORIGINES:
        return
    if not valeur:
        raise ValueError(
            f"table '{table}': 'origine' est vide. Elle entre dans la cle "
            "primaire et decide si une re-extraction a le droit d'effacer la "
            f"ligne. Attendu l'une de {sorted(gouvernance_store.ORIGINES)}."
        )
    raise ValueError(
        f"table '{table}': origine inconnue {valeur!r}. Attendu l'une de "
        f"{sorted(gouvernance_store.ORIGINES)}. `origine` entre dans la cle "
        "primaire: une valeur nouvelle ne signale rien, elle fabrique un "
        "second objet pour un seul fait - deux lignes dans la matrice pour un "
        "acte, et son montant compte deux fois."
    )


def _normaliser_dates(table: str, ligne: dict[str, str]) -> None:
    """Range les dates en ISO, ou refuse la ligne en disant laquelle.

    Toute regle de droit du modele est une comparaison de chaines: l'echeance
    de l'article 21-5, le plafond de l'article 21-2, l'expiration d'une
    delegation. Une chaine qu'aucun ordre lexical ne classe correctement ne
    rend pas la regle fausse une fois sur deux - elle la rend fausse toujours,
    dans un sens ou dans l'autre, et sans lever. Mesure du 2026-09-04 sur des
    dates `jj/mm/aaaa`: une accusation fausse portee contre le syndic d'un
    cote, un depassement de plafond reel rendu invisible de l'autre.

    La normalisation a lieu ici plutot qu'a la lecture pour une raison de
    magasin: la base doit porter une seule forme, sinon deux lignes ecrites par
    deux chemins differents ne se comparent plus entre elles.
    """
    for colonne in COLONNES_DATE.get(table, ()):
        if colonne not in ligne:
            continue
        try:
            ligne[colonne] = date_iso(ligne[colonne])
        except DateNonOrdonnable as exc:
            raise ValueError(f"table '{table}', colonne '{colonne}': {exc}") from exc


def _refuser_les_cles_en_double(
    table: str, cles: Sequence[str], lignes: Sequence[dict[str, str]]
) -> None:
    """Deux lignes du meme lot ne peuvent pas porter la meme cle.

    `INSERT OR REPLACE` en garde une et jette l'autre, sans un mot. Le cas
    n'est pas theorique: sur une assemblee reelle, deux lignes portaient le
    numero 3 - une ligne parasite decrivant un lot, et le vote sur le
    non-renouvellement du mandat du syndic - et le journal ecrivait `9` la ou
    le coffre en gardait 8. Sur le second corpus, `11.1` a `11.8` non lus
    comme sous-numeros rendaient six fois le meme identifiant, donc un acte
    pour six resolutions.

    Deux faits distincts qui reclament la meme identite sont une question a
    trancher, jamais une ligne a supprimer en silence.

    **La detection est celle de la couche partagee**, `collisions_de_cle`: le
    registre des resolutions rapporte les memes collisions au lieu de les
    refuser. Une detection, deux politiques - deux detections finiraient par
    diverger, et un lot serait accepte ici et compte la-bas.
    """
    collisions = gouvernance_store.collisions_de_cle(lignes, cles)
    if collisions:
        cle, combien = next(iter(collisions.items()))
        raise ValueError(
            f"table '{table}': {combien} lignes du meme lot portent la cle "
            f"{dict(zip(cles, cle))}. L'ecriture en garderait une et jetterait "
            "les autres sans le dire. Deux faits distincts reclament ici la "
            "meme identite: c'est un numero, un sous-numero ou une date a "
            f"departager. Cles en collision dans ce lot: {len(collisions)}."
        )


def ecrire(
    instance: Any,
    table: str,
    lignes: Sequence[dict[str, str]],
    doc_ids: Sequence[str],
) -> int:
    """Remplace les lignes derivees des documents cites, et rend leur nombre.

    La garde qui protege les corrections humaines est dans la couche partagee,
    donc dans la clause `DELETE` elle-meme. Deux consequences a connaitre:

    - une ligne `CORRIGE_HUMAIN` survit a toute re-extraction du meme document;
    - `doc_ids` vide n'efface rien. C'est ainsi que `traces_controle` s'ecrit:
      une conclusion humaine ne derive d'aucun document, donc rien ne doit
      pouvoir la supprimer par document.
    """
    if table not in TABLES:
        raise ValueError(f"Table inconnue pour le lot actes: {table}")
    colonnes, cles, _ = TABLES[table]
    # La couche partagee prend les colonnes declarees et ignore le reste. Une
    # cle mal orthographiee disparaitrait donc sans bruit, et la perte ne se
    # verrait qu'a l'ecran, plus tard, sur une valeur vide inexplicable. On la
    # signale ici, au point d'ecriture.
    connues = set(colonnes)
    lignes = [dict(ligne) for ligne in lignes]
    for ligne in lignes:
        inconnues = sorted(set(ligne) - connues)
        if inconnues:
            raise ValueError(
                f"table '{table}': colonnes inconnues {inconnues}. "
                "Un champ non declare serait ecrit nulle part et perdu en silence."
            )
        _valider_vocabulaire(table, ligne)
        # Les deux normalisations vivent au meme point d'ecriture, et pour la
        # meme raison: une base qui contient des chaines ambigues fait
        # trebucher chaque nouveau lecteur, et un lecteur qui se trompe ne le
        # sait pas. Ici la faute a un seul endroit et un seul moment.
        ligne.update(_normaliser_montants(table, ligne))
        _normaliser_dates(table, ligne)
    _refuser_les_cles_en_double(table, cles, lignes)
    preparer(instance)
    return gouvernance_store.remplacer_pour_documents(
        instance, colonnes, lignes, doc_ids, table=table, cles=cles
    )


def lire_table(instance: Any, table: str) -> list[dict[str, str]]:
    """Le contenu brut d'une table. Rarement le bon outil: preferer `lire_vue`.

    Lire la table nue montre `EXTRAIT` **et** `CORRIGE_HUMAIN` du meme objet.
    C'est ce qu'on veut pour un export d'audit, jamais pour un ecran.
    """
    if table not in TABLES:
        raise ValueError(f"Table inconnue pour le lot actes: {table}")
    _, _, ordre = TABLES[table]
    return gouvernance_store.lire(instance, table=table, ordre=ordre)


def lire_vue(
    instance: Any,
    vue: str,
    criteres: Sequence[tuple[str, str, Any]] = (),
    *,
    ordre: str = "",
    limite: int | None = None,
) -> list[dict[str, Any]]:
    """Lecture filtree d'une vue, par le contrat de `_actes_requetes`.

    Aucune chaine SQL ne vient de l'appelant: il donne des noms de filtres
    declares et des valeurs parametrees. C'est ce qui rend impossible le retour
    du balayage de mots-cles - il n'y a pas d'endroit ou l'ecrire.

    **Les vues sont realignees avant la lecture.** Une base ecrite par une
    version anterieure porte la regle de droit de cette version; la laisser
    repondre rendrait des nombres coherents entre eux et faux, sans un signal.
    C'est le seul endroit du produit ou ce realignement a lieu.
    """
    if vue not in NOMS_VUES:
        raise ValueError(f"Vue inconnue: {vue}")
    sql, params = requetes.construire_requete(
        criteres, vue=vue, ordre=ordre, limite=limite
    )
    try:
        chemin = gouvernance_store.store_path(instance)
    except GouvernanceStoreIndisponible:
        return []
    if not chemin.exists():
        return []
    rafraichir_vues(instance)
    with connexion(instance) as cx:
        try:
            curseur = cx.execute(sql, params)
        except sqlite3.OperationalError as exc:
            # Une TABLE absente est une instance ou rien n'a encore ete verse:
            # liste vide, et l'appelant doit distinguer `pas de coffre`,
            # `coffre vide` et `aucun resultat` - trou T10 du blueprint.
            #
            # Une VUE absente n'est pas cela, et c'est la correction du
            # 2026-09-04: elle vient d'etre recreee juste au-dessus, donc si
            # elle manque encore, la base est abimee. Rendre `[]` affichait
            # `aucun acte n'est encore verse` sur une base qui en portait 173.
            #
            # Tout le reste remonte. Un `no such column` avale par un `except
            # OperationalError` large rend une liste vide indiscernable d'une
            # absence de resultat - c'est exactement le defaut T10, et il s'est
            # produit pendant l'ecriture de ce module: une colonne manquante
            # dans une vue a rendu zero constat au lieu de 818, en silence.
            manquant = str(exc).split("no such table:")[-1].strip()
            if "no such table" in str(exc) and manquant not in NOMS_VUES:
                return []
            raise SchemaDeGouvernanceDivergent(
                f"vue '{vue}': la lecture a echoue sur \"{exc}\" alors que les "
                "vues viennent d'etre realignees sur le code. Une liste vide "
                "ici s'afficherait comme un modele non alimente."
            ) from exc
        return [dict(row) for row in curseur]
