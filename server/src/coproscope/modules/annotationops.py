from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any

from ..core.event_types import PDF_ANNOTATION_CREATED
from ..core.events_v1 import BusinessEventDraft, build_business_event_draft, normalize_visibility


SCHEMA_VERSION = "coproscope.annotation.v1"

TARGET_PDF = "pdf"
TARGET_IMAGE = "image"
TARGET_KINDS = frozenset({TARGET_PDF, TARGET_IMAGE})

STATUS_DRAFT = "brouillon"
STATUS_OPEN = "ouverte"
STATUS_REVIEWED = "revue"
STATUS_RESOLVED = "resolue"
STATUS_ARCHIVED = "archivee"
ANNOTATION_STATUSES = frozenset({STATUS_DRAFT, STATUS_OPEN, STATUS_REVIEWED, STATUS_RESOLVED, STATUS_ARCHIVED})

DIFFUSION_CS = "conseil_syndical"
DIFFUSION_COPRO = "copro"
DIFFUSION_PUBLIC_REDACTED = "public_apres_expurgation"
DIFFUSION_BLOCKED = "non_diffusable"
DIFFUSIONS = frozenset({DIFFUSION_CS, DIFFUSION_COPRO, DIFFUSION_PUBLIC_REDACTED, DIFFUSION_BLOCKED})

CONFIDENTIALITY_INTERNAL = "interne"
CONFIDENTIALITY_CS = "reserve_cs"
CONFIDENTIALITY_REDACTION_REQUIRED = "a_biffer"
CONFIDENTIALITY_CONFIDENTIAL = "confidentiel"
CONFIDENTIALITY_BLOCKED = "bloque"
CONFIDENTIALITIES = frozenset(
    {
        CONFIDENTIALITY_INTERNAL,
        CONFIDENTIALITY_CS,
        CONFIDENTIALITY_REDACTION_REQUIRED,
        CONFIDENTIALITY_CONFIDENTIAL,
        CONFIDENTIALITY_BLOCKED,
    }
)

ANNOTATION_EVENT_TYPE = PDF_ANNOTATION_CREATED
SOURCE_MODULE = "annotationops"
NO_SOURCE_WRITE_NOTICE = "source_pdf_or_image_is_never_modified"

_HASH_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$", re.IGNORECASE)
_SAFE_REF_RE = re.compile(r"^[A-Za-z0-9_.:#-]+$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_UNIX_PRIVATE_RE = re.compile(r"^/(?:Users|home|var|tmp|mnt|etc|private|restricted|raw)(?:/|$)", re.IGNORECASE)
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .-]{7,}\d)(?!\d)")


@dataclass(frozen=True)
class AnnotationZone:
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class AnnotationAnchor:
    page: int
    zone: AnnotationZone
    target_kind: str = TARGET_PDF
    fragment_ref: str = ""
    anchor_hash: str = ""


@dataclass(frozen=True)
class CollaborativeAnnotation:
    annotation_id: str
    document_ref: str
    document_hash: str
    anchor: AnnotationAnchor
    comment: str
    author_ref: str
    created_at: str
    point_ref: str
    action_ref: str
    proof_ref: str
    status: str = STATUS_OPEN
    diffusion: str = DIFFUSION_CS
    confidentiality: str = CONFIDENTIALITY_CS
    supersedes_annotation_id: str = ""
    event_refs: tuple[str, ...] = field(default_factory=tuple)
    source_hint_blocked: bool = False
    no_source_write: bool = True


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    reason: str
    severity: str = "error"


