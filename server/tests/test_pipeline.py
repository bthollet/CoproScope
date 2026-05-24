from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.cli import _dispatch, build_parser
from coproscope.core.common import RunContext, load_instance, read_csv
from coproscope.core.doctor import run_doctor
from coproscope.core.pipeline import run_pipeline
from coproscope.core.share import audit_repo, export_shareable


class CoproScopePipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.example_root = Path(self.tempdir.name) / "synthetic_copro"
        shutil.copytree(source_example, self.example_root)
        self.instance = load_instance(str(self.example_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _windows_leak(self) -> str:
        return "C:" + "\\Users\\ExampleUser\\Documents\\CoproScope\\instances\\instance_privee_test\\raw\\scan.pdf"

    def _file_uri_leak(self) -> str:
        return "file" + "://C:/" + "Users/ExampleUser/raw/scan.pdf"

    def _local_token(self) -> str:
        return "local" + "-secret"

    def test_doctor_passes_on_synthetic_instance(self) -> None:
        run = RunContext(self.instance, "doctor")
        issues = run_doctor(self.instance, run)
        run.finish("OK" if issues == 0 else "WARN", f"issues={issues}")
        self.assertEqual(issues, 0)

    def test_pipeline_run_creates_expected_outputs(self) -> None:
        run = RunContext(self.instance, "pipeline run")
        run_pipeline(self.instance, run, copy_classified=True)
        run.finish("OK", "pipeline completed")

        documents_path = self.instance.register("documents")
        ag_path = self.instance.register("ag")
        kpi_path = self.instance.register("kpi")
        findings_path = self.instance.register("findings")
        reports_dir = self.instance.artifact("reports_dir")

        self.assertTrue(documents_path.exists())
        self.assertTrue(ag_path.exists())
        self.assertTrue(kpi_path.exists())
        self.assertTrue(findings_path.exists())
        self.assertTrue((reports_dir / "rapport_completude_documentaire.md").exists())
        self.assertTrue((reports_dir / "rapport_ag_preparation.md").exists())
        self.assertTrue((reports_dir / "matrice_due_diligence_publique.csv").exists())

        _, document_rows = read_csv(documents_path)
        _, ag_rows = read_csv(ag_path)
        _, kpi_rows = read_csv(kpi_path)

        self.assertGreaterEqual(len(document_rows), 5)
        self.assertGreaterEqual(len(ag_rows), 1)
        self.assertTrue(any(row.get("kpi_id") == "KPI-001" for row in kpi_rows))
        self.assertTrue(any(row.get("document_type") == "Contrat_Syndic" for row in document_rows))

    def test_share_audit_respects_public_private_boundary(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        config_path = repo_root / "server" / "src" / "coproscope" / "configs" / "github_sharing.default.yml"
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_root = Path(tmpdir)
            (audit_root / "server" / "src" / "coproscope").mkdir(parents=True)
            (audit_root / "server" / "src" / "coproscope.egg-info").mkdir(parents=True)
            (audit_root / "docs").mkdir(parents=True)
            (audit_root / "examples" / "synthetic_copro" / "raw").mkdir(parents=True)
            (audit_root / "examples" / "synthetic_copro" / "logs").mkdir(parents=True)
            (audit_root / ".github").mkdir(parents=True)
            (audit_root / "README.md").write_text("# repo\n", encoding="utf-8")
            (audit_root / "server" / "src" / "coproscope" / "cli.py").write_text("print('ok')\n", encoding="utf-8")
            (audit_root / "server" / "src" / "coproscope.egg-info" / "PKG-INFO").write_text("metadata\n", encoding="utf-8")
            (audit_root / "docs" / "github_sharing.md").write_text("# doc\n", encoding="utf-8")
            (audit_root / "docs" / "private_note.md").write_text(
                f"Recette locale: {self._windows_leak()}?token={self._local_token()}\n",
                encoding="utf-8",
            )
            (audit_root / "examples" / "synthetic_copro" / "raw" / "demo.txt").write_text("demo\n", encoding="utf-8")
            (audit_root / "examples" / "synthetic_copro" / "logs" / "action_log.csv").write_text("x\n", encoding="utf-8")
            (audit_root / ".github" / "pull_request_template.md").write_text("template\n", encoding="utf-8")

            result = audit_repo(audit_root, config_path)
            shareable = result["shareable"]
            blocked = result["blocked"]
            self.assertIn("README.md", shareable)
            self.assertIn("server/src/coproscope/cli.py", shareable)
            self.assertIn("docs/github_sharing.md", shareable)
            self.assertIn(".github/pull_request_template.md", shareable)
            self.assertIn("examples/synthetic_copro/raw/demo.txt", shareable)
            self.assertIn("server/src/coproscope.egg-info/", blocked)
            self.assertIn("examples/synthetic_copro/logs/", blocked)
            self.assertIn("docs/private_note.md", blocked)
            violations = {item["path"]: item["rules"] for item in result["content_violations"]}
            self.assertIn("local_windows_path", violations["docs/private_note.md"])
            self.assertIn("local_access_token", violations["docs/private_note.md"])
            violation = result["content_violations"][0]
            self.assertEqual(violation["status"], "publication_blocked")
            self.assertEqual(violation["reason"], "allowed_path_refused_content")
            self.assertTrue(violation["value_masked"])
            self.assertEqual(violation["effect"], "file_not_copied_to_public_export")
            manifest_preview = json.dumps(result, ensure_ascii=True)
            self.assertNotIn(self._local_token(), manifest_preview)
            self.assertNotIn("C:\\Users", manifest_preview)

    def test_share_export_copies_only_shareable_files(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        config_path = repo_root / "server" / "src" / "coproscope" / "configs" / "github_sharing.default.yml"
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_root = Path(tmpdir) / "repo"
            export_root = Path(tmpdir) / "export"
            (audit_root / "server" / "src" / "coproscope").mkdir(parents=True)
            (audit_root / "server" / "src" / "coproscope.egg-info").mkdir(parents=True)
            (audit_root / "examples" / "synthetic_copro" / "raw").mkdir(parents=True)
            (audit_root / "examples" / "synthetic_copro" / "logs").mkdir(parents=True)
            (audit_root / "docs").mkdir(parents=True)
            (audit_root / ".github").mkdir(parents=True)
            (audit_root / "README.md").write_text("# repo\n", encoding="utf-8")
            (audit_root / "server" / "src" / "coproscope" / "cli.py").write_text("print('ok')\n", encoding="utf-8")
            (audit_root / "server" / "src" / "coproscope.egg-info" / "PKG-INFO").write_text("metadata\n", encoding="utf-8")
            (audit_root / "examples" / "synthetic_copro" / "raw" / "demo.txt").write_text("demo\n", encoding="utf-8")
            (audit_root / "examples" / "synthetic_copro" / "logs" / "action_log.csv").write_text("x\n", encoding="utf-8")
            (audit_root / "docs" / "github_sharing.md").write_text("# doc\n", encoding="utf-8")
            (audit_root / "docs" / "private_note.md").write_text(
                f"Piece locale a ne pas publier: {self._file_uri_leak()}?token={self._local_token()}\n",
                encoding="utf-8",
            )
            (audit_root / ".github" / "pull_request_template.md").write_text("template\n", encoding="utf-8")

            result = export_shareable(audit_root, config_path, export_root, clean=True)

            self.assertEqual(result["exported_count"], 5)
            self.assertEqual(result["repo_root"], "repo")
            self.assertEqual(result["export_dir"], "export")
            self.assertEqual(result["manifest_path"], "share-manifest.json")
            self.assertTrue((export_root / "README.md").exists())
            self.assertTrue((export_root / "server" / "src" / "coproscope" / "cli.py").exists())
            self.assertTrue((export_root / "examples" / "synthetic_copro" / "raw" / "demo.txt").exists())
            self.assertFalse((export_root / "examples" / "synthetic_copro" / "logs" / "action_log.csv").exists())
            self.assertFalse((export_root / "docs" / "private_note.md").exists())
            self.assertFalse((export_root / "server" / "src" / "coproscope.egg-info" / "PKG-INFO").exists())
            self.assertTrue((export_root / "share-manifest.json").exists())
            manifest_text = (export_root / "share-manifest.json").read_text(encoding="utf-8")
            self.assertIn("content_violations", manifest_text)
            self.assertIn("docs/private_note.md", manifest_text)
            self.assertNotIn(self._local_token(), manifest_text)
            self.assertNotIn("C:/" + "Users", manifest_text)
            manifest_preview = json.dumps(result, ensure_ascii=True)
            self.assertNotIn(str(audit_root), manifest_preview)
            self.assertNotIn(str(export_root), manifest_preview)

    def test_share_audit_cli_fails_on_content_violation_without_echoing_secret(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        config_path = repo_root / "server" / "src" / "coproscope" / "configs" / "github_sharing.default.yml"
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_root = Path(tmpdir) / "repo"
            (audit_root / "docs").mkdir(parents=True)
            (audit_root / "README.md").write_text("# repo\n", encoding="utf-8")
            (audit_root / "docs" / "handoff.md").write_text(
                f"A verifier hors publication: {self._file_uri_leak()}?token={self._local_token()}\n",
                encoding="utf-8",
            )

            args = build_parser().parse_args(
                [
                    "share-audit",
                    "--repo-root",
                    str(audit_root),
                    "--config",
                    str(config_path),
                ]
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                result = _dispatch(args)

            output = stdout.getvalue()
            self.assertEqual(result, 1)
            self.assertIn("content_violations", output)
            self.assertIn("docs/handoff.md", output)
            self.assertIn("publication_blocked", output)
            self.assertNotIn(self._local_token(), output)
            self.assertNotIn("C:/" + "Users", output)


if __name__ == "__main__":
    unittest.main()
