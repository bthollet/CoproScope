from __future__ import annotations

import unittest
from datetime import date

from coproscope.modules import _budget_previsionnel_controles as C
from coproscope.modules import budget_previsionnel as B


def ligne(compte: str, montant: float | None = 100.0, libelle: str = "") -> B.LigneBudget:
    return B.LigneBudget(compte_brut=compte, libelle=libelle, montant=montant)


def dossier(**kw) -> B.Dossier:
    return B.Dossier(**kw)


class NomenclatureTests(unittest.TestCase):
    """L'axe: le numero fait foi, jamais le libelle ni la mise en forme."""

    def test_numero_nu_reconnu(self) -> None:
        self.assertEqual(B.normaliser("601"), "601")
        self.assertEqual(B.normaliser("450-1"), "450-1")

    def test_remplissage_a_quatre_chiffres_des_deux_cabinets(self) -> None:
        # Un cabinet ecrit 4501, 5010, 1050, 1210 pour 450-1, 501, 105, 12-1.
        self.assertEqual(B.normaliser("4501"), "450-1")
        self.assertEqual(B.normaliser("5010"), "501")
        self.assertEqual(B.normaliser("1050"), "105")
        self.assertEqual(B.normaliser("1210"), "12-1")

    def test_libelle_du_cabinet_ne_change_rien(self) -> None:
        # 613 est "Locations mobilieres" au texte, "Locations compteurs" chez
        # un cabinet: le controle ne doit pas voir la difference.
        self.assertEqual(B.normaliser("613"), B.normaliser("613"))
        constat_a = C.b2_nomenclature(
            dossier(budget=B.BudgetPrevisionnel(lignes=(ligne("613", 10, "Locations mobilieres"),)))
        )
        constat_b = C.b2_nomenclature(
            dossier(budget=B.BudgetPrevisionnel(lignes=(ligne("613", 10, "Locations compteurs"),)))
        )
        self.assertEqual(constat_a.statut, constat_b.statut)

    def test_agregats_de_presentation(self) -> None:
        # "60x", "62... (autres que 621 et 622)" et "671-673" ne sont pas des
        # comptes: ce sont des regroupements imprimes par un cabinet.
        self.assertEqual(B.normaliser("60x"), "60")
        self.assertEqual(B.normaliser("62... Autres"), "62")
        self.assertEqual(B.normaliser("671-673 Travaux"), "671")

    def test_subdivision_licite_rattachee_et_non_signalee(self) -> None:
        # L'article 8 de l'arrete autorise toute subdivision necessaire.
        self.assertEqual(B.normaliser("61503"), "615")
        self.assertEqual(B.rattacher("61503"), "615")

    def test_numero_sans_rattachement_rendu_none(self) -> None:
        self.assertIsNone(B.normaliser("Total general"))
        self.assertIsNone(B.normaliser(""))
        self.assertIsNone(B.normaliser(None))

    def test_compte_supprime_reste_visible(self) -> None:
        # 1032 est "(Supprime)" dans la version en vigueur. Le rattachement par
        # prefixe le ferait disparaitre sous 103: il doit rester identifiable.
        self.assertEqual(B.normaliser("1032"), "1032")
        self.assertIn("1032", B.COMPTES_SUPPRIMES)


class PerimetreTests(unittest.TestCase):
    def test_b1_signale_les_charges_de_travaux_au_budget(self) -> None:
        d = dossier(budget=B.BudgetPrevisionnel(lignes=(ligne("601"), ligne("671", 5000.0))))
        constat = C.b1_perimetre_article_44(d)
        self.assertEqual(constat.statut, B.ECART)
        self.assertIn("671", constat.message)

    def test_b1_ignore_une_ligne_de_classe_67_a_zero(self) -> None:
        d = dossier(budget=B.BudgetPrevisionnel(lignes=(ligne("601"), ligne("671", 0.0))))
        constat = C.b1_perimetre_article_44(d)
        self.assertEqual(constat.statut, B.CONFORME)

    def test_b1_ne_tranche_pas_la_classe_66(self) -> None:
        # Les deux cabinets rangent 66 differemment et le modele d'annexe 2
        # n'est pas reproduit sur Legifrance: on ne decide pas a sa place.
        d = dossier(budget=B.BudgetPrevisionnel(lignes=(ligne("662", 300.0),)))
        constat = C.b1_perimetre_article_44(d)
        self.assertEqual(constat.statut, B.A_VERIFIER_HUMAIN)

    def test_b1_sans_montant_lu_ne_conclut_pas(self) -> None:
        # Des comptes lus sans leurs montants ne prouvent pas un perimetre
        # propre: ils prouvent qu'on n'a pas lu la colonne du budget.
        d = dossier(budget=B.BudgetPrevisionnel(lignes=(ligne("601", None), ligne("671", None))))
        constat = C.b1_perimetre_article_44(d)
        self.assertEqual(constat.statut, B.INAPPLICABLE)
        self.assertIn("budget.lignes[].montant", constat.entrees_manquantes)

    def test_b1_dit_ce_qu_il_ne_prouve_pas(self) -> None:
        d = dossier(budget=B.BudgetPrevisionnel(lignes=(ligne("615"),)))
        constat = C.b1_perimetre_article_44(d)
        self.assertIn("615", constat.ne_prouve_pas)

    def test_b3_signale_le_compte_supprime(self) -> None:
        d = dossier(budget=B.BudgetPrevisionnel(lignes=(ligne("1032", 50.0),)))
        constat = C.b3_compte_supprime(d)
        self.assertEqual(constat.statut, B.ECART)


