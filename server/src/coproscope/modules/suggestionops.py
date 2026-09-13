from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from typing import Any


SUGGESTION_STATUS_REVIEW = "a_revoir"
SUGGESTION_STATUS_DISMISSED = "ecartee"
SUGGESTION_STATUS_TRANSFORMED = "transformee"
SUGGESTION_STATUSES = frozenset(
    {
        SUGGESTION_STATUS_REVIEW,
        SUGGESTION_STATUS_DISMISSED,
        SUGGESTION_STATUS_TRANSFORMED,
    }
)

REVIEW_PENDING = "pending"
REVIEW_ACCEPTED = "accepted"
REVIEW_REJECTED = "rejected"
REVIEW_NEEDS_MORE_PROOF = "needs_more_proof"
REVIEW_DECISIONS = frozenset(
    {
        REVIEW_PENDING,
        REVIEW_ACCEPTED,
        REVIEW_REJECTED,
        REVIEW_NEEDS_MORE_PROOF,
    }
)

OUTCOME_ACTION = "action"
OUTCOME_REQUEST = "demande"
OUTCOME_POINT = "point"
OUTCOME_INDICATOR = "indicateur"
OUTCOME_EXPORT = "export"
OUTCOME_TYPES = frozenset(
    {
        OUTCOME_ACTION,
        OUTCOME_REQUEST,
        OUTCOME_POINT,
        OUTCOME_INDICATOR,
        OUTCOME_EXPORT,
    }
)

DEFAULT_TRANSFORMATIONS = (
    OUTCOME_ACTION,
    OUTCOME_REQUEST,
    OUTCOME_POINT,
    OUTCOME_INDICATOR,
    OUTCOME_EXPORT,
)

WHY_FIELDS = ("why", "pourquoi", "reason", "raison", "motif")
PROOF_FIELDS = ("proof", "preuve", "proof_ref", "proof_refs", "evidence", "source_proof")
SOURCE_FIELDS = ("source", "origin", "origine", "source_ref", "document_source", "registre")
ACTION_FIELDS = ("next_action", "prochaine_action", "action", "action_attendue", "recommended_action")
PUBLIC_FIELDS = ("public", "audience", "diffusion", "visibility", "visibilite")
CONFIDENCE_FIELDS = ("confidence", "confiance", "certainty", "certitude")
IMPACT_FIELDS = ("impact", "benefit", "benefice", "gain")
EFFORT_FIELDS = ("effort", "complexity", "complexite", "charge")


@dataclass(frozen=True)
class SuggestionTrigger:
    trigger_id: str
    source: str
    proof: str
    why: str
    kind: str = ""
    object_ref: str = ""
    detected_at: str = ""
    confidence: str = "moyenne"
    public: str = "conseil_syndical"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ImprovementSuggestion:
    suggestion_id: str
    title: str
    why: str
    proof: str
    source: str
    next_action: str
    impact: str
    effort: str
    confidence: str
    public: str
    trigger_id: str = ""
    status: str = SUGGESTION_STATUS_REVIEW
    transformations: tuple[str, ...] = DEFAULT_TRANSFORMATIONS
    notes: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SuggestionReview:
    review_id: str
    suggestion_id: str
    reviewer: str
    decision: str = REVIEW_PENDING
    rationale: str = ""
    reviewed_at: str = ""
    selected_outcome_type: str = ""
    public: str = ""


@dataclass(frozen=True)
class SuggestionOutcome:
    outcome_id: str
    suggestion_id: str
    review_id: str
    outcome_type: str
    title: str
    why: str
    proof: str
    source: str
    next_action: str
    impact: str
    effort: str
    confidence: str
    public: str
    payload: dict[str, str] = field(default_factory=dict)


def normalize_trigger(row: Mapping[str, Any]) -> SuggestionTrigger:
    row_data = dict(row)
    source = _first_text(row_data, SOURCE_FIELDS)
    proof = _first_text(row_data, PROOF_FIELDS)
    why = _first_text(row_data, WHY_FIELDS)
    trigger_id = _first_text(row_data, ("trigger_id", "id", "key")) or _stable_id("TRG", source, proof, why)
    metadata = _metadata(
        row_data,
        {
            "trigger_id",
            "id",
            "key",
            "kind",
            "type",
            "object_ref",
            "object_id",
            "detected_at",
            *SOURCE_FIELDS,
            *PROOF_FIELDS,
            *WHY_FIELDS,
            *CONFIDENCE_FIELDS,
            *PUBLIC_FIELDS,
        },
    )
    return SuggestionTrigger(
        trigger_id=trigger_id,
        source=source,
        proof=proof,
        why=why,
        kind=_first_text(row_data, ("kind", "type")),
        object_ref=_first_text(row_data, ("object_ref", "object_id", "doc_id", "piece_ref")),
        detected_at=_first_text(row_data, ("detected_at", "date", "created_at")),
        confidence=_normalize_confidence(_first_text(row_data, CONFIDENCE_FIELDS) or "moyenne"),
        public=_first_text(row_data, PUBLIC_FIELDS) or "conseil_syndical",
        metadata=metadata,
    )


