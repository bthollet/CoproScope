"""Les montants ecrits a la francaise, de la chaine lue au plafond compare.

Constats couverts, audit du modele du 2026-09-04: C023 (`2.500` rendu 2,50),
C026 (aucune normalisation a l'ecriture), C033 et C036 (`CAST AS REAL` sur un
montant francais: 18 240,00 EUR devient 18), C059 (la file dite triee par
montant met le plus gros ecart en dernier), C098 (un montant illisible s'affiche
en cellule vide).

Chacun de ces tests echoue sur le code d'avant. Ils tiennent une seule
propriete: **un montant est lu juste, ou il est nomme illisible; jamais un
nombre plausible.**
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import actes_autorisation as A
from coproscope.modules._montants import (
    MontantIllisible,
    montant_decimal,
    montant_normalise,
    sql_reel,
    sql_taux,
    taux_normalise,
)
from coproscope.web._controle_gouvernance_source import euros

#: L'etalon de l'audit: le total des charges de l'exercice 2025, tel qu'il est
#: imprime sur l'annexe. Il traverse toute la chaine dans le dernier test.
ETALON_CHARGES = "357 493,10"


class LectureTests(unittest.TestCase):
    """Ce que la regle sait lire, et ce qu'elle refuse de deviner."""

    def test_le_montant_francais_garde_son_ordre_de_grandeur(self) -> None:
        """`18 240,00 EUR` vaut 18 240, pas 18. C036."""
        self.assertEqual(montant_normalise("18 240,00 EUR"), "18240.00")
        self.assertEqual(montant_normalise(ETALON_CHARGES), "357493.10")
        self.assertEqual(montant_normalise("2 000"), "2000.00")
        self.assertEqual(montant_normalise("1 200 000"), "1200000.00")

    def test_les_deux_conventions_de_separateur_sont_lues(self) -> None:
        """Le dernier separateur est le decimal, chez les deux cabinets."""
        self.assertEqual(montant_normalise("1.234,56"), "1234.56")
        self.assertEqual(montant_normalise("1,234.56"), "1234.56")
        self.assertEqual(montant_normalise("2.500,00"), "2500.00")
        self.assertEqual(montant_normalise("1.200.000,55"), "1200000.55")

    def test_un_point_de_milliers_seul_est_refuse_au_lieu_de_diviser(self) -> None:
        """C023: `2.500` rendait `2.50`, donc un plafond divise par mille."""
        for ecrit in ("2.500", "5.000", "10.000", "1.234"):
            with self.assertRaises(MontantIllisible) as capture:
                montant_normalise(ecrit)
            self.assertIn("trois chiffres", capture.exception.motif)

    def test_ce_qui_n_est_pas_un_montant_est_refuse_et_non_ramene_a_zero(self) -> None:
        """C026 et C036: `environ 2000` valait 0,00 EUR, `20%` valait 20."""
        for ecrit in ("environ 2000", "20%", "abc", "1.2.3", "1 20 0"):
            with self.assertRaises(MontantIllisible):
                montant_normalise(ecrit)

    def test_absent_et_illisible_ne_se_confondent_pas(self) -> None:
        self.assertEqual(montant_normalise(""), "")
        self.assertEqual(montant_normalise(None), "")
        self.assertEqual(montant_normalise("   "), "")
        with self.assertRaises(MontantIllisible):
            montant_normalise("non chiffre")

    def test_le_zero_ecrit_reste_un_zero_lu(self) -> None:
        """`0,00` est un fait, pas une absence."""
        self.assertEqual(montant_normalise("0,00"), "0.00")
        self.assertEqual(montant_decimal("0,00"), 0)
        self.assertIsNone(montant_decimal(""))

    def test_la_notation_comptable_du_signe_est_lue(self) -> None:
        self.assertEqual(montant_normalise("(1 200,00)"), "-1200.00")
        self.assertEqual(montant_normalise("-500,00"), "-500.00")

    def test_un_taux_a_virgule_n_est_pas_tronque(self) -> None:
        """`5,5 %` de T.V.A. valait 5 par le CAST, donc un ecart fabrique."""
        self.assertEqual(taux_normalise("5,5 %"), "5.50")
        self.assertEqual(taux_normalise("20"), "20.00")


