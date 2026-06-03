from __future__ import annotations

import json
import unittest

from coproscope.modules import drive_shared_state_merge


class DriveSharedStateMergeTests(unittest.TestCase):
    def test_merges_disjoint_nested_changes_without_payload_in_metadata(self) -> None:
        result = drive_shared_state_merge.merge_shared_state(
            base={"decision": {"etat": "vote"}, "travaux": {"count": 1}},
            local={"decision": {"etat": "vote", "note": "FICTIF local"}, "travaux": {"count": 1}},
            remote={"decision": {"etat": "vote"}, "travaux": {"count": 2}},
        )
        serialized = json.dumps({key: value for key, value in result.items() if key != "merged_state"}, ensure_ascii=True).lower()

        self.assertEqual(result["status"], "merged")
        self.assertEqual(result["merged_state"]["decision"]["note"], "FICTIF local")
        self.assertEqual(result["merged_state"]["travaux"]["count"], 2)
        self.assertNotIn("fictif local", serialized)

    def test_conflicts_on_same_or_parent_path_changes(self) -> None:
        same = drive_shared_state_merge.merge_shared_state(
            base={"note": "base"},
            local={"note": "local"},
            remote={"note": "remote"},
        )
        parent = drive_shared_state_merge.merge_shared_state(
            base={"bloc": {"a": 1}},
            local={"bloc": "local"},
            remote={"bloc": {"a": 1, "b": 2}},
        )

        self.assertEqual(same["status"], "conflict")
        self.assertEqual(same["reason"], "overlapping_shared_state_paths")
        self.assertEqual(parent["status"], "conflict")
        self.assertGreater(parent["overlap_count"], 0)

    def test_refuses_merge_when_visible_delta_is_missing(self) -> None:
        result = drive_shared_state_merge.merge_shared_state(
            base={"note": "base"},
            local={"note": "base"},
            remote={"note": "remote"},
        )

        self.assertEqual(result["status"], "conflict")
        self.assertEqual(result["reason"], "insufficient_visible_delta")


if __name__ == "__main__":
    unittest.main()
