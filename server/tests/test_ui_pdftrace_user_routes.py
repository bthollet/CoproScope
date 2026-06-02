from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, load_instance, read_csv, relative_to, write_csv
from coproscope.modules import pdftrace_registry
from coproscope.web.app import create_app


FORBIDDEN_PUBLIC_MARKERS = (
    "zotero_position",
    "rects",
    "source_engine",
    "selected_text_hash",
    "original_path",
    "raw/",
    "raw\\",
    "restricted",
)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class PdfTraceUserRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(self.repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except Exception as exc:  # pragma: no cover
            self.skipTest(f"fastapi test client unavailable: {exc}")
        return TestClient(create_app(self.instance, 2025, access_token="local-secret"))

    def _add_pdf_document(self, doc_id: str, *, page_count: str = "3") -> tuple[Path, bytes]:
        return self._add_document(doc_id, extension="pdf", page_count=page_count)

    def _add_document(self, doc_id: str, *, extension: str, page_count: str = "") -> tuple[Path, bytes]:
        fields, rows = read_csv(self.instance.register("documents"))
        fields = fields or list(DEFAULT_DOCUMENT_FIELDS)
        content = f"FICTIF {extension} trace user route test\n".encode("utf-8")
        if extension == "pdf":
            content = b"%PDF-1.4\n% FICTIF pdf trace user route test\n"
        doc_path = self.instance_root / "staging" / extension / f"{doc_id}.{extension}"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_bytes(content)
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": f"{doc_id}.{extension}",
                "extension": extension,
                "sha256": _sha256(content),
                "size_bytes": str(doc_path.stat().st_size),
                "original_path": relative_to(self.instance_root, doc_path),
                "source_zone": "STAGING",
                "document_type": f"{extension.upper()} FICTIF",
                "page_count": page_count,
                "text_char_count": "120",
            }
        )
        write_csv(self.instance.register("documents"), fields, rows)
        return doc_path, content

    def test_pdf_trace_queue_empty_state_explains_local_guardrails(self) -> None:
        client = self._client()

        queue = client.get("/pdf-traces?token=local-secret")
        documents = client.get("/documents?token=local-secret")
        body = unescape(queue.text)

        self.assertEqual(queue.status_code, 200)
        self.assertEqual(documents.status_code, 200)
        self.assertIn("File locale de reprise PDF", body)
        self.assertIn("0", body)
        self.assertIn("Aucune trace PDF candidate a relire.", body)
        self.assertIn("Aucun export global PDF/Zotero n'est active.", body)
        self.assertIn("Le PDF original n'est pas modifie.", body)
        self.assertIn("File reprises PDF", unescape(documents.text))
        self._assert_public_pages_are_clean(body)

    def test_user_can_save_and_resume_pdf_trace_without_public_leaks(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE"
        pdf_path, pdf_bytes = self._add_pdf_document(doc_id)
        client = self._client()

        detail_before = client.get(f"/documents/{doc_id}?token=local-secret")
        save_response = client.post(
            f"/documents/{doc_id}/traces?token=local-secret",
            data={
                "page": "2",
                "zone_x": "0.20",
                "zone_y": "0.25",
                "zone_width": "0.40",
                "zone_height": "0.10",
                "comment": "Point budget fictif a relire",
            },
            follow_redirects=False,
        )
        trace_rows = read_csv(pdftrace_registry.trace_register_path(self.instance))[1]
        trace_id = trace_rows[0]["trace_id"]
        detail_after = client.get(f"/documents/{doc_id}?trace_id={trace_id}&token=local-secret")
        queue = client.get("/pdf-traces?token=local-secret")

        self.assertEqual(detail_before.status_code, 200)
        self.assertEqual(save_response.status_code, 303)
        self.assertIn(f"/documents/{doc_id}?trace=saved&trace_id={trace_id}", save_response.headers["location"])
        self.assertIn("token=local-secret", save_response.headers["location"])
        self.assertEqual(detail_after.status_code, 200)
        self.assertEqual(queue.status_code, 200)
        self.assertEqual(pdf_path.read_bytes(), pdf_bytes)
        self.assertEqual(trace_rows[0]["page"], "2")
        self.assertEqual(trace_rows[0]["write_policy"], "source_pdf_is_never_modified")

        detail_body = unescape(detail_after.text)
        queue_body = unescape(queue.text)
        self.assertIn("Tracer une preuve candidate", detail_body)
        self.assertIn("Page 2 sur 3", detail_body)
        self.assertIn("Point de reprise ouvert", detail_body)
        self.assertIn("Vous reprenez ici: Zone encadree page 2.", detail_body)
        self.assertIn("File locale de reprise PDF", queue_body)
        self.assertIn(f"/documents/{doc_id}?trace_id={trace_id}", queue.text)
        self.assertIn(f"/documents/{doc_id}?trace_id={trace_id}&amp;token=local-secret#pdf-reader", queue.text)
        self.assertIn("#pdf-reader", queue.text)
        self.assertNotIn("Point budget fictif a relire", queue_body)
        self._assert_public_pages_are_clean(detail_body, queue_body)

    def test_pdf_trace_routes_keep_token_and_reject_invalid_public_actions(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-INVALID"
        self._add_pdf_document(doc_id, page_count="1")
        client = self._client()

        blocked_queue = client.get("/pdf-traces")
        invalid_page = client.post(
            f"/documents/{doc_id}/traces?token=local-secret",
            data={
                "page": "2",
                "zone_x": "0.20",
                "zone_y": "0.25",
                "zone_width": "0.40",
                "zone_height": "0.10",
            },
            follow_redirects=False,
        )
        trace_path = pdftrace_registry.trace_register_path(self.instance)
        rows = read_csv(trace_path)[1] if trace_path.exists() else []

        self.assertEqual(blocked_queue.status_code, 403)
        self.assertEqual(invalid_page.status_code, 422)
        self.assertIn("page de trace hors document", invalid_page.text)
        self.assertEqual(rows, [])

    def test_pdf_trace_save_rejects_non_pdf_and_missing_document_without_side_effect(self) -> None:
        doc_id = "DOC-NON-PDF-USER-TRACE"
        self._add_document(doc_id, extension="txt")
        client = self._client()

        non_pdf = client.post(
            f"/documents/{doc_id}/traces?token=local-secret",
            data={
                "page": "1",
                "zone_x": "0.20",
                "zone_y": "0.25",
                "zone_width": "0.40",
                "zone_height": "0.10",
            },
            follow_redirects=False,
        )
        missing = client.post(
            "/documents/DOC-MISSING-TRACE/traces?token=local-secret",
            data={
                "page": "1",
                "zone_x": "0.20",
                "zone_y": "0.25",
                "zone_width": "0.40",
                "zone_height": "0.10",
            },
            follow_redirects=False,
        )
        trace_path = pdftrace_registry.trace_register_path(self.instance)
        rows = read_csv(trace_path)[1] if trace_path.exists() else []

        self.assertEqual(non_pdf.status_code, 422)
        self.assertIn("trace reservee aux PDF", non_pdf.text)
        self.assertEqual(missing.status_code, 404)
        self.assertIn("Document introuvable.", missing.text)
        self.assertEqual(rows, [])

    def test_pdf_trace_save_rejects_incomplete_zone_without_sidecar(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-INCOMPLETE-ZONE"
        self._add_pdf_document(doc_id)
        client = self._client()

        response = client.post(
            f"/documents/{doc_id}/traces?token=local-secret",
            data={
                "page": "1",
                "zone_x": "0.20",
                "zone_y": "0.25",
                "zone_height": "0.10",
                "comment": "Zone oubliee par l'utilisateur",
            },
            follow_redirects=False,
        )
        trace_path = pdftrace_registry.trace_register_path(self.instance)
        rows = read_csv(trace_path)[1] if trace_path.exists() else []

        self.assertEqual(response.status_code, 422)
        self.assertIn("zone de trace a selectionner", response.text)
        self.assertEqual(rows, [])

    def test_pdf_trace_save_rejects_non_numeric_page_without_sidecar(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-BAD-PAGE"
        self._add_pdf_document(doc_id)
        client = self._client()

        response = self._save_trace(client, doc_id, "deux", "Page saisie en toutes lettres", follow_redirects=False)
        trace_path = pdftrace_registry.trace_register_path(self.instance)
        rows = read_csv(trace_path)[1] if trace_path.exists() else []

        self.assertEqual(response.status_code, 422)
        self.assertIn("page de trace invalide", response.text)
        self.assertEqual(rows, [])

    def test_pdf_trace_save_rejects_local_path_note_without_sidecar(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-PATH-NOTE"
        self._add_pdf_document(doc_id)
        client = self._client()

        response = self._save_trace(
            client,
            doc_id,
            "1",
            r"Relire C:\Users\Example\raw\piece.pdf avant partage",
            follow_redirects=False,
        )
        trace_path = pdftrace_registry.trace_register_path(self.instance)
        rows = read_csv(trace_path)[1] if trace_path.exists() else []

        self.assertEqual(response.status_code, 422)
        self.assertIn("note trop sensible", response.text)
        self.assertEqual(rows, [])

    def test_pdf_trace_queue_counts_multiple_traces_and_blocks_sensitive_notes(self) -> None:
        first_doc_id = "DOC-PDF-USER-TRACE-FIRST"
        second_doc_id = "DOC-PDF-USER-TRACE-SECOND"
        self._add_pdf_document(first_doc_id)
        self._add_pdf_document(second_doc_id)
        client = self._client()

        first_save = self._save_trace(client, first_doc_id, "1", "Note fictive non sensible")
        second_save = self._save_trace(client, second_doc_id, "3", "Autre note fictive")
        sensitive_save = self._save_trace(client, first_doc_id, "2", "Contact test@example.com", follow_redirects=False)
        queue = client.get("/pdf-traces?token=local-secret")

        self.assertEqual(first_save.status_code, 303)
        self.assertEqual(second_save.status_code, 303)
        self.assertEqual(sensitive_save.status_code, 422)
        self.assertIn("note trop sensible", sensitive_save.text)
        self.assertEqual(queue.status_code, 200)
        body = unescape(queue.text)
        self.assertIn("<strong>2</strong><span>traces a relire</span>", queue.text)
        self.assertIn(f"Document {first_doc_id}", body)
        self.assertIn(f"Document {second_doc_id}", body)
        self.assertIn("Zone encadree page 1", body)
        self.assertIn("Zone encadree page 3", body)
        self.assertIn("Ouvrir la trace", body)
        self.assertNotIn("Note fictive non sensible", body)
        self.assertNotIn("Autre note fictive", body)
        self.assertNotIn("test@example.com", body)
        self._assert_public_pages_are_clean(body)

    def test_pdf_trace_queue_keeps_distinct_resume_links_for_same_document(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-SAME-DOC"
        self._add_pdf_document(doc_id)
        client = self._client()

        first_save = self._save_trace(client, doc_id, "1", "Premier point fictif")
        second_save = self._save_trace(client, doc_id, "3", "Second point fictif")
        trace_rows = read_csv(pdftrace_registry.trace_register_path(self.instance))[1]
        queue = client.get("/pdf-traces?token=local-secret")

        self.assertEqual(first_save.status_code, 303)
        self.assertEqual(second_save.status_code, 303)
        self.assertEqual(queue.status_code, 200)
        self.assertEqual(len(trace_rows), 2)
        first_trace_id = trace_rows[0]["trace_id"]
        second_trace_id = trace_rows[1]["trace_id"]
        self.assertNotEqual(first_trace_id, second_trace_id)
        body = unescape(queue.text)
        self.assertIn("<strong>2</strong><span>traces a relire</span>", queue.text)
        self.assertIn("Zone encadree page 1", body)
        self.assertIn("Zone encadree page 3", body)
        self.assertIn(f"/documents/{doc_id}?trace_id={first_trace_id}&amp;token=local-secret#pdf-reader", queue.text)
        self.assertIn(f"/documents/{doc_id}?trace_id={second_trace_id}&amp;token=local-secret#pdf-reader", queue.text)
        self.assertNotIn("Premier point fictif", body)
        self.assertNotIn("Second point fictif", body)
        self._assert_public_pages_are_clean(body)

    def test_pdf_trace_queue_ignores_legacy_raw_document_ref_without_leak(self) -> None:
        trace_path = pdftrace_registry.trace_register_path(self.instance)
        write_csv(
            trace_path,
            pdftrace_registry.PDF_TRACE_FIELDS,
            [
                {
                    **{field: "" for field in pdftrace_registry.PDF_TRACE_FIELDS},
                    "trace_id": "TRACE-LEGACY-RAW",
                    "document_ref": "raw/DOC-LEGACY",
                    "page": "1",
                    "zone_x": "0.10",
                    "zone_y": "0.10",
                    "zone_width": "0.20",
                    "zone_height": "0.20",
                    "document_hash_status": "document_hash_not_checked",
                    "diffusion": "non_diffusable",
                    "text_status": "non_confirme",
                    "comment": r"C:\Users\Example\raw\piece.pdf",
                }
            ],
        )
        client = self._client()

        response = client.get("/pdf-traces?token=local-secret")

        self.assertEqual(response.status_code, 200)
        body = unescape(response.text)
        self.assertIn("<strong>0</strong><span>traces a relire</span>", response.text)
        self.assertIn("Aucune trace PDF candidate a relire.", body)
        self.assertNotIn("TRACE-LEGACY-RAW", body)
        self.assertNotIn("DOC-LEGACY", body)
        self.assertNotIn("piece.pdf", body)
        self._assert_public_pages_are_clean(body)

    def test_document_detail_ignores_unknown_trace_id_without_leak(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-UNKNOWN-TRACE"
        self._add_pdf_document(doc_id)
        client = self._client()

        response = client.get(f"/documents/{doc_id}?trace_id=raw/TRACE-SECRET&token=local-secret")

        self.assertEqual(response.status_code, 200)
        body = unescape(response.text)
        self.assertIn("Tracer une preuve candidate", body)
        self.assertNotIn("Point de reprise ouvert", body)
        self.assertNotIn("TRACE-SECRET", body)
        self._assert_public_pages_are_clean(body)

    def _save_trace(self, client, doc_id: str, page: str, comment: str, *, follow_redirects: bool = False):
        return client.post(
            f"/documents/{doc_id}/traces?token=local-secret",
            data={
                "page": page,
                "zone_x": "0.20",
                "zone_y": "0.25",
                "zone_width": "0.40",
                "zone_height": "0.10",
                "comment": comment,
            },
            follow_redirects=follow_redirects,
        )

    def _assert_public_pages_are_clean(self, *bodies: str) -> None:
        for body in bodies:
            lowered = body.lower()
            self.assertNotIn(str(self.instance_root).lower(), lowered)
            for marker in FORBIDDEN_PUBLIC_MARKERS:
                self.assertNotIn(marker, lowered)


if __name__ == "__main__":
    unittest.main()
