# -*- coding: utf-8 -*-
"""Les quatre egalites du decret 2005-240 sont des fonctions, pas une phrase.

`RM-2026-0094`. L'item disait le lot *moins cher qu'il n'y parait*: la source
est deja declaree au registre, et le modele porte deja trois des totaux. Il
demandait de porter les quatre egalites dans le code, et de lever
l'auto-limitation declaree par les lecteurs d'annexes.

**L'AUTO-LIMITATION ETAIT JUSTE, ET ELLE EST DEVENUE FAUSSE.** Les lecteurs
declaraient que *les modeles d'annexes ne sont pas reproduits au Journal
officiel accessible par machine*. Trois voies numeriques l'ont confirme le
2026-09-06: l'API rend `Annexe non reproduite`, la page du JO renvoie au
tableau papier, le PDF est refuse en 401 puis 403. **Puis Brice a depose le
fichier officiel lui-meme** - `joe_20050318_0065_0007.pdf`, JO du 18 mars
2005, texte 7 sur 102, NOR `SOCU0412534D` - lu page par page. La limitation
portait sur l'ACCES, et l'acces a ete comble. **Ce qui n'est pas leve:** les
rubriques de ventilation des annexes 3 et 4 sont arretees par le reglement de
copropriete, donc jamais universelles.

**CE QUE CES TESTS EPROUVENT, ET CE QU'ILS N'EPROUVENT PAS.** Ils eprouvent
l'arithmetique des egalites, leur reserve de lecture, et le fait qu'un total
manquant ne conclut jamais. Ils n'eprouvent **pas** que la chaine de lecture
remplit ces totaux: elle ne le fait pas encore, et c'est le residu nomme du
lot. Le distinguer importe - un controle branche sur rien rendrait
`INDETERMINE` partout, ce qui est correct mais ne verifie aucune comptabilite.
"""
from __future__ import annotations

import importlib
import unittest
from decimal import Decimal

E = importlib.import_module("coproscope.modules._comptes_egalites_annexes")


class L_EGALITE_DES_OPERATIONS_COURANTES(unittest.TestCase):
    """`CTRL-A10-1` et `CTRL-A10-3`: une seule arithmetique, deux moments."""

    def test_deux_totaux_egaux_concluent(self) -> None:
        r = E.egalite_courantes(Decimal("12000.00"), Decimal("12000.00"),
                                E.BLOC_COURANTES, E.APPROBATION_DES_COMPTES)
        self.assertEqual(E.CONFORME, r.etat)
        self.assertTrue(r.conclut())
        self.assertEqual("CTRL-A10-1", r.controle)

    def test_le_meme_controle_change_de_NOM_au_vote_du_budget(self) -> None:
        """Le decret pose la meme egalite aux deux moments: une seule
        arithmetique, sinon la regle peut diverger en deux endroits."""
        r = E.egalite_courantes(Decimal("1.00"), Decimal("1.00"),
                                E.BLOC_COURANTES, E.VOTE_DU_BUDGET)
        self.assertEqual("CTRL-A10-3", r.controle)
        self.assertEqual(E.CONFORME, r.etat)

    def test_un_ecart_est_nomme_et_chiffre(self) -> None:
        r = E.egalite_courantes(Decimal("12000.00"), Decimal("11500.00"),
                                E.BLOC_COURANTES, E.APPROBATION_DES_COMPTES)
        self.assertEqual(E.ECART, r.etat)
        self.assertFalse(r.conclut())
        self.assertIn("500", r.motif)

    def test_un_arrondi_au_centime_n_est_pas_un_ecart(self) -> None:
        r = E.egalite_courantes(Decimal("12000.01"), Decimal("12000.00"),
                                E.BLOC_COURANTES, E.APPROBATION_DES_COMPTES)
        self.assertEqual(E.CONFORME, r.etat)

    def test_un_total_absent_ne_conclut_PAS(self) -> None:
        """Le coeur de la regle des trois etats: l'absence n'est pas la
        conformite. Un rapport comptable se lit comme une attestation."""
        r = E.egalite_courantes(None, Decimal("12000.00"), E.BLOC_COURANTES,
                                E.APPROBATION_DES_COMPTES)
        self.assertEqual(E.INDETERMINE, r.etat)
        self.assertFalse(r.conclut())


