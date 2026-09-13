from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from typing import Any


STATUS_OK = "OK"
STATUS_ATTENTION = "attention"
STATUS_ALERT = "alerte"
STATUS_VERIFY = "a_verifier"
STATUS_VALUES = frozenset({STATUS_OK, STATUS_ATTENTION, STATUS_ALERT, STATUS_VERIFY})

CONTEXT_FIELDS = ("vault_id", "instance_id", "scope_id")
PROOF_FIELDS = ("proof_ref", "proof_refs", "proof_doc_id", "proof_doc_ids", "preuve", "source_proof")
SOURCE_FIELDS = ("source", "source_id", "document_source", "registre", "origin")
PERIOD_FIELDS = ("period", "periode", "month", "mois", "date", "occurred_at")
ACTION_FIELDS = ("next_action", "prochaine_action", "action", "action_attendue", "recommended_action")


@dataclass(frozen=True)
class IndicatorDefinition:
    indicator_id: str
    theme: str
    name: str
    formula: str = ""
    unit: str = ""
    periodicity: str = ""
    access_level: str = ""
    vault_id: str = ""
    instance_id: str = ""
    scope_id: str = ""


@dataclass(frozen=True)
class MetricObservation:
    indicator_id: str
    value: float | str
    period: str
    source: str
    proof_ref: str
    data_quality: str = ""
    vault_id: str = ""
    instance_id: str = ""
    scope_id: str = ""
    theme: str = ""
    label: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TargetThreshold:
    indicator_id: str
    target: float | None = None
    attention: float | None = None
    alert: float | None = None
    direction: str = "max"
    justification: str = ""
    vault_id: str = ""
    instance_id: str = ""
    scope_id: str = ""


@dataclass(frozen=True)
class DashboardCard:
    indicator_id: str
    theme: str
    title: str
    period: str
    status: str
    value: float | str
    unit: str
    source: str
    proof_ref: str
    confidence: str
    next_action: str
    novice_reading: str = ""
    trend: str = ""
    probable_cause: str = ""
    vault_id: str = ""
    instance_id: str = ""
    scope_id: str = ""


@dataclass(frozen=True)
class ManagementQuestion:
    question_id: str
    indicator_id: str
    audience: str
    question: str
    next_action: str = ""
    due_at: str = ""
    source: str = ""
    proof_ref: str = ""
    confidence: str = ""
    vault_id: str = ""
    instance_id: str = ""
    scope_id: str = ""


def normalize_indicator_definition(row: Mapping[str, Any]) -> IndicatorDefinition:
    row_data = dict(row)
    return IndicatorDefinition(
        indicator_id=_first_text(row_data, ("indicator_id", "id", "code", "key")),
        theme=_first_text(row_data, ("theme", "thematique")),
        name=_first_text(row_data, ("name", "nom", "label", "title")),
        formula=_first_text(row_data, ("formula", "formule")),
        unit=_first_text(row_data, ("unit", "unite")),
        periodicity=_first_text(row_data, ("periodicity", "periodicite")),
        access_level=_first_text(row_data, ("access_level", "niveau_acces", "access")),
        vault_id=_first_text(row_data, ("vault_id",)),
        instance_id=_first_text(row_data, ("instance_id",)),
        scope_id=_first_text(row_data, ("scope_id", "perimetre")),
    )


