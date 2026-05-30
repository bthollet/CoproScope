from __future__ import annotations

import re
from types import MappingProxyType
from typing import Final


VAULT_INITIALIZED: Final = "vault_initialized"
MEMBER_INVITED: Final = "member_invited"
MEMBER_REVOKED: Final = "member_revoked"
RECOVERY_KEY_REGISTERED: Final = "recovery_key_registered"
KEY_RECOVERY_PERFORMED: Final = "key_recovery_performed"
ARCHIVE_DOWNLOADED: Final = "archive_downloaded"
ARCHIVE_INTEGRITY_VERIFIED: Final = "archive_integrity_verified"
REPLICA_REGISTERED: Final = "replica_registered"
REPLICA_CHECKED: Final = "replica_checked"

DOCUMENT_ADDED: Final = "document_added"
DOCUMENT_VERSION_ADDED: Final = "document_version_added"
OCR_COMPLETED: Final = "ocr_completed"
CLASSIFICATION_COMPLETED: Final = "classification_completed"
COMMENT_ADDED: Final = "comment_added"
POINT_CREATED: Final = "point_created"
ACTION_CREATED: Final = "action_created"
REQUEST_CREATED: Final = "request_created"
REQUEST_ACTION_RECORDED: Final = "request_action_recorded"
PROOF_RECORDED: Final = "proof_recorded"
OBJECT_FOLLOWUP_RECORDED: Final = "object_followup_recorded"
STATUS_CHANGED: Final = "status_changed"
DIFFUSION_DECIDED: Final = "diffusion_decided"
REDACTION_COMPLETED: Final = "redaction_completed"
EXPORT_CREATED: Final = "export_created"
PASSATION_EXPORT_CREATED: Final = "passation_export_created"
SUGGESTION_REVIEW_REQUESTED: Final = "suggestion_review_requested"
SUGGESTION_OUTCOME_PREPARED: Final = "suggestion_outcome_prepared"
PDF_ANNOTATION_CREATED: Final = "pdf_annotation_created"
PLUGIN_ACTIVATED: Final = "plugin_activated"
PLUGIN_RESULT_RECORDED: Final = "plugin_result_recorded"
MIGRATION_RECORDED: Final = "migration_recorded"

EVENT_TYPES_V1: Final[tuple[str, ...]] = (
    VAULT_INITIALIZED,
    MEMBER_INVITED,
    MEMBER_REVOKED,
    RECOVERY_KEY_REGISTERED,
    KEY_RECOVERY_PERFORMED,
    ARCHIVE_DOWNLOADED,
    ARCHIVE_INTEGRITY_VERIFIED,
    REPLICA_REGISTERED,
    REPLICA_CHECKED,
    DOCUMENT_ADDED,
    DOCUMENT_VERSION_ADDED,
    OCR_COMPLETED,
    CLASSIFICATION_COMPLETED,
    COMMENT_ADDED,
    POINT_CREATED,
    ACTION_CREATED,
    REQUEST_CREATED,
    REQUEST_ACTION_RECORDED,
    PROOF_RECORDED,
    OBJECT_FOLLOWUP_RECORDED,
    STATUS_CHANGED,
    DIFFUSION_DECIDED,
    REDACTION_COMPLETED,
    EXPORT_CREATED,
    PASSATION_EXPORT_CREATED,
    SUGGESTION_REVIEW_REQUESTED,
    SUGGESTION_OUTCOME_PREPARED,
    PDF_ANNOTATION_CREATED,
    PLUGIN_ACTIVATED,
    PLUGIN_RESULT_RECORDED,
    MIGRATION_RECORDED,
)
EVENT_TYPE_SET_V1: Final[frozenset[str]] = frozenset(EVENT_TYPES_V1)

LEGACY_EVENT_TYPE_ALIASES_V1: Final = MappingProxyType(
    {
        "plugin.result_recorded": PLUGIN_RESULT_RECORDED,
        "passation.export_ref_created": PASSATION_EXPORT_CREATED,
        "request.normalized": REQUEST_CREATED,
        "request.action": REQUEST_ACTION_RECORDED,
        "request.action_recorded": REQUEST_ACTION_RECORDED,
        "suggestion.review_requested": SUGGESTION_REVIEW_REQUESTED,
        "suggestion.outcome_prepared": SUGGESTION_OUTCOME_PREPARED,
    }
)

_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_AMBIGUOUS_MARKERS = (".", "-", " ", "/", "\\", ":")


def normalize_event_type(value: object) -> str:
    """Return a canonical V1 event type, or raise ValueError."""

    event_type = _clean_event_type(value)
    if event_type in LEGACY_EVENT_TYPE_ALIASES_V1:
        canonical = LEGACY_EVENT_TYPE_ALIASES_V1[event_type]
        raise ValueError(f"legacy event_type {event_type!r} must be migrated to {canonical!r}")
    if any(marker in event_type for marker in _AMBIGUOUS_MARKERS) or not _SNAKE_CASE_RE.fullmatch(event_type):
        raise ValueError("event_type must use lower snake_case without separators other than '_'")
    if event_type not in EVENT_TYPE_SET_V1:
        raise ValueError(f"unsupported V1 event_type: {event_type}")
    return event_type


def validate_event_type(value: object) -> bool:
    normalize_event_type(value)
    return True


def migrate_legacy_event_type(value: object) -> str:
    event_type = _clean_event_type(value)
    canonical = LEGACY_EVENT_TYPE_ALIASES_V1.get(event_type)
    if canonical:
        return canonical
    return normalize_event_type(event_type)


def _clean_event_type(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("event_type must be a string")
    event_type = value.strip()
    if not event_type:
        raise ValueError("event_type is required")
    return event_type


__all__ = [
    "ACTION_CREATED",
    "ARCHIVE_DOWNLOADED",
    "ARCHIVE_INTEGRITY_VERIFIED",
    "CLASSIFICATION_COMPLETED",
    "COMMENT_ADDED",
    "DIFFUSION_DECIDED",
    "DOCUMENT_ADDED",
    "DOCUMENT_VERSION_ADDED",
    "EVENT_TYPES_V1",
    "EVENT_TYPE_SET_V1",
    "EXPORT_CREATED",
    "KEY_RECOVERY_PERFORMED",
    "LEGACY_EVENT_TYPE_ALIASES_V1",
    "MEMBER_INVITED",
    "MEMBER_REVOKED",
    "MIGRATION_RECORDED",
    "OCR_COMPLETED",
    "PASSATION_EXPORT_CREATED",
    "PDF_ANNOTATION_CREATED",
    "PLUGIN_ACTIVATED",
    "PLUGIN_RESULT_RECORDED",
    "POINT_CREATED",
    "PROOF_RECORDED",
    "OBJECT_FOLLOWUP_RECORDED",
    "RECOVERY_KEY_REGISTERED",
    "REDACTION_COMPLETED",
    "REPLICA_CHECKED",
    "REPLICA_REGISTERED",
    "REQUEST_ACTION_RECORDED",
    "REQUEST_CREATED",
    "STATUS_CHANGED",
    "SUGGESTION_OUTCOME_PREPARED",
    "SUGGESTION_REVIEW_REQUESTED",
    "VAULT_INITIALIZED",
    "migrate_legacy_event_type",
    "normalize_event_type",
    "validate_event_type",
]
