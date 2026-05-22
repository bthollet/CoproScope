from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from coproscope.modules.indicatorops import (
    STATUS_VALUES,
    DashboardCard,
    IndicatorDefinition,
    MetricObservation,
    TargetThreshold,
    build_dashboard_card,
    confidence_level,
    normalize_indicator_definition,
    normalize_metric_observation,
    normalize_target_threshold,
)


DOMAIN_CONSOMMATIONS = "consommations"
DOMAIN_ENTRETIEN = "entretien"
DOMAIN_INVESTISSEMENTS = "amortissement/investissements"
DOMAIN_ESPACES_VERTS = "espaces verts"
DOMAIN_TRAVAUX = "travaux"
DOMAIN_GOUVERNANCE = "gouvernance"
DOMAIN_DEMANDES = "demandes"
DOMAIN_RISQUES = "risques"

PILOTAGE_DOMAINS = frozenset(
    {
        DOMAIN_CONSOMMATIONS,
        DOMAIN_ENTRETIEN,
        DOMAIN_INVESTISSEMENTS,
        DOMAIN_ESPACES_VERTS,
        DOMAIN_TRAVAUX,
        DOMAIN_GOUVERNANCE,
        DOMAIN_DEMANDES,
        DOMAIN_RISQUES,
    }
)

DOMAIN_ALIASES = {
    "conso": DOMAIN_CONSOMMATIONS,
    "consommation": DOMAIN_CONSOMMATIONS,
    "consommations": DOMAIN_CONSOMMATIONS,
    "energie": DOMAIN_CONSOMMATIONS,
    "eau": DOMAIN_CONSOMMATIONS,
    "entretien": DOMAIN_ENTRETIEN,
    "maintenance": DOMAIN_ENTRETIEN,
    "contrats": DOMAIN_ENTRETIEN,
    "contrat": DOMAIN_ENTRETIEN,
    "amortissement": DOMAIN_INVESTISSEMENTS,
    "amortissements": DOMAIN_INVESTISSEMENTS,
    "amortissement_investissements": DOMAIN_INVESTISSEMENTS,
    "investissement": DOMAIN_INVESTISSEMENTS,
    "investissements": DOMAIN_INVESTISSEMENTS,
    "capex": DOMAIN_INVESTISSEMENTS,
    "fonds_travaux": DOMAIN_INVESTISSEMENTS,
    "espaces_verts": DOMAIN_ESPACES_VERTS,
    "jardin": DOMAIN_ESPACES_VERTS,
    "jardins": DOMAIN_ESPACES_VERTS,
    "travaux": DOMAIN_TRAVAUX,
    "chantier": DOMAIN_TRAVAUX,
    "gouvernance": DOMAIN_GOUVERNANCE,
    "ag": DOMAIN_GOUVERNANCE,
    "assemblee_generale": DOMAIN_GOUVERNANCE,
    "conseil_syndical": DOMAIN_GOUVERNANCE,
    "demandes": DOMAIN_DEMANDES,
    "demande": DOMAIN_DEMANDES,
    "requetes": DOMAIN_DEMANDES,
    "syndic": DOMAIN_DEMANDES,
    "risques": DOMAIN_RISQUES,
    "risque": DOMAIN_RISQUES,
    "risques_contentieux": DOMAIN_RISQUES,
    "contentieux": DOMAIN_RISQUES,
    "sinistres": DOMAIN_RISQUES,
    "sinistre": DOMAIN_RISQUES,
}

DIFFUSION_CS = "conseil_syndical"
DIFFUSION_SYNDIC = "conseil_syndical_et_syndic"
DIFFUSION_RESTREINT = "restreint_cs"
DIFFUSION_AG = "assemblee_generale"
DIFFUSION_VALUES = frozenset({DIFFUSION_CS, DIFFUSION_SYNDIC, DIFFUSION_RESTREINT, DIFFUSION_AG})

ATTACHMENT_FIELDS = ("point_ref", "point_id", "rattachement_point", "pilotage_point_ref")
ACTION_REF_FIELDS = ("action_ref", "action_id", "rattachement_action", "pilotage_action_ref")
DIFFUSION_FIELDS = ("diffusion", "public", "audience", "visibilite", "visibility")
DOMAIN_FIELDS = ("domain", "domaine", "theme", "thematique")
OWNER_FIELDS = ("owner", "responsable", "pilote", "assigned_to")
DUE_FIELDS = ("due_at", "echeance", "deadline", "date_limite")
NEXT_ACTION_FIELDS = ("next_action", "prochaine_action", "action", "action_attendue", "recommended_action")


