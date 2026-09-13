from __future__ import annotations

import unittest

from coproscope.core.event_types import (
    DOCUMENT_ADDED,
    PASSATION_EXPORT_CREATED,
    PDF_ANNOTATION_CREATED,
    PLUGIN_RESULT_RECORDED,
    REQUEST_ACTION_RECORDED,
    REQUEST_CREATED,
)
from coproscope.core.events_v1 import BusinessEventDraft, payload_hash
from coproscope.vault.business_events import (
    BUSINESS_EVENT_VAULT_ENVELOPE_SCHEMA,
    BusinessEventVaultContext,
    envelope_hash,
    prepare_business_event_envelope,
)
from coproscope.vault.projection_events import (
    empty_projection,
    project_business_event_envelopes,
)


class VaultProjectionEventsTests(unittest.TestCase):
    def test_projects_hash_only_envelopes_into_minimal_memory_indexes(self) -> None:
        request = _envelope_for(REQUEST_CREATED, "REQ-1", source_module="requestops", sequence=1)
        action = _envelope_for(REQUEST_ACTION_RECORDED, "REQ-1-ACT-1", source_module="requestops", sequence=2)
        plugin = _envelope_for(PLUGIN_RESULT_RECORDED, "official.docops:result:abc", source_module="plugins.results", sequence=3)
        export = _envelope_for(PASSATION_EXPORT_CREATED, "PASSATION-2026-05", source_module="passation_exports", sequence=4)
        annotation = _envelope_for(PDF_ANNOTATION_CREATED, "ANN-1", source_module="annotationops", sequence=5)

        projection = project_business_event_envelopes((request, action, plugin, export, annotation))

        self.assertEqual(set(projection.requests), {"REQ-1"})
        self.assertEqual(set(projection.actions), {"REQ-1-ACT-1"})
        self.assertEqual(set(projection.plugins), {"official.docops:result:abc"})
        self.assertEqual(set(projection.exports), {"PASSATION-2026-05"})
        self.assertEqual(set(projection.annotations), {"ANN-1"})
        self.assertEqual(projection.diagnostics, ())
        self.assertEqual(projection.requests["REQ-1"].business_payload_hash, request.body["business_payload_hash"])
        self.assertEqual(projection.requests["REQ-1"].source_event_hashes, (request.canonical_hash,))
        serialized = str(projection.to_dict()).lower()
        self.assertNotIn("clear_payload", serialized)
        self.assertNotIn("encrypted_payload", serialized)

    def test_rejects_non_canonical_and_unknown_event_types_as_diagnostics(self) -> None:
        legacy = _manual_envelope("request.normalized", "REQ-legacy")
        unknown = _manual_envelope("request_escalated", "REQ-unknown")
        unsupported_but_canonical = _manual_envelope(DOCUMENT_ADDED, "DOC-1")

        projection = project_business_event_envelopes((legacy, unknown, unsupported_but_canonical))

        self.assertEqual(projection.requests, {})
        self.assertEqual([diagnostic.code for diagnostic in projection.diagnostics], ["invalid_event_type", "unknown_event_type", "unknown_event_type"])
        self.assertEqual(projection.diagnostics[0].severity, "error")
        self.assertEqual(projection.diagnostics[2].severity, "warning")

    def test_preserves_conflicts_without_overwriting_existing_projection(self) -> None:
        first = _envelope_for(REQUEST_CREATED, "REQ-1", source_module="requestops", sequence=1, payload_seed="alpha")
        conflicting = _envelope_for(REQUEST_CREATED, "REQ-1", source_module="requestops", sequence=2, payload_seed="beta")

        projection = project_business_event_envelopes((first, conflicting))

        self.assertEqual(projection.requests["REQ-1"].business_payload_hash, first.body["business_payload_hash"])
        self.assertEqual(len(projection.diagnostics), 1)
        self.assertEqual(projection.diagnostics[0].code, "conflict")
        self.assertEqual(projection.diagnostics[0].existing_event_hash, first.canonical_hash)
        self.assertEqual(projection.diagnostics[0].conflicting_event_hash, conflicting.canonical_hash)

    def test_rejects_payload_bearing_or_tampered_envelopes_without_mutating_input(self) -> None:
        projection = empty_projection()
        dirty = _manual_envelope(REQUEST_CREATED, "REQ-dirty")
        dirty["payload"] = {"clear": "forbidden"}
        dirty["canonical_hash"] = envelope_hash(dirty)
        dirty["vault_event_hash"] = dirty["canonical_hash"].removeprefix("sha256:")
        tampered = dict(_manual_envelope(REQUEST_CREATED, "REQ-tampered"))
        tampered["object_id"] = "REQ-tampered-edited"

        result = project_business_event_envelopes((dirty, tampered), initial=projection)

        self.assertEqual(projection.requests, {})
        self.assertEqual(result.requests, {})
        self.assertEqual([diagnostic.code for diagnostic in result.diagnostics], ["payload_present", "invalid_hash"])

    def test_detects_device_sequence_fork_before_object_projection(self) -> None:
        first = _envelope_for(REQUEST_CREATED, "REQ-1", sequence=1, payload_seed="alpha")
        fork = _envelope_for(REQUEST_CREATED, "REQ-2", sequence=1, payload_seed="beta")

        projection = project_business_event_envelopes((first, fork))

        self.assertEqual(set(projection.requests), {"REQ-1"})
        self.assertEqual(len(projection.diagnostics), 1)
        self.assertEqual(projection.diagnostics[0].code, "conflict")
        self.assertIn("device sequence", projection.diagnostics[0].message)


