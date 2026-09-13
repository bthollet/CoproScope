# -*- coding: utf-8 -*-
"""Le lanceur de la suite ne peut pas annoncer OK sans avoir joue un test.

`RM-2026-0171`. **Le defaut etait dans l'instrument dont depend chaque verdict
de ce depot**, et il a ete mesure, pas deduit.

`tools/lancer_la_suite.py` imprimait `'OK' if resultat.wasSuccessful() else
'ECHEC'` et rendait le code correspondant. Or **`wasSuccessful()` vaut `True`
quand ZERO test n'a tourne**: sans echec ni erreur, la methode ne distingue pas
*tout est passe* de *rien n'a ete joue*. Sonde du 2026-09-12 sur une suite
vide: `testsRun = 0`, `wasSuccessful() = True`, donc **`verdict : OK` et code
`0`**.

Le fichier COMPTAIT `demarres`, l'IMPRIMAIT, et **ne s'en servait pas** - alors
que son propre en-tete promet *un verdict qui dit ce qu'il a joue*. C'est la
forme la plus pure de la faute que ce depot nomme: un chiffre affiche a cote
d'une decision qui l'ignore.

----------------------------------------------------------------------
Pourquoi cette garde appelle `main` et non seulement `verdict`
----------------------------------------------------------------------

**Le reproche qui a fait naitre ce lot etait que tester la fonction pure ne
prouve rien.** Une garde qui n'eprouve que `verdict(collectes, demarres, ...)`
laisse l'etat NON CABLE passer: `main` peut continuer d'appeler
`wasSuccessful()` directement, la fonction pure reste verte, et le defaut vit.
*Tester une fonction n'est pas tester son cablage, et le cablage est ici tout
l'argument.*

Cette garde fait donc les deux: elle eprouve la fonction sur des cas fabriques,
**et elle appelle `main` lui-meme** sur un dossier sans aucun test, ou la
reponse est connue - aucun test joue, donc le code doit etre NON NUL.

**Ce qu'elle ne fait pas.** Elle ne rejoue pas la suite complete: ce serait une
seconde suite dans le meme arbre, ce que le `CLAUDE.md` interdit apres deux
passages concurrents bloques sans verdict. Elle mesure le comportement du
lanceur sur un dossier vide, ce qui est le cas limite qui mentait.
"""
from __future__ import annotations

import importlib.util
import io
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

RACINE = Path(__file__).resolve().parents[2]
LANCEUR = RACINE / "tools" / "lancer_la_suite.py"