def normalize_metric_observation(row: Mapping[str, Any]) -> MetricObservation:
    row_data = dict(row)
    metadata = {
        _cell(key): _cell(value)
        for key, value in row_data.items()
        if _cell(key)
        and _cell(value)
        and _cell(key)
        not in {
            "indicator_id",
            "id",
            "code",
            "key",
            "value",
            "valeur",
            "metric_value",
            "data_quality",
            "qualite_donnees",
            "theme",
            "label",
            *CONTEXT_FIELDS,
            *PROOF_FIELDS,
            *SOURCE_FIELDS,
            *PERIOD_FIELDS,
        }
    }
    return MetricObservation(
        indicator_id=_first_text(row_data, ("indicator_id", "id", "code", "key")),
        value=_number_or_text(_first_text(row_data, ("value", "valeur", "metric_value"))),
        period=_first_text(row_data, PERIOD_FIELDS),
        source=_first_text(row_data, SOURCE_FIELDS),
        proof_ref=_first_text(row_data, PROOF_FIELDS),
        data_quality=_first_text(row_data, ("data_quality", "qualite_donnees", "quality")),
        vault_id=_first_text(row_data, ("vault_id",)),
        instance_id=_first_text(row_data, ("instance_id",)),
        scope_id=_first_text(row_data, ("scope_id", "perimetre")),
        theme=_first_text(row_data, ("theme", "thematique")),
        label=_first_text(row_data, ("label", "name", "nom", "title")),
        metadata=metadata,
    )


def normalize_target_threshold(row: Mapping[str, Any]) -> TargetThreshold:
    row_data = dict(row)
    return TargetThreshold(
        indicator_id=_first_text(row_data, ("indicator_id", "id", "code", "key")),
        target=_number_or_none(_first_text(row_data, ("target", "cible"))),
        attention=_number_or_none(_first_text(row_data, ("attention", "warning", "seuil_attention"))),
        alert=_number_or_none(_first_text(row_data, ("alert", "alerte", "seuil_alerte"))),
        direction=_normalize_direction(_first_text(row_data, ("direction", "sens"))),
        justification=_first_text(row_data, ("justification", "reason", "motif")),
        vault_id=_first_text(row_data, ("vault_id",)),
        instance_id=_first_text(row_data, ("instance_id",)),
        scope_id=_first_text(row_data, ("scope_id", "perimetre")),
    )


def normalize_management_question(row: Mapping[str, Any]) -> ManagementQuestion:
    row_data = dict(row)
    indicator_id = _first_text(row_data, ("indicator_id", "id", "code", "key"))
    question = _first_text(row_data, ("question", "management_question", "demande"))
    return ManagementQuestion(
        question_id=_first_text(row_data, ("question_id", "id")) or _stable_id("MQ", indicator_id, question),
        indicator_id=indicator_id,
        audience=_first_text(row_data, ("audience", "destinataire", "to")) or "syndic",
        question=question,
        next_action=_first_text(row_data, ACTION_FIELDS),
        due_at=_first_text(row_data, ("due_at", "echeance", "deadline")),
        source=_first_text(row_data, SOURCE_FIELDS),
        proof_ref=_first_text(row_data, PROOF_FIELDS),
        confidence=_first_text(row_data, ("confidence", "confiance")),
        vault_id=_first_text(row_data, ("vault_id",)),
        instance_id=_first_text(row_data, ("instance_id",)),
        scope_id=_first_text(row_data, ("scope_id", "perimetre")),
    )


def normalize_indicator_definitions(rows: Iterable[Mapping[str, Any]]) -> list[IndicatorDefinition]:
    return [normalize_indicator_definition(row) for row in rows]


def normalize_metric_observations(rows: Iterable[Mapping[str, Any]]) -> list[MetricObservation]:
    return [normalize_metric_observation(row) for row in rows]


def normalize_target_thresholds(rows: Iterable[Mapping[str, Any]]) -> list[TargetThreshold]:
    return [normalize_target_threshold(row) for row in rows]


def normalize_management_questions(rows: Iterable[Mapping[str, Any]]) -> list[ManagementQuestion]:
    return [normalize_management_question(row) for row in rows]


def rows_from_csv(text: str) -> list[dict[str, str]]:
    if not text.strip():
        return []
    return [dict(row) for row in csv.DictReader(io.StringIO(text))]


def observations_from_csv(text: str) -> list[MetricObservation]:
    return normalize_metric_observations(rows_from_csv(text))


def definitions_from_csv(text: str) -> list[IndicatorDefinition]:
    return normalize_indicator_definitions(rows_from_csv(text))


