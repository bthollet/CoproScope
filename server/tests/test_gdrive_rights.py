from __future__ import annotations

import json
import unittest
from typing import Any

from coproscope.cli import build_parser
from coproscope.modules import gdrive_rights


class _FakeRequest:
    def __init__(self, payload: dict[str, object] | None = None, error: Exception | None = None) -> None:
        self.payload = payload or {}
        self.error = error

    def execute(self) -> dict[str, object]:
        if self.error:
            raise self.error
        return self.payload


class _FakeFiles:
    def __init__(self, metadata: dict[str, object] | None = None, error: Exception | None = None) -> None:
        self.metadata = metadata or {}
        self.error = error
        self.get_calls: list[dict[str, object]] = []

    def get(self, **kwargs: object) -> _FakeRequest:
        self.get_calls.append(kwargs)
        return _FakeRequest(self.metadata, self.error)


class _FakePermissions:
    def __init__(self, permissions: list[dict[str, object]] | None = None, error: Exception | None = None) -> None:
        self.permissions = permissions or []
        self.error = error
        self.list_calls: list[dict[str, object]] = []

    def list(self, **kwargs: object) -> _FakeRequest:
        self.list_calls.append(kwargs)
        return _FakeRequest({"permissions": self.permissions}, self.error)


class _FakeDriveService:
    def __init__(
        self,
        *,
        metadata: dict[str, object] | None = None,
        permissions: list[dict[str, object]] | None = None,
        files_error: Exception | None = None,
        permissions_error: Exception | None = None,
    ) -> None:
        self.files_api = _FakeFiles(metadata, files_error)
        self.permissions_api = _FakePermissions(permissions, permissions_error)

    def files(self) -> _FakeFiles:
        return self.files_api

    def permissions(self) -> _FakePermissions:
        return self.permissions_api


