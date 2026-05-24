from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field, replace
from typing import Any

from coproscope.core.event_types import (
    ACTION_CREATED,
    EVENT_TYPE_SET_V1,
    EXPORT_CREATED,
    PASSATION_EXPORT_CREATED,
    PDF_ANNOTATION_CREATED,
    PLUGIN_ACTIVATED,
    PLUGIN_RESULT_RECORDED,
    REQUEST_ACTION_RECORDED,
    REQUEST_CREATED,
    normalize_event_type,
)
from coproscope.core.events_v1 import stable_hash
from coproscope.vault.business_events import (
    BUSINESS_EVENT_VAULT_ENVELOPE_SCHEMA,
    BusinessEventVaultEnvelope,
    envelope_hash,
)


PROJECTION_SCHEMA_VERSION = "coproscope.vault.business_projection.v1"

_SUPPORTED_EVENT_TYPES: dict[str, tuple[str, str]] = {
    REQUEST_CREATED: ("requests", "request"),
    REQUEST_ACTION_RECORDED: ("actions", "request_action"),
    ACTION_CREATED: ("actions", "action"),
    PLUGIN_ACTIVATED: ("plugins", "plugin"),
    PLUGIN_RESULT_RECORDED: ("plugins", "plugin_run"),
    EXPORT_CREATED: ("exports", "export"),
    PASSATION_EXPORT_CREATED: ("exports", "passation_export"),
    PDF_ANNOTATION_CREATED: ("annotations", "annotation"),
}

_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_VAULT_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_SAFE_REF_RE = re.compile(r"^[A-Za-z0-9_.:#-]+$")
_FORBIDDEN_PAYLOAD_KEYS = frozenset({"payload", "clear_payload", "encrypted_payload", "business_payload"})


@dataclass(frozen=True)
class ProjectionDiagnostic:
    code: str
    severity: str
    message: str
    event_hash: str = ""
    event_type: str = ""
    object_id: str = ""
    existing_event_hash: str = ""
    conflicting_event_hash: str = ""

    def to_dict(self) -> dict[str, str]:
        return {key: value for key, value in asdict(self).items() if value}


