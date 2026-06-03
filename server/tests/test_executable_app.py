from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from coproscope import executable_app


def _make_synthetic_instance(root: Path) -> Path:
    instance = root / "examples" / "synthetic_copro"
    instance.mkdir(parents=True)
    (instance / "instance.yml").write_text("id: demo\nname: Demo\n", encoding="utf-8")
    return instance


class ExecutableAppTests(unittest.TestCase):
    def test_default_config_uses_bundled_synthetic_instance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            instance = _make_synthetic_instance(root)
            config = executable_app.config_from_args(
                [],
                {"COPROSCOPE_UI_TOKEN": "local-token"},
                cwd=root,
                bundle_root=root,
            )

        self.assertEqual(config.instance_root, instance)
        self.assertEqual(config.host, "127.0.0.1")
        self.assertEqual(config.port, 8765)
        self.assertTrue(config.open_window)
        self.assertFalse(config.open_browser)
        self.assertEqual(config.url, "http://127.0.0.1:8765/?token=local-token")

    def test_env_instance_root_overrides_demo_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            selected = Path(directory) / "selected"
            selected.mkdir()
            config = executable_app.config_from_args(
                [],
                {
                    "COPROSCOPE_INSTANCE_ROOT": str(selected),
                    "COPROSCOPE_UI_PORT": "8790",
                    "COPROSCOPE_NO_BROWSER": "1",
                    "COPROSCOPE_UI_TOKEN": "abc",
                },
                cwd=Path(directory),
            )

        self.assertEqual(config.instance_root, selected)
        self.assertEqual(config.port, 8790)
        self.assertFalse(config.open_browser)
        self.assertFalse(config.open_window)

    def test_browser_flag_keeps_old_browser_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = executable_app.config_from_args(
                ["--browser"],
                {"COPROSCOPE_UI_TOKEN": "abc"},
                cwd=root,
                bundle_root=root,
            )

        self.assertTrue(config.open_browser)
        self.assertFalse(config.open_window)

    def test_cli_prefix_forwards_to_existing_cli(self) -> None:
        captured: list[str] = []

        def fake_runner(args: list[str]) -> int:
            captured.extend(args)
            return 7

        code = executable_app.main(
            ["cli", "doctor", "--instance-root", "examples/synthetic_copro"],
            runner=fake_runner,
        )

        self.assertEqual(code, 7)
        self.assertEqual(captured, ["doctor", "--instance-root", "examples/synthetic_copro"])

    def test_run_launcher_calls_server_with_tokenized_loopback(self) -> None:
        calls: dict[str, object] = {}
        with tempfile.TemporaryDirectory() as directory:
            instance_root = Path(directory)
            (instance_root / "instance.yml").write_text("id: demo\nname: Demo\n", encoding="utf-8")
            config = executable_app.LauncherConfig(
                instance_root=instance_root,
                year=2026,
                host="127.0.0.1",
                port=8766,
                token="session-token",
                display_mode=executable_app.DISPLAY_NONE,
            )

            def fake_load_instance(instance: str | None, instance_root_value: str | None) -> object:
                calls["load"] = (instance, instance_root_value)
                return {"instance_root": instance_root_value}

            def fake_serve(instance: object, year: int, **kwargs: object) -> None:
                calls["serve"] = (instance, year, kwargs)

            code = executable_app.run_launcher(
                config,
                load_instance_func=fake_load_instance,
                serve_func=fake_serve,
            )

        self.assertEqual(code, 0)
        self.assertEqual(calls["load"], (None, str(instance_root)))
        served_instance, served_year, served_kwargs = calls["serve"]  # type: ignore[misc]
        self.assertEqual(served_instance, {"instance_root": str(instance_root)})
        self.assertEqual(served_year, 2026)
        self.assertEqual(served_kwargs["access_token"], "session-token")
        self.assertFalse(served_kwargs["unsafe_lan"])

    def test_run_launcher_window_starts_server_then_window(self) -> None:
        calls: dict[str, object] = {}
        with tempfile.TemporaryDirectory() as directory:
            instance_root = Path(directory)
            (instance_root / "instance.yml").write_text("id: demo\nname: Demo\n", encoding="utf-8")
            config = executable_app.LauncherConfig(
                instance_root=instance_root,
                year=2026,
                host="127.0.0.1",
                port=8767,
                token="window-token",
                display_mode=executable_app.DISPLAY_WINDOW,
            )

            def fake_load_instance(instance: str | None, instance_root_value: str | None) -> object:
                calls["load"] = (instance, instance_root_value)
                return {"instance_root": instance_root_value}

            def fake_serve(instance: object, year: int, **kwargs: object) -> None:
                calls["serve"] = (instance, year, kwargs)

            def fake_wait(_config: executable_app.LauncherConfig) -> bool:
                deadline = time.monotonic() + 2.0
                while "serve" not in calls and time.monotonic() < deadline:
                    time.sleep(0.01)
                return "serve" in calls

            def fake_window(title: str, url: str) -> None:
                calls["window"] = (title, url)

            code = executable_app.run_launcher(
                config,
                load_instance_func=fake_load_instance,
                serve_func=fake_serve,
                open_window_func=fake_window,
                wait_for_server_func=fake_wait,
            )

        self.assertEqual(code, 0)
        self.assertEqual(calls["load"], (None, str(instance_root)))
        self.assertIn("serve", calls)
        self.assertEqual(calls["window"], ("CoproScope", "http://127.0.0.1:8767/?token=window-token"))


if __name__ == "__main__":
    unittest.main()