def normalize_annotation(row: Mapping[str, Any]) -> CollaborativeAnnotation:
    data = dict(row)
    source_hint = _first_text(data, ("source_path", "original_path", "file_path", "path", "local_path"))
    source_hint_blocked = bool(source_hint and contains_private_path(source_hint))
    document_ref = _safe_ref(_first_text(data, ("document_ref", "doc_id", "document_id", "source_ref")))
    document_hash = _normalize_hash(_first_text(data, ("document_hash", "sha256", "source_hash")))
    page = _int_or_default(_first_text(data, ("page", "page_number", "page_index")), 1)
    anchor = AnnotationAnchor(
        page=page,
        zone=_zone_from_mapping(data),
        target_kind=_normalize_target_kind(_first_text(data, ("target_kind", "media_type", "kind"))),
        fragment_ref=_safe_ref(_first_text(data, ("fragment_ref", "fragment", "selection_ref"))),
        anchor_hash=_normalize_hash(_first_text(data, ("anchor_hash", "selection_hash", "zone_hash"))),
    )
    annotation_id = _safe_ref(_first_text(data, ("annotation_id", "id", "key"))) or _stable_annotation_id(
        document_ref,
        document_hash,
        str(page),
        _first_text(data, ("comment", "commentaire", "note")),
    )
    return CollaborativeAnnotation(
        annotation_id=annotation_id,
        document_ref=document_ref,
        document_hash=document_hash,
        anchor=anchor,
        comment=_safe_text(_first_text(data, ("comment", "commentaire", "note"))),
        author_ref=_safe_ref(_first_text(data, ("author_ref", "actor_ref", "auteur_ref", "created_by"))),
        created_at=_safe_text(_first_text(data, ("created_at", "date", "occurred_at"))),
        point_ref=_safe_ref(_first_text(data, ("point_ref", "point_id", "related_point_id"))),
        action_ref=_safe_ref(_first_text(data, ("action_ref", "action_id", "related_action_id"))),
        proof_ref=_safe_ref(_first_text(data, ("proof_ref", "preuve_ref", "evidence_ref"))),
        status=_normalize_status(_first_text(data, ("status", "statut"))),
        diffusion=_normalize_diffusion(_first_text(data, ("diffusion", "visibility", "public"))),
        confidentiality=_normalize_confidentiality(_first_text(data, ("confidentiality", "confidentialite", "restriction"))),
        supersedes_annotation_id=_safe_ref(_first_text(data, ("supersedes_annotation_id", "remplace_annotation_id"))),
        event_refs=_safe_refs(_as_sequence(data.get("event_refs") or data.get("event_ref"))),
        source_hint_blocked=source_hint_blocked,
        no_source_write=True,
    )


def validate_annotation(annotation: CollaborativeAnnotation) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    required = {
        "annotation_id": annotation.annotation_id,
        "document_ref": annotation.document_ref,
        "document_hash": annotation.document_hash,
        "comment": annotation.comment,
        "author_ref": annotation.author_ref,
        "created_at": annotation.created_at,
        "point_ref": annotation.point_ref,
        "action_ref": annotation.action_ref,
        "proof_ref": annotation.proof_ref,
    }
    for field_name, value in required.items():
        if not _cell(value):
            issues.append(ValidationIssue(field_name, "missing required value"))

    if annotation.source_hint_blocked:
        issues.append(ValidationIssue("source_hint", "private path was supplied and blocked"))
    if not annotation.no_source_write:
        issues.append(ValidationIssue("no_source_write", "annotations must not modify source PDF/image"))
    if not _is_hash(annotation.document_hash):
        issues.append(ValidationIssue("document_hash", "sha256 hash required"))
    if annotation.status not in ANNOTATION_STATUSES:
        issues.append(ValidationIssue("status", f"unsupported status {annotation.status!r}"))
    if annotation.diffusion not in DIFFUSIONS:
        issues.append(ValidationIssue("diffusion", f"unsupported diffusion {annotation.diffusion!r}"))
    if annotation.confidentiality not in CONFIDENTIALITIES:
        issues.append(ValidationIssue("confidentiality", f"unsupported confidentiality {annotation.confidentiality!r}"))
    if annotation.confidentiality in {CONFIDENTIALITY_BLOCKED, CONFIDENTIALITY_CONFIDENTIAL} and annotation.diffusion != DIFFUSION_BLOCKED:
        issues.append(ValidationIssue("diffusion", "confidential or blocked annotations must be non_diffusable"))
    issues.extend(_validate_anchor(annotation.anchor))
    issues.extend(_validate_private_details(annotation))
    issues.extend(_validate_refs(annotation))
    return tuple(issues)


