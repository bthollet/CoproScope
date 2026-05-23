from __future__ import annotations

import unittest
from pathlib import Path


class RefonteUxCycleDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[2]
        cls.protocol_path = cls.repo_root / "docs" / "refonte_ux_cycles_image_dev_test.md"
        cls.register_path = cls.repo_root / "docs" / "registre_cycles_refonte_ux.md"
        cls.prompts_path = cls.repo_root / "docs" / "prompts_agents_refonte_ux.md"
        cls.protocol = cls.protocol_path.read_text(encoding="utf-8")
        cls.register = cls.register_path.read_text(encoding="utf-8")
        cls.prompts = cls.prompts_path.read_text(encoding="utf-8")
        cls.protocol_lower = cls.protocol.lower()
        cls.register_lower = cls.register.lower()
        cls.prompts_lower = cls.prompts.lower()

    def test_protocol_declares_parallel_image_dev_test_cycles(self) -> None:
        self.assertTrue(self.protocol_path.exists())
        for marker in [
            "Image -> Dev -> Test produit",
            "Cycle N-1",
            "Cycle N",
            "Cycle N+1",
            "A tester maintenant",
            "En dev maintenant",
            "En enquete maintenant",
            "Commande prete",
            "Decision requise",
            "Prochain mouvement",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), self.protocol_lower)

    def test_protocol_includes_full_cycle_definition_and_no_go_rules(self) -> None:
        for marker in [
            "Enquete sur image",
            "Commande dev",
            "Developpement",
            "Test du produit livre",
            "Cloture du bloc",
            "aucun developpement",
            "compteur non cliquable",
            "rupture token",
            "langage est comprehensible",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), self.protocol_lower)

    def test_protocol_contains_initial_pipeline_and_cockpit_command(self) -> None:
        for marker in [
            "Cockpit Canva",
            "Registre decisions/actions/preuves",
            "Controle comptes",
            "Memoire copropriete",
            "Commande dev - Cycle 1 Cockpit complet",
            "model.ux.cockpit.summary_cards",
            "model.ux.cockpit.risk_alerts",
            "cs-shell",
            "cs-kpi-card",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), self.protocol_lower)

    def test_register_tracks_all_three_active_fluxes(self) -> None:
        self.assertTrue(self.register_path.exists())
        for marker in [
            "A tester maintenant",
            "En dev maintenant",
            "En enquete maintenant",
            "Cycle 1",
            "Cycle 2",
            "COMMANDE_PRETE",
            "ENQUETE_A_LANCER",
            "Journal de coordination",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), self.register_lower)

    def test_prompts_cover_required_agent_roles(self) -> None:
        self.assertTrue(self.prompts_path.exists())
        for marker in [
            "Designer de service",
            "Membre conseil syndical novice",
            "Dev front",
            "Dev back/viewmodel",
            "QA UX/visuelle",
            "Integrateur-scribe",
            "preuve + action + memoire",
            "model.ux.<bloc>",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), self.prompts_lower)


if __name__ == "__main__":
    unittest.main()