def thresholds_from_csv(text: str) -> list[TargetThreshold]:
    return normalize_target_thresholds(rows_from_csv(text))


def build_dashboard_card(
    definition: IndicatorDefinition,
    observation: MetricObservation,
    threshold: TargetThreshold | None = None,
    *,
    next_action: str = "",
    novice_reading: str = "",
    trend: str = "",
    probable_cause: str = "",
) -> DashboardCard:
    if definition.indicator_id and observation.indicator_id and definition.indicator_id != observation.indicator_id:
        raise ValueError("definition and observation indicator_id must match")
    if not _same_context(definition, observation):
        raise ValueError("definition and observation contexts must not be mixed")
    if threshold and (threshold.indicator_id != observation.indicator_id or not _same_context(threshold, observation)):
        raise ValueError("threshold and observation contexts must not be mixed")

    theme = observation.theme or definition.theme
    source = observation.source or "source manquante"
    proof_ref = observation.proof_ref or "preuve manquante"
    status = evaluate_threshold(observation, threshold)
    confidence = confidence_level(observation)
    action = _cell(next_action) or _default_next_action(status, theme)
    return DashboardCard(
        indicator_id=observation.indicator_id or definition.indicator_id,
        theme=theme,
        title=observation.label or definition.name,
        period=observation.period,
        status=status,
        value=observation.value,
        unit=definition.unit,
        source=source,
        proof_ref=proof_ref,
        confidence=confidence,
        next_action=action,
        novice_reading=_cell(novice_reading) or _default_novice_reading(observation, definition, status),
        trend=_cell(trend),
        probable_cause=_cell(probable_cause),
        vault_id=observation.vault_id or definition.vault_id,
        instance_id=observation.instance_id or definition.instance_id,
        scope_id=observation.scope_id or definition.scope_id,
    )


def build_dashboard_cards(
    definitions: Iterable[IndicatorDefinition | Mapping[str, Any]],
    observations: Iterable[MetricObservation | Mapping[str, Any]],
    thresholds: Iterable[TargetThreshold | Mapping[str, Any]] | None = None,
) -> list[DashboardCard]:
    defs = [_as_definition(item) for item in definitions]
    obs = [_as_observation(item) for item in observations]
    ths = [_as_threshold(item) for item in (thresholds or [])]

    cards: list[DashboardCard] = []
    for observation in obs:
        definition = _best_match(defs, observation) or IndicatorDefinition(
            indicator_id=observation.indicator_id,
            theme=observation.theme,
            name=observation.label or observation.indicator_id,
        )
        threshold = _best_match(ths, observation)
        action = observation.metadata.get("next_action") or observation.metadata.get("prochaine_action")
        cards.append(build_dashboard_card(definition, observation, threshold, next_action=action))
    return cards


def evaluate_threshold(observation: MetricObservation, threshold: TargetThreshold | None = None) -> str:
    if not observation.proof_ref or not observation.source:
        return STATUS_VERIFY
    if threshold is None:
        return STATUS_OK
    if not _threshold_is_coherent(threshold):
        return STATUS_VERIFY
    value = _float_or_none(observation.value)
    if value is None:
        return STATUS_VERIFY
    if threshold.alert is not None and _breaches(value, threshold.alert, threshold.direction):
        return STATUS_ALERT
    if threshold.attention is not None and _breaches(value, threshold.attention, threshold.direction):
        return STATUS_ATTENTION
    return STATUS_OK


def confidence_level(observation: MetricObservation) -> str:
    if not observation.proof_ref or not observation.source:
        return STATUS_VERIFY
    quality = observation.data_quality.lower()
    if quality in {"faible", "low", "incomplete", "incomplet"}:
        return "faible"
    if quality in {"haute", "high", "verified", "verifie", "verifiee"}:
        return "haute"
    return "moyenne"


def card_to_dict(card: DashboardCard) -> dict[str, Any]:
    return asdict(card)


