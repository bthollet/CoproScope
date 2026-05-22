from __future__ import annotations

import unittest
from html import unescape
from pathlib import Path

from coproscope.web.document_intake_view import build_document_intake_view


REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = REPO_ROOT / "server" / "src" / "coproscope" / "web" / "templates"
VIEW_PATH = REPO_ROOT / "server" / "src" / "coproscope" / "web" / "document_intake_view.py"
TEMPLATE_PATH = TEMPLATE_DIR / "document_intake.html"
DOC_PATH = REPO_ROOT / "docs" / "integration_ui_ajout_document.md"


class DocumentIntakeUiModelTests(unittest.TestCase):
    def test_view_model_builds_novice_cards_from_runtime_without_private_paths(self) -> None:
        view = build_document_intake_view(
            [
                {
                    "doc_id": "DOC-PV-2026",
                    "file_name": r"C:\Users\ExampleUser\pv_secret.pdf",
                    "original_path": r"C:\Users\ExampleUser\pv_secret.pdf",
                    "sha256": "abcdef1234567890abcdef1234567890",
                    "file_format": "pdf",
                    "size_bytes": "2048",
                    "document_type": "PV_AG",
                    "domain": "gouvernance",
                    "period": "2026",
                    "classification_status": "ACCEPTE",
                    "privacy_status": "RESERVE_CS",
                    "attachments": [
                        {
                            "piece_label": "PV AG 2026",
                            "point_id": "AG-2026-R7",
                            "point_label": "Resolution travaux toiture",
                            "point_kind": "ag",
                            "action_kind": "verifier",
                            "action_label": "Verifier le devis retenu.",
                            "proof_intent": "decision",
                            "proof_label": "Decision votee.",
                        }
                    ],
                }
            ]
        )

        card = view["cards"][0]
        self.assertEqual(view["summary"]["total"], 1)
        self.assertEqual(card["document_label"], "Document 1")
        self.assertEqual(card["doc_id"], "DOC-PV-2026")
        self.assertEqual(card["privacy"]["status_label"], "reserve conseil syndical")
        self.assertIn("piece -> point -> action -> preuve", view["novice_steps"][3]["body"])
        self.assertIn("PV AG 2026", card["attachments"][0]["chain_label"])
        self.assertIn("Un chemin prive a ete masque", " ".join(card["warning_labels"]))

        serialized = str(view).lower()
        self.assertNotIn("c:\\", serialized)
        self.assertNotIn("users", serialized)
        self.assertNotIn("ExampleUser", serialized)
        self.assertNotIn("pv_secret", serialized)

    def test_view_model_surfaces_blocked_cloud_and_missing_linking_next_steps(self) -> None:
        view = build_document_intake_view(
            [
                {
                    "doc_id": "DOC-BLOCKED",
                    "sha256": "abcdef1234567890",
                    "local_reference": "opaque/DOC-BLOCKED",
                    "source_kind": "cloud_raw",
                    "document_type": "Dossier_Contentieux",
                    "classification_status": "ACCEPTED",
                    "privacy_status": "BLOQUE",
                },
                {
                    "doc_id": "DOC-TODO",
                    "sha256": "abcdef1234567890",
                    "local_reference": "opaque/DOC-TODO",
                    "document_type": "Facture",
                    "classification_status": "PROPOSED",
                    "privacy_status": "A_ARBITRER",
                },
            ]
        )

        self.assertEqual(view["summary"]["blocked"], 1)
        self.assertEqual(view["summary"]["todo"], 1)
        blocked = view["blocked_cards"][0]
        todo = view["todo_cards"][0]
        linking = next(item for item in todo["checklist"] if item["step_id"] == "rattachement")
        self.assertIn("Retirer la cible cloud", blocked["drop_guidance"])
        self.assertIn("Bloquer l'export", blocked["privacy_guard"])
        self.assertIn("Choisir un niveau de confidentialite", todo["privacy_guard"])
        self.assertIn("point", linking["next_action"])
        self.assertIn("preuve", linking["next_action"])


class DocumentIntakeUiTemplateTests(unittest.TestCase):
    def test_template_renders_runtime_surface_and_empty_state(self) -> None:
        html = self._render(
            build_document_intake_view(
                [
                    {
                        "doc_id": "DOC-DEVIS",
                        "sha256": "abcdef1234567890",
                        "local_reference": "opaque/DOC-DEVIS",
                        "display_name": "devis_toiture.pdf",
                        "document_type": "Devis",
                        "classification_status": "ACCEPTED",
                        "privacy_status": "A_BIFFER",
                        "required_derivative": "derivees/DOC-DEVIS-biffe",
                        "attachments": [
                            {
                                "piece_label": "Devis toiture",
                                "point_label": "Travaux toiture",
                                "action_label": "Comparer au vote AG.",
                                "proof_label": "Devis retenu.",
                            }
                        ],
                    }
                ]
            )
        )
        empty_html = self._render(build_document_intake_view([]))

        self.assertIn("Ajout de document", html)
        self.assertIn("Depot local", html)
        self.assertIn("Confidentialite avant partage", html)
        self.assertIn("piece -> point -> action -> preuve", html)
        self.assertIn("Documents a ajouter", html)
        self.assertIn("devis_toiture.pdf", html)
        self.assertIn("version biffee requise", html)
        self.assertIn("Prochaine action", html)
        self.assertIn("Evenements futurs", html)
        self.assertIn("document_added", html)
        self.assertIn("Deposer un document depuis ce poste", html)
        self.assertIn("Le depot local recoit les fichiers", html)
        self.assertIn('type="file"', html)
        self.assertIn("Le parcours d'ajout est pret a brancher", empty_html)
        self.assertNotIn('href="/document-intake', html)
        self.assertNotIn('href="/ajout-document', html)

    def test_ui_layer_does_not_define_route_or_touch_app_template_contract(self) -> None:
        source = VIEW_PATH.read_text(encoding="utf-8")
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertNotIn("@app.", source)
        self.assertNotIn("@router.", source)
        self.assertNotIn("FastAPI", source)
        self.assertIn('extends "base.html"', template)
        self.assertIn("build_document_intake_view", source)

    def test_documentation_names_integration_boundary_and_privacy_contract(self) -> None:
        doc = DOC_PATH.read_text(encoding="utf-8")
        normalized = doc.lower()

        for marker in [
            "UI ajout de document",
            "document_intake",
            "document_intake_view.py",
            "document_intake.html",
            "sans modifier app.py",
            "sans modifier base.html",
            "deposer localement",
            "confidentialite",
            "piece -> point -> action -> preuve",
            "statut runtime",
            "prochaine action",
            "aucun nom reel",
            "aucun chemin prive",
            "aucun raw dans cloud",
            "tests cibles",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), normalized)

    def _render(self, document_intake: dict[str, object]) -> str:
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
        except ImportError:
            self.skipTest("Jinja2 unavailable")

        env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(("html", "xml")),
        )
        env.globals["url_for"] = lambda name, **kwargs: f"/static/{kwargs.get('path', '')}"
        rendered = env.get_template("document_intake.html").render(
            model={
                "instance": {"name": "Demo copro", "year": 2026, "id": "demo"},
                "document_intake": document_intake,
            },
            document_intake=document_intake,
            page="document_intake",
            ui_token_query="",
            ui_token_param="",
        )
        return unescape(rendered)


if __name__ == "__main__":
    unittest.main()
