"""Les replis muets du decompte des voix, fermes le 2026-09-04.

Chaque test reproduit d'abord la mesure de l'audit, puis exige le fait nomme qui
la remplace. Tous echouent sur le code du 2026-09-03: c'est ce qui les distingue
d'une paraphrase du code corrige.

Les nombres sont des **totaux de voix** releves sur les proces-verbaux des deux
cabinets du corpus. Aucun nom, aucun tantieme individuel, aucun sens de vote
nominatif n'y figure.
"""

from __future__ import annotations

import unittest

from coproscope.modules import _decompte_voix as D

# Cabinet A, assemblee etalon: 4 899 voix presentes sur 10 000 tantiemes.
A_PRESENTES = 4899
A_TOTALES = 10000


class LArticle25UnNEstPasUneMajoriteDEntree(unittest.TestCase):
    """Le second vote n'existe que si le tiers qui l'ouvre a ete recueilli."""

    def test_sous_le_tiers_l_adoption_n_est_pas_confirmee(self):
        # Mesure de l'audit: 3 000 voix pour, 100 contre, sur 10 000 tantiemes.
        # Le tiers est a 3 334. Le module rendait ADOPTEE_CONFIRMEE a 96,77 %.
        verdict = D.decompte_resolution(
            majorite="25-1", voix_pour=3000, voix_contre=100, voix_totales=A_TOTALES
        )
        self.assertEqual(verdict.etat, D.ETAT_PASSERELLE_25_1_NON_OUVERTE)
        self.assertNotEqual(verdict.etat, D.ETAT_ADOPTEE_CONFIRMEE)

    def test_sous_le_tiers_aucun_pourcentage_n_est_rendu(self):
        verdict = D.decompte_resolution(
            majorite="25-1", voix_pour=3000, voix_contre=100, voix_totales=A_TOTALES
        )
        self.assertIsNone(verdict.pourcentage)
        self.assertFalse(verdict.affichable)

    def test_le_tiers_manquant_est_nomme_au_lieu_d_etre_saute(self):
        # Sans le total du syndicat, la condition d'ouverture est invisible: le
        # module comptait alors sur les seules voix exprimees, sans le dire.
        verdict = D.decompte_resolution(
            majorite="25-1", voix_pour=3000, voix_contre=100
        )
        self.assertEqual(verdict.etat, D.ETAT_ASSIETTE_INDETERMINEE)
        self.assertIn("tiers des voix", verdict.motif)

    def test_au_dessus_du_tiers_le_second_vote_se_compte_sur_les_exprimees(self):
        verdict = D.decompte_resolution(
            majorite="25-1", voix_pour=3491, voix_contre=1408, voix_totales=A_TOTALES
        )
        self.assertEqual(verdict.etat, D.ETAT_ADOPTEE_CONFIRMEE)
        self.assertEqual(verdict.base_retenue, 3491 + 1408)
        self.assertTrue(
            any("condition d'ouverture" in c for c in verdict.constats),
            verdict.constats,
        )

    def test_la_condition_porte_sur_le_premier_vote_quand_il_est_fourni(self):
        # Le second vote peut recueillir plus de voix que le premier: c'est le
        # premier qui ouvre la passerelle.
        verdict = D.decompte_resolution(
            majorite="25-1",
            voix_pour=4000,
            voix_contre=100,
            voix_totales=A_TOTALES,
            voix_pour_premier_vote=3000,
        )
        self.assertEqual(verdict.etat, D.ETAT_PASSERELLE_25_1_NON_OUVERTE)


class LesNombresLusDoiventPouvoirEtreTousVrais(unittest.TestCase):
    """Un decompte impossible est un constat, pas un pourcentage."""

    def test_plus_de_voix_pour_que_de_presents(self):
        # Mesure de l'audit: 6 000 pour, 4 899 presents -> 98,36 % confirmes.
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=6000,
            voix_contre=100,
            voix_presentes=A_PRESENTES,
            voix_totales=A_TOTALES,
        )
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_INCOHERENT)
        self.assertIsNone(verdict.pourcentage)
        self.assertIn("4899", verdict.motif)
        self.assertIn("6100", verdict.motif)

    def test_plus_de_voix_pour_que_le_total_du_syndicat(self):
        # Mesure de l'audit: 49 000 sur 10 000 -> ADOPTEE_CONFIRMEE a 490 %.
        verdict = D.decompte_resolution(
            majorite="25", voix_pour=49000, voix_totales=A_TOTALES
        )
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_INCOHERENT)
        self.assertIsNone(verdict.pourcentage)

    def test_un_nombre_de_voix_negatif_n_est_pas_un_decompte(self):
        # Mesure de l'audit: -100 pour, 200 contre -> REJET_CONFIRME a -100 %.
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=-100, voix_contre=200
        )
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_INCOHERENT)
        self.assertIsNone(verdict.pourcentage)

    def test_l_abstention_entre_dans_le_controle_croise(self):
        # Mesure de l'audit: une abstention de 99 999 ne changeait rien, le
        # parametre n'etait lu nulle part.
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=100,
            voix_contre=50,
            voix_abstention=99999,
            voix_presentes=A_PRESENTES,
        )
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_INCOHERENT)
        self.assertIn("abstentions", verdict.motif)

    def test_l_arithmetique_du_cabinet_b_tombe_juste_et_ne_produit_rien(self):
        # 30 725 exprimees + 4 570 abstentions = 35 295, sous les 36 036 de la
        # feuille de presence. Aucun controle ne doit se declencher.
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=27885,
            voix_contre=2840,
            voix_abstention=4570,
            voix_presentes=36036,
            voix_totales=48750,
            denominateur_ecrit=30725,
        )
        self.assertEqual(verdict.etat, D.ETAT_ADOPTEE_CONFIRMEE)
        self.assertEqual(verdict.constats, [])


