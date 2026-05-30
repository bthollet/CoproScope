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
from coproscope.web.courriers_preuves_view import build_courriers_preuves_view


REQUIRED_LABELS = (
    "Courriers et preuves",
    "Scenario FICTIF",
    "Verification humaine requise",
    "Verifier avant envoi",
    "Brouillons a valider",
    "Preuves a rattacher",
    "Reponses recues",
    "Brouillon",
    "Texte prepare localement, pas encore transmis",
    "Mandat",
    "Raison qui autorise quelqu'un a agir ou ecrire",
    "Preuve de depot",
    "Trace que l'envoi a ete depose chez un service",
    "Preuve de reception",
    "recu ou refuse",
    "Validation humaine",
    "Copier le brouillon",
    "Rattacher une preuve",
    "source_of_truth=false",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "@",
    "C:\\",
    "file://",
    "raw",
    "restricted",
    "private",
    "OAuth",
    "IMAP",
    "SMTP",
    "LRAR",
    "Drive",
    "API prestataire",
    "email",
    "telephone",
    "adresse",
    "Envoyer",
    "Envoyer automatiquement",
    "Envoi automatique pret",
    "courrier reel",
    "secretValue",
)


class UiCourriersPreuvesTests(unittest.TestCase):
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

    def test_courriers_preuves_view_model_is_synthetic_and_blocks_transmission(self) -> None:
        view = build_courriers_preuves_view(2026)

        self.assertEqual(view["title"], "Courriers et preuves")
        self.assertIn("FICTIF", view["notice"])
        self.assertEqual(len(view["summary"]), 3)
        self.assertEqual(len(view["definitions"]), 4)
        self.assertEqual(len(view["drafts"]), 3)
        self.assertEqual(len(view["proofs"]), 3)
        self.assertTrue(any(action["enabled"] == "false" for action in view["actions"]))
        self.assertTrue(all(draft["id"].startswith("DRAFT-FICTIF-") for draft in view["drafts"]))
        self.assertEqual(view["shell_model"]["instance"]["id"], "FICTIF")

    def test_courriers_preuves_route_is_token_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/courriers/preuves")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Courriers et preuves", forbidden.text)

        response = client.get("/courriers/preuves?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn('href="/courriers/preuves?token=local-secret"', response.text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)

        visible = _visible_text(text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_courriers_preuves_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("courriers uses synthetic view")):
            response = self._client(access_token="local-secret").get(
                "/courriers/preuves",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Courriers et preuves", response.text)
        self.assertIn("Aucune transmission", response.text)

    def test_courriers_preuves_css_stacks_table_on_mobile(self) -> None:
        css_path = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "styles_part_18.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn(".cpr-table", css)
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