class LA_RESERVE_DE_LECTURE_EST_PORTEE_PAR_LE_CODE(unittest.TestCase):
    """L'annexe 2 porte DEUX blocs, et le texte ne dit pas lequel il vise."""

    def test_un_bloc_non_designe_rend_INDETERMINE(self) -> None:
        r = E.egalite_courantes(Decimal("1.00"), Decimal("1.00"),
                                "BLOC_INCONNU", E.APPROBATION_DES_COMPTES)
        self.assertEqual(E.INDETERMINE, r.etat)
        self.assertIn("deux", r.motif)

    def test_le_mauvais_bloc_ne_se_compare_pas_au_hasard(self) -> None:
        """Comparer l'annexe 3 au bloc travaux produirait un ecart FAUX, plus
        couteux qu'une absence de controle: il accuse une comptabilite."""
        r = E.egalite_courantes(Decimal("1.00"), Decimal("1.00"),
                                E.BLOC_TRAVAUX_EXCEPTIONNELLES,
                                E.APPROBATION_DES_COMPTES)
        self.assertEqual(E.INDETERMINE, r.etat)

    def test_le_bloc_travaux_exige_son_propre_bloc(self) -> None:
        r = E.egalite_travaux_et_exceptionnelles(
            Decimal("1.00"), Decimal("1.00"), E.BLOC_COURANTES)
        self.assertEqual(E.INDETERMINE, r.etat)


class L_EGALITE_DU_SOLDE_EN_ATTENTE(unittest.TestCase):
    """`CTRL-A5-1`: la colonne E de l'annexe 5 et le compte 12 de l'annexe 1."""

    def test_les_deux_expressions_du_meme_solde_coincident(self) -> None:
        r = E.egalite_solde_en_attente(Decimal("-4200.00"), Decimal("-4200.00"))
        self.assertEqual(E.CONFORME, r.etat)

    def test_un_solde_absent_ne_conclut_pas(self) -> None:
        r = E.egalite_solde_en_attente(Decimal("-4200.00"), None)
        self.assertEqual(E.INDETERMINE, r.etat)


class LE_MOMENT_DECIDE_DES_EGALITES_EXIGIBLES(unittest.TestCase):
    """Exiger les quatre a tous les moments inventerait des obligations."""

    def test_le_vote_du_budget_n_exige_qu_une_egalite(self) -> None:
        rendues = E.toutes_les_egalites(
            total_annexe3_courantes=Decimal("1.00"),
            total_annexe2_courantes=Decimal("1.00"),
            moment=E.VOTE_DU_BUDGET)
        self.assertEqual(1, len(rendues))
        self.assertEqual("CTRL-A10-3", rendues[0].controle)

    def test_l_approbation_en_exige_trois(self) -> None:
        rendues = E.toutes_les_egalites(moment=E.APPROBATION_DES_COMPTES)
        self.assertEqual(
            ["CTRL-A10-1", "CTRL-A10-2", "CTRL-A5-1"],
            [r.controle for r in rendues])

    def test_les_quatre_controles_du_decret_sont_tous_joignables(self) -> None:
        """Quatre controles pour trois egalites: l'article 10 pose la meme aux
        deux moments, et c'est ce qui fait quatre lignes au referentiel."""
        noms = {r.controle for r in E.toutes_les_egalites(
            moment=E.APPROBATION_DES_COMPTES)}
        noms |= {r.controle for r in E.toutes_les_egalites(
            moment=E.VOTE_DU_BUDGET)}
        self.assertEqual(
            {"CTRL-A10-1", "CTRL-A10-2", "CTRL-A10-3", "CTRL-A5-1"}, noms)


class LA_COMPOSITION_NE_MASQUE_PAS_UN_CONTROLE_NON_FAIT(unittest.TestCase):
    """Chainer des controles masque leur echec: lecon deja payee."""

    def test_un_indetermine_domine_trois_conformes(self) -> None:
        conforme = E.egalite_solde_en_attente(Decimal("1.00"), Decimal("1.00"))
        indetermine = E.egalite_solde_en_attente(Decimal("1.00"), None)
        self.assertEqual(
            E.INDETERMINE,
            E.la_plus_prudente(conforme, conforme, conforme, indetermine))

    def test_un_ecart_domine_un_indetermine(self) -> None:
        ecart = E.egalite_solde_en_attente(Decimal("1.00"), Decimal("9.00"))
        indetermine = E.egalite_solde_en_attente(Decimal("1.00"), None)
        self.assertEqual(E.ECART, E.la_plus_prudente(indetermine, ecart))

    def test_rien_a_composer_n_est_pas_conforme(self) -> None:
        self.assertEqual(E.INDETERMINE, E.la_plus_prudente())


class LE_FONDEMENT_SE_LIT_AU_REGISTRE(unittest.TestCase):
    """Le code cite une CLE; le registre cite le texte, sa version, sa date."""

    def test_chaque_egalite_sait_citer_son_article(self) -> None:
        for egalite in E.toutes_les_egalites(moment=E.APPROBATION_DES_COMPTES):
            with self.subTest(controle=egalite.controle):
                citation = egalite.citation()
                self.assertIn("LEGIARTI", citation)
                self.assertRegex(citation, r"version du \d{4}-\d{2}-\d{2}")

    def test_aucun_identifiant_n_est_recopie_dans_ce_module(self) -> None:
        """La regle des fondements: le code ne recopie jamais un numero."""
        from pathlib import Path
        source = (Path(E.__file__)).read_text(encoding="utf-8")
        self.assertNotIn("LEGIARTI0000", source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
