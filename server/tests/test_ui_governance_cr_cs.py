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
from coproscope.web.governance_cr_cs_view import build_governance_cr_cs_view


REQUIRED_LABELS = (
    "Compte rendu du conseil syndical",
    "document interne, aucun envoi officiel",
    "Validation interne a preparer",
    "Verifier avant partage",
    "Relire decisions",
    "Reunion et presents",
    "Validation interne",
    "Decisions, actions et preuves",
    "Preuve / source",
    "Qui pourra voir ce document",
    "Journal de versions",
    "Ne vaut pas proces-verbal d'assemblee generale",
    "fichier prepare reste local",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "PV AG",
    "Signer",
    "Publier",
    "Envoyer officiel",
    "Resolution adoptee",
    "signature qualifiee",
    "Notification envoyee",
    "C:\\",
    "file://",
    "raw",
    "restricted",
    "private",
)


class UiGovernanceCrCsTests(unittest.TestCase):
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

    def test_governance_cr_cs_view_model_is_synthetic_and_blocked_by_default(self) -> None:
        view = build_governance_cr_cs_view(2026)

        self.assertEqual(view["title"], "Compte rendu du conseil syndical")
        self.assertIn("FICTIF", view["notice"])
        self.assertIn("Validation interne", view["status"]["label"])
        self.assertEqual(len(view["decisions"]), 3)
        self.assertEqual(len(view["validation_steps"]), 4)
        self.assertTrue(any(action["enabled"] == "false" for action in view["actions"]))
        self.assertEqual(view["shell_model"]["instance"]["id"], "FICTIF")

    def test_governance_cr_cs_route_is_token_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/gouvernance/compte-rendu-cs")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Compte rendu du conseil syndical", forbidden.text)

        response = client.get("/gouvernance/compte-rendu-cs?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn('href="/gouvernance/compte-rendu-cs?token=local-secret"', response.text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)

        visible = _visible_text(text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_governance_cr_cs_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("governance cr uses synthetic view")):
            response = self._client(access_token="local-secret").get(
                "/gouvernance/compte-rendu-cs",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Compte rendu du conseil syndical", response.text)
        self.assertIn("Validation interne", response.text)

    def test_governance_cr_cs_css_stacks_decisions_on_mobile(self) -> None:
        css_path = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "styles_part_16.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn(".crcs-decision-table", css)
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
