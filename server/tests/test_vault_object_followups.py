from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from coproscope.core.event_types import ACTION_CREATED, OBJECT_FOLLOWUP_RECORDED, POINT_CREATED, PROOF_RECORDED
from coproscope.vault import reconstruction
from coproscope.vault.public_object_followups_read_model import read_object_followups_v1


class VaultObjectFollowupsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.db_path = self.root / "vault_reconstruction.sqlite3"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

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
            "author_key_id": "ak_followup_test",
            "device_id": "dev_followup_test",
            "sequence": sequence,
            "created_at": f"2026-05-27T10:{sequence:02d}:00+00:00",
        }
        return reconstruction.ReconstructionEvent.from_envelope(
            envelope,
            payload,
            event_hash=f"hash_{event_id}",
            event_path=f"events/dev_followup_test/{sequence:012d}.json",
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def test_partial_proof_on_one_expected_piece_keeps_parent_point_open(self) -> None:
        events = [
            self._event(
                "evt_point",
                POINT_CREATED,
                "PNT-1",
                {"point_id": "PNT-1", "title": "Point assurance", "status": "open"},
                sequence=1,
            ),
            self._event(
                "evt_action_1",
                ACTION_CREATED,
                "ACT-1",
                {
                    "action_id": "ACT-1",
                    "title": "Demander attestation A",
                    "status": "open",
                    "related_point_ids": ["PNT-1"],
                    "expected_piece_id": "PCE-1",
                    "expected_piece_label": "Attestation A",
                },
                sequence=2,
            ),
            self._event(
                "evt_action_2",
                ACTION_CREATED,
                "ACT-2",
                {
                    "action_id": "ACT-2",
                    "title": "Demander contrat B",
                    "status": "open",
                    "related_point_ids": ["PNT-1"],
                    "expected_piece_id": "PCE-2",
                    "expected_piece_label": "Contrat B",
                },
                sequence=3,
            ),
            self._event(
                "evt_proof_1",
                PROOF_RECORDED,
                "PRF-1",
                {
                    "proof_id": "PRF-1",
                    "target_kind": "expected_piece",
                    "target_id": "PCE-1",
                    "summary": "Attestation A recue",
                    "effect": "partially_resolves",
                    "target_status_after": "partially_resolved",
                    "remaining_reason": "Contrat B encore attendu",
                    "visibility": "cs_only",
                },
                sequence=4,
            ),
        ]

        result = reconstruction.rebuild_cache_from_events(events, self.db_path, vault_id="vault_followups")

        self.assertEqual(result["object_followups"], 6)
        connection = self._connect()
        try:
            point = connection.execute("SELECT status FROM points WHERE point_id = 'PNT-1'").fetchone()
            self.assertEqual(point["status"], "open")
            pieces = {
                row["piece_id"]: row["status"]
                for row in connection.execute("SELECT piece_id, status FROM expected_pieces ORDER BY piece_id")
            }
            self.assertEqual(pieces, {"PCE-1": "partially_resolved", "PCE-2": "open"})
            followups = connection.execute(
                """
                SELECT followup_kind, followup_id, effect, status_after, remaining_reason
                FROM object_followups
                WHERE parent_kind = 'point' AND parent_id = 'PNT-1'
                ORDER BY occurred_at, event_id, row_id
                """
            ).fetchall()
            self.assertEqual([row["followup_id"] for row in followups if row["followup_kind"] == "action"], ["ACT-1", "ACT-2"])
            self.assertIn(("proof", "PRF-1", "partially_resolves"), [(row["followup_kind"], row["followup_id"], row["effect"]) for row in followups])
        finally:
            connection.close()

        public_rows = read_object_followups_v1(self.db_path, parent_kind="point", parent_id="PNT-1")
        self.assertEqual(public_rows[-1]["effect"], "partially_resolves")
        self.assertEqual(public_rows[-1]["status_after"], "partially_resolved")
        self.assertEqual(public_rows[-1]["remaining_reason"], "Contrat B encore attendu")
        payload = json.dumps(public_rows, ensure_ascii=False).lower()
        self.assertIn("leve partiellement", payload)
        self.assertNotIn("cs_only", payload)
        self.assertNotIn("payload_json", payload)

    def test_incident_can_accumulate_actions_and_partial_proof_without_duplicate_parent(self) -> None:
        events = [
            self._event(
                "evt_inc_action_1",
                ACTION_CREATED,
                "ACT-INC-1",
                {
                    "action_id": "ACT-INC-1",
                    "title": "Programmer intervention",
                    "parent_kind": "incident",
                    "parent_id": "INC-1",
                },
                sequence=1,
            ),
            self._event(
                "evt_inc_action_2",
                ACTION_CREATED,
                "ACT-INC-2",
                {
                    "action_id": "ACT-INC-2",
                    "title": "Demander assurance",
                    "parent_kind": "incident",
                    "parent_id": "INC-1",
                },
                sequence=2,
            ),
            self._event(
                "evt_inc_photo",
                PROOF_RECORDED,
                "PRF-PHOTO",
                {
                    "proof_id": "PRF-PHOTO",
                    "parent_kind": "incident",
                    "parent_id": "INC-1",
                    "target_kind": "milestone",
                    "target_id": "MS-PHOTO",
                    "summary": "Photo apres intervention",
                    "effect": "partially_resolves",
                    "remaining_reason": "Preuve finale de cloture encore manquante",
                },
                sequence=3,
            ),
        ]

        reconstruction.rebuild_cache_from_events(events, self.db_path, vault_id="vault_incident")

        public_rows = read_object_followups_v1(self.db_path, parent_kind="incident", parent_id="INC-1")
        self.assertEqual([row["followup_id"] for row in public_rows if row["followup_kind"] == "action"], ["ACT-INC-1", "ACT-INC-2"])
        self.assertEqual(public_rows[-1]["effect"], "partially_resolves")
        self.assertIn("Preuve finale", public_rows[-1]["remaining_reason"])

    def test_reconciliation_followups_keep_line_open_when_bank_movement_is_missing(self) -> None:
        events = [
            self._event(
                "evt_invoice_proof",
                PROOF_RECORDED,
                "PRF-FAC",
                {
                    "proof_id": "PRF-FAC",
                    "parent_kind": "reconciliation_line",
                    "parent_id": "LINE-1",
                    "target_kind": "reconciliation_cell",
                    "target_id": "CELL-INVOICE",
                    "summary": "Facture rapprochee",
                    "effect": "partially_resolves",
                    "status_after": "orange",
                    "remaining_reason": "Mouvement bancaire manquant",
                },
                sequence=1,
            ),
            self._event(
                "evt_human_reserve",
                OBJECT_FOLLOWUP_RECORDED,
                "VAL-1",
                {
                    "parent_kind": "reconciliation_line",
                    "parent_id": "LINE-1",
                    "followup_kind": "human_validation",
                    "followup_id": "VAL-1",
                    "effect": "keeps_open",
                    "status_after": "orange",
                    "summary": "Validation avec reserve",
                    "remaining_reason": "Mouvement bancaire manquant",
                },
                sequence=2,
            ),
        ]

        reconstruction.rebuild_cache_from_events(events, self.db_path, vault_id="vault_reconciliation")

        rows = read_object_followups_v1(self.db_path, parent_kind="reconciliation_line", parent_id="LINE-1")
        self.assertEqual([row["effect"] for row in rows], ["partially_resolves", "keeps_open"])
        self.assertEqual(rows[-1]["status_after"], "orange")
        self.assertEqual(rows[-1]["remaining_reason"], "Mouvement bancaire manquant")

    def test_public_followups_reader_masks_private_payload_markers(self) -> None:
        event = self._event(
            "evt_private_followup",
            OBJECT_FOLLOWUP_RECORDED,
            "PRF-PRIVATE",
            {
                "parent_kind": "point",
                "parent_id": "PNT-SAFE",
                "followup_kind": "proof",
                "followup_id": r"C:\Users\brice\raw\secret.pdf",
                "effect": "partially_resolves",
                "summary": r"Piece recue depuis C:\Users\brice\raw\secret.pdf token=local-secret",
                "remaining_reason": "Voir logs private payload_json",
                "visibility": "cs_only",
            },
            sequence=1,
        )
        reconstruction.rebuild_cache_from_events([event], self.db_path, vault_id="vault_private")

        rows = read_object_followups_v1(self.db_path, parent_kind="point", parent_id="PNT-SAFE")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["summary"], "leve partiellement")
        self.assertEqual(rows[0]["remaining_reason"], "")
        self.assertEqual(rows[0]["visibility"], "conseil_syndical")
        payload = json.dumps(rows, ensure_ascii=False).lower()
        for marker in ("c:\\", "users", "raw", "secret", "token=", "payload_json", "logs", "private", "cs_only"):
            self.assertNotIn(marker, payload)

    def test_incremental_projection_creates_followup_schema_on_existing_db(self) -> None:
        reconstruction.rebuild_cache_from_events([], self.db_path, vault_id="vault_incremental")
        connection = self._connect()
        try:
            connection.execute("DROP TABLE object_followups")
            connection.commit()
        finally:
            connection.close()

        events = [
            self._event(
                "evt_incremental_point",
                POINT_CREATED,
                "PNT-INCR",
                {"point_id": "PNT-INCR", "title": "Point incremental", "status": "open"},
                sequence=1,
            ),
            self._event(
                "evt_incremental_action",
                ACTION_CREATED,
                "ACT-INCR",
                {
                    "action_id": "ACT-INCR",
                    "title": "Action incremental",
                    "related_point_ids": ["PNT-INCR"],
                    "expected_piece_id": "PCE-INCR",
                    "expected_piece_label": "Piece incremental",
                },
                sequence=2,
            ),
        ]

        result = reconstruction.apply_incremental_events(events, self.db_path, vault_id="vault_incremental")

        self.assertEqual(result["applied_events"], 2)
        rows = read_object_followups_v1(self.db_path, parent_kind="point", parent_id="PNT-INCR")
        self.assertEqual([row["followup_id"] for row in rows], ["ACT-INCR", "PCE-INCR"])


if __name__ == "__main__":
    unittest.main()
