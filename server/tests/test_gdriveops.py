from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from coproscope.modules import drive_instance_sync, gdriveops


class _FakeRequest:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def execute(self) -> dict[str, object]:
        return self.payload


class _FakeDriveFiles:
    def __init__(self) -> None:
        self.created: list[dict[str, object]] = []
        self.media_bodies: list[object] = []

    def list(self, **kwargs: object) -> _FakeRequest:
        raise AssertionError("Drive smoke upload must not list Drive files.")

    def create(
        self,
        *,
        body: dict[str, object],
        fields: str,
        media_body: object | None = None,
    ) -> _FakeRequest:
        self.created.append(body)
        self.media_bodies.append(media_body)
        if body.get("mimeType") == "application/vnd.google-apps.folder":
            return _FakeRequest({"id": "folder-id", "name": body["name"]})
        return _FakeRequest({"id": "file-id", "name": body["name"], "mimeType": body["mimeType"], "size": "16"})


class _FakeDriveService:
    def __init__(self) -> None:
        self.files_api = _FakeDriveFiles()

    def files(self) -> _FakeDriveFiles:
        return self.files_api


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

    def test_status_accepts_powershell_utf8_bom_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            client = root / "client_secret_dev.json"
            token = root / "token_drive_file.json"
            client.write_text('{"installed": {"client_id": "id"}}', encoding="utf-8")
            token.write_text(
                json.dumps({"scopes": [gdriveops.DRIVE_FILE_SCOPE]}),
                encoding="utf-8-sig",
            )

            status = gdriveops.oauth_status(client_secrets_path=client, token_path=token)

        self.assertEqual(status["status"], "ready")
        self.assertTrue(status["scope_ok"])

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
        self.assertFalse(result["gate"]["cleartext_canary_checked"])
        sync_contract = result["encrypted_candidate"]["sync_contract"]
        self.assertEqual(sync_contract["protocol"], gdriveops.SYNC_PROTOCOL)
        self.assertEqual(sync_contract["generation"], gdriveops.DEFAULT_SYNC_GENERATION)
        self.assertEqual(sync_contract["parent_sha256"], "")
        self.assertEqual(sync_contract["conflict_policy"], gdriveops.SYNC_CONFLICT_POLICY)

    def test_prepare_smoke_emits_collaboration_contract_without_paths(self) -> None:
        parent_hash = "1" * 64
        canary = "SYNC-CANARY-LOCAL-ONLY"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blob = root / "sync" / "blobs" / "ab" / f"{'a' * 64}.blob"
            token = root / "token_drive_file.json"
            blob.parent.mkdir(parents=True)
            blob.write_bytes(b"ciphertext-only")
            token.write_text(json.dumps({"scopes": [gdriveops.DRIVE_FILE_SCOPE]}), encoding="utf-8")

            result = gdriveops.prepare_encrypted_drive_smoke(
                sync_root=root / "sync",
                encrypted_path=blob,
                token_path=token,
                cleartext_canary=canary,
                generation=3,
                parent_sha256=parent_hash,
            )

        serialized = json.dumps(result, ensure_ascii=True)
        sync_contract = result["encrypted_candidate"]["sync_contract"]
        self.assertEqual(result["status"], "prepared")
        self.assertEqual(sync_contract["protocol"], gdriveops.SYNC_PROTOCOL)
        self.assertEqual(sync_contract["packet_kind"], "encrypted_blob")
        self.assertEqual(sync_contract["generation"], 3)
        self.assertEqual(sync_contract["parent_sha256"], parent_hash)
        self.assertEqual(sync_contract["remote_name_policy"], gdriveops.SYNC_REMOTE_NAME_POLICY)
        self.assertEqual(sync_contract["conflict_policy"], gdriveops.SYNC_CONFLICT_POLICY)
        self.assertEqual(sync_contract["collaboration_mode"], "direct-sync-compatible")
        self.assertTrue(str(sync_contract["remote_name"]).startswith("coproscope-encrypted-smoke-"))
        self.assertNotIn(canary, serialized)
        self.assertNotIn(str(root), serialized)
        self.assertNotIn("token_drive_file", serialized)

    def test_prepare_and_upload_accept_instance_cspkg_without_cleartext(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "sync" / "packages" / f"{'a' * 64}.cspkg"
            token = root / "token_drive_file.json"
            package.parent.mkdir(parents=True)
            package.write_text('{"ciphertext":"only"}', encoding="utf-8")
            token.write_text(json.dumps({"scopes": [gdriveops.DRIVE_FILE_SCOPE]}), encoding="utf-8")
            service = _FakeDriveService()

            prepared = gdriveops.prepare_encrypted_drive_smoke(sync_root=root / "sync", encrypted_path=package, token_path=token)
            uploaded = gdriveops.upload_encrypted_drive_smoke(
                sync_root=root / "sync",
                encrypted_path=package,
                token_path=token,
                drive_service=service,
                media_factory=lambda path: {"file_name": path.name},
            )

        serialized = json.dumps({"prepared": prepared, "uploaded": uploaded}, ensure_ascii=True)
        self.assertEqual(prepared["status"], "prepared")
        self.assertEqual(prepared["encrypted_candidate"]["sync_contract"]["packet_kind"], "encrypted_instance_package")
        self.assertTrue(prepared["encrypted_candidate"]["sync_contract"]["remote_name"].endswith(".cspkg"))
        self.assertEqual(uploaded["status"], "uploaded")
        self.assertEqual(service.files_api.created[1]["appProperties"]["coproscope_surface"], "encrypted-instance-package")
        self.assertNotIn(str(root), serialized)
        self.assertNotIn("token_drive_file", serialized)

    def test_prepare_accepts_cspkg_produced_by_instance_sync(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            token = root / "token_drive_file.json"
            token.write_text(json.dumps({"scopes": [gdriveops.DRIVE_FILE_SCOPE]}), encoding="utf-8")
            published = drive_instance_sync.publish_instance_update(
                instance=SimpleNamespace(instance_id="copro-fictive"),
                sync_root=root / "sync",
                local_state_root=root / "poste-a-local",
            )

            prepared = gdriveops.prepare_encrypted_drive_smoke(sync_root=root / "sync", token_path=token)

        serialized = json.dumps({"published": published, "prepared": prepared}, ensure_ascii=True)
        self.assertEqual(published["status"], "published")
        self.assertEqual(prepared["status"], "prepared")
        self.assertEqual(prepared["encrypted_candidate"]["sync_contract"]["packet_kind"], "encrypted_instance_package")
        self.assertIn("packages/", prepared["encrypted_candidate"]["relative_path"])
        self.assertNotIn(str(root), serialized)

    def test_prepare_smoke_rejects_invalid_collaboration_parent_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blob = root / "sync" / "blobs" / "ac" / f"{'a' * 64}.blob"
            blob.parent.mkdir(parents=True)
            blob.write_bytes(b"ciphertext-only")

            with self.assertRaisesRegex(ValueError, "sha256"):
                gdriveops.prepare_encrypted_drive_smoke(
                    sync_root=root / "sync",
                    encrypted_path=blob,
                    token_path=root / "missing-token.json",
                    parent_sha256="not-a-hash",
                )

    def test_prepare_smoke_checks_cleartext_canary_without_leaking_it(self) -> None:
        canary = "CANARY-DO-NOT-UPLOAD"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blob = root / "sync" / "blobs" / "ee" / f"{'e' * 64}.blob"
            token = root / "token_drive_file.json"
            blob.parent.mkdir(parents=True)
            blob.write_bytes(b"ciphertext-only")
            token.write_text(json.dumps({"scopes": [gdriveops.DRIVE_FILE_SCOPE]}), encoding="utf-8")

            result = gdriveops.prepare_encrypted_drive_smoke(
                sync_root=root / "sync",
                encrypted_path=blob,
                token_path=token,
                cleartext_canary=canary,
            )

        serialized = json.dumps(result, ensure_ascii=True)
        self.assertEqual(result["status"], "prepared")
        self.assertTrue(result["ready_for_upload"])
        self.assertTrue(result["gate"]["cleartext_canary_checked"])
        self.assertNotIn(canary, serialized)

    def test_cleartext_canary_blocks_upload_before_drive_call_without_leaking_marker(self) -> None:
        canary = "PRIVATE-CLEAR-CANARY"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blob = root / "sync" / "blobs" / "ff" / f"{'f' * 64}.blob"
            token = root / "token_drive_file.json"
            blob.parent.mkdir(parents=True)
            blob.write_bytes(f"ciphertext-prefix-{canary}-suffix".encode("utf-8"))
            token.write_text(json.dumps({"scopes": [gdriveops.DRIVE_FILE_SCOPE]}), encoding="utf-8")
            service = _FakeDriveService()

            result = gdriveops.upload_encrypted_drive_smoke(
                sync_root=root / "sync",
                encrypted_path=blob,
                token_path=token,
                drive_service=service,
                media_factory=lambda path: {"file_name": path.name},
                cleartext_canary=canary,
            )

        serialized = json.dumps(result, ensure_ascii=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["gate"]["code"], "cleartext_canary_detected")
        self.assertFalse(result["upload_attempted"])
        self.assertIsNone(result["encrypted_candidate"])
        self.assertEqual(service.files_api.created, [])
        self.assertNotIn(canary, serialized)
        self.assertNotIn(str(root), serialized)

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

    def test_upload_smoke_uses_drive_service_only_after_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blob = root / "sync" / "blobs" / "cc" / f"{'c' * 64}.blob"
            token = root / "token_drive_file.json"
            blob.parent.mkdir(parents=True)
            blob.write_bytes(b"ciphertext-only")
            token.write_text(json.dumps({"scopes": [gdriveops.DRIVE_FILE_SCOPE]}), encoding="utf-8")
            service = _FakeDriveService()

            result = gdriveops.upload_encrypted_drive_smoke(
                sync_root=root / "sync",
                encrypted_path=blob,
                token_path=token,
                drive_service=service,
                media_factory=lambda path: {"file_name": path.name},
                generation=2,
                parent_sha256="2" * 64,
            )
            serialized = json.dumps(result, ensure_ascii=True)

        self.assertEqual(result["status"], "uploaded")
        self.assertTrue(result["upload_attempted"])
        self.assertEqual(result["drive"]["folder_name"], gdriveops.DEFAULT_SMOKE_FOLDER_NAME)
        self.assertTrue(result["drive"]["file_id_present"])
        self.assertEqual(len(service.files_api.created), 2)
        file_metadata = service.files_api.created[1]
        self.assertEqual(file_metadata["parents"], ["folder-id"])
        self.assertEqual(file_metadata["mimeType"], "application/octet-stream")
        self.assertEqual(file_metadata["appProperties"]["coproscope_surface"], "encrypted-vault-smoke")
        self.assertEqual(file_metadata["appProperties"]["coproscope_protocol"], gdriveops.SYNC_PROTOCOL)
        self.assertEqual(file_metadata["appProperties"]["coproscope_generation"], "2")
        self.assertEqual(file_metadata["appProperties"]["coproscope_parent_sha256"], "2" * 64)
        sync_contract = result["encrypted_candidate"]["sync_contract"]
        self.assertEqual(sync_contract["generation"], 2)
        self.assertEqual(sync_contract["parent_sha256"], "2" * 64)
        self.assertNotIn(str(root), serialized)
        self.assertNotIn("token_drive_file", serialized)
        self.assertNotIn("files(id,name)", serialized)

    def test_upload_smoke_does_not_call_drive_for_bad_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            blob = root / "sync" / "blobs" / "dd" / f"{'d' * 64}.blob"
            token = root / "token_drive_file.json"
            blob.parent.mkdir(parents=True)
            blob.write_bytes(b"ciphertext-only")
            token.write_text(
                json.dumps({"scope": f"{gdriveops.DRIVE_FILE_SCOPE} https://www.googleapis.com/auth/drive"}),
                encoding="utf-8",
            )
            service = _FakeDriveService()

            result = gdriveops.upload_encrypted_drive_smoke(
                sync_root=root / "sync",
                encrypted_path=blob,
                token_path=token,
                drive_service=service,
                media_factory=lambda path: {"file_name": path.name},
            )

        self.assertEqual(result["status"], "action_required")
        self.assertFalse(result["upload_attempted"])
        self.assertEqual(service.files_api.created, [])


if __name__ == "__main__":
    unittest.main()
