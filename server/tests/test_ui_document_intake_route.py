from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app


class UiDocumentIntakeRouteTests(unittest.TestCase):
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

    def test_document_intake_route_renders_preparation_view_without_configured_token(self) -> None:
        response = self._client().get("/documents/ajouter")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Ajout de document", response.text)
        self.assertIn("Documents a ajouter", response.text)
        self.assertIn("PV assemblee generale 2025", response.text)
        self.assertIn("Devis travaux a biffer", response.text)
        self.assertIn("Contrat de rattachement", response.text)
        self.assertIn("piece -&gt; point -&gt; action -&gt; preuve", response.text)
        self.assertIn('href="/documents/ajouter"', response.text)
        self.assertIn(
            'aria-label="Ajouter un document, preparation novice sans upload reel"',
            response.text,
        )
        self.assertIn("Deposer un document depuis ce poste", response.text)
        self.assertIn('action="/depot"', response.text)
        self.assertIn('method="post"', response.text.lower())
        self.assertIn('type="file"', response.text.lower())
        self.assertIn('href="/depot?intent=document"', response.text)

    def test_document_intake_route_uses_existing_token_guard_and_nav_token(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/documents/ajouter")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Documents a ajouter", forbidden.text)

        response = client.get("/documents/ajouter?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn("Ajout de document", response.text)
        self.assertIn("Documents a ajouter", response.text)
        self.assertIn('href="/documents/ajouter?token=local-secret"', response.text)
        self.assertIn('action="/depot?token=local-secret"', response.text)
        self.assertIn('href="/depot?intent=document&amp;token=local-secret"', response.text)
        self.assertIn("<span>Ajouter un document</span>", response.text)
        self.assertIn('aria-current="page"', response.text)

        fresh_client = self._client(access_token="local-secret")
        header_response = fresh_client.get(
            "/documents/ajouter",
            headers={"x-coproscope-token": "local-secret"},
        )
        self.assertEqual(header_response.status_code, 200)
        self.assertIn("Documents a ajouter", header_response.text)

    def test_document_intake_route_does_not_shadow_document_detail_route(self) -> None:
        response = self._client(access_token="local-secret").get("/documents/inconnu?token=local-secret")

        self.assertEqual(response.status_code, 404)
        self.assertIn("Document introuvable", response.text)


if __name__ == "__main__":
    unittest.main()
