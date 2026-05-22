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

    def test_rebuild_cache_exposes_business_tables_without_worker_branching(self) -> None:
        db_path = self.local_root / "business.sqlite3"
        events = [
            self._event(
                "evt_point",
                "point_created",
                "POINT-ASSURANCE",
                {
                    "point_id": "POINT-ASSURANCE",
                    "title": "Attestation assurance absente",
                    "category": "assurance",
                    "severity": "P1",
                    "proof_ids": ["PRF-ASSURANCE"],
                },
                sequence=1,
            ),
            self._event(
                "evt_action",
                "action_created",
                "ACT-ASSURANCE",
                {
                    "action_id": "ACT-ASSURANCE",
                    "title": "Demander l'attestation assurance 2026",
                    "status": "open",
                    "priority": "P1",
                    "owner_ref": "syndic",
                    "due_at": "2026-05-27",
                    "related_point_ids": ["POINT-ASSURANCE"],
                    "expected_piece_id": "PCE-ASSURANCE",
                    "expected_piece_label": "Attestation assurance 2026",
                    "holder_label": "Syndic",
                },
                sequence=2,
            ),
            self._event(
                "evt_action_update",
                "action_created",
                "ACT-ASSURANCE",
                {
                    "action_id": "ACT-ASSURANCE",
                    "status": "waiting",
                    "next_step": "Relancer si aucune reponse avant echeance.",
                },
                sequence=3,
            ),
            self._event(
                "evt_request",
                "request_created",
                "REQ-ASSURANCE",
                {
                    "request_id": "REQ-ASSURANCE",
                    "subject": "Attestation assurance 2026",
                    "channel": "portail_syndic",
                    "status": "local_draft",
                    "linked_action_id": "ACT-ASSURANCE",
                    "linked_piece_id": "PCE-ASSURANCE",
                },
                sequence=4,
            ),
            self._event(
                "evt_request_action",
                "request_action_recorded",
                "JRN-ASSURANCE-1",
                {
                    "journal_id": "JRN-ASSURANCE-1",
                    "request_id": "REQ-ASSURANCE",
                    "action_type": "copied_locally",
                    "summary": "Relance preparee et copiee localement.",
                    "status_after": "recorded_locally",
                },
                sequence=5,
            ),
            self._event(
                "evt_export",
                "passation_export_created",
                "EXP-PASSATION",
                {
                    "export_id": "EXP-PASSATION",
                    "format": "json",
                    "profile": "conseil_syndical",
                    "source_object_ids": ["ACT-ASSURANCE", "REQ-ASSURANCE"],
                },
                sequence=6,
            ),
        ]

        result = reconstruction.rebuild_cache_from_events(events, db_path, vault_id="vault_test")

        self.assertEqual(result["points"], 1)
        self.assertEqual(result["actions"], 1)
        self.assertEqual(result["expected_pieces"], 1)
        self.assertEqual(result["requests"], 1)
        self.assertGreaterEqual(result["object_links"], 4)

        connection = sqlite3.connect(db_path)
        try:
            connection.row_factory = sqlite3.Row
            tables = {
                row["name"]
                for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
            }
            self.assertIn("source_import_map", tables)
            self.assertIn("object_event_sources", tables)
            self.assertIn("object_links", tables)

            action = connection.execute("SELECT * FROM actions WHERE action_id = 'ACT-ASSURANCE'").fetchone()
            self.assertEqual(action["status"], "waiting")
            self.assertEqual(json.loads(action["source_event_ids_json"]), ["evt_action", "evt_action_update"])

            piece = connection.execute("SELECT * FROM expected_pieces WHERE piece_id = 'PCE-ASSURANCE'").fetchone()
            self.assertEqual(piece["label"], "Attestation assurance 2026")
            self.assertEqual(piece["linked_action_id"], "ACT-ASSURANCE")

            request = connection.execute("SELECT * FROM requests WHERE request_id = 'REQ-ASSURANCE'").fetchone()
            self.assertEqual(request["status"], "recorded_locally")

            export = connection.execute("SELECT * FROM exports WHERE export_id = 'EXP-PASSATION'").fetchone()
            self.assertEqual(export["source_of_truth"], 0)

            target_indexes = {
                row["name"] for row in connection.execute("PRAGMA index_list('object_links')").fetchall()
            }
            self.assertIn("idx_object_links_target", target_indexes)
        finally:
            connection.close()

    def test_audit360_import_funnels_rows_into_business_tables_idempotently(self) -> None:
        db_path = self.local_root / "audit360.sqlite3"
        reconstruction.rebuild_cache_from_events([], db_path, vault_id="vault_test")
        rows = [
            {
                "source_kind": "audit360_matrix",
                "source_file": "matrice_preuves_attendues.csv",
                "source_row_id": "row-17",
                "control_id": "CTRL-ASSURANCE",
                "point_de_controle": "Attestation assurance immeuble",
                "constat": "La piece n'est pas visible dans le corpus transmis.",
                "risque_concret": "Le conseil syndical ne peut pas verifier la couverture.",
                "preuve_attendue": "Attestation assurance multirisque 2026",
                "action_a_faire": "Demander l'attestation au syndic.",
                "acteur_ou_entreprise": "Syndic",
                "priorite": "P1",
                "statut_action": "open",
            }
        ]

        first = reconstruction.import_audit360_rows(
            db_path,
            rows,
            import_run_id="run-a",
            imported_at="2026-05-21T12:00:00+00:00",
        )
        second = reconstruction.import_audit360_rows(
            db_path,
            rows,
            import_run_id="run-a",
            imported_at="2026-05-21T12:00:00+00:00",
        )

        self.assertEqual(first["created"]["points"], 1)
        self.assertEqual(first["created"]["actions"], 1)
        self.assertEqual(first["created"]["expected_pieces"], 1)
        self.assertEqual(first["source_import_map"], 3)
        self.assertEqual(second["created"]["points"], 0)
        self.assertEqual(second["created"]["actions"], 0)
        self.assertEqual(second["created"]["expected_pieces"], 0)
        self.assertEqual(second["created"]["source_import_map"], 0)

        connection = sqlite3.connect(db_path)
        try:
            connection.row_factory = sqlite3.Row
            action = connection.execute("SELECT * FROM actions").fetchone()
            piece = connection.execute("SELECT * FROM expected_pieces").fetchone()
            mappings = connection.execute("SELECT object_kind, object_id FROM source_import_map ORDER BY object_kind").fetchall()
            links = connection.execute(
                "SELECT source_kind, relation, target_kind FROM object_links ORDER BY source_kind, relation, target_kind"
            ).fetchall()

            self.assertEqual(action["title"], "Demander l'attestation au syndic.")
            self.assertEqual(action["source_module"], "audit360")
            self.assertEqual(piece["label"], "Attestation assurance multirisque 2026")
            self.assertEqual(piece["linked_action_id"], action["action_id"])
            self.assertEqual([row["object_kind"] for row in mappings], ["action", "expected_piece", "point"])
            self.assertIn(("action", "expects", "expected_piece"), [tuple(row) for row in links])
            self.assertIn(("action", "relates_to", "point"), [tuple(row) for row in links])
        finally:
            connection.close()

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
