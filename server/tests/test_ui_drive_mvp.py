from __future__ import annotations

import re
import shutil
import tempfile
import unittest
import json
import os
import time
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
        self.assertIn("Ce poste seulement", visible)
        self.assertIn("A configurer", visible)
        self.assertIn("Synchronisation de ce poste", visible)
        self.assertIn("Tester la preparation", visible)
        self.assertIn("Tester la recuperation", visible)
        self.assertIn("Synchroniser maintenant", visible)
        self.assertIn("Surveiller maintenant", visible)
        self.assertIn("Activer la surveillance", visible)
        self.assertTrue("Preparer ce poste" in visible or "Poste prepare" in visible)
        self.assertIn("Creer le dossier Google chiffre", visible)
        self.assertTrue(
            "Choisissez d'abord le dossier Google Drive chiffre" in visible
            or "Choisissez maintenant le dossier Google Drive" in visible
        )
        self.assertIn("Affichage limite a cet ordinateur", visible)
        self.assertIn("Prochaine action", visible)
        self.assertIn("Frontiere de securite", visible)
        self.assertIn("Code d'acces coffre", visible)
        self.assertIn("Creer un code", visible)
        self.assertIn("Importer le code", visible)
        self.assertIn("Paquets chiffres", visible)
        self.assertIn('href="/coffre/partage?token=drive-mvp-local"', response.text)
        self.assertIn('action="/coffre/drive/publier-test?token=drive-mvp-local"', response.text)
        self.assertIn('action="/coffre/drive/recuperer-test?token=drive-mvp-local"', response.text)
        self.assertIn('action="/coffre/drive/code-acces?token=drive-mvp-local"', response.text)
        self.assertIn('action="/coffre/drive/importer-code?token=drive-mvp-local"', response.text)
        self.assertNotIn('action="/coffre/drive/synchroniser?token=drive-mvp-local"', response.text)
        self.assertNotIn('action="/coffre/drive/surveiller?token=drive-mvp-local"', response.text)
        self.assertNotIn('action="/coffre/drive/surveillance/activer?token=drive-mvp-local"', response.text)
        self.assertIn('data-testid="drive-sync-status"', response.text)
        self.assertNotIn("CSP-DRIVE-KEY-V1", response.text)
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

    def test_drive_key_code_can_be_created_and_imported_without_drive_storage(self) -> None:
        client = self._client()

        exported = client.post("/coffre/drive/code-acces?token=drive-mvp-local", follow_redirects=False)
        self.assertEqual(exported.status_code, 303)
        export_page = client.get(exported.headers["location"])
        code_match = re.search(r"(CSP-DRIVE-KEY-V1\.[A-Za-z0-9_-]+\.[0-9a-f]{16})", export_page.text)
        self.assertIsNotNone(code_match)
        code = code_match.group(1) if code_match else ""
        export_visible = _visible_text(unescape(export_page.text))
        self.assertIn("Code pret", export_visible)
        self.assertIn("Ne placez pas ce code dans Drive", export_visible)

        imported = client.post(
            "/coffre/drive/importer-code?token=drive-mvp-local",
            data={"secret_code": code},
            follow_redirects=False,
        )
        self.assertEqual(imported.status_code, 303)
        import_page = client.get(imported.headers["location"])
        import_visible = _visible_text(unescape(import_page.text))

        self.assertIn("Code importe", import_visible)
        self.assertNotIn(code, import_page.text)
        self.assertNotIn(str(self.instance_root), import_page.text)

    def test_drive_prepare_local_poste_creates_profile_without_leaking_paths(self) -> None:
        old_profile = os.environ.get("COPROSCOPE_DRIVE_PROFILE_ROOT")
        old_local = os.environ.get("COPROSCOPE_DRIVE_LOCAL_ROOT")
        local_root = Path(self.tempdir.name) / "local-drive-setup"
        profile_root = Path(self.tempdir.name) / "profile-drive-setup"
        os.environ["COPROSCOPE_DRIVE_PROFILE_ROOT"] = str(profile_root)
        os.environ["COPROSCOPE_DRIVE_LOCAL_ROOT"] = str(local_root)
        try:
            client = self._client()

            prepared = client.post("/coffre/drive/preparer-poste?token=drive-mvp-local", follow_redirects=False)
            self.assertEqual(prepared.status_code, 303)
            result_page = client.get(prepared.headers["location"])
            visible = _visible_text(unescape(result_page.text))
            serialized = result_page.text

            self.assertIn("Preparation locale de ce poste", visible)
            self.assertIn("Poste prepare", visible)
            self.assertIn("Google reste a connecter", visible)
            self.assertIn("Le dossier local chiffre est pret", visible)
            self.assertTrue((local_root / "synthetic-copro" / "sync_chiffre" / "packages").is_dir())
            self.assertTrue((local_root / "synthetic-copro" / "sync_chiffre" / "devices").is_dir())
            self.assertTrue((profile_root / "config" / "drive_profile.json").is_file())
            self.assertNotIn(str(local_root), serialized)
            self.assertNotIn(str(profile_root), serialized)
            self.assertNotIn("token_drive_file", serialized)
            self.assertNotIn("client_secret", serialized)
        finally:
            _restore_env("COPROSCOPE_DRIVE_PROFILE_ROOT", old_profile)
            _restore_env("COPROSCOPE_DRIVE_LOCAL_ROOT", old_local)

    def test_drive_google_folder_can_be_created_after_local_setup_and_google_connection(self) -> None:
        old_profile = os.environ.get("COPROSCOPE_DRIVE_PROFILE_ROOT")
        old_local = os.environ.get("COPROSCOPE_DRIVE_LOCAL_ROOT")
        local_root = Path(self.tempdir.name) / "local-google-folder"
        profile_root = Path(self.tempdir.name) / "profile-google-folder"
        os.environ["COPROSCOPE_DRIVE_PROFILE_ROOT"] = str(profile_root)
        os.environ["COPROSCOPE_DRIVE_LOCAL_ROOT"] = str(local_root)
        try:
            app = create_app(self.instance, 2025, access_token="drive-mvp-local")
            service = _FakeDriveService()
            app.state.drive_service_factory = lambda token_path=None: service
            try:
                from fastapi.testclient import TestClient
            except ImportError as exc:
                self.skipTest(f"FastAPI test client unavailable: {exc}")
            client = TestClient(app)

            prepared = client.post("/coffre/drive/preparer-poste?token=drive-mvp-local", follow_redirects=False)
            self.assertEqual(prepared.status_code, 303)
            oauth_dir = profile_root / "oauth" / "synthetic-copro"
            oauth_dir.mkdir(parents=True, exist_ok=True)
            (oauth_dir / "client_secret.json").write_text("{}", encoding="utf-8")
            (oauth_dir / "token_drive_file.json").write_text(
                json.dumps({"scopes": ["https://www.googleapis.com/auth/drive.file"]}),
                encoding="utf-8",
            )

            ready_page = client.get("/coffre/drive?token=drive-mvp-local")
            self.assertIn('action="/coffre/drive/dossier-google/creer?token=drive-mvp-local"', ready_page.text)
            created = client.post("/coffre/drive/dossier-google/creer?token=drive-mvp-local", follow_redirects=False)
            self.assertEqual(created.status_code, 303)
            result_page = client.get(created.headers["location"])
            visible = _visible_text(unescape(result_page.text))
            serialized = result_page.text
            profile = json.loads((profile_root / "config" / "drive_profile.json").read_text(encoding="utf-8"))

            self.assertIn("Dossier Google chiffre", visible)
            self.assertIn("Dossier Google pret", visible)
            self.assertIn("Synchroniser maintenant", visible)
            self.assertEqual(profile["instances"]["synthetic-copro"]["folder_id"], "fake-google-folder-id-secret")
            self.assertNotIn("fake-google-folder-id-secret", serialized)
            self.assertNotIn(str(local_root), serialized)
            self.assertNotIn(str(profile_root), serialized)
            self.assertNotIn("token_drive_file", serialized)
            self.assertNotIn("client_secret", serialized)
            self.assertEqual(service.files_api.created[0]["mimeType"], "application/vnd.google-apps.folder")
        finally:
            _restore_env("COPROSCOPE_DRIVE_PROFILE_ROOT", old_profile)
            _restore_env("COPROSCOPE_DRIVE_LOCAL_ROOT", old_local)

    def test_drive_real_sync_route_uses_configured_drive_without_leaking_ids_or_paths(self) -> None:
        sync = self.instance_root / "staging" / "drive-real-sync"
        state = self.instance_root / "staging" / "drive-real-state"
        oauth = self.instance_root / "staging" / "oauth"
        sync.mkdir(parents=True)
        state.mkdir(parents=True)
        oauth.mkdir(parents=True)
        client_secret = oauth / "client.json"
        token = oauth / "token.json"
        client_secret.write_text("{}", encoding="utf-8")
        token.write_text(json.dumps({"scopes": ["https://www.googleapis.com/auth/drive.file"]}), encoding="utf-8")
        self.instance.payload.setdefault("settings", {})["drive_sync"] = {
            "folder_id": "fake-google-folder-id-secret",
            "sync_root": str(sync),
            "local_state_root": str(state),
            "client_secrets_path": str(client_secret),
            "token_path": str(token),
        }
        service = _FakeDriveService()
        app = create_app(self.instance, 2025, access_token="drive-mvp-local")
        app.state.drive_service_factory = lambda token_path=None: service
        try:
            from fastapi.testclient import TestClient
        except ImportError as exc:
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        client = TestClient(app)

        page = client.get("/coffre/drive?token=drive-mvp-local")
        self.assertIn('action="/coffre/drive/synchroniser?token=drive-mvp-local"', page.text)
        self.assertIn('action="/coffre/drive/surveiller?token=drive-mvp-local"', page.text)
        self.assertIn('action="/coffre/drive/surveillance/activer?token=drive-mvp-local"', page.text)
        synced = client.post("/coffre/drive/synchroniser?token=drive-mvp-local", follow_redirects=False)
        self.assertEqual(synced.status_code, 303)
        result_page = client.get(synced.headers["location"])
        visible = _visible_text(unescape(result_page.text))
        serialized = result_page.text

        self.assertIn("Synchronisation terminee", visible)
        self.assertIn("Dossier Google configure", visible)
        self.assertIn("Drive pret", visible)
        self.assertEqual(len(service.files_api.created), 1)
        self.assertNotIn("fake-google-folder-id-secret", serialized)
        self.assertNotIn(str(sync), serialized)
        self.assertNotIn(str(token), serialized)

    def test_drive_watch_route_runs_one_supervision_pass_from_ui(self) -> None:
        sync = self.instance_root / "staging" / "drive-watch-sync"
        state = self.instance_root / "staging" / "drive-watch-state"
        oauth = self.instance_root / "staging" / "oauth-watch"
        sync.mkdir(parents=True)
        state.mkdir(parents=True)
        oauth.mkdir(parents=True)
        client_secret = oauth / "client.json"
        token = oauth / "token.json"
        client_secret.write_text("{}", encoding="utf-8")
        token.write_text(json.dumps({"scopes": ["https://www.googleapis.com/auth/drive.file"]}), encoding="utf-8")
        self.instance.payload.setdefault("settings", {})["drive_sync"] = {
            "folder_id": "fake-google-folder-id-secret",
            "sync_root": str(sync),
            "local_state_root": str(state),
            "client_secrets_path": str(client_secret),
            "token_path": str(token),
        }
        service = _FakeDriveService()
        app = create_app(self.instance, 2025, access_token="drive-mvp-local")
        app.state.drive_service_factory = lambda token_path=None: service
        try:
            from fastapi.testclient import TestClient
        except ImportError as exc:
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        client = TestClient(app)

        watched = client.post("/coffre/drive/surveiller?token=drive-mvp-local", follow_redirects=False)
        self.assertEqual(watched.status_code, 303)
        result_page = client.get(watched.headers["location"])
        visible = _visible_text(unescape(result_page.text))
        serialized = result_page.text

        self.assertIn("Surveillance de ce poste", visible)
        self.assertIn("Surveillance terminee", visible)
        self.assertIn("Affichage limite a ce poste", visible)
        self.assertEqual(len(service.files_api.created), 1)
        self.assertNotIn("fake-google-folder-id-secret", serialized)
        self.assertNotIn(str(sync), serialized)
        self.assertNotIn(str(token), serialized)

    def test_drive_watch_service_starts_and_stops_from_ui(self) -> None:
        sync = self.instance_root / "staging" / "drive-watch-service-sync"
        state = self.instance_root / "staging" / "drive-watch-service-state"
        oauth = self.instance_root / "staging" / "oauth-watch-service"
        sync.mkdir(parents=True)
        state.mkdir(parents=True)
        oauth.mkdir(parents=True)
        client_secret = oauth / "client.json"
        token = oauth / "token.json"
        client_secret.write_text("{}", encoding="utf-8")
        token.write_text(json.dumps({"scopes": ["https://www.googleapis.com/auth/drive.file"]}), encoding="utf-8")
        self.instance.payload.setdefault("settings", {})["drive_sync"] = {
            "folder_id": "fake-google-folder-id-secret",
            "sync_root": str(sync),
            "local_state_root": str(state),
            "client_secrets_path": str(client_secret),
            "token_path": str(token),
        }
        service = _FakeDriveService()
        app = create_app(self.instance, 2025, access_token="drive-mvp-local")
        app.state.drive_service_factory = lambda token_path=None: service
        app.state.drive_watch_interval_seconds = 0.1
        try:
            from fastapi.testclient import TestClient
        except ImportError as exc:
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        client = TestClient(app)

        started = client.post("/coffre/drive/surveillance/activer?token=drive-mvp-local", follow_redirects=False)
        self.assertEqual(started.status_code, 303)
        self.assertTrue(_wait_for_watch_cycles(app, 1))
        running_page = client.get(started.headers["location"])
        running_visible = _visible_text(unescape(running_page.text))

        self.assertIn("Surveillance automatique", running_visible)
        self.assertIn("Arreter la surveillance", running_visible)
        self.assertIn("L'etat affiche ne decrit que cet ordinateur", running_visible)

        stopped = client.post("/coffre/drive/surveillance/arreter?token=drive-mvp-local", follow_redirects=False)
        self.assertEqual(stopped.status_code, 303)
        stopped_page = client.get(stopped.headers["location"])
        stopped_visible = _visible_text(unescape(stopped_page.text))
        serialized = stopped_page.text

        self.assertIn("Surveillance automatique arretee", stopped_visible)
        self.assertIn("Activer la surveillance", stopped_visible)
        self.assertEqual(len(service.files_api.created), 1)
        self.assertNotIn("fake-google-folder-id-secret", serialized)
        self.assertNotIn(str(sync), serialized)
        self.assertNotIn(str(token), serialized)

    def test_drive_real_sync_blocks_public_google_folder_without_upload(self) -> None:
        sync = self.instance_root / "staging" / "drive-real-sync-public"
        state = self.instance_root / "staging" / "drive-real-state-public"
        oauth = self.instance_root / "staging" / "oauth-public"
        sync.mkdir(parents=True)
        state.mkdir(parents=True)
        oauth.mkdir(parents=True)
        client_secret = oauth / "client.json"
        token = oauth / "token.json"
        client_secret.write_text("{}", encoding="utf-8")
        token.write_text(json.dumps({"scopes": ["https://www.googleapis.com/auth/drive.file"]}), encoding="utf-8")
        self.instance.payload.setdefault("settings", {})["drive_sync"] = {
            "folder_id": "fake-google-folder-id-secret",
            "sync_root": str(sync),
            "local_state_root": str(state),
            "client_secrets_path": str(client_secret),
            "token_path": str(token),
        }
        service = _FakeDriveService(public=True)
        app = create_app(self.instance, 2025, access_token="drive-mvp-local")
        app.state.drive_service_factory = lambda token_path=None: service
        try:
            from fastapi.testclient import TestClient
        except ImportError as exc:
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        client = TestClient(app)

        synced = client.post("/coffre/drive/synchroniser?token=drive-mvp-local", follow_redirects=False)
        self.assertEqual(synced.status_code, 303)
        result_page = client.get(synced.headers["location"])
        visible = _visible_text(unescape(result_page.text))
        serialized = result_page.text

        self.assertIn("Droits Google a corriger", visible)
        self.assertIn("Dossier Google partage par lien public", visible)
        self.assertEqual(len(service.files_api.created), 0)
        self.assertNotIn("fake-google-folder-id-secret", serialized)
        self.assertNotIn(str(sync), serialized)
        self.assertNotIn(str(token), serialized)

    def test_drive_css_is_imported_by_manifest(self) -> None:
        static_root = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static"
        manifest = (static_root / "styles.css").read_text(encoding="utf-8")
        css = (static_root / "styles_part_28.css").read_text(encoding="utf-8")

        self.assertIn("styles_part_28.css", manifest)
        self.assertIn(".drive-page", css)
        self.assertIn(".drive-status-dock", css)
        self.assertIn(".drive-status-dock--ok", css)
        self.assertIn(".drive-status-dock--error", css)
        self.assertIn("right: 18px", css)
        self.assertIn("overflow-wrap: anywhere", css)
        self.assertIn("box-sizing: border-box", css)
        self.assertIn("max-width: 100%", css)
        self.assertNotIn("left: calc(276px", css)
        self.assertIn("@media (max-width: 760px)", css)


