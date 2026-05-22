from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import secrets
import sqlite3
import tempfile
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from coproscope.vault import local_reconstruction


class CoproScopeVaultLocalReconstructionUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.local_root = self.root / "local"
        self.local_root.mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _event(
        self,
        event_id: str,
        event_type: str,
        object_id: str,
        payload: dict[str, object],
        *,
        author_key_id: str = "ak_alpha",
        device_id: str = "dev_alpha",
        sequence: int = 1,
        created_at: str = "2026-05-20T10:00:00+00:00",
    ) -> local_reconstruction.LocalVaultEvent:
        envelope = {
            "event_id": event_id,
            "event_type": event_type,
            "object_id": object_id,
            "author_key_id": author_key_id,
            "device_id": device_id,
            "sequence": sequence,
            "created_at": created_at,
        }
        return local_reconstruction.LocalVaultEvent.from_envelope(
            envelope,
            payload,
            event_hash=f"hash_{event_id}",
            event_path=f"events/{device_id}/{sequence:012d}.json",
        )

    def test_rebuild_from_decrypted_events_populates_minimal_tables(self) -> None:
        db_path = self.local_root / "cache.sqlite3"
        events = [
            self._event(
                "evt_init",
                "vault_initialized",
                "vault_test",
                {"device_id": "dev_alpha", "author_key_id": "ak_alpha"},
                sequence=1,
            ),
            self._event(
                "evt_doc",
                "document_added",
                "doc_alpha",
                {
                    "document_id": "doc_alpha",
                    "original_name": "pv.pdf",
                    "source_sha256": "source_hash",
                    "size_bytes": 42,
                    "blob_id": "blob_alpha",
                    "blob_sha256": "blob_hash",
                    "imported_at": "2026-05-20T10:01:00+00:00",
                },
                sequence=2,
                created_at="2026-05-20T10:01:00+00:00",
            ),
            self._event(
                "evt_member",
                "member_added",
                "mem_beta",
                {
                    "member_id": "mem_beta",
                    "author_key_id": "ak_beta",
                    "display_name": "Beta Conseil",
                },
                sequence=3,
                created_at="2026-05-20T10:02:00+00:00",
            ),
        ]

        result = local_reconstruction.rebuild_local_reconstruction_from_events(
            events,
            db_path,
            vault_id="vault_test",
            local_root=self.local_root,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["documents"], 1)
        self.assertEqual(result["document_versions"], 1)
        self.assertEqual(result["members"], 2)
        self.assertEqual(result["devices"], 1)
        connection = sqlite3.connect(db_path)
        try:
            connection.row_factory = sqlite3.Row
            tables = {
                row["name"]
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            }
            self.assertEqual(tables, {"documents", "document_versions", "members", "devices", "sync_state"})
            document = connection.execute("SELECT * FROM documents WHERE document_id = 'doc_alpha'").fetchone()
            self.assertEqual(document["original_name"], "pv.pdf")
            member = connection.execute("SELECT * FROM members WHERE member_id = 'mem_beta'").fetchone()
            self.assertEqual(member["display_name"], "Beta Conseil")
            sync_state = {
                row["key"]: row["value"]
                for row in connection.execute("SELECT key, value FROM sync_state").fetchall()
            }
            self.assertEqual(sync_state["event_count"], "3")
        finally:
            connection.close()

    def test_reconstruction_db_path_must_stay_under_local_root(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "local_root"):
            local_reconstruction.resolve_db_path(self.local_root, self.root / "outside.sqlite3")


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "cryptography is required for vault tests")
class SyntheticVault:
    def __init__(self, root: Path) -> None:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        self.local_root = root / "local"
        self.sync_root = root / "sync"
        self.local_root.mkdir(parents=True)
        for name in ("blobs", "events", "keys"):
            (self.sync_root / name).mkdir(parents=True, exist_ok=True)
        self.vault_id = "vault_" + uuid.uuid4().hex
        self.device_id = "dev_alpha"
        self.vault_key = AESGCM.generate_key(bit_length=256)
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = self.private_key.public_key()
        private_raw = self.private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_raw = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.author_key_id = "ak_" + _sha256_bytes(public_raw)[:16]
        self.created_at = datetime(2026, 5, 20, 10, 0, tzinfo=timezone.utc)
        self.state = {
            "schema_version": "1.0",
            "vault_id": self.vault_id,
            "created_at": self.created_at.isoformat(),
            "local_root": str(self.local_root.resolve()),
            "sync_root": str(self.sync_root.resolve()),
            "device_id": self.device_id,
            "author_key_id": self.author_key_id,
            "vault_key": _b64(self.vault_key),
            "signing_private_key": _b64(private_raw),
            "signing_public_key": _b64(public_raw),
        }
        self._write_json(self.local_root / local_reconstruction.LOCAL_STATE_FILE, self.state)
        self._write_json(
            self.sync_root / "vault.json",
            {
                "schema_version": "1.0",
                "vault_id": self.vault_id,
                "created_at": self.created_at.isoformat(),
            },
        )
        self._write_json(
            self.sync_root / "keys" / f"{self.author_key_id}.json",
            {
                "schema_version": "1.0",
                "key_type": "ed25519-public",
                "author_key_id": self.author_key_id,
                "public_key": _b64(public_raw),
                "created_at": self.created_at.isoformat(),
            },
        )

    def _write_json(self, path: Path, value: Any, *, canonical: bool = False) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if canonical:
            path.write_bytes(_canonical_bytes(value))
        else:
            path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def append_event(self, event_type: str, object_id: str, payload: dict[str, Any]) -> Path:
        return self._append_raw_signed_event(event_type, object_id, payload, author_key_id=self.author_key_id)

    def _append_raw_signed_event(
        self,
        event_type: str,
        object_id: str,
        payload: dict[str, Any],
        *,
        author_key_id: str,
    ) -> Path:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        device_dir = self.sync_root / "events" / self.device_id
        device_dir.mkdir(parents=True, exist_ok=True)
        previous_files = sorted(device_dir.glob("*.json"))
        sequence = len(previous_files) + 1
        previous_hash = _sha256_bytes(previous_files[-1].read_bytes()) if previous_files else ""
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(self.vault_key).encrypt(nonce, _canonical_bytes(payload), None)
        created_at = (self.created_at + timedelta(seconds=sequence)).isoformat()
        event = {
            "event_id": f"evt_{sequence}_{event_type}",
            "vault_id": self.vault_id,
            "schema_version": "1.0",
            "event_type": event_type,
            "author_key_id": author_key_id,
            "device_id": self.device_id,
            "sequence": sequence,
            "created_at": created_at,
            "object_id": object_id,
            "prev_device_event_hash": previous_hash,
            "encrypted_payload_hash": _sha256_bytes(ciphertext),
            "payload_nonce": _b64(nonce),
            "encrypted_payload": _b64(ciphertext),
        }
        event["signature"] = _b64(self.private_key.sign(_canonical_bytes(event)))
        event_hash = _sha256_bytes(_canonical_bytes(event))
        event_path = device_dir / f"{sequence:012d}_{event_hash}.json"
        self._write_json(event_path, event, canonical=True)
        return event_path

    def add_blob(self, plaintext: bytes) -> tuple[str, str]:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(self.vault_key).encrypt(nonce, plaintext, None)
        blob_id = _sha256_bytes(ciphertext)
        blob_path = self.sync_root / "blobs" / blob_id[:2] / f"{blob_id}.blob"
        blob_path.parent.mkdir(parents=True, exist_ok=True)
        blob_path.write_bytes(ciphertext)
        return blob_id, _sha256_bytes(ciphertext)


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "cryptography is required for vault tests")
class CoproScopeVaultLocalReconstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.vault = SyntheticVault(self.root)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _connect_result_db(self, result: dict[str, object]) -> sqlite3.Connection:
        connection = sqlite3.connect(str(result["db_path"]))
        connection.row_factory = sqlite3.Row
        return connection

    def test_rebuild_decrypts_valid_events_into_minimal_sqlite_tables(self) -> None:
        self.vault.append_event(
            "vault_initialized",
            self.vault.vault_id,
            {
                "vault_id": self.vault.vault_id,
                "device_id": self.vault.device_id,
                "author_key_id": self.vault.author_key_id,
            },
        )
        blob_id, blob_sha256 = self.vault.add_blob(b"budget cache local")
        self.vault.append_event(
            "document_added",
            "doc_budget",
            {
                "document_id": "doc_budget",
                "original_name": "budget-2026.txt",
                "source_sha256": _sha256_bytes(b"budget cache local"),
                "size_bytes": 18,
                "blob_id": blob_id,
                "blob_sha256": blob_sha256,
                "imported_at": "2026-05-20T12:00:00+00:00",
            },
        )
        self.vault.append_event(
            "document_version_added",
            "doc_budget",
            {
                "document_id": "doc_budget",
                "blob_id": blob_id,
                "blob_sha256": blob_sha256,
                "source_sha256": "version_source_hash",
                "size_bytes": 18,
                "imported_at": "2026-05-20T12:05:00+00:00",
            },
        )

        result = local_reconstruction.rebuild_local_reconstruction(self.vault.local_root, self.vault.sync_root)

        self.assertTrue(result["ok"])
        self.assertEqual(result["events"], 3)
        self.assertEqual(result["documents"], 1)
        self.assertEqual(result["document_versions"], 2)
        self.assertEqual(result["members"], 1)
        self.assertEqual(result["devices"], 1)
        self.assertEqual(Path(str(result["db_path"])).parent, self.vault.local_root.resolve())

        connection = self._connect_result_db(result)
        try:
            tables = {
                row["name"]
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            }
            self.assertEqual(tables, {"documents", "document_versions", "members", "devices", "sync_state"})

            document = connection.execute("SELECT * FROM documents").fetchone()
            self.assertEqual(document["document_id"], "doc_budget")
            self.assertEqual(document["original_name"], "budget-2026.txt")
            self.assertEqual(document["versions_count"], 2)
            self.assertEqual(document["current_blob_id"], blob_id)

            versions = connection.execute(
                "SELECT version_index, source_sha256 FROM document_versions ORDER BY version_index"
            ).fetchall()
            self.assertEqual([row["version_index"] for row in versions], [1, 2])
            self.assertEqual(versions[1]["source_sha256"], "version_source_hash")

            member = connection.execute("SELECT * FROM members").fetchone()
            self.assertEqual(member["author_key_id"], self.vault.author_key_id)
            self.assertEqual(member["status"], "active")

            device = connection.execute("SELECT * FROM devices").fetchone()
            self.assertEqual(device["device_id"], self.vault.device_id)
            self.assertEqual(device["event_count"], 3)
            self.assertEqual(device["last_sequence"], 3)

            sync_state = {
                row["key"]: row["value"]
                for row in connection.execute("SELECT key, value FROM sync_state").fetchall()
            }
            self.assertEqual(sync_state["schema_version"], local_reconstruction.SCHEMA_VERSION)
            self.assertEqual(sync_state["event_count"], "3")
            self.assertEqual(sync_state["source_local_root"], str(self.vault.local_root.resolve()))
        finally:
            connection.close()

    def test_rebuild_tracks_member_and_device_lifecycle_events(self) -> None:
        self.vault.append_event(
            "vault_initialized",
            self.vault.vault_id,
            {"device_id": self.vault.device_id, "author_key_id": self.vault.author_key_id},
        )
        self.vault.append_event(
            "member_added",
            "mem_beta",
            {
                "member_id": "mem_beta",
                "author_key_id": "ak_beta",
                "display_name": "Beta Conseil",
                "email": "beta@example.test",
                "role": "conseil_syndical",
            },
        )
        self.vault.append_event(
            "device_registered",
            "dev_beta",
            {"device_id": "dev_beta", "member_id": "mem_beta", "author_key_id": "ak_beta"},
        )
        self.vault.append_event("device_revoked", "dev_beta", {"device_id": "dev_beta", "member_id": "mem_beta"})
        self.vault.append_event("member_revoked", "mem_beta", {"member_id": "mem_beta"})

        result = local_reconstruction.rebuild_local_reconstruction(self.vault.local_root, self.vault.sync_root)

        self.assertEqual(result["events"], 5)
        self.assertEqual(result["members"], 2)
        self.assertEqual(result["devices"], 2)
        connection = self._connect_result_db(result)
        try:
            member = connection.execute("SELECT * FROM members WHERE member_id = 'mem_beta'").fetchone()
            self.assertEqual(member["author_key_id"], "ak_beta")
            self.assertEqual(member["display_name"], "Beta Conseil")
            self.assertEqual(member["email"], "beta@example.test")
            self.assertEqual(member["role"], "conseil_syndical")
            self.assertEqual(member["status"], "revoked")
            self.assertIsNotNone(member["revoked_at"])

            device = connection.execute("SELECT * FROM devices WHERE device_id = 'dev_beta'").fetchone()
            self.assertEqual(device["member_id"], "mem_beta")
            self.assertEqual(device["author_key_id"], "ak_beta")
            self.assertEqual(device["status"], "revoked")
            self.assertEqual(device["event_count"], 0)
        finally:
            connection.close()

    def test_rebuild_refuses_invalid_event_chain_before_writing_db(self) -> None:
        event_path = self.vault.append_event(
            "vault_initialized",
            self.vault.vault_id,
            {"device_id": self.vault.device_id, "author_key_id": self.vault.author_key_id},
        )
        envelope = json.loads(event_path.read_text(encoding="utf-8"))
        envelope["event_type"] = "vault_initialized_tampered"
        event_path.write_text(json.dumps(envelope, sort_keys=True, separators=(",", ":")), encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "invalid vault"):
            local_reconstruction.rebuild_local_reconstruction(self.vault.local_root, self.vault.sync_root)

        self.assertFalse(local_reconstruction.default_db_path(self.vault.local_root).exists())

    def test_rebuild_rejects_blob_id_that_could_escape_sync_root(self) -> None:
        self.vault.append_event(
            "vault_initialized",
            self.vault.vault_id,
            {"device_id": self.vault.device_id, "author_key_id": self.vault.author_key_id},
        )
        self.vault.append_event(
            "document_added",
            "doc_escape",
            {
                "document_id": "doc_escape",
                "original_name": "escape.txt",
                "source_sha256": _sha256_bytes(b"escape"),
                "size_bytes": 6,
                "blob_id": "..\\outside\\secret",
                "blob_sha256": "not_a_real_hash",
                "imported_at": "2026-05-20T12:00:00+00:00",
            },
        )

        with self.assertRaisesRegex(RuntimeError, "Invalid blob id|invalid blob id"):
            local_reconstruction.rebuild_local_reconstruction(self.vault.local_root, self.vault.sync_root)

        self.assertFalse(local_reconstruction.default_db_path(self.vault.local_root).exists())

    def test_rebuild_rejects_author_key_id_that_could_escape_sync_root(self) -> None:
        malicious_author_key_id = "..\\outside\\key"
        event_path = self.vault._append_raw_signed_event(
            "vault_initialized",
            self.vault.vault_id,
            {"device_id": self.vault.device_id, "author_key_id": malicious_author_key_id},
            author_key_id=malicious_author_key_id,
        )

        with self.assertRaisesRegex(RuntimeError, "Invalid author_key_id"):
            local_reconstruction.rebuild_local_reconstruction(self.vault.local_root, self.vault.sync_root)

        self.assertTrue(event_path.exists())
        self.assertFalse(local_reconstruction.default_db_path(self.vault.local_root).exists())

    def test_rebuild_rejects_vault_verify_failures_before_writing_db(self) -> None:
        self.vault.append_event(
            "vault_initialized",
            self.vault.vault_id,
            {"device_id": self.vault.device_id, "author_key_id": self.vault.author_key_id},
        )
        snapshot_dir = self.vault.sync_root / "snapshots"
        snapshot_dir.mkdir()
        (snapshot_dir / "bad.snapshot").write_text("[]", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "Invalid snapshot JSON payload"):
            local_reconstruction.rebuild_local_reconstruction(self.vault.local_root, self.vault.sync_root)

        self.assertFalse(local_reconstruction.default_db_path(self.vault.local_root).exists())


if __name__ == "__main__":
    unittest.main()
