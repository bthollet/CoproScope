from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, load_instance, relative_to, write_csv
from coproscope.modules.factureops import INVOICE_EVIDENCE_FIELDS
from coproscope.web.document_viewer import build_document_detail


class UiDocumentViewerInvoiceContextTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_invoice_evidence_date_replaces_legal_clause_date_on_detail(self) -> None:
        doc_id = "DOC-INVOICE-DATE"
        pdf_path = self.instance_root / "200_INBOX" / "facture.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n% invoice\n")
        row = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        row.update(
            {
                "doc_id": doc_id,
                "file_name": "facture.pdf",
                "extension": "pdf",
                "original_path": relative_to(self.instance_root, pdf_path),
                "lot": "Factures_Fournisseurs",
                "document_type": "Facture",
                "suspected_date": "2012-11",
            }
        )
        write_csv(self.instance.register("documents"), list(DEFAULT_DOCUMENT_FIELDS), [row])
        evidence_dir = self.instance.artifact("accounting_dir") / "2025"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence = {field: "" for field in INVOICE_EVIDENCE_FIELDS}
        evidence.update({"doc_id": doc_id, "date_facture": "2025-02-05"})
        write_csv(evidence_dir / "invoice_evidence_2025.csv", INVOICE_EVIDENCE_FIELDS, [evidence])

        detail = build_document_detail(self.instance, doc_id)

        self.assertEqual(detail["doc"]["suspected_date"], "2025-02-05")
        self.assertIn("2025-02-05", detail["evidence"]["chain"][1]["value"])


if __name__ == "__main__":
    unittest.main()
