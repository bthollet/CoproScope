from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance, read_csv, write_csv
from coproscope.modules import pdftrace_registry
from coproscope.modules.pdftrace_preannotation import (
    KIND_AMOUNT,
    KIND_DATE,
    KIND_REFERENCE,
    KIND_RESOLUTION,
    STATUS_ABSENT,
    STATUS_AMBIGUOUS,
    STATUS_ANCHORED,
    STATUS_ANCHORED_CONTEXT,
    save_preannotation_traces,
    amount_variants,
    date_variants,
    generic_targets_from_text,
    preannotate,
    preannotation_annotation_rows,
    preannotation_summary,
    reference_variants,
    targets_from_invoice_row,
)
from coproscope.modules.pdftraceops import PROOF_STATUS_CANDIDATE, build_text_map_from_words


HASH = "sha256:" + "c" * 64
CREATED_AT = "2026-06-11T10:00:00+02:00"


def _word(text: str, index: int, line_y: int = 20) -> dict[str, object]:
    left = 10 + index * 45
    return {"text": text, "x0": left, "y0": line_y, "x1": left + 40, "y1": line_y + 10}


def _invoice_map():
    page0 = [
        _word("Facture", 0),
        _word("F-2026-118", 1),
        _word("du", 2),
        _word("15/01/2026", 3),
        _word("Montant", 0, 40),
        _word("987,65", 1, 40),
        _word("Total", 2, 40),
        _word("TTC", 3, 40),
        _word("1", 0, 60),
        _word("234,56", 1, 60),
    ]
    page1 = [
        _word("Rappel", 0),
        _word("acompte", 1),
        _word("1", 2),
        _word("234,56", 3),
        _word("Resolution", 0, 40),
        _word("n°12", 1, 40),
        _word("adoptee", 2, 40),
    ]
    return build_text_map_from_words(
        document_ref="DOC-TEST-PREANNOT",
        document_hash=HASH,
        pages=[
            {"page_index": 0, "width": 200, "height": 100, "words": page0},
            {"page_index": 1, "width": 200, "height": 100, "words": page1},
        ],
    )


class VariantTests(unittest.TestCase):
    def test_amount_variants_cover_french_formats(self) -> None:
        variants = amount_variants("1234.56")
        self.assertIn("1 234,56", variants)
        self.assertIn("1234,56", variants)
        self.assertIn("1.234,56", variants)

    def test_amount_variants_parse_french_input(self) -> None:
        variants = amount_variants("1 234,56")
        self.assertIn("1234,56", variants)
        self.assertIn("1234.56", variants)

    def test_amount_variants_integer_forms_for_round_amounts(self) -> None:
        variants = amount_variants("12,00")
        self.assertIn("12", variants)

    def test_date_variants_include_french_long_form(self) -> None:
        variants = date_variants("2026-03-05")
        self.assertIn("05/03/2026", variants)
        self.assertIn("5 mars 2026", variants)

    def test_reference_variants_split_and_collapse(self) -> None:
        variants = reference_variants("F-2026-118")
        self.assertIn("F 2026 118", variants)
        self.assertIn("F2026118", variants)


class TargetTests(unittest.TestCase):
    def test_targets_from_invoice_row_skips_empty_fields(self) -> None:
        targets = targets_from_invoice_row(
            {"ttc": "987.65", "numero_facture": "F-2026-118", "date_facture": "2026-01-15", "ht": ""}
        )
        fields = {target.field for target in targets}
        self.assertEqual(fields, {"ttc", "numero_facture", "date_facture"})

    def test_generic_targets_dedupe_and_classify(self) -> None:
        text = (
            "Total TTC 1 234,56 € paye le 15/01/2026, rappel 1 234,56 EUR. "
            "Facture n° F-2026-118. La résolution n° 12 est adoptée."
        )
        targets = generic_targets_from_text(text)
        kinds = [target.kind for target in targets]
        self.assertEqual(kinds.count(KIND_AMOUNT), 1)
        self.assertEqual(kinds.count(KIND_DATE), 1)
        self.assertEqual(kinds.count(KIND_RESOLUTION), 1)
        self.assertEqual(kinds.count(KIND_REFERENCE), 1)

    def test_generic_targets_respect_cap(self) -> None:
        text = " ".join(f"{value},10" for value in range(100, 130))
        targets = generic_targets_from_text(text, max_per_kind=5)
        self.assertEqual(len([t for t in targets if t.kind == KIND_AMOUNT]), 5)