def annotation_to_dict(annotation: CollaborativeAnnotation) -> dict[str, Any]:
    return _json_ready(annotation)


def event_payload(annotation: CollaborativeAnnotation) -> dict[str, Any]:
    _raise_if_invalid(annotation)
    return {
        "schema_version": SCHEMA_VERSION,
        "event_type": ANNOTATION_EVENT_TYPE,
        "annotation_id": annotation.annotation_id,
        "document_ref": annotation.document_ref,
        "document_hash": _normalize_hash(annotation.document_hash),
        "anchor": {
            "page": annotation.anchor.page,
            "zone": asdict(annotation.anchor.zone),
            "target_kind": annotation.anchor.target_kind,
            "fragment_ref": annotation.anchor.fragment_ref,
            "anchor_hash": annotation.anchor.anchor_hash,
        },
        "links": {
            "point_ref": annotation.point_ref,
            "action_ref": annotation.action_ref,
            "proof_ref": annotation.proof_ref,
        },
        "status": annotation.status,
        "diffusion": annotation.diffusion,
        "confidentiality": annotation.confidentiality,
        "non_destructive": True,
        "write_policy": NO_SOURCE_WRITE_NOTICE,
    }


def draft_annotation_event(
    annotation: CollaborativeAnnotation,
    *,
    actor_ref: str,
    device_ref: str,
    occurred_at: str | None = None,
    previous_hash: str | None = None,
) -> BusinessEventDraft:
    payload = event_payload(annotation)
    return build_business_event_draft(
        event_type=ANNOTATION_EVENT_TYPE,
        object_id=annotation.annotation_id,
        actor_ref=actor_ref,
        device_ref=device_ref,
        occurred_at=occurred_at or annotation.created_at,
        payload=payload,
        source_module=SOURCE_MODULE,
        visibility=normalize_visibility(annotation.diffusion),
        previous_hash=previous_hash,
    )


def non_destructive_sidecar_plan(annotation: CollaborativeAnnotation) -> dict[str, Any]:
    _raise_if_invalid(annotation)
    return {
        "source_document_ref": annotation.document_ref,
        "source_document_hash": _normalize_hash(annotation.document_hash),
        "source_write_allowed": False,
        "source_mutation": "forbidden",
        "sidecar_object_ref": f"{annotation.document_ref}:annotations:{annotation.annotation_id}",
        "write_policy": NO_SOURCE_WRITE_NOTICE,
    }


def contains_private_path(value: str) -> bool:
    text = _cell(value)
    if not text:
        return False
    lowered = text.lower()
    if _WINDOWS_DRIVE_RE.match(text) or _UNIX_PRIVATE_RE.match(text):
        return True
    if text.startswith("\\\\") or "file://" in lowered:
        return True
    if "\\" in text or "../" in lowered or "..\\" in lowered:
        return True
    return bool(re.search(r"(^|[\\/])(?:raw|restricted|private|secret)([\\/]|$)", lowered))


def _validate_anchor(anchor: AnnotationAnchor) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    if anchor.target_kind not in TARGET_KINDS:
        issues.append(ValidationIssue("anchor.target_kind", f"unsupported target kind {anchor.target_kind!r}"))
    if anchor.page < 1:
        issues.append(ValidationIssue("anchor.page", "page numbers are one-based"))
    zone_values = (anchor.zone.x, anchor.zone.y, anchor.zone.width, anchor.zone.height)
    if any(value < 0 or value > 1 for value in zone_values):
        issues.append(ValidationIssue("anchor.zone", "zone coordinates must be normalized between 0 and 1"))
    if anchor.zone.width <= 0 or anchor.zone.height <= 0:
        issues.append(ValidationIssue("anchor.zone", "zone width and height must be positive"))
    if anchor.anchor_hash and not _is_hash(anchor.anchor_hash):
        issues.append(ValidationIssue("anchor.anchor_hash", "sha256 hash required"))
    return tuple(issues)


