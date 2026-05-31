from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..core.common import InstanceConfig, now_iso, read_csv, write_csv
from .annotationops import normalize_annotation, validate_annotation
from .pdftrace_contracts import (
    DOCUMENT_HASH_MISMATCH,
    DOCUMENT_HASH_NOT_CHECKED,
    NO_SOURCE_WRITE_NOTICE,
    TEXT_STATUS_UNCONFIRMED,
    contains_sensitive_text,
    document_hash_status,
    file_sha256,
)
from .pdftraceops import build_zone_trace_candidate, candidate_to_annotation_row
from .pdftraceops import extract_pdf_text_map
from .pdftrace_zone_text import build_zone_text_candidate


REGISTER_FILENAME = "registre_pdf_traces.csv"

BLOCKED_HASH_PATH_PARTS = {
    "raw",
    "brut",
    "bruts",
    "restricted",
    "restreint",
    "restreints",
    "private",
    "logs",
    "journaux",
    "secret",
    "secrets",
}

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
    "selected_text_hash",
    "selected_text_excerpt",
    "confidence",
    "document_hash_status",
    "diffusion",
    "confidentiality",
    "status",
    "comment",
    "write_policy",
    "source_engine",
]

AUTHOR_REF = "membre_cs_demo"
MIN_ZONE_SIZE = 0.01


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

    page = _required_page(form.get("page"))
    _validate_page_in_document(instance, document_ref, document, page)
    zone = _required_zone(form)
    hash_status = _current_document_hash_status(instance, document_ref, document, document_hash)
    comment = _comment(form.get("comment"))
    if contains_sensitive_text(comment):
        raise ValueError("note trop sensible pour une trace candidate")

    candidate = _zone_text_candidate(instance, document_ref, document, document_hash, page, zone) or build_zone_trace_candidate(
        document_ref=document_ref,
        document_hash=document_hash,
        page_index=page - 1,
        page_label=str(page),
        zone=zone,
        document_hash_status=hash_status,
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
        "selected_text_hash": _selected_text_hash(candidate),
        "selected_text_excerpt": _selected_text_excerpt(candidate),
        "confidence": candidate.confidence,
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
    return [_public_trace_summary(row) for row in read_document_trace_rows(instance, document_ref)]


def public_trace_reprise_queue(instance: InstanceConfig) -> dict[str, object]:
    documents = _document_summary_index(instance)
    items: list[dict[str, str]] = []
    for row in read_trace_rows(instance):
        summary = _public_trace_summary(row)
        document_ref = summary["document_ref"]
        if not document_ref or not summary["trace_id"] or not summary["resume_path"]:
            continue
        document = documents.get(document_ref, {})
        items.append(
            {
                "document_ref": document_ref,
                "document_label": document.get("label", f"Document {document_ref}"),
                "document_type": document.get("document_type", "Document"),
                "created_at": summary["created_at"],
                "page": summary["page"],
                "zone": summary["zone"],
                "status": summary["status"],
                "diffusion": summary["diffusion"],
                "text": summary["text"],
                "next_action": summary["next_action"],
                "resume_path": summary["resume_path"],
            }
        )
    return {
        "count": str(len(items)),
        "rows": items,
        "empty": "Aucune trace PDF candidate a relire.",
        "privacy_notice": "File locale uniquement: pas d'export, pas de PDF modifie, preuve candidate avant validation humaine.",
    }


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


def _page_label(row: Mapping[str, str]) -> str:
    return str(max(1, _positive_int(row.get("page", ""))))


def _public_trace_summary(row: Mapping[str, str]) -> dict[str, str]:
    safe_document_ref = _safe_ref(row.get("document_ref"))
    trace_id = _safe_ref(row.get("trace_id")) or _short_hash(row.get("anchor_hash", ""))
    page = _page_label(row)
    return {
        "document_ref": safe_document_ref,
        "trace_id": trace_id,
        "created_at": row.get("created_at", ""),
        "anchor": _short_hash(row.get("anchor_hash", "")),
        "page": page,
        "zone": f"Zone encadree page {page}",
        "zone_x": _safe_unit(row.get("zone_x", "")),
        "zone_y": _safe_unit(row.get("zone_y", "")),
        "zone_width": _safe_unit(row.get("zone_width", "")),
        "zone_height": _safe_unit(row.get("zone_height", "")),
        "resume_path": f"/documents/{safe_document_ref}?trace_id={trace_id}" if safe_document_ref and trace_id else "",
        "status": _trace_status_label(row.get("document_hash_status", "")),
        "diffusion": _diffusion_label(row.get("diffusion", "")),
        "text": _text_label(row.get("text_status", ""), row.get("document_hash_status", "")),
        "excerpt": _public_text(row.get("selected_text_excerpt", "")),
        "comment": _public_comment(row.get("comment", "")),
        "next_action": _reprise_next_action(row.get("text_status", ""), row.get("document_hash_status", "")),
    }


def _document_summary_index(instance: InstanceConfig) -> dict[str, dict[str, str]]:
    try:
        _, rows = read_csv(instance.register("documents"))
    except KeyError:
        return {}
    index: dict[str, dict[str, str]] = {}
    for row in rows:
        document_ref = _safe_ref(row.get("doc_id"))
        if not document_ref:
            continue
        index[document_ref] = {
            "label": f"Document {document_ref}",
            "document_type": _public_text(row.get("document_type", "")) or "Document",
        }
    return index


def _public_text(value: Any) -> str:
    text = _short_text(_cell(value))
    return "" if contains_sensitive_text(text) else text


def _public_comment(value: Any) -> str:
    text = _public_text(value)
    return text if text else ""


def _required_page(value: Any) -> int:
    try:
        page = int(str(value or "").strip())
    except (TypeError, ValueError):
        raise ValueError("page de trace invalide") from None
    if page < 1:
        raise ValueError("page de trace invalide")
    return page


def _validate_page_in_document(
    instance: InstanceConfig,
    document_ref: str,
    document: Mapping[str, Any],
    page: int,
) -> None:
    page_count = _positive_int(document.get("page_count"))
    if page_count <= 0:
        page_count = _positive_int(_registered_document(instance, document_ref).get("page_count"))
    if page_count > 0 and page > page_count:
        raise ValueError("page de trace hors document")


def _required_zone(form: Mapping[str, Any]) -> dict[str, float]:
    zone = {
        "x": _required_float_value(form.get("zone_x"), "zone_x"),
        "y": _required_float_value(form.get("zone_y"), "zone_y"),
        "width": _required_float_value(form.get("zone_width"), "zone_width"),
        "height": _required_float_value(form.get("zone_height"), "zone_height"),
    }
    if zone["width"] < MIN_ZONE_SIZE or zone["height"] < MIN_ZONE_SIZE:
        raise ValueError("zone de trace trop petite")
    if zone["x"] + zone["width"] > 1 or zone["y"] + zone["height"] > 1:
        raise ValueError("zone de trace hors page")
    return zone


def _required_float_value(value: Any, field: str) -> float:
    text = str(value if value is not None else "").strip()
    if not text:
        raise ValueError("zone de trace a selectionner")
    try:
        parsed = float(text)
    except (TypeError, ValueError):
        raise ValueError(f"{field} invalide") from None
    if parsed != parsed or parsed in {float("inf"), float("-inf")}:
        raise ValueError(f"{field} invalide")
    if parsed < 0 or parsed > 1:
        raise ValueError("zone de trace hors page")
    return parsed


def _positive_int(value: Any) -> int:
    try:
        parsed = int(str(value or "").strip())
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def _zone_text_candidate(
    instance: InstanceConfig,
    document_ref: str,
    document: Mapping[str, Any],
    document_hash: str,
    page: int,
    zone: Mapping[str, Any],
):
    source_path = _source_pdf_path(instance, document)
    if source_path is None:
        source_path = _source_pdf_path(instance, _registered_document(instance, document_ref))
    if source_path is None:
        return None
    try:
        text_map = extract_pdf_text_map(source_path, document_ref=document_ref, document_hash=document_hash)
    except Exception:
        return None
    return build_zone_text_candidate(text_map, page_index=page - 1, page_label=str(page), zone=zone)


def _selected_text_excerpt(candidate) -> str:
    text = _cell(candidate.selected_text)
    if not text:
        return ""
    if _cell(candidate.document_hash_status) == DOCUMENT_HASH_MISMATCH:
        return "Document modifie depuis la trace: verifier la zone avant usage."
    if candidate.private_excerpt_blocked or contains_sensitive_text(text):
        return "[extrait masque: contenu local ou sensible]"
    return f"Texte repere: {_short_text(text)}"


def _selected_text_hash(candidate) -> str:
    if not candidate.selected_text.strip():
        return ""
    if candidate.private_excerpt_blocked or contains_sensitive_text(candidate.selected_text):
        return candidate.anchor_hash
    return candidate.selected_text_hash


def _current_document_hash_status(
    instance: InstanceConfig,
    document_ref: str,
    document: Mapping[str, Any],
    expected_hash: str,
) -> str:
    source_path = _source_pdf_path(instance, document)
    if source_path is None:
        source_path = _source_pdf_path(instance, _registered_document(instance, document_ref))
    if source_path is None:
        return DOCUMENT_HASH_NOT_CHECKED
    try:
        source_hash = file_sha256(source_path)
    except OSError:
        return DOCUMENT_HASH_NOT_CHECKED
    return document_hash_status(expected_hash, source_hash)


def _source_pdf_path(instance: InstanceConfig, document: Mapping[str, Any]) -> Path | None:
    original_path = _cell(document.get("original_path"))
    if not original_path:
        return None
    path = instance.resolve_path(original_path)
    if path is None:
        return None
    try:
        resolved = path.resolve()
        root = instance.instance_root.resolve()
    except OSError:
        return None
    if not _is_relative_to(resolved, root):
        return None
    if _is_blocked_hash_path(resolved, root):
        return None
    try:
        return resolved if resolved.is_file() else None
    except OSError:
        return None


def _is_blocked_hash_path(path: Path, root: Path) -> bool:
    try:
        relative_parts = [part.lower() for part in path.relative_to(root).parts]
    except ValueError:
        return True
    return any(part in BLOCKED_HASH_PATH_PARTS for part in relative_parts)


def _registered_document(instance: InstanceConfig, document_ref: str) -> Mapping[str, Any]:
    try:
        _, rows = read_csv(instance.register("documents"))
    except KeyError:
        return {}
    for row in rows:
        if row.get("doc_id") == document_ref:
            return row
    return {}


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


def _safe_unit(value: Any) -> str:
    try:
        parsed = float(str(value or "").strip())
    except (TypeError, ValueError):
        return ""
    if parsed != parsed or parsed < 0 or parsed > 1:
        return ""
    return _format_float(parsed)


def _reprise_bucket(text_status: str, hash_status: str) -> str:
    normalized_hash_status = _cell(hash_status)
    normalized_text_status = _cell(text_status)
    if normalized_hash_status == DOCUMENT_HASH_MISMATCH:
        return "document_a_reverifier"
    if normalized_hash_status == DOCUMENT_HASH_NOT_CHECKED:
        return "version_a_verifier"
    if normalized_text_status == TEXT_STATUS_UNCONFIRMED:
        return "zone_seule_a_relire"
    return "texte_repere_a_relire"


def _reprise_next_action(text_status: str, hash_status: str) -> str:
    bucket = _reprise_bucket(text_status, hash_status)
    if bucket == "document_a_reverifier":
        return "Rouvrir le PDF et confirmer que la zone pointe toujours le bon passage."
    if bucket == "version_a_verifier":
        return "Verifier la version du PDF avant de reconstruire la donnee."
    if bucket == "zone_seule_a_relire":
        return "Relire manuellement la zone encadree et saisir la donnee utile."
    return "Relire l'extrait repere puis confirmer ou corriger la donnee."


def _diffusion_label(value: str) -> str:
    return "Non diffusable par defaut" if _cell(value) == "non_diffusable" else "Diffusion a verifier"


def _trace_status_label(hash_status: str) -> str:
    if _cell(hash_status) == DOCUMENT_HASH_MISMATCH:
        return "Trace candidate enregistree - a verifier"
    return "Trace candidate enregistree"


def _text_label(value: str, hash_status: str) -> str:
    if _cell(hash_status) == DOCUMENT_HASH_MISMATCH:
        return "Le document a change depuis son ajout dans CoproScope. Verifiez que la zone encadree montre toujours le bon passage."
    if _cell(hash_status) == DOCUMENT_HASH_NOT_CHECKED:
        return "Version du document non verifiee: relisez la zone encadree avant usage."
    if _cell(value) == TEXT_STATUS_UNCONFIRMED:
        return "Texte non confirme : seule la zone encadree est gardee."
    return "Texte repere automatiquement, a relire. Preuve non validee par CoproScope."


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
    "public_trace_reprise_queue",
    "public_trace_summaries",
    "read_document_trace_rows",
    "read_trace_rows",
    "save_zone_trace",
    "trace_register_path",
]
