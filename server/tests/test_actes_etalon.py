"""Le schema confronte a l'etalon etabli a la main sur les sources primaires.

Reference: `docs/etalon_corpus_tests_ux.md`, proces-verbal du 03/07/2024 et
annexes comptables de l'exercice 2025.

Ce que ces tests verifient n'est **pas** que l'extracteur trouve ces valeurs -
ce n'est pas ce lot. C'est que le schema sache les representer sans les
confondre, et qu'aucun predicat n'aille conclure a l'adoption la ou le document
se tait.

Rappel de methode, pose apres qu'un premier etalon se soit revele faux: une
reference precise n'est pas une preuve. Les nombres ci-dessous viennent d'une
lecture manuelle de la source primaire, pas d'une note qui la cite.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import actes_autorisation as A

from tests.test_actes_autorisation import _Instance, _acte, _dossier


class EtalonIssuesTests(unittest.TestCase):
    """Les quatre issues du proces-verbal du 03/07/2024.

    55 resolutions: 39 adoptees, 7 rejetees, 8 portant `Pas de vote`, et **1
    dont le proces-verbal n'enonce jamais l'issue** - la resolution 28, budget
    previsionnel 2024, dont les trois lignes de vote sont presentes et dont la
    phrase de conclusion manque. Plus 1 majorite non enoncee, resolution 23.
    """

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=False)

    def _etalon(self) -> None:
        lignes = []
        numero = 1
        for issue, combien in (("ADOPTEE", 39), ("REJETEE", 7), ("PAS_DE_VOTE", 8)):
            for _ in range(combien):
                lignes.append(_acte(
                    f"ACTE-{numero:03d}", numero=str(numero), resultat=issue,
                    majorite_annoncee="24", objet=f"Resolution {numero}",
                ))
                numero += 1
        # Resolution 28: des voix sont comptees, l'issue n'est pas enoncee.
        lignes.append(_acte(
            "ACTE-028B", numero="28", resultat="VOTE_SANS_FORMULE",
            majorite_annoncee="24", montant_autorise="280000.00",
            objet="Budget previsionnel de l'exercice 2024",
        ))
        # Resolution 23: aucune majorite enoncee.
        lignes[22]["majorite_annoncee"] = "NON_ENONCEE"
        A.ecrire(self.instance, A.TABLE_ACTES, lignes, ["DOC-PV"])

    def test_les_quatre_issues_se_comptent_separement(self) -> None:
        self._etalon()
        compte = {
            issue: len(A.matrice(self.instance, [("resultat", "eq", issue)]))
            for issue in ("ADOPTEE", "REJETEE", "PAS_DE_VOTE", "VOTE_SANS_FORMULE")
        }
        self.assertEqual(compte, {"ADOPTEE": 39, "REJETEE": 7,
                                  "PAS_DE_VOTE": 8, "VOTE_SANS_FORMULE": 1})
        self.assertEqual(sum(compte.values()), 55)

    def test_pas_de_vote_et_issue_non_enoncee_ne_sont_pas_le_meme_etat(self) -> None:
        """Aucun des deux n'est un NULL, et ils n'ont pas la meme cellule.

        `Pas de vote` est enonce par le proces-verbal: la source dit ce qui
        s'est passe, donc elle est disponible. Une issue non enoncee laisse la
        cellule `A confirmer` - jamais une adoption.
        """
        self._etalon()
        cellules = {l["acte_id"]: l["cel_resolution"] for l in A.matrice(self.instance)}
        pas_de_vote = A.matrice(self.instance, [("resultat", "eq", "PAS_DE_VOTE")])
        self.assertTrue(all(l["cel_resolution"] == "PIECE_PRODUITE"
                            for l in pas_de_vote))
        self.assertEqual(cellules["ACTE-028B"], "AFFIRME_SANS_PIECE")

    def test_une_issue_non_enoncee_ne_fabrique_jamais_un_vote(self) -> None:
        """Le piege naturel du corpus: conclure a l'adoption faute de phrase.

        La resolution 28 porte 280 000,00 et aucune depense rattachee. Rangee
        avec les adoptees, elle produirait un constat d'inexecution - donc une
        affirmation que l'assemblee a decide quelque chose. Elle n'en produit
        pas, et elle produit le sien.
        """
        self._etalon()
        par_code: dict[str, set[str]] = {}
        for constat in A.constats(self.instance):
            par_code.setdefault(constat["code"], set()).add(constat["sujet_id"])
        self.assertNotIn("ACTE-028B", par_code.get("ACTE_SANS_EXECUTION", set()))
        self.assertIn("ACTE-028B", par_code.get("ISSUE_NON_ENONCEE", set()))

    def test_le_motif_de_l_issue_non_enoncee_refuse_de_conclure(self) -> None:
        self._etalon()
        motif = next(c["motif"] for c in A.constats(self.instance)
                     if c["code"] == "ISSUE_NON_ENONCEE")
        self.assertIn("n'enonce pas l'issue", motif)
        self.assertIn("Rien n'autorise a conclure", motif)

    def test_une_majorite_non_enoncee_est_un_fait_pas_une_colonne_vide(self) -> None:
        self._etalon()
        sujets = {c["sujet_id"] for c in A.constats(self.instance)
                  if c["code"] == "MAJORITE_NON_ENONCEE"}
        self.assertEqual(len(sujets), 1)

    def test_le_vocabulaire_des_issues_est_celui_de_la_voie_resolutions(self) -> None:
        """Pas de troisieme source de verite - y compris pour les mots."""
        from coproscope.modules import _resolutions_motifs as M

        for valeur in (M.PAS_DE_VOTE, M.VOTE_SANS_FORMULE, M.SANS_ISSUE):
            self.assertIn(valeur, A.RESULTATS)
        self.assertFalse(A.resultat_valide(""))
        self.assertTrue(A.resultat_valide("VOTE_SANS_FORMULE"))
        self.assertEqual(A.RESULTATS_AUTORISANTS, ("ADOPTEE",))


class EcartsComptablesTests(unittest.TestCase):
    """Un ecart se porte comme un constat rattache a une piece.

    Jamais comme une correction silencieuse de la valeur: corriger ferait
    disparaitre la question a poser au syndic, qui est le livrable.
    """

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=False)

    def _pieces(self) -> None:
        A.ecrire(self.instance, A.TABLE_DOSSIERS, [
            # Prime d'assurance: 3 693,90 de T.V.A. extraits d'une depense qui
            # n'en supporte pas.
            _dossier("P-B-F01", date_depense="2025-01-09", montant_ttc="22163.40",
                     libelle="Primes d'assurances", exercice="2025",
                     taux_tva_annonce="", tva_annoncee="3693.90",
                     tva_regime="EXONERE"),
            # La piece porte 10 %, la comptabilite extrait 20 %.
            _dossier("P-B-F03", date_depense="2025-03-28", montant_ttc="1665.66",
                     libelle="Entretien et petites reparations", exercice="2025",
                     taux_tva_annonce="10.00", tva_annoncee="277.61",
                     tva_regime="NORMAL"),
            # La piece porte `T.V.A. non applicable`.
            _dossier("P-B-F12", date_depense="2025-01-20", montant_ttc="1200.00",
                     libelle="Entretien et petites reparations", exercice="2025",
                     taux_tva_annonce="", tva_annoncee="200.00",
                     tva_regime="NON_APPLICABLE"),
            # Conforme: 770,00 a 10 % donne bien 70,00.
            _dossier("P-B-F04", date_depense="2025-02-15", montant_ttc="770.00",
                     libelle="Entretien et petites reparations", exercice="2025",
                     taux_tva_annonce="10.00", tva_annoncee="70.00",
                     tva_regime="NORMAL"),
        ], ["DOC-ANNEXE"])

    def test_les_trois_ecarts_reels_sortent_et_la_piece_conforme_non(self) -> None:
        self._pieces()
        ecarts = {c["sujet_id"]: c for c in A.constats(self.instance)
                  if c["code"] == "TVA_INCOHERENTE"}
        self.assertEqual(set(ecarts), {"P-B-F01", "P-B-F03", "P-B-F12"})
        self.assertAlmostEqual(ecarts["P-B-F03"]["montant_en_jeu"], 126.19, places=2)
        self.assertAlmostEqual(ecarts["P-B-F12"]["montant_en_jeu"], 200.00, places=2)
        self.assertAlmostEqual(ecarts["P-B-F01"]["montant_en_jeu"], 3693.90, places=2)

    def test_la_valeur_de_la_piece_n_est_jamais_corrigee(self) -> None:
        self._pieces()
        lignes = {l["dossier_id"]: l for l in A.lire_vue(
            self.instance, "v_dossiers_tva", [("depense_exercice", "eq", "2025")])}
        # Ce que la comptabilite a retenu est intact...
        self.assertEqual(lignes["P-B-F03"]["tva_annoncee"], "277.61")
        # ...et ce que la piece annonce est calcule a cote, pas a la place.
        self.assertAlmostEqual(lignes["P-B-F03"]["tva_attendue"], 151.42, places=2)

    def test_la_tva_est_incluse_dans_le_montant_a_repartir(self) -> None:
        """1 200,00 au taux de 20 % donne 200,00, pas 240,00.

        Un outil qui traiterait le montant a repartir comme un hors taxes
        surevaluerait chaque ligne de l'annexe.
        """
        A.ecrire(self.instance, A.TABLE_DOSSIERS, [
            _dossier("P-B-F12", montant_ttc="1200.00", taux_tva_annonce="20.00",
                     tva_annoncee="200.00", tva_regime="NORMAL", exercice="2025"),
        ], ["DOC-ANNEXE"])
        ligne = A.lire_vue(self.instance, "v_dossiers_tva",
                           [("depense_exercice", "eq", "2025")])[0]
        self.assertAlmostEqual(ligne["tva_attendue"], 200.00, places=2)
        self.assertEqual(
            [c["code"] for c in A.constats(self.instance)
             if c["code"] == "TVA_INCOHERENTE"], [])

    def test_le_total_des_charges_retombe_sur_l_etalon(self) -> None:
        """357 493,10 = 304 021,37 courantes + 53 471,73 travaux et exceptionnel.

        Le montant est stocke en colonne TEXT, comme tout ce magasin. Ce test
        verifie que la forme canonique de `montant_texte` traverse le stockage
        et la somme sans perdre le centime.
        """
        A.ecrire(self.instance, A.TABLE_DOSSIERS, [
            _dossier("COURANTES", exercice="2025",
                     montant_ttc=A.montant_texte("304 021,37"),
                     imputation="BUDGET_PREVISIONNEL"),
            _dossier("TRAVAUX", exercice="2025",
                     montant_ttc=A.montant_texte("53 471,73"),
                     imputation="VOTE_SEPARE"),
        ], ["DOC-ANNEXE"])
        lignes = A.lire_vue(self.instance, "v_dossiers",
                            [("depense_exercice", "eq", "2025")])
        self.assertAlmostEqual(
            sum(float(l["montant_ttc"]) for l in lignes), 357493.10, places=2)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
