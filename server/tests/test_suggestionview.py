from __future__ import annotations

import unittest

from coproscope.modules.suggestionops import (
    OUTCOME_ACTION,
    OUTCOME_EXPORT,
    OUTCOME_INDICATOR,
    OUTCOME_POINT,
    OUTCOME_REQUEST,
    REVIEW_ACCEPTED,
    REVIEW_PENDING,
    SUGGESTION_STATUS_DISMISSED,
    ImprovementSuggestion,
    SuggestionReview,
    normalize_suggestion,
)
from coproscope.modules.suggestionview import (
    CARD_DESTINATIONS,
    build_suggestion_cards,
    suggestion_card_from_review,
    suggestion_card_to_dict,
)


class SuggestionViewTests(unittest.TestCase):
    def test_builds_cockpit_ready_card_from_sourced_accepted_suggestion(self) -> None:
        suggestion = normalize_suggestion(
            {
                "title": "Relancer le syndic sur l'attestation assurance",
                "why": "La piece attendue n'est pas presente dans le coffre.",
                "proof": "MATRICE-PREUVES#assurance",
                "source": "DocOps",
                "next_action": "Verifier la matrice puis preparer une demande au syndic.",
                "impact": "fort",
                "effort": "faible",
                "confidence": "haute",
                "public": "conseil_syndical",
                "transformations": "demande;action;point",
            }
        )
        review = SuggestionReview(
            review_id="REV-ASSURANCE",
            suggestion_id=suggestion.suggestion_id,
            reviewer="Alice",
            decision=REVIEW_ACCEPTED,
            rationale="La matrice cite clairement la piece attendue.",
            selected_outcome_type=OUTCOME_REQUEST,
            public="commission_assurance",
        )

        cards = build_suggestion_cards([suggestion], [review])

        self.assertEqual(len(cards), 1)
        card = cards[0]
        self.assertEqual(card.title, "Relancer le syndic sur l'attestation assurance")
        self.assertEqual(card.why, "La piece attendue n'est pas presente dans le coffre.")
        self.assertEqual(card.proof, "MATRICE-PREUVES#assurance")
        self.assertEqual(card.source, "DocOps")
        self.assertEqual(card.evidence, "DocOps - MATRICE-PREUVES#assurance")
        self.assertEqual(card.next_action, "Verifier la matrice puis preparer une demande au syndic.")
        self.assertEqual(card.diffusion, "commission_assurance")
        self.assertEqual(card.confidence, "haute")
        self.assertEqual(card.effort, "faible")
        self.assertEqual(card.destination, OUTCOME_REQUEST)
        self.assertEqual(card.destination_label, "Demande syndic")
        self.assertEqual(card.available_destinations, (OUTCOME_ACTION, OUTCOME_REQUEST, OUTCOME_POINT))
        self.assertFalse(card.automatic_effect)

    def test_filters_unsourced_or_unaccepted_suggestions(self) -> None:
        accepted = SuggestionReview(
            review_id="REV-OK",
            suggestion_id="SUG-SOURCED",
            reviewer="Alice",
            decision=REVIEW_ACCEPTED,
            rationale="Preuve lisible.",
            selected_outcome_type=OUTCOME_ACTION,
        )
        pending = SuggestionReview(
            review_id="REV-PENDING",
            suggestion_id="SUG-PENDING",
            reviewer="Bob",
            decision=REVIEW_PENDING,
            rationale="En cours.",
            selected_outcome_type=OUTCOME_ACTION,
        )
        sourced = self._suggestion("SUG-SOURCED")
        without_proof = self._suggestion("SUG-NOPROOF", proof="")
        without_source = self._suggestion("SUG-NOSOURCE", source="")
        pending_suggestion = self._suggestion("SUG-PENDING")

        cards = build_suggestion_cards(
            [sourced, without_proof, without_source, pending_suggestion],
            [accepted, pending],
        )

        self.assertEqual([card.suggestion_id for card in cards], ["SUG-SOURCED"])

    def test_does_not_build_card_for_dismissed_suggestion(self) -> None:
        suggestion = self._suggestion("SUG-DISMISSED", status=SUGGESTION_STATUS_DISMISSED)
        review = SuggestionReview(
            review_id="REV-DISMISSED",
            suggestion_id=suggestion.suggestion_id,
            reviewer="Alice",
            decision=REVIEW_ACCEPTED,
            rationale="Ancienne revue.",
            selected_outcome_type=OUTCOME_ACTION,
        )

        self.assertEqual(build_suggestion_cards([suggestion], [review]), [])

    def test_selected_destination_must_be_allowed_by_suggestion(self) -> None:
        suggestion = self._suggestion("SUG-INDICATOR", transformations=(OUTCOME_INDICATOR,))
        review = SuggestionReview(
            review_id="REV-BAD-DESTINATION",
            suggestion_id=suggestion.suggestion_id,
            reviewer="Alice",
            decision=REVIEW_ACCEPTED,
            rationale="Suggestion acceptee mais mauvaise cible.",
            selected_outcome_type=OUTCOME_EXPORT,
        )

        self.assertIsNone(suggestion_card_from_review(suggestion, review))

    def test_defaults_to_first_available_destination_when_review_does_not_select_one(self) -> None:
        suggestion = self._suggestion("SUG-MULTI", transformations=(OUTCOME_POINT, OUTCOME_EXPORT))
        review = SuggestionReview(
            review_id="REV-NO-DESTINATION",
            suggestion_id=suggestion.suggestion_id,
            reviewer="Alice",
            decision=REVIEW_ACCEPTED,
            rationale="Accepte pour affichage cockpit.",
        )

        card = suggestion_card_from_review(suggestion, review)

        self.assertIsNotNone(card)
        self.assertEqual(card.destination, OUTCOME_POINT)
        self.assertEqual(card.available_destinations, (OUTCOME_POINT, OUTCOME_EXPORT))

    def test_dict_export_stays_ui_only_and_serializable(self) -> None:
        suggestion = self._suggestion("SUG-DICT", transformations=CARD_DESTINATIONS)
        review = SuggestionReview(
            review_id="REV-DICT",
            suggestion_id=suggestion.suggestion_id,
            reviewer="Alice",
            decision=REVIEW_ACCEPTED,
            rationale="Carte prete pour affichage.",
            selected_outcome_type=OUTCOME_EXPORT,
        )

        card = suggestion_card_from_review(suggestion, review)
        self.assertIsNotNone(card)
        data = suggestion_card_to_dict(card)

        self.assertEqual(data["destination"], OUTCOME_EXPORT)
        self.assertEqual(data["automatic_effect"], False)
        self.assertNotIn("outcome_id", data)
        self.assertNotIn("payload", data)

    def _suggestion(
        self,
        suggestion_id: str,
        *,
        proof: str = "PREUVE-1",
        source: str = "SuggestionOpsTest",
        status: str = "a_revoir",
        transformations: tuple[str, ...] = (OUTCOME_ACTION,),
    ) -> ImprovementSuggestion:
        return ImprovementSuggestion(
            suggestion_id=suggestion_id,
            title=f"Suggestion {suggestion_id}",
            why="Un point utile merite une revue humaine.",
            proof=proof,
            source=source,
            next_action="Relire la preuve et choisir une suite.",
            impact="moyen",
            effort="faible",
            confidence="moyenne",
            public="conseil_syndical",
            status=status,
            transformations=transformations,
        )


if __name__ == "__main__":
    unittest.main()
