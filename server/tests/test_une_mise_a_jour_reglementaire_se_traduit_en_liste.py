# -*- coding: utf-8 -*-
"""Cet article a bouge: qu'est-ce qui en depend ?

`RM-2026-0089`, second geste de la description: *TRACER - un choix de code
fonde sur un texte porte son identifiant, de sorte qu'une mise a jour
reglementaire se traduise MECANIQUEMENT en liste de controles a reverifier, au
lieu d'un audit manuel*. La contre-enquete du 2026-09-09 avait abattu la
fermeture de l'item en constatant que **quatre points sur cinq restaient
ouverts**, dont celui-ci.

**CE QUI EXISTAIT ET CE QUI MANQUAIT.** L'index DIRECT - une cle vers un
article, avec sa version et sa date de lecture - existe depuis l'origine.
L'index INVERSE n'existait nulle part: il fallait relire le registre a l'oeil
pour savoir ce qui depend d'un article donne. `cles_par_legiarti` le rend.

**L'AXE.** Ce qui VARIE: le nombre de registres, le nombre de cles par article,
le domaine du controle. Ce qui reste INVARIANT: **un article et les choix qui
en dependent sont une relation a double sens**, et n'en tenir qu'un seul sens
oblige a un audit manuel a chaque mise a jour.

**UNE REPONSE VIDE NE VEUT PAS DIRE *ARTICLE INCONNU*.** Elle veut dire *aucun
choix de ce registre n'en depend*. Les deux se distinguent en interrogeant
`SOURCES`, et le test le fige: confondre les deux ferait conclure *rien a
reverifier* sur un article qu'un autre registre porte.

**CE QUI RESTE OUVERT DANS L'ITEM, ET N'EST PAS TOUCHE ICI.** La description
exige aussi que la lecture consigne **le TEXTE RETENU**. Le registre porte
`legiarti`, `version_debut` et `lu_le`, mais son champ `texte` porte la
designation du texte ENGLOBANT - *de la loi n. 65-557* - et non une ligne de
l'article lu, si bien que `citation()` cite un article **sans en restituer un
mot**. Combler ce point demande une lecture PISTE, donc un acces reseau que la
suite n'a pas et qu'on ne simule pas: **ecrire une regle de droit de memoire
est precisement ce que la skill interdit.** Le point reste donc ouvert, et il
est nomme.
"""
from __future__ import annotations

import unittest

from coproscope.modules._budget_previsionnel_sources import (
    SOURCES,
    cles_par_legiarti,
    source,
)


class UN_ARTICLE_SAIT_CE_QUI_DEPEND_DE_LUI(unittest.TestCase):
    def test_l_index_inverse_retrouve_la_cle(self) -> None:
        cle, declaration = next(iter(SOURCES.items()))
        self.assertIn(cle, cles_par_legiarti(declaration.legiarti))

    def test_il_les_retrouve_TOUTES(self) -> None:
        """Le point de l'item: la liste doit etre complete, pas indicative.

        Une liste partielle est pire qu'aucune: elle donne l'impression que
        l'audit manuel n'est plus necessaire.
        """
        for cle, declaration in SOURCES.items():
            with self.subTest(cle=cle):
                self.assertIn(cle, cles_par_legiarti(declaration.legiarti))

    def test_chaque_reponse_est_triee_et_sans_doublon(self) -> None:
        """Une liste de controles a reverifier se lit; son ordre est donc
        stable, et un doublon ferait croire a deux dependances."""
        for declaration in SOURCES.values():
            rendues = cles_par_legiarti(declaration.legiarti)
            with self.subTest(legiarti=declaration.legiarti):
                self.assertEqual(tuple(sorted(set(rendues))), rendues)

    def test_un_article_INCONNU_rend_le_vide_sans_lever(self) -> None:
        self.assertEqual((), cles_par_legiarti("LEGIARTI000000000000"))

    def test_le_vide_ne_se_confond_pas_avec_INCONNU(self) -> None:
        """Deux faits differents, deux facons de les obtenir.

        `cles_par_legiarti` rend vide dans les deux cas; c'est `source` qui
        distingue, en levant sur une cle inconnue. Sans cette distinction, un
        lecteur conclurait *rien a reverifier* sur un article qu'un autre
        registre porte.
        """
        with self.assertRaises(KeyError):
            source("cle.qui.n.existe.pas")


class LA_LISTE_SERT_A_QUELQUE_CHOSE(unittest.TestCase):
    """Temoin d'utilite: sans cela, l'index serait une fonction morte."""

    def test_elle_rend_des_cles_que_le_registre_sait_citer(self) -> None:
        for declaration in SOURCES.values():
            for cle in cles_par_legiarti(declaration.legiarti):
                with self.subTest(cle=cle):
                    citation = source(cle).citation()
                    self.assertIn(declaration.legiarti, citation)
                    self.assertIn("version du", citation)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
