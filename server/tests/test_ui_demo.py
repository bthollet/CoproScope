"""Construction de l'instance demo fictive et gardes de publication.

Ce module porte aussi le socle partage `DemoInstanceTestCase`: la copie de
`examples/synthetic_copro` vers un dossier temporaire, puis la construction de
la demo publiable. Les groupes thematiques voisins l'importent au lieu de
recopier la fixture:

- `test_ui_demo_dashboard_model.py`: lecture du read model de tableau de bord;
- `test_ui_demo_depot.py`: depot de pieces, pipelines et export zip;
- `test_ui_demo_routes_securite.py`: routes servies, jeton d'acces et garde LAN.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance
from coproscope.modules.demoops import build_demo_instance


class DemoInstanceTestCase(unittest.TestCase):
    """Socle partage: une instance source copiee, une demo construite a la demande."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.source_root = Path(self.tempdir.name) / "source"
        self.demo_root = Path(self.tempdir.name) / "demo_public"
        shutil.copytree(source_example, self.source_root)
        self.source = load_instance(str(self.source_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _build_demo(self):
        run = RunContext(self.source, "demo build test")
        result = build_demo_instance(
            self.source,
            run,
            output_instance=self.demo_root,
            mode="fictive",
            year=2025,
            run_source_audit=True,
            max_text_chars=8000,
        )
        run.finish("OK", "demo build test complete")
        return result, load_instance(str(self.demo_root / "instance.yml"), None)


class UiAndDemoTests(DemoInstanceTestCase):
    """Demo publiable: nom fictif, et gardes qui bloquent une fuite de la source."""

    def test_demo_build_creates_fictive_publishable_instance(self) -> None:
        result, demo = self._build_demo()

        self.assertEqual(result["status"], "ok")
        self.assertTrue((self.demo_root / "instance.yml").exists())
        self.assertTrue((self.demo_root / "demo_manifest.json").exists())
        self.assertTrue((self.demo_root / "outputs" / "accounting" / "2025" / "summary_2025.json").exists())
        self.assertFalse((self.demo_root / "restricted" / "C8_local_only" / "table_correspondance_biffage.csv").exists())
        self.assertEqual(demo.display_name, "Residence Les Tilleuls")

        public_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in self.demo_root.rglob("*")
            if path.is_file()
            and "restricted" not in path.parts
            and path.suffix.lower() in {".txt", ".md", ".csv", ".json", ".yml"}
        )
        self.assertNotIn("Residence Les Platanes", public_text)
        self.assertNotIn("synthetic-copro", public_text)
        self.assertIn("Residence Les Tilleuls", public_text)
        self.assertIn("APPROVED_FICTIVE_DEMO", public_text)

    def _rename_source(self, display_name: str) -> None:
        config_path = self.source_root / "instance.yml"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        payload["display_name"] = display_name
        config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.source = load_instance(str(config_path), None)

    def _plant_in_demo_outputs(self, file_name: str, content: str) -> None:
        planted = self.demo_root / "outputs" / "demo" / file_name
        planted.parent.mkdir(parents=True, exist_ok=True)
        planted.write_text(content, encoding="utf-8")

    def test_demo_build_blocks_when_source_name_reaches_an_output(self) -> None:
        self._rename_source("Residence Bellevoie")
        self._plant_in_demo_outputs("note_heritee.txt", "Note heritee de la source: Bellevoie.\n")

        result, _ = self._build_demo()

        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["publication_validation"]["decision"], "BLOCKED_REVIEW_REQUIRED")
        self.assertEqual(result["publication_validation"]["blocked_reason"], "NOM_LOCAL")

    def _declarer_noms_locaux(self, *jetons: str) -> None:
        config_path = self.source_root / "instance.yml"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        payload.setdefault("settings", {}).setdefault("demoops", {})["noms_locaux"] = list(jetons)
        config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.source = load_instance(str(config_path), None)

    def test_la_garde_regarde_les_manifestes_ecrits_apres_elle(self) -> None:
        """Un test de PORTEE, pas de comportement.

        La garde validait l'arborescence, puis trois fichiers y etaient ecrits:
        le rapport et les deux manifestes de publication. Elle declarait donc
        propre un arbre qu'elle n'avait pas fini de regarder.

        `individualisation` est un mot que SEULS les deux manifestes portent -
        mesure faite sur une demo generee: aucun autre fichier de l'instance ne
        le contient. Le declarer interdit revient donc a poser une sonde dans
        la zone que la garde ne voyait pas.

        Si quelqu'un ramene un jour la validation avant l'ecriture des
        manifestes, le mot redevient invisible, la demo repasse au vert, et
        **ce test tombe**. C'est sa seule raison d'exister: une garde dont la
        portee se retracte ne casse rien, elle rassure.
        """
        self._declarer_noms_locaux("individualisation")

        result, _ = self._build_demo()

        self.assertEqual(result["publication_validation"]["decision"], "BLOCKED_REVIEW_REQUIRED")
        self.assertEqual(result["publication_validation"]["blocked_reason"], "NOM_LOCAL")

    def test_demo_build_blocks_on_phone_number_left_in_an_output(self) -> None:
        self._plant_in_demo_outputs("note_contact.txt", "Contact chantier: 06 12 34 56 78\n")

        result, _ = self._build_demo()

        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["publication_validation"]["decision"], "BLOCKED_REVIEW_REQUIRED")
        self.assertEqual(result["publication_validation"]["blocked_reason"], "PHONE")


if __name__ == "__main__":
    unittest.main()
