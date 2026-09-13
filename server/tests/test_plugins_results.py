from __future__ import annotations

import json
import unittest

from coproscope.plugins.results import (
    PLUGIN_RESULT_RECORDED_EVENT_TYPE,
    RESULT_STATUS_BLOCKED,
    RESULT_STATUS_COMPLETED,
    PluginProducedObjectRef,
    PluginResultRecordRequest,
    prepare_plugin_result_recorded,
    validate_result_payload_safety,
)


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
HASH_D = "sha256:" + "d" * 64


class PluginsResultsTests(unittest.TestCase):
    def test_prepare_result_recorded_payload_is_ready_for_future_signature(self) -> None:
        request = PluginResultRecordRequest(
            plugin_id="official.docops",
            result_event_type="document.completeness_checked",
            input_hashes={"document.register": HASH_A, "proof.matrix": HASH_B},
            parameters_hash=HASH_C,
            result_hash=HASH_D,
            produced_object_refs=(
                PluginProducedObjectRef(
                    object_type="document.completeness_matrix",
                    object_id="docops.matrix.2026",
                    contract_name="document.completeness_matrix",
                    object_hash=HASH_D,
                ),
            ),
        )

        event = prepare_plugin_result_recorded(request)

        self.assertEqual(event.event_type, PLUGIN_RESULT_RECORDED_EVENT_TYPE)
        self.assertEqual(event.plugin_id, "official.docops")
        self.assertEqual(event.plugin_version, "1.0.0")
        self.assertEqual(event.status, RESULT_STATUS_COMPLETED)
        self.assertEqual(event.errors, ())
        self.assertEqual(event.signature_payload["plugin_version"], "1.0.0")
        self.assertEqual(event.signature_payload["parameters_hash"], HASH_C)
        self.assertEqual(event.signature_payload["result_hash"], HASH_D)
        self.assertNotIn("parameters", event.signature_payload)
        self.assertEqual(validate_result_payload_safety(event.signature_payload), ())

    def test_result_event_type_must_be_declared_by_manifest(self) -> None:
        request = PluginResultRecordRequest(
            plugin_id="official.comptascope",
            result_event_type="document.ocr_completed",
            input_hashes={"document.register": HASH_A},
            parameters_hash=HASH_B,
            result_hash=HASH_C,
        )

        event = prepare_plugin_result_recorded(request)

        self.assertEqual(event.status, RESULT_STATUS_BLOCKED)
        self.assertEqual(
            event.errors,
            ("official.comptascope: result_event_type is not declared by the plugin manifest",),
        )

    def test_unsafe_paths_and_sensitive_values_are_not_exposed_in_payload(self) -> None:
        request = PluginResultRecordRequest(
            plugin_id="official.privacy_biffage",
            result_event_type="privacy.export_sanitized",
            input_hashes={r"raw\secret.pdf": r"C:\vault\raw\secret.pdf", "privacy.rules": HASH_A},
            parameters_hash="password=super-secret",
            result_hash=HASH_B,
            warnings=("source at raw/secret.pdf ignored", "biffage map reviewed"),
            produced_object_refs=(
                PluginProducedObjectRef(
                    object_type="privacy.sanitized_bundle",
                    object_id=r"raw\secret.pdf",
                    contract_name="privacy.sanitized_bundle",
                    object_hash=HASH_C,
                ),
                PluginProducedObjectRef(
                    object_type="privacy.audit_log",
                    object_id="privacy.audit.2026",
                    contract_name="privacy.audit_log",
                    object_hash=HASH_D,
                ),
            ),
        )

        event = prepare_plugin_result_recorded(request)
        payload_text = json.dumps(event.to_dict(), ensure_ascii=True, sort_keys=True)

        self.assertEqual(event.status, RESULT_STATUS_BLOCKED)
        self.assertIn("input_hashes contains an unsafe input key", event.errors)
        self.assertIn("parameters_hash is not a sha256 hash", event.errors)
        self.assertIn("warnings[0] contains unsafe detail", event.errors)
        self.assertIn("produced_object_refs[0].object_id contains unsafe detail", event.errors)
        self.assertNotIn("secret.pdf", payload_text)
        self.assertNotIn("super-secret", payload_text)
        self.assertNotIn(r"C:\\vault", payload_text)
        self.assertEqual(event.input_hashes, {"privacy.rules": HASH_A})
        self.assertEqual(event.parameters_hash, "sha256:invalid")
        self.assertEqual(event.warnings, ("biffage map reviewed",))
        self.assertEqual(len(event.produced_object_refs), 1)

    def test_docops_comptascope_privacyops_and_docai_results_stay_logical(self) -> None:
        examples = (
            (
                "official.docops",
                "document.classified",
                "document.register",
                "docops.document.register.2026",
            ),
            (
                "official.comptascope",
                "accounting.expense_reconciled",
                "accounting.reconciliation",
                "comptascope.reconciliation.2025",
            ),
            (
                "official.privacy_biffage",
                "privacy.redaction_planned",
                "privacy.audit_log",
                "privacy.audit.2026",
            ),
            (
                "official.docai_ocr",
                "document.ocr_completed",
                "document.text",
                "docai.text.doc-001",
            ),
        )

        for plugin_id, event_type, contract_name, object_id in examples:
            with self.subTest(plugin_id=plugin_id):
                event = prepare_plugin_result_recorded(
                    PluginResultRecordRequest(
                        plugin_id=plugin_id,
                        result_event_type=event_type,
                        input_hashes={"logical.input": HASH_A},
                        parameters_hash=HASH_B,
                        result_hash=HASH_C,
                        produced_object_refs=(
                            PluginProducedObjectRef(
                                object_type=contract_name,
                                object_id=object_id,
                                contract_name=contract_name,
                                object_hash=HASH_D,
                            ),
                        ),
                    )
                )

                payload_text = json.dumps(event.signature_payload, sort_keys=True)
                self.assertEqual(event.errors, ())
                self.assertNotIn("raw/", payload_text)
                self.assertNotIn("\\raw\\", payload_text)
                self.assertNotIn("_path", payload_text)
                self.assertNotIn("password", payload_text)
                self.assertNotIn("token", payload_text)
                self.assertNotIn("secret", payload_text)

    def test_payload_safety_validator_rejects_paths_and_sensitive_parameter_keys(self) -> None:
        errors = validate_result_payload_safety(
            {
                "event_type": PLUGIN_RESULT_RECORDED_EVENT_TYPE,
                "parameters": {"access_token": "token=abc"},
                "raw_path": "raw/pv.pdf",
            }
        )

        self.assertIn("parameters.access_token uses a sensitive key", errors)
        self.assertIn("raw_path uses a path key", errors)
        self.assertIn("raw_path contains unsafe detail", errors)


if __name__ == "__main__":
    unittest.main()
