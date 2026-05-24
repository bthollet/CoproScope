from __future__ import annotations

import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, AG_FIELDS, load_instance, read_csv, write_csv
from coproscope.modules import decisionops
from coproscope.web.agcontentieux_view import build_agcontentieux_passation_view, flatten_work_items


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTANCE_ROOT = REPO_ROOT / "examples" / "synthetic_copro"
TEMPLATE_DIR = REPO_ROOT / "server" / "src" / "coproscope" / "web" / "templates"
TEMPLATE_PATH = TEMPLATE_DIR / "agcontentieux.html"


class AGContentieuxUiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(INSTANCE_ROOT, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _documents(self) -> tuple[list[str], list[dict[str, str]]]:
        fields, rows = read_csv(self.instance.register("documents"))
        return fields or list(DEFAULT_DOCUMENT_FIELDS), rows

    def _render_template(self, model: dict[str, object]) -> str:
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
        except ImportError:
            self.skipTest("Jinja2 unavailable")

        env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(("html", "xml")),
        )
        env.globals["url_for"] = lambda name, **kwargs: f"/static/{kwargs.get('path', '')}"
        return env.get_template("agcontentieux.html").render(
            model={
                "instance": {
                    "id": self.instance.instance_id,
                    "name": self.instance.display_name,
                    "year": "2026",
                }
            },
            page="agcontentieux",
            ui_token_query="",
            ui_token_param="",
            agcontentieux=model,
        )

    def _seed_contentieux_and_decision(self) -> None:
        fields, rows = self._documents()
        rows.append(
            {
                **{field: "" for field in fields},
                "doc_id": "DOC-CONTENTIEUX",
                "sha256": "abcdef1234567890",
                "file_name": "note_contentieux_factuelle.md",
                "document_type": "Note_Contentieux",
                "lot": "Contentieux",
                "suspected_date": "2026-05-10",
                "restriction_reasons": "contentieux",
                "notes": "Dossier contentieux factuel pour test UI.",
            }
        )
        write_csv(self.instance.register("documents"), fields, rows)
        write_csv(
            decisionops.decision_register_path(self.instance),
            decisionops.DECISION_ACTION_FIELDS,
            [
                {
                    "decision_action_id": "DAP-AG-001",
                    "ag_id": "AG-2026-04-29",
                    "source_doc_id": "DOC-4E884D06E0AD",
                    "source_file": "2026-04-29_convocation_ag.txt",
                    "resolution_ref": "R01",
                    "decision_text": "Question sur les annexes de convocation",
                    "action_attendue": "Demander au syndic la piece manquante avant l'AG.",
                    "responsable": "Conseil syndical",
                    "echeance": "2026-06-01",
                    "preuve_attendue": "Annexe de convocation transmise.",
                    "proof_doc_ids": "",
                    "proof_document_types": "Annexe_AG",
                    "related_request_ids": "",
                    "related_invoice_refs": "",
                    "related_work_refs": "",
                    "statut": "PREUVE_A_DEMANDER",
                    "priorite": "P1",
                    "notes": "Question issue de la convocation.",
                }
            ],
        )

    def test_model_surfaces_ag_contentieux_passation_work_items(self) -> None:
        self._seed_contentieux_and_decision()

        model = build_agcontentieux_passation_view(self.instance, 2026)

        self.assertEqual(model["summary"]["questions"], 1)
        self.assertGreaterEqual(model["summary"]["pieces"], 1)
        self.assertEqual(model["summary"]["contentieux"], 1)
        self.assertEqual(model["summary"]["risk_notes"], 1)
        self.assertGreaterEqual(model["summary"]["evidence"], 2)
        self.assertFalse(model["summary"]["is_empty"])
        self.assertIn("non juridique", model["novice"]["legal_notice"])
        self.assertEqual(model["passation"]["pack"]["restriction"], "confidential")
        self.assertIn("contentieux-1", model["passation"]["pack"]["contentieux_case_ids"])

        items = flatten_work_items(model)
        joined = " ".join(str(item) for item in items)
        self.assertIn("Question sur les annexes de convocation", joined)
        self.assertIn("note_contentieux_factuelle.md", joined)
        self.assertIn("preuve", joined.lower())
        self.assertIn("diffusion", joined.lower())
        self.assertIn("echeance", joined.lower())

    def test_model_exposes_clear_empty_state_without_raw_paths(self) -> None:
        write_csv(self.instance.register("documents"), list(DEFAULT_DOCUMENT_FIELDS), [])
        write_csv(self.instance.register("ag"), list(AG_FIELDS), [])
        decision_path = decisionops.decision_register_path(self.instance)
        if decision_path.exists():
            decision_path.unlink()

        model = build_agcontentieux_passation_view(self.instance, 2026)
        text = str(model)

        self.assertTrue(model["summary"]["is_empty"])
        self.assertEqual(model["summary"]["questions"], 0)
        self.assertEqual(model["summary"]["pieces"], 0)
        self.assertIn("Rien a preparer", model["novice"]["empty_title"])
        self.assertIn("Aucun element charge", " ".join(model["passation"]["pack"]["open_points"]))
        self.assertNotIn(str(self.instance_root), text)
        self.assertNotIn("raw\\", text.lower())
        self.assertNotIn("raw/", text.lower())

    def test_template_contains_required_passation_surface(self) -> None:
        text = TEMPLATE_PATH.read_text(encoding="utf-8")

        for expected in [
            "Question AG",
            "Piece de convocation",
            "Dossier contentieux",
            "Note de risque non juridique",
            "Preuves et sources",
            "Restriction / diffusion",
            "Prochaine action",
            "Echeance",
            "Statut",
            "Pack passation",
            "Etat vide",
        ]:
            self.assertIn(expected, text)

    def test_template_renders_seeded_model_with_novice_copy(self) -> None:
        self._seed_contentieux_and_decision()
        model = build_agcontentieux_passation_view(self.instance, 2026)

        body = unescape(self._render_template(model))

        self.assertIn("AG, contentieux, passation", body)
        self.assertIn("Question AG", body)
        self.assertIn("Piece de convocation", body)
        self.assertIn("Dossier contentieux", body)
        self.assertIn("Note de risque non juridique", body)
        self.assertIn("Pack passation AG/contentieux 2026", body)
        self.assertIn("Demander au syndic la piece manquante avant l'AG.", body)
        self.assertIn("note_contentieux_factuelle.md", body)
        self.assertIn("confidentiel", body)
        self.assertIn("conseil syndical", body)
        self.assertNotIn(str(self.instance_root), body)


if __name__ == "__main__":
    unittest.main()