def _validate_private_details(annotation: CollaborativeAnnotation) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for path, value in _walk_text(annotation):
        if contains_private_path(value):
            issues.append(ValidationIssue(path, "private path marker detected"))
        if _EMAIL_RE.search(value):
            issues.append(ValidationIssue(path, "email-like private data detected"))
        if any(_looks_like_phone(match.group(0)) for match in _PHONE_RE.finditer(value)):
            issues.append(ValidationIssue(path, "phone-like private data detected"))
    return tuple(issues)


def _validate_refs(annotation: CollaborativeAnnotation) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for field_name in (
        "annotation_id",
        "document_ref",
        "author_ref",
        "point_ref",
        "action_ref",
        "proof_ref",
        "supersedes_annotation_id",
    ):
        value = _cell(getattr(annotation, field_name))
        if value and not _SAFE_REF_RE.match(value):
            issues.append(ValidationIssue(field_name, "reference must be opaque and path-free"))
    for index, value in enumerate(annotation.event_refs):
        if value and not _SAFE_REF_RE.match(value):
            issues.append(ValidationIssue(f"event_refs[{index}]", "reference must be opaque and path-free"))
    return tuple(issues)


def _raise_if_invalid(annotation: CollaborativeAnnotation) -> None:
    issues = validate_annotation(annotation)
    if issues:
        details = "; ".join(f"{issue.field}: {issue.reason}" for issue in issues if issue.severity == "error")
        raise ValueError(f"Annotation is not event-ready: {details}")


def _zone_from_mapping(data: Mapping[str, Any]) -> AnnotationZone:
    zone = data.get("zone")
    if isinstance(zone, Mapping):
        return AnnotationZone(
            x=_float_or_default(zone.get("x"), 0.0),
            y=_float_or_default(zone.get("y"), 0.0),
            width=_float_or_default(zone.get("width", zone.get("w")), 1.0),
            height=_float_or_default(zone.get("height", zone.get("h")), 1.0),
        )
    if isinstance(zone, (list, tuple)) and len(zone) >= 4:
        return AnnotationZone(
            x=_float_or_default(zone[0], 0.0),
            y=_float_or_default(zone[1], 0.0),
            width=_float_or_default(zone[2], 1.0),
            height=_float_or_default(zone[3], 1.0),
        )
    return AnnotationZone(
        x=_float_or_default(_first_text(data, ("x", "zone_x")), 0.0),
        y=_float_or_default(_first_text(data, ("y", "zone_y")), 0.0),
        width=_float_or_default(_first_text(data, ("width", "w", "zone_width")), 1.0),
        height=_float_or_default(_first_text(data, ("height", "h", "zone_height")), 1.0),
    )


def _normalize_target_kind(value: str) -> str:
    text = _token(value)
    aliases = {"": TARGET_PDF, "pdf": TARGET_PDF, "document_pdf": TARGET_PDF, "image": TARGET_IMAGE, "photo": TARGET_IMAGE}
    return aliases.get(text, text)


def _normalize_status(value: str) -> str:
    text = _token(value)
    aliases = {
        "": STATUS_OPEN,
        "draft": STATUS_DRAFT,
        "brouillon": STATUS_DRAFT,
        "open": STATUS_OPEN,
        "ouverte": STATUS_OPEN,
        "a_traiter": STATUS_OPEN,
        "reviewed": STATUS_REVIEWED,
        "revue": STATUS_REVIEWED,
        "resolved": STATUS_RESOLVED,
        "resolue": STATUS_RESOLVED,
        "archive": STATUS_ARCHIVED,
        "archivee": STATUS_ARCHIVED,
    }
    return aliases.get(text, text)


def _normalize_diffusion(value: str) -> str:
    text = _token(value)
    aliases = {
        "": DIFFUSION_CS,
        "cs": DIFFUSION_CS,
        "conseil": DIFFUSION_CS,
        "conseil_syndical": DIFFUSION_CS,
        "copro": DIFFUSION_COPRO,
        "coproprietaires": DIFFUSION_COPRO,
        "public": DIFFUSION_PUBLIC_REDACTED,
        "public_apres_expurgation": DIFFUSION_PUBLIC_REDACTED,
        "restreint": DIFFUSION_BLOCKED,
        "confidentiel": DIFFUSION_BLOCKED,
        "bloque": DIFFUSION_BLOCKED,
        "non_diffusable": DIFFUSION_BLOCKED,
    }
    return aliases.get(text, text)


