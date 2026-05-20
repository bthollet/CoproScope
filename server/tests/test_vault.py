from __future__ import annotations

import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from coproscope.vault import core as vault
from coproscope.vault import reconstruction


class CoproScopeVaultReconstructionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.local_root = self.root / "local"

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
    ) -> reconstruction.ReconstructionEvent:
        envelope = {
            "event_id": event_id,
            "event_type": event_type,
            "object_id": object_id,
            "author_key_id": author_key_id,
            "device_id": device_id,
            "sequence": sequence,
            "created_at": created_at,
        }
        return reconstruction.ReconstructionEvent.from_envelope(
            envelope,
            payload,
            event_hash=f"hash_{event_id}",
            event_path=f"events/{device_id}/{sequence:012d}.json",
        )

    def test_rebuild_cache_indexes_documents_identities_and_status_conflicts(self) -> None:
        db_path = self.local_root / "vault_reconstruction.sqlite3"
        events = [
            self._event(
                "evt_init",
                "vault_initialized",
                "vault_test",
                {"vault_id": "vault_test"},
                sequence=1,
                created_at="2026-05-20T10:00:00+00:00",
            ),
            self._event(
                "evt_doc",
                "document_added",
                "doc_alpha",
                {
                    "document_id": "doc_alpha",
                    "original_name": "pv-secret.pdf",
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
                "evt_status_a",
                "status_changed",
                "doc_alpha",
                {"field": "review_status", "status": "approved"},
                sequence=3,
                created_at="2026-05-20T10:02:00+00:00",
            ),
            self._event(
                "evt_status_b",
                "status_changed",
                "doc_alpha",
                {"field": "review_status", "status": "needs_review"},
                author_key_id="ak_beta",
                device_id="dev_beta",
                sequence=1,
                created_at="2026-05-20T10:02:00+00:00",
            ),
        ]

        result = reconstruction.rebuild_cache_from_events(
            events,
            db_path,
            vault_id="vault_test",
            key_records=[
                {
                    "author_key_id": "ak_alpha",
                    "public_key": "alpha_public",
                    "key_type": "ed25519-public",
                    "created_at": "2026-05-20T09:59:00+00:00",
                },
                {
                    "author_key_id": "ak_beta",
                    "public_key": "beta_public",
                    "key_type": "ed25519-public",
                    "created_at": "2026-05-20T09:59:00+00:00",
                },
            ],
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["events"], 4)
        self.assertEqual(result["documents"], 1)
        self.assertEqual(result["identities"], 2)
        self.assertEqual(result["status_observations"], 2)
        self.assertEqual(result["conflicts"], 1)

        connection = sqlite3.connect(db_path)
        try:
            connection.row_factory = sqlite3.Row
            document = connection.execute("SELECT * FROM documents WHERE document_id = 'doc_alpha'").fetchone()
            self.assertEqual(document["original_name"], "pv-secret.pdf")
            self.assertEqual(document["current_blob_id"], "blob_alpha")
            self.assertEqual(document["versions_count"], 1)

            alpha = connection.execute("SELECT * FROM identities WHERE author_key_id = 'ak_alpha'").fetchone()
            beta = connection.execute("SELECT * FROM identities WHERE author_key_id = 'ak_beta'").fetchone()
            self.assertEqual(json.loads(alpha["devices_json"]), ["dev_alpha"])
            self.assertEqual(json.loads(beta["devices_json"]), ["dev_beta"])
            self.assertEqual(alpha["event_count"], 3)
            self.assertEqual(beta["event_count"], 1)

            conflict = connection.execute("SELECT * FROM conflicts").fetchone()
            self.assertEqual(conflict["object_id"], "doc_alpha")
            self.assertEqual(conflict["field"], "review_status")
            self.assertEqual(json.loads(conflict["event_ids_json"]), ["evt_status_a", "evt_status_b"])
            values = {item["value"] for item in json.loads(conflict["details_json"])["contenders"]}
            self.assertEqual(values, {"approved", "needs_review"})
        finally:
            connection.close()

    def test_resolution_event_suppresses_open_conflict_but_keeps_observations(self) -> None:
        db_path = self.local_root / "resolved.sqlite3"
        events = [
            self._event("evt_status_a", "status_changed", "doc_alpha", {"field": "status", "status": "approved"}),
            self._event(
                "evt_status_b",
                "status_changed",
                "doc_alpha",
                {"field": "status", "status": "needs_review"},
                author_key_id="ak_beta",
                device_id="dev_beta",
            ),
            self._event(
                "evt_resolved",
                "conflict_resolved",
                "doc_alpha",
                {"object_id": "doc_alpha", "field": "status", "resolution": "approved"},
                sequence=4,
                created_at="2026-05-20T10:05:00+00:00",
            ),
        ]

        result = reconstruction.rebuild_cache_from_events(events, db_path, vault_id="vault_test")

        self.assertEqual(result["status_observations"], 2)
        self.assertEqual(result["conflicts"], 0)

    def test_reconstruction_cache_path_must_stay_under_local_root(self) -> None:
        outside = self.root / "outside.sqlite3"
        with self.assertRaisesRegex(RuntimeError, "local root"):
            reconstruction.resolve_reconstruction_db_path(self.local_root, outside)


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "cryptography is required for vault tests")
class CoproScopeVaultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.local_root = self.root / "local"
        self.sync_root = self.root / "sync"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_init_import_verify_without_plaintext_leak(self) -> None:
        init_result = vault.vault_init(self.local_root, self.sync_root)
        self.assertTrue(init_result["ok"])
        self.assertTrue((self.sync_root / "vault.json").exists())
        self.assertTrue((self.local_root / vault.LOCAL_STATE_FILE).exists())

        source = self.root / "secret-document-alpha.txt"
        source.write_text("TOP SECRET UNIQUE CONTENT 9b3f0d", encoding="utf-8")
        import_result = vault.vault_import(self.local_root, self.sync_root, source)
        self.assertTrue(import_result["ok"])
        self.assertTrue(Path(import_result["blob_path"]).exists())

        verify = vault.vault_verify(self.local_root, self.sync_root)
        self.assertTrue(verify["valid"], verify)
        self.assertEqual(verify["errors"], [])

        forbidden_plaintext = [
            b"secret-document-alpha",
            b"TOP SECRET UNIQUE CONTENT",
            str(source).encode("utf-8"),
        ]
        for path in self.sync_root.rglob("*"):
            if path.is_file():
                data = path.read_bytes()
                for needle in forbidden_plaintext:
                    self.assertNotIn(needle, data, f"{needle!r} leaked in {path}")

    def test_tampered_event_invalidates_verify(self) -> None:
        vault.vault_init(self.local_root, self.sync_root)
        source = self.root / "piece.txt"
        source.write_text("hello", encoding="utf-8")
        result = vault.vault_import(self.local_root, self.sync_root, source)
        event_path = Path(result["event"]["event_path"])

        event = json.loads(event_path.read_text(encoding="utf-8"))
        event["event_type"] = "document_added_tampered"
        event_path.write_text(json.dumps(event, sort_keys=True, separators=(",", ":")), encoding="utf-8")

        verify = vault.vault_verify(self.local_root, self.sync_root)
        self.assertFalse(verify["valid"])
        self.assertTrue(any("signature" in error or "hash" in error for error in verify["errors"]))

    def test_init_is_idempotent_without_duplicate_initial_event(self) -> None:
        first = vault.vault_init(self.local_root, self.sync_root)
        second = vault.vault_init(self.local_root, self.sync_root)

        self.assertTrue(first["created_vault"])
        self.assertTrue(first["created_state"])
        self.assertIsNotNone(first["event"])
        self.assertFalse(second["created_vault"])
        self.assertFalse(second["created_state"])
        self.assertIsNone(second["event"])
        self.assertEqual(second["vault_id"], first["vault_id"])

        status = vault.vault_status(self.local_root, self.sync_root)
        self.assertEqual(status["events"], 1)
        self.assertEqual(status["blobs"], 0)

        verify = vault.vault_verify(self.local_root, self.sync_root)
        self.assertTrue(verify["valid"], verify)

    def test_missing_blob_invalidates_verify(self) -> None:
        vault.vault_init(self.local_root, self.sync_root)
        source = self.root / "piece.txt"
        source.write_text("blob must stay linked", encoding="utf-8")
        result = vault.vault_import(self.local_root, self.sync_root, source)

        Path(result["blob_path"]).unlink()

        verify = vault.vault_verify(self.local_root, self.sync_root)
        self.assertFalse(verify["valid"])
        self.assertTrue(any("missing blob" in error for error in verify["errors"]))

    def test_deleted_first_event_breaks_device_chain(self) -> None:
        init_result = vault.vault_init(self.local_root, self.sync_root)
        source = self.root / "piece.txt"
        source.write_text("hello", encoding="utf-8")
        vault.vault_import(self.local_root, self.sync_root, source)

        Path(init_result["event"]["event_path"]).unlink()

        verify = vault.vault_verify(self.local_root, self.sync_root)
        self.assertFalse(verify["valid"])
        self.assertTrue(
            any("expected sequence 1" in error or "invalid previous event hash" in error for error in verify["errors"])
        )

    def test_forbidden_git_or_venv_entries_are_rejected(self) -> None:
        dirty_sync = self.root / "dirty-sync"
        (dirty_sync / ".venv").mkdir(parents=True)
        with self.assertRaises(RuntimeError):
            vault.vault_init(self.local_root, dirty_sync)

        vault.vault_init(self.local_root, self.sync_root)
        (self.sync_root / ".git").mkdir()
        verify = vault.vault_verify(self.local_root, self.sync_root)
        self.assertFalse(verify["valid"])
        self.assertTrue(any("Forbidden development/runtime entry" in error for error in verify["errors"]))

    def test_status_counts_events_blobs_and_forbidden_entries(self) -> None:
        vault.vault_init(self.local_root, self.sync_root)
        source = self.root / "doc.txt"
        source.write_text("content", encoding="utf-8")
        vault.vault_import(self.local_root, self.sync_root, source)
        status = vault.vault_status(self.local_root, self.sync_root)
        self.assertTrue(status["ok"])
        self.assertGreaterEqual(status["events"], 2)
        self.assertEqual(status["blobs"], 1)
        self.assertEqual(status["forbidden_entries"], [])

    def test_rebuild_local_cache_indexes_verified_import(self) -> None:
        vault.vault_init(self.local_root, self.sync_root)
        source = self.root / "cache-source.txt"
        source.write_text("cache me", encoding="utf-8")
        vault.vault_import(self.local_root, self.sync_root, source)

        result = reconstruction.rebuild_local_cache(self.local_root, self.sync_root)

        self.assertTrue(result["ok"])
        self.assertEqual(result["documents"], 1)
        self.assertGreaterEqual(result["identities"], 1)
        self.assertEqual(Path(result["db_path"]).parent, self.local_root.resolve())
        connection = sqlite3.connect(result["db_path"])
        try:
            document = connection.execute("SELECT original_name FROM documents").fetchone()
            self.assertEqual(document[0], "cache-source.txt")
        finally:
            connection.close()

    def test_snapshot_is_counted_and_does_not_expose_import_plaintext(self) -> None:
        vault.vault_init(self.local_root, self.sync_root)
        source = self.root / "snapshot-secret.txt"
        source.write_text("SNAPSHOT SECRET CONTENT 4fa62a", encoding="utf-8")
        vault.vault_import(self.local_root, self.sync_root, source)

        result = vault.vault_snapshot(self.local_root, self.sync_root)
        snapshot_path = Path(result["snapshot_path"])

        self.assertTrue(result["ok"])
        self.assertTrue(snapshot_path.exists())
        status = vault.vault_status(self.local_root, self.sync_root)
        self.assertEqual(status["snapshots"], 1)
        verify = vault.vault_verify(self.local_root, self.sync_root)
        self.assertTrue(verify["valid"], verify)

        snapshot_bytes = snapshot_path.read_bytes()
        self.assertNotIn(b"snapshot-secret.txt", snapshot_bytes)
        self.assertNotIn(b"SNAPSHOT SECRET CONTENT", snapshot_bytes)


if __name__ == "__main__":
    unittest.main()
