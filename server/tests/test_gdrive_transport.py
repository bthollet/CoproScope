from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from coproscope.cli import build_parser
from coproscope.modules import drive_instance_sync, gdrive_transport, gdriveops


class _FakeRequest:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def execute(self) -> dict[str, object]:
        return self.payload


class _FakeMediaRequest:
    def __init__(self, content: bytes) -> None:
        self.content = content


class _FakeDriveFiles:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}
        self.created: list[dict[str, object]] = []
        self.list_calls: list[dict[str, object]] = []
        self.downloaded_ids: list[str] = []

    def list(self, **kwargs: object) -> _FakeRequest:
        self.list_calls.append(kwargs)
        return _FakeRequest({"files": [record["metadata"] for record in self.records.values()]})

    def create(self, *, body: dict[str, object], fields: str, media_body: object | None = None) -> _FakeRequest:
        self.created.append(body)
        if body.get("mimeType") == "application/vnd.google-apps.folder":
            return _FakeRequest({"id": "folder-id", "name": body["name"]})
        file_id = f"file-{len(self.records) + 1}"
        content = bytes(media_body.get("content", b"")) if isinstance(media_body, dict) else b""
        metadata = {
            "id": file_id,
            "name": body["name"],
            "mimeType": body["mimeType"],
            "size": str(len(content)),
            "modifiedTime": f"2026-05-30T20:{len(self.records):02d}:00Z",
            "appProperties": dict(body.get("appProperties") or {}),
        }
        self.records[file_id] = {"metadata": metadata, "content": content}
        return _FakeRequest({"id": file_id, "name": body["name"], "mimeType": body["mimeType"], "size": str(len(content))})

    def get_media(self, *, fileId: str) -> _FakeMediaRequest:
        self.downloaded_ids.append(fileId)
        return _FakeMediaRequest(bytes(self.records[fileId]["content"]))

    def tamper_first_content(self) -> None:
        first_id = sorted(self.records)[0]
        self.records[first_id]["content"] = b"tampered"


class _FakeDriveService:
    def __init__(self) -> None:
        self.files_api = _FakeDriveFiles()

    def files(self) -> _FakeDriveFiles:
        return self.files_api


