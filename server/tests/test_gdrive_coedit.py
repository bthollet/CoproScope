from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import coproscope.modules.gdrive_coedit as coedit


class GoogleDriveCoeditionProtocolTests(unittest.TestCase):
    def _prepared_packet(
        self,
        root: Path,
        *,
        payload: bytes,
        object_sha256: str = "a" * 64,
        actor_key_sha256: str = "b" * 64,
        device_key_sha256: str = "c" * 64,
        parents: list[str] | None = None,
        sequence: int = 1,
    ) -> dict[str, object]:
        packet_hash = hashlib.sha256(payload).hexdigest()
        packet = root / "sync" / "changes" / packet_hash[:2] / f"{packet_hash}.change"
        packet.parent.mkdir(parents=True)
        packet.write_bytes(payload)
        return coedit.prepare_encrypted_change_packet(
            sync_root=root / "sync",
            encrypted_change_path=packet,
            object_sha256=object_sha256,
            actor_key_sha256=actor_key_sha256,
            device_key_sha256=device_key_sha256,
            parents=parents or [],
            sequence=sequence,
        )

    def _assert_sanitized_simulator_output(self, result: dict[str, object], root: Path) -> None:
        serialized = json.dumps(result, ensure_ascii=True).lower()
        self.assertNotIn(str(root).lower(), serialized)
        for forbidden in ("token", "secret", "raw", "private", "logs", "drive_id", "relative_path"):
            self.assertNotIn(forbidden, serialized)

    def test_prepare_change_packet_builds_append_only_manifest_without_paths(self) -> None:
        payload = b"encrypted-change-packet"
        packet_hash = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "sync" / "changes" / packet_hash[:2] / f"{packet_hash}.change"
            packet.parent.mkdir(parents=True)
            packet.write_bytes(payload)

            result = coedit.prepare_encrypted_change_packet(
                sync_root=root / "sync",
                encrypted_change_path=packet,
                object_sha256="a" * 64,
                actor_key_sha256="b" * 64,
                device_key_sha256="c" * 64,
                parents=["d" * 64, "e" * 64, "d" * 64],
                sequence=7,
            )

        serialized = json.dumps(result, ensure_ascii=True)
        change_packet = result["change_packet"]
        merge_contract = result["merge_contract"]
        self.assertEqual(result["status"], "prepared")
        self.assertFalse(result["upload_attempted"])
        self.assertEqual(change_packet["protocol"], coedit.COEDIT_PROTOCOL)
        self.assertEqual(change_packet["packet_kind"], "encrypted_change")
        self.assertEqual(change_packet["sha256"], packet_hash)
        self.assertEqual(change_packet["parents"], ["d" * 64, "e" * 64])
        self.assertEqual(change_packet["sequence"], 7)
        self.assertEqual(change_packet["identity_disclosure"], "pseudonymous-key-fingerprints-only")
        self.assertEqual(merge_contract["mode"], "append-only-encrypted-change-log")
        self.assertEqual(merge_contract["merge_policy"], coedit.MERGE_POLICY)
        self.assertEqual(merge_contract["conflict_policy"], coedit.CONFLICT_POLICY)
        self.assertTrue(merge_contract["allows_parallel_parents"])
        self.assertNotIn(str(root), serialized)
        self.assertNotIn("token", serialized.lower())
        self.assertNotIn("secret", serialized.lower())

    def test_prepare_change_packet_blocks_hash_name_mismatch_without_leaking_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "sync" / "changes" / "ff" / f"{'f' * 64}.change"
            packet.parent.mkdir(parents=True)
            packet.write_bytes(b"encrypted-change-packet")

            result = coedit.prepare_encrypted_change_packet(
                sync_root=root / "sync",
                encrypted_change_path=packet,
                object_sha256="a" * 64,
                actor_key_sha256="b" * 64,
                device_key_sha256="c" * 64,
                parents=[],
            )

        serialized = json.dumps(result, ensure_ascii=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["gate"]["code"], "hash_name_mismatch")
        self.assertIsNone(result["change_packet"])
        self.assertIsNone(result["merge_contract"])
        self.assertNotIn(str(root), serialized)

    def test_prepare_change_packet_rejects_non_pseudonymous_identity_fields(self) -> None:
        payload = b"encrypted-change-packet"
        packet_hash = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "sync" / "changes" / packet_hash[:2] / f"{packet_hash}.change"
            packet.parent.mkdir(parents=True)
            packet.write_bytes(payload)

            with self.assertRaisesRegex(ValueError, "actor key"):
                coedit.prepare_encrypted_change_packet(
                    sync_root=root / "sync",
                    encrypted_change_path=packet,
                    object_sha256="a" * 64,
                    actor_key_sha256="person@example.test",
                    device_key_sha256="c" * 64,
                    parents=[],
                )

    def test_prepare_change_packet_blocks_forbidden_source_location(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = root / "sync" / "raw" / f"{'a' * 64}.change"
            packet.parent.mkdir(parents=True)
            packet.write_bytes(b"encrypted-change-packet")

            result = coedit.prepare_encrypted_change_packet(
                sync_root=root / "sync",
                encrypted_change_path=packet,
                object_sha256="a" * 64,
                actor_key_sha256="b" * 64,
                device_key_sha256="c" * 64,
                parents=[],
            )

        serialized = json.dumps(result, ensure_ascii=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["gate"]["code"], "forbidden_source_location")
        self.assertIsNone(result["change_packet"])
        self.assertNotIn(str(root), serialized)
        self.assertNotIn("raw", result["gate"]["message"].lower())

    def test_simulator_merges_same_parent_disjoint_component_hashes_without_leaks(self) -> None:
        shared_parent = "d" * 64
        first_component = "1" * 64
        second_component = "2" * 64
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self._prepared_packet(
                root,
                payload=b"encrypted-change-device-one",
                parents=[shared_parent],
                sequence=9,
            )
            second = self._prepared_packet(
                root,
                payload=b"encrypted-change-device-two",
                actor_key_sha256="e" * 64,
                device_key_sha256="f" * 64,
                parents=[shared_parent],
                sequence=1,
            )

            result = coedit.simulate_two_device_coedition(
                first_packet=first,
                first_intent={"component_sha256": first_component},
                second_packet=second,
                second_intent={"component_sha256": second_component},
            )

        self.assertEqual(result["status"], "merged")
        self.assertEqual(result["protocol"], coedit.COEDIT_PROTOCOL)
        self.assertEqual(result["silent_overwrite"], "forbidden")
        self.assertEqual(result["merge"]["type"], "concurrent_disjoint_component_hashes")
        self.assertEqual(result["merge"]["component_sha256s"], [first_component, second_component])
        self.assertEqual(result["branch"]["relation"], "parallel-shared-parent")
        self.assertEqual(result["branch"]["shared_parent_sha256s"], [shared_parent])
        self.assertFalse(result["network_attempted"])
        self.assertFalse(result["upload_attempted"])
        self._assert_sanitized_simulator_output(result, root)

    def test_simulator_conflicts_on_overlapping_component_hash_and_forbids_overwrite(self) -> None:
        shared_parent = "d" * 64
        component = "1" * 64
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self._prepared_packet(root, payload=b"encrypted-change-overlap-one", parents=[shared_parent])
            second = self._prepared_packet(
                root,
                payload=b"encrypted-change-overlap-two",
                actor_key_sha256="e" * 64,
                device_key_sha256="f" * 64,
                parents=[shared_parent],
            )

            result = coedit.simulate_two_device_coedition(
                first_packet=first,
                first_intent={"component_sha256": component},
                second_packet=second,
                second_intent={"component_sha256": component},
            )

        self.assertEqual(result["status"], "conflict")
        self.assertEqual(result["silent_overwrite"], "forbidden")
        self.assertIsNone(result["merge"])
        self.assertEqual(result["conflict"]["type"], "overlapping_component_hashes")
        self.assertEqual(result["conflict"]["component_sha256s"], [component])
        self._assert_sanitized_simulator_output(result, root)

    def test_simulator_blocks_different_objects_or_blocked_packets_without_sensitive_terms(self) -> None:
        shared_parent = "d" * 64
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self._prepared_packet(root, payload=b"encrypted-change-object-one", parents=[shared_parent])
            second = self._prepared_packet(
                root,
                payload=b"encrypted-change-object-two",
                object_sha256="9" * 64,
                actor_key_sha256="e" * 64,
                device_key_sha256="f" * 64,
                parents=[shared_parent],
            )

            different_object = coedit.simulate_two_device_coedition(
                first_packet=first,
                first_intent={"component_sha256": "1" * 64},
                second_packet=second,
                second_intent={"component_sha256": "2" * 64},
            )

            blocked_path = root / "sync" / "raw" / f"{'a' * 64}.change"
            blocked_path.parent.mkdir(parents=True)
            blocked_path.write_bytes(b"encrypted-change-blocked")
            blocked = coedit.prepare_encrypted_change_packet(
                sync_root=root / "sync",
                encrypted_change_path=blocked_path,
                object_sha256="a" * 64,
                actor_key_sha256="b" * 64,
                device_key_sha256="c" * 64,
                parents=[shared_parent],
            )
            blocked_packet = coedit.simulate_two_device_coedition(
                first_packet=blocked,
                first_intent={"component_sha256": "1" * 64},
                second_packet=first,
                second_intent={"component_sha256": "2" * 64},
            )

        self.assertEqual(different_object["status"], "blocked")
        self.assertEqual(different_object["blockers"][0]["code"], "object_sha256_mismatch")
        self.assertEqual(blocked_packet["status"], "blocked")
        self.assertEqual(blocked_packet["blockers"][0]["code"], "packet_blocked")
        self._assert_sanitized_simulator_output(different_object, root)
        self._assert_sanitized_simulator_output(blocked_packet, root)

    def test_simulator_requires_no_network_upload_or_drive_identifier(self) -> None:
        shared_parent = "d" * 64
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self._prepared_packet(root, payload=b"encrypted-change-network-one", parents=[shared_parent])
            second = self._prepared_packet(
                root,
                payload=b"encrypted-change-network-two",
                actor_key_sha256="e" * 64,
                device_key_sha256="f" * 64,
                parents=[shared_parent],
            )

            result = coedit.simulate_two_device_coedition(
                first_packet=first,
                first_intent={"component_sha256": "1" * 64},
                second_packet=second,
                second_intent={"component_sha256": "2" * 64},
            )

        self.assertFalse(result["network_attempted"])
        self.assertFalse(result["upload_attempted"])
        self.assertFalse(result["transport"]["network_attempted"])
        self.assertFalse(result["transport"]["upload_attempted"])
        self.assertEqual(result["transport"]["remote_reference"], "not-required")
        self._assert_sanitized_simulator_output(result, root)

    def test_simulator_returns_noop_for_same_packet_twice(self) -> None:
        shared_parent = "d" * 64
        component = "1" * 64
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packet = self._prepared_packet(root, payload=b"encrypted-change-idempotent", parents=[shared_parent])

            result = coedit.simulate_two_device_coedition(
                first_packet=packet,
                first_intent={"component_sha256": component},
                second_packet=packet,
                second_intent={"component_sha256": component},
            )

        self.assertEqual(result["status"], "noop")
        self.assertIsNone(result["merge"])
        self.assertEqual(result["ordered_result"]["type"], "idempotent_same_packet")
        self.assertEqual(result["ordered_result"]["component_sha256s"], [component])
        self._assert_sanitized_simulator_output(result, root)

    def test_simulator_returns_ordered_for_causal_packets_without_using_sequence_as_ancestry(self) -> None:
        base_parent = "d" * 64
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parent_packet = self._prepared_packet(
                root,
                payload=b"encrypted-change-parent",
                parents=[base_parent],
                sequence=99,
            )
            parent_hash = parent_packet["change_packet"]["sha256"]
            child_packet = self._prepared_packet(
                root,
                payload=b"encrypted-change-child",
                actor_key_sha256="e" * 64,
                device_key_sha256="f" * 64,
                parents=[parent_hash],
                sequence=1,
            )

            result = coedit.simulate_two_device_coedition(
                first_packet=child_packet,
                first_intent={"component_sha256": "2" * 64},
                second_packet=parent_packet,
                second_intent={"component_sha256": "1" * 64},
            )

        self.assertEqual(result["status"], "ordered")
        self.assertIsNone(result["merge"])
        self.assertEqual(result["ordered_result"]["type"], "causal_packet_order")
        order = result["ordered_result"]["order"]
        self.assertEqual(order[0]["packet_sha256"], parent_hash)
        self.assertEqual(order[0]["display_sequence"], 99)
        self.assertEqual(order[1]["display_sequence"], 1)
        self._assert_sanitized_simulator_output(result, root)

    def test_simulator_conflicts_when_parent_or_component_metadata_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self._prepared_packet(root, payload=b"encrypted-change-no-parent-one")
            second = self._prepared_packet(
                root,
                payload=b"encrypted-change-no-parent-two",
                actor_key_sha256="e" * 64,
                device_key_sha256="f" * 64,
            )

            no_parent = coedit.simulate_two_device_coedition(
                first_packet=first,
                first_intent={"component_sha256": "1" * 64},
                second_packet=second,
                second_intent={"component_sha256": "2" * 64},
            )
            no_component = coedit.simulate_two_device_coedition(
                first_packet=first,
                first_intent={"logical_target": "resolution:one"},
                second_packet=second,
                second_intent={"component_sha256": "2" * 64},
            )

        self.assertEqual(no_parent["status"], "conflict")
        self.assertEqual(no_parent["conflict"]["type"], "ambiguous_parentage")
        self.assertEqual(no_component["status"], "conflict")
        self.assertEqual(no_component["conflict"]["type"], "intent_metadata_missing")
        self._assert_sanitized_simulator_output(no_parent, root)
        self._assert_sanitized_simulator_output(no_component, root)


if __name__ == "__main__":
    unittest.main()
