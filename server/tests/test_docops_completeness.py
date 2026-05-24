from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance, read_csv, write_csv
from coproscope.modules import docuscope


class DocOpsCompletenessTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.example_root = Path(self.tempdir.name) / "synthetic_copro"
        shutil.copytree(source_example, self.example_root)
        self.instance = load_instance(str(self.example_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _prepare_classified_documents(self) -> None:
        run = RunContext(self.instance, "docops completeness setup")
        docuscope.inventory(self.instance, run)
        docuscope.extract_text(self.instance, run)
        docuscope.classify(self.instance, run, copy_files=False)

    def test_email_trace_is_classified_as_communication_document(self) -> None:
        raw_email = self.example_root / "raw" / "2026-05-13_echange_syndic.txt"
        raw_email.write_text(
            "\n".join(
                [
                    "Sujet: pieces de copropriete",
                    "Email recu du syndic concernant les pieces attendues.",
                    "Le conseil syndical conserve cette trace locale comme preuve de suivi.",
                ]
            ),
            encoding="utf-8",
        )

        self._prepare_classified_documents()

        _, rows = read_csv(self.instance.register("documents"))
        email_rows = [row for row in rows if row.get("file_name") == raw_email.name]

        self.assertEqual(len(email_rows), 1)
        self.assertEqual(email_rows[0]["lot"], "Communication")
        self.assertEqual(email_rows[0]["document_type"], "Communication")
        self.assertEqual(email_rows[0]["classification_status"], "AUTO_CLASSIFIED")

    def test_actionable_matrix_distinguishes_present_missing_stale_and_classification_doubt(self) -> None:
        self._prepare_classified_documents()
        proofs_path = self.instance.matrix("proofs")
        assert proofs_path is not None
        write_csv(
            proofs_path,
            ["proof_id", "lot", "expected_label", "document_type", "criticality", "freshness_months"],
            [
                {
                    "proof_id": "PRV-CONV",
                    "lot": "AG",
                    "expected_label": "Convocation AG et annexes",
                    "document_type": "Convocation_AG",
                    "criticality": "P1",
                    "freshness_months": "",
                },
                {
                    "proof_id": "PRV-SYN",
                    "lot": "Syndic",
                    "expected_label": "Contrat syndic en cours",
                    "document_type": "Contrat_Syndic",
                    "criticality": "P0",
                    "freshness_months": "24",
                },
                {
                    "proof_id": "PRV-ITE",
                    "lot": "ITE_Travaux",
                    "expected_label": "Chronologie et devis travaux",
                    "document_type": "Dossier_ITE_Travaux",
                    "criticality": "P1",
                    "freshness_months": "",
                },
                {
                    "proof_id": "PRV-ASS",
                    "lot": "Assurance",
                    "expected_label": "Contrat assurance immeuble",
                    "document_type": "Contrat_Assurance",
                    "criticality": "P1",
                    "freshness_months": "",
                },
            ],
        )

        documents_path = self.instance.register("documents")
        fields, rows = read_csv(documents_path)
        for row in rows:
            if row.get("document_type") == "Contrat_Syndic":
                row["suspected_date"] = "2020-01-15"
            if row.get("file_name") == "2026-03-01_devis_toiture.txt":
                row["lot"] = "ITE_Travaux"
                row["document_type"] = "A_CLASSER"
                row["classification_status"] = "A_CLASSER"
        write_csv(documents_path, fields, rows)

        run = RunContext(self.instance, "docops completeness")
        report_path = docuscope.missing_docs(self.instance, run)

        reports_dir = self.instance.artifact("reports_dir")
        _, matrix_rows = read_csv(reports_dir / "matrice_completude_documentaire.csv")
        _, request_rows = read_csv(reports_dir / "pieces_a_demander.csv")
        _, finding_rows = read_csv(self.instance.register("findings"))
        statuses = {row["proof_id"]: row["status"] for row in matrix_rows}

        self.assertEqual(statuses["PRV-CONV"], "PRESENT")
        self.assertEqual(statuses["PRV-SYN"], "OBSOLETE")
        self.assertEqual(statuses["PRV-ITE"], "A_CLASSER")
        self.assertEqual(statuses["PRV-ASS"], "ABSENT")
        self.assertEqual({row["source_ref"] for row in request_rows}, {"PRV-SYN", "PRV-ITE", "PRV-ASS"})
        self.assertTrue(any(row.get("source_ref") == "PRV-ASS" for row in finding_rows))
        self.assertIn("## Pieces a demander", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
