from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app
from coproscope.web.governance_atelier_ag_view import build_governance_atelier_ag_view


REQUIRED_LABELS = (
    "Atelier AG",
    "Scenario FICTIF",
    "Projet CS - non officiel",
    "Version de travail",
    "Verifier avant partage",
    "Questions a preparer",
    "Resolutions en brouillon",
    "Preuves a rattacher",
    "Diffusions a verifier",
    "Pas une convocation",
    "Pas un proces-verbal",
    "Questions, resolutions et preuves",
    "Explication des devis manquants",
    "Choix d'un prestataire travaux",
    "Controle avant partage",
    "Fait",
    "Preuve",
    "Regle",
    "Action",
    "Revue de diffusion avant export",
    "Actions de travail",
    "Envoyer convocation",
    "Publier proces-verbal",
    "Enregistrer vote",
    "Journal de versions",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "@",
    "C:\\",
    "file://",
    "raw",
    "restricted",
    "private",
    "Convocation envoyee",
    "Proces-verbal publie",
    "Vote officiel enregistre",
    "signature qualifiee",
    "avis juridique",
    "OAuth",
    "Drive",
)


class UiGovernanceAtelierAgTests(unittest.TestCase):
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

    def test_governance_atelier_ag_view_model_is_synthetic_and_official_actions_blocked(self) -> None:
        view = build_governance_atelier_ag_view(2026)

        self.assertEqual(view["title"], "Atelier AG")
        self.assertIn("FICTIF", view["notice"])
        self.assertEqual(len(view["summary"]), 4)
        self.assertEqual(len(view["agenda_items"]), 4)
        self.assertEqual(len(view["review_steps"]), 4)
        self.assertTrue(any(action["enabled"] == "false" for action in view["actions"]))
        self.assertTrue(all(item["id"].startswith("AG-FICTIF-") for item in view["agenda_items"]))
        self.assertEqual(view["shell_model"]["instance"]["id"], "FICTIF")

    def test_governance_atelier_ag_route_is_token_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/gouvernance/atelier-ag")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Atelier AG", forbidden.text)

        response = client.get("/gouvernance/atelier-ag?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn('href="/gouvernance/atelier-ag?token=local-secret"', response.text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)

        visible = _visible_text(text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_governance_atelier_ag_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("atelier ag uses synthetic view")):
            response = self._client(access_token="local-secret").get(
                "/gouvernance/atelier-ag",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Atelier AG", response.text)
        self.assertIn("Projet CS - non officiel", response.text)

    def test_governance_atelier_ag_css_stacks_table_on_mobile(self) -> None:
        css_path = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "styles_part_21.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn(".agw-table", css)
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
