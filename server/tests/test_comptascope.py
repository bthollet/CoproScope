from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance, read_csv
from coproscope.modules.accounting import (
    accounting_controls,
    reconcile_invoice_expenses,
    reconstruct_accounting,
    suggest_supplier_aliases,
    supplier_aliases_from_suggestions,
)
from coproscope.modules.evidenceops import build_evidence_report
from coproscope.modules.gristops import sync_grist
from coproscope.modules.tools import tools_status


class ComptaScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.example_root = Path(self.tempdir.name) / "synthetic_copro"
        shutil.copytree(source_example, self.example_root)
        self.instance = load_instance(str(self.example_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_reconstruct_accounting_from_synthetic_invoice(self) -> None:
        run = RunContext(self.instance, "accounting reconstruct")
        result = reconstruct_accounting(self.instance, run, 2025)
        run.finish("OK", "accounting reconstruct complete")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["invoice_count"], 1)
        self.assertEqual(result["entry_count"], 1)
        self.assertTrue(Path(str(result["invoice_evidence"])).exists())
        self.assertTrue(Path(str(result["ledger_reconstruction"])).exists())
        self.assertTrue(Path(str(result["duckdb"])).exists())
        self.assertTrue(Path(str(result["invoice_expense_matches"])).exists())
        self.assertTrue(Path(str(result["report"])).exists())
        self.assertEqual(result["expense_match_counts"], {"MATCH_AMOUNT_ALIAS": 1})
        self.assertIn("supplier_alias_suggestion_count", result)

        _, invoices = read_csv(Path(str(result["invoice_evidence"])))
        self.assertEqual(invoices[0]["numero_facture"], "FAC-2025-001")
        self.assertEqual(invoices[0]["ttc"], "1200.00")
        self.assertEqual(invoices[0]["statut_controle"], "PROBABLE")
        _, matches = read_csv(Path(str(result["invoice_expense_matches"])))
        self.assertEqual(matches[0]["match_status"], "MATCH_AMOUNT_ALIAS")
        self.assertIn("alias fournisseur", matches[0]["match_reason"])
        self.assertIn("NON_RAPPROCHE", Path(str(result["report"])).read_text(encoding="utf-8"))

    def test_controls_grist_and_evidence_exports(self) -> None:
        run = RunContext(self.instance, "workers accounting dashboards")
        reconstruct_accounting(self.instance, run, 2025)
        report_path = self.example_root / "outputs" / "accounting" / "2025" / "rapport_comptascope_2025.md"
        report_path.unlink()
        controls = accounting_controls(self.instance, run, 2025)
        grist = sync_grist(self.instance, run, target="local", dataset="demo", year=2025)
        evidence = build_evidence_report(self.instance, run, dataset="demo", year=2025)
        run.finish("OK", "exports complete")

        self.assertEqual(controls["status"], "ok")
        self.assertEqual(grist["status"], "ok")
        self.assertEqual(evidence["status"], "ok")
        self.assertIn("invoice_evidence", grist["exports"])
        self.assertIn("invoice_expense_matches", grist["exports"])
        self.assertIn("supplier_alias_suggestions", grist["exports"])
        self.assertIn("rapport_comptascope", grist["exports"])
        self.assertTrue(report_path.exists())
        self.assertGreaterEqual(evidence["invoice_count"], 1)
        self.assertEqual(evidence["matched_count"], 1)
        self.assertIn("supplier_alias_suggestion_count", evidence)

    def test_tools_status_shape(self) -> None:
        status = tools_status()
        self.assertIn("checks", status)
        self.assertTrue(any(check["name"] == "duckdb" for check in status["checks"]))
        self.assertTrue(any(check["name"] == "grist_api" for check in status["checks"]))

    def test_reconciliation_explains_ambiguous_repeated_amounts(self) -> None:
        invoices = [
            {"doc_id": "DOC-1", "fournisseur": "ASV", "numero_facture": "F1", "ttc": "198.00", "compte_propose": "615000", "famille_charge": "entretien_maintenance"},
            {"doc_id": "DOC-2", "fournisseur": "ASV", "numero_facture": "F2", "ttc": "198.00", "compte_propose": "615000", "famille_charge": "entretien_maintenance"},
        ]
        expenses = [
            {
                "statement_line_id": "DEP-1",
                "account": "615000",
                "reference": "X1",
                "supplier_hint": "ASV",
                "label": "ASV / intervention",
                "amount": "198.00",
            }
        ]

        matches = reconcile_invoice_expenses(invoices, expenses)

        self.assertEqual(matches[0]["match_status"], "CANDIDAT_MONTANT_AMBIGU")
        self.assertIn("plusieurs factures", matches[0]["match_reason"])

    def test_reconciliation_can_infer_repeated_supplier_aliases(self) -> None:
        invoices = [
            {
                "doc_id": "DOC-1",
                "fournisseur": "EAU EXEMPLE",
                "numero_facture": "EAU-1",
                "ttc": "120.00",
                "compte_propose": "601000",
                "famille_charge": "energie_eau",
            },
            {
                "doc_id": "DOC-2",
                "fournisseur": "EAU EXEMPLE",
                "numero_facture": "EAU-2",
                "ttc": "240.00",
                "compte_propose": "601000",
                "famille_charge": "energie_eau",
            },
        ]
        expenses = [
            {
                "statement_line_id": "DEP-1",
                "account": "601000",
                "reference": "COMPTEUR-1",
                "supplier_hint": "EAUCO",
                "label": "EAUCO / compteur 1",
                "amount": "120.00",
            },
            {
                "statement_line_id": "DEP-2",
                "account": "601000",
                "reference": "COMPTEUR-2",
                "supplier_hint": "EAUCO",
                "label": "EAUCO / compteur 2",
                "amount": "240.00",
            },
        ]

        suggestions = suggest_supplier_aliases(invoices, expenses)
        aliases = supplier_aliases_from_suggestions(suggestions)
        matches = reconcile_invoice_expenses(invoices, expenses, aliases)

        self.assertEqual(suggestions[0]["suggestion_status"], "AUTO_APPLICABLE")
        self.assertEqual(suggestions[0]["suggested_alias"], "EAUCO")
        self.assertEqual(matches[0]["match_status"], "MATCH_AMOUNT_ALIAS")

    def test_reconstruct_can_start_from_preloaded_invoice_csv(self) -> None:
        preload = self.example_root / "system" / "accounting" / "preloaded_invoice_evidence_2025.csv"
        preload.parent.mkdir(parents=True, exist_ok=True)
        preload.write_text(
            "\n".join(
                [
                    "doc_id,fournisseur,numero_facture,date_facture,ttc,compte_propose,famille_charge,statut_controle,confidence",
                    "PRE-1,PRELOADED SERVICES,PRE-2025-001,2025-02-01,42.00,615000,entretien_maintenance,PROBABLE,preloaded",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.instance.payload.setdefault("settings", {}).setdefault("comptascope", {})["invoice_evidence_csv"] = (
            "./system/accounting/preloaded_invoice_evidence_2025.csv"
        )

        run = RunContext(self.instance, "accounting reconstruct")
        result = reconstruct_accounting(self.instance, run, 2025)
        run.finish("OK", "preloaded accounting complete")

        _, invoices = read_csv(Path(str(result["invoice_evidence"])))
        self.assertEqual(result["invoice_count"], 1)
        self.assertEqual(invoices[0]["fournisseur"], "PRELOADED SERVICES")
        self.assertEqual(invoices[0]["ttc"], "42.00")


if __name__ == "__main__":
    unittest.main()
