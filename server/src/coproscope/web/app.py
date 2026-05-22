from __future__ import annotations

import html
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from ..core.common import InstanceConfig, RunContext
from .depot import (
    DepositError,
    DEPOSIT_CONTEXT_KEYS,
    build_local_export_zip,
    create_deposit_from_uploads,
    latest_deposit_manifest,
    read_deposit_manifest,
    run_accounting_pipeline,
    run_all_non_heavy_pipeline,
    run_docai_pipeline,
    run_docops_pipeline,
    run_light_pipeline,
)
from .context_banner import build_context_banner
from .memory_event_view import DEMO_MEMORY_EVENT_ID, build_memory_event_detail, public_memory_event_id
from .passation_blocker_view import build_passation_blocker_detail, enrich_passation_preview_blocker_links
from .viewmodel import actions_to_csv, actions_to_markdown, build_dashboard_model, filter_action_items

try:  # Optional dependency: create_app raises a clearer error when it is absent.
    from fastapi import Request as FastAPIRequest  # type: ignore
except ImportError:  # pragma: no cover - depends on optional extra
    FastAPIRequest = Any  # type: ignore


PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
TOKEN_COOKIE_NAME = "coproscope_ui_token"
PUBLIC_PATH_PREFIXES = ("/static/",)
PUBLIC_PATHS = {"/health"}
FORBIDDEN_WEB_ROOTS = {
    ".env",
    ".git",
    "logs",
    "private",
    "raw",
    "restricted",
}
FORBIDDEN_EXPORT_PARTS = {
    ".env",
    ".git",
    "logs",
    "private",
    "raw",
    "restricted",
}
PASSATION_EXPORT_WATERMARK = "export dérivé, non source collaborative"
PASSATION_EXPORT_FORBIDDEN_PATTERNS = (
    re.compile(r"\braw\b", re.IGNORECASE),
    re.compile(r"\brestricted\b", re.IGNORECASE),
    re.compile(r"\blogs\b", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"\\\\"),
    re.compile(r"(?:^|[\\/\s\"'])/(?:Users|home)/", re.IGNORECASE),
    re.compile(r"(?:^|[\\/\s\"'])(?:raw|restricted|logs|private)[\\/]", re.IGNORECASE),
)
PRIVATE_FORM_PATTERNS = (
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"\\\\"),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"(?:^|[\\/\s\"'=])/(?:Users|home)/", re.IGNORECASE),
    re.compile(r"(?:^|[\\/\s\"'=])(?:raw|restricted|logs|private|system)[\\/]", re.IGNORECASE),
)
CONTEXT_BANNER_PAGES = {
    "overview",
    "actions",
    "documents",
    "document_intake",
    "pieces",
    "requests",
    "governance",
    "pilotage",
    "depot",
}
ACTION_ROUTE_MISSING_ID = "reference-locale-masquee"
ACTION_ROUTE_PRIVATE_TOKENS = {"raw", "restricted", "logs", "private", "system"}
ACTION_ROUTE_PRIVATE_ROOTS = {"users", "home", "var", "tmp", "etc", "opt", "root", "mnt", "volumes"}
PASSATION_PREVIEW_QUERY_KEYS = {"scope", "selected", "audience"}


def _route_public_tokens(value: str) -> list[str]:
    normalized = value.replace("\\", "/").lower()
    tokenized = "".join(char if char.isalnum() else " " for char in normalized)
    return tokenized.split()


def _contains_private_route_reference(value: object) -> bool:
    normalized = str(value or "").replace("\\", "/").strip().lower()
    if not normalized:
        return False
    tokens = _route_public_tokens(normalized)
    first_token = tokens[0] if tokens else ""
    has_private_path_marker = (
        "file://" in normalized
        or "://" in normalized
        or (len(normalized) > 2 and normalized[1:3] == ":/")
        or normalized.startswith("//")
        or normalized.startswith("/")
        or first_token in ACTION_ROUTE_PRIVATE_ROOTS
    )
    return has_private_path_marker or any(token in ACTION_ROUTE_PRIVATE_TOKENS for token in tokens)


def _public_action_route_id(action_id: object) -> str:
    text = " ".join(str(action_id or "").strip().split())[:140]
    if not text or _contains_private_route_reference(text):
        return ACTION_ROUTE_MISSING_ID
    return text


def _collect_action_ids_from_rows(rows: object) -> set[str]:
    action_ids: set[str] = set()
    if not isinstance(rows, list):
        return action_ids
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in ("id", "action_id"):
            action_id = _public_action_route_id(row.get(key))
            if action_id != ACTION_ROUTE_MISSING_ID:
                action_ids.add(action_id)
    return action_ids


def _known_action_route_ids(model: dict[str, object]) -> set[str]:
    action_ids = _collect_action_ids_from_rows(model.get("action_items"))
    action_ids.update(_collect_action_ids_from_rows(model.get("actions")))
    ux = model.get("ux") if isinstance(model.get("ux"), dict) else {}
    registre = ux.get("registre") if isinstance(ux, dict) and isinstance(ux.get("registre"), dict) else {}
    if isinstance(registre, dict):
        action_ids.update(_collect_action_ids_from_rows(registre.get("items")))
        selected = registre.get("selected")
        if isinstance(selected, dict):
            selected_id = _public_action_route_id(selected.get("id") or selected.get("action_id"))
            if selected_id != ACTION_ROUTE_MISSING_ID:
                action_ids.add(selected_id)
        groups = registre.get("ag_groups")
        if isinstance(groups, list):
            for group in groups:
                if isinstance(group, dict):
                    action_ids.update(_collect_action_ids_from_rows(group.get("items")))
    return action_ids


def _known_memoire_event_route_ids(model: dict[str, object]) -> set[str]:
    event_ids: set[str] = set()
    ux = model.get("ux") if isinstance(model.get("ux"), dict) else {}
    memoire = ux.get("memoire") if isinstance(ux, dict) and isinstance(ux.get("memoire"), dict) else {}
    if isinstance(memoire, dict):
        for event in memoire.get("timeline", []):
            if isinstance(event, dict):
                event_id = _public_action_route_id(event.get("id"))
                if event_id != ACTION_ROUTE_MISSING_ID:
                    event_ids.add(event_id)
        for key in ("selected_event", "event_detail"):
            detail = memoire.get(key)
            if isinstance(detail, dict):
                event_id = _public_action_route_id(detail.get("id"))
                if event_id != ACTION_ROUTE_MISSING_ID:
                    event_ids.add(event_id)
    event_detail = ux.get("event_detail") if isinstance(ux, dict) and isinstance(ux.get("event_detail"), dict) else {}
    if isinstance(event_detail, dict):
        event_id = _public_action_route_id(event_detail.get("id"))
        if event_id != ACTION_ROUTE_MISSING_ID:
            event_ids.add(event_id)
    return event_ids