class EgaliteAnnexesTests(unittest.TestCase):
    def test_b4_egalite_respectee(self) -> None:
        d = dossier(
            annexes=B.Annexes(
                total_charges_annexe2_courantes=303500.0,
                total_charges_annexe3_courantes=303500.0,
            )
        )
        self.assertEqual(C.b4_egalite_annexes(d).statut, B.CONFORME)

    def test_b4_ecart_chiffre(self) -> None:
        d = dossier(
            annexes=B.Annexes(
                total_charges_annexe2_courantes=303500.0,
                total_charges_annexe3_courantes=303000.0,
            )
        )
        constat = C.b4_egalite_annexes(d)
        self.assertEqual(constat.statut, B.ECART)
        self.assertIn("500.00", constat.message)

    def test_b4_ne_parle_pas_de_l_annexe_4(self) -> None:
        d = dossier(annexes=B.Annexes())
        constat = C.b4_egalite_annexes(d)
        self.assertIn("annexe 4", constat.ne_prouve_pas)


class FondsTravauxTests(unittest.TestCase):
    BASE = dict(
        destination_habitation=True,
        date_reception_travaux_construction=date(1980, 1, 1),
        plan_pluriannuel_adopte=False,
    )

    def _dossier(self, cotisation: float, budget: float = 300000.0, **kw) -> B.Dossier:
        champs = dict(self.BASE, cotisation_fonds_travaux_votee=cotisation, **kw)
        return dossier(
            budget=B.BudgetPrevisionnel(
                exercice_debut=date(2027, 1, 1), exercice_fin=date(2027, 12, 31),
                total_charges=budget,
            ),
            copropriete=B.Copropriete(**champs),
        )

    def test_b5_plancher_de_cinq_pour_cent(self) -> None:
        constat = C.b5_plancher_fonds_travaux(
            self._dossier(15000.0)
        )
        self.assertEqual(constat.statut, B.CONFORME)

    def test_b5_cotisation_insuffisante(self) -> None:
        constat = C.b5_plancher_fonds_travaux(
            self._dossier(10000.0)
        )
        self.assertEqual(constat.statut, B.ECART)

    def test_b5_second_plancher_si_plan_adopte(self) -> None:
        # 5 % de 300 000 = 15 000, mais 2,5 % d'un plan de 1 800 000 = 45 000.
        constat = C.b5_plancher_fonds_travaux(
            self._dossier(
                15000.0, plan_pluriannuel_adopte=True, montant_travaux_plan_adopte=1800000.0
            )
        )
        self.assertEqual(constat.statut, B.ECART)
        self.assertIn("2,5 %", constat.message)

    def test_b5_inapplicable_avant_le_terme_de_dix_ans(self) -> None:
        constat = C.b5_plancher_fonds_travaux(
            self._dossier(0.0, date_reception_travaux_construction=date(2020, 6, 1))
        )
        self.assertEqual(constat.statut, B.INAPPLICABLE)
        self.assertIn("copropriete.date_reception_travaux_construction", constat.entrees_manquantes)

    def test_b5_inapplicable_sans_date_de_reception(self) -> None:
        d = dossier(
            budget=B.BudgetPrevisionnel(total_charges=300000.0),
            copropriete=B.Copropriete(
                destination_habitation=True,
                cotisation_fonds_travaux_votee=1.0,
                plan_pluriannuel_adopte=False,
            ),
        )
        constat = C.b5_plancher_fonds_travaux(d)
        self.assertEqual(constat.statut, B.INAPPLICABLE)