class FrenchLayoutTests(unittest.TestCase):
    def test_no_cents_amount_with_currency_is_detected(self) -> None:
        targets = generic_targets_from_text("Travaux votés pour 12 000 € le 3 mars 2026.")
        kinds = {target.kind: target.value for target in targets}
        self.assertIn(KIND_AMOUNT, kinds)
        self.assertIn(KIND_DATE, kinds)
        self.assertEqual(kinds[KIND_DATE], "3 mars 2026")

    def test_cents_amount_does_not_spawn_currency_tail_target(self) -> None:
        targets = generic_targets_from_text("Total 1 234,56 €")
        amounts = [target for target in targets if target.kind == KIND_AMOUNT]
        self.assertEqual(len(amounts), 1)

    def test_round_amount_variants_include_plain_integers(self) -> None:
        variants = amount_variants("12 000 €")
        self.assertIn("12 000", variants)
        self.assertIn("12000", variants)

    def test_glued_currency_symbol_still_anchors(self) -> None:
        text_map = build_text_map_from_words(
            document_ref="DOC-TEST-GLUED",
            document_hash=HASH,
            pages=[
                {
                    "page_index": 0,
                    "width": 200,
                    "height": 100,
                    "words": [_word("Total", 0), _word("1234,56€", 1)],
                }
            ],
        )
        results = preannotate(text_map, targets_from_invoice_row({"ttc": "1234.56"}))
        self.assertEqual(results[0].status, STATUS_ANCHORED)

    def test_long_french_date_anchors_as_literal(self) -> None:
        text_map = build_text_map_from_words(
            document_ref="DOC-TEST-DATELONGUE",
            document_hash=HASH,
            pages=[
                {
                    "page_index": 0,
                    "width": 200,
                    "height": 100,
                    "words": [_word("le", 0), _word("3", 1), _word("mars", 2), _word("2026", 3)],
                }
            ],
        )
        targets = generic_targets_from_text("AG du 3 mars 2026")
        results = preannotate(text_map, targets)
        by_kind = {result.target.kind: result for result in results}
        self.assertEqual(by_kind[KIND_DATE].status, STATUS_ANCHORED)


class PreannotateTests(unittest.TestCase):
    def test_amount_anchored_once(self) -> None:
        results = preannotate(_invoice_map(), targets_from_invoice_row({"ttc": "987.65"}))
        self.assertEqual(results[0].status, STATUS_ANCHORED)
        self.assertEqual(results[0].occurrences, 1)
        self.assertEqual(results[0].candidates[0].page_index, 0)

    def test_repeated_amount_is_ambiguous(self) -> None:
        results = preannotate(_invoice_map(), targets_from_invoice_row({"ttc": "1234.56"}))
        self.assertEqual(results[0].status, STATUS_AMBIGUOUS)
        self.assertEqual(results[0].occurrences, 2)

    def test_missing_amount_is_absent(self) -> None:
        results = preannotate(_invoice_map(), targets_from_invoice_row({"ttc": "55.55"}))
        self.assertEqual(results[0].status, STATUS_ABSENT)
        self.assertEqual(results[0].candidates, tuple())

    def test_date_and_reference_anchor(self) -> None:
        targets = targets_from_invoice_row(
            {"date_facture": "2026-01-15", "numero_facture": "F-2026-118"}
        )
        results = {result.target.field: result for result in preannotate(_invoice_map(), targets)}
        self.assertEqual(results["date_facture"].status, STATUS_ANCHORED)
        self.assertEqual(results["numero_facture"].status, STATUS_ANCHORED)

    def test_partial_word_overlap_is_not_an_exact_anchor(self) -> None:
        text_map = build_text_map_from_words(
            document_ref="DOC-TEST-OVERLAP",
            document_hash=HASH,
            pages=[
                {
                    "page_index": 0,
                    "width": 200,
                    "height": 100,
                    "words": [_word("11", 0), _word("234,56", 1)],
                }
            ],
        )
        results = preannotate(text_map, targets_from_invoice_row({"ttc": "1234.56"}))
        self.assertEqual(results[0].status, STATUS_ABSENT)

    def test_summary_counts_by_status_and_kind(self) -> None:
        targets = targets_from_invoice_row({"ttc": "987.65", "ht": "55.55", "tva": "1234.56"})
        summary = preannotation_summary(preannotate(_invoice_map(), targets))
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary[STATUS_ANCHORED], 1)
        self.assertEqual(summary[STATUS_AMBIGUOUS], 1)
        self.assertEqual(summary[STATUS_ABSENT], 1)
        self.assertEqual(summary["par_type"][KIND_AMOUNT][STATUS_ANCHORED], 1)


