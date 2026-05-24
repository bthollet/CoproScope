from __future__ import annotations

import json
import unittest

from coproscope.modules.timelineops import (
    build_object_timeline,
    create_logical_shortcut,
    normalize_action_log_entries,
    validate_shortcut_no_private_path,
)


class TimelineOpsTests(unittest.TestCase):
    def test_build_object_timeline_sorts_chronologically_and_keeps_stable_ties(self) -> None:
        register_rows = [
            {"decision_action_id": "ACT-1", "date": "2026-05-20T10:00:00+00:00", "summary": "same timestamp first"},
            {"decision_action_id": "ACT-1", "date": "2026-05-20T10:00:00+00:00", "summary": "same timestamp second"},
            {"decision_action_id": "ACT-1", "date": "2026-05-20T09:00:00+00:00", "summary": "earliest"},
        ]
        action_rows = [
            {"timestamp": "2026-05-20T10:00:00+00:00", "run_id": "run-1", "action": "manual_note", "target": "ACT-1", "detail": "action log tie"}
        ]
        event_rows = [
            {"event_id": "evt-late", "event_type": "status_changed", "object_id": "ACT-1", "created_at": "2026-05-20T11:00:00+00:00", "payload": {"status": "DONE"}}
        ]

        timeline = build_object_timeline("ACT-1", register_rows, action_rows, event_rows)

        self.assertEqual(
            [row["summary"] for row in timeline],
            ["earliest", "same timestamp first", "same timestamp second", "action log tie", "status_changed"],
        )
        self.assertEqual(timeline[3]["event_type"], "action_log_added")
        self.assertEqual(timeline[4]["status"], "DONE")

    def test_normalize_action_log_entries_uses_object_refs_without_private_paths(self) -> None:
        rows = normalize_action_log_entries(
            [
                {
                    "timestamp": "2026-05-20T12:00:00+00:00",
                    "run_id": "run-path",
                    "action": "write",
                    "target": r"C:\Users\ExampleUser\CoproScope\private.pdf",
                    "detail": "private target is not promoted to object id",
                },
                {
                    "timestamp": "2026-05-20T12:01:00+00:00",
                    "run_id": "run-doc",
                    "action": "write",
                    "target": "DOC-1",
                    "detail": "logical target",
                },
            ]
        )

        self.assertEqual(rows[0]["object_id"], "")
        self.assertEqual(rows[0]["target_ref"], "")
        self.assertEqual(rows[1]["object_id"], "DOC-1")
        self.assertEqual(rows[1]["target_ref"], "DOC-1")

    def test_logical_shortcut_contains_no_private_path_or_windows_lnk(self) -> None:
        shortcut = create_logical_shortcut("AG-2026-04-29", "DOC-PROOF-1", "ag proof")

        self.assertTrue(validate_shortcut_no_private_path(shortcut))
        self.assertEqual(shortcut["event_type"], "shortcut_created")
        self.assertFalse(shortcut["creates_windows_lnk"])
        self.assertNotIn(".lnk", json.dumps(shortcut, sort_keys=True).lower())
        self.assertFalse(any("path" in key.lower() for key in shortcut))

        with self.assertRaises(ValueError):
            validate_shortcut_no_private_path(
                {
                    "shortcut_id": "LSC-BAD",
                    "object_id": "AG-1",
                    "target_object_id": "DOC-1",
                    "target_path": r"C:\Users\ExampleUser\CoproScope\restricted\piece.pdf",
                }
            )

        with self.assertRaises(ValueError):
            create_logical_shortcut("AG-1", r"C:\Users\ExampleUser\preuve.pdf", "ag")

    def test_deleting_shortcut_does_not_delete_target_document_or_proof(self) -> None:
        proof_documents = {"DOC-PROOF-1": {"object_id": "DOC-PROOF-1", "kind": "proof"}}
        shortcuts = [create_logical_shortcut("ACT-1", "DOC-PROOF-1", "proof")]

        remaining_shortcuts = [item for item in shortcuts if item["shortcut_id"] != shortcuts[0]["shortcut_id"]]

        self.assertEqual(remaining_shortcuts, [])
        self.assertIn("DOC-PROOF-1", proof_documents)
        self.assertTrue(shortcuts[0]["target_retained_on_delete"])
        self.assertFalse(shortcuts[0]["removes_target_on_delete"])
        self.assertEqual(shortcuts[0]["delete_behavior"], "shortcut_only")

    def test_timeline_keeps_status_proof_and_comment_from_registers_and_events(self) -> None:
        register_rows = [
            {
                "decision_action_id": "ACT-1",
                "date": "2026-05-20",
                "statut": "PREUVE_A_DEMANDER",
                "proof_doc_ids": "DOC-OLD",
                "notes": "preuve initialement manquante",
            }
        ]
        event_rows = [
            {
                "event_id": "evt-status",
                "event_type": "status_changed",
                "object_id": "ACT-1",
                "created_at": "2026-05-20T10:00:00+00:00",
                "payload_json": json.dumps({"status": "EN_COURS", "comment": "relance envoyee"}),
            },
            {
                "event_id": "evt-proof",
                "event_type": "proof_linked",
                "object_id": "ACT-1",
                "created_at": "2026-05-20T11:00:00+00:00",
                "payload": {"proof_doc_id": "DOC-PROOF-1", "comment": "PV signe rattache"},
            },
        ]

        timeline = build_object_timeline("ACT-1", register_rows=register_rows, event_log_rows=event_rows)

        self.assertEqual(timeline[0]["status"], "PREUVE_A_DEMANDER")
        self.assertEqual(timeline[0]["proof_ref"], "DOC-OLD")
        self.assertEqual(timeline[0]["comment"], "preuve initialement manquante")
        self.assertEqual(timeline[1]["status"], "EN_COURS")
        self.assertEqual(timeline[1]["comment"], "relance envoyee")
        self.assertEqual(timeline[2]["proof_ref"], "DOC-PROOF-1")
        self.assertEqual(timeline[2]["comment"], "PV signe rattache")


if __name__ == "__main__":
    unittest.main()
