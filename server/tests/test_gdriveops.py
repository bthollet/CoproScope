from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import gdriveops


class GoogleDriveOAuthBootstrapTests(unittest.TestCase):
    def test_status_reports_missing_client_without_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            status = gdriveops.oauth_status(
                client_secrets_path=root / "client_secret_dev.json",
                token_path=root / "token_drive_file.json",
            )

        self.assertEqual(status["status"], "action_required")
        self.assertFalse(status["client_secrets_present"])
        self.assertFalse(status["token_present"])
        self.assertIn("Download", status["next_action"])
        self.assertNotIn("client_secret_value", json.dumps(status))
        self.assertNotIn(str(root), json.dumps(status))

    def test_status_accepts_existing_token_with_drive_file_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            client = root / "client_secret_dev.json"
            token = root / "token_drive_file.json"
            client.write_text('{"installed": {"client_id": "id"}}', encoding="utf-8")
            token.write_text(
                json.dumps({"scopes": [gdriveops.DRIVE_FILE_SCOPE]}),
                encoding="utf-8",
            )

            status = gdriveops.oauth_status(client_secrets_path=client, token_path=token)

        self.assertEqual(status["status"], "ready")
        self.assertTrue(status["client_secrets_present"])
        self.assertTrue(status["token_present"])
        self.assertTrue(status["scope_ok"])
        self.assertEqual(status["requested_scopes"], [gdriveops.DRIVE_FILE_SCOPE])

    def test_status_rejects_token_with_broader_drive_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            client = root / "client_secret_dev.json"
            token = root / "token_drive_file.json"
            client.write_text('{"installed": {"client_id": "id"}}', encoding="utf-8")
            token.write_text(
                json.dumps({"scope": f"{gdriveops.DRIVE_FILE_SCOPE} https://www.googleapis.com/auth/drive"}),
                encoding="utf-8",
            )

            status = gdriveops.oauth_status(client_secrets_path=client, token_path=token)

        self.assertEqual(status["status"], "action_required")
        self.assertFalse(status["scope_ok"])
        self.assertIn("drive.file", status["next_action"])

    def test_normalize_scopes_deduplicates_and_falls_back_to_drive_file(self) -> None:
        self.assertEqual(
            gdriveops.normalize_scopes(["", gdriveops.DRIVE_FILE_SCOPE, gdriveops.DRIVE_FILE_SCOPE]),
            (gdriveops.DRIVE_FILE_SCOPE,),
        )
        self.assertEqual(gdriveops.normalize_scopes([]), (gdriveops.DRIVE_FILE_SCOPE,))

    def test_normalize_scopes_rejects_any_non_minimal_drive_scope(self) -> None:
        with self.assertRaisesRegex(ValueError, "drive.file"):
            gdriveops.normalize_scopes(["https://www.googleapis.com/auth/drive"])

    def test_prepare_smoke_does_not_upload_without_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blob = root / "sync" / "blobs" / "aa" / f"{'a' * 64}.blob"
            blob.parent.mkdir(parents=True)
            blob.write_bytes(b"ciphertext-only")

            result = gdriveops.prepare_encrypted_drive_smoke(
                sync_root=root / "sync",
                encrypted_path=blob,
                token_path=root / "missing-token.json",
            )

        self.assertEqual(result["status"], "action_required")
        self.assertFalse(result["upload_attempted"])
        self.assertFalse(result["ready_for_upload"])
        self.assertFalse(result["token_present"])
        self.assertEqual(result["gate"]["code"], "encrypted_vault_surface")
        self.assertEqual(result["encrypted_candidate"]["relative_path"], f"blobs/aa/{'a' * 64}.blob")

    def test_prepare_smoke_becomes_ready_only_with_minimal_scope_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blob = root / "sync" / "blobs" / "bb" / f"{'b' * 64}.blob"
            token = root / "token_drive_file.json"
            blob.parent.mkdir(parents=True)
            blob.write_bytes(b"ciphertext-only")
            token.write_text(
                json.dumps({"scopes": [gdriveops.DRIVE_FILE_SCOPE]}),
                encoding="utf-8",
            )

            result = gdriveops.prepare_encrypted_drive_smoke(
                sync_root=root / "sync",
                encrypted_path=blob,
                token_path=token,
            )

        self.assertEqual(result["status"], "prepared")
        self.assertTrue(result["ready_for_upload"])
        self.assertFalse(result["upload_attempted"])

    def test_upload_guard_blocks_raw_path_without_leaking_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "sync" / "raw" / "secret-copro.pdf"
            raw.parent.mkdir(parents=True)
            raw.write_bytes(b"plain private bytes")

            result = gdriveops.prepare_encrypted_drive_smoke(
                sync_root=root / "sync",
                encrypted_path=raw,
                token_path=root / "missing-token.json",
            )

            serialized = json.dumps(result, ensure_ascii=True)

        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["upload_attempted"])
        self.assertIsNone(result["encrypted_candidate"])
        self.assertEqual(result["gate"]["code"], "forbidden_source_location")
        self.assertNotIn(str(raw), serialized)
        self.assertNotIn("secret-copro.pdf", serialized)
        self.assertNotIn("raw", serialized.lower())


if __name__ == "__main__":
    unittest.main()
