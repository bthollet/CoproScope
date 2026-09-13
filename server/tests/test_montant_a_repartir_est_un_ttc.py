"""La colonne `montant a repartir` est un TTC, et personne ne lui ajoute la taxe.

Lot `RM-2026-0064`.

L'item demandait de VERIFIER, pas de supposer: un outil qui traiterait cette
colonne comme un hors taxes, ou qui lui ajouterait la colonne de taxe,
surevaluerait chaque ligne du montant de sa propre taxe.

Mesure du 2026-09-08 sur l'exercice 2025 du premier cabinet, 548 lignes portant
a la fois un taux et une taxe:

- compatibles avec une taxe INCLUSE dans le montant: **548 sur 548**;
- compatibles avec une taxe AJOUTEE au montant: **0**.

La convention est donc etablie par mesure et non par lecture d'en-tete. Un
outil qui additionnerait les deux colonnes porterait le total de 357 493,10 a
401 039,02, soit **+12,2 pour cent** sur un exercice entier.

Etat du code a l'issue de la verification: aucun consommateur n'ajoute la taxe.
`_load_expense_statement_lines` ne lit que `amount`, et la colonne `tva` est
transportee sans jamais entrer dans une somme. Le test ci-dessous fige cette
propriete, qui est aujourd'hui vraie et qu'une refonte pourrait casser sans
qu'aucun autre test ne s'en apercoive - l'erreur serait un total plausible.
"""

from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from coproscope.modules._comptes_extraction_lexique import taxe_ajoutee, taxe_incluse
from coproscope.web.viewmodels._accounting_questions import _accounting_total_charges
from coproscope.web.viewmodels._base import DataTable
from coproscope.web.viewmodels._montant_source import SOURCE_ETAT_DEPENSES
from tests._instance_de_lot import corpus_portant

#: Cherchee par ce qu'elle PORTE - voir `_instance_de_lot.py`.
_ETATS = "staging/text/2025-12-31_REDDITION*.txt"
CORPUS = corpus_portant(
    _ETATS,
    mesure="que le montant a repartir d'un etat des depenses est bien un TTC",
)


def _table(rows: list[dict[str, str]]) -> DataTable:
    return DataTable(path=Path("."), fields=list(rows[0]) if rows else [], rows=rows)


class LaTaxeNEstJamaisAjoutee(unittest.TestCase):
    """Vaut en CI: le total ne doit pas bouger quand une colonne de taxe existe."""

    def test_le_total_ignore_la_colonne_de_taxe(self) -> None:
        lignes = [
            {"statement_line_id": "DEP-2025-0001", "amount": "232,12", "tva": "21,10"},
            {"statement_line_id": "DEP-2025-0002", "amount": "646,72", "tva": "58,79"},
        ]
        lu = _accounting_total_charges(
            _table(lignes), _table([]), _table([]), _table([]), _table([])
        )
        self.assertEqual(lu.source, SOURCE_ETAT_DEPENSES)
        # 232,12 + 646,72 = 878,84. Avec les taxes ajoutees on lirait 958,73.
        self.assertAlmostEqual(lu.valeur, 878.84, places=2)

    def test_l_identite_de_taxe_incluse_est_celle_du_corpus(self) -> None:
        """232,12 a 10 pour cent porte 21,10 de taxe INCLUSE, pas 23,21 ajoutee."""

        montant = Decimal("232.12")
        taux = Decimal("10.00")
        self.assertEqual(taxe_incluse(montant, taux), Decimal("21.10"))
        self.assertEqual(taxe_ajoutee(montant, taux), Decimal("23.21"))


@unittest.skipUnless(CORPUS.mesurable, CORPUS.motif_de_saut)
class ConventionMesureeSurLeCorpus(unittest.TestCase):
    def test_toutes_les_lignes_a_taux_sont_des_ttc(self) -> None:
        from coproscope.modules._comptes_extraction_etat import lire_etat_depenses

        # Relu MAINTENANT. `next(...glob(...))` rendait un `StopIteration` nu
        # quand l'instance disparaissait apres le chargement du module.
        cible = CORPUS.une_piece(_ETATS)
        etat = lire_etat_depenses(cible.read_text(encoding="utf-8"))
        incluses = ajoutees = 0
        for ligne in etat.lignes:
            if ligne.taux_taxe and ligne.montant_taxe is not None:
                if abs(taxe_incluse(ligne.montant_a_repartir, ligne.taux_taxe) - ligne.montant_taxe) <= Decimal("0.01"):
                    incluses += 1
                elif abs(taxe_ajoutee(ligne.montant_a_repartir, ligne.taux_taxe) - ligne.montant_taxe) <= Decimal("0.01"):
                    ajoutees += 1
        self.assertGreater(incluses, 500)
        self.assertEqual(ajoutees, 0)


if __name__ == "__main__":
    unittest.main()
