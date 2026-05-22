from __future__ import annotations

import re
import unittest

from coproscope.core.event_types import (
    ACTION_CREATED,
    COMMENT_ADDED,
    DOCUMENT_ADDED,
    EVENT_TYPES_V1,
    LEGACY_EVENT_TYPE_ALIASES_V1,
    PASSATION_EXPORT_CREATED,
    PDF_ANNOTATION_CREATED,
    PLUGIN_RESULT_RECORDED,
    POINT_CREATED,
    REQUEST_ACTION_RECORDED,
    REQUEST_CREATED,
    SUGGESTION_OUTCOME_PREPARED,
    SUGGESTION_REVIEW_REQUESTED,
    migrate_legacy_event_type,
    normalize_event_type,
    validate_event_type,
)


class EventTypesTests(unittest.TestCase):
    def test_core_event_type_constants_are_snake_case_and_unique(self) -> None:
        expected = {
            DOCUMENT_ADDED,
            COMMENT_ADDED,
            POINT_CREATED,
            ACTION_CREATED,
            PLUGIN_RESULT_RECORDED,
            PASSATION_EXPORT_CREATED,
            REQUEST_CREATED,
            REQUEST_ACTION_RECORDED,
            SUGGESTION_REVIEW_REQUESTED,
            SUGGESTION_OUTCOME_PREPARED,
            PDF_ANNOTATION_CREATED,
        }

        self.assertTrue(expected.issubset(set(EVENT_TYPES_V1)))
        self.assertEqual(len(EVENT_TYPES_V1), len(set(EVENT_TYPES_V1)))
        for event_type in EVENT_TYPES_V1:
            with self.subTest(event_type=event_type):
                self.assertRegex(event_type, re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$"))
                self.assertNotIn(".", event_type)

    def test_normalize_accepts_only_known_canonical_event_types(self) -> None:
        self.assertEqual(normalize_event_type("document_added"), DOCUMENT_ADDED)
        self.assertEqual(normalize_event_type(" plugin_result_recorded "), PLUGIN_RESULT_RECORDED)
        self.assertTrue(validate_event_type("request_created"))

    def test_normalize_rejects_dotted_and_ambiguous_formats(self) -> None:
        invalid_values = (
            "plugin.result_recorded",
            "passation.export_ref_created",
            "document.added",
            "document-added",
            "document added",
            "document/added",
            "DocumentAdded",
            "DOCUMENT_ADDED",
            "document__added",
            "",
            None,
        )

        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_event_type(value)

    def test_unknown_snake_case_is_not_valid_v1(self) -> None:
        with self.assertRaises(ValueError):
            normalize_event_type("invoice_archived")

    def test_legacy_migration_is_explicit(self) -> None:
        self.assertEqual(LEGACY_EVENT_TYPE_ALIASES_V1["plugin.result_recorded"], PLUGIN_RESULT_RECORDED)
        self.assertEqual(migrate_legacy_event_type("plugin.result_recorded"), PLUGIN_RESULT_RECORDED)
        self.assertEqual(migrate_legacy_event_type("passation.export_ref_created"), PASSATION_EXPORT_CREATED)
        self.assertEqual(migrate_legacy_event_type("request.normalized"), REQUEST_CREATED)
        self.assertEqual(migrate_legacy_event_type("request.action"), REQUEST_ACTION_RECORDED)
        self.assertEqual(migrate_legacy_event_type("request.action_recorded"), REQUEST_ACTION_RECORDED)
        self.assertEqual(migrate_legacy_event_type("suggestion.review_requested"), SUGGESTION_REVIEW_REQUESTED)
        self.assertEqual(migrate_legacy_event_type("suggestion.outcome_prepared"), SUGGESTION_OUTCOME_PREPARED)
        self.assertEqual(migrate_legacy_event_type("document_added"), DOCUMENT_ADDED)


if __name__ == "__main__":
    unittest.main()