def _normalize_confidentiality(value: str) -> str:
    text = _token(value)
    aliases = {
        "": CONFIDENTIALITY_CS,
        "interne": CONFIDENTIALITY_INTERNAL,
        "internal": CONFIDENTIALITY_INTERNAL,
        "cs": CONFIDENTIALITY_CS,
        "reserve_cs": CONFIDENTIALITY_CS,
        "a_biffer": CONFIDENTIALITY_REDACTION_REQUIRED,
        "redaction": CONFIDENTIALITY_REDACTION_REQUIRED,
        "confidentiel": CONFIDENTIALITY_CONFIDENTIAL,
        "confidential": CONFIDENTIALITY_CONFIDENTIAL,
        "bloque": CONFIDENTIALITY_BLOCKED,
        "blocked": CONFIDENTIALITY_BLOCKED,
    }
    return aliases.get(text, text)


def _safe_text(value: Any) -> str:
    return _cell(value)


def _safe_ref(value: Any) -> str:
    text = _cell(value)
    if not text or contains_private_path(text) or not _SAFE_REF_RE.match(text):
        return ""
    return text


def _safe_refs(values: Iterable[Any]) -> tuple[str, ...]:
    refs: list[str] = []
    for value in values:
        ref = _safe_ref(value)
        if ref and ref not in refs:
            refs.append(ref)
    return tuple(refs)


def _normalize_hash(value: Any) -> str:
    text = _cell(value).lower()
    if not text:
        return ""
    if _HASH_RE.match(text):
        return text if text.startswith("sha256:") else f"sha256:{text}"
    return text


def _is_hash(value: Any) -> bool:
    return bool(_HASH_RE.match(_cell(value)))


def _first_text(row: Mapping[str, Any], fields: Iterable[str]) -> str:
    for field_name in fields:
        value = _cell(row.get(field_name))
        if value:
            return value
    return ""


def _stable_annotation_id(*parts: str) -> str:
    material = "|".join(_cell(part) for part in parts if _cell(part)) or "annotation"
    import hashlib

    return f"ANN-{hashlib.sha256(material.encode('utf-8')).hexdigest()[:12].upper()}"


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return {key: _json_ready(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _walk_text(value: object, path: str = "annotation") -> tuple[tuple[str, str], ...]:
    if is_dataclass(value):
        values: list[tuple[str, str]] = []
        for key, item in asdict(value).items():
            values.extend(_walk_text(item, f"{path}.{key}"))
        return tuple(values)
    if isinstance(value, Mapping):
        values = []
        for key, item in value.items():
            values.extend(_walk_text(item, f"{path}.{key}"))
        return tuple(values)
    if isinstance(value, (list, tuple)):
        values = []
        for index, item in enumerate(value):
            values.extend(_walk_text(item, f"{path}[{index}]"))
        return tuple(values)
    if isinstance(value, str):
        return ((path, value),)
    return ()


def _as_sequence(value: object) -> tuple[object, ...]:
    if value is None or value == "":
        return ()
    if isinstance(value, (list, tuple, set)):
        return tuple(value)
    if isinstance(value, str) and (";" in value or "," in value or "|" in value):
        return tuple(item.strip() for item in re.split(r"[;,|]", value) if item.strip())
    return (value,)


def _int_or_default(value: Any, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _float_or_default(value: Any, default: float) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _looks_like_phone(value: str) -> bool:
    digits = re.sub(r"\D+", "", value)
    return len(digits) >= 10


def _token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _cell(value).lower()).strip("_")


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    if is_dataclass(value):
        return str(asdict(value))
    if isinstance(value, (dict, list, tuple, set)):
        return str(value)
    return str(value).strip()
