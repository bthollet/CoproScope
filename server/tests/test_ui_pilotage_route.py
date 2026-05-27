from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.web.app import create_app


class UiPilotageRouteTests(unittest.TestCase):
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

    def test_pilotage_route_renders_template_without_configured_token(self) -> None:
        response = self._client().get("/pilotage")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Pilotage des indicateurs", response.text)
        self.assertIn("Taux documents OCR requis", response.text)
        self.assertIn("Registre KPI local", response.text)
        self.assertIn('href="/pilotage"', response.text)
        self.assertIn(">A surveiller</span>", response.text)
        self.assertIn("Preuve ou source", response.text)
        self.assertIn("Confiance", response.text)
        self.assertIn("Prochaine action", response.text)
        self.assertIn("Ouvrir les decisions a suivre", response.text)

    def test_pilotage_route_uses_existing_token_guard_and_nav_token(self) -> None:
        client = self._client(access_token="local-secret")

        self.assertEqual(client.get("/pilotage").status_code, 403)

        response = client.get("/pilotage?token=local-secret")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Pilotage des indicateurs", response.text)
        self.assertIn('href="/pilotage?token=local-secret"', response.text)
        self.assertIn('href="/actions?scope=decisions&amp;token=local-secret"', response.text)
        self.assertIn('aria-label="Indicateurs, quoi surveiller en priorite"', response.text)
        self.assertIn('aria-current="page"', response.text)


if __name__ == "__main__":
    unittest.main()
