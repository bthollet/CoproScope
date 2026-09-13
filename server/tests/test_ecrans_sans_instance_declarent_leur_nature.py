# -*- coding: utf-8 -*-
"""Un ecran qui ne PEUT PAS lire l'instance doit declarer sa nature.

Instruction de `RM-2026-0059` le 2026-09-08. L'item annonce *quatre pages sur
onze ne lisent aucune donnee*. Le critere retenu ici est plus dur que celui de
l'item: la fonction de construction n'a **aucun canal d'entree** - tous ses
parametres sont des scalaires, `(year: int = 2025)` - donc elle ne *peut pas*
lire de donnees, quoi qu'il arrive dans son corps.

**Deux mesures, a un jour d'intervalle, et l'ecart n'est pas un bruit.**
Le 2026-09-08, **huit** routes servies etaient dans ce cas, et les huit se
declaraient deja. Le 2026-09-09: **zero**. Entre les deux, le commit `4140931`
- *« identite: douze ecrans nommaient une copropriete qui n'etait pas la
leur »* - a donne un parametre `instance` a ces huit constructeurs. Les deux
lots ne touchaient pas les memes lignes: **git n'avait aucun conflit a
signaler**, et la population de cette garde est passee de huit a zero le jour
de sa livraison. C'est la deuxieme fois de la journee qu'un lot vide le corpus
d'une garde d'un autre lot sans qu'aucun outil ne le voie.

**Ce que la garde protege n'a pas change pour autant.** Elle n'est pas un
compteur de defauts - un compteur qui exige que son defaut survive rougit le
jour ou le produit va mieux. Elle garantit qu'un ecran ajoute demain sans canal
d'entree ne pourra pas afficher des donnees inventees sans le dire.

**MAIS LA COUVERTURE DES HUIT EST PERDUE, ET REPARER L'INSTRUMENT NE LA REND
PAS.** Le lot `RM-2026-0059` l'avait dit et laisse l'arbitrage ouvert: *« NON
CORRIGE, et c'est la decision a prendre [...] Redefinir le critere est un
arbitrage produit. »* Mesure du 2026-09-10: les huit rendent toujours du
contenu fictif - de 3 a 23 marqueurs par ecran sur une instance reelle - et
les huit portent une `notice`, donc l'honnetete tient. Ce qui a disparu est ce
qui la FORCAIT.

Le critere qui la rendrait n'est pas trouvable par simple elargissement, et on
l'a mesure au lieu de le supposer: **aucun** des 35 constructeurs ne rend un
modele identique avec et sans instance, parce que tous en tirent au moins
l'identite de la copropriete. Un ecran peut donc lire l'instance pour NOMMER la
copropriete et inventer tout le reste - c'est exactement l'etat des huit. Le
critere juste porte sur *l'ecran invente-t-il ses donnees*, pas sur la forme de
sa signature, et le choisir est un arbitrage produit qui reste a Brice.

**Ce qui manquait est la GARDE.** Cette honnetete tenait par convention. Un
neuvieme ecran ajoute demain sans mention passerait tous les tests existants et
afficherait des donnees inventees sans le dire - et l'auteur n'aurait rien fait
de mal, puisque rien ne le lui demandait.

**L'axe, et il ne porte pas sur le mot employe.** Ce qui est verifie ici est la
PRESENCE d'une nature declaree et le fait qu'elle atteigne l'ecran, jamais sa
redaction. Exiger le mot `FICTIF` serait coder une modalite: la neuvieme page
dirait `maquette`, `demonstration` ou `exemple`, la garde la refuserait a tort,
et on l'affaiblirait pour la faire passer.

**Ce test ne tranche pas `RM-2026-0059`.** Brancher ces ecrans sur une source
reelle ou les retirer est une decision de produit qui appartient a Brice. Il
garantit seulement qu'aucun d'eux, ni aucun de leurs futurs freres, ne puisse
mentir en silence en attendant cette decision.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil
import re
import unittest
from pathlib import Path

import coproscope.web as web_pkg

RACINE_WEB = Path(web_pkg.__file__).resolve().parent
GABARITS = RACINE_WEB / "templates"

#: Types qui ne peuvent transporter aucune donnee de copropriete: un entier, un
#: texte, un booleen. Un constructeur dont TOUS les parametres sont de ce genre
#: n'a aucun canal d'entree - il ne peut que rendre ce qui est ecrit dans son
#: corps.
#:
#: **Ce critere a remplace une modalite, et l'erreur vaut d'etre gardee.** La
#: premiere version demandait *le constructeur a-t-il un parametre nomme
#: `instance` ?*. C'etait coder UNE facon de recevoir des donnees: elle
#: accusait a tort `build_annotations_view` et `build_document_intake_view`,
#: qui recoivent leurs lignes directement. La question juste n'est pas comment
#: les donnees arrivent, c'est **s'il existe un chemin par lequel elles
#: pourraient arriver**.
#:
#: **Hors des valeurs observees:** une annotation inconnue est traitee comme
#: pouvant porter des donnees, donc l'ecran n'est PAS declare aveugle. La garde
#: se tait plutot que d'accuser a tort - se degrader en silence est ici le bon
#: comportement, parce que le cout d'un faux positif est qu'on affaiblisse la
#: garde pour le faire taire.
TYPES_SANS_DONNEES = {"int", "str", "bool", "float"}


def _constructeurs_de_vue():
    """Tous les `build_*` de la couche web, sans regarder le nom des fichiers.

    **La version precedente lisait `if not info.name.endswith("_view")`, et
    c'etait une modalite.** Son module frere a corrige exactement ce point le
    2026-09-09 - *« la garde ne voyait que les fichiers nommes *_view »* - et la
    correction n'a pas ete portee ici: six `build_*` vivaient dans l'angle mort,
    dont `build_governance_overview`. **Une correction ne couvre que le site
    qu'elle touche**, et c'est la deuxieme fois de la journee.
    """
    trouves = []
    for info in pkgutil.walk_packages([str(RACINE_WEB)], "coproscope.web."):
        try:
            module = importlib.import_module(info.name)
        except Exception:  # noqa: BLE001 - un module non importable n'est pas un ecran
            continue
        for nom, objet in vars(module).items():
            if not nom.startswith("build_") or not inspect.isfunction(objet):
                continue
            if objet.__module__ != module.__name__:
                continue
            trouves.append((module, nom, objet))
    return trouves


def _a_un_canal_de_donnees(fonction) -> bool:
    """Existe-t-il un parametre par lequel des donnees pourraient entrer ?"""
    for p in inspect.signature(fonction).parameters.values():
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            return True
        annotation = p.annotation
        if annotation is inspect.Parameter.empty:
            return True
        texte = annotation if isinstance(annotation, str) else getattr(annotation, "__name__", str(annotation))
        if texte.strip() not in TYPES_SANS_DONNEES:
            return True
    return False


def _appelable_sans_argument(fonction) -> bool:
    return all(
        p.default is not inspect.Parameter.empty
        or p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        for p in inspect.signature(fonction).parameters.values()
    )


class EcranSansInstanceDeclareSaNature(unittest.TestCase):
    def setUp(self) -> None:
        self.aveugles = [
            (m, n, f) for (m, n, f) in _constructeurs_de_vue()
            if not _a_un_canal_de_donnees(f) and _appelable_sans_argument(f)
        ]

    def test_LA_COLLECTE_ATTEINT_REELLEMENT_LES_ECRANS(self):
        """Garde de l'instrument, premiere moitie: le balayage trouve du code.

        **Ce test exigeait autre chose, et la phrase contredite est citee.** Il
        affirmait `assertGreaterEqual(len(self.aveugles), 1, "aucun
        constructeur de vue collecte: la collecte est cassee, pas le produit")`
        - c'est-a-dire qu'**au moins un ecran aveugle devait exister**.

        **Il etait rouge le jour meme de sa livraison, son lot l'avait DIT, et
        c'est le fil qui l'a fusionne sans jouer ce module.** Sa doctrine annonce *« la mesure en trouve huit »*: mesure du
        2026-09-08 sur les huit ecrans de signature `(year: int = 2025)`. Le
        commit `4140931`, *« identite: douze ecrans nommaient une copropriete
        qui n'etait pas la leur »*, leur a donne a tous les huit un parametre
        `instance` - donc un canal d'entree. Les deux lots ne se touchaient
        pas: **git n'avait aucun conflit a signaler**, et la population de
        cette garde est passee de huit a zero.

        **Un compteur de defauts ne fait pas une garde d'instrument.** Exiger
        qu'un ecran aveugle existe revient a exiger que le defaut survive: le
        jour ou le produit va mieux, la garde rougit. Ce qui doit etre garanti
        est que **l'instrument fonctionne**, et cela se prouve en deux temps -
        la collecte atteint le code (ici), et le critere sait encore dire non
        (test suivant), sur un temoin ecrit pour cela.
        """
        tous = _constructeurs_de_vue()
        self.assertGreaterEqual(
            len(tous), 25,
            "la collecte ne trouve presque plus de constructeur d'ecran: c'est "
            "le balayage qui est casse, pas le produit (29 au 2026-09-09)",
        )

    def test_LE_CRITERE_SAIT_ENCORE_DIRE_NON(self):
        """Garde de l'instrument, seconde moitie: eprouvee sur un temoin.

        Zero ecran aveugle peut vouloir dire deux choses opposees: le produit
        n'en a plus, ou le critere ne sait plus en reconnaitre. Un temoin ecrit
        ici, de la forme exacte que la garde vise, tranche entre les deux.
        """

        def build_temoin_aveugle(year: int = 2025) -> dict:
            return {"notice": "temoin de garde, jamais servi"}

        self.assertFalse(_a_un_canal_de_donnees(build_temoin_aveugle))
        self.assertTrue(_appelable_sans_argument(build_temoin_aveugle))

        def build_temoin_branche(instance: object = None) -> dict:
            return {}

        self.assertTrue(_a_un_canal_de_donnees(build_temoin_branche))

    def test_AUCUN_ECRAN_AVEUGLE_AUJOURD_HUI_ET_C_EST_UN_FAIT_DATE(self):
        """Ce que la mesure rend aujourd'hui, ecrit pour qu'un retour se voie.

        Huit au 2026-09-08, zero au 2026-09-09 apres `4140931`. Si un ecran
        aveugle reapparait, ce test rougit **et les deux suivants prennent le
        relais** en exigeant sa declaration: la garde n'est pas desarmee, elle
        attend.
        """
        self.assertEqual(
            [], [(m.__name__, n) for m, n, _ in self.aveugles],
            "un ecran sans aucun canal d'entree est reapparu: il doit declarer "
            "sa nature, et les tests suivants le verifient",
        )

    def test_chaque_ecran_aveugle_porte_une_nature_declaree(self):
        for module, nom, fonction in self.aveugles:
            with self.subTest(vue=nom):
                modele = fonction()
                self.assertIsInstance(modele, dict, "%s ne rend pas un modele" % nom)
                mention = str(modele.get("notice") or "").strip()
                self.assertTrue(
                    mention,
                    "%s (%s) n'a aucun canal d'entree, donc il ne peut lire aucune donnee, "
                    "et il ne declare pas sa nature. Ajoute une cle `notice` disant ce que cet "
                    "ecran montre reellement. Le mot employe est libre." % (nom, module.__name__),
                )

    def test_la_nature_declaree_atteint_l_ecran(self):
        """Une mention presente dans un dictionnaire et absente du gabarit ne dit rien.

        C'est exactement le defaut corrige le matin meme sur le panneau coffre:
        la page avait la verite sous la main et affichait autre chose.
        """
        for module, nom, fonction in self.aveugles:
            with self.subTest(vue=nom):
                source = Path(inspect.getfile(module)).read_text(encoding="utf-8")
                gabarits = re.findall(r'name="([a-z0-9_]+\.html)"', source)
                self.assertTrue(gabarits, "%s ne nomme aucun gabarit" % nom)
                rendus = []
                for fichier in gabarits:
                    chemin = GABARITS / fichier
                    if chemin.exists() and "notice" in chemin.read_text(encoding="utf-8"):
                        rendus.append(fichier)
                self.assertTrue(
                    rendus,
                    "%s declare sa nature mais aucun de ses gabarits (%s) ne la rend: "
                    "la mention n'atteint pas l'ecran" % (nom, ", ".join(gabarits)),
                )


if __name__ == "__main__":
    unittest.main()
