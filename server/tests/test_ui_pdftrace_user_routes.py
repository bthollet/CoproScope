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
        fields, rows = read_csv(self.instance.register("documents"))
        fields = fields or list(DEFAULT_DOCUMENT_FIELDS)
        pdf_bytes = b"%PDF-1.4\n% FICTIF pdf trace user route test\n"
        pdf_path = self.instance_root / "staging" / "pdf" / f"{doc_id}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(pdf_bytes)
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": f"{doc_id}.pdf",
                "extension": "pdf",
                "sha256": _sha256(pdf_bytes),
                "size_bytes": str(pdf_path.stat().st_size),
                "original_path": relative_to(self.instance_root, pdf_path),
                "source_zone": "STAGING",
                "document_type": "PDF FICTIF",
                "page_count": page_count,
                "text_char_count": "120",
            }
        )
        write_csv(self.instance.register("documents"), fields, rows)
        return pdf_path, pdf_bytes

    def _add_text_document(self, doc_id: str) -> None:
        fields, rows = read_csv(self.instance.register("documents"))
        fields = fields or list(DEFAULT_DOCUMENT_FIELDS)
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": f"{doc_id}.txt",
                "extension": "txt",
                "sha256": _sha256(b"document texte fictif"),
                "size_bytes": "23",
                "source_zone": "STAGING",
                "document_type": "NOTE FICTIVE",
                "text_char_count": "23",
            }
        )
        write_csv(self.instance.register("documents"), fields, rows)

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
        self.assertIn("Repere court", detail_body)
        self.assertNotIn("<small>Ancre", detail_body)
        self.assertIn("Note courte: Point budget fictif a relire", detail_body)
        self.assertNotIn("Commentaire: Point budget fictif a relire", detail_body)
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

    def test_pdf_trace_save_without_token_is_forbidden_without_sidecar(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-NO-TOKEN"
        self._add_pdf_document(doc_id)
        client = self._client()

        response = client.post(
            f"/documents/{doc_id}/traces",
            data={
                "page": "1",
                "zone_x": "0.20",
                "zone_y": "0.25",
                "zone_width": "0.40",
                "zone_height": "0.10",
                "comment": "Trace sans jeton",
            },
            follow_redirects=False,
        )
        trace_path = pdftrace_registry.trace_register_path(self.instance)
        rows = read_csv(trace_path)[1] if trace_path.exists() else []

        self.assertEqual(response.status_code, 403)
        self.assertEqual(rows, [])

    def test_pdf_trace_queue_empty_state_is_clear_and_private(self) -> None:
        client = self._client()

        response = client.get("/pdf-traces?token=local-secret")

        body = unescape(response.text)
        self.assertIn("File locale de reprise PDF", body)
        self.assertIn("<strong>0</strong><span>traces a relire</span>", response.text)
        self.assertIn("Aucune trace PDF candidate a relire.", body)
        self.assertIn("File locale uniquement: pas d'export, pas de PDF modifie", body)
        self.assertNotIn("Ouvrir la trace", body)
        self._assert_public_pages_are_clean(body)

    def test_pdf_trace_save_unknown_document_returns_404_without_sidecar(self) -> None:
        client = self._client()

        response = self._save_trace(client, "DOC-UNKNOWN-USER-TRACE", "1", "Trace document inconnu", follow_redirects=False)
        trace_path = pdftrace_registry.trace_register_path(self.instance)
        rows = read_csv(trace_path)[1] if trace_path.exists() else []

        self.assertEqual(response.status_code, 404)
        self.assertIn("Document introuvable", response.text)
        self.assertEqual(rows, [])

    def test_pdf_trace_save_rejects_non_pdf_document_without_sidecar(self) -> None:
        doc_id = "DOC-NON-PDF-USER-TRACE"
        self._add_text_document(doc_id)
        client = self._client()

        response = self._save_trace(client, doc_id, "1", "Tentative sur document texte", follow_redirects=False)
        trace_path = pdftrace_registry.trace_register_path(self.instance)
        rows = read_csv(trace_path)[1] if trace_path.exists() else []

        self.assertEqual(response.status_code, 422)
        self.assertIn("trace reservee aux PDF", response.text)
        self.assertEqual(rows, [])

    def test_pdf_trace_save_rejects_zone_outside_page_without_sidecar(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-ZONE-OUT"
        self._add_pdf_document(doc_id)
        client = self._client()

        response = client.post(
            f"/documents/{doc_id}/traces?token=local-secret",
            data={
                "page": "1",
                "zone_x": "0.80",
                "zone_y": "0.25",
                "zone_width": "0.40",
                "zone_height": "0.10",
                "comment": "Zone qui deborde de la page",
            },
            follow_redirects=False,
        )
        trace_path = pdftrace_registry.trace_register_path(self.instance)
        rows = read_csv(trace_path)[1] if trace_path.exists() else []

        self.assertEqual(response.status_code, 422)
        self.assertIn("zone de trace hors page", response.text)
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

    def test_pdf_trace_queue_ignores_legacy_raw_document_ref_without_leak(self) -> None:
        self._write_legacy_trace(
            trace_id="TRACE-LEGACY-RAW",
            document_ref="raw/DOC-LEGACY",
            comment=r"C:\Users\Example\raw\piece.pdf",
        )
        client = self._client()

        response = client.get("/pdf-traces?token=local-secret")

        body = unescape(response.text)
        self.assertIn("<strong>0</strong><span>traces a relire</span>", response.text)
        self.assertIn("Aucune trace PDF candidate a relire.", body)
        self.assertNotIn("TRACE-LEGACY-RAW", body)
        self.assertNotIn("DOC-LEGACY", body)
        self.assertNotIn("piece.pdf", body)
        self._assert_public_pages_are_clean(body)

    def test_pdf_trace_queue_ignores_orphan_trace_without_broken_link(self) -> None:
        self._write_legacy_trace(
            trace_id="TRACE-ORPHAN-LEGACY",
            document_ref="DOC-REMOVED-LEGACY",
            page="2",
            comment="Trace issue d'un document supprime",
        )
        client = self._client()

        response = client.get("/pdf-traces?token=local-secret")

        body = unescape(response.text)
        self.assertIn("<strong>0</strong><span>traces a relire</span>", response.text)
        self.assertIn("Aucune trace PDF candidate a relire.", body)
        self.assertNotIn("TRACE-ORPHAN-LEGACY", body)
        self.assertNotIn("DOC-REMOVED-LEGACY", body)
        self.assertNotIn("/documents/DOC-REMOVED-LEGACY", response.text)
        self._assert_public_pages_are_clean(body)

    def test_pdf_trace_queue_hides_technical_legacy_fields_for_valid_trace(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-LEGACY-TECH"
        self._add_pdf_document(doc_id)
        self._write_legacy_trace(
            trace_id="TRACE-LEGACY-TECH",
            document_ref=doc_id,
            page="2",
            selected_text_hash="sha256:secret-demo-hash",
            source_engine="zotero_position",
            comment="Commentaire interne legacy a masquer",
        )
        client = self._client()

        response = client.get("/pdf-traces?token=local-secret")

        body = unescape(response.text)
        self.assertIn("<strong>1</strong><span>traces a relire</span>", response.text)
        self.assertIn(f"Document {doc_id}", body)
        self.assertIn("Zone encadree page 2", body)
        self.assertIn("Version du document non verifiee", body)
        self.assertIn("Verifier la version du PDF", body)
        self.assertIn(f"/documents/{doc_id}?trace_id=TRACE-LEGACY-TECH&amp;token=local-secret#pdf-reader", response.text)
        self.assertNotIn("Commentaire interne legacy a masquer", body)
        self.assertNotIn("document_hash_not_checked", body)
        self.assertNotIn("non_confirme", body)
        self.assertNotIn("secret-demo-hash", body)
        self._assert_public_pages_are_clean(body)

    def test_pdf_trace_legacy_without_usable_zone_has_no_resume_link(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-NO-ZONE"
        self._add_pdf_document(doc_id)
        self._write_legacy_trace(
            trace_id="TRACE-LEGACY-NO-ZONE",
            document_ref=doc_id,
            page="2",
            zone_width="",
            comment="Zone legacy incomplete",
        )
        client = self._client()

        queue = client.get("/pdf-traces?token=local-secret")
        detail = client.get(f"/documents/{doc_id}?trace_id=TRACE-LEGACY-NO-ZONE&token=local-secret")

        queue_body, detail_body = self._assert_no_legacy_resume(queue, detail, doc_id, "TRACE-LEGACY-NO-ZONE")
        self.assertNotIn("Reprendre cette trace", detail_body)
        self.assertNotIn("Zone legacy incomplete", detail_body)

    def test_pdf_trace_legacy_page_outside_document_has_no_resume_link(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-PAGE-OUT"
        self._add_pdf_document(doc_id, page_count="3")
        self._write_legacy_trace(
            trace_id="TRACE-LEGACY-PAGE-99",
            document_ref=doc_id,
            page="99",
            comment="Page legacy hors PDF",
        )
        client = self._client()

        queue = client.get("/pdf-traces?token=local-secret")
        detail = client.get(f"/documents/{doc_id}?trace_id=TRACE-LEGACY-PAGE-99&token=local-secret")

        _, detail_body = self._assert_no_legacy_resume(queue, detail, doc_id, "TRACE-LEGACY-PAGE-99")
        self.assertNotIn("Page legacy hors PDF", detail_body)
        self.assertNotIn("Page 99", detail_body)

    def test_pdf_trace_legacy_zero_page_has_no_resume_link(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-PAGE-ZERO"
        self._add_pdf_document(doc_id, page_count="3")
        self._write_legacy_trace(
            trace_id="TRACE-LEGACY-PAGE-ZERO",
            document_ref=doc_id,
            page="0",
            comment="Page legacy nulle",
        )
        client = self._client()

        queue = client.get("/pdf-traces?token=local-secret")
        detail = client.get(f"/documents/{doc_id}?trace_id=TRACE-LEGACY-PAGE-ZERO&token=local-secret")

        _, detail_body = self._assert_no_legacy_resume(queue, detail, doc_id, "TRACE-LEGACY-PAGE-ZERO")
        self.assertNotIn("Page legacy nulle", detail_body)

    def test_pdf_trace_legacy_polluted_anchor_fallback_has_no_resume_link(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-POLLUTED-ANCHOR"
        response = self._queue_with_legacy_anchor(doc_id, "raw/SECRET-ANCHOR-HASH", "Ancre legacy polluee")

        body = unescape(response.text)
        self.assertIn("<strong>0</strong><span>traces a relire</span>", response.text)
        self.assertNotIn("SECRET-ANCHOR", body)
        self.assertNotIn("Ancre legacy polluee", body)
        self.assertNotIn(f"/documents/{doc_id}?trace_id=", response.text)
        self._assert_public_pages_are_clean(body)

    def test_pdf_trace_legacy_clean_anchor_fallback_keeps_resume_link(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-CLEAN-ANCHOR"
        response = self._queue_with_legacy_anchor(doc_id, "SAFEANCHOR123456", "Ancre legacy saine")

        detail_body = unescape(self._client().get(f"/documents/{doc_id}?trace_id=SAFEANCH&token=local-secret").text)
        self.assertIn("<strong>1</strong><span>traces a relire</span>", response.text)
        self.assertIn(f"/documents/{doc_id}?trace_id=SAFEANCH&amp;token=local-secret#pdf-reader", response.text)
        self.assertIn("Point de reprise ouvert", detail_body)
        self.assertIn("Vous reprenez ici: Zone encadree page 2.", detail_body)
        self.assertNotIn("SAFEANCHOR123456", detail_body)
        self._assert_public_pages_are_clean(unescape(response.text), detail_body)

    def test_document_detail_ignores_unknown_trace_id_without_leak(self) -> None:
        doc_id = "DOC-PDF-USER-TRACE-UNKNOWN-TRACE"
        self._add_pdf_document(doc_id)
        client = self._client()

        response = client.get(f"/documents/{doc_id}?trace_id=raw/TRACE-SECRET&token=local-secret")

        body = unescape(response.text)
        self.assertIn("Tracer une preuve candidate", body)
        self.assertNotIn("Point de reprise ouvert", body)
        self.assertNotIn("TRACE-SECRET", body)
        self._assert_public_pages_are_clean(body)

    def test_document_detail_ignores_trace_id_from_another_document(self) -> None:
        first_doc_id = "DOC-PDF-USER-TRACE-CROSS-A"
        second_doc_id = "DOC-PDF-USER-TRACE-CROSS-B"
        self._add_pdf_document(first_doc_id)
        self._add_pdf_document(second_doc_id)
        client = self._client()

        save_response = self._save_trace(client, second_doc_id, "2", "Trace du second document")
        trace_rows = read_csv(pdftrace_registry.trace_register_path(self.instance))[1]
        foreign_trace_id = trace_rows[0]["trace_id"]
        response = client.get(f"/documents/{first_doc_id}?trace_id={foreign_trace_id}&token=local-secret")

        self.assertEqual(save_response.status_code, 303)
        body = unescape(response.text)
        self.assertIn("Tracer une preuve candidate", body)
        self.assertNotIn("Point de reprise ouvert", body)
        self.assertNotIn("Vous reprenez ici", body)
        self.assertNotIn(foreign_trace_id, body)
        self.assertNotIn("Trace du second document", body)
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

    def _write_legacy_trace(self, **overrides: str) -> None:
        row = {
            **{field: "" for field in pdftrace_registry.PDF_TRACE_FIELDS},
            "page": "1",
            "zone_x": "0.10",
            "zone_y": "0.10",
            "zone_width": "0.20",
            "zone_height": "0.20",
            "document_hash_status": "document_hash_not_checked",
            "diffusion": "non_diffusable",
            "text_status": "non_confirme",
            **overrides,
        }
        write_csv(pdftrace_registry.trace_register_path(self.instance), pdftrace_registry.PDF_TRACE_FIELDS, [row])

    def _queue_with_legacy_anchor(self, doc_id: str, anchor_hash: str, comment: str):
        self._add_pdf_document(doc_id, page_count="3")
        self._write_legacy_trace(
            trace_id="",
            document_ref=doc_id,
            page="2",
            anchor_hash=anchor_hash,
            comment=comment,
        )
        return self._client().get("/pdf-traces?token=local-secret")

    def _assert_no_legacy_resume(self, queue, detail, doc_id: str, trace_id: str) -> tuple[str, str]:
        self.assertEqual(queue.status_code, 200)
        self.assertEqual(detail.status_code, 200)
        queue_body = unescape(queue.text)
        detail_body = unescape(detail.text)
        self.assertIn("<strong>0</strong><span>traces a relire</span>", queue.text)
        self.assertNotIn(trace_id, queue_body)
        self.assertNotIn(f"/documents/{doc_id}?trace_id={trace_id}", queue.text)
        self.assertNotIn("Point de reprise ouvert", detail_body)
        self.assertNotIn("Vous reprenez ici", detail_body)
        self._assert_public_pages_are_clean(queue_body, detail_body)
        return queue_body, detail_body

    def _assert_public_pages_are_clean(self, *bodies: str) -> None:
        for body in bodies:
            lowered = body.lower()
            self.assertNotIn(str(self.instance_root).lower(), lowered)
            for marker in FORBIDDEN_PUBLIC_MARKERS:
                self.assertNotIn(marker, lowered)


if __name__ == "__main__":
    unittest.main()
