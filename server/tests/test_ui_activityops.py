from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance
from coproscope.web.activity_view import build_activity_view
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app


REQUIRED_LABELS = (
    "Activite en cours",
    "Travaux agents, blocages et prochains passages",
    "Travaux actifs",
    "Blocages",
    "Lire les statuts",
    "Travaille",
    "A relire",
    "Bloque",
    "Dernier passage",
    "Prochaine relance",
    "Travaux agents et heartbeats",
    "Blocages a regarder",
    "Derniers passages heartbeat",
    "Retour aux indicateurs",
    "Ouvrir journal technique",
    "Afficher consignes longues",
)

FORBIDDEN_VISIBLE_MARKERS = (
    "C:\\",
    "file://",
    "raw",
    "restricted",
    "logs",
    "private",
    "token=",
    "secretValue",
    "prompt complet",
    "OAuth",
)


class UiActivityOpsTests(unittest.TestCase):
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

    def test_activity_view_model_reads_presence_without_leaking_sensitive_details(self) -> None:
        docs_root = Path(self.tempdir.name) / "docs"
        docs_root.mkdir()
        (docs_root / "presence_agents.md").write_text(
            "\n".join(
                [
                    "| Conversation | Roadmap | Chantier | Role | Statut | Ownership | Worktree | Debut | Expire | Mission | Notes |",
                    "|---|---|---|---|---|---|---|---|---|---|---|",
                    "| `CONV-TEST-1` | `RM-TEST` | `CH-TEST` | Owner UI | `EN_COURS` | `docs/trace.md`; `C:\\Users\\demo\\raw\\x.txt` | local | 2026-05-26 00:00 +02:00 | 2026-05-26 01:00 +02:00 | Continuer sans token=abc | prompt complet C:\\Users\\demo\\private\\note.txt secretValue |",
                    "| `CONV-TEST-2` | `RM-TEST` | `CH-TEST` | QA | `BLOQUE` | `docs/trace.md` | local | 2026-05-26 00:01 +02:00 | n/a | Attendre action manuelle | serveur visible a relancer |",
                ]
            ),
            encoding="utf-8",
        )
        (docs_root / "roadmap_backlog_central.md").write_text(
            "| Date | Roadmap | Event | Detail |\n"
            "|---|---|---|---|\n"
            "| 2026-05-26 00:00 +02:00 | `relance-equipe-agile-gouvernail-autonome` | `HEARTBEAT` | prompt complet token=abc C:\\Users\\demo\\logs\\x.log |\n",
            encoding="utf-8",
        )

        view = build_activity_view(docs_root)
        visible = str(view)

        self.assertEqual(view["title"], "Activite en cours")
        self.assertEqual(len(view["activities"]), 2)
        self.assertEqual(view["blocked"][0]["blocked_by"], "serveur a relancer")
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_activity_route_is_token_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/pilotage/activite")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Activite en cours", forbidden.text)

        response = client.get("/pilotage/activite?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn('href="/pilotage/activite?token=local-secret"', response.text)
        self.assertIn('href="/pilotage?token=local-secret"', response.text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)

        visible = _visible_text(text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_activity_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("activity uses dedicated view")):
            response = self._client(access_token="local-secret").get(
                "/pilotage/activite",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Activite en cours", response.text)
        self.assertIn("Details techniques", response.text)

    def test_activity_css_stacks_table_on_mobile(self) -> None:
        css_path = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "styles_part_24.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn(".act-table", css)
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
