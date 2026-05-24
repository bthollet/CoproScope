from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app


class UiAGContentieuxRouteTests(unittest.TestCase):
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

    def test_agcontentieux_route_renders_template_without_configured_token(self) -> None:
        response = self._client().get("/ag-contentieux")

        self.assertEqual(response.status_code, 200)
        self.assertIn("AG, contentieux, passation", response.text)
        self.assertIn("Checklist de passation", response.text)
        self.assertIn('href="/ag-contentieux"', response.text)
        self.assertIn('aria-label="AG, contentieux et passation, lecture novice"', response.text)

    def test_agcontentieux_route_uses_existing_token_guard_and_nav_token(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/ag-contentieux")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Checklist de passation", forbidden.text)

        response = client.get("/ag-contentieux?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn("AG, contentieux, passation", response.text)
        self.assertIn("Checklist de passation", response.text)
        self.assertIn('href="/ag-contentieux?token=local-secret"', response.text)
        self.assertIn("<span>AG / contentieux</span>", response.text)
        self.assertIn('aria-current="page"', response.text)

        fresh_client = self._client(access_token="local-secret")
        header_response = fresh_client.get("/ag-contentieux", headers={"x-coproscope-token": "local-secret"})
        self.assertEqual(header_response.status_code, 200)
        self.assertIn("Checklist de passation", header_response.text)

    def test_agcontentieux_route_skips_full_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("ag/contentieux uses its own view model")):
            response = self._client(access_token="local-secret").get("/ag-contentieux?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertIn("AG, contentieux, passation", response.text)


if __name__ == "__main__":
    unittest.main()
