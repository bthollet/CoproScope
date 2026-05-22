from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from coproscope.modules.suggestionops import (
    OUTCOME_ACTION,
    OUTCOME_EXPORT,
    OUTCOME_INDICATOR,
    OUTCOME_POINT,
    OUTCOME_REQUEST,
    REVIEW_ACCEPTED,
    SUGGESTION_STATUS_REVIEW,
    ImprovementSuggestion,
    SuggestionReview,
    can_transform,
    normalize_review,
    normalize_suggestion,
)


CARD_DESTINATIONS = (
    OUTCOME_ACTION,
    OUTCOME_REQUEST,
    OUTCOME_POINT,
    OUTCOME_INDICATOR,
    OUTCOME_EXPORT,
)

DESTINATION_LABELS = {
    OUTCOME_ACTION: "Action",
    OUTCOME_REQUEST: "Demande syndic",
    OUTCOME_POINT: "Point de suivi",
    OUTCOME_INDICATOR: "Indicateur",
    OUTCOME_EXPORT: "Export",
}


@dataclass(frozen=True)
class SuggestionUICard:
    card_id: str
    suggestion_id: str
    review_id: str
    title: str
    why: str
    proof: str
    source: str
    evidence: str
    next_action: str
    diffusion: str
    confidence: str
    effort: str
    destination: str
    destination_label: str
    available_destinations: tuple[str, ...]
    automatic_effect: bool = False


def build_suggestion_cards(
    suggestions: Iterable[ImprovementSuggestion | Mapping[str, Any]],
    reviews: Iterable[SuggestionReview | Mapping[str, Any]],
) -> list[SuggestionUICard]:
    """Return cockpit-ready cards without creating business outcomes."""

    reviews_by_suggestion = _accepted_reviews_by_suggestion(reviews)
    cards: list[SuggestionUICard] = []
    for raw_suggestion in suggestions:
        suggestion = _coerce_suggestion(raw_suggestion)
        if not _is_card_candidate(suggestion):
            continue

        for review in reviews_by_suggestion.get(suggestion.suggestion_id, ()):
            card = suggestion_card_from_review(suggestion, review)
            if card is not None:
                cards.append(card)
                break

    return cards


def suggestion_card_from_review(
    suggestion: ImprovementSuggestion | Mapping[str, Any],
    review: SuggestionReview | Mapping[str, Any],
) -> SuggestionUICard | None:
    """Build one UI card when a sourced suggestion has an accepted review."""

    normalized_suggestion = _coerce_suggestion(suggestion)
    normalized_review = _coerce_review(review)
    if not _is_card_candidate(normalized_suggestion):
        return None
    if normalized_review.suggestion_id != normalized_suggestion.suggestion_id:
        return None
    if normalized_review.decision != REVIEW_ACCEPTED:
        return None

    available_destinations = _available_destinations(normalized_suggestion, normalized_review)
    if not available_destinations:
        return None

    destination = _selected_destination(normalized_review, available_destinations)
    if destination is None:
        return None

    return SuggestionUICard(
        card_id=f"CARD-{normalized_suggestion.suggestion_id}-{normalized_review.review_id}",
        suggestion_id=normalized_suggestion.suggestion_id,
        review_id=normalized_review.review_id,
        title=normalized_suggestion.title,
        why=normalized_suggestion.why,
        proof=normalized_suggestion.proof,
        source=normalized_suggestion.source,
        evidence=_evidence_label(normalized_suggestion),
        next_action=normalized_suggestion.next_action,
        diffusion=normalized_review.public or normalized_suggestion.public,
        confidence=normalized_suggestion.confidence,
        effort=normalized_suggestion.effort,
        destination=destination,
        destination_label=DESTINATION_LABELS[destination],
        available_destinations=available_destinations,
    )


def suggestion_card_to_dict(card: SuggestionUICard) -> dict[str, Any]:
    return asdict(card)


def suggestion_cards_to_dicts(cards: Iterable[SuggestionUICard]) -> list[dict[str, Any]]:
    return [suggestion_card_to_dict(card) for card in cards]


def _accepted_reviews_by_suggestion(
    reviews: Iterable[SuggestionReview | Mapping[str, Any]],
) -> dict[str, list[SuggestionReview]]:
    grouped: dict[str, list[SuggestionReview]] = {}
    for raw_review in reviews:
        review = _coerce_review(raw_review)
        if review.decision != REVIEW_ACCEPTED:
            continue
        grouped.setdefault(review.suggestion_id, []).append(review)
    return grouped


def _available_destinations(
    suggestion: ImprovementSuggestion,
    review: SuggestionReview,
) -> tuple[str, ...]:
    result: list[str] = []
    for destination in CARD_DESTINATIONS:
        if destination not in suggestion.transformations:
            continue
        try:
            if can_transform(suggestion, review, destination):
                result.append(destination)
        except ValueError:
            continue
    return tuple(result)


def _selected_destination(
    review: SuggestionReview,
    available_destinations: tuple[str, ...],
) -> str | None:
    selected = review.selected_outcome_type
    if selected:
        return selected if selected in available_destinations else None
    return available_destinations[0] if available_destinations else None


def _is_card_candidate(suggestion: ImprovementSuggestion) -> bool:
    return (
        suggestion.status == SUGGESTION_STATUS_REVIEW
        and _has_text(suggestion.title)
        and _has_text(suggestion.why)
        and _has_text(suggestion.proof)
        and _has_text(suggestion.source)
        and _has_text(suggestion.next_action)
        and _has_text(suggestion.public)
        and _has_text(suggestion.confidence)
        and _has_text(suggestion.effort)
    )


def _evidence_label(suggestion: ImprovementSuggestion) -> str:
    return f"{suggestion.source} - {suggestion.proof}"


def _coerce_suggestion(value: ImprovementSuggestion | Mapping[str, Any]) -> ImprovementSuggestion:
    if isinstance(value, ImprovementSuggestion):
        return value
    return normalize_suggestion(value)


def _coerce_review(value: SuggestionReview | Mapping[str, Any]) -> SuggestionReview:
    if isinstance(value, SuggestionReview):
        return value
    return normalize_review(value)


def _has_text(value: str) -> bool:
    return bool(str(value).strip())
