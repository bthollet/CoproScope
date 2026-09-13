from __future__ import annotations

import json
import unittest

from coproscope.core.events_v1 import BusinessEventDraft, draft_hash, payload_hash
from coproscope.core.event_types import (
    PLUGIN_RESULT_RECORDED,
    REQUEST_CREATED,
    SUGGESTION_REVIEW_REQUESTED,
)
from coproscope.vault.business_events import (
    BUSINESS_EVENT_VAULT_ENVELOPE_SCHEMA,
    BUSINESS_EVENT_VAULT_SIGNATURE_STATUS,
    BusinessEventVaultContext,
    envelope_hash,
    prepare_business_event_envelope,
)


HASH_A = "sha256:" + "a" * 64


class VaultBusinessEventsTests(unittest.TestCase):
    def test_prepares_hash_only_append_envelope_from_safe_business_event_draft(self) -> None:
        draft = BusinessEventDraft(
            event_type=REQUEST_CREATED,
            object_id="REQ-2026-001",
            actor_ref="account:cs",
            device_ref="device:local",
            occurred_at="2026-05-20T12:30:00Z",
            payload_hash=payload_hash({"request_id": "REQ-2026-001", "status": "open"}),
            previous_hash=HASH_A,
            source_module="requestops",
        )
        context = BusinessEventVaultContext(
            vault_id="vault-copro",
            device_id="dev_local",
            author_key_id="ak_1234567890abcdef",
            sequence=12,
            created_at="2026-05-20T12:31:00+00:00",
            prev_device_event_hash="b" * 64,
        )

        envelope = prepare_business_event_envelope(draft, context)
        serialized = json.dumps(envelope.to_dict(), sort_keys=True)

        self.assertEqual(envelope.body["schema_version"], BUSINESS_EVENT_VAULT_ENVELOPE_SCHEMA)
        self.assertEqual(envelope.body["vault_signature_status"], BUSINESS_EVENT_VAULT_SIGNATURE_STATUS)
        self.assertEqual(envelope.body["business_draft_hash"], draft_hash(draft))
        self.assertEqual(envelope.body["business_payload_hash"], draft.payload_hash)
        self.assertEqual(envelope.body["business_previous_hash"], HASH_A)
        self.assertEqual(envelope.body["prev_device_event_hash"], "b" * 64)
        self.assertRegex(envelope.canonical_hash, r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(envelope.vault_event_hash, envelope.canonical_hash.removeprefix("sha256:"))
        self.assertEqual(envelope_hash(envelope.to_dict()), envelope.canonical_hash)
        self.assertNotIn("clear_payload", serialized)
        self.assertNotIn("encrypted_payload", serialized)
        self.assertNotIn("open", serialized)

    def test_canonical_hash_is_stable_and_changes_with_chain_context(self) -> None:
        draft = BusinessEventDraft(
            event_type=SUGGESTION_REVIEW_REQUESTED,
            object_id="SUG-1",
            actor_ref="account:cs",
            device_ref="device:local",
            occurred_at="2026-05-20T13:00:00Z",
            payload_hash=payload_hash({"suggestion_id": "SUG-1"}),
            source_module="suggestionops",
        )
        base_context = BusinessEventVaultContext(
            vault_id="vault-copro",
            device_id="dev_local",
            author_key_id="ak_1234567890abcdef",
            sequence=1,
            created_at="2026-05-20T13:01:00+00:00",
        )
        same_context = BusinessEventVaultContext(**base_context.__dict__)
        next_context = BusinessEventVaultContext(
            vault_id="vault-copro",
            device_id="dev_local",
            author_key_id="ak_1234567890abcdef",
            sequence=2,
            created_at="2026-05-20T13:01:00+00:00",
            prev_device_event_hash="c" * 64,
        )

        self.assertEqual(
            prepare_business_event_envelope(draft, base_context).canonical_hash,
            prepare_business_event_envelope(draft, same_context).canonical_hash,
        )
        self.assertNotEqual(
            prepare_business_event_envelope(draft, base_context).canonical_hash,
            prepare_business_event_envelope(draft, next_context).canonical_hash,
        )

    def test_rejects_invalid_draft_or_vault_context(self) -> None:
        draft = BusinessEventDraft(
            event_type=PLUGIN_RESULT_RECORDED,
            object_id="official.docops:result",
            actor_ref="account:system",
            device_ref="device:local",
            occurred_at="2026-05-20T14:00:00Z",
            payload_hash=payload_hash({"result_id": "RESULT-1"}),
            source_module="plugins.results",
        )

        with self.assertRaises(ValueError):
            prepare_business_event_envelope(
                draft,
                BusinessEventVaultContext(
                    vault_id="vault copro",
                    device_id="dev_local",
                    author_key_id="ak_1234567890abcdef",
                    sequence=1,
                    created_at="2026-05-20T14:01:00+00:00",
                ),
            )

        with self.assertRaises(ValueError):
            prepare_business_event_envelope(
                draft,
                BusinessEventVaultContext(
                    vault_id="vault-copro",
                    device_id="dev_local",
                    author_key_id="ak_1234567890abcdef",
                    sequence=1,
                    created_at="2026-05-20T14:01:00+00:00",
                    prev_device_event_hash=HASH_A,
                ),
            )

        unsafe_draft = BusinessEventDraft(
            event_type=PLUGIN_RESULT_RECORDED,
            object_id="official.docops:result",
            actor_ref="account:system",
            device_ref="device:local",
            occurred_at="2026-05-20T14:00:00Z",
            payload_hash="not-a-hash",
            source_module="plugins.results",
        )
        with self.assertRaises(ValueError):
            prepare_business_event_envelope(
                unsafe_draft,
                BusinessEventVaultContext(
                    vault_id="vault-copro",
                    device_id="dev_local",
                    author_key_id="ak_1234567890abcdef",
                    sequence=1,
                    created_at="2026-05-20T14:01:00+00:00",
                ),
            )


if __name__ == "__main__":
    unittest.main()
