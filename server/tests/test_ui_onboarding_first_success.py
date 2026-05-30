from __future__ import annotations

import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app


class UiOnboardingFirstSuccessTests(unittest.TestCase):
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

    def test_overview_surfaces_first_success_with_token_safe_targets(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/")
        self.assertEqual(forbidden.status_code, 403)

        response = client.get("/?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn("Premier succes conseille", text)
        self.assertIn("Creer une trace locale", text)
        self.assertIn("Rien n'est envoye automatiquement.", text)
        self.assertIn("Preuve ou source", text)
        self.assertIn("prochaine action", text.lower())
        self.assertIn("Prudence diffusion", text)
        self.assertIn("Trace gardee pour la passation", text)
        self.assertIn("Demander une piece ou relancer le syndic", text)
        self.assertIn("Traiter une priorite", text)
        self.assertIn("Ajouter ou rattacher un document", text)
        self.assertIn("Transmettre ou reprendre la memoire", text)
        self.assertIn('href="/demandes?token=local-secret#nouvelle-demande"', response.text)
        self.assertIn('href="/actions?priority=P1&amp;token=local-secret"', response.text)
        self.assertIn('href="/documents/ajouter?token=local-secret"', response.text)
        self.assertIn('href="/exports/passation?token=local-secret"', response.text)

        for forbidden_marker in ("C:\\", "file://", "raw/", "restricted/", "logs/", "private/"):
            with self.subTest(forbidden_marker=forbidden_marker):
                self.assertNotIn(forbidden_marker, response.text)


if __name__ == "__main__":
    unittest.main()
