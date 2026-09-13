from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from coproscope.vault import core as vault


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _write_snapshot(path: Path, snapshot: dict[str, Any], *, update_filename: bool) -> Path:
    data = _canonical_bytes(snapshot)
    target = path
    if update_filename:
        prefix = path.stem.split("_", 1)[0]
        target = path.with_name(f"{prefix}_{hashlib.sha256(data).hexdigest()}.snapshot")
    if target != path and path.exists():
        path.unlink()
    target.write_bytes(data)
    return target


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "cryptography is required for vault tests")
class CoproScopeVaultSnapshotHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.local_root = self.root / "local"
        self.sync_root = self.root / "sync"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _create_snapshot(self) -> Path:
        vault.vault_init(self.local_root, self.sync_root)
        source = self.root / "piece.txt"
        source.write_text("snapshot hardening content", encoding="utf-8")
        vault.vault_import(self.local_root, self.sync_root, source)
        result = vault.vault_snapshot(self.local_root, self.sync_root)
        snapshot_path = Path(result["snapshot_path"])

        verify = vault.vault_verify(self.local_root, self.sync_root)
        self.assertTrue(verify["valid"], verify)
        self.assertEqual(verify["snapshots"], 1)
        return snapshot_path

    def test_verify_rejects_snapshot_file_hash_mismatch(self) -> None:
        snapshot_path = self._create_snapshot()
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["created_at"] = "2026-05-20T00:00:00+00:00"
        _write_snapshot(snapshot_path, snapshot, update_filename=False)

        verify = vault.vault_verify(self.local_root, self.sync_root)

        self.assertFalse(verify["valid"], verify)
        self.assertTrue(any("snapshot hash does not match filename" in error for error in verify["errors"]))

    def test_verify_rejects_snapshot_encrypted_payload_hash_mismatch(self) -> None:
        snapshot_path = self._create_snapshot()
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["encrypted_payload_hash"] = "0" * 64
        _write_snapshot(snapshot_path, snapshot, update_filename=True)

        verify = vault.vault_verify(self.local_root, self.sync_root)

        self.assertFalse(verify["valid"], verify)
        self.assertTrue(any("invalid encrypted payload hash" in error for error in verify["errors"]))

    def test_verify_rejects_snapshot_vault_id_mismatch(self) -> None:
        snapshot_path = self._create_snapshot()
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["vault_id"] = "vault_other"
        _write_snapshot(snapshot_path, snapshot, update_filename=True)

        verify = vault.vault_verify(self.local_root, self.sync_root)

        self.assertFalse(verify["valid"], verify)
        self.assertTrue(any("vault_id does not match vault" in error for error in verify["errors"]))

    def test_verify_rejects_snapshot_payload_that_cannot_be_decrypted(self) -> None:
        snapshot_path = self._create_snapshot()
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        ciphertext = bytearray(base64.b64decode(snapshot["encrypted_payload"].encode("ascii")))
        ciphertext[0] ^= 1
        tampered_ciphertext = bytes(ciphertext)
        snapshot["encrypted_payload"] = base64.b64encode(tampered_ciphertext).decode("ascii")
        snapshot["encrypted_payload_hash"] = hashlib.sha256(tampered_ciphertext).hexdigest()
        _write_snapshot(snapshot_path, snapshot, update_filename=True)

        verify = vault.vault_verify(self.local_root, self.sync_root)

        self.assertFalse(verify["valid"], verify)
        self.assertTrue(any("snapshot encrypted payload is not decryptable" in error for error in verify["errors"]))

    def test_verify_rejects_invalid_snapshot_json(self) -> None:
        snapshot_path = self._create_snapshot()
        snapshot_path.write_text('{"schema_version":', encoding="utf-8")

        verify = vault.vault_verify(self.local_root, self.sync_root)

        self.assertFalse(verify["valid"], verify)
        self.assertTrue(any("Expecting value" in error for error in verify["errors"]))


if __name__ == "__main__":
    unittest.main()
