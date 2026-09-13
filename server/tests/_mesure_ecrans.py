# -*- coding: utf-8 -*-
"""L'INSTRUMENT de la garde `test_ecran_promet_ce_que_la_production_produit`.

Separe du fichier de garde le 2026-09-09, quand celui-ci a depasse 600 lignes.
Ici vit ce qui MESURE - l'instance vide, l'absorption, l'autorisateur SQLite,
les deux collectes de constructeurs. Dans le fichier de garde vivent les
DECLARATIONS et les assertions.

Les deux collectes sont volontairement independantes l'une de l'autre:
`_constructeurs_de_vue` passe par l'import, `_constructeurs_dans_les_sources`
par le texte. Une garde compare leurs resultats, parce qu'une collecte qui rend
moins qu'elle ne devrait ne se distingue pas, seule, d'une couche web plus
petite.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import json
import pkgutil
import shutil
import sqlite3
from pathlib import Path

import coproscope.web as web_pkg
from coproscope.vault.gouvernance_store import GOUVERNANCE_DB_FILE

RACINE_WEB = Path(web_pkg.__file__).resolve().parent
DEPOT = Path(__file__).resolve().parents[2]

#: Le proces-verbal minimal absorbe par l'instance vide. Il porte les trois
#: formes dont la chaine a besoin pour exercer ses chemins d'ecriture: une
#: approbation de comptes, un vote de travaux avec montant, et une delegation au
#: conseil syndical avec plafond et duree - c'est cette derniere qui fait poser
#: un lien de seuil, donc qui prouve que `liens_gouvernance` a un producteur.
PV_MINIMAL = """PROCES-VERBAL DE L'ASSEMBLEE GENERALE ORDINAIRE
Assemblee generale du 20 mai 2026

RESOLUTION N1 - Approbation des comptes de l'exercice 2025
Le syndicat approuve les comptes de l'exercice clos le 31 decembre 2025.
Vote a la majorite de l'article 24. POUR: 8500 - CONTRE: 0 - ABSTENTION: 500.
Cette resolution est adoptee.

RESOLUTION N2 - Travaux de refection de la toiture
Le syndicat autorise les travaux de refection de la toiture pour un montant de
42 000,00 EUR, conformement au devis de l'entreprise mandatee.
Vote a la majorite de l'article 25. POUR: 7200 - CONTRE: 1300 - ABSTENTION: 500.
Cette resolution est adoptee.

