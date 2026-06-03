from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from coproscope.cli import build_parser
from coproscope.modules import drive_instance_sync, drive_watch


class _FakeRequest:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def execute(self) -> dict[str, object]:
        return self.payload


class _FakeMediaRequest:
    def __init__(self, content: bytes) -> None:
        self.content = content


class _FakeDriveFiles:
    def __init__(self, *, shared: bool = False, can_write: bool = True) -> None:
        self.records: dict[str, dict[str, Any]] = {}
        self.shared = shared
        self.can_write = can_write

    def get(self, **_: object) -> _FakeRequest:
        return _FakeRequest(
            {
                "mimeType": "application/vnd.google-apps.folder",
                "ownedByMe": True,
                "shared": self.shared,
                "capabilities": {"canAddChildren": self.can_write, "canEdit": self.can_write, "canShare": True},
            }
        )

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
        self.records[sorted(self.records)[0]]["content"] = b"tampered"


class _FakeDriveService:
    def __init__(self, *, permissions: list[dict[str, object]] | None = None, shared: bool = False, can_write: bool = True) -> None:
        self.files_api = _FakeDriveFiles(shared=shared, can_write=can_write)
        self.permissions_api = _FakePermissions(
            permissions or [{"type": "user", "role": "owner", "emailAddress": "owner@example.invalid"}]
        )

    def files(self) -> _FakeDriveFiles:
        return self.files_api

    def permissions(self) -> "_FakePermissions":
        return self.permissions_api


class _FakePermissions:
    def __init__(self, permissions: list[dict[str, object]]) -> None:
        self.permissions = permissions

    def list(self, **_: object) -> _FakeRequest:
        return _FakeRequest({"permissions": self.permissions})


