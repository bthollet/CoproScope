from __future__ import annotations

import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, load_instance, read_csv, relative_to, write_csv
from coproscope.modules import pdftrace_registry
from coproscope.web.app import create_app

from tests.test_ui_pdftrace_user_routes import FORBIDDEN_PUBLIC_MARKERS, _sha256


class PdfTraceLegacyPrivacyRouteTests(unittest.TestCase):
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

    def test_legacy_trace_id_containing_token_is_not_public_resume_link(self) -> None:
        self._assert_polluted_trace_id_is_private(
            "TRACE-token=secret-local",
            "Trace legacy avec jeton dans identifiant",
            ("TRACE-token", "secret-local"),
        )

    def test_legacy_trace_id_containing_local_path_is_not_public_resume_link(self) -> None:
        self._assert_polluted_trace_id_is_private(
            r"C:\Users\Example\raw\piece.pdf",
            "Trace legacy avec chemin dans identifiant",
            ("Users", "piece.pdf"),
        )

    def test_legacy_selected_text_hash_is_not_visible_on_public_pages(self) -> None:
        doc_id = "DOC-PDF-LEGACY-HASH-FIELD"
        self._add_pdf_document(doc_id)
        self._write_legacy_trace(
            trace_id="TRACE-LEGACY-HASH-FIELD",
            document_ref=doc_id,
            selected_text_hash="sha256:private-selected-text-hash",
            comment="Note legacy avec hash technique",
        )
        client = self._client()

        queue = client.get("/pdf-traces?token=local-secret")
        detail = client.get(f"/documents/{doc_id}?trace_id=TRACE-LEGACY-HASH-FIELD&token=local-secret")

        queue_body = unescape(queue.text)
        detail_body = unescape(detail.text)
        self.assertIn("<strong>1</strong><span>traces a relire</span>", queue.text)
        self.assertIn("Point de reprise ouvert", detail_body)
        self.assertNotIn("private-selected-text-hash", queue_body)
        self.assertNotIn("private-selected-text-hash", detail_body)
        self._assert_public_pages_are_clean(queue_body, detail_body)

    def test_legacy_source_engine_is_not_visible_on_public_pages(self) -> None:
        doc_id = "DOC-PDF-LEGACY-SOURCE-ENGINE"
        self._add_pdf_document(doc_id)
        self._write_legacy_trace(
            trace_id="TRACE-LEGACY-SOURCE-ENGINE",
            document_ref=doc_id,
            source_engine="zotero_position",
            comment="Note legacy avec moteur interne",
        )
        client = self._client()

        queue = client.get("/pdf-traces?token=local-secret")
        detail = client.get(f"/documents/{doc_id}?trace_id=TRACE-LEGACY-SOURCE-ENGINE&token=local-secret")

        queue_body = unescape(queue.text)
        detail_body = unescape(detail.text)
        self.assertIn("<strong>1</strong><span>traces a relire</span>", queue.text)
        self.assertIn("Point de reprise ouvert", detail_body)
        self.assertNotIn("zotero_position", queue_body)
        self.assertNotIn("zotero_position", detail_body)
        self._assert_public_pages_are_clean(queue_body, detail_body)

    def test_legacy_rects_extra_column_is_not_visible_on_public_pages(self) -> None:
        doc_id = "DOC-PDF-LEGACY-ZONE"
        self._add_pdf_document(doc_id)
        self._write_legacy_trace(
            trace_id="TRACE-LEGACY-ZONE",
            document_ref=doc_id,
            rects='[{"x":0.10,"y":0.20,"width":0.30,"height":0.40}]',
            comment="Note legacy de reprise",
        )
        client = self._client()

        queue = client.get("/pdf-traces?token=local-secret")
        detail = client.get(f"/documents/{doc_id}?trace_id=TRACE-LEGACY-ZONE&token=local-secret")

        queue_body = unescape(queue.text)
        detail_body = unescape(detail.text)
        self.assertIn("<strong>1</strong><span>traces a relire</span>", queue.text)
        self.assertIn("Point de reprise ouvert", detail_body)
        self.assertNotIn("0.30", queue_body)
        self.assertNotIn("0.40", detail_body)
        self._assert_public_pages_are_clean(queue_body, detail_body)

    def _add_pdf_document(self, doc_id: str) -> None:
        fields, rows = read_csv(self.instance.register("documents"))
        fields = fields or list(DEFAULT_DOCUMENT_FIELDS)
        pdf_bytes = b"%PDF-1.4\n% FICTIF pdf trace legacy privacy test\n"
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
                "page_count": "3",
            }
        )
        write_csv(self.instance.register("documents"), fields, rows)

    def _write_legacy_trace(self, **overrides: str) -> None:
        fields = [*pdftrace_registry.PDF_TRACE_FIELDS]
        fields.extend(field for field in overrides if field not in fields)
        row = {
            **{field: "" for field in fields},
            "page": "2",
            "zone_x": "0.10",
            "zone_y": "0.10",
            "zone_width": "0.20",
            "zone_height": "0.20",
            "document_hash_status": "document_hash_not_checked",
            "diffusion": "non_diffusable",
            "text_status": "non_confirme",
            **overrides,
        }
        write_csv(pdftrace_registry.trace_register_path(self.instance), fields, [row])

    def _assert_polluted_trace_id_is_private(self, trace_id: str, comment: str, hidden_markers: tuple[str, ...]) -> None:
        doc_id = "DOC-PDF-LEGACY-PRIVATE-TRACE"
        self._add_pdf_document(doc_id)
        self._write_legacy_trace(trace_id=trace_id, document_ref=doc_id, comment=comment)
        client = self._client()

        queue = client.get("/pdf-traces?token=local-secret")
        detail = client.get(f"/documents/{doc_id}?trace_id={trace_id}&token=local-secret")

        queue_body = unescape(queue.text)
        detail_body = unescape(detail.text)
        self.assertIn("<strong>0</strong><span>traces a relire</span>", queue.text)
        for marker in hidden_markers:
            self.assertNotIn(marker, queue_body)
        self.assertNotIn(comment, detail_body)
        self.assertNotIn("Point de reprise ouvert", detail_body)
        self._assert_public_pages_are_clean(queue_body, detail_body)

    def _assert_public_pages_are_clean(self, *bodies: str) -> None:
        for body in bodies:
            lowered = body.lower()
            self.assertNotIn(str(self.instance_root).lower(), lowered)
            for marker in FORBIDDEN_PUBLIC_MARKERS:
                self.assertNotIn(marker, lowered)


if __name__ == "__main__":
    unittest.main()
