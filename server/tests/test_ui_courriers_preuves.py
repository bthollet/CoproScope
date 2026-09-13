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
from coproscope.web.courriers_preuves_view import build_courriers_preuves_view


# **Cinq libelles ont ete retires de cette liste le 2026-09-11, et ils
# exigeaient que l'ecran reste invente.** `Brouillons a valider`,
# `Preuves a rattacher` et `Reponses recues` etaient les titres de trois
# compteurs ecrits en dur - `3`, `2`, `1` - qui **contredisaient le tableau
# situe juste en dessous**: un seul des trois brouillons portait le statut
# annonce, et le tableau des preuves en comptait trois quand le bandeau en
# annoncait deux. `Scenario FICTIF` et `Verifier avant envoi` ne sont plus vrais
# des que la page lit vraiment ce que la chaine a calcule.
#
# Ce qui RESTE est ce qui survit au branchement: le titre, les definitions, les
# limites que l'outil s'impose et les gestes bloques. C'etait du contenu
# REDIGE, pas une donnee inventee.
REQUIRED_LABELS = (
    "Courriers et preuves",
    "Verification humaine requise",
    "Brouillon",
    "Texte prepare localement, pas encore transmis",
    "Mandat",
    "Raison qui autorise quelqu'un a agir ou ecrire",
    "Preuve de depot",
    "Trace que l'envoi a ete depose chez un service",
    "Preuve de reception",
    "recu ou refuse",
    "Validation humaine",
    "Copier le brouillon",
    "Rattacher une preuve",
    "source_of_truth=false",
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
    "LRAR",
    "Drive",
    "API prestataire",
    "email",
    "telephone",
    "adresse",
    "Envoyer",
    "Envoyer automatiquement",
    "Envoi automatique pret",
    "courrier reel",
    "secretValue",
)


class UiCourriersPreuvesTests(unittest.TestCase):
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
        return TestClient(create_app(self.instance, 2025, access_token=access_token, rebrancher=frozenset({"courriers_preuves"})))

    def test_courriers_preuves_sans_rapport_se_degrade_proprement(self) -> None:
        """**Ce test exigeait que l'ecran reste invente, jusqu'au 2026-09-11.**

        Il verifiait que les trois brouillons commencent par `DRAFT-FICTIF-`,
        donc il aurait rougi le jour du branchement quelle que soit la qualite
        de celui-ci. Et il exigeait trois compteurs dont **les valeurs
        contredisaient le tableau de la meme page**.

        Ce qui est garde ici est la propriete qui survit: sans rapport produit,
        l'ecran ne montre rien d'invente, il dit ce qu'il faut faire, et les
        transmissions restent bloquees.
        """
        view = build_courriers_preuves_view(2026)

        self.assertEqual(view["title"], "Courriers et preuves")
        self.assertEqual(view["etat_matiere"], "chaine_non_passee")
        self.assertEqual(len(view["summary"]), 3)
        self.assertEqual(len(view["definitions"]), 4)
        self.assertEqual(view["drafts"], [])
        self.assertEqual(view["proofs"], [])
        self.assertTrue(view["status"]["cta"],
                        "un ecran sans matiere doit dire quoi faire")
        self.assertTrue(any(a["enabled"] == "false" for a in view["actions"]),
                        "les transmissions doivent rester bloquees")

    def test_courriers_preuves_route_is_token_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/courriers/preuves")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Courriers et preuves", forbidden.text)

        response = client.get("/courriers/preuves?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        # Ecran debranche (RM-2026-0183): plus d'entree dans la navigation de la coque.
        self.assertNotIn('href="/courriers/preuves?token=local-secret"', response.text)
        for label in REQUIRED_LABELS:
            self.assertIn(label, text)

        visible = _visible_text(text)
        for marker in FORBIDDEN_VISIBLE_MARKERS:
            self.assertNotIn(marker, visible)

    def test_courriers_preuves_route_accepts_header_token_and_skips_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("courriers uses synthetic view")):
            response = self._client(access_token="local-secret").get(
                "/courriers/preuves",
                headers={"x-coproscope-token": "local-secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Courriers et preuves", response.text)
        self.assertIn("Aucune transmission", response.text)

    def test_courriers_preuves_css_stacks_table_on_mobile(self) -> None:
        css_path = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static" / "styles_part_18.css"
        css = css_path.read_text(encoding="utf-8")

        self.assertIn(".cpr-table", css)
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
