"""L'assiette du decompte des voix, et le refus de calculer sans elle.

Chaque test porte le nom de la promesse qu'il tient. La promesse centrale du lot
tient en une phrase: **un pourcentage de voix ne sort jamais d'un denominateur
imprime, il sort de l'assiette que la majorite annoncee impose.**

Les nombres ci-dessous sont des **totaux de voix** releves sur les
proces-verbaux des deux cabinets du corpus. Aucun nom, aucun tantieme
individuel, aucun sens de vote nominatif n'y figure - le proces-verbal etalon
nomme environ 120 coproprietaires avec leur vote, et c'est la donnee la plus
sensible du corpus. Les totaux et les assiettes globales sont seuls reproduits.

Si un test ne passait que pour un cabinet, l'assiette serait une modalite et non
un axe. Les deux cabinets sont donc eprouves ici.
"""

from __future__ import annotations

import unittest

from coproscope.modules import _decompte_voix as D


# Cabinet A, assemblee etalon: la feuille de presence totalise 4 899 voix sur
# 10 000 tantiemes generaux.
A_PRESENTES = 4899
A_TOTALES = 10000

# Cabinet B, assemblee 2024: 36 036 voix presentes, representees ou votant par
# correspondance, sur 48 750 tantiemes.
B_PRESENTES = 36036
B_TOTALES = 48750


class RegimeDeMajorite(unittest.TestCase):
    """Chaque majorite nomme son assiette, et une majorite absente le dit."""

    def test_article_24_se_compte_sur_les_voix_exprimees(self):
        regime = D.regime_de_majorite("24")
        self.assertEqual(regime.assiette, D.ASSIETTE_VOIX_EXPRIMEES)
        self.assertIn("LEGIARTI000051749514", [ident for _, ident in regime.sources])

    def test_article_25_se_compte_sur_les_voix_de_tous(self):
        regime = D.regime_de_majorite("25")
        self.assertEqual(regime.assiette, D.ASSIETTE_TOUTES_LES_VOIX)
        self.assertIn("LEGIARTI000051749507", [ident for _, ident in regime.sources])

    def test_le_second_vote_de_l_article_25_1_revient_aux_voix_exprimees(self):
        regime = D.regime_de_majorite("25-1")
        self.assertEqual(regime.assiette, D.ASSIETTE_VOIX_EXPRIMEES)

    def test_l_article_26_est_une_double_condition(self):
        regime = D.regime_de_majorite("26")
        self.assertEqual(regime.assiette, D.ASSIETTE_DOUBLE)

    def test_une_majorite_non_enoncee_ne_devient_pas_l_article_24(self):
        self.assertIsNone(D.regime_de_majorite(None))
        self.assertIsNone(D.regime_de_majorite("Majorite simple"))


class LesAbstentionsNeSontPasDesVoixExprimees(unittest.TestCase):
    """L'article 24 compte le pour et le contre, jamais l'abstention."""

    def test_l_abstention_sort_de_l_assiette_de_l_article_24(self):
        # Cabinet A, resolution ou 679 voix se sont abstenues.
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=3922, voix_contre=298, voix_abstention=679
        )
        self.assertEqual(verdict.base_retenue, 3922 + 298)
        self.assertNotIn(679, (verdict.base_retenue, verdict.seuil_requis))

    def test_sans_les_voix_contre_l_assiette_n_est_pas_reconstituable(self):
        verdict = D.decompte_resolution(majorite="24", voix_pour=4746)
        self.assertEqual(verdict.etat, D.ETAT_ASSIETTE_INDETERMINEE)
        self.assertIsNone(verdict.pourcentage)
        self.assertFalse(verdict.affichable)


