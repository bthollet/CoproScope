"""Une facture s'admet sur sa forme, jamais sur son vocabulaire. Lot `RM-2026-0058`.

Comme pour le pont d'etat des depenses, deux familles: la regle, sur gabarits
construits, qui tourne en CI; et l'epreuve sur corpus reel, qui se saute
ailleurs et qui seule dit quelque chose sur la justesse.
"""

from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from coproscope.modules._factures_admission import (
    ADMISE_SANS_DECOMPOSITION,
    ADMISE,
    REFUS_CHIFFRAGE_NON_FERME,
    REFUS_MONTANTS_ILLISIBLES,
    REFUS_SANS_IDENTIFICATION,
    admettre_facture,
    bilan,
)
from tests._instance_de_lot import corpus_portant

#: Cherchee par ce qu'elle PORTE - voir `_instance_de_lot.py`.
_PIECES = "staging/text_factures/*.txt"
CORPUS = corpus_portant(_PIECES, mesure="l'admission des factures, sur corpus reel")

# Une facture ordinaire: identifiee, chiffree, et dont le chiffrage se ferme.
FACTURE = """SOCIETE EXEMPLE
Facture n FA2025-0147
Date : 12/03/2025
Prestation d'entretien des parties communes
Total HT
1 000,00
TVA 20,00 %
200,00
Total TTC
1 200,00
"""

# Le piege exact de `RM-2026-0058`: un document qui PARLE de factures sans en
# etre une. Un proces-verbal d'assemblee, un tableau de bord.
PROCES_VERBAL = """PROCES-VERBAL DE L'ASSEMBLEE GENERALE
Seance du 29/04/2025
Resolution n 4: le syndic presentera les factures de travaux au conseil
syndical. Le total TTC des depenses de l'exercice s'eleve a 357 493,10 euros.
La resolution est adoptee.
"""

# Le montant sur la ligne SUIVANTE, comme le rend la couche de texte d'un PDF.
FACTURE_APLATIE = """FOURNISSEUR ENERGIE
Facture n 780000518262
2 mai 2026
MONTANT TTC a payer
65,39
Total HT
54,49
TVA
10,90
"""

# Sans taxe applicable: le chiffrage se ferme avec une taxe nulle.
FACTURE_SANS_TVA = """AUTO ENTREPRENEUR
Facture n 2025-11
Date 04/07/2025
TVA non applicable, article 293 B du CGI
Total HT
480,00
Net a payer
480,00
"""


