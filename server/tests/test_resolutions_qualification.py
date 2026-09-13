from __future__ import annotations

import unittest

from coproscope.modules import _resolutions_qualification as Q


class DecisionActeeTests(unittest.TestCase):
    def test_clause_operatoire_preferee_a_l_intitule(self) -> None:
        segment = (
            "12- Vote des travaux de toiture. Article 24 "
            "L'assemblee generale decide de retenir le devis de la societe ALPHA "
            "pour un montant de 3 449,60 EUR."
        )
        actee = Q.decision_actee(segment)
        self.assertIn("decide de retenir", actee)

    def test_objet_cite_entre_guillemets_l_emporte(self) -> None:
        """Cas releve le 17/06/2026: l'intitule n'est qu'une enveloppe."""
        segment = (
            '13- Vote de la Resolution n°13 conformement a la demande de M. X, '
            'et telle quelle est ecrite. "delegation limitee de pouvoirs au '
            'conseil syndical pour certaines decisions relevant de l\'article 24"'
        )
        self.assertEqual(
            Q.decision_actee(segment),
            "delegation limitee de pouvoirs au conseil syndical pour certaines "
            "decisions relevant de l'article 24",
        )

    def test_absence_de_clause_rend_vide(self) -> None:
        self.assertEqual(Q.decision_actee("3- Election du secretaire."), "")


class QualificationTests(unittest.TestCase):
    def test_seuil_de_mise_en_concurrence_sous_trois_formulations(self) -> None:
        for texte in (
            "montant a partir duquel une mise en concurrence est obligatoire",
            "la mise en concurrence est rendue obligatoire",
            "mise en concurrence des entreprises pour attribution des marches",
        ):
            self.assertIn("SEUIL_MISE_EN_CONCURRENCE", Q.qualifications(texte), texte)

    def test_delegation_au_conseil_syndical_et_mandat_au_syndic_sont_distincts(self) -> None:
        delegation = "delegation limitee de pouvoirs au conseil syndical"
        mandat = "L'assemblee generale confere au syndic tout pouvoir a l'effet de"
        self.assertEqual(Q.qualifications(delegation), ["DELEGATION_CS"])
        self.assertEqual(Q.qualifications(mandat), ["MANDAT_SYNDIC"])

    def test_resolution_ordinaire_ne_porte_aucune_qualification(self) -> None:
        self.assertEqual(Q.qualifications("Election du president de seance."), [])


class DureeEtValiditeTests(unittest.TestCase):
    def test_duree_en_mois_et_en_annees(self) -> None:
        self.assertEqual(Q.duree_mois("pour une periode de 14 MOIS"), 14)
        self.assertEqual(Q.duree_mois("pour une duree de 24 mois"), 24)
        self.assertEqual(Q.duree_mois("pour une duree de 2 ans"), 24)

    def test_absence_de_duree_nest_pas_supposee(self) -> None:
        self.assertIsNone(Q.duree_mois("montant fixe a 1.000 EUR TTC"))

    def test_fenetre_de_validite(self) -> None:
        self.assertEqual(Q.fenetre_validite("2023-06-28", 14), ("2023-06-28", "2024-08-28"))
        self.assertEqual(Q.fenetre_validite("2024-07-03", 24), ("2024-07-03", "2026-07-03"))

    def test_sans_duree_le_terme_reste_vide(self) -> None:
        self.assertEqual(Q.fenetre_validite("2022-07-20", None), ("2022-07-20", ""))

    def test_seuil_de_2023_couvre_l_assemblee_de_juillet_2024(self) -> None:
        """Le coeur du controle: quel seuil etait en vigueur ce jour-la."""
        du, au = Q.fenetre_validite("2023-06-28", 14)
        self.assertIs(Q.en_vigueur_le(du, au, "2024-07-03"), True)
        self.assertIs(Q.en_vigueur_le(du, au, "2024-09-01"), False)

    def test_sans_terme_la_question_reste_sans_reponse(self) -> None:
        du, au = Q.fenetre_validite("2022-07-20", None)
        self.assertIsNone(Q.en_vigueur_le(du, au, "2024-07-03"))


class MontantSeuilTests(unittest.TestCase):
    def test_montants_sous_leurs_ecritures_rencontrees(self) -> None:
        self.assertEqual(Q.montant_seuil("Montant propose 2.000,00 € T.T.C."), "2000.00")
        self.assertEqual(Q.montant_seuil("decide de fixer a 1.000 € TTC le montant"), "1000")

    def test_absence_de_montant_rend_vide(self) -> None:
        self.assertEqual(Q.montant_seuil("Election du secretaire de seance."), "")


class DiscordanceIntituleCorpsTests(unittest.TestCase):
    """Releve dans le depouillement manuel du 18/08/2026, PV du 03/07/2024."""

    RES_26 = (
        "26° - Vote du montant des marches et contrats a partir desquels la "
        "consultation du Conseil Syndical est obligatoire par le Syndic, "
        "Montant propose 2.000,00 € T.T.C. pour une duree de 24 mois. "
        "L'Assemblee Generale annuelle decide que le Conseil Syndical sera "
        "consulte prealablement a la passation de tous marches au-dela d'un "
        "seuil de 1000€ TTC pour une periode de 24 MOIS. Ont vote pour : 4635/10.000"
    )
    RES_27 = (
        "27° - Fixation d'un montant a partir duquel la mise en concurrence est "
        "rendue obligatoire. Montant propose 2.000 € T.T.C pour une duree de 24 mois. "
        "L'AG annuelle decide de fixer a 2.000€ TTC le montant a partir duquel une "
        "mise en concurrence est obligatoire, montant decide pour une periode de 3 ans. "
        "Ont vote pour : 3809/10.000"
    )

    def test_le_corps_fait_foi_sur_le_montant(self) -> None:
        v = Q.valeurs_seuil(self.RES_26)
        self.assertEqual(v["montant"], "1000")
        self.assertEqual(v["montant_intitule"], "2000.00")

    def test_le_corps_fait_foi_sur_la_duree(self) -> None:
        v = Q.valeurs_seuil(self.RES_27)
        self.assertEqual(v["duree_mois"], 36)
        self.assertEqual(v["duree_intitule"], 24)

    def test_la_discordance_est_un_constat_pas_un_silence(self) -> None:
        self.assertEqual(len(Q.valeurs_seuil(self.RES_26)["divergences"]), 1)
        self.assertIn("montant", Q.valeurs_seuil(self.RES_26)["divergences"][0])
        self.assertIn("duree", Q.valeurs_seuil(self.RES_27)["divergences"][0])

    def test_pas_de_divergence_quand_les_deux_concordent(self) -> None:
        texte = (
            "5° - Seuil. Montant propose 1.000 € TTC pour une duree de 12 mois. "
            "L'Assemblee Generale decide de fixer a 1.000€ TTC pour une periode "
            "de 12 mois. Ont vote pour : 4000/10.000"
        )
        self.assertEqual(Q.valeurs_seuil(texte)["divergences"], [])

    def test_la_ponctuation_ne_tronque_plus_la_clause(self) -> None:
        """Regression: couper au premier point perdait le montant du corps."""
        clause = Q.decision_actee(self.RES_26)
        self.assertIn("1000", clause)


if __name__ == "__main__":
    unittest.main()
