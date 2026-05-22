from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from .event_types import (
    PASSATION_EXPORT_CREATED,
    PLUGIN_RESULT_RECORDED,
    REQUEST_ACTION_RECORDED,
    REQUEST_CREATED,
    SUGGESTION_OUTCOME_PREPARED,
    SUGGESTION_REVIEW_REQUESTED,
    normalize_event_type,
)


EVENT_DRAFT_SCHEMA = "coproscope.business_event_draft.v1"
SIGNATURE_STATUS_PENDING = "pending_future_signature"
DEFAULT_VISIBILITY = "conseil_syndical"
NON_DIFFUSABLE_VISIBILITY = "non_diffusable"

_HASH_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_.:#-]+$")
_SAFE_REF_RE = re.compile(r"^[A-Za-z0-9_.:#-]+$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_UNIX_ABSOLUTE_RE = re.compile(r"^/(?:Users|home|var|tmp|mnt|etc|private|restricted|raw)(?:/|$)", re.IGNORECASE)
_SENSITIVE_KEY_MARKERS = (
    "api_key",
    "apikey",
    "access_token",
    "client_secret",
    "credential",
    "password",
    "private_path",
    "absolute_path",
    "local_path",
    "secret",
    "token",
)
_PATH_KEY_MARKERS = ("path", "paths", "raw")
_UNSAFE_VALUE_MARKERS = (
    "bearer ",
    "client_secret=",
    "password=",
    "secret=",
    "token=",
    "file://",
    "/raw/",
    "\\raw\\",
    "raw/",
    "raw\\",
    "/restricted/",
    "\\restricted\\",
    "../",
    "..\\",
)


@dataclass(frozen=True)
class BusinessEventDraft:
    event_type: str
    object_id: str
    actor_ref: str
    device_ref: str
    occurred_at: str
    payload_hash: str
    previous_hash: str | None = None
    source_module: str = ""
    visibility: str = DEFAULT_VISIBILITY
    future_signature_status: str = SIGNATURE_STATUS_PENDING

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


def canonical_json(value: object) -> str:
    """Return the canonical JSON form used before hashing event draft payloads."""

    return json.dumps(_canonical_value(value), ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def stable_hash(value: object) -> str:
    canonical = canonical_json(value)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def payload_hash(payload: Mapping[str, object]) -> str:
    assert_payload_safe(payload)
    return stable_hash(payload)


def draft_to_canonical_json(draft: BusinessEventDraft) -> str:
    validate_draft(draft)
    return canonical_json(draft.to_dict())


def draft_hash(draft: BusinessEventDraft) -> str:
    return stable_hash(json.loads(draft_to_canonical_json(draft)))


def build_business_event_draft(
    *,
    event_type: str,
    object_id: str,
    actor_ref: str,
    device_ref: str,
    occurred_at: str,
    payload: Mapping[str, object],
    source_module: str,
    visibility: str = DEFAULT_VISIBILITY,
    previous_hash: str | None = None,
    future_signature_status: str = SIGNATURE_STATUS_PENDING,
) -> BusinessEventDraft:
    draft = BusinessEventDraft(
        event_type=normalize_event_type(event_type),
        object_id=_required_identifier(object_id, "object_id"),
        actor_ref=_required_identifier(actor_ref, "actor_ref"),
        device_ref=_required_identifier(device_ref, "device_ref"),
        occurred_at=_required_text(occurred_at, "occurred_at"),
        payload_hash=payload_hash(payload),
        previous_hash=_optional_hash(previous_hash),
        source_module=_required_identifier(source_module, "source_module"),
        visibility=normalize_visibility(visibility),
        future_signature_status=_required_identifier(future_signature_status, "future_signature_status"),
    )
    validate_draft(draft)
    return draft


def draft_from_requestops_request(
    request: object,
    *,
    actor_ref: str,
    device_ref: str,
    occurred_at: str | None = None,
    previous_hash: str | None = None,
) -> BusinessEventDraft:
    data = _object_mapping(request)
    object_id = _first_text(data, ("request_id", "id"))
    payload = _without_empty(
        {
            "schema": EVENT_DRAFT_SCHEMA,
            "request_id": object_id,
            "channel": _safe_text(data.get("channel")),
            "status": _safe_text(data.get("status")),
            "visibility": normalize_visibility(data.get("visibility")),
            "origin_kind": _safe_text(data.get("origin_kind")),
            "origin_id": _safe_ref(data.get("origin_id")),
            "proof_refs": _safe_refs((data.get("proof_ref"),)),
            "source_refs": _safe_refs((data.get("source_ref"),)),
            "related_point_id": _safe_ref(data.get("related_point_id")),
            "related_action_id": _safe_ref(data.get("related_action_id")),
        }
    )
    return build_business_event_draft(
        event_type=REQUEST_CREATED,
        object_id=object_id,
        actor_ref=actor_ref,
        device_ref=device_ref,
        occurred_at=occurred_at or _first_text(data, ("received_at", "created_at")),
        payload=payload,
        source_module="requestops",
        visibility=data.get("visibility", DEFAULT_VISIBILITY),
        previous_hash=previous_hash,
    )


def draft_from_requestops_action(
    action: object,
    *,
    actor_ref: str,
    device_ref: str,
    occurred_at: str | None = None,
    previous_hash: str | None = None,
) -> BusinessEventDraft:
    data = _object_mapping(action)
    object_id = _first_text(data, ("journal_id", "event_id", "id"))
    payload = _without_empty(
        {
            "schema": EVENT_DRAFT_SCHEMA,
            "journal_id": object_id,
            "request_id": _safe_ref(data.get("request_id")),
            "action_type": _safe_text(data.get("action_type")),
            "status_after": _safe_text(data.get("status_after")),
            "visibility": normalize_visibility(data.get("visibility")),
            "proof_refs": _safe_refs((data.get("proof_ref"),)),
            "source_refs": _safe_refs((data.get("source_ref"),)),
        }
    )
    return build_business_event_draft(
        event_type=REQUEST_ACTION_RECORDED,
        object_id=object_id,
        actor_ref=actor_ref,
        device_ref=device_ref,
        occurred_at=occurred_at or _first_text(data, ("occurred_at", "created_at")),
        payload=payload,
        source_module="requestops",
        visibility=data.get("visibility", DEFAULT_VISIBILITY),
        previous_hash=previous_hash,
    )


def draft_from_suggestionops_suggestion(
    suggestion: object,
    *,
    actor_ref: str,
    device_ref: str,
    occurred_at: str,
    previous_hash: str | None = None,
) -> BusinessEventDraft:
    data = _object_mapping(suggestion)
    object_id = _first_text(data, ("suggestion_id", "id"))
    payload = _without_empty(
        {
            "schema": EVENT_DRAFT_SCHEMA,
            "suggestion_id": object_id,
            "trigger_id": _safe_ref(data.get("trigger_id")),
            "status": _safe_text(data.get("status")),
            "source_refs": _safe_refs((data.get("source"),)),
            "proof_refs": _safe_refs(_split_refs(data.get("proof"))),
            "transformations": tuple(_safe_text(item) for item in _as_sequence(data.get("transformations")) if _safe_text(item)),
            "confidence": _safe_text(data.get("confidence")),
            "public": normalize_visibility(data.get("public")),
        }
    )
    return build_business_event_draft(
        event_type=SUGGESTION_REVIEW_REQUESTED,
        object_id=object_id,
        actor_ref=actor_ref,
        device_ref=device_ref,
        occurred_at=occurred_at,
        payload=payload,
        source_module="suggestionops",
        visibility=data.get("public", DEFAULT_VISIBILITY),
        previous_hash=previous_hash,
    )


def draft_from_suggestionops_outcome(
    outcome: object,
    *,
    actor_ref: str,
    device_ref: str,
    occurred_at: str,
    previous_hash: str | None = None,
) -> BusinessEventDraft:
    data = _object_mapping(outcome)
    object_id = _first_text(data, ("outcome_id", "id"))
    payload_data = _object_mapping(data.get("payload", {}))
    payload = _without_empty(
        {
            "schema": EVENT_DRAFT_SCHEMA,
            "outcome_id": object_id,
            "suggestion_id": _safe_ref(data.get("suggestion_id")),
            "review_id": _safe_ref(data.get("review_id")),
            "outcome_type": _safe_text(data.get("outcome_type")),
            "target_object_type": _safe_text(payload_data.get("object_type")),
            "status": _safe_text(payload_data.get("status")),
            "proof_refs": _safe_refs(_split_refs(data.get("proof"))),
            "source_refs": _safe_refs((data.get("source"),)),
            "public": normalize_visibility(data.get("public")),
        }
    )
    return build_business_event_draft(
        event_type=SUGGESTION_OUTCOME_PREPARED,
        object_id=object_id,
        actor_ref=actor_ref,
        device_ref=device_ref,
        occurred_at=occurred_at,
        payload=payload,
        source_module="suggestionops",
        visibility=data.get("public", DEFAULT_VISIBILITY),
        previous_hash=previous_hash,
    )


def draft_from_plugin_result(
    plugin_result: object,
    *,
    actor_ref: str,
    device_ref: str,
    occurred_at: str,
    previous_hash: str | None = None,
) -> BusinessEventDraft:
    data = _object_mapping(plugin_result)
    signature_payload = _object_mapping(data.get("signature_payload", {}))
    plugin_id = _first_text(data, ("plugin_id",))
    result_event_type = _first_text(data, ("result_event_type",))
    result_hash_text = _first_text(data, ("result_hash",)) or _first_text(signature_payload, ("result_hash",))
    object_id = f"{plugin_id}:{result_event_type}:{_hash_suffix(result_hash_text)}"
    payload = _without_empty(
        {
            "schema": EVENT_DRAFT_SCHEMA,
            "event_type": _safe_text(data.get("event_type")),
            "plugin_id": plugin_id,
            "plugin_version": _safe_text(data.get("plugin_version")),
            "result_event_type": result_event_type,
            "input_hashes": _safe_hash_mapping(data.get("input_hashes")),
            "parameters_hash": _safe_hash(data.get("parameters_hash")),
            "result_hash": _safe_hash(result_hash_text),
            "status": _safe_text(data.get("status")),
            "produced_object_refs": _safe_produced_object_refs(data.get("produced_object_refs")),
            "errors": tuple(_safe_text(item) for item in _as_sequence(data.get("errors")) if _safe_text(item)),
        }
    )
    return build_business_event_draft(
        event_type=PLUGIN_RESULT_RECORDED,
        object_id=object_id,
        actor_ref=actor_ref,
        device_ref=device_ref,
        occurred_at=occurred_at,
        payload=payload,
        source_module="plugins.results",
        visibility=DEFAULT_VISIBILITY,
        previous_hash=previous_hash,
    )


def draft_from_passation_export_ref(
    export_document: Mapping[str, object],
    *,
    actor_ref: str,
    device_ref: str,
    occurred_at: str | None = None,
    previous_hash: str | None = None,
) -> BusinessEventDraft:
    scope = _object_mapping(export_document.get("scope", {}))
    payload = _without_empty(
        {
            "schema": EVENT_DRAFT_SCHEMA,
            "schema_version": _safe_text(export_document.get("schema_version")),
            "source_of_truth": bool(export_document.get("source_of_truth")),
            "source_refs": _safe_refs(export_document.get("source_refs")),
            "proof_refs": _safe_refs(export_document.get("proof_refs")),
            "scope_kind": _safe_text(scope.get("kind")),
            "diffusion": normalize_visibility(scope.get("diffusion")),
        }
    )
    object_id = _safe_ref(export_document.get("export_id")) or f"passation_export:{stable_hash(payload)[7:19]}"
    return build_business_event_draft(
        event_type=PASSATION_EXPORT_CREATED,
        object_id=object_id,
        actor_ref=actor_ref,
        device_ref=device_ref,
        occurred_at=occurred_at or _first_text(export_document, ("generated_at", "created_at")),
        payload=payload,
        source_module="passation_exports",
        visibility=scope.get("diffusion", DEFAULT_VISIBILITY),
        previous_hash=previous_hash,
    )


def assert_payload_safe(payload: Mapping[str, object]) -> None:
    errors: list[str] = []
    _collect_safety_errors(payload, "payload", errors)
    if errors:
        raise ValueError("; ".join(errors))


def validate_draft(draft: BusinessEventDraft) -> bool:
    for field_name in ("event_type", "object_id", "actor_ref", "device_ref", "occurred_at", "payload_hash", "source_module", "visibility"):
        _required_text(getattr(draft, field_name), field_name)
    if draft.event_type != normalize_event_type(draft.event_type):
        raise ValueError("event_type must be canonical V1 lower snake_case")
    for field_name in ("event_type", "object_id", "actor_ref", "device_ref", "source_module", "future_signature_status"):
        _required_identifier(getattr(draft, field_name), field_name)
    _safe_hash(draft.payload_hash)
    _optional_hash(draft.previous_hash)
    if draft.visibility != normalize_visibility(draft.visibility):
        raise ValueError("visibility must be normalized")
    if draft.future_signature_status != SIGNATURE_STATUS_PENDING:
        raise ValueError("future_signature_status is not supported")
    return True


def normalize_visibility(value: object) -> str:
    text = _token(value)
    aliases = {
        "": DEFAULT_VISIBILITY,
        "cs": DEFAULT_VISIBILITY,
        "conseil": DEFAULT_VISIBILITY,
        "conseil_syndical": DEFAULT_VISIBILITY,
        "board": DEFAULT_VISIBILITY,
        "copro": "copro",
        "copropriete": "copro",
        "coproprietaires": "copro",
        "tous_coproprietaires": "copro",
        "public": "public_apres_expurgation",
        "public_apres_expurgation": "public_apres_expurgation",
        "restreint": NON_DIFFUSABLE_VISIBILITY,
        "restricted": NON_DIFFUSABLE_VISIBILITY,
        "confidentiel": NON_DIFFUSABLE_VISIBILITY,
        "confidential": NON_DIFFUSABLE_VISIBILITY,
        "non_exporte": NON_DIFFUSABLE_VISIBILITY,
        "non_diffusable": NON_DIFFUSABLE_VISIBILITY,
    }
    return aliases.get(text, text or DEFAULT_VISIBILITY)


def _canonical_value(value: object) -> object:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(value[key]) for key in sorted(value, key=lambda item: str(item))}
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, set):
        return sorted((_canonical_value(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=True))
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _collect_safety_errors(value: object, location: str, errors: list[str]) -> None:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = _cell(key)
            child_location = f"{location}.{key_text}" if key_text else location
            if _is_sensitive_key(key_text):
                errors.append(f"{child_location} uses a sensitive key")
            if _looks_like_path_key(key_text):
                errors.append(f"{child_location} uses a path/raw key")
            _collect_safety_errors(child, child_location, errors)
        return
    if isinstance(value, (list, tuple, set)):
        for index, child in enumerate(value):
            _collect_safety_errors(child, f"{location}[{index}]", errors)
        return
    if isinstance(value, str) and _contains_unsafe_detail(value):
        errors.append(f"{location} contains unsafe detail")


def _object_mapping(value: object) -> dict[str, Any]:
    if value is None:
        return {}
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        mapped = to_dict()
        if isinstance(mapped, Mapping):
            return dict(mapped)
    return {key: getattr(value, key) for key in dir(value) if not key.startswith("_") and not callable(getattr(value, key))}


def _safe_hash_mapping(value: object) -> dict[str, str]:
    data = _object_mapping(value)
    return {key: _safe_hash(data[key]) for key in sorted(data) if _safe_identifier(key, required=False) and _safe_hash(data[key])}


def _safe_produced_object_refs(value: object) -> tuple[dict[str, str], ...]:
    refs: list[dict[str, str]] = []
    for item in _as_sequence(value):
        data = _object_mapping(item)
        ref = _without_empty(
            {
                "object_type": _safe_text(data.get("object_type")),
                "object_id": _safe_ref(data.get("object_id")),
                "contract_name": _safe_text(data.get("contract_name")),
                "object_hash": _safe_hash(data.get("object_hash")),
            }
        )
        if ref:
            refs.append(ref)
    return tuple(refs)


def _safe_hash(value: object) -> str:
    text = _cell(value)
    if not text:
        return ""
    if not _HASH_RE.match(text):
        raise ValueError("hash must be sha256")
    return text if text.startswith("sha256:") else f"sha256:{text}"


def _optional_hash(value: object) -> str | None:
    text = _cell(value)
    if not text:
        return None
    return _safe_hash(text)


def _required_identifier(value: object, field_name: str) -> str:
    return _safe_identifier(value, field_name=field_name, required=True)


def _safe_identifier(value: object, *, field_name: str = "identifier", required: bool) -> str:
    text = _required_text(value, field_name) if required else _cell(value)
    if not text:
        return ""
    if not _SAFE_IDENTIFIER_RE.match(text) or _contains_unsafe_detail(text):
        raise ValueError(f"{field_name} contains unsafe detail")
    return text


def _required_text(value: object, field_name: str) -> str:
    text = _cell(value)
    if not text:
        raise ValueError(f"{field_name} is required")
    if _contains_unsafe_detail(text):
        raise ValueError(f"{field_name} contains unsafe detail")
    return text


def _safe_text(value: object) -> str:
    text = _cell(value)
    if not text:
        return ""
    if _contains_unsafe_detail(text):
        return ""
    return text


def _safe_ref(value: object) -> str:
    text = _cell(value)
    if not text or _contains_unsafe_detail(text) or not _SAFE_REF_RE.match(text):
        return ""
    return text


def _safe_refs(values: object) -> tuple[str, ...]:
    refs: list[str] = []
    for value in _as_sequence(values):
        ref = _safe_ref(value)
        if ref and ref not in refs:
            refs.append(ref)
    return tuple(refs)


def _split_refs(value: object) -> tuple[str, ...]:
    text = _cell(value)
    if not text:
        return ()
    return tuple(item.strip() for item in re.split(r"[;,|]", text) if item.strip())


def _first_text(data: Mapping[str, object], fields: Iterable[str]) -> str:
    for field_name in fields:
        value = _cell(data.get(field_name))
        if value:
            return value
    return ""


def _hash_suffix(value: object) -> str:
    text = _safe_hash(value)
    return text[7:19] if text else stable_hash(_cell(value))[7:19]


def _without_empty(data: Mapping[str, object]) -> dict[str, object]:
    return {key: value for key, value in data.items() if value not in ("", None, (), [], {})}


def _as_sequence(value: object) -> Sequence[object]:
    if value is None or value == "":
        return ()
    if isinstance(value, (list, tuple, set)):
        return tuple(value)
    return (value,)


def _is_sensitive_key(key: str) -> bool:
    normalized = _token(key)
    return any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS)


