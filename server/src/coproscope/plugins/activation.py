from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict, dataclass

from coproscope.plugins.catalog import (
    CATALOG_VERSION,
    PluginManifest,
    get_plugin_manifest,
    recommended_plugins_for_vault,
    required_plugins_for_vault,
)


ACTIVATION_EVENT_TYPE = "plugin_activated"
ACTIVATION_STATUS_READY_FOR_SIGNATURE = "ready_for_signature"
ACTIVATION_STATUS_BLOCKED = "blocked"
ACTIVATION_STATUS_REVOKED = "revoked"
REVOCATION_STATUS_VALID = "valid"
REVOCATION_STATUS_REVOKED = "revoked"
REVOCATION_STATUS_UNKNOWN = "unknown"
SIGNATURE_STATUS_PENDING = "pending_future_signature"


@dataclass(frozen=True)
class PluginCompatibilityCheck:
    compatible: bool
    catalog_version: str
    app_version: str
    vault_format_version: str
    python_version: str
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PluginActivationRequest:
    plugin_id: str
    activated_by: str
    activated_at: str
    permissions_granted: tuple[str, ...]
    config_hash: str = "sha256:empty-config"
    activated_by_policy: str = "explicit_user_activation"
    app_version: str = "0.1.0"
    vault_format_version: str = "1"
    revocation_status: str = REVOCATION_STATUS_VALID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PluginActivationEvent:
    event_type: str
    plugin_id: str
    plugin_version: str
    manifest_hash: str
    permissions_granted: tuple[str, ...]
    config_hash: str
    activated_by: str
    activated_by_policy: str
    activated_at: str
    activation_status: str
    revocation_status: str
    signature_status: str
    compatibility: PluginCompatibilityCheck
    required_by_vault: bool
    recommended_by_vault: bool
    errors: tuple[str, ...]
    signature_payload: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def required_vault_plugin_ids() -> frozenset[str]:
    return frozenset(plugin.plugin_id for plugin in required_plugins_for_vault())


def recommended_vault_plugin_ids() -> frozenset[str]:
    return frozenset(plugin.plugin_id for plugin in recommended_plugins_for_vault())


def canonical_manifest_payload(manifest: PluginManifest) -> dict[str, object]:
    payload = manifest.to_dict()
    payload.pop("signature", None)
    return payload


