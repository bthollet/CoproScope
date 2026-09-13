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
    "Liste factures, anomalies et action suivante",
    "Montant TTC absent",
    "Lecture locale insuffisante",
    "Doublon potentiel",
    "Action suivante",
    "Ouvrir le document protege",
    "Liste de travail locale",
    "A verifier en premier",
    "Voir les factures a verifier",
    "Montant et date",
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
    "resultat_id",
    "sources_utilisees",
    "resultat_premier",
    "relancer OCR",
    "Table derivee locale",
    "Total candidates",
    "Statut machine prioritaire",
    "restricted",
    "private",
    "raw/",
    "raw\\",
    "NATIVE_TEXT",
    "=====",
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
        self.assertIn('aria-current="page">Toutes</a>', response.text)
        self.assertIn('href="/documents/DOC-INV-001?source=factures&amp;token=local-secret"', response.text)
        self.assertNotIn('<a class="cs-comptes-kpi', response.text)
        self.assertNotIn('<div class="cs-comptes-kpi', response.text)
        self.assertEqual(response.text.count('<div class="cs-summary-chip'), 4)
        self.assertNotIn("Factures reperees", text)
        self.assertNotIn("Probables", text)
        self.assertIn("Lien document masque", text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)
        self.assertNotIn("200_INBOX", text)
        self.assertNotIn("Facture_2025030513520296", text)
        self.assertIn("refaire la lecture automatique du document", text)
        self.assertNotIn("relancer OCR", text)
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
        self.assertEqual(view["rows"][0]["blocking_alert"], "Lecture locale insuffisante")
        self.assertIn("avant conclusion", view["rows"][0]["next_action"])
        priority_view = build_factures_review_view(self.instance, 2025, active_filter="priorite-haute")
        self.assertEqual([row["doc_id"] for row in priority_view["rows"]], ["DOC-INV-001"])
        summary = {item["label"]: item["value"] for item in build_factures_review_view(self.instance, 2025)["summary"]}
        self.assertEqual(summary["Anomalies critiques"], "1")
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, rendered_model)

    def test_filter_active_state_and_singular_labels_are_readable(self) -> None:
        write_csv(
            self.year_dir / "invoice_evidence_2025.csv",
            INVOICE_EVIDENCE_FIELDS,
            [
                _invoice_row(
                    doc_id="DOC-HORS-001",
                    fournisseur="Fournisseur exercice",
                    numero_facture="EX-001",
                    date_facture="2024-12-31",
                    ttc="120.00",
                    compte_propose="615000",
                    famille_charge="entretien_maintenance",
                    statut_controle="INCERTAIN",
                    anomalies="FACTURE_HORS_EXERCICE",
                ),
            ],
        )
        client = self._client(access_token="local-secret")

        response = client.get("/comptes/factures-a-revoir?filtre=hors-exercice&token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn('aria-current="page">Hors exercice</a>', response.text)
        self.assertIn("1 facture affichee sur 1 facture a revoir", text)
        self.assertIn("1 ligne", text)
        self.assertNotIn("1 factures", text)
        self.assertNotIn("1 lignes", text)

    def test_supplier_contact_details_are_not_rendered(self) -> None:
        write_csv(
            self.year_dir / "invoice_evidence_2025.csv",
            INVOICE_EVIDENCE_FIELDS,
            [
                _invoice_row(
                    doc_id="DOC-CONTACT-001",
                    fournisseur=(
                        "Entretien exemple 12345678900330611223344 53 Avenue Fictive 13000 Ville - "
                        "Telephone : (0033) 06.11.22.33.44 - Courriel : contact@example.test"
                    ),
                    numero_facture="EV-001",
                    date_facture="2025-04-24",
                    ttc="1340.00",
                    compte_propose="615000",
                    famille_charge="entretien_maintenance",
                    statut_controle="INCERTAIN",
                    anomalies="SIREN_SIRET_ABSENT",
                ),
            ],
        )
        client = self._client(access_token="local-secret")

        response = client.get("/comptes/factures-a-revoir?token=local-secret")
        text = unescape(response.text)
        visible = _visible_text(text)
        view = build_factures_review_view(self.instance, 2025)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(view["rows"][0]["supplier"], "Entretien exemple")
        self.assertIn("Entretien exemple", text)
        for marker in ("123456", "0033", "06.11", "contact@example.test", "Avenue Fictive", "Telephone", "Courriel"):
            self.assertNotIn(marker, visible)
            self.assertNotIn(marker, response.text)

    def test_public_invoice_fields_mask_private_details(self) -> None:
        write_csv(
            self.year_dir / "invoice_evidence_2025.csv",
            INVOICE_EVIDENCE_FIELDS,
            [
                _invoice_row(
                    doc_id="contact@example.test",
                    fournisseur="Prestataire demo 12 rue Locale 13000 Ville",
                    numero_facture=(
                        "SIRET 123 456 789 00033 tel 06 11 22 33 44 "
                        "IBAN FR7630006000011234567890189"
                    ),
                    date_facture="2025-04-24 53 Avenue Fictive 13000 Ville",
                    ttc="1340.00",
                    compte_propose=r"615000 C:\\Users\\demo\\raw\\piece.pdf",
                    famille_charge="maintenance 98765432100012 raw/private",
                    statut_controle="INCERTAIN",
                    anomalies="SIREN_SIRET_ABSENT|contact@example.test|12 rue cachee",
                ),
            ],
        )
        client = self._client(access_token="local-secret")

        response = client.get("/comptes/factures-a-revoir?token=local-secret")
        text = unescape(response.text)
        visible = _visible_text(text)
        view = build_factures_review_view(self.instance, 2025)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(view["rows"][0]["supplier"], "Prestataire demo")
        self.assertEqual(view["rows"][0]["href"], "")
        self.assertIn("Lien document masque", text)
        for marker in (
            "contact@example.test",
            "contact-example",
            "06 11",
            "FR763",
            "123 456",
            "987654",
            "rue Locale",
            "rue cachee",
            "Avenue Fictive",
            "raw/private",
            "C:\\",
        ):
            self.assertNotIn(marker, visible)
            self.assertNotIn(marker, response.text)

    def test_internal_table_headers_and_actor_initials_are_not_rendered(self) -> None:
        write_csv(
            self.year_dir / "invoice_evidence_2025.csv",
            INVOICE_EVIDENCE_FIELDS,
            [
                _invoice_row(
                    doc_id="JR",
                    fournisseur='"resultat_id","acteur","controle","sources_utilisees","resultat_premier"',
                    numero_facture="JR",
                    date_facture="2025-11-24",
                    ttc="IBAN FR7630006000011234567890189",
                    compte_propose="606100",
                    famille_charge="energie_eau",
                    statut_controle="A_CONTROLER",
                    anomalies="MONTANT_TTC_ABSENT",
                ),
            ],
        )
        client = self._client(access_token="local-secret")

        response = client.get("/comptes/factures-a-revoir?token=local-secret")
        text = unescape(response.text)
        visible = _visible_text(text)
        view = build_factures_review_view(self.instance, 2025)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(view["rows"][0]["id"], "facture-a-identifier")
        self.assertEqual(view["rows"][0]["doc_id"], "")
        self.assertEqual(view["rows"][0]["href"], "")
        self.assertEqual(view["rows"][0]["supplier"], "Fournisseur a identifier")
        self.assertEqual(view["rows"][0]["invoice_number"], "Reference a identifier")
        self.assertEqual(view["rows"][0]["amount"], "Montant a verifier")
        self.assertIn("refaire la lecture automatique du document", text)
        for marker in ("resultat_id", "sources_utilisees", "resultat_premier", '"acteur"', ">JR<", "FR763", "relancer OCR"):
            self.assertNotIn(marker, visible)
            self.assertNotIn(marker, response.text)

    def test_anomalies_stay_linked_when_public_doc_id_is_masked(self) -> None:
        write_csv(
            self.year_dir / "invoice_evidence_2025.csv",
            INVOICE_EVIDENCE_FIELDS,
            [
                _invoice_row(
                    doc_id="JR",
                    fournisseur="Fournisseur sans lien public",
                    numero_facture="JR",
                    date_facture="2025-11-24",
                    ttc="1340.00",
                    compte_propose="606100",
                    famille_charge="energie_eau",
                    statut_controle="PROBABLE",
                ),
            ],
        )
        write_csv(
            self.year_dir / "invoice_anomalies_2025.csv",
            INVOICE_ANOMALY_FIELDS,
            [
                _anomaly_row(
                    doc_id="JR",
                    severity="P0",
                    anomaly="MONTANT_TTC_ABSENT",
                ),
            ],
        )

        view = build_factures_review_view(self.instance, 2025)
        rendered_model = str(view)

        self.assertEqual(len(view["rows"]), 1)
        self.assertEqual(view["rows"][0]["doc_id"], "")
        self.assertEqual(view["rows"][0]["href"], "")
        self.assertEqual(view["rows"][0]["priority_key"], "P1")
        self.assertIn("Montant TTC absent", view["rows"][0]["anomalies"])
        self.assertIn("Lecture locale insuffisante", view["rows"][0]["blocking_alert"])
        self.assertNotIn("JR", rendered_model)

    def test_french_amount_format_is_rendered_correctly(self) -> None:
        write_csv(
            self.year_dir / "invoice_evidence_2025.csv",
            INVOICE_EVIDENCE_FIELDS,
            [
                _invoice_row(
                    doc_id="DOC-MONTANT-FR",
                    fournisseur="Fournisseur montant",
                    numero_facture="FR-001",
                    date_facture="2025-04-24",
                    ttc="1 340,00 EUR",
                    compte_propose="615000",
                    famille_charge="entretien_maintenance",
                    statut_controle="INCERTAIN",
                ),
            ],
        )

        view = build_factures_review_view(self.instance, 2025)

        self.assertEqual(view["rows"][0]["amount"], "1340.00 EUR")

    def test_fire_safety_anomaly_has_dedicated_next_action(self) -> None:
        write_csv(
            self.year_dir / "invoice_evidence_2025.csv",
            INVOICE_EVIDENCE_FIELDS,
            [
                _invoice_row(
                    doc_id="DOC-FIRE-001",
                    fournisseur="Fournisseur securite incendie",
                    numero_facture="FIRE-001",
                    date_facture="2025-01-22",
                    ttc="454.01",
                    compte_propose="615000",
                    famille_charge="securite_incendie",
                    statut_controle="INCERTAIN",
                    anomalies="SECURITE_INCENDIE_A_DEVISER",
                ),
            ],
        )

        view = build_factures_review_view(self.instance, 2025)

        self.assertEqual(view["rows"][0]["priority_label"], "Priorite haute")
        self.assertIn("Securite incendie a deviser", view["rows"][0]["anomalies"])
        self.assertIn("remise en conformite incendie", view["rows"][0]["next_action"])

    def test_insurance_rib_anomaly_has_dedicated_next_action(self) -> None:
        write_csv(
            self.year_dir / "invoice_evidence_2025.csv",
            INVOICE_EVIDENCE_FIELDS,
            [
                _invoice_row(
                    doc_id="DOC-INS-001",
                    fournisseur="Courtier assurance",
                    numero_facture="QUI-001",
                    date_facture="2025-01-09",
                    ttc="22163.40",
                    compte_propose="616000",
                    famille_charge="assurance",
                    statut_controle="INCERTAIN",
                    anomalies="ASSURANCE_RIB_A_CONTROLER",
                ),
            ],
        )

        view = build_factures_review_view(self.instance, 2025)

        self.assertEqual(view["rows"][0]["priority_label"], "Priorite haute")
        self.assertIn("RIB ou mandat assurance a controler", view["rows"][0]["anomalies"])
        self.assertIn("mandat du courtier", view["rows"][0]["next_action"])

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
                _invoice_row(
                    doc_id="DOC-INV-RAW-LABEL",
                    fournisseur="",
                    numero_facture="===== NATIVE_TEXT ===== FA2025030513520296",
                    date_facture="2025-03-05",
                    ttc="120.00",
                    statut_controle="A_CONTROLER",
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
