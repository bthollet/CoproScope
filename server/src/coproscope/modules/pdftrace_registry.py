from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from ..core.common import InstanceConfig, now_iso, read_csv, write_csv
from .annotationops import normalize_annotation, validate_annotation
from .pdftrace_contracts import NO_SOURCE_WRITE_NOTICE, TEXT_STATUS_UNCONFIRMED, contains_sensitive_text
from .pdftraceops import build_zone_trace_candidate, candidate_to_annotation_row


REGISTER_FILENAME = "registre_pdf_traces.csv"

PDF_TRACE_FIELDS = [
    "trace_id",
    "created_at",
    "document_ref",
    "document_hash",
    "page",
    "zone_x",
    "zone_y",
    "zone_width",
    "zone_height",
    "anchor_hash",
    "fragment_ref",
    "point_ref",
    "action_ref",
    "proof_ref",
    "proof_status",
    "text_status",
    "document_hash_status",
    "diffusion",
    "confidentiality",
    "status",
    "comment",
    "write_policy",
    "source_engine",
]

DEFAULT_ZONE = {"x": 0.16, "y": 0.22, "width": 0.52, "height": 0.16}
AUTHOR_REF = "membre_cs_demo"


def trace_register_path(instance: InstanceConfig):
    base = instance.register("documents").parent.resolve()
    root = instance.instance_root.resolve()
    if not _is_relative_to(base, root):
        raise ValueError("registre documents hors instance")
    return base / REGISTER_FILENAME


def read_trace_rows(instance: InstanceConfig) -> list[dict[str, str]]:
    _, rows = read_csv(trace_register_path(instance))
    return rows


def read_document_trace_rows(instance: InstanceConfig, document_ref: str) -> list[dict[str, str]]:
    safe_ref = _safe_ref(document_ref)
    return [row for row in read_trace_rows(instance) if row.get("document_ref") == safe_ref]


def save_zone_trace(
    instance: InstanceConfig,
    document: Mapping[str, Any],
    form: Mapping[str, Any],
    *,
    created_at: str | None = None,
) -> dict[str, str]:
    document_ref = _safe_ref(document.get("doc_id"))
    document_hash = _cell(document.get("sha256"))
    extension = _cell(document.get("extension")).lower().lstrip(".")
    if not document_ref:
        raise ValueError("document invalide")
    if extension != "pdf":
        raise ValueError("trace reservee aux PDF")
    if not document_hash:
        raise ValueError("empreinte document requise")

    page = max(1, _int_value(form.get("page"), 1))
    zone = {
        "x": _float_value(form.get("zone_x"), DEFAULT_ZONE["x"]),
        "y": _float_value(form.get("zone_y"), DEFAULT_ZONE["y"]),
        "width": _float_value(form.get("zone_width"), DEFAULT_ZONE["width"]),
        "height": _float_value(form.get("zone_height"), DEFAULT_ZONE["height"]),
    }
    comment = _comment(form.get("comment"))
    if contains_sensitive_text(comment):
        raise ValueError("note trop sensible pour une trace candidate")

    candidate = build_zone_trace_candidate(
        document_ref=document_ref,
        document_hash=document_hash,
        page_index=page - 1,
        page_label=str(page),
        zone=zone,
    )
    annotation_row = candidate_to_annotation_row(
        candidate,
        comment=comment,
        author_ref=AUTHOR_REF,
        created_at=created_at or now_iso(),
        point_ref=_safe_ref(form.get("point_ref")) or f"POINT-{document_ref}",
        action_ref=_safe_ref(form.get("action_ref")) or f"ACTION-{document_ref}",
        proof_ref=_safe_ref(form.get("proof_ref")) or f"PROOF-{document_ref}",
        diffusion="non_diffusable",
    )
    annotation = normalize_annotation(annotation_row)
    issues = _actionable_issues(validate_annotation(annotation))
    if issues:
        details = "; ".join(f"{issue.field}: {issue.reason}" for issue in issues)
        raise ValueError(f"trace candidate refusee: {details}")

    row = {
        "trace_id": annotation.annotation_id,
        "created_at": annotation.created_at,
        "document_ref": annotation.document_ref,
        "document_hash": annotation.document_hash,
        "page": str(annotation.anchor.page),
        "zone_x": _format_float(annotation.anchor.zone.x),
        "zone_y": _format_float(annotation.anchor.zone.y),
        "zone_width": _format_float(annotation.anchor.zone.width),
        "zone_height": _format_float(annotation.anchor.zone.height),
        "anchor_hash": annotation.anchor.anchor_hash,
        "fragment_ref": annotation.anchor.fragment_ref,
        "point_ref": annotation.point_ref,
        "action_ref": annotation.action_ref,
        "proof_ref": annotation.proof_ref,
        "proof_status": candidate.proof_status,
        "text_status": candidate.text_status,
        "document_hash_status": candidate.document_hash_status,
        "diffusion": annotation.diffusion,
        "confidentiality": annotation.confidentiality,
        "status": annotation.status,
        "comment": annotation.comment,
        "write_policy": NO_SOURCE_WRITE_NOTICE,
        "source_engine": candidate.source_engine,
    }
    rows = read_trace_rows(instance)
    write_csv(trace_register_path(instance), PDF_TRACE_FIELDS, [*rows, row])
    return row


