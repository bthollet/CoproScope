# -*- coding: utf-8 -*-
"""Une periode close se designe par son annee OU par sa date de fin.

`RM-2026-0116`. **L'item se declarait corrige, et la mesure du 2026-09-11 dit
le contraire.** Sur six libelles d'approbation de comptes, date d'assemblee
2025-06-01, **cinq retombaient sur `ORDINAIRE`** - y compris
*« Approbation des comptes de l'exercice CLOS AU 31 decembre 2024 »*, celui que
l'item nomme explicitement comme le cas qui echoue, et
*« comptes arretes au 31 decembre 2024 »*. Le seul qui passait etait
*« exercice 2024 »*.

**La cause exacte.** `periode_close` enumerait deux GABARITS: `du JJ/MM/AAAA au
JJ/MM/AAAA`, et `exercice` suivi IMMEDIATEMENT de quatre chiffres. Le
classement dependait donc de la presence d'une annee accolee au mot
`exercice` - pas du sens de la phrase. Et `None`, qui veut dire *je ne sais
pas*, etait traite comme faux par l'appelant, ce qui renvoyait la resolution
sur `ORDINAIRE`, **le seau generique qui porte les controles de seuil**: un
doute prenait la branche la plus lourde de consequences, en silence.

**LA PREUVE QUE C'ETAIT UNE MODALITE VIENT DU SECOND CABINET, et elle est
sans appel.** Mesure sur `instances/erables_pseudo_test` - 22 documents, second
cabinet, quatre exercices - sur les **53 lignes** qui parlent d'approbation de
comptes:

| | reconnues `APPROBATION_COMPTES` |
|---|---:|
| avant | **0** |
| apres | **8** |

**Zero sur cinquante-trois.** Le gabarit `exercice AAAA` ne ratait pas un cas
limite chez ce cabinet: il ratait **tout**. Et sur le corpus de travail, le
meme correctif change **zero ligne sur 393** - c'est l'autre moitie de la
demonstration: le premier cabinet ecrit la forme couverte, le second non, et
un gabarit calibre sur le premier passait donc tous les tests.

**L'AXE.** Ce qui VARIE: la maniere de designer la periode - par son annee, par
son intervalle, par sa date de cloture, en chiffres ou en lettres. Ce qui reste
INVARIANT: **une approbation de comptes porte sur une periode achevee, et cette
periode a une date de fin.**

**AUCUN LECTEUR NOUVEAU N'EST ECRIT.** `core._date_candidats` lisait deja les
trois formes, et `role_du_candidat` ecartait deja ce qui n'est pas une date -
numero de piece, date d'acte cite, jeton colle a d'autres chiffres. Le module
etait dans le depot et n'etait pas consulte ici, **exactement comme le champ
`exclut` de `RM-2026-0144`**: un troisieme cas, le meme jour, du meme motif.
"""

from __future__ import annotations

import unittest

from coproscope.modules._resolutions_qualification import (
    periode_close,
    portee_resolution,
)

AG = "2025-06-01"


class LES_TROIS_MANIERES_DE_DIRE_LA_MEME_PERIODE(unittest.TestCase):
    """Le meme exercice, sous trois plumes, doit rendre le meme type."""

    def test_l_annee_accolee_au_mot_exercice(self) -> None:
        """La seule forme qui passait avant ce lot."""
        portee, _ = portee_resolution(
            "Approbation des comptes de l’exercice 2024", AG)
        self.assertEqual("APPROBATION_COMPTES", portee)

    def test_la_date_de_cloture_en_toutes_lettres(self) -> None:
        """**Le cas que l'item nommait, et qui echouait encore.**"""
        portee, _ = portee_resolution(
            "Approbation des comptes de l’exercice clos au 31 décembre 2024",
            AG)
        self.assertEqual("APPROBATION_COMPTES", portee)

    def test_la_date_de_cloture_en_chiffres(self) -> None:
        portee, _ = portee_resolution(
            "Approbation des comptes de l’exercice clos au 31/12/2024", AG)
        self.assertEqual("APPROBATION_COMPTES", portee)

    def test_arretes_au_sans_le_mot_exercice(self) -> None:
        """Le mot `exercice` n'est pas la condition: la periode l'est."""
        portee, _ = portee_resolution(
            "Approbation des comptes arrêtés au 31 décembre 2024", AG)
        self.assertEqual("APPROBATION_COMPTES", portee)

    def test_un_numero_de_resolution_en_tete_ne_gene_pas(self) -> None:
        portee, _ = portee_resolution(
            "Résolution n° 3 - Approbation des comptes de l’exercice "
            "clos au 31 décembre 2024", AG)
        self.assertEqual("APPROBATION_COMPTES", portee)


