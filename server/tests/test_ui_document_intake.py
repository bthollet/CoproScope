from __future__ import annotations

import unittest
from html import unescape
from pathlib import Path

from coproscope.web.document_intake_view import build_document_intake_view


REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = REPO_ROOT / "server" / "src" / "coproscope" / "web" / "templates"
VIEW_PATH = REPO_ROOT / "server" / "src" / "coproscope" / "web" / "document_intake_view.py"
TEMPLATE_PATH = TEMPLATE_DIR / "document_intake.html"
DOC_PATH = REPO_ROOT / "docs" / "archive" / "notes_integration" / "integration_ui_ajout_document.md"


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
        self.assertEqual(view["title"], "Absorber des informations")
        self.assertEqual(card["document_label"], "Document 1")
        self.assertEqual(card["doc_id"], "DOC-PV-2026")
        self.assertEqual(card["source_id"], "inbox")
        self.assertEqual(card["privacy"]["status_label"], "reserve au conseil syndical")
        self.assertIn("piece -> point -> action -> preuve", view["novice_steps"][3]["body"])
        self.assertIn("PV AG 2026", card["attachments"][0]["chain_label"])
        self.assertIn("Un chemin prive a ete masque", " ".join(card["warning_labels"]))
        self.assertEqual(view["docops_workflow"][0]["counter"], "0/1")
        self.assertEqual(view["docops_workflow"][1]["counter"], "0/1")
        self.assertEqual(view["docops_workflow"][5]["counter"], "0/1")

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

    def test_view_model_counts_docops_workflow_steps(self) -> None:
        view = build_document_intake_view(
            [
                {
                    "doc_id": "DOC-READY",
                    "sha256": "a" * 64,
                    "local_reference": "opaque/DOC-READY",
                    "status_ocr": "TEXT_EXTRACTED",
                    "text_char_count": "1200",
                    "document_type": "FACTURE_COMPTE",
                    "classification_status": "PROPOSED",
                    "privacy_status": "RESERVE_CS",
                },
                {
                    "doc_id": "DOC-RENFORT",
                    "sha256": "b" * 64,
                    "local_reference": "opaque/DOC-RENFORT",
                    "status_ocr": "OCR_REQUIRED",
                    "document_type": "A_CLASSER",
                    "classification_status": "A_CLASSER",
                    "privacy_status": "A_ARBITRER",
                },
            ]
        )

        counters = {step["key"]: step["counter"] for step in view["docops_workflow"]}
        self.assertEqual(counters["depot"], "2/2")
        self.assertEqual(counters["texte"], "1/2")
        self.assertEqual(counters["type"], "1/2")
        self.assertEqual(counters["confidentialite"], "1/2")
        self.assertEqual(counters["renfort"], "1/2")
        self.assertEqual(counters["pret"], "1/2")


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

        self.assertIn("Ajouter des pieces au coffre local", html)
        self.assertIn("Sources d'absorption", html)
        self.assertIn("Inbox du coffre", html)
        self.assertIn("Glisser-deposer", html)
        self.assertIn("Drive Desktop", html)
        self.assertIn("Mailbox", html)
        self.assertIn("Prequalification locale", html)
        self.assertIn("Validation humaine", html)
        self.assertIn("Sans IA/cloud", html)
        self.assertIn("Glissez vos fichiers ici", html)
        self.assertIn("Etapes de traitement des pieces", html)
        self.assertIn("Texte reconnu", html)
        self.assertIn("Traitement renforce", html)
        self.assertIn("Pretes a rattacher", html)
        self.assertIn("Corriger une file de documents", html)
        self.assertIn("Ouvrir le tri de lot", html)
        self.assertIn('href="/documents/tri-feedback"', html)
        self.assertIn("Continuer document par document", html)
        self.assertIn("DocOps propose, vous confirmez.", html)
        self.assertIn("Reserve CS demande un motif.", html)
        self.assertIn("A masquer demande des pages ou plages.", html)
        self.assertIn("A decider plus tard ne diffuse rien.", html)
        self.assertIn("Confidentialite avant partage", html)
        self.assertIn("piece -> point -> action -> preuve", html)
        self.assertIn("Documents a ajouter", html)
        self.assertIn("informations a qualifier", html)
        self.assertIn("devis_toiture.pdf", html)
        self.assertIn("Proposition locale", html)
        self.assertIn("a masquer avant partage", html)
        self.assertIn("Prochaine action", html)
        self.assertIn("Type documentaire", html)
        self.assertIn("Confidentialite", html)
        self.assertIn('name="document_type"', html)
        self.assertIn('name="privacy_status"', html)
        self.assertIn("Diffusion bloquee", html)
        self.assertIn("OCR / texte local", html)
        self.assertNotIn("Evenements futurs", html)
        self.assertNotIn("document_added", html)
        self.assertIn("Deposer un document depuis ce poste", html)
        self.assertIn("Le depot local recoit les fichiers", html)
        self.assertIn('type="file"', html)
        self.assertIn('name="return" value="document_intake"', html)
        self.assertIn('required aria-describedby="document-intake-upload-help"', html)
        self.assertIn("Je ne sais pas encore", html)
        self.assertIn("AG", html)
        self.assertIn("FACTURE_COMPTE", html)
        self.assertIn("CONTRAT_ASSURANCE_SYNDIC", html)
        self.assertIn("CONTENTIEUX_INCIDENT", html)
        self.assertIn("A decider", html)
        self.assertIn("Peut etre partage tel quel", html)
        self.assertIn("Si vous hesitez, gardez A decider ou Je ne sais pas encore.", html)
        self.assertIn("Enregistrer ce choix local", html)
        self.assertIn("Deposez vos premiers documents", empty_html)
        self.assertNotIn("Corriger une file de documents", empty_html)
        self.assertNotIn("document_intake_view.py", html)
        self.assertNotIn("document_intake.html", html)
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
            "branchement novice",
            "retour apres upload",
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
            intake_sources={
                "selected_source": "all",
                "selected_label": "Toutes les sources",
                "total_to_qualify": document_intake["summary"]["total"],
                "human_review_notice": "Prequalification locale: CoproScope propose, vous confirmez avant classement, rattachement ou diffusion.",
                "source_cards": [
                    {
                        "id": "inbox",
                        "label": "Inbox du coffre",
                        "kind_label": "Dossier du vault",
                        "state_label": "Actif",
                        "state_tone": "ok",
                        "count": document_intake["summary"]["total"],
                        "last_absorption": "Registre local",
                        "rule_label": "Validation humaine obligatoire.",
                        "href": "/documents/ajouter?source=inbox",
                        "selected": False,
                    },
                    {
                        "id": "drag_drop",
                        "label": "Glisser-deposer",
                        "kind_label": "Upload web local",
                        "state_label": "Actif",
                        "state_tone": "ok",
                        "count": 0,
                        "last_absorption": "Depot web",
                        "rule_label": "Copie locale.",
                        "href": "/documents/ajouter?source=drag_drop",
                        "selected": False,
                    },
                    {
                        "id": "drive_desktop",
                        "label": "Drive Desktop",
                        "kind_label": "Dossier synchronise local",
                        "state_label": "A configurer",
                        "state_tone": "p2",
                        "count": 0,
                        "last_absorption": "Aucun connecteur cloud actif.",
                        "rule_label": "Le cloud n'est pas source de verite.",
                        "href": "/documents/ajouter?source=drive_desktop",
                        "selected": False,
                    },
                    {
                        "id": "mailbox",
                        "label": "Mailbox",
                        "kind_label": "Connecteur futur",
                        "state_label": "A connecter",
                        "state_tone": "p2",
                        "count": 0,
                        "last_absorption": "Aucun IMAP/OAuth actif.",
                        "rule_label": "Permissions minimales.",
                        "href": "/documents/ajouter?source=mailbox",
                        "selected": False,
                    },
                ],
                "source_filters": [
                    {"id": "all", "label": "Toutes les sources", "count": document_intake["summary"]["total"], "href": "/documents/ajouter", "selected": True}
                ],
            },
            page="document_intake",
            ui_token_query="",
            ui_token_param="",
        )
        return unescape(rendered)


if __name__ == "__main__":
    unittest.main()
