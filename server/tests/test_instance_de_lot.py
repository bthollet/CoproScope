# -*- coding: utf-8 -*-
"""`RM-2026-0150`: le verdict ne doit plus dependre de l'instant.

L'item se resume a une phrase: *une suite dont le verdict depend de l'instant
ou l'on efface un dossier ne mesure pas le code*. Ces tests-ci mesurent
exactement cela, sur des instances bidons construites dans un dossier
temporaire - **aucun corpus prive, donc ils tournent en CI**, contrairement aux
mesures qu'ils protegent.

Ils portent sur l'INSTRUMENT. `RM-2026-0172` a montre pourquoi cela compte:
*cinq gardes sur cinq se presentaient comme des axes et etaient des greps sur
deux ou trois orthographes.* Une aide partagee qui decide si douze tests
mesurent ou se taisent merite ses propres tests.
"""

from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

import tests._instance_de_lot as aide
from tests._instance_de_lot import Corpus, corpus_portant

PIECE = "staging/text/2025-12-31_REDDITION.txt"
MOTIF = "staging/text/2025-12-31_REDDITION*.txt"
#: Le motif que la mesure LIT quand il differe de celui sur lequel elle a ete
#: selectionnee - le cas de `test_comptes_extraction_pont`.
AUTRE_MOTIF = "staging/text_factures/*.txt"
MESURE = "que le montant a repartir est bien un TTC"


class _RacineBidon(unittest.TestCase):
    """Une racine d'instances jetable. Jamais celle du poste."""

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp(prefix="rm0150_"))
        self.addCleanup(shutil.rmtree, self.racine, ignore_errors=True)

    def instance(self, nom: str, contenu: str = "x", piece: str = PIECE) -> Path:
        chemin = self.racine / nom / piece
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(contenu, encoding="utf-8")
        return self.racine / nom

    def corpus(self, *motifs: str) -> Corpus:
        return Corpus(self.racine, motifs or (MOTIF,), MESURE)


class LeVerdictNeDependPasDeLInstant(_RacineBidon):
    """Le coeur de `RM-2026-0150`, et la seule propriete qui compte vraiment."""

    def test_effacer_avant_ou_pendant_la_mesure_donne_le_meme_genre_de_verdict(self) -> None:
        """Efface avant, efface pendant: une non-mesure declaree dans les deux cas.

        C'est l'incident d'origine. Un dossier efface AVANT le chargement du
        module donnait un saut propre; efface APRES, il donnait douze echecs.
        Deux passages du meme code, deux verdicts - selon l'instant seul.
        """
        # Efface avant: le corpus n'est pas mesurable, et il le dit.
        avant = self.corpus()
        self.assertFalse(avant.mesurable)
        self.assertIn("MESURE NON FAITE", avant.motif_de_saut)

        # Efface pendant: la garde avait trouve, la lecture ne trouve plus.
        instance = self.instance("test_corpus")
        pendant = self.corpus()
        self.assertTrue(pendant.mesurable, "la garde doit passer avant l'effacement")
        shutil.rmtree(instance)
        with self.assertRaises(unittest.SkipTest) as leve:
            pendant.pieces(MOTIF)
        self.assertIn("MESURE INTERROMPUE", str(leve.exception))
        self.assertIn("PENDANT", str(leve.exception))

    def test_toucher_une_autre_instance_ne_deplace_pas_la_mesure(self) -> None:
        """Le tri par date de derniere ecriture deplacait la mesure d'un corpus
        a l'autre **sans qu'une ligne de test ait change**. Reproduit sur
        `913d744`: un `touch` faisait passer la lecture de `CORPUS B` a
        `CORPUS A`. Le verdict doit desormais etre le meme des deux cotes.
        """
        a = self.instance("test_corpus_A", contenu="CORPUS A")
        time.sleep(0.02)
        self.instance("test_corpus_B", contenu="CORPUS B")

        avant = self.corpus()
        os.utime(a, None)
        apres = self.corpus()

        self.assertEqual(avant.mesurable, apres.mesurable)
        self.assertEqual(avant.motif_de_saut, apres.motif_de_saut)
        self.assertEqual(avant.identite, apres.identite)


