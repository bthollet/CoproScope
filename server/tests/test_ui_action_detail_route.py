from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from urllib.parse import unquote

from coproscope.core.common import load_instance
from coproscope.web.app import create_app


class UiActionDetailRouteTests(unittest.TestCase):
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

    def test_action_cards_link_to_real_detail_route_that_opens_selected_sheet(self) -> None:
        client = self._client(access_token="local-secret")

        index_response = client.get("/actions?token=local-secret")
        self.assertEqual(index_response.status_code, 200)
        match = re.search(r'href="/actions/([^"?]+)\?token=local-secret"', index_response.text)
        self.assertIsNotNone(match)
        action_id = unquote(match.group(1))

        detail_response = client.get(f"/actions/{action_id}?token=local-secret", follow_redirects=False)
        self.assertEqual(detail_response.status_code, 303)
        self.assertIn(f"/actions?selected={action_id}&token=local-secret", detail_response.headers["location"])

        selected_response = client.get(detail_response.headers["location"])
        self.assertEqual(selected_response.status_code, 200)
        self.assertIn("Fiche decision", selected_response.text)
        self.assertIn("Actions de cette fiche", selected_response.text)
        self.assertIn("Preparer une relance syndic", selected_response.text)
        self.assertNotIn("Envoyer automatiquement", selected_response.text)

    def test_unknown_action_detail_redirects_to_actions_with_missing_marker(self) -> None:
        client = self._client(access_token="local-secret")

        detail_response = client.get("/actions/ACT-UNKNOWN-404?token=local-secret", follow_redirects=False)

        self.assertEqual(detail_response.status_code, 303)
        self.assertEqual(
            detail_response.headers["location"],
            "/actions?action_missing=ACT-UNKNOWN-404&token=local-secret",
        )

        selected_response = client.get(detail_response.headers["location"])
        self.assertEqual(selected_response.status_code, 200)
        self.assertIn("Aucune fiche ouverte avec ce lien.", selected_response.text)
        self.assertNotIn("Fiche decision", selected_response.text)

    def test_unknown_private_like_action_id_is_not_reflected_in_redirect(self) -> None:
        client = self._client(access_token="local-secret")

        detail_response = client.get(
            "/actions/C:%5CUsers%5CExampleUser%5Craw%5Cpiece-privee.pdf?token=local-secret",
            follow_redirects=False,
        )

        self.assertEqual(detail_response.status_code, 303)
        location = detail_response.headers["location"]
        self.assertEqual(location, "/actions?action_missing=reference-locale-masquee&token=local-secret")
        self.assertNotIn("Users", location)
        self.assertNotIn("raw", location)
        self.assertNotIn("piece-privee", location)

    def test_action_missing_query_shows_safe_fallbacks_with_token(self) -> None:
        client = self._client(access_token="local-secret")

        response = client.get("/actions?token=local-secret&action_missing=C%3A%5CUsers%5Csecret.txt")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Action introuvable", text)
        self.assertIn("La fiche demandee n'est plus disponible avec ce lien.", text)
        self.assertIn("Aucune fiche ouverte avec ce lien.", text)
        self.assertIn('href="/actions?priority=P1&token=local-secret"', text)
        self.assertIn('href="/actions?token=local-secret"', text)
        self.assertNotIn("Fiche decision", text)
        self.assertNotIn(r"C:\Users", text)
        self.assertNotIn("secret.txt", text)


if __name__ == "__main__":
    unittest.main()
