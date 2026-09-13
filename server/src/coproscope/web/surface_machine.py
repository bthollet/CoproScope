"""Ce qu'une surface machine rend, et pourquoi c'est une DECLARATION.

**Le defaut, mesure le 2026-09-09 sur `913d744`.** `/api/model` rendait
`_dashboard_model()` **verbatim**: 318 872 octets de JSON, 19 branches, 22
tables. Aucun gabarit et aucun script de l'interface ne la consomme - verifie
par recherche sur `templates/` et `static/`, zero occurrence. Cette route
n'existe donc que pour etre lue par une machine, et elle rendait tout ce que le
modele portait.

**Le chiffre annonce etait de 15. La mesure en donne 102.** `RM-2026-0130`
parlait de « 15 colonnes de tiers », nombre repris du test
`test_RESIDU_la_surface_machine_rend_encore_les_valeurs_de_tiers`. Ce test
n'instrumentait qu'**un seul** registre, `registre_documents.csv`, qui porte 54
colonnes dont 15 de tiers. En posant la sentinelle dans **les 18 CSV** de
l'instance - 114 colonnes de tiers au total - il en ressort **102** par
`/api/model`, dont `fournisseur`, `numero_facture`, `siren_siret`,
`author_label`, `emitter`.

Le 15 n'etait pas une erreur de calcul: c'etait la **portee du temoin** prise
pour la taille du defaut. C'est exactement la lecon du 2026-09-08, reecrite un
cran plus haut: *une garde ne couvre pas ce qu'elle parcourt, elle couvre ce que
son temoin atteint* - et un CHIFFRE rendu par une garde herite de la meme
limite que la garde.

**Et le defaut ne s'arrete pas aux colonnes.** La meme mesure a trouve, sortant
de la meme route:

- **24 chemins locaux absolus**, dont `model.instance.root`, c'est-a-dire le
  repertoire personnel reel de l'utilisateur en production;
- des valeurs de tiers arrivees dans des cles qui ne sont **pas** des noms de
  colonnes - `model.ux.comptes.ag_report.p2_points[].explanation`,
  `model.accounting.guide.p2[].question`. Un filtre par nom de cle les aurait
  laissees passer, et aurait eu l'air de fonctionner.

**L'axe.** Une route rend **ce que sa vue exige**, jamais tout ce que sa table
porte. C'est la dimension; les 102 colonnes en sont des valeurs observees
aujourd'hui, et coder leur liste serait coder des modalites - la 103e sortirait
demain sans que personne ne le sache.

**L'invariant le long de l'axe:** ce qui sort d'une surface machine est ecrit
par CoproScope, jamais recopie d'un registre.

**Ce que le code en fait.** La surface est **construite**, pas filtree. C'est le
point de conception, et il ne se resume pas a un gout pour les listes blanches:

- **filtrer**, c'est partir du tout et retirer ce qu'on a pense a nommer. Ce
  qu'on oublie **sort**. Une colonne 55, une cle `explanation`, une refonte du
  modele: chacune est une occasion d'oubli, et l'oubli est **muet**;
- **construire**, c'est partir de rien et ajouter ce qu'on declare. Ce qu'on
  oublie **manque**. Un champ absent se voit tout de suite; une fuite ne se voit
  jamais.

Le sens du defaut est choisi, comme dans `provenance_champs.py`: liste ouverte
par le bas, fermee par le haut.

**Ce qui se passe hors des valeurs observees - le test d'acceptation.** Un
troisieme registre arrive demain avec des colonnes inconnues; un lot ajoute une
branche `model.contrats`. Que se passe-t-il ? La branche n'est pas declaree,
donc elle **ne sort pas**. Ses tables sont comptees - `lignes` et `colonnes`,
deux entiers - et rien d'autre. Le systeme se degrade en **disant moins**, pas
en **disant faux**: il n'y a aucun chemin par lequel une valeur inconnue sorte
en silence, parce qu'aucune valeur de registre n'est jamais recopiee.

**Ce que cette surface ne protege PAS, et qu'il ne faut pas se raconter.**

1. Elle ne protege que `/api/model`. Les 53 autres routes GET restent couvertes
   par `test_ui_nom_de_fichier_ne_fuit_pas`, qui travaille par sentinelle sur
   les reponses servies. Les deux gardes sont independantes;
2. le **nom** d'une table sort - par exemple `documents.documents`. Ce sont les
   cles structurelles du modele, ecrites dans le code du viewmodel, jamais lues
   dans un registre. Si un lot construisait un jour une cle de modele a partir
   d'une valeur de registre, ce raisonnement tomberait, et c'est la sentinelle
   de `test_surface_machine_ne_rend_que_le_declare.py` qui le dirait - elle
   compare des VALEURS, donc elle voit ce que ce module ne voit pas;
3. les **comptes** sont eux-memes une information: savoir qu'une copropriete a
   9 documents et 2 anomalies n'est pas rien. C'est un choix assume, pas un
   oubli - un resume qui ne compte rien ne serait plus un resume.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass

#: Nom du contrat rendu. Il est **dans la reponse** pour qu'un consommateur
#: sache ce qu'il lit, et pour qu'un changement de surface soit un changement
#: de nom plutot qu'une mutation silencieuse du meme mot `model`.
SURFACE_DECLAREE = "resume_declare_v1"

#: Ce que la surface annonce d'elle-meme, en clair, pour l'humain qui l'ouvre.
#: `/api/model` etait un dump; le dire evite qu'on reprenne l'ancienne habitude
#: en croyant que la route a simplement cesse de fonctionner.
NOTE_SURFACE = (
    "Resume declare. Cette route ne rend aucune valeur lue dans un registre: "
    "seulement les noms de branches et de tables du modele, ecrits par "
    "CoproScope, et des comptes. Voir web/surface_machine.py."
)


def _champ(noeud: object, nom: str) -> object:
    """Lit un champ, que le noeud soit un dictionnaire ou un objet.

    **La representation d'une table est un degre de liberte, pas une modalite.**
    Premiere version de ce fichier: `isinstance(noeud, dict)`. Elle a recense
    **2 tables sur 22**, parce que le modele porte ses tables comme des
    `DataTable` - une dataclass - et ne les convertit en dictionnaires qu'au
    moment de la serialisation JSON, donc APRES ce parcours. Les deux seules
    trouvees etaient les deux qui, par hasard, etaient encore des dictionnaires.

    Le chiffre corrige ici est 22, et non 20: ce fichier annoncait deux
    totaux differents pour la meme notion - 20 dans ce module, 22 dans son
    test - alors que la mesure en donne 22 sur `examples/synthetic_copro`
    comme sur le corpus etalon. Deux comptages concurrents pour une meme
    notion, dans un module ecrit contre ce defaut.

    Le defaut etait exactement celui que ce module denonce: un compte qui a
    l'air d'une preuve et qui mesure la portee de l'instrument. Il n'aurait fait
    echouer aucun test de fuite - une table non recensee ne fuit rien, elle
    manque. C'est la mesure d'utilisabilite qui l'a montre, pas la garde.
    """

    if isinstance(noeud, Mapping):
        return noeud.get(nom)
    if is_dataclass(noeud) and not isinstance(noeud, type):
        return getattr(noeud, nom, None)
    return None


def _enfants(noeud: object):
    """Les sous-noeuds a visiter, avec le suffixe de chemin qui les designe."""

    if isinstance(noeud, Mapping):
        for cle, valeur in noeud.items():
            if isinstance(cle, str):
                yield f".{cle}", valeur
    elif isinstance(noeud, (list, tuple)):
        for valeur in noeud:
            yield "[]", valeur
    elif is_dataclass(noeud) and not isinstance(noeud, type):
        for champ in fields(noeud):
            yield f".{champ.name}", getattr(noeud, champ.name, None)


def _largeur(noeud: object) -> int:
    """Le nombre de colonnes de la table, sans emettre leur nom.

    On prefere l'en-tete declare quand il existe; sinon on retombe sur les cles
    reellement presentes dans les lignes. Les deux rendent un ENTIER: aucun nom
    de colonne ne sort d'ici.
    """

    champs = _champ(noeud, "fields")
    if isinstance(champs, (list, tuple)) and champs:
        return len(champs)
    lignes = _champ(noeud, "rows")
    cles: set[str] = set()
    for ligne in lignes or []:
        if isinstance(ligne, Mapping):
            cles.update(cle for cle in ligne if isinstance(cle, str))
    return len(cles)


def _recense_tables(noeud: object, chemin: str, trouve: dict[str, dict[str, int]]) -> None:
    """Parcourt le modele et compte chaque table rencontree, a toute profondeur.

    Une table se reconnait a sa **forme** - un `rows` qui est une liste - et non
    a son nom ni a son type. Une table ajoutee demain sous un nom inconnu, ou
    portee par une autre classe, est comptee le jour de son ajout.
    """

    lignes = _champ(noeud, "rows")
    if isinstance(lignes, (list, tuple)):
        trouve[chemin or "(racine)"] = {
            "lignes": len(lignes),
            "colonnes": _largeur(noeud),
        }
    for suffixe, enfant in _enfants(noeud):
        _recense_tables(enfant, f"{chemin}{suffixe}" if chemin else suffixe.lstrip("."), trouve)


def resume_machine(model: object) -> dict[str, object]:
    """Le resume declare que rend `/api/model`.

    **Ne modifie jamais `model`.** Le modele du tableau de bord est mis en cache
    et partage par toutes les routes HTML de l'application: le muter ici
    changerait ce que voient 53 autres pages. Cette fonction ne fait que lire,
    et construit une structure neuve.

    Toute valeur emise est soit une chaine ecrite dans ce fichier, soit une cle
    structurelle du modele, soit un entier. Aucune n'est recopiee d'un registre.
    """

    tables: dict[str, dict[str, int]] = {}
    _recense_tables(model, "", tables)
    branches = sorted(model) if isinstance(model, Mapping) else []
    return {
        "surface": SURFACE_DECLAREE,
        "note": NOTE_SURFACE,
        "branches": [cle for cle in branches if isinstance(cle, str)],
        "tables": {nom: dict(compte) for nom, compte in sorted(tables.items())},
        "total_tables": len(tables),
        "total_lignes": sum(compte["lignes"] for compte in tables.values()),
    }
