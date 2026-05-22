from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..modules import pilotageops


STATUS_LABELS = {
    "OK": "suivi stable",
    "attention": "a surveiller",
    "alerte": "prioritaire",
    "a_verifier": "a verifier",
}

STATUS_HELP = {
    "OK": "La situation reste dans le seuil suivi.",
    "attention": "Un ecart existe: il faut garder le point visible.",
    "alerte": "Le conseil syndical doit traiter ce point en priorite.",
    "a_verifier": "La carte manque de source, de preuve ou de seuil fiable.",
}

STATUS_CLASS = {
    "OK": "is-ok",
    "attention": "is-review",
    "alerte": "is-risk",
    "a_verifier": "is-private",
}

DIFFUSION_LABELS = {
    pilotageops.DIFFUSION_CS: "Conseil syndical",
    pilotageops.DIFFUSION_SYNDIC: "Conseil syndical et syndic",
    pilotageops.DIFFUSION_RESTREINT: "Restreint au conseil syndical",
    pilotageops.DIFFUSION_AG: "Assemblee generale",
}

DOMAIN_LABELS = {
    pilotageops.DOMAIN_CONSOMMATIONS: "Consommations",
    pilotageops.DOMAIN_ENTRETIEN: "Entretien",
    pilotageops.DOMAIN_INVESTISSEMENTS: "Amortissement et investissements",
    pilotageops.DOMAIN_ESPACES_VERTS: "Espaces verts",
    pilotageops.DOMAIN_TRAVAUX: "Travaux",
    pilotageops.DOMAIN_GOUVERNANCE: "Gouvernance",
    pilotageops.DOMAIN_DEMANDES: "Demandes",
    pilotageops.DOMAIN_RISQUES: "Risques",
}

CARD_REQUIRED_FIELDS = (
    "indicator_id",
    "domain",
    "title",
    "period",
    "status",
    "threshold",
    "source",
    "proof_ref",
    "novice_reading",
    "next_action",
    "diffusion",
)

_DEFAULT_CARDS = object()


def build_pilotage_view(
    cards: Iterable[pilotageops.PilotageCard | Mapping[str, Any]] | object = _DEFAULT_CARDS,
    *,
    title: str = "Pilotage des indicateurs",
    intro: str = (
        "Chaque carte relie un chiffre a une periode, une preuve, un seuil et une action possible. "
        "Le but est de savoir quoi regarder sans connaitre la formule."
    ),
    period_label: str = "",
    source_label: str = "",
    instance: Any | None = None,
) -> dict[str, Any]:
    """Prepare indicator cards for the UI without adding a global route."""
    resolved_cards = (
        _cards_from_default_source(instance=instance, period_label=period_label)
        if cards is _DEFAULT_CARDS
        else list(cards)  # type: ignore[arg-type]
    )
    card_views = [_card_view(card) for card in resolved_cards]
    status_counts = Counter(card["status"] for card in card_views)
    domain_counts = Counter(card["domain"] for card in card_views)
    return {
        "title": title,
        "intro": intro,
        "period_label": period_label,
        "source_label": source_label,
        "has_cards": bool(card_views),
        "cards": card_views,
        "summary": {
            "total": len(card_views),
            "alerts": status_counts.get("alerte", 0),
            "attention": status_counts.get("attention", 0),
            "to_verify": status_counts.get("a_verifier", 0),
            "stable": status_counts.get("OK", 0),
            "domains": len(domain_counts),
        },
        "status_counts": _count_rows(status_counts, STATUS_LABELS),
        "domain_counts": _count_rows(domain_counts, DOMAIN_LABELS),
        "legend": _legend(),
        "empty_state": {
            "title": "Aucun indicateur pret a afficher",
            "body": (
                "Branchez des cartes issues de pilotageops pour afficher le domaine, la periode, "
                "la preuve, le seuil, le statut et la prochaine action. En attendant, rien n'est "
                "masque: l'interface signale simplement que le pilotage n'est pas encore alimente."
            ),
            "next_step": "Commencer par produire une carte avec build_pilotage_card, puis la rattacher a un point ou a une action.",
        },
    }


