# -*- coding: utf-8 -*-
"""Les garanties du LECTEUR de style, eprouvees sur lui et non sur le produit.

`test_ui_identite_barre_haute.py` demande *aucune regle ne supprime l'identite*.
Il ne peut repondre juste que si son lecteur repond juste. Ce fichier-ci garde
le lecteur, parce qu'un lecteur faux rend un vert qui a l'air d'une preuve.

**Ce qui a rendu ce fichier necessaire, mesure le 2026-09-09 sur `177945d`.**
La garde livree ce jour-la annoncait dans son en-tete: *elle peut donc echouer a
tort, jamais reussir a tort*, et onze reintroductions du defaut avaient ete
eprouvees - les onze mordaient. Elle reussissait pourtant a tort. Le defaut
exact de `RM-2026-0111` - `@media (max-width: 1280px) { ...
.cs-topbar-identity { display: none } }` - remis dans la feuille sous un
selecteur a pseudo-classe IMBRIQUEE laissait la suite VERTE, dix tests sur dix.
La regle etait lue, sa declaration etait correctement classee comme supprimante,
et c'est le RATTACHEMENT qui rendait `None`: *cette regle ne vise pas la
chaine*. Une reponse fausse, rendue en silence, sur une forme de selecteur que
le depot emploie deja - a cet endroit meme, sur un ancetre de l'identite:
`.cs-topbar:not(:has(.cs-search))`, dans `styles_part_30.css`.

**L'axe, parce que la reparation ne doit pas etre `:not(:has())`.** Un lecteur
partiel a deux facons de se tromper, et elles ne se valent pas. Sur-attraper
fait rougir la garde sur une regle inoffensive: cela se voit, se lit et se
discute. Sous-attraper fait taire la garde sur une regle nuisible: cela ne se
voit jamais. **Ce qu'on ne sait pas lire doit donc etre retenu, pas ecarte** -
et cela vaut de toute forme inconnue, pas seulement de celles qu'on vient de
rencontrer.

Ce que ce fichier NE prouve pas: rien ici ne rend une page. Que l'identite soit
LISIBLE, non recouverte et dans le premier viewport demande un moteur de rendu,
qu'aucun test de ce depot ne possede.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


def _charge(nom: str, fichier: str):
    """Charge par CHEMIN: ce depot joue ses tests a plat et en paquet."""
    specification = importlib.util.spec_from_file_location(
        nom, Path(__file__).resolve().with_name(fichier))
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


lecture = _charge("coproscope_lecteur_style_garde", "_lecture_style_coque.py")
garde = _charge("coproscope_garde_identite", "test_ui_identite_barre_haute.py")

#: Le compose teste est le dernier maillon; les ancetres n'importent pas ici.
CHAINE_JOUET = [
    ("html", frozenset(), None, frozenset()),
    ("body", frozenset({"cs-shell"}), None, frozenset({"class"})),
    ("header", frozenset({"cs-topbar"}), None, frozenset({"class"})),
    ("div", frozenset({"cs-topbar-identity"}), None, frozenset({"class"})),
]


class LesPseudoClassesImbriqueesSontLuesTests(unittest.TestCase):
    """Le defaut precis qui a laisse repasser `RM-2026-0111`."""

    def test_l_aplatissement_descend_a_toute_profondeur(self) -> None:
        cas = {
            ".a:not(.b)": ".a:not()",
            ".cs-topbar:not(:has(.cs-search))": ".cs-topbar:not()",
            ".z:where(:not(.q))": ".z:where()",
            "a:is(.x, .y):not(:has(> b))": "a:is():not()",
            ".p:has(:is(:not(.deep)))": ".p:has()",
        }
        for entree, attendu in cas.items():
            self.assertEqual(
                lecture._aplatit_fonctions(entree), attendu,
                "\n\n  `%s` mal aplati. L'ancienne version substituait la\n"
                "  parenthese la plus INTERNE, en boucle, et laissait\n"
                "  `:not(:has())` - une forme que le lecteur ne sait pas lire.\n"
                % entree)

    def test_la_forme_deja_presente_dans_le_depot_vise_bien_la_chaine(self) -> None:
        """`styles_part_30.css` ecrit deja cela sur un ancetre de l'identite."""
        for selecteur in (".cs-topbar:not(:has(.cs-search))",
                          ".cs-topbar:not(:has(.cs-search)) .cs-topbar-identity",
                          ".cs-topbar-identity:where(:not(.x))"):
            self.assertIsNotNone(
                lecture._vise(selecteur, CHAINE_JOUET),
                "\n\n  `%s` ne retombe pas sur la chaine d'identite.\n"
                "  Une regle ecrite sous cette forme masquerait l'identite\n"
                "  sans faire rougir la garde: c'est le trou du 2026-09-09.\n"
                % selecteur)