def _lanceur():
    """Le module du lanceur, charge par son CHEMIN.

    Il vit dans `tools/`, qui n'est pas un paquet importable depuis la suite.
    On le charge donc par specification de fichier, ce que d'autres gardes du
    depot font deja pour le meme dossier.
    """
    spec = importlib.util.spec_from_file_location("_lanceur_sous_test", LANCEUR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class LE_VERDICT_NE_CONFOND_PAS_VIDE_ET_PASSE(unittest.TestCase):
    def setUp(self) -> None:
        self.lanceur = _lanceur()

    def test_zero_test_DEMARRE_est_un_echec(self) -> None:
        """Le cas qui mentait, et il mentait dans le sens le plus dangereux."""
        libelle, code = self.lanceur.verdict(
            collectes=2993, demarres=0, absents=2993, succes=True)
        self.assertNotEqual(0, code, "un passage qui n'a joue AUCUN test rend "
                                     "encore un code de succes")
        self.assertIn("ECHEC", libelle)
        self.assertIn("DEMARRE", libelle)

    def test_zero_test_COLLECTE_est_un_echec(self) -> None:
        """Une collecte vide est une suite introuvable, pas une suite saine."""
        libelle, code = self.lanceur.verdict(
            collectes=0, demarres=0, absents=0, succes=True)
        self.assertNotEqual(0, code)
        self.assertIn("COLLECTE", libelle)

    def test_un_echec_reste_un_echec(self) -> None:
        libelle, code = self.lanceur.verdict(
            collectes=3000, demarres=3000, absents=0, succes=False)
        self.assertEqual(1, code)
        self.assertEqual("ECHEC", libelle)

    def test_un_passage_plein_et_reussi_est_OK(self) -> None:
        """Le temoin sans lequel la garde pourrait tout refuser."""
        libelle, code = self.lanceur.verdict(
            collectes=3000, demarres=3000, absents=0, succes=True)
        self.assertEqual(0, code)
        self.assertEqual("OK", libelle)

    def test_des_absents_ne_font_pas_echouer_mais_se_DISENT(self) -> None:
        """L'etat reel du depot: 6 absents, verdict OK.

        Un saut pose au niveau d'une classe appelle `addSkip` sans passer par
        `startTest`; c'est legitime. Ce qui ne l'est pas, c'est qu'un absent se
        lise comme un test passe - donc le libelle porte le compte.
        """
        libelle, code = self.lanceur.verdict(
            collectes=3032, demarres=3026, absents=6, succes=True)
        self.assertEqual(0, code, "des absents ne doivent pas faire echouer")
        self.assertIn("OK", libelle)
        self.assertIn("6", libelle,
                      "le libelle ne dit pas combien de tests n'ont jamais "
                      "demarre: l'absent se lirait comme un test passe")


class LE_CABLAGE_EST_MESURE_PAR_MAIN_LUI_MEME(unittest.TestCase):
    """Sans ceci, `main` pourrait garder son ancien calcul en silence."""

    def test_main_sur_un_dossier_SANS_TEST_rend_un_code_non_nul(self) -> None:
        cwd = os.getcwd()
        lanceur = _lanceur()
        try:
            with TemporaryDirectory() as dossier:
                # Un dossier reel, vide de tout `test_*.py`.
                journal = io.StringIO()
                # stderr AUSSI: le lanceur interne y ecrit son 'NO TESTS RAN',
                # qui sortirait dans le journal de chaque passage complet - or
                # c'est ce journal qu'on lit pour connaitre le verdict.
                with redirect_stdout(journal), redirect_stderr(io.StringIO()):
                    code = lanceur.main([], dossier=dossier)
                sortie = journal.getvalue()
        finally:
            os.chdir(cwd)

        self.assertNotEqual(
            0, code,
            "le lanceur rend un code de SUCCES sur un dossier sans aucun "
            "test. C'est le defaut qui a fait naitre cette garde: "
            "`wasSuccessful()` vaut True quand rien n'a tourne, et le verdict "
            "s'appuyait sur lui seul.")
        self.assertIn(
            "ECHEC", sortie,
            "le journal du lanceur n'annonce pas ECHEC alors qu'aucun test "
            "n'a ete joue - et c'est le journal qu'un agent recopie")

    def test_main_passe_REELLEMENT_par_verdict(self) -> None:
        """Le cablage, mesure la ou il vit.

        On remplace `verdict` dans le module et on verifie que `main` lit la
        reponse posee. Si `main` recalcule son code lui-meme, le remplacement
        n'a aucun effet et ce test tombe - ce qui est exactement le defaut que
        le sceptique reprochait a une garde limitee a la fonction pure.
        """
        cwd = os.getcwd()
        lanceur = _lanceur()
        appels: list[tuple] = []

        def _temoin(collectes, demarres, absents, succes):
            appels.append((collectes, demarres, absents, succes))
            return "LIBELLE-TEMOIN", 42

        lanceur.verdict = _temoin
        try:
            with TemporaryDirectory() as dossier:
                journal = io.StringIO()
                with redirect_stdout(journal), redirect_stderr(io.StringIO()):
                    code = lanceur.main([], dossier=dossier)
                sortie = journal.getvalue()
        finally:
            os.chdir(cwd)

        self.assertEqual(
            [(0, 0, 0, True)], appels,
            "`main` n'a pas appele `verdict`, ou ne lui a pas passe ce qu'il "
            "avait compte: le cablage n'existe pas et la fonction pure ne "
            "garde rien")
        self.assertEqual(
            42, code,
            "`main` ne rend pas le code que `verdict` a decide: il le "
            "recalcule, donc la fonction pure peut etre juste pendant que le "
            "lanceur ment")
        self.assertIn("LIBELLE-TEMOIN", sortie,
                      "`main` n'imprime pas le libelle que `verdict` a rendu")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
