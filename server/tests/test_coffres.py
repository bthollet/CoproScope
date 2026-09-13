from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from coproscope.core.coffres import (
    CoproCoffre,
    normalize_coffre,
    switch_context_summary,
    validate_coffre_isolation,
)


class CoproCoffresTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _coffre_dict(self, coffre_id: str, *, governance_scope: str | None = None) -> dict[str, str]:
        data = {
            "coffre_id": coffre_id,
            "display_name": f"Copro {coffre_id}",
            "instance_path": str(self.root / coffre_id / "instance.yml"),
            "local_root": str(self.root / coffre_id / "cache"),
            "sync_root": str(self.root / coffre_id / "sync"),
            "keys_root": str(self.root / coffre_id / "keys"),
            "role_hint": "conseil_syndical",
            "last_opened_at": "2026-05-20T10:00:00+00:00",
        }
        if governance_scope is not None:
            data["governance_scope"] = governance_scope
        return data

    def test_two_distinct_coffres_are_normalized_and_isolated(self) -> None:
        alpha = normalize_coffre(self._coffre_dict("alpha"))
        beta = normalize_coffre(json.dumps(self._coffre_dict("beta")))

        self.assertIsInstance(alpha, CoproCoffre)
        self.assertEqual(alpha.coffre_id, "alpha")
        self.assertEqual(beta.display_name, "Copro beta")
        self.assertTrue(alpha.local_root.is_absolute())

        isolation = validate_coffre_isolation([alpha, beta])
        self.assertTrue(isolation["ok"], isolation["risks"])
        self.assertEqual(isolation["risks"], [])

    def test_shared_sync_cache_or_keys_root_reports_isolation_risks(self) -> None:
        baseline = self._coffre_dict("baseline")
        shared_sync = self._coffre_dict("shared-sync")
        shared_sync["sync_root"] = baseline["sync_root"]
        shared_cache = self._coffre_dict("shared-cache")
        shared_cache["local_root"] = baseline["local_root"]
        shared_keys = self._coffre_dict("shared-keys")
        shared_keys["keys_root"] = baseline["keys_root"]

        isolation = validate_coffre_isolation([baseline, shared_sync, shared_cache, shared_keys])

        self.assertFalse(isolation["ok"])
        risk_fields = {(risk["first_field"], risk["second_field"]) for risk in isolation["risks"]}
        self.assertIn(("sync_root", "sync_root"), risk_fields)
        self.assertIn(("local_root", "local_root"), risk_fields)
        self.assertIn(("keys_root", "keys_root"), risk_fields)

    def test_shared_instance_path_reports_isolation_risk(self) -> None:
        alpha = self._coffre_dict("alpha")
        beta = self._coffre_dict("beta")
        beta["instance_path"] = alpha["instance_path"]

        isolation = validate_coffre_isolation([alpha, beta])

        self.assertFalse(isolation["ok"])
        self.assertEqual(isolation["risks"][0]["first_field"], "instance_path")
        self.assertEqual(isolation["risks"][0]["second_field"], "instance_path")

    def test_nested_roots_and_ambiguous_names_report_novice_confusion_risks(self) -> None:
        alpha = self._coffre_dict("alpha")
        beta = self._coffre_dict("beta")
        beta["display_name"] = "  copro alpha  "
        beta["sync_root"] = str(Path(alpha["sync_root"]) / "nested-beta")

        isolation = validate_coffre_isolation([alpha, beta])

        self.assertFalse(isolation["ok"])
        risk_types = {risk["risk"] for risk in isolation["risks"]}
        self.assertIn("ambiguous_display_name", risk_types)
        self.assertIn("nested_protected_path", risk_types)

    def test_duplicate_coffre_id_reports_identity_risk(self) -> None:
        alpha = self._coffre_dict("alpha")
        duplicate = self._coffre_dict("ALPHA")

        isolation = validate_coffre_isolation([alpha, duplicate])

        self.assertFalse(isolation["ok"])
        self.assertIn("duplicate_coffre_id", {risk["risk"] for risk in isolation["risks"]})

    def test_switch_summary_does_not_carry_document_token_or_role(self) -> None:
        alpha = normalize_coffre(self._coffre_dict("alpha"))
        beta = normalize_coffre(self._coffre_dict("beta"))
        current_context = {
            "document_id": "doc-secret",
            "access_token": "token-secret",
            "token": "generic-token-secret",
            "role": "syndic",
        }

        summary = switch_context_summary(alpha, beta, current_context=current_context)

        self.assertEqual(summary["from_coffre_id"], "alpha")
        self.assertEqual(summary["to_coffre_id"], "beta")
        self.assertEqual(summary["role_hint"], "conseil_syndical")
        self.assertEqual(summary["carried_context"], {})
        self.assertEqual(summary["cleared_context"], ["document_id", "access_token", "token", "role"])
        self.assertEqual(summary["dropped_context_keys"], ["document_id", "access_token", "token", "role"])
        self.assertIsNone(summary["effective_document_id"])
        self.assertIsNone(summary["effective_access_token"])
        self.assertIsNone(summary["effective_role"])
        self.assertTrue(summary["requires_document_selection"])
        self.assertTrue(summary["requires_reauthentication"])
        self.assertTrue(summary["requires_role_confirmation"])
        self.assertNotIn("doc-secret", json.dumps(summary))
        self.assertNotIn("token-secret", json.dumps(summary))
        self.assertNotIn("generic-token-secret", json.dumps(summary))
        self.assertNotIn('"role": "syndic"', json.dumps(summary))

    def test_governance_scope_is_metadata_and_does_not_merge_coffres(self) -> None:
        alpha = normalize_coffre(self._coffre_dict("alpha", governance_scope="multi-batiments"))
        beta = normalize_coffre(self._coffre_dict("beta", governance_scope="multi-batiments"))

        isolation = validate_coffre_isolation([alpha, beta])
        summary = switch_context_summary(alpha, beta)

        self.assertTrue(isolation["ok"], isolation["risks"])
        self.assertEqual(alpha.governance_scope, "multi-batiments")
        self.assertEqual(beta.governance_scope, "multi-batiments")
        self.assertEqual(summary["governance_scope"], "multi-batiments")
        self.assertEqual(summary["from_coffre_id"], "alpha")
        self.assertEqual(summary["to_coffre_id"], "beta")


if __name__ == "__main__":
    unittest.main()
