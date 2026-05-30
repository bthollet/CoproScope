from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance, write_csv
from coproscope.modules import incidentops
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app
from coproscope.web.incidentops_view import build_incidentops_view


REQUIRED_LABELS = (
    "Incidents et sinistres",
    "Signalements a qualifier",
    "Qualifier un signalement",
    "Incidents ouverts",
    "Preuves de cloture",
    "Signalement",
    "Fait remonte localement",
    "Sinistre",
    "Preuve de cloture",
    "Synthese neutre",
    "File incidents et sinistres",
    "Assurance",
    "Preuve attendue",
    "Decisions avant cloture",
    "Validation humaine",
    "Voir actions incidents",
    "Ajouter preuve locale",
    "Declaration assurance",
    "Partager aux coproprietaires",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "@",
    "C:\\",
    "file://",
    "raw",
    "restricted",
    "private",
    "OAuth",
    "IMAP",
    "SMTP",
    "Drive",
    "photo originale",
    "assurance reelle",
    "declaration automatique",
    "Envoyer",
    "secretValue",
)


class UiIncidentOpsTests(unittest.TestCase):
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

    def test_incidentops_view_model_falls_back_to_fictive_examples(self) -> None:
        view = build_incidentops_view(year=2026)

        self.assertEqual(view["title"], "Incidents et sinistres")
        self.assertIn("FICTIF", view["notice"])
        self.assertEqual(len(view["summary"]), 4)
        self.assertEqual(len(view["incidents"]), 3)
        self.assertTrue(any(action["enabled"] == "false" for action in view["actions"]))
        self.assertTrue(all(row["id"].startswith("INC-FICTIF-") for row in view["incidents"]))
        self.assertEqual(view["shell_model"]["instance"]["id"], "FICTIF")

    def test_incidentops_view_model_reads_local_register_without_leaking_paths(self) -> None:
        write_csv(
            incidentops.incident_register_path(self.instance),
            incidentops.INCIDENT_FIELDS,
            [
                {
                    "incident_id": "INC-LOCAL-001",
                    "date_signalement": "2026-05-03",
                    "lieu": "Parking",
                    "description": "Fuite persistante",
                    "piece_ref": "DOC-INC-1",
                    "photo_or_piece": r"C:\\Users\\demo\\raw\\photo.jpg",
                    "status": "A_QUALIFIER",
                    "source_refs": "raw/photo.jpg",
                }
            ],
        )

        view = build_incidentops_view(instance=self.instance, year=2026)
        visible = str(view)

        self.assertEqual(view["incidents"][0]["source_label"], "Registre local")
        self.assertEqual(view["incidents"][0]["status_label"], "a qualifier")
        self.assertEqual(view["incidents"][0]["proof_state"], "Piece candidate a verifier")
        self.assertIn("Assurance a qualifier", view["incidents"][0]["assurance"])
        self.assertNotIn("raw/photo.jpg", visible)
        self.assertNotIn("C:\\", visible)

    def test_incidentops_route_is_token_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/incidents")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Incidents et sinistres", forbidden.text)

        response = client.get("/incidents?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn('href="/incidents?token=local-secret"', response.text)
        self.assertIn('href="/actions?scope=incidents&amp;token=local-secret"', response.text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)

        visible = _visible_text(text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_incidentops_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("incidents uses dedicated view")):
            response = self._client(access_token="local-secret").get(
                "/incidents",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Incidents et sinistres", response.text)
        self.assertIn("Aucune declaration", response.text)

    def test_incidentops_css_stacks_table_on_mobile(self) -> None:
        css_path = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "styles_part_22.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn(".inc-table", css)
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