RESOLUTION N3 - Mandat donne au conseil syndical
Le syndicat donne mandat au conseil syndical pour engager les depenses courantes
dans la limite de 5 000,00 EUR par operation, pour une duree de douze mois.
Vote a la majorite de l'article 25. POUR: 8000 - CONTRE: 500 - ABSTENTION: 500.
Cette resolution est adoptee.
"""


ECRITURES = (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE)


def _instance_vide(racine: Path) -> Path:
    """Une instance VIDE qui reabsorbe ses pieces, jamais une copie chargee.

    Consigne de Brice du 2026-09-07: une copie chargee porte la SORTIE de la
    version precedente du code et la fait entrer comme si c'etait une entree.
    Ici la question posee est *quel chemin ECRIT*, donc une instance qui
    contiendrait deja les lignes repondrait a cote.
    """
    source = DEPOT / "examples" / "synthetic_copro"
    racine.mkdir(parents=True, exist_ok=True)
    shutil.copy(source / "instance.yml", racine / "instance.yml")
    shutil.copytree(source / "raw", racine / "raw")
    shutil.copytree(source / "system", racine / "system")
    for dossier in ("registers", "outputs", "staging", "logs"):
        (racine / dossier).mkdir()
    config = json.loads((racine / "instance.yml").read_text(encoding="utf-8"))
    config.setdefault("settings", {})["vault"] = {"local_root": "./vault_local"}
    (racine / "instance.yml").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (racine / "raw" / "2026-05-20_pv_assemblee_generale.txt").write_text(
        PV_MINIMAL, encoding="utf-8"
    )
    return racine


class _Mouchard:
    """Note, par observation SQLite, les tables lues et ecrites des magasins.

    Le point d'interception est `sqlite3.connect` lui-meme, pas une fonction du
    depot: toute couche, presente ou future, qui ouvre un magasin est vue.

    **CE QUI A CHANGE LE 2026-09-12, ET POURQUOI CE N'ETAIT PAS UN DETAIL.**
    L'autorisateur ne s'armait que si le fichier ouvert s'appelait
    `gouvernance.sqlite3`. C'etait une **modalite**: l'axe est *un magasin du
    coffre*, et le depot en porte **deux** - `gouvernance.sqlite3`, que la
    chaine ecrit et que les ecrans lisent, et `vault_reconstruction.sqlite3`,
    ou vivent les objets reconstruits `points`, `actions`, `expected_pieces`,
    `object_links`, `event_log` et `source_import_map`. Tout le second etait
    **hors du champ de vision de la garde**, ecritures comme lectures.

    **La mesure du jour dit que cela ne changeait rien AUJOURD'HUI, et il faut
    le dire aussi:** une seule base est ouverte pendant toute la mesure,
    `gouvernance.sqlite3`. Le defaut etait donc **latent**, pas actif - mais le
    second magasin existe deja dans le code, et le jour ou un ecran le lirait,
    la garde serait restee muette. *Le silence d'une garde n'est une preuve que
    si l'on sait ou elle regarde.*

    Ce que l'instrument note desormais: la **base** avec la table, dans
    `par_base`. `lues` et `ecrites` restent l'union, donc les assertions
    existantes sont inchangees; `bases_vues` dit ce qui a reellement ete ouvert,
    ce qui permet a une garde d'affirmer qu'un magasin n'a ete touche par aucun
    chemin exerce - au lieu de le supposer.
    """

    def __init__(self) -> None:
        self.lues: set[str] = set()
        self.ecrites: set[str] = set()
        #: `(base, table) -> {"lues"|"ecrites"}`, pour distinguer les magasins.
        self.par_base: dict[str, dict[str, set[str]]] = {}
        #: Les noms de fichier des bases REELLEMENT ouvertes pendant la mesure.
        self.bases_vues: set[str] = set()
        self.mode = "ecriture"
        self.connexions_vues = 0
        self._vrai_connect = sqlite3.connect

    def __enter__(self) -> "_Mouchard":
        sqlite3.connect = self._connect
        return self

    def __exit__(self, *_exc) -> None:
        sqlite3.connect = self._vrai_connect

    def _connect(self, *args, **kwargs):
        connexion = self._vrai_connect(*args, **kwargs)
        chemin = str(args[0] if args else kwargs.get("database", ""))
        nom = Path(chemin).name
        # Aucun nom de fichier n'est enumere ici. Une base en memoire n'est pas
        # un magasin: elle ne survit pas a la connexion, donc rien de ce qu'elle
        # porte ne peut etre montre a personne.
        if not nom or nom == ":memory:":
            return connexion
        self.bases_vues.add(nom)
        if nom == GOUVERNANCE_DB_FILE:
            self.connexions_vues += 1
        connexion.set_authorizer(
            lambda action, arg1, arg2, base, source, _nom=nom:
            self._autoriser(action, arg1, arg2, base, source, _nom))
        return connexion

    def _autoriser(self, action, arg1, arg2, base, source, nom=""):
        vu = None
        if action in ECRITURES:
            if self.mode == "ecriture":
                self.ecrites.add(arg1)
                vu = "ecrites"
        elif action == sqlite3.SQLITE_READ:
            if self.mode == "lecture":
                self.lues.add(arg1)
                vu = "lues"
        if vu and nom:
            entree = self.par_base.setdefault(nom, {"lues": set(), "ecrites": set()})
            entree[vu].add(arg1)
        return sqlite3.SQLITE_OK

    def connexion_directe(self, chemin: Path) -> sqlite3.Connection:
        return self._vrai_connect(str(chemin))


def _constructeurs_de_vue():
    """Tous les `build_*` de la couche web, sous-paquets compris.

    **Le selecteur est le PAQUET, jamais un suffixe de nom de fichier.**
    Correction du 2026-09-09, apres mesure. La version precedente ne regardait
    que les modules dont le nom finit par `_view`, et se degradait FAUX EN
    SILENCE: un constructeur pose ailleurs n'etait ni mesure, ni declare hors
    portee, ni signale - il sortait de la garde sans qu'aucun test ne bouge.

    Ce n'etait pas une hypothese. Preuve par A/B, fonction identique au bit
    pres, lisant une table orpheline non declaree:

    - dans `temoin_refutateur_view.py`, la garde tombe en nommant l'ecran;
    - dans `governance.py`, la suite entiere passe au VERT.

    Seul le suffixe du nom de fichier differait. Et l'angle mort etait deja
    peuple: six `build_*` y vivaient, dont `build_governance_overview(instance,
    year)`, exactement la forme que cette garde pretend couvrir.

    `RM-2026-0087` avait etabli le meme defaut dans ce meme dossier la veille -
    *27 des 87 modules .py de web/ sont invisibles a un balayage a plat* - et
    l'avait corrige par un parcours recursif. La lecon n'avait pas traverse.
    """
    vus: set[str] = set()
    for info in sorted(
        pkgutil.walk_packages([str(RACINE_WEB)], prefix="coproscope.web."),
        key=lambda i: i.name,
    ):
        if info.name in vus:
            continue
        vus.add(info.name)
        module = importlib.import_module(info.name)
        for nom, objet in sorted(vars(module).items()):
            if not nom.startswith("build_") or not inspect.isfunction(objet):
                continue
            if objet.__module__ != module.__name__:
                continue
            yield nom, objet


def _defs_de_module(noeud):
    """Les `def` de niveau module, sans descendre dans les corps de fonction.

    Un `build_ligne` niche dans une fonction n'est pas un constructeur d'ecran
    et ne pourra jamais etre collecte: l'exiger fabriquerait un faux positif
    qu'on ne pourrait lever qu'en affaiblissant la garde.
    """
    for enfant in ast.iter_child_nodes(noeud):
        if isinstance(enfant, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield enfant
        elif isinstance(enfant, (ast.If, ast.Try, ast.With)):
            yield from _defs_de_module(enfant)


def _constructeurs_dans_les_sources() -> dict[str, str]:
    """Tout `def build_*` ECRIT sous `web/`, lu par l'AST et non par l'import.

    Second instrument, independant du premier. La collecte par import depend
    d'une chaine entiere - le module s'importe, le paquet se parcourt, la
    fonction porte le bon `__module__`. Si un maillon cede, elle rend moins,
    et moins ressemble a rien. Le balayage du texte, lui, ne depend que du
    fichier: l'ecart entre les deux est ce qui rougit.
    """
    trouves: dict[str, str] = {}
    for chemin in sorted(RACINE_WEB.rglob("*.py")):
        arbre = ast.parse(chemin.read_text(encoding="utf-8"))
        for noeud in _defs_de_module(arbre):
            if noeud.name.startswith("build_"):
                trouves[noeud.name] = chemin.relative_to(RACINE_WEB).as_posix()
    return trouves


def _arguments_requis(fonction) -> list[str]:
    return [
        p.name
        for p in inspect.signature(fonction).parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    ]