def _looks_like_path_key(key: str) -> bool:
    normalized = _token(key)
    return normalized in _PATH_KEY_MARKERS or normalized.endswith("_path") or normalized.endswith("_paths")


def _contains_unsafe_detail(value: str) -> bool:
    text = _cell(value)
    if not text:
        return False
    lowered = text.lower()
    normalized = lowered.replace("/", "\\")
    if _WINDOWS_DRIVE_RE.match(text) or _UNIX_ABSOLUTE_RE.match(text):
        return True
    if text.startswith("\\\\") or "\\" in text:
        return True
    if any(marker in lowered for marker in _UNSAFE_VALUE_MARKERS):
        return True
    if re.search(r"(?<![a-z0-9])raw(?![a-z0-9])", lowered):
        return True
    if re.search(r"(?<![a-z0-9])restricted(?![a-z0-9])", lowered):
        return True
    if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text):
        return True
    if _contains_phone_like_detail(text):
        return True
    if "secret" in normalized or "token=" in normalized or "password=" in normalized:
        return True
    return False


def _token(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _cell(value).lower()).strip("_")


def _contains_phone_like_detail(value: str) -> bool:
    for match in re.finditer(r"(?<!\d)(?:\+?\d[\d .-]{7,}\d)(?!\d)", value):
        text = match.group(0)
        digits = re.sub(r"\D+", "", text)
        if len(digits) < 10:
            continue
        if text.startswith("+") or re.search(r"\d[ .]\d", text):
            return True
        if text.startswith("0") and "-" not in text and len(digits) <= 12:
            return True
    return False


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    if is_dataclass(value):
        return json.dumps(asdict(value), ensure_ascii=True, sort_keys=True)
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(_canonical_value(value), ensure_ascii=True, sort_keys=True)
    return str(value).strip()