class PasDeVoteNEstPasUneIrregularite(unittest.TestCase):
    """L'article 17 du decret n'est pas oppose a une question non mise aux voix."""

    def test_le_vocabulaire_de_l_extracteur_est_lu(self):
        verdict = D.decompte_resolution(majorite="24", issue_annoncee="PAS_DE_VOTE")
        self.assertEqual(verdict.etat, D.ETAT_SANS_VOTE)
        self.assertNotIn("article 17", verdict.motif)

    def test_sans_objet_et_reportee_le_sont_aussi(self):
        for issue in ("SANS_OBJET", "REPORTEE", "Pas de vote", "Sans objet"):
            with self.subTest(issue=issue):
                verdict = D.decompte_resolution(majorite="25", issue_annoncee=issue)
                self.assertEqual(verdict.etat, D.ETAT_SANS_VOTE)

    def test_une_issue_non_tracee_reste_un_decompte_absent(self):
        # "on ne sait rien" n'est pas "le document dit qu'il n'y a pas eu de
        # vote": l'irregularite reste opposable.
        verdict = D.decompte_resolution(
            majorite="24", issue_annoncee="SANS_ISSUE_TRACEE"
        )
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_ABSENT)
        self.assertIn("article 17", verdict.motif)


class LeVoteParCorrespondanceAmende(unittest.TestCase):
    """L'article 17-1 A al. 2, et la ligne sans laquelle on ne recalcule pas."""

    def test_sans_la_ligne_publiee_le_controle_n_est_pas_conduit(self):
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=15400,
            voix_contre=15325,
            resolution_amendee=True,
        )
        self.assertEqual(verdict.etat, D.ETAT_ASSIETTE_INDETERMINEE)
        self.assertIn("defaillant", verdict.motif)
        self.assertIn(
            "LEGIARTI000039313644", [ident for _, ident in verdict.sources]
        )

    def test_avec_la_ligne_publiee_le_verdict_bascule(self):
        # Mesure de l'audit sur le cas du cabinet B: adoptee a 50,12 % sur
        # 30 725 avant retrait, rejetee a 48,89 % sur 29 984 apres.
        avant = D.decompte_resolution(
            majorite="24", voix_pour=15400, voix_contre=15325
        )
        self.assertEqual(avant.etat, D.ETAT_ADOPTEE_CONFIRMEE)
        self.assertEqual(avant.base_retenue, 30725)

        apres = D.decompte_resolution(
            majorite="24",
            voix_pour=15400,
            voix_contre=15325,
            resolution_amendee=True,
            voix_correspondance_favorables=741,
        )
        self.assertEqual(apres.etat, D.ETAT_REJET_CONFIRME)
        self.assertEqual(apres.base_retenue, 29984)
        self.assertEqual(apres.seuil_requis, 14993)
        self.assertAlmostEqual(apres.pourcentage, 48.89)
        self.assertTrue(
            any("amendee en seance" in c for c in apres.constats), apres.constats
        )

    def test_une_ligne_plus_grande_que_le_pour_est_un_decompte_incoherent(self):
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=100,
            voix_contre=50,
            resolution_amendee=True,
            voix_correspondance_favorables=200,
        )
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_INCOHERENT)


class LArticle26ConfronteAussi(unittest.TestCase):
    """La promesse du module tenait sur trois regimes sur quatre."""

    def test_le_denominateur_imprime_est_confronte(self):
        verdict = D.decompte_resolution(
            majorite="26",
            voix_pour=7000,
            voix_totales=A_TOTALES,
            denominateur_ecrit=A_PRESENTES,
            nombre_membres=120,
            nombre_votants_pour=80,
        )
        self.assertTrue(
            any("modalite d'ecriture" in c for c in verdict.constats), verdict.constats
        )

    def test_les_deux_tiers_hors_d_atteinte_sont_signales(self):
        verdict = D.decompte_resolution(
            majorite="26",
            voix_pour=4000,
            voix_totales=A_TOTALES,
            voix_presentes=A_PRESENTES,
            nombre_membres=120,
            nombre_votants_pour=80,
        )
        self.assertTrue(
            any("hors d'atteinte" in c for c in verdict.constats), verdict.constats
        )
        self.assertTrue(any("article 26" in c for c in verdict.constats))

    def test_le_refus_faute_de_membres_porte_quand_meme_les_constats(self):
        verdict = D.decompte_resolution(
            majorite="26",
            voix_pour=4000,
            voix_totales=A_TOTALES,
            voix_presentes=A_PRESENTES,
        )
        self.assertEqual(verdict.etat, D.ETAT_ASSIETTE_INDETERMINEE)
        self.assertTrue(verdict.constats)