def normalize_suggestion(row: Mapping[str, Any]) -> ImprovementSuggestion:
    row_data = dict(row)
    why = _first_text(row_data, WHY_FIELDS)
    proof = _first_text(row_data, PROOF_FIELDS)
    source = _first_text(row_data, SOURCE_FIELDS)
    title = _first_text(row_data, ("title", "titre", "name", "nom", "subject", "sujet"))
    next_action = _first_text(row_data, ACTION_FIELDS)
    suggestion_id = _first_text(row_data, ("suggestion_id", "id", "key")) or _stable_id(
        "SUG",
        source,
        proof,
        title,
        why,
    )
    status = _normalize_status(_first_text(row_data, ("status", "statut")))
    transformations = _normalize_transformations(
        _first_text(row_data, ("transformations", "outcomes", "transformations_possibles"))
    )
    metadata = _metadata(
        row_data,
        {
            "suggestion_id",
            "id",
            "key",
            "title",
            "titre",
            "name",
            "nom",
            "subject",
            "sujet",
            "trigger_id",
            "status",
            "statut",
            "notes",
            "transformations",
            "outcomes",
            "transformations_possibles",
            *WHY_FIELDS,
            *PROOF_FIELDS,
            *SOURCE_FIELDS,
            *ACTION_FIELDS,
            *IMPACT_FIELDS,
            *EFFORT_FIELDS,
            *CONFIDENCE_FIELDS,
            *PUBLIC_FIELDS,
        },
    )
    return ImprovementSuggestion(
        suggestion_id=suggestion_id,
        title=title or _default_title(source, why),
        why=why,
        proof=proof,
        source=source,
        next_action=next_action,
        impact=_first_text(row_data, IMPACT_FIELDS),
        effort=_first_text(row_data, EFFORT_FIELDS),
        confidence=_normalize_confidence(_first_text(row_data, CONFIDENCE_FIELDS)),
        public=_first_text(row_data, PUBLIC_FIELDS),
        trigger_id=_first_text(row_data, ("trigger_id",)),
        status=status,
        transformations=transformations,
        notes=_first_text(row_data, ("notes", "commentaire", "comment")),
        metadata=metadata,
    )


def suggestion_from_trigger(
    trigger: SuggestionTrigger | Mapping[str, Any],
    *,
    title: str = "",
    next_action: str = "",
    impact: str = "",
    effort: str = "",
    public: str = "",
    transformations: Iterable[str] = DEFAULT_TRANSFORMATIONS,
) -> ImprovementSuggestion:
    normalized = trigger if isinstance(trigger, SuggestionTrigger) else normalize_trigger(trigger)
    suggestion = ImprovementSuggestion(
        suggestion_id=_stable_id("SUG", normalized.source, normalized.proof, normalized.why, title),
        title=_cell(title) or _default_title(normalized.source, normalized.why),
        why=normalized.why,
        proof=normalized.proof,
        source=normalized.source,
        next_action=_cell(next_action) or "Faire relire la suggestion par un humain avant toute suite.",
        impact=_cell(impact) or "a_qualifier",
        effort=_cell(effort) or "a_qualifier",
        confidence=_normalize_confidence(normalized.confidence),
        public=_cell(public) or normalized.public,
        trigger_id=normalized.trigger_id,
        status=SUGGESTION_STATUS_REVIEW,
        transformations=_normalize_transformations(";".join(transformations)),
        metadata=dict(normalized.metadata),
    )
    validate_suggestion(suggestion)
    return suggestion


def normalize_review(row: Mapping[str, Any]) -> SuggestionReview:
    row_data = dict(row)
    suggestion_id = _first_text(row_data, ("suggestion_id", "id_suggestion"))
    reviewer = _first_text(row_data, ("reviewer", "reviewed_by", "relecteur", "validateur"))
    decision = _normalize_review_decision(_first_text(row_data, ("decision", "status", "statut")))
    return SuggestionReview(
        review_id=_first_text(row_data, ("review_id", "id", "key")) or _stable_id("REV", suggestion_id, reviewer, decision),
        suggestion_id=suggestion_id,
        reviewer=reviewer,
        decision=decision,
        rationale=_first_text(row_data, ("rationale", "motif", "commentaire", "notes")),
        reviewed_at=_first_text(row_data, ("reviewed_at", "date", "created_at")),
        selected_outcome_type=_normalize_outcome_type(_first_text(row_data, ("selected_outcome_type", "outcome_type", "type_sortie"))),
        public=_first_text(row_data, PUBLIC_FIELDS),
    )