def build_pilotage_view_from_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    title: str = "Pilotage des indicateurs",
    period_label: str = "",
    source_label: str = "",
) -> dict[str, Any]:
    cards = pilotageops.pilotage_cards_from_rows(rows)
    return build_pilotage_view(cards, title=title, period_label=period_label, source_label=source_label)


def _cards_from_default_source(
    *,
    instance: Any | None,
    period_label: str,
) -> list[pilotageops.PilotageCard]:
    registry_rows = _pilotage_rows_from_instance(instance, period_label=period_label)
    if registry_rows:
        return pilotageops.pilotage_cards_from_rows(registry_rows)
    return _local_example_cards(period_label=period_label, instance=instance)


def _pilotage_rows_from_instance(instance: Any | None, *, period_label: str) -> list[dict[str, Any]]:
    if instance is None or not hasattr(instance, "register"):
        return []
    try:
        kpi_path = Path(instance.register("kpi"))
    except (KeyError, TypeError, ValueError, OSError):
        return []
    raw_rows = _read_csv_rows(kpi_path)
    rows = [
        _kpi_row_to_pilotage_row(row, kpi_path=kpi_path, instance=instance, period_label=period_label, index=index)
        for index, row in enumerate(raw_rows, start=1)
        if _first_text(row, ("indicator_id", "kpi_id", "id", "code", "key", "indicator", "label", "name"))
    ]
    return [row for row in rows if row]


def _kpi_row_to_pilotage_row(
    row: Mapping[str, Any],
    *,
    kpi_path: Path,
    instance: Any,
    period_label: str,
    index: int,
) -> dict[str, Any]:
    indicator_id = _first_text(row, ("indicator_id", "kpi_id", "id", "code", "key")) or f"KPI-{index:03d}"
    title = _first_text(row, ("indicator", "label", "name", "nom", "title")) or indicator_id
    family = _first_text(row, ("domain", "domaine", "theme", "family", "famille"))
    raw_value = _first_text(row, ("value", "valeur", "metric_value")) or "a renseigner"
    source_detail = _first_text(row, ("source", "source_register", "registre_source")) or "registre kpi"
    row_status = _first_text(row, ("status", "statut"))
    has_computed_value = raw_value != "a renseigner" and row_status.upper() not in {"TO_FILL", "A_RENSEIGNER"}
    proof_ref = _first_text(row, ("proof_ref", "preuve", "source_ref", "doc_id"))
    if not proof_ref and has_computed_value:
        proof_ref = f"{kpi_path.name}:{indicator_id}"
    return {
        "indicator_id": indicator_id,
        "domaine": _domain_for_kpi(family, title, source_detail),
        "name": title,
        "value": raw_value,
        "unit": _first_text(row, ("unit", "unite")),
        "period": _first_text(row, ("period", "periode", "exercice")) or period_label or "periode locale",
        "source": f"Registre KPI local - {source_detail}",
        "proof_ref": proof_ref,
        "data_quality": "verified" if has_computed_value else "incomplete",
        "attention": _first_text(row, ("attention", "warning", "seuil_attention")),
        "alert": _first_text(row, ("alert", "alerte", "seuil_alerte")),
        "direction": _first_text(row, ("direction", "sens")) or "max",
        "point_ref": _first_text(row, ("point_ref", "rattachement_point")) or f"POINT-PILOTAGE-{_slug(indicator_id)}",
        "action_ref": _first_text(row, ("action_ref", "rattachement_action")),
        "prochaine_action": _first_text(row, pilotageops.NEXT_ACTION_FIELDS) or _next_action_for_kpi(title, has_computed_value),
        "diffusion": _first_text(row, pilotageops.DIFFUSION_FIELDS) or "cs",
        "owner": _first_text(row, pilotageops.OWNER_FIELDS),
        "due_at": _first_text(row, pilotageops.DUE_FIELDS),
        "vault_id": _first_text(row, ("vault_id",)),
        "instance_id": _first_text(row, ("instance_id",)) or _instance_id(instance),
        "scope_id": _first_text(row, ("scope_id", "perimetre")),
    }


