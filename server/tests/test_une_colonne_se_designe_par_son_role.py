# -*- coding: utf-8 -*-
"""Une colonne d'annexe se designe par son role, jamais par sa position.

Constat `C037` de `RM-2026-0086`. Sa formulation d'origine - *le total est pris
dans la derniere colonne, donc souvent un budget a venir au lieu du realise* -
avait ete instruite le 2026-09-10 et jugee douteuse: le seul consommateur de ce
champ **veut** un budget.

**Ce que la mesure sur les DEUX cabinets a trouve a la place, et c'est pire.**
Sur 39 documents d'annexe, `lire_annexe` rendait un total dans **16 documents ou
aucune colonne n'etait identifiee** - la derniere valeur d'une suite de 1, 2, 4
ou 8 nombres sans nom. Chez le second cabinet, c'etait le cas de TOUS les
documents portant un total. Trois autres annoncaient dix colonnes pour cinq
totaux. Le defaut n'est donc pas *on prend la mauvaise colonne*, c'est **on elit
une valeur dans une liste dont on ignore la structure**.

**L'axe.** Ce qui varie: la formulation et la mise en page de l'entete. Ce qui
reste invariant: un entete situe la colonne sur **deux dimensions
independantes** - la nature du montant (constate ou prevu) et son statut dans la
seance (deja arrete ou soumis maintenant). Une enumeration de cinq libelles
casse au sixieme; deux axes binaires rendent `inconnu` sur la dimension qu'ils
n'ont pas lue.

**Ce que ces tests ne demandent jamais:** qu'une colonne soit devinee. Un role
incomplet n'est pas elu, deux colonnes de meme role ne sont pas departagees, et
une ligne de total qui ne correspond a aucune structure ne produit aucun total.
"""

from __future__ import annotations

import unittest
from decimal import Decimal

from coproscope.modules._comptes_extraction_annexe import lire_annexe
from coproscope.modules._comptes_extraction_modele import (
    STRUCTURE_DE_COLONNES_INCONNUE,
    ColonneAnnexe,
)
from coproscope.modules._comptes_extraction_roles import (
    ARRETE,
    BUDGET,
    NATURE_INCONNUE,
    REALISE,
    SOUMIS,
    STATUT_INCONNU,
    colonne_du_role,
    entetes_de_colonnes,
    role_de_l_entete,
)

#: Le bloc d'entetes tel que le premier cabinet et la fixture du depot
#: l'ecrivent: libelles coupes par le retour a la ligne, puis les millesimes.
ENTETES_MILLESIMES = """Exercice
precedent
approuve
Exercice clos
budget vote
Exercice clos
realise a
approuver
Budget
previsionnel en
cours vote
Budget
previsionnel a
voter
2028
2029
2029
2030
2031""".splitlines()

#: Le meme bloc, mais avec les reperes RELATIFS du modele reglementaire. C'est
#: la forme du second cabinet: `N`, `N + 1`, `N + 2`, `N - 1`.
ENTETES_RELATIFS = """Exercice clos
realise a
approuver
Budget
previsionnel a
voter
N
N + 2""".splitlines()


class LES_DEUX_AXES_SE_LISENT_SEPAREMENT(unittest.TestCase):
    """Nature et statut ne dependent pas l'un de l'autre."""

    def test_les_quatre_combinaisons_existent_et_se_lisent(self) -> None:
        attendus = {
            "Exercice clos budget vote": (BUDGET, ARRETE),
            "Exercice clos realise a approuver": (REALISE, SOUMIS),
            "Budget previsionnel a voter": (BUDGET, SOUMIS),
            "Compte de gestion realise approuve": (REALISE, ARRETE),
        }
        for entete, (nature, statut) in attendus.items():
            with self.subTest(entete=entete):
                role = role_de_l_entete(entete)
                self.assertEqual(nature, role.nature)
                self.assertEqual(statut, role.statut)
                self.assertTrue(role.complet)

    def test_le_SOUMIS_l_emporte_sur_l_ARRETE_et_ce_n_est_pas_arbitraire(self) -> None:
        """`a approuver` CONTIENT `approuver`, et `budget vote` contient `vote`.

        Se tromper de sens ici transforme un montant soumis au vote de ce soir
        en un montant deja acquis - c'est-a-dire l'inverse de ce que la piece
        dit.
        """
        self.assertEqual(SOUMIS, role_de_l_entete("Exercice clos realise a approuver").statut)
        self.assertEqual(ARRETE, role_de_l_entete("Exercice precedent approuve").statut)

    def test_l_accent_et_la_casse_ne_changent_rien(self) -> None:
        for ecriture in ("EXERCICE CLOS RÉALISÉ À APPROUVER",
                         "exercice clos réalisé à approuver",
                         "Exercice  clos   realise a approuver"):
            with self.subTest(ecriture=ecriture):
                role = role_de_l_entete(ecriture)
                self.assertEqual((REALISE, SOUMIS), (role.nature, role.statut))


