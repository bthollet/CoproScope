from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "tools" / "reconstruction_protocol.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("reconstruction_protocol", TOOL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load tool from {TOOL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tool = _load_tool()


class TemporaryCwd:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.previous = Path.cwd()

    def __enter__(self) -> None:
        os.chdir(self.path)

    def __exit__(self, *_exc: object) -> None:
        os.chdir(self.previous)


class ReconstructionProtocolToolTests(unittest.TestCase):
    #: Un nom de FIXTURE, jamais un nom reel: le depot ne doit porter
    #: aucune trace de patronyme ni de nom de copropriete (`RM-2026-0137`).
    INSTANCE = "instance_de_lot_20260523"

    def setUp(self) -> None:
        patch = mock.patch.dict(
            os.environ, {tool.VARIABLE_INSTANCE: self.INSTANCE})
        patch.start()
        self.addCleanup(patch.stop)

    def _workspace(self, active_other: bool = False) -> tuple[tempfile.TemporaryDirectory[str], Path, Path]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name) / "repo"
        docs = root / "docs"
        docs.mkdir(parents=True)
        row = ""
        if active_other:
            row = (
                "| `CONV-X` | `RM-2026-0003` | `CH-X` | role | `EN_COURS` | own | wt | "
                "2026-05-31 10:00 +0200 | n/a | suite | trace |\n"
            )
        (docs / "presence_agents.md").write_text(
            "| Conversation | Roadmap | Chantier | Role | Statut | Ownership | Worktree / branche | "
            "Dernier heartbeat | Expire | Prochain geste | Trace finale |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|\n"
            f"{row}",
            encoding="utf-8",
        )
        (docs / "roadmap_backlog_central.md").write_text("# test\n", encoding="utf-8")
        instance = Path(temp.name) / "instance_de_lot_20260523" / "instance"
        instance.mkdir(parents=True)
        return temp, root, instance

    def _run(self, root: Path, args: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with TemporaryCwd(root), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = tool.main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def _base(self, instance: Path) -> list[str]:
        return ["--instance-root", str(instance)]

    def test_refuse_toute_instance_qui_n_est_pas_celle_declaree(self) -> None:
        """Le refus ne tient a AUCUN nom propre ecrit dans le code.

        Ce test remplace, le 2026-09-10, un test qui verifiait le refus
        d'une ancienne instance nommee en clair (`RM-2026-0137`). Le nom
        n'etait pas la garde: la condition generale refusait deja ce
        dossier, et la ligne nommee ne changeait que le message. La garde
        est donc verifiee ici sur ce qui la fonde vraiment - un dossier
        dont le parent n'est pas l'instance declaree est refuse, quel que
        soit son nom.
        """
        temp, root, _instance = self._workspace()
        try:
            for nom in ("une_ancienne_instance", "autre_chose", "instance"):
                with self.subTest(nom=nom):
                    autre = Path(temp.name) / "instances" / nom / "instance"
                    autre.mkdir(parents=True, exist_ok=True)

                    code, _out, err = self._run(
                        root, ["--instance-root", str(autre), "status"])

                    self.assertEqual(2, code)
                    self.assertIn("Instance refusee", err)
        finally:
            temp.cleanup()

    def test_sans_configuration_l_outil_REFUSE_au_lieu_de_laisser_passer(self) -> None:
        """Trois etats, et le troisieme n'est jamais un feu vert.

        Le nom du dossier attendu vit hors du depot. Un poste ou il n'est
        pas pose ne doit pas valider le premier dossier venu: il doit
        s'arreter en le disant.
        """
        temp, root, instance = self._workspace()
        try:
            with mock.patch.dict(os.environ, {tool.VARIABLE_INSTANCE: ""}):
                code, _out, err = self._run(root, self._base(instance) + ["status"])
            self.assertEqual(2, code)
            self.assertIn("non configuree", err)
            self.assertIn(tool.VARIABLE_INSTANCE, err)
        finally:
            temp.cleanup()

    def test_init_waits_when_another_chantier_is_active(self) -> None:
        temp, root, instance = self._workspace(active_other=True)
        try:
            code, out, _err = self._run(root, self._base(instance) + ["init"])

            self.assertEqual(2, code)
            self.assertIn("Preflight: WAIT_MERGE", out)
            state = tool.read_json(tool.state_path(instance))
            self.assertEqual("WAIT_MERGE", state["preflight"]["status"])
        finally:
            temp.cleanup()

    def test_gate_blocks_without_cloud_analysis(self) -> None:
        temp, root, instance = self._workspace()
        try:
            self.assertEqual(0, self._run(root, self._base(instance) + ["init"])[0])
            self.assertEqual(0, self._run(root, self._base(instance) + ["checkpoint"])[0])
            self.assertEqual(0, self._run(root, self._base(instance) + ["next-doc"])[0])

            code, out, _err = self._run(root, self._base(instance) + ["gate"])

            self.assertEqual(2, code)
            self.assertIn("analyse IA cloud cote expert", out)
            self.assertIn("controle IA cloud cote designer", out)
        finally:
            temp.cleanup()

    def test_legacy_heartbeat_alias_records_manual_checkpoint(self) -> None:
        temp, root, instance = self._workspace()
        try:
            self.assertEqual(0, self._run(root, self._base(instance) + ["init"])[0])

            code, out, _err = self._run(root, self._base(instance) + ["heartbeat"])

            self.assertEqual(0, code)
            self.assertIn("Point de reprise protocole enregistre", out)
            state = tool.read_json(tool.state_path(instance))
            self.assertEqual(1, len(state["checkpoints"]))
        finally:
            temp.cleanup()

    def test_full_document_cycle_can_close(self) -> None:
        temp, root, instance = self._workspace()
        sha = "A" * 64
        try:
            commands = [
                ["init"],
                ["checkpoint"],
                ["next-doc"],
                ["record", "expert", "--note", "audit local", "--cloud-analysis", "--audit-analysis"],
                ["record", "designer", "--note", "controle cible", "--cloud-analysis"],
                ["record", "novice", "--note", "retour novice"],
                ["record", "coproscope", "--note", "observation UI", "--route", "/documents/ajouter?source=inbox"],
                [
                    "record-executable-test",
                    "--exe-path",
                    r"C:\builds\CoproScope.exe",
                    "--exe-sha256",
                    sha,
                    "--result",
                    "ok",
                    "--route",
                    "/documents/DOC-0001",
                ],
                ["triage", "--no-items", "--machine-reviewed"],
            ]
            for command in commands:
                self.assertEqual(0, self._run(root, self._base(instance) + command)[0], command)

            code, out, _err = self._run(root, self._base(instance) + ["gate", "--close"])

            self.assertEqual(0, code)
            self.assertIn("OK - passage autorise", out)
            state = tool.read_json(tool.state_path(instance))
            self.assertIsNone(state["current_doc"])
            self.assertEqual("DOC-0001", state["last_closed_doc"])
        finally:
            temp.cleanup()

    def test_next_doc_refuses_skip_without_series_rule(self) -> None:
        temp, root, instance = self._workspace()
        try:
            self.assertEqual(0, self._run(root, self._base(instance) + ["init"])[0])

            code, _out, err = self._run(root, self._base(instance) + ["next-doc", "--inbox-index", "5"])

            self.assertEqual(2, code)
            self.assertIn("Saut de document refuse", err)
        finally:
            temp.cleanup()

    def test_series_requires_all_approvals(self) -> None:
        temp, root, instance = self._workspace()
        try:
            self.assertEqual(0, self._run(root, self._base(instance) + ["init"])[0])

            code, _out, err = self._run(root, self._base(instance) + ["series", "--rule-id", "S1", "--examples", "2"])

            self.assertEqual(2, code)
            self.assertIn("validations expert, designer et QA requises", err)
        finally:
            temp.cleanup()

    def test_safe_summary_does_not_export_private_notes(self) -> None:
        temp, root, instance = self._workspace()
        try:
            self.assertEqual(0, self._run(root, self._base(instance) + ["init"])[0])
            self.assertEqual(0, self._run(root, self._base(instance) + ["next-doc"])[0])
            private_note = r"C:\Users\brice\secret\raw\piece.pdf OCR brut nominatif"
            self.assertEqual(
                0,
                self._run(
                    root,
                    self._base(instance)
                    + ["record", "expert", "--note", private_note, "--cloud-analysis", "--audit-analysis"],
                )[0],
            )

            code, out, _err = self._run(root, self._base(instance) + ["export-safe-summary"])

            self.assertEqual(0, code)
            self.assertNotIn("secret", out)
            self.assertNotIn("raw", out.lower())
            self.assertNotIn("OCR brut", out)
            self.assertIn("DOC-0001", out)
        finally:
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
