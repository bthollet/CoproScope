from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app


FORBIDDEN_VISIBLE = (
    "OAuth",
    "scope",
    "client_secret",
    "refresh_token",
    "token_drive_file",
    "drive.file",
    "file://",
    "C:\\",
    "raw",
    "restricted",
    "private",
    "Drive OK",
    "Dossier synchronise",
    "MVP",
    "local-first",
    "couche Google",
    "index minimal",
    "cles publiques",
    "API Google",
    "Controle local expurge",
    "Publier en demonstration locale",
    "Recuperer en demonstration locale",
    "Poste A",
    "Poste B",
    "Secret local",
    "autres postes",
    "autres ordinateurs",
    "autres coproprietaires",
)


class UiDriveMvpTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self):
        try:
            from fastapi.testclient import TestClient
        except ImportError as exc:
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        return TestClient(create_app(self.instance, 2025, access_token="drive-mvp-local"))

    def test_drive_route_uses_current_shell_and_drive_css(self) -> None:
        client = self._client()

        forbidden = client.get("/coffre/drive")
        self.assertEqual(forbidden.status_code, 403)

        response = client.get("/coffre/drive?token=drive-mvp-local")
        text = unescape(response.text)
        visible = _visible_text(text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn("styles.css?v=20260530-drive-convergence", response.text)
        self.assertIn("Drive chiffre", visible)
        self.assertIn("Drive n'est pas encore relie", visible)
        self.assertIn("Ce poste seulement", visible)
        self.assertIn("Etat Drive", visible)
        self.assertIn("Test sans envoi lisible", visible)
        self.assertIn("Tester la preparation", visible)
        self.assertIn("Tester la recuperation", visible)
        self.assertIn("Affichage limite a cet ordinateur", visible)
        self.assertIn("Prochaine action", visible)
        self.assertIn('href="/coffre/partage?token=drive-mvp-local"', response.text)
        self.assertIn('action="/coffre/drive/publier-test?token=drive-mvp-local"', response.text)
        self.assertIn('action="/coffre/drive/recuperer-test?token=drive-mvp-local"', response.text)
        self.assertIn('data-testid="drive-sync-status"', response.text)
        for marker in FORBIDDEN_VISIBLE:
            self.assertNotIn(marker, visible)

    def test_drive_publish_recover_demo_is_clickable_and_local_only(self) -> None:
        client = self._client()

        published = client.post("/coffre/drive/publier-test?token=drive-mvp-local", follow_redirects=False)
        self.assertEqual(published.status_code, 303)
        publish_page = client.get(published.headers["location"])
        publish_visible = _visible_text(unescape(publish_page.text))
        self.assertIn("Preparation test terminee", publish_visible)
        self.assertIn("Changements chiffres deposes en demonstration locale", publish_visible)
        self.assertIn("Partage Google non verifie par ce test", publish_visible)

        recovered = client.post("/coffre/drive/recuperer-test?token=drive-mvp-local", follow_redirects=False)
        self.assertEqual(recovered.status_code, 303)
        recover_page = client.get(recovered.headers["location"])
        recover_visible = _visible_text(unescape(recover_page.text))
        self.assertIn("Recuperation test terminee", recover_visible)
        self.assertIn("Changements verifies et recuperes sur ce poste", recover_visible)
        self.assertIn("L'etat affiche est limite a cet ordinateur", recover_visible)
        for marker in FORBIDDEN_VISIBLE:
            self.assertNotIn(marker, recover_visible)

    def test_drive_css_is_imported_by_manifest(self) -> None:
        static_root = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static"
        manifest = (static_root / "styles.css").read_text(encoding="utf-8")
        css = (static_root / "styles_part_28.css").read_text(encoding="utf-8")

        self.assertIn("styles_part_28.css", manifest)
        self.assertIn(".drive-intro", css)
        self.assertIn(".drive-sync-bar", css)
        self.assertIn(".drive-sync-bar--ok", css)
        self.assertIn(".drive-sync-bar--error", css)
        self.assertIn("right: 18px", css)
        self.assertNotIn("left: calc(276px", css)
        self.assertIn("@media (max-width: 760px)", css)


def _visible_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return " ".join(without_tags.split())


if __name__ == "__main__":
    unittest.main()
