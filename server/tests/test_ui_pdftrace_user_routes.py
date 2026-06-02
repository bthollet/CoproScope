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

    def _assert_public_pages_are_clean(self, *bodies: str) -> None:
        for body in bodies:
            lowered = body.lower()
            self.assertNotIn(str(self.instance_root).lower(), lowered)
            for marker in FORBIDDEN_PUBLIC_MARKERS:
                self.assertNotIn(marker, lowered)


if __name__ == "__main__":
    unittest.main()
