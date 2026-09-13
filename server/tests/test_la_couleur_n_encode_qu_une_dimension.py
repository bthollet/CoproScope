# -*- coding: utf-8 -*-
"""Sur une bulle, une seule dimension a le droit d'etre portee par la couleur.

`RM-2026-0118`, premiere demande: *verifier d'abord que la couleur n'encode
qu'UNE dimension: une couleur qui porte la gravite ET l'avancement est
illisible par construction*. Sa colonne preuve disait `a produire`.

**MESURE DU 2026-09-12**, sur les regles de `.cs-bulle` du mur de controle:

| dimension portee par | regles de couleur | regles de forme |
|---|---:|---:|
| `is-{statut}` - la force de la PIECE | 4 | 1 |
| `data-franchissement` - le resultat de la COMPARAISON | **0** | 2 |

**La propriete tient** - la couleur n'a qu'un occupant - et `RM-2026-0143` a
voulu poser le marqueur de franchissement **en forme**, precisement parce que
la doctrine du depot interdit qu'un statut repose sur la seule couleur.

**CE PARAGRAPHE AFFIRMAIT *un bord epaissi pour `franchi`*, ET C'ETAIT FAUX.**
Calcul de la cascade du 2026-09-12: la regle `franchi` pose
`border-left-width: 4px`, la largeur que le socle `.cs-bulle` donne deja. Elle
n'a aucun effet: une bulle franchie, non franchie ou sans comparaison sont
rendues identiques. Ce fichier ne pouvait pas le voir, pour deux raisons que
sa lecture confirme: il decouvre les valeurs de franchissement dans la FEUILLE
- donc `non_franchi`, sans regle, n'est jamais examine - et il compte la
PRESENCE d'une declaration de forme, pas sa difference avec le socle. La
propriete *deux etats ne se rendent pas pareil* est mesuree par effet dans
`test_deux_etats_de_franchissement_se_voient.py`, ou le defaut est en dette
nommee.

**L'AXE.** Ce qui VARIE: le nombre de dimensions qu'une bulle doit montrer, et
leurs noms - la force de la piece, le franchissement, et ce qu'un ecran futur
voudra ajouter. Ce qui reste INVARIANT: **la couleur n'a qu'un canal, donc une
seule dimension peut l'occuper**; toute dimension supplementaire s'exprime par
la forme - bord, epaisseur, tirets, graisse. **Hors des valeurs observees:** une
dimension nouvelle, sous un attribut que personne n'a prevu, tombe sous la
meme regle le jour ou elle recoit sa premiere couleur.

**CE QUE CE TEST NE FAIT PAS.** Il ne juge pas si la dimension qui occupe la
couleur est la BONNE - c'est la grille de Brice, et elle n'est pas dans l'item.
Il ne traite pas non plus la variation inexpliquee du nombre de bulles, qui
demande des pages rendues. Ces deux moities restent le residu de l'item.
"""
from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "coproscope_tests_media_css_dimensions",
    Path(__file__).resolve().with_name("_media_css.py"))
_MEDIA = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MEDIA)

#: Ce qui peint. `fill` est inclus parce qu'une bulle peut porter une icone.
COULEUR = re.compile(
    r"(?:^|;)\s*(?:color|background|background-color|border-color|"
    r"border-left-color|border-top-color|border-right-color|"
    r"border-bottom-color|fill)\s*:", re.I)

#: Ce qui se voit en monochrome et a l'impression.
FORME = re.compile(
    r"(?:^|;)\s*(?:border-style|border-width|border-left-width|"
    r"text-decoration|font-weight|font-style|outline-style|opacity|content)\s*:",
    re.I)

#: L'element du mur de controle. Le test porte sur lui et pas sur toute la
#: feuille: la question de l'item est celle d'UNE bulle qui doit montrer
#: plusieurs choses a la fois.
BULLE = ".cs-bulle"


