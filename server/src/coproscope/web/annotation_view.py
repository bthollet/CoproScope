from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from ..core.events_v1 import SIGNATURE_STATUS_PENDING
from ..modules import annotationops


STATUS_LABELS = {
    annotationops.STATUS_DRAFT: "brouillon",
    annotationops.STATUS_OPEN: "ouverte",
    annotationops.STATUS_REVIEWED: "revue",
    annotationops.STATUS_RESOLVED: "resolue",
    annotationops.STATUS_ARCHIVED: "archivee",
}

STATUS_CLASS = {
    annotationops.STATUS_DRAFT: "is-review",
    annotationops.STATUS_OPEN: "is-ok",
    annotationops.STATUS_REVIEWED: "is-public",
    annotationops.STATUS_RESOLVED: "is-ok",
    annotationops.STATUS_ARCHIVED: "is-private",
}

TARGET_LABELS = {
    annotationops.TARGET_PDF: "PDF",
    annotationops.TARGET_IMAGE: "image",
}

DIFFUSION_LABELS = {
    annotationops.DIFFUSION_CS: "conseil syndical",
    annotationops.DIFFUSION_COPRO: "coproprietaires",
    annotationops.DIFFUSION_PUBLIC_REDACTED: "public apres biffage",
    annotationops.DIFFUSION_BLOCKED: "non diffusable",
}

CONFIDENTIALITY_LABELS = {
    annotationops.CONFIDENTIALITY_INTERNAL: "interne",
    annotationops.CONFIDENTIALITY_CS: "reserve conseil syndical",
    annotationops.CONFIDENTIALITY_REDACTION_REQUIRED: "biffage requis",
    annotationops.CONFIDENTIALITY_CONFIDENTIAL: "confidentiel",
    annotationops.CONFIDENTIALITY_BLOCKED: "bloque",
}

CONFIDENTIALITY_CLASS = {
    annotationops.CONFIDENTIALITY_INTERNAL: "is-ok",
    annotationops.CONFIDENTIALITY_CS: "is-review",
    annotationops.CONFIDENTIALITY_REDACTION_REQUIRED: "is-risk",
    annotationops.CONFIDENTIALITY_CONFIDENTIAL: "is-private",
    annotationops.CONFIDENTIALITY_BLOCKED: "is-private",
}

_DEFAULT_ANNOTATIONS = object()
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .-]{7,}\d)(?!\d)")


def build_annotations_view(
    annotations: Iterable[annotationops.CollaborativeAnnotation | Mapping[str, Any]] | object = _DEFAULT_ANNOTATIONS,
    *,
    title: str = "Annotations collaboratives",
    intro: str = (
        "Une annotation relie une page et une zone a un commentaire, puis a un point, "
        "une action et une preuve. Le PDF ou l'image source reste intact."
    ),
    document_label: str = "",
    source_label: str = "",
) -> dict[str, Any]:
    """Prepare PDF/image annotation cards for a template without defining a route."""

    source_annotations = [] if annotations is _DEFAULT_ANNOTATIONS else list(annotations)  # type: ignore[arg-type]
    rows = [_annotation_view(annotation) for annotation in source_annotations]
    status_counts = Counter(row["status"] for row in rows)
    confidentiality_counts = Counter(row["confidentiality"] for row in rows)
    invalid_count = sum(1 for row in rows if row["issues"])
    blocked_count = sum(1 for row in rows if row["diffusion"] == annotationops.DIFFUSION_BLOCKED)
    return {
        "title": title,
        "intro": intro,
        "document_label": _text(document_label),
        "source_label": _text(source_label),
        "has_annotations": bool(rows),
        "rows": rows,
        "summary": {
            "total": len(rows),
            "open": status_counts.get(annotationops.STATUS_OPEN, 0),
            "ready_events": sum(1 for row in rows if row["event_ready"]),
            "needs_review": invalid_count,
            "blocked": blocked_count,
        },
        "status_counts": _count_rows(status_counts, STATUS_LABELS),
        "confidentiality_counts": _count_rows(confidentiality_counts, CONFIDENTIALITY_LABELS),
        "legend": _legend(),
        "empty_state": {
            "title": "Aucune annotation a afficher",
            "body": (
                "La vue est prete a recevoir des annotations issues de annotationops. "
                "Chaque ligne devra porter un document_ref, une page, une zone, un commentaire, "
                "un point, une action, une preuve et une regle de confidentialite."
            ),
            "next_step": "Creer une annotation sidecar, puis preparer son evenement futur signe sans modifier le fichier source.",
        },
        "safety": {
            "non_destructive": True,
            "source_write_allowed": False,
            "path_policy": "aucun chemin prive affiche",
            "event_signature_status": SIGNATURE_STATUS_PENDING,
        },
    }


def build_annotations_view_from_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    title: str = "Annotations collaboratives",
    document_label: str = "",
    source_label: str = "",
) -> dict[str, Any]:
    return build_annotations_view(
        [annotationops.normalize_annotation(row) for row in rows],
        title=title,
        document_label=document_label,
        source_label=source_label,
    )


