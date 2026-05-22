from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlparse

from coproscope.core.common import load_instance, write_csv
from coproscope.modules import decisionops, docuscope, incidentops
from coproscope.web.viewmodel import build_dashboard_model


FORBIDDEN_UX_MARKERS = ("raw", "restricted", "logs", "private", "file://", "payload")


def _hrefs(value: object, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            next_path = f"{path}.{key}"
            if (key == "href" or key.endswith("_href")) and isinstance(child, str) and child:
                yield next_path, child
            yield from _hrefs(child, next_path)
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _hrefs(child, f"{path}[{index}]")


class Cycle5MissingViewsViewmodelContractsTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)
        self._seed_cycle5_outputs()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _seed_cycle5_outputs(self) -> None:
        reports_dir = self.instance.artifact("reports_dir")
        reports_dir.mkdir(parents=True, exist_ok=True)
        write_csv(
            decisionops.decision_register_path(self.instance),
            decisionops.DECISION_ACTION_FIELDS,
            [
                {
                    "decision_action_id": "DAP-TOITURE",
                    "ag_id": "AG-2025",
                    "source_doc_id": "DOC-PV-2025",
                    "source_file": "pv_ag_2025.txt",
                    "resolution_ref": "R12",
                    "decision_text": "Resolution toiture: devis accepte et calendrier a confirmer.",
                    "action_attendue": "Relancer le syndic et obtenir ordre de service, planning et preuve de reception.",
                    "responsable": "Syndic / commission travaux",
                    "echeance": "2025-09-30",
                    "preuve_attendue": "Ordre de service et PV de reception.",
                    "proof_doc_ids": "",
                    "proof_document_types": "",
                    "related_request_ids": "REQ-TOITURE",
                    "related_invoice_refs": "",
                    "related_work_refs": "TRX-TOITURE",
                    "statut": "PREUVE_A_DEMANDER",
                    "priorite": "P1",
                    "notes": "",
                }
            ],
        )
        write_csv(
            incidentops.incident_register_path(self.instance),
            incidentops.INCIDENT_FIELDS,
            [
                {
                    "incident_id": "INC-INFILTRATION",
                    "date_signalement": "2025-07-04",
                    "lieu": "Local velo",
                    "description": "Infiltration persistante apres orage.",
                    "piece_ref": "mail_syndic.txt",
                    "doc_ids": "",
                    "photo_or_piece": "",
                    "syndic_or_provider": "Syndic",
                    "status": "EN_RELANCE",
                    "priority": "P1",
                    "next_action": "Relancer l'entreprise et dater la reprise.",
                    "action_due_date": "2025-07-12",
                    "expected_closure_proof": "Photo apres reprise et bon d'intervention.",
                    "closure_proof_ref": "",
                    "contract_or_insurance_ref": "Contrat entretien toiture",
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
                    "proof_id": "PRV-CONTRAT-SYNDIC",
                    "lot": "contrats",
                    "expected_label": "Contrat syndic signe",
                    "document_type": "Contrat_Syndic",
                    "status": "ABSENT",
                    "criticality": "P1",
                    "freshness_months": "",
                    "matched_doc_ids": "",
                    "evidence_paths": "",
                    "newest_date": "",
                    "reason": "Contrat necessaire pour reprendre les obligations.",
                    "action": "Demander la derniere version signee au syndic.",
                }
            ],
        )
        write_csv(
            reports_dir / "pieces_a_demander.csv",
            docuscope.DOCUMENT_REQUEST_FIELDS,
            [
                {
                    "request_id": "REQ-CONTRAT-SYNDIC",
                    "source_ref": "PRV-CONTRAT-SYNDIC",
                    "priority": "P1",
                    "status": "ABSENT",
                    "subject": "Contrat syndic signe",
                    "expected_piece": "Contrat syndic signe",
                    "reason": "Contrat necessaire pour reprendre les obligations.",
                    "related_doc_ids": "",
                    "evidence_paths": "",
                    "suggested_diligence": "Demander la derniere version signee au syndic.",
                }
            ],
        )

    def assertLocalHref(self, href: str, path: str) -> None:
        decoded = unquote(href)
        parsed = urlparse(decoded)
        self.assertFalse(parsed.scheme or parsed.netloc, f"{path} must be local: {href!r}")
        self.assertTrue(decoded.startswith("/") or decoded.startswith("#"), f"{path} must be a local path: {href!r}")
        self.assertNotIn("\\", decoded, f"{path} must not contain backslashes: {href!r}")
        self.assertNotIn("://", decoded, f"{path} must not contain a URL scheme: {href!r}")

    def assertNoForbiddenUxMarkers(self, payload: object) -> None:
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).replace("\\", "/").lower()
        self.assertNotIn(str(self.instance_root).replace("\\", "/").lower(), serialized)
        for marker in FORBIDDEN_UX_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotRegex(serialized, rf"(^|[^a-z]){re.escape(marker)}([^a-z]|$)")

    def test_priority_views_cover_late_actions_missing_pieces_and_syndic_followups(self) -> None:
        ux = build_dashboard_model(self.instance, 2025)["ux"]
        priority_views = ux["priority_views"]

        late = priority_views["late_actions"]
        missing = priority_views["missing_pieces"]
        followups = priority_views["syndic_followups"]

        self.assertEqual(late["context"]["route"], "/actions?view=retards")
        self.assertEqual(missing["context"]["route"], "/pieces?proof=missing")
        self.assertEqual(followups["context"]["route"], "/demandes/relance")
        self.assertTrue(late["items"])
        self.assertTrue(missing["items"])
        self.assertTrue(followups["items"])

        for item in late["items"]:
            for field in ["id", "title", "delay_label", "expected_proof", "next_step", "href", "followup_href", "piece_href", "memory_href"]:
                self.assertIn(field, item)
        for item in missing["items"]:
            for field in ["expected_piece", "reason", "proof_purpose", "status_label", "request_href", "deposit_href"]:
                self.assertIn(field, item)
        for item in followups["items"]:
            self.assertIn(item["status"], {"draft", "ready_to_copy"})
            self.assertNotIn("Envoyee", item["status_label"])
            self.assertIn("draft", item)
            self.assertIn("body", item["draft"])
            self.assertNotIn("note interne", json.dumps(item["draft"], ensure_ascii=False).lower())

        self.assertNoForbiddenUxMarkers(priority_views)
        for path, href in _hrefs(priority_views):
            with self.subTest(href_path=path):
                self.assertLocalHref(href, path)

    def test_action_and_memory_detail_contracts_are_public_and_actionable(self) -> None:
        ux = build_dashboard_model(self.instance, 2025)["ux"]
        action_detail = ux["action_detail"]
        memoire = ux["memoire"]
        selected_event = memoire["selected_event"]

        self.assertEqual(action_detail["context"]["route"], "/actions")
        self.assertEqual(action_detail["context"]["selected_id"], ux["registre"]["selected"]["id"])
        self.assertTrue(action_detail["selected"]["next_step"])
        self.assertIn(action_detail["proofs"]["state"], {"missing", "candidate", "verified", "rejected", "blocked"})
        self.assertTrue(action_detail["proofs"]["state_label"])
        self.assertIsInstance(action_detail["handover"]["missing_for_handover"], list)
        self.assertIn("reason", action_detail["share"])

        self.assertEqual(memoire["context"]["route"], "/chantiers")
        self.assertEqual(ux["event_detail"]["id"], selected_event["id"])
        self.assertEqual(1, len([event for event in memoire["timeline"] if event.get("is_selected")]))
        self.assertIn("why_in_memory", selected_event)
        self.assertIn("proofs", selected_event)
        self.assertEqual({"verified", "candidates", "missing"}, set(selected_event["proofs"].keys()))
        self.assertIsInstance(selected_event["passation"]["include_in_handover"], bool)
        self.assertTrue(selected_event["restriction"]["label"])
        self.assertTrue(selected_event["restriction"]["reason"])
        if selected_event["documents"]:
            self.assertIn("why_linked", selected_event["documents"][0])

        self.assertNoForbiddenUxMarkers({"action_detail": action_detail, "memoire": memoire, "event_detail": ux["event_detail"]})

    def test_passation_export_contract_exposes_preview_blockers_and_safe_formats(self) -> None:
        ux = build_dashboard_model(self.instance, 2025)["ux"]
        export = ux["passation_export"]
        preview = ux["passation_export_preview"]

        self.assertEqual(export["context"]["route"], "/exports/passation")
        self.assertEqual(preview["context"]["route"], "/exports/passation")
        self.assertFalse(preview["source_of_truth"])
        self.assertTrue(preview["watermark"])
        self.assertFalse(export["context"]["source_of_truth"])
        self.assertFalse(export["audit"]["source_of_truth"])
        self.assertTrue(preview["sections_included"])
        self.assertIn("formats_available", preview)
        self.assertEqual({"txt", "json"}, {format_item["id"] for format_item in preview["formats_available"]})
        self.assertIn("excluded_or_blocked", preview)
        self.assertEqual(export["summary"]["can_export"], not bool(export["blockers"]))
        self.assertEqual(export["downloads"]["can_download"], export["summary"]["can_export"])
        for format_item in export["formats"]:
            self.assertEqual(format_item["enabled"], export["downloads"]["can_download"])
            self.assertLocalHref(format_item["href"], f"formats.{format_item['id']}.href")
        for item in export["omitted"]["items"]:
            for field in ["label", "reason", "type_label"]:
                self.assertIn(field, item)
        checklist_ids = {item["id"] for item in export["checklist"]}
        self.assertTrue({"audience", "restrictions", "missing-proofs", "watermark"}.issubset(checklist_ids))
        self.assertNoForbiddenUxMarkers({"export": export, "preview": preview})
        for path, href in _hrefs({"export": export, "preview": preview}):
            with self.subTest(href_path=path):
                self.assertLocalHref(href, path)

    def test_action_filters_render_coherent_models_for_missing_views(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError as exc:
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        from coproscope.web.app import create_app

        client = TestClient(create_app(self.instance, 2025), raise_server_exceptions=False)
        for route, expected in [
            ("/actions?priority=P1", "Registre des decisions"),
            ("/actions?scope=syndic", "Syndic"),
            ("/actions?status=a_demander", "Demander au syndic"),
        ]:
            with self.subTest(route=route):
                response = client.get(route)
                text = unescape(response.text)
                self.assertEqual(response.status_code, 200)
                self.assertIn(expected, text)
                for marker in ("raw/", "restricted/", "logs/", "file://", str(self.instance_root)):
                    self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