class EcritureTests(unittest.TestCase):
    """La normalisation est imposee au point d'ecriture, pas esperee."""

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.racine, ignore_errors=True)
        self.instance = _Instance(self.racine)

    def test_un_montant_francais_ecrit_brut_est_stocke_normalise(self) -> None:
        """C026: la valeur brute partait en base et les vues rendaient 18,0."""
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("ACTE-1", montant_autorise="18 240,00 EUR")], ["DOC-PV"])
        (ligne,) = A.lire_table(self.instance, A.TABLE_ACTES)
        self.assertEqual(ligne["montant_autorise"], "18240.00")

    def test_un_montant_illisible_fait_echouer_l_ecriture_en_le_disant(self) -> None:
        """Le repli muet devient un fait nomme, avec sa colonne."""
        with self.assertRaises(MontantIllisible) as capture:
            A.ecrire(self.instance, A.TABLE_ACTES,
                     [_acte("ACTE-1", montant_autorise="environ 2 000")], ["DOC-PV"])
        self.assertIn("montant_autorise", capture.exception.motif)
        self.assertEqual(A.lire_table(self.instance, A.TABLE_ACTES), [])

    def test_la_depense_et_le_taux_de_tva_sont_normalises_aussi(self) -> None:
        A.ecrire(self.instance, A.TABLE_DOSSIERS,
                 [_dossier("DEP-1", montant_ttc="1 665,66",
                           taux_tva_annonce="10", tva_annoncee="277,61")],
                 ["DOC-FAC"])
        (ligne,) = A.lire_table(self.instance, A.TABLE_DOSSIERS)
        self.assertEqual(ligne["montant_ttc"], "1665.66")
        self.assertEqual(ligne["taux_tva_annonce"], "10.00")
        self.assertEqual(ligne["tva_annoncee"], "277.61")


