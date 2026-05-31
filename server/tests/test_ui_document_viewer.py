from __future__ import annotations

import shutil
import tempfile
import unittest
import hashlib
from html import unescape
from pathlib import Path

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, load_instance, read_csv, relative_to, write_csv
from coproscope.modules import pdftrace_registry
from coproscope.web.app import create_app
from coproscope.web.document_viewer import build_document_detail


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


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
        self.assertIn("Atelier de preuve", body)
        self.assertIn("Selection PDF indisponible", body)
        self.assertIn("Parcours novice et point d'action", body)
        self.assertIn("Apercu autorise", body)
        self.assertIn("Texte local extrait pour la fiche securisee.", body)
        self.assertIn("Diffusion et signature", body)
        self.assertIn("Signature a venir", body)
        self.assertIn("Annotations", body)
        self.assertIn("Annotation signee", body)
        self.assertIn("evenements futurs separes", body)
        self.assertIn("aucune annotation n'est injectee dans le PDF", body)
        self.assertIn("Preuve candidate a verifier", body)
        self.assertIn("La source originale n'est pas modifiee", body)
        self.assertIn("Non diffusable par defaut", body)
        self.assertIn("Ancres sans PDF modifie", body)
        self.assertIn("Historique", body)
        self.assertLess(body.index("Atelier de preuve"), body.index("Parcours novice et point d'action"))
        self.assertNotIn("Tracer une preuve dans ce PDF", body)
        self.assertNotIn("Le PDF original n'est pas modifie", body)
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
        self.assertFalse(detail["pdf_trace"]["available"])
        self.assertFalse(detail["pdf_trace"]["has_pdf_viewer"])
        self.assertEqual(detail["pdf_trace"]["primary_action"], "Selection PDF indisponible")
        self.assertEqual(detail["pdf_trace"]["status"], "Preuve candidate a verifier")
        self.assertIn("reservee aux PDF", detail["pdf_trace"]["limitation_notice"])
        self.assertIn("ne valide pas la preuve", detail["pdf_trace"]["validation_notice"])
        self.assertIn("source originale", detail["pdf_trace"]["source_notice"])
        self.assertEqual(detail["pdf_trace"]["diffusion_status"], "Non diffusable par defaut")
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

    def test_document_detail_never_displays_file_name_as_local_path(self) -> None:
        fields, rows = self._documents()
        doc_id = "DOC-PATH-NAME"
        pdf_path = self.instance_root / "staging" / "pdf" / "contrat_affichage.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n% display name test\n")
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": r"C:\Users\demo\raw\contrat_affichage.pdf",
                "extension": "pdf",
                "original_path": relative_to(self.instance_root, pdf_path),
                "source_zone": "STAGING",
                "document_type": "PDF",
                "status_ocr": "TEXT_EXTRACTED",
            }
        )
        self._write_documents(fields, rows)

        response = self._client().get(f"/documents/{doc_id}")
        body = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("contrat_affichage.pdf", body)
        self.assertNotIn("C:", body)
        self.assertNotIn("Users", body)
        self.assertNotIn("demo", body)
        self.assertNotIn("raw\\", body.lower())
        self.assertNotIn("raw/", body.lower())

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
        self.assertIn("Apercu PDF textuel", body)
        self.assertIn("Texte extrait", body)
        self.assertIn("Enregistrer comme trace a verifier", body)
        self.assertIn("Dessinez une zone sur la page avant d'enregistrer comme trace candidate.", body)
        self.assertIn("Zone a selectionner", body)
        self.assertNotIn("Lecteur PDF", body)
        self.assertNotIn("Miniature page 1", body)
        self.assertNotIn("100 %", body)
        self.assertIn("Texte OCR de secours pour PDF indisponible.", body)
        self.assertNotIn("data:application/pdf", response.text)
        self.assertNotIn("raw/scan_preview.pdf", body)
        self.assertNotIn("raw\\scan_preview.pdf", body)

    def test_pdf_trace_workshop_keeps_novice_wording_and_hides_technical_fields(self) -> None:
        fields, rows = self._documents()
        doc_id = "DOC-PDF-TRACE-UI"
        pdf_path = self.instance_root / "staging" / "pdf" / "trace_demo.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n% fictive PDF for UI test\n")
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": "trace_demo.pdf",
                "extension": "pdf",
                "sha256": "d" * 64,
                "size_bytes": str(pdf_path.stat().st_size),
                "original_path": relative_to(self.instance_root, pdf_path),
                "source_zone": "STAGING",
                "document_type": "PDF",
                "status_ocr": "TEXT_EXTRACTED",
                "classification_status": "A_RELIRE",
                "page_count": "3",
                "text_char_count": "120",
            }
        )
        self._write_documents(fields, rows)

        response = self._client().get(f"/documents/{doc_id}")
        body = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Atelier de trace PDF", body)
        self.assertIn("Lecteur PDF", body)
        self.assertIn("Miniatures des pages", body)
        self.assertIn("Page precedente", body)
        self.assertIn("Page suivante", body)
        self.assertIn("Page 1 sur 3", body)
        self.assertIn("Choisissez la page, puis encadrez la zone", body)
        self.assertIn("100 %", body)
        self.assertIn("Zone a selectionner sur la page 1", body)
        self.assertIn("Annotations", body)
        self.assertIn("Historique", body)
        self.assertIn("Informations techniques et traitement local", body)
        self.assertIn("Tracer une preuve candidate", body)
        self.assertIn("Enregistrer comme trace a verifier", body)
        self.assertIn("Tirer les poignees pour ajuster.", body)
        self.assertIn("Dessinez une zone sur la page", body)
        self.assertIn("Zone a selectionner", body)
        self.assertIn("data-pdf-trace-workbench", response.text)
        self.assertIn('data-pdf-trace-page-count="3"', response.text)
        self.assertIn("data-pdf-trace-selection", response.text)
        self.assertIn("data-pdf-trace-form", response.text)
        self.assertIn("data-pdf-trace-submit disabled", response.text)
        self.assertIn('data-pdf-trace-field="x"', response.text)
        self.assertIn('name="zone_x" value=""', response.text)
        self.assertIn('name="zone_y" value=""', response.text)
        self.assertIn('name="zone_width" value=""', response.text)
        self.assertIn('name="zone_height" value=""', response.text)
        self.assertIn("/static/pdf_trace_selection.js", response.text)
        self.assertIn("Preuve candidate a verifier", body)
        self.assertIn("Texte reconnu automatiquement : relisez avant de vous en servir.", body)
        self.assertIn("Texte non confirme : seule la zone encadree est gardee.", body)
        self.assertIn("Le fichier a change depuis la trace. Verifiez avant usage.", body)
        self.assertIn("Le PDF original n'est pas modifie.", body)
        self.assertIn("CoproScope garde un repere dans le PDF, mais ne valide pas la preuve.", body)
        self.assertIn("Non diffusable par defaut", body)
        self.assertIn("Les evenements restent separes du fichier source.", body)
        self.assertLess(body.index("Lecteur PDF"), body.index("Parcours novice et point d'action"))
        self.assertLess(body.index("Le PDF original n'est pas modifie."), body.index("Annotations"))
        self.assertLess(body.index("Texte non confirme : seule la zone encadree est gardee."), body.index("Annotations"))
        self.assertLess(body.index("Enregistrer comme trace a verifier"), body.index("Informations techniques et traitement local"))
        self.assertLess(body.index("Annotations"), body.index("Metadonnees"))
        self.assertLess(body.index("Historique"), body.index("Traitement local"))
        self.assertLess(body.index("Informations techniques et traitement local"), body.index("Moteur OCR"))
        self.assertNotIn("Tracer une preuve dans ce PDF", body)
        self.assertNotIn("zotero_position", body)
        self.assertNotIn("source_engine", body)
        self.assertNotIn("rects", body)
        self.assertNotIn(str(self.instance_root), body)
        self.assertNotIn("raw/", body.lower())
        script = (Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "pdf_trace_selection.js").read_text(encoding="utf-8")
        self.assertIn("data-pdf-trace-workbench", script)
        self.assertIn("data-pdf-trace-selection", script)
        self.assertIn("data-pdf-trace-field=", script)
        self.assertIn("data-pdf-trace-submit", script)
        self.assertIn("data-pdf-trace-page-next", script)
        self.assertIn("setCurrentPage", script)
        self.assertIn("pointerdown", script)
        self.assertIn("pointerup", script)
        self.assertNotIn('field(form, "page").value = "1"', script)
        self.assertNotIn("zotero_position", script)
        self.assertNotIn("source_engine", script)
        self.assertNotIn("rects", script)

    def test_pdf_trace_save_creates_sidecar_without_mutating_pdf(self) -> None:
        fields, rows = self._documents()
        doc_id = "DOC-PDF-TRACE-SAVE"
        pdf_path = self.instance_root / "staging" / "pdf" / "trace_save.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_bytes = b"%PDF-1.4\n% sidecar save test\n"
        pdf_path.write_bytes(pdf_bytes)
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": "trace_save.pdf",
                "extension": "pdf",
                "sha256": _sha256(pdf_bytes),
                "size_bytes": str(pdf_path.stat().st_size),
                "original_path": relative_to(self.instance_root, pdf_path),
                "source_zone": "STAGING",
                "document_type": "PDF",
                "status_ocr": "TEXT_EXTRACTED",
                "classification_status": "A_RELIRE",
                "page_count": "3",
                "text_char_count": "120",
            }
        )
        self._write_documents(fields, rows)

        client = self._client()
        response = client.post(
            f"/documents/{doc_id}/traces",
            data={
                "page": "2",
                "zone_x": "0.20",
                "zone_y": "0.25",
                "zone_width": "0.40",
                "zone_height": "0.10",
                "comment": "Budget previsionnel a relire",
            },
            follow_redirects=False,
        )
        trace_fields, trace_rows = read_csv(pdftrace_registry.trace_register_path(self.instance))
        detail = client.get(f"/documents/{doc_id}")
        body = unescape(detail.text)

        self.assertEqual(response.status_code, 303)
        self.assertIn(f"/documents/{doc_id}?", response.headers["location"])
        self.assertEqual(pdf_path.read_bytes(), pdf_bytes)
        self.assertEqual(trace_fields, pdftrace_registry.PDF_TRACE_FIELDS)
        self.assertEqual(len(trace_rows), 1)
        self.assertEqual(trace_rows[0]["document_ref"], doc_id)
        self.assertEqual(trace_rows[0]["page"], "2")
        self.assertEqual(trace_rows[0]["proof_status"], "preuve_candidate")
        self.assertEqual(trace_rows[0]["text_status"], "non_confirme")
        self.assertEqual(trace_rows[0]["document_hash_status"], "hash_conforme")
        self.assertEqual(trace_rows[0]["diffusion"], "non_diffusable")
        self.assertEqual(trace_rows[0]["write_policy"], "source_pdf_is_never_modified")
        self.assertEqual(detail.status_code, 200)
        self.assertIn("Trace candidate enregistree", body)
        self.assertIn("Non diffusable par defaut", body)
        self.assertIn("Zone encadree page 2", body)
        self.assertIn("Le PDF original n'est pas modifie.", body)
        self.assertIn("Budget previsionnel a relire", body)
        self.assertNotIn("zotero_position", body)
        self.assertNotIn("source_engine", body)
        self.assertNotIn("rects", body)
        self.assertNotIn(str(self.instance_root), body)
        self.assertNotIn("raw/", body.lower())

    def test_pdf_trace_save_marks_changed_source_hash_to_verify_without_mutating_pdf(self) -> None:
        fields, rows = self._documents()
        doc_id = "DOC-PDF-TRACE-HASH-CHANGED"
        pdf_path = self.instance_root / "staging" / "pdf" / "trace_hash_changed.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        registered_bytes = b"%PDF-1.4\n% registered version\n"
        changed_bytes = b"%PDF-1.4\n% changed version\n"
        pdf_path.write_bytes(registered_bytes)
        registered_hash = _sha256(registered_bytes)
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": "trace_hash_changed.pdf",
                "extension": "pdf",
                "sha256": registered_hash,
                "size_bytes": str(pdf_path.stat().st_size),
                "original_path": relative_to(self.instance_root, pdf_path),
                "source_zone": "STAGING",
                "document_type": "PDF",
            }
        )
        self._write_documents(fields, rows)
        pdf_path.write_bytes(changed_bytes)

        client = self._client()
        response = client.post(
            f"/documents/{doc_id}/traces",
            data={
                "page": "1",
                "zone_x": "0.20",
                "zone_y": "0.25",
                "zone_width": "0.40",
                "zone_height": "0.10",
                "comment": "Zone a verifier apres changement",
            },
            follow_redirects=False,
        )
        trace_rows = read_csv(pdftrace_registry.trace_register_path(self.instance))[1]
        detail = client.get(f"/documents/{doc_id}")
        body = unescape(detail.text)

        self.assertEqual(response.status_code, 303)
        self.assertEqual(pdf_path.read_bytes(), changed_bytes)
        self.assertEqual(len(trace_rows), 1)
        self.assertEqual(trace_rows[0]["document_hash"], f"sha256:{registered_hash}")
        self.assertEqual(trace_rows[0]["document_hash_status"], "hash_a_verifier")
        self.assertIn("Trace candidate enregistree - a verifier", body)
        self.assertIn("Le document a change depuis son ajout dans CoproScope", body)
        self.assertIn("Verifiez que la zone encadree montre toujours le bon passage", body)
        self.assertNotIn(str(self.instance_root), body)
        self.assertNotIn("original_path", body)
        self.assertNotIn("source_engine", body)
        self.assertNotIn("zotero_position", body)
        self.assertNotIn("rects", body)
        self.assertNotIn("raw/", body.lower())
        self.assertNotIn("raw\\", body.lower())

    def test_pdf_trace_save_marks_hash_not_verified_when_source_is_unavailable(self) -> None:
        fields, rows = self._documents()
        outside_pdf = Path(self.tempdir.name) / "outside_trace.pdf"
        outside_pdf.write_bytes(b"%PDF-1.4\n% outside instance\n")
        raw_pdf = self.instance_root / "raw" / "source_trace.pdf"
        raw_pdf.parent.mkdir(parents=True, exist_ok=True)
        raw_pdf.write_bytes(b"%PDF-1.4\n% raw source\n")
        cases = (
            ("DOC-PDF-TRACE-NO-SOURCE", ""),
            ("DOC-PDF-TRACE-OUTSIDE-SOURCE", str(outside_pdf)),
            ("DOC-PDF-TRACE-BLOCKED-SOURCE", relative_to(self.instance_root, raw_pdf)),
        )
        for doc_id, original_path in cases:
            rows.append(
                {
                    **{field: "" for field in fields},
                    "doc_id": doc_id,
                    "file_name": f"{doc_id}.pdf",
                    "extension": "pdf",
                    "sha256": "b" * 64,
                    "original_path": original_path,
                    "source_zone": "STAGING",
                    "document_type": "PDF",
                }
            )
        self._write_documents(fields, rows)

        client = self._client()
        for index, (doc_id, _original_path) in enumerate(cases, start=1):
            with self.subTest(doc_id=doc_id):
                response = client.post(
                    f"/documents/{doc_id}/traces",
                    data={
                        "page": "1",
                        "zone_x": "0.20",
                        "zone_y": "0.25",
                        "zone_width": "0.40",
                        "zone_height": "0.10",
                        "comment": "Zone a relire",
                    },
                    follow_redirects=False,
                )
                trace_rows = read_csv(pdftrace_registry.trace_register_path(self.instance))[1]
                detail = client.get(f"/documents/{doc_id}")
                body = unescape(detail.text)

                self.assertEqual(response.status_code, 303)
                self.assertEqual(len(trace_rows), index)
                self.assertEqual(trace_rows[-1]["document_ref"], doc_id)
                self.assertEqual(trace_rows[-1]["document_hash_status"], "hash_non_verifie")
                self.assertIn("Version du document non verifiee", body)
                self.assertNotIn(str(self.instance_root), body)
                self.assertNotIn(str(outside_pdf), body)
                self.assertNotIn("original_path", body)
                self.assertNotIn("source_engine", body)
                self.assertNotIn("zotero_position", body)
                self.assertNotIn("rects", body)
                self.assertNotIn("raw/", body.lower())
                self.assertNotIn("raw\\", body.lower())

    def test_pdf_trace_save_rejects_private_comment_without_writing_sidecar(self) -> None:
        fields, rows = self._documents()
        doc_id = "DOC-PDF-TRACE-PRIVATE"
        pdf_path = self.instance_root / "staging" / "pdf" / "trace_private.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n% private comment test\n")
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": "trace_private.pdf",
                "extension": "pdf",
                "sha256": "f" * 64,
                "size_bytes": str(pdf_path.stat().st_size),
                "original_path": relative_to(self.instance_root, pdf_path),
                "source_zone": "STAGING",
                "document_type": "PDF",
            }
        )
        self._write_documents(fields, rows)

        response = self._client().post(
            f"/documents/{doc_id}/traces",
            data={
                "page": "1",
                "zone_x": "0.20",
                "zone_y": "0.25",
                "zone_width": "0.40",
                "zone_height": "0.10",
                "comment": r"C:\Users\demo\raw\piece.pdf",
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(read_csv(pdftrace_registry.trace_register_path(self.instance))[1], [])

    def test_pdf_trace_save_rejects_missing_or_invalid_zone_without_sidecar(self) -> None:
        fields, rows = self._documents()
        doc_id = "DOC-PDF-TRACE-ZONE-INVALID"
        pdf_path = self.instance_root / "staging" / "pdf" / "trace_invalid_zone.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n% invalid zone test\n")
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": "trace_invalid_zone.pdf",
                "extension": "pdf",
                "sha256": "a" * 64,
                "size_bytes": str(pdf_path.stat().st_size),
                "original_path": relative_to(self.instance_root, pdf_path),
                "source_zone": "STAGING",
                "document_type": "PDF",
                "page_count": "3",
            }
        )
        self._write_documents(fields, rows)

        invalid_forms = (
            {"page": "1", "comment": "Zone absente"},
            {"page": "1", "zone_x": "0.1", "zone_y": "0.1", "zone_width": "0", "zone_height": "0.2"},
            {"page": "1", "zone_x": "-0.1", "zone_y": "0.1", "zone_width": "0.2", "zone_height": "0.2"},
            {"page": "1", "zone_x": "0.9", "zone_y": "0.1", "zone_width": "0.2", "zone_height": "0.2"},
            {"page": "1", "zone_x": "x", "zone_y": "0.1", "zone_width": "0.2", "zone_height": "0.2"},
            {"page": "4", "zone_x": "0.1", "zone_y": "0.1", "zone_width": "0.2", "zone_height": "0.2"},
        )
        client = self._client()
        for form in invalid_forms:
            with self.subTest(form=form):
                response = client.post(f"/documents/{doc_id}/traces", data=form)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(read_csv(pdftrace_registry.trace_register_path(self.instance))[1], [])


if __name__ == "__main__":
    unittest.main()