class CeQuOnNeSaitPasLireEstRetenuTests(unittest.TestCase):
    """Sur-attraper se voit; sous-attraper ne se voit jamais."""

    def test_un_compose_illisible_est_retenu_et_nomme(self) -> None:
        avant = set(lecture.ILLISIBLES)
        illisible = ".cs-topbar-identity%%syntaxe-de-demain%%"
        self.assertTrue(
            lecture._compose_matche(illisible, CHAINE_JOUET[-1]),
            "\n\n  Un compose que le lecteur ne sait pas analyser a ete ECARTE.\n"
            "  Le lecteur repond alors *cette regle ne vise pas la chaine*\n"
            "  pour une regle qu'il n'a pas lue - une reponse fausse rendue\n"
            "  en silence. Il doit repondre *peut-etre*, donc `True`.\n")
        self.assertIn(
            illisible, lecture.ILLISIBLES - avant,
            "le compose retenu faute d'etre lu doit aussi etre NOMME")

    def test_le_lecteur_comprend_tout_le_css_reellement_servi(self) -> None:
        """Plancher anti-mutisme, pris dans l'autre sens.

        La voie de l'aveu doit rester une voie de secours, pas le regime
        courant. Zero ici veut dire *le lecteur lit tout ce que le produit
        ecrit* - ce qui n'est vrai que depuis l'aplatissement - et non *le
        compteur ne bouge jamais*: le test au-dessus prouve qu'il bouge.
        """
        lecture.ILLISIBLES.clear()
        garde._infractions()
        self.assertEqual(
            sorted(lecture.ILLISIBLES), [],
            "\n\n  Le lecteur ne sait plus analyser ces composes du produit.\n"
            "  Ils sont retenus par securite, donc la garde peut rougir a\n"
            "  tort: etendez `COMPOSE` au lieu de subir le bruit.\n")


class ToutCeQuiEstServiEstLuTests(unittest.TestCase):
    def test_le_manifeste_est_lui_meme_une_feuille_lue(self) -> None:
        feuilles, scripts = lecture._feuilles_a_lire()
        self.assertIn(
            lecture.MANIFESTE, feuilles,
            "\n\n  `styles.css` est servi au navigateur: une regle ecrite sous\n"
            "  ses `@import` s'applique a la page. La garde doit la lire.\n")
        # Plancher a la mesure du 2026-09-13: 27 feuilles, apres le retrait de 8
        # feuilles d'ecrans supprimes (`RM-2026-0183`).
        self.assertGreaterEqual(len(feuilles), 27)
        self.assertGreaterEqual(len(scripts), 1)

    def test_le_gabarit_est_juge_autant_que_les_feuilles(self) -> None:
        """`style=` et `hidden` cachent l'identite sans qu'une feuille bouge."""
        noeud = CHAINE_JOUET[-1]
        self.assertEqual(garde._fautes_du_gabarit([noeud], [{"class": "x"}]), [])
        self.assertTrue(
            garde._fautes_du_gabarit([noeud], [{"hidden": ""}]),
            "l'attribut HTML `hidden` vaut `display: none`")
        self.assertTrue(
            garde._fautes_du_gabarit([noeud], [{"style": "display: none"}]),
            "un `style=` pose sur la chaine echappait entierement a la garde")
        self.assertEqual(
            garde._fautes_du_gabarit([noeud], [{"style": "color: #475467"}]), [],
            "un `style=` inoffensif ne doit pas rougir")


