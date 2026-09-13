from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from typing import Any

from . import agcontentieux
from . import requestops


SCHEMA_VERSION = "passation_export_derive.v1"
WATERMARK = "export dérivé, non source collaborative"
SOURCE_NOTICE = (
    "Payload derive depuis des objets abstraits agcontentieux/requestops/timeline; "
    "il ne constitue pas une source de verite collaborative."
)

_FORBIDDEN_KEYS = {"raw", "payload", "metadata", "private_path", "absolute_path", "local_path"}


def build_passation_derived_export(
    *,
    title: str,
    passation_pack: object | None = None,
    dossiers_ag: Iterable[object] = (),
    contentieux_cases: Iterable[object] = (),
    evidence_bundles: Iterable[object] = (),
    legal_risk_notes: Iterable[object] = (),
    requests: Iterable[object] = (),
    timeline_entries: Iterable[Mapping[str, Any]] | Mapping[str, Iterable[Mapping[str, Any]]] = (),
    export_id: str = "",
    generated_at: datetime | str | None = None,
) -> dict[str, Any]:
    """Build a redacted, derived handover export without making it a truth source."""

    dossiers = tuple(dossiers_ag)
    cases = tuple(contentieux_cases)
    bundles = tuple(evidence_bundles)
    notes = tuple(legal_risk_notes)
    all_records: tuple[object, ...] = tuple(
        item for item in (*((passation_pack,) if passation_pack is not None else ()), *dossiers, *cases, *bundles, *notes) if item is not None
    )
    omissions: list[dict[str, str]] = []
    request_cards = _request_cards(requests, omissions)
    timeline_cards = _timeline_cards(timeline_entries, omissions)

    document = {
        "schema_version": SCHEMA_VERSION,
        "watermark": WATERMARK,
        "source_of_truth": False,
        "source_notice": SOURCE_NOTICE,
        "export_id": _sanitize_text(export_id),
        "title": _sanitize_text(title),
        "generated_at": _generated_at(generated_at),
        "scope": {
            "kind": "passation_ag_contentieux",
            "restriction": _restriction_label(_max_restriction(all_records)),
            "diffusion": _diffusion_label(_min_diffusion(all_records)),
        },
        "source_refs": _clean_refs(agcontentieux.source_reference_ids(all_records)),
        "proof_refs": _clean_refs(agcontentieux.proof_reference_ids(all_records)),
        "sections": {
            "passation": _pack_card(passation_pack, omissions) if passation_pack is not None else {},
            "ag": [_ag_card(record, omissions) for record in dossiers],
            "contentieux": [_contentieux_card(record, omissions) for record in cases],
            "preuves": [_bundle_card(record, omissions) for record in bundles],
            "vigilance": [_risk_note_card(record, omissions) for record in notes],
            "demandes": request_cards,
            "chronologie": timeline_cards,
        },
        "next_actions": _next_actions((*all_records, *request_cards, *timeline_cards)),
        "omissions": omissions,
    }
    _record_missing_refs(all_records, omissions)
    _assert_export_safe(document)
    return document


def render_passation_derived_json(document: Mapping[str, Any]) -> str:
    _assert_export_safe(document)
    return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True)


