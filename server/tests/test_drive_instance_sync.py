from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from coproscope.modules import drive_instance_sync


class DriveInstanceSyncTests(unittest.TestCase):
    def test_publish_and_recover_keep_cleartext_and_state_outside_drive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sync = root / "Drive-Copro-FICTIF"
            state = root / "etat-local"
            instance = SimpleNamespace(instance_id="copro-fictive")

            published = drive_instance_sync.publish_instance_update(instance=instance, sync_root=sync, local_state_root=state)
            recovered = drive_instance_sync.recover_instance_update(instance=instance, sync_root=sync, local_state_root=state)
            again = drive_instance_sync.recover_instance_update(instance=instance, sync_root=sync, local_state_root=state)
            sync_text = _text(sync).lower()
            serialized = json.dumps({"published": published, "recovered": recovered, "again": again}, ensure_ascii=True).lower()

            self.assertEqual(published["status"], "published")
            self.assertEqual(recovered["status"], "recovered")
            self.assertEqual(again["status"], "idle")
            self.assertGreater(published["sync_surface"]["encrypted_file_count"], 0)
            self.assertGreater(published["sync_surface"]["public_key_count"], 0)
            self.assertNotIn("coproscope-drive-demo-canary", sync_text)
            self.assertNotIn("device_key", sync_text)
            self.assertNotIn("private key", sync_text)
            self.assertNotIn(str(root).lower(), serialized)
            self.assertTrue((state / "cache_instance" / "last_recovered.json").exists())

    def test_local_state_inside_drive_folder_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sync = root / "Drive-Copro-FICTIF"
            instance = SimpleNamespace(instance_id="copro-fictive")

            result = drive_instance_sync.publish_instance_update(
                instance=instance,
                sync_root=sync,
                local_state_root=sync / "etat-local",
            )

            self.assertEqual(result["status"], "blocked")
            self.assertIn("Etat local", result["result_label"])

    def test_unexpected_file_in_drive_folder_blocks_publish(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sync = root / "Drive-Copro-FICTIF"
            sync.mkdir()
            (sync / "document-lisible.txt").write_text("FICTIF clair", encoding="utf-8")
            instance = SimpleNamespace(instance_id="copro-fictive")

            result = drive_instance_sync.publish_instance_update(
                instance=instance,
                sync_root=sync,
                local_state_root=root / "etat-local",
            )

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["sync_surface"]["unexpected_file_count"], 1)


def _text(root: Path) -> str:
    chunks: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            chunks.append(path.read_bytes().decode("utf-8", errors="ignore"))
    return "\n".join(chunks)


if __name__ == "__main__":
    unittest.main()
