from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Mapping

from coproscope.plugins.activation import SIGNATURE_STATUS_PENDING
from coproscope.plugins.catalog import PluginManifest, get_plugin_manifest


PLUGIN_RESULT_RECORDED_EVENT_TYPE = "plugin_result_recorded"
RESULT_STATUS_COMPLETED = "completed"
RESULT_STATUS_PARTIAL = "partial"
RESULT_STATUS_FAILED = "failed"
RESULT_STATUS_BLOCKED = "blocked"
RESULT_STATUSES = (
    RESULT_STATUS_COMPLETED,
    RESULT_STATUS_PARTIAL,
    RESULT_STATUS_FAILED,
    RESULT_STATUS_BLOCKED,
)

_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SAFE_REF_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_PATH_MARKERS = (
    "/raw/",
    "\\raw\\",
    "raw/",
    "raw\\",
    "../",
    "..\\",
    "/restricted/",
    "\\restricted\\",
    "/private/",
    "\\private\\",
)
_SENSITIVE_KEY_MARKERS = (
    "api_key",
    "apikey",
    "access_token",
    "client_secret",
    "credential",
    "password",
    "secret",
    "token",
)
_SENSITIVE_VALUE_MARKERS = (
    "bearer ",
    "client_secret=",
    "password=",
    "secret=",
    "token=",
)
_INVALID_HASH_PLACEHOLDER = "sha256:invalid"


@dataclass(frozen=True)
class PluginProducedObjectRef:
    object_type: str
    object_id: str
    contract_name: str
    object_hash: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PluginResultRecordRequest:
    plugin_id: str
    result_event_type: str
    input_hashes: Mapping[str, str]
    parameters_hash: str
    result_hash: str
    status: str = RESULT_STATUS_COMPLETED
    warnings: tuple[str, ...] = ()
    produced_object_refs: tuple[PluginProducedObjectRef, ...] = ()


@dataclass(frozen=True)
class PluginResultRecorded:
    event_type: str
    plugin_id: str
    plugin_version: str
    result_event_type: str
    input_hashes: dict[str, str]
    parameters_hash: str
    result_hash: str
    status: str
    warnings: tuple[str, ...]
    produced_object_refs: tuple[PluginProducedObjectRef, ...]
    signature_status: str
    errors: tuple[str, ...]
    signature_payload: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def prepare_plugin_result_recorded(request: PluginResultRecordRequest) -> PluginResultRecorded:
    manifest = get_plugin_manifest(request.plugin_id)
    errors: list[str] = []
    input_hashes = _safe_input_hashes(request.input_hashes, errors)
    parameters_hash = _safe_hash(request.parameters_hash, "parameters_hash", errors)
    result_hash = _safe_hash(request.result_hash, "result_hash", errors)
    warnings = _safe_warnings(request.warnings, errors)
    produced_object_refs = _safe_produced_object_refs(
        request.produced_object_refs,
        manifest,
        errors,
    )
    result_event_type = _safe_result_event_type(request.result_event_type, errors)
    errors.extend(_result_event_errors(manifest, result_event_type))
    requested_status = request.status if request.status in RESULT_STATUSES else RESULT_STATUS_BLOCKED
    if request.status not in RESULT_STATUSES:
        errors.append("status is not supported")
    status = RESULT_STATUS_BLOCKED if errors else requested_status
    signature_payload = _signature_payload(
        manifest=manifest,
        result_event_type=result_event_type,
        input_hashes=input_hashes,
        parameters_hash=parameters_hash,
        result_hash=result_hash,
        status=status,
        warnings=warnings,
        produced_object_refs=produced_object_refs,
        errors=tuple(errors),
    )

    return PluginResultRecorded(
        event_type=PLUGIN_RESULT_RECORDED_EVENT_TYPE,
        plugin_id=manifest.plugin_id,
        plugin_version=manifest.version,
        result_event_type=result_event_type,
        input_hashes=input_hashes,
        parameters_hash=parameters_hash,
        result_hash=result_hash,
        status=status,
        warnings=warnings,
        produced_object_refs=produced_object_refs,
        signature_status=SIGNATURE_STATUS_PENDING,
        errors=tuple(errors),
        signature_payload=signature_payload,
    )


def validate_result_payload_safety(payload: Mapping[str, object]) -> tuple[str, ...]:
    errors: list[str] = []
    _collect_payload_safety_errors(payload, "", errors)
    return tuple(errors)


def _signature_payload(
    *,
    manifest: PluginManifest,
    result_event_type: str,
    input_hashes: dict[str, str],
    parameters_hash: str,
    result_hash: str,
    status: str,
    warnings: tuple[str, ...],
    produced_object_refs: tuple[PluginProducedObjectRef, ...],
    errors: tuple[str, ...],
) -> dict[str, object]:
    payload = {
        "event_type": PLUGIN_RESULT_RECORDED_EVENT_TYPE,
        "plugin_id": manifest.plugin_id,
        "plugin_version": manifest.version,
        "result_event_type": result_event_type,
        "input_hashes": input_hashes,
        "parameters_hash": parameters_hash,
        "result_hash": result_hash,
        "status": status,
        "warnings": warnings,
        "produced_object_refs": tuple(ref.to_dict() for ref in produced_object_refs),
        "errors": errors,
    }
    safety_errors = validate_result_payload_safety(payload)
    if safety_errors:
        payload = {
            **payload,
            "status": RESULT_STATUS_BLOCKED,
            "errors": (*errors, *safety_errors),
        }
    return payload