class LeDecompteEstConfronteALIssueProclamee(unittest.TestCase):
    """`CONFIRMEE` ne peut plus dire "confirme" sans avoir compare."""

    def test_le_seuil_atteint_contre_un_rejet_proclame(self):
        # Mesure de l'audit: le module rendait ADOPTEE_CONFIRMEE.
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=100, voix_contre=10, issue_annoncee="Rejetee"
        )
        self.assertEqual(verdict.etat, D.ETAT_ISSUE_CONTREDITE)

    def test_le_seuil_non_atteint_contre_une_adoption_proclamee_sous_l_article_24(self):
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=10, voix_contre=100, issue_annoncee="Adoptee"
        )
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_INSUFFISANT)

    def test_la_contradiction_se_voit_aussi_sous_l_article_26(self):
        verdict = D.decompte_resolution(
            majorite="26",
            voix_pour=7000,
            voix_totales=A_TOTALES,
            nombre_membres=100,
            nombre_votants_pour=60,
            issue_annoncee="Rejetee",
        )
        self.assertEqual(verdict.etat, D.ETAT_ISSUE_CONTREDITE)

    def test_un_accord_reste_une_confirmation(self):
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=100, voix_contre=10, issue_annoncee="Adoptee"
        )
        self.assertEqual(verdict.etat, D.ETAT_ADOPTEE_CONFIRMEE)


class LeRefusNeMentPlusSurSonMotif(unittest.TestCase):
    """Une majorite enoncee et non reconnue n'est pas une majorite absente."""

    def test_un_libelle_non_reconnu_le_dit(self):
        verdict = D.decompte_resolution(majorite="25B", voix_pour=100, voix_contre=10)
        self.assertEqual(verdict.etat, D.ETAT_ASSIETTE_INDETERMINEE)
        self.assertIn("25B", verdict.motif)
        self.assertIn("n'est pas un regime reconnu", verdict.motif)
        self.assertNotIn("n'est pas enoncee", verdict.motif)

    def test_une_majorite_reellement_absente_le_dit_autrement(self):
        verdict = D.decompte_resolution(majorite="", voix_pour=100, voix_contre=10)
        self.assertIn("n'est pas enoncee", verdict.motif)

    def test_le_bruit_d_ecriture_ne_fait_pas_manquer_un_regime(self):
        for libelle in ("Article 24", "art. 25", "ARTICLES N° 26", " 25-1 "):
            with self.subTest(libelle=libelle):
                self.assertIsNotNone(D.regime_de_majorite(libelle))

    def test_la_lettre_de_l_article_25_n_est_pas_effacee(self):
        # `25B` n'est pas ramene a `25`: la lettre separe des regimes.
        self.assertIsNone(D.regime_de_majorite("25B"))


class LeDenominateurImprimeSurvitAuRefus(unittest.TestCase):
    """12 des 24 refus de la piece etalon jetaient un denominateur lu."""

    def test_un_refus_faute_de_voix_contre_restitue_le_denominateur(self):
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=4746, denominateur_ecrit=A_TOTALES
        )
        self.assertEqual(verdict.etat, D.ETAT_ASSIETTE_INDETERMINEE)
        self.assertIsNone(verdict.pourcentage)
        self.assertEqual(verdict.denominateur_ecrit, A_TOTALES)

    def test_un_decompte_absent_restitue_le_denominateur(self):
        verdict = D.decompte_resolution(majorite="24", denominateur_ecrit=A_PRESENTES)
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_ABSENT)
        self.assertEqual(verdict.denominateur_ecrit, A_PRESENTES)

    def test_une_majorite_non_reconnue_restitue_le_denominateur(self):
        verdict = D.decompte_resolution(
            majorite="23", voix_pour=100, denominateur_ecrit=A_TOTALES
        )
        self.assertEqual(verdict.denominateur_ecrit, A_TOTALES)


class LeFaitEtalonResteCalculable(unittest.TestCase):
    """4 899 presents sur 10 000: l'article 25 etait hors d'atteinte."""

    def test_les_dix_huit_adoptions_restent_expliquees_par_la_passerelle(self):
        adoptees = [
            3491, 4067, 4746, 4746, 4698, 3857, 4746, 4224, 4746, 4794,
            4794, 4434, 3922, 4010, 4794, 4635, 3809, 4737,
        ]
        for pour in adoptees:
            with self.subTest(pour=pour):
                verdict = D.decompte_resolution(
                    majorite="25",
                    voix_pour=pour,
                    voix_contre=A_PRESENTES - pour,
                    voix_totales=A_TOTALES,
                    voix_presentes=A_PRESENTES,
                    issue_annoncee="ADOPTEE",
                )
                self.assertEqual(verdict.etat, D.ETAT_PASSERELLE_25_1_REQUISE)
                self.assertTrue(
                    any("hors d'atteinte" in c for c in verdict.constats)
                )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