def validate_trigger(trigger: SuggestionTrigger) -> bool:
    _require_fields(trigger, ("source", "proof", "why"))
    return True


def validate_suggestion(suggestion: ImprovementSuggestion) -> bool:
    _require_fields(
        suggestion,
        (
            "suggestion_id",
            "title",
            "why",
            "proof",
            "source",
            "next_action",
            "impact",
            "effort",
            "confidence",
            "public",
        ),
    )
    if suggestion.status not in SUGGESTION_STATUSES:
        raise ValueError(f"Unsupported suggestion status: {suggestion.status}")
    unsupported = [item for item in suggestion.transformations if item not in OUTCOME_TYPES]
    if unsupported:
        raise ValueError(f"Unsupported transformation type: {', '.join(unsupported)}")
    return True


def validate_review(review: SuggestionReview, suggestion: ImprovementSuggestion | None = None) -> bool:
    _require_fields(review, ("review_id", "suggestion_id"))
    if suggestion and review.suggestion_id != suggestion.suggestion_id:
        raise ValueError("review and suggestion ids must match")
    if review.decision not in REVIEW_DECISIONS:
        raise ValueError(f"Unsupported review decision: {review.decision}")
    if review.decision != REVIEW_PENDING:
        _require_fields(review, ("reviewer", "rationale"))
    return True


def can_transform(suggestion: ImprovementSuggestion, review: SuggestionReview, outcome_type: str) -> bool:
    validate_suggestion(suggestion)
    validate_review(review, suggestion)
    normalized_type = _normalize_outcome_type(outcome_type)
    return (
        normalized_type in suggestion.transformations
        and review.decision == REVIEW_ACCEPTED
        and bool(_cell(review.reviewer))
        and bool(_cell(review.rationale))
    )


def build_outcome(
    suggestion: ImprovementSuggestion,
    review: SuggestionReview,
    outcome_type: str | None = None,
) -> SuggestionOutcome:
    normalized_type = _normalize_outcome_type(outcome_type or review.selected_outcome_type)
    if normalized_type not in OUTCOME_TYPES:
        raise ValueError(f"Unsupported outcome type: {outcome_type or review.selected_outcome_type}")
    if not can_transform(suggestion, review, normalized_type):
        raise ValueError("A suggestion needs an accepted human review before transformation")

    payload = outcome_payload(suggestion, normalized_type)
    return SuggestionOutcome(
        outcome_id=_stable_id("OUT", suggestion.suggestion_id, review.review_id, normalized_type),
        suggestion_id=suggestion.suggestion_id,
        review_id=review.review_id,
        outcome_type=normalized_type,
        title=suggestion.title,
        why=suggestion.why,
        proof=suggestion.proof,
        source=suggestion.source,
        next_action=suggestion.next_action,
        impact=suggestion.impact,
        effort=suggestion.effort,
        confidence=suggestion.confidence,
        public=review.public or suggestion.public,
        payload=payload,
    )


def outcome_payload(suggestion: ImprovementSuggestion, outcome_type: str) -> dict[str, str]:
    normalized_type = _normalize_outcome_type(outcome_type)
    if normalized_type not in OUTCOME_TYPES:
        raise ValueError(f"Unsupported outcome type: {outcome_type}")
    base = {
        "title": suggestion.title,
        "why": suggestion.why,
        "proof": suggestion.proof,
        "source": suggestion.source,
        "next_action": suggestion.next_action,
        "impact": suggestion.impact,
        "effort": suggestion.effort,
        "confidence": suggestion.confidence,
        "public": suggestion.public,
        "origin_suggestion_id": suggestion.suggestion_id,
    }
    if normalized_type == OUTCOME_ACTION:
        base.update({"object_type": "action", "status": "todo", "proof_expected": suggestion.proof})
    elif normalized_type == OUTCOME_REQUEST:
        base.update({"object_type": "demande", "status": "todo", "expected_piece": suggestion.proof})
    elif normalized_type == OUTCOME_POINT:
        base.update({"object_type": "point", "status": "a_qualifier"})
    elif normalized_type == OUTCOME_INDICATOR:
        base.update({"object_type": "indicateur", "period": "", "unit": "", "threshold": ""})
    elif normalized_type == OUTCOME_EXPORT:
        base.update({"object_type": "export", "diffusion_review": "required"})
    return base


