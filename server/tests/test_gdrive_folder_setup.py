from __future__ import annotations

import json
import unittest

from coproscope.modules import gdrive_folder_setup


class GoogleDriveFolderSetupTests(unittest.TestCase):
    def test_create_private_sync_folder_redacts_google_identifiers(self) -> None:
        service = _FakeDriveService()

        result = gdrive_folder_setup.create_private_sync_folder(drive_service=service)
        serialized = json.dumps(result, ensure_ascii=True).lower()

        self.assertEqual(result["status"], "configured")
        self.assertEqual(result["folder_id"], "folder-secret-id")
        self.assertIn("Dossier Google pret", result["result_label"])
        self.assertNotIn("folder-secret-id", serialized.replace('"folder_id": "folder-secret-id"', ""))
        self.assertNotIn("owner@example", serialized)
        self.assertNotIn("token", serialized)
        self.assertEqual(service.files_api.created[0]["mimeType"], "application/vnd.google-apps.folder")

    def test_create_blocks_public_folder_before_configuration(self) -> None:
        service = _FakeDriveService(public=True)

        result = gdrive_folder_setup.create_private_sync_folder(drive_service=service)
        serialized = json.dumps(result, ensure_ascii=True).lower()

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["blocker_code"], "public_link")
        self.assertNotIn("folder-secret-id", serialized)
        self.assertNotIn("owner@example", serialized)

    def test_create_failure_returns_novice_safe_message(self) -> None:
        service = _FakeDriveService(fail_create=True)

        result = gdrive_folder_setup.create_private_sync_folder(drive_service=service)
        serialized = json.dumps(result, ensure_ascii=True).lower()

        self.assertEqual(result["status"], "blocked")
        self.assertIn("Verifiez la connexion Google", result["summary"])
        self.assertNotIn("traceback", serialized)


class _FakeRequest:
    def __init__(self, payload: dict[str, object], *, fail: bool = False) -> None:
        self.payload = payload
        self.fail = fail

    def execute(self) -> dict[str, object]:
        if self.fail:
            raise RuntimeError("network token failure")
        return self.payload


class _FakeDriveFiles:
    def __init__(self, *, public: bool, fail_create: bool) -> None:
        self.public = public
        self.fail_create = fail_create
        self.created: list[dict[str, object]] = []

    def create(self, *, body: dict[str, object], fields: str) -> _FakeRequest:
        self.created.append(body)
        return _FakeRequest({"id": "folder-secret-id", "name": body.get("name", ""), "mimeType": body.get("mimeType", "")}, fail=self.fail_create)

    def get(self, **kwargs: object) -> _FakeRequest:
        return _FakeRequest(
            {
                "mimeType": "application/vnd.google-apps.folder",
                "ownedByMe": True,
                "shared": self.public,
                "capabilities": {"canAddChildren": True, "canEdit": True, "canShare": True},
            }
        )


class _FakePermissions:
    def __init__(self, *, public: bool) -> None:
        self.public = public

    def list(self, **kwargs: object) -> _FakeRequest:
        rows = [{"type": "user", "role": "owner", "emailAddress": "owner@example.invalid"}]
        if self.public:
            rows.append({"type": "anyone", "role": "reader", "allowFileDiscovery": False})
        return _FakeRequest({"permissions": rows})


class _FakeDriveService:
    def __init__(self, *, public: bool = False, fail_create: bool = False) -> None:
        self.files_api = _FakeDriveFiles(public=public, fail_create=fail_create)
        self.permissions_api = _FakePermissions(public=public)

    def files(self) -> _FakeDriveFiles:
        return self.files_api

    def permissions(self) -> _FakePermissions:
        return self.permissions_api


if __name__ == "__main__":
    unittest.main()