def _local_example_cards(*, period_label: str, instance: Any | None) -> list[pilotageops.PilotageCard]:
    instance_id = _instance_id(instance)
    period = period_label or "periode locale"
    rows = [
        {
            "indicator_id": "demo_local_conso_eau",
            "domaine": pilotageops.DOMAIN_CONSOMMATIONS,
            "name": "Exemple local - derive eau froide",
            "value": 18,
            "unit": "%",
            "period": period,
            "source": "Exemple local CoproScope",
            "proof_ref": "DEMO-LOCAL-CONSO-001",
            "attention": 10,
            "alert": 20,
            "point_ref": "POINT-DEMO-CONSO",
            "prochaine_action": "Remplacer cette carte exemple local par les releves ou factures de la copropriete.",
            "diffusion": "cs",
            "instance_id": instance_id,
        },
        {
            "indicator_id": "demo_local_entretien_contrat",
            "domaine": pilotageops.DOMAIN_ENTRETIEN,
            "name": "Exemple local - controle contrat entretien",
            "value": 1,
            "unit": "ecart",
            "period": period,
            "source": "Exemple local CoproScope",
            "proof_ref": "DEMO-LOCAL-ENTRETIEN-001",
            "attention": 1,
            "alert": 3,
            "point_ref": "POINT-DEMO-ENTRETIEN",
            "prochaine_action": "Verifier le contrat reel puis rattacher la facture ou le devis correspondant.",
            "diffusion": "cs",
            "instance_id": instance_id,
        },
        {
            "indicator_id": "demo_local_gouvernance_pv",
            "domaine": pilotageops.DOMAIN_GOUVERNANCE,
            "name": "Exemple local - decision AG sans suite",
            "value": 2,
            "unit": "decisions",
            "period": period,
            "source": "Exemple local CoproScope",
            "proof_ref": "DEMO-LOCAL-GOUV-001",
            "attention": 1,
            "alert": 3,
            "point_ref": "POINT-DEMO-GOUVERNANCE",
            "prochaine_action": "Remplacer par le PV AG ou le registre de decisions, puis nommer un responsable.",
            "diffusion": "cs",
            "instance_id": instance_id,
        },
    ]
    return pilotageops.pilotage_cards_from_rows(rows)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _domain_for_kpi(*parts: str) -> str:
    text = " ".join(_text(part).lower() for part in parts if _text(part))
    if any(token in text for token in ("eau", "energie", "conso", "chauffage")):
        return pilotageops.DOMAIN_CONSOMMATIONS
    if any(token in text for token in ("entretien", "maintenance", "contrat")):
        return pilotageops.DOMAIN_ENTRETIEN
    if any(token in text for token in ("demande", "syndic", "reponse", "requete")):
        return pilotageops.DOMAIN_DEMANDES
    if any(token in text for token in ("travaux", "chantier", "devis")):
        return pilotageops.DOMAIN_TRAVAUX
    if any(token in text for token in ("risque", "contentieux", "sinistre")):
        return pilotageops.DOMAIN_RISQUES
    return pilotageops.DOMAIN_GOUVERNANCE


def _next_action_for_kpi(title: str, has_computed_value: bool) -> str:
    if has_computed_value:
        return f"Controler la source du KPI puis decider si une action de suivi est necessaire: {title}."
    return f"Completer le registre KPI local avant decision: {title}."


def _instance_id(instance: Any | None) -> str:
    if instance is None:
        return ""
    try:
        return _text(instance.instance_id)
    except (AttributeError, KeyError, TypeError, ValueError):
        return ""


def _first_text(row: Mapping[str, Any], fields: Iterable[str]) -> str:
    for field_name in fields:
        value = _text(row.get(field_name))
        if value:
            return value
    return ""


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in _text(value).upper()).strip("-") or "KPI"


