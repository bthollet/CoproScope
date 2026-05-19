from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance, read_csv
from coproscope.modules.accounting import accounting_controls, reconstruct_accounting
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

        _, invoices = read_csv(Path(str(result["invoice_evidence"])))
        self.assertEqual(invoices[0]["numero_facture"], "FAC-2025-001")
        self.assertEqual(invoices[0]["ttc"], "1200.00")
        self.assertEqual(invoices[0]["statut_controle"], "PROBABLE")

    def test_controls_grist_and_evidence_exports(self) -> None:
        run = RunContext(self.instance, "workers accounting dashboards")
        reconstruct_accounting(self.instance, run, 2025)
        controls = accounting_controls(self.instance, run, 2025)
        grist = sync_grist(self.instance, run, target="local", dataset="demo", year=2025)
        evidence = build_evidence_report(self.instance, run, dataset="demo", year=2025)
        run.finish("OK", "exports complete")

        self.assertEqual(controls["status"], "ok")
        self.assertEqual(grist["status"], "ok")
        self.assertEqual(evidence["status"], "ok")
        self.assertIn("invoice_evidence", grist["exports"])
        self.assertGreaterEqual(evidence["invoice_count"], 1)

    def test_tools_status_shape(self) -> None:
        status = tools_status()
        self.assertIn("checks", status)
        self.assertTrue(any(check["name"] == "duckdb" for check in status["checks"]))
        self.assertTrue(any(check["name"] == "grist_api" for check in status["checks"]))


if __name__ == "__main__":
    unittest.main()
