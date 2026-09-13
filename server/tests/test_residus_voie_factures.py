"""Ce que la voie factures laisse expose, rendu visible plutot que decrit.

Lot du 2026-09-08, items `RM-2026-0074`, `RM-2026-0064` et `RM-2026-0058`.

Une garantie se decrit avec ce qu'elle laisse expose, pas dans sa version
lissee. Les trois tests ci-dessous ne verifient pas que le code est correct:
ils **epinglent un defaut connu et non corrige**, pour qu'il cesse d'etre une
phrase dans un rapport et devienne une valeur mesuree qui bouge quand le code
bouge.

Ils passent tant que le residu est celui qui a ete mesure. Si l'un echoue, ce
n'est pas forcement une regression: c'est que l'ordre de grandeur du residu a
change et qu'il faut le remesurer.
"""

from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from coproscope.modules._comptes_extraction_etat import lire_etat_depenses
from coproscope.modules._factures_admission import bilan
from tests._instance_de_lot import corpus_portant

#: Cherchees par ce qu'elles PORTENT - voir `_instance_de_lot.py`.
_ETATS = "staging/text/2025-12-31_REDDITION*.txt"
_FACTURES = "staging/text_factures/*.txt"
CORPUS_ETATS = corpus_portant(
    _ETATS, mesure="les residus de lecture des etats de depenses")
CORPUS_FACTURES = corpus_portant(
    _FACTURES, mesure="les residus de lecture des factures")


@unittest.skipUnless(CORPUS_ETATS.mesurable, CORPUS_ETATS.motif_de_saut)
class ResiduColonneDeTaxe(unittest.TestCase):
    """La colonne de taxe ne se conserve pas aussi bien que celle des montants.

    L'admission d'un etat des depenses repose sur la conservation de la colonne
    `montant a repartir`, qui retombe EXACTEMENT sur le total imprime, ecart
    0,00, sur les quatre exercices du premier cabinet.

    La colonne de taxe, elle, ne retombe pas exactement: 44 317,09 sommes sur
    les lignes de detail contre 44 324,59 imprimes au total general, soit un
    manque de 7,50 EUR. Deux lignes portent une taxe sans porter de taux, ce qui
    explique une partie du reste.

    Consequence a connaitre: rien dans ce lot ne garantit un total de TVA au
    centime. Un controle de TVA construit sur la somme des lignes de detail
    partirait de 7,50 EUR trop bas.
    """

    @classmethod
    def setUpClass(cls) -> None:
        # Relu MAINTENANT: entre la garde et cette ligne, l'instance a pu etre
        # supprimee par la doctrine. Il en sort un saut nomme, pas un
        # `StopIteration` nu.
        cible = CORPUS_ETATS.une_piece(_ETATS)
        cls.etat = lire_etat_depenses(cible.read_text(encoding="utf-8"))

    def test_la_colonne_des_montants_se_conserve_exactement(self) -> None:
        somme = sum((l.montant_a_repartir or Decimal("0.00")) for l in self.etat.lignes)
        self.assertEqual(somme, self.etat.total_general)

    def test_la_colonne_de_taxe_ne_se_conserve_pas_exactement(self) -> None:
        """Le residu, epingle: 7,50 EUR sur 44 324,59."""

        somme = sum((l.montant_taxe or Decimal("0.00")) for l in self.etat.lignes)
        total = self.etat.total("GENERAL")
        manque = total.montant_taxe - somme
        self.assertGreater(manque, Decimal("0.00"), "le residu a disparu: le remesurer")
        self.assertLess(manque, Decimal("20.00"), "le residu a grossi: le remesurer")


@unittest.skipUnless(CORPUS_FACTURES.mesurable, CORPUS_FACTURES.motif_de_saut)
class ResiduDoublonsFactures(unittest.TestCase):
    """La regle d'admission admet; elle ne deduplique pas.

    `RM-2026-0058` visait deux defauts distincts: des pieces qui ne sont pas des
    factures, et des documents COMPTES DEUX FOIS. Ce lot traite le premier. Le
    second reste entier: sur les pieces admises du corpus, un couple
    (numero, montant) apparait deux fois, pour 10 071,04 EUR comptes en trop.

    Deduplication et admission sont deux questions differentes, et les melanger
    aurait produit une regle qui fait mal les deux. Le residu est donc explicite
    et attend son propre lot.
    """

    @classmethod
    def setUpClass(cls) -> None:
        # Non vide par construction: une liste vide sort en saut nomme au lieu
        # de laisser les boucles tourner sans une seule assertion.
        cls.pieces = CORPUS_FACTURES.textes(_FACTURES)

    def test_des_doublons_subsistent_parmi_les_pieces_admises(self) -> None:
        verdicts, _ = bilan(self.pieces)
        vus: dict[tuple[str, str], int] = {}
        for verdict in verdicts.values():
            if verdict.admise and verdict.numero and verdict.ttc is not None:
                cle = (verdict.numero, str(verdict.ttc))
                vus[cle] = vus.get(cle, 0) + 1
        doublons = {cle: n for cle, n in vus.items() if n > 1}
        self.assertTrue(
            doublons,
            "plus aucun doublon: la deduplication a ete faite, mettre a jour ce residu",
        )

    def test_le_refus_pour_chiffrage_non_ferme_est_le_poste_le_plus_lourd(self) -> None:
        """Le cout en rappel n'est pas mesure, faute d'etalon fait a la main.

        108 pieces sont refusees parce que leur chiffrage ne se ferme pas. Une
        part est faite de documents qui ne sont pas des factures; une autre part,
        NON MESUREE, est faite de vraies factures que le lecteur n'a pas su lire.
        Etablir laquelle demande un etalon releve a la main sur les 341 pieces,
        qui n'existe pas. La regle penche donc du cote du refus, ce qui est le
        bon sens de l'erreur, mais son taux de rappel reste inconnu.
        """

        _, resultat = bilan(self.pieces)
        motifs = dict(resultat.par_motif)
        self.assertGreater(motifs.get("REFUS_CHIFFRAGE_NON_FERME", 0), 0)


if __name__ == "__main__":
    unittest.main()
