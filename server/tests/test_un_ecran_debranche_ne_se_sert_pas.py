# -*- coding: utf-8 -*-
"""Un ecran debranche ne se sert pas, et il revient quand on le rebranche.

`RM-2026-0183`. Voir `coproscope/web/debranchement.py`. La mesure porte sur les
routes REELLEMENT enregistrees par `create_app`, jamais sur la liste de cles:
une cle qui n'eteint plus rien, ou une route qui echappe a son interrupteur, se
voit ici.
"""
from __future__ import annotations

import unittest

from coproscope.web.debranchement import CHEMINS_DEBRANCHES, DEBRANCHES, rebranchements, sous
from tests._exemple_copie import exemple_copie


def _routes(app) -> set[tuple[str, str]]:
    return {(route.path, methode) for route in app.routes for methode in (getattr(route, "methods", None) or ())}


class UN_ECRAN_DEBRANCHE_NE_SE_SERT_PAS(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from coproscope.web.app import create_app

        with exemple_copie("debranche") as instance:
            cls.defaut = _routes(create_app(instance, 2025))
            cls.tout = _routes(create_app(instance, 2025, rebrancher=frozenset(DEBRANCHES)))
            cls.par_cle = {
                cle: _routes(create_app(instance, 2025, rebrancher=frozenset({cle}))) - cls.defaut
                for cle in DEBRANCHES
            }

    def test_chaque_cle_eteint_au_moins_une_route(self) -> None:
        muettes = sorted(cle for cle, ajout in self.par_cle.items() if not ajout)
        self.assertEqual([], muettes, "ces cles ne rebranchent rien: l'interrupteur ne commande plus aucune route")

    def test_les_cles_couvrent_exactement_ce_qui_est_eteint(self) -> None:
        union = set().union(*self.par_cle.values())
        self.assertEqual(self.tout - self.defaut, union)

    def test_chaque_cle_nomme_son_item_et_ses_chemins(self) -> None:
        self.assertEqual(set(DEBRANCHES), set(CHEMINS_DEBRANCHES))
        for cle, rm in DEBRANCHES.items():
            with self.subTest(cle=cle):
                self.assertRegex(rm, r"^RM-\d{4}-\d{4}$")
                chemins_get = {chemin for chemin, methode in self.par_cle[cle] if methode == "GET"}
                for chemin in chemins_get:
                    self.assertIsNotNone(
                        sous(chemin, CHEMINS_DEBRANCHES[cle]),
                        "la route GET %s est eteinte par `%s` mais aucun de ses chemins declares ne la couvre: "
                        "un lien vers elle ne serait pas neutralise" % (chemin, cle))

    def test_une_cle_inconnue_est_refusee(self) -> None:
        with self.assertRaises(ValueError):
            rebranchements({"ajouter_documents"})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
