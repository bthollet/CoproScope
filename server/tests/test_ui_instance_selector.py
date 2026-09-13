from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.web.app import (
    INSTANCE_SELECTOR_COOKIE_NAME,
    create_instance_selector_app,
    discover_local_instances,
)


class UiInstanceSelectorTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instances_root = Path(self.tempdir.name) / "instances"
        self.instances_root.mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _copy_instance(
        self,
        dirname: str,
        instance_id: str,
        display_name: str,
        *,
        nested: bool = False,
    ):
        target = self.instances_root / dirname / "instance" if nested else self.instances_root / dirname
        shutil.copytree(self.source_example, target)
        config_path = target / "instance.yml"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        payload["instance_id"] = instance_id
        payload["display_name"] = display_name
        config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return load_instance(str(config_path), None)

    def test_discovers_direct_and_nested_local_instances(self) -> None:
        alpha = self._copy_instance("alpha", "alpha", "Residence Alpha")
        self._copy_instance("reconstruction", "reconstruction-sim", "Reconstruction test", nested=True)

        choices = discover_local_instances(alpha)

        self.assertEqual({choice.instance.instance_id for choice in choices}, {"alpha", "reconstruction-sim"})
        self.assertEqual({choice.choice_id for choice in choices}, {"alpha", "reconstruction-sim"})

    def test_selector_switches_instance_with_cookie_without_exposing_paths(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        alpha = self._copy_instance("alpha", "alpha", "Residence Alpha")
        self._copy_instance("beta", "beta", "Residence Beta")
        client = TestClient(create_instance_selector_app(alpha, 2025, access_token="local-secret"))

        self.assertEqual(client.get("/instances").status_code, 403)

        selector = client.get("/instances?token=local-secret")
        self.assertEqual(selector.status_code, 200)
        self.assertIn("Residence Alpha", selector.text)
        self.assertIn("Residence Beta", selector.text)
        self.assertNotIn(str(self.instances_root), selector.text)

        selected = client.get(
            "/instances/select?instance=beta&token=local-secret",
            follow_redirects=False,
        )
        self.assertEqual(selected.status_code, 303)
        self.assertEqual(selected.cookies.get(INSTANCE_SELECTOR_COOKIE_NAME), "beta")

        client.cookies.set(INSTANCE_SELECTOR_COOKIE_NAME, "beta")
        health = client.get("/health?token=local-secret")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["instance"], "beta")


if __name__ == "__main__":
    unittest.main()