def render_passation_derived_markdown(document: Mapping[str, Any]) -> str:
    _assert_export_safe(document)
    sections = _mapping(document.get("sections"))
    scope = _mapping(document.get("scope"))
    lines = [
        f"# {_md(document.get('title') or 'Export passation derive')}",
        "",
        f"**{WATERMARK}**",
        "",
        _md(document.get("source_notice")),
        "",
        f"- Schema: `{_md(document.get('schema_version'))}`",
        f"- Source de verite: `{str(document.get('source_of_truth')).lower()}`",
        f"- Restriction: `{_md(scope.get('restriction'))}`",
        f"- Diffusion: `{_md(scope.get('diffusion'))}`",
        f"- Sources: {_inline_refs(document.get('source_refs'))}",
        f"- Preuves: {_inline_refs(document.get('proof_refs'))}",
        "",
    ]

    pack = _mapping(sections.get("passation"))
    if pack:
        lines.extend(
            [
                "## Passation",
                "",
                f"- Objet: {_md(pack.get('title'))}",
                f"- Perimetre: {_md(pack.get('handover_scope'))}",
                f"- Prochaine action: {_md(pack.get('next_action'))}",
                "",
            ]
        )

    _append_cards(lines, "AG", sections.get("ag"), "title")
    _append_cards(lines, "Contentieux", sections.get("contentieux"), "title")
    _append_cards(lines, "Preuves", sections.get("preuves"), "title")
    _append_cards(lines, "Vigilance", sections.get("vigilance"), "subject")
    _append_cards(lines, "Demandes", sections.get("demandes"), "subject")
    _append_cards(lines, "Chronologie", sections.get("chronologie"), "summary")

    next_actions = _sequence(document.get("next_actions"))
    if next_actions:
        lines.extend(["## Prochaines actions", ""])
        for action in next_actions:
            item = _mapping(action)
            due = f" (echeance: {_md(item.get('due_on'))})" if item.get("due_on") else ""
            lines.append(f"- `{_md(item.get('object_id'))}`: {_md(item.get('next_action'))}{due}")
        lines.append("")

    omissions = _sequence(document.get("omissions"))
    if omissions:
        lines.extend(["## Limites de l'export", ""])
        for omission in omissions:
            item = _mapping(omission)
            lines.append(f"- `{_md(item.get('object_id'))}`: {_md(item.get('reason'))}")
        lines.append("")

    markdown = "\n".join(lines).rstrip() + "\n"
    _assert_export_safe({"markdown": markdown})
    return markdown


def _pack_card(record: object, omissions: list[dict[str, str]]) -> dict[str, Any]:
    card = _base_card(record, "PassationPack", "pack_id", omissions)
    card.update(
        {
            "title": _field(record, "title"),
            "handover_scope": _field(record, "handover_scope"),
            "dossier_ag_ids": _clean_refs(_field(record, "dossier_ag_ids", ())),
            "contentieux_case_ids": _clean_refs(_field(record, "contentieux_case_ids", ())),
            "evidence_bundle_ids": _clean_refs(_field(record, "evidence_bundle_ids", ())),
            "legal_risk_note_ids": _clean_refs(_field(record, "legal_risk_note_ids", ())),
            "open_points": _clean_texts(_field(record, "open_points", ())),
        }
    )
    return _without_empty(card)


def _ag_card(record: object, omissions: list[dict[str, str]]) -> dict[str, Any]:
    card = _base_card(record, "DossierAG", "dossier_id", omissions)
    card.update(
        {
            "title": _field(record, "title"),
            "ag_date": _date_text(_field(record, "ag_date")),
            "questions": [_child_question(item) for item in _field(record, "questions", ())],
            "pieces": [_child_piece(item) for item in _field(record, "pieces", ())],
        }
    )
    return _without_empty(card)


def _contentieux_card(record: object, omissions: list[dict[str, str]]) -> dict[str, Any]:
    card = _base_card(record, "ContentieuxCase", "case_id", omissions)
    card.update(
        {
            "title": _field(record, "title"),
            "matter": _field(record, "matter"),
            "risk_note_refs": _clean_refs(_field(record, "risk_note_refs", ())),
        }
    )
    return _without_empty(card)


def _bundle_card(record: object, omissions: list[dict[str, str]]) -> dict[str, Any]:
    card = _base_card(record, "EvidenceBundle", "bundle_id", omissions)
    card.update(
        {
            "title": _field(record, "title"),
            "purpose": _field(record, "purpose"),
            "evidence_refs": [_evidence_ref_card(item) for item in _field(record, "evidence_refs", ())],
        }
    )
    return _without_empty(card)