class VuesTests(unittest.TestCase):
    """Ce que les vues comparent quand la base porte du texte non canonique."""

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.racine, ignore_errors=True)
        self.instance = _Instance(self.racine)

    def _forcer(self, table: str, colonne: str, valeur: str, cle: str) -> None:
        """Ecrit une valeur non canonique en contournant la normalisation.

        C'est le seul moyen de reproduire une base ecrite par une version
        anterieure, ou par une main. La ceinture doit tenir la aussi.
        """
        champ = {A.TABLE_ACTES: "acte_id", A.TABLE_DOSSIERS: "dossier_id"}[table]
        with A.connexion(self.instance) as cx, cx:
            cx.execute(
                f'UPDATE "{table}" SET "{colonne}" = ? WHERE "{champ}" = ?',
                (valeur, cle),
            )

    def test_un_montant_non_canonique_reste_non_lu_au_lieu_de_valoir_dix_huit(
        self,
    ) -> None:
        """C033 et C036: `CAST` rendait 18.0 sur `18 240,00 EUR`."""
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("ACTE-1", montant_autorise="18240.00")], ["DOC-PV"])
        self._forcer(A.TABLE_ACTES, "montant_autorise", "18 240,00 EUR", "ACTE-1")
        (ligne,) = A.lire_vue(self.instance, "v_execution")
        self.assertIsNone(ligne["montant_autorise"])

    def test_un_montant_non_chiffre_ne_compte_plus_comme_acte_quantifie(self) -> None:
        """C033, second volet: `non chiffre` valait 0,0, donc IS NOT NULL.

        Trois actes etaient annonces "quantifies" pour un seul montant
        reellement lisible. Le taux de gouvernance mesurait alors la presence
        d'une chaine, pas celle d'un montant.
        """
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("ACTE-1", montant_autorise="18240.00", entreprise="WE GROUP"),
            _acte("ACTE-2", numero="13", montant_autorise="", entreprise="WE GROUP"),
        ], ["DOC-PV"])
        self._forcer(A.TABLE_ACTES, "montant_autorise", "non chiffre", "ACTE-2")
        (taux,) = A.lire_vue(self.instance, "v_taux_gouvernance")
        self.assertEqual((taux["actes"], taux["actes_quantifies"]), (2, 1))

    def test_le_plafond_de_l_article_21_2_se_declenche_sur_un_millier(self) -> None:
        """Un seuil de 1 000 EUR contre une depense de 18 240,00 EUR."""
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("DELEG", portee="DELEGATION_CS", montant_autorise="1 000,00 EUR",
                  date_effet="2024-01-15", valide_du="2024-01-15",
                  valide_au="2026-01-14", numero="", resultat=""),
            _acte("DECISION", nature="DECISION_CS_DELEGUEE", portee="ENGAGEMENT_DEPENSE",
                  date_effet="2024-09-01", numero="", resultat=""),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_DOSSIERS,
                 [_dossier("DEP-1", montant_ttc="18 240,00 EUR",
                           date_depense="2024-09-15")], ["DOC-FAC"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("DECISION", "FONDE_PAR", "DELEG", target_kind="acte"),
            _lien("DECISION", "AUTORISE", "DEP-1"),
        ], ["DOC-FAC"])
        (cumul,) = A.lire_vue(self.instance, "v_cumul_delegation")
        self.assertEqual(cumul["plafond"], 1000.0)
        self.assertEqual(cumul["cumul"], 18240.0)
        codes = [c["code"] for c in A.lire_vue(self.instance, "v_constats")]
        self.assertIn("PLAFOND_DEPASSE", codes)

    def test_un_plafond_franchi_ne_passe_plus_pour_un_ecran_vert(self) -> None:
        """Le faux negatif silencieux, celui qu'aucun ecran ne pouvait trahir.

        Plafond 800,00 EUR, une seule depense de 2 000,00 EUR. Avant, le
        `CAST` rendait 800,0 pour le plafond (pas de blanc a couper) et 2,0
        pour la depense (blanc de milliers): 2 < 800, aucun constat, et
        l'ecran affichait "Le plafond n'est pas atteint" sur une delegation
        franchie du double et demi.
        """
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("DELEG", portee="DELEGATION_CS", montant_autorise="800,00 EUR",
                  date_effet="2024-01-15", valide_du="2024-01-15",
                  valide_au="2026-01-14", numero="", resultat=""),
            _acte("DECISION", nature="DECISION_CS_DELEGUEE",
                  portee="ENGAGEMENT_DEPENSE", date_effet="2024-09-01",
                  numero="", resultat=""),
        ], ["DOC-PV"])
        A.ecrire(self.instance, A.TABLE_DOSSIERS,
                 [_dossier("DEP-1", montant_ttc="2 000,00 EUR",
                           date_depense="2024-09-15")], ["DOC-FAC"])
        A.ecrire(self.instance, A.TABLE_LIENS, [
            _lien("DECISION", "FONDE_PAR", "DELEG", target_kind="acte"),
            _lien("DECISION", "AUTORISE", "DEP-1"),
        ], ["DOC-FAC"])
        (cumul,) = A.lire_vue(self.instance, "v_cumul_delegation")
        self.assertEqual((cumul["plafond"], cumul["cumul"]), (800.0, 2000.0))
        codes = [c["code"] for c in A.lire_vue(self.instance, "v_constats")]
        self.assertIn("PLAFOND_DEPASSE", codes)

