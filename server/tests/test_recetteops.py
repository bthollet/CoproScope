from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import InstanceConfig
from coproscope.modules import recetteops


class RecetteOpsTests(unittest.TestCase):
    def test_route_and_query_remove_token_and_private_values(self) -> None:
        route, query = recetteops.route_and_query(
            "/actions?token=secret&status=open&path=C:\\Users\\brice\\private"
        )

        self.assertEqual(route, "/actions")
        self.assertEqual(query, "status=open")
        self.assertNotIn("token", query)
        self.assertNotIn("Users", query)

    def test_validated_annotation_cleans_private_markers(self) -> None:
        row = recetteops.validated_annotation(
            {
                "url": "file:///C:/Users/brice/raw/demo",
                "target_kind": "zone",
                "target_label": "C:\\Users\\brice\\secret",
                "comment": "Voir raw\\secret avant partage.",
                "severity": "bloquant",
                "box_width": "120.25",
            }
        )

        self.assertEqual(row["route"], "/")
        self.assertEqual(row["target_label"], "")
        self.assertEqual(row["comment"], "")
        self.assertEqual(row["severity"], "bloquant")
        self.assertEqual(row["box_width"], "120.2")

    def test_memory_rows_are_isolated_by_instance_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root_a = Path(directory) / "a"
            root_b = Path(directory) / "b"
            root_a.mkdir()
            root_b.mkdir()
            instance_a = InstanceConfig(root_a / "instance.yml", {"instance_id": "a"})
            instance_b = InstanceConfig(root_b / "instance.yml", {"instance_id": "b"})

            recetteops.save_annotation(instance_a, {"url": "/actions?token=secret", "comment": "Bouton confus"})

            self.assertIn("Bouton confus", recetteops.render_markdown_export(instance_a))
            self.assertNotIn("Bouton confus", recetteops.render_markdown_export(instance_b))

    def test_exports_are_derived_and_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "instance"
            registers = root / "registers"
            registers.mkdir(parents=True)
            instance = InstanceConfig(
                root / "instance.yml",
                {
                    "instance_id": "demo",
                    "registers": {"documents": "registers/documents.csv"},
                },
            )
            recetteops.save_annotation(
                instance,
                {
                    "url": "/documents?token=secret&view=list",
                    "target_label": "Nouvelle demande",
                    "comment": "Le libelle n'est pas clair.",
                },
            )

            json_payload = recetteops.render_json_export(instance)
            markdown = recetteops.render_markdown_export(instance)

        self.assertIn("DERIVED_RECETTE_QA", json_payload)
        self.assertIn("Nouvelle demande", markdown)
        for payload in (json_payload, markdown):
            self.assertNotIn("token", payload)
            self.assertNotIn("secret", payload)
            self.assertNotIn("C:\\", payload)
            self.assertNotIn("file://", payload)


if __name__ == "__main__":
    unittest.main()
