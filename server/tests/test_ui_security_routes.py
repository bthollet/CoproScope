from __future__ import annotations

import ast
import shutil
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app


class UiSecurityRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self, access_token: str | None = None):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")
        return TestClient(create_app(self.instance, 2025, access_token=access_token))

    def test_token_gate_protects_ui_and_exports_when_token_is_configured(self) -> None:
        client = self._client(access_token="local-secret")

        for path in [
            "/",
            "/actions",
            "/exports/actions.csv",
            "/exports/actions.md",
            "/depot",
            "/api/model",
            "/exports/local.zip",
        ]:
            self.assertEqual(client.get(path).status_code, 403, path)

        response = client.get("/?token=local-secret")
        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)

        for path in ["/actions", "/exports/actions.csv", "/exports/actions.md", "/depot", "/api/model", "/exports/local.zip"]:
            self.assertEqual(client.get(path).status_code, 200, path)

        fresh_client = self._client(access_token="local-secret")
        self.assertEqual(fresh_client.get("/exports/actions.csv?token=local-secret").status_code, 200)
        self.assertEqual(fresh_client.get("/api/model", headers={"x-coproscope-token": "local-secret"}).status_code, 200)

    def test_private_roots_and_raw_export_paths_are_never_served(self) -> None:
        for relative in [
            "raw/private_note.txt",
            "restricted/secret.txt",
            "logs/run.log",
            "private/source.txt",
        ]:
            path = self.instance_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("PRIVATE_ROUTE_LEAK", encoding="utf-8")

        client = self._client()
        token_client = self._client(access_token="local-secret")

        for path in [
            "/raw/private_note.txt",
            "/restricted/secret.txt",
            "/logs/run.log",
            "/private/source.txt",
            "/exports/raw/private_note.txt",
            "/exports/restricted/secret.txt",
            "/exports/private/source.txt",
            "/exports/logs/run.log",
        ]:
            response = client.get(path)
            self.assertEqual(response.status_code, 404, path)
            self.assertNotIn("PRIVATE_ROUTE_LEAK", response.text)
            token_response = token_client.get(f"{path}?token=local-secret")
            self.assertEqual(token_response.status_code, 404, path)
            self.assertNotIn("PRIVATE_ROUTE_LEAK", token_response.text)

    def test_local_zip_excludes_forbidden_roots_and_sensitive_mappings(self) -> None:
        allowed = self.instance_root / "outputs" / "reports" / "safe_report.txt"
        allowed.parent.mkdir(parents=True, exist_ok=True)
        allowed.write_text("SAFE_REPORT_INCLUDED", encoding="utf-8")
        unsafe_content = self.instance_root / "outputs" / "accounting" / "unsafe_paths.csv"
        unsafe_content.parent.mkdir(parents=True, exist_ok=True)
        unsafe_content.write_text(
            "doc,path\nDOC-PRIVATE,G:\\Mon Drive\\copro\\raw\\secret.txt\n",
            encoding="utf-8",
        )
        unsafe_binary = self.instance_root / "outputs" / "accounting" / "unsafe.duckdb"
        unsafe_binary.write_bytes(b"BINARY_SHOULD_NOT_EXPORT")

        blocked_files = [
            self.instance_root / "raw" / "raw_secret.txt",
            self.instance_root / "restricted" / "restricted_secret.txt",
            self.instance_root / "logs" / "run.log",
            self.instance_root / "private" / "private_secret.txt",
            self.instance_root / "outputs" / "reports" / "private" / "nested_secret.txt",
            self.instance_root / "outputs" / "privacy" / "table_correspondance_biffage.csv",
            self.instance_root / "outputs" / "deposits" / "redaction_mapping.csv",
        ]
        for path in blocked_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("ZIP_EXPORT_LEAK", encoding="utf-8")

        response = self._client(access_token="local-secret").get("/exports/local.zip?token=local-secret")

        self.assertEqual(response.status_code, 200)
        with zipfile.ZipFile(BytesIO(response.content)) as archive:
            names = archive.namelist()
            combined = b"".join(archive.read(name) for name in names)

        self.assertIn("outputs/reports/safe_report.txt", names)
        self.assertIn(b"SAFE_REPORT_INCLUDED", combined)
        self.assertNotIn(b"ZIP_EXPORT_LEAK", combined)
        self.assertNotIn(b"Mon Drive", combined)
        self.assertNotIn(b"raw\\secret", combined)
        self.assertNotIn("outputs/accounting/unsafe_paths.csv", names)
        self.assertNotIn("outputs/accounting/unsafe.duckdb", names)
        self.assertFalse(any(name.startswith(("raw/", "restricted/", "logs/", "private/")) for name in names))
        self.assertFalse(any("/private/" in name for name in names))
        self.assertFalse(any("table_correspondance" in name or "mapping" in name for name in names))

    def test_ui_open_test_dispatch_stays_foreground_without_browser_or_hidden_process(self) -> None:
        from coproscope import cli

        args = cli.build_parser().parse_args(
            [
                "ui",
                "open-test",
                "--instance-root",
                str(self.instance.instance_root),
                "--year",
                "2025",
                "--host",
                "127.0.0.1",
                "--port",
                "8769",
                "--token",
                "qa-2115-local",
            ]
        )
        with patch("coproscope.web.app.serve") as mocked_serve:
            result = cli._dispatch(args)

        self.assertEqual(result, 0)
        mocked_serve.assert_called_once()
        _, kwargs = mocked_serve.call_args
        self.assertEqual(kwargs["access_token"], "qa-2115-local")
        self.assertEqual(kwargs["host"], "127.0.0.1")
        self.assertEqual(kwargs["port"], 8769)
        self.assertFalse(kwargs["unsafe_lan"])

        source = Path(cli.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_calls = {"Popen", "run", "call", "check_call", "check_output", "Start-Process", "taskkill", "open"}
        offenders: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                name = func.attr
                owner = func.value.id if isinstance(func.value, ast.Name) else ""
                if owner in {"subprocess", "webbrowser"} or name in {"system", "startfile"}:
                    offenders.append(f"{owner}.{name}")
            elif isinstance(func, ast.Name) and func.id in forbidden_calls:
                offenders.append(func.id)
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
