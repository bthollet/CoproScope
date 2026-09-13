from __future__ import annotations

import unittest
from pathlib import Path


class LivraisonTestableContinueDocTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[2]
        cls.doc_path = cls.repo_root / "docs" / "archive" / "recettes_ux" / "livraison_testable_continue.md"
        cls.text = cls.doc_path.read_text(encoding="utf-8")
        cls.normalized = cls.text.lower()

    def test_document_exists_and_declares_delivery_scope(self) -> None:
        self.assertTrue(self.doc_path.exists())
        self.assertIn("# Livraison testable continue", self.text)
        self.assertIn("Date de reference: 2026-05-20.", self.text)
        self.assertIn("lot QA de livraison testable continue", self.text)
        self.assertIn("sans revendiquer une recette navigateur deja faite", self.normalized)

    def test_visible_server_command_is_documented_without_hidden_automation(self) -> None:
        launch_section = self._section("## Contrat de lancement visible", "## Donnees synthetiques")

        required_markers = [
            "ui open-test",
            "--instance-root .\\examples\\synthetic_copro",
            "--host 127.0.0.1",
            "--port 8769",
            "--token qa-livraison-continue-local",
            "serveur visible au premier plan",
            "Ctrl+C",
            "ouverture manuelle",
            "aucun process cache",
            "aucune ouverture navigateur automatique",
            "aucun scan de ports",
            "aucun `taskkill`",
            "aucun `Start-Process` cache",
        ]

        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), launch_section.lower())

    def test_synthetic_data_boundary_is_explicit(self) -> None:
        data_section = self._section("## Donnees synthetiques", "## Routes a tester manuellement")

        for marker in [
            "examples/synthetic_copro",
            "donnees reelles",
            "pieces privees",
            "chemins utilisateur",
            "synchronisation cloud",
            "revue separee",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), data_section.lower())

    def test_routes_to_test_cover_pages_exports_and_private_guards(self) -> None:
        routes_section = self._section("## Routes a tester manuellement", "## Etat UI")

        required_routes = [
            "/",
            "/actions",
            "/documents",
            "/documents/{doc_id}",
            "/pieces",
            "/demandes",
            "/ag-contentieux",
            "/gouvernance",
            "/pilotage",
            "/depot",
            "/confidentialite",
            "/chantiers",
            "/health",
            "/api/model",
            "/exports/actions.csv",
            "/exports/actions.md",
            "/exports/local.zip",
            "/exports/passation.json",
            "/exports/passation.txt",
            "/exports/{export_path:path}",
            "/{root_name}/{path:path}",
        ]

        for route in required_routes:
            with self.subTest(route=route):
                self.assertIn(route, routes_section)

        for marker in ["protegee par token", "raw", "restricted", "logs", "private"]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), routes_section.lower())

    def test_ui_and_vault_state_have_testable_features_and_limits(self) -> None:
        ui_section = self._section("## Etat UI", "## Etat coffre et vault")
        vault_section = self._section("## Etat coffre et vault", "## Tests a lancer")

        for marker in [
            "token local",
            "x-coproscope-token",
            "exports passation derives",
            "garde-fous contre chemins prives",
            "pas de validation navigateur manuelle",
            "pas de lancement navigateur automatique",
            "revue humaine",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), ui_section.lower())

        for marker in [
            "coffre",
            "vault init",
            "vault import",
            "vault status",
            "vault verify",
            "vault snapshot",
            "transport, pas moteur de synchronisation",
            "sync externe n'est pas garantie",
            "aucun moteur cache de sync",
            "pas de scan de processus, de ports ou de clients cloud",
            "signatures collaboratives finales",
            "source de verite",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), vault_section.lower())

    def test_test_commands_and_qa_exit_criteria_are_static_and_runnable(self) -> None:
        tests_section = self._section("## Tests a lancer", "## Criteres de sortie QA")
        criteria_section = self._section("## Criteres de sortie QA")

        for marker in [
            "C:\\Users\\brice\\CoproScope\\coproscope\\server",
            "test_docs_livraison_testable_continue.py",
            "test_ui_smoke_routes_expanded.py",
            "test_ui_security_routes.py",
            "unittest discover -s tests -v",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, tests_section)

        for marker in [
            "commande visible autorisee",
            "process cache",
            "scan de ports",
            "ouverture navigateur automatique",
            "routes pages, exports et garde-fous",
            "donnees synthetiques",
            "smoke tests UI et securite routes",
            "ne promettent pas plus que ce qui est testable",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), criteria_section.lower())

    def _section(self, start: str, end: str | None = None) -> str:
        start_index = self.text.index(start)
        end_index = self.text.index(end, start_index) if end else len(self.text)
        return self.text[start_index:end_index]


if __name__ == "__main__":
    unittest.main()