class AnnotationRowTests(unittest.TestCase):
    def test_rows_are_value_free_candidates(self) -> None:
        results = preannotate(_invoice_map(), targets_from_invoice_row({"ttc": "987.65"}))
        rows = preannotation_annotation_rows(results, created_at=CREATED_AT)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["proof_status"], PROOF_STATUS_CANDIDATE)
        self.assertEqual(row["preannotation_status"], STATUS_ANCHORED)
        self.assertIn("champ ttc", str(row["comment"]))
        self.assertNotIn("987", str(row["comment"]))

    def test_ambiguous_rows_skipped_unless_requested(self) -> None:
        results = preannotate(_invoice_map(), targets_from_invoice_row({"ttc": "1234.56"}))
        self.assertEqual(preannotation_annotation_rows(results, created_at=CREATED_AT), [])
        rows = preannotation_annotation_rows(results, created_at=CREATED_AT, include_ambiguous=True)
        self.assertEqual(len(rows), 1)
        self.assertIn("2 occurrences a desambiguiser", str(rows[0]["comment"]))


class HexDocRefPhoneFalsePositiveTests(unittest.TestCase):
    def test_hex_doc_ref_with_long_digit_run_is_accepted(self) -> None:
        from coproscope.modules.pdftrace_contracts import validate_document_identity

        validate_document_identity("DOC-3504975596D8", HASH)
        validate_document_identity("DOC-0B1940145729", HASH)

    def test_letter_prefixed_decimal_ref_is_accepted(self) -> None:
        from coproscope.modules.pdftrace_contracts import validate_document_identity

        validate_document_identity("DOC-197441098683", HASH)

    def test_pure_digit_ref_stays_rejected_as_phone_like(self) -> None:
        from coproscope.modules.pdftrace_contracts import validate_document_identity

        with self.assertRaises(ValueError):
            validate_document_identity("0612345678", HASH)

    def test_real_phone_numbers_still_detected(self) -> None:
        from coproscope.modules.pdftrace_contracts import contains_sensitive_text

        self.assertTrue(contains_sensitive_text("appelez le 06 12 34 56 78"))
        self.assertTrue(contains_sensitive_text("tel +33612345678 merci"))
        self.assertFalse(contains_sensitive_text("DOC-626415808A9F"))


class LineDisambiguationTests(unittest.TestCase):
    def _two_line_map(self, line_a: tuple[str, ...], line_b: tuple[str, ...]):
        words = [_word(text, index, 20) for index, text in enumerate(line_a)]
        words += [_word(text, index, 60) for index, text in enumerate(line_b)]
        return build_text_map_from_words(
            document_ref="DOC-TEST-LIGNES",
            document_hash=HASH,
            pages=[{"page_index": 0, "width": 200, "height": 100, "words": words}],
        )

    def test_invoice_context_disambiguates_repeated_amount(self) -> None:
        text_map = self._two_line_map(("Total", "TTC", "1", "234,56"), ("Acompte", "1", "234,56"))
        results = preannotate(text_map, targets_from_invoice_row({"ttc": "1234.56"}))
        result = results[0]
        self.assertEqual(result.status, STATUS_ANCHORED_CONTEXT)
        self.assertEqual(result.occurrences, 2)
        self.assertEqual(len(result.candidates), 1)
        self.assertAlmostEqual(result.candidates[0].rects[0].y, 0.2)

    def test_without_matching_labels_stays_ambiguous(self) -> None:
        text_map = self._two_line_map(("Solde", "initial", "1", "234,56"), ("Acompte", "1", "234,56"))
        results = preannotate(text_map, targets_from_invoice_row({"ttc": "1234.56"}))
        self.assertEqual(results[0].status, STATUS_AMBIGUOUS)
        self.assertEqual(len(results[0].candidates), 2)

    def test_generic_target_context_picks_first_mention_line(self) -> None:
        text = "Honoraires gestion courante 444,44 EUR puis acompte travaux 444,44 EUR"
        amount = next(t for t in generic_targets_from_text(text) if t.kind == KIND_AMOUNT)
        self.assertIn("honoraires", amount.context)
        text_map = self._two_line_map(("Honoraires", "gestion", "444,44"), ("Acompte", "travaux", "444,44"))
        results = preannotate(text_map, (amount,))
        self.assertEqual(results[0].status, STATUS_ANCHORED_CONTEXT)
        self.assertAlmostEqual(results[0].candidates[0].rects[0].y, 0.2)


class RegisterSaveTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _register_document(self, doc_id: str) -> None:
        fields, rows = read_csv(self.instance.register("documents"))
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": doc_id,
                "file_name": f"{doc_id}.pdf",
                "extension": "pdf",
                "sha256": "c" * 64,
                "document_type": "Facture",
                "page_count": "1",
                "text_char_count": "120",
            }
        )
        write_csv(self.instance.register("documents"), fields, rows)

    def test_save_appends_dedupes_and_feeds_queue(self) -> None:
        doc_id = "DOC-PREANNOT-1"
        self._register_document(doc_id)
        text_map = build_text_map_from_words(
            document_ref=doc_id,
            document_hash=HASH,
            pages=[
                {
                    "page_index": 0,
                    "width": 200,
                    "height": 100,
                    "words": [_word("Total", 0), _word("TTC", 1), _word("987,65", 2)],
                }
            ],
        )
        results = preannotate(text_map, targets_from_invoice_row({"ttc": "987.65"}))
        outcome = save_preannotation_traces(self.instance, results, created_at=CREATED_AT)
        self.assertEqual(outcome["ecrites"], 1)

        again = save_preannotation_traces(self.instance, results, created_at=CREATED_AT)
        self.assertEqual(again["ecrites"], 0)
        self.assertEqual(again["deja_presentes"], 1)

        register_rows = pdftrace_registry.read_trace_rows(self.instance)
        self.assertEqual(len(register_rows), 1)
        row = register_rows[0]
        self.assertEqual(row["source_engine"], "moteur_preannotation")
        self.assertEqual(row["proof_status"], PROOF_STATUS_CANDIDATE)
        self.assertIn("champ ttc", row["comment"])
        self.assertNotIn("987", row["comment"])

        queue = pdftrace_registry.public_trace_reprise_queue(self.instance)
        items = queue["rows"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["document_ref"], doc_id)
        self.assertTrue(items[0]["resume_path"].startswith(f"/documents/{doc_id}?trace_id="))

    def test_tiny_anchor_zone_is_padded_to_stay_resumable(self) -> None:
        doc_id = "DOC-PREANNOT-2"
        self._register_document(doc_id)
        text_map = build_text_map_from_words(
            document_ref=doc_id,
            document_hash=HASH,
            pages=[
                {
                    "page_index": 0,
                    "width": 200,
                    "height": 100,
                    "words": [
                        {"text": "987,65", "x0": 10, "y0": 20, "x1": 50, "y1": 20.8},
                    ],
                }
            ],
        )
        results = preannotate(text_map, targets_from_invoice_row({"ttc": "987.65"}))
        outcome = save_preannotation_traces(self.instance, results, created_at=CREATED_AT)
        self.assertEqual(outcome["ecrites"], 1)
        row = pdftrace_registry.read_trace_rows(self.instance)[-1]
        self.assertGreaterEqual(float(row["zone_height"]), 0.01)
        queue = pdftrace_registry.public_trace_reprise_queue(self.instance)
        refs = [item["document_ref"] for item in queue["rows"]]
        self.assertIn(doc_id, refs)


if __name__ == "__main__":
    unittest.main()
