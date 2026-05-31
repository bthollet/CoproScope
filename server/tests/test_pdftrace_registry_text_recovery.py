from __future__ import annotations

import hashlib
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path

from coproscope.core.common import load_instance, read_csv, relative_to, write_csv
from coproscope.modules import pdftrace_registry
from coproscope.modules.pdftrace_contracts import hash_text


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class PdfTraceRegistryTextRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _documents(self) -> tuple[list[str], list[dict[str, str]]]:
        return read_csv(self.instance.register("documents"))

    def _write_documents(self, fields: list[str], rows: list[dict[str, str]]) -> None:
        write_csv(self.instance.register("documents"), fields, rows)

    def _add_pdf(self, doc_id: str, content: bytes = b"%PDF-1.4\n% text zone recovery\n") -> Path:
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
                "page_count": "1",
                "text_char_count": "120",
            }
        )
        self._write_documents(fields, rows)
        return pdf_path

    def test_zone_trace_recovers_candidate_text_from_text_pdf_without_mutating_source(self) -> None:
        doc_id = "DOC-PDF-ZONE-TEXT"
        pdf_path = self._add_pdf(doc_id)
        original_bytes = pdf_path.read_bytes()

        with _patched_fitz(
            [
                (10, 20, 55, 30, "Budget", 0, 0, 0),
                (60, 20, 90, 30, "vote", 0, 0, 1),
                (10, 80, 40, 90, "hors-zone", 0, 1, 0),
            ]
        ):
            row = pdftrace_registry.save_zone_trace(
                self.instance,
                _registered_document(self.instance, doc_id),
                {
                    "page": "1",
                    "zone_x": "0.05",
                    "zone_y": "0.15",
                    "zone_width": "0.50",
                    "zone_height": "0.20",
                    "comment": "Texte candidat a verifier",
                },
                created_at="2026-05-31T04:20:00Z",
            )

        summaries = pdftrace_registry.public_trace_summaries(self.instance, doc_id)

        self.assertEqual(pdf_path.read_bytes(), original_bytes)
        self.assertEqual(row["text_status"], "texte_reconnu")
        self.assertEqual(row["source_engine"], "pymupdf_text_map")
        self.assertEqual(row["confidence"], "text_from_selected_zone")
        self.assertTrue(row["selected_text_hash"].startswith("sha256:"))
        self.assertIn("Budget vote", row["selected_text_excerpt"])
        self.assertNotIn("hors-zone", row["selected_text_excerpt"])
        self.assertEqual(summaries[0]["text"], "Texte repere automatiquement, a relire. Preuve non validee par CoproScope.")
        self.assertNotIn(str(self.instance_root), str(summaries))

    def test_zone_trace_masks_sensitive_candidate_text(self) -> None:
        doc_id = "DOC-PDF-ZONE-SENSITIVE"
        self._add_pdf(doc_id)

        with _patched_fitz(
            [
                (10, 20, 55, 30, "contact", 0, 0, 0),
                (60, 20, 125, 30, "test@example.com", 0, 0, 1),
                (130, 20, 190, 30, "token=abc123", 0, 0, 2),
            ]
        ):
            row = pdftrace_registry.save_zone_trace(
                self.instance,
                _registered_document(self.instance, doc_id),
                {
                    "page": "1",
                    "zone_x": "0.05",
                    "zone_y": "0.15",
                    "zone_width": "0.90",
                    "zone_height": "0.20",
                    "comment": "Texte sensible a masquer",
                },
            )

        rendered = str(row) + str(pdftrace_registry.public_trace_summaries(self.instance, doc_id))
        raw_text_hash = hash_text("contact test@example.com token=abc123")

        self.assertEqual(row["text_status"], "texte_reconnu")
        self.assertIn("extrait masque", row["selected_text_excerpt"])
        self.assertNotEqual(row["selected_text_hash"], raw_text_hash)
        self.assertEqual(row["selected_text_hash"], row["anchor_hash"])
        self.assertNotIn("test@example.com", rendered)
        self.assertNotIn("token=abc123", rendered)

    def test_zone_trace_marks_recovered_text_to_verify_when_document_changed(self) -> None:
        doc_id = "DOC-PDF-ZONE-CHANGED"
        registered = b"%PDF-1.4\n% registered\n"
        changed = b"%PDF-1.4\n% changed\n"
        pdf_path = self._add_pdf(doc_id, registered)
        pdf_path.write_bytes(changed)

        with _patched_fitz([(10, 20, 55, 30, "Budget", 0, 0, 0), (60, 20, 90, 30, "vote", 0, 0, 1)]):
            row = pdftrace_registry.save_zone_trace(
                self.instance,
                _registered_document(self.instance, doc_id),
                {
                    "page": "1",
                    "zone_x": "0.05",
                    "zone_y": "0.15",
                    "zone_width": "0.50",
                    "zone_height": "0.20",
                    "comment": "Texte a verifier apres changement",
                },
            )

        summaries = pdftrace_registry.public_trace_summaries(self.instance, doc_id)

        self.assertEqual(pdf_path.read_bytes(), changed)
        self.assertEqual(row["document_hash_status"], "hash_a_verifier")
        self.assertEqual(row["text_status"], "a_verifier")
        self.assertIn("Document modifie", row["selected_text_excerpt"])
        self.assertIn("document a change", summaries[0]["text"])
        self.assertNotIn("preuve validee", str(summaries).lower())

    def test_zone_trace_keeps_zone_only_when_text_extraction_is_unavailable(self) -> None:
        doc_id = "DOC-PDF-ZONE-FALLBACK"
        self._add_pdf(doc_id)

        with _patched_broken_fitz():
            row = pdftrace_registry.save_zone_trace(
                self.instance,
                _registered_document(self.instance, doc_id),
                {
                    "page": "1",
                    "zone_x": "0.05",
                    "zone_y": "0.15",
                    "zone_width": "0.50",
                    "zone_height": "0.20",
                    "comment": "Zone seule",
                },
            )

        self.assertEqual(row["text_status"], "non_confirme")
        self.assertEqual(row["source_engine"], "manual_pdf_pointer")
        self.assertEqual(row["confidence"], "zone_only")
        self.assertEqual(row["selected_text_excerpt"], "")

    def test_zone_trace_appends_after_legacy_register_without_text_columns(self) -> None:
        doc_id = "DOC-PDF-ZONE-LEGACY"
        self._add_pdf(doc_id)
        legacy_fields = [
            field
            for field in pdftrace_registry.PDF_TRACE_FIELDS
            if field not in {"selected_text_hash", "selected_text_excerpt", "confidence"}
        ]
        write_csv(
            pdftrace_registry.trace_register_path(self.instance),
            legacy_fields,
            [
                {
                    **{field: "" for field in legacy_fields},
                    "trace_id": "ANN-LEGACY",
                    "document_ref": doc_id,
                    "page": "1",
                    "zone_x": "0.1",
                    "zone_y": "0.1",
                    "zone_width": "0.2",
                    "zone_height": "0.2",
                    "text_status": "non_confirme",
                    "document_hash_status": "hash_non_verifie",
                }
            ],
        )

        with _patched_fitz([(10, 20, 55, 30, "Budget", 0, 0, 0), (60, 20, 90, 30, "vote", 0, 0, 1)]):
            pdftrace_registry.save_zone_trace(
                self.instance,
                _registered_document(self.instance, doc_id),
                {
                    "page": "1",
                    "zone_x": "0.05",
                    "zone_y": "0.15",
                    "zone_width": "0.50",
                    "zone_height": "0.20",
                    "comment": "Nouvelle trace apres registre ancien",
                },
            )

        fields, rows = read_csv(pdftrace_registry.trace_register_path(self.instance))

        self.assertEqual(fields, pdftrace_registry.PDF_TRACE_FIELDS)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["trace_id"], "ANN-LEGACY")
        self.assertEqual(rows[0]["selected_text_excerpt"], "")
        self.assertIn("Budget vote", rows[1]["selected_text_excerpt"])


def _registered_document(instance, doc_id: str) -> dict[str, str]:
    return next(row for row in read_csv(instance.register("documents"))[1] if row.get("doc_id") == doc_id)


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


class _patched_broken_fitz:
    def __enter__(self):
        self.original = sys.modules.get("fitz")
        sys.modules["fitz"] = types.SimpleNamespace(open=lambda _path: (_ for _ in ()).throw(RuntimeError("broken")))

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