class UneAmbiguiteSeDeclareEtNeSeTranchePas(_RacineBidon):
    def test_deux_instances_portant_les_pieces_ne_sont_pas_departagees(self) -> None:
        """Deux corpus differents portant les memes pieces: la mesure ne sait
        pas duquel elle parle. Prendre le plus recent repondrait a une question
        qu'on n'a pas posee."""
        self.instance("test_corpus_A")
        self.instance("test_corpus_B")
        corpus = self.corpus()
        self.assertFalse(corpus.mesurable)
        motif = corpus.motif_de_saut
        self.assertIn("BASE AMBIGUE", motif)
        self.assertIn("test_corpus_A", motif)
        self.assertIn("test_corpus_B", motif)

    def test_une_seule_candidate_reste_mesurable(self) -> None:
        """Le controle negatif: la declaration d'ambiguite ne doit pas eteindre
        le cas ordinaire."""
        self.instance("test_corpus_A")
        self.assertTrue(self.corpus().mesurable)

    def test_une_piece_en_double_est_une_ambiguite_et_non_un_premier_arrive(self) -> None:
        """`next(...glob(...))` prenait le premier fichier rendu par le systeme
        de fichiers, ce qui n'est pas un choix."""
        instance = self.instance("test_corpus_A")
        seconde = instance / "staging" / "text" / "2025-12-31_REDDITION_bis.txt"
        seconde.write_text("y", encoding="utf-8")
        with self.assertRaises(unittest.SkipTest) as leve:
            self.corpus().une_piece(MOTIF)
        self.assertIn("PIECE AMBIGUE", str(leve.exception))


class LeSautNommeCeQuiNAPasEteVerifie(_RacineBidon):
    """`OK (skipped=N)` sans motif utile est le defaut, pas la solution."""

    def test_chaque_motif_de_saut_porte_la_mesure_qui_n_a_pas_eu_lieu(self) -> None:
        aucune = self.corpus().motif_de_saut
        self.instance("test_corpus_A")
        self.instance("test_corpus_B")
        ambigue = self.corpus().motif_de_saut
        for motif in (aucune, ambigue):
            self.assertIn(MESURE, motif, "le saut ne dit pas ce qui n'est pas verifie")
            self.assertIn(MOTIF, motif, "le saut ne dit pas quelles pieces manquent")

    def test_lire_un_motif_absent_de_la_selection_ne_rend_pas_un_vide_muet(self) -> None:
        """Serie A de `RM-2026-0172`: un dictionnaire vide fait passer quatorze
        boucles **sans une seule assertion**, et le lanceur affiche `Ran 14
        tests, OK`. Aucun `skipped`, aucun `Ran 0`: rien pour alerter.

        Le cas n'est pas theorique: deux modules SELECTIONNENT sur un motif et
        LISENT sur un autre - une ancre de reddition puis tous les `.txt`, un
        manifeste puis un coffre. Rien ne garantit que le second rende quelque
        chose, et c'est precisement la que le vide muet entre.
        """
        self.instance("test_corpus_A")
        corpus = self.corpus()
        self.assertTrue(corpus.mesurable, "selectionne sur un motif present")
        with self.assertRaises(unittest.SkipTest) as leve:
            corpus.textes("staging/text_factures/*.txt")
        self.assertIn("ne rend plus aucune piece", str(leve.exception))
        self.assertIn(MESURE, str(leve.exception))


class LaMesureQuiReussitPorteLIdentiteDeSaBase(_RacineBidon):
    """`RM-2026-0172`: *toute mesure doit porter l'identite de sa base, pas
    seulement son resultat.* La garde respectait cette regle du cote du saut et
    la violait du cote du succes."""

    def test_l_identite_nomme_l_instance_et_compte_les_pieces(self) -> None:
        """**Cette assertion ne mordait pas, et c'est mesure.**

        Elle disait `assertIn("2", identite)`. Or le motif lui-meme contient
        `2025-12-31`: le `2` trouve etait celui de l'annee. Controle negatif du
        2026-09-09: en retirant COMPLETEMENT le compte de `identite`, les neuf
        tests restaient verts. C'est exactement le piege du mot de la
        declaration qui subsiste ailleurs dans la ligne. On assied donc
        l'assertion sur le motif ET son compte, ensemble, et on verifie le
        compte des DEUX cotes pour qu'une constante en dur tombe aussi.
        """
        instance = self.instance("test_corpus_A")
        autre = instance / "staging" / "text" / "2025-12-31_REDDITION_bis.txt"
        autre.write_text("y", encoding="utf-8")
        identite = self.corpus().identite
        self.assertIn("test_corpus_A", identite)
        self.assertIn("%s: 2)" % MOTIF, identite, "compte de pieces absent: %s" % identite)

    def test_l_identite_compte_une_seule_piece_quand_il_n_y_en_a_qu_une(self) -> None:
        """L'autre cote du controle: un compte fige a `2` doit tomber ici."""
        self.instance("test_corpus_A")
        self.assertIn("%s: 1)" % MOTIF, self.corpus().identite)

    def test_l_identite_est_imprimee_au_journal_quand_la_mesure_a_lieu(self) -> None:
        """Le fait doit atteindre le lecteur, a cote du `OK`."""
        import io
        import sys

        import tests._instance_de_lot as aide

        self.instance("test_corpus_A")
        ancienne, capture = aide.RACINE_INSTANCES, io.StringIO()
        ancien_err, sys.stderr = sys.stderr, capture
        try:
            aide.RACINE_INSTANCES = self.racine
            corpus_portant(MOTIF, mesure=MESURE)
        finally:
            aide.RACINE_INSTANCES, sys.stderr = ancienne, ancien_err
        self.assertIn("test_corpus_A", capture.getvalue())
        self.assertIn(MESURE, capture.getvalue())

    def test_le_compte_annonce_est_celui_des_pieces_LUES_et_non_de_la_selection(self) -> None:
        """**Le fait affiche doit etre le fait consomme.**

        `identite` ne compte que les motifs de SELECTION. Deux modules
        selectionnent sur un motif et lisent sur un autre. Mesure du
        2026-09-09, sur cent pieces etrangeres et une seule reddition: le
        journal annoncait `*REDDITION*.txt: 1` pendant que la mesure lisait
        **101** fichiers. Le compte cense rendre visible un corpus a 3 pieces
        la ou le lecteur en attend 341 ne portait donc pas sur ce qui etait lu.
        """
        instance = self.instance("test_corpus_A")
        lues = instance / "staging" / "text_factures"
        lues.mkdir(parents=True)
        for i in range(7):
            (lues / ("f%d.txt" % i)).write_text("z", encoding="utf-8")

        capture = io.StringIO()
        ancien_err, sys.stderr = sys.stderr, capture
        try:
            corpus = self.corpus()
            self.assertEqual(7, len(corpus.pieces(AUTRE_MOTIF)))
        finally:
            sys.stderr = ancien_err
        journal = capture.getvalue()
        self.assertIn("%s: 7" % AUTRE_MOTIF, journal, "compte lu absent: %r" % journal)


