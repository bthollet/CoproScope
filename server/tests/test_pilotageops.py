from __future__ import annotations

import unittest

from coproscope.modules.indicatorops import STATUS_ALERT, STATUS_OK, STATUS_VERIFY
from coproscope.modules.pilotageops import (
    DIFFUSION_CS,
    DIFFUSION_RESTREINT,
    DIFFUSION_SYNDIC,
    DOMAIN_DEMANDES,
    DOMAIN_ESPACES_VERTS,
    DOMAIN_INVESTISSEMENTS,
    DOMAIN_RISQUES,
    PILOTAGE_DOMAINS,
    PilotageCard,
    build_pilotage_card,
    build_pilotage_cards,
    card_to_dict,
    normalize_domain,
    pilotage_cards_from_csv,
    threshold_summary,
    validate_pilotage_card,
)


class PilotageOpsTests(unittest.TestCase):
    def test_composes_actionable_card_with_source_threshold_diffusion_and_links(self) -> None:
        card = build_pilotage_card(
            {
                "indicator_id": "eau_derive_mensuelle",
                "theme": "Consommations",
                "name": "Derive eau",
                "unit": "%",
            },
            {
                "indicator_id": "eau_derive_mensuelle",
                "value": "24",
                "period": "2026-05",
                "source": "FactureOps",
                "proof_ref": "FACT-EAU-2026-05",
                "data_quality": "verified",
                "vault_id": "vault-a",
                "instance_id": "inst-a",
            },
            {"indicator_id": "eau_derive_mensuelle", "attention": "10", "alert": "20", "direction": "max"},
            attachment={
                "indicator_id": "eau_derive_mensuelle",
                "point_ref": "POINT-EAU-2026-05",
                "action_ref": "ACT-RELANCE-RELEVE-EAU",
                "diffusion": "syndic",
                "next_action": "Demander le releve compteur et comparer au contrat.",
                "vault_id": "vault-a",
                "instance_id": "inst-a",
            },
        )

        self.assertEqual(card.domain, "consommations")
        self.assertEqual(card.status, STATUS_ALERT)
        self.assertEqual(card.threshold, "attention >= 10; alerte >= 20")
        self.assertEqual(card.source, "FactureOps")
        self.assertEqual(card.proof_ref, "FACT-EAU-2026-05")
        self.assertEqual(card.diffusion, DIFFUSION_SYNDIC)
        self.assertEqual(card.point_ref, "POINT-EAU-2026-05")
        self.assertEqual(card.action_ref, "ACT-RELANCE-RELEVE-EAU")
        self.assertIn("Point prioritaire", card.novice_reading)
        self.assertTrue(validate_pilotage_card(card))

    def test_missing_proof_stays_visible_and_card_is_attached_to_default_point(self) -> None:
        card = build_pilotage_card(
            {
                "indicator_id": "demandes_syndic_retard",
                "theme": "Demandes",
                "name": "Demandes syndic en retard",
            },
            {
                "indicator_id": "demandes_syndic_retard",
                "value": 3,
                "period": "2026-05",
                "source": "SyndicOps",
                "proof_ref": "",
                "data_quality": "incomplete",
            },
            {"indicator_id": "demandes_syndic_retard", "attention": 2, "alert": 5},
        )

        self.assertEqual(card.domain, DOMAIN_DEMANDES)
        self.assertEqual(card.status, STATUS_VERIFY)
        self.assertEqual(card.proof_ref, "preuve manquante")
        self.assertEqual(card.diffusion, DIFFUSION_CS)
        self.assertTrue(card.point_ref.startswith("POINT-"))
        self.assertIn("verifier", card.next_action.lower())
        self.assertTrue(validate_pilotage_card(card))

    def test_domain_aliases_cover_required_pilotage_domains(self) -> None:
        expected = {
            "consommations": "consommations",
            "maintenance": "entretien",
            "fonds travaux": DOMAIN_INVESTISSEMENTS,
            "espaces verts": DOMAIN_ESPACES_VERTS,
            "chantier": "travaux",
            "AG": "gouvernance",
            "syndic": DOMAIN_DEMANDES,
            "contentieux": DOMAIN_RISQUES,
        }

        self.assertEqual(set(expected.values()), PILOTAGE_DOMAINS)
        for raw, domain in expected.items():
            self.assertEqual(normalize_domain(raw), domain)

    def test_risk_cards_default_to_restricted_diffusion(self) -> None:
        card = build_pilotage_card(
            {"indicator_id": "piece_contentieux_absente", "theme": "Risques/contentieux", "name": "Piece contentieux absente"},
            {
                "indicator_id": "piece_contentieux_absente",
                "value": "assignation absente",
                "period": "2026-05",
                "source": "Dossier contentieux",
                "proof_ref": "DOS-CONT-1",
            },
            None,
        )

        self.assertEqual(card.domain, DOMAIN_RISQUES)
        self.assertEqual(card.diffusion, DIFFUSION_RESTREINT)
        self.assertEqual(card.threshold, "seuil non renseigne")
        self.assertTrue(validate_pilotage_card(card))

    def test_build_pilotage_cards_matches_thresholds_and_attachments_by_context(self) -> None:
        definitions = [
            {"indicator_id": "cout_jardin_passage", "theme": "Espaces verts", "name": "Cout par passage", "unit": "EUR", "vault_id": "vault-a"},
            {"indicator_id": "cout_jardin_passage", "theme": "Espaces verts", "name": "Cout par passage B", "unit": "EUR", "vault_id": "vault-b"},
        ]
        observations = [
            {
                "indicator_id": "cout_jardin_passage",
                "value": "180",
                "period": "2026-Q2",
                "source": "FactureOps",
                "proof_ref": "FACT-JARDIN-A",
                "vault_id": "vault-a",
            },
            {
                "indicator_id": "cout_jardin_passage",
                "value": "180",
                "period": "2026-Q2",
                "source": "FactureOps",
                "proof_ref": "FACT-JARDIN-B",
                "vault_id": "vault-b",
            },
        ]
        thresholds = [
            {"indicator_id": "cout_jardin_passage", "attention": "150", "alert": "200", "vault_id": "vault-a"},
            {"indicator_id": "cout_jardin_passage", "attention": "300", "alert": "400", "vault_id": "vault-b"},
        ]
        attachments = [
            {"indicator_id": "cout_jardin_passage", "point_ref": "POINT-JARDIN-A", "vault_id": "vault-a"},
            {"indicator_id": "cout_jardin_passage", "point_ref": "POINT-JARDIN-B", "vault_id": "vault-b"},
        ]

        cards = build_pilotage_cards(definitions, observations, thresholds, attachments)

        self.assertEqual([card.status for card in cards], ["attention", STATUS_OK])
        self.assertEqual([card.point_ref for card in cards], ["POINT-JARDIN-A", "POINT-JARDIN-B"])
        self.assertEqual([card.title for card in cards], ["Cout par passage", "Cout par passage B"])

    def test_csv_rows_create_cards_without_ui_dependency(self) -> None:
        rows = pilotage_cards_from_csv(
            "indicator_id,domaine,name,value,period,source,proof_ref,attention,alert,point_ref,action_ref,prochaine_action,diffusion\n"
            "travaux_retard,travaux,Retard reception,18,2026-05,PV AG,PV-2026-04,7,15,POINT-TRAVAUX,ACT-TRAVAUX,"
            "Demander la preuve de cloture,cs\n"
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].status, STATUS_ALERT)
        self.assertEqual(rows[0].diffusion, DIFFUSION_CS)
        self.assertEqual(rows[0].point_ref, "POINT-TRAVAUX")
        self.assertEqual(rows[0].action_ref, "ACT-TRAVAUX")
        self.assertTrue(validate_pilotage_card(rows[0]))

    def test_validation_rejects_orphan_card_without_point_or_action(self) -> None:
        orphan = PilotageCard(
            card_id="PLC-ORPHAN",
            indicator_id="gouvernance_decision",
            domain="gouvernance",
            title="Decision sans suite",
            period="2026-05",
            status=STATUS_OK,
            value=1,
            unit="decision",
            threshold="seuil non renseigne",
            source="AGOps",
            proof_ref="PV-2026",
            confidence="moyenne",
            novice_reading="Une decision reste a suivre.",
            next_action="Rattacher a un point de suivi.",
            diffusion=DIFFUSION_CS,
            point_ref="",
            action_ref="",
        )

        with self.assertRaises(ValueError):
            validate_pilotage_card(orphan)

    def test_invalid_explicit_diffusion_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_pilotage_card(
                {"indicator_id": "gouvernance_decision", "theme": "Gouvernance", "name": "Decision a suivre"},
                {
                    "indicator_id": "gouvernance_decision",
                    "value": 1,
                    "period": "2026-05",
                    "source": "AGOps",
                    "proof_ref": "PV-2026",
                },
                None,
                diffusion="reseaux sociaux",
            )

    def test_threshold_summary_supports_min_direction_for_amortissement(self) -> None:
        self.assertEqual(
            threshold_summary({"target": 50, "attention": 30, "alert": 15, "direction": "min"}),  # type: ignore[arg-type]
            "cible 50; attention <= 30; alerte <= 15",
        )

    def test_card_to_dict_keeps_actionable_fields(self) -> None:
        card = build_pilotage_card(
            {"indicator_id": "fonds_travaux_couverture", "theme": "Investissements", "name": "Couverture fonds travaux", "unit": "%"},
            {
                "indicator_id": "fonds_travaux_couverture",
                "value": 12,
                "period": "2026",
                "source": "Budget",
                "proof_ref": "BUDGET-2026",
            },
            {"indicator_id": "fonds_travaux_couverture", "attention": 30, "alert": 15, "direction": "min"},
            attachment={"indicator_id": "fonds_travaux_couverture", "action_ref": "ACT-ARBITRAGE-AG"},
        )

        data = card_to_dict(card)

        self.assertEqual(data["domain"], DOMAIN_INVESTISSEMENTS)
        self.assertEqual(data["action_ref"], "ACT-ARBITRAGE-AG")
        self.assertIn("next_action", data)


if __name__ == "__main__":
    unittest.main()
