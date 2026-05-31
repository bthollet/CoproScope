from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance, read_csv, write_csv
from coproscope.modules.accounting import COMPTASCOPE_REVIEW_FIELDS
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app
from coproscope.web.compta_rapprochement_view import (
    READ_MODEL_NAME,
    build_compta_reconciliation_view,
)


REQUIRED_LABELS = (
    "Controle des comptes",
    "Sources du controle",
    "Lignes a controler",
    "Controle humain ouvert",
    "Factures, lignes comptables et decisions",
    "Commencez par l'action proposee",
    "Ligne selectionnee et preuves",
    "Retour aux comptes",
    "Relues ou reservees",
    "Traces locales du conseil",
    "Comptabilite",
    "Banque",
    "Facture",
    "Decision / devis",
    "Action immediate",
    "A faire sur cette ligne",
    "Tracer le controle local",
    "Aucune validation de paiement",
    "Rapprochement 4 sources",
    "La facture seule ne confirme jamais le paiement",
    "Question syndic et suite",
    "Trace conseil syndical",
    "Marquer comme relu par le conseil",
    "Garder une reserve visible",
    "Question syndic a relire et copier, aucun envoi automatique",
    "Banque et grand livre restent a fournir",
    "Banque non fournie",
    "Grand livre non fourni",
    "Elle ne valide pas un paiement ni la comptabilite officielle",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "C:\\",
    "file://",
    "/Users/",
    "/home/",
    "Read model",
    "raw/",
    "restricted/",
    "logs/",
    "private/",
    "secretValue",
    "Envoyer automatiquement",
)


class UiComptesRapprochementTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)
        self.accounting_dir = self.instance.artifact("accounting_dir")
        self.accounting_dir.mkdir(parents=True, exist_ok=True)
        self._seed_review_rows()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self, access_token: str | None = None):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")
        return TestClient(create_app(self.instance, 2025, access_token=access_token))

    def test_view_model_builds_public_queue_from_comptascope_review_rows(self) -> None:
        view = build_compta_reconciliation_view(instance=self.instance, year=2025)
        visible = str(view)

        self.assertEqual(view["read_model_name"], READ_MODEL_NAME)
        self.assertEqual(len(view["items"]), 2)
        self.assertEqual(view["items"][0]["id"], "REV-2025-001")
        self.assertEqual([cell["kind"] for cell in view["items"][0]["cells"]], ["Comptabilite", "Banque", "Facture", "Decision / devis"])
        self.assertIn("Brouillon a copier", view["items"][0]["copy_text"])
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_view_model_replaces_raw_document_labels(self) -> None:
        write_csv(
            self.accounting_dir / "controle_comptes_guide_2025.csv",
            COMPTASCOPE_REVIEW_FIELDS,
            [
                _review_row(
                    review_id="REV-2025-FILE-001",
                    fournisseur="sha256,count,doc_ids,paths",
                    numero_facture="abour.pdf",
                    doc_id="DOC-FAC-FILE",
                    ttc="73333.05",
                    question_syndic="Merci de rapprocher la facture Vid de # 09_Devis_ventilation_Baillargues.pdf.",
                    motif="Colonnes sources date,document_type,count,doc_ids,examples.",
                    bloc_copiable=(
                        "Controle - Facture abour.pdf - # 09_Devis_ventilation_Baillargues.pdf - "
                        "date,document_type,count,doc_ids,examples - Vid"
                    ),
                )
            ],
        )

        item = build_compta_reconciliation_view(instance=self.instance, year=2025)["items"][0]
        visible = str(item)
        self.assertEqual(item["title"], "Piece comptable a qualifier")
        self.assertNotIn(".pdf", visible)
        self.assertNotIn("sha256,count,doc_ids,paths", visible)
        self.assertNotIn("date,document_type,count,doc_ids,examples", visible)
        self.assertNotIn("Facture abour", visible)
        self.assertNotIn("abour.pdf", visible)
        self.assertNotIn("Facture Vid", item["subtitle"])
        self.assertNotIn("facture Vid", visible)
        self.assertNotIn("_Devis_", visible)
        self.assertIn("73333.05 EUR", item["subtitle"])

    def test_view_model_loads_real_year_subdirectory_layout(self) -> None:
        root_path = self.accounting_dir / "controle_comptes_guide_2025.csv"
        _, rows = read_csv(root_path)
        year_dir = self.accounting_dir / "2025"
        year_dir.mkdir(parents=True, exist_ok=True)
        root_path.unlink()
        write_csv(year_dir / "controle_comptes_guide_2025.csv", COMPTASCOPE_REVIEW_FIELDS, rows)

        view = build_compta_reconciliation_view(instance=self.instance, year=2025)
        client = self._client(access_token="local-secret")
        response = client.post(
            "/comptes/rapprochement/validation?token=local-secret",
            data={"review_id": "REV-2025-001", "decision": "validated", "note": ""},
            follow_redirects=False,
        )

        self.assertEqual(len(view["items"]), 2)
        self.assertEqual(view["items"][0]["id"], "REV-2025-001")
        self.assertEqual(response.status_code, 303)
        self.assertTrue((year_dir / "compta_human_validations_2025.csv").exists())

    def test_route_is_token_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/comptes/rapprochement")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Controle des comptes", forbidden.text)

        response = client.get("/comptes/rapprochement?token=local-secret")
        text = unescape(response.text)
        visible = _visible_text(text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn('href="/comptes?token=local-secret"', response.text)
        self.assertIn('action="/comptes/rapprochement/validation?token=local-secret"', response.text)
        self.assertIn('<details class="panel cs-rappro-detail" open>', response.text)
        self.assertIn('<summary class="panel-head cs-rappro-detail-summary">', response.text)
        self.assertNotIn("ComptaScope - controle prudent", text)
        self.assertNotIn("Decision avant rapport", text)
        self.assertNotIn("<h3>Diffusion</h3>", response.text)
        self.assertNotIn("Historique local", text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)
        self.assertEqual(visible.count("Controle des comptes"), 1)
        self.assertNotIn(READ_MODEL_NAME, visible)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("dedicated view")):
            response = self._client(access_token="local-secret").get(
                "/comptes/rapprochement",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Controle des comptes", response.text)

    def test_right_detail_panel_is_foldable(self) -> None:
        response = self._client(access_token="local-secret").get("/comptes/rapprochement?token=local-secret")
        static_root = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static"
        css = (static_root / "styles_part_07.css").read_text(encoding="utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("<details", response.text)
        self.assertIn("cs-rappro-detail", response.text)
        self.assertIn("cs-rappro-detail-summary", response.text)
        self.assertIn("Masquer le detail", response.text)
        self.assertIn("Afficher le detail", response.text)
        self.assertIn(".cs-rappro-detail:not([open])", css)
        self.assertIn(".cs-rappro-detail-summary::marker", css)
        self.assertNotIn('content: "v"', css)
        self.assertIn("cursor: pointer", css)

    def test_detail_uses_four_source_matrix_without_bank_overclaim(self) -> None:
        response = self._client(access_token="local-secret").get("/comptes/rapprochement?token=local-secret")
        text = unescape(response.text)
        static_root = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static"
        css = (static_root / "styles_part_30.css").read_text(encoding="utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("cs-rappro-matrix-grid", response.text)
        self.assertIn("cs-rappro-summary-action", response.text)
        self.assertIn("cs-rappro-action", response.text)
        self.assertIn('href="#rappro-validation"', response.text)
        self.assertIn('id="rappro-validation"', response.text)
        self.assertLess(response.text.index("cs-rappro-action"), response.text.index("cs-rappro-matrix"))
        self.assertLess(response.text.index("cs-rappro-matrix"), response.text.index("cs-focus-card"))
        self.assertLess(response.text.index("Action immediate"), response.text.index("Rapprochement 4 sources"))
        self.assertIn('role="listitem" class="cs-rappro-source-cell', response.text)
        matrix_text = text[text.index("Rapprochement 4 sources") :]
        order = [matrix_text.index(label) for label in ("Comptabilite", "Banque", "Facture", "Decision / devis")]
        self.assertEqual(order, sorted(order))
        self.assertIn("Banque non fournie", text)
        self.assertIn("aucun paiement n'est confirme", text)
        self.assertIn("source manquante", text)
        self.assertIn('href="/documents/DOC-FAC-001?token=local-secret"', response.text)
        self.assertIn("grid-template-columns: repeat(4, minmax(0, 1fr))", css)
        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn("@media (max-width: 640px)", css)
        self.assertIn("@media (max-width: 560px)", css)
        self.assertNotIn("@media (max-width: 1320px)", css)
        self.assertIn("-webkit-line-clamp: 2", css)
        self.assertIn(".cs-comptes-header .lead", css)
        self.assertIn("-webkit-line-clamp: 1", css)
        self.assertIn("min-width: 142px", css)
        imports = (static_root / "styles.css").read_text(encoding="utf-8")
        self.assertIn("styles_part_30.css?v=20260531-compta-031", imports)

    def test_long_queue_keeps_detail_before_scrollable_line_list(self) -> None:
        write_csv(
            self.accounting_dir / "controle_comptes_guide_2025.csv",
            COMPTASCOPE_REVIEW_FIELDS,
            [
                _review_row(
                    review_id=f"REV-2025-LONG-{index:03d}",
                    priorite="P1" if index % 3 == 0 else "P2",
                    fournisseur=f"Fournisseur fictif {index:03d}",
                    numero_facture=f"FAC-{index:03d}",
                    doc_id=f"DOC-FAC-{index:03d}",
                    ttc=str(100 + index),
                    statut_rapprochement="NON_RAPPROCHE",
                    libelle_statut="A traiter avant assemblee",
                    motif="Source bancaire absente.",
                    prochaine_action="Verifier les sources avant validation.",
                )
                for index in range(1, 828)
            ],
        )
        response = self._client(access_token="local-secret").get("/comptes/rapprochement?token=local-secret")
        css = (
            Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "styles_part_30.css"
        ).read_text(encoding="utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("827 lignes", response.text)
        self.assertLess(response.text.index('id="rappro-file"'), response.text.index("cs-comptes-kpis"))
        self.assertLess(response.text.index('id="rappro-file"'), response.text.index("rappro-definitions-title"))
        self.assertLess(response.text.index("cs-rappro-detail"), response.text.index("cs-rappro-queue-panel"))
        self.assertLess(response.text.index("Rapprochement 4 sources"), response.text.index("Lignes a controler"))
        self.assertIn(".cs-rappro-queue-list", css)
        self.assertIn(".cs-rappro-summary-action", css)
        self.assertIn(".cs-rappro-action", css)
        self.assertLess(response.text.index("Action immediate"), response.text.index("Rapprochement 4 sources"))
        self.assertLess(response.text.index("Rapprochement 4 sources"), response.text.index("cs-focus-card"))
        self.assertIn("white-space: normal", css)
        self.assertIn("overflow-wrap: anywhere", css)
        self.assertIn("max-height: min(680px, calc(100vh - 174px))", css)
        self.assertIn("overflow-y: auto", css)
        self.assertIn("@media (max-width: 980px)", css)
        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn("@media (max-width: 640px)", css)
        self.assertIn(".cs-comptes-header .cs-header-tools", css)
        self.assertIn("flex: 0 1 auto", css)
        self.assertIn("flex-direction: row", css)
        self.assertIn("justify-content: flex-end", css)
        self.assertIn(".cs-comptes-header .lead", css)
        self.assertIn("grid-row: 1", css)

    def test_validation_post_appends_human_trace_without_private_note_leak(self) -> None:
        client = self._client(access_token="local-secret")
        response = client.post(
            "/comptes/rapprochement/validation?token=local-secret",
            data={
                "review_id": "REV-2025-001",
                "decision": "validated_with_reserve",
                "note": r"Reserve depuis C:\\Users\\demo\\raw\\secret.txt",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertIn("/comptes/rapprochement?selected=REV-2025-001", response.headers["location"])
        _, rows = read_csv(self.accounting_dir / "compta_human_validations_2025.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["decision"], "validated_with_reserve")
        self.assertEqual(rows[0]["decision_label"], "Reserve visible")
        self.assertNotIn("C:\\", rows[0]["note"])
        self.assertNotIn("raw", rows[0]["note"].lower())

        follow_up = client.get(response.headers["location"])
        text = unescape(follow_up.text)
        self.assertEqual(follow_up.status_code, 200)
        self.assertIn("Reserve visible", text)
        self.assertIn("Elle ne valide pas un paiement ni la comptabilite officielle", text)
        self.assertNotIn("C:\\", _visible_text(text))
        self.assertNotIn("raw", _visible_text(text).lower())

    def _seed_review_rows(self) -> None:
        write_csv(
            self.accounting_dir / "controle_comptes_guide_2025.csv",
            COMPTASCOPE_REVIEW_FIELDS,
            [
                _review_row(
                    review_id="REV-2025-001",
                    priorite="P1",
                    fournisseur="Ascenseur FICTIF",
                    numero_facture="FAC-001",
                    doc_id="DOC-FAC-001",
                    date_facture="2025-02-10",
                    ttc="1200.00",
                    niveau_preuve="facture extraite",
                    statut_rapprochement="NON_RAPPROCHE",
                    libelle_statut="A traiter avant assemblee",
                    motif="Aucun mouvement compatible n'est rattache.",
                    prochaine_action="Demander mouvement bancaire et decision ou devis.",
                    question_syndic="Pouvez-vous transmettre le mouvement bancaire et le devis associe ?",
                    bloc_copiable="Brouillon a copier, aucun envoi automatique: merci de transmettre le mouvement et la justification.",
                ),
                _review_row(
                    review_id="REV-2025-002",
                    priorite="P2",
                    fournisseur="Nettoyage FICTIF",
                    numero_facture="FAC-002",
                    doc_id="DOC-FAC-002",
                    date_facture="2025-03-05",
                    ttc="480.00",
                    niveau_preuve="facture et ligne candidate",
                    statut_rapprochement="CANDIDAT_MONTANT_FAMILLE",
                    libelle_statut="A confirmer",
                    ligne_depense_candidate="DEP-2025-002",
                    reference_depense="REF-2025-002",
                    libelle_depense="Entretien parties communes",
                    montant_depense="480.00",
                    ecriture_candidate="Ligne entretien candidate",
                    compte_candidate="615",
                    motif="Montant exact mais libelle a relire.",
                    prochaine_action="Confirmer le fournisseur avant validation.",
                ),
            ],
        )


def _review_row(**updates: str) -> dict[str, str]:
    row = {field: "" for field in COMPTASCOPE_REVIEW_FIELDS}
    row.update({key: str(value) for key, value in updates.items()})
    row["exercice"] = row.get("exercice") or "2025"
    return row


def _visible_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return " ".join(without_tags.split())


if __name__ == "__main__":
    unittest.main()
