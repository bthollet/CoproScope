from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.cli import _dispatch, build_parser
from coproscope.core.common import RunContext, load_instance, read_csv
from coproscope.modules import agscope, decisionops, docuscope


class DecisionOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.example_root = Path(self.tempdir.name) / "synthetic_copro"
        shutil.copytree(source_example, self.example_root)
        self.instance = load_instance(str(self.example_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_builds_decision_action_register_from_ag_resolutions(self) -> None:
        run = RunContext(self.instance, "decisionops")
        docuscope.inventory(self.instance, run)
        docuscope.extract_text(self.instance, run)
        docuscope.classify(self.instance, run, copy_files=False)
        agscope.analyze(self.instance, run)

        result = decisionops.build_decision_register(self.instance, run)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["decision_action_count"], 3)
        register_path = Path(str(result["register"]))
        report_path = Path(str(result["report"]))
        self.assertTrue(register_path.exists())
        self.assertTrue(report_path.exists())
        _, rows = read_csv(register_path)

        self.assertEqual({row["resolution_ref"] for row in rows}, {"R1", "R2", "R3"})
        self.assertTrue(all(row["statut"] == "CANDIDAT_AVANT_AG" for row in rows))
        self.assertTrue(all(row["echeance"] for row in rows))
        self.assertTrue(any(row["proof_document_types"] == "Contrat_Syndic" for row in rows))
        self.assertTrue(any("Devis" in row["proof_document_types"] for row in rows))
        self.assertTrue(any("Annexe_Comptable" in row["proof_document_types"] for row in rows))
        self.assertIn("Decisions ou resolutions suivies: 3", report_path.read_text(encoding="utf-8"))

    def test_missing_proof_after_pv_is_marked_as_request_needed(self) -> None:
        pv = self.example_root / "raw" / "2026-05-20_pv_ag.txt"
        pv.write_text(
            "\n".join(
                [
                    "Proces-verbal assemblee generale 2026-05-20",
                    "Resolution 4 - Decision de creer un local velo - article 24",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        run = RunContext(self.instance, "decisionops pv")
        docuscope.inventory(self.instance, run)
        docuscope.extract_text(self.instance, run)
        docuscope.classify(self.instance, run, copy_files=False)

        result = decisionops.build_decision_register(self.instance, run)

        _, rows = read_csv(Path(str(result["register"])))
        pv_rows = [row for row in rows if row["source_file"] == "2026-05-20_pv_ag.txt"]
        self.assertEqual(len(pv_rows), 1)
        self.assertEqual(pv_rows[0]["statut"], "PREUVE_A_DEMANDER")
        self.assertEqual(pv_rows[0]["proof_doc_ids"], "")

    def test_cli_builds_decision_register(self) -> None:
        run = RunContext(self.instance, "decisionops cli setup")
        docuscope.inventory(self.instance, run)
        docuscope.extract_text(self.instance, run)
        docuscope.classify(self.instance, run, copy_files=False)
        agscope.analyze(self.instance, run)

        args = build_parser().parse_args(
            [
                "decisions",
                "build",
                "--instance-root",
                str(self.example_root),
                "--no-ag-analyze",
            ]
        )

        self.assertEqual(_dispatch(args), 0)
        self.assertTrue((self.example_root / "registers" / "registre_decisions_actions_preuves.csv").exists())


if __name__ == "__main__":
    unittest.main()
