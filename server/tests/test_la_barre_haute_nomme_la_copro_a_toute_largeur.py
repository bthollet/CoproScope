# -*- coding: utf-8 -*-
"""A toute largeur, l'ecran dit quelle copropriete et quel exercice on regarde.

`RM-2026-0111`. Le correctif est en place - le sceptique du triage l'avait
verifie sans faire confiance au resume - mais le constat demandait autre chose:
**rendre la regle mesurable par un test qui evalue vraiment une requete de
media**.

**LE TROU QUE L'ITEM NOMMAIT.** La suite ne contient **aucun moteur de
rendu** - zero occurrence de `playwright`, `selenium`, `puppeteer` ou
`viewport` sous `server/tests/` - donc **aucune requete de media n'etait
evaluee par aucun test**. La seule garde responsive lisait le fichier et
verifiait qu'une chaine `display: none;` existe *quelque part* dans un bloc:
jamais **ce qui** est cache, jamais **a quelle largeur**. C'est le mode de
defaillance de `RM-2026-0106`, loge dans une garde.

**L'AXE.** Ce qui VARIE: la largeur disponible - une fenetre portant une barre
laterale d'assistant passe sous 1281 px sans que l'utilisateur fasse quoi que
ce soit. Ce qui reste INVARIANT: **l'utilisateur sait toujours quelle copro et
quel exercice il regarde**, et il peut toujours atteindre le mode test, qui est
le canal de recueil prevu par le protocole d'equipe agile.

**CE QUE CE TEST N'EST PAS.** L'evaluateur de `_media_css.py` n'est pas un
navigateur: il compare les selecteurs textuellement, n'applique aucune regle de
specificite et ne connait pas l'heritage - un parent cache rendrait l'enfant
invisible sans qu'il le voie. Il repond a une question etroite et verifiable:
**cette regle precise cache-t-elle cet element a cette largeur ?** Il ne
remplace donc pas une recette sur page reelle, et le dire fait partie du
livrable.

**MESURE DU 2026-09-12**, huit largeurs de 420 a 1440 px: `.cs-topbar-identity`
vaut `flex` partout, `.cs-topbar .instance-meta` ne porte aucun `display`, et
`.instance-switch-link` - qui porte le bouton `Mode test` et le lien de choix
de copro - vaut `inline-flex` partout. **Le zero est un vrai zero:** le meme
instrument trouve **23 selecteurs caches en etroit et pas en large**, donc il
evalue bien les requetes de media.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "coproscope_tests_media_css",
    Path(__file__).resolve().with_name("_media_css.py"))
_MEDIA = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MEDIA)

#: Les largeurs mesurees le 2026-09-07 dans un vrai navigateur, reprises ici.
#: Ce ne sont pas des modalites choisies: 1440 est au-dessus du seuil, 1280 est
#: le seuil exact, et les six autres descendent jusqu'au telephone.
LARGEURS = (420, 760, 900, 1024, 1120, 1200, 1280, 1440)

#: Ce que la barre haute doit porter a toute largeur. Chaque entree nomme ce
#: que l'utilisateur perd si la regle tombe.
PORTEURS = {
    ".cs-topbar-identity": "le nom de la copropriete et l'exercice regardes",
    ".instance-switch-link": "le bouton `Mode test` et le lien de choix de copro",
    ".cs-topbar .instance-meta": "le bloc qui portait l'identite avant qu'elle "
                                 "en soit sortie",
}


class L_IDENTITE_SURVIT_A_TOUTE_LARGEUR(unittest.TestCase):
    def setUp(self) -> None:
        self.css = _MEDIA.feuilles()

    def test_rien_de_ce_qui_nomme_la_copro_n_est_cache(self) -> None:
        caches = [
            (selecteur, largeur, ce_qui_se_perd)
            for selecteur, ce_qui_se_perd in PORTEURS.items()
            for largeur in LARGEURS
            if _MEDIA.est_cache(self.css, selecteur, largeur)
        ]
        self.assertEqual(
            [], caches,
            "a cette largeur, l'ecran cesse de porter %s. Le seuil n'est pas "
            "exotique: une fenetre avec une barre laterale d'assistant y passe "
            "sans que l'utilisateur fasse quoi que ce soit. Caches: %s"
            % ("ce qui suit", caches))

    def test_le_seuil_de_1280_ne_cache_plus_l_identite(self) -> None:
        """La regle exacte que l'item nommait, a la largeur exacte.

        `@media (max-width: 1280px) { .cs-topbar .instance-meta {
        display: none } }` faisait disparaitre, sous 1281 px, le nom de la
        copro, l'exercice, le choix de copro et le mode test.
        """
        for largeur in (1280, 1279, 900):
            with self.subTest(largeur=largeur):
                self.assertNotEqual(
                    "none",
                    _MEDIA.propriete(self.css, ".cs-topbar .instance-meta",
                                     "display", largeur))


class L_EVALUATEUR_APPLIQUE_VRAIMENT_LES_MEDIA(unittest.TestCase):
    """Garde de l'instrument: sans elle, le test ci-dessus passerait a vide.

    Un evaluateur qui ne verrait aucune requete de media declarerait tout
    visible - et son zero se lirait comme une bonne nouvelle. C'est la
    quatrieme forme de la serie A de `RM-2026-0172`.
    """

    def setUp(self) -> None:
        self.css = _MEDIA.feuilles()

    def test_il_lit_bien_les_feuilles(self) -> None:
        self.assertGreater(len(self.css), 100000)

    def test_il_trouve_des_elements_caches_SEULEMENT_en_etroit(self) -> None:
        import re

        def caches(largeur: int) -> set[str]:
            return {selecteur
                    for selecteur, corps in _MEDIA.regles(self.css, largeur)
                    if re.search(r"display\s*:\s*none", corps)}

        propres_a_l_etroit = caches(420) - caches(1440)
        self.assertGreater(
            len(propres_a_l_etroit), 10,
            "l'evaluateur ne distingue pas les largeurs: il n'applique pas les "
            "requetes de media, et tout test qui s'appuie dessus est vide")

    def test_une_regle_hors_media_vaut_a_toute_largeur(self) -> None:
        """Temoin de conservation: le socle ne depend pas de la largeur."""
        valeurs = {_MEDIA.propriete(self.css, ".cs-topbar-identity", "display", l)
                   for l in LARGEURS}
        self.assertEqual({"flex"}, valeurs)

    def test_les_limites_de_l_evaluateur_sont_ECRITES(self) -> None:
        """Une garantie se decrit avec ce qu'elle laisse expose."""
        source = Path(_MEDIA.__file__).read_text(encoding="utf-8")
        for limite in ("specificite", "heritage", "textuellement"):
            with self.subTest(limite=limite):
                self.assertIn(limite, source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