class BaseHeriteeTests(unittest.TestCase):
    """La ceinture sur la chaine reelle, pas seulement en SQL de laboratoire."""

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.racine, ignore_errors=True)
        self.instance = _Instance(self.racine)

    def _forcer(self, table: str, colonne: str, valeur: str, cle: str) -> None:
        champ = {A.TABLE_ACTES: "acte_id", A.TABLE_DOSSIERS: "dossier_id"}[table]
        with A.connexion(self.instance) as cx, cx:
            cx.execute(
                f'UPDATE "{table}" SET "{colonne}" = ? WHERE "{champ}" = ?',
                (valeur, cle),
            )

    def test_un_montant_a_blanc_de_milliers_ne_vaut_pas_son_premier_groupe(
        self,
    ) -> None:
        """`18 240.00` en base rendait 18.0 dans `v_execution`, sans un mot."""
        for herite in ("18 240.00", "357 493.10"):
            with self.subTest(herite=herite):
                racine = Path(tempfile.mkdtemp())
                self.addCleanup(shutil.rmtree, racine, ignore_errors=True)
                instance = _Instance(racine)
                A.ecrire(instance, A.TABLE_ACTES,
                         [_acte("ACTE-1", montant_autorise="18240.00")], ["DOC-PV"])
                champ = "acte_id"
                with A.connexion(instance) as cx, cx:
                    cx.execute(
                        f'UPDATE "{A.TABLE_ACTES}" SET "montant_autorise" = ? '
                        f'WHERE "{champ}" = ?', (herite, "ACTE-1"))
                (ligne,) = A.lire_vue(instance, "v_execution")
                self.assertIsNone(ligne["montant_autorise"])

    def test_un_taux_entier_ne_desarme_plus_le_controle_de_tva(self) -> None:
        """Regression du lot montants: le constat s'eteignait sans rien dire.

        Base non migree, `taux_tva_annonce = '10'`. Avant le lot: 151.45
        attendus contre 151.42 comptabilises, TVA_INCOHERENTE emis. Apres le
        lot et avant ce correctif: `tva_attendue` NULL, donc le `WHERE` du
        constat ne retenait plus rien - un controle qui marchait, eteint sans
        exception, sans compteur et sans mention a l'ecran.
        """
        A.ecrire(self.instance, A.TABLE_DOSSIERS, [
            _dossier("D-1", montant_ttc="1666.00", tva_annoncee="151.42",
                     taux_tva_annonce="10.00", tva_regime="NORMAL"),
        ], ["DOC-FAC"])
        self._forcer(A.TABLE_DOSSIERS, "taux_tva_annonce", "10", "D-1")
        (ligne,) = A.lire_vue(self.instance, "v_dossiers_tva")
        self.assertEqual(ligne["tva_attendue"], 151.45)
        codes = [c["code"] for c in A.lire_vue(self.instance, "v_constats")]
        self.assertIn("TVA_INCOHERENTE", codes)

    def test_un_montant_ecrit_et_illisible_est_stocke_comme_tel(self) -> None:
        """`ILLISIBLE` n'est pas `ABSENT`, et la base doit le dire.

        Ce test tient la frontiere reelle de l'etat, mesuree le 2026-09-05: il
        est **vrai dans la colonne**, et il ne remonte pas encore aux vues -
        `v_acte_effectif` ne lit `montant_source` que si `montant_autorise` est
        non vide. La propagation appartient a la zone vues; tant qu'elle n'est
        pas faite, ce test dit exactement ou l'etat s'arrete, pour qu'aucun
        lecteur ne croie l'inverse.
        """
        from coproscope.modules._pont_actes_lignes import _montant_et_source
        from coproscope.modules._pont_actes_source import Candidat

        candidat = Candidat(ligne={"montant_seuil": "2.500"}, source="RESOLUTION")
        montant, source = _montant_et_source(candidat)
        self.assertEqual(montant, "")
        self.assertEqual(source, "ILLISIBLE")

        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("ACTE-1", montant_autorise="", montant_source=source)],
                 ["DOC-PV"])
        (stocke,) = A.lire_table(self.instance, A.TABLE_ACTES)
        self.assertEqual(stocke["montant_source"], "ILLISIBLE")
        # La limite, nommee plutot que supposee.
        (vue,) = A.lire_vue(self.instance, "v_acte_effectif")
        self.assertEqual(vue["montant_lu_sur"], "ABSENT")


