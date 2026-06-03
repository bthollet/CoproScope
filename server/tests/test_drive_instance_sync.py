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
            self.assertNotIn("instance_sync_key", sync_text)
            self.assertNotIn("private key", sync_text)
            self.assertNotIn(str(root).lower(), serialized)
            self.assertTrue((state / "cache_instance" / "last_recovered.json").exists())

    def test_second_authorized_post_recovers_update_from_first_post(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sync = root / "Drive-Copro-FICTIF"
            post_a = root / "poste-a-local"
            post_b = root / "poste-b-local"
            instance_a = SimpleNamespace(
                instance_id="copro-fictive",
                drive_shared_state={
                    "dernier_point": "FICTIF travaux votes",
                    "compteur_documents": 3,
                },
            )
            instance_b = SimpleNamespace(instance_id="copro-fictive")

            published = drive_instance_sync.publish_instance_update(instance=instance_a, sync_root=sync, local_state_root=post_a)
            post_b.mkdir()
            (post_b / drive_instance_sync.SYNC_KEY_FILE).write_bytes((post_a / drive_instance_sync.SYNC_KEY_FILE).read_bytes())
            recovered = drive_instance_sync.recover_instance_update(instance=instance_b, sync_root=sync, local_state_root=post_b)
            shared_state = json.loads((post_b / "cache_instance" / drive_instance_sync.SHARED_STATE_FILE).read_text(encoding="utf-8"))

            sync_text = _text(sync).lower()
            serialized = json.dumps({"published": published, "recovered": recovered}, ensure_ascii=True).lower()

            self.assertEqual(published["status"], "published")
            self.assertEqual(recovered["status"], "recovered")
            self.assertTrue((post_b / "cache_instance" / "last_recovered.json").exists())
            self.assertEqual(shared_state["shared_state"]["dernier_point"], "FICTIF travaux votes")
            self.assertEqual(shared_state["shared_state"]["compteur_documents"], 3)
            self.assertNotIn("copro-fictive", sync_text)
            self.assertNotIn("travaux votes", sync_text)
            self.assertNotIn("dernier_point", sync_text)
            self.assertNotIn("instance_sync_key", sync_text)
            self.assertNotIn(str(root).lower(), serialized)

    def test_shared_state_redacts_local_paths_and_secrets_before_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sync = root / "Drive-Copro-FICTIF"
            post_a = root / "poste-a-local"
            post_b = root / "poste-b-local"
            instance = SimpleNamespace(
                instance_id="copro-fictive",
                payload={
                    "drive_shared_state": {
                        "note": "FICTIF decision partagee",
                        "local_path": str(root / "source-privee"),
                        "token": "secret-FICTIF-a-ne-pas-copier",
                    }
                },
            )

            drive_instance_sync.publish_instance_update(instance=instance, sync_root=sync, local_state_root=post_a)
            post_b.mkdir()
            (post_b / drive_instance_sync.SYNC_KEY_FILE).write_bytes((post_a / drive_instance_sync.SYNC_KEY_FILE).read_bytes())
            drive_instance_sync.recover_instance_update(instance=instance, sync_root=sync, local_state_root=post_b)
            shared_state = json.loads((post_b / "cache_instance" / drive_instance_sync.SHARED_STATE_FILE).read_text(encoding="utf-8"))
            shared_text = json.dumps(shared_state, ensure_ascii=True).lower()

            self.assertEqual(shared_state["shared_state"]["note"], "FICTIF decision partagee")
            self.assertEqual(shared_state["shared_state"]["local_path"], "[masque]")
            self.assertEqual(shared_state["shared_state"]["token"], "[masque]")
            self.assertNotIn(str(root).lower(), shared_text)
            self.assertNotIn("secret-fictif", shared_text)
            self.assertNotIn("decision partagee", _text(sync).lower())

    def test_two_authorized_posts_round_trip_without_cleartext_in_drive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sync = root / "Drive-Copro-FICTIF"
            post_a = root / "poste-a-local"
            post_b = root / "poste-b-local"
            instance = SimpleNamespace(instance_id="copro-fictive")

            first_publish = drive_instance_sync.publish_instance_update(instance=instance, sync_root=sync, local_state_root=post_a)
            post_b.mkdir()
            (post_b / drive_instance_sync.SYNC_KEY_FILE).write_bytes((post_a / drive_instance_sync.SYNC_KEY_FILE).read_bytes())
            first_recover = drive_instance_sync.recover_instance_update(instance=instance, sync_root=sync, local_state_root=post_b)
            second_publish = drive_instance_sync.publish_instance_update(instance=instance, sync_root=sync, local_state_root=post_b)
            second_recover = drive_instance_sync.recover_instance_update(instance=instance, sync_root=sync, local_state_root=post_a)

            sync_text = _text(sync).lower()
            self.assertEqual(first_publish["status"], "published")
            self.assertEqual(first_recover["status"], "recovered")
            self.assertEqual(second_publish["status"], "published")
            self.assertEqual(second_recover["status"], "recovered")
            self.assertEqual(second_publish["sync_surface"]["encrypted_file_count"], 2)
            self.assertNotIn("copro-fictive", sync_text)
            self.assertNotIn("instance_sync_key", sync_text)
            self.assertNotIn("coproscope-drive-demo-canary", sync_text)

    def test_second_post_with_different_local_key_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sync = root / "Drive-Copro-FICTIF"
            post_a = root / "poste-a-local"
            post_b = root / "poste-b-local"
            instance = SimpleNamespace(instance_id="copro-fictive")

            drive_instance_sync.publish_instance_update(instance=instance, sync_root=sync, local_state_root=post_a)
            recovered = drive_instance_sync.recover_instance_update(instance=instance, sync_root=sync, local_state_root=post_b)

            serialized = json.dumps(recovered, ensure_ascii=True).lower()
            self.assertEqual(recovered["status"], "blocked")
            self.assertIn("recuperation", recovered["result_label"].lower())
            self.assertNotIn(str(root).lower(), serialized)

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
