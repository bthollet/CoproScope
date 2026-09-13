from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import secrets
from pathlib import Path
from typing import Any, Callable, Mapping

from fastapi import Request

from ..core.common import InstanceConfig, append_csv_row, now_iso
from .docops_feedback_view import (
    DOCUMENT_TYPE_CHOICES,
    JUSTIFICATION_REQUIRED,
    PRIVACY_CHOICES,
    SYNTHETIC_DOCOPS_PROPOSALS,
    template_context as docops_template_context,
)


FEEDBACK_FIELDS = [
    "feedback_id",
    "session_id",
    "doc_id",
    "sha256",
    "document_type_before",
    "document_type_after",
    "privacy_before",
    "privacy_after",
    "justification",
    "redaction_scope",
    "reviewer",
    "reviewed_at",
    "source",
    "apply_status",
    "apply_error",
]
EXPORT_FIELDS = ["source_of_truth", "dataset_kind", "watermark", *FEEDBACK_FIELDS]
REGISTER_FILENAME = "registre_feedback_docops.csv"
_DOC_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]{3,80}$")
_SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
_SAFE_TEXT_RE = re.compile("^[A-Za-z0-9\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u00FF\\u0152\\u0153 .,:;!?()_'/-]{0,240}$")
_PRIVATE_MARKERS = (
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"\\\\"),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])(?:raw|restricted|logs|private|system|staging)(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])(?:Users|home)(?:[\\/]|$)", re.IGNORECASE),
)
_MEMORY_FEEDBACK_ROWS: dict[str, list[dict[str, str]]] = {}


class DocOpsFeedbackValidationError(ValueError):
    pass


def mount_docops_feedback_routes(
    app: Any,
    *,
    templates: Any,
    context: Callable[..., dict[str, object]],
    require_token: Callable[[Any], None],
    instance: InstanceConfig,
    year: int,
    shell_model: Callable[[InstanceConfig, int], dict[str, object]],
    html_response_class: Any,
    http_exception_class: type[Exception],
) -> None:
    @app.get("/documents/tri-feedback", response_class=html_response_class)
    def docops_feedback_page(request: Request):
        require_token(request)
        return templates.TemplateResponse(
            request=request,
            name="docops_feedback.html",
            context=context(
                request,
                "docops_feedback",
                model=shell_model(instance, year),
                **docops_template_context(),
            ),
        )

    @app.post("/documents/tri-feedback", response_class=html_response_class)
    async def docops_feedback_save(request: Request):
        require_token(request)
        try:
            saved = save_feedback_from_form(instance, await request.form())
        except DocOpsFeedbackValidationError as exc:
            raise http_exception_class(status_code=422, detail=str(exc)) from exc
        return templates.TemplateResponse(
            request=request,
            name="docops_feedback.html",
            context=context(
                request,
                "docops_feedback",
                model=shell_model(instance, year),
                **docops_template_context(saved=saved),
            ),
        )


def register_docops_feedback_routes(
    app: Any,
    templates: Any,
    context: Callable[..., dict[str, object]],
    instance: InstanceConfig,
    year: int,
    require_token: Callable[[Any], None],
    shell_model: Callable[[InstanceConfig, int], dict[str, object]],
    http_exception_class: type[Exception],
    html_response_class: Any,
    response_class: type[Any],
    download_headers: Callable[[str], dict[str, str]],
) -> None:
    mount_docops_feedback_routes(
        app,
        templates=templates,
        context=context,
        require_token=require_token,
        instance=instance,
        year=year,
        shell_model=shell_model,
        html_response_class=html_response_class,
        http_exception_class=http_exception_class,
    )

    @app.get("/exports/docops-feedback-tri.csv")
    def export_docops_feedback_csv(request: Request):
        require_token(request)
        return response_class(
            content=render_feedback_export_csv(instance),
            media_type="text/csv; charset=utf-8",
            headers=download_headers("docops_feedback_tri.csv"),
        )

    @app.get("/exports/docops-feedback-tri.json")
    def export_docops_feedback_json(request: Request):
        require_token(request)
        return response_class(
            content=render_feedback_export_json(instance),
            media_type="application/json; charset=utf-8",
            headers=download_headers("docops_feedback_tri.json"),
        )


def save_feedback_from_form(instance: InstanceConfig, form: Mapping[str, object]) -> dict[str, str]:
    row = _validated_feedback_row(form)
    path = feedback_register_path(instance)
    if path is None:
        _memory_feedback_rows(instance).append(row)
        return {**row, "storage": "memory"}
    append_csv_row(path, FEEDBACK_FIELDS, row)
    return {**row, "storage": "csv", "storage_name": REGISTER_FILENAME}


def render_feedback_export_csv(instance: InstanceConfig) -> str:
    rows = _feedback_rows(instance)
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=EXPORT_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(_export_row(row))
    return stream.getvalue()


