from __future__ import annotations

import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, load_instance, relative_to, write_csv
from coproscope.web.app import create_app


class UiDocumentViewerPrivateInboxTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")
        return TestClient(create_app(self.instance, 2025))

    def test_private_inbox_detail_masks_raw_name_and_preview_until_reviewed(self) -> None:
        doc_id = "DOC-INBOX-PRIVATE"
        pdf_path = self.instance_root / "200_INBOX" / "nom_prive_original.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n% private inbox pdf\n")
        text_path = self.instance_root / "staging" / "text" / f"{doc_id}.native.txt"
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text("PRIVATE_TEXT_CANARY", encoding="utf-8")
        row = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        row.update(
            {
                "doc_id": doc_id,
                "file_name": "nom_prive_original.pdf",
                "extension": "pdf",
                "original_path": relative_to(self.instance_root, pdf_path),
                "text_path": relative_to(self.instance_root, text_path),
                "source_zone": "RAW",
                "document_type": "Facture",
                "status_ocr": "TEXT_EXTRACTED",
                "text_char_count": "19",
                "privacy_review_status": "A_REVOIR",
                "publication_form": "redaction_required",
            }
        )
        write_csv(self.instance.register("documents"), list(DEFAULT_DOCUMENT_FIELDS), [row])

        response = self._client().get(f"/documents/{doc_id}")
        body = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(doc_id, body)
        self.assertIn("apercu indisponible", body.lower())
        self.assertNotIn("nom_prive_original.pdf", body)
        self.assertNotIn("PRIVATE_TEXT_CANARY", body)
        self.assertNotIn("data:application/pdf", response.text)
        self.assertNotIn("RAW", body)

    def test_ocr_required_raw_detail_masks_original_preview(self) -> None:
        doc_id = "DOC-INBOX-OCR"
        pdf_path = self.instance_root / "200_INBOX" / "scan_original_prive.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n% ocr required pdf\n")
        row = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        row.update(
            {
                "doc_id": doc_id,
                "file_name": "scan_original_prive.pdf",
                "extension": "pdf",
                "original_path": relative_to(self.instance_root, pdf_path),
                "source_zone": "RAW",
                "document_type": "A_CLASSER",
                "classification_status": "A_CLASSER",
                "status_ocr": "OCR_REQUIRED",
                "text_char_count": "0",
                "privacy_review_status": "AUTO_POLICY",
                "publication_form": "raw",
            }
        )
        write_csv(self.instance.register("documents"), list(DEFAULT_DOCUMENT_FIELDS), [row])

        response = self._client().get(f"/documents/{doc_id}")
        body = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("apercu indisponible", body.lower())
        self.assertNotIn("scan_original_prive.pdf", body)
        self.assertNotIn("data:application/pdf", response.text)
        self.assertNotIn("RAW", body)


if __name__ == "__main__":
    unittest.main()