def normalize_suggestions(rows: Iterable[Mapping[str, Any]]) -> list[ImprovementSuggestion]:
    return [normalize_suggestion(row) for row in rows]


def rows_from_csv(text: str) -> list[dict[str, str]]:
    if not text.strip():
        return []
    return [dict(row) for row in csv.DictReader(io.StringIO(text))]


def suggestions_from_csv(text: str) -> list[ImprovementSuggestion]:
    return normalize_suggestions(rows_from_csv(text))


def suggestion_to_dict(suggestion: ImprovementSuggestion) -> dict[str, Any]:
    return asdict(suggestion)


def review_to_dict(review: SuggestionReview) -> dict[str, Any]:
    return asdict(review)


def outcome_to_dict(outcome: SuggestionOutcome) -> dict[str, Any]:
    return asdict(outcome)


def _require_fields(item: Any, field_names: Iterable[str]) -> None:
    missing = [field_name for field_name in field_names if not _cell(getattr(item, field_name, ""))]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def _normalize_status(value: str) -> str:
    text = _token(value)
    if text in {"dismissed", "ecarte", "ecartee", "rejected"}:
        return SUGGESTION_STATUS_DISMISSED
    if text in {"transformed", "transforme", "transformee"}:
        return SUGGESTION_STATUS_TRANSFORMED
    return SUGGESTION_STATUS_REVIEW


def _normalize_review_decision(value: str) -> str:
    text = _token(value)
    if text in {"accepted", "accept", "accepte", "approuve", "approved"}:
        return REVIEW_ACCEPTED
    if text in {"rejected", "reject", "refuse", "ecarte", "ecartee"}:
        return REVIEW_REJECTED
    if text in {"needs_more_proof", "preuve", "a_completer", "more_proof"}:
        return REVIEW_NEEDS_MORE_PROOF
    return REVIEW_PENDING


def _normalize_outcome_type(value: str) -> str:
    text = _token(value)
    aliases = {
        "request": OUTCOME_REQUEST,
        "demande": OUTCOME_REQUEST,
        "syndic_request": OUTCOME_REQUEST,
        "indicator": OUTCOME_INDICATOR,
        "indicateur": OUTCOME_INDICATOR,
        "metric": OUTCOME_INDICATOR,
        "action": OUTCOME_ACTION,
        "point": OUTCOME_POINT,
        "export": OUTCOME_EXPORT,
    }
    return aliases.get(text, text)


def _normalize_transformations(value: str) -> tuple[str, ...]:
    if not _cell(value):
        return DEFAULT_TRANSFORMATIONS
    result: list[str] = []
    for raw in re.split(r"[;,|]", value):
        normalized = _normalize_outcome_type(raw)
        if normalized and normalized not in result:
            result.append(normalized)
    return tuple(result) or DEFAULT_TRANSFORMATIONS


def _normalize_confidence(value: str) -> str:
    text = _token(value)
    if text in {"high", "haute", "forte", "verified", "verifie", "verifiee"}:
        return "haute"
    if text in {"low", "faible", "incomplete", "incomplet"}:
        return "faible"
    if text in {"verify", "a_verifier", "unknown", "incertain"}:
        return "a_verifier"
    return "moyenne"


def _metadata(row: Mapping[str, Any], reserved: set[str]) -> dict[str, str]:
    normalized_reserved = {_token(field) for field in reserved}
    metadata: dict[str, str] = {}
    for key, value in row.items():
        key_text = _cell(key)
        value_text = _cell(value)
        if key_text and value_text and _token(key_text) not in normalized_reserved:
            metadata[key_text] = value_text
    return metadata


def _first_text(row: Mapping[str, Any], fields: Iterable[str]) -> str:
    for field_name in fields:
        value = _cell(row.get(field_name))
        if value:
            return value
    return ""


def _default_title(source: str, why: str) -> str:
    if source and why:
        return f"Amelioration candidate depuis {source}: {why[:80]}"
    if why:
        return f"Amelioration candidate: {why[:80]}"
    return "Amelioration candidate"


def _stable_id(prefix: str, *parts: str) -> str:
    material = "|".join(_cell(part) for part in parts if _cell(part)) or prefix
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12].upper()
    readable = re.sub(r"[^A-Za-z0-9]+", "-", material).strip("-").upper()[:36]
    return f"{prefix}-{readable}-{digest}" if readable else f"{prefix}-{digest}"


def _token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _cell(value).lower()).strip("_")


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True, ensure_ascii=True)
    return str(value).strip()
