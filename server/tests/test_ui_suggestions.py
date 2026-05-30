from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance, write_csv
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app
from coproscope.web.suggestions_view import build_suggestions_view


REQUIRED_LABELS = (
    "Suggestions utiles",
    "Suggestions sourcees, preuves et suites possibles",
    "Suggestions a relire",
    "Suggestions sourcees",
    "Cartes affichables",
    "Revue humaine",
    "Preuve",
    "Destination",
    "Effet automatique",
    "Suggestions affichables",
    "File de revue",
    "Voir actions",
    "Voir demandes syndic",
    "Creer action automatiquement",
    "Exporter sans revue",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "C:\\",
    "file://",
    "raw",
    "restricted",
    "logs",
    "private",
    "secretValue",
    "OAuth",
    "IMAP",
    "SMTP",
)


class UiSuggestionsTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self, access_token: str | None = None):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")
        return TestClient(create_app(self.instance, 2025, access_token=access_token))

    def test_suggestions_view_model_falls_back_to_fictive_examples(self) -> None:
        view = build_suggestions_view(year=2026)

        self.assertEqual(view["title"], "Suggestions utiles")
        self.assertIn("FICTIF", view["notice"])
        self.assertEqual(len(view["suggestions"]), 3)
        self.assertEqual(len(view["cards"]), 1)
        self.assertEqual(view["cards"][0]["destination_label"], "Demande syndic")
        self.assertTrue(any(action["enabled"] == "false" for action in view["actions"]))

    def test_suggestions_view_model_reads_derived_rows_without_leaking_paths(self) -> None:
        reports_dir = self.instance.artifact("reports_dir")
        reports_dir.mkdir(parents=True, exist_ok=True)
        write_csv(
            reports_dir / "suggestions_utiles.csv",
            [
                "suggestion_id",
                "title",
                "why",
                "proof",
                "source",
                "next_action",
                "impact",
                "effort",
                "confidence",
                "public",
                "transformations",
            ],
            [
                {
                    "suggestion_id": "SUG-LOCAL-1",
                    "title": "Relancer le syndic",
                    "why": "Piece source signalee dans C:\\Users\\demo\\raw\\note.txt",
                    "proof": r"C:\\Users\\demo\\private\\preuve.pdf",
                    "source": "DocOps",
                    "next_action": "Relire puis preparer une demande.",
                    "impact": "fort",
                    "effort": "faible",
                    "confidence": "haute",
                    "public": "conseil_syndical",
                    "transformations": "demande;action",
                }
            ],
        )
        write_csv(
            reports_dir / "suggestions_reviews.csv",
            ["review_id", "suggestion_id", "reviewer", "decision", "rationale", "selected_outcome_type", "public"],
            [
                {
                    "review_id": "REV-LOCAL-1",
                    "suggestion_id": "SUG-LOCAL-1",
                    "reviewer": "CS",
                    "decision": "accepted",
                    "rationale": "Preuve lisible.",
                    "selected_outcome_type": "demande",
                    "public": "conseil_syndical",
                }
            ],
        )

        view = build_suggestions_view(instance=self.instance, year=2026)
        visible = str(view)

        self.assertEqual(view["cards"][0]["source_label"], "Synthese derivee")
        self.assertIn("[retire]", visible)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_suggestions_route_is_token_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/suggestions")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Suggestions utiles", forbidden.text)

        response = client.get("/suggestions?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn('href="/suggestions?token=local-secret"', response.text)
        self.assertIn('href="/actions?scope=suggestions&amp;token=local-secret"', response.text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)

        visible = _visible_text(text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_suggestions_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("suggestions uses dedicated view")):
            response = self._client(access_token="local-secret").get(
                "/suggestions",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Suggestions utiles", response.text)
        self.assertIn("Aucune creation", response.text)

    def test_suggestions_css_stacks_table_on_mobile(self) -> None:
        css_path = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "styles_part_25.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn(".sug-table", css)
        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn("grid-template-columns: 1fr", css)
        mobile_block = re.search(r"@media.*", css, flags=re.DOTALL).group(0)
        self.assertNotIn("overflow-x: auto", mobile_block)


def _visible_text(html: str) -> str:
    without_scripts = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    return " ".join(without_tags.split())


if __name__ == "__main__":
    unittest.main()