@dataclass(frozen=True)
class ProjectedBusinessObject:
    object_id: str
    object_kind: str
    event_type: str
    created_at: str
    occurred_at: str
    source_module: str
    visibility: str
    business_draft_hash: str
    business_payload_hash: str
    first_event_hash: str
    last_event_hash: str
    source_event_hashes: tuple[str, ...] = field(default_factory=tuple)
    device_ids: tuple[str, ...] = field(default_factory=tuple)
    sequences: tuple[int, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def merge_same_business_event(self, other: ProjectedBusinessObject) -> ProjectedBusinessObject:
        return replace(
            self,
            last_event_hash=other.last_event_hash,
            source_event_hashes=_append_unique(self.source_event_hashes, other.source_event_hashes),
            device_ids=_append_unique(self.device_ids, other.device_ids),
            sequences=tuple(sorted(set((*self.sequences, *other.sequences)))),
        )


@dataclass(frozen=True)
class VaultBusinessProjection:
    schema_version: str = PROJECTION_SCHEMA_VERSION
    requests: dict[str, ProjectedBusinessObject] = field(default_factory=dict)
    actions: dict[str, ProjectedBusinessObject] = field(default_factory=dict)
    plugins: dict[str, ProjectedBusinessObject] = field(default_factory=dict)
    exports: dict[str, ProjectedBusinessObject] = field(default_factory=dict)
    annotations: dict[str, ProjectedBusinessObject] = field(default_factory=dict)
    device_sequences: dict[str, dict[int, str]] = field(default_factory=dict)
    diagnostics: tuple[ProjectionDiagnostic, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "requests": _objects_to_dict(self.requests),
            "actions": _objects_to_dict(self.actions),
            "plugins": _objects_to_dict(self.plugins),
            "exports": _objects_to_dict(self.exports),
            "annotations": _objects_to_dict(self.annotations),
            "device_sequences": {
                device_id: {str(sequence): event_hash for sequence, event_hash in sorted(sequences.items())}
                for device_id, sequences in sorted(self.device_sequences.items())
            },
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }

    def projection_hash(self, *, include_diagnostics: bool = True) -> str:
        data = self.to_dict()
        if not include_diagnostics:
            data["diagnostics"] = []
        return stable_hash(data)


def empty_projection() -> VaultBusinessProjection:
    return VaultBusinessProjection()


def project_business_event_envelopes(
    envelopes: Iterable[BusinessEventVaultEnvelope | Mapping[str, Any]],
    *,
    initial: VaultBusinessProjection | None = None,
) -> VaultBusinessProjection:
    projection = initial or empty_projection()
    for envelope in envelopes:
        projection = apply_business_event_envelope(projection, envelope)
    return projection


def apply_business_event_envelope(
    projection: VaultBusinessProjection,
    envelope: BusinessEventVaultEnvelope | Mapping[str, Any],
) -> VaultBusinessProjection:
    data = _envelope_to_dict(envelope)
    diagnostics = list(projection.diagnostics)
    event_hash = _event_hash(data)
    envelope_errors = _validate_envelope(data, event_hash)
    if envelope_errors:
        diagnostics.extend(envelope_errors)
        return _with_diagnostics(projection, diagnostics)

    event_type = str(data["event_type"])
    object_id = str(data["object_id"])
    canonical_type = _canonical_event_type(event_type, event_hash, object_id)
    if isinstance(canonical_type, ProjectionDiagnostic):
        diagnostics.append(canonical_type)
        return _with_diagnostics(projection, diagnostics)

    destination = _SUPPORTED_EVENT_TYPES.get(canonical_type)
    if destination is None:
        diagnostics.append(
            ProjectionDiagnostic(
                code="unknown_event_type",
                severity="warning",
                message="canonical event_type is not applied by the P0 projection",
                event_hash=event_hash,
                event_type=canonical_type,
                object_id=object_id,
            )
        )
        return _with_diagnostics(projection, diagnostics)

    sequence_conflict = _device_sequence_conflict(projection, data, event_hash)
    if sequence_conflict:
        diagnostics.append(sequence_conflict)
        return _with_diagnostics(projection, diagnostics)

    collection_name, object_kind = destination
    candidate = _projected_object(data, event_hash, canonical_type, object_kind)
    collection = getattr(projection, collection_name)
    existing = collection.get(object_id)
    if existing and not _same_business_object(existing, candidate):
        diagnostics.append(
            ProjectionDiagnostic(
                code="conflict",
                severity="error",
                message="object already has a different hash-only business event",
                event_hash=event_hash,
                event_type=canonical_type,
                object_id=object_id,
                existing_event_hash=existing.last_event_hash,
                conflicting_event_hash=candidate.last_event_hash,
            )
        )
        return _with_diagnostics(projection, diagnostics)

    updated = dict(collection)
    updated[object_id] = existing.merge_same_business_event(candidate) if existing else candidate
    device_sequences = _add_device_sequence(projection.device_sequences, data, event_hash)
    return replace(
        projection,
        **{
            collection_name: updated,
            "device_sequences": device_sequences,
            "diagnostics": tuple(diagnostics),
        },
    )


def _envelope_to_dict(envelope: BusinessEventVaultEnvelope | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(envelope, BusinessEventVaultEnvelope):
        return envelope.to_dict()
    data = dict(envelope)
    if "canonical_hash" not in data:
        computed = envelope_hash(data)
        data["canonical_hash"] = computed
        data["vault_event_hash"] = computed.removeprefix("sha256:")
    return data


def _validate_envelope(data: Mapping[str, Any], event_hash: str) -> tuple[ProjectionDiagnostic, ...]:
    diagnostics: list[ProjectionDiagnostic] = []
    event_type = str(data.get("event_type", ""))
    object_id = str(data.get("object_id", ""))

    if data.get("schema_version") != BUSINESS_EVENT_VAULT_ENVELOPE_SCHEMA:
        diagnostics.append(_invalid("invalid_schema", "unsupported business event vault envelope schema", data, event_hash))

    forbidden = sorted(key for key in data if key in _FORBIDDEN_PAYLOAD_KEYS)
    if forbidden:
        diagnostics.append(_invalid("payload_present", f"hash-only envelope contains payload fields: {', '.join(forbidden)}", data, event_hash))

    for field_name in (
        "event_type",
        "object_id",
        "created_at",
        "occurred_at",
        "device_id",
        "author_key_id",
        "business_draft_hash",
        "business_payload_hash",
    ):
        if not str(data.get(field_name, "")).strip():
            diagnostics.append(_invalid("invalid_envelope", f"{field_name} is required", data, event_hash))

    if not _safe_ref(data.get("object_id")):
        diagnostics.append(_invalid("invalid_envelope", "object_id must be an opaque safe reference", data, event_hash))

    sequence = data.get("sequence")
    if not isinstance(sequence, int) or sequence < 1:
        diagnostics.append(_invalid("invalid_envelope", "sequence must be a positive integer", data, event_hash))

    for field_name in ("business_draft_hash", "business_payload_hash", "business_previous_hash"):
        value = str(data.get(field_name, "") or "")
        if value and not _HASH_RE.fullmatch(value):
            diagnostics.append(_invalid("invalid_hash", f"{field_name} must be a sha256 hash", data, event_hash))

    prev_device_event_hash = str(data.get("prev_device_event_hash", "") or "")
    if prev_device_event_hash and not _VAULT_HASH_RE.fullmatch(prev_device_event_hash):
        diagnostics.append(_invalid("invalid_hash", "prev_device_event_hash must be vault sha256 hex", data, event_hash))

    canonical_hash = str(data.get("canonical_hash", "") or "")
    if not _HASH_RE.fullmatch(canonical_hash):
        diagnostics.append(_invalid("invalid_hash", "canonical_hash must be a sha256 hash", data, event_hash))
    else:
        expected_hash = envelope_hash(data)
        if canonical_hash != expected_hash:
            diagnostics.append(_invalid("invalid_hash", "canonical_hash does not match envelope body", data, event_hash))

    vault_event_hash = str(data.get("vault_event_hash", "") or "")
    if vault_event_hash and vault_event_hash != canonical_hash.removeprefix("sha256:"):
        diagnostics.append(_invalid("invalid_hash", "vault_event_hash does not match canonical_hash", data, event_hash))

    if not event_type or not object_id:
        return tuple(diagnostics)
    return tuple(diagnostics)


def _canonical_event_type(event_type: str, event_hash: str, object_id: str) -> str | ProjectionDiagnostic:
    if _SNAKE_CASE_RE.fullmatch(event_type) and event_type not in EVENT_TYPE_SET_V1:
        return ProjectionDiagnostic(
            code="unknown_event_type",
            severity="error",
            message="event_type uses canonical syntax but is not known in V1",
            event_hash=event_hash,
            event_type=event_type,
            object_id=object_id,
        )
    try:
        return normalize_event_type(event_type)
    except ValueError as exc:
        return ProjectionDiagnostic(
            code="invalid_event_type",
            severity="error",
            message=str(exc),
            event_hash=event_hash,
            event_type=event_type,
            object_id=object_id,
        )


def _device_sequence_conflict(
    projection: VaultBusinessProjection,
    data: Mapping[str, Any],
    event_hash: str,
) -> ProjectionDiagnostic | None:
    device_id = str(data.get("device_id", "") or "")
    sequence = data.get("sequence")
    if not device_id or not isinstance(sequence, int):
        return None
    existing_hash = projection.device_sequences.get(device_id, {}).get(sequence)
    if existing_hash and existing_hash != event_hash:
        return ProjectionDiagnostic(
            code="conflict",
            severity="error",
            message="device sequence already points to a different event hash",
            event_hash=event_hash,
            event_type=str(data.get("event_type", "")),
            object_id=str(data.get("object_id", "")),
            existing_event_hash=existing_hash,
            conflicting_event_hash=event_hash,
        )
    return None


def _projected_object(
    data: Mapping[str, Any],
    event_hash: str,
    event_type: str,
    object_kind: str,
) -> ProjectedBusinessObject:
    sequence = data.get("sequence")
    return ProjectedBusinessObject(
        object_id=str(data["object_id"]),
        object_kind=object_kind,
        event_type=event_type,
        created_at=str(data.get("created_at", "")),
        occurred_at=str(data.get("occurred_at", "")),
        source_module=str(data.get("business_source_module", "")),
        visibility=str(data.get("business_visibility", "")),
        business_draft_hash=str(data.get("business_draft_hash", "")),
        business_payload_hash=str(data.get("business_payload_hash", "")),
        first_event_hash=event_hash,
        last_event_hash=event_hash,
        source_event_hashes=(event_hash,),
        device_ids=(str(data.get("device_id", "")),),
        sequences=(sequence,) if isinstance(sequence, int) else (),
    )


def _same_business_object(left: ProjectedBusinessObject, right: ProjectedBusinessObject) -> bool:
    return (
        left.object_kind == right.object_kind
        and left.event_type == right.event_type
        and left.business_draft_hash == right.business_draft_hash
        and left.business_payload_hash == right.business_payload_hash
    )


def _add_device_sequence(
    current: Mapping[str, Mapping[int, str]],
    data: Mapping[str, Any],
    event_hash: str,
) -> dict[str, dict[int, str]]:
    device_id = str(data.get("device_id", "") or "")
    sequence = data.get("sequence")
    result = {key: dict(value) for key, value in current.items()}
    if device_id and isinstance(sequence, int):
        result.setdefault(device_id, {})[sequence] = event_hash
    return result


def _with_diagnostics(
    projection: VaultBusinessProjection,
    diagnostics: list[ProjectionDiagnostic],
) -> VaultBusinessProjection:
    return replace(projection, diagnostics=tuple(diagnostics))


def _invalid(code: str, message: str, data: Mapping[str, Any], event_hash: str) -> ProjectionDiagnostic:
    return ProjectionDiagnostic(
        code=code,
        severity="error",
        message=message,
        event_hash=event_hash,
        event_type=str(data.get("event_type", "") or ""),
        object_id=str(data.get("object_id", "") or ""),
    )


def _event_hash(data: Mapping[str, Any]) -> str:
    canonical_hash = str(data.get("canonical_hash", "") or "")
    if canonical_hash:
        return canonical_hash
    return envelope_hash(data)


def _safe_ref(value: object) -> str:
    text = str(value or "").strip()
    if not text or not _SAFE_REF_RE.fullmatch(text):
        return ""
    return text


def _append_unique(left: tuple[Any, ...], right: tuple[Any, ...]) -> tuple[Any, ...]:
    values = list(left)
    for item in right:
        if item not in values:
            values.append(item)
    return tuple(values)


def _objects_to_dict(objects: Mapping[str, ProjectedBusinessObject]) -> dict[str, dict[str, Any]]:
    return {key: objects[key].to_dict() for key in sorted(objects)}


__all__ = [
    "PROJECTION_SCHEMA_VERSION",
    "ProjectedBusinessObject",
    "ProjectionDiagnostic",
    "VaultBusinessProjection",
    "apply_business_event_envelope",
    "empty_projection",
    "project_business_event_envelopes",
]