def hash_plugin_manifest(manifest: PluginManifest) -> str:
    canonical = json.dumps(
        canonical_manifest_payload(manifest),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def check_plugin_compatibility(
    manifest: PluginManifest,
    *,
    app_version: str,
    vault_format_version: str,
    python_version: str | None = None,
    catalog_version: str = CATALOG_VERSION,
) -> PluginCompatibilityCheck:
    compatibility = manifest.compatibility
    actual_python = python_version or sys.version.split()[0]
    errors: list[str] = []

    if compatibility.catalog_version != catalog_version:
        errors.append(
            f"catalog version mismatch: expected {compatibility.catalog_version}, got {catalog_version}"
        )
    if _version_lt(app_version, compatibility.app_min_version):
        errors.append(
            f"app version {app_version} is below required {compatibility.app_min_version}"
        )
    if compatibility.app_max_version and _version_gt(app_version, compatibility.app_max_version):
        errors.append(
            f"app version {app_version} is above supported {compatibility.app_max_version}"
        )
    if _version_lt(vault_format_version, compatibility.vault_format_min):
        errors.append(
            f"vault format {vault_format_version} is below required {compatibility.vault_format_min}"
        )
    if compatibility.vault_format_max and _version_gt(
        vault_format_version, compatibility.vault_format_max
    ):
        errors.append(
            f"vault format {vault_format_version} is above supported {compatibility.vault_format_max}"
        )
    if _version_lt(actual_python, compatibility.python_min):
        errors.append(
            f"python version {actual_python} is below required {compatibility.python_min}"
        )

    return PluginCompatibilityCheck(
        compatible=not errors,
        catalog_version=catalog_version,
        app_version=app_version,
        vault_format_version=vault_format_version,
        python_version=actual_python,
        errors=tuple(errors),
    )


def prepare_plugin_activation(request: PluginActivationRequest) -> PluginActivationEvent:
    manifest = get_plugin_manifest(request.plugin_id)
    compatibility = check_plugin_compatibility(
        manifest,
        app_version=request.app_version,
        vault_format_version=request.vault_format_version,
    )
    manifest_hash = hash_plugin_manifest(manifest)
    errors = (
        *_v1_policy_errors(manifest),
        *_revocation_errors(request.revocation_status),
        *_permission_errors(manifest, request.permissions_granted),
        *compatibility.errors,
    )
    activation_status = _activation_status(request.revocation_status, errors)
    signature_payload = _signature_payload(
        request=request,
        manifest=manifest,
        manifest_hash=manifest_hash,
        activation_status=activation_status,
        compatibility=compatibility,
        errors=tuple(errors),
    )

    return PluginActivationEvent(
        event_type=ACTIVATION_EVENT_TYPE,
        plugin_id=manifest.plugin_id,
        plugin_version=manifest.version,
        manifest_hash=manifest_hash,
        permissions_granted=tuple(request.permissions_granted),
        config_hash=request.config_hash,
        activated_by=request.activated_by,
        activated_by_policy=request.activated_by_policy,
        activated_at=request.activated_at,
        activation_status=activation_status,
        revocation_status=request.revocation_status,
        signature_status=SIGNATURE_STATUS_PENDING,
        compatibility=compatibility,
        required_by_vault=manifest.plugin_id in required_vault_plugin_ids(),
        recommended_by_vault=manifest.plugin_id in recommended_vault_plugin_ids(),
        errors=tuple(errors),
        signature_payload=signature_payload,
    )


def _signature_payload(
    *,
    request: PluginActivationRequest,
    manifest: PluginManifest,
    manifest_hash: str,
    activation_status: str,
    compatibility: PluginCompatibilityCheck,
    errors: tuple[str, ...],
) -> dict[str, object]:
    return {
        "event_type": ACTIVATION_EVENT_TYPE,
        "plugin_id": manifest.plugin_id,
        "plugin_version": manifest.version,
        "manifest_hash": manifest_hash,
        "permissions_granted": tuple(request.permissions_granted),
        "config_hash": request.config_hash,
        "activated_by": request.activated_by,
        "activated_by_policy": request.activated_by_policy,
        "activated_at": request.activated_at,
        "activation_status": activation_status,
        "revocation_status": request.revocation_status,
        "compatibility": compatibility.to_dict(),
        "errors": errors,
    }


def _v1_policy_errors(manifest: PluginManifest) -> tuple[str, ...]:
    errors: list[str] = []
    if not manifest.official:
        errors.append(f"{manifest.plugin_id}: only official plugins are allowed in V1")
    if manifest.community_allowed_v1:
        errors.append(f"{manifest.plugin_id}: community plugins are not allowed in V1")
    if manifest.auto_update:
        errors.append(f"{manifest.plugin_id}: auto-update is forbidden in V1")
    if not manifest.local_outside_vault:
        errors.append(f"{manifest.plugin_id}: plugin code must stay local and outside the vault")
    if not manifest.activation_requires_signature:
        errors.append(f"{manifest.plugin_id}: activation must require a future signature")
    return tuple(errors)


def _revocation_errors(revocation_status: str) -> tuple[str, ...]:
    if revocation_status == REVOCATION_STATUS_VALID:
        return ()
    if revocation_status == REVOCATION_STATUS_REVOKED:
        return ("manifest is revoked",)
    if revocation_status == REVOCATION_STATUS_UNKNOWN:
        return ("manifest revocation status is unknown",)
    return (f"unknown revocation status: {revocation_status}",)


def _permission_errors(
    manifest: PluginManifest,
    permissions_granted: tuple[str, ...],
) -> tuple[str, ...]:
    allowed_permissions = {permission.code for permission in manifest.permissions}
    errors = [
        f"{manifest.plugin_id}: unknown permission granted: {permission}"
        for permission in permissions_granted
        if permission not in allowed_permissions
    ]
    return tuple(errors)


def _activation_status(revocation_status: str, errors: tuple[str, ...]) -> str:
    if revocation_status == REVOCATION_STATUS_REVOKED:
        return ACTIVATION_STATUS_REVOKED
    if errors:
        return ACTIVATION_STATUS_BLOCKED
    return ACTIVATION_STATUS_READY_FOR_SIGNATURE


def _version_lt(left: str, right: str) -> bool:
    left_parts, right_parts = _padded_version_tuple(left, right)
    return left_parts < right_parts


def _version_gt(left: str, right: str) -> bool:
    left_parts, right_parts = _padded_version_tuple(left, right)
    return left_parts > right_parts


def _padded_version_tuple(left: str, right: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
    left_parts = _version_tuple(left)
    right_parts = _version_tuple(right)
    length = max(len(left_parts), len(right_parts))
    return (
        left_parts + (0,) * (length - len(left_parts)),
        right_parts + (0,) * (length - len(right_parts)),
    )


def _version_tuple(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for raw_part in version.split("."):
        digits = ""
        for character in raw_part:
            if not character.isdigit():
                break
            digits += character
        parts.append(int(digits or "0"))
    return tuple(parts)