class LeDenominateurImprimeNeFondePasLePourcentage(unittest.TestCase):
    """La mesure qui a fonde ce module, sur les deux cabinets."""

    def test_cabinet_a_imprime_le_total_sur_une_resolution_de_l_article_24(self):
        # Resolution du budget: annoncee sous l'article 24, imprimee `/10.000`,
        # alors que le detail publie totalise 4 746 + 105 + 48 = 4 899.
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=4746,
            voix_contre=105,
            voix_abstention=48,
            denominateur_ecrit=10000,
        )
        self.assertEqual(verdict.base_retenue, 4851)
        self.assertEqual(verdict.etat, D.ETAT_ADOPTEE_CONFIRMEE)
        self.assertTrue(any("modalite d'ecriture" in c for c in verdict.constats))

    def test_le_pourcentage_est_calcule_sur_l_assiette_deduite_pas_sur_l_imprime(self):
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=4746,
            voix_contre=105,
            denominateur_ecrit=10000,
        )
        self.assertAlmostEqual(verdict.pourcentage, round(100 * 4746 / 4851, 2))
        self.assertNotAlmostEqual(verdict.pourcentage, 47.46)

    def test_cabinet_b_quand_l_imprime_coincide_aucun_constat_n_est_produit(self):
        # Assemblee 2024: pour 27 885, contre 2 840, imprimes tous deux sur
        # 30 725 - qui est bien la somme des voix exprimees.
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=27885,
            voix_contre=2840,
            voix_abstention=4570,
            denominateur_ecrit=30725,
        )
        self.assertEqual(verdict.base_retenue, 30725)
        self.assertEqual(verdict.constats, [])

    def test_cabinet_b_imprime_un_autre_denominateur_dans_la_meme_resolution(self):
        # La ligne d'abstention de la meme resolution est imprimee sur 48 009.
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=27885,
            voix_contre=2840,
            denominateur_ecrit=48009,
        )
        self.assertEqual(verdict.base_retenue, 30725)
        self.assertTrue(verdict.constats)


class LArticle25PeutEtreHorsDAtteinte(unittest.TestCase):
    """Le predicat qui explique l'assemblee etalon entiere."""

    def test_une_presence_minoritaire_rend_l_article_25_inatteignable(self):
        self.assertFalse(D.majorite_25_atteignable(A_PRESENTES, A_TOTALES))

    def test_une_presence_majoritaire_le_rend_atteignable(self):
        self.assertTrue(D.majorite_25_atteignable(B_PRESENTES, B_TOTALES))

    def test_la_moitie_exacte_ne_suffit_pas(self):
        self.assertFalse(D.majorite_25_atteignable(5000, 10000))
        self.assertTrue(D.majorite_25_atteignable(5001, 10000))

    def test_sans_feuille_de_presence_le_predicat_ne_tranche_pas(self):
        self.assertIsNone(D.majorite_25_atteignable(None, A_TOTALES))

    def test_le_constat_est_porte_dans_le_verdict(self):
        verdict = D.decompte_resolution(
            majorite="25",
            voix_pour=4746,
            voix_contre=105,
            voix_totales=A_TOTALES,
            voix_presentes=A_PRESENTES,
        )
        self.assertTrue(
            any("hors d'atteinte" in c for c in verdict.constats), verdict.constats
        )


class LaPasserelleDeLArticle25Un(unittest.TestCase):
    """Le tiers des voix de tous, et ce qu'il ouvre."""

    def test_le_seuil_du_tiers_est_arrondi_au_superieur(self):
        self.assertEqual(D.seuil_passerelle_25_1(10000), 3334)
        self.assertEqual(D.seuil_passerelle_25_1(48750), 16250)

    def test_le_tiers_exact_suffit(self):
        self.assertTrue(D.passerelle_25_1_ouverte(16250, 48750))
        self.assertFalse(D.passerelle_25_1_ouverte(16249, 48750))

    def test_les_dix_huit_adoptions_de_l_etalon_passent_toutes_par_la_passerelle(self):
        """Voix pour des resolutions de l'article 25 declarees adoptees."""

        adoptees = [
            3491, 4067, 4746, 4746, 4698, 3857, 4746, 4224, 4746, 4794,
            4794, 4434, 3922, 4010, 4794, 4635, 3809, 4737,
        ]
        seuil_25 = D.seuil_majorite_absolue(A_TOTALES)
        for pour in adoptees:
            with self.subTest(pour=pour):
                # Aucune n'atteint le seuil de l'article 25...
                self.assertLess(pour, seuil_25)
                # ...et toutes franchissent le tiers de l'article 25-1.
                self.assertTrue(D.passerelle_25_1_ouverte(pour, A_TOTALES))

    def test_les_trois_rejets_de_l_etalon_n_atteignent_pas_le_tiers(self):
        for pour in (3152, 1982, 1369):
            with self.subTest(pour=pour):
                self.assertFalse(D.passerelle_25_1_ouverte(pour, A_TOTALES))

    def test_le_verdict_nomme_la_passerelle_au_lieu_de_conclure_a_l_adoption(self):
        verdict = D.decompte_resolution(
            majorite="25",
            voix_pour=3491,
            voix_contre=1408,
            voix_totales=A_TOTALES,
            voix_presentes=A_PRESENTES,
            issue_annoncee="adoptee",
        )
        self.assertEqual(verdict.etat, D.ETAT_PASSERELLE_25_1_REQUISE)

    def test_un_rejet_sous_le_tiers_est_confirme(self):
        verdict = D.decompte_resolution(
            majorite="25",
            voix_pour=1369,
            voix_contre=3482,
            voix_totales=A_TOTALES,
            voix_presentes=A_PRESENTES,
            issue_annoncee="rejetee",
        )
        self.assertEqual(verdict.etat, D.ETAT_REJET_CONFIRME)

    def test_proclamee_adoptee_sous_le_tiers_devient_un_constat(self):
        verdict = D.decompte_resolution(
            majorite="25",
            voix_pour=1369,
            voix_contre=3482,
            voix_totales=A_TOTALES,
            voix_presentes=A_PRESENTES,
            issue_annoncee="adoptee",
        )
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_INSUFFISANT)