class HORS_DES_VALEURS_OBSERVEES_LE_ROLE_SE_DECLARE_INCOMPLET(unittest.TestCase):
    """Le temoin de sante: le critere doit savoir dire *je n'ai pas lu*."""

    def test_une_nature_non_ecrite_donne_NATURE_INCONNUE(self) -> None:
        """`Exercice precedent approuve` ne dit pas s'il s'agit d'un realise.

        C'est le cas reel de la premiere colonne des deux corpus. Le module ne
        le range pas d'office parmi les realises: il le declare.
        """
        role = role_de_l_entete("Exercice precedent approuve")
        self.assertEqual(NATURE_INCONNUE, role.nature)
        self.assertFalse(role.complet)

    def test_un_mot_inconnu_ne_fabrique_aucun_role(self) -> None:
        role = role_de_l_entete("Colonne estimative provisoire")
        self.assertEqual(NATURE_INCONNUE, role.nature)
        self.assertEqual(STATUT_INCONNU, role.statut)
        self.assertFalse(role.complet)

    def test_un_entete_vide_ne_leve_pas_et_ne_conclut_pas(self) -> None:
        for vide in ("", "   ", None):
            with self.subTest(vide=vide):
                role = role_de_l_entete(vide)
                self.assertFalse(role.complet)


class UN_REPERE_D_EXERCICE_A_DEUX_FORMES_ET_UN_SEUL_AXE(unittest.TestCase):
    """Millesime absolu ou repere relatif: c'est la meme dimension.

    Mesure du 2026-09-10: un localisateur limite aux millesimes trouvait **zero
    bloc d'entete** chez le second cabinet, qui ecrit `N`, `N + 1`, `N + 2`.
    Vingt-huit une fois les reperes relatifs admis. Coder la seule forme vue
    chez le premier cabinet aurait rendu ce lecteur aveugle a tout un cabinet.
    """

    def test_la_forme_absolue_est_lue(self) -> None:
        self.assertEqual(5, len(entetes_de_colonnes(ENTETES_MILLESIMES)))

    def test_la_forme_RELATIVE_est_lue_aussi(self) -> None:
        entetes = entetes_de_colonnes(ENTETES_RELATIFS)
        self.assertEqual(2, len(entetes))
        roles = [role_de_l_entete(e) for e in entetes]
        self.assertEqual([(REALISE, SOUMIS), (BUDGET, SOUMIS)],
                         [(r.nature, r.statut) for r in roles])


class LE_DECOUPAGE_REFUSE_PLUTOT_QUE_DE_DEVINER(unittest.TestCase):
    """Autant d'entetes que de colonnes, ou rien."""

    def test_un_bloc_concordant_rend_ses_entetes(self) -> None:
        self.assertEqual(
            ["Exercice precedent approuve", "Exercice clos budget vote",
             "Exercice clos realise a approuver",
             "Budget previsionnel en cours vote", "Budget previsionnel a voter"],
            entetes_de_colonnes(ENTETES_MILLESIMES))

    def test_un_bloc_NON_concordant_rend_une_liste_VIDE(self) -> None:
        """Trois entetes pour cinq colonnes ne disent pas ou passe la frontiere."""
        boiteux = """Exercice clos
budget vote
Exercice clos
realise a
approuver
2028
2029
2029
2030
2031""".splitlines()
        self.assertEqual([], entetes_de_colonnes(boiteux))

    def test_un_seul_repere_ne_fait_pas_un_tableau(self) -> None:
        self.assertEqual([], entetes_de_colonnes(["Exercice clos realise", "2029"]))


