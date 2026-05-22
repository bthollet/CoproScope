from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance, now_iso
from coproscope.web.app import create_app
from coproscope.web.depot import write_deposit_manifest
from coproscope.web.viewmodel import build_dashboard_model


class DepotFlowUiTests(unittest.TestCase):
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

    def _piece_id(self) -> str:
        pieces = build_dashboard_model(self.instance, 2025)["ux"]["pieces"]
        self.assertTrue(pieces["missing"])
        return str(pieces["missing"][0]["id"])

    def test_depot_page_explains_local_first_flow_and_outputs(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        deposit_id = "DEPOT-20260520T120000Z"
        write_deposit_manifest(
            self.instance,
            {
                "deposit_id": deposit_id,
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "target_dir": "raw/_depot_ui/DEPOT-20260520T120000Z",
                "files": [
                    {
                        "original_name": "note_syndic.txt",
                        "stored_name": "note_syndic.txt",
                        "path": "raw/_depot_ui/DEPOT-20260520T120000Z/note_syndic.txt",
                        "size_bytes": 42,
                        "sha256": "abc123",
                    }
                ],
                "doc_ids": ["DOC-DEPOT-001"],
                "steps": [
                    {
                        "name": "inventory",
                        "status": "ok",
                        "started_at": now_iso(),
                        "finished_at": now_iso(),
                        "before": {"documents": 0, "privacy_reviews": 0, "redaction_queue": 0, "doc_ids": []},
                        "after": {
                            "documents": 7,
                            "privacy_reviews": 3,
                            "redaction_queue": 2,
                            "doc_ids": ["DOC-DEPOT-001"],
                        },
                        "result": {},
                        "error": r"C:\Users\demo\raw\secret.txt introuvable",
                    }
                ],
                "status": "processed",
            },
        )

        client = TestClient(create_app(self.instance, 2025))
        response = client.get(f"/depot?depot={deposit_id}")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Depot guide & exports locaux", text)
        self.assertIn("Cette page ne synchronise rien vers un service cloud.", text)
        self.assertIn("Ce qui est prepare pour le coffre chiffre", text)
        self.assertIn("piece -> action -> preuve", text)
        self.assertIn("Sorties du depot", text)
        self.assertIn("1 documents rattaches aux registres locaux; 1 etapes tracees", text)
        self.assertIn("Resume des sorties", text)
        self.assertIn("7 documents indexes - 3 lignes confidentialite - 2 elements en file biffage", text)
        self.assertIn("Actions et preuves a suivre", text)
        self.assertIn("Il exclut les zones locales non servies, les secrets et les correspondances sensibles.", text)
        self.assertIn("Fichier 1", text)
        self.assertIn("Traitement local a reprendre; le detail technique reste dans les journaux locaux.", text)
        self.assertNotIn("raw/_depot_ui", text)
        self.assertNotIn("note_syndic.txt", text)
        self.assertNotIn(r"C:\Users", text)
        self.assertNotIn("secret.txt", text)

    def test_depot_prefills_received_answer_from_piece_detail_query(self) -> None:
        piece_id = self._piece_id()

        response = self._client(access_token="local-secret").get(
            f"/depot?intent=proof&status=reponse-recue&return=pieces&piece_detail={piece_id}&token=local-secret"
        )
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Reponse recue pour cette piece", text)
        self.assertIn("Piece candidate a verifier", text)
        self.assertIn("La reponse recue restera une piece candidate", text)
        self.assertIn("Preuve attendue", text)
        self.assertIn("Retour detail piece/preuve", text)
        self.assertIn("Reponse recue a rattacher", text)
        self.assertIn("Deposer comme reponse candidate", text)
        self.assertIn('id="depot-files"', response.text)
        self.assertIn('required aria-describedby="depot-upload-help"', response.text)
        self.assertIn(f'name="piece_detail" value="{piece_id}"', response.text)
        self.assertIn('name="status" value="reponse-recue"', response.text)
        self.assertIn('action="/depot?token=local-secret"', response.text)
        self.assertNotIn("C:\\Users", text)
        self.assertNotIn("file://", text)
        self.assertNotIn("raw/", text)
        self.assertNotIn("restricted/", text)

    def test_depot_piece_detail_prefill_reuses_dashboard_model_for_context(self) -> None:
        piece_id = self._piece_id()
        client = self._client(access_token="local-secret")

        from coproscope.web import app as web_app

        calls: list[str] = []
        real_build = web_app.build_dashboard_model

        def counted_build(instance, year=2025):  # type: ignore[no-untyped-def]
            calls.append(instance.instance_id)
            return real_build(instance, year)

        with patch("coproscope.web.app.build_dashboard_model", side_effect=counted_build), patch(
            "coproscope.web.piece_detail_view.build_dashboard_model",
            side_effect=AssertionError("depot piece context should reuse the route dashboard model"),
        ):
            response = client.get(
                f"/depot?intent=proof&status=reponse-recue&return=pieces&piece_detail={piece_id}&token=local-secret"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(calls), 1)

    def test_depot_upload_persists_received_answer_context_without_private_leaks(self) -> None:
        piece_id = self._piece_id()

        response = self._client(access_token="local-secret").post(
            "/depot?token=local-secret",
            data={
                "intent": "proof",
                "status": "reponse-recue",
                "return": "pieces",
                "piece_detail": piece_id,
                "missing_for": r"C:\Users\ExampleUser\raw\secret.txt",
                "source": "comptes",
            },
            files=[
                (
                    "files",
                    (
                        "reponse_syndic_fictive.txt",
                        b"Reponse syndic fictive pour justificatif ascenseur.\n",
                        "text/plain",
                    ),
                )
            ],
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        location = response.headers["location"]
        self.assertIn("/depot?", location)
        self.assertIn("depot=", location)
        self.assertIn("token=local-secret", location)
        manifests = sorted((self.instance_root / "outputs" / "deposits").glob("DEPOT-*.json"))
        matches = [
            path
            for path in manifests
            if piece_id in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(len(matches), 1)
        manifest_text = matches[0].read_text(encoding="utf-8")
        manifest = json.loads(manifest_text)

        self.assertEqual(manifest["context"]["intent"], "proof")
        self.assertEqual(manifest["context"]["status"], "reponse-recue")
        self.assertEqual(manifest["context"]["return"], "pieces")
        self.assertEqual(manifest["context"]["piece_detail"], piece_id)
        self.assertEqual(manifest["context"]["source"], "comptes")
        self.assertNotIn("missing_for", manifest["context"])
        context_text = json.dumps(manifest["context"], ensure_ascii=False)
        self.assertNotIn("C:\\Users", manifest_text)
        self.assertNotIn("secret.txt", manifest_text)
        self.assertNotIn("raw\\", context_text)
        self.assertNotIn("raw/", context_text)


if __name__ == "__main__":
    unittest.main()
