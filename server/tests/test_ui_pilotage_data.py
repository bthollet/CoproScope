from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.web.pilotage_view import build_pilotage_view


class PilotageUiDataTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _instance(self):
        return load_instance(str(self.instance_root / "instance.yml"), None)

    def test_default_view_uses_existing_kpi_register_rows_via_pilotageops(self) -> None:
        kpi_path = self.instance_root / "registers" / "kpi.csv"
        kpi_path.write_text(
            "\n".join(
                [
                    "kpi_id,family,indicator,formula,source,status,value,notes",
                    "KPI-EAU,Energie,Derive eau froide,ecart mensuel,registre_releves,CALCULATED,18,preuve locale",
                    "KPI-SYNDIC,Syndic,Delai moyen de reponse syndic,date reponse - demande,registre_demandes,TO_FILL,,a completer",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        view = build_pilotage_view(instance=self._instance(), period_label="2026")

        self.assertEqual(view["summary"]["total"], 2)
        self.assertTrue(all(card["card_id"].startswith("PLC-") for card in view["cards"]))
        self.assertEqual(view["cards"][0]["domain_label"], "Consommations")
        self.assertEqual(view["cards"][0]["proof_source"], "Registre KPI local - registre_releves - kpi.csv:KPI-EAU")
        self.assertIn("Controler la source du KPI", view["cards"][0]["next_action"])
        self.assertEqual(view["cards"][1]["domain_label"], "Demandes")
        self.assertEqual(view["cards"][1]["status"], "a_verifier")
        self.assertIn("preuve manquante", view["cards"][1]["proof_source"])
        self.assertNotIn("Exemple local", " ".join(card["title"] for card in view["cards"]))

    def test_default_view_falls_back_to_three_clearly_marked_local_examples(self) -> None:
        (self.instance_root / "registers" / "kpi.csv").write_text(
            "kpi_id,family,indicator,formula,source,status,value,notes\n",
            encoding="utf-8",
        )

        view = build_pilotage_view(instance=self._instance(), period_label="2026")

        self.assertEqual(view["summary"]["total"], 3)
        self.assertEqual(
            {card["domain"] for card in view["cards"]},
            {"consommations", "entretien", "gouvernance"},
        )
        for card in view["cards"]:
            self.assertIn("Exemple local", card["title"])
            self.assertIn("Exemple local CoproScope", card["proof_source"])
            self.assertTrue(card["next_action"])
            self.assertTrue(card["proof_ref"].startswith("DEMO-LOCAL-"))

    def test_pilotage_route_is_fed_without_changing_route_signature(self) -> None:
        kpi_path = self.instance_root / "registers" / "kpi.csv"
        kpi_path.write_text(
            "\n".join(
                [
                    "kpi_id,family,indicator,formula,source,status,value,notes",
                    "KPI-GOUV,Gouvernance,Decisions AG suivies,decisions tracees,registre_ag,CALCULATED,4,local",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        try:
            from fastapi.testclient import TestClient  # type: ignore
            from coproscope.web.app import create_app
        except ImportError:
            self.skipTest("web test stack unavailable")

        response = TestClient(create_app(self._instance(), 2026)).get("/pilotage")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Decisions AG suivies", response.text)
        self.assertIn("Registre KPI local - registre_ag", response.text)
        self.assertNotIn("Aucun indicateur pret a afficher", response.text)


if __name__ == "__main__":
    unittest.main()
