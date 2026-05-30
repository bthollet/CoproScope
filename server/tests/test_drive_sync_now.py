from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from coproscope.cli import build_parser
from coproscope.modules import drive_instance_sync, drive_sync_now


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

    def list(self, **_: object) -> _FakeRequest:
        return _FakeRequest({"files": [record["metadata"] for record in self.records.values()]})

    def create(self, *, body: dict[str, object], fields: str, media_body: object | None = None) -> _FakeRequest:
        file_id = f"file-{len(self.records) + 1}"
        content = bytes(media_body.get("content", b"")) if isinstance(media_body, dict) else b""
        metadata = {
            "id": file_id,
            "name": body["name"],
            "mimeType": body["mimeType"],
            "size": str(len(content)),
            "modifiedTime": f"2026-05-30T21:{len(self.records):02d}:00Z",
            "appProperties": dict(body.get("appProperties") or {}),
        }
        self.records[file_id] = {"metadata": metadata, "content": content}
        return _FakeRequest({"id": file_id, "name": body["name"], "mimeType": body["mimeType"], "size": str(len(content))})

    def get_media(self, *, fileId: str) -> _FakeMediaRequest:
        return _FakeMediaRequest(bytes(self.records[fileId]["content"]))

    def tamper_first_content(self) -> None:
        first_id = sorted(self.records)[0]
        self.records[first_id]["content"] = b"tampered"


class _FakeDriveService:
    def __init__(self) -> None:
        self.files_api = _FakeDriveFiles()

    def files(self) -> _FakeDriveFiles:
        return self.files_api


class DriveSyncNowTests(unittest.TestCase):
    def test_two_posts_sync_now_receive_each_other_without_cleartext_or_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = _FakeDriveService()
            instance = SimpleNamespace(instance_id="copro-fictive")
            post_a_sync = root / "poste-a-sync"
            post_a_state = root / "poste-a-state"
            post_b_sync = root / "poste-b-sync"
            post_b_state = root / "poste-b-state"

            first = _sync(instance, service, post_a_sync, post_a_state)
            post_b_state.mkdir()
            (post_b_state / drive_instance_sync.SYNC_KEY_FILE).write_bytes(
                (post_a_state / drive_instance_sync.SYNC_KEY_FILE).read_bytes()
            )
            second = _sync(instance, service, post_b_sync, post_b_state)
            third = _sync(instance, service, post_a_sync, post_a_state)

            serialized = json.dumps({"first": first, "second": second, "third": third}, ensure_ascii=True).lower()
            self.assertEqual(first["status"], "synced")
            self.assertEqual(second["status"], "synced")
            self.assertEqual(third["status"], "synced")
            self.assertFalse(first["inbound"]["applied"])
            self.assertTrue(second["inbound"]["applied"])
            self.assertTrue(third["inbound"]["applied"])
            self.assertEqual(len(service.files_api.records), 3)
            self.assertNotIn("folder-secret", serialized)
            self.assertNotIn("file-", serialized)
            self.assertNotIn(str(root).lower(), serialized)
            self.assertNotIn("instance_sync_key", _text(post_a_sync).lower())
            self.assertNotIn("instance_sync_key", _text(post_b_sync).lower())
            self.assertNotIn("copro-fictive", _text(post_a_sync).lower())
            self.assertNotIn("copro-fictive", _text(post_b_sync).lower())

    def test_sync_now_blocks_tampered_remote_before_publish(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = _FakeDriveService()
            instance = SimpleNamespace(instance_id="copro-fictive")

            first = _sync(instance, service, root / "sync-a", root / "state-a")
            service.files_api.tamper_first_content()
            second = _sync(instance, service, root / "sync-b", root / "state-b")

            serialized = json.dumps({"first": first, "second": second}, ensure_ascii=True).lower()
            self.assertEqual(first["status"], "synced")
            self.assertEqual(second["status"], "blocked")
            self.assertEqual(second["phases"][0]["status"], "blocked")
            self.assertFalse(second["outbound"]["uploaded"])
            self.assertEqual(len(service.files_api.records), 1)
            self.assertNotIn("folder-secret", serialized)
            self.assertNotIn("file-", serialized)
            self.assertNotIn(str(root).lower(), serialized)

    def test_cli_exposes_drive_sync_now_manual_action(self) -> None:
        args = build_parser().parse_args(
            [
                "drive",
                "sync-now",
                "--instance-root",
                "instance-demo",
                "--folder-id",
                "folder-secret",
                "--sync-root",
                "sync-local",
                "--local-state-root",
                "state-local",
                "--token-path",
                "token.json",
            ]
        )

        self.assertEqual(args.drive_command, "sync-now")
        self.assertEqual(args.folder_id, "folder-secret")
        self.assertEqual(args.local_state_root, "state-local")


def _sync(instance: object, service: _FakeDriveService, sync: Path, state: Path) -> dict[str, object]:
    return drive_sync_now.sync_now(
        instance=instance,
        drive_service=service,
        folder_id="folder-secret",
        sync_root=sync,
        local_state_root=state,
        media_factory=lambda path: {"content": path.read_bytes()},
        media_downloader_factory=lambda request: request.content,
    )


def _text(root: Path) -> str:
    return "\n".join(path.read_bytes().decode("utf-8", errors="ignore") for path in sorted(root.rglob("*")) if path.is_file())


if __name__ == "__main__":
    unittest.main()
