from __future__ import annotations

import unittest

from coproscope.modules.suggestionops import (
    OUTCOME_ACTION,
    OUTCOME_EXPORT,
    OUTCOME_INDICATOR,
    OUTCOME_POINT,
    OUTCOME_REQUEST,
    REVIEW_ACCEPTED,
    REVIEW_NEEDS_MORE_PROOF,
    SUGGESTION_STATUS_REVIEW,
    ImprovementSuggestion,
    SuggestionReview,
    build_outcome,
    can_transform,
    normalize_review,
    normalize_suggestion,
    normalize_trigger,
    outcome_payload,
    suggestion_from_trigger,
    suggestions_from_csv,
    validate_suggestion,
)


class SuggestionOpsTests(unittest.TestCase):
    def test_normalizes_sourced_suggestion_with_required_fields(self) -> None:
        suggestion = normalize_suggestion(
            {
                "titre": "Rendre visibles les demandes syndic en retard",
                "pourquoi": "Trois demandes restent sans reponse avant le conseil syndical.",
                "preuve": "REG-DEMANDES-2026-05",
                "source": "SyndicOps",
                "prochaine_action": "Relire les demandes et choisir celles a relancer.",
                "impact": "fort",
                "effort": "faible",
                "confiance": "haute",
                "public": "conseil_syndical",
            }
        )

        self.assertEqual(suggestion.status, SUGGESTION_STATUS_REVIEW)
        self.assertEqual(suggestion.proof, "REG-DEMANDES-2026-05")
        self.assertEqual(suggestion.source, "SyndicOps")
        self.assertEqual(suggestion.confidence, "haute")
        self.assertTrue(validate_suggestion(suggestion))

    def test_suggestion_without_source_or_proof_is_rejected(self) -> None:
        suggestion = ImprovementSuggestion(
            suggestion_id="SUG-MANUAL",
            title="Suggestion sans preuve",
            why="Cela semble utile.",
            proof="",
            source="",
            next_action="Faire quelque chose.",
            impact="moyen",
            effort="moyen",
            confidence="faible",
            public="conseil_syndical",
        )

        with self.assertRaises(ValueError):
            validate_suggestion(suggestion)

    def test_trigger_builds_review_only_suggestion_never_automatic_decision(self) -> None:
        trigger = normalize_trigger(
            {
                "kind": "piece_manquante",
                "source": "DocOps",
                "preuve": "MATRICE-PREUVES#assurance",
                "pourquoi": "L'attestation assurance n'est pas rattachee au coffre.",
                "confiance": "haute",
            }
        )

        suggestion = suggestion_from_trigger(
            trigger,
            title="Demander l'attestation assurance",
            next_action="Verifier avec le syndic si la piece existe.",
            impact="fort",
            effort="faible",
        )

        self.assertEqual(suggestion.status, SUGGESTION_STATUS_REVIEW)
        self.assertEqual(suggestion.trigger_id, trigger.trigger_id)
        self.assertEqual(suggestion.confidence, "haute")
        self.assertIn(OUTCOME_REQUEST, suggestion.transformations)

    def test_transform_requires_accepted_human_review(self) -> None:
        suggestion = normalize_suggestion(
            {
                "title": "Relancer le syndic sur la facture ascenseur",
                "why": "Ecart entre contrat et facture detecte.",
                "proof": "FACT-ASC-2026-04;CONTRAT-ASC",
                "source": "ComptaScope",
                "next_action": "Relire l'ecart puis envoyer une question au syndic.",
                "impact": "moyen",
                "effort": "faible",
                "confidence": "moyenne",
                "public": "commission_comptes",
                "transformations": "demande;action;point",
            }
        )
        pending_review = normalize_review(
            {
                "suggestion_id": suggestion.suggestion_id,
                "reviewer": "Alice",
                "decision": "pending",
                "rationale": "Lecture en cours.",
            }
        )

        self.assertFalse(can_transform(suggestion, pending_review, OUTCOME_REQUEST))
        with self.assertRaises(ValueError):
            build_outcome(suggestion, pending_review, OUTCOME_REQUEST)

        accepted_review = SuggestionReview(
            review_id="REV-1",
            suggestion_id=suggestion.suggestion_id,
            reviewer="Alice",
            decision=REVIEW_ACCEPTED,
            rationale="La piece source est lisible et la question est legitime.",
            selected_outcome_type=OUTCOME_REQUEST,
        )

        outcome = build_outcome(suggestion, accepted_review)

        self.assertEqual(outcome.outcome_type, OUTCOME_REQUEST)
        self.assertEqual(outcome.payload["object_type"], "demande")
        self.assertEqual(outcome.payload["origin_suggestion_id"], suggestion.suggestion_id)

    def test_review_needing_more_proof_cannot_transform_even_with_reviewer(self) -> None:
        suggestion = normalize_suggestion(
            {
                "title": "Creer un indicateur eau",
                "why": "La consommation augmente mais la periode source est incomplete.",
                "proof": "FACT-EAU-2026-05",
                "source": "IndicatorOps",
                "next_action": "Verifier les factures des trois derniers mois.",
                "impact": "moyen",
                "effort": "moyen",
                "confidence": "a_verifier",
                "public": "conseil_syndical",
                "transformations": "indicateur",
            }
        )
        review = SuggestionReview(
            review_id="REV-2",
            suggestion_id=suggestion.suggestion_id,
            reviewer="Bob",
            decision=REVIEW_NEEDS_MORE_PROOF,
            rationale="Il manque deux factures pour conclure.",
            selected_outcome_type=OUTCOME_INDICATOR,
        )

        self.assertFalse(can_transform(suggestion, review, OUTCOME_INDICATOR))

    def test_all_expected_outcome_payloads_stay_actionable_and_sourced(self) -> None:
        suggestion = normalize_suggestion(
            {
                "title": "Clarifier la diffusion du pack passation",
                "why": "Le pack memoire contient des documents sensibles.",
                "proof": "PRIVACY-REPORT-2026-05",
                "source": "PrivacyOps",
                "next_action": "Faire une revue de diffusion avant export.",
                "impact": "fort",
                "effort": "moyen",
                "confidence": "haute",
                "public": "conseil_syndical",
            }
        )

        for outcome_type in [OUTCOME_ACTION, OUTCOME_REQUEST, OUTCOME_POINT, OUTCOME_INDICATOR, OUTCOME_EXPORT]:
            payload = outcome_payload(suggestion, outcome_type)
            self.assertEqual(payload["proof"], "PRIVACY-REPORT-2026-05")
            self.assertEqual(payload["source"], "PrivacyOps")
            self.assertEqual(payload["next_action"], "Faire une revue de diffusion avant export.")

    def test_csv_helper_keeps_lightweight_aliases(self) -> None:
        rows = suggestions_from_csv(
            "titre,pourquoi,preuve,source,prochaine_action,impact,effort,confiance,public\n"
            "Suivre les espaces verts,Cout par passage absent,FACT-JARDIN-2025,FactureOps,"
            "Creer un point de controle,faible,faible,moyenne,commission_espaces_verts\n"
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].title, "Suivre les espaces verts")
        self.assertEqual(rows[0].next_action, "Creer un point de controle")
        self.assertTrue(validate_suggestion(rows[0]))


if __name__ == "__main__":
    unittest.main()
