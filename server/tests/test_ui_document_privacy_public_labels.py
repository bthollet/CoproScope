from __future__ import annotations

import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, load_instance, read_csv, write_csv
from coproscope.core.privacy import SCREENING_FIELDS
from coproscope.modules import docuscope
from coproscope.web.app import create_app
from coproscope.web.document_viewer import build_document_detail


PRIVATE_MARKERS = (
    r"C:\Users",
    "100_Collecte_RAW",
    "raw/source.pdf",
    "original_path",
)


class DocumentPrivacyPublicLabelTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError as exc:
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        return TestClient(create_app(self.instance, 2025))

    def _seed_private_document(self) -> None:
        fields, rows = read_csv(self.instance.register("documents"))
        fields = fields or list(DEFAULT_DOCUMENT_FIELDS)
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": "DOC-PUBLIC-LABEL",
                "file_name": r"C:\Users\Example\100_Collecte_RAW\source.pdf",
                "extension": "pdf",
                "original_path": r"C:\Users\Example\100_Collecte_RAW\source.pdf",
                "source_zone": "100_Collecte_RAW",
                "document_type": "PV_AG",
                "raw_max_college": "C8_Restreint_Critique",
                "derivative_max_college": "C2_Coproprietaires",
            }
        )
        write_csv(self.instance.register("documents"), fields, rows)

        reports_dir = self.instance.artifact("reports_dir")
        reports_dir.mkdir(parents=True, exist_ok=True)
        (reports_dir / "rapport_completude_documentaire.md").write_text(
            r"Piece locale: C:\Users\Example\100_Collecte_RAW\source.pdf",
            encoding="utf-8",
        )
        write_csv(
            reports_dir / "matrice_completude_documentaire.csv",
            docuscope.COMPLETENESS_FIELDS,
            [
                {
                    "proof_id": "PRV-PRIVATE",
                    "lot": "ag",
                    "expected_label": "PV d'AG",
                    "document_type": "PV_AG",
                    "status": "A_CLASSER",
                    "criticality": "P1",
                    "freshness_months": "",
                    "matched_doc_ids": "",
                    "evidence_paths": "raw/source.pdf",
                    "newest_date": "",
                    "reason": "Classer la piece sans exposer son chemin local.",
                    "action": "Verifier la fiche document.",
                }
            ],
        )

        privacy_dir = self.instance.root("staging") / "privacy_dir"
        privacy_dir.mkdir(parents=True, exist_ok=True)
        review_fields = [
            *SCREENING_FIELDS,
            "privacy_review_status",
            "review_status_recommendation",
            "review_next_step",
            "review_justification_required",
            "publication_blocker",
        ]
        write_csv(
            privacy_dir / "registre_screening_confidentialite.csv",
            review_fields,
            [
                {
                    **{field: "" for field in review_fields},
                    "doc_id": "DOC-PUBLIC-LABEL",
                    "sha256": "a" * 64,
                    "original_path": r"C:\Users\Example\100_Collecte_RAW\source.pdf",
                    "file_name": r"C:\Users\Example\100_Collecte_RAW\source.pdf",
                    "extension": ".pdf",
                    "source_zone": "100_Collecte_RAW",
                    "raw_max_college": "C8_Restreint_Critique",
                    "derivative_max_college": "C2_Coproprietaires",
                    "publication_form": "aggregation_required",
                    "required_transformations": "Synthese seulement",
                    "review_required": "YES",
                    "remediation_priority": "P1",
                    "privacy_review_status": "A_ARBITRER",
                    "review_status_recommendation": "DIFFUSABLE_APRES_AGREGATION",
                    "review_next_step": "Produire une synthese sans liste nominative.",
                    "review_justification_required": "YES",
                }
            ],
        )

    def assertNoPrivateMarkers(self, text: str) -> None:
        for marker in PRIVATE_MARKERS:
            self.assertNotIn(marker, text)

    def test_documents_and_privacy_routes_hide_local_paths(self) -> None:
        self._seed_private_document()
        client = self._client()

        documents = unescape(client.get("/documents").text)
        privacy = unescape(client.get("/confidentialite").text)

        self.assertIn("source.pdf", documents)
        self.assertIn("DOC-PUBLIC-LABEL", documents)
        self.assertIn("Rapport disponible localement", documents)
        self.assertIn("source.pdf", privacy)
        self.assertIn("DOC-PUBLIC-LABEL", privacy)
        self.assertNoPrivateMarkers(documents)
        self.assertNoPrivateMarkers(privacy)

    def test_document_detail_uses_best_row_when_doc_id_is_duplicated(self) -> None:
        fields, rows = read_csv(self.instance.register("documents"))
        fields = fields or list(DEFAULT_DOCUMENT_FIELDS)
        rows.extend(
            [
                {
                    **{field: "" for field in fields},
                    "doc_id": "DOC-DUPLICATE-AG",
                    "file_name": "ag_duplicate.pdf",
                    "document_type": "Convocation_AG",
                },
                {
                    **{field: "" for field in fields},
                    "doc_id": "DOC-DUPLICATE-AG",
                    "file_name": "ag_duplicate.pdf",
                    "document_type": "PV_AG",
                    "suspected_date": "2024-07-03",
                    "status_ocr": "TEXT_EXTRACTED",
                },
            ]
        )
        write_csv(self.instance.register("documents"), fields, rows)

        detail = build_document_detail(self.instance, "DOC-DUPLICATE-AG")

        self.assertEqual(detail["doc"]["document_type"], "PV_AG")
        self.assertEqual(detail["doc"]["suspected_date"], "2024-07-03")


if __name__ == "__main__":
    unittest.main()
