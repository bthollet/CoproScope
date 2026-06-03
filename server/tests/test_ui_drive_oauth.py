from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.web.app import create_app


FORBIDDEN_VISIBLE = (
    "OAuth",
    "scope",
    "client_secret",
    "token_drive_file",
    "drive.file",
    "file://",
    "C:\\",
    "raw",
    "restricted",
    "private",
    "traceback",
)


class UiDriveOAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)
        self.old_profile = os.environ.get("COPROSCOPE_DRIVE_PROFILE_ROOT")
        self.old_local = os.environ.get("COPROSCOPE_DRIVE_LOCAL_ROOT")
        self.profile_root = Path(self.tempdir.name) / "profile-google-connect"
        self.local_root = Path(self.tempdir.name) / "local-google-connect"
        os.environ["COPROSCOPE_DRIVE_PROFILE_ROOT"] = str(self.profile_root)
        os.environ["COPROSCOPE_DRIVE_LOCAL_ROOT"] = str(self.local_root)

    def tearDown(self) -> None:
        _restore_env("COPROSCOPE_DRIVE_PROFILE_ROOT", self.old_profile)
        _restore_env("COPROSCOPE_DRIVE_LOCAL_ROOT", self.old_local)
        self.tempdir.cleanup()

    def _client(self, app: object | None = None):
        try:
            from fastapi.testclient import TestClient
        except ImportError as exc:
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        return TestClient(app or create_app(self.instance, 2025, access_token="drive-mvp-local"))

    def test_connect_google_button_is_clickable_after_local_setup_and_blocks_cleanly_without_internal_file(self) -> None:
        client = self._client()

        prepared = client.post("/coffre/drive/preparer-poste?token=drive-mvp-local", follow_redirects=False)
        self.assertEqual(prepared.status_code, 303)
        page = client.get(prepared.headers["location"])
        visible = _visible_text(unescape(page.text))

        self.assertIn("Connecter Google", visible)
        self.assertIn('action="/coffre/drive/connecter-google?token=drive-mvp-local"', page.text)

        connected = client.post("/coffre/drive/connecter-google?token=drive-mvp-local", follow_redirects=False)
        self.assertEqual(connected.status_code, 303)
        result_page = client.get(connected.headers["location"])
        result_visible = _visible_text(unescape(result_page.text))

        self.assertIn("Connexion Google", result_visible)
        self.assertIn("Action requise", result_visible)
        self.assertIn("Connexion Google non disponible", result_visible)
        for marker in FORBIDDEN_VISIBLE:
            self.assertNotIn(marker, result_visible)
            self.assertNotIn(marker, result_page.text)
        self.assertNotIn(str(self.profile_root), result_page.text)
        self.assertNotIn(str(self.local_root), result_page.text)

    def test_connect_google_route_uses_background_flow_and_enables_google_folder(self) -> None:
        app = create_app(self.instance, 2025, access_token="drive-mvp-local")
        token_path = self.profile_root / "oauth" / "synthetic-copro" / "token_drive_file.json"

        def fake_flow(**kwargs: object) -> dict[str, object]:
            token_path.parent.mkdir(parents=True, exist_ok=True)
            token_path.write_text(json.dumps({"scopes": ["https://www.googleapis.com/auth/drive.file"]}), encoding="utf-8")
            return {"status": "ok", "token_path": str(token_path)}

        app.state.drive_oauth_flow = fake_flow
        client = self._client(app)

        prepared = client.post("/coffre/drive/preparer-poste?token=drive-mvp-local", follow_redirects=False)
        self.assertEqual(prepared.status_code, 303)
        client_path = self.profile_root / "oauth" / "synthetic-copro" / "client_secret.json"
        client_path.parent.mkdir(parents=True, exist_ok=True)
        client_path.write_text("{}", encoding="utf-8")

        connected = client.post("/coffre/drive/connecter-google?token=drive-mvp-local", follow_redirects=False)
        self.assertEqual(connected.status_code, 303)
        self.assertTrue(_wait_until(lambda: token_path.exists()))
        result_page = client.get("/coffre/drive?token=drive-mvp-local")
        visible = _visible_text(unescape(result_page.text))

        self.assertIn("Compte Google pret", visible)
        self.assertIn("Google connecte", visible)
        self.assertIn('action="/coffre/drive/dossier-google/creer?token=drive-mvp-local"', result_page.text)
        for marker in FORBIDDEN_VISIBLE:
            self.assertNotIn(marker, visible)
            self.assertNotIn(marker, result_page.text)
        self.assertNotIn(str(self.profile_root), result_page.text)
        self.assertNotIn(str(self.local_root), result_page.text)

    def test_connect_google_route_requires_ui_token(self) -> None:
        client = self._client()

        response = client.post("/coffre/drive/connecter-google")

        self.assertEqual(response.status_code, 403)


def _visible_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return " ".join(without_tags.split())


def _wait_until(predicate: object, *, timeout: float = 1.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():  # type: ignore[operator]
            return True
        time.sleep(0.02)
    return False


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


if __name__ == "__main__":
    unittest.main()