def _visible_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return " ".join(without_tags.split())


def _wait_for_watch_cycles(app: object, expected: int, *, timeout: float = 2.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        service = getattr(getattr(app, "state", object()), "drive_watch_service", None)
        if service is not None:
            snapshot = service.snapshot()
            if int(snapshot.get("cycles_completed") or 0) >= expected:
                return True
        time.sleep(0.02)
    return False


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


class _FakeRequest:
    def __init__(self, payload: dict[str, object] | None = None) -> None:
        self.payload = payload or {}

    def execute(self) -> dict[str, object]:
        return self.payload


class _FakeCreateRequest:
    def __init__(self, created: list[dict[str, object]], body: dict[str, object]) -> None:
        self.created = created
        self.body = body

    def execute(self) -> dict[str, object]:
        item = {"id": f"fake-file-{len(self.created) + 1}", "name": self.body.get("name", ""), "size": "1"}
        self.created.append(item)
        return item


class _FakeDriveFiles:
    def __init__(self, *, public: bool = False) -> None:
        self.created: list[dict[str, object]] = []
        self.public = public

    def get(self, **kwargs: object) -> _FakeRequest:
        return _FakeRequest(
            {
                "mimeType": "application/vnd.google-apps.folder",
                "ownedByMe": True,
                "shared": self.public,
                "capabilities": {"canAddChildren": True, "canEdit": True, "canShare": True},
            }
        )

    def list(self, **kwargs: object) -> _FakeRequest:
        return _FakeRequest()

    def get_media(self, **kwargs: object) -> _FakeRequest:
        return _FakeRequest()

    def create(self, *, body: dict[str, object], media_body: object | None = None, fields: str) -> _FakeCreateRequest | _FakeRequest:
        if body.get("mimeType") == "application/vnd.google-apps.folder":
            self.created.append(body)
            return _FakeRequest({"id": "fake-google-folder-id-secret", "name": body.get("name", ""), "mimeType": body.get("mimeType", "")})
        return _FakeCreateRequest(self.created, body)


class _FakeDriveService:
    def __init__(self, *, public: bool = False) -> None:
        self.files_api = _FakeDriveFiles(public=public)
        self.permissions_api = _FakePermissions(public=public)

    def files(self) -> _FakeDriveFiles:
        return self.files_api

    def permissions(self) -> "_FakePermissions":
        return self.permissions_api


class _FakePermissions:
    def __init__(self, *, public: bool = False) -> None:
        self.public = public

    def list(self, **kwargs: object) -> _FakeRequest:
        rows = [{"type": "user", "role": "owner", "emailAddress": "owner@example.invalid"}]
        if self.public:
            rows.append({"type": "anyone", "role": "reader", "allowFileDiscovery": False})
        return _FakeRequest({"permissions": rows})


if __name__ == "__main__":
    unittest.main()
