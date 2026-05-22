from __future__ import annotations

import unittest
from pathlib import Path


class UiJourConseilSyndicalTests(unittest.TestCase):
    def setUp(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        self.actions_template = repo / "server" / "src" / "coproscope" / "web" / "templates" / "actions.html"
        self.parcours_doc = repo / "docs" / "parcours_jour_cs.md"

    def test_actions_page_exposes_short_cs_workflow(self) -> None:
        html = self.actions_template.read_text(encoding="utf-8")

        self.assertIn("Boite de travail du conseil syndical", html)
        self.assertIn("Parcours jour de conseil syndical", html)
        for label in [
            "Demander au syndic",
            "Verifier la preuve",
            "Rattacher au bon point",
            "Arbitrer en CS",
            "Cloturer avec preuve",
        ]:
            self.assertIn(label, html)

    def test_action_cards_show_context_proof_next_step_and_diffusion_caution(self) -> None:
        html = self.actions_template.read_text(encoding="utf-8")

        self.assertIn("Fiches action a traiter maintenant", html)
        self.assertIn("{% for action in action_rows[:6] %}", html)
        for label in ["Pourquoi", "Preuve / source", "Prochaine action", "Prudence diffusion"]:
            self.assertGreaterEqual(html.count(f"<dt>{label}</dt>"), 6)
        self.assertIn("{{ action.detail or action.domain_label }}", html)
        self.assertIn("{{ action.evidence or action.source }}", html)
        self.assertIn("{{ action.next_step }}", html)
        self.assertIn("Ne pas annoncer la cloture", html)

    def test_parcours_doc_exists_for_handoff(self) -> None:
        markdown = self.parcours_doc.read_text(encoding="utf-8")

        self.assertIn("# Parcours jour de conseil syndical", markdown)
        for step in ["Demander", "Verifier", "Rattacher", "Arbitrer", "Cloturer"]:
            self.assertIn(step, markdown)
        self.assertIn("preuve / source", markdown.lower())
        self.assertIn("prudence diffusion", markdown.lower())


if __name__ == "__main__":
    unittest.main()
