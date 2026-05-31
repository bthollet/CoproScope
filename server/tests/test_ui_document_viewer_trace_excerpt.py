from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
import types
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import load_instance, read_csv, relative_to, write_csv
from coproscope.modules import pdftrace_registry
from coproscope.modules.pdftrace_contracts import hash_text
from coproscope.web.app import create_app


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class DocumentViewerTraceExcerptTests(unittest.TestCase):
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

    def _add_pdf(self, doc_id: str, content: bytes = b"%PDF-1.4\n% trace excerpt UI\n") -> Path:
        fields, rows = self._documents()
        pdf_path = self.instance_root / "staging" / "pdf" / f"{doc_id}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(content)
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": f"{doc_id}.pdf",
                "extension": "pdf",
                "sha256": _sha256(content),
                "size_bytes": str(pdf_path.stat().st_size),
                "original_path": relative_to(self.instance_root, pdf_path),
                "source_zone": "STAGING",
                "document_type": "PDF",
                "status_ocr": "TEXT_EXTRACTED",
                "classification_status": "A_RELIRE",
                "page_count": "1",
                "text_char_count": "120",
            }
        )
        self._write_documents(fields, rows)
        return pdf_path

    def test_pdf_trace_text_excerpt_is_visible_and_separate_from_comment(self) -> None:
        doc_id = "DOC-PDF-TRACE-EXCERPT"
        self._add_pdf(doc_id)

        with _patched_fitz(
            [
                (10, 20, 55, 30, "Budget", 0, 0, 0),
                (60, 20, 90, 30, "vote", 0, 0, 1),
                (10, 80, 40, 90, "hors-zone", 0, 1, 0),
            ]
        ):
            response = self._client().post(
                f"/documents/{doc_id}/traces",
                data={
                    "page": "1",
                    "zone_x": "0.05",
                    "zone_y": "0.15",
                    "zone_width": "0.50",
                    "zone_height": "0.20",
                    "comment": "Budget previsionnel a relire",
                },
                follow_redirects=False,
            )
        detail = self._client().get(f"/documents/{doc_id}")
        body = unescape(detail.text)

        self.assertEqual(response.status_code, 303)
        self.assertEqual(detail.status_code, 200)
        self.assertIn("Texte repere automatiquement, a relire. Preuve non validee par CoproScope.", body)
        self.assertIn("Extrait repere", body)
        self.assertIn("Texte repere: Budget vote", body)
        self.assertIn("Commentaire: Budget previsionnel a relire", body)
        self.assertLess(body.index("Texte repere: Budget vote"), body.index("Commentaire: Budget previsionnel a relire"))
        self.assertNotIn("hors-zone", body)
        self._assert_no_private_or_technical_leak(body)

    def test_pdf_trace_sensitive_excerpt_is_masked_in_document_detail(self) -> None:
        doc_id = "DOC-PDF-TRACE-SENSITIVE-EXCERPT"
        self._add_pdf(doc_id)

        with _patched_fitz(
            [
                (10, 20, 55, 30, "contact", 0, 0, 0),
                (60, 20, 125, 30, "test@example.com", 0, 0, 1),
                (130, 20, 190, 30, "token=abc123", 0, 0, 2),
            ]
        ):
            response = self._client().post(
                f"/documents/{doc_id}/traces",
                data={
                    "page": "1",
                    "zone_x": "0.05",
                    "zone_y": "0.15",
                    "zone_width": "0.90",
                    "zone_height": "0.20",
                    "comment": "Texte sensible a masquer",
                },
                follow_redirects=False,
            )
        body = unescape(self._client().get(f"/documents/{doc_id}").text)
        raw_text_hash = hash_text("contact test@example.com token=abc123")

        self.assertEqual(response.status_code, 303)
        self.assertIn("extrait masque", body)
        self.assertNotIn("test@example.com", body)
        self.assertNotIn("token=abc123", body)
        self.assertNotIn(raw_text_hash, body)
        self._assert_no_private_or_technical_leak(body)

    def test_pdf_trace_changed_document_excerpt_stays_to_verify(self) -> None:
        doc_id = "DOC-PDF-TRACE-CHANGED-EXCERPT"
        pdf_path = self._add_pdf(doc_id, b"%PDF-1.4\n% registered version\n")
        pdf_path.write_bytes(b"%PDF-1.4\n% changed version\n")

        with _patched_fitz([(10, 20, 55, 30, "Budget", 0, 0, 0), (60, 20, 90, 30, "vote", 0, 0, 1)]):
            response = self._client().post(
                f"/documents/{doc_id}/traces",
                data={
                    "page": "1",
                    "zone_x": "0.05",
                    "zone_y": "0.15",
                    "zone_width": "0.50",
                    "zone_height": "0.20",
                    "comment": "Trace a verifier apres changement",
                },
                follow_redirects=False,
            )
        body = unescape(self._client().get(f"/documents/{doc_id}").text)

        self.assertEqual(response.status_code, 303)
        self.assertIn("Document modifie depuis la trace: verifier la zone avant usage.", body)
        self.assertIn("Le document a change depuis son ajout dans CoproScope", body)
        self.assertNotIn("preuve validee", body.lower())
        self._assert_no_private_or_technical_leak(body)

    def _assert_no_private_or_technical_leak(self, body: str) -> None:
        forbidden = (
            "source_engine",
            "zotero_position",
            "rects",
            "selected_text_hash",
            "original_path",
            str(self.instance_root),
            "raw/",
            "raw\\",
        )
        for value in forbidden:
            self.assertNotIn(value, body)


class _patched_fitz:
    def __init__(self, words):
        self.words = words
        self.original = None

    def __enter__(self):
        self.original = sys.modules.get("fitz")
        sys.modules["fitz"] = _fake_fitz_module(self.words)

    def __exit__(self, *_args):
        if self.original is None:
            sys.modules.pop("fitz", None)
        else:
            sys.modules["fitz"] = self.original


def _fake_fitz_module(words) -> types.SimpleNamespace:
    class Rect:
        width = 200
        height = 100

    class Page:
        rect = Rect()
        rotation = 0

        def get_text(self, mode: str):
            if mode != "words":
                raise AssertionError(mode)
            return words

    class Document:
        page_count = 1

        def load_page(self, index: int) -> Page:
            if index != 0:
                raise AssertionError(index)
            return Page()

        def close(self) -> None:
            return None

        def save(self, *_args, **_kwargs) -> None:
            raise AssertionError("source PDF must not be saved")

        write = save
        saveIncr = save

    return types.SimpleNamespace(open=lambda _path: Document())


if __name__ == "__main__":
    unittest.main()
