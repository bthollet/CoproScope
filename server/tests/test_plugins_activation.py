from __future__ import annotations

import unittest
from dataclasses import replace

from coproscope.plugins.activation import (
    ACTIVATION_EVENT_TYPE,
    ACTIVATION_STATUS_BLOCKED,
    ACTIVATION_STATUS_READY_FOR_SIGNATURE,
    ACTIVATION_STATUS_REVOKED,
    REVOCATION_STATUS_REVOKED,
    PluginActivationRequest,
    check_plugin_compatibility,
    hash_plugin_manifest,
    prepare_plugin_activation,
    recommended_vault_plugin_ids,
    required_vault_plugin_ids,
)
from coproscope.plugins.catalog import PluginSignature, get_plugin_manifest


class PluginsActivationTests(unittest.TestCase):
    def test_required_and_recommended_sets_are_exposed_after_catalog(self) -> None:
        self.assertEqual(
            required_vault_plugin_ids(),
            frozenset({"official.docops", "official.privacy_biffage"}),
        )
        self.assertEqual(
            recommended_vault_plugin_ids(),
            frozenset(
                {
                    "official.docops",
                    "official.comptascope",
                    "official.privacy_biffage",
                    "official.evidence_exports",
                }
            ),
        )

    def test_manifest_hash_is_stable_and_excludes_signature_placeholder(self) -> None:
        manifest = get_plugin_manifest("official.docops")
        changed_signature = PluginSignature(
            status="placeholder",
            authority="another-future-authority",
            key_id="ANOTHER-FUTURE-KEY",
            digest_sha256="sha256:another-future-digest",
            signature="sig:another-future-signature",
            activation_policy="future_signed_activation_required",
        )

        self.assertRegex(hash_plugin_manifest(manifest), r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(
            hash_plugin_manifest(manifest),
            hash_plugin_manifest(replace(manifest, signature=changed_signature)),
        )

    def test_prepare_activation_event_is_ready_for_future_signature(self) -> None:
        manifest = get_plugin_manifest("official.docops")
        granted = tuple(permission.code for permission in manifest.permissions)
        request = PluginActivationRequest(
            plugin_id=manifest.plugin_id,
            activated_by="local-admin",
            activated_at="2026-05-20T19:30:00Z",
            permissions_granted=granted,
            config_hash="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )

        event = prepare_plugin_activation(request)

        self.assertEqual(event.event_type, ACTIVATION_EVENT_TYPE)
        self.assertEqual(event.plugin_id, "official.docops")
        self.assertEqual(event.plugin_version, manifest.version)
        self.assertEqual(event.activation_status, ACTIVATION_STATUS_READY_FOR_SIGNATURE)
        self.assertEqual(event.errors, ())
        self.assertTrue(event.compatibility.compatible)
        self.assertTrue(event.required_by_vault)
        self.assertTrue(event.recommended_by_vault)
        self.assertEqual(event.signature_payload["manifest_hash"], event.manifest_hash)
        self.assertEqual(event.signature_payload["permissions_granted"], granted)
        self.assertNotIn("activation_signature", event.signature_payload)

    def test_compatibility_check_blocks_unsupported_runtime(self) -> None:
        manifest = get_plugin_manifest("official.comptascope")

        check = check_plugin_compatibility(
            manifest,
            app_version="0.0.9",
            vault_format_version="0",
            python_version="3.10.9",
        )

        self.assertFalse(check.compatible)
        self.assertIn("app version 0.0.9 is below required 0.1.0", check.errors)
        self.assertIn("vault format 0 is below required 1", check.errors)
        self.assertIn("python version 3.10.9 is below required 3.11", check.errors)

    def test_revoked_manifest_prepares_revoked_status_without_activation(self) -> None:
        manifest = get_plugin_manifest("official.privacy_biffage")
        request = PluginActivationRequest(
            plugin_id=manifest.plugin_id,
            activated_by="local-admin",
            activated_at="2026-05-20T19:35:00Z",
            permissions_granted=tuple(permission.code for permission in manifest.permissions),
            revocation_status=REVOCATION_STATUS_REVOKED,
        )

        event = prepare_plugin_activation(request)

        self.assertEqual(event.activation_status, ACTIVATION_STATUS_REVOKED)
        self.assertEqual(event.errors, ("manifest is revoked",))

    def test_unknown_permission_blocks_activation_payload(self) -> None:
        request = PluginActivationRequest(
            plugin_id="official.evidence_exports",
            activated_by="local-admin",
            activated_at="2026-05-20T19:40:00Z",
            permissions_granted=("vault.read.outputs", "network.unbounded"),
        )

        event = prepare_plugin_activation(request)

        self.assertEqual(event.activation_status, ACTIVATION_STATUS_BLOCKED)
        self.assertIn(
            "official.evidence_exports: unknown permission granted: network.unbounded",
            event.errors,
        )


if __name__ == "__main__":
    unittest.main()