class CeintureSqlTests(unittest.TestCase):
    """La ceinture doit faire ce que sa docstring affirme, pas moins.

    `sql_reel` promet de rendre `NULL` sur tout ce qui n'est pas
    `-?\\d+\\.\\d\\d`. Sa premiere version ne portait qu'un `GLOB
    '[0-9]*.[0-9][0-9]'`, et dans un motif GLOB `*` avale tout - blanc de
    milliers compris. Elle laissait donc passer le defaut meme qu'elle existe
    pour arreter, en silence, sur le seul cas ou elle sert: une base ecrite par
    une version anterieure ou a la main.
    """

    def _lu(self, expression: str, valeur: str) -> object:
        import sqlite3

        cx = sqlite3.connect(":memory:")
        cx.execute("CREATE TABLE t(v TEXT)")
        cx.execute("INSERT INTO t VALUES(?)", (valeur,))
        return cx.execute(f"SELECT {expression} FROM t").fetchone()[0]

    def test_le_blanc_de_milliers_n_est_plus_avale_par_l_etoile(self) -> None:
        """C033/C036 residuels: `18 240.00` rendait 18.0 a travers la ceinture."""
        for herite in ("18 240.00", "357 493.10", "1 000.00"):
            self.assertIsNone(
                self._lu(sql_reel("v"), herite),
                f"{herite!r} doit rester non lu, pas valoir son premier groupe",
            )

    def test_un_second_separateur_n_est_plus_avale_non_plus(self) -> None:
        """`2.500.00` rendait 2.5: trois ordres de grandeur, sans un mot."""
        self.assertIsNone(self._lu(sql_reel("v"), "2.500.00"))
        self.assertIsNone(self._lu(sql_reel("v"), "1.234.567.00"))

    def test_le_signe_au_milieu_n_est_pas_un_montant(self) -> None:
        self.assertIsNone(self._lu(sql_reel("v"), "1-2.00"))

    def test_la_forme_canonique_reste_lue_telle_qu_on_la_croit(self) -> None:
        """Le resserrage ne doit rien casser de ce qui marchait."""
        self.assertEqual(self._lu(sql_reel("v"), "18240.00"), 18240.0)
        self.assertEqual(self._lu(sql_reel("v"), "-18240.00"), -18240.0)
        self.assertEqual(self._lu(sql_reel("v"), "0.00"), 0.0)
        self.assertEqual(self._lu(sql_reel("v"), "357493.10"), 357493.1)

    def test_un_taux_entier_nu_reste_lisible_comme_taux(self) -> None:
        """La regression: `sql_reel` sur un taux eteignait TVA_INCOHERENTE.

        Un taux n'a pas de milliers, donc `10` ne peut pas etre ambigu. Lui
        imposer la forme canonique des montants rendait NULL une valeur
        parfaitement normale.
        """
        self.assertEqual(self._lu(sql_taux("v"), "10"), 10.0)
        self.assertEqual(self._lu(sql_taux("v"), "5.5"), 5.5)
        self.assertEqual(self._lu(sql_taux("v"), "20.00"), 20.0)

    def test_un_taux_qu_on_ne_sait_pas_lire_reste_non_lu(self) -> None:
        for ecrit in ("20%", "10,5", "abc", "", "5.", "1.2.3"):
            self.assertIsNone(self._lu(sql_taux("v"), ecrit), ecrit)


class RaccordBudgetTests(unittest.TestCase):
    """C043: le total lu en `Decimal` arrivait tel quel dans un champ `float`."""

    def test_les_seize_controles_du_budget_survivent_au_total_extrait(self) -> None:
        from decimal import Decimal

        from coproscope.modules import budget_previsionnel as B
        from coproscope.modules.comptes_extraction import _total_de
        from coproscope.modules._comptes_extraction_modele import AnnexeComptable
        from coproscope.modules._budget_previsionnel_modele import (
            Copropriete,
            Dossier,
        )

        annexe = AnnexeComptable(total_charges=Decimal(ETALON_CHARGES.replace(" ", "")
                                                       .replace(",", ".")))
        total = _total_de(annexe)
        self.assertIsInstance(total, float)

        dossier = Dossier(
            budget=B.BudgetPrevisionnel(total_charges=total),
            copropriete=Copropriete(avance_reserve_prevue_reglement=1000.0),
        )
        constats = B.evaluer(dossier)
        self.assertIn("B-6", [c.controle for c in constats])
        self.assertEqual(len(constats), 16)


