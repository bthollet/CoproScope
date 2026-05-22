from __future__ import annotations

import json
import unittest

from coproscope.core.events_v1 import (
    BusinessEventDraft,
    assert_payload_safe,
    canonical_json,
    draft_from_passation_export_ref,
    draft_from_plugin_result,
    draft_from_requestops_action,
    draft_from_requestops_request,
    draft_from_suggestionops_outcome,
    draft_from_suggestionops_suggestion,
    draft_hash,
    draft_to_canonical_json,
    payload_hash,
    stable_hash,
    validate_draft,
)
from coproscope.core.event_types import (
    PASSATION_EXPORT_CREATED,
    PLUGIN_RESULT_RECORDED,
    REQUEST_ACTION_RECORDED,
    REQUEST_CREATED,
    SUGGESTION_OUTCOME_PREPARED,
    SUGGESTION_REVIEW_REQUESTED,
)
from coproscope.modules.requestops import normalize_action, normalize_request
from coproscope.modules.suggestionops import REVIEW_ACCEPTED, SuggestionReview, build_outcome, normalize_suggestion
from coproscope.plugins.results import PluginProducedObjectRef, PluginResultRecordRequest, prepare_plugin_result_recorded


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
HASH_D = "sha256:" + "d" * 64


class EventsV1Tests(unittest.TestCase):
    def test_canonical_json_and_payload_hash_are_stable(self) -> None:
        left = {"b": [2, 1], "a": {"y": "ok", "x": "stable"}}
        right = {"a": {"x": "stable", "y": "ok"}, "b": [2, 1]}

        self.assertEqual(canonical_json(left), canonical_json(right))
        self.assertEqual(payload_hash(left), payload_hash(right))
        self.assertEqual(stable_hash(left), payload_hash(left))

    def test_rejects_secret_paths_raw_and_restricted_markers(self) -> None:
        unsafe_payloads = (
            {"local_path": "DOC-1"},
            {"source_ref": r"C:\Users\ExampleUser\CoproScope\raw\piece.pdf"},
            {"note": "Bearer token=abc"},
            {"scope": "restricted"},
            {"raw": "copie brute"},
        )

        for payload in unsafe_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    assert_payload_safe(payload)

    def test_requestops_request_and_action_drafts_are_hash_only_and_linkable(self) -> None:
        request = normalize_request(
            {
                "channel": "email",
                "subject": "Fuite avec contact alice@example.org",
                "summary": r"Piece initiale dans C:\Users\ExampleUser\raw\photo.jpg",
                "proof_ref": "MSG-2026-05-20",
                "source_ref": "REG-DEMANDES",
                "next_action": "Qualifier la demande.",
                "visibility": "restricted",
                "received_at": "2026-05-20T10:00:00Z",
            }
        )
        action = normalize_action(
            {
                "request_id": request.request_id,
                "occurred_at": "2026-05-20T10:05:00Z",
                "actor_role": "conseil_syndical",
                "action_type": "qualification",
                "summary": "Demande qualifiee sans detail nominatif.",
                "proof_ref": "MSG-2026-05-20",
                "status_after": "en_cours",
            }
        )

        request_draft = draft_from_requestops_request(
            request,
            actor_ref="account:cs",
            device_ref="device:local",
        )
        action_draft = draft_from_requestops_action(
            action,
            actor_ref="account:cs",
            device_ref="device:local",
            previous_hash=draft_hash(request_draft),
        )
        serialized = json.dumps([request_draft.to_dict(), action_draft.to_dict()], sort_keys=True)

        self.assertEqual(request_draft.event_type, REQUEST_CREATED)
        self.assertEqual(request_draft.visibility, "non_diffusable")
        self.assertEqual(action_draft.previous_hash, draft_hash(request_draft))
        self.assertEqual(action_draft.event_type, REQUEST_ACTION_RECORDED)
        self.assertTrue(request_draft.payload_hash.startswith("sha256:"))
        self.assertNotIn("alice@example.org", serialized)
        self.assertNotIn("raw", serialized.lower())
        self.assertNotIn("restricted", serialized.lower())
        self.assertTrue(validate_draft(request_draft))
        self.assertTrue(validate_draft(action_draft))

    def test_suggestionops_suggestion_and_outcome_drafts_share_previous_hash(self) -> None:
        suggestion = normalize_suggestion(
            {
                "title": "Relancer le syndic",
                "why": "Deux demandes restent ouvertes.",
                "proof": "REG-DEMANDES-2026-05;MSG-42",
                "source": "SyndicOps",
                "next_action": "Faire valider la relance.",
                "impact": "moyen",
                "effort": "faible",
                "confidence": "haute",
                "public": "conseil_syndical",
                "transformations": "demande;action",
            }
        )
        review = SuggestionReview(
            review_id="REV-1",
            suggestion_id=suggestion.suggestion_id,
            reviewer="account:cs",
            decision=REVIEW_ACCEPTED,
            rationale="Preuves suffisantes.",
            selected_outcome_type="demande",
        )
        outcome = build_outcome(suggestion, review)

        suggestion_draft = draft_from_suggestionops_suggestion(
            suggestion,
            actor_ref="account:cs",
            device_ref="device:local",
            occurred_at="2026-05-20T11:00:00Z",
        )
        outcome_draft = draft_from_suggestionops_outcome(
            outcome,
            actor_ref="account:cs",
            device_ref="device:local",
            occurred_at="2026-05-20T11:05:00Z",
            previous_hash=draft_hash(suggestion_draft),
        )

        self.assertEqual(suggestion_draft.event_type, SUGGESTION_REVIEW_REQUESTED)
        self.assertEqual(outcome_draft.event_type, SUGGESTION_OUTCOME_PREPARED)
        self.assertEqual(suggestion_draft.source_module, "suggestionops")
        self.assertEqual(outcome_draft.previous_hash, draft_hash(suggestion_draft))
        self.assertNotEqual(suggestion_draft.payload_hash, outcome_draft.payload_hash)
        self.assertTrue(validate_draft(outcome_draft))

    def test_plugin_result_draft_uses_signature_safe_result_payload(self) -> None:
        event = prepare_plugin_result_recorded(
            PluginResultRecordRequest(
                plugin_id="official.docops",
                result_event_type="document.completeness_checked",
                input_hashes={"document.register": HASH_A},
                parameters_hash=HASH_B,
                result_hash=HASH_C,
                produced_object_refs=(
                    PluginProducedObjectRef(
                        object_type="document.completeness_matrix",
                        object_id="docops.matrix.2026",
                        contract_name="document.completeness_matrix",
                        object_hash=HASH_D,
                    ),
                ),
            )
        )

        draft = draft_from_plugin_result(
            event,
            actor_ref="account:system",
            device_ref="device:local",
            occurred_at="2026-05-20T12:00:00Z",
        )

        self.assertEqual(draft.event_type, PLUGIN_RESULT_RECORDED)
        self.assertEqual(draft.source_module, "plugins.results")
        self.assertIn("official.docops:document.completeness_checked", draft.object_id)
        self.assertNotIn("document.completeness_matrix", draft_to_canonical_json(draft))
        self.assertTrue(validate_draft(draft))

    def test_passation_export_ref_draft_keeps_only_export_refs(self) -> None:
        document = {
            "schema_version": "passation_export_derive.v1",
            "source_of_truth": False,
            "export_id": "PASSATION-2026-05",
            "generated_at": "2026-05-20T12:00:00+00:00",
            "title": "Export passation avec chemin ignore",
            "source_refs": ("DOC-1", r"C:\Users\ExampleUser\private.pdf"),
            "proof_refs": ("EV-1", "EV-1"),
            "scope": {"kind": "passation_ag_contentieux", "diffusion": "coproprietaires"},
        }

        draft = draft_from_passation_export_ref(
            document,
            actor_ref="account:cs",
            device_ref="device:local",
        )
        serialized = draft_to_canonical_json(draft)

        self.assertEqual(draft.object_id, "PASSATION-2026-05")
        self.assertEqual(draft.event_type, PASSATION_EXPORT_CREATED)
        self.assertEqual(draft.visibility, "copro")
        self.assertNotIn("private.pdf", serialized)
        self.assertTrue(validate_draft(draft))

    def test_business_event_draft_is_hashable_without_vault_side_effect(self) -> None:
        draft = BusinessEventDraft(
            event_type=REQUEST_CREATED,
            object_id="REQ-1",
            actor_ref="account:cs",
            device_ref="device:local",
            occurred_at="2026-05-20T12:30:00Z",
            payload_hash=payload_hash({"request_id": "REQ-1"}),
            source_module="requestops",
        )

        self.assertTrue(validate_draft(draft))
        self.assertEqual(draft_hash(draft), draft_hash(BusinessEventDraft(**draft.to_dict())))


if __name__ == "__main__":
    unittest.main()
