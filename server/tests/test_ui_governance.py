from __future__ import annotations

import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from coproscope.core.common import load_instance
from coproscope.web.app import create_app
from coproscope.web.governance import build_governance_overview


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTANCE_ROOT = REPO_ROOT / "examples" / "synthetic_copro"


class GovernanceUiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.instance = load_instance(None, str(INSTANCE_ROOT))

    def test_governance_route_renders_local_control_topics(self) -> None:
        client = TestClient(create_app(self.instance, year=2025))
        response = client.get("/gouvernance")

        self.assertEqual(response.status_code, 200)
        text = response.text
        self.assertIn("Tableau de controle local", text)
        self.assertIn("Coffres separes, organisations reliees", text)
        self.assertIn("Survie de l'archive", text)
        self.assertIn("Organisations imbriquees", text)
        self.assertIn("Droits croises", text)
        self.assertIn("Demandes au syndic", text)
        self.assertIn("Commissions et acces", text)
        self.assertIn("Indicateurs centraux", text)
        self.assertIn("Archive complete", text)
        self.assertNotIn("vault", text.lower())
        self.assertNotIn("quorum", text.lower())
        self.assertNotIn("hash", text.lower())
        self.assertNotIn("commission_mandate_allowed", text)

    def test_governance_model_keeps_copro_coffres_separate(self) -> None:
        model = build_governance_overview(self.instance, 2025)

        rules = " ".join(model["vaults"]["rules"])
        self.assertIn("coffres", rules)
        self.assertIn("cles", rules)
        self.assertIn("gouvernance complexe", rules)
        self.assertNotIn("vault", rules)

    def test_governance_model_explains_complex_organizations_without_merging_coffres(self) -> None:
        model = build_governance_overview(self.instance, 2025)

        organization_labels = [item["label"] for item in model["complexity"]["organizations"]]
        self.assertIn("Syndicat primaire", organization_labels)
        self.assertIn("Syndicat secondaire", organization_labels)
        self.assertIn("ASL", organization_labels)
        self.assertIn("Union de syndicats", organization_labels)
        guardrails = " ".join(model["complexity"]["guardrails"])
        self.assertIn("un droit croise ouvre une lecture precise", guardrails)
        self.assertIn("pas tout un coffre voisin", guardrails)
        complexity_text = " ".join(model["complexity"]["guardrails"])
        complexity_text += " " + " ".join(item["rule"] for item in model["complexity"]["cross_rights"])
        self.assertIn("coffre source", complexity_text.lower())

    def test_governance_model_translates_resilience_codes_for_ui(self) -> None:
        model = build_governance_overview(self.instance, 2025)

        self.assertEqual(model["vault"]["status"], "a_configurer")
        self.assertEqual(model["vault"]["status_label"], "a configurer")
        self.assertIn("les cles de secours", " ".join(model["vault"]["risk_labels"]))
        self.assertNotIn("no_key_quorum", " ".join(model["vault"]["risk_labels"]))

    def test_governance_nav_link_is_available(self) -> None:
        client = TestClient(create_app(self.instance, year=2025))
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("/gouvernance", response.text)


if __name__ == "__main__":
    unittest.main()
