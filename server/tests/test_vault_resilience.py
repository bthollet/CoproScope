from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from coproscope.vault import core as vault
from coproscope.vault import resilience


@unittest.skipUnless(importlib.util.find_spec("cryptography"), "cryptography is required for vault tests")
class CoproScopeVaultResilienceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.local_root = self.root / "local"
        self.sync_root = self.root / "sync"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _init_import(self) -> dict[str, Any]:
        vault.vault_init(self.local_root, self.sync_root)
        source = self.root / "piece.txt"
        source.write_text("resilience vault content", encoding="utf-8")
        return vault.vault_import(self.local_root, self.sync_root, source)

    def _init_import_snapshot(self) -> dict[str, Any]:
        result = self._init_import()
        vault.vault_snapshot(self.local_root, self.sync_root)
        return result

    def _append_document_event(self, payload: dict[str, Any]) -> None:
        roots = vault.roots_from_args(
            type("Args", (), {"local_root": str(self.local_root), "sync_root": str(self.sync_root)})()
        )
        state = vault._load_state(roots.local_root)
        vault.append_event(roots, state, "document_added", str(payload.get("document_id", "doc")), payload)

    def _write_json(self, relative_path: str, payload: dict[str, Any]) -> Path:
        path = self.sync_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return path

    def _write_reader_replica(self) -> None:
        self._write_json(
            "replicas/reader-replica.json",
            {
                "schema_version": "coproscope-vault-replica-v1",
                "replica_id": "replica_reader_1",
                "role": "reader",
                "read_only": True,
                "owner_role": "coowner",
                "last_checked_at": "2026-05-20T10:00:00+00:00",
            },
        )

    def test_audit_counts_vault_and_reports_baseline_capture_risks(self) -> None:
        self._init_import()

        without_snapshot = resilience.audit_survivability(self.local_root, self.sync_root)
        self.assertEqual(without_snapshot["events"], 2)
        self.assertEqual(without_snapshot["blobs"], 1)
        self.assertEqual(without_snapshot["snapshots"], 0)
        self.assertIn("no_snapshot", without_snapshot["risks"])
        self.assertIn("single_device", without_snapshot["risks"])
        self.assertIn("no_recovery_key", without_snapshot["risks"])
        self.assertIn("no_key_quorum", without_snapshot["risks"])
        self.assertIn("no_coowner_recovery_guardian", without_snapshot["risks"])
        self.assertIn("no_reader_replica", without_snapshot["risks"])

        vault.vault_snapshot(self.local_root, self.sync_root)
        with_snapshot = resilience.audit_survivability(self.local_root, self.sync_root)
        self.assertEqual(with_snapshot["snapshots"], 1)
        self.assertNotIn("no_snapshot", with_snapshot["risks"])
        self.assertEqual(with_snapshot["counts"]["event_devices"], 1)

    def test_audit_reports_missing_blob_and_forbidden_sync_entry(self) -> None:
        import_result = self._init_import_snapshot()
        Path(import_result["blob_path"]).unlink()
        (self.sync_root / ".git").mkdir()

        report = resilience.audit_survivability(self.local_root, self.sync_root)

        self.assertEqual(report["status"], "incomplete")
        self.assertIn("missing_blob", report["risks"])
        self.assertIn("forbidden_entries", report["risks"])
        self.assertEqual(report["counts"]["missing_blobs"], 1)
        self.assertTrue(report["missing_blobs"][0]["expected_path"].startswith("blobs/"))
        self.assertTrue(any(entry.endswith(".git") for entry in report["forbidden_entries"]))

    def test_audit_reports_invalid_blob_id_without_escaping_sync_root(self) -> None:
        vault.vault_init(self.local_root, self.sync_root)
        self._append_document_event(
            {
                "document_id": "doc_escape",
                "original_name": "escape.txt",
                "source_sha256": "source_hash",
                "size_bytes": 6,
                "blob_id": "..\\outside\\secret",
                "blob_sha256": "not_a_real_hash",
            }
        )

        report = resilience.audit_survivability(self.local_root, self.sync_root)

        self.assertIn("missing_blob", report["risks"])
        self.assertEqual(report["missing_blobs"][0]["blob_id"], "..\\outside\\secret")
        self.assertEqual(report["missing_blobs"][0]["expected_path"], "")
        self.assertTrue(any("invalid blob id" in warning["warning"] for warning in report["warnings"]))

    def test_reader_replica_manifest_removes_reader_replica_risk(self) -> None:
        self._init_import_snapshot()
        self._write_reader_replica()

        report = resilience.audit_survivability(self.local_root, self.sync_root)

        self.assertNotIn("no_reader_replica", report["risks"])
        self.assertEqual(report["counts"]["replicas"], 1)
        self.assertEqual(report["counts"]["reader_replicas"], 1)
        self.assertEqual(report["reader_replicas"][0]["replica_id"], "replica_reader_1")

    def test_recovery_quorum_compartments_and_coowner_archive_are_reported(self) -> None:
        self._init_import_snapshot()
        self._write_reader_replica()
        self._write_json(
            "recovery/recovery-key.json",
            {
                "schema_version": "coproscope-vault-recovery-v1",
                "recovery_key_id": "rk_collective",
                "kind": "recovery_key",
                "quorum_required": 2,
                "shares": [
                    {"holder_id": "cs_alpha", "holder_role": "cs"},
                    {"holder_id": "copro_beta", "holder_role": "coowner_non_cs"},
                    {"holder_id": "passation_guardian", "holder_role": "external_guardian"},
                ],
            },
        )
        self._write_json(
            "keys/compartments/collective.json",
            {
                "schema_version": "coproscope-vault-compartment-v1",
                "compartment_id": "collective_open",
                "key_id": "key_collective_open",
                "sensitivity": "coowner_open",
                "encrypted": True,
                "allowed_roles": ["coowner", "cs"],
            },
        )
        self._write_json(
            "exports/coowner-complete-archive.json",
            {
                "schema_version": "coproscope-vault-coowner-archive-v1",
                "archive_id": "archive_full_2026_05_20",
                "complete_archive": True,
                "coowner_downloadable": True,
                "presence_verifiable": True,
                "integrity_verifiable": True,
                "reconstructible_open_scope": True,
                "sensitive_compartments_stay_encrypted": True,
                "downloadable_by": ["coowner"],
            },
        )

        report = resilience.audit_survivability(self.local_root, self.sync_root)

        self.assertNotIn("no_recovery_key", report["risks"])
        self.assertNotIn("no_key_quorum", report["risks"])
        self.assertNotIn("no_coowner_recovery_guardian", report["risks"])
        self.assertTrue(report["recovery_governance"]["quorum_satisfied"])
        self.assertTrue(report["recovery_governance"]["has_coowner_guardian"])
        self.assertTrue(report["recovery_governance"]["no_single_cs_dependency"])
        self.assertEqual(report["counts"]["key_compartments"], 1)
        self.assertTrue(report["coowner_archive"]["available"])
        self.assertTrue(report["coowner_archive"]["verifiable"])
        self.assertTrue(report["coowner_archive"]["reconstructible_open_scope"])
        self.assertTrue(report["coowner_archive"]["sensitive_compartments_stay_encrypted"])
        self.assertNotIn("no_coowner_complete_archive", report["diagnostics"])
        self.assertNotIn("no_key_compartments", report["diagnostics"])


if __name__ == "__main__":
    unittest.main()
