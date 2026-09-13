"""Read model du tableau de bord construit sur l'instance demo.

Extrait de `test_ui_demo.py` (603 lignes) pour tenir le plafond de 600 lignes du
depot. La fixture d'instance demo reste partagee via `DemoInstanceTestCase`.
"""

from __future__ import annotations

import unittest

from coproscope.core.common import write_csv
from coproscope.modules import decisionops, docuscope, incidentops
from coproscope.web.app import create_app
from coproscope.web.viewmodel import build_dashboard_model

from tests.test_ui_demo import DemoInstanceTestCase


class UiDemoDashboardModelTests(DemoInstanceTestCase):
    """Ce que `build_dashboard_model` agrege, plafonne et deduplique."""

    def test_dashboard_model_reads_demo_outputs_and_chantiers(self) -> None:
        _, demo = self._build_demo()
        model = build_dashboard_model(demo, 2025)

        self.assertEqual(model["instance"]["name"], "Residence Les Tilleuls")
        self.assertGreaterEqual(model["kpis"]["documents"], 6)
        self.assertGreaterEqual(model["kpis"]["invoices"], 6)
        self.assertTrue(any(module["label"] == "ComptaScope" for module in model["modules"]))
        self.assertTrue(any(stream["label"] == "Travaux suivis" for stream in model["workstreams"]))
        self.assertNotIn("demo", model)
        self.assertFalse(any(module["label"] == "Copro demo" for module in model["modules"]))
        self.assertGreaterEqual(model["action_summary"]["total"], model["action_summary"]["preview_count"])
        self.assertTrue(model["action_items"])
        self.assertIn("by_domain", model["action_summary"])
        self.assertIn("by_status", model["action_summary"])
        self.assertTrue(model["accounting"]["syndic_questions"])

    def test_dashboard_model_groups_generated_accounting_signals(self) -> None:
        _, demo = self._build_demo()
        accounting_dir = demo.artifact("accounting_dir") / "2025"
        accounting_dir.mkdir(parents=True, exist_ok=True)
        anomaly_fields = [
            "anomaly_id",
            "exercice",
            "severity",
            "status",
            "doc_id",
            "fournisseur",
            "numero_facture",
            "ttc",
            "anomaly",
            "evidence_level",
            "extraction_method",
            "evidence",
            "action",
        ]
        write_csv(
            accounting_dir / "invoice_anomalies_2025.csv",
            anomaly_fields,
            [
                {
                    "anomaly_id": f"ANOM-{index:03d}",
                    "exercice": "2025",
                    "severity": "P1" if index < 45 else "P2",
                    "status": "A_TRAITER",
                    "doc_id": f"DOC-{index:03d}",
                    "fournisseur": f"Fournisseur {index:03d}",
                    "numero_facture": f"F-{index:03d}",
                    "ttc": "100.00",
                    "anomaly": "Controle a clarifier avec le syndic.",
                    "evidence_level": "candidate",
                    "extraction_method": "local_text",
                    "evidence": f"DOC-{index:03d}",
                    "action": "Demander une confirmation au syndic.",
                }
                for index in range(80)
            ],
        )

        model = build_dashboard_model(demo, 2025)

        compta_actions = [action for action in model["action_items"] if action.get("source") == "ComptaScope"]
        self.assertLessEqual(len(compta_actions), 31)
        self.assertTrue(any("signaux regroupes" in action.get("title", "") for action in compta_actions))
        self.assertLessEqual(model["action_summary"]["scope_counts"]["comptes"], 31)

    def test_dashboard_model_deduplicates_decision_register_view(self) -> None:
        _, demo = self._build_demo()
        duplicate = {
            "decision_action_id": "DAP-DUPLICATE",
            "ag_id": "AG-2025",
            "source_doc_id": "DOC-AG",
            "source_file": "pv_ag_2025.txt",
            "resolution_ref": "R01",
            "decision_text": "Resolution 1 - travaux toiture votes.",
            "action_attendue": "Demander le devis signe.",
            "responsable": "Syndic",
            "echeance": "2025-06-15",
            "preuve_attendue": "Devis signe.",
            "proof_doc_ids": "",
            "proof_document_types": "",
            "related_request_ids": "",
            "related_invoice_refs": "",
            "related_work_refs": "",
            "statut": "PREUVE_A_DEMANDER",
            "priorite": "P1",
            "notes": "Aucune preuve locale rattachee.",
        }
        richer_duplicate = {**duplicate, "proof_doc_ids": "DOC-PROOF"}
        write_csv(
            decisionops.decision_register_path(demo),
            decisionops.DECISION_ACTION_FIELDS,
            [duplicate, richer_duplicate],
        )

        model = build_dashboard_model(demo, 2025)

        decision_summary = model["decisions"]["summary"]
        decision_actions = [action for action in model["action_items"] if action.get("domain") == "decisions"]
        self.assertEqual(decision_summary["raw_total"], 2)
        self.assertEqual(decision_summary["total"], 1)
        self.assertEqual(decision_summary["deduplicated"], 1)
        self.assertEqual(len(decision_actions), 1)
        self.assertEqual(decision_actions[0]["evidence"], "Devis signe.")

    def test_dashboard_model_surfaces_decisions_incidents_and_docops_actions(self) -> None:
        _, demo = self._build_demo()
        reports_dir = demo.artifact("reports_dir")
        write_csv(
            decisionops.decision_register_path(demo),
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
            incidentops.incident_register_path(demo),
            incidentops.INCIDENT_FIELDS,
            [
                {
                    "incident_id": "INC-001",
                    "date_signalement": "2025-05-02",
                    "lieu": "Hall",
                    "description": "Infiltration signalee apres pluie.",
                    "piece_ref": "mail_syndic.txt",
                    "doc_ids": "DOC-MAIL",
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
                    "proof_id": "PRV-ATTEST",
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

        model = build_dashboard_model(demo, 2025)

        self.assertEqual(model["decisions"]["summary"]["total"], 1)
        self.assertEqual(model["decisions"]["summary"]["missing_proofs"], 1)
        self.assertEqual(model["incidents"]["summary"]["open"], 1)
        self.assertEqual(model["documents"]["actionable"]["summary"]["to_request"], 1)
        self.assertEqual(model["documents"]["actionable"]["summary"]["obsolete"], 1)
        domains = {action["domain"] for action in model["action_items"]}
        self.assertIn("decisions", domains)
        self.assertIn("incidents", domains)
        self.assertIn("documents", domains)
        self.assertGreaterEqual(model["action_summary"]["scope_counts"]["decisions"], 1)
        self.assertGreaterEqual(model["action_summary"]["scope_counts"]["incidents"], 1)

        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        client = TestClient(create_app(demo, 2025))
        chantiers = client.get("/chantiers")
        self.assertEqual(chantiers.status_code, 200)
        self.assertIn("Memoire de copropriete", chantiers.text)
        self.assertIn("Resolution 1 - travaux toiture votes.", chantiers.text)
        self.assertIn("Hall - INC-001", chantiers.text)
        self.assertIn("Preuves essentielles", chantiers.text)
        actions_csv = client.get("/exports/actions.csv")
        self.assertIn("decisions", actions_csv.text)
        self.assertIn("incidents", actions_csv.text)


if __name__ == "__main__":
    unittest.main()