def public_trace_summaries(instance: InstanceConfig, document_ref: str) -> list[dict[str, str]]:
    summaries: list[dict[str, str]] = []
    for row in read_document_trace_rows(instance, document_ref):
        summaries.append(
            {
                "trace_id": row.get("trace_id", ""),
                "created_at": row.get("created_at", ""),
                "anchor": _short_hash(row.get("anchor_hash", "")),
                "page": row.get("page", "") or "1",
                "zone": f"Zone encadree page {row.get('page', '') or '1'}",
                "status": "Trace candidate enregistree",
                "diffusion": _diffusion_label(row.get("diffusion", "")),
                "text": _text_label(row.get("text_status", "")),
                "comment": _short_text(row.get("comment", "")),
            }
        )
    return summaries


def _cell(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _safe_ref(value: Any) -> str:
    text = _cell(value)
    if not text or contains_sensitive_text(text):
        return ""
    return text if re.fullmatch(r"[A-Za-z0-9_.:#-]+", text) else ""


def _comment(value: Any) -> str:
    text = _cell(value)[:180]
    return text or "Trace candidate depuis l'atelier document."


def _int_value(value: Any, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _float_value(value: Any, default: float) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _format_float(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _short_hash(value: str) -> str:
    cleaned = _cell(value).replace("sha256:", "")
    if len(cleaned) <= 12:
        return cleaned
    return cleaned[:8]


def _short_text(value: str) -> str:
    text = _cell(value)
    return f"{text[:117]}..." if len(text) > 120 else text


def _diffusion_label(value: str) -> str:
    return "Non diffusable par defaut" if _cell(value) == "non_diffusable" else "Diffusion a verifier"


def _text_label(value: str) -> str:
    if _cell(value) == TEXT_STATUS_UNCONFIRMED:
        return "Texte non confirme : seule la zone encadree est gardee."
    return "Texte a relire avant usage."


def _actionable_issues(issues):
    return tuple(issue for issue in issues if not _is_hash_phone_false_positive(issue))


def _is_hash_phone_false_positive(issue) -> bool:
    return (
        issue.reason == "phone-like private data detected"
        and issue.field in {"annotation.anchor.anchor_hash", "annotation.anchor.fragment_ref"}
    )


def _is_relative_to(path, parent) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


__all__ = [
    "PDF_TRACE_FIELDS",
    "REGISTER_FILENAME",
    "public_trace_summaries",
    "read_document_trace_rows",
    "read_trace_rows",
    "save_zone_trace",
    "trace_register_path",
]
