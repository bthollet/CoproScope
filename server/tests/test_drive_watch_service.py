from __future__ import annotations

import json
import threading
import time
import unittest

from coproscope.modules.drive_watch_service import DriveWatchService


class DriveWatchServiceTests(unittest.TestCase):
    def test_service_runs_until_stopped_without_leaking_details(self) -> None:
        first_pass = threading.Event()
        calls = {"count": 0}

        def watch_once() -> dict[str, object]:
            calls["count"] += 1
            first_pass.set()
            return {
                "status": "idle",
                "summary": "Aucun changement detecte.",
                "result_label": "Rien a appliquer",
                "share_label": "Affichage limite a ce poste.",
            }

        service = DriveWatchService(watch_once, interval_seconds=0.1)

        started = service.start()
        self.assertEqual(started["status"], "running")
        self.assertTrue(first_pass.wait(timeout=1.0))
        snapshot = service.snapshot()
        stopped = service.stop()
        serialized = json.dumps([started, snapshot, stopped], ensure_ascii=True).lower()

        self.assertGreaterEqual(snapshot["cycles_completed"], 1)
        self.assertEqual(stopped["status"], "stopped")
        self.assertFalse(stopped["running"])
        self.assertGreaterEqual(calls["count"], 1)
        self.assertNotIn("token", serialized)
        self.assertNotIn("secret", serialized)
        self.assertNotIn("c:\\", serialized)

    def test_service_stops_on_blockage_and_sanitizes_error_text(self) -> None:
        def watch_once() -> dict[str, object]:
            return {
                "status": "blocked",
                "summary": r"C:\secret\raw\token.json",
                "result_label": "Erreur OAuth token",
                "share_label": "Dossier Google a verifier.",
            }

        service = DriveWatchService(watch_once, interval_seconds=0.1)

        service.start()
        blocked = _wait_until(lambda: service.snapshot()["status"] == "blocked")
        snapshot = service.snapshot()
        serialized = json.dumps(snapshot, ensure_ascii=True).lower()

        self.assertTrue(blocked)
        self.assertFalse(snapshot["running"])
        self.assertEqual(snapshot["cycles_completed"], 1)
        self.assertNotIn("token", serialized)
        self.assertNotIn("secret", serialized)
        self.assertNotIn("raw", serialized)
        self.assertNotIn("c:\\", serialized)

    def test_start_is_idempotent_while_worker_is_alive(self) -> None:
        first_pass = threading.Event()
        release = threading.Event()
        calls = {"count": 0}

        def watch_once() -> dict[str, object]:
            calls["count"] += 1
            first_pass.set()
            release.wait(timeout=1.0)
            return {"status": "idle", "summary": "Aucun changement detecte."}

        service = DriveWatchService(watch_once, interval_seconds=0.1)

        service.start()
        self.assertTrue(first_pass.wait(timeout=1.0))
        duplicate = service.start()
        release.set()
        service.stop()

        self.assertEqual(duplicate["status"], "working")
        self.assertEqual(calls["count"], 1)


def _wait_until(predicate: object, *, timeout: float = 1.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():  # type: ignore[operator]
            return True
        time.sleep(0.02)
    return False


if __name__ == "__main__":
    unittest.main()