def _risk_note_card(record: object, omissions: list[dict[str, str]]) -> dict[str, Any]:
    card = _base_card(record, "LegalRiskNote", "note_id", omissions)
    card.update(
        {
            "subject": _field(record, "subject"),
            "observations": _clean_texts(_field(record, "observations", ())),
            "risk_signals": _clean_texts(_field(record, "risk_signals", ())),
            "scope_notice": _field(record, "scope_notice"),
        }
    )
    return _without_empty(card)


def _base_card(record: object, object_type: str, id_field: str, omissions: list[dict[str, str]]) -> dict[str, Any]:
    object_id = _field(record, id_field)
    source_refs = _clean_refs(_field(record, "source_refs", ()))
    proof_refs = _clean_refs(_field(record, "proof_refs", ()))
    _track_ref_omissions(object_id, _field(record, "source_refs", ()), source_refs, "source_refs", omissions)
    _track_ref_omissions(object_id, _field(record, "proof_refs", ()), proof_refs, "proof_refs", omissions)
    return {
        "object_type": object_type,
        "object_id": _sanitize_text(object_id),
        "status": _sanitize_text(_field(record, "status")),
        "restriction": _restriction_label(_field(record, "restriction")),
        "diffusion": _diffusion_label(_field(record, "diffusion")),
        "source_refs": source_refs,
        "proof_refs": proof_refs,
        "decision_refs": _clean_refs(_field(record, "decision_refs", ())),
        "action_refs": _clean_refs(_field(record, "action_refs", ())),
        "event_refs": _clean_refs(_field(record, "event_refs", ())),
        "next_action": _field(record, "next_action"),
        "due_on": _date_text(_field(record, "due_on")),
    }


def _child_question(record: object) -> dict[str, Any]:
    return _without_empty(
        {
            "object_type": "QuestionAG",
            "object_id": _field(record, "question_id"),
            "title": _field(record, "title"),
            "objective": _field(record, "objective"),
            "source_refs": _clean_refs(_field(record, "source_refs", ())),
            "proof_refs": _clean_refs(_field(record, "proof_refs", ())),
            "restriction": _restriction_label(_field(record, "restriction")),
            "diffusion": _diffusion_label(_field(record, "diffusion")),
            "next_action": _field(record, "next_action"),
            "due_on": _date_text(_field(record, "due_on")),
        }
    )


def _child_piece(record: object) -> dict[str, Any]:
    return _without_empty(
        {
            "object_type": "PieceConvocation",
            "object_id": _field(record, "piece_id"),
            "label": _field(record, "label"),
            "source_refs": _clean_refs(_field(record, "source_refs", ())),
            "proof_refs": _clean_refs(_field(record, "proof_refs", ())),
            "restriction": _restriction_label(_field(record, "restriction")),
            "diffusion": _diffusion_label(_field(record, "diffusion")),
            "next_action": _field(record, "next_action"),
            "due_on": _date_text(_field(record, "due_on")),
        }
    )


def _evidence_ref_card(record: object) -> dict[str, Any]:
    return _without_empty(
        {
            "object_type": "EvidenceRef",
            "object_id": _field(record, "evidence_id"),
            "source_ref": _clean_ref(_field(record, "source_ref")),
            "title": _field(record, "title"),
            "source_kind": _field(record, "source_kind"),
            "source_hash": _field(record, "source_hash"),
            "captured_on": _date_text(_field(record, "captured_on")),
            "restriction": _restriction_label(_field(record, "restriction")),
            "diffusion": _diffusion_label(_field(record, "diffusion")),
            "status": _field(record, "status"),
            "next_action": _field(record, "next_action"),
            "due_on": _date_text(_field(record, "due_on")),
        }
    )