@dataclass(frozen=True)
class PilotageAttachment:
    indicator_id: str
    point_ref: str = ""
    action_ref: str = ""
    next_action: str = ""
    diffusion: str = ""
    owner: str = ""
    due_at: str = ""
    vault_id: str = ""
    instance_id: str = ""
    scope_id: str = ""


@dataclass(frozen=True)
class PilotageCard:
    card_id: str
    indicator_id: str
    domain: str
    title: str
    period: str
    status: str
    value: float | str
    unit: str
    threshold: str
    source: str
    proof_ref: str
    confidence: str
    novice_reading: str
    next_action: str
    diffusion: str
    point_ref: str
    action_ref: str
    owner: str = ""
    due_at: str = ""
    trend: str = ""
    probable_cause: str = ""
    vault_id: str = ""
    instance_id: str = ""
    scope_id: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


def normalize_attachment(row: Mapping[str, Any]) -> PilotageAttachment:
    row_data = dict(row)
    return PilotageAttachment(
        indicator_id=_first_text(row_data, ("indicator_id", "id", "code", "key")),
        point_ref=_first_text(row_data, ATTACHMENT_FIELDS),
        action_ref=_first_text(row_data, ACTION_REF_FIELDS),
        next_action=_first_text(row_data, NEXT_ACTION_FIELDS),
        diffusion=_normalize_diffusion(_first_text(row_data, DIFFUSION_FIELDS)),
        owner=_first_text(row_data, OWNER_FIELDS),
        due_at=_first_text(row_data, DUE_FIELDS),
        vault_id=_first_text(row_data, ("vault_id",)),
        instance_id=_first_text(row_data, ("instance_id",)),
        scope_id=_first_text(row_data, ("scope_id", "perimetre")),
    )


def normalize_attachments(rows: Iterable[Mapping[str, Any]]) -> list[PilotageAttachment]:
    return [normalize_attachment(row) for row in rows]


def build_pilotage_card(
    definition: IndicatorDefinition | Mapping[str, Any],
    observation: MetricObservation | Mapping[str, Any],
    threshold: TargetThreshold | Mapping[str, Any] | None = None,
    *,
    attachment: PilotageAttachment | Mapping[str, Any] | None = None,
    domain: str = "",
    next_action: str = "",
    diffusion: str = "",
    point_ref: str = "",
    action_ref: str = "",
    owner: str = "",
    due_at: str = "",
    novice_reading: str = "",
) -> PilotageCard:
    normalized_definition = _as_definition(definition)
    normalized_observation = _as_observation(observation)
    normalized_threshold = _as_threshold(threshold) if threshold is not None else None
    normalized_attachment = _as_attachment(attachment) if attachment is not None else None
    if normalized_attachment and not _same_context(normalized_attachment, normalized_observation):
        raise ValueError("attachment and observation contexts must not be mixed")

    action = (
        _cell(next_action)
        or _cell(getattr(normalized_attachment, "next_action", ""))
        or normalized_observation.metadata.get("next_action")
        or normalized_observation.metadata.get("prochaine_action")
    )
    dashboard = build_dashboard_card(
        normalized_definition,
        normalized_observation,
        normalized_threshold,
        next_action=action,
        novice_reading=novice_reading,
    )

    card_domain = normalize_domain(domain or dashboard.theme or normalized_definition.theme or normalized_observation.theme)
    resolved_diffusion = _normalize_diffusion(
        diffusion or getattr(normalized_attachment, "diffusion", "") or normalized_observation.metadata.get("diffusion", "")
    ) or _default_diffusion(card_domain, dashboard.status)
    resolved_point_ref = (
        _cell(point_ref)
        or _cell(getattr(normalized_attachment, "point_ref", ""))
        or normalized_observation.metadata.get("point_ref", "")
        or _default_point_ref(card_domain, dashboard.indicator_id, dashboard.period)
    )
    resolved_action_ref = (
        _cell(action_ref)
        or _cell(getattr(normalized_attachment, "action_ref", ""))
        or normalized_observation.metadata.get("action_ref", "")
    )
    resolved_owner = _cell(owner) or _cell(getattr(normalized_attachment, "owner", ""))
    resolved_due_at = _cell(due_at) or _cell(getattr(normalized_attachment, "due_at", ""))

    card = PilotageCard(
        card_id=_stable_id("PLC", dashboard.indicator_id, dashboard.period, card_domain, resolved_point_ref, resolved_action_ref),
        indicator_id=dashboard.indicator_id,
        domain=card_domain,
        title=dashboard.title,
        period=dashboard.period,
        status=dashboard.status,
        value=dashboard.value,
        unit=dashboard.unit,
        threshold=threshold_summary(normalized_threshold),
        source=dashboard.source,
        proof_ref=dashboard.proof_ref,
        confidence=dashboard.confidence or confidence_level(normalized_observation),
        novice_reading=novice_sentence(dashboard, card_domain),
        next_action=dashboard.next_action,
        diffusion=resolved_diffusion,
        point_ref=resolved_point_ref,
        action_ref=resolved_action_ref,
        owner=resolved_owner,
        due_at=resolved_due_at,
        trend=dashboard.trend,
        probable_cause=dashboard.probable_cause,
        vault_id=dashboard.vault_id,
        instance_id=dashboard.instance_id,
        scope_id=dashboard.scope_id,
        metadata={
            "dashboard_status": dashboard.status,
            "threshold_direction": normalized_threshold.direction if normalized_threshold else "",
        },
    )
    validate_pilotage_card(card)
    return card