class RegleDeForme(unittest.TestCase):
    def test_une_facture_ordinaire_est_admise(self) -> None:
        verdict = admettre_facture(FACTURE)
        self.assertTrue(verdict.admise, verdict.explication)
        self.assertEqual(verdict.ttc, Decimal("1200.00"))
        self.assertEqual(verdict.ecart, Decimal("0.00"))

    def test_un_proces_verbal_qui_parle_de_factures_n_en_est_pas_une(self) -> None:
        """Le defaut d'origine: `facture` et `total ttc` suffisaient a admettre."""

        verdict = admettre_facture(PROCES_VERBAL)
        self.assertFalse(verdict.admise)
        self.assertNotEqual(verdict.motif, ADMISE)

    def test_le_montant_peut_suivre_son_libelle_a_la_ligne(self) -> None:
        """La couche de texte d'un PDF aplatit le tableau: un jeton par ligne.

        Exiger le montant sur la meme ligne que son libelle aurait code une
        modalite de mise en page. Mesure: cette seule exigence rejetait 81 des
        factures reelles du corpus, soit la totalite des admises.
        """

        verdict = admettre_facture(FACTURE_APLATIE)
        self.assertTrue(verdict.admise, verdict.explication)
        self.assertEqual(verdict.ttc, Decimal("65.39"))

    def test_une_facture_sans_tva_applicable_est_admise(self) -> None:
        """Hors valeurs observees: le mode degrade doit rester correct."""

        verdict = admettre_facture(FACTURE_SANS_TVA)
        self.assertTrue(verdict.admise, verdict.explication)
        self.assertEqual(verdict.tva, Decimal("0.00"))

    def test_une_facture_qui_n_imprime_pas_sa_decomposition_est_admise_a_part(self) -> None:
        """La conservation est un test de REFUTATION, pas une condition d'entree.

        Une facture au forfait, un ticket, une note simple n'affichent qu'un
        total du. Exiger que la decomposition se ferme quand elle n'est pas
        imprimee aurait code la modalite `toute facture imprime son hors taxes`.
        L'absence de preuve n'est pas une preuve d'absence - mais le niveau de
        preuve etant plus faible, il se compte a part.
        """

        minimale = "Facture FAC-2025-777\nFournisseur Demo\nDate 15/01/2025\nTotal TTC 1200,00\n"
        verdict = admettre_facture(minimale)
        self.assertTrue(verdict.admise, verdict.explication)
        self.assertEqual(verdict.motif, ADMISE_SANS_DECOMPOSITION)
        self.assertEqual(verdict.ttc, Decimal("1200.00"))

    def test_une_decomposition_imprimee_qui_ne_ferme_pas_reste_refusee(self) -> None:
        """La refutation garde toute sa force quand la preuve EST imprimee."""

        faux = "Facture n 9876\nDate 01/02/2025\nTotal HT\n100,00\nTVA\n20,00\nTotal TTC\n999,00\n"
        self.assertFalse(admettre_facture(faux).admise)

    def test_une_piece_sans_numero_ni_date_est_refusee_en_le_disant(self) -> None:
        verdict = admettre_facture("Un texte quelconque sans rien d'identifiable.")
        self.assertFalse(verdict.admise)
        self.assertEqual(verdict.motif, REFUS_SANS_IDENTIFICATION)
        self.assertIn("identifier", verdict.explication)

    def test_une_piece_sans_couche_de_texte_est_comptee_et_non_ignoree(self) -> None:
        """18 pour cent du corpus reel. Les ignorer laisserait croire au complet."""

        verdict = admettre_facture("Facture n 12345\nDate 01/02/2025\n")
        self.assertFalse(verdict.admise)
        self.assertEqual(verdict.motif, REFUS_MONTANTS_ILLISIBLES)
        self.assertIn("reconnaissance de caracteres", verdict.explication)

    def test_un_chiffrage_qui_ne_se_ferme_pas_est_refuse_et_chiffre(self) -> None:
        faux = "Facture n 9\nDate 01/02/2025\nTotal HT\n100,00\nTVA\n20,00\nTotal TTC\n999,00\n"
        verdict = admettre_facture(faux)
        self.assertFalse(verdict.admise)
        self.assertEqual(verdict.motif, REFUS_CHIFFRAGE_NON_FERME)
        self.assertIsNotNone(verdict.ecart)
        self.assertIn("Ecart mesure", verdict.explication)

    def test_le_bilan_conserve_admises_plus_refusees(self) -> None:
        _, resultat = bilan({"a": FACTURE, "b": PROCES_VERBAL, "c": FACTURE_SANS_TVA})
        self.assertTrue(resultat.tient)
        self.assertEqual(resultat.lues, 3)
        self.assertEqual(resultat.admises, 2)
        self.assertEqual(resultat.refusees, 1)

    def test_chaque_refus_est_ventile_par_motif(self) -> None:
        _, resultat = bilan({"pv": PROCES_VERBAL, "ok": FACTURE})
        motifs = dict(resultat.par_motif)
        self.assertEqual(motifs.get(ADMISE), 1)
        self.assertEqual(sum(n for m, n in resultat.par_motif if m != ADMISE), 1)


@unittest.skipUnless(CORPUS.mesurable, CORPUS.motif_de_saut)
class CorpusReelExtranet(unittest.TestCase):
    """341 pieces d'un extranet de syndic, nommees par empreinte."""

    @classmethod
    def setUpClass(cls) -> None:
        # Relu MAINTENANT, pas au chargement du module: entre les deux, la
        # doctrine a pu faire supprimer l'instance. Vide ou disparu, il en sort
        # un saut qui nomme la cause, jamais une boucle sans assertion.
        cls.pieces = CORPUS.textes(_PIECES)

    def test_la_conservation_tient_sur_le_corpus_entier(self) -> None:
        _, resultat = bilan(self.pieces)
        self.assertTrue(resultat.tient)
        self.assertEqual(resultat.admises + resultat.refusees, resultat.lues)

    def test_aucune_poignee_de_pieces_ne_porte_la_quasi_totalite_du_total(self) -> None:
        """Le constat d'origine: 4 lignes sur 601 portaient 94,5 pour cent."""

        verdicts, resultat = bilan(self.pieces)
        montants = sorted(
            (v.ttc for v in verdicts.values() if v.admise and v.ttc is not None), reverse=True
        )
        self.assertGreater(len(montants), 20)
        part = sum(montants[:4]) / resultat.total_admis
        self.assertLess(part, Decimal("0.80"))

    def test_les_pieces_illisibles_sont_comptees(self) -> None:
        _, resultat = bilan(self.pieces)
        motifs = dict(resultat.par_motif)
        self.assertGreater(motifs.get(REFUS_MONTANTS_ILLISIBLES, 0), 0)


if __name__ == "__main__":
    unittest.main()
