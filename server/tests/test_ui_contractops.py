from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance, write_csv
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app
from coproscope.web.contractops_view import build_contractops_view


REQUIRED_LABELS = (
    "Contrats et obligations",
    "Obligations a verifier",
    "Verifier une obligation",
    "Contrats suivis",
    "Attestations attendues",
    "Contrat",
    "Obligation",
    "Attestation",
    "Clause clef",
    "Preuve attendue",
    "File contrats, obligations et attestations",
    "Decisions avant relance",
    "Voir pieces contrats",
    "Voir charges liees",
    "Voir travaux lies",
    "Voir incidents lies",
    "Rappel juridique automatique",
    "Lancer mise en concurrence",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "@",
    "C:\\",
    "file://",
    "raw",
    "restricted",
    "private",
    "OAuth",
    "Drive",
    "contrat reel",
    "attestation originale",
    "mise en concurrence automatique",
    "Envoyer",
    "secretValue",
)


class UiContractOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self, access_token: str | None = None):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")
        return TestClient(create_app(self.instance, 2025, access_token=access_token))

    def test_contractops_view_model_falls_back_to_fictive_examples(self) -> None:
        view = build_contractops_view(year=2026)

        self.assertEqual(view["title"], "Contrats et obligations")
        self.assertIn("FICTIF", view["notice"])
        self.assertEqual(len(view["summary"]), 4)
        self.assertEqual(len(view["contracts"]), 3)
        self.assertTrue(any(action["enabled"] == "false" for action in view["actions"]))
        self.assertTrue(all(row["source_label"] == "FICTIF" for row in view["contracts"]))
        self.assertEqual(view["shell_model"]["instance"]["id"], "FICTIF")

    def test_contractops_view_model_reads_derived_rows_without_leaking_paths(self) -> None:
        reports_dir = self.instance.artifact("reports_dir")
        reports_dir.mkdir(parents=True, exist_ok=True)
        write_csv(
            reports_dir / "matrice_completude_documentaire.csv",
            [
                "proof_id",
                "expected_label",
                "document_type",
                "status",
                "criticality",
                "evidence_paths",
                "reason",
                "action",
            ],
            [
                {
                    "proof_id": "PRV-CONTRAT-SYNDIC",
                    "expected_label": "Contrat syndic signe",
                    "document_type": "Contrat_Syndic",
                    "status": "ABSENT",
                    "criticality": "P1",
                    "evidence_paths": r"C:\\Users\\demo\\raw\\contrat.pdf",
                    "reason": "Contrat necessaire pour reprendre les obligations.",
                    "action": "Demander la derniere version signee au syndic.",
                }
            ],
        )

        view = build_contractops_view(instance=self.instance, year=2026)
        visible = str(view)

        self.assertEqual(view["contracts"][0]["source_label"], "Synthese derivee")
        self.assertEqual(view["contracts"][0]["status_label"], "preuve manquante")
        self.assertIn("Syndic", view["contracts"][0]["family_label"])
        self.assertNotIn("raw", visible)
        self.assertNotIn("C:\\", visible)

    def test_contractops_route_is_token_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/contrats")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Contrats et obligations", forbidden.text)

        response = client.get("/contrats?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn('href="/contrats?token=local-secret"', response.text)
        self.assertIn('href="/pieces?proof=missing&amp;group=contrats&amp;token=local-secret"', response.text)
        self.assertIn('href="/incidents?scope=contrats&amp;token=local-secret"', response.text)
        self.assertIn('title="Points qui demandent une preuve ou une verification."', response.text)
        self.assertIn('class="panel ctr-help"', response.text)
        self.assertIn("6 definitions", text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)

        visible = _visible_text(text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_contractops_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("contracts uses dedicated view")):
            response = self._client(access_token="local-secret").get(
                "/contrats",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Contrats et obligations", response.text)
        self.assertIn("Aucun envoi", response.text)

    def test_contractops_css_stacks_table_on_mobile(self) -> None:
        css_path = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "styles_part_23.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn(".ctr-table", css)
        self.assertIn(".ctr-summary article", css)
        self.assertIn("padding: 0.55rem 0.7rem", css)
        self.assertIn("grid-template-columns: auto minmax(0, 1fr)", css)
        self.assertIn(".ctr-help summary", css)
        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn("grid-template-columns: 1fr", css)
        mobile_block = re.search(r"@media.*", css, flags=re.DOTALL).group(0)
        self.assertNotIn("overflow-x: auto", mobile_block)


def _visible_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return " ".join(without_tags.split())


if __name__ == "__main__":
    unittest.main()
