from __future__ import annotations

import json
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import InstanceConfig
from coproscope.web.context_banner import build_context_banner


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / "server" / "src" / "coproscope" / "web" / "templates"
PARTIAL = TEMPLATE_DIR / "_context_banner.html"
DOC = ROOT / "docs" / "archive" / "notes_integration" / "bandeau_contexte_coffre_role_sync.md"


class UiContextBannerTests(unittest.TestCase):
    def _instance(self, root: Path, settings: dict[str, object] | None = None) -> InstanceConfig:
        path = root / "instance.yml"
        path.write_text("{}", encoding="utf-8")
        return InstanceConfig(
            path=path,
            payload={
                "instance_id": "copro-alpha",
                "display_name": "Residence Alpha",
                "settings": settings or {},
            },
        )

    def test_model_is_novice_readable_without_configured_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            instance = self._instance(Path(temp_dir))
            banner = build_context_banner(instance)

        self.assertEqual(banner["coffre_id"], "copro-alpha")
        self.assertEqual(banner["coffre_label"], "Residence Alpha")
        self.assertEqual(banner["role_label"], "Role a confirmer")
        self.assertEqual(banner["access_level_label"], "niveau a confirmer")
        self.assertEqual(banner["vault_state_label"], "Coffre signe a declarer")
        self.assertEqual(banner["sync_state_label"], "Sync non branchee")
        self.assertEqual(banner["last_checked_label"], "Derniere verification: a faire")
        self.assertIn("Declarer le cache local", banner["next_action"])
        self.assertIn("confirmez le contexte", banner["novice_text"])
        self.assertNotIn(tempfile.gettempdir(), json.dumps(banner))

    def test_model_reads_configured_vault_role_access_and_sync_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            local_root = root / "local"
            sync_root = root / "sync"
            local_root.mkdir()
            sync_root.mkdir()
            (local_root / "vault_local.json").write_text("{}", encoding="utf-8")
            (sync_root / "vault.json").write_text('{"vault_id": "vault-alpha"}', encoding="utf-8")
            (sync_root / "events" / "device-a").mkdir(parents=True)
            (sync_root / "blobs").mkdir()
            instance = self._instance(
                root,
                {
                    "context_banner": {
                        "role": "conseil_syndical",
                        "access_level": "C4_Conseil_Syndical",
                    },
                    "vault": {
                        "local_root": "local",
                        "sync_root": "sync",
                        "sync_profile": "local_folder",
                        "last_verified_at": "2026-05-20 18:30",
                    },
                },
            )

            banner = build_context_banner(instance)

        self.assertEqual(banner["role_label"], "Conseil syndical")
        self.assertEqual(banner["access_level_label"], "conseil syndical")
        self.assertEqual(banner["vault_state_label"], "Coffre pret localement")
        self.assertEqual(banner["sync_state_label"], "Sync sans alerte bloquante")
        self.assertEqual(banner["last_checked_label"], "Derniere verification: 2026-05-20 18:30")
        self.assertIn("Continuer", banner["next_action"])
        self.assertEqual(banner["tone"], "ok")

    def test_model_surfaces_sync_protection_without_private_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            local_root = root / "local"
            sync_root = root / "sync"
            local_root.mkdir()
            sync_root.mkdir()
            (local_root / "vault_local.json").write_text("{}", encoding="utf-8")
            (sync_root / "vault.json").write_text('{"vault_id": "vault-alpha"}', encoding="utf-8")
            (sync_root / "events" / "device-a").mkdir(parents=True)
            (sync_root / "blobs").mkdir()
            (sync_root / ".venv").mkdir()
            instance = self._instance(
                root,
                {
                    "context_banner": {
                        "role": "conseil_syndical",
                        "access_level": "C4_Conseil_Syndical",
                    },
                    "vault": {
                        "local_root": "local",
                        "sync_root": "sync",
                        "sync_profile": "google_drive_desktop",
                    },
                },
            )

            banner = build_context_banner(instance)

        serialized = json.dumps(banner, ensure_ascii=False)
        self.assertEqual(banner["sync_state"], "protection")
        self.assertEqual(banner["sync_state_label"], "Sync en protection")
        self.assertIn("publication suspendue", serialized)
        self.assertIn("notification interne", serialized)
        self.assertIn("Suspendre le partage", banner["next_action"])
        self.assertNotIn(str(root), serialized)
        self.assertNotIn(".venv", serialized)

    def test_partial_is_isolated_and_renders_expected_words(self) -> None:
        source = PARTIAL.read_text(encoding="utf-8")
        self.assertNotIn("extends", source)
        self.assertNotIn("base.html", source)
        self.assertIn("context_banner", source)
        self.assertIn("Prochaine action", source)

        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
        except ImportError:
            return

        with tempfile.TemporaryDirectory() as temp_dir:
            banner = build_context_banner(self._instance(Path(temp_dir)), role_hint="coproprietaire")

        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=select_autoescape(("html", "xml")))
        rendered = unescape(env.get_template("_context_banner.html").render(context_banner=banner))

        self.assertIn('aria-label="Contexte du coffre, du role et de la synchronisation"', rendered)
        self.assertIn("Residence Alpha", rendered)
        self.assertIn("Coproprietaire", rendered)
        self.assertIn("Sync non branchee", rendered)
        self.assertIn("Prochaine action", rendered)

    def test_document_explains_integration_contract_without_route_refactor(self) -> None:
        text = DOC.read_text(encoding="utf-8")

        self.assertIn("build_context_banner", text)
        self.assertIn("_context_banner.html", text)
        self.assertIn("pas branche dans base.html", text)
        self.assertIn("coffre courant", text)
        self.assertIn("role", text)
        self.assertIn("niveau acces", text)
        self.assertIn("coffre signe", text)
        self.assertIn("sync", text)
        self.assertIn("prochaine action", text)


if __name__ == "__main__":
    unittest.main()
