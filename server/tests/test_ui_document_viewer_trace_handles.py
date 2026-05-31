from __future__ import annotations

import hashlib
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import load_instance, read_csv, relative_to, write_csv
from coproscope.web.app import create_app


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class DocumentViewerTraceHandleTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.repo_root = repo_root
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

    def _add_pdf(self, doc_id: str) -> None:
        fields, rows = self._documents()
        pdf_path = self.instance_root / "staging" / "pdf" / f"{doc_id}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_bytes = b"%PDF-1.4\n% trace handles\n"
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
                "page_count": "3",
                "text_char_count": "120",
            }
        )
        self._write_documents(fields, rows)

    def test_pdf_trace_selection_renders_eight_visible_handles_without_leaks(self) -> None:
        doc_id = "DOC-PDF-TRACE-HANDLES"
        self._add_pdf(doc_id)

        response = self._client().get(f"/documents/{doc_id}")
        body = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Zone a selectionner sur la page 1", body)
        self.assertIn("Zone ajustable sur la page {page}", response.text)
        self.assertIn("Tirer les poignees pour ajuster.", body)
        self.assertIn("Enregistrer comme trace a verifier", body)
        for handle in ("nw", "n", "ne", "e", "se", "s", "sw", "w"):
            self.assertIn(f'data-pdf-trace-handle="{handle}"', response.text)
            self.assertIn(f"cs-pdf-trace-selection-handle-{handle}", response.text)
        self.assertNotIn("source_engine", body)
        self.assertNotIn("zotero_position", body)
        self.assertNotIn("rects", body)
        self.assertNotIn("selected_text_hash", body)
        self.assertNotIn(str(self.instance_root), body)
        self.assertNotIn("raw/", body.lower())

    def test_pdf_trace_selection_script_supports_resize_and_bounds(self) -> None:
        script = (
            self.repo_root / "server" / "src" / "coproscope" / "web" / "static" / "pdf_trace_selection.js"
        ).read_text(encoding="utf-8")

        self.assertIn("data-pdf-trace-handle", script)
        self.assertIn("boundedResizeRect", script)
        self.assertIn("Zone trop petite : recommencez la selection", script)
        self.assertIn("clamp(point.x, 0, layerWidth)", script)
        self.assertIn("clamp(point.y, 0, layerHeight)", script)
        self.assertIn("drag.kind === \"resize\"", script)
        self.assertIn("resetSelection(emptyForPage())", script)
        self.assertIn("field(form, \"x\").value = \"\"", script)
        self.assertNotIn("zotero_position", script)
        self.assertNotIn("source_engine", script)
        self.assertNotIn("rects", script)

    def test_pdf_trace_handle_css_uses_tactile_targets(self) -> None:
        styles = (
            self.repo_root / "server" / "src" / "coproscope" / "web" / "static" / "styles_part_31.css"
        ).read_text(encoding="utf-8")

        self.assertIn(".cs-pdf-trace-selection-handle", styles)
        self.assertIn("width: 16px", styles)
        self.assertIn("@media (pointer: coarse)", styles)
        self.assertIn("width: 22px", styles)
        for handle in ("nw", "n", "ne", "e", "se", "s", "sw", "w"):
            self.assertIn(f".cs-pdf-trace-selection-handle-{handle}", styles)


if __name__ == "__main__":
    unittest.main()
