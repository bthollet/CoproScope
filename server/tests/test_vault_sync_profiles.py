from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coproscope.vault.sync_profiles import (
    SYNC_PROFILE_IDS,
    audit_sync_folder,
    get_sync_profile,
    known_sync_profiles,
)


class VaultSyncProfilesTests(unittest.TestCase):
    def test_all_expected_profiles_are_present(self) -> None:
        profiles = known_sync_profiles()

        self.assertEqual([profile.id for profile in profiles], list(SYNC_PROFILE_IDS))
        self.assertEqual(
            {profile.id for profile in profiles},
            {
                "google_drive_desktop",
                "onedrive",
                "dropbox",
                "nextcloud",
                "syncthing_p2p",
                "cold_encrypted_backup",
                "local_folder",
            },
        )
        for profile in profiles:
            self.assertIn(profile.type, {"folder_transport", "peer_to_peer", "offline_backup"})
            self.assertIn(".git", profile.mandatory_exclusions)
            self.assertIn(".venv", profile.mandatory_exclusions)
            self.assertIn("decrypted_blobs", profile.mandatory_exclusions)
            self.assertIn("tmp_exports", profile.mandatory_exclusions)
            self.assertTrue(profile.risks)
            self.assertTrue(profile.conflict_markers)
            self.assertTrue(profile.transport_risk_rules)

    def test_syncthing_is_marked_peer_to_peer(self) -> None:
        profile = get_sync_profile("syncthing_p2p")

        self.assertEqual(profile.type, "peer_to_peer")
        self.assertIn("deletions", " ".join(profile.risks))
        self.assertIn("sync_engine_metadata", {rule.kind for rule in profile.transport_risk_rules})

    def test_audit_detects_forbidden_entries_and_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()
            (root / ".venv").mkdir()
            (root / "nested").mkdir()
            (root / "nested" / "budget (ExampleUser's conflicted copy).xlsx").write_text("", encoding="utf-8")
            (root / "status sync conflict.docx").write_text("", encoding="utf-8")
            (root / "Drive note.gdoc").write_text("", encoding="utf-8")

            audit = audit_sync_folder(root, "dropbox")

        self.assertFalse(audit.clean)
        self.assertIn(".git", audit.forbidden_entries)
        self.assertIn(".venv", audit.forbidden_entries)
        self.assertIn("nested/budget (ExampleUser's conflicted copy).xlsx", audit.conflict_markers)
        self.assertIn("status sync conflict.docx", audit.conflict_markers)
        self.assertIn("Drive note.gdoc", audit.conflict_markers)

    def test_audit_detects_provider_and_p2p_conflict_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "decision edit conflict.docx").write_text("", encoding="utf-8")
            (root / "preuve copie en conflit.pdf").write_text("", encoding="utf-8")
            (root / "events.sync-conflict-20260520.json").write_text("", encoding="utf-8")

            onedrive_audit = audit_sync_folder(root, "onedrive")
            drive_audit = audit_sync_folder(root, "google_drive_desktop")
            syncthing_audit = audit_sync_folder(root, "syncthing_p2p")

        self.assertEqual(onedrive_audit.forbidden_entries, ())
        self.assertIn("decision edit conflict.docx", onedrive_audit.conflict_markers)
        self.assertIn("preuve copie en conflit.pdf", drive_audit.conflict_markers)
        self.assertIn("events.sync-conflict-20260520.json", syncthing_audit.conflict_markers)

    def test_audit_reports_unreliable_transport_risks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "Drive note.gsheet").write_text("", encoding="utf-8")
            (root / "draft.PARTIAL").write_text("", encoding="utf-8")
            (root / "~$budget.xlsx").write_text("", encoding="utf-8")
            (root / "Thumbs.db").write_text("", encoding="utf-8")

            audit = audit_sync_folder(root, "google_drive_desktop")

        risks = {(risk.path, risk.kind, risk.severity) for risk in audit.transport_risks}
        self.assertFalse(audit.clean)
        self.assertIn(("Drive note.gsheet", "provider_placeholder", "error"), risks)
        self.assertIn(("draft.PARTIAL", "partial_write", "error"), risks)
        self.assertIn(("~$budget.xlsx", "partial_write", "error"), risks)
        self.assertIn(("Thumbs.db", "host_metadata", "warning"), risks)

    def test_syncthing_control_files_are_transport_state_not_vault_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".stfolder").mkdir()
            (root / ".stignore").write_text("*.tmp\n", encoding="utf-8")

            audit = audit_sync_folder(root, "syncthing_p2p")

        risks = {(risk.path, risk.kind, risk.severity) for risk in audit.transport_risks}
        self.assertFalse(audit.clean)
        self.assertIn((".stfolder", "sync_engine_metadata", "warning"), risks)
        self.assertIn((".stignore", "sync_engine_metadata", "warning"), risks)

    def test_audit_ignores_clean_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "events").mkdir()
            (root / "events" / "device-a").mkdir()
            (root / "events" / "device-a" / "000001.json").write_text("{}", encoding="utf-8")
            (root / "blobs").mkdir()

            audit = audit_sync_folder(root, "local_folder")

        self.assertTrue(audit.clean)
        self.assertEqual(audit.forbidden_entries, ())
        self.assertEqual(audit.conflict_markers, ())
        self.assertEqual(audit.transport_risks, ())


if __name__ == "__main__":
    unittest.main()
