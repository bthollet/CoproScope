from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance, read_csv
from coproscope.modules import docai, docuscope


class DocAITests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.example_root = Path(self.tempdir.name) / "synthetic_copro"
        shutil.copytree(source_example, self.example_root)
        self.instance = load_instance(str(self.example_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _row_for_file(self, file_name: str) -> dict[str, str]:
        _, rows = read_csv(self.instance.register("documents"))
        for row in rows:
            if row.get("file_name") == file_name:
                return row
        raise AssertionError(f"Missing row for {file_name}")

    def test_sidecar_ocr_lifts_scan_to_ocr_done(self) -> None:
        scan = self.example_root / "raw" / "scan.png"
        scan.write_bytes(b"synthetic image placeholder")
        scan.with_name("scan.png.ocr.txt").write_text(
            "SYNTHESE OCR\nFacture n FAC-001\nTotal TTC 120,00\n",
            encoding="utf-8",
        )

        run = RunContext(self.instance, "docai test")
        docuscope.inventory(self.instance, run)
        docuscope.extract_text(self.instance, run)

        before = self._row_for_file("scan.png")
        self.assertEqual(before.get("status_ocr"), "OCR_REQUIRED")

        docai.run_ocr(self.instance, run, doc_id=before["doc_id"], mode="local-basic", engine="sidecar-ocr")
        after = self._row_for_file("scan.png")

        self.assertEqual(after.get("status_ocr"), "OCR_DONE")
        self.assertEqual(after.get("ocr_engine"), "sidecar_ocr")
        self.assertIn("P2_LOCAL_OCR_SIDECAR_OCR", after.get("extraction_level", ""))
        self.assertTrue((self.example_root / after["text_path"]).exists())

    def test_docling_and_layout_enrichment_write_artifacts_without_heavy_dependencies(self) -> None:
        run = RunContext(self.instance, "docai enrich test")
        docuscope.inventory(self.instance, run)
        docuscope.extract_text(self.instance, run)
        row = self._row_for_file("2026-04-29_convocation_ag.txt")

        docai.enrich(self.instance, run, backend="docling", doc_id=row["doc_id"], mode="local-basic")
        docai.enrich(self.instance, run, backend="layoutlmv3", doc_id=row["doc_id"], mode="local-heavy")
        enriched = self._row_for_file("2026-04-29_convocation_ag.txt")

        self.assertTrue((self.example_root / enriched["docling_path"]).exists())
        self.assertTrue((self.example_root / enriched["layout_path"]).exists())
        self.assertIn("P1_DOCLING_STRUCTURE", enriched.get("extraction_level", ""))
        self.assertIn("P3_LAYOUT_LAYOUTLMV3", enriched.get("extraction_level", ""))

    def test_docai_status_reports_optional_backends(self) -> None:
        status = docai.docai_status(self.instance, mode="local-basic")
        self.assertEqual(status["mode"], "local_basic")
        self.assertEqual(status["privacy"], "local_only")
        self.assertIn("docling", status["modules"])


if __name__ == "__main__":
    unittest.main()