def render_feedback_export_json(instance: InstanceConfig) -> str:
    payload = {
        "export_type": "docops_feedback_tri",
        "source_of_truth": False,
        "watermark": "DERIVED_DOCOPS_FEEDBACK",
        "dataset_kind": "derived_feedback_register",
        "rows": [_export_row(row) for row in _feedback_rows(instance)],
    }
    return json.dumps(payload, ensure_ascii=True, indent=2) + "\n"


def feedback_register_path(instance: InstanceConfig) -> Path | None:
    try:
        base = instance.register("documents").parent.resolve()
        root = instance.instance_root.resolve()
    except (KeyError, OSError):
        return None
    target = (base / REGISTER_FILENAME).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target


def _feedback_rows(instance: InstanceConfig) -> list[dict[str, str]]:
    path = feedback_register_path(instance)
    if path is None or not path.exists():
        return [dict(row) for row in _memory_feedback_rows(instance)]
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _memory_feedback_rows(instance: InstanceConfig) -> list[dict[str, str]]:
    key = _memory_feedback_key(instance)
    return _MEMORY_FEEDBACK_ROWS.setdefault(key, [])


def _memory_feedback_key(instance: InstanceConfig) -> str:
    try:
        root = str(instance.instance_root.resolve()).encode("utf-8", "surrogatepass")
        return hashlib.sha256(root).hexdigest()
    except OSError:
        return str(id(instance))


def _validated_feedback_row(form: Mapping[str, object]) -> dict[str, str]:
    doc_id = _clean(form.get("doc_id"), max_length=80)
    sha256 = _clean(form.get("sha256"), max_length=64)
    document_type = _clean(form.get("document_type"), max_length=40)
    privacy_status = _clean(form.get("privacy_status"), max_length=40)
    reviewer = _clean(form.get("reviewer"), max_length=60)
    justification = _clean(form.get("justification"), max_length=240)
    redaction_scope = _clean(form.get("redaction_scope"), max_length=120)
    if not _DOC_ID_RE.fullmatch(doc_id) or not _SHA256_RE.fullmatch(sha256):
        raise DocOpsFeedbackValidationError("Correction DocOps refusee.")
    proposal = _proposal_for(doc_id)
    if proposal is None or proposal.get("sha256") != sha256:
        raise DocOpsFeedbackValidationError("Correction DocOps refusee.")
    if document_type not in DOCUMENT_TYPE_CHOICES or privacy_status not in _privacy_values():
        raise DocOpsFeedbackValidationError("Correction DocOps refusee.")
    if len(reviewer) < 2 or not _safe_text(reviewer):
        raise DocOpsFeedbackValidationError("Correction DocOps refusee.")
    if privacy_status in JUSTIFICATION_REQUIRED and not justification:
        raise DocOpsFeedbackValidationError("Justification requise pour cette restriction.")
    if privacy_status == "A_MASQUER" and not redaction_scope:
        raise DocOpsFeedbackValidationError("Pages ou plages a masquer requises.")
    if justification and not _safe_text(justification):
        raise DocOpsFeedbackValidationError("Correction DocOps refusee.")
    if redaction_scope and not _safe_text(redaction_scope):
        raise DocOpsFeedbackValidationError("Correction DocOps refusee.")
    return {
        "feedback_id": f"FB-{secrets.token_hex(4).upper()}",
        "session_id": "SESSION-TRI-FEEDBACK-LOCAL",
        "doc_id": doc_id,
        "sha256": sha256.lower(),
        "document_type_before": proposal.get("document_type", ""),
        "document_type_after": document_type,
        "privacy_before": proposal.get("privacy_status", ""),
        "privacy_after": privacy_status,
        "justification": justification,
        "redaction_scope": redaction_scope,
        "reviewer": reviewer,
        "reviewed_at": now_iso(),
        "source": "tri_feedback_ui",
        "apply_status": "RECORDED",
        "apply_error": "",
    }


def _proposal_for(doc_id: str) -> dict[str, str] | None:
    return next((row for row in SYNTHETIC_DOCOPS_PROPOSALS if row.get("doc_id") == doc_id), None)


def _privacy_values() -> set[str]:
    return {choice["value"] for choice in PRIVACY_CHOICES}


def _clean(value: object, *, max_length: int) -> str:
    return " ".join(str(value or "").strip().split())[:max_length]


def _safe_text(value: str) -> bool:
    return bool(_SAFE_TEXT_RE.fullmatch(value)) and not any(pattern.search(value) for pattern in _PRIVATE_MARKERS)


def _export_row(row: Mapping[str, str]) -> dict[str, str]:
    exported = {field: _safe_export_value(row.get(field, "")) for field in FEEDBACK_FIELDS}
    return {
        "source_of_truth": "false",
        "dataset_kind": "derived_feedback_register",
        "watermark": "DERIVED_DOCOPS_FEEDBACK",
        **exported,
    }


def _safe_export_value(value: str) -> str:
    text = _clean(value, max_length=240)
    if any(pattern.search(text) for pattern in _PRIVATE_MARKERS):
        return ""
    return text
