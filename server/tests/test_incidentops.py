from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance, read_csv
from coproscope.modules import docuscope, incidentops


class IncidentOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.example_root = Path(self.tempdir.name) / "synthetic_copro"
        shutil.copytree(source_example, self.example_root)
        self.instance = load_instance(str(self.example_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_build_register_detects_incident_and_exports_open_items(self) -> None:
        signalement = self.example_root / "raw" / "2026-05-03_signalement_fuite_parking.txt"
        signalement.write_text(
            "\n".join(
                [
                    "Signalement incident",
                    "Lieu: Parking niveau -1",
                    "Fuite persistante sur canalisation commune.",
                    "Photo jointe a demander au syndic.",
                ]
            ),
            encoding="utf-8",
        )

        run = RunContext(self.instance, "incidentops test")
        docuscope.inventory(self.instance, run)
        docuscope.extract_text(self.instance, run)

        result = incidentops.build_incident_register(self.instance, run)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["incident_count"], 1)
        self.assertEqual(result["open_incident_count"], 1)
        self.assertEqual(result["open_incident_issue_count"], 0)

        _, incidents = read_csv(Path(result["incident_register"]))
        self.assertEqual(len(incidents), 1)
        row = incidents[0]
        self.assertEqual(row["date_signalement"], "2026-05-03")
        self.assertEqual(row["lieu"], "Parking niveau -1")
        self.assertEqual(row["status"], "A_QUALIFIER")
        self.assertTrue(row["next_action"])
        self.assertTrue(row["expected_closure_proof"])
        self.assertTrue(row["action_due_date"])

        _, open_rows = read_csv(Path(result["open_incidents_export"]))
        self.assertEqual([item["incident_id"] for item in open_rows], [row["incident_id"]])
        self.assertTrue(Path(result["incident_report"]).exists())

    def test_open_export_excludes_closed_incidents(self) -> None:
        run = RunContext(self.instance, "incidentops manual test")
        register = incidentops.write_incident_register(
            self.instance,
            run,
            [
                {
                    "date_signalement": "2026-04-12",
                    "lieu": "Hall",
                    "description": "Panne eclairage hall",
                    "status": "EN_COURS",
                    "syndic_or_provider": "Entreprise maintenance",
                },
                {
                    "date_signalement": "2026-04-01",
                    "lieu": "Local technique",
                    "description": "Intervention terminee",
                    "status": "CLOTURE",
                    "closure_proof_ref": "PV intervention",
                },
            ],
        )
        export = incidentops.export_open_incidents(self.instance, run)

        _, all_rows = read_csv(register)
        _, open_rows = read_csv(export)

        self.assertEqual(len(all_rows), 2)
        self.assertEqual(len(open_rows), 1)
        self.assertEqual(open_rows[0]["status"], "EN_COURS")
        self.assertIn("Relancer Entreprise maintenance", open_rows[0]["next_action"])
        self.assertTrue(open_rows[0]["expected_closure_proof"])

    def test_validate_open_incidents_requires_action_and_expected_proof(self) -> None:
        issues = incidentops.validate_open_incidents(
            [
                {
                    "incident_id": "INC-TEST",
                    "status": "EN_COURS",
                    "next_action": "",
                    "expected_closure_proof": "",
                }
            ]
        )

        self.assertEqual(
            issues,
            [
                {
                    "incident_id": "INC-TEST",
                    "missing": "next_action;expected_closure_proof",
                    "status": "EN_COURS",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