class OnPeutDireOuSontLesDonnees(_RacineBidon):
    """L'orientation de Brice citee dans `RM-2026-0150`, et non implementee.

    *"il faut parametriser l'instance sur laquelle les tests se deroulent.
    Quand c'est pertinent."* - *"Un test ne devrait pas savoir OU sont les
    donnees: on devrait pouvoir le lui dire, et il se tait proprement - en le
    disant - quand on ne le lui dit pas."*

    Sans ce geste, les seuls remedes offerts a une base ambigue etaient
    *supprimer un corpus* ou *modifier le test*. Mesure du 2026-09-09: deux
    copies de l'etalon font tomber la confrontation de `Ran 6, OK` a
    `OK (skipped=4)` - or `RM-2026-0150` demande d'en rebatir une seconde.
    """

    def poser(self, nom: str, valeur: str) -> None:
        ancienne = os.environ.get(nom)
        os.environ[nom] = valeur

        def rendre() -> None:
            if ancienne is None:
                os.environ.pop(nom, None)
            else:
                os.environ[nom] = ancienne

        self.addCleanup(rendre)

    def test_designer_une_instance_departage_sans_rien_supprimer(self) -> None:
        self.instance("test_corpus_A", contenu="CORPUS A")
        b = self.instance("test_corpus_B", contenu="CORPUS B")
        self.assertFalse(self.corpus().mesurable, "les deux sont bien ambigues")

        self.poser(aide.VAR_RACINE, str(self.racine))
        self.poser(aide.VAR_INSTANCE, str(b))
        corpus = corpus_portant(MOTIF, mesure=MESURE)
        self.assertTrue(corpus.mesurable)
        self.assertEqual("CORPUS B", corpus.une_piece(MOTIF).read_text(encoding="utf-8"))

    def test_une_designation_qui_echoue_ne_retombe_pas_sur_une_autre_instance(self) -> None:
        """Le point qui compte: **jamais de repli silencieux.**

        Un repli ferait mesurer un corpus que personne n'a demande, sans le
        dire - le defaut meme que `RM-2026-0150` nomme.
        """
        self.instance("test_corpus_A")
        vide = self.racine / "test_corpus_vide"
        vide.mkdir()

        self.poser(aide.VAR_RACINE, str(self.racine))
        self.poser(aide.VAR_INSTANCE, str(vide))
        corpus = corpus_portant(MOTIF, mesure=MESURE)
        self.assertFalse(corpus.mesurable)
        motif = corpus.motif_de_saut
        self.assertIn("INSTANCE DESIGNEE INSUFFISANTE", motif)
        self.assertIn(aide.VAR_INSTANCE, motif)
        self.assertIn("test_corpus_vide", motif)
        self.assertNotIn("test_corpus_A", motif, "un repli s'est produit")
        self.assertIn(MESURE, motif)

    def test_la_racine_se_parametre_et_le_saut_la_nomme(self) -> None:
        self.poser(aide.VAR_RACINE, str(self.racine))
        self.assertFalse(corpus_portant(MOTIF, mesure=MESURE).mesurable)
        self.instance("test_corpus_A")
        self.assertTrue(corpus_portant(MOTIF, mesure=MESURE).mesurable)

    def test_le_saut_ambigu_propose_de_dire_laquelle(self) -> None:
        """Un saut qui ne nomme aucun geste faisable est un cul-de-sac."""
        self.instance("test_corpus_A")
        self.instance("test_corpus_B")
        self.assertIn(aide.VAR_INSTANCE, self.corpus().motif_de_saut)


if __name__ == "__main__":
    unittest.main()