def _request_cards(requests: Iterable[object], omissions: list[dict[str, str]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for request in requests:
        request_id = _field(request, "request_id")
        visibility = _field(request, "visibility")
        if visibility == requestops.VISIBILITY_RESTRICTED:
            omissions.append(
                {
                    "object_id": _sanitize_text(request_id),
                    "field": "demande",
                    "reason": "visibilite restreinte exclue de l'export derive",
                }
            )
            continue
        cards.append(
            _without_empty(
                {
                    "object_type": "CoproRequest",
                    "object_id": _sanitize_text(request_id),
                    "received_at": _sanitize_text(_field(request, "received_at")),
                    "channel": _sanitize_text(_field(request, "channel")),
                    "subject": _field(request, "subject"),
                    "summary": _field(request, "summary"),
                    "status": _sanitize_text(_field(request, "status")),
                    "restriction": _visibility_label(visibility),
                    "diffusion": _visibility_diffusion_label(visibility),
                    "source_refs": _clean_refs((_field(request, "source_ref"),)),
                    "proof_refs": _clean_refs((_field(request, "proof_ref"),)),
                    "related_point_id": _clean_ref(_field(request, "related_point_id")),
                    "related_action_id": _clean_ref(_field(request, "related_action_id")),
                    "origin_kind": _sanitize_text(_field(request, "origin_kind")),
                    "origin_id": _clean_ref(_field(request, "origin_id")),
                    "next_action": _field(request, "next_action"),
                }
            )
        )
    return cards


def _timeline_cards(
    timeline_entries: Iterable[Mapping[str, Any]] | Mapping[str, Iterable[Mapping[str, Any]]],
    omissions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for entry in _iter_timeline_entries(timeline_entries):
        object_id = _clean_ref(entry.get("object_id"))
        proof_ref = _clean_ref(entry.get("proof_ref"))
        if entry.get("object_id") and not object_id:
            omissions.append({"object_id": "", "field": "chronologie.object_id", "reason": "chemin prive retire"})
        if entry.get("proof_ref") and not proof_ref:
            omissions.append({"object_id": object_id, "field": "chronologie.proof_ref", "reason": "chemin prive retire"})
        cards.append(
            _without_empty(
                {
                    "object_type": "TimelineEntry",
                    "object_id": object_id,
                    "timeline_id": _clean_ref(entry.get("timeline_id")),
                    "source": _sanitize_text(entry.get("source")),
                    "source_id": _clean_ref(entry.get("source_id")),
                    "occurred_at": _sanitize_text(entry.get("occurred_at")),
                    "event_type": _sanitize_text(entry.get("event_type")),
                    "status": _sanitize_text(entry.get("status")),
                    "proof_refs": _clean_refs((proof_ref,)),
                    "summary": _sanitize_text(entry.get("summary")),
                    "comment": _sanitize_text(entry.get("comment")),
                }
            )
        )
    return cards


def _next_actions(items: Iterable[object]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        if isinstance(item, Mapping):
            object_id = _sanitize_text(item.get("object_id"))
            object_type = _sanitize_text(item.get("object_type"))
            next_action = _sanitize_text(item.get("next_action"))
            due_on = _sanitize_text(item.get("due_on"))
            proof_refs = _clean_refs(item.get("proof_refs", ()))
            source_refs = _clean_refs(item.get("source_refs", ()))
        else:
            object_id = _record_id(item)
            object_type = type(item).__name__
            next_action = _field(item, "next_action")
            due_on = _date_text(_field(item, "due_on"))
            proof_refs = _clean_refs(_field(item, "proof_refs", ()))
            source_refs = _clean_refs(_field(item, "source_refs", ()))
        if not object_id or not next_action:
            continue
        key = (object_id, next_action)
        if key in seen:
            continue
        seen.add(key)
        actions.append(
            _without_empty(
                {
                    "object_id": object_id,
                    "object_type": object_type,
                    "next_action": next_action,
                    "due_on": due_on,
                    "source_refs": source_refs,
                    "proof_refs": proof_refs,
                }
            )
        )
    return actions


def _record_missing_refs(records: Iterable[object], omissions: list[dict[str, str]]) -> None:
    for record in records:
        object_id = _record_id(record)
        if object_id and not _clean_refs(agcontentieux.source_reference_ids(record)) and not _clean_refs(agcontentieux.proof_reference_ids(record)):
            omissions.append(
                {
                    "object_id": object_id,
                    "field": "preuve_source",
                    "reason": "aucune source ou preuve diffusable rattachee",
                }
            )


def _track_ref_omissions(
    object_id: str,
    original: object,
    cleaned: Iterable[str],
    field: str,
    omissions: list[dict[str, str]],
) -> None:
    original_refs = tuple(_as_sequence(original))
    cleaned_refs = tuple(cleaned)
    if len(original_refs) > len(cleaned_refs):
        omissions.append(
            {
                "object_id": _sanitize_text(object_id),
                "field": field,
                "reason": "reference locale ou privee retiree",
            }
        )


def _iter_timeline_entries(
    timeline_entries: Iterable[Mapping[str, Any]] | Mapping[str, Iterable[Mapping[str, Any]]],
) -> Iterable[Mapping[str, Any]]:
    if isinstance(timeline_entries, Mapping):
        for entries in timeline_entries.values():
            yield from entries
        return
    yield from timeline_entries


def _field(record: object, field_name: str, default: Any = "") -> Any:
    value = record.get(field_name, default) if isinstance(record, Mapping) else getattr(record, field_name, default)
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, (date, datetime)):
        return _date_text(value)
    return value


def _record_id(record: object) -> str:
    for field_name in ("pack_id", "dossier_id", "case_id", "bundle_id", "note_id", "evidence_id", "request_id"):
        value = _field(record, field_name)
        if value:
            return _sanitize_text(value)
    return ""


def _clean_refs(values: object) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for value in _as_sequence(values):
        ref = _clean_ref(value)
        if not ref or ref in seen:
            continue
        seen.add(ref)
        refs.append(ref)
    return refs


def _clean_ref(value: object) -> str:
    original = _cell(value)
    text = _sanitize_text(value)
    if not text or text == "[chemin-retire]" or _looks_like_private_path(original) or _looks_like_private_path(text):
        return ""
    return text


def _clean_texts(values: object) -> list[str]:
    return [text for text in (_sanitize_text(value) for value in _as_sequence(values)) if text]


def _sanitize_text(value: object) -> str:
    text = _cell(value)
    if not text:
        return ""
    text = re.sub(r"file://\S+", "[chemin-retire]", text, flags=re.IGNORECASE)
    text = re.sub(r"[A-Za-z]:\\[^\s,;)\]]+", "[chemin-retire]", text)
    text = re.sub(r"\\\\[^\s,;)\]]+", "[chemin-retire]", text)
    text = re.sub(r"(?:/Users|/home)/[^\s,;)\]]+", "[chemin-retire]", text, flags=re.IGNORECASE)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[donnee-privee]", text)
    text = re.sub(r"(?<!\d)(?:\+?\d[\d .-]{7,}\d)(?!\d)", "[donnee-privee]", text)
    text = re.sub(r"\brestricted\b", "restreint", text, flags=re.IGNORECASE)
    text = re.sub(r"\braw\b", "brut", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def _looks_like_private_path(value: str) -> bool:
    text = _cell(value)
    if not text:
        return False
    lowered = text.lower().replace("/", "\\")
    if text.lower().startswith("file://"):
        return True
    if re.search(r"^[a-zA-Z]:\\", text) or text.startswith("\\\\"):
        return True
    if "\\" in text:
        return True
    if lowered.startswith("\\users\\") or "\\users\\" in lowered or "\\home\\" in lowered:
        return True
    if "onedrive" in lowered or "\\restricted\\" in lowered or "\\restreint\\" in lowered:
        return True
    return text.startswith("/") and "/" in text[1:]
