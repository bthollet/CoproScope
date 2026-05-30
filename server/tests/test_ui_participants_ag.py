from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app
from coproscope.web.participants_ag_view import build_participants_ag_view


REQUIRED_LABELS = (
    "Participants et droits AG",
    "Scenario FICTIF",
    "Verification humaine requise",
    "Verifier les pouvoirs",
    "Coproprietaires a verifier",
    "Pouvoirs recus",
    "Votes incomplets",
    "Mots utiles pour l'AG",
    "Voix AG",
    "Nombre de voix utilise pour voter une resolution",
    "Pouvoir",
    "Document par lequel un coproprietaire confie son vote",
    "Mandataire",
    "Personne qui vote pour un coproprietaire absent",
    "Feuille de presence",
    "Preuve de qui etait present",
    "Personnes a verifier",
    "OWN-FICTIF-01",
    "Droits et pouvoirs AG",
    "Presence et pouvoirs",
    "Resolutions a rattacher",
    "Sources et sorties bloquees",
    "Actions bloquees",
    "Aucun import reel",
    "Aucun vote officiel",
    "source_of_truth=false",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "@",
    "C:\\",
    "file://",
    "raw",
    "restricted",
    "private",
    "coproprietaires.csv",
    "Export officiel pret",
    "Vote officiel enregistre",
    "Convocation envoyee",
    "signature qualifiee",
    "telephone",
    "OAuth",
    "Drive",
)


class UiParticipantsAgTests(unittest.TestCase):
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

    def test_participants_ag_view_model_is_synthetic_and_blocks_official_actions(self) -> None:
        view = build_participants_ag_view(2026)

        self.assertEqual(view["title"], "Participants et droits AG")
        self.assertIn("FICTIF", view["notice"])
        self.assertEqual(len(view["participants"]), 4)
        self.assertEqual(len(view["summary"]), 3)
        self.assertEqual(len(view["definitions"]), 4)
        self.assertEqual(len(view["resolutions"]), 3)
        self.assertTrue(any(action["enabled"] == "false" for action in view["actions"]))
        self.assertTrue(all(person["owner_id"].startswith("OWN-FICTIF-") for person in view["participants"]))
        self.assertTrue(all(person["lot"].startswith("LOT-") for person in view["participants"]))
        self.assertIn("Votes incomplets", view["summary"][2]["label"])
        self.assertEqual(view["shell_model"]["instance"]["id"], "FICTIF")

    def test_participants_ag_route_is_token_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/gouvernance/participants-ag")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Participants et droits AG", forbidden.text)

        response = client.get("/gouvernance/participants-ag?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn('href="/gouvernance/participants-ag?token=local-secret"', response.text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)

        visible = _visible_text(text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_participants_ag_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("participants ag uses synthetic view")):
            response = self._client(access_token="local-secret").get(
                "/gouvernance/participants-ag",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Participants et droits AG", response.text)
        self.assertIn("Aucun import reel", response.text)

    def test_participants_ag_css_stacks_table_on_mobile(self) -> None:
        css_path = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "styles_part_17.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn(".pag-table", css)
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
