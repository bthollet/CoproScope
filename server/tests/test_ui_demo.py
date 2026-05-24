from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import RunContext, load_instance, read_csv, write_csv
from coproscope.modules import decisionops, docuscope, incidentops
from coproscope.modules.demoops import build_demo_instance
from coproscope.web.app import create_app, serve
from coproscope.web.depot import (
    DepositError,
    create_deposit_from_uploads,
    deposit_manifest_path,
    read_deposit_manifest,
    write_deposit_manifest,
)
from coproscope.web.viewmodel import build_dashboard_model


class UiAndDemoTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.source_root = Path(self.tempdir.name) / "source"
        self.demo_root = Path(self.tempdir.name) / "demo_public"
        shutil.copytree(source_example, self.source_root)
        self.source = load_instance(str(self.source_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _build_demo(self):
        run = RunContext(self.source, "demo build test")
        result = build_demo_instance(
            self.source,
            run,
            output_instance=self.demo_root,
            mode="fictive",
            year=2025,
            run_source_audit=True,
            max_text_chars=8000,
        )
        run.finish("OK", "demo build test complete")
        return result, load_instance(str(self.demo_root / "instance.yml"), None)

    def test_demo_build_creates_fictive_publishable_instance(self) -> None:
        result, demo = self._build_demo()

        self.assertEqual(result["status"], "ok")
        self.assertTrue((self.demo_root / "instance.yml").exists())
        self.assertTrue((self.demo_root / "demo_manifest.json").exists())
        self.assertTrue((self.demo_root / "outputs" / "accounting" / "2025" / "summary_2025.json").exists())
        self.assertFalse((self.demo_root / "restricted" / "C8_local_only" / "table_correspondance_biffage.csv").exists())
        self.assertEqual(demo.display_name, "Residence Les Tilleuls")

        public_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in self.demo_root.rglob("*")
            if path.is_file()
            and "restricted" not in path.parts
            and path.suffix.lower() in {".txt", ".md", ".csv", ".json", ".yml"}
        )
        self.assertNotIn("Residence Les Platanes", public_text)
        self.assertNotIn("synthetic-copro", public_text)
        self.assertIn("Residence Les Tilleuls", public_text)
        self.assertIn("APPROVED_FICTIVE_DEMO", public_text)

    def test_dashboard_model_reads_demo_outputs_and_chantiers(self) -> None:
        _, demo = self._build_demo()
        model = build_dashboard_model(demo, 2025)

        self.assertEqual(model["instance"]["name"], "Residence Les Tilleuls")
        self.assertGreaterEqual(model["kpis"]["documents"], 6)
        self.assertGreaterEqual(model["kpis"]["invoices"], 6)
        self.assertTrue(any(module["label"] == "ComptaScope" for module in model["modules"]))
        self.assertTrue(any(stream["label"] == "WorksOps" for stream in model["workstreams"]))
        self.assertNotIn("demo", model)
        self.assertFalse(any(module["label"] == "Copro demo" for module in model["modules"]))
        self.assertGreaterEqual(model["action_summary"]["total"], model["action_summary"]["preview_count"])
        self.assertTrue(model["action_items"])
        self.assertIn("by_domain", model["action_summary"])
        self.assertIn("by_status", model["action_summary"])
        self.assertTrue(model["accounting"]["syndic_questions"])

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

    def test_local_web_routes_render_without_serving_private_roots(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        _, demo = self._build_demo()
        client = TestClient(create_app(demo, 2025))

        for path in [
            "/",
            "/actions",
            "/actions?scope=comptes",
            "/exports/actions.csv",
            "/exports/actions.md",
            "/comptes",
            "/documents",
            "/confidentialite",
            "/chantiers",
            "/depot",
            "/api/model",
            "/exports/local.zip",
            "/health",
        ]:
            response = client.get(path)
            self.assertEqual(response.status_code, 200, path)

        csv_export = client.get("/exports/actions.csv")
        self.assertIn("priority,status,domain,source", csv_export.text)
        markdown_export = client.get("/exports/actions.md?scope=comptes")
        self.assertIn("# Actions CoproScope", markdown_export.text)

        for forbidden in ["/demo", "/raw/2025-01-18_facture_entretien_jardin.txt", "/restricted/secret.txt", "/.env.local"]:
            response = client.get(forbidden)
            self.assertEqual(response.status_code, 404, forbidden)

    def test_depot_upload_pipeline_buttons_and_safe_export_zip(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        _, demo = self._build_demo()
        client = TestClient(create_app(demo, 2025))

        upload = client.post(
            "/depot",
            files=[
                (
                    "files",
                    (
                        "2026-05-20_note_syndic.txt",
                        b"Note syndic fictive\nConvocation AG et devis travaux a verifier.\n",
                        "text/plain",
                    ),
                )
            ],
            follow_redirects=False,
        )
        self.assertEqual(upload.status_code, 303)

        manifests = sorted((self.demo_root / "outputs" / "deposits").glob("DEPOT-*.json"))
        self.assertEqual(len(manifests), 1)
        manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
        deposit_id = manifest["deposit_id"]
        self.assertTrue((self.demo_root / manifest["files"][0]["path"]).exists())
        self.assertTrue(manifest["doc_ids"])
        step_names = [step["name"] for step in manifest["steps"]]
        self.assertIn("inventory", step_names)
        self.assertTrue(any(name.startswith("extract_text:") for name in step_names))
        self.assertIn("classify", step_names)
        self.assertIn("privacy_screening", step_names)
        self.assertIn("redaction_queue", step_names)

        _, document_rows = read_csv(demo.register("documents"))
        uploaded = [row for row in document_rows if row.get("file_name") == "2026-05-20_note_syndic.txt"]
        self.assertEqual(len(uploaded), 1)
        self.assertEqual(uploaded[0]["status_ocr"], "TEXT_EXTRACTED")
        self.assertNotEqual(uploaded[0]["classification_status"], "PENDING")

        with patch("coproscope.web.depot.docai.process_after_native_extract", return_value=demo.register("documents")):
            response = client.post(f"/depot/{deposit_id}/pipeline/docai", follow_redirects=False)
            self.assertEqual(response.status_code, 303, "docai")
        for pipeline in ["docops", "compta"]:
            response = client.post(f"/depot/{deposit_id}/pipeline/{pipeline}", follow_redirects=False)
            self.assertEqual(response.status_code, 303, pipeline)

        updated = json.loads(manifests[0].read_text(encoding="utf-8"))
        updated_step_names = [step["name"] for step in updated["steps"]]
        self.assertTrue(any(name.startswith("docai_local_heavy:") for name in updated_step_names))
        self.assertIn("missing_docs", updated_step_names)
        self.assertIn("invoices", updated_step_names)

        forbidden = client.get(f"/raw/_depot_ui/{deposit_id}/2026-05-20_note_syndic.txt")
        self.assertEqual(forbidden.status_code, 404)

        export = client.get("/exports/local.zip")
        self.assertEqual(export.status_code, 200)
        with zipfile.ZipFile(BytesIO(export.content)) as archive:
            names = archive.namelist()
            deposit_manifest = archive.read(f"outputs/deposits/{deposit_id}.json").decode("utf-8")
        self.assertIn("exports/coproscope_actions_2025.csv", names)
        self.assertIn(f"outputs/deposits/{deposit_id}.json", names)
        self.assertIn("[reference locale masquee]", deposit_manifest)
        self.assertNotIn("raw/_depot_ui", deposit_manifest)
        self.assertFalse(any(name.startswith("raw/") for name in names))
        self.assertFalse(any(name.startswith("restricted/") for name in names))
        self.assertFalse(any(name.startswith("logs/") for name in names))
        self.assertFalse(any("/private/" in name or name.startswith("outputs/evidence/private/") for name in names))
        self.assertFalse(any(".env" in name or "table_correspondance" in name or "mapping" in name for name in names))

    def test_deposit_manifest_rejects_path_traversal_and_ignores_payload_id(self) -> None:
        _, demo = self._build_demo()
        raw_evil = self.demo_root / "raw" / "evil.json"
        raw_evil.write_text(
            json.dumps({"deposit_id": "../../raw/rewritten", "status": "attacker-controlled"}),
            encoding="utf-8",
        )

        self.assertIsNone(read_deposit_manifest(demo, "../../raw/evil"))
        self.assertIsNone(read_deposit_manifest(demo, "DEPOT-not-a-date"))

        legit_id = "DEPOT-20260520T120000Z"
        legit_path = deposit_manifest_path(demo, legit_id)
        legit_path.write_text(
            json.dumps({"deposit_id": "../../raw/rewritten", "status": "ok"}),
            encoding="utf-8",
        )
        manifest = read_deposit_manifest(demo, legit_id)
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["deposit_id"], legit_id)

        write_deposit_manifest(demo, manifest)
        self.assertTrue(legit_path.exists())
        self.assertFalse((self.demo_root / "raw" / "rewritten.json").exists())
        with self.assertRaises(DepositError):
            write_deposit_manifest(demo, {"deposit_id": "../../raw/rewritten"})

    def test_deposit_upload_rejects_empty_and_unsupported_files(self) -> None:
        _, demo = self._build_demo()

        class FakeUpload:
            def __init__(self, filename: str, payload: bytes) -> None:
                self.filename = filename
                self.file = BytesIO(payload)

        with self.assertRaises(DepositError):
            create_deposit_from_uploads(demo, [FakeUpload("payload.exe", b"not allowed")])
        with self.assertRaises(DepositError):
            create_deposit_from_uploads(demo, [FakeUpload("empty.txt", b"")])

        self.assertFalse((self.demo_root / "raw" / "_depot_ui").exists())

    def test_token_guard_protects_sensitive_ui_routes(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        _, demo = self._build_demo()
        client = TestClient(create_app(demo, 2025, access_token="local-secret"))

        self.assertEqual(client.get("/depot").status_code, 403)
        self.assertEqual(client.get("/api/model").status_code, 403)
        self.assertEqual(client.get("/exports/local.zip").status_code, 403)

        self.assertEqual(client.get("/depot?token=local-secret").status_code, 200)
        self.assertEqual(client.get("/api/model", headers={"x-coproscope-token": "local-secret"}).status_code, 200)
        self.assertEqual(client.get("/exports/local.zip?token=local-secret").status_code, 200)

    def test_serve_refuses_lan_without_explicit_unsafe_flag(self) -> None:
        _, demo = self._build_demo()

        with self.assertRaises(ValueError):
            serve(demo, 2025, host="0.0.0.0", port=8765, access_token="local-secret")

    def test_ui_open_test_uses_visible_foreground_server_options(self) -> None:
        _, demo = self._build_demo()
        from coproscope.cli import _dispatch, build_parser

        args = build_parser().parse_args(
            [
                "ui",
                "open-test",
                "--instance-root",
                str(demo.instance_root),
                "--year",
                "2025",
                "--host",
                "127.0.0.1",
                "--port",
                "8769",
                "--token",
                "qa-2000-local",
            ]
        )
        with patch("coproscope.web.app.serve") as mocked_serve:
            result = _dispatch(args)

        self.assertEqual(result, 0)
        mocked_serve.assert_called_once()
        _, kwargs = mocked_serve.call_args
        self.assertEqual(kwargs["year"], 2025)
        self.assertEqual(kwargs["host"], "127.0.0.1")
        self.assertEqual(kwargs["port"], 8769)
        self.assertEqual(kwargs["access_token"], "qa-2000-local")
        self.assertFalse(kwargs["unsafe_lan"])


if __name__ == "__main__":
    unittest.main()