def _dimension(selecteur: str) -> str:
    """Quelle dimension ce selecteur qualifie-t-il ?"""
    if re.search(r"\.is-[a-z0-9_]+", selecteur):
        return "force de la piece"
    if "data-franchissement" in selecteur:
        return "resultat de la comparaison"
    return "socle"


def _compte() -> dict[str, dict[str, int]]:
    css = _MEDIA.feuilles()
    trouve: dict[str, dict[str, int]] = {}
    for selecteur, corps in _MEDIA.regles(css, 1440):
        if BULLE not in selecteur:
            continue
        cle = _dimension(selecteur)
        compte = trouve.setdefault(cle, {"couleur": 0, "forme": 0})
        if COULEUR.search(corps):
            compte["couleur"] += 1
        if FORME.search(corps):
            compte["forme"] += 1
    return trouve


class UNE_SEULE_DIMENSION_OCCUPE_LA_COULEUR(unittest.TestCase):
    def test_l_instrument_trouve_bien_les_regles_de_la_bulle(self) -> None:
        """Sans regles lues, le test suivant passerait a vide."""
        compte = _compte()
        self.assertIn("force de la piece", compte)
        self.assertIn("resultat de la comparaison", compte)
        self.assertGreater(
            sum(c["couleur"] + c["forme"] for c in compte.values()), 5,
            "presque aucune regle de bulle lue: l'instrument est casse")

    def test_au_plus_UNE_dimension_qualifiante_peint(self) -> None:
        """Le coeur de l'item: la couleur n'a qu'un canal.

        Le socle - `.cs-bulle` nu - a le droit de peindre: il ne qualifie rien,
        il pose le fond commun. Ce sont les dimensions QUALIFIANTES qui se
        disputent le canal.
        """
        peignent = sorted(
            dimension for dimension, compte in _compte().items()
            if dimension != "socle" and compte["couleur"] > 0)
        self.assertLessEqual(
            len(peignent), 1,
            "deux dimensions se partagent la couleur d'une meme bulle: elle "
            "devient illisible par construction, parce qu'un lecteur ne peut "
            "pas savoir laquelle des deux il regarde. Dimensions qui "
            "peignent: %s" % peignent)

    def test_chaque_VALEUR_qui_ne_peint_pas_se_voit_quand_meme(self) -> None:
        """Sinon elle serait invisible, ce qui est le defaut symetrique.

        **La verification porte sur chaque VALEUR, pas sur la dimension**, et
        la campagne de mutation a montre pourquoi: avec deux valeurs
        - `franchi` et `non_comparable` - retirer le marqueur de l'une laissait
        l'autre le porter, et une garde comptant par dimension n'y voyait rien.
        Une valeur sans marqueur est un etat que le lecteur ne peut pas
        distinguer, meme si son voisin se voit.
        """
        css = _MEDIA.feuilles()
        valeurs: dict[str, int] = {}
        for selecteur, corps in _MEDIA.regles(css, 1440):
            if BULLE not in selecteur:
                continue
            for valeur in re.findall(r'data-franchissement="([a-z_]+)"', selecteur):
                valeurs.setdefault(valeur, 0)
                if COULEUR.search(corps) or FORME.search(corps):
                    valeurs[valeur] += 1
        self.assertTrue(valeurs, "aucune valeur de franchissement stylee")
        muettes = sorted(valeur for valeur, marques in valeurs.items() if not marques)
        self.assertEqual(
            [], muettes,
            "ces etats ne prennent ni couleur ni forme: le lecteur ne peut pas "
            "les distinguer. %s" % muettes)

    def test_le_franchissement_passe_par_la_FORME(self) -> None:
        """Conservation de ce que `RM-2026-0143` a pose, nomme ici.

        Si un lot futur donnait une couleur au franchissement, le test
        ci-dessus mordrait - mais ce test-ci dit POURQUOI la forme a ete
        choisie, pour qu'on ne la retire pas en croyant simplifier.
        """
        compte = _compte()["resultat de la comparaison"]
        self.assertEqual(0, compte["couleur"])
        self.assertGreater(compte["forme"], 0)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
