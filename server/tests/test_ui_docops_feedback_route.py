from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import InstanceConfig, load_instance
from coproscope.web.app import create_app
from coproscope.web.docops_feedback_route import render_feedback_export_csv, save_feedback_from_form
from coproscope.web.docops_feedback_view import SYNTHETIC_DOCOPS_PROPOSALS


class UiDocOpsFeedbackRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self, access_token: str | None = "local-secret"):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")
        return TestClient(create_app(self.instance, 2025, access_token=access_token))

    def test_tri_feedback_requires_token_when_configured(self) -> None:
        response = self._client().get("/documents/tri-feedback")

        self.assertEqual(response.status_code, 403)
        self.assertNotIn("Corriger les propositions DocOps", response.text)

    def test_tri_feedback_route_is_not_shadowed_by_document_detail(self) -> None:
        client = self._client()

        response = client.get("/documents/tri-feedback?token=local-secret")
        missing = client.get("/documents/inconnu?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Corriger les propositions DocOps", response.text)
        self.assertEqual(missing.status_code, 404)
        self.assertIn("Document introuvable", missing.text)

    def test_tri_feedback_html_uses_synthetic_allowlist_without_private_paths(self) -> None:
        response = self._client().get("/documents/tri-feedback?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertIn("DOC-FICTIF-TRI-001", response.text)
        forbidden = [
            "2025-01-15_facture_entretien_jardin.txt",
            "raw\\",
            "restricted\\",
            "system\\",
            "staging\\",
            "file://",
            "C:\\",
            "/Users/",
        ]
        for marker in forbidden:
            self.assertNotIn(marker, response.text, marker)

    def test_tri_feedback_post_invalid_choice_is_rejected(self) -> None:
        proposal = SYNTHETIC_DOCOPS_PROPOSALS[0]

        response = self._client().post(
            "/documents/tri-feedback?token=local-secret",
            data={
                "doc_id": proposal["doc_id"],
                "sha256": proposal["sha256"],
                "document_type": "Facture",
                "privacy_status": "INVALID",
                "reviewer": "membre_cs_demo",
                "justification": "",
                "redaction_scope": "",
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertNotIn(proposal["sha256"], response.text)

    def test_tri_feedback_post_with_required_justification_is_accepted(self) -> None:
        proposal = SYNTHETIC_DOCOPS_PROPOSALS[1]

        missing = self._client().post(
            "/documents/tri-feedback?token=local-secret",
            data={
                "doc_id": proposal["doc_id"],
                "sha256": proposal["sha256"],
                "document_type": "Facture",
                "privacy_status": "A_MASQUER",
                "reviewer": "membre_cs_demo",
                "justification": "",
                "redaction_scope": "",
            },
        )
        self.assertEqual(missing.status_code, 422)

        missing_scope = self._client().post(
            "/documents/tri-feedback?token=local-secret",
            data={
                "doc_id": proposal["doc_id"],
                "sha256": proposal["sha256"],
                "document_type": "Facture",
                "privacy_status": "A_MASQUER",
                "reviewer": "membre_cs_demo",
                "justification": "Donnees personnelles a masquer avant partage.",
                "redaction_scope": "",
            },
        )
        self.assertEqual(missing_scope.status_code, 422)

        response = self._client().post(
            "/documents/tri-feedback?token=local-secret",
            data={
                "doc_id": proposal["doc_id"],
                "sha256": proposal["sha256"],
                "document_type": "Facture",
                "privacy_status": "A_MASQUER",
                "reviewer": "membre_cs_demo",
                "justification": "Donnees personnelles a masquer avant partage.",
                "redaction_scope": "pages 2-3",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Correction enregistree", response.text)
        register = self.instance_root / "registers" / "registre_feedback_docops.csv"
        self.assertTrue(register.exists())
        content = register.read_text(encoding="utf-8")
        self.assertIn(proposal["doc_id"], content)
        self.assertIn("tri_feedback_ui", content)
        self.assertNotIn("raw\\", content)

    def test_tri_feedback_human_fields_accept_accents_without_private_paths(self) -> None:
        proposal = SYNTHETIC_DOCOPS_PROPOSALS[1]
        client = self._client()

        accepted = client.post(
            "/documents/tri-feedback?token=local-secret",
            data={
                "doc_id": proposal["doc_id"],
                "sha256": proposal["sha256"],
                "document_type": "Facture",
                "privacy_status": "A_MASQUER",
                "reviewer": "\u00c9lodie CS",
                "justification": (
                    "Donn\u00e9es personnelles \u00e0 masquer avant partage du "
                    "proc\u00e8s-verbal."
                ),
                "redaction_scope": "pages 2 \u00e0 3",
            },
        )

        rejected = client.post(
            "/documents/tri-feedback?token=local-secret",
            data={
                "doc_id": proposal["doc_id"],
                "sha256": proposal["sha256"],
                "document_type": "Facture",
                "privacy_status": "A_MASQUER",
                "reviewer": "\u00c9lodie CS",
                "justification": "Verifier C:\\Users\\brice\\secret avant partage.",
                "redaction_scope": "pages 2 \u00e0 3",
            },
        )

        self.assertEqual(accepted.status_code, 200)
        self.assertIn("Correction enregistree", accepted.text)
        self.assertEqual(rejected.status_code, 422)

    def test_tri_feedback_exports_are_tokenized_and_derived(self) -> None:
        client = self._client()
        proposal = SYNTHETIC_DOCOPS_PROPOSALS[1]
        client.post(
            "/documents/tri-feedback?token=local-secret",
            data={
                "doc_id": proposal["doc_id"],
                "sha256": proposal["sha256"],
                "document_type": "Facture",
                "privacy_status": "A_MASQUER",
                "reviewer": "membre_cs_demo",
                "justification": "Donnees personnelles a masquer avant partage.",
                "redaction_scope": "pages 2-3",
            },
        )

        blocked = self._client().get("/exports/docops-feedback-tri.csv")
        csv_response = client.get("/exports/docops-feedback-tri.csv?token=local-secret")
        json_response = client.get("/exports/docops-feedback-tri.json?token=local-secret")

        self.assertEqual(blocked.status_code, 403)
        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(json_response.status_code, 200)
        self.assertIn("source_of_truth", csv_response.text)
        self.assertIn("dataset_kind", csv_response.text)
        self.assertIn("false", csv_response.text)
        self.assertIn("DERIVED_DOCOPS_FEEDBACK", csv_response.text)
        self.assertIn(proposal["doc_id"], csv_response.text)
        self.assertIn('"source_of_truth": false', json_response.text)
        self.assertIn('"watermark": "DERIVED_DOCOPS_FEEDBACK"', json_response.text)
        self.assertIn(proposal["doc_id"], json_response.text)
        for payload in (csv_response.text, json_response.text):
            for marker in ("raw", "restricted", "logs", "file://", "C:\\", "/Users/", "original_path", "text_path"):
                self.assertNotIn(marker, payload)

    def test_memory_feedback_fallback_is_isolated_by_instance_root(self) -> None:
        proposal = SYNTHETIC_DOCOPS_PROPOSALS[0]
        root_a = Path(self.tempdir.name) / "memory-a"
        root_b = Path(self.tempdir.name) / "memory-b"
        root_a.mkdir()
        root_b.mkdir()
        instance_a = InstanceConfig(root_a / "instance.yml", {"instance_id": "memory-a"})
        instance_b = InstanceConfig(root_b / "instance.yml", {"instance_id": "memory-b"})

        save_feedback_from_form(
            instance_a,
            {
                "doc_id": proposal["doc_id"],
                "sha256": proposal["sha256"],
                "document_type": "PV_AG",
                "privacy_status": "OUVERT_COPROPRIETAIRES",
                "reviewer": "membre_cs_demo",
                "justification": "",
                "redaction_scope": "",
            },
        )

        self.assertIn(proposal["doc_id"], render_feedback_export_csv(instance_a))
        self.assertNotIn(proposal["doc_id"], render_feedback_export_csv(instance_b))


if __name__ == "__main__":
    unittest.main()
