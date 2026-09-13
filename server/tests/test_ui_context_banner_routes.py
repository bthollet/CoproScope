from __future__ import annotations

import re
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

    def _banner_html(self, text: str) -> str:
        match = re.search(r'(<section class="context-banner\b.*?</section>)', text, re.S)
        self.assertIsNotNone(match, "context banner section missing")
        return match.group(1) if match else ""

    def test_main_pages_render_context_banner_without_configured_vault(self) -> None:
        client = self._client()

        for path in ["/", "/documents", "/pieces", "/demandes"]:
            with self.subTest(path=path):
                response = client.get(path)
                text = unescape(response.text)

                self.assertEqual(response.status_code, 200)
                banner = self._banner_html(text)
                self.assertIn('class="context-banner context-banner--review"', banner)
                self.assertIn("Residence Les Platanes", banner)
                # La page de contexte `/gouvernance` est supprimee (RM-2026-0183):
                # le bandeau ne pointe plus vers elle, et ne pointe vers rien.
                self.assertNotIn("Voir le contexte", banner)
                self.assertNotIn("href=", banner)
                self.assertNotIn("Coffre signe a declarer", banner)
                self.assertNotIn("Sync non branchee", banner)
                self.assertNotIn("Prochaine action", banner)

    def test_context_banner_next_action_preserves_local_token(self) -> None:
        client = self._client(token="local-secret")

        response = client.get("/documents?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn('class="context-banner context-banner--review"', text)
        self.assertNotIn('href="/gouvernance', text)
        banner = self._banner_html(response.text)
        self.assertNotIn("token=local-secret&amp;token=local-secret", banner)

    def test_non_main_pages_keep_existing_no_banner_contract(self) -> None:
        client = self._client()

        response = client.get("/incidents")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('class="context-banner', response.text)


if __name__ == "__main__":
    unittest.main()
