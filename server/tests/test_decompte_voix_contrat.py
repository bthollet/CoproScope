"""Le contrat de types avec l'extracteur, et les sources que le verdict porte.

Deux constats de l'audit du 2026-09-04 que le lot du 2026-09-04 avait laisses
sans reponse - ni corriges, ni refutes, ni renvoyes hors portee.

**C096 - le contrat de types n'est pas defendu.** Les champs de voix de
`Resolution` sont declares `str = ""`, et la chaine vide y signifie exactement
"le proces-verbal ne publie pas les voix". Mesures d'origine, reproduites sur le
code du 2026-09-04:

    decompte_resolution("24", voix_pour="")          -> ValueError
    decompte_resolution("25", voix_pour=6000, voix_totales="10000") -> TypeError
    decompte_resolution("24", voix_pour=100.9, voix_contre=0) -> 100, sans un mot

Le garde qui devait rendre `DECOMPTE_ABSENT` rendait une trace, et la troncature
d'un nombre a virgule ne disait rien.

**C097 - cinq des six constantes de source sont mortes.** Un verdict rendu sur
un vote reel ne citait que l'article de la majorite: ni l'article 22 I, qui
definit ce qu'est une voix, ni l'article 10 dernier alinea, qui fonde le
scrutin par cle speciale, ni l'article 14 du decret pour la feuille de presence
lorsqu'elle sert le controle croise.

Les nombres sont des totaux de voix releves sur les deux cabinets du corpus.
Aucun nom, aucun tantieme individuel, aucun sens de vote nominatif n'y figure.
"""

from __future__ import annotations

import unittest

from coproscope.modules import _decompte_voix as D

A_PRESENTES = 4899
A_TOTALES = 10000


class LaChaineVideEstUneAbsenceDeVoix(unittest.TestCase):
    """Le type que l'extracteur produit reellement traverse le module."""

    def test_voix_pour_vide_rend_le_decompte_absent_au_lieu_de_lever(self):
        # Mesure d'origine: ValueError: invalid literal for int() with base 10.
        verdict = D.decompte_resolution(majorite="24", voix_pour="")
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_ABSENT)

    def test_les_trois_champs_de_voix_acceptent_la_chaine_vide(self):
        for champ in ("voix_contre", "voix_abstention", "voix_presentes"):
            with self.subTest(champ=champ):
                verdict = D.decompte_resolution(
                    majorite="24", voix_pour="100", **{champ: ""}
                )
                self.assertNotEqual(verdict.etat, D.ETAT_DECOMPTE_ILLISIBLE)

    def test_une_chaine_de_chiffres_est_lue_comme_le_nombre_qu_elle_ecrit(self):
        verdict = D.decompte_resolution(
            majorite="24", voix_pour="4746", voix_contre="153"
        )
        self.assertEqual(verdict.voix_pour, 4746)
        self.assertEqual(verdict.base_retenue, 4899)

    def test_un_total_ecrit_en_chaine_ne_leve_plus_sur_la_comparaison(self):
        # Mesure d'origine: TypeError '<=' not supported between str and int.
        verdict = D.decompte_resolution(
            majorite="25", voix_pour="6000", voix_totales="10000"
        )
        self.assertEqual(verdict.etat, D.ETAT_ADOPTEE_CONFIRMEE)
        self.assertEqual(verdict.base_retenue, A_TOTALES)