class GoogleDriveTransportTests(unittest.TestCase):
    def test_uploaded_instance_package_can_be_read_back_and_recovered_by_second_post(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = SimpleNamespace(instance_id="copro-fictive")
            post_a_sync = root / "poste-a-sync"
            post_b_sync = root / "poste-b-sync"
            post_a_state = root / "poste-a-state"
            post_b_state = root / "poste-b-state"
            token = root / "token_drive_file.json"
            token.write_text(json.dumps({"scopes": [gdriveops.DRIVE_FILE_SCOPE]}), encoding="utf-8")

            published = drive_instance_sync.publish_instance_update(
                instance=instance,
                sync_root=post_a_sync,
                local_state_root=post_a_state,
            )
            package_path = next((post_a_sync / drive_instance_sync.PACKAGE_DIR).glob("*.cspkg"))
            service = _FakeDriveService()
            uploaded = gdriveops.upload_encrypted_drive_smoke(
                sync_root=post_a_sync,
                encrypted_path=package_path,
                token_path=token,
                drive_service=service,
                media_factory=lambda path: {"content": path.read_bytes()},
            )
            post_b_state.mkdir()
            (post_b_state / drive_instance_sync.SYNC_KEY_FILE).write_bytes(
                (post_a_state / drive_instance_sync.SYNC_KEY_FILE).read_bytes()
            )

            listed = gdrive_transport.list_encrypted_instance_packages(drive_service=service, folder_id="folder-id")
            downloaded = gdrive_transport.download_latest_encrypted_instance_package(
                drive_service=service,
                folder_id="folder-id",
                sync_root=post_b_sync,
                media_downloader_factory=lambda request: request.content,
            )
            recovered = drive_instance_sync.recover_instance_update(
                instance=instance,
                sync_root=post_b_sync,
                local_state_root=post_b_state,
            )

            serialized = json.dumps(
                {"published": published, "uploaded": uploaded, "listed": listed, "downloaded": downloaded, "recovered": recovered},
                ensure_ascii=True,
            ).lower()
            self.assertEqual(published["status"], "published")
            self.assertEqual(uploaded["status"], "uploaded")
            self.assertEqual(listed["status"], "ready")
            self.assertEqual(downloaded["status"], "downloaded")
            self.assertEqual(recovered["status"], "recovered")
            self.assertEqual(len(list((post_b_sync / drive_instance_sync.PACKAGE_DIR).glob("*.cspkg"))), 1)
            self.assertNotIn("folder-id", serialized)
            self.assertNotIn("file-", serialized)
            self.assertNotIn(str(root).lower(), serialized)
            self.assertNotIn("copro-fictive", _text(post_b_sync).lower())
            self.assertNotIn("instance_sync_key", _text(post_b_sync).lower())

    def test_download_blocks_tampered_remote_package_without_writing_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = SimpleNamespace(instance_id="copro-fictive")
            token = root / "token_drive_file.json"
            token.write_text(json.dumps({"scopes": [gdriveops.DRIVE_FILE_SCOPE]}), encoding="utf-8")
            published = drive_instance_sync.publish_instance_update(
                instance=instance,
                sync_root=root / "sync-a",
                local_state_root=root / "state-a",
            )
            package_path = next((root / "sync-a" / drive_instance_sync.PACKAGE_DIR).glob("*.cspkg"))
            service = _FakeDriveService()
            gdriveops.upload_encrypted_drive_smoke(
                sync_root=root / "sync-a",
                encrypted_path=package_path,
                token_path=token,
                drive_service=service,
                media_factory=lambda path: {"content": path.read_bytes()},
            )
            service.files_api.tamper_first_content()

            result = gdrive_transport.download_latest_encrypted_instance_package(
                drive_service=service,
                folder_id="folder-id",
                sync_root=root / "sync-b",
                media_downloader_factory=lambda request: request.content,
            )

            serialized = json.dumps({"published": published, "result": result}, ensure_ascii=True).lower()
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["blocker_code"], "sha256_mismatch")
            self.assertFalse((root / "sync-b" / drive_instance_sync.PACKAGE_DIR).exists())
            self.assertNotIn("folder-id", serialized)
            self.assertNotIn("file-", serialized)
            self.assertNotIn(str(root).lower(), serialized)

    def test_list_redacts_ids_and_ignores_non_instance_packages(self) -> None:
        service = _FakeDriveService()
        service.files_api.records["file-secret-1"] = {
            "metadata": {
                "id": "file-secret-1",
                "name": "coproscope-encrypted-smoke-aaaaaaaaaaaa.cspkg",
                "mimeType": "application/octet-stream",
                "size": "12",
                "modifiedTime": "2026-05-30T20:00:00Z",
                "appProperties": {
                    "coproscope_surface": gdrive_transport.PACKAGE_SURFACE,
                    "coproscope_protocol": gdriveops.SYNC_PROTOCOL,
                    "coproscope_sha256": "a" * 64,
                    "coproscope_generation": "2",
                },
            },
            "content": b"not-used",
        }
        service.files_api.records["file-secret-2"] = {
            "metadata": {
                "id": "file-secret-2",
                "name": "raw-private.cspkg",
                "mimeType": "application/octet-stream",
                "appProperties": {
                    "coproscope_surface": gdrive_transport.PACKAGE_SURFACE,
                    "coproscope_protocol": gdriveops.SYNC_PROTOCOL,
                    "coproscope_sha256": "b" * 64,
                },
            },
            "content": b"not-used",
        }

        result = gdrive_transport.list_encrypted_instance_packages(drive_service=service, folder_id="folder-secret")
        serialized = json.dumps(result, ensure_ascii=True).lower()

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["remote_package_count"], 1)
        self.assertEqual(result["packages"][0]["generation"], 2)
        self.assertIn("remote_ref", result["packages"][0])
        self.assertNotIn("file-secret", serialized)
        self.assertNotIn("folder-secret", serialized)
        self.assertNotIn("raw-private", serialized)

    def test_cli_exposes_drive_pull_package_without_requiring_paths_in_output_contract(self) -> None:
        args = build_parser().parse_args(
            [
                "drive",
                "pull-package",
                "--folder-id",
                "folder-secret",
                "--sync-root",
                "sync-cache",
                "--token-path",
                "token.json",
            ]
        )

        self.assertEqual(args.drive_command, "pull-package")
        self.assertEqual(args.folder_id, "folder-secret")
        self.assertEqual(args.sync_root, "sync-cache")


def _text(root: Path) -> str:
    return "\n".join(path.read_bytes().decode("utf-8", errors="ignore") for path in sorted(root.rglob("*")) if path.is_file())


if __name__ == "__main__":
    unittest.main()
