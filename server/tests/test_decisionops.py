from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.cli import _dispatch, build_parser
from coproscope.core.common import RunContext, load_instance, read_csv, write_csv
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

    def test_resolution_line_filter_ignores_generic_form_wording(self) -> None:
        lines = decisionops._resolution_lines(
            "\n".join(
                [
                    "Une seule par résolution",
                    "De, en mon nom, prendre toutes résolutions nécessaires",
                    "Résolution n°1. Election du syndic",
                    "23.1- Vote de la Résolution n°3 conformément à la demande",
                ]
            ),
            ["resolution", "question", "ordre du jour", "decision"],
        )

        self.assertEqual(len(lines), 2)
        self.assertIn("Election du syndic", lines[0])

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

    def test_doc_id_build_preserves_other_existing_decision_rows(self) -> None:
        run = RunContext(self.instance, "decisionops targeted")
        docuscope.inventory(self.instance, run)
        docuscope.extract_text(self.instance, run)
        docuscope.classify(self.instance, run, copy_files=False)
        agscope.analyze(self.instance, run)
        _, docs = read_csv(self.instance.register("documents"))
        convocation = next(row for row in docs if row["file_name"] == "2026-04-29_convocation_ag.txt")

        register_path = decisionops.decision_register_path(self.instance)
        write_csv(
            register_path,
            decisionops.DECISION_ACTION_FIELDS,
            [
                {
                    "decision_action_id": "DAP-OTHER",
                    "ag_id": "AG-OTHER",
                    "source_doc_id": "DOC-OTHER",
                    "source_file": "other.pdf",
                    "resolution_ref": "R1",
                    "decision_text": "Autre decision",
                    "statut": "OPEN",
                    "priorite": "P2",
                }
            ],
        )

        decisionops.build_decision_register(self.instance, run, doc_id=convocation["doc_id"])

        _, rows = read_csv(register_path)
        self.assertTrue(any(row["source_doc_id"] == "DOC-OTHER" for row in rows))
        self.assertTrue(any(row["source_doc_id"] == convocation["doc_id"] for row in rows))


if __name__ == "__main__":
    unittest.main()