class UneValeurIllisibleEstNommee(unittest.TestCase):
    """Une valeur ecrite qu'on ne sait pas lire n'est pas une valeur absente."""

    def test_un_nombre_a_virgule_n_est_plus_tronque_en_silence(self):
        # Mesure d'origine: 100.9 devenait 100 voix pour, sans un mot.
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=100.9, voix_contre=0
        )
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_ILLISIBLE)
        self.assertIsNone(verdict.pourcentage)

    def test_le_motif_nomme_le_champ_et_la_valeur_lue(self):
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=100.9, voix_contre=0
        )
        self.assertIn("voix pour", verdict.motif)
        self.assertIn("100.9", verdict.motif)

    def test_un_texte_qui_n_est_pas_un_nombre_est_refuse_sans_exception(self):
        for valeur in ("environ 2000", "4 746 / 10.000", "n/a", "-"):
            with self.subTest(valeur=valeur):
                verdict = D.decompte_resolution(majorite="24", voix_pour=valeur)
                self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_ILLISIBLE)

    def test_un_booleen_ne_devient_pas_une_voix(self):
        # True est un entier en Python: sans garde, il valait 1 voix pour.
        verdict = D.decompte_resolution(majorite="24", voix_pour=True)
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_ILLISIBLE)

    def test_le_denominateur_imprime_survit_au_refus_d_illisibilite(self):
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=100.9, denominateur_ecrit=4899
        )
        self.assertEqual(verdict.denominateur_ecrit, 4899)

    def test_l_illisible_ne_se_confond_pas_avec_l_absent(self):
        absent = D.decompte_resolution(majorite="24", voix_pour="")
        illisible = D.decompte_resolution(majorite="24", voix_pour="environ 2000")
        self.assertNotEqual(absent.etat, illisible.etat)


class LesSourcesDuScrutinSontPortees(unittest.TestCase):
    """Un ecran qui affiche verdict.sources doit voir le fondement du scrutin."""

    @staticmethod
    def _articles(verdict) -> list[str]:
        return [libelle for libelle, _ in verdict.sources]

    def test_l_article_qui_definit_une_voix_accompagne_tout_decompte(self):
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=800, voix_contre=200, denominateur_ecrit=1155
        )
        self.assertIn(D.SOURCE_VOIX[0], self._articles(verdict))

    def test_le_scrutin_par_cle_speciale_cite_l_article_10(self):
        # Mesure d'origine: un verdict article 24 sur cle speciale ne portait
        # que ('loi 65-557, art. 24 I', ...).
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=800,
            voix_contre=200,
            denominateur_ecrit=1155,
            cle_speciale=True,
        )
        self.assertIn(D.SOURCE_CLE_SPECIALE[0], self._articles(verdict))

    def test_sans_declaration_de_cle_speciale_l_article_10_n_est_pas_invente(self):
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=800, voix_contre=200
        )
        self.assertNotIn(D.SOURCE_CLE_SPECIALE[0], self._articles(verdict))

    def test_la_feuille_de_presence_est_citee_des_qu_elle_sert(self):
        verdict = D.decompte_resolution(
            majorite="25",
            voix_pour=6000,
            voix_presentes=8000,
            voix_totales=A_TOTALES,
        )
        self.assertIn(D.SOURCE_FEUILLE_PRESENCE[0], self._articles(verdict))

    def test_le_vote_par_correspondance_cite_sa_neutralisation(self):
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=30725,
            voix_contre=4570,
            resolution_amendee=True,
            voix_correspondance_favorables=741,
        )
        self.assertIn(D.SOURCE_CORRESPONDANCE_PRESENT[0], self._articles(verdict))

    def test_aucune_source_n_est_citee_deux_fois(self):
        verdict = D.decompte_resolution(
            majorite="25",
            voix_pour=6000,
            voix_presentes=8000,
            voix_totales=A_TOTALES,
            cle_speciale=True,
        )
        self.assertEqual(len(verdict.sources), len(set(verdict.sources)))


