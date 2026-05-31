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
from coproscope.web.worksops_travaux_view import build_travaux_suivis_view


REQUIRED_LABELS = (
    "Travaux suivis",
    "Ou en est-on ?",
    "Ce qui bloque",
    "Ce qui manque pour continuer",
    "A faire maintenant",
    "Pieces confirmees",
    "Pieces a verifier",
    "Pieces manquantes",
    "Preparer une demande",
    "Voir l'apercu avant partage",
    "A verifier avant partage",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "WorksOps",
    "OperationTravaux",
    "read model",
    "projection",
    "source_of_truth=false",
    "token",
    "hash",
    "OCR",
    "raw",
    "restricted",
    "private",
    "Travaux OK",
    "Facture validee",
    "Cloturer le chantier",
    "Envoyer automatiquement",
)


class UiWorksOpsTravauxTests(unittest.TestCase):
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

    def test_travaux_view_model_is_fully_synthetic_and_actionable(self) -> None:
        view = build_travaux_suivis_view(2026)

        self.assertEqual(view["title"], "Travaux suivis")
        self.assertIn("FICTIF", view["notice"])
        self.assertEqual(view["summary"]["confirmed"], 3)
        self.assertEqual(view["summary"]["to_verify"], 2)
        self.assertEqual(view["summary"]["missing"], 2)
        self.assertIn("A verifier avant partage", view["share"]["status"])
        self.assertIn("Preparer une demande", {item["label"] for item in view["actions"]})
        self.assertIn("autorisation d'echafaudage", view["actions"][0]["detail"])
        self.assertIn("photos avant travaux", view["actions"][0]["detail"])
        self.assertEqual(view["shell_model"]["instance"]["id"], "FICTIF")

    def test_travaux_route_is_token_guarded_and_renders_required_labels(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/travaux")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Travaux suivis", forbidden.text)

        response = client.get("/travaux?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)
        self.assertIn('href="/travaux?view=apercu&amp;token=local-secret"', response.text)
        self.assertIn(
            'href="/demandes?from=travaux&amp;preuve=autorisation-echafaudage&amp;token=local-secret"',
            response.text,
        )
        self.assertIn('href="/travaux?token=local-secret"', response.text)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn('aria-label="Travaux suivis, preuves manquantes et partage a verifier"', response.text)
        self.assertIn("Scenario FICTIF avec donnees synthetiques", text)
        self.assertIn("autorisation d'echafaudage", text)
        self.assertIn("photos avant travaux", text)
        self.assertIn("meme perimetre, les memes materiaux et la meme duree", text)
        self.assertIn("synthese pour le conseil syndical", text)

        visible = _visible_text(text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_travaux_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("travaux uses synthetic view")):
            response = self._client(access_token="local-secret").get(
                "/travaux",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Travaux suivis", response.text)
        self.assertIn("A verifier avant partage", response.text)

    def test_responsive_navigation_uses_wrapping_grid(self) -> None:
        static_dir = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static"
        shell_css = (static_dir / "styles_part_05.css").read_text(encoding="utf-8")
        mobile_css = (static_dir / "styles_part_06.css").read_text(encoding="utf-8")
        nav_block = re.search(r"\.cs-sidebar \.nav \{(?P<body>.*?)\}", shell_css, flags=re.DOTALL)

        self.assertIn("repeat(auto-fit, minmax(132px, 1fr))", shell_css)
        self.assertIn("repeat(auto-fit, minmax(118px, 1fr))", mobile_css)
        self.assertIn("max-height: 46px", mobile_css)
        self.assertIn(".cs-sidebar .nav:focus-within", mobile_css)
        self.assertIn(".cs-sidebar .nav a.active", mobile_css)
        self.assertIn("order: -1", mobile_css)
        self.assertIsNotNone(nav_block)
        self.assertNotIn("overflow-x: auto", nav_block.group("body"))


def _visible_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return " ".join(without_tags.split())


if __name__ == "__main__":
    unittest.main()