def validate_dashboard_card(card: DashboardCard) -> bool:
    missing = [
        field_name
        for field_name in ("theme", "period", "source", "proof_ref", "confidence", "next_action")
        if not _cell(getattr(card, field_name))
    ]
    if missing:
        raise ValueError(f"Dashboard card is missing required fields: {', '.join(missing)}")
    if card.status not in STATUS_VALUES:
        raise ValueError(f"Unsupported dashboard status: {card.status}")
    return True


def observation_context_key(observation: MetricObservation | Mapping[str, Any]) -> tuple[str, str, str]:
    item = _as_observation(observation) if not isinstance(observation, MetricObservation) else observation
    return (item.vault_id, item.instance_id, item.scope_id)


def _as_definition(item: IndicatorDefinition | Mapping[str, Any]) -> IndicatorDefinition:
    return item if isinstance(item, IndicatorDefinition) else normalize_indicator_definition(item)


def _as_observation(item: MetricObservation | Mapping[str, Any]) -> MetricObservation:
    return item if isinstance(item, MetricObservation) else normalize_metric_observation(item)


def _as_threshold(item: TargetThreshold | Mapping[str, Any]) -> TargetThreshold:
    return item if isinstance(item, TargetThreshold) else normalize_target_threshold(item)


def _best_match(items: Iterable[Any], observation: MetricObservation) -> Any | None:
    fallback = None
    for item in items:
        if item.indicator_id != observation.indicator_id:
            continue
        if not _same_context(item, observation):
            continue
        if all(getattr(item, field) == getattr(observation, field) for field in CONTEXT_FIELDS):
            return item
        fallback = item
    return fallback


def _same_context(left: Any, right: Any) -> bool:
    for field_name in CONTEXT_FIELDS:
        left_value = _cell(getattr(left, field_name, ""))
        right_value = _cell(getattr(right, field_name, ""))
        if left_value and right_value and left_value != right_value:
            return False
    return True


def _breaches(value: float, threshold: float, direction: str) -> bool:
    if direction == "min":
        return value <= threshold
    return value >= threshold


def _threshold_is_coherent(threshold: TargetThreshold) -> bool:
    if threshold.attention is None and threshold.alert is None:
        return True
    if threshold.attention is None or threshold.alert is None:
        return True
    if threshold.direction == "min":
        return threshold.alert <= threshold.attention
    return threshold.alert >= threshold.attention


def _normalize_direction(value: str) -> str:
    text = _cell(value).lower()
    if text in {"min", "minimum", "lower_is_bad", "bas"}:
        return "min"
    return "max"


def _default_next_action(status: str, theme: str) -> str:
    if status == STATUS_VERIFY:
        return "Verifier la source et rattacher une preuve."
    if status == STATUS_ALERT:
        return "Ouvrir un point de pilotage et demander une explication au syndic."
    if status == STATUS_ATTENTION:
        return "Surveiller l'ecart et preparer une question de suivi."
    return f"Maintenir le suivi {theme.lower()}." if theme else "Maintenir le suivi."


def _default_novice_reading(
    observation: MetricObservation,
    definition: IndicatorDefinition,
    status: str,
) -> str:
    label = observation.label or definition.name or observation.indicator_id
    if status == STATUS_VERIFY:
        return f"{label}: information a verifier faute de preuve ou de source."
    return f"{label}: {observation.value} sur la periode {observation.period}."


def _first_text(row: Mapping[str, Any], fields: Iterable[str]) -> str:
    for field_name in fields:
        value = _cell(row.get(field_name))
        if value:
            return value
    return ""


def _number_or_text(value: str) -> float | str:
    number = _float_or_none(value)
    return number if number is not None else _cell(value)


def _number_or_none(value: str) -> float | None:
    return _float_or_none(value)


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = _cell(value).replace("\u00a0", " ").replace(" ", "").replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


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


def _stable_id(prefix: str, *parts: str) -> str:
    material = "|".join(_cell(part) for part in parts if _cell(part))
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", material).strip("-").upper()
    return f"{prefix}-{normalized[:48]}" if normalized else f"{prefix}-UNSPECIFIED"