class ProcedureTests(unittest.TestCase):
    def test_p1_vote_avant_exercice(self) -> None:
        d = dossier(
            budget=B.BudgetPrevisionnel(exercice_debut=date(2027, 1, 1)),
            vote=B.Vote(date_assemblee=date(2026, 6, 29)),
        )
        self.assertEqual(C.p1_vote_avant_exercice(d).statut, B.CONFORME)

    def test_p1_vote_tardif_n_est_pas_un_manquement(self) -> None:
        # L'alinea 2 de l'article 43 organise le vote en cours d'exercice: le
        # constat isole aiguille vers P-2, il ne conclut pas.
        d = dossier(
            budget=B.BudgetPrevisionnel(exercice_debut=date(2026, 1, 1)),
            vote=B.Vote(date_assemblee=date(2026, 6, 29)),
        )
        constat = C.p1_vote_avant_exercice(d)
        self.assertEqual(constat.statut, B.A_VERIFIER_HUMAIN)
        self.assertIn("P-2", constat.message)

    def test_p2_regime_transitoire_respecte(self) -> None:
        d = dossier(
            budget=B.BudgetPrevisionnel(exercice_debut=date(2026, 1, 1)),
            vote=B.Vote(
                date_assemblee=date(2026, 6, 29),
                autorisation_provisions_transitoires=True,
                provisions_transitoires_appelees=2,
                assiette_provisions_transitoires=75000.0,
                budget_precedent_vote=300000.0,
            ),
        )
        self.assertEqual(C.p2_provisions_transitoires(d).statut, B.CONFORME)

    def test_p2_trois_provisions_et_mauvaise_assiette(self) -> None:
        d = dossier(
            budget=B.BudgetPrevisionnel(exercice_debut=date(2026, 1, 1)),
            vote=B.Vote(
                date_assemblee=date(2026, 6, 29),
                autorisation_provisions_transitoires=False,
                provisions_transitoires_appelees=3,
                assiette_provisions_transitoires=80000.0,
                budget_precedent_vote=300000.0,
            ),
        )
        constat = C.p2_provisions_transitoires(d)
        self.assertEqual(constat.statut, B.ECART)
        self.assertIn("autorisation", constat.message)
        self.assertIn("deux au plus", constat.message)

    def test_p3_douze_mois(self) -> None:
        d = dossier(
            budget=B.BudgetPrevisionnel(
                exercice_debut=date(2027, 1, 1), exercice_fin=date(2027, 12, 31)
            )
        )
        self.assertEqual(C.p3_duree_exercice(d).statut, B.CONFORME)

    def test_p3_duree_atypique_hors_premier_exercice(self) -> None:
        d = dossier(
            budget=B.BudgetPrevisionnel(
                exercice_debut=date(2027, 1, 1), exercice_fin=date(2028, 3, 31)
            ),
            copropriete=B.Copropriete(premier_exercice=False),
        )
        self.assertEqual(C.p3_duree_exercice(d).statut, B.ECART)

    def test_p3_premier_exercice_de_dix_huit_mois_admis(self) -> None:
        d = dossier(
            budget=B.BudgetPrevisionnel(
                exercice_debut=date(2027, 1, 1), exercice_fin=date(2028, 6, 30)
            ),
            copropriete=B.Copropriete(premier_exercice=True),
        )
        self.assertEqual(C.p3_duree_exercice(d).statut, B.CONFORME)

    def test_p3_premier_exercice_trop_long(self) -> None:
        d = dossier(
            budget=B.BudgetPrevisionnel(
                exercice_debut=date(2027, 1, 1), exercice_fin=date(2028, 12, 31)
            ),
            copropriete=B.Copropriete(premier_exercice=True),
        )
        self.assertEqual(C.p3_duree_exercice(d).statut, B.ECART)

    def test_p4_delai_depasse(self) -> None:
        d = dossier(
            vote=B.Vote(date_assemblee=date(2026, 9, 30)),
            copropriete=B.Copropriete(cloture_exercice_precedent=date(2025, 12, 31)),
        )
        self.assertEqual(C.p4_delai_six_mois(d).statut, B.ECART)

    def test_p5_comparatif_est_previsionnel_contre_previsionnel(self) -> None:
        d = dossier(
            convocation=B.Convocation(
                projet_budget_notifie=True, comparatif_dernier_budget_vote_notifie=False
            ),
            copropriete=B.Copropriete(premier_exercice=False),
        )
        constat = C.p5_comparatif_dernier_budget(d)
        self.assertEqual(constat.statut, B.ECART)
        self.assertIn("realise", constat.ne_prouve_pas)

    def test_p5_ne_choisit_pas_entre_piece_absente_et_premiere_annee(self) -> None:
        d = dossier(
            convocation=B.Convocation(
                projet_budget_notifie=True, comparatif_dernier_budget_vote_notifie=False
            )
        )
        constat = C.p5_comparatif_dernier_budget(d)
        self.assertEqual(constat.statut, B.INAPPLICABLE)
        self.assertIn("copropriete.premier_exercice", constat.entrees_manquantes)

    def test_p3_duree_atypique_sans_rang_d_exercice(self) -> None:
        d = dossier(
            budget=B.BudgetPrevisionnel(
                exercice_debut=date(2027, 1, 1), exercice_fin=date(2028, 3, 31)
            )
        )
        constat = C.p3_duree_exercice(d)
        self.assertEqual(constat.statut, B.INAPPLICABLE)
        self.assertIn("copropriete.premier_exercice", constat.entrees_manquantes)

    def test_p7_majorite_hors_article_24(self) -> None:
        d = dossier(vote=B.Vote(article_majorite="25"))
        self.assertEqual(C.p7_majorite(d).statut, B.ECART)

    def test_p7_variantes_d_ecriture_de_l_article_24(self) -> None:
        for ecriture in ("24", " 24 ", "Article 24", "article24"):
            d = dossier(vote=B.Vote(article_majorite=ecriture))
            with self.subTest(ecriture=ecriture):
                self.assertEqual(
                    C.p7_majorite(d).statut, B.CONFORME
                )

    def test_p8_ne_conclut_jamais_a_un_manquement(self) -> None:
        d = dossier(copropriete=B.Copropriete(concertation_conseil_syndical_tracee=False))
        constat = C.p8_concertation(d)
        self.assertEqual(constat.statut, B.A_VERIFIER_HUMAIN)


