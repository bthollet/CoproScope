from __future__ import annotations

import unittest
from html import unescape
from pathlib import Path

from coproscope.core.events_v1 import SIGNATURE_STATUS_PENDING
from coproscope.modules.annotationops import ANNOTATION_EVENT_TYPE
from coproscope.web.annotation_view import build_annotations_view, build_annotations_view_from_rows


REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = REPO_ROOT / "server" / "src" / "coproscope" / "web" / "templates"
ANNOTATION_VIEW_PATH = REPO_ROOT / "server" / "src" / "coproscope" / "web" / "annotation_view.py"
ANNOTATION_TEMPLATE_PATH = TEMPLATE_DIR / "annotations.html"
DOC_PATH = REPO_ROOT / "docs" / "archive" / "notes_integration" / "integration_ui_annotations.md"
HASH = "sha256:" + "a" * 64


class AnnotationUiTests(unittest.TestCase):
    def test_view_model_prepares_page_zone_comment_chain_confidentiality_and_future_event(self) -> None:
        view = build_annotations_view_from_rows(
            [
                {
                    "annotation_id": "ANN-PV-2026-R7",
                    "doc_id": "DOC-PV-2026",
                    "sha256": HASH,
                    "page": "7",
                    "zone": {"x": 0.12, "y": 0.25, "width": 0.3, "height": 0.08},
                    "commentaire": "Verifier la mention de la resolution travaux.",
                    "author_ref": "user:cs-1",
                    "created_at": "2026-05-20T08:30:00Z",
                    "point_id": "AG-2026-R7",
                    "action_id": "ACT-TRAVAUX-1",
                    "proof_ref": "PROOF-PV-R7",
                    "diffusion": "conseil syndical",
                    "confidentialite": "reserve_cs",
                }
            ],
            document_label="DOC-PV-2026",
        )

        self.assertTrue(view["has_annotations"])
        self.assertEqual(view["summary"]["total"], 1)
        self.assertEqual(view["summary"]["ready_events"], 1)
        row = view["rows"][0]
        self.assertEqual(row["page_label"], "page 7")
        self.assertIn("largeur 30%", row["zone"]["label"])
        self.assertEqual(row["comment"], "Verifier la mention de la resolution travaux.")
        self.assertEqual(row["chain_label"], "Point AG-2026-R7 -> Action ACT-TRAVAUX-1 -> Preuve PROOF-PV-R7")
        self.assertEqual(row["confidentiality_label"], "reserve conseil syndical")
        self.assertEqual(row["event"]["event_type"], ANNOTATION_EVENT_TYPE)
        self.assertEqual(row["event"]["signature_status"], SIGNATURE_STATUS_PENDING)
        self.assertFalse(row["sidecar"]["source_write_allowed"])

    def test_view_model_masks_private_paths_and_blocks_event_readiness(self) -> None:
        view = build_annotations_view_from_rows(
            [
                {
                    "annotation_id": "ANN-PRIVATE",
                    "doc_id": "DOC-PV-PRIVATE",
                    "source_path": r"C:\Users\ExampleUser\secret\pv.pdf",
                    "sha256": HASH,
                    "page": "1",
                    "comment": r"Voir C:\Users\ExampleUser\secret\notes.txt",
                    "author_ref": "user:cs-1",
                    "created_at": "2026-05-20T09:00:00Z",
                    "point_ref": "POINT-1",
                    "action_ref": "ACT-1",
                    "proof_ref": "PROOF-1",
                }
            ]
        )

        row = view["rows"][0]
        rendered = str(view)

        self.assertFalse(row["event_ready"])
        self.assertTrue(row["source_hint_blocked"])
        self.assertTrue(row["comment_masked"])
        self.assertIn("Commentaire masque", row["comment"])
        self.assertTrue(any(issue["field"] == "source_hint" for issue in row["issues"]))
        self.assertNotIn(r"C:\Users", rendered)
        self.assertNotIn("secret", rendered.lower())
        self.assertNotIn("notes.txt", rendered)

    def test_template_renders_annotations_without_global_route_or_private_path(self) -> None:
        annotations = build_annotations_view_from_rows(
            [
                {
                    "annotation_id": "ANN-IMG-1",
                    "document_ref": "IMG-FACADE-1",
                    "document_hash": HASH,
                    "target_kind": "image",
                    "page": "1",
                    "zone": [0.4, 0.2, 0.2, 0.2],
                    "comment": "Localiser la fissure visible sur la photo.",
                    "author_ref": "user:cs-1",
                    "created_at": "2026-05-20T11:00:00Z",
                    "point_ref": "INC-FACADE",
                    "action_ref": "ACT-EXPERTISE",
                    "proof_ref": "PHOTO-FACADE",
                    "confidentiality": "a_biffer",
                    "diffusion": "public_apres_expurgation",
                }
            ],
            source_label="annotationops",
        )

        html = self._render(annotations)

        self.assertIn("Annotations collaboratives", html)
        self.assertIn("Page / zone", html)
        self.assertIn("page 1", html)
        self.assertIn("x 40%, y 20%, largeur 20%, hauteur 20%", html)
        self.assertIn("Localiser la fissure visible sur la photo.", html)
        self.assertIn("Point INC-FACADE -> Action ACT-EXPERTISE -> Preuve PHOTO-FACADE", html)
        self.assertIn("Confidentialite", html)
        self.assertIn("biffage requis", html)
        self.assertIn("Evenement futur signe", html)
        self.assertIn(ANNOTATION_EVENT_TYPE, html)
        self.assertIn(SIGNATURE_STATUS_PENDING, html)
        self.assertIn("source_write_allowed=False", html)
        self.assertNotIn(r"C:\Users", html)
        self.assertNotIn("file://", html)
        self.assertNotIn('href="/annotations', html)

    def test_empty_state_and_static_boundary_are_explicit(self) -> None:
        empty_html = self._render(build_annotations_view([]))
        source = ANNOTATION_VIEW_PATH.read_text(encoding="utf-8")
        template = ANNOTATION_TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("Aucune annotation a afficher", empty_html)
        self.assertIn("page, une zone, un commentaire", empty_html)
        self.assertNotIn("@app.", source)
        self.assertNotIn("@router.", source)
        self.assertNotIn("FastAPI", source)
        self.assertNotIn('href="/annotations', template)

    def test_documentation_names_integration_contract(self) -> None:
        doc = DOC_PATH.read_text(encoding="utf-8").lower()

        for marker in [
            "ui annotations collaboratives",
            "annotation_view.py",
            "annotations.html",
            "pas de route",
            "page/zone",
            "commentaire",
            "point/action/preuve",
            "confidentialite",
            "evenement futur signe",
            "aucun chemin prive",
            "non destructif",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, doc)

    def _render(self, annotations: dict[str, object]) -> str:
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
        except ImportError:
            return unescape(ANNOTATION_TEMPLATE_PATH.read_text(encoding="utf-8"))

        env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(("html", "xml")),
        )
        env.globals["url_for"] = lambda name, **kwargs: f"/static/{kwargs.get('path', '')}"
        rendered = env.get_template("annotations.html").render(
            model={"instance": {"name": "Demo copro", "year": 2026, "id": "demo"}, "annotations": annotations},
            annotations=annotations,
            page="annotations",
            ui_token_query="",
            ui_token_param="",
        )
        return unescape(rendered)


if __name__ == "__main__":
    unittest.main()
