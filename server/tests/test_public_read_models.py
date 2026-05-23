import json
import re
import shutil
import sqlite3
import unittest
import uuid
from html import unescape
from pathlib import Path
from unittest import mock

from coproscope.core.common import load_instance
from coproscope.vault import public_read_models, reconstruction


class PublicReadModelTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        temp_parent = repo_root / "server" / ".tmp-test"
        temp_parent.mkdir(parents=True, exist_ok=True)
        self.test_root = temp_parent / f"public_read_models_{uuid.uuid4().hex}"
        self.test_root.mkdir()
        self.instance_root = self.test_root / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)
        self.local_root = self.instance_root / "local"
        self.sync_root = self.instance_root / "sync"
        self.local_root.mkdir()
        self.sync_root.mkdir()
        settings = self.instance.payload.setdefault("settings", {})
        settings["vault"] = {"local_root": "local", "sync_root": "sync"}
        self.db_path = reconstruction.resolve_reconstruction_db_path(self.local_root)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_root, ignore_errors=True)

    def _event(
        self,
        event_id: str,
        event_type: str,
        object_id: str,
        payload: dict[str, object],
        *,
        sequence: int,
    ) -> reconstruction.ReconstructionEvent:
        envelope = {
            "event_id": event_id,
            "event_type": event_type,
            "object_id": object_id,
            "author_key_id": "ak_public_test",
            "device_id": "dev_public_test",
            "sequence": sequence,
            "created_at": f"2026-05-20T10:{sequence:02d}:00+00:00",
        }
        return reconstruction.ReconstructionEvent.from_envelope(
            envelope,
            payload,
            event_hash=f"hash_{event_id}",
            event_path=f"events/dev_public_test/{sequence:012d}.json",
        )

    def _build_public_db(self) -> None:
        events = [
            self._event(
                "evt_public_action",
                "action_created",
                "ACT-PUBLIC-ASSURANCE",
                {
                    "action_id": "ACT-PUBLIC-ASSURANCE",
                    "title": "Demander l'attestation assurance 2026",
                    "status": "open",
                    "priority": "P1",
                    "domain": "Assurance",
                    "source_module": "Audit360",
                    "owner_ref": "Syndic",
                    "next_step": "Demander l'attestation au syndic.",
                    "diffusion_status": "cs_only",
                    "expected_piece_id": "PCE-PUBLIC-ASSURANCE",
                    "expected_piece_label": "Attestation assurance 2026",
                    "holder_label": r"C:\Users\brice\raw\secret.pdf",
                    "linked_request_id": "REQ-PUBLIC-ASSURANCE",
                    "received_doc_ids": ["DOC-PRIVATE-CANDIDATE"],
                    "payload_json": {"secret": "do-not-output"},
                    "locator_json": {"page": 1},
                    "message_draft": "Texte prive a ne jamais exposer",
                },
                sequence=1,
            ),
            self._event(
                "evt_public_request",
                "request_created",
                "REQ-PUBLIC-ASSURANCE",
                {
                    "request_id": "REQ-PUBLIC-ASSURANCE",
                    "subject": "Attestation assurance 2026",
                    "recipient_label": "Syndic",
                    "status": "local_draft",
                    "message_draft": "Bonjour avec token=local-secret et file://trace",
                    "linked_action_id": "ACT-PUBLIC-ASSURANCE",
                    "linked_piece_id": "PCE-PUBLIC-ASSURANCE",
                },
                sequence=2,
            ),
            self._event(
                "evt_public_action_p2",
                "action_created",
                "ACT-PUBLIC-ROUTINE",
                {
                    "action_id": "ACT-PUBLIC-ROUTINE",
                    "title": "Verifier le suivi courant",
                    "status": "open",
                    "priority": "P2",
                    "domain": "Documents",
                    "source_module": "DocOps",
                    "owner_ref": "Conseil syndical",
                    "next_step": "Verifier le classement public.",
                    "diffusion_status": "metadata_only",
                },
                sequence=3,
            ),
            self._event(
                "evt_public_request_duplicate",
                "request_created",
                "REQ-PUBLIC-ASSURANCE-SECOND",
                {
                    "request_id": "REQ-PUBLIC-ASSURANCE-SECOND",
                    "subject": "Relance doublon",
                    "recipient_label": "Syndic",
                    "status": "local_draft",
                    "message_draft": "Deuxieme brouillon prive",
                    "linked_action_id": "ACT-PUBLIC-ASSURANCE",
                    "linked_piece_id": "PCE-PUBLIC-ASSURANCE",
                },
                sequence=4,
            ),
        ]
        reconstruction.rebuild_cache_from_events(events, self.db_path, vault_id="vault_public_test")

    def test_public_missing_pieces_reader_exposes_exact_allowlist_without_private_markers(self) -> None:
        self._build_public_db()

        rows = public_read_models.read_public_missing_pieces_v1(self.db_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(tuple(rows[0].keys()), public_read_models.PUBLIC_MISSING_PIECES_COLUMNS)
        self.assertEqual(rows[0]["item_id"], "PCE-PUBLIC-ASSURANCE")
        self.assertEqual(rows[0]["expected_piece"], "Attestation assurance 2026")
        self.assertEqual(rows[0]["owner_label"], "Syndic")
        self.assertEqual(rows[0]["related_request_id"], "REQ-PUBLIC-ASSURANCE")
        self.assertEqual(rows[0]["candidate_count"], 1)
        self.assertEqual(rows[0]["diffusion_label"], "Conseil syndical uniquement")
        self.assertEqual(rows[0]["request_href"], "/demandes/relance?piece_detail=PCE-PUBLIC-ASSURANCE&request_id=REQ-PUBLIC-ASSURANCE")
        payload = json.dumps(rows, ensure_ascii=False).lower()
        for marker in [
            "payload_json",
            "event_path",
            "source_file",
            "source_path",
            "original_name",
            "original_path",
            "current_blob_id",
            "source_sha256",
            "locator_json",
            "message_draft",
            "chemin",
            "cs_only",
            "c:\\",
            "file://",
            "raw",
            "restricted",
            "logs",
            "private",
            "token=",
            "local-secret",
            str(self.instance_root).lower(),
        ]:
            self.assertNotIn(marker, payload)

        connection = sqlite3.connect(self.db_path)
        try:
            persistent_view = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'view' AND name = ?",
                (public_read_models.PUBLIC_MISSING_PIECES_VIEW,),
            ).fetchone()
        finally:
            connection.close()
        self.assertIsNone(persistent_view)

    def test_public_actions_reader_exposes_versioned_allowlist_filtered_by_priority(self) -> None:
        self._build_public_db()

        rows = public_read_models.read_public_actions_v1(self.db_path, priority="P1")

        self.assertEqual(len(rows), 1)
        self.assertEqual(tuple(rows[0].keys()), public_read_models.PUBLIC_ACTIONS_COLUMNS)
        self.assertEqual(rows[0]["id"], "ACT-PUBLIC-ASSURANCE")
        self.assertEqual(rows[0]["title"], "Demander l'attestation assurance 2026")
        self.assertEqual(rows[0]["priority"], "P1")
        self.assertEqual(rows[0]["priority_label"], "A traiter maintenant")
        self.assertEqual(rows[0]["status"], "a_traiter")
        self.assertEqual(rows[0]["owner"], "Syndic")
        self.assertEqual(rows[0]["channel"], "syndic")
        self.assertEqual(rows[0]["evidence"], "Attestation assurance 2026")
        self.assertEqual(rows[0]["diffusion_label"], "Conseil syndical uniquement")
        self.assertEqual(rows[0]["related_piece_id"], "PCE-PUBLIC-ASSURANCE")
        self.assertEqual(rows[0]["related_request_id"], "REQ-PUBLIC-ASSURANCE")
        self.assertEqual(rows[0]["href"], "/actions?selected=ACT-PUBLIC-ASSURANCE")
        self.assertEqual(
            rows[0]["request_href"],
            "/demandes/relance?action_id=ACT-PUBLIC-ASSURANCE&request_id=REQ-PUBLIC-ASSURANCE",
        )
        self.assertEqual(rows[0]["read_model_version"], public_read_models.PUBLIC_ACTIONS_SCHEMA_VERSION)
        payload = json.dumps(rows, ensure_ascii=False).lower()
        for marker in [
            "payload_json",
            "event_path",
            "source_file",
            "source_path",
            "original_name",
            "original_path",
            "current_blob_id",
            "source_sha256",
            "locator_json",
            "message_draft",
            "chemin",
            "cs_only",
            "c:\\",
            "file://",
            "raw",
            "restricted",
            "logs",
            "private",
            "token=",
            "local-secret",
            str(self.instance_root).lower(),
        ]:
            self.assertNotIn(marker, payload)

        connection = sqlite3.connect(self.db_path)
        try:
            persistent_view = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'view' AND name = ?",
                (public_read_models.PUBLIC_ACTIONS_VIEW,),
            ).fetchone()
        finally:
            connection.close()
        self.assertIsNone(persistent_view)

    def test_public_actions_reader_returns_empty_when_projection_version_is_absent(self) -> None:
        self._build_public_db()
        connection = sqlite3.connect(self.db_path)
        try:
            connection.execute("DELETE FROM projection_meta")
            connection.commit()
        finally:
            connection.close()

        rows = public_read_models.read_public_actions_v1(self.db_path, priority="P1")

        self.assertEqual(rows, [])

    def test_public_actions_reader_returns_empty_when_schema_is_incompatible(self) -> None:
        bad_db = self.test_root / "bad_actions.sqlite3"
        connection = sqlite3.connect(bad_db)
        try:
            connection.execute(
                "CREATE TABLE projection_meta(projector_id TEXT, projector_version TEXT, applied_count INTEGER)"
            )
            connection.execute("CREATE TABLE actions(action_id TEXT PRIMARY KEY)")
            connection.execute(
                "INSERT INTO projection_meta(projector_id, projector_version, applied_count) VALUES (?, ?, ?)",
                (
                    reconstruction.DEFAULT_PROJECTION_PROJECTOR_ID,
                    reconstruction.DEFAULT_PROJECTION_PROJECTOR_VERSION,
                    0,
                ),
            )
            connection.commit()
        finally:
            connection.close()

        rows = public_read_models.read_public_actions_v1(bad_db, priority="P1")

        self.assertEqual(rows, [])

    def test_public_missing_pieces_reader_sql_has_no_wildcard_or_full_text_lookup(self) -> None:
        sources = [
            Path(public_read_models.__file__).read_text(encoding="utf-8"),
            Path(public_read_models.read_public_actions_v1.__code__.co_filename).read_text(encoding="utf-8"),
        ]

        for source in sources:
            self.assertIsNone(re.search(r"SELECT\s+\*", source, re.IGNORECASE))
            self.assertIsNone(re.search(r"\bMATCH\b", source, re.IGNORECASE))
            self.assertIsNone(re.search(r"\bfts\d?\b", source, re.IGNORECASE))
            self.assertIsNone(re.search(r"CREATE\s+VIEW", source, re.IGNORECASE))

    def test_missing_pieces_route_uses_public_read_model_without_dashboard_build(self) -> None:
        self._build_public_db()
        try:
            from fastapi.testclient import TestClient  # type: ignore
            from coproscope.web.app import create_app
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        with mock.patch(
            "coproscope.web.app.build_dashboard_model",
            side_effect=AssertionError("dashboard model must not be built for public missing pieces"),
        ):
            client = TestClient(create_app(self.instance, 2025))
            response = client.get("/pieces?proof=missing")

        text = unescape(response.text)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Pieces manquantes", text)
        self.assertIn("Attestation assurance 2026", text)
        self.assertIn("Syndic", text)
        self.assertIn("Conseil syndical uniquement", text)
        self.assertIn("1 candidate a verifier", text)
        self.assertIn("Relancer syndic", text)
        self.assertIn("Ajouter reponse recue", text)
        self.assertIn('href="/pieces/PCE-PUBLIC-ASSURANCE"', text)
        self.assertNotIn("cs_only", text)

    def test_missing_pieces_route_uses_empty_public_model_when_projection_is_absent(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
            from coproscope.web.app import create_app
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        with mock.patch(
            "coproscope.web.app.build_dashboard_model",
            side_effect=AssertionError("missing public projection must not fall back to dashboard model"),
        ):
            client = TestClient(create_app(self.instance, 2025))
            response = client.get("/pieces?proof=missing")

        text = unescape(response.text)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Aucune piece manquante affichee pour le moment", text)
        self.assertIn("La projection locale ne remonte pas encore de piece a demander", text)

    def test_serve_does_not_prewarm_dashboard(self) -> None:
        try:
            from coproscope.web import app as web_app
        except ImportError:
            self.skipTest("UI stack unavailable")

        with mock.patch(
            "coproscope.web.app.build_dashboard_model",
            side_effect=AssertionError("serve must not prewarm dashboard model"),
        ), mock.patch("uvicorn.run") as run:
            web_app.serve(self.instance, 2025, access_token="local-secret")

        self.assertTrue(run.called)


if __name__ == "__main__":
    unittest.main()
