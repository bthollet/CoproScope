from __future__ import annotations

import sys
import types
import unittest
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

from coproscope.modules.annotationops import event_payload, non_destructive_sidecar_plan, normalize_annotation, validate_annotation
from coproscope.modules.pdftraceops import (
    DOCUMENT_HASH_MATCH,
    DOCUMENT_HASH_MISMATCH,
    PUBLIC_TEXT_EXCERPT_MASK,
    PROOF_STATUS_CANDIDATE,
    SOURCE_ENGINE_PYMUPDF,
    TEXT_STATUS_REVIEW_REQUIRED,
    TEXT_STATUS_RECOGNIZED,
    build_text_map_from_words,
    build_zone_trace_candidate,
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
        self.assertTrue(candidate.anchor_hash.startswith("sha256:"))
        self.assertEqual(candidate.text_status, TEXT_STATUS_RECOGNIZED)
        self.assertEqual(candidate.sort_index, "00000|0.200000|0.325000")
        position = zotero_position(candidate)
        self.assertEqual(position["pageIndex"], 0)
        self.assertEqual(position["pageLabel"], "1")
        self.assertEqual(position["rects"][0]["x"], 0.325)
        self.assertEqual(position["rects"][1]["width"], 0.15)
        payload = candidate_to_public_dict(candidate)
        self.assertEqual(payload["proof_status"], PROOF_STATUS_CANDIDATE)
        self.assertEqual(payload["selected_text_excerpt"], PUBLIC_TEXT_EXCERPT_MASK)
        self.assertEqual(payload["user_notice"]["proof"], "Preuve candidate a verifier")

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
        self.assertEqual(row["diffusion"], "non_diffusable")
        self.assertEqual(row["anchor_hash"], candidate.anchor_hash)
        self.assertEqual(len(row["rects"]), 2)
        self.assertEqual(event_payload(annotation)["diffusion"], "non_diffusable")
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

    def test_sensitive_text_markers_are_never_exposed_in_public_payload(self) -> None:
        text_map = build_text_map_from_words(
            document_ref="DOC-SENSITIVE-HINT",
            document_hash=HASH,
            pages=[
                {
                    "page_index": 0,
                    "words": [
                        {"text": "contact", "x": 0.1, "y": 0.1, "width": 0.1, "height": 0.04},
                        {"text": "test@example.com", "x": 0.2, "y": 0.1, "width": 0.2, "height": 0.04},
                        {"text": "token=abc123", "x": 0.4, "y": 0.1, "width": 0.2, "height": 0.04},
                    ],
                }
            ],
        )
        candidate = find_text_traces(text_map, "test@example.com token=abc123")[0]
        raw_text_hash = "sha256:" + hashlib.sha256("test@example.com token=abc123".encode("utf-8")).hexdigest()

        payload = candidate_to_public_dict(candidate)
        rendered = str(payload)

        self.assertTrue(payload["private_excerpt_blocked"])
        self.assertNotEqual(payload["selected_text_hash"], raw_text_hash)
        self.assertIn("extrait masque", payload["selected_text_excerpt"])
        self.assertNotIn("test@example.com", rendered)
        self.assertNotIn("token=abc123", rendered)

    def test_same_phrase_twice_has_same_text_hash_and_distinct_anchor(self) -> None:
        text_map = build_text_map_from_words(
            document_ref="DOC-DUPLICATE",
            document_hash=HASH,
            pages=[
                {
                    "page_index": 0,
                    "words": [
                        {"text": "appel", "x": 0.1, "y": 0.1, "width": 0.1, "height": 0.03},
                        {"text": "fonds", "x": 0.22, "y": 0.1, "width": 0.1, "height": 0.03},
                        {"text": "appel", "x": 0.1, "y": 0.5, "width": 0.1, "height": 0.03},
                        {"text": "fonds", "x": 0.22, "y": 0.5, "width": 0.1, "height": 0.03},
                    ],
                }
            ],
        )

        first, second = find_text_traces(text_map, "appel fonds", max_candidates=2)

        self.assertEqual(first.selected_text_hash, second.selected_text_hash)
        self.assertNotEqual(first.anchor_hash, second.anchor_hash)
        self.assertNotEqual(first.sort_index, second.sort_index)

    def test_multiline_selection_keeps_detailed_rectangles_in_sidecar_row(self) -> None:
        text_map = build_text_map_from_words(
            document_ref="DOC-MULTILINE",
            document_hash=HASH,
            pages=[
                {
                    "page_index": 0,
                    "words": [
                        {"text": "appel", "x": 0.1, "y": 0.2, "width": 0.1, "height": 0.04},
                        {"text": "fonds", "x": 0.1, "y": 0.35, "width": 0.1, "height": 0.04},
                    ],
                }
            ],
        )
        candidate = find_text_traces(text_map, "appel fonds")[0]

        row = candidate_to_annotation_row(
            candidate,
            comment="Relire la selection sur deux lignes.",
            author_ref="user:cs-demo",
            created_at="2026-05-31T01:45:00Z",
            point_ref="POINT-MULTILINE-1",
            action_ref="ACT-MULTILINE-1",
            proof_ref="PROOF-MULTILINE-1",
        )

        self.assertEqual(len(row["rects"]), 2)
        self.assertEqual(row["zone"]["y"], 0.2)
        self.assertEqual(row["zone"]["height"], 0.19)

    def test_document_ref_rejects_path_or_sensitive_marker(self) -> None:
        for document_ref in (r"C:\Users\Example\demo.pdf", "DOC token=abc123", "raw/DOC-1", "DOC.private", "DOC:raw"):
            with self.subTest(document_ref=document_ref):
                with self.assertRaises(ValueError):
                    build_text_map_from_words(document_ref=document_ref, document_hash=HASH, pages=[])

    def test_annotation_comment_with_private_data_is_not_event_ready(self) -> None:
        candidate = build_zone_trace_candidate(
            document_ref="DOC-SCAN-COMMENT-1",
            document_hash=HASH,
            page_index=0,
            zone={"x": 0.2, "y": 0.3, "width": 0.25, "height": 0.1},
        )
        row = candidate_to_annotation_row(
            candidate,
            comment="Relire avec test@example.com avant partage.",
            author_ref="user:cs-demo",
            created_at="2026-05-31T01:35:00Z",
            point_ref="POINT-COMMENT-1",
            action_ref="ACT-RELIRE-COMMENT-1",
            proof_ref="PROOF-SCAN-COMMENT-1",
        )
        issues = validate_annotation(normalize_annotation(row))

        self.assertTrue(any(issue.field.endswith("comment") for issue in issues))

    def test_zone_trace_keeps_scanned_page_area_without_confirmed_text(self) -> None:
        candidate = build_zone_trace_candidate(
            document_ref="DOC-SCAN-1",
            document_hash=HASH,
            page_index=4,
            page_label="Annexe 5",
            zone={"x": 0.2, "y": 0.3, "width": 0.25, "height": 0.1},
        )

        payload = candidate_to_public_dict(candidate)
        row = candidate_to_annotation_row(
            candidate,
            comment="Zone a relire: le texte n'est pas confirme.",
            author_ref="user:cs-demo",
            created_at="2026-05-31T01:25:00Z",
            point_ref="POINT-SCAN-1",
            action_ref="ACT-RELIRE-1",
            proof_ref="PROOF-SCAN-1",
        )
        annotation = normalize_annotation(row)

        self.assertEqual(payload["text_status"], "non_confirme")
        self.assertIn("Texte non confirme", payload["selected_text_excerpt"])
        self.assertEqual(payload["coproscope_anchor"]["page"], 5)
        self.assertEqual(payload["zotero_position"]["pageIndex"], 4)
        self.assertEqual(payload["zotero_position"]["rects"][0]["width"], 0.25)
        self.assertEqual(validate_annotation(annotation), tuple())
        self.assertFalse(non_destructive_sidecar_plan(annotation)["source_write_allowed"])

    def test_zone_trace_clamps_zone_inside_page(self) -> None:
        candidate = build_zone_trace_candidate(
            document_ref="DOC-SCAN-CLAMP",
            document_hash=HASH,
            page_index=0,
            zone={"x": 0.9, "y": 0.95, "width": 0.4, "height": 0.2},
        )

        rect = candidate_to_public_dict(candidate)["zotero_position"]["rects"][0]

        self.assertEqual(rect["x"], 0.9)
        self.assertEqual(rect["width"], 0.1)
        self.assertEqual(rect["height"], 0.05)

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

    def test_extract_pdf_text_map_checks_hash_and_does_not_write_source(self) -> None:
        original_fitz = sys.modules.get("fitz")
        sys.modules["fitz"] = _fake_fitz_module()
        try:
            with TemporaryDirectory() as tmp:
                pdf_path = Path(tmp) / "demo.pdf"
                pdf_path.write_bytes(b"%PDF-1.7 demo")
                original_bytes = pdf_path.read_bytes()
                expected_hash = _file_hash(original_bytes)

                text_map = extract_pdf_text_map(pdf_path, document_ref="DOC-DEMO-HASH", document_hash=expected_hash)

                self.assertEqual(text_map.document_hash_status, DOCUMENT_HASH_MATCH)
                self.assertEqual(pdf_path.read_bytes(), original_bytes)
        finally:
            if original_fitz is None:
                sys.modules.pop("fitz", None)
            else:
                sys.modules["fitz"] = original_fitz

    def test_hash_mismatch_marks_candidate_as_review_required(self) -> None:
        original_fitz = sys.modules.get("fitz")
        sys.modules["fitz"] = _fake_fitz_module()
        try:
            with TemporaryDirectory() as tmp:
                pdf_path = Path(tmp) / "demo.pdf"
                pdf_path.write_bytes(b"%PDF-1.7 changed")
                text_map = extract_pdf_text_map(pdf_path, document_ref="DOC-DEMO-MISMATCH", document_hash=HASH)
        finally:
            if original_fitz is None:
                sys.modules.pop("fitz", None)
            else:
                sys.modules["fitz"] = original_fitz

        candidate = find_text_traces(text_map, "Appel")[0]
        payload = candidate_to_public_dict(candidate)

        self.assertEqual(text_map.document_hash_status, DOCUMENT_HASH_MISMATCH)
        self.assertEqual(candidate.text_status, TEXT_STATUS_REVIEW_REQUIRED)
        self.assertIn("fichier a change", payload["selected_text_excerpt"])


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

        def save(self, *_args, **_kwargs) -> None:
            raise AssertionError("source PDF must not be saved")

        write = save
        saveIncr = save

    return types.SimpleNamespace(open=lambda _path: Document())


def _file_hash(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


if __name__ == "__main__":
    unittest.main()