def _card_view(card: pilotageops.PilotageCard | Mapping[str, Any]) -> dict[str, Any]:
    data = _card_data(card)
    _validate_card_data(data)
    status = _text(data.get("status"))
    domain = _text(data.get("domain"))
    diffusion = _text(data.get("diffusion"))
    point_ref = _text(data.get("point_ref"))
    action_ref = _text(data.get("action_ref"))
    return {
        "card_id": _text(data.get("card_id")),
        "indicator_id": _text(data.get("indicator_id")),
        "domain": domain,
        "domain_label": DOMAIN_LABELS.get(domain, domain),
        "title": _text(data.get("title")) or _text(data.get("indicator_id")),
        "period": _text(data.get("period")),
        "status": status,
        "status_label": STATUS_LABELS.get(status, status),
        "status_help": STATUS_HELP.get(status, "Statut a confirmer."),
        "status_class": STATUS_CLASS.get(status, "is-review"),
        "value": _value_text(data.get("value"), _text(data.get("unit"))),
        "threshold": _text(data.get("threshold")),
        "source": _text(data.get("source")),
        "proof_ref": _text(data.get("proof_ref")),
        "proof_source": _proof_source(_text(data.get("source")), _text(data.get("proof_ref"))),
        "confidence": _text(data.get("confidence")),
        "novice_reading": _text(data.get("novice_reading")),
        "next_action": _text(data.get("next_action")),
        "diffusion": diffusion,
        "diffusion_label": DIFFUSION_LABELS.get(diffusion, diffusion),
        "point_ref": point_ref,
        "action_ref": action_ref,
        "attachment_label": _attachment_label(point_ref, action_ref),
        "owner": _text(data.get("owner")),
        "due_at": _text(data.get("due_at")),
        "trend": _text(data.get("trend")),
        "probable_cause": _text(data.get("probable_cause")),
    }


def _card_data(card: pilotageops.PilotageCard | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(card, pilotageops.PilotageCard):
        pilotageops.validate_pilotage_card(card)
        return pilotageops.card_to_dict(card)
    return dict(card)


def _validate_card_data(data: Mapping[str, Any]) -> None:
    missing = [field for field in CARD_REQUIRED_FIELDS if not _text(data.get(field))]
    if missing:
        raise ValueError(f"Pilotage UI card is missing required fields: {', '.join(missing)}")
    status = _text(data.get("status"))
    if status not in pilotageops.STATUS_VALUES:
        raise ValueError(f"Unsupported pilotage UI status: {status}")
    domain = _text(data.get("domain"))
    if domain not in pilotageops.PILOTAGE_DOMAINS:
        raise ValueError(f"Unsupported pilotage UI domain: {domain}")
    diffusion = _text(data.get("diffusion"))
    if diffusion not in pilotageops.DIFFUSION_VALUES:
        raise ValueError(f"Unsupported pilotage UI diffusion: {diffusion}")
    if not _text(data.get("point_ref")) and not _text(data.get("action_ref")):
        raise ValueError("Pilotage UI card must be attached to a point or an action")


def _count_rows(counts: Counter[str], labels: Mapping[str, str]) -> list[dict[str, Any]]:
    return [
        {"key": key, "label": labels.get(key, key), "count": count}
        for key, count in counts.items()
        if count
    ]


def _legend() -> list[dict[str, str]]:
    return [
        {
            "status": status,
            "label": label,
            "help": STATUS_HELP[status],
            "class": STATUS_CLASS[status],
        }
        for status, label in STATUS_LABELS.items()
    ]


def _proof_source(source: str, proof_ref: str) -> str:
    parts = [part for part in (source, proof_ref) if part]
    return " - ".join(parts) if parts else "source ou preuve a renseigner"


def _attachment_label(point_ref: str, action_ref: str) -> str:
    parts: list[str] = []
    if point_ref:
        parts.append(f"Point {point_ref}")
    if action_ref:
        parts.append(f"Action {action_ref}")
    return " / ".join(parts) if parts else "rattachement a completer"


def _value_text(value: Any, unit: str) -> str:
    if isinstance(value, float):
        raw = pilotageops.format_number(value)
    else:
        raw = _text(value)
    return f"{raw} {unit}".strip()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()