def build_pilotage_cards(
    definitions: Iterable[IndicatorDefinition | Mapping[str, Any]],
    observations: Iterable[MetricObservation | Mapping[str, Any]],
    thresholds: Iterable[TargetThreshold | Mapping[str, Any]] | None = None,
    attachments: Iterable[PilotageAttachment | Mapping[str, Any]] | None = None,
) -> list[PilotageCard]:
    normalized_definitions = [_as_definition(item) for item in definitions]
    normalized_observations = [_as_observation(item) for item in observations]
    normalized_thresholds = [_as_threshold(item) for item in (thresholds or [])]
    normalized_attachments = [_as_attachment(item) for item in (attachments or [])]

    cards: list[PilotageCard] = []
    for observation in normalized_observations:
        definition = _best_match(normalized_definitions, observation) or IndicatorDefinition(
            indicator_id=observation.indicator_id,
            theme=observation.theme,
            name=observation.label or observation.indicator_id,
        )
        threshold = _best_match(normalized_thresholds, observation)
        attachment = _best_match(normalized_attachments, observation)
        cards.append(build_pilotage_card(definition, observation, threshold, attachment=attachment))
    return cards


def pilotage_card_from_row(row: Mapping[str, Any]) -> PilotageCard:
    row_data = dict(row)
    definition = normalize_indicator_definition(row_data)
    observation = normalize_metric_observation(row_data)
    threshold = normalize_target_threshold(row_data)
    attachment = normalize_attachment(row_data)
    return build_pilotage_card(
        definition,
        observation,
        threshold,
        attachment=attachment,
        domain=_first_text(row_data, DOMAIN_FIELDS),
    )


def pilotage_cards_from_rows(rows: Iterable[Mapping[str, Any]]) -> list[PilotageCard]:
    return [pilotage_card_from_row(row) for row in rows]


def rows_from_csv(text: str) -> list[dict[str, str]]:
    if not text.strip():
        return []
    return [dict(row) for row in csv.DictReader(io.StringIO(text))]


def pilotage_cards_from_csv(text: str) -> list[PilotageCard]:
    return pilotage_cards_from_rows(rows_from_csv(text))


def threshold_summary(threshold: TargetThreshold | Mapping[str, Any] | None) -> str:
    normalized = _as_threshold(threshold)
    if normalized is None:
        return "seuil non renseigne"
    parts: list[str] = []
    if normalized.target is not None:
        parts.append(f"cible {format_number(normalized.target)}")
    if normalized.attention is not None:
        parts.append(f"attention {_direction_symbol(normalized.direction)} {format_number(normalized.attention)}")
    if normalized.alert is not None:
        parts.append(f"alerte {_direction_symbol(normalized.direction)} {format_number(normalized.alert)}")
    return "; ".join(parts) if parts else "seuil non renseigne"


def novice_sentence(card: DashboardCard, domain: str) -> str:
    base = _cell(card.novice_reading)
    if not base:
        base = f"{card.title}: {card.value} sur {card.period}."
    if card.status == "OK":
        status_text = "Situation suivie sans alerte."
    elif card.status == "attention":
        status_text = "Point a surveiller."
    elif card.status == "alerte":
        status_text = "Point prioritaire a traiter."
    else:
        status_text = "Information a verifier avant decision."
    return f"{base} Domaine: {domain}. {status_text}"


def normalize_domain(value: str) -> str:
    text = _token(value)
    domain = DOMAIN_ALIASES.get(text, _cell(value).lower())
    if domain not in PILOTAGE_DOMAINS:
        raise ValueError(f"Unsupported pilotage domain: {_cell(value) or 'missing'}")
    return domain


