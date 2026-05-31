from __future__ import annotations

import re
from pathlib import Path

from ..core.common import DEFAULT_DOCUMENT_FIELDS, InstanceConfig, read_csv, write_csv
from .depot import read_deposit_manifest, write_deposit_manifest
from .document_intake_sources import (
    REGISTER_SOURCE_IDS,
    SOURCE_DRAG_DROP,
    SOURCE_DRIVE_DESKTOP,
    SOURCE_INBOX,
    build_document_intake_source_context,
    normalize_document_intake_source,
    select_document_intake_rows,
    source_id_from_register_row,
)
from .document_intake_view_options import DOCUMENT_TYPE_VALUES, normalize_document_type_value


DOCUMENT_INBOX_INTAKE_LIMIT = 1000
DOCUMENT_INBOX_PENDING_STATUSES = {"", "PENDING", "A_CLASSER", "UNCLASSIFIED", "TO_CLASSIFY", "PROPOSED"}
DOCUMENT_INBOX_REVIEW_OCR_STATUSES = {"", "PENDING", "OCR_REQUIRED", "EXTRACTION_ERROR", "SOURCE_MISSING", "UNSUPPORTED"}
DOCUMENT_INBOX_REVIEW_PRIVACY_STATUSES = {"", "A_REVOIR", "A_ARBITRER", "BLOQUE"}
DOCUMENT_INBOX_REVIEW_PUBLICATION_FORMS = {"aggregation_required", "metadata_only", "redaction_required"}
DOCUMENT_INTAKE_TYPE_VALUES = set(DOCUMENT_TYPE_VALUES)
DOCUMENT_INTAKE_PRIVACY_VALUES = {"A_ARBITRER", "DIFFUSABLE_BRUT", "A_BIFFER", "RESERVE_CS", "BLOQUE"}
DOCUMENT_INTAKE_POINT_KINDS = {"ag", "decision", "demande", "facture", "incident", "chantier", "contentieux", "preuve_libre"}
DOCUMENT_INTAKE_ACTION_KINDS = {"verifier", "demander", "relancer", "biffer", "transmettre", "classer"}
DOCUMENT_INTAKE_PROOF_INTENTS = {"presence", "decision", "reception", "execution", "paiement", "refus", "cloture"}
DOCUMENT_INTAKE_LINK_FIELDS = (
    "point_kind",
    "point_id",
    "point_label",
    "action_kind",
    "action_label",
    "proof_intent",
    "proof_label",
)
DOCUMENT_INTAKE_REGISTER_MERGE_FIELDS = (
    "document_type",
    "classification_status",
    "privacy_review_status",
    "status_ocr",
    "text_char_count",
    "text_path",
    "extraction_level",
    "text_quality",
    "ocr_engine",
    "ai_review_status",
    "required_transformations",
    "redaction_status",
    *DOCUMENT_INTAKE_LINK_FIELDS,
)


def _document_intake_rows_from_manifest(
    manifest: dict[str, object] | None,
    register_rows: dict[str, dict[str, str]] | None = None,
) -> list[dict[str, object]]:
    if not manifest:
        return []
    files = manifest.get("files")
    if not isinstance(files, list):
        return []
    doc_ids = manifest.get("doc_ids") if isinstance(manifest.get("doc_ids"), list) else []
    deposit_id = str(manifest.get("deposit_id") or "DEPOT")
    text_statuses = _document_intake_local_text_statuses(manifest)
    rows: list[dict[str, object]] = []
    for index, file_info in enumerate(files, start=1):
        if not isinstance(file_info, dict):
            continue
        sha256 = str(file_info.get("sha256") or "")
        doc_id = str(doc_ids[index - 1]) if index <= len(doc_ids) and doc_ids[index - 1] else ""
        if not doc_id and sha256:
            doc_id = f"DOC-{sha256[:12].upper()}"
        stored_name = str(file_info.get("stored_name") or file_info.get("original_name") or "")
        extension = Path(stored_name).suffix.lower().lstrip(".")
        row = {
            "doc_id": doc_id,
            "display_name": f"Fichier {index}",
            "local_reference": f"depot-local/{deposit_id}/fichier-{index}",
            "sha256": sha256,
            "file_format": extension,
            "size_bytes": str(file_info.get("size_bytes") or ""),
            "document_type": "A_CLASSER",
            "classification_status": "A_CLASSER",
            "privacy_status": "A_ARBITRER",
            "privacy_rationale": "A choisir avant tout partage hors instance locale.",
            "source_kind": "depot_local",
            "source_id": SOURCE_DRAG_DROP,
            "source_label": "Glisser-deposer",
        }
        if register_rows and doc_id in register_rows:
            for field in DOCUMENT_INTAKE_REGISTER_MERGE_FIELDS:
                value = register_rows[doc_id].get(field, "")
                if value:
                    row[field] = value
        if doc_id in text_statuses:
            row["local_text_status"] = text_statuses[doc_id]
        rows.append(row)
    return rows