class UNE_DEMANDE_QUI_NE_DESIGNE_PAS_UNE_SEULE_COLONNE_N_EST_PAS_SATISFAITE(
        unittest.TestCase):
    """Trois refus qui se valent, et le deuxieme n'est pas un detail."""

    def setUp(self) -> None:
        entetes = entetes_de_colonnes(ENTETES_MILLESIMES)
        self.colonnes = [ColonneAnnexe(exercice="", intitule=e, role=role_de_l_entete(e))
                         for e in entetes]

    def test_un_role_unique_est_designe(self) -> None:
        self.assertEqual(4, colonne_du_role(self.colonnes, BUDGET, SOUMIS))
        self.assertEqual(2, colonne_du_role(self.colonnes, REALISE, SOUMIS))

    def test_DEUX_colonnes_de_meme_role_ne_sont_pas_departagees(self) -> None:
        """Un entete repete par l'aplatissement porte deux fois chaque colonne.

        Prendre la premiere ou la derniere serait de nouveau une election par
        position - le defaut meme que ce lot corrige.
        """
        self.assertIsNone(colonne_du_role(self.colonnes, BUDGET, ARRETE))

    def test_un_role_absent_rend_None(self) -> None:
        self.assertIsNone(colonne_du_role(self.colonnes, REALISE, ARRETE))

    def test_un_role_INCOMPLET_n_est_jamais_elu(self) -> None:
        self.assertIsNone(colonne_du_role(self.colonnes, NATURE_INCONNUE, ARRETE))


class AUCUN_TOTAL_N_EST_ELU_DANS_UNE_LISTE_SANS_STRUCTURE(unittest.TestCase):
    """Le coeur de `C037`, mesure sur 39 documents des deux cabinets."""

    CONCORDANTE = """===== PAGE 1 =====
Exercice clos
realise a
approuver
Budget
previsionnel a
voter
2029
2030
ANNEXE N° 3
Compte de gestion pour operations courantes du 01/01/2029 au 31/12/2029
TOTAL CHARGES NETTES
1 050,00
1 300,00
"""

    SANS_ENTETE = """===== PAGE 1 =====
ANNEXE N° 3
Compte de gestion pour operations courantes du 01/01/2029 au 31/12/2029
TOTAL CHARGES NETTES
1 050,00
1 300,00
"""

    def test_une_annexe_concordante_elit_et_porte_ses_roles(self) -> None:
        annexe = lire_annexe(self.CONCORDANTE)
        self.assertEqual(2, len(annexe.colonnes))
        self.assertEqual(Decimal("1300.00"), annexe.total_charges)
        self.assertEqual([(REALISE, SOUMIS), (BUDGET, SOUMIS)],
                         [(c.role.nature, c.role.statut) for c in annexe.colonnes])

    def test_sans_entete_de_colonnes_AUCUN_total_n_est_elu(self) -> None:
        """C'est le cas de 16 documents sur 39 dans les deux corpus mesures."""
        annexe = lire_annexe(self.SANS_ENTETE)
        self.assertEqual(0, len(annexe.colonnes))
        self.assertGreater(len(annexe.total_charges_par_colonne), 0,
                           "des nombres sont bien lus: c'est ce qui rendait le piege credible")
        self.assertIsNone(annexe.total_charges)

    def test_et_le_refus_SE_DIT_au_lieu_de_se_taire(self) -> None:
        annexe = lire_annexe(self.SANS_ENTETE)
        codes = [c.code for c in annexe.constats]
        self.assertIn(STRUCTURE_DE_COLONNES_INCONNUE, codes)
        message = next(c.message for c in annexe.constats
                       if c.code == STRUCTURE_DE_COLONNES_INCONNUE)
        self.assertIn("2 nombre(s)", message)
        self.assertIn("0 colonne(s)", message)

    def test_une_annexe_sans_aucun_nombre_ne_declare_pas_de_refus(self) -> None:
        """Rien a elire n'est pas la meme chose qu'un refus d'elire.

        Un constat publie sur une annexe qui ne porte aucun total ferait crier
        la garde en permanence, et une garde qui crie toujours finit ignoree.
        """
        annexe = lire_annexe("===== PAGE 1 =====\nANNEXE N° 3\nRien ici, 1 000,00 est un poste\n")
        self.assertIsNone(annexe.total_charges)
        self.assertNotIn(STRUCTURE_DE_COLONNES_INCONNUE,
                         [c.code for c in annexe.constats])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
