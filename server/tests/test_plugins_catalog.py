from __future__ import annotations

import unittest

from coproscope.plugins.catalog import (
    CATALOG_VERSION,
    PluginManifest,
    get_plugin_manifest,
    official_catalog,
    plugin_ids,
    recommended_plugins_for_vault,
    required_plugins_for_vault,
    validate_official_catalog,
)


class PluginsCatalogTests(unittest.TestCase):
    def test_catalog_contains_initial_official_v1_plugins(self) -> None:
        self.assertEqual(
            plugin_ids(),
            (
                "official.docops",
                "official.comptascope",
                "official.privacy_biffage",
                "official.docai_ocr",
                "official.evidence_exports",
            ),
        )
        self.assertTrue(all(isinstance(plugin, PluginManifest) for plugin in official_catalog()))

    def test_v1_policy_is_local_signed_and_without_auto_update_or_community_plugins(self) -> None:
        self.assertEqual(validate_official_catalog(), ())
        for plugin in official_catalog():
            self.assertTrue(plugin.official)
            self.assertFalse(plugin.community_allowed_v1)
            self.assertFalse(plugin.auto_update)
            self.assertTrue(plugin.local_outside_vault)
            self.assertTrue(plugin.activation_requires_signature)
            self.assertEqual(plugin.signature.status, "placeholder")
            self.assertEqual(plugin.signature.activation_policy, "future_signed_activation_required")
            self.assertEqual(plugin.compatibility.catalog_version, CATALOG_VERSION)

    def test_each_manifest_declares_permissions_events_and_contracts(self) -> None:
        for plugin in official_catalog():
            self.assertGreaterEqual(len(plugin.permissions), 1, plugin.plugin_id)
            self.assertGreaterEqual(len(plugin.event_types_produced), 1, plugin.plugin_id)
            self.assertGreaterEqual(len(plugin.input_contracts), 1, plugin.plugin_id)
            self.assertGreaterEqual(len(plugin.output_contracts), 1, plugin.plugin_id)
            self.assertTrue(all(permission.code for permission in plugin.permissions))
            self.assertTrue(all(event for event in plugin.event_types_produced))
            self.assertTrue(all(contract.name and contract.version and contract.path for contract in plugin.input_contracts))
            self.assertTrue(all(contract.name and contract.version and contract.path for contract in plugin.output_contracts))

    def test_vault_required_and_recommended_sets_are_explicit(self) -> None:
        self.assertEqual(
            tuple(plugin.plugin_id for plugin in required_plugins_for_vault()),
            ("official.docops", "official.privacy_biffage"),
        )
        self.assertEqual(
            tuple(plugin.plugin_id for plugin in recommended_plugins_for_vault()),
            (
                "official.docops",
                "official.comptascope",
                "official.privacy_biffage",
                "official.evidence_exports",
            ),
        )

    def test_docai_heavy_ocr_is_separate_from_docops(self) -> None:
        docops = get_plugin_manifest("official.docops")
        docai = get_plugin_manifest("official.docai_ocr")

        self.assertFalse(docai.required_by_vault)
        self.assertFalse(docai.recommended_by_vault)
        self.assertIn("local.compute.heavy", {permission.code for permission in docai.permissions})
        self.assertIn("document.ocr_completed", docai.event_types_produced)
        self.assertNotIn("document.ocr_completed", docops.event_types_produced)
        self.assertNotIn("coproscope.modules.docai", docops.modules)

    def test_manifest_can_be_serialized_for_docs_or_api_preview(self) -> None:
        manifest = get_plugin_manifest("official.comptascope").to_dict()

        self.assertEqual(manifest["plugin_id"], "official.comptascope")
        self.assertEqual(manifest["signature"]["status"], "placeholder")
        self.assertEqual(manifest["permissions"][0]["code"], "vault.read.documents")


if __name__ == "__main__":
    unittest.main()
