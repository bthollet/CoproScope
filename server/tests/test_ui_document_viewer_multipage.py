from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import load_instance, read_csv, relative_to, write_csv
from coproscope.modules import pdftrace_registry
from coproscope.web.app import create_app


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class DocumentViewerMultipageTraceTests(unittest.TestCase):
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
        except Exception as exc:  # pragma: no cover
            self.skipTest(f"fastapi test client unavailable: {exc}")
        return TestClient(create_app(self.instance, 2025))

    def _documents(self) -> tuple[list[str], list[dict[str, str]]]:
        return read_csv(self.instance.register("documents"))

    def _write_documents(self, fields: list[str], rows: list[dict[str, str]]) -> None:
        write_csv(self.instance.register("documents"), fields, rows)

    def _add_pdf(self, doc_id: str, *, page_count: str = "3") -> tuple[Path, bytes]:
        fields, rows = self._documents()
        pdf_path = self.instance_root / "staging" / "pdf" / f"{doc_id}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_bytes = b"%PDF-1.4\n% multipage trace test\n"
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
                "document_type": "PDF",
                "page_count": page_count,
                "text_char_count": "120",
            }
        )
        self._write_documents(fields, rows)
        return pdf_path, pdf_bytes

    def test_pdf_trace_multipage_controls_are_rendered_without_leaks(self) -> None:
        doc_id = "DOC-PDF-MULTIPAGE-CONTROLS"
        self._add_pdf(doc_id, page_count="3")

        response = self._client().get(f"/documents/{doc_id}")
        body = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn('data-pdf-trace-current-page="1"', response.text)
        self.assertIn('data-pdf-trace-page-count="3"', response.text)
        self.assertIn("Page precedente", body)
        self.assertIn("Page suivante", body)
        self.assertIn("Page 1 sur 3", body)
        self.assertIn("Miniatures des pages", body)
        self.assertIn('name="page" value="1"', response.text)
        self.assertIn("Choisissez la page, puis encadrez la zone", body)
        self.assertIn("Zone a selectionner sur la page 1", body)
        self.assertIn('data-pdf-trace-ready-label="Zone ajustable sur la page {page}"', response.text)
        self.assertIn("Enregistrer comme trace a verifier", body)
        self.assertIn("Tirer les poignees pour ajuster.", body)
        self.assertIn("Le PDF original n'est pas modifie.", body)
        self.assertNotIn(str(self.instance_root), body)
        self.assertNotIn("original_path", body)
        self.assertNotIn("source_engine", body)
        self.assertNotIn("zotero_position", body)
        self.assertNotIn("rects", body)

    def test_pdf_trace_multipage_post_saves_selected_page(self) -> None:
        doc_id = "DOC-PDF-MULTIPAGE-SAVE"
        pdf_path, pdf_bytes = self._add_pdf(doc_id, page_count="3")

        response = self._client().post(
            f"/documents/{doc_id}/traces",
            data={
                "page": "2",
                "zone_x": "0.20",
                "zone_y": "0.25",
                "zone_width": "0.40",
                "zone_height": "0.10",
                "comment": "Tableau a relire page 2",
            },
            follow_redirects=False,
        )
        trace_rows = read_csv(pdftrace_registry.trace_register_path(self.instance))[1]
        detail = self._client().get(f"/documents/{doc_id}")
        body = unescape(detail.text)

        self.assertEqual(response.status_code, 303)
        self.assertEqual(pdf_path.read_bytes(), pdf_bytes)
        self.assertEqual(trace_rows[0]["page"], "2")
        self.assertEqual(trace_rows[0]["proof_status"], "preuve_candidate")
        self.assertEqual(trace_rows[0]["text_status"], "non_confirme")
        self.assertEqual(trace_rows[0]["diffusion"], "non_diffusable")
        self.assertEqual(trace_rows[0]["write_policy"], "source_pdf_is_never_modified")
        self.assertIn("Zone encadree page 2", body)
        self.assertIn("Tableau a relire page 2", body)
        self.assertNotIn(str(self.instance_root), body)
        self.assertNotIn("source_engine", body)
        self.assertNotIn("zotero_position", body)
        self.assertNotIn("rects", body)

    def test_pdf_trace_multipage_rejects_page_outside_known_document(self) -> None:
        doc_id = "DOC-PDF-MULTIPAGE-INVALID"
        self._add_pdf(doc_id, page_count="3")

        response = self._client().post(
            f"/documents/{doc_id}/traces",
            data={
                "page": "4",
                "zone_x": "0.20",
                "zone_y": "0.25",
                "zone_width": "0.40",
                "zone_height": "0.10",
                "comment": "Page impossible",
            },
            follow_redirects=False,
        )
        trace_path = pdftrace_registry.trace_register_path(self.instance)
        rows = read_csv(trace_path)[1] if trace_path.exists() else []

        self.assertEqual(response.status_code, 422)
        self.assertIn("page de trace hors document", response.text)
        self.assertEqual(rows, [])

    def test_pdf_trace_script_resets_zone_when_page_changes(self) -> None:
        script = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "coproscope"
            / "web"
            / "static"
            / "pdf_trace_selection.js"
        ).read_text(encoding="utf-8")

        self.assertIn("data-pdf-trace-page-next", script)
        self.assertIn("data-pdf-trace-page-prev", script)
        self.assertIn("data-pdf-trace-page-input", script)
        self.assertIn("resetSelection", script)
        self.assertIn('field(form, "page").value = String(currentPage);', script)
        self.assertNotIn('field(form, "page").value = "1";', script)
        self.assertNotIn("zotero_position", script)
        self.assertNotIn("source_engine", script)
        self.assertNotIn("rects", script)


if __name__ == "__main__":
    unittest.main()