def _safe_input_hashes(input_hashes: Mapping[str, str], errors: list[str]) -> dict[str, str]:
    safe: dict[str, str] = {}
    for key in sorted(input_hashes):
        value = input_hashes[key]
        location = f"input_hashes.{key}"
        if not _is_safe_key(key):
            errors.append("input_hashes contains an unsafe input key")
            continue
        if not _is_sha256(value):
            errors.append(f"{location} is not a sha256 hash")
            continue
        safe[key] = value
    return safe


def _safe_hash(value: str, field_name: str, errors: list[str]) -> str:
    if _is_sha256(value):
        return value
    errors.append(f"{field_name} is not a sha256 hash")
    return _INVALID_HASH_PLACEHOLDER


def _safe_warnings(warnings: tuple[str, ...], errors: list[str]) -> tuple[str, ...]:
    safe: list[str] = []
    for index, warning in enumerate(warnings):
        if _contains_private_path_or_secret(warning) or "\n" in warning or "\r" in warning:
            errors.append(f"warnings[{index}] contains unsafe detail")
            continue
        safe.append(warning)
    return tuple(safe)


def _safe_result_event_type(result_event_type: str, errors: list[str]) -> str:
    if _is_safe_identifier(result_event_type):
        return result_event_type
    errors.append("result_event_type contains unsafe detail")
    return "invalid.result_event_type"


def _safe_produced_object_refs(
    produced_object_refs: tuple[PluginProducedObjectRef, ...],
    manifest: PluginManifest,
    errors: list[str],
) -> tuple[PluginProducedObjectRef, ...]:
    output_contracts = {contract.name for contract in manifest.output_contracts}
    safe: list[PluginProducedObjectRef] = []
    for index, ref in enumerate(produced_object_refs):
        prefix = f"produced_object_refs[{index}]"
        if ref.contract_name not in output_contracts:
            errors.append(f"{prefix}.contract_name is not declared by the plugin manifest")
            continue
        if not _is_safe_identifier(ref.object_type):
            errors.append(f"{prefix}.object_type contains unsafe detail")
            continue
        if not _is_safe_identifier(ref.object_id):
            errors.append(f"{prefix}.object_id contains unsafe detail")
            continue
        if not _is_safe_identifier(ref.contract_name):
            errors.append(f"{prefix}.contract_name contains unsafe detail")
            continue
        if not _is_sha256(ref.object_hash):
            errors.append(f"{prefix}.object_hash is not a sha256 hash")
            continue
        safe.append(ref)
    return tuple(safe)


def _result_event_errors(manifest: PluginManifest, result_event_type: str) -> tuple[str, ...]:
    if result_event_type in manifest.event_types_produced:
        return ()
    return (f"{manifest.plugin_id}: result_event_type is not declared by the plugin manifest",)


def _collect_payload_safety_errors(
    value: object,
    location: str,
    errors: list[str],
) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_location = f"{location}.{key_text}" if location else key_text
            if _is_sensitive_key(key_text) and key_text != "parameters_hash":
                errors.append(f"{child_location} uses a sensitive key")
            if _looks_like_path_key(key_text):
                errors.append(f"{child_location} uses a path key")
            _collect_payload_safety_errors(child, child_location, errors)
        return
    if isinstance(value, (tuple, list)):
        for index, child in enumerate(value):
            _collect_payload_safety_errors(child, f"{location}[{index}]", errors)
        return
    if isinstance(value, str) and _contains_private_path_or_secret(value):
        errors.append(f"{location or 'payload'} contains unsafe detail")


def _is_sha256(value: str) -> bool:
    return bool(_HASH_RE.match(value))


def _is_safe_identifier(value: str) -> bool:
    return (
        bool(_SAFE_REF_RE.match(value))
        and not _is_sensitive_key(value)
        and not _looks_like_path_key(value)
        and not _contains_private_path_or_secret(value)
    )


def _is_safe_key(value: str) -> bool:
    return _is_safe_identifier(value)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS)


def _looks_like_path_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized.endswith("_path") or normalized == "path" or normalized.endswith("_paths")


def _contains_private_path_or_secret(value: str) -> bool:
    normalized = value.lower()
    if _WINDOWS_DRIVE_RE.match(value) or normalized.startswith(("/", "\\")):
        return True
    if any(marker in normalized for marker in _PATH_MARKERS):
        return True
    if any(marker in normalized for marker in _SENSITIVE_VALUE_MARKERS):
        return True
    return False