def _document_intake_preparation_rows(year: int) -> list[dict[str, object]]:
    return [
        {
            "doc_id": f"DOC-PREP-PV-{year}",
            "display_name": f"PV assemblee generale {year}",
            "local_reference": f"depot-local/DOC-PREP-PV-{year}",
            "sha256": "a1b2c3d4e5f60718293a4b5c6d7e8f90",
            "file_format": "pdf",
            "size_bytes": "245760",
            "document_type": "PV_AG",
            "domain": "gouvernance",
            "period": str(year),
            "classification_status": "ACCEPTED",
            "privacy_status": "RESERVE_CS",
            "privacy_rationale": "Lecture limitee avant validation de la version diffusable.",
            "attachments": [
                {
                    "piece_label": f"PV AG {year}",
                    "point_id": f"AG-{year}-PREP",
                    "point_label": "Point AG a confirmer",
                    "point_kind": "ag",
                    "action_kind": "verifier",
                    "action_label": "Verifier que le point et la decision cible sont corrects.",
                    "proof_intent": "decision",
                    "proof_label": "Decision votee ou a confirmer.",
                }
            ],
        },
        {
            "doc_id": f"DOC-PREP-FACTURE-{year}",
            "display_name": f"Facture entretien {year}",
            "local_reference": f"depot-local/DOC-PREP-FACTURE-{year}",
            "sha256": "abcdef1234567890abcdef1234567890",
            "file_format": "pdf",
            "size_bytes": "98304",
            "document_type": "Facture",
            "domain": "comptes",
            "period": str(year),
            "classification_status": "PROPOSED",
            "privacy_status": "A_ARBITRER",
            "privacy_rationale": "A confirmer avant tout partage hors instance locale.",
        },
        {
            "doc_id": f"DOC-PREP-BIFFAGE-{year}",
            "display_name": "Devis travaux a biffer",
            "local_reference": f"depot-local/DOC-PREP-BIFFAGE-{year}",
            "sha256": "0123456789abcdef0123456789abcdef",
            "file_format": "pdf",
            "size_bytes": "372736",
            "document_type": "Devis",
            "domain": "travaux",
            "period": str(year),
            "classification_status": "ACCEPTED",
            "privacy_status": "A_BIFFER",
            "privacy_rationale": "Une version diffusable doit masquer les donnees non partageables.",
            "required_derivative": f"derivees/DOC-PREP-BIFFAGE-{year}-biffe",
            "attachments": [
                {
                    "piece_label": "Devis travaux",
                    "point_label": "Travaux a preparer",
                    "point_kind": "chantier",
                    "action_kind": "biffer",
                    "action_label": "Preparer la version diffusable.",
                    "proof_intent": "presence",
                    "proof_label": "Version biffee disponible.",
                }
            ],
        },
    ]


def _require_web_stack():
    try:
        from fastapi import FastAPI, HTTPException, Request  # type: ignore
        from fastapi.responses import HTMLResponse, RedirectResponse, Response  # type: ignore
        from fastapi.staticfiles import StaticFiles  # type: ignore
        from fastapi.templating import Jinja2Templates  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "UI dependencies are missing. Install them with: python -m pip install -e .[ui]"
        ) from exc
    return FastAPI, HTTPException, Request, HTMLResponse, RedirectResponse, Response, StaticFiles, Jinja2Templates


def _refs(*values: object) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in ("", None):
            continue
        items = value if isinstance(value, (list, tuple, set)) else [value]
        for item in items:
            text = str(item).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            refs.append(text)
    return refs