class ChaqueIdentiteMarqueeEstProtegeeTests(unittest.TestCase):
    """Ne garder que la chaine la plus longue etait une modalite."""

    GABARIT_JOUET = (
        '<html><body class="cs-shell">'
        '<header class="cs-topbar"><div class="cs-topbar-identity">'
        '<span data-cs-identite="copropriete">Coffre</span>'
        '</div></header>'
        '<div class="cs-ailleurs">'
        '<span data-cs-identite="exercice">Exercice</span>'
        '</div></body></html>')

    def test_deux_sous_arbres_marques_donnent_deux_chaines(self) -> None:
        arbre = garde._Arbre()
        arbre.feed(self.GABARIT_JOUET)
        chaines = garde._chaines(arbre.trouves)
        self.assertEqual(
            len(chaines), 2,
            "\n\n  Un role d'identite pose hors du sous-arbre principal n'est\n"
            "  plus protege: seule la chaine la plus longue etait jugee, et\n"
            "  une regle masquant l'autre passait en silence.\n"
            "  chaines vues: %s\n"
            % [[n[0] for n in c] for c, _ in chaines])

    def test_le_produit_declare_au_moins_une_chaine(self) -> None:
        self.assertGreaterEqual(len(garde._chaines(garde._identites())), 1)


class LeVerdictEstBRANCHESurCesLecturesTests(unittest.TestCase):
    """Une unite juste que le verdict n'appelle pas ne garde rien.

    Ecrit apres une erreur commise ici meme le 2026-09-09: `_fautes_du_gabarit`
    et `_chaines` etaient eprouvees separement, et les deux passaient encore
    quand on debranchait leur appel dans `_infractions`. C'est la meme forme de
    faux vert que celle qu'on reproche a la garde d'origine - un morceau
    correct, jamais interroge. Ce test attaque donc `_infractions` lui-meme.
    """

    #: Une SECONDE chaine, plus courte, dont le noeud porte `hidden`. Elle
    #: n'est vue que si le verdict juge toutes les chaines ET regarde le
    #: gabarit. Debrancher l'une ou l'autre lecture rend ce test vert a tort,
    #: donc rouge ici.
    def _trouves_fabriques(self):
        longue = [("html", frozenset(), None, frozenset()),
                  ("body", frozenset({"cs-shell"}), None, frozenset({"class"})),
                  ("div", frozenset({"cs-app-shell"}), None, frozenset({"class"})),
                  ("div", frozenset({"cs-workspace"}), None, frozenset({"class"})),
                  ("header", frozenset({"cs-topbar"}), None, frozenset({"class"})),
                  ("span", frozenset(), None, frozenset({"data-cs-identite"}))]
        courte = [("html", frozenset(), None, frozenset()),
                  ("span", frozenset({"cs-ailleurs"}), None,
                   frozenset({"class", "hidden", "data-cs-identite"}))]
        return [(longue, [{}] * len(longue), "copropriete", 1),
                (courte, [{}, {"hidden": "", "class": "cs-ailleurs"}],
                 "exercice", 2)]

    def test_une_identite_cachee_hors_de_la_chaine_principale_est_vue(self) -> None:
        origine = garde._identites
        garde._identites = self._trouves_fabriques
        try:
            fautes, _, _, _, _ = garde._infractions()
        finally:
            garde._identites = origine
        self.assertTrue(
            any("hidden" in f for f in fautes),
            "\n\n  `_infractions` n'a pas signale une identite marquee `hidden`\n"
            "  posee dans un second sous-arbre. Soit il ne juge que la chaine\n"
            "  la plus longue, soit il ne lit pas les attributs du gabarit.\n"
            "  Les deux lectures peuvent etre justes SEPAREMENT et n'etre\n"
            "  jamais appelees: c'est ce test qui prouve le branchement.\n"
            "  fautes rendues: %s\n" % (fautes,))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
