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
from coproscope.web.coffre_partage_view import build_coffre_partage_view


REQUIRED_LABELS = (
    "Coffre et partage",
    "Verifier avant partage",
    "Avant de partager",
    "Coffre local",
    "Transport chiffre",
    "Personnes",
    "Ordinateurs reconnus",
    "Referent de secours",
    "Relire droits",
    "Lire",
    "Ajouter",
    "Valider",
    "Exporter",
    "Peut gerer les acces",
    "Droit sensible",
    "Deux versions du coffre existent",
    "Invitation bloquee",
    "Retrait prudent",
    "Recuperation encadree",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "vault",
    "OAuth",
    "scope",
    "device",
    "admin",
    "Envoyer automatiquement",
    "Invitation envoyee",
    "Export pret",
    "Efface les copies",
    "C:\\",
    "file://",
    "raw",
    "restricted",
    "private",
)


class UiCoffrePartageTests(unittest.TestCase):
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

    def test_coffre_partage_view_model_is_synthetic_and_blocked_by_default(self) -> None:
        view = build_coffre_partage_view(2026)

        self.assertEqual(view["title"], "Coffre et partage")
        self.assertIn("FICTIF", view["notice"])
        self.assertIn("Verification requise", view["status"]["label"])
        self.assertEqual(len(view["members"]), 3)
        self.assertEqual(len(view["rights"]), 5)
        self.assertTrue(all(action["enabled"] == "false" for action in view["actions"]))
        self.assertIn("Deux versions du coffre existent", view["states"]["conflict"]["label"])
        self.assertEqual(view["shell_model"]["instance"]["id"], "FICTIF")

    def test_coffre_partage_route_is_token_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/coffre/partage")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Coffre et partage", forbidden.text)

        response = client.get("/coffre/partage?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn('href="/coffre/partage?token=local-secret"', response.text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)
        self.assertIn("Aucune invitation ou export n'est actif", text)
        self.assertIn("Retirer l'acces n'efface pas les copies deja obtenues", text)
        self.assertIn("aucune recuperation solitaire", text)

        visible = _visible_text(text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_coffre_partage_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("coffre uses synthetic view")):
            response = self._client(access_token="local-secret").get(
                "/coffre/partage",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Coffre et partage", response.text)
        self.assertIn("Invitation bloquee", response.text)

    def test_coffre_partage_css_stacks_rights_on_mobile(self) -> None:
        css_path = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "styles_part_15.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn(".coffre-rights-table", css)
        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn("grid-template-columns: 1fr 1fr", css)
        self.assertNotIn("overflow-x: auto", re.search(r"@media.*", css, flags=re.DOTALL).group(0))


def _visible_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return " ".join(without_tags.split())


if __name__ == "__main__":
    unittest.main()