class LeControleCroiseNeMelangePasDeuxUnites(unittest.TestCase):
    """La presence generale et le total d'une cle speciale ne se comparent pas.

    Regression annoncee "a surveiller" le 2026-09-05, et reproduite des que
    l'appelant declare le scrutin restreint: la feuille de presence porte les
    tantiemes generaux, le total porte ceux de la cle. Les confronter faisait
    dire "la feuille de presence depasse le total des voix du syndicat" alors
    que rien n'etait incoherent.
    """

    def test_la_presence_generale_ne_contredit_pas_le_total_d_une_cle(self):
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=900,
            voix_contre=100,
            voix_presentes=A_PRESENTES,
            voix_totales=1155,
            cle_speciale=True,
        )
        self.assertNotEqual(verdict.etat, D.ETAT_DECOMPTE_INCOHERENT)

    def test_le_controle_non_conduit_est_dit_au_lieu_d_etre_tu(self):
        verdict = D.decompte_resolution(
            majorite="24",
            voix_pour=900,
            voix_contre=100,
            voix_presentes=A_PRESENTES,
            voix_totales=1155,
            cle_speciale=True,
        )
        self.assertTrue(
            any("cle speciale" in c for c in verdict.constats), verdict.constats
        )

    def test_hors_cle_speciale_le_controle_croise_reste_entier(self):
        # Non-regression: c'est le controle que C038 a ouvert, il ne doit pas
        # etre desarme par le nouveau parametre.
        verdict = D.decompte_resolution(
            majorite="25",
            voix_pour=6000,
            voix_presentes=6000,
            voix_totales=A_PRESENTES,
        )
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_INCOHERENT)

    def test_une_valeur_negative_reste_refusee_meme_sur_cle_speciale(self):
        verdict = D.decompte_resolution(
            majorite="24", voix_pour=-100, voix_contre=10, cle_speciale=True
        )
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_INCOHERENT)

    def test_le_pour_reste_confronte_au_total_de_sa_propre_cle(self):
        verdict = D.decompte_resolution(
            majorite="25", voix_pour=1200, voix_totales=1155, cle_speciale=True
        )
        self.assertEqual(verdict.etat, D.ETAT_DECOMPTE_INCOHERENT)


class LUnanimiteDeLArticle26Existe(unittest.TestCase):
    """Les deux tiers ne sont pas l'unanimite, et le module le dit."""

    def test_l_unanimite_est_un_regime_reconnu(self):
        # Mesure d'origine: zero occurrence de "unanim" dans le module, et
        # majorite="unanimite" ressortait ASSIETTE_INDETERMINEE.
        self.assertIsNotNone(D.regime_de_majorite("unanimite"))

    def test_les_deux_tiers_ne_suffisent_pas_a_l_unanimite(self):
        verdict = D.decompte_resolution(
            majorite="unanimite", voix_pour=7000, voix_totales=A_TOTALES
        )
        self.assertNotEqual(verdict.etat, D.ETAT_ADOPTEE_CONFIRMEE)
        self.assertEqual(verdict.seuil_requis, A_TOTALES)

    def test_la_totalite_des_voix_confirme_l_adoption(self):
        verdict = D.decompte_resolution(
            majorite="unanimite",
            voix_pour=A_TOTALES,
            voix_totales=A_TOTALES,
            issue_annoncee="Adoptee",
        )
        self.assertEqual(verdict.etat, D.ETAT_ADOPTEE_CONFIRMEE)
        self.assertEqual(verdict.pourcentage, 100.0)

    def test_une_confirmation_a_l_article_26_dit_ce_qu_elle_ne_verifie_pas(self):
        # L'article 26 dernier alinea reserve certains objets a l'unanimite. Le
        # module ne lit pas l'objet: il doit le dire plutot que de laisser
        # croire que les deux tiers repondent a toute la question.
        verdict = D.decompte_resolution(
            majorite="26",
            voix_pour=7000,
            voix_totales=A_TOTALES,
            nombre_membres=10,
            nombre_votants_pour=7,
        )
        self.assertEqual(verdict.etat, D.ETAT_ADOPTEE_CONFIRMEE)
        self.assertTrue(
            any("unanimite" in c for c in verdict.constats), verdict.constats
        )


class LaPorteeReelleEstEcriteDansLeModule(unittest.TestCase):
    """Ce que le pont passe reellement, et ce qu'il ne passe pas.

    Le seul consommateur de production, `_pont_actes_lignes._decompte`, passe
    cinq parametres sur quatorze. Le module ne peut pas y remedier seul, mais il
    ne doit pas laisser croire que ses controles s'exercent sur des donnees
    reelles: la limite est ecrite dans sa docstring, et ce test la verrouille.
    """

    def test_la_docstring_du_module_declare_les_parametres_non_cables(self):
        texte = D.__doc__ or ""
        self.assertIn("cinq parametres", texte)
        for parametre in ("voix_totales", "voix_presentes", "issue_annoncee"):
            with self.subTest(parametre=parametre):
                self.assertIn(parametre, texte)

    def test_majorite_25_atteignable_declare_n_avoir_aucun_appelant(self):
        texte = D.majorite_25_atteignable.__doc__ or ""
        self.assertIn("aucun appelant", texte)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
