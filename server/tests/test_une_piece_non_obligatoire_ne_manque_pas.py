# -*- coding: utf-8 -*-
"""Une piece qu'aucun texte n'impose ne se lit pas comme une piece qui manque.

`RM-2026-0164`, point (2), demande de Brice: *« devis associes » plutot que
« devis retenu », ou mieux « presence du devis, oui ou non », puisque le devis,
il n'est pas obligatoire*. Et la consequence de surete qu'il en tire lui-meme:
**une absence de devis n'est PAS un manquement** et ne doit pas etre presentee
parmi les pieces a reclamer.

**Deux mots portaient tout le defaut.** `retenu` presuppose qu'un choix a eu
lieu entre plusieurs devis - le lot precedent avait compte `89 faux positifs`
sur cette base - et `Aucun devis rattache`, sec, se lit comme le constat d'une
piece qui manque.

**Mesure du 2026-09-11, instance VIDE reabsorbant 858 pieces sources, sur la
matrice de gouvernance reelle (550 actes):** `cel_devis` vaut `ABSENT` sur
**206 actes**, `AFFIRME_SANS_PIECE` sur 149 et `NON_APPLICABLE` sur 195. Deux
cent six lignes annoncaient donc un vide sous un mot qui promettait un choix.

**L'AXE, et c'est celui de toute cette colonne.** Ce qui VARIE d'une
copropriete a l'autre: le nombre de devis produits - zero, un, quatre -, la
maniere dont la resolution les met en jeu, le fait qu'un vote porte sur chaque
devis ou sur l'ensemble. Ce qui reste INVARIANT: **aucun texte n'impose de
devis**, donc un controle de presence de devis ne peut pas rendre son absence
comme un manquement.

**Ce que ce lot ne fait PAS.** Il ne touche pas au point (1) de l'item -
l'architecture resolution/devis, *ne pas coder « 13.4 signifie quatre devis »* -
qui reste ouvert et demande une enquete. Il traite la formulation, qui etait
nommee separement et qui se mesure.
"""

from __future__ import annotations

import unittest

from coproscope.web import _controle_gouvernance_cellules as C


class LE_NOM_NE_PRESUPPOSE_PLUS_UN_CHOIX(unittest.TestCase):
    """`retenu` promet un arbitrage entre plusieurs devis."""

    def test_le_libelle_ne_dit_plus_retenu(self) -> None:
        self.assertNotIn("retenu", C._L_DEVIS["nom"].lower())

    def test_il_dit_l_ASSOCIATION_et_non_l_election(self) -> None:
        """Le mot de Brice: *devis associes*."""
        self.assertIn("associé", C._L_DEVIS["nom"].lower())

    def test_la_phrase_de_presence_ne_dit_plus_retenu_non_plus(self) -> None:
        """Corriger le titre en laissant le corps l'affirmer ne corrige rien."""
        self.assertNotIn("retenu", C._L_DEVIS["disponible"].lower())


class UNE_ABSENCE_NON_EXIGEE_SE_DIT_COMME_TELLE(unittest.TestCase):
    """**Le coeur de la demande, et c'est une consequence de surete.**"""

    def test_l_absence_declare_que_le_devis_n_est_pas_obligatoire(self) -> None:
        phrase = C._L_DEVIS["manquante"].lower()
        self.assertIn("n'est pas obligatoire", phrase)

    def test_elle_dit_explicitement_que_ce_n_est_pas_un_manquement(self) -> None:
        """Sans cela, le lecteur range la ligne avec les pieces a reclamer -
        exactement ce que Brice demande d'eviter."""
        self.assertIn("n'est pas un manquement", C._L_DEVIS["manquante"].lower())

    def test_elle_reste_une_phrase_ET_NON_un_vide(self) -> None:
        """Retirer la phrase reglerait le probleme en supprimant l'information.
        Une cellule muette ne dit pas *rien n'est exige*, elle ne dit rien."""
        self.assertTrue(C._L_DEVIS["manquante"].strip())


class LES_AUTRES_LIBELLES_NE_SONT_PAS_TOUCHES(unittest.TestCase):
    """**Le temoin, et il compte.** Les autres controles portent, eux, sur des
    pieces que le droit exige: leur absence EST une nouvelle, et ce lot ne
    devait pas l'adoucir au passage.
    """

    def test_l_avis_du_conseil_syndical_reste_un_constat_ferme(self) -> None:
        phrase = C._L_AVIS["manquante"].lower()
        self.assertNotIn("n'est pas obligatoire", phrase)
        self.assertIn("article 21", phrase)

    def test_l_annexe_appelee_par_la_resolution_reste_un_constat_ferme(self) -> None:
        self.assertNotIn("n'est pas obligatoire", C._L_ANNEXE["manquante"].lower())

    def test_un_seul_libelle_du_module_declare_une_non_obligation(self) -> None:
        """Si un second apparaissait sans mesure, ce serait une pente."""
        jeux = [v for k, v in vars(C).items()
                if k.startswith("_L_") and isinstance(v, dict) and "manquante" in v]
        declarent = [j for j in jeux
                     if "n'est pas obligatoire" in j["manquante"].lower()]
        self.assertEqual(
            1, len(declarent),
            "plusieurs libelles declarent une non-obligation: chacune doit "
            "etre fondee sur un texte, et mesuree")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
