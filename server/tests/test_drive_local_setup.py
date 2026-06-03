from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.modules import drive_local_setup


class DriveLocalSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_prepare_creates_local_encrypted_surface_and_profile(self) -> None:
        base_root = Path(self.tempdir.name) / "local-root"
        profile_root = Path(self.tempdir.name) / "profile"

        result = drive_local_setup.prepare_drive_local_workspace(
            self.instance,
            base_root=base_root,
            profile_root=profile_root,
        )
        settings = drive_local_setup.drive_profile_settings(self.instance, profile_root=profile_root)
        sync_root = Path(str(settings["sync_root"]))
        local_state_root = Path(str(settings["local_state_root"]))
        serialized = json.dumps(result, ensure_ascii=True).lower()

        self.assertEqual(result["status"], "prepared")
        self.assertTrue((sync_root / "packages").is_dir())
        self.assertTrue((sync_root / "devices").is_dir())
        self.assertTrue(local_state_root.is_dir())
        self.assertTrue((profile_root / "config" / "drive_profile.json").is_file())
        self.assertEqual(drive_local_setup.inspect_local_setup(sync_root, local_state_root)["status"], "ready")
        self.assertNotIn(str(base_root).lower(), serialized)
        self.assertNotIn("token", serialized)
        self.assertNotIn("secret", serialized)
        self.assertNotIn("raw", serialized)

    def test_prepare_refuses_cloud_or_repo_locations(self) -> None:
        profile_root = Path(self.tempdir.name) / "profile"

        with self.assertRaises(ValueError):
            drive_local_setup.prepare_drive_local_workspace(
                self.instance,
                base_root=Path(self.tempdir.name) / "Google Drive",
                profile_root=profile_root,
            )

        with self.assertRaises(ValueError):
            drive_local_setup.prepare_drive_local_workspace(
                self.instance,
                base_root=Path(__file__).resolve().parents[2],
                profile_root=profile_root,
            )

    def test_profile_settings_ignores_unsafe_stored_paths(self) -> None:
        profile_root = Path(self.tempdir.name) / "profile"
        profile_path = profile_root / "config" / "drive_profile.json"
        profile_path.parent.mkdir(parents=True)
        profile_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "instances": {
                        "synthetic-copro": {
                            "sync_root": str(Path(self.tempdir.name) / "Google Drive" / "sync"),
                            "local_state_root": str(Path(self.tempdir.name) / "state"),
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

        self.assertEqual(drive_local_setup.drive_profile_settings(self.instance, profile_root=profile_root), {})


if __name__ == "__main__":
    unittest.main()
