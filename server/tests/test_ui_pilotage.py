from __future__ import annotations

import unittest
from html import unescape
from pathlib import Path

from coproscope.modules.pilotageops import build_pilotage_card, card_to_dict
from coproscope.web.pilotage_view import build_pilotage_view, build_pilotage_view_from_rows


REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = REPO_ROOT / "server" / "src" / "coproscope" / "web" / "templates"
PILOTAGE_VIEW_PATH = REPO_ROOT / "server" / "src" / "coproscope" / "web" / "pilotage_view.py"
PILOTAGE_TEMPLATE_PATH = TEMPLATE_DIR / "pilotage.html"


class PilotageUiTests(unittest.TestCase):
    def test_view_model_prepares_indicator_card_fields_for_template(self) -> None:
        card = build_pilotage_card(
            {"indicator_id": "eau_derive_mensuelle", "theme": "Consommations", "name": "Derive eau", "unit": "%"},
            {
                "indicator_id": "eau_derive_mensuelle",
                "value": "24",
                "period": "2026-05",
                "source": "FactureOps",
                "proof_ref": "FACT-EAU-2026-05",
                "data_quality": "verified",
            },
            {"indicator_id": "eau_derive_mensuelle", "attention": "10", "alert": "20"},
            attachment={
                "indicator_id": "eau_derive_mensuelle",
                "point_ref": "POINT-EAU",
                "action_ref": "ACT-RELANCE-EAU",
                "diffusion": "syndic",
                "next_action": "Demander le releve compteur et comparer au contrat.",
            },
        )

        view = build_pilotage_view([card], period_label="Mai 2026", source_label="pilotageops")

        self.assertTrue(view["has_cards"])
        self.assertEqual(view["summary"]["total"], 1)
        self.assertEqual(view["summary"]["alerts"], 1)
        ui_card = view["cards"][0]
        self.assertEqual(ui_card["domain_label"], "Consommations")
        self.assertEqual(ui_card["period"], "2026-05")
        self.assertEqual(ui_card["proof_source"], "FactureOps - FACT-EAU-2026-05")
        self.assertEqual(ui_card["threshold"], "attention >= 10; alerte >= 20")
        self.assertEqual(ui_card["status_label"], "prioritaire")
        self.assertEqual(ui_card["confidence_label"], "haute")
        self.assertIn("Demander le releve", ui_card["next_action"])
        self.assertEqual(ui_card["action_href"], "/actions?selected=ACT-RELANCE-EAU")
        self.assertEqual(ui_card["action_label"], "Ouvrir l'action rattachee")
        self.assertEqual(ui_card["diffusion_label"], "Conseil syndical et syndic")
        self.assertIn("Point POINT-EAU", ui_card["attachment_label"])
        self.assertIn("Action ACT-RELANCE-EAU", ui_card["attachment_label"])

    def test_view_model_accepts_card_dicts_from_pilotageops(self) -> None:
        card = build_pilotage_card(
            {"indicator_id": "fonds_travaux", "theme": "Investissements", "name": "Fonds travaux", "unit": "%"},
            {
                "indicator_id": "fonds_travaux",
                "value": 12,
                "period": "2026",
                "source": "Budget",
                "proof_ref": "BUDGET-2026",
            },
            {"indicator_id": "fonds_travaux", "attention": 30, "alert": 15, "direction": "min"},
            attachment={"indicator_id": "fonds_travaux", "action_ref": "ACT-ARBITRAGE-AG"},
        )

        view = build_pilotage_view([card_to_dict(card)])

        self.assertEqual(view["cards"][0]["domain_label"], "Amortissement et investissements")
        self.assertIn("Action ACT-ARBITRAGE-AG", view["cards"][0]["attachment_label"])
        self.assertEqual(view["cards"][0]["action_href"], "/actions?selected=ACT-ARBITRAGE-AG")

    def test_view_model_rejects_indicator_without_confidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "confidence"):
            build_pilotage_view(
                [
                    {
                        "indicator_id": "score_sans_confiance",
                        "domain": "gouvernance",
                        "title": "Score sans confiance",
                        "period": "2026-05",
                        "status": "OK",
                        "threshold": "seuil renseigne",
                        "source": "Registre test",
                        "proof_ref": "DOC-1",
                        "novice_reading": "Carte volontairement incomplete.",
                        "next_action": "Completer avant affichage.",
                        "diffusion": "cs",
                        "point_ref": "POINT-TEST",
                    }
                ]
            )

    def test_view_model_empty_state_is_useful_for_novice(self) -> None:
        view = build_pilotage_view([])

        self.assertFalse(view["has_cards"])
        self.assertEqual(view["summary"]["total"], 0)
        self.assertIn("Aucun indicateur", view["empty_state"]["title"])
        self.assertIn("domaine", view["empty_state"]["body"])
        self.assertIn("build_pilotage_card", view["empty_state"]["next_step"])

    def test_view_model_from_rows_uses_pilotageops_without_ui_recalculation(self) -> None:
        view = build_pilotage_view_from_rows(
            [
                {
                    "indicator_id": "travaux_retard",
                    "domaine": "travaux",
                    "name": "Retard reception",
                    "value": "18",
                    "period": "2026-05",
                    "source": "PV AG",
                    "proof_ref": "PV-2026-04",
                    "attention": "7",
                    "alert": "15",
                    "point_ref": "POINT-TRAVAUX",
                    "prochaine_action": "Demander la preuve de cloture.",
                    "diffusion": "cs",
                }
            ]
        )

        self.assertEqual(view["cards"][0]["status"], "alerte")
        self.assertEqual(view["cards"][0]["domain_label"], "Travaux")
        self.assertEqual(view["cards"][0]["attachment_label"], "Point POINT-TRAVAUX")

    def test_template_renders_cards_and_empty_state_without_global_route(self) -> None:
        card = build_pilotage_card(
            {"indicator_id": "demandes_retard", "theme": "Demandes", "name": "Demandes en retard"},
            {
                "indicator_id": "demandes_retard",
                "value": 3,
                "period": "2026-05",
                "source": "SyndicOps",
                "proof_ref": "",
                "data_quality": "incomplete",
            },
            {"indicator_id": "demandes_retard", "attention": 2, "alert": 5},
        )
        html = self._render(build_pilotage_view([card]))
        empty_html = self._render(build_pilotage_view([]))

        self.assertIn("Pilotage des indicateurs", html)
        self.assertIn("Domaine", html)
        self.assertIn("Periode", html)
        self.assertIn("Preuve ou source", html)
        self.assertIn("Seuil", html)
        self.assertIn("Confiance", html)
        self.assertIn("Prochaine action", html)
        self.assertIn("Diffusion", html)
        self.assertIn("Rattachement", html)
        self.assertIn("preuve manquante", html)
        self.assertIn('href="/actions?scope=syndic"', html)
        self.assertIn("Ouvrir les demandes a suivre", html)
        self.assertIn("Aucun indicateur pret a afficher", empty_html)
        self.assertNotIn('href="/pilotage', html)
        self.assertNotIn('href="/pilotage', empty_html)

    def test_pilotage_ui_layer_does_not_define_route(self) -> None:
        source = PILOTAGE_VIEW_PATH.read_text(encoding="utf-8")
        template = PILOTAGE_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertNotIn("@app.", source)
        self.assertNotIn("@router.", source)
        self.assertNotIn("FastAPI", source)
        self.assertNotIn('href="/pilotage', template)

    def _render(self, pilotage: dict[str, object]) -> str:
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
        except ImportError:
            return unescape(PILOTAGE_TEMPLATE_PATH.read_text(encoding="utf-8"))

        env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(("html", "xml")),
        )
        env.globals["url_for"] = lambda name, **kwargs: f"/static/{kwargs.get('path', '')}"
        rendered = env.get_template("pilotage.html").render(
            model={"instance": {"name": "Demo copro", "year": 2026, "id": "demo"}, "pilotage": pilotage},
            pilotage=pilotage,
            page="pilotage",
            ui_token_query="",
            ui_token_param="",
        )
        return unescape(rendered)


if __name__ == "__main__":
    unittest.main()
