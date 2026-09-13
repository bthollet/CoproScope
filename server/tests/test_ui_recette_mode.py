from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.web.app import create_app


class UiRecetteModeTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self, *, recette_mode: bool, access_token: str | None = "local-secret"):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")
        return TestClient(create_app(self.instance, 2025, access_token=access_token, recette_mode=recette_mode))

    def test_recette_toolbar_is_present_by_default(self) -> None:
        response = self._client(recette_mode=False).get("/?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertIn("id=\"cs-recette-config\"", response.text)
        self.assertIn("/static/recette_mode.js", response.text)
        self.assertIn('"recetteModeEnabled":false', response.text.replace(" ", ""))
        self.assertIn("id=\"cs-recette-mode-toggle\"", response.text)

    def test_recette_toolbar_is_present_when_enabled(self) -> None:
        response = self._client(recette_mode=True).get("/?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertIn('"recetteModeEnabled":true', response.text.replace(" ", ""))
        self.assertIn("/static/recette_mode.js", response.text)
        self.assertIn("id=\"cs-recette-mode-toggle\"", response.text)

    def test_recette_routes_require_token(self) -> None:
        client = self._client(recette_mode=True)

        self.assertEqual(client.get("/recette").status_code, 403)
        self.assertEqual(client.post("/recette/annotations", json={}).status_code, 403)
        self.assertEqual(client.get("/exports/recette-annotations.md").status_code, 403)

    def test_recette_post_and_exports_are_safe(self) -> None:
        client = self._client(recette_mode=True)
        response = client.post(
            "/recette/annotations?token=local-secret",
            json={
                "url": "/actions?token=local-secret&scope=syndic",
                "target_kind": "object",
                "target_label": "Nouvelle demande",
                "target_selector": "a",
                "target_text": "Nouvelle demande",
                "comment": "Le bouton est difficile a comprendre.",
                "severity": "important",
                "viewport_width": 1280,
                "viewport_height": 720,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        page = client.get("/recette?token=local-secret")
        json_export = client.get("/exports/recette-annotations.json?token=local-secret")
        md_export = client.get("/exports/recette-annotations.md?token=local-secret")

        self.assertEqual(page.status_code, 200)
        self.assertEqual(json_export.status_code, 200)
        self.assertEqual(md_export.status_code, 200)
        self.assertIn("Nouvelle demande", page.text)
        self.assertIn("DERIVED_RECETTE_QA", json_export.text)
        self.assertIn("Le bouton est difficile", md_export.text)
        for payload in (json_export.text, md_export.text):
            self.assertNotIn("local-secret", payload)
            self.assertNotIn("token", payload)
            self.assertNotIn("C:\\", payload)
            self.assertNotIn("file://", payload)

    def test_recette_routes_do_not_exist_when_disabled(self) -> None:
        client = self._client(recette_mode=False)

        self.assertEqual(client.get("/recette?token=local-secret").status_code, 404)

    def test_recette_routes_can_be_enabled_by_cookie(self) -> None:
        client = self._client(recette_mode=False)
        client.cookies.set("coproscope_recette_mode", "1", path="/")

        self.assertEqual(client.get("/recette?token=local-secret").status_code, 200)


class UneMarqueDesigneUnEndroitDuDocument(unittest.TestCase):
    """Les deux defauts signales par Brice le 2026-09-07, gardes sur leur axe.

    Ses mots: *ton mode de recettage ne [donne] pas de feedback sur les objets
    selectionnes*, et *ta zone de selection reste fixe quand on se deplace dans
    la page*. Meme cause pour la seconde: la marque etait `position: fixed` et
    calculee en coordonnees de fenetre, donc elle designait un endroit de l'oeil
    et non un endroit du document.

    Ces gardes sont STRUCTURELLES, pas comportementales: la suite n'a aucun
    moteur de rendu (`RM-2026-0111`), donc rien ici ne prouve que la marque suit
    vraiment - cela se verifie a l'oeil, dans une fenetre visible. Ce qu'elles
    empechent, c'est le retour de l'ancrage qui rendait le suivi impossible par
    construction.
    """

    STATIQUE = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static"

    def _regle(self, feuille: str, selecteur: str) -> str:
        texte = (self.STATIQUE / feuille).read_text(encoding="utf-8")
        debut = texte.index(selecteur + " {")
        return texte[debut : texte.index("}", debut)]

    def test_les_marques_sont_ancrees_au_document_et_non_a_la_fenetre(self) -> None:
        for marque in (".recette-zone-box", ".recette-cible-box"):
            corps = self._regle("styles_part_29.css", marque)
            self.assertIn(
                "position: absolute",
                corps,
                msg=(
                    f"`{marque}` doit se placer par rapport au DOCUMENT. En `fixed` elle "
                    "reste collee a la fenetre et se decale des que la page defile: c'est "
                    "le defaut signale le 2026-09-07."
                ),
            )
            self.assertNotIn("position: fixed", corps)

    def test_le_message_du_mode_test_ne_passe_plus_par_la_barre_haute(self) -> None:
        """Deux raisons, mesurees toutes les deux, pas supposees.

        Un libelle un peu long insere dans `.instance-meta` faisait grandir la
        barre haute et descendre la page de 110 px - la marque se retrouvait
        alors a cote de sa cible. Et sous 1281 px ce conteneur est masque
        (`RM-2026-0111`), donc le message n'etait pas lisible du tout.
        """
        script = (self.STATIQUE / "recette_mode.js").read_text(encoding="utf-8")
        self.assertIn(
            "recette-panel__note",
            script,
            "Le panneau doit porter sa propre ligne de message.",
        )
        corps = script[script.index("function message(") :]
        corps = corps[: corps.index("\n  }")]
        self.assertNotIn(
            "status",
            corps,
            msg=(
                "`message()` ecrit de nouveau dans la zone de statut de la barre haute. "
                "Ce conteneur repousse le contenu de la page quand il grandit, et il "
                "disparait sous 1281 px."
            ),
        )

    def test_le_survol_et_le_clic_designent_le_meme_element(self) -> None:
        """Sans definition unique, on surligne un element et on en enregistre un autre."""
        script = (self.STATIQUE / "recette_mode.js").read_text(encoding="utf-8")
        self.assertEqual(
            script.count("var CIBLES ="),
            1,
            "La liste des elements pointables doit etre definie une seule fois.",
        )
        self.assertGreaterEqual(
            script.count("closest(CIBLES)"),
            2,
            "Le survol et le clic doivent tous deux passer par cette definition unique.",
        )


if __name__ == "__main__":
    unittest.main()
