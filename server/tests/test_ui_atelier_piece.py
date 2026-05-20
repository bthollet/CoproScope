from __future__ import annotations

import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import load_instance, write_csv
from coproscope.modules import decisionops, docuscope, incidentops
from coproscope.web.app import create_app
from coproscope.web.viewmodel import build_dashboard_model


class AtelierPieceUiTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _seed_workshop_outputs(self) -> None:
        reports_dir = self.instance.artifact("reports_dir")
        write_csv(
            reports_dir / "matrice_completude_documentaire.csv",
            docuscope.COMPLETENESS_FIELDS,
            [
                {
                    "proof_id": "PRV-PV",
                    "lot": "ag",
                    "expected_label": "PV AG signe",
                    "document_type": "PV_AG",
                    "status": "PRESENT",
                    "criticality": "P1",
                    "freshness_months": "",
                    "matched_doc_ids": "DOC-AG",
                    "evidence_paths": "DOC-AG:pv_ag_2025.txt",
                    "newest_date": "2025-05-01",
                    "reason": "Piece presente.",
                    "action": "Aucune demande.",
                },
                {
                    "proof_id": "PRV-CONTRAT",
                    "lot": "contrats",
                    "expected_label": "Contrat syndic signe",
                    "document_type": "Contrat_Syndic",
                    "status": "ABSENT",
                    "criticality": "P1",
                    "freshness_months": "",
                    "matched_doc_ids": "",
                    "evidence_paths": "",
                    "newest_date": "",
                    "reason": "Aucune piece locale ne correspond au type attendu.",
                    "action": "Demander la piece au syndic.",
                },
                {
                    "proof_id": "PRV-ASSURANCE",
                    "lot": "assurance",
                    "expected_label": "Attestation assurance recente",
                    "document_type": "Attestation_Assurance",
                    "status": "OBSOLETE",
                    "criticality": "P2",
                    "freshness_months": "12",
                    "matched_doc_ids": "DOC-OLD",
                    "evidence_paths": "DOC-OLD:assurance_2023.txt",
                    "newest_date": "2023-01-01",
                    "reason": "Version trop ancienne.",
                    "action": "Demander une version recente.",
                },
            ],
        )
        write_csv(
            reports_dir / "pieces_a_demander.csv",
            docuscope.DOCUMENT_REQUEST_FIELDS,
            [
                {
                    "request_id": "REQ-DOC-PRV-CONTRAT",
                    "source_ref": "PRV-CONTRAT",
                    "priority": "P1",
                    "status": "ABSENT",
                    "subject": "Demander au syndic: Contrat syndic signe",
                    "expected_piece": "Contrat syndic signe",
                    "reason": "Aucune piece locale ne correspond au type attendu.",
                    "related_doc_ids": "",
                    "evidence_paths": "",
                    "suggested_diligence": "Demander la piece au syndic et rattacher sa reponse au registre.",
                }
            ],
        )
        write_csv(
            decisionops.decision_register_path(self.instance),
            decisionops.DECISION_ACTION_FIELDS,
            [
                {
                    "decision_action_id": "DAP-001",
                    "ag_id": "AG-2025",
                    "source_doc_id": "DOC-AG",
                    "source_file": "pv_ag_2025.txt",
                    "resolution_ref": "R01",
                    "decision_text": "Resolution 1 - travaux toiture votes.",
                    "action_attendue": "Demander le devis signe, le calendrier et la preuve de reception.",
                    "responsable": "Syndic / commission travaux",
                    "echeance": "2025-06-15",
                    "preuve_attendue": "Devis vote et ordre de service.",
                    "proof_doc_ids": "",
                    "proof_document_types": "",
                    "related_request_ids": "",
                    "related_invoice_refs": "",
                    "related_work_refs": "",
                    "statut": "PREUVE_A_DEMANDER",
                    "priorite": "P1",
                    "notes": "Aucune preuve locale rattachee automatiquement.",
                }
            ],
        )
        write_csv(
            incidentops.incident_register_path(self.instance),
            incidentops.INCIDENT_FIELDS,
            [
                {
                    "incident_id": "INC-001",
                    "date_signalement": "2025-05-02",
                    "lieu": "Hall",
                    "description": "Infiltration signalee apres pluie.",
                    "piece_ref": "mail_syndic.txt",
                    "doc_ids": "",
                    "photo_or_piece": "",
                    "syndic_or_provider": "Syndic",
                    "status": "EN_COURS",
                    "priority": "P1",
                    "next_action": "Relancer le syndic sur la date d'intervention.",
                    "action_due_date": "2025-05-09",
                    "expected_closure_proof": "Bon d'intervention ou photo apres resolution.",
                    "closure_proof_ref": "",
                    "contract_or_insurance_ref": "",
                    "source_refs": "mail_syndic.txt",
                    "notes": "",
                }
            ],
        )

    def test_piece_workshop_links_pieces_points_actions_and_proofs(self) -> None:
        self._seed_workshop_outputs()

        model = build_dashboard_model(self.instance, 2025)
        workshop = model["piece_workshop"]

        self.assertEqual(workshop["summary"]["total"], 5)
        self.assertEqual(workshop["summary"]["docops"], 3)
        self.assertEqual(workshop["summary"]["decisions"], 1)
        self.assertEqual(workshop["summary"]["incidents"], 1)
        self.assertGreaterEqual(workshop["summary"]["needs_action"], 4)
        self.assertGreaterEqual(workshop["summary"]["with_local_proof"], 2)

        items = workshop["items"]
        self.assertTrue(
            any(
                item["piece"] == "Contrat syndic signe"
                and item["point"] == "contrats"
                and item["next_step"] == "Demander la piece au syndic et rattacher sa reponse au registre."
                for item in items
            )
        )
        self.assertTrue(
            any(item["point_type"] == "Decision AG" and "R01" in item["point"] for item in items)
        )
        self.assertTrue(
            any(
                item["point_type"] == "Incident"
                and item["piece"] == "Bon d'intervention ou photo apres resolution."
                for item in items
            )
        )

        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        client = TestClient(create_app(self.instance, 2025))
        response = client.get("/pieces")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Atelier pieces", text)
        self.assertIn("Contrat syndic signe", text)
        self.assertIn("Point de rattachement", text)
        self.assertIn("R01", text)
        self.assertIn("Bon d'intervention ou photo apres resolution.", text)


if __name__ == "__main__":
    unittest.main()
