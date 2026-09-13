# -*- coding: utf-8 -*-
"""Une contradiction de l'instrument ne sort pas par le canal des constats.

Demande de Brice, revue du 2026-09-07 a 12:08, mot pour mot:
« ce n'est pas possible. Ou alors vraiment sous forme de message d'erreur, que
l'instance est cassee, il faut la refaire. »

Avant: le desaccord METIER entre deux sources - qui est une information sur la
copropriete - et l'incoherence TECHNIQUE entre deux vues du meme calcul - qui
est un defaut du logiciel - sortaient par le MEME bandeau de provenance, l'un
colorant simplement l'autre en rouge. Le lecteur ne pouvait pas savoir ce qu'il
regardait.
"""
from __future__ import annotations

import unittest

from coproscope.web._controle_gouvernance_panne import NATURES_PANNE, panne_instrument


class CanalDePanneInstrument(unittest.TestCase):
    def test_rien_a_signaler_quand_les_deux_vues_s_accordent(self):
        self.assertIsNone(panne_instrument(12, 12))

    def test_rien_a_signaler_quand_la_synthese_n_a_annonce_aucun_nombre(self):
        """Arriver sans `n` dans l'adresse n'est pas une contradiction."""
        self.assertIsNone(panne_instrument(None, 12))

    def test_la_contradiction_nomme_les_deux_nombres_qui_la_fondent(self):
        p = panne_instrument(12, 9)
        self.assertIsNotNone(p)
        self.assertEqual("comptes_contradictoires", p["nature"])
        self.assertEqual((12, 9), (p["attendu"], p["trouve"]))
        self.assertIn("12", p["explication"])
        self.assertIn("9", p["explication"])
        self.assertIn("refaire" if "refaire" in p["consigne"] else "Reconstruisez", p["consigne"])

    def test_la_seule_autre_cause_possible_est_dite_et_non_tue(self):
        """Residu nomme, et rendu executable.

        L'ecran ne sait pas distinguer une instance incoherente d'un lien ancien
        portant un nombre perime. Affirmer la premiere sans dire la seconde
        serait une fausse alerte - donc exactement le defaut que ce canal
        corrige, retourne contre l'utilisateur.
        """
        p = panne_instrument(12, 9)
        self.assertIn("signet", p["reserve"].lower() + p["reserve"])
        self.assertTrue(p["reserve"].strip(), "la reserve ne doit jamais etre vide")

    def test_une_nature_inconnue_se_degrade_en_disant_qu_elle_ne_sait_pas(self):
        """Le repli est JOIGNABLE, et c'est la raison d'etre du parametre.

        La premiere version figeait la nature en constante interne: la branche
        du bas ne pouvait jamais s'executer. Une garde qu'aucune entree ne peut
        declencher n'est pas une garde.
        """
        self.assertNotIn("contradiction_encore_inconnue", NATURES_PANNE)
        p = panne_instrument(12, 9, nature="contradiction_encore_inconnue")
        self.assertIsNotNone(p)
        self.assertIn("ne sait pas decrire", p["explication"])
        self.assertTrue(p["consigne"].strip())
        self.assertTrue(p["reserve"].strip())

    def test_toute_nature_declaree_porte_les_trois_champs_que_le_gabarit_rend(self):
        """Conservation: le gabarit rend titre, explication et consigne.

        Une nature ajoutee plus tard sans l'un des trois laisserait un bloc
        d'alerte troue, et le trou serait silencieux a l'ecran.
        """
        for nom, modele in NATURES_PANNE.items():
            with self.subTest(nature=nom):
                for champ in ("titre", "explication", "consigne"):
                    self.assertTrue(modele.get(champ, "").strip(),
                                    "la nature %r n'a pas de %s" % (nom, champ))


if __name__ == "__main__":
    unittest.main()
