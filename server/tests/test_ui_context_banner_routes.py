from __future__ import annotations

import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import load_instance


ROOT = Path(__file__).resolve().parents[2]
INSTANCE_ROOT = ROOT / "examples" / "synthetic_copro"


class UiContextBannerRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.instance = load_instance(None, str(INSTANCE_ROOT))

    def _client(self, token: str | None = None):
        try:
            from fastapi.testclient import TestClient  # type: ignore
            from coproscope.web.app import create_app
        except ImportError as exc:  # pragma: no cover - optional UI dependency
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        return TestClient(create_app(self.instance, year=2025, access_token=token))

    def test_main_pages_render_context_banner_without_configured_vault(self) -> None:
        client = self._client()

        for path in ["/", "/actions", "/documents", "/pieces", "/depot", "/gouvernance", "/demandes", "/pilotage"]:
            with self.subTest(path=path):
                response = client.get(path)
                text = unescape(response.text)

                self.assertEqual(response.status_code, 200)
                self.assertIn('class="context-banner context-banner--review"', text)
                self.assertIn("Residence Les Platanes", text)
                self.assertIn("Coffre signe a declarer", text)
                self.assertIn("Sync non branchee", text)
                self.assertIn("Prochaine action", text)

    def test_context_banner_next_action_preserves_local_token(self) -> None:
        client = self._client(token="local-secret")

        response = client.get("/actions?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn('class="context-banner context-banner--review"', text)
        self.assertIn('href="/gouvernance?token=local-secret"', text)

    def test_non_main_pages_keep_existing_no_banner_contract(self) -> None:
        client = self._client()

        response = client.get("/confidentialite")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('class="context-banner', response.text)


if __name__ == "__main__":
    unittest.main()
