from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import load_instance, write_csv
from coproscope.modules.factureops import INVOICE_ANOMALY_FIELDS, INVOICE_EVIDENCE_FIELDS
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app
from coproscope.web.factures_review_view import build_factures_review_view


REQUIRED_LABELS = (
    "Factures a revoir",
    "A traiter",
    "A controler",
    "Incertaines",
    "Anomalies critiques",
    "Priorite haute",
    "A completer",
    "A verifier",
    "File factures, anomalies et action suivante",
    "Montant TTC absent",
    "Doublon potentiel",
    "Action suivante",
    "Ouvrir le document protege",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "C:\\",
    "file://",
    "/Users/",
    "/home/",
    "source_path",
    "raw_path",
    "pdf_path",
    "text_path",
    "source_file",
    "document_path",
    "evidence",
    "ocr_text",
    "excerpt",
    "secretValue",
    "secret_facture.pdf",
    "restricted",
    "private",
    "raw/",
    "raw\\",
)


class UiFacturesReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)
        self.year_dir = self.instance.artifact("accounting_dir") / "2025"
        self.year_dir.mkdir(parents=True, exist_ok=True)
        (self.year_dir / "invoice_evidence_2025.csv").unlink(missing_ok=True)
        (self.year_dir / "invoice_anomalies_2025.csv").unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self, access_token: str | None = None):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")
        return TestClient(create_app(self.instance, 2025, access_token=access_token))

    def test_missing_invoice_exports_renders_empty_state(self) -> None:
        response = self._client(access_token="local-secret").get("/comptes/factures-a-revoir?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Aucune table facture locale n'est disponible", text)
        self.assertIn("Factures a revoir", text)

    def test_route_is_token_guarded_and_novice_readable_without_private_leaks(self) -> None:
        self._seed_invoice_exports()
        client = self._client(access_token="local-secret")

        forbidden = client.get("/comptes/factures-a-revoir")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Factures a revoir", forbidden.text)

        response = client.get("/comptes/factures-a-revoir?token=local-secret")
        text = unescape(response.text)
        visible = _visible_text(text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn('href="/comptes?token=local-secret"', response.text)
        self.assertIn('href="/documents/DOC-INV-001?source=factures&amp;token=local-secret"', response.text)
        self.assertIn("Lien document masque", text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)
            self.assertNotIn(marker, response.text)
        self.assertNotIn("alert(1)", response.text)
        self.assertNotIn("&lt;script", response.text.lower())

    def test_filters_and_view_model_keep_only_public_fields(self) -> None:
        self._seed_invoice_exports()
        view = build_factures_review_view(self.instance, 2025, active_filter="doublons")
        rendered_model = str(view)

        self.assertEqual(view["active_filter"], "doublons")
        self.assertEqual(len(view["rows"]), 1)
        self.assertEqual(view["rows"][0]["supplier"], "Fournisseur fictif")
        self.assertEqual(view["rows"][0]["priority_label"], "Priorite haute")
        self.assertIn("Doublon potentiel", view["rows"][0]["anomalies"])
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, rendered_model)

    def _seed_invoice_exports(self) -> None:
        write_csv(
            self.year_dir / "invoice_evidence_2025.csv",
            INVOICE_EVIDENCE_FIELDS,
            [
                _invoice_row(
                    doc_id="DOC-INV-001",
                    fournisseur="Fournisseur fictif",
                    numero_facture="FAC-001",
                    date_facture="2025-03-10",
                    ttc="",
                    compte_propose="615000",
                    famille_charge="entretien_maintenance",
                    statut_controle="A_CONTROLER",
                    anomalies="MONTANT_TTC_ABSENT|DOUBLON_POTENTIEL",
                ),
                _invoice_row(
                    doc_id=r"C:\\Users\\demo\\raw\\secretValue.pdf",
                    source_path=r"C:\\Users\\demo\\restricted\\secretValue.pdf",
                    file_name="secret_facture.pdf",
                    fournisseur=r"Prestataire <script>alert(1)</script> C:\\Users\\demo\\private",
                    numero_facture="secret_facture.pdf",
                    date_facture="file://private/date.txt",
                    ttc="file://private/100.pdf",
                    compte_propose=r"615 C:\\Users\\demo\\raw",
                    famille_charge="private maintenance",
                    statut_controle="INCERTAIN",
                    anomalies="FOURNISSEUR_ABSENT|file://private/source.pdf",
                ),
                _invoice_row(
                    doc_id="DOC-INV-OK",
                    fournisseur="Autre fournisseur fictif",
                    numero_facture="FAC-OK",
                    date_facture="2025-04-01",
                    ttc="42.00",
                    compte_propose="601000",
                    famille_charge="energie_eau",
                    statut_controle="PROBABLE",
                ),
            ],
        )
        write_csv(
            self.year_dir / "invoice_anomalies_2025.csv",
            INVOICE_ANOMALY_FIELDS
            + ["raw_path", "pdf_path", "text_path", "ocr_text", "excerpt", "source_file", "document_path"],
            [
                _anomaly_row(
                    doc_id="DOC-INV-001",
                    severity="P1",
                    anomaly="MONTANT_TTC_ABSENT",
                    evidence=r"C:\\Users\\demo\\raw\\secretValue.txt",
                    raw_path=r"C:\\Users\\demo\\raw\\secretValue.pdf",
                    pdf_path="file://private/secretValue.pdf",
                    ocr_text="secretValue OCR brut",
                    excerpt="secretValue extrait",
                ),
                _anomaly_row(doc_id="DOC-INV-001", severity="P1", anomaly="DOUBLON_POTENTIEL"),
            ],
        )


def _invoice_row(**updates: str) -> dict[str, str]:
    row = {field: "" for field in INVOICE_EVIDENCE_FIELDS}
    row.update({key: str(value) for key, value in updates.items()})
    row["exercice"] = row.get("exercice") or "2025"
    return row


def _anomaly_row(**updates: str) -> dict[str, str]:
    row = {field: "" for field in INVOICE_ANOMALY_FIELDS}
    row.update({key: str(value) for key, value in updates.items()})
    row["exercice"] = row.get("exercice") or "2025"
    return row


def _visible_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return " ".join(without_tags.split())


if __name__ == "__main__":
    unittest.main()
