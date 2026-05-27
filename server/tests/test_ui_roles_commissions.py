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
from coproscope.web.roles_commissions_view import build_roles_commissions_view


REQUIRED_LABELS = (
    "Roles et commissions",
    "Scenario FICTIF",
    "Validation humaine obligatoire",
    "Relire les droits par ressource",
    "Profils synthetiques",
    "Commissions",
    "Ressources protegees",
    "Actions sensibles",
    "Aucun annuaire reel",
    "Aucun droit applique",
    "Mots utiles",
    "Role",
    "Commission",
    "Referent",
    "Ressource",
    "PROF-FICTIF-01",
    "Commission travaux",
    "Commission finances",
    "Droits par ressource",
    "Coffre travaux",
    "Participants AG",
    "source_of_truth=false",
    "Actions bloquees",
    "Inviter un membre",
    "Changer un droit",
    "Exporter un annuaire",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "@",
    "C:\\",
    "file://",
    "raw",
    "restricted",
    "private",
    "coproprietaires.csv",
    "Annuaire reel",
    "Invitation envoyee",
    "Droit applique",
    "OAuth",
    "Drive",
    "secretValue",
)


class UiRolesCommissionsTests(unittest.TestCase):
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

    def test_roles_commissions_view_model_is_synthetic_and_blocks_sensitive_actions(self) -> None:
        view = build_roles_commissions_view(2026)

        self.assertEqual(view["title"], "Roles et commissions")
        self.assertIn("FICTIF", view["notice"])
        self.assertEqual(len(view["summary"]), 4)
        self.assertEqual(len(view["profiles"]), 5)
        self.assertEqual(len(view["commissions"]), 3)
        self.assertEqual(len(view["rights_matrix"]), 6)
        self.assertTrue(all(profile["id"].startswith("PROF-FICTIF-") for profile in view["profiles"]))
        self.assertTrue(all(action["enabled"] == "false" for action in view["actions"]))
        self.assertTrue(any(row["resource"] == "Exports derives" for row in view["rights_matrix"]))
        self.assertEqual(view["shell_model"]["instance"]["id"], "FICTIF")

    def test_roles_commissions_route_is_token_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/gouvernance/roles-commissions")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Roles et commissions", forbidden.text)

        response = client.get("/gouvernance/roles-commissions?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn('href="/gouvernance/roles-commissions?token=local-secret"', response.text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)

        visible = _visible_text(text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_roles_commissions_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("roles uses synthetic view")):
            response = self._client(access_token="local-secret").get(
                "/gouvernance/roles-commissions",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Roles et commissions", response.text)
        self.assertIn("Aucun droit reel applique", response.text)

    def test_roles_commissions_css_stacks_table_on_mobile(self) -> None:
        css_path = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "styles_part_26.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn(".rol-table", css)
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
