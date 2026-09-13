from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from coproscope.modules.drive_oauth_service import DriveOAuthService


class DriveOAuthServiceTests(unittest.TestCase):
    def test_missing_client_file_returns_human_blockage_without_leak(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service = DriveOAuthService(
                client_secrets_path=root / "missing.json",
                token_path=root / "token.json",
            )

            result = service.start()
            serialized = json.dumps(result, ensure_ascii=True).lower()

        self.assertEqual(result["status"], "blocked")
        self.assertIn("Connexion Google non disponible", result["summary"])
        self.assertNotIn("token", serialized)
        self.assertNotIn("secret", serialized)
        self.assertNotIn("oauth", serialized)
        self.assertNotIn("c:\\", serialized)

    def test_successful_flow_marks_google_ready_without_returning_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client = root / "client.json"
            token = root / "token.json"
            client.write_text("{}", encoding="utf-8")

            def fake_flow(**kwargs: object) -> dict[str, object]:
                token.write_text(json.dumps({"scopes": ["https://www.googleapis.com/auth/drive.file"]}), encoding="utf-8")
                return {"status": "ok", "token_path": str(token), "client": str(client)}

            service = DriveOAuthService(
                client_secrets_path=client,
                token_path=token,
                flow_runner=fake_flow,
            )

            first = service.start()
            ready = _wait_until(lambda: service.snapshot()["status"] == "ready")
            snapshot = service.snapshot()
            serialized = json.dumps([first, snapshot], ensure_ascii=True).lower()

        self.assertEqual(first["status"], "working")
        self.assertTrue(ready)
        self.assertEqual(snapshot["status"], "ready")
        self.assertNotIn("token.json", serialized)
        self.assertNotIn("client.json", serialized)
        self.assertNotIn(str(root).lower(), serialized)
        self.assertNotIn("secret", serialized)
        self.assertNotIn("oauth", serialized)

    def test_flow_exception_is_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            client = root / "client.json"
            client.write_text("{}", encoding="utf-8")

            def failing_flow(**kwargs: object) -> dict[str, object]:
                raise RuntimeError(r"C:\raw\client_secret.json token_drive_file")

            service = DriveOAuthService(
                client_secrets_path=client,
                token_path=root / "token.json",
                flow_runner=failing_flow,
            )

            service.start()
            blocked = _wait_until(lambda: service.snapshot()["status"] == "blocked")
            snapshot = service.snapshot()
            serialized = json.dumps(snapshot, ensure_ascii=True).lower()

        self.assertTrue(blocked)
        self.assertIn("Connexion Google interrompue", snapshot["summary"])
        self.assertNotIn("token", serialized)
        self.assertNotIn("secret", serialized)
        self.assertNotIn("raw", serialized)
        self.assertNotIn("c:\\", serialized)


def _wait_until(predicate: object, *, timeout: float = 1.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():  # type: ignore[operator]
            return True
        time.sleep(0.02)
    return False


if __name__ == "__main__":
    unittest.main()