class LesClesSpeciales(unittest.TestCase):
    """Un scrutin reserve se compte sur le total de sa cle, pas sur le general."""

    def test_un_vote_sur_cle_speciale_se_tranche_sur_ses_propres_voix(self):
        # Cabinet A, travaux propres a une entree: 122 pour, 309 contre, sur une
        # cle de 610 tantiemes. Le proces-verbal conclut au rejet.
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=122,
            voix_contre=309,
            voix_totales=610,
            denominateur_ecrit=610,
        )
        self.assertEqual(verdict.base_retenue, 431)
        self.assertEqual(verdict.etat, D.ETAT_REJET_CONFIRME)

    def test_le_total_de_la_cle_n_est_pas_l_assiette_de_l_article_24(self):
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=122, voix_contre=309, denominateur_ecrit=610
        )
        self.assertNotEqual(verdict.base_retenue, 610)
        self.assertTrue(verdict.constats)


class LArticle26NeSeTrancheQuAvecLesDeuxConditions(unittest.TestCase):
    """La double majorite ne se verifie pas a moitie."""

    def test_le_seuil_des_deux_tiers_est_arrondi_au_superieur(self):
        self.assertEqual(D.seuil_deux_tiers(10000), 6667)

    def test_sans_le_nombre_de_membres_le_controle_n_a_pas_d_objet(self):
        verdict = D.decompte_resolution(
            majorite="26", voix_pour=7000, voix_contre=100, voix_totales=10000
        )
        self.assertEqual(verdict.etat, D.ETAT_ASSIETTE_INDETERMINEE)
        self.assertIsNone(verdict.pourcentage)
        self.assertIn("nombre de membres", verdict.motif)

    def test_les_deux_tiers_des_voix_ne_suffisent_pas_sans_la_majorite_en_nombre(self):
        verdict = D.decompte_resolution(
            majorite="26",
            voix_pour=7000,
            voix_contre=100,
            voix_totales=10000,
            nombre_membres=100,
            nombre_votants_pour=40,
        )
        self.assertEqual(verdict.etat, D.ETAT_REJET_CONFIRME)

    def test_les_deux_conditions_reunies_confirment_l_adoption(self):
        verdict = D.decompte_resolution(
            majorite="26",
            voix_pour=7000,
            voix_contre=100,
            voix_totales=10000,
            nombre_membres=100,
            nombre_votants_pour=60,
        )
        self.assertEqual(verdict.etat, D.ETAT_ADOPTEE_CONFIRMEE)


class LEcranRefuseDeConclure(unittest.TestCase):
    """Les etats de refus sont des resultats, pas des pannes."""

    def test_sans_majorite_enoncee_aucun_pourcentage(self):
        verdict = D.decompte_resolution(majorite=None, voix_pour=100, voix_contre=10)
        self.assertEqual(verdict.etat, D.ETAT_ASSIETTE_INDETERMINEE)
        self.assertFalse(verdict.affichable)

    def test_sans_voix_publiees_l_ecran_dit_que_le_controle_n_est_pas_conduit(self):
        verdict = D.decompte_resolution(majorite="24")
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_ABSENT)
        self.assertFalse(verdict.affichable)
        self.assertIn("article 17", verdict.motif)

    def test_l_article_25_sans_total_du_syndicat_ne_se_calcule_pas(self):
        verdict = D.decompte_resolution(majorite="25", voix_pour=4746, voix_contre=105)
        self.assertEqual(verdict.etat, D.ETAT_ASSIETTE_INDETERMINEE)
        self.assertFalse(verdict.affichable)

    def test_tout_verdict_affichable_nomme_sa_base(self):
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=4746, voix_contre=105
        )
        self.assertTrue(verdict.affichable)
        self.assertIsNotNone(verdict.base_retenue)
        self.assertIsNotNone(verdict.assiette)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