def _envelope_for(
    event_type: str,
    object_id: str,
    *,
    source_module: str = "test",
    sequence: int = 1,
    payload_seed: str = "payload",
):
    payload_hash_value = payload_hash({"object_id": object_id, "seed": payload_seed}) if payload_seed == "payload" else "sha256:" + payload_seed[0] * 64
    draft = BusinessEventDraft(
        event_type=event_type,
        object_id=object_id,
        actor_ref="account:cs",
        device_ref="device:local",
        occurred_at="2026-05-20T12:00:00Z",
        payload_hash=payload_hash_value,
        source_module=source_module,
    )
    return prepare_business_event_envelope(
        draft,
        BusinessEventVaultContext(
            vault_id="vault-copro",
            device_id="dev_local",
            author_key_id="ak_1234567890abcdef",
            sequence=sequence,
            created_at=f"2026-05-20T12:{sequence:02d}:00+00:00",
        ),
    )


def _manual_envelope(event_type: str, object_id: str) -> dict[str, object]:
    body: dict[str, object] = {
        "schema_version": BUSINESS_EVENT_VAULT_ENVELOPE_SCHEMA,
        "vault_id": "vault-copro",
        "event_type": event_type,
        "object_id": object_id,
        "sequence": 1,
        "created_at": "2026-05-20T12:00:00+00:00",
        "occurred_at": "2026-05-20T12:00:00Z",
        "device_id": "dev_local",
        "author_key_id": "ak_1234567890abcdef",
        "prev_device_event_hash": "",
        "business_draft_hash": "sha256:" + "a" * 64,
        "business_previous_hash": "",
        "business_payload_hash": "sha256:" + "b" * 64,
        "business_actor_ref": "account:cs",
        "business_device_ref": "device:local",
        "business_source_module": "test",
        "business_visibility": "conseil_syndical",
        "business_future_signature_status": "pending_future_signature",
        "vault_signature_status": "pending_vault_signature",
    }
    canonical_hash = envelope_hash(body)
    body["canonical_hash"] = canonical_hash
    body["vault_event_hash"] = canonical_hash.removeprefix("sha256:")
    return body


if __name__ == "__main__":
    unittest.main()