class GoogleDriveRightsTests(unittest.TestCase):
    def test_private_folder_rights_are_summarized_without_accounts_or_ids(self) -> None:
        service = _FakeDriveService(
            metadata=_metadata(shared=False, can_share=True),
            permissions=[
                {"id": "perm-owner-secret", "type": "user", "role": "owner", "emailAddress": "owner@example.com"},
            ],
        )

        result = gdrive_rights.inspect_drive_folder_rights(drive_service=service, folder_id="folder-secret")
        serialized = json.dumps(result, ensure_ascii=True).lower()

        self.assertEqual(result["status"], "inspected")
        self.assertEqual(result["sharing"]["status"], "prive")
        self.assertTrue(result["current_google_account"]["can_write_files"])
        self.assertTrue(result["sync_account_policy"]["google_account_required_for_api_sync"])
        self.assertFalse(result["sync_account_policy"]["gmail_address_required"])
        self.assertNotIn("folder-secret", serialized)
        self.assertNotIn("perm-owner", serialized)
        self.assertNotIn("owner@example", serialized)

    def test_shared_and_public_folder_flags_are_visible_without_identity_leaks(self) -> None:
        service = _FakeDriveService(
            metadata=_metadata(shared=True, can_share=False),
            permissions=[
                {"id": "perm-owner", "type": "user", "role": "owner", "emailAddress": "owner@example.com"},
                {"id": "perm-group", "type": "group", "role": "writer", "emailAddress": "group@example.com"},
                {"id": "perm-anyone", "type": "anyone", "role": "reader", "allowFileDiscovery": False},
            ],
        )

        result = gdrive_rights.inspect_drive_folder_rights(drive_service=service, folder_id="folder-secret")
        serialized = json.dumps(result, ensure_ascii=True).lower()

        self.assertEqual(result["sharing"]["status"], "lien_public")
        self.assertTrue(result["sharing"]["public_link_present"])
        self.assertEqual(result["sharing"]["type_counts"], {"anyone": 1, "group": 1, "user": 1})
        self.assertFalse(result["current_google_account"]["can_manage_sharing"])
        self.assertNotIn("group@example", serialized)
        self.assertNotIn("perm-", serialized)
        self.assertNotIn("folder-secret", serialized)

    def test_permission_list_failure_returns_limited_status_without_blocking_access(self) -> None:
        service = _FakeDriveService(
            metadata=_metadata(shared=True),
            permissions_error=RuntimeError("permission denied for secret folder-id"),
        )

        result = gdrive_rights.inspect_drive_folder_rights(drive_service=service, folder_id="folder-secret")
        serialized = json.dumps(result, ensure_ascii=True).lower()

        self.assertEqual(result["status"], "limited")
        self.assertEqual(result["sharing"]["status"], "droits_non_lisibles")
        self.assertFalse(result["sharing"]["permissions_readable"])
        self.assertTrue(result["current_google_account"]["can_write_files"])
        self.assertNotIn("permission denied", serialized)
        self.assertNotIn("folder-secret", serialized)

    def test_missing_folder_blocks_without_leaking_folder_id(self) -> None:
        service = _FakeDriveService(files_error=RuntimeError("not found folder-secret"))

        result = gdrive_rights.inspect_drive_folder_rights(drive_service=service, folder_id="folder-secret")
        serialized = json.dumps(result, ensure_ascii=True).lower()

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["blocker_code"], "folder_unavailable")
        self.assertNotIn("folder-secret", serialized)

    def test_sync_validation_blocks_public_domain_unreadable_and_no_write(self) -> None:
        public = _rights("lien_public", can_write=True, permissions_readable=True)
        domain = _rights("partage_domaine", can_write=True, permissions_readable=True)
        unreadable = _rights("droits_non_lisibles", can_write=True, permissions_readable=False)
        no_write = _rights("prive", can_write=False, permissions_readable=True)

        self.assertEqual(gdrive_rights.validate_drive_sync_rights(public)["blocker_code"], "public_link")
        self.assertEqual(gdrive_rights.validate_drive_sync_rights(domain)["blocker_code"], "domain_share")
        self.assertEqual(gdrive_rights.validate_drive_sync_rights(unreadable)["blocker_code"], "permissions_unreadable")
        self.assertEqual(gdrive_rights.validate_drive_sync_rights(no_write)["blocker_code"], "missing_write_access")

    def test_sync_validation_allows_private_and_nominal_shared_folders(self) -> None:
        private = gdrive_rights.validate_drive_sync_rights(_rights("prive", can_write=True, permissions_readable=True))
        nominal = gdrive_rights.validate_drive_sync_rights(_rights("partage_nominal", can_write=True, permissions_readable=True))

        self.assertEqual(private["status"], "ok")
        self.assertEqual(nominal["status"], "ok")
        self.assertIn("autorisee", str(nominal["summary"]))

    def test_cli_exposes_folder_rights(self) -> None:
        args = build_parser().parse_args(
            [
                "drive",
                "folder-rights",
                "--folder-id",
                "folder-secret",
                "--token-path",
                "token.json",
            ]
        )

        self.assertEqual(args.drive_command, "folder-rights")
        self.assertEqual(args.folder_id, "folder-secret")


def _metadata(*, shared: bool, can_share: bool = True) -> dict[str, Any]:
    return {
        "id": "folder-secret",
        "name": "CoproScope test folder",
        "mimeType": gdrive_rights.FOLDER_MIME_TYPE,
        "ownedByMe": True,
        "shared": shared,
        "capabilities": {"canAddChildren": True, "canEdit": True, "canShare": can_share},
    }


def _rights(share_status: str, *, can_write: bool, permissions_readable: bool) -> dict[str, object]:
    return {
        "status": "inspected" if permissions_readable else "limited",
        "folder": {"is_folder": True, "folder_id_present": True, "id_disclosure": "redacted"},
        "current_google_account": {"can_write_files": can_write, "can_manage_sharing": True},
        "sharing": {
            "status": share_status,
            "permissions_readable": permissions_readable,
            "permission_count": 1,
            "public_link_present": share_status == "lien_public",
            "domain_share_present": share_status == "partage_domaine",
        },
        "payload_disclosure": "counts_only",
        "path_disclosure": "none",
    }


if __name__ == "__main__":
    unittest.main()
