from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from coproscope.cli import build_parser
from coproscope.modules import drive_instance_sync, drive_watch_loop


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
            "modifiedTime": f"2026-05-30T22:{len(self.records):02d}:00Z",
            "appProperties": dict(body.get("appProperties") or {}),
        }
        self.records[file_id] = {"metadata": metadata, "content": content}
        return _FakeRequest({"id": file_id, "name": body["name"], "mimeType": body["mimeType"], "size": str(len(content))})

    def get_media(self, *, fileId: str) -> _FakeMediaRequest:
        return _FakeMediaRequest(bytes(self.records[fileId]["content"]))

    def tamper_first_content(self) -> None:
        self.records[sorted(self.records)[0]]["content"] = b"tampered"


class _FakeDriveService:
    def __init__(self) -> None:
        self.files_api = _FakeDriveFiles()

    def files(self) -> _FakeDriveFiles:
        return self.files_api


class DriveWatchLoopTests(unittest.TestCase):
    def test_watch_loop_idles_after_first_publish_without_duplicate_uploads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = _FakeDriveService()
            instance = SimpleNamespace(instance_id="copro-fictive")

            result = _loop(instance, service, root / "sync-a", root / "state-a", marker="a-v1", cycles=3)
            serialized = json.dumps(result, ensure_ascii=True).lower()

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["counts"], {"synced": 1, "idle": 2, "blocked": 0})
            self.assertEqual(len(service.files_api.records), 1)
            self.assertTrue(result["cycles"][0]["uploaded"])
            self.assertFalse(result["cycles"][1]["uploaded"])
            self.assertNotIn("folder-secret", serialized)
            self.assertNotIn("file-", serialized)
            self.assertNotIn(str(root).lower(), serialized)

    def test_watch_loop_publishes_when_local_marker_changes_mid_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = _FakeDriveService()
            instance = SimpleNamespace(instance_id="copro-fictive")
            markers = ["a-v1", "a-v1", "a-v2"]

            result = _loop(
                instance,
                service,
                root / "sync-a",
                root / "state-a",
                marker_factory=lambda index: markers[index],
                cycles=3,
            )

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["counts"], {"synced": 2, "idle": 1, "blocked": 0})
            self.assertEqual(len(service.files_api.records), 2)
            self.assertTrue(result["cycles"][2]["local_changed"])
            self.assertTrue(result["cycles"][2]["uploaded"])

    def test_watch_loop_applies_remote_change_then_stops_idle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = _FakeDriveService()
            instance = SimpleNamespace(instance_id="copro-fictive")
            first = _loop(instance, service, root / "sync-a", root / "state-a", marker="a-v1", cycles=1)
            state_b = root / "state-b"
            state_b.mkdir()
            (state_b / drive_instance_sync.SYNC_KEY_FILE).write_bytes((root / "state-a" / drive_instance_sync.SYNC_KEY_FILE).read_bytes())

            second = _loop(instance, service, root / "sync-b", state_b, marker="b-v1", cycles=2)

            self.assertEqual(first["status"], "completed")
            self.assertEqual(second["status"], "completed")
            self.assertTrue(second["cycles"][0]["applied"])
            self.assertTrue(second["cycles"][0]["uploaded"])
            self.assertEqual(second["cycles"][1]["status"], "idle")
            self.assertEqual(len(service.files_api.records), 2)

    def test_watch_loop_blocks_on_tampered_remote_without_uploading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = _FakeDriveService()
            instance = SimpleNamespace(instance_id="copro-fictive")
            _loop(instance, service, root / "sync-a", root / "state-a", marker="a-v1", cycles=1)
            service.files_api.tamper_first_content()
            state_b = root / "state-b"
            state_b.mkdir()
            (state_b / drive_instance_sync.SYNC_KEY_FILE).write_bytes((root / "state-a" / drive_instance_sync.SYNC_KEY_FILE).read_bytes())

            result = _loop(instance, service, root / "sync-b", state_b, marker="b-v1", cycles=3)
            serialized = json.dumps(result, ensure_ascii=True).lower()

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["cycles_completed"], 1)
            self.assertFalse(result["cycles"][0]["uploaded"])
            self.assertEqual(len(service.files_api.records), 1)
            self.assertNotIn("folder-secret", serialized)
            self.assertNotIn("file-", serialized)
            self.assertNotIn(str(root).lower(), serialized)

    def test_cli_exposes_drive_watch_loop(self) -> None:
        args = build_parser().parse_args(
            [
                "drive",
                "watch-loop",
                "--instance-root",
                "instance-demo",
                "--folder-id",
                "folder-secret",
                "--sync-root",
                "sync-local",
                "--local-state-root",
                "state-local",
                "--local-change-marker",
                "opaque-v1",
                "--interval-seconds",
                "0",
                "--max-cycles",
                "2",
            ]
        )

        self.assertEqual(args.drive_command, "watch-loop")
        self.assertEqual(args.max_cycles, 2)


def _loop(
    instance: object,
    service: _FakeDriveService,
    sync: Path,
    state: Path,
    *,
    marker: str | None = None,
    marker_factory: Any = None,
    cycles: int,
) -> dict[str, object]:
    return drive_watch_loop.watch_loop(
        instance=instance,
        drive_service=service,
        folder_id="folder-secret",
        sync_root=sync,
        local_state_root=state,
        local_change_marker=marker,
        local_change_marker_factory=marker_factory,
        interval_seconds=0,
        max_cycles=cycles,
        sleep=lambda _: None,
        media_factory=lambda path: {"content": path.read_bytes()},
        media_downloader_factory=lambda request: request.content,
    )


if __name__ == "__main__":
    unittest.main()
