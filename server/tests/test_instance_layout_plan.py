from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.cli import _dispatch, build_parser
from coproscope.core.common import load_instance
from coproscope.modules.instance_layout import build_instance_layout_plan


class InstanceLayoutPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_build_instance_layout_plan_is_dry_run_and_relative_only(self) -> None:
        private_note = self.instance_root / "raw" / "layout-secret.txt"
        private_note.write_text("PRIVATE_LAYOUT_LEAK", encoding="utf-8")

        plan = build_instance_layout_plan(self.instance)
        payload = json.dumps(plan, ensure_ascii=True)

        self.assertEqual(plan["status"], "planned")
        self.assertTrue(plan["ok"])
        self.assertTrue(plan["dry_run"])
        self.assertFalse(plan["will_modify_files"])
        self.assertEqual(plan["destructive_operations"], [])
        self.assertIn("01 - Deposez les nouveaux fichiers ici/A deposer ici", payload)
        self.assertIn("novice_v1", payload)
        self.assertNotIn("PRIVATE_LAYOUT_LEAK", payload)
        self.assertNotIn(str(self.instance_root), payload)
        self.assertNotIn("file://", payload)
        self.assertNotIn("C:\\", payload)
        for forbidden in ("raw", "restricted", "logs", "private"):
            self.assertNotIn(forbidden, payload.lower())
        self.assertEqual(plan["migration_safety"]["source_of_truth"], False)
        self.assertIn("manifeste doc_id plus sha256", plan["migration_safety"]["required_before_apply"])
        for operation in plan["operations"]:
            self.assertFalse(Path(operation["path"]).is_absolute(), operation)
            self.assertTrue(operation["status"].startswith("dry_run_"), operation)

    def test_build_instance_layout_plan_does_not_create_directories(self) -> None:
        planned_visible = self.instance_root / "01 - Deposez les nouveaux fichiers ici"
        planned_technical = self.instance_root / ".coproscope"
        self.assertFalse(planned_visible.exists())
        self.assertFalse(planned_technical.exists())

        build_instance_layout_plan(self.instance)

        self.assertFalse(planned_visible.exists())
        self.assertFalse(planned_technical.exists())

    def test_instance_layout_plan_cli_outputs_json_without_applying_changes(self) -> None:
        args = build_parser().parse_args(
            [
                "instance",
                "layout",
                "plan",
                "--instance-root",
                str(self.instance_root),
            ]
        )
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = _dispatch(args)

        payload = json.loads(stdout.getvalue())
        output = json.dumps(payload, ensure_ascii=True)

        self.assertEqual(result, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "planned")
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["will_modify_files"])
        self.assertEqual(payload["destructive_operations"], [])
        self.assertFalse((self.instance_root / ".coproscope").exists())
        self.assertNotIn(str(self.instance_root), output)
        self.assertNotIn("raw", output.lower())
        self.assertNotIn("logs", output.lower())


if __name__ == "__main__":
    unittest.main()