class CE_QUI_RESTE_INCONNU_LE_DIT_ENCORE(unittest.TestCase):
    """**La prudence du module ne doit pas etre perdue au passage.**

    L'item reprochait que `None` soit traite comme faux. Il ne demandait pas
    de faire disparaitre `None`: sans periode lisible, on ne sait pas si la
    resolution arrete un exercice clos ou vote un budget a venir.
    """

    def test_sans_aucune_periode_la_reponse_reste_je_ne_sais_pas(self) -> None:
        self.assertIsNone(periode_close("Approbation des comptes annuels", AG))

    def test_et_la_portee_reste_donc_non_determinee(self) -> None:
        portee, _ = portee_resolution("Approbation des comptes annuels", AG)
        self.assertEqual("ORDINAIRE", portee)

    def test_sans_date_d_assemblee_on_ne_conclut_pas_non_plus(self) -> None:
        """Comparer une fin de periode a rien ne dit rien."""
        self.assertIsNone(periode_close(
            "Approbation des comptes de l’exercice clos au 31/12/2024", ""))


class UNE_PERIODE_NON_ACHEVEE_N_EST_PAS_CLOSE(unittest.TestCase):
    """Le controle temporel, et il doit survivre a l'elargissement."""

    def test_un_exercice_qui_finit_APRES_l_assemblee_n_est_pas_clos(self) -> None:
        self.assertFalse(periode_close(
            "Approbation des comptes de l’exercice clos au 31 décembre 2026",
            AG))

    def test_et_la_resolution_ne_devient_donc_pas_une_approbation(self) -> None:
        portee, _ = portee_resolution(
            "Approbation des comptes de l’exercice clos au 31 décembre 2026",
            AG)
        self.assertNotEqual("APPROBATION_COMPTES", portee)

    def test_un_budget_a_venir_reste_un_budget(self) -> None:
        """Le temoin de non-regression: elargir la lecture des periodes ne doit
        pas faire basculer les budgets."""
        portee, _ = portee_resolution(
            "Vote du budget prévisionnel de l’exercice 2026", AG)
        self.assertEqual("BUDGET_PREVISIONNEL", portee)


class LA_FIN_RETENUE_EST_LA_PLUS_TARDIVE(unittest.TestCase):
    """Un intervalle se borne par sa fin, pas par son ouverture."""

    def test_deux_dates_dans_le_libelle_retiennent_la_seconde(self) -> None:
        """Prendre la premiere daterait l'exercice par son ouverture, donc le
        declarerait clos un an trop tot."""
        self.assertTrue(periode_close(
            "Approbation des comptes, période allant du 1 janvier 2024 "
            "au 31 décembre 2024", AG))

    def test_un_intervalle_qui_se_termine_apres_l_AG_n_est_pas_clos(self) -> None:
        self.assertFalse(periode_close(
            "Comptes de la période allant du 1 janvier 2025 "
            "au 31 décembre 2025", AG))


class CE_QUI_N_EST_PAS_UNE_DATE_DE_CLOTURE_EST_ECARTE(unittest.TestCase):
    """**Elargir la lecture des dates ouvre un risque, et il est garde.**

    Une date presente dans un libelle peut y figurer pour une autre raison.
    `role_du_candidat` le sait deja: il ecarte un jeton colle a d'autres
    chiffres, un numero de piece, et la date d'un ACTE CITE.
    """

    def test_la_date_d_un_texte_CITE_ne_clot_aucun_exercice(self) -> None:
        """Sans cette regle, `decret n° 2012-1115 du 2 octobre 2012` daterait
        la cloture en 2012 - donc `clos`, sur une resolution dont la periode
        n'est pas dite du tout."""
        self.assertIsNone(periode_close(
            "Approbation des comptes établis selon le décret n° 2012-1115 "
            "du 2 octobre 2012", AG))

    def test_le_temoin_la_meme_date_sans_acte_cite_est_bien_lue(self) -> None:
        """Sinon la regle ci-dessus pourrait passer parce qu'aucune date n'est
        lue du tout."""
        self.assertTrue(periode_close(
            "Approbation des comptes arrêtés au 2 octobre 2012", AG))


class UN_QUANTIEME_ABSENT_SE_LIT_COMME_LA_FIN_DU_MOIS(unittest.TestCase):
    """**Et le cas qui le prouve est un mois qui CHEVAUCHE l'assemblee.**

    `decembre 2024` vu d'une assemblee de juin 2025 est clos dans les deux
    lectures - le premier comme le trente-et-un - donc ce cas ne prouve rien.
    Il faut un mois dont le premier jour precede l'assemblee et le dernier la
    suit: la lecture decide alors du verdict.
    """

    def test_le_mois_en_cours_a_la_date_de_l_assemblee_n_est_PAS_clos(self) -> None:
        self.assertFalse(
            periode_close("Approbation des comptes de juin 2025", "2025-06-15"),
            "un exercice dont le mois n'est pas termine est declare clos: le "
            "quantieme absent a ete lu comme le PREMIER du mois")

    def test_le_mois_precedent_l_est(self) -> None:
        """Le temoin de sante: sans lui, le test ci-dessus passerait aussi
        avec une lecture qui ne trouve jamais de date."""
        self.assertTrue(
            periode_close("Approbation des comptes de mai 2025", "2025-06-15"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
