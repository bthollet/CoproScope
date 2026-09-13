"""Routes servies par l'app locale, jeton d'acces et garde reseau.

Extrait de `test_ui_demo.py` (603 lignes) pour tenir le plafond de 600 lignes du
depot. La fixture d'instance demo reste partagee via `DemoInstanceTestCase`.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from coproscope.web.app import create_app, serve

from tests.test_ui_demo import DemoInstanceTestCase


class UiDemoRoutesSecuriteTests(DemoInstanceTestCase):
    """Ce qui repond 200, ce qui repond 404 ou 403, et ce que le CLI passe a `serve`."""

    def test_local_web_routes_render_without_serving_private_roots(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        _, demo = self._build_demo()
        client = TestClient(create_app(demo, 2025))

        for path in [
            "/",
            "/exports/actions.csv",
            "/exports/actions.md",
            "/comptes",
            "/documents",
            "/chantiers",
            "/api/model",
            "/exports/local.zip",
            "/health",
        ]:
            response = client.get(path)
            self.assertEqual(response.status_code, 200, path)

        # RM-2026-0183: ecrans retires, plus servis.
        for path in ["/actions", "/actions?scope=comptes", "/confidentialite", "/depot"]:
            self.assertEqual(client.get(path).status_code, 404, path)

        csv_export = client.get("/exports/actions.csv")
        self.assertIn("priority,status,domain,source", csv_export.text)
        markdown_export = client.get("/exports/actions.md?scope=comptes")
        self.assertIn("# Actions CoproScope", markdown_export.text)

        for forbidden in ["/demo", "/raw/2025-01-18_facture_entretien_jardin.txt", "/restricted/secret.txt", "/.env.local"]:
            response = client.get(forbidden)
            self.assertEqual(response.status_code, 404, forbidden)

    def test_token_guard_protects_sensitive_ui_routes(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        _, demo = self._build_demo()
        client = TestClient(create_app(demo, 2025, access_token="local-secret"))

        # RM-2026-0183: `/depot` (GET) est retire; le jeton reste eprouve sur les routes servies.
        self.assertEqual(client.get("/api/model").status_code, 403)
        self.assertEqual(client.get("/exports/local.zip").status_code, 403)

        self.assertEqual(client.get("/api/model", headers={"x-coproscope-token": "local-secret"}).status_code, 200)
        self.assertEqual(client.get("/exports/local.zip?token=local-secret").status_code, 200)

    def test_serve_refuses_lan_without_explicit_unsafe_flag(self) -> None:
        _, demo = self._build_demo()

        with self.assertRaises(ValueError):
            serve(demo, 2025, host="0.0.0.0", port=8765, access_token="local-secret")

    def test_ui_open_test_uses_visible_foreground_server_options(self) -> None:
        _, demo = self._build_demo()
        from coproscope.cli import _dispatch, build_parser

        args = build_parser().parse_args(
            [
                "ui",
                "open-test",
                "--instance-root",
                str(demo.instance_root),
                "--year",
                "2025",
                "--host",
                "127.0.0.1",
                "--port",
                "8769",
                "--token",
                "qa-2000-local",
            ]
        )
        with patch("coproscope.web.app.serve") as mocked_serve:
            result = _dispatch(args)

        self.assertEqual(result, 0)
        mocked_serve.assert_called_once()
        _, kwargs = mocked_serve.call_args
        self.assertEqual(kwargs["year"], 2025)
        self.assertEqual(kwargs["host"], "127.0.0.1")
        self.assertEqual(kwargs["port"], 8769)
        self.assertEqual(kwargs["access_token"], "qa-2000-local")
        self.assertFalse(kwargs["unsafe_lan"])


if __name__ == "__main__":
    unittest.main()