def validate_pilotage_card(card: PilotageCard) -> bool:
    missing = [
        field_name
        for field_name in (
            "card_id",
            "indicator_id",
            "domain",
            "period",
            "threshold",
            "source",
            "proof_ref",
            "confidence",
            "novice_reading",
            "next_action",
            "diffusion",
        )
        if not _cell(getattr(card, field_name))
    ]
    if missing:
        raise ValueError(f"Pilotage card is missing required fields: {', '.join(missing)}")
    if card.domain not in PILOTAGE_DOMAINS:
        raise ValueError(f"Unsupported pilotage domain: {card.domain}")
    if card.status not in STATUS_VALUES:
        raise ValueError(f"Unsupported pilotage status: {card.status}")
    if card.diffusion not in DIFFUSION_VALUES:
        raise ValueError(f"Unsupported pilotage diffusion: {card.diffusion}")
    if not _cell(card.point_ref) and not _cell(card.action_ref):
        raise ValueError("Pilotage card must be attached to a point or action")
    return True


def card_to_dict(card: PilotageCard) -> dict[str, Any]:
    return asdict(card)


def format_number(value: float | int) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def _as_definition(item: IndicatorDefinition | Mapping[str, Any]) -> IndicatorDefinition:
    return item if isinstance(item, IndicatorDefinition) else normalize_indicator_definition(item)


def _as_observation(item: MetricObservation | Mapping[str, Any]) -> MetricObservation:
    return item if isinstance(item, MetricObservation) else normalize_metric_observation(item)


def _as_threshold(item: TargetThreshold | Mapping[str, Any] | None) -> TargetThreshold | None:
    if item is None:
        return None
    return item if isinstance(item, TargetThreshold) else normalize_target_threshold(item)


def _as_attachment(item: PilotageAttachment | Mapping[str, Any]) -> PilotageAttachment:
    return item if isinstance(item, PilotageAttachment) else normalize_attachment(item)


def _best_match(items: Iterable[Any], observation: MetricObservation) -> Any | None:
    fallback = None
    for item in items:
        if item.indicator_id != observation.indicator_id:
            continue
        if not _same_context(item, observation):
            continue
        if all(getattr(item, field_name, "") == getattr(observation, field_name, "") for field_name in ("vault_id", "instance_id", "scope_id")):
            return item
        fallback = item
    return fallback


def _same_context(left: Any, right: Any) -> bool:
    for field_name in ("vault_id", "instance_id", "scope_id"):
        left_value = _cell(getattr(left, field_name, ""))
        right_value = _cell(getattr(right, field_name, ""))
        if left_value and right_value and left_value != right_value:
            return False
    return True


def _default_diffusion(domain: str, status: str) -> str:
    if domain == DOMAIN_RISQUES:
        return DIFFUSION_RESTREINT
    if status == "alerte":
        return DIFFUSION_SYNDIC
    return DIFFUSION_CS


def _default_point_ref(domain: str, indicator_id: str, period: str) -> str:
    slug = _token(f"{domain}-{indicator_id}-{period}") or "pilotage"
    return f"POINT-{slug.upper()[:72]}"


def _direction_symbol(direction: str) -> str:
    return "<=" if direction == "min" else ">="


def _normalize_diffusion(value: str) -> str:
    text = _token(value)
    if not text:
        return ""
    aliases = {
        "cs": DIFFUSION_CS,
        "conseil_syndical": DIFFUSION_CS,
        "interne_cs": DIFFUSION_CS,
        "syndic": DIFFUSION_SYNDIC,
        "conseil_syndical_et_syndic": DIFFUSION_SYNDIC,
        "cs_syndic": DIFFUSION_SYNDIC,
        "restreint": DIFFUSION_RESTREINT,
        "restreint_cs": DIFFUSION_RESTREINT,
        "confidentiel": DIFFUSION_RESTREINT,
        "ag": DIFFUSION_AG,
        "assemblee_generale": DIFFUSION_AG,
    }
    normalized = aliases.get(text, text if text in DIFFUSION_VALUES else "")
    if not normalized:
        raise ValueError(f"Unsupported pilotage diffusion: {_cell(value)}")
    return normalized


def _first_text(row: Mapping[str, Any], fields: Iterable[str]) -> str:
    for field_name in fields:
        value = _cell(row.get(field_name))
        if value:
            return value
    return ""


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


def _token(value: Any) -> str:
    folded = unicodedata.normalize("NFKD", _cell(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", folded.lower()).strip("_")


def _stable_id(prefix: str, *parts: str) -> str:
    material = "|".join(_cell(part) for part in parts if _cell(part)) or prefix
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12].upper()
    readable = re.sub(r"[^A-Za-z0-9]+", "-", material).strip("-").upper()[:36]
    return f"{prefix}-{readable}-{digest}" if readable else f"{prefix}-{digest}"
