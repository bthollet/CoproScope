from __future__ import annotations

import unittest

from coproscope.modules.indicatorops import (
    STATUS_ALERT,
    STATUS_ATTENTION,
    STATUS_OK,
    STATUS_VERIFY,
    IndicatorDefinition,
    MetricObservation,
    TargetThreshold,
    build_dashboard_card,
    build_dashboard_cards,
    definitions_from_csv,
    observations_from_csv,
    thresholds_from_csv,
    validate_dashboard_card,
)


class IndicatorOpsTests(unittest.TestCase):
    def test_indicator_without_proof_is_marked_to_verify(self) -> None:
        definition = IndicatorDefinition(
            indicator_id="gouvernance_decisions_sans_preuve",
            theme="Gouvernance",
            name="Decisions sans preuve",
            unit="decision",
        )
        observation = MetricObservation(
            indicator_id="gouvernance_decisions_sans_preuve",
            value=3,
            period="2026-05",
            source="AGOps",
            proof_ref="",
            vault_id="vault-a",
        )

        card = build_dashboard_card(definition, observation, next_action="Demander les PV et pieces rattachees.")

        self.assertEqual(card.status, STATUS_VERIFY)
        self.assertEqual(card.confidence, STATUS_VERIFY)
        self.assertEqual(card.proof_ref, "preuve manquante")
        self.assertEqual(card.source, "AGOps")
        self.assertTrue(validate_dashboard_card(card))

    def test_thresholds_return_ok_attention_and_alert(self) -> None:
        definition = IndicatorDefinition(
            indicator_id="contrats_ecart_facture",
            theme="Contrats",
            name="Ecart facture contrat",
            unit="%",
        )
        threshold = TargetThreshold(
            indicator_id="contrats_ecart_facture",
            attention=10,
            alert=20,
            direction="max",
        )

        cards = [
            build_dashboard_card(
                definition,
                MetricObservation(
                    indicator_id="contrats_ecart_facture",
                    value=value,
                    period="2026-05",
                    source="ComptaScope",
                    proof_ref=f"DOC-{value}",
                ),
                threshold,
                next_action="Question syndic",
            )
            for value in (5, 12, 25)
        ]

        self.assertEqual([card.status for card in cards], [STATUS_OK, STATUS_ATTENTION, STATUS_ALERT])

    def test_min_direction_threshold_marks_low_values_as_attention_or_alert(self) -> None:
        definition = IndicatorDefinition(
            indicator_id="fonds_travaux_couverture",
            theme="Investissements",
            name="Couverture du fonds travaux",
            unit="%",
        )
        threshold = TargetThreshold(
            indicator_id="fonds_travaux_couverture",
            attention=30,
            alert=15,
            direction="min",
            justification="Plus la couverture est basse, plus le risque est fort.",
        )

        cards = [
            build_dashboard_card(
                definition,
                MetricObservation(
                    indicator_id="fonds_travaux_couverture",
                    value=value,
                    period="2026",
                    source="Budget",
                    proof_ref=f"BUDGET-{value}",
                ),
                threshold,
            )
            for value in (45, 25, 10)
        ]

        self.assertEqual([card.status for card in cards], [STATUS_OK, STATUS_ATTENTION, STATUS_ALERT])

    def test_ambiguous_thresholds_are_not_reported_as_ok(self) -> None:
        definition = IndicatorDefinition(
            indicator_id="eau_derive_mensuelle",
            theme="Consommations",
            name="Derive mensuelle eau",
            unit="%",
        )
        inverted_threshold = TargetThreshold(
            indicator_id="eau_derive_mensuelle",
            attention=20,
            alert=10,
            direction="max",
            justification="Seuils inverses par erreur de saisie.",
        )

        card = build_dashboard_card(
            definition,
            MetricObservation(
                indicator_id="eau_derive_mensuelle",
                value=12,
                period="2026-05",
                source="FactureOps",
                proof_ref="FACT-EAU-2026-05",
            ),
            inverted_threshold,
        )

        self.assertEqual(card.status, STATUS_VERIFY)
        self.assertIn("Verifier", card.next_action)

    def test_cards_do_not_mix_two_vaults_or_instances(self) -> None:
        definitions = [
            {
                "indicator_id": "demandes_retard",
                "theme": "Demandes",
                "name": "Demandes en retard",
                "vault_id": "vault-a",
                "instance_id": "inst-a",
            },
            {
                "indicator_id": "demandes_retard",
                "theme": "Demandes",
                "name": "Demandes en retard autre copro",
                "vault_id": "vault-b",
                "instance_id": "inst-b",
            },
        ]
        thresholds = [
            {"indicator_id": "demandes_retard", "attention": "2", "alert": "4", "vault_id": "vault-a", "instance_id": "inst-a"},
            {"indicator_id": "demandes_retard", "attention": "20", "alert": "40", "vault_id": "vault-b", "instance_id": "inst-b"},
        ]
        observations = [
            {
                "indicator_id": "demandes_retard",
                "value": "5",
                "period": "2026-05",
                "source": "SyndicOps",
                "proof_ref": "DOC-A",
                "vault_id": "vault-a",
                "instance_id": "inst-a",
                "scope_id": "bat-a",
            },
            {
                "indicator_id": "demandes_retard",
                "value": "5",
                "period": "2026-05",
                "source": "SyndicOps",
                "proof_ref": "DOC-B",
                "vault_id": "vault-b",
                "instance_id": "inst-b",
                "scope_id": "bat-b",
            },
        ]

        cards = build_dashboard_cards(definitions, observations, thresholds)

        self.assertEqual([(card.vault_id, card.instance_id, card.scope_id) for card in cards], [("vault-a", "inst-a", "bat-a"), ("vault-b", "inst-b", "bat-b")])
        self.assertEqual(cards[0].status, STATUS_ALERT)
        self.assertEqual(cards[1].status, STATUS_OK)
        self.assertEqual(cards[0].title, "Demandes en retard")
        self.assertEqual(cards[1].title, "Demandes en retard autre copro")

    def test_context_mismatch_raises_instead_of_crossing_scopes(self) -> None:
        definition = IndicatorDefinition(
            indicator_id="contrats_reconduction",
            theme="Contrats",
            name="Contrats en reconduction proche",
            vault_id="vault-a",
            instance_id="inst-a",
        )
        observation = MetricObservation(
            indicator_id="contrats_reconduction",
            value=1,
            period="2026-05",
            source="Contrats",
            proof_ref="CONTRAT-1",
            vault_id="vault-b",
            instance_id="inst-a",
        )

        with self.assertRaises(ValueError):
            build_dashboard_card(definition, observation)

    def test_novice_card_has_required_guardrails_and_next_action(self) -> None:
        definition = IndicatorDefinition(
            indicator_id="travaux_reception_retard",
            theme="Travaux",
            name="Retard de reception travaux",
            formula="jours depuis date prevue",
            unit="jours",
            periodicity="mensuel",
            access_level="copro",
        )
        observation = MetricObservation(
            indicator_id="travaux_reception_retard",
            value=18,
            period="2026-05",
            source="PV AG et action log",
            proof_ref="PV-2026-04;PHOTO-RESERVE-1",
            data_quality="verified",
            vault_id="vault-a",
            instance_id="inst-a",
            scope_id="chauffage",
        )
        threshold = TargetThreshold(indicator_id="travaux_reception_retard", attention=7, alert=15)

        card = build_dashboard_card(definition, observation, threshold)

        self.assertEqual(card.theme, "Travaux")
        self.assertEqual(card.period, "2026-05")
        self.assertEqual(card.source, "PV AG et action log")
        self.assertEqual(card.proof_ref, "PV-2026-04;PHOTO-RESERVE-1")
        self.assertEqual(card.confidence, "haute")
        self.assertTrue(card.next_action)
        self.assertIn("Retard de reception travaux", card.novice_reading)
        self.assertTrue(validate_dashboard_card(card))

    def test_missing_source_is_visible_and_keeps_language_stable(self) -> None:
        definition = IndicatorDefinition(
            indicator_id="risque_piece_manquante",
            theme="Risques/contentieux",
            name="Piece manquante critique",
        )
        observation = MetricObservation(
            indicator_id="risque_piece_manquante",
            value="assignation absente",
            period="2026-05",
            source="",
            proof_ref="DOS-CONTENTIEUX-1",
        )

        card = build_dashboard_card(definition, observation)

        self.assertEqual(card.status, STATUS_VERIFY)
        self.assertEqual(card.source, "source manquante")
        self.assertTrue(validate_dashboard_card(card))
        self.assertNotIn("conforme", card.novice_reading.lower())

    def test_csv_helpers_normalize_rows_without_heavy_dependencies(self) -> None:
        definitions = definitions_from_csv("indicator_id,theme,name,unit\nenergie_derive,Consommations,Derive electricite,%\n")
        observations = observations_from_csv(
            "indicator_id,value,period,source,proof_ref,vault_id\nenergie_derive,\"12,5\",2026-05,FactureOps,DOC-EDF,vault-a\n"
        )
        thresholds = thresholds_from_csv("indicator_id,attention,alert\nenergie_derive,10,20\n")

        card = build_dashboard_card(definitions[0], observations[0], thresholds[0])

        self.assertEqual(card.value, 12.5)
        self.assertEqual(card.status, STATUS_ATTENTION)
        self.assertEqual(card.vault_id, "vault-a")


if __name__ == "__main__":
    unittest.main()
