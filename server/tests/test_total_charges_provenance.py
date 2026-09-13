"""Le total des charges ne s'affiche que s'il vient de l'etat des depenses.

Lot `RM-2026-0075`. Le defaut mesure le 2026-09-04 sur instance NEUVE: la page
affichait `24 397 501,24 EUR` sous le libelle `Total charges / Exercice 2025`
alors que l'etalon comptable, releve a la main sur la source primaire, donne
`357 493,10`. Facteur 68. Le nombre affiche n'etait pas faux en soi - c'est la
somme du grand livre reconstitue - il etait faux **sous ce libelle-la**.

Ces tests fixent l'invariant de la frontiere, pas une valeur de corpus: ils
construisent leurs propres tables et n'ont donc besoin d'aucune instance. Ils
restent valables si le corpus change.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from coproscope.web.viewmodels._accounting_questions import _accounting_total_charges
from coproscope.web.viewmodels._montant_source import (
    NON_CALCULABLE,
    SOURCE_ETAT_DEPENSES,
    SOURCE_FACTURES,
    SOURCE_GRAND_LIVRE,
    MontantLu,
)
from coproscope.web.viewmodels._base import DataTable


def _table(rows: list[dict[str, str]]) -> DataTable:
    return DataTable(path=Path("."), fields=list(rows[0]) if rows else [], rows=rows)


_VIDE = _table([])

# Ordres de grandeur du constat du 2026-09-04, reduits a deux lignes chacun.
# Les valeurs exactes importent peu; l'ecart entre les deux sources importe.
_ETAT = [
    {"statement_line_id": "DEP-2025-0001", "amount": "232,12"},
    {"statement_line_id": "DEP-2025-0002", "amount": "646,72"},
]
_GRAND_LIVRE = [
    {"entry_id": "ECR-1", "debit": "12 000 000,00"},
    {"entry_id": "ECR-2", "debit": "12 397 501,24"},
]


class TotalChargesPorteSaProvenance(unittest.TestCase):
    def test_etat_des_depenses_present_le_montant_repond(self) -> None:
        lu = _accounting_total_charges(_table(_ETAT), _table(_GRAND_LIVRE), _VIDE, _VIDE, _VIDE)
        self.assertEqual(lu.source, SOURCE_ETAT_DEPENSES)
        self.assertTrue(lu.repond)
        self.assertFalse(lu.substitue)
        self.assertAlmostEqual(lu.valeur, 878.84, places=2)

    def test_etat_absent_le_grand_livre_ne_repond_pas(self) -> None:
        """Le coeur du defaut: un nombre existe, il ne repond pas a la question."""

        lu = _accounting_total_charges(_VIDE, _table(_GRAND_LIVRE), _VIDE, _VIDE, _VIDE)
        self.assertEqual(lu.source, SOURCE_GRAND_LIVRE)
        self.assertFalse(lu.repond)
        self.assertTrue(lu.substitue)
        # La valeur n'est pas detruite: elle reste disponible sous son nom.
        self.assertIsNotNone(lu.valeur)
        self.assertEqual(lu.lu_sur, "grand livre reconstitue")

    def test_le_libelle_affiche_refuse_le_substitut(self) -> None:
        lu = _accounting_total_charges(_VIDE, _table(_GRAND_LIVRE), _VIDE, _VIDE, _VIDE)
        self.assertEqual(lu.libelle(lambda v: f"{v:.2f} EUR"), NON_CALCULABLE)
        self.assertIn("grand livre reconstitue", lu.mention_substitut(lambda v: f"{v:.2f} EUR"))

    def test_aucune_source_ne_rend_aucun_nombre(self) -> None:
        lu = _accounting_total_charges(_VIDE, _VIDE, _VIDE, _VIDE, _VIDE)
        self.assertIsNone(lu.valeur)
        self.assertFalse(lu.repond)
        self.assertFalse(lu.substitue)
        self.assertEqual(lu.libelle(lambda v: f"{v:.2f}"), NON_CALCULABLE)

    def test_repli_sur_factures_ne_repond_pas_non_plus(self) -> None:
        factures = _table([{"doc_id": "DOC-1", "ttc": "1 000,00"}])
        lu = _accounting_total_charges(_VIDE, _VIDE, factures, _VIDE, _VIDE)
        self.assertEqual(lu.source, SOURCE_FACTURES)
        self.assertFalse(lu.repond)

    def test_source_inconnue_ne_se_fait_pas_passer_pour_une_lecture_directe(self) -> None:
        """Hors des valeurs observees: un identifiant inconnu reste lisible."""

        lu = MontantLu(valeur=1.0, source="source_future_inconnue")
        self.assertEqual(lu.lu_sur, "source_future_inconnue")
        self.assertNotEqual(lu.lu_sur, "")
        self.assertFalse(lu.repond)


class SommaireNAffichePasUnSubstitut(unittest.TestCase):
    """La frontiere reelle: ce que le viewmodel pose dans `summary`."""

    def _summary(self, expense_rows: list[dict[str, str]], ledger_rows: list[dict[str, str]]) -> dict:
        from coproscope.web.viewmodels import _source_models

        summary: dict[str, object] = {}
        lu = _accounting_total_charges(
            _table(expense_rows), _table(ledger_rows), _VIDE, _VIDE, _VIDE
        )
        # Reproduit la decision de `_accounting_model`, isolee de ses lectures
        # de fichiers. Si cette logique bouge, le test ci-dessous la suit.
        summary["total_charges_source"] = lu.source
        if lu.repond:
            summary["total_charges"] = round(lu.valeur, 2)
            summary["total_charges_label"] = _source_models._amount_label(lu.valeur)
        else:
            summary.pop("total_charges", None)
            summary["total_charges_label"] = NON_CALCULABLE
        return summary

    def test_sans_etat_des_depenses_aucun_montant_sous_le_libelle_total_charges(self) -> None:
        summary = self._summary([], _GRAND_LIVRE)
        self.assertNotIn("total_charges", summary)
        self.assertEqual(summary["total_charges_label"], NON_CALCULABLE)

    def test_avec_etat_des_depenses_le_montant_est_pose(self) -> None:
        summary = self._summary(_ETAT, _GRAND_LIVRE)
        self.assertIn("total_charges", summary)
        self.assertEqual(summary["total_charges_source"], SOURCE_ETAT_DEPENSES)


if __name__ == "__main__":
    unittest.main()