def _list_of_dicts(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _passation_display_text(value: object, fallback: str = "") -> str:
    text = " ".join(str(value or fallback).replace("_", " ").split())
    return re.sub(r"\b(20\d{2})-(\d{2})-(\d{2})\b", r"\3/\2/\1", text)


def _memoire_passation_projection(
    instance: InstanceConfig,
    year: int,
    *,
    dashboard_model: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        model = dashboard_model if dashboard_model is not None else build_dashboard_model(instance, year)
    except Exception:
        return {"open_points": [], "timeline_entries": [], "document_bundle": None}
    ux = model.get("ux") if isinstance(model.get("ux"), dict) else {}
    memoire = ux.get("memoire") if isinstance(ux.get("memoire"), dict) else {}
    passation = memoire.get("passation") if isinstance(memoire.get("passation"), dict) else {}
    transmit = memoire.get("transmit") if isinstance(memoire.get("transmit"), dict) else {}

    open_points = []
    for topic in _list_of_dicts(passation.get("open_topics"))[:12]:
        title = _passation_display_text(topic.get("title"), "Sujet ouvert")
        next_step = _passation_display_text(topic.get("next_step"))
        open_points.append(f"{title}: {next_step}" if next_step else title)

    timeline_entries = []
    for event in _list_of_dicts(memoire.get("timeline"))[:30]:
        event_id = str(event.get("id") or "").strip()
        document_refs = _refs(event.get("document_refs"))
        title = _passation_display_text(event.get("title"), "Evenement memoire")
        subtitle = _passation_display_text(event.get("subtitle"))
        summary = " - ".join(part for part in (title, subtitle) if part)
        timeline_entries.append(
            {
                "timeline_id": event_id,
                "object_id": event_id,
                "source": "memoire_copropriete",
                "source_id": event_id,
                "occurred_at": event.get("date_label") or event.get("date_iso") or "",
                "event_type": event.get("kind") or event.get("category_label") or "memoire",
                "status": event.get("status", ""),
                "proof_ref": document_refs[0] if document_refs else "",
                "summary": summary,
                "comment": _passation_display_text(event.get("passation_note") or event.get("next_action")),
            }
        )

    evidence_refs = []
    for document in _list_of_dicts(transmit.get("items"))[:30]:
        document_id = str(document.get("id") or "").strip()
        if not document_id:
            continue
        can_download = bool(document.get("can_download"))
        evidence_refs.append(
            {
                "evidence_id": document_id,
                "source_ref": document_id,
                "title": _passation_display_text(document.get("title"), document_id),
                "source_kind": "document_memoire",
                "restriction": "internal" if can_download else "confidential",
                "diffusion": "coproprietaires" if can_download else "cs",
                "status": "pret" if can_download else "a_verifier",
                "next_action": "Verifier la diffusion avant transmission." if not can_download else "",
            }
        )
    document_bundle = None
    if evidence_refs:
        document_bundle = {
            "bundle_id": f"documents-memoire-passation-{year}",
            "title": f"Documents memoire passation {year}",
            "purpose": "Documents publics de la memoire utiles au relais du conseil syndical.",
            "evidence_refs": evidence_refs,
            "source_refs": [item["source_ref"] for item in evidence_refs],
            "proof_refs": [item["evidence_id"] for item in evidence_refs],
        }
    return {
        "open_points": open_points,
        "timeline_entries": timeline_entries,
        "document_bundle": document_bundle,
    }


def _passation_export_document(
    instance: InstanceConfig,
    year: int,
    *,
    scope: str = "",
    selected: str = "",
    dashboard_model: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from ..modules.passation_exports import build_passation_derived_export
    from ..modules.requestops import read_request_register
    from .agcontentieux_view import build_agcontentieux_passation_view

    view = build_agcontentieux_passation_view(instance, year)
    memoire_projection = _memoire_passation_projection(instance, year, dashboard_model=dashboard_model)
    dossiers = [
        {
            "dossier_id": item.get("id", ""),
            "title": item.get("title", ""),
            "ag_date": item.get("ag_date", ""),
            "questions": [
                {
                    "question_id": question.get("id", ""),
                    "dossier_ag_id": question.get("dossier_id", ""),
                    "title": question.get("title", ""),
                    "objective": question.get("objective", ""),
                    "source_refs": _refs(question.get("source_ref"), question.get("source_refs")),
                    "proof_refs": _refs(question.get("proof_ref"), question.get("proof_refs")),
                    "restriction": question.get("restriction", ""),
                    "diffusion": question.get("diffusion", ""),
                    "status": question.get("status", ""),
                    "next_action": question.get("next_action", ""),
                    "due_on": question.get("due_on", ""),
                }
                for question in item.get("questions", [])
            ],
            "pieces": [
                {
                    "piece_id": piece.get("id", ""),
                    "dossier_ag_id": piece.get("dossier_id", ""),
                    "label": piece.get("title", ""),
                    "source_refs": _refs(piece.get("source_ref"), piece.get("source_refs")),
                    "proof_refs": _refs(piece.get("proof_ref"), piece.get("proof_refs")),
                    "restriction": piece.get("restriction", ""),
                    "diffusion": piece.get("diffusion", ""),
                    "status": piece.get("status", ""),
                    "next_action": piece.get("next_action", ""),
                    "due_on": piece.get("due_on", ""),
                }
                for piece in item.get("pieces", [])
            ],
            "source_refs": _refs(item.get("source_ref"), item.get("source_refs")),
            "proof_refs": _refs(item.get("proof_ref"), item.get("proof_refs")),
            "restriction": item.get("restriction", ""),
            "diffusion": item.get("diffusion", ""),
            "status": item.get("status", ""),
            "next_action": item.get("next_action", ""),
            "due_on": item.get("due_on", ""),
        }
        for item in view["ag"]["dossiers"]
    ]
    contentieux_cases = [
        {
            "case_id": item.get("id", ""),
            "title": item.get("title", ""),
            "matter": item.get("matter", ""),
            "source_refs": _refs(item.get("source_ref"), item.get("source_refs")),
            "proof_refs": _refs(item.get("proof_ref"), item.get("proof_refs")),
            "restriction": item.get("restriction", ""),
            "diffusion": item.get("diffusion", ""),
            "status": item.get("status", ""),
            "next_action": item.get("next_action", ""),
            "due_on": item.get("due_on", ""),
        }
        for item in view["contentieux"]["cases"]
    ]
    legal_risk_notes = [
        {
            "note_id": item.get("id", ""),
            "subject": item.get("title", ""),
            "observations": item.get("observations", []),
            "risk_signals": item.get("risk_signals", []),
            "scope_notice": item.get("scope_notice", ""),
            "source_refs": _refs(item.get("source_ref"), item.get("source_refs")),
            "proof_refs": _refs(item.get("proof_ref"), item.get("proof_refs")),
            "restriction": item.get("restriction", ""),
            "diffusion": item.get("diffusion", ""),
            "status": item.get("status", ""),
            "next_action": item.get("next_action", ""),
            "due_on": item.get("due_on", ""),
        }
        for item in view["contentieux"]["risk_notes"]
    ]
    evidence_items = view["evidence"]["items"]
    evidence_bundles = []
    if evidence_items:
        evidence_bundles.append(
            {
                "bundle_id": f"preuves-passation-{year}",
                "title": f"Preuves derivees passation {year}",
                "purpose": "References de preuve diffusable pour passation AG/contentieux.",
                "evidence_refs": [
                    {
                        "evidence_id": item.get("id", ""),
                        "source_ref": item.get("source_ref", ""),
                        "title": item.get("title", ""),
                        "source_kind": item.get("source_kind", ""),
                        "source_hash": item.get("source_hash", ""),
                        "captured_on": item.get("captured_on", ""),
                        "restriction": item.get("restriction", ""),
                        "diffusion": item.get("diffusion", ""),
                        "status": item.get("status", ""),
                        "next_action": item.get("next_action", ""),
                        "due_on": item.get("due_on", ""),
                    }
                    for item in evidence_items
                ],
                "source_refs": _refs(*(item.get("source_ref", "") for item in evidence_items)),
                "proof_refs": _refs(*(item.get("id", "") for item in evidence_items)),
            }
        )
    memoire_document_bundle = memoire_projection.get("document_bundle")
    if isinstance(memoire_document_bundle, dict):
        evidence_bundles.append(memoire_document_bundle)

    pack = view["passation"]["pack"]
    passation_pack = {
        "pack_id": pack.get("id", ""),
        "title": pack.get("title", ""),
        "handover_scope": "AG/contentieux, memoire de copropriete, documents et sujets ouverts",
        "dossier_ag_ids": pack.get("dossier_ag_ids", []),
        "contentieux_case_ids": pack.get("contentieux_case_ids", []),
        "evidence_bundle_ids": [item["bundle_id"] for item in evidence_bundles],
        "legal_risk_note_ids": pack.get("legal_risk_note_ids", []),
        "open_points": _refs(pack.get("open_points", []), memoire_projection.get("open_points", [])),
        "proof_refs": _refs(pack.get("evidence_refs", [])),
        "restriction": pack.get("restriction", ""),
        "diffusion": pack.get("diffusion", ""),
        "status": pack.get("status", ""),
        "next_action": pack.get("next_action", ""),
        "due_on": pack.get("due_on", ""),
    }
    try:
        requests = read_request_register(instance)
    except Exception:
        requests = []
    document = build_passation_derived_export(
        title=f"Export passation derive {instance.display_name} {year}",
        passation_pack=passation_pack,
        dossiers_ag=dossiers,
        contentieux_cases=contentieux_cases,
        evidence_bundles=evidence_bundles,
        legal_risk_notes=legal_risk_notes,
        requests=requests,
        timeline_entries=memoire_projection.get("timeline_entries", []),
        export_id=f"{instance.instance_id}-passation-{year}",
    )
    document["watermark"] = PASSATION_EXPORT_WATERMARK
    if scope == "event" and selected:
        document = _passation_export_for_event(document, selected)
    return document


def _passation_export_for_event(document: dict[str, Any], selected: str) -> dict[str, Any]:
    selected_id = str(selected or "").strip()
    if not selected_id or _contains_private_route_reference(selected_id):
        return document
    scoped = dict(document)
    sections = dict(scoped.get("sections")) if isinstance(scoped.get("sections"), dict) else {}
    chronologie = _list_of_dicts(sections.get("chronologie"))
    entries = [
        item
        for item in chronologie
        if selected_id
        in {
            str(item.get("object_id") or ""),
            str(item.get("timeline_id") or ""),
            str(item.get("source_id") or ""),
        }
    ]
    refs = {
        str(ref)
        for item in entries
        for ref in [
            item.get("object_id"),
            item.get("timeline_id"),
            item.get("source_id"),
            *list(item.get("proof_refs") or []),
        ]
        if str(ref or "").strip()
    }
    filtered_sections = dict(sections)
    filtered_sections["chronologie"] = entries
    filtered_sections["ag"] = []
    filtered_sections["contentieux"] = []
    filtered_sections["vigilance"] = []
    filtered_sections["demandes"] = [
        item
        for item in _list_of_dicts(sections.get("demandes"))
        if refs
        & {
            str(item.get("object_id") or ""),
            str(item.get("origin_id") or ""),
            str(item.get("related_action_id") or ""),
            *[str(ref) for ref in (item.get("source_refs") or [])],
            *[str(ref) for ref in (item.get("proof_refs") or [])],
        }
    ]
    filtered_proofs = []
    for bundle in _list_of_dicts(sections.get("preuves")):
        evidence_refs = [
            ref
            for ref in _list_of_dicts(bundle.get("evidence_refs"))
            if refs
            & {
                str(ref.get("object_id") or ""),
                str(ref.get("evidence_id") or ""),
                str(ref.get("source_ref") or ""),
            }
        ]
        if evidence_refs:
            copy = dict(bundle)
            copy["evidence_refs"] = evidence_refs
            copy["source_refs"] = [ref.get("source_ref") for ref in evidence_refs if ref.get("source_ref")]
            copy["proof_refs"] = [
                ref.get("object_id") or ref.get("evidence_id") or ref.get("source_ref")
                for ref in evidence_refs
                if ref.get("object_id") or ref.get("evidence_id") or ref.get("source_ref")
            ]
            filtered_proofs.append(copy)
    filtered_sections["preuves"] = filtered_proofs
    passation = dict(sections.get("passation")) if isinstance(sections.get("passation"), dict) else {}
    if entries:
        entry = entries[0]
        summary = str(entry.get("summary") or selected_id)
        passation["title"] = f"Extrait passation - {summary}"
        passation["open_points"] = [
            summary,
            str(entry.get("comment") or "Evenement memoire a transmettre avec ses limites."),
            str(entry.get("status") or "Statut a verifier"),
        ]
        passation["proof_refs"] = sorted(refs)
        scoped["title"] = f"{scoped.get('title', 'Export passation derive')} - {summary}"
    else:
        passation["title"] = f"Extrait passation - {selected_id}"
        passation["open_points"] = ["Evenement introuvable dans le perimetre exportable."]
        passation["proof_refs"] = []
        scoped["title"] = f"{scoped.get('title', 'Export passation derive')} - {selected_id}"
    filtered_sections["passation"] = passation
    scoped["sections"] = filtered_sections
    scoped["scope"] = {
        "kind": "passation_event",
        "selected": selected_id,
        "restriction": passation.get("restriction") or "conseil_syndical",
        "diffusion": passation.get("diffusion") or "conseil_syndical",
    }
    scoped["source_refs"] = sorted(refs)
    scoped["proof_refs"] = sorted(refs)
    scoped["next_actions"] = [
        item
        for item in _list_of_dicts(scoped.get("next_actions"))
        if refs
        & {
            str(item.get("object_id") or ""),
            *[str(ref) for ref in (item.get("source_refs") or [])],
            *[str(ref) for ref in (item.get("proof_refs") or [])],
        }
    ]
    scoped["omissions"] = [
        item
        for item in _list_of_dicts(scoped.get("omissions"))
        if selected_id in str(item) or bool(refs & {str(value) for value in item.values()})
    ]
    return scoped


def _scoped_passation_preview(preview: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
    scope = document.get("scope") if isinstance(document.get("scope"), dict) else {}
    if scope.get("kind") != "passation_event":
        return preview
    scoped_preview = dict(preview)
    sections = dict(document.get("sections")) if isinstance(document.get("sections"), dict) else {}
    passation = dict(sections.get("passation")) if isinstance(sections.get("passation"), dict) else {}
    chronologie = _list_of_dicts(sections.get("chronologie"))
    demandes = _list_of_dicts(sections.get("demandes"))
    preuves = _list_of_dicts(sections.get("preuves"))
    proof_refs = [str(ref) for ref in document.get("proof_refs", []) if str(ref or "").strip()]
    omissions = _list_of_dicts(document.get("omissions"))
    selected_id = str(scope.get("selected") or "").strip()
    restriction = str(scope.get("restriction") or "").strip()
    event_title = str(passation.get("title") or document.get("title") or "Extrait de passation").strip()
    open_points = [str(item) for item in passation.get("open_points", []) if str(item or "").strip()]
    if selected_id and not omissions:
        omissions = [
            {
                "id": "BLOCK-FICTIF-RELANCE-ASCENSEUR",
                "label": "Relance ascenseur non tracee",
                "reason": "Date, canal et destinataire doivent etre notes avant de presenter la relance comme faite.",
                "type_label": "Blocage export",
                "review_href": f"/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR?scope=event&selected={quote(selected_id)}",
            }
        ]

    context = dict(scoped_preview.get("context")) if isinstance(scoped_preview.get("context"), dict) else {}
    context.update(
        {
            "title": "Apercu de passation - extrait evenement",
            "subtitle": "Perimetre filtre: seuls cet evenement, ses preuves et ses points ouverts seront telecharges.",
            "scope_label": selected_id,
        }
    )
    scoped_preview["context"] = context

    diffusion_limited_count = 1 if restriction and restriction not in {"diffusable", "public"} else 0
    summary = dict(scoped_preview.get("summary")) if isinstance(scoped_preview.get("summary"), dict) else {}
    summary.update(
        {
            "included_events_count": len(chronologie),
            "open_topics_count": len(open_points),
            "included_actions_count": len(demandes),
            "included_documents_count": len(proof_refs),
            "missing_proofs_count": 0,
            "diffusion_limited_count": diffusion_limited_count,
            "omitted_items_count": len(omissions),
            "can_export": bool(chronologie or open_points or proof_refs),
            "can_export_label": "Extrait pret a relire avant telechargement",
        }
    )
    scoped_preview["summary"] = summary

    scoped_preview["preview"] = {
        "title": event_title,
        "intro": "Apercu strictement limite a l'evenement selectionne dans la memoire.",
        "sections": [
            {
                "id": "perimetre",
                "title": "Perimetre de l'extrait",
                "items": [
                    f"Evenement selectionne: {selected_id or 'a confirmer'}",
                    f"{len(chronologie)} evenement inclus",
                    f"{len(proof_refs)} reference(s) preuve citee(s)",
                ],
            },
            {
                "id": "points",
                "title": "Points ouverts",
                "items": open_points,
                "empty_label": "Aucun point ouvert pour cet evenement.",
            },
        ],
    }

    scoped_preview["included"] = {
        "events": [
            {
                "id": str(item.get("object_id") or item.get("timeline_id") or selected_id),
                "title": str(item.get("summary") or event_title),
                "date_label": str(item.get("occurred_at") or "Date a confirmer"),
                "status_label": str(item.get("status") or "A verifier"),
                "href": f"/chantiers?selected={quote(str(item.get('object_id') or selected_id))}",
            }
            for item in chronologie
        ],
        "actions": [
            {
                "id": str(item.get("object_id") or item.get("request_id") or ""),
                "title": str(item.get("title") or item.get("summary") or "Demande liee"),
                "next_step": str(item.get("next_action") or item.get("status") or "A reprendre."),
                "href": "/demandes",
            }
            for item in demandes
        ],
        "documents": [
            {
                "id": ref,
                "title": ref,
                "diffusion_label": "Reference citee dans l'extrait",
                "href": "/documents",
            }
            for ref in proof_refs
        ],
    }

    scoped_preview["omitted"] = {
        "items": [
            {
                "id": str(item.get("id") or item.get("object_id") or index),
                "label": str(item.get("label") or item.get("title") or "Element exclu ou masque"),
                "reason": str(item.get("reason") or "Hors perimetre de cet extrait."),
                "type_label": str(item.get("type_label") or item.get("object_type") or "Element"),
                "review_href": "/confidentialite",
            }
            for index, item in enumerate(omissions, start=1)
        ],
        "summary_label": f"{len(omissions)} element(s) exclus dans cet extrait.",
    }
    scoped_preview["blockers"] = []
    downloads = dict(scoped_preview.get("downloads")) if isinstance(scoped_preview.get("downloads"), dict) else {}
    downloads["can_download"] = bool(chronologie or open_points or proof_refs)
    downloads["download_disabled_reason"] = "Evenement introuvable dans le perimetre exportable." if not downloads["can_download"] else ""
    scoped_preview["downloads"] = downloads
    empty_states = dict(scoped_preview.get("empty_states")) if isinstance(scoped_preview.get("empty_states"), dict) else {}
    no_content = dict(empty_states.get("no_content")) if isinstance(empty_states.get("no_content"), dict) else {}
    no_content.update(
        {
            "is_visible": not bool(chronologie or open_points or proof_refs),
            "label": "Aucun contenu exportable trouve pour cet evenement.",
            "href": "/chantiers",
        }
    )
    empty_states["no_content"] = no_content
    scoped_preview["empty_states"] = empty_states
    return scoped_preview


def _assert_passation_export_route_safe(payload: str) -> None:
    for pattern in PASSATION_EXPORT_FORBIDDEN_PATTERNS:
        if pattern.search(payload):
            raise ValueError("passation export contains forbidden raw, restricted, log or private-path material")


def _safe_form_text(value: object, *, fallback: str = "") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    if any(pattern.search(text) for pattern in PRIVATE_FORM_PATTERNS):
        return fallback or "[reference locale masquee]"
    return text


def _safe_deposit_context(items: object) -> dict[str, str]:
    context: dict[str, str] = {}
    iterable = items if hasattr(items, "__iter__") else []
    for key, value in iterable:  # type: ignore[misc]
        if key == "token" or key not in DEPOSIT_CONTEXT_KEYS:
            continue
        text = _safe_form_text(value)
        if not text or text == "[reference locale masquee]" or _contains_private_route_reference(text):
            continue
        context[str(key)] = text[:180]
    return context


def _depot_prefill_context(
    instance: InstanceConfig,
    year: int,
    raw_context: dict[str, str],
    *,
    dashboard_model: dict[str, object] | None = None,
) -> dict[str, object]:
    if not raw_context:
        return {"is_visible": False, "hidden_fields": []}
    piece_ref = (
        raw_context.get("piece_detail")
        or raw_context.get("piece_id")
        or raw_context.get("missing_for")
        or raw_context.get("action")
        or ""
    )
    piece_detail: dict[str, object] = {}
    if piece_ref:
        from .piece_detail_view import build_piece_detail

        detail = build_piece_detail(instance, year, piece_ref, dashboard_model=dashboard_model)
        if detail.get("state") == "found":
            piece_detail = detail
    piece = piece_detail.get("piece") if isinstance(piece_detail.get("piece"), dict) else {}
    proof = piece_detail.get("proof") if isinstance(piece_detail.get("proof"), dict) else {}
    diffusion = piece_detail.get("diffusion") if isinstance(piece_detail.get("diffusion"), dict) else {}
    safe_piece_id = _safe_form_text(piece.get("id") or piece_ref, fallback="")
    merged_context = dict(raw_context)
    if safe_piece_id and "piece_detail" not in merged_context:
        merged_context["piece_detail"] = safe_piece_id
    hidden_fields = [
        {"name": key, "value": value}
        for key, value in sorted(merged_context.items())
        if key in DEPOSIT_CONTEXT_KEYS and value
    ]
    return {
        "is_visible": True,
        "title": "Reponse recue pour cette piece",
        "status_label": "Piece candidate a verifier",
        "notice": "La reponse recue restera une piece candidate jusqu'au controle du conseil syndical.",
        "piece_label": _safe_form_text(piece.get("label"), fallback="Piece attendue a rattacher"),
        "proof_expected_label": _safe_form_text(proof.get("expected_label"), fallback="Preuve attendue a preciser"),
        "holder_label": _safe_form_text(piece.get("holder_label"), fallback="Detenteur a confirmer"),
        "diffusion_label": _safe_form_text(diffusion.get("label"), fallback="Diffusion a verifier"),
        "return_href": f"/pieces/{safe_piece_id}" if safe_piece_id else "/pieces?proof=missing",
        "hidden_fields": hidden_fields,
        "context": merged_context,
    }


def _safe_passation_preview_query(request: FastAPIRequest) -> dict[str, str]:
    query: dict[str, str] = {}
    for key, value in request.query_params.items():
        if key == "token" or key not in PASSATION_PREVIEW_QUERY_KEYS:
            continue
        text = str(value or "").strip()
        if not text or _contains_private_route_reference(text):
            continue
        query[key] = text[:140]
    return query


def _html_escape(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def _preview_list(items: object, *, label_key: str = "label", detail_key: str = "reason", empty: str = "Aucun element.") -> str:
    rows = _list_of_dicts(items)[:12]
    if not rows:
        return f"<p>{_html_escape(empty)}</p>"
    rendered = []
    for item in rows:
        label = item.get(label_key) or item.get("title") or item.get("id") or "Element"
        detail = item.get(detail_key) or item.get("detail") or item.get("description") or ""
        count = item.get("count")
        suffix = f" <small>{_html_escape(count)}</small>" if count not in (None, "") else ""
        rendered.append(f"<li><strong>{_html_escape(label)}</strong>{suffix}<br><span>{_html_escape(detail)}</span></li>")
    return "<ul>" + "".join(rendered) + "</ul>"


def _render_passation_preview_html(
    preview: dict[str, Any],
    *,
    query: dict[str, str],
    links: dict[str, str],
) -> str:
    context = preview.get("context") if isinstance(preview.get("context"), dict) else {}
    summary = preview.get("summary") if isinstance(preview.get("summary"), dict) else {}
    restrictions = preview.get("restrictions") if isinstance(preview.get("restrictions"), dict) else {}
    preview_block = preview.get("preview") if isinstance(preview.get("preview"), dict) else {}
    included = preview.get("included") if isinstance(preview.get("included"), dict) else {}
    title = context.get("title") or "Apercu de passation"
    watermark = PASSATION_EXPORT_WATERMARK or preview.get("watermark") or context.get("watermark")
    source_of_truth = "false" if preview.get("source_of_truth") is False or context.get("source_of_truth") is False else "true"
    sections = _list_of_dicts(preview.get("sections_included"))
    formats = _list_of_dicts(preview.get("formats_available") or preview.get("formats"))
    format_rows = []
    for item in formats:
        format_id = str(item.get("id") or "").lower()
        href = links.get(format_id) or item.get("href") or "#"
        format_rows.append(
            {
                "label": item.get("label") or format_id.upper(),
                "description": item.get("description") or "",
                "href": href,
            }
        )
    section_items = _preview_list(sections, detail_key="id", empty="Aucune section incluse.")
    excluded_items = _preview_list(
        preview.get("excluded_or_blocked") or preview.get("blockers"),
        detail_key="reason",
        empty="Aucun element exclu ou bloque.",
    )
    events = _preview_list(included.get("events"), label_key="title", detail_key="next_action", empty="Aucun evenement inclus.")
    documents = _preview_list(included.get("documents"), label_key="title", detail_key="diffusion_label", empty="Aucun document inclus.")
    preview_sections = _preview_list(preview_block.get("sections"), label_key="title", detail_key="id", empty="Aucune section d'apercu.")
    format_html = (
        "<ul>"
        + "".join(
            f"<li><a href=\"{_html_escape(item['href'])}\"><strong>{_html_escape(item['label'])}</strong></a><br>"
            f"<span>{_html_escape(item['description'])}</span></li>"
            for item in format_rows
        )
        + "</ul>"
        if format_rows
        else "<p>Aucun format disponible.</p>"
    )
    query_label = ", ".join(f"{key}={value}" for key, value in query.items()) or "handover"
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="fr">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            f"  <title>{_html_escape(title)} - CoproScope</title>",
            "</head>",
            "<body>",
            '  <main data-route="/exports/passation">',
            f"    <p>{_html_escape(watermark)}</p>",
            f"    <h1>{_html_escape(title)}</h1>",
            f"    <p>{_html_escape(context.get('subtitle') or 'Apercu verifiable avant telechargement.')}</p>",
            "    <dl>",
            f"      <dt>source_of_truth</dt><dd>{source_of_truth}</dd>",
            f"      <dt>Perimetre</dt><dd>{_html_escape(query_label)}</dd>",
            f"      <dt>Evenements inclus</dt><dd>{_html_escape(summary.get('included_events_count', 0))}</dd>",
            f"      <dt>Documents inclus</dt><dd>{_html_escape(summary.get('included_documents_count', 0))}</dd>",
            f"      <dt>Sujets ouverts</dt><dd>{_html_escape(summary.get('open_topics_count', 0))}</dd>",
            f"      <dt>Restriction</dt><dd>{_html_escape(restrictions.get('label') or 'Diffusion a relire')}</dd>",
            "    </dl>",
            "    <nav aria-label=\"Telechargements derives\">",
            f"      <a href=\"{_html_escape(links.get('txt', '#'))}\">Telecharger TXT</a>",
            f"      <a href=\"{_html_escape(links.get('json', '#'))}\">Telecharger JSON</a>",
            f"      <a href=\"{_html_escape(links.get('self', '/exports/passation'))}\">Actualiser l'apercu</a>",
            "    </nav>",
            "    <section><h2>Sections incluses</h2>",
            section_items,
            "    </section>",
            "    <section><h2>Elements exclus ou bloques</h2>",
            excluded_items,
            "    </section>",
            "    <section><h2>Restrictions</h2>",
            f"      <p>{_html_escape(restrictions.get('reason') or 'Relire avant partage externe.')}</p>",
            "    </section>",
            "    <section><h2>Apercu de contenu</h2>",
            preview_sections,
            "    </section>",
            "    <section><h2>Evenements</h2>",
            events,
            "    </section>",
            "    <section><h2>Documents</h2>",
            documents,
            "    </section>",
            "    <section><h2>Formats disponibles</h2>",
            format_html,
            "    </section>",
            "  </main>",
            "</body>",
            "</html>",
        ]
    )


def create_app(instance: InstanceConfig, year: int = 2025, access_token: str | None = None):
    FastAPI, HTTPException, Request, HTMLResponse, RedirectResponse, Response, StaticFiles, Jinja2Templates = _require_web_stack()

    app = FastAPI(title="CoproScope local", docs_url=None, redoc_url=None)
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    def _is_public_path(path: str) -> bool:
        return path in PUBLIC_PATHS or any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES)

    def _request_has_token(request: FastAPIRequest) -> bool:
        if not access_token:
            return False
        supplied = (
            request.query_params.get("token")
            or request.headers.get("x-coproscope-token", "")
            or request.cookies.get(TOKEN_COOKIE_NAME, "")
        )
        return bool(supplied and secrets.compare_digest(str(supplied), access_token))

    def _require_token(request: FastAPIRequest) -> None:
        if not access_token:
            return
        if not _request_has_token(request):
            raise HTTPException(status_code=403, detail="Jeton local requis.")

    def _token_suffix(request: FastAPIRequest) -> str:
        if not access_token or not _request_has_token(request):
            return ""
        return f"token={quote(access_token)}"

    def _token_value(request: FastAPIRequest) -> str:
        if not access_token or not _request_has_token(request):
            return ""
        return access_token

    def _url_with_token(request: FastAPIRequest, path: str) -> str:
        suffix = _token_suffix(request)
        if not suffix:
            return path
        separator = "&" if "?" in path else "?"
        return f"{path}{separator}{suffix}"

    @app.middleware("http")
    async def _local_token_gate(request: FastAPIRequest, call_next):  # type: ignore[no-untyped-def]
        if access_token and not _is_public_path(str(request.url.path)) and not _request_has_token(request):
            return Response("Jeton local requis.", status_code=403, media_type="text/plain; charset=utf-8")
        response = await call_next(request)
        if access_token and _request_has_token(request):
            response.set_cookie(
                TOKEN_COOKIE_NAME,
                access_token,
                httponly=True,
                samesite="lax",
                secure=False,
            )
        return response

    def context(request: FastAPIRequest, page: str, **extra: object) -> dict[str, object]:
        model = extra.pop("model", None)
        if model is None:
            model = build_dashboard_model(instance, year)
        values: dict[str, object] = {
            "request": request,
            "page": page,
            "model": model,
            "ui_token_query": f"?{_token_suffix(request)}" if _token_suffix(request) else "",
            "ui_token_param": _token_suffix(request),
            "pilotage_route_enabled": True,
        }
        if page in CONTEXT_BANNER_PAGES:
            values["context_banner"] = build_context_banner(
                instance,
                next_action_href=_url_with_token(request, "/gouvernance"),
            )
        values.update(extra)
        return values

    def _filtered_actions(scope: str = "", priority: str = "", status: str = "") -> tuple[dict[str, object], list[dict[str, str]]]:
        model = build_dashboard_model(instance, year)
        actions = filter_action_items(
            model["action_items"],  # type: ignore[arg-type]
            scope=scope,
            priority=priority,
            status=status,
        )
        return model, actions

    def _query_suffix(scope: str = "", priority: str = "", status: str = "", token: str = "") -> str:
        query = {
            key: value
            for key, value in {
                "scope": scope,
                "priority": priority,
                "status": status,
                "token": token,
            }.items()
            if value
        }
        return f"?{urlencode(query)}" if query else ""

    def _download_headers(filename: str) -> dict[str, str]:
        return {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        }

    @app.get("/", response_class=HTMLResponse)
    def overview(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="overview.html", context=context(request, "overview"))

    @app.get("/actions", response_class=HTMLResponse)
    def actions(request: FastAPIRequest, scope: str = "", priority: str = "", status: str = ""):
        model, rows = _filtered_actions(scope=scope, priority=priority, status=status)
        return templates.TemplateResponse(
            request=request,
            name="actions.html",
            context=context(
                request,
                "actions",
                model=model,
                action_rows=rows,
                action_filters={
                    "scope": scope or "tous",
                    "priority": priority or "tous",
                    "status": status or "tous",
                },
                action_query_suffix=_query_suffix(scope=scope, priority=priority, status=status, token=_token_value(request)),
            ),
        )

    @app.get("/actions/{action_id}")
    def action_detail(request: FastAPIRequest, action_id: str):
        public_action_id = _public_action_route_id(action_id)
        query_name = "selected" if public_action_id in _known_action_route_ids(build_dashboard_model(instance, year)) else "action_missing"
        target = f"/actions?{urlencode({query_name: public_action_id})}"
        return RedirectResponse(_url_with_token(request, target), status_code=303)

    @app.get("/comptes", response_class=HTMLResponse)
    def accounting(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="accounting.html", context=context(request, "accounting"))

    @app.get("/documents", response_class=HTMLResponse)
    def documents(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="documents.html", context=context(request, "documents"))

    @app.get("/documents/ajouter", response_class=HTMLResponse)
    def document_intake_page(request: FastAPIRequest):
        from .document_intake_view import template_context

        _require_token(request)
        return templates.TemplateResponse(
            request=request,
            name="document_intake.html",
            context=context(
                request,
                "document_intake",
                **template_context(_document_intake_preparation_rows(year)),
            ),
        )

    @app.get("/documents/{doc_id}", response_class=HTMLResponse)
    def document_detail(request: FastAPIRequest, doc_id: str):
        from .document_viewer import DocumentNotFoundError, build_document_detail

        try:
            detail = build_document_detail(instance, doc_id)
        except DocumentNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Document introuvable.") from exc
        return templates.TemplateResponse(
            request=request,
            name="document_detail.html",
            context=context(request, "documents", document_detail=detail),
        )

    @app.get("/pieces", response_class=HTMLResponse)
    def pieces(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="pieces.html", context=context(request, "pieces"))

    @app.get("/pieces/{piece_id}", response_class=HTMLResponse)
    def piece_detail(request: FastAPIRequest, piece_id: str):
        from .piece_detail_view import build_piece_detail

        model = build_dashboard_model(instance, year)
        detail = build_piece_detail(instance, year, piece_id, dict(request.query_params), dashboard_model=model)
        return templates.TemplateResponse(
            request=request,
            name="piece_detail.html",
            context=context(request, "pieces", model=model, piece_detail=detail),
        )

    @app.get("/demandes", response_class=HTMLResponse)
    def requests_page(request: FastAPIRequest):
        from .requests_view import template_context

        _require_token(request)
        return templates.TemplateResponse(
            request=request,
            name="requests.html",
            context=context(request, "requests", **template_context(instance, year)),
        )

    @app.post("/demandes")
    async def create_request(request: FastAPIRequest):
        from ..modules import requestops

        _require_token(request)
        form = await request.form()
        subject = _safe_form_text(form.get("subject"))
        if not subject:
            raise HTTPException(status_code=422, detail="Sujet requis.")
        channel = str(form.get("channel") or requestops.CHANNEL_EMAIL).strip()
        source_ref = _safe_form_text(form.get("source_ref"))
        visibility = str(form.get("visibility") or requestops.VISIBILITY_CS).strip()
        next_action = _safe_form_text(form.get("next_action"))
        today = datetime.now(timezone.utc).date().isoformat()
        request_id = f"REQ-UI-{secrets.token_hex(4).upper()}"
        row = {
            "request_id": request_id,
            "received_at": today,
            "author_label": "membre_cs_demo",
            "author_role": "conseil_syndical",
            "channel": channel,
            "subject": subject,
            "summary": subject,
            "proof_ref": "",
            "source_ref": source_ref or "source_locale_a_rattacher",
            "status": requestops.STATUS_TO_QUALIFY,
            "next_action": next_action or "Qualifier la demande puis rattacher la preuve ou la reponse attendue.",
            "related_point_id": "",
            "related_action_id": "",
            "visibility": visibility,
            "origin_kind": "ui_demo",
            "origin_id": request_id,
            "notes": "Creation depuis l'interface locale; donnees de demonstration uniquement.",
        }
        existing = requestops.read_request_register(instance)
        new_request = requestops.normalize_request(row)
        run = RunContext(instance, "ui create request")
        try:
            requestops.write_request_register(instance, run, [*existing, new_request])
        except Exception:
            run.finish("FAILED", f"request {request_id} not created")
            raise
        else:
            run.finish("OK", f"created request {request_id}")
        return RedirectResponse(
            url=_url_with_token(request, f"/demandes?status=created&request_id={request_id}#nouvelle-demande"),
            status_code=303,
        )

    @app.get("/demandes/relance", response_class=HTMLResponse)
    def relance_syndic_page(
        request: FastAPIRequest,
        request_id: str = "",
        action_id: str = "",
        piece_id: str = "",
        piece_detail: str = "",
        sent: str = "",
        sent_id: str = "",
    ):
        from .relance_syndic_view import build_relance_syndic_view

        _require_token(request)
        model = build_dashboard_model(instance, year) if piece_detail or piece_id else None
        return templates.TemplateResponse(
            request=request,
            name="relance_syndic.html",
            context=context(
                request,
                "requests",
                model=model,
                relance=build_relance_syndic_view(
                    instance,
                    year,
                    request_id=request_id,
                    action_id=action_id,
                    piece_id=piece_id,
                    piece_detail=piece_detail,
                    sent=sent,
                    sent_id=sent_id,
                    dashboard_model=model,
                ),
            ),
        )

    @app.post("/demandes/relance")
    async def validate_relance_syndic(request: FastAPIRequest):
        from ..modules import requestops

        _require_token(request)
        form = await request.form()
        request_id = _safe_form_text(form.get("request_id"))
        if not request_id:
            raise HTTPException(status_code=422, detail="Demande requise.")
        try:
            requests = requestops.read_request_register(instance)
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Registre demandes indisponible.") from exc
        selected = next((item for item in requests if item.request_id == request_id), None)
        if selected is None:
            raise HTTPException(status_code=404, detail="Demande introuvable.")
        try:
            existing_actions = requestops.normalize_actions(
                requestops.rows_from_csv(requestops.request_action_log_path(instance).read_text(encoding="utf-8-sig"))
            )
        except (OSError, ValueError):
            existing_actions = []
        today = datetime.now(timezone.utc).date().isoformat()
        sent_date = _safe_form_text(form.get("sent_date")) or today
        sent_channel = _safe_form_text(form.get("sent_channel")) or "canal a preciser"
        sent_recipient = _safe_form_text(form.get("sent_recipient")) or "destinataire a preciser"
        sent_note = _safe_form_text(form.get("sent_note"))
        summary = (
            "Relance fictive notee hors CoproScope: "
            f"date {sent_date}, canal {sent_channel}, destinataire {sent_recipient}."
        )
        if sent_note:
            summary = f"{summary} Note: {sent_note}"
        action = requestops.normalize_action(
            {
                "journal_id": f"JRN-UI-RELANCE-{secrets.token_hex(4).upper()}",
                "request_id": request_id,
                "occurred_at": today,
                "actor_role": "conseil_syndical",
                "action_type": "relance",
                "summary": summary,
                "proof_ref": selected.proof_ref,
                "source_ref": selected.source_ref,
                "status_after": requestops.STATUS_FOLLOW_UP,
                "next_action": "Attendre la reponse du syndic puis rattacher la piece recue.",
                "visibility": selected.visibility,
            }
        )
        run = RunContext(instance, "ui validate syndic followup")
        try:
            requestops.write_request_action_log(instance, run, [*existing_actions, action])
        except Exception:
            run.finish("FAILED", f"followup {request_id} not recorded")
            raise
        else:
            run.finish("OK", f"followup {request_id} recorded")
        return RedirectResponse(
            url=_url_with_token(request, f"/demandes/relance?request_id={request_id}&sent=1&sent_id={action.journal_id}"),
            status_code=303,
        )

    @app.get("/ag-contentieux", response_class=HTMLResponse)
    def agcontentieux_page(request: FastAPIRequest):
        from .agcontentieux_view import build_agcontentieux_passation_view

        _require_token(request)
        return templates.TemplateResponse(
            request=request,
            name="agcontentieux.html",
            context=context(
                request,
                "agcontentieux",
                agcontentieux=build_agcontentieux_passation_view(instance, year),
            ),
        )

    @app.get("/gouvernance", response_class=HTMLResponse)
    def governance(request: FastAPIRequest):
        from .governance import build_governance_overview

        return templates.TemplateResponse(
            request=request,
            name="governance.html",
            context=context(request, "governance", governance=build_governance_overview(instance, year)),
        )

    @app.get("/pilotage", response_class=HTMLResponse)
    def pilotage(request: FastAPIRequest):
        _require_token(request)
        from .pilotage_view import build_pilotage_view

        pilotage_view = build_pilotage_view(instance=instance, period_label=str(year), source_label="pilotageops")
        return templates.TemplateResponse(
            request=request,
            name="pilotage.html",
            context=context(request, "pilotage", pilotage=pilotage_view, pilotage_view=pilotage_view),
        )

    @app.get("/confidentialite", response_class=HTMLResponse)
    def privacy(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="privacy.html", context=context(request, "privacy"))

    @app.get("/chantiers", response_class=HTMLResponse)
    def workstreams(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="workstreams.html", context=context(request, "workstreams"))

    @app.get("/chantiers/{event_id}")
    def workstream_detail(request: FastAPIRequest, event_id: str):
        public_event_id = public_memory_event_id(event_id)
        if public_event_id == DEMO_MEMORY_EVENT_ID:
            return templates.TemplateResponse(
                request=request,
                name="memory_event_detail.html",
                context=context(
                    request,
                    "workstreams",
                    memory_event=build_memory_event_detail(public_event_id, dict(request.query_params)),
                ),
            )
        query_name = "selected" if public_event_id in _known_memoire_event_route_ids(build_dashboard_model(instance, year)) else "event_missing"
        target = f"/chantiers?{urlencode({query_name: public_event_id})}"
        return RedirectResponse(_url_with_token(request, target), status_code=303)

    @app.get("/depot", response_class=HTMLResponse)
    def depot_page(request: FastAPIRequest, depot: str = "", status: str = ""):
        _require_token(request)
        selected = read_deposit_manifest(instance, depot) if depot else latest_deposit_manifest(instance)
        depot_context = _safe_deposit_context(request.query_params.items())
        model = build_dashboard_model(instance, year) if any(
            depot_context.get(key) for key in ("piece_detail", "piece_id", "missing_for", "action")
        ) else None
        return templates.TemplateResponse(
            request=request,
            name="depot.html",
            context=context(
                request,
                "depot",
                model=model,
                selected_deposit=selected,
                pipeline_status=status,
                depot_prefill=_depot_prefill_context(instance, year, depot_context, dashboard_model=model),
            ),
        )

    @app.post("/depot")
    async def depot_upload(request: FastAPIRequest):
        _require_token(request)
        form = await request.form()
        uploads = [value for key, value in form.multi_items() if key in {"files", "file"}]
        depot_context = _safe_deposit_context(form.multi_items())
        try:
            manifest = create_deposit_from_uploads(instance, uploads, context=depot_context)
        except DepositError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        run_light_pipeline(instance, manifest)
        return RedirectResponse(
            url=_url_with_token(request, f"/depot?depot={manifest['deposit_id']}&status=uploaded"),
            status_code=303,
        )

    @app.post("/depot/{deposit_id}/pipeline/{pipeline}")
    def depot_pipeline(request: FastAPIRequest, deposit_id: str, pipeline: str):
        _require_token(request)
        manifest = read_deposit_manifest(instance, deposit_id)
        if manifest is None:
            raise HTTPException(status_code=404, detail="Depot introuvable.")
        if pipeline == "docai":
            run_docai_pipeline(instance, manifest)
        elif pipeline == "docops":
            run_docops_pipeline(instance, manifest)
        elif pipeline == "compta":
            run_accounting_pipeline(instance, manifest, year)
        elif pipeline == "all":
            run_all_non_heavy_pipeline(instance, manifest, year)
        else:
            raise HTTPException(status_code=404, detail="Pipeline inconnu.")
        return RedirectResponse(
            url=_url_with_token(request, f"/depot?depot={deposit_id}&status={pipeline}"),
            status_code=303,
        )

    @app.get("/api/model")
    def api_model(request: FastAPIRequest):
        _require_token(request)
        return build_dashboard_model(instance, year)

    @app.get("/exports/actions.csv")
    def export_actions_csv(request: FastAPIRequest, scope: str = "", priority: str = "", status: str = ""):
        _require_token(request)
        _, rows = _filtered_actions(scope=scope, priority=priority, status=status)
        return Response(
            content=actions_to_csv(rows),
            media_type="text/csv; charset=utf-8",
            headers=_download_headers(f"coproscope_actions_{year}.csv"),
        )

    @app.get("/exports/actions.md")
    def export_actions_markdown(request: FastAPIRequest, scope: str = "", priority: str = "", status: str = ""):
        _require_token(request)
        _, rows = _filtered_actions(scope=scope, priority=priority, status=status)
        return Response(
            content=actions_to_markdown(rows),
            media_type="text/markdown; charset=utf-8",
            headers=_download_headers(f"coproscope_actions_{year}.md"),
        )

    @app.get("/exports/local.zip")
    def export_local_zip(request: FastAPIRequest):
        _require_token(request)
        _, rows = _filtered_actions()
        payload = build_local_export_zip(
            instance,
            year=year,
            actions_csv=actions_to_csv(rows),
            actions_markdown=actions_to_markdown(rows),
        )
        return Response(
            content=payload,
            media_type="application/zip",
            headers=_download_headers(f"coproscope_pack_local_{year}.zip"),
        )

    @app.get("/exports/passation/blocages/{blocker_id}", response_class=HTMLResponse)
    def export_passation_blocker_detail(request: FastAPIRequest, blocker_id: str):
        _require_token(request)
        query = _safe_passation_preview_query(request)
        model = build_dashboard_model(instance, year)
        ux = model.get("ux") if isinstance(model.get("ux"), dict) else {}
        preview = ux.get("passation_export_preview") if isinstance(ux.get("passation_export_preview"), dict) else {}
        if not preview and isinstance(ux.get("passation_export"), dict):
            preview = ux["passation_export"]
        preview = dict(preview)
        scoped_document = _passation_export_document(
            instance=instance,
            year=year,
            scope=query.get("scope", ""),
            selected=query.get("selected", ""),
            dashboard_model=model,
        )
        preview = enrich_passation_preview_blocker_links(
            _scoped_passation_preview(preview, scoped_document),
            query,
        )
        detail = build_passation_blocker_detail(preview, blocker_id, query)
        return templates.TemplateResponse(
            request=request,
            name="passation_blocker_detail.html",
            context=context(
                request,
                "workstreams",
                model=model,
                passation_export=preview,
                passation_blocker=detail,
                passation_preview_query=query,
            ),
        )

    @app.get("/exports/passation.json")
    def export_passation_json(request: FastAPIRequest):
        from ..modules.passation_exports import render_passation_derived_json

        _require_token(request)
        query = _safe_passation_preview_query(request)
        try:
            payload = render_passation_derived_json(
                _passation_export_document(
                    instance,
                    year,
                    scope=query.get("scope", ""),
                    selected=query.get("selected", ""),
                )
            )
            _assert_passation_export_route_safe(payload)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Export passation derive refuse.") from exc
        return Response(
            content=payload,
            media_type="application/json; charset=utf-8",
            headers=_download_headers(f"coproscope_passation_derivee_{year}.json"),
        )

    @app.get("/exports/passation.txt")
    def export_passation_text(request: FastAPIRequest):
        from ..modules.passation_exports import render_passation_derived_markdown

        _require_token(request)
        query = _safe_passation_preview_query(request)
        try:
            payload = render_passation_derived_markdown(
                _passation_export_document(
                    instance,
                    year,
                    scope=query.get("scope", ""),
                    selected=query.get("selected", ""),
                )
            ).replace(
                "export dÃ©rivÃ©, non source collaborative",
                PASSATION_EXPORT_WATERMARK,
            ).replace(
                "export dérivé, non source collaborative",
                PASSATION_EXPORT_WATERMARK,
            )
            _assert_passation_export_route_safe(payload)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Export passation derive refuse.") from exc
        return Response(
            content=payload,
            media_type="text/plain; charset=utf-8",
            headers=_download_headers(f"coproscope_passation_derivee_{year}.txt"),
        )

    @app.get("/exports/passation", response_class=HTMLResponse)
    def export_passation_preview(request: FastAPIRequest):
        _require_token(request)
        query = _safe_passation_preview_query(request)

        def _target(path: str) -> str:
            target = path
            if query:
                target = f"{target}?{urlencode(query)}"
            return target

        model = build_dashboard_model(instance, year)
        ux = model.get("ux") if isinstance(model.get("ux"), dict) else {}
        preview = ux.get("passation_export_preview") if isinstance(ux.get("passation_export_preview"), dict) else {}
        if not preview and isinstance(ux.get("passation_export"), dict):
            preview = ux["passation_export"]
        preview = dict(preview)
        scoped_document = _passation_export_document(
            instance=instance,
            year=year,
            scope=query.get("scope", ""),
            selected=query.get("selected", ""),
            dashboard_model=model,
        )
        preview = enrich_passation_preview_blocker_links(
            _scoped_passation_preview(preview, scoped_document),
            query,
        )
        preview_context = dict(preview.get("context")) if isinstance(preview.get("context"), dict) else {}
        preview_context["watermark"] = PASSATION_EXPORT_WATERMARK
        preview_context["source_of_truth"] = False
        preview["context"] = preview_context
        preview["watermark"] = PASSATION_EXPORT_WATERMARK
        formats = []
        for item in _list_of_dicts(preview.get("formats") or preview.get("formats_available")):
            row = dict(item)
            format_id = str(row.get("id") or "").lower()
            if format_id == "txt":
                row["href"] = _target("/exports/passation.txt")
            elif format_id == "json":
                row["href"] = _target("/exports/passation.json")
            formats.append(row)
        preview["formats"] = formats
        preview["formats_available"] = formats
        downloads = dict(preview.get("downloads")) if isinstance(preview.get("downloads"), dict) else {}
        downloads.update(
            {
                "preview_href": _target("/exports/passation"),
                "text_href": _target("/exports/passation.txt"),
                "json_href": _target("/exports/passation.json"),
            }
        )
        preview["downloads"] = downloads
        return templates.TemplateResponse(
            request=request,
            name="passation_export.html",
            context=context(
                request,
                "workstreams",
                model=model,
                passation_export=preview,
                passation_preview_query=query,
            ),
        )

    @app.get("/exports/{export_path:path}")
    def blocked_export_path(export_path: str):
        parts = [part.lower() for part in Path(export_path.replace("\\", "/")).parts]
        if any(part in FORBIDDEN_EXPORT_PARTS for part in parts):
            raise HTTPException(status_code=404, detail="Export interdit.")
        raise HTTPException(status_code=404, detail="Export introuvable.")

    @app.get("/health")
    def health():
        return {"status": "ok", "instance": instance.instance_id, "year": year}

    @app.get("/{root_name}/{path:path}")
    def blocked_private_roots(root_name: str, path: str):
        if root_name.lower() in FORBIDDEN_WEB_ROOTS:
            raise HTTPException(status_code=404, detail="Racine privee non servie.")
        raise HTTPException(status_code=404, detail="Route introuvable.")

    return app


def _ui_token() -> str:
    return os.environ.get("COPROSCOPE_UI_TOKEN") or secrets.token_urlsafe(24)


def serve(
    instance: InstanceConfig,
    year: int = 2025,
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    access_token: str | None = None,
    unsafe_lan: bool = False,
) -> None:
    if host not in LOOPBACK_HOSTS and not unsafe_lan:
        raise ValueError("Refusing to expose the UI outside loopback without --unsafe-lan.")
    access_token = access_token or _ui_token()
    try:
        import uvicorn  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "Uvicorn is missing. Install UI dependencies with: python -m pip install -e .[ui]"
        ) from exc

    print(f"CoproScope UI token URL: http://{host}:{port}/?token={quote(access_token)}")
    uvicorn.run(create_app(instance, year, access_token=access_token), host=host, port=port, log_level="info")
