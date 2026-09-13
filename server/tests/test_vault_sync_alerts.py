from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coproscope.vault.sync_alerts import (
    VaultIntegrityFinding,
    VaultSyncActionCode,
    VaultSyncAlertLevel,
    classify_vault_sync_audit,
    evaluate_vault_sync_alerts,
)
from coproscope.vault.sync_profiles import SyncAudit


class VaultSyncAlertsTests(unittest.TestCase):
    def test_clean_sync_provider_is_information_without_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "events" / "device-a").mkdir(parents=True)
            (root / "events" / "device-a" / "000001.json").write_text("{}", encoding="utf-8")
            (root / "blobs").mkdir()

            report = evaluate_vault_sync_alerts(root, "google_drive_desktop")

        self.assertEqual(report.level, VaultSyncAlertLevel.INFORMATION)
        self.assertEqual(report.lock_mode, "none")
        self.assertFalse(report.publication_suspended)
        self.assertTrue(report.has_action(VaultSyncActionCode.NO_LOCK))
        self.assertTrue(report.notification_required)
        self.assertEqual(report.internal_events[0].event_type, "vault.sync_alert.classified")

    def test_conflict_markers_are_attention_without_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "budget conflicted copy.xlsx").write_text("", encoding="utf-8")
            (root / "events.sync-conflict-20260520.json").write_text("{}", encoding="utf-8")

            report = evaluate_vault_sync_alerts(root, "dropbox")

        self.assertEqual(report.level, VaultSyncAlertLevel.ATTENTION)
        self.assertEqual(report.lock_mode, "none")
        self.assertFalse(report.publication_suspended)
        self.assertTrue(report.has_action(VaultSyncActionCode.NO_LOCK))
        self.assertIn("provider_conflict_markers", {alert.code for alert in report.alerts})

    def test_forbidden_cache_and_temporary_exports_are_protection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()
            (root / ".venv").mkdir()
            (root / ".cache").mkdir()
            (root / "tmp_exports").mkdir()
            (root / "exports_tmp").mkdir()

            report = evaluate_vault_sync_alerts(root, "local_folder")

        self.assertEqual(report.level, VaultSyncAlertLevel.PROTECTION)
        self.assertEqual(report.lock_mode, "none")
        self.assertTrue(report.publication_suspended)
        self.assertFalse(report.has_action(VaultSyncActionCode.NO_LOCK))
        self.assertIn("forbidden_sync_entries", {alert.code for alert in report.alerts})
        self.assertIn(".git", report.sync_audit.forbidden_entries)
        self.assertIn(".venv", report.sync_audit.forbidden_entries)
        self.assertIn(".cache", report.sync_audit.forbidden_entries)
        self.assertIn("tmp_exports", report.sync_audit.forbidden_entries)
        self.assertIn("exports_tmp", report.sync_audit.forbidden_entries)

    def test_temporary_transport_bytes_are_protection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "draft.tmp").write_text("partial", encoding="utf-8")
            (root / "upload.partial").write_text("partial", encoding="utf-8")

            report = evaluate_vault_sync_alerts(root, "onedrive")

        self.assertEqual(report.level, VaultSyncAlertLevel.PROTECTION)
        self.assertTrue(report.publication_suspended)
        self.assertIn("unstable_transport_bytes", {alert.code for alert in report.alerts})

    def test_signature_hash_and_missing_blob_findings_are_incident(self) -> None:
        clean_audit = SyncAudit(
            path="C:/vault/sync",
            profile_id="local_folder",
            forbidden_entries=(),
            conflict_markers=(),
            transport_risks=(),
        )

        report = classify_vault_sync_audit(
            clean_audit,
            integrity_findings=[
                VaultIntegrityFinding(
                    code="missing_signature",
                    detail="event has no signature",
                    path="events/device-a/000001.json",
                )
            ],
            integrity_report={
                "valid": False,
                "errors": [
                    "events/device-a/000002_bad.json: event hash does not match filename",
                    "events/device-a/000003_good.json: missing blob abc123",
                ],
            },
        )

        self.assertEqual(report.level, VaultSyncAlertLevel.INCIDENT)
        self.assertEqual(report.lock_mode, "read_only")
        self.assertFalse(report.publication_suspended)
        self.assertTrue(report.has_action(VaultSyncActionCode.LOCK_READONLY))
        alert = next(alert for alert in report.alerts if alert.code == "vault_integrity_incident")
        self.assertIn("events/device-a/000001.json", alert.paths)
        self.assertIn("events/device-a/000002_bad.json", alert.paths)
        self.assertIn("events/device-a/000003_good.json", alert.paths)


if __name__ == "__main__":
    unittest.main()
