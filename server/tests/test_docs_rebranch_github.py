from __future__ import annotations

import unittest
from pathlib import Path


class RebranchGithubLocalDocTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[2]
        cls.doc_path = cls.repo_root / "docs" / "rebranch_github_local.md"
        cls.text = cls.doc_path.read_text(encoding="utf-8")
        cls.normalized = cls.text.lower()

    def test_document_exists_and_declares_scope(self) -> None:
        self.assertTrue(self.doc_path.exists())
        self.assertIn("# Rebranch GitHub local", self.text)
        self.assertIn("github.com/bthollet/coproscope", self.normalized)
        self.assertIn("sans ecrire sur drive", self.normalized)
        self.assertIn("sans muter les remotes git", self._compact(self.text))

    def test_non_destructive_checks_are_explicit(self) -> None:
        section = self._section("## Checks non destructifs", "## Exclusions de sync")

        for marker in [
            "git status --short",
            "git branch --show-current",
            "git remote -v",
            "git rev-parse --show-toplevel",
            "git ls-remote https://github.com/bthollet/coproscope.git HEAD",
            "arreter ici",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), section.lower())

    def test_sync_exclusions_cover_git_virtualenv_and_caches(self) -> None:
        section = self._section("## Exclusions de sync", "## Branche locale codex")
        compact = self._compact(section)

        for marker in [
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            "tmp_exports",
            "decrypted_blobs",
            "dossier synchronise",
            "archive diffusable",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, compact)

    def test_codex_branch_remote_and_future_pr_are_documented(self) -> None:
        branch = self._section("## Branche locale codex", "## Remote GitHub attendu")
        remote = self._section("## Remote GitHub attendu", "## PR future")
        future_pr = self._section("## PR future", "## Separation docs instance et noyau")

        self.assertIn("git switch -c codex/rebranch-github-local", branch)
        self.assertIn("ne sont ni revert ni nettoyees", branch.lower())
        self.assertIn("git remote get-url origin", remote)
        self.assertIn("git@github.com:bthollet/coproscope.git", remote)
        self.assertIn("interdit de modifier le remote", remote.lower())
        self.assertIn("pull request est future", future_pr.lower())
        self.assertIn("pr brouillon", future_pr.lower())
        self.assertIn("ecrit sur github", future_pr.lower())

    def test_instance_and_core_docs_are_separated(self) -> None:
        section = self._section("## Separation docs instance et noyau", "## Criteres d'acceptation")

        for marker in [
            "documents noyau",
            "depot github",
            "documents d'instance",
            "noms, adresses, lots",
            "copropriete reelle",
            "anonymisation explicite",
            "si le doute existe",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), section.lower())

    def test_runbook_does_not_document_remote_mutation_commands(self) -> None:
        forbidden_commands = [
            "git remote add",
            "git remote set-url",
            "git remote remove",
            "git remote rename",
        ]

        for command in forbidden_commands:
            with self.subTest(command=command):
                self.assertNotIn(command, self.normalized)

    def _section(self, start: str, end: str | None = None) -> str:
        start_index = self.text.index(start)
        end_index = self.text.index(end, start_index) if end else len(self.text)
        return self.text[start_index:end_index]

    def _compact(self, value: str) -> str:
        return " ".join(value.lower().split())


if __name__ == "__main__":
    unittest.main()
