from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.web.app import create_app


class UiRecetteModeTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self, *, recette_mode: bool, access_token: str | None = "local-secret"):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")
        return TestClient(create_app(self.instance, 2025, access_token=access_token, recette_mode=recette_mode))

    def test_recette_toolbar_is_absent_by_default(self) -> None:
        response = self._client(recette_mode=False).get("/?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("cs-recette-config", response.text)
        self.assertNotIn("Mode test actif", response.text)

    def test_recette_toolbar_is_present_when_enabled(self) -> None:
        response = self._client(recette_mode=True).get("/?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertIn("cs-recette-config", response.text)
        self.assertIn("/static/recette_mode.js", response.text)

    def test_recette_routes_require_token(self) -> None:
        client = self._client(recette_mode=True)

        self.assertEqual(client.get("/recette").status_code, 403)
        self.assertEqual(client.post("/recette/annotations", json={}).status_code, 403)
        self.assertEqual(client.get("/exports/recette-annotations.md").status_code, 403)

    def test_recette_post_and_exports_are_safe(self) -> None:
        client = self._client(recette_mode=True)
        response = client.post(
            "/recette/annotations?token=local-secret",
            json={
                "url": "/actions?token=local-secret&scope=syndic",
                "target_kind": "object",
                "target_label": "Nouvelle demande",
                "target_selector": "a",
                "target_text": "Nouvelle demande",
                "comment": "Le bouton est difficile a comprendre.",
                "severity": "important",
                "viewport_width": 1280,
                "viewport_height": 720,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        page = client.get("/recette?token=local-secret")
        json_export = client.get("/exports/recette-annotations.json?token=local-secret")
        md_export = client.get("/exports/recette-annotations.md?token=local-secret")

        self.assertEqual(page.status_code, 200)
        self.assertEqual(json_export.status_code, 200)
        self.assertEqual(md_export.status_code, 200)
        self.assertIn("Nouvelle demande", page.text)
        self.assertIn("DERIVED_RECETTE_QA", json_export.text)
        self.assertIn("Le bouton est difficile", md_export.text)
        for payload in (json_export.text, md_export.text):
            self.assertNotIn("local-secret", payload)
            self.assertNotIn("token", payload)
            self.assertNotIn("C:\\", payload)
            self.assertNotIn("file://", payload)

    def test_recette_routes_do_not_exist_when_disabled(self) -> None:
        client = self._client(recette_mode=False)

        self.assertEqual(client.get("/recette?token=local-secret").status_code, 404)


if __name__ == "__main__":
    unittest.main()