class DriveWatchTests(unittest.TestCase):
    def test_watch_once_publishes_then_idles_then_applies_remote_without_reupload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = _FakeDriveService()
            instance = SimpleNamespace(instance_id="copro-fictive")
            post_a_state = root / "poste-a-state"
            post_b_state = root / "poste-b-state"

            first = _watch(instance, service, root / "poste-a-sync", post_a_state, "a-v1")
            idle = _watch(instance, service, root / "poste-a-sync", post_a_state, "a-v1")
            post_b_state.mkdir()
            (post_b_state / drive_instance_sync.SYNC_KEY_FILE).write_bytes(
                (post_a_state / drive_instance_sync.SYNC_KEY_FILE).read_bytes()
            )
            second = _watch(instance, service, root / "poste-b-sync", post_b_state, "b-v1")
            third = _watch(instance, service, root / "poste-a-sync", post_a_state, "a-v1")
            final_idle = _watch(instance, service, root / "poste-a-sync", post_a_state, "a-v1")

            serialized = json.dumps([first, idle, second, third, final_idle], ensure_ascii=True).lower()
            self.assertEqual(first["status"], "synced")
            self.assertTrue(first["outbound"]["uploaded"])
            self.assertEqual(idle["status"], "idle")
            self.assertEqual(len(service.files_api.records), 2)
            self.assertTrue(second["inbound"]["applied"])
            self.assertTrue(second["outbound"]["uploaded"])
            self.assertTrue(third["inbound"]["applied"])
            self.assertFalse(third["outbound"]["uploaded"])
            self.assertEqual(final_idle["status"], "idle")
            self.assertNotIn("folder-secret", serialized)
            self.assertNotIn("file-", serialized)
            self.assertNotIn(str(root).lower(), serialized)
            self.assertNotIn("instance_sync_key", _text(root / "poste-a-sync").lower())
            self.assertNotIn("copro-fictive", _text(root / "poste-b-sync").lower())

    def test_watch_once_uploads_only_when_local_marker_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = _FakeDriveService()
            instance = SimpleNamespace(instance_id="copro-fictive")
            state = root / "state-a"
            sync = root / "sync-a"

            first = _watch(instance, service, sync, state, "a-v1")
            second = _watch(instance, service, sync, state, "a-v2")

            self.assertEqual(first["status"], "synced")
            self.assertEqual(second["status"], "synced")
            self.assertFalse(second["inbound"]["checked"])
            self.assertTrue(second["outbound"]["uploaded"])
            self.assertEqual(len(service.files_api.records), 2)

    def test_watch_once_blocks_tampered_remote_before_local_upload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = _FakeDriveService()
            instance = SimpleNamespace(instance_id="copro-fictive")
            post_a_state = root / "state-a"
            post_b_state = root / "state-b"

            first = _watch(instance, service, root / "sync-a", post_a_state, "a-v1")
            service.files_api.tamper_first_content()
            post_b_state.mkdir()
            (post_b_state / drive_instance_sync.SYNC_KEY_FILE).write_bytes(
                (post_a_state / drive_instance_sync.SYNC_KEY_FILE).read_bytes()
            )
            second = _watch(instance, service, root / "sync-b", post_b_state, "b-v1")

            serialized = json.dumps({"first": first, "second": second}, ensure_ascii=True).lower()
            self.assertEqual(second["status"], "blocked")
            self.assertEqual(second["actions"][0]["source"], "remote")
            self.assertFalse(second["outbound"]["uploaded"])
            self.assertEqual(len(service.files_api.records), 1)
            self.assertNotIn("folder-secret", serialized)
            self.assertNotIn("file-", serialized)
            self.assertNotIn(str(root).lower(), serialized)

    def test_watch_once_blocks_public_google_folder_before_listing_or_upload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = _FakeDriveService(
                shared=True,
                permissions=[
                    {"type": "user", "role": "owner", "emailAddress": "owner@example.invalid"},
                    {"type": "anyone", "role": "reader", "allowFileDiscovery": False},
                ],
            )
            instance = SimpleNamespace(instance_id="copro-fictive")

            result = _watch(instance, service, root / "sync-a", root / "state-a", "a-v1")
            serialized = json.dumps(result, ensure_ascii=True).lower()

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["blocker_code"], "public_link")
            self.assertEqual(len(service.files_api.records), 0)
            self.assertNotIn("folder-secret", serialized)
            self.assertNotIn("file-", serialized)
            self.assertNotIn(str(root).lower(), serialized)

    def test_watch_once_blocks_concurrent_remote_and_local_changes_without_upload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = _FakeDriveService()
            instance = SimpleNamespace(instance_id="copro-fictive")
            state_a = root / "state-a"
            state_b = root / "state-b"

            _watch(instance, service, root / "sync-a", state_a, "a-v1")
            state_b.mkdir()
            (state_b / drive_instance_sync.SYNC_KEY_FILE).write_bytes((state_a / drive_instance_sync.SYNC_KEY_FILE).read_bytes())
            _watch(instance, service, root / "sync-b", state_b, "b-v1")
            _watch(instance, service, root / "sync-a", state_a, "a-v1")
            _watch(instance, service, root / "sync-b", state_b, "b-v2")
            result = _watch(instance, service, root / "sync-a", state_a, "a-v2")
            serialized = json.dumps(result, ensure_ascii=True).lower()

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["blocker_code"], "concurrent_changes")
            self.assertEqual(result["conflict"]["policy"], "no_silent_overwrite")
            self.assertFalse(result["inbound"]["applied"])
            self.assertFalse(result["outbound"]["uploaded"])
            self.assertEqual(len(service.files_api.records), 3)
            self.assertNotIn("folder-secret", serialized)
            self.assertNotIn("file-", serialized)
            self.assertNotIn(str(root).lower(), serialized)

    def test_watch_once_merges_disjoint_concurrent_shared_state_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            service = _FakeDriveService()
            instance_a = SimpleNamespace(instance_id="copro-fictive", drive_shared_state={"base": "FICTIF-v1"})
            instance_b = SimpleNamespace(instance_id="copro-fictive", drive_shared_state={"base": "FICTIF-v1"})
            state_a = root / "state-a"
            state_b = root / "state-b"

            _watch(instance_a, service, root / "sync-a", state_a, "a-v1")
            state_b.mkdir()
            (state_b / drive_instance_sync.SYNC_KEY_FILE).write_bytes((state_a / drive_instance_sync.SYNC_KEY_FILE).read_bytes())
            _watch(instance_b, service, root / "sync-b", state_b, "b-v1")
            _watch(instance_a, service, root / "sync-a", state_a, "a-v1")
            instance_b.drive_shared_state = {"base": "FICTIF-v1", "remote_note": "FICTIF distant"}
            _watch(instance_b, service, root / "sync-b", state_b, "b-v2")
            instance_a.drive_shared_state = {"base": "FICTIF-v1", "local_note": "FICTIF local"}

            merged = _watch(instance_a, service, root / "sync-a", state_a, "a-v2")
            recovered_on_b = _watch(instance_b, service, root / "sync-b", state_b, "b-v2")
            cache_a = _cached_shared_state(state_a)
            cache_b = _cached_shared_state(state_b)
            serialized = json.dumps({"merged": merged, "recovered": recovered_on_b}, ensure_ascii=True).lower()

            self.assertEqual(merged["status"], "synced")
            self.assertEqual(merged["merge"]["status"], "merged")
            self.assertTrue(merged["outbound"]["uploaded"])
            self.assertEqual(len(service.files_api.records), 4)
            self.assertEqual(cache_a["local_note"], "FICTIF local")
            self.assertEqual(cache_a["remote_note"], "FICTIF distant")
            self.assertEqual(cache_b["local_note"], "FICTIF local")
            self.assertEqual(cache_b["remote_note"], "FICTIF distant")
            self.assertNotIn("folder-secret", serialized)
            self.assertNotIn("file-", serialized)
            self.assertNotIn(str(root).lower(), serialized)
            self.assertNotIn("fictif local", _text(root / "sync-a").lower())
            self.assertNotIn("fictif distant", _text(root / "sync-b").lower())

    def test_cli_exposes_drive_watch_once(self) -> None:
        args = build_parser().parse_args(
            [
                "drive",
                "watch-once",
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
            ]
        )

        self.assertEqual(args.drive_command, "watch-once")
        self.assertEqual(args.local_change_marker, "opaque-v1")


def _watch(instance: object, service: _FakeDriveService, sync: Path, state: Path, marker: str) -> dict[str, object]:
    return drive_watch.watch_once(
        instance=instance,
        drive_service=service,
        folder_id="folder-secret",
        sync_root=sync,
        local_state_root=state,
        local_change_marker=marker,
        media_factory=lambda path: {"content": path.read_bytes()},
        media_downloader_factory=lambda request: request.content,
    )


def _text(root: Path) -> str:
    return "\n".join(path.read_bytes().decode("utf-8", errors="ignore") for path in sorted(root.rglob("*")) if path.is_file())


def _cached_shared_state(state: Path) -> dict[str, object]:
    payload = json.loads((state / "cache_instance" / drive_instance_sync.SHARED_STATE_FILE).read_text(encoding="utf-8"))
    return dict(payload["shared_state"])


if __name__ == "__main__":
    unittest.main()
