from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance
from coproscope.modules.demoops import build_demo_instance
from coproscope.web.app import create_app
from coproscope.web.viewmodel import build_dashboard_model


class UiAndDemoTests(unittest.TestCase):
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

    def test_dashboard_model_reads_demo_outputs_and_chantiers(self) -> None:
        _, demo = self._build_demo()
        model = build_dashboard_model(demo, 2025)

        self.assertEqual(model["instance"]["name"], "Residence Les Tilleuls")
        self.assertGreaterEqual(model["kpis"]["documents"], 6)
        self.assertGreaterEqual(model["kpis"]["invoices"], 6)
        self.assertTrue(any(module["label"] == "ComptaScope" for module in model["modules"]))
        self.assertTrue(any(stream["label"] == "WorksOps" for stream in model["workstreams"]))
        self.assertNotIn("demo", model)
        self.assertFalse(any(module["label"] == "Copro demo" for module in model["modules"]))
        self.assertGreaterEqual(model["action_summary"]["total"], model["action_summary"]["preview_count"])
        self.assertTrue(model["action_items"])
        self.assertIn("by_domain", model["action_summary"])
        self.assertIn("by_status", model["action_summary"])
        self.assertTrue(model["accounting"]["syndic_questions"])

    def test_local_web_routes_render_without_serving_private_roots(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        _, demo = self._build_demo()
        client = TestClient(create_app(demo, 2025))

        for path in [
            "/",
            "/actions",
            "/actions?scope=comptes",
            "/exports/actions.csv",
            "/exports/actions.md",
            "/comptes",
            "/documents",
            "/confidentialite",
            "/chantiers",
            "/api/model",
            "/health",
        ]:
            response = client.get(path)
            self.assertEqual(response.status_code, 200, path)

        csv_export = client.get("/exports/actions.csv")
        self.assertIn("priority,status,domain,source", csv_export.text)
        markdown_export = client.get("/exports/actions.md?scope=comptes")
        self.assertIn("# Actions CoproScope", markdown_export.text)

        for forbidden in ["/demo", "/raw/2025-01-18_facture_entretien_jardin.txt", "/restricted/secret.txt", "/.env.local"]:
            response = client.get(forbidden)
            self.assertEqual(response.status_code, 404, forbidden)


if __name__ == "__main__":
    unittest.main()