def _annotation_view(annotation_or_row: annotationops.CollaborativeAnnotation | Mapping[str, Any]) -> dict[str, Any]:
    annotation = _annotation(annotation_or_row)
    issues = annotationops.validate_annotation(annotation)
    event_ready = not issues
    confidentiality = annotation.confidentiality
    diffusion = annotation.diffusion
    return {
        "annotation_id": annotation.annotation_id or "ANN-A-COMPLETER",
        "document_ref": annotation.document_ref or "document a renseigner",
        "document_hash": _short_hash(annotation.document_hash),
        "target_kind": annotation.anchor.target_kind,
        "target_kind_label": TARGET_LABELS.get(annotation.anchor.target_kind, annotation.anchor.target_kind),
        "page": annotation.anchor.page,
        "page_label": f"page {annotation.anchor.page}" if annotation.anchor.page >= 1 else "page a corriger",
        "zone": _zone_view(annotation.anchor.zone),
        "comment": _comment_label(annotation.comment),
        "comment_masked": _has_private_detail(annotation.comment),
        "author_ref": annotation.author_ref or "auteur a renseigner",
        "created_at": annotation.created_at or "date a renseigner",
        "point_ref": annotation.point_ref or "point a rattacher",
        "action_ref": annotation.action_ref or "action a rattacher",
        "proof_ref": annotation.proof_ref or "preuve a rattacher",
        "chain_label": _chain_label(annotation.point_ref, annotation.action_ref, annotation.proof_ref),
        "status": annotation.status,
        "status_label": STATUS_LABELS.get(annotation.status, annotation.status or "a verifier"),
        "status_class": STATUS_CLASS.get(annotation.status, "is-review"),
        "diffusion": diffusion,
        "diffusion_label": DIFFUSION_LABELS.get(diffusion, diffusion or "diffusion a choisir"),
        "confidentiality": confidentiality,
        "confidentiality_label": CONFIDENTIALITY_LABELS.get(confidentiality, confidentiality or "a qualifier"),
        "confidentiality_class": CONFIDENTIALITY_CLASS.get(confidentiality, "is-review"),
        "event_ready": event_ready,
        "event": _event_view(annotation, event_ready),
        "sidecar": _sidecar_view(annotation),
        "issues": [_issue_view(issue) for issue in issues],
        "source_hint_blocked": annotation.source_hint_blocked,
        "non_destructive": annotation.no_source_write,
    }


def _annotation(annotation_or_row: annotationops.CollaborativeAnnotation | Mapping[str, Any]) -> annotationops.CollaborativeAnnotation:
    if isinstance(annotation_or_row, annotationops.CollaborativeAnnotation):
        return annotation_or_row
    return annotationops.normalize_annotation(annotation_or_row)


def _event_view(annotation: annotationops.CollaborativeAnnotation, event_ready: bool) -> dict[str, Any]:
    return {
        "event_type": annotationops.ANNOTATION_EVENT_TYPE,
        "signature_status": SIGNATURE_STATUS_PENDING,
        "signature_label": "evenement futur signe",
        "readiness": "pret a signer" if event_ready else "a corriger avant signature",
        "actor_ref": annotation.author_ref or "acteur a renseigner",
        "occurred_at": annotation.created_at or "date a renseigner",
        "write_policy": annotationops.NO_SOURCE_WRITE_NOTICE,
        "payload_scope": "document_ref, hash, page, zone, point, action, preuve, confidentialite",
    }


def _sidecar_view(annotation: annotationops.CollaborativeAnnotation) -> dict[str, Any]:
    document_ref = annotation.document_ref or "DOCUMENT"
    annotation_id = annotation.annotation_id or "ANNOTATION"
    return {
        "source_document_ref": document_ref,
        "source_document_hash": _short_hash(annotation.document_hash),
        "source_write_allowed": False,
        "source_mutation": "forbidden",
        "sidecar_object_ref": f"{document_ref}:annotations:{annotation_id}",
    }


def _zone_view(zone: annotationops.AnnotationZone) -> dict[str, Any]:
    return {
        "x": _percent(zone.x),
        "y": _percent(zone.y),
        "width": _percent(zone.width),
        "height": _percent(zone.height),
        "label": f"x {_percent(zone.x)}, y {_percent(zone.y)}, largeur {_percent(zone.width)}, hauteur {_percent(zone.height)}",
    }


def _issue_view(issue: annotationops.ValidationIssue) -> dict[str, str]:
    return {
        "field": _text(issue.field) or "champ",
        "reason": _text(issue.reason) or "a verifier",
        "severity": _text(issue.severity) or "error",
    }


def _comment_label(value: str) -> str:
    text = _text(value)
    if not text:
        return "Commentaire a renseigner."
    if _has_private_detail(text):
        return "Commentaire masque: detail prive detecte."
    return text


def _has_private_detail(value: str) -> bool:
    text = _text(value)
    if not text:
        return False
    if annotationops.contains_private_path(text):
        return True
    if _EMAIL_RE.search(text):
        return True
    return any(_looks_like_phone(match.group(0)) for match in _PHONE_RE.finditer(text))


def _looks_like_phone(value: str) -> bool:
    digits = re.sub(r"\D+", "", value)
    return len(digits) >= 10


def _chain_label(point_ref: str, action_ref: str, proof_ref: str) -> str:
    parts = [
        f"Point {point_ref}" if point_ref else "Point a rattacher",
        f"Action {action_ref}" if action_ref else "Action a rattacher",
        f"Preuve {proof_ref}" if proof_ref else "Preuve a rattacher",
    ]
    return " -> ".join(parts)


def _legend() -> list[dict[str, str]]:
    return [
        {"status": status, "label": label, "class": STATUS_CLASS.get(status, "is-review")}
        for status, label in STATUS_LABELS.items()
    ]


def _count_rows(counts: Counter[str], labels: Mapping[str, str]) -> list[dict[str, Any]]:
    return [
        {"key": key, "label": labels.get(key, key), "count": count}
        for key, count in counts.items()
        if count
    ]


def _short_hash(value: str) -> str:
    cleaned = _text(value)
    if not cleaned:
        return "empreinte a renseigner"
    prefix = "sha256:"
    body = cleaned[len(prefix) :] if cleaned.startswith(prefix) else cleaned
    if len(body) <= 20:
        return cleaned
    return f"sha256:{body[:12]}...{body[-8:]}"


def _percent(value: float) -> str:
    return f"{value * 100:.0f}%"


def _text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()
