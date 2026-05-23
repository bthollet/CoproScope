from __future__ import annotations

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import InstanceConfig, RunContext
from coproscope.core.doctor import run_doctor
from coproscope.modules import instancegit


@unittest.skipIf(shutil.which("git") is None, "git executable is required")
class InstanceGitTests(unittest.TestCase):
    def _instance(self, root: Path) -> InstanceConfig:
        return InstanceConfig(
            path=root / "instance.yml",
            payload={
                "instance_id": "test-local",
                "display_name": "Test local",
                "roots": {"logs": "./logs"},
            },
        )

    def _doctor_instance(self, root: Path, *, instance_id: str = "private-local") -> InstanceConfig:
        for directory in ["raw", "system", "outputs", "staging", "logs", "registers"]:
            (root / directory).mkdir(parents=True, exist_ok=True)
        payload = {
            "instance_id": instance_id,
            "display_name": "Private local",
            "roots": {
                "workspace": ".",
                "raw": "./raw",
                "system": "./system",
                "outputs": "./outputs",
                "staging": "./staging",
                "logs": "./logs",
            },
            "registers": {
                "documents": "./registers/documents.csv",
                "duplicates": "./registers/duplicates.csv",
                "manifest": "./registers/manifest.csv",
                "requests": "./registers/requests.csv",
                "ag": "./registers/ag.csv",
                "findings": "./registers/findings.csv",
                "kpi": "./registers/kpi.csv",
            },
        }
        (root / "instance.yml").write_text('{"instance_id": "private-local"}', encoding="utf-8")
        return InstanceConfig(path=root / "instance.yml", payload=payload)

    def _doctor_output(self, instance: InstanceConfig) -> tuple[int, str]:
        run = RunContext(instance, "doctor test")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            issues = run_doctor(instance, run)
        return issues, stdout.getvalue()

    def test_git_init_creates_local_repo_without_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "instance.yml").write_text('{"instance_id": "test-local", "roots": {"logs": "./logs"}}', encoding="utf-8")

            result = instancegit.ensure_local_git_repo(self._instance(root))

        self.assertTrue(result["ok"])
        self.assertTrue(result["is_git_repo"])
        self.assertEqual(result["branch"], "main")
        self.assertFalse(result["has_github_remote"])
        self.assertEqual(result["remotes"], [])
        self.assertEqual(result["policy"], "local_instance_git_no_github_remote")
        self.assertTrue(result["gitignore_updated"])

    def test_status_blocks_github_remote_on_instance_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = self._instance(root)
            instancegit.ensure_local_git_repo(instance)
            instancegit._git(root, "remote", "add", "origin", "https://github.com/example/private-instance.git")

            result = instancegit.inspect_instance_git(instance)

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "blocked_github_remote")
        self.assertTrue(result["has_github_remote"])
        self.assertIn("github.com/example/private-instance.git", " ".join(result["github_remotes"]))

    def test_gitignore_keeps_instance_data_trackable_but_excludes_secrets_and_core_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            updated = instancegit.ensure_instance_gitignore(root)
            text = (root / ".gitignore").read_text(encoding="utf-8")

        self.assertTrue(updated)
        self.assertIn("Do not push this repository to GitHub", text)
        self.assertIn(".env.local", text)
        self.assertIn("client_secret*.json", text)
        self.assertIn("coproscope/", text)
        self.assertNotIn("raw/", text)
        self.assertNotIn("outputs/", text)
        self.assertNotIn("registers/", text)

    def test_doctor_requires_git_for_working_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            instance = self._doctor_instance(Path(tmp))

            issues, output = self._doctor_output(instance)

        self.assertEqual(issues, 1)
        self.assertIn("Git local instance", output)
        self.assertIn("A_INITIALISER", output)
        self.assertIn("coprocs instance git-init", output)

    def test_doctor_accepts_local_git_instance_without_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = self._doctor_instance(root)
            instancegit.ensure_local_git_repo(instance)

            issues, output = self._doctor_output(instance)

        self.assertEqual(issues, 0)
        self.assertIn("depot_git: OK", output)
        self.assertIn("remote_github: aucune", output)

    def test_doctor_blocks_github_remote_without_echoing_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = self._doctor_instance(root)
            instancegit.ensure_local_git_repo(instance)
            instancegit._git(root, "remote", "add", "origin", "https://github.com/example/private-instance.git")

            issues, output = self._doctor_output(instance)

        self.assertEqual(issues, 1)
        self.assertIn("REMOTE_GITHUB_INTERDITE", output)
        self.assertNotIn("github.com/example/private-instance", output)


if __name__ == "__main__":
    unittest.main()
