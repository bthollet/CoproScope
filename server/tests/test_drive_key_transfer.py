from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

from coproscope.cli import _dispatch, build_parser
from coproscope.modules import drive_instance_sync, drive_key_transfer


class DriveKeyTransferTests(unittest.TestCase):
    def test_second_post_imports_key_code_then_recovers_first_post_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sync = root / "Drive-Copro-FICTIF"
            post_a = root / "poste-a-local"
            post_b = root / "poste-b-local"
            instance_a = SimpleNamespace(
                instance_id="copro-fictive",
                drive_shared_state={"note": "FICTIF partage via code coffre"},
            )
            instance_b = SimpleNamespace(instance_id="copro-fictive")

            published = drive_instance_sync.publish_instance_update(instance=instance_a, sync_root=sync, local_state_root=post_a)
            key_code = drive_key_transfer.create_sync_key_code(local_state_root=post_a)
            imported = drive_key_transfer.import_sync_key_code(
                local_state_root=post_b,
                secret_code=str(key_code["secret_code"]),
            )
            recovered = drive_instance_sync.recover_instance_update(instance=instance_b, sync_root=sync, local_state_root=post_b)
            shared_state = json.loads((post_b / "cache_instance" / drive_instance_sync.SHARED_STATE_FILE).read_text(encoding="utf-8"))
            sync_text = _text(sync).lower()
            public_result = json.dumps({"published": published, "imported": imported, "recovered": recovered}, ensure_ascii=True).lower()

            self.assertEqual(published["status"], "published")
            self.assertEqual(imported["status"], "imported")
            self.assertEqual(recovered["status"], "recovered")
            self.assertEqual(shared_state["shared_state"]["note"], "FICTIF partage via code coffre")
            self.assertEqual(
                (post_a / drive_instance_sync.SYNC_KEY_FILE).read_bytes(),
                (post_b / drive_instance_sync.SYNC_KEY_FILE).read_bytes(),
            )
            self.assertNotIn("partage via code", sync_text)
            self.assertNotIn("instance_sync_key", sync_text)
            self.assertNotIn("secret_code", public_result)
            self.assertNotIn(str(root).lower(), public_result)

    def test_key_code_file_cli_does_not_print_secret_or_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_a = root / "state-a"
            state_b = root / "state-b"
            code_file = root / "code-temporaire.txt"

            export_args = build_parser().parse_args(
                ["drive", "key-export", "--local-state-root", str(state_a), "--output-file", str(code_file)]
            )
            import_args = build_parser().parse_args(
                ["drive", "key-import", "--local-state-root", str(state_b), "--code-file", str(code_file)]
            )
            export_stdout = io.StringIO()
            import_stdout = io.StringIO()
            with redirect_stdout(export_stdout):
                export_code = _dispatch(export_args)
            with redirect_stdout(import_stdout):
                import_code = _dispatch(import_args)
            output = f"{export_stdout.getvalue()}\n{import_stdout.getvalue()}".lower()

            self.assertEqual(export_code, 0)
            self.assertEqual(import_code, 0)
            self.assertTrue(code_file.exists())
            self.assertEqual((state_a / drive_instance_sync.SYNC_KEY_FILE).read_bytes(), (state_b / drive_instance_sync.SYNC_KEY_FILE).read_bytes())
            self.assertNotIn("csp-drive-key-v1", output)
            self.assertNotIn("secret_code", output)
            self.assertNotIn(str(root).lower(), output)

    def test_import_refuses_tampered_or_conflicting_key_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state_a = root / "state-a"
            state_b = root / "state-b"
            state_c = root / "state-c"

            original = drive_key_transfer.create_sync_key_code(local_state_root=state_a)
            tampered_code = str(original["secret_code"])[:-1] + "0"
            tampered = drive_key_transfer.import_sync_key_code(local_state_root=state_b, secret_code=tampered_code)
            first_import = drive_key_transfer.import_sync_key_code(local_state_root=state_c, secret_code=str(original["secret_code"]))
            other = drive_key_transfer.create_sync_key_code(local_state_root=root / "other-state")
            conflict = drive_key_transfer.import_sync_key_code(local_state_root=state_c, secret_code=str(other["secret_code"]))

            serialized = json.dumps({"tampered": tampered, "conflict": conflict}, ensure_ascii=True).lower()
            self.assertEqual(tampered["status"], "blocked")
            self.assertEqual(first_import["status"], "imported")
            self.assertEqual(conflict["status"], "blocked")
            self.assertFalse((state_b / drive_instance_sync.SYNC_KEY_FILE).exists())
            self.assertNotIn("csp-drive-key-v1", serialized)
            self.assertNotIn(str(root).lower(), serialized)


def _text(root: Path) -> str:
    return "\n".join(path.read_bytes().decode("utf-8", errors="ignore") for path in sorted(root.rglob("*")) if path.is_file())


if __name__ == "__main__":
    unittest.main()