class PremiereAnneeTests(unittest.TestCase):
    """Un budget N ne se compare pas a un budget N-1 qui n'existe pas."""

    def test_p5_inapplicable_au_premier_budget(self) -> None:
        d = dossier(
            convocation=B.Convocation(
                projet_budget_notifie=True, comparatif_dernier_budget_vote_notifie=False
            ),
            copropriete=B.Copropriete(premier_exercice=True),
        )
        constat = C.p5_comparatif_dernier_budget(d)
        self.assertEqual(constat.statut, B.INAPPLICABLE)
        self.assertIn("vote.budget_precedent_vote", constat.entrees_manquantes)

    def test_p4_inapplicable_au_premier_exercice(self) -> None:
        d = dossier(
            vote=B.Vote(date_assemblee=date(2027, 9, 30)),
            copropriete=B.Copropriete(premier_exercice=True),
        )
        self.assertEqual(
            C.p4_delai_six_mois(d).statut, B.INAPPLICABLE
        )


class ContratTests(unittest.TestCase):
    def test_dossier_vide_ne_rend_aucun_conforme(self) -> None:
        # Le piege a eviter: un dossier sans donnee ne doit pas ressembler a une
        # copropriete en regle.
        constats = B.evaluer(B.Dossier())
        repartition = B.repartition(constats)
        self.assertEqual(len(constats), 16)
        self.assertEqual(repartition[B.CONFORME], 0)
        self.assertEqual(repartition[B.ECART], 0)
        self.assertEqual(repartition[B.INAPPLICABLE], 16)

    def test_chaque_constat_cite_un_legiarti(self) -> None:
        for constat in B.evaluer(B.Dossier()):
            with self.subTest(controle=constat.controle):
                self.assertTrue(constat.legiartis)
                for identifiant in constat.legiartis:
                    self.assertTrue(identifiant.startswith("LEGIARTI"))

    def test_chaque_controle_dit_ce_qu_il_ne_prouve_pas(self) -> None:
        for constat in B.evaluer(B.Dossier()):
            with self.subTest(controle=constat.controle):
                self.assertTrue(constat.ne_prouve_pas.strip())

    def test_un_inapplicable_doit_nommer_ce_qui_manque(self) -> None:
        with self.assertRaises(ValueError):
            B.Constat(controle="X-1", statut=B.INAPPLICABLE, enonce="e", message="m")

    def test_statut_inconnu_refuse(self) -> None:
        with self.assertRaises(ValueError):
            B.Constat(controle="X-1", statut="PEUT_ETRE", enonce="e", message="m")

    def test_entrees_manquantes_classees_par_ce_qu_elles_debloquent(self) -> None:
        index = B.entrees_manquantes(B.evaluer(B.Dossier()))
        self.assertIn("budget.lignes", index)
        self.assertEqual(index["budget.lignes"], ("B-1", "B-2", "B-3"))

    def test_identifiants_de_controle_uniques_et_lettres(self) -> None:
        codes = [c.controle for c in B.evaluer(B.Dossier())]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(code[0] in "BP" and code[1] == "-" for code in codes))

    def test_source_inconnue_echoue_en_le_disant(self) -> None:
        with self.assertRaises(KeyError) as capture:
            B.source("loi.99")
        self.assertIn("Legifrance", str(capture.exception))


if __name__ == "__main__":
    unittest.main()
