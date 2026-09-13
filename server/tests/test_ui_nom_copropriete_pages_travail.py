"""Les deux pages de travail disent de quelle copropriete elles parlent.

Defaut mesure le 2026-09-04 sur instance reelle: sur `/comptes` comme sur
`/ag-contentieux`, le nom de la copropriete n'apparaissait qu'une seule fois
dans tout le HTML, dans la balise `title`. Le corps de page ne portait que
l'identifiant technique du coffre. Une capture d'ecran, une impression ou un
export ne nommaient donc la copropriete nulle part - alors que le tableau de
bord, lui, affiche depuis longtemps un panneau `Contexte actif`.
"""

from __future__ import annotations

import re
import unittest
from html import unescape
from pathlib import Path

from coproscope.core.common import load_instance


ROOT = Path(__file__).resolve().parents[2]
INSTANCE_ROOT = ROOT / "examples" / "synthetic_copro"

PAGES_DE_TRAVAIL = ("/comptes", "/ag-contentieux")


class NomCoproprietePagesTravailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.instance = load_instance(None, str(INSTANCE_ROOT))

    def _client(self):
        try:
            from fastapi.testclient import TestClient  # type: ignore
            from coproscope.web.app import create_app
        except ImportError as exc:  # pragma: no cover - dependance UI optionnelle
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        return TestClient(create_app(self.instance, year=2025, access_token=None))

    @staticmethod
    def _corps(html: str) -> str:
        """Le HTML prive de sa balise `title`: ce qu'une capture montre."""
        return re.sub(r"<title>.*?</title>", "", html, flags=re.S)

    def test_le_nom_de_la_copropriete_est_dans_le_corps_des_deux_pages(self) -> None:
        client = self._client()

        for chemin in PAGES_DE_TRAVAIL:
            with self.subTest(chemin=chemin):
                reponse = client.get(chemin)
                self.assertEqual(reponse.status_code, 200)
                corps = self._corps(unescape(reponse.text))
                self.assertIn(self.instance.display_name, corps)

    def test_le_nom_ne_repose_plus_sur_le_seul_titre_du_navigateur(self) -> None:
        """Sans cette garde, la regression est invisible: la page reste belle."""
        client = self._client()

        for chemin in PAGES_DE_TRAVAIL:
            with self.subTest(chemin=chemin):
                texte = unescape(client.get(chemin).text)
                occurrences = texte.count(self.instance.display_name)
                self.assertGreater(
                    occurrences,
                    1,
                    f"{chemin}: le nom de la copropriete n'apparait que dans <title>",
                )

    def test_les_deux_pages_portent_le_panneau_de_contexte_actif(self) -> None:
        client = self._client()

        for chemin in PAGES_DE_TRAVAIL:
            with self.subTest(chemin=chemin):
                texte = client.get(chemin).text
                self.assertIn('aria-label="Contexte actif"', texte)


if __name__ == "__main__":
    unittest.main()