class ChaineCompleteTests(unittest.TestCase):
    """L'etalon de l'audit traverse la chaine sans perdre d'ordre de grandeur."""

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.racine, ignore_errors=True)
        self.instance = _Instance(self.racine)

    def test_le_total_des_charges_2025_traverse_la_chaine(self) -> None:
        A.ecrire(self.instance, A.TABLE_ACTES,
                 [_acte("ACTE-COMPTES", portee="APPROBATION_COMPTES",
                        montant_autorise=ETALON_CHARGES, exercice="2025",
                        date_effet="2026-06-30")], ["DOC-PV"])
        (stocke,) = A.lire_table(self.instance, A.TABLE_ACTES)
        self.assertEqual(stocke["montant_autorise"], "357493.10")
        (vue,) = A.lire_vue(self.instance, "v_execution")
        self.assertEqual(vue["montant_autorise"], 357493.10)
        # L'ecran met un blanc insecable entre les milliers: on compare sur les
        # chiffres, qui sont ce que le test defend.
        affiche = euros(vue["montant_autorise"])
        self.assertEqual(
            "".join(c for c in affiche if c.isdigit() or c == ","), "357493,10"
        )


# --------------------------------------------------------------------------
# Fixtures - identiques a celles de test_actes_autorisation, gardees locales
# pour que ce fichier se lise seul.
# --------------------------------------------------------------------------

class _Instance:
    def __init__(self, racine: Path) -> None:
        self.racine = racine

    def settings(self) -> dict:
        return {"vault": {"local_root": "./vault_local"}}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / valeur.lstrip("./")).resolve()


def _acte(acte_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "acte_id": acte_id, "nature": "RESOLUTION_AG", "etat": "CONSTATEE",
        "portee": "ORDINAIRE", "date_effet": "2024-07-03", "exercice": "2024",
        "ag_id": "AG-2024-07-03", "numero": "12", "sous_numero": "",
        "objet": "Ravalement de la facade sud", "montant_autorise": "",
        "entreprise": "", "montant_source": "", "entreprise_source": "",
        "valide_du": "", "valide_au": "", "majorite_requise": "24",
        "majorite_appliquee": "24", "resultat": "ADOPTEE", "resolution_id": "",
        "page": "4", "ancre": "", "confiance": "forte",
        "doc_id": "DOC-PV", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


def _dossier(dossier_id: str, **kw: str) -> dict[str, str]:
    ligne = {
        "dossier_id": dossier_id, "exercice": "2024",
        "date_depense": "2024-09-15", "montant_ttc": "18240.00",
        "fournisseur": "WE GROUP", "libelle": "Ravalement facade sud",
        "imputation": "VOTE_SEPARE", "imputation_motif": "", "aiguillage": "ART_44",
        "facture_doc_id": "DOC-FAC", "ecriture_ref": "", "page": "",
        "ancre": "", "doc_id": "DOC-FAC", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


def _lien(source: str, relation: str, cible: str, **kw: str) -> dict[str, str]:
    provenance = kw.pop("provenance", "COPROSCOPE_CALCULE")
    target_kind = kw.pop("target_kind", "dossier")
    ligne = {
        "lien_id": A.lien_id("acte", source, relation, target_kind, cible, provenance),
        "source_kind": "acte", "source_id": source, "relation": relation,
        "target_kind": target_kind, "target_id": cible, "provenance": provenance,
        "force_probatoire": "PIECE_PRODUITE", "motif": "", "doute": "",
        "montant_impute": "", "libelle_cible": "", "echeance": "",
        "constate_le": "2024-09-20", "auteur": "", "page": "", "ancre": "",
        "doc_id": "DOC-FAC", "origine": "EXTRAIT",
    }
    ligne.update(kw)
    return ligne


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
