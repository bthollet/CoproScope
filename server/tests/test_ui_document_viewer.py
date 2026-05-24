from __future__ import annotations

import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, load_instance, read_csv, relative_to, write_csv
from coproscope.web.app import create_app
from coproscope.web.document_viewer import build_document_detail


class DocumentViewerUiTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")
        return TestClient(create_app(self.instance, 2025))

    def _documents(self) -> tuple[list[str], list[dict[str, str]]]:
        fields, rows = read_csv(self.instance.register("documents"))
        return fields or list(DEFAULT_DOCUMENT_FIELDS), rows

    def _write_documents(self, fields: list[str], rows: list[dict[str, str]]) -> None:
        write_csv(self.instance.register("documents"), fields, rows)

    def test_document_detail_route_renders_synthetic_document(self) -> None:
        fields, rows = self._documents()
        doc = rows[0]
        text = "Texte local extrait pour la fiche securisee.\nAucune reponse fichier brut n'est attendue.\n"
        text_path = self.instance_root / "staging" / "text" / f"{doc['doc_id']}.preview.txt"
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(text, encoding="utf-8")
        doc["text_path"] = relative_to(self.instance_root, text_path)
        doc["status_ocr"] = "TEXT_EXTRACTED"
        doc["text_char_count"] = str(len(text))
        self._write_documents(fields, rows)

        response = self._client().get(f"/documents/{doc['doc_id']}")
        body = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Fiche document - atelier de piece", body)
        self.assertIn(doc["file_name"], body)
        self.assertIn("Parcours novice: piece -> point -> action -> preuve", body)
        self.assertIn("Point, action, preuve", body)
        self.assertIn("Apercu autorise", body)
        self.assertIn("Texte local extrait pour la fiche securisee.", body)
        self.assertIn("Diffusion et signature", body)
        self.assertIn("Signature a venir", body)
        self.assertIn("Annotations futures", body)
        self.assertIn("Annotation signee", body)
        self.assertIn("evenements futurs separes", body)
        self.assertIn("aucune annotation n'est injectee dans le PDF", body)
        self.assertIn("Ancres sans PDF modifie", body)
        self.assertIn("Historique visible", body)
        self.assertNotIn(str(self.instance_root), body)
        self.assertNotIn("raw/", body.lower())
        self.assertNotIn("raw\\", body.lower())

    def test_document_detail_view_model_tracks_evidence_annotations_anchors_and_history(self) -> None:
        fields, rows = self._documents()
        doc = rows[0]
        doc["page_count"] = "2"
        doc["text_char_count"] = "42"
        doc["privacy_review_status"] = "REVIEW_PENDING"
        doc["redaction_status"] = "REDACTION_TODO"
        self._write_documents(fields, rows)

        detail = build_document_detail(self.instance, doc["doc_id"])

        self.assertEqual(detail["workbench"]["steps"][0]["label"], "1. Piece")
        self.assertEqual(detail["workbench"]["steps"][2]["label"], "3. Action")
        self.assertEqual(detail["diffusion"]["label"], "Diffusion a arbitrer")
        self.assertEqual(detail["signature"]["label"], "Signature a venir")
        self.assertEqual(detail["evidence"]["status"], "piece probatoire")
        self.assertEqual(detail["annotations"]["mode"], "evenements futurs separes")
        annotation_events = detail["annotations"]["events"]
        self.assertEqual(annotation_events[0]["label"], "Annotation signee")
        self.assertEqual(annotation_events[0]["status"], "a venir")
        self.assertIn("separe", annotation_events[0]["note"])
        self.assertEqual(annotation_events[1]["label"], "Point rattache")
        self.assertEqual(detail["anchors"]["status"], "ancres sans ecriture PDF")
        self.assertEqual(detail["anchors"]["entries"][0]["label"], "Ancre P1")
        self.assertIn("historique", detail["history"]["status"])

    def test_document_detail_unknown_and_traversal_doc_ids_return_404(self) -> None:
        client = self._client()

        self.assertEqual(client.get("/documents/DOC-INCONNU").status_code, 404)
        self.assertEqual(client.get("/documents/%2e%2e").status_code, 404)

    def test_document_detail_does_not_read_paths_outside_instance(self) -> None:
        fields, rows = self._documents()
        outside = Path(self.tempdir.name) / "outside_secret.txt"
        outside.write_text("SECRET_OUTSIDE_INSTANCE", encoding="utf-8")
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": "DOC-TRAVERSAL",
                "file_name": "traversal.pdf",
                "extension": "pdf",
                "original_path": "raw/traversal.pdf",
                "text_path": "../outside_secret.txt",
                "source_zone": "RAW",
                "document_type": "PDF",
                "status_ocr": "OCR_DONE",
            }
        )
        self._write_documents(fields, rows)

        response = self._client().get("/documents/DOC-TRAVERSAL")
        body = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Aucun apercu exploitable", body)
        self.assertNotIn("SECRET_OUTSIDE_INSTANCE", body)
        self.assertNotIn(str(outside), body)

    def test_raw_and_restricted_files_are_not_served_directly(self) -> None:
        restricted = self.instance_root / "restricted" / "secret.txt"
        restricted.parent.mkdir(parents=True, exist_ok=True)
        restricted.write_text("secret", encoding="utf-8")
        client = self._client()

        self.assertEqual(client.get("/raw/2026-05-12_demande_pieces_syndic.txt").status_code, 404)
        self.assertEqual(client.get("/restricted/secret.txt").status_code, 404)

        doc_id = self._documents()[1][0]["doc_id"]
        detail = client.get(f"/documents/{doc_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertTrue(detail.headers["content-type"].startswith("text/html"))
        self.assertNotIn("content-disposition", {key.lower() for key in detail.headers})

    def test_pdf_without_safe_media_preview_falls_back_to_extracted_text(self) -> None:
        fields, rows = self._documents()
        doc_id = "DOC-PDF-FALLBACK"
        raw_pdf = self.instance_root / "raw" / "scan_preview.pdf"
        raw_pdf.write_bytes(b"%PDF-1.4\n% synthetic test pdf\n")
        text = "Texte OCR de secours pour PDF indisponible.\n"
        text_path = self.instance_root / "staging" / "text" / f"{doc_id}.ocr.txt"
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(text, encoding="utf-8")
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": "scan_preview.pdf",
                "extension": "pdf",
                "size_bytes": str(raw_pdf.stat().st_size),
                "original_path": relative_to(self.instance_root, raw_pdf),
                "text_path": relative_to(self.instance_root, text_path),
                "source_zone": "RAW",
                "document_type": "Scan_PDF",
                "status_ocr": "OCR_DONE",
                "text_char_count": str(len(text)),
            }
        )
        self._write_documents(fields, rows)

        response = self._client().get(f"/documents/{doc_id}")
        body = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Apercu media indisponible; affichage du texte extrait.", body)
        self.assertIn("Texte OCR de secours pour PDF indisponible.", body)
        self.assertNotIn("data:application/pdf", response.text)
        self.assertNotIn("raw/scan_preview.pdf", body)
        self.assertNotIn("raw\\scan_preview.pdf", body)


if __name__ == "__main__":
    unittest.main()
