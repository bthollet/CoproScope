from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Mapping

from coproscope.core.events_v1 import BusinessEventDraft, canonical_json, draft_hash, validate_draft


BUSINESS_EVENT_VAULT_ENVELOPE_SCHEMA = "coproscope.vault.business_event_envelope.v1"
BUSINESS_EVENT_VAULT_SIGNATURE_STATUS = "pending_vault_signature"

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.:#-]+$")
_VAULT_EVENT_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class BusinessEventVaultContext:
    vault_id: str
    device_id: str
    author_key_id: str
    sequence: int
    created_at: str
    prev_device_event_hash: str = ""


@dataclass(frozen=True)
class BusinessEventVaultEnvelope:
    body: Mapping[str, Any]
    canonical_hash: str

    @property
    def vault_event_hash(self) -> str:
        return self.canonical_hash.removeprefix("sha256:")

    def to_dict(self) -> dict[str, Any]:
        result = dict(self.body)
        result["canonical_hash"] = self.canonical_hash
        result["vault_event_hash"] = self.vault_event_hash
        return result

    def canonical_body_json(self) -> str:
        return canonical_json(self.body)

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())


def prepare_business_event_envelope(
    draft: BusinessEventDraft,
    context: BusinessEventVaultContext,
) -> BusinessEventVaultEnvelope:
    """Prepare a hash-only business event envelope for a future vault append."""
    validate_draft(draft)
    context_values = _validate_context(context)

    body = _envelope_body(draft, context_values)
    canonical_hash = _canonical_hash(body)
    return BusinessEventVaultEnvelope(body=body, canonical_hash=canonical_hash)


def envelope_hash(envelope_or_body: BusinessEventVaultEnvelope | Mapping[str, Any]) -> str:
    if isinstance(envelope_or_body, BusinessEventVaultEnvelope):
        return envelope_or_body.canonical_hash
    body = dict(envelope_or_body)
    body.pop("canonical_hash", None)
    body.pop("vault_event_hash", None)
    return _canonical_hash(body)


def _envelope_body(draft: BusinessEventDraft, context: Mapping[str, Any]) -> dict[str, Any]:
    business_draft_hash = draft_hash(draft)
    return {
        "schema_version": BUSINESS_EVENT_VAULT_ENVELOPE_SCHEMA,
        "vault_id": context["vault_id"],
        "event_type": draft.event_type,
        "object_id": draft.object_id,
        "sequence": context["sequence"],
        "created_at": context["created_at"],
        "occurred_at": draft.occurred_at,
        "device_id": context["device_id"],
        "author_key_id": context["author_key_id"],
        "prev_device_event_hash": context["prev_device_event_hash"],
        "business_draft_hash": business_draft_hash,
        "business_previous_hash": draft.previous_hash or "",
        "business_payload_hash": draft.payload_hash,
        "business_actor_ref": draft.actor_ref,
        "business_device_ref": draft.device_ref,
        "business_source_module": draft.source_module,
        "business_visibility": draft.visibility,
        "business_future_signature_status": draft.future_signature_status,
        "vault_signature_status": BUSINESS_EVENT_VAULT_SIGNATURE_STATUS,
    }


def _canonical_hash(value: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _validate_context(context: BusinessEventVaultContext) -> dict[str, Any]:
    values = {
        "vault_id": _required_safe_id(context.vault_id, "vault_id"),
        "device_id": _required_safe_id(context.device_id, "device_id"),
        "author_key_id": _required_safe_id(context.author_key_id, "author_key_id"),
        "created_at": str(context.created_at).strip(),
        "prev_device_event_hash": str(context.prev_device_event_hash or "").strip(),
        "sequence": context.sequence,
    }
    if not isinstance(context.sequence, int) or context.sequence < 1:
        raise ValueError("sequence must be a positive integer")
    if not values["created_at"]:
        raise ValueError("created_at is required")
    prev = values["prev_device_event_hash"]
    if prev and not _VAULT_EVENT_HASH_RE.match(prev):
        raise ValueError("prev_device_event_hash must be a vault sha256 hex hash")
    return values


def _required_safe_id(value: object, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    if not _SAFE_ID_RE.match(text):
        raise ValueError(f"{field_name} contains unsafe characters")
    return text


__all__ = [
    "BUSINESS_EVENT_VAULT_ENVELOPE_SCHEMA",
    "BUSINESS_EVENT_VAULT_SIGNATURE_STATUS",
    "BusinessEventVaultContext",
    "BusinessEventVaultEnvelope",
    "envelope_hash",
    "prepare_business_event_envelope",
]
