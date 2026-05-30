from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path

from coproscope.modules.annotationops import non_destructive_sidecar_plan, normalize_annotation, validate_annotation
from coproscope.modules.pdftraceops import (
    SOURCE_ENGINE_PYMUPDF,
    build_text_map_from_words,
    candidate_to_annotation_row,
    candidate_to_public_dict,
    extract_pdf_text_map,
    find_text_traces,
    text_map_to_dict,
    zotero_position,
)


HASH = "sha256:" + "b" * 64


class PdfTraceOpsTests(unittest.TestCase):
    def test_finds_text_and_builds_zotero_compatible_position(self) -> None:
        text_map = build_text_map_from_words(
            document_ref="DOC-PV-2026",
            document_hash=HASH,
            pages=[
                {
                    "page_index": 0,
                    "width": 200,
                    "height": 100,
                    "words": [
                        {"text": "Resolution", "x0": 10, "y0": 20, "x1": 60, "y1": 30},
                        {"text": "travaux", "x0": 65, "y0": 20, "x1": 105, "y1": 30},
                        {"text": "votee", "x0": 110, "y0": 20, "x1": 140, "y1": 30},
                    ],
                }
            ],
        )

        candidates = find_text_traces(text_map, "travaux votee")

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.page_index, 0)
        self.assertEqual(candidate.page_label, "1")
        self.assertEqual(candidate.selected_text, "travaux votee")
        self.assertTrue(candidate.selected_text_hash.startswith("sha256:"))
        self.assertEqual(candidate.sort_index, "00000|0.200000|0.325000")
        position = zotero_position(candidate)
        self.assertEqual(position["pageIndex"], 0)
        self.assertEqual(position["pageLabel"], "1")
        self.assertEqual(position["rects"][0]["x"], 0.325)
        self.assertEqual(position["rects"][1]["width"], 0.15)

    def test_candidate_becomes_valid_non_destructive_annotation_row(self) -> None:
        text_map = build_text_map_from_words(
            document_ref="DOC-FACTURE-1",
            document_hash=HASH,
            pages=[
                {
                    "page_index": 2,
                    "page_label": "A-3",
                    "words": [
                        {"text": "Montant", "x": 0.1, "y": 0.7, "width": 0.15, "height": 0.04},
                        {"text": "12480", "x": 0.3, "y": 0.7, "width": 0.12, "height": 0.04},
                    ],
                }
            ],
        )
        candidate = find_text_traces(text_map, "Montant 12480")[0]

        row = candidate_to_annotation_row(
            candidate,
            comment="Verifier le montant avant rattachement au controle comptes.",
            author_ref="user:cs-demo",
            created_at="2026-05-31T01:10:00Z",
            point_ref="POINT-COMPTES-1",
            action_ref="ACT-CONTROLE-1",
            proof_ref="PROOF-FACTURE-1",
        )
        annotation = normalize_annotation(row)

        self.assertEqual(validate_annotation(annotation), tuple())
        self.assertEqual(annotation.anchor.page, 3)
        self.assertEqual(annotation.anchor.zone.x, 0.1)
        self.assertEqual(annotation.anchor.zone.width, 0.32)
        self.assertFalse(non_destructive_sidecar_plan(annotation)["source_write_allowed"])

    def test_private_path_text_is_masked_from_public_payload(self) -> None:
        text_map = build_text_map_from_words(
            document_ref="DOC-LOCAL-HINT",
            document_hash=HASH,
            pages=[
                {
                    "page_index": 0,
                    "words": [
                        {"text": r"C:\Users\Example\secret.pdf", "x": 0.1, "y": 0.1, "width": 0.5, "height": 0.04}
                    ],
                }
            ],
        )
        candidate = find_text_traces(text_map, "secret.pdf")[0]

        payload = candidate_to_public_dict(candidate)
        rendered = str(payload)

        self.assertTrue(payload["private_excerpt_blocked"])
        self.assertIn("extrait masque", payload["selected_text_excerpt"])
        self.assertNotIn(r"C:\Users", rendered)
        self.assertNotIn("secret.pdf", rendered)

    def test_extract_pdf_text_map_uses_pymupdf_words_without_exposing_source_path(self) -> None:
        original_fitz = sys.modules.get("fitz")
        sys.modules["fitz"] = _fake_fitz_module()
        try:
            text_map = extract_pdf_text_map(
                Path(r"C:\Users\Example\raw\demo.pdf"),
                document_ref="DOC-DEMO",
                document_hash=HASH,
            )
        finally:
            if original_fitz is None:
                sys.modules.pop("fitz", None)
            else:
                sys.modules["fitz"] = original_fitz

        self.assertEqual(text_map.source_engine, SOURCE_ENGINE_PYMUPDF)
        self.assertEqual(text_map.pages[0].words[0].text, "Appel")
        payload = text_map_to_dict(text_map)
        rendered = str(payload)
        self.assertNotIn(r"C:\Users", rendered)
        self.assertNotIn("raw", rendered.lower())


def _fake_fitz_module() -> types.SimpleNamespace:
    class Rect:
        width = 200
        height = 100

    class Page:
        rect = Rect()
        rotation = 0

        def get_text(self, mode: str):
            if mode != "words":
                raise AssertionError(mode)
            return [(10, 20, 50, 30, "Appel", 0, 0, 0), (55, 20, 95, 30, "fonds", 0, 0, 1)]

    class Document:
        page_count = 1

        def load_page(self, index: int) -> Page:
            if index != 0:
                raise AssertionError(index)
            return Page()

        def close(self) -> None:
            return None

    return types.SimpleNamespace(open=lambda _path: Document())


if __name__ == "__main__":
    unittest.main()