def _document_intake_register_rows_by_doc_id(instance: InstanceConfig) -> dict[str, dict[str, str]]:
    try:
        _, rows = read_csv(instance.register("documents"))
    except (KeyError, OSError):
        return {}
    return {str(row.get("doc_id") or ""): row for row in rows if row.get("doc_id")}


def _document_intake_local_text_statuses(manifest: dict[str, object]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    steps = manifest.get("steps")
    if not isinstance(steps, list):
        return statuses
    for step in steps:
        if not isinstance(step, dict):
            continue
        name = str(step.get("name") or "")
        if not name.startswith("extract_text:"):
            continue
        doc_id = _document_intake_doc_id(name.split(":", 1)[1])
        if not doc_id:
            continue
        status = str(step.get("status") or "").strip().lower()
        statuses[doc_id] = "ok" if status == "ok" else "error" if status == "error" else "pending"
    return statuses


def _document_intake_type_value(value: object) -> str:
    return normalize_document_type_value(value)


def _document_intake_privacy_value(value: object) -> str:
    token = _document_intake_choice_token(value)
    return token if token in DOCUMENT_INTAKE_PRIVACY_VALUES else "A_ARBITRER"


def _document_intake_doc_id(value: object) -> str:
    text = str(value or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", text):
        return ""
    return text


def _document_intake_saved_choices(manifest: dict[str, object] | None) -> dict[str, dict[str, str]]:
    raw_choices = manifest.get("intake_choices") if isinstance(manifest, dict) else {}
    if not isinstance(raw_choices, dict):
        return {}
    choices: dict[str, dict[str, str]] = {}
    for raw_doc_id, raw_choice in raw_choices.items():
        doc_id = _document_intake_doc_id(raw_doc_id)
        if not doc_id or not isinstance(raw_choice, dict):
            continue
        choices[doc_id] = {
            "document_type": _document_intake_type_value(raw_choice.get("document_type")),
            "privacy_status": _document_intake_privacy_value(raw_choice.get("privacy_status")),
        }
    return choices


def _document_intake_saved_links(manifest: dict[str, object] | None) -> dict[str, dict[str, str]]:
    raw_links = manifest.get("intake_links") if isinstance(manifest, dict) else {}
    if not isinstance(raw_links, dict):
        return {}
    links: dict[str, dict[str, str]] = {}
    for raw_doc_id, raw_link in raw_links.items():
        doc_id = _document_intake_doc_id(raw_doc_id)
        if not doc_id or not isinstance(raw_link, dict):
            continue
        links[doc_id] = _document_intake_link_payload(raw_link)
    return links


def _apply_document_intake_saved_choices(
    rows: list[dict[str, object]],
    choices: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    if not choices:
        return rows
    prepared: list[dict[str, object]] = []
    for row in rows:
        copy = dict(row)
        choice = choices.get(str(copy.get("doc_id") or ""))
        if choice:
            document_type = _document_intake_type_value(choice.get("document_type"))
            privacy_status = _document_intake_privacy_value(choice.get("privacy_status"))
            copy["document_type"] = document_type
            copy["classification_status"] = "A_CLASSER" if document_type == "A_CLASSER" else "PROPOSED"
            copy["privacy_status"] = privacy_status
            copy["privacy_rationale"] = _document_intake_privacy_rationale(privacy_status)
        prepared.append(copy)
    return prepared


def _apply_document_intake_saved_links(
    rows: list[dict[str, object]],
    links: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    if not links:
        return rows
    prepared: list[dict[str, object]] = []
    for row in rows:
        copy = dict(row)
        link = links.get(str(copy.get("doc_id") or ""))
        if link:
            copy.update(link)
        prepared.append(copy)
    return prepared


def _save_document_intake_manifest_choice(
    instance: InstanceConfig,
    deposit_id: str,
    doc_id: str,
    document_type: str,
    privacy_status: str,
) -> bool:
    manifest = read_deposit_manifest(instance, deposit_id)
    if manifest is None:
        return False
    known_doc_ids = {str(value) for value in manifest.get("doc_ids", []) if value}
    if doc_id not in known_doc_ids:
        return False
    choices = _document_intake_saved_choices(manifest)
    choices[doc_id] = {"document_type": document_type, "privacy_status": privacy_status}
    manifest["intake_choices"] = choices
    write_deposit_manifest(instance, manifest)
    return True


def _save_document_intake_manifest_link(
    instance: InstanceConfig,
    deposit_id: str,
    doc_id: str,
    link: dict[str, str],
) -> bool:
    manifest = read_deposit_manifest(instance, deposit_id)
    if manifest is None:
        return False
    known_doc_ids = {str(value) for value in manifest.get("doc_ids", []) if value}
    if doc_id not in known_doc_ids:
        return False
    links = _document_intake_saved_links(manifest)
    links[doc_id] = link
    manifest["intake_links"] = links
    write_deposit_manifest(instance, manifest)
    return True


def _save_document_intake_register_choice(
    instance: InstanceConfig,
    doc_id: str,
    document_type: str,
    privacy_status: str,
) -> bool:
    fields, rows = read_csv(instance.register("documents"))
    if not rows:
        return False
    fields = fields or list(DEFAULT_DOCUMENT_FIELDS)
    for required in ("document_type", "classification_status", "privacy_review_status"):
        if required not in fields:
            fields.append(required)
    updated = False
    for row in rows:
        if str(row.get("doc_id") or "") != doc_id:
            continue
        row["document_type"] = document_type
        row["classification_status"] = "A_CLASSER" if document_type == "A_CLASSER" else "PROPOSED"
        row["privacy_review_status"] = privacy_status
        updated = True
    if updated:
        write_csv(instance.register("documents"), fields, rows)
    return updated


def _save_document_intake_register_link(instance: InstanceConfig, doc_id: str, link: dict[str, str]) -> bool:
    fields, rows = read_csv(instance.register("documents"))
    if not rows:
        return False
    fields = fields or list(DEFAULT_DOCUMENT_FIELDS)
    for required in DOCUMENT_INTAKE_LINK_FIELDS:
        if required not in fields:
            fields.append(required)
    updated = False
    for row in rows:
        if str(row.get("doc_id") or "") != doc_id:
            continue
        row.update(link)
        updated = True
    if updated:
        write_csv(instance.register("documents"), fields, rows)
    return updated


def _document_intake_rows_from_register(
    instance: InstanceConfig,
    *,
    limit: int = DOCUMENT_INBOX_INTAKE_LIMIT,
) -> list[dict[str, object]]:
    try:
        _, register_rows = read_csv(instance.register("documents"))
    except (KeyError, OSError):
        return []
    duplicate_groups: dict[str, int] = {}
    duplicate_seen: dict[str, int] = {}
    for register_row in register_rows:
        sha256 = str(register_row.get("sha256") or "").strip()
        if sha256:
            duplicate_groups[sha256] = duplicate_groups.get(sha256, 0) + 1
    rows: list[dict[str, object]] = []
    for register_row in register_rows:
        classification_status = str(register_row.get("classification_status") or "").strip().upper()
        document_type = _document_intake_type_value(register_row.get("document_type"))
        status_ocr = str(register_row.get("status_ocr") or "").strip().upper()
        privacy_status = str(register_row.get("privacy_review_status") or "").strip().upper()
        publication_form = str(register_row.get("publication_form") or "").strip().lower()
        needs_review = (
            classification_status in DOCUMENT_INBOX_PENDING_STATUSES
            or document_type.upper() == "A_CLASSER"
            or status_ocr in DOCUMENT_INBOX_REVIEW_OCR_STATUSES
            or privacy_status in DOCUMENT_INBOX_REVIEW_PRIVACY_STATUSES
            or publication_form in DOCUMENT_INBOX_REVIEW_PUBLICATION_FORMS
        )
        if not needs_review:
            continue
        sha256 = str(register_row.get("sha256") or "").strip()
        doc_id = str(register_row.get("doc_id") or "").strip()
        if not doc_id and sha256:
            doc_id = f"DOC-{sha256[:12].upper()}"
        if not doc_id:
            continue
        duplicate_count = duplicate_groups.get(sha256, 0)
        duplicate_seen[sha256] = duplicate_seen.get(sha256, 0) + 1
        duplicate_of = f"DUP-{sha256[:12].upper()}" if duplicate_count > 1 else ""
        text_char_count = str(register_row.get("text_char_count") or "").strip()
        text_path = str(register_row.get("text_path") or "").strip()
        if not text_char_count or text_char_count == "0" or status_ocr in DOCUMENT_INBOX_REVIEW_OCR_STATUSES:
            text_path = ""
        source_id = source_id_from_register_row(register_row)
        source_label = (
            "Inbox du coffre"
            if source_id == SOURCE_INBOX
            else "Drive Desktop"
            if source_id == SOURCE_DRIVE_DESKTOP
            else "Dossier local"
        )
        rows.append(
            {
                "doc_id": doc_id,
                "display_name": f"Fichier inbox {len(rows) + 1}" if source_id == SOURCE_INBOX else f"Fichier source locale {len(rows) + 1}",
                "local_reference": f"inbox-reconstruction:{doc_id}",
                "sha256": sha256,
                "file_format": str(register_row.get("extension") or "").strip().lower().lstrip("."),
                "size_bytes": str(register_row.get("size_bytes") or ""),
                "document_type": document_type,
                "classification_status": classification_status or "A_CLASSER",
                "privacy_status": str(register_row.get("privacy_review_status") or "A_ARBITRER").strip(),
                "privacy_rationale": "A choisir avant tout partage hors instance locale.",
                "status_ocr": status_ocr,
                "text_char_count": text_char_count,
                "text_path": text_path,
                "extraction_level": str(register_row.get("extraction_level") or ""),
                "text_quality": str(register_row.get("text_quality") or ""),
                "required_transformations": str(register_row.get("required_transformations") or ""),
                "redaction_status": str(register_row.get("redaction_status") or ""),
                "publication_form": publication_form,
                "duplicate_of": duplicate_of,
                "duplicate_count": str(duplicate_count) if duplicate_count > 1 else "",
                "duplicate_index": str(duplicate_seen[sha256]) if duplicate_count > 1 else "",
                "source_kind": str(register_row.get("source_kind") or "depot_local").strip() or "depot_local",
                "source_id": source_id,
                "source_label": source_label,
            }
        )
        for field in DOCUMENT_INTAKE_LINK_FIELDS:
            value = str(register_row.get(field) or "").strip()
            if value:
                rows[-1][field] = value
        if len(rows) >= limit:
            break
    return rows


def _document_intake_page_rows_and_sources(
    instance: InstanceConfig,
    selected_manifest: dict[str, object] | None,
    source: object,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    upload_rows = _apply_document_intake_saved_links(
        _apply_document_intake_saved_choices(
            _document_intake_rows_from_manifest(selected_manifest, _document_intake_register_rows_by_doc_id(instance)),
            _document_intake_saved_choices(selected_manifest),
        ),
        _document_intake_saved_links(selected_manifest),
    )
    register_rows = _document_intake_rows_from_register(instance)
    selected_source = normalize_document_intake_source(source)
    rows = select_document_intake_rows(upload_rows, register_rows, selected_source)
    sources = build_document_intake_source_context(
        instance,
        selected_source=selected_source,
        selected_manifest=selected_manifest,
        upload_rows=upload_rows,
        register_rows=register_rows,
    )
    return rows, sources


def _document_intake_is_register_source(value: object) -> bool:
    return normalize_document_intake_source(value) in REGISTER_SOURCE_IDS


def _document_intake_source_value(value: object) -> str:
    return normalize_document_intake_source(value)


def _document_intake_link_payload(values: object) -> dict[str, str]:
    getter = values.get if hasattr(values, "get") else {}.get
    return {
        "point_kind": _document_intake_token_value(getter("point_kind"), DOCUMENT_INTAKE_POINT_KINDS, "preuve_libre"),
        "point_id": _document_intake_doc_id(getter("point_id")),
        "point_label": _document_intake_link_label(getter("point_label")),
        "action_kind": _document_intake_token_value(getter("action_kind"), DOCUMENT_INTAKE_ACTION_KINDS, "verifier"),
        "action_label": _document_intake_link_label(getter("action_label")),
        "proof_intent": _document_intake_token_value(getter("proof_intent"), DOCUMENT_INTAKE_PROOF_INTENTS, "presence"),
        "proof_label": _document_intake_link_label(getter("proof_label")),
    }


def _document_intake_link_complete(link: dict[str, str]) -> bool:
    return bool(link.get("point_label") and link.get("action_label") and link.get("proof_label"))


def _document_intake_token_value(value: object, allowed: set[str], default: str) -> str:
    token = re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower()).strip("_")
    return token if token in allowed else default


def _document_intake_link_label(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())[:160]
    if not text:
        return ""
    if re.search(r"([A-Za-z]:[\\/]|^/|^\\\\|https?://|file://|@|[\\/])", text, flags=re.IGNORECASE):
        return ""
    return text


def _document_intake_choice_token(value: object) -> str:
    return re.sub(r"[^A-Z0-9_]+", "_", str(value or "").strip().upper()).strip("_")


def _document_intake_privacy_rationale(value: str) -> str:
    if value == "DIFFUSABLE_BRUT":
        return "Diffusion brute possible seulement dans le contexte choisi."
    if value == "A_BIFFER":
        return "Version masquee a nommer avant toute diffusion."
    if value == "RESERVE_CS":
        return "Lecture limitee au conseil syndical."
    if value == "BLOQUE":
        return "Aucun partage tant qu'un arbitrage n'est pas fait."
    return "A choisir avant tout partage hors instance locale."
