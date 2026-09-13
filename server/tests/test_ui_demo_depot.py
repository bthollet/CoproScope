"""Depot de pieces, pipelines declenches depuis l'UI et export zip diffusable.

Extrait de `test_ui_demo.py` (603 lignes) pour tenir le plafond de 600 lignes du
depot. La fixture d'instance demo reste partagee via `DemoInstanceTestCase`.
"""

from __future__ import annotations

import json
import unittest
import zipfile
from io import BytesIO

from coproscope.core.common import read_csv
from coproscope.web.app import create_app
from coproscope.web.depot import (
    DepositError,
    create_deposit_from_uploads,
    deposit_manifest_path,
    read_deposit_manifest,
    write_deposit_manifest,
)

from tests.test_ui_demo import DemoInstanceTestCase


class UiDemoDepotTests(DemoInstanceTestCase):
    """Ce qu'un depot ecrit, ce qu'il refuse, et ce que l'export laisse sortir."""

    def test_depot_upload_pipeline_buttons_and_safe_export_zip(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        _, demo = self._build_demo()
        client = TestClient(create_app(demo, 2025, rebrancher=frozenset({"ajouter_document"})))

        upload = client.post(
            "/depot",
            files=[
                (
                    "files",
                    (
                        "2026-05-20_note_syndic.txt",
                        b"Note syndic fictive\nConvocation AG et devis travaux a verifier.\n",
                        "text/plain",
                    ),
                )
            ],
            follow_redirects=False,
        )
        self.assertEqual(upload.status_code, 303)

        manifests = sorted((self.demo_root / "outputs" / "deposits").glob("DEPOT-*.json"))
        self.assertEqual(len(manifests), 1)
        manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
        deposit_id = manifest["deposit_id"]
        self.assertTrue((self.demo_root / manifest["files"][0]["path"]).exists())
        self.assertTrue(manifest["doc_ids"])
        step_names = [step["name"] for step in manifest["steps"]]
        self.assertIn("inventory", step_names)
        self.assertTrue(any(name.startswith("extract_text:") for name in step_names))
        self.assertIn("classify", step_names)
        self.assertIn("privacy_screening", step_names)
        self.assertIn("redaction_queue", step_names)

        _, document_rows = read_csv(demo.register("documents"))
        uploaded = [row for row in document_rows if row.get("file_name") == "2026-05-20_note_syndic.txt"]
        self.assertEqual(len(uploaded), 1)
        self.assertEqual(uploaded[0]["status_ocr"], "TEXT_EXTRACTED")
        self.assertNotEqual(uploaded[0]["classification_status"], "PENDING")

        # Les boutons de pipeline par depot ont disparu avec l'ecran /depot (RM-2026-0183).
        response = client.post(f"/depot/{deposit_id}/pipeline/docai", follow_redirects=False)
        self.assertIn(response.status_code, (404, 405))

        forbidden = client.get(f"/raw/_depot_ui/{deposit_id}/2026-05-20_note_syndic.txt")
        self.assertEqual(forbidden.status_code, 404)

        export = client.get("/exports/local.zip")
        self.assertEqual(export.status_code, 200)
        with zipfile.ZipFile(BytesIO(export.content)) as archive:
            names = archive.namelist()
            deposit_manifest = archive.read(f"outputs/deposits/{deposit_id}.json").decode("utf-8")
        self.assertIn("exports/coproscope_actions_2025.csv", names)
        self.assertIn(f"outputs/deposits/{deposit_id}.json", names)
        self.assertIn("[reference locale masquee]", deposit_manifest)
        self.assertNotIn("raw/_depot_ui", deposit_manifest)
        self.assertFalse(any(name.startswith("raw/") for name in names))
        self.assertFalse(any(name.startswith("restricted/") for name in names))
        self.assertFalse(any(name.startswith("logs/") for name in names))
        self.assertFalse(any("/private/" in name or name.startswith("outputs/evidence/private/") for name in names))
        self.assertFalse(any(".env" in name or "table_correspondance" in name or "mapping" in name for name in names))

    def test_deposit_manifest_rejects_path_traversal_and_ignores_payload_id(self) -> None:
        _, demo = self._build_demo()
        raw_evil = self.demo_root / "raw" / "evil.json"
        raw_evil.write_text(
            json.dumps({"deposit_id": "../../raw/rewritten", "status": "attacker-controlled"}),
            encoding="utf-8",
        )

        self.assertIsNone(read_deposit_manifest(demo, "../../raw/evil"))
        self.assertIsNone(read_deposit_manifest(demo, "DEPOT-not-a-date"))

        legit_id = "DEPOT-20260520T120000Z"
        legit_path = deposit_manifest_path(demo, legit_id)
        legit_path.write_text(
            json.dumps({"deposit_id": "../../raw/rewritten", "status": "ok"}),
            encoding="utf-8",
        )
        manifest = read_deposit_manifest(demo, legit_id)
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["deposit_id"], legit_id)

        write_deposit_manifest(demo, manifest)
        self.assertTrue(legit_path.exists())
        self.assertFalse((self.demo_root / "raw" / "rewritten.json").exists())
        with self.assertRaises(DepositError):
            write_deposit_manifest(demo, {"deposit_id": "../../raw/rewritten"})

    def test_deposit_upload_rejects_empty_and_unsupported_files(self) -> None:
        _, demo = self._build_demo()

        class FakeUpload:
            def __init__(self, filename: str, payload: bytes) -> None:
                self.filename = filename
                self.file = BytesIO(payload)

        with self.assertRaises(DepositError):
            create_deposit_from_uploads(demo, [FakeUpload("payload.exe", b"not allowed")])
        with self.assertRaises(DepositError):
            create_deposit_from_uploads(demo, [FakeUpload("empty.txt", b"")])

        self.assertFalse((self.demo_root / "raw" / "_depot_ui").exists())


if __name__ == "__main__":
    unittest.main()
