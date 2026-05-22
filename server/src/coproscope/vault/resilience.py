from __future__ import annotations

import json
import unicodedata
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import core


DOCUMENT_EVENT_TYPES = {"document_added", "document_version_added"}
RECOVERY_EVENT_TYPES = {"recovery_key_registered", "key_recovery_registered"}
REPLICA_EVENT_TYPES = {"replica_registered", "replica_checked"}
KEY_COMPARTMENT_EVENT_TYPES = {"key_compartment_registered", "compartment_key_registered"}
COOWNER_ARCHIVE_EVENT_TYPES = {"reconstruction_pack_created", "coowner_archive_created", "complete_archive_created"}
RESILIENCE_EVENT_TYPES = (
    RECOVERY_EVENT_TYPES
    | REPLICA_EVENT_TYPES
    | KEY_COMPARTMENT_EVENT_TYPES
    | COOWNER_ARCHIVE_EVENT_TYPES
    | {"vault_survivability_checked"}
)

RISK_NO_SNAPSHOT = "no_snapshot"
RISK_SINGLE_DEVICE = "single_device"
RISK_MISSING_BLOB = "missing_blob"
RISK_FORBIDDEN_ENTRIES = "forbidden_entries"
RISK_NO_RECOVERY_KEY = "no_recovery_key"
RISK_NO_KEY_QUORUM = "no_key_quorum"
RISK_NO_COOWNER_RECOVERY_GUARDIAN = "no_coowner_recovery_guardian"
RISK_NO_READER_REPLICA = "no_reader_replica"

RISK_ORDER = [
    RISK_NO_SNAPSHOT,
    RISK_SINGLE_DEVICE,
    RISK_MISSING_BLOB,
    RISK_FORBIDDEN_ENTRIES,
    RISK_NO_RECOVERY_KEY,
    RISK_NO_KEY_QUORUM,
    RISK_NO_COOWNER_RECOVERY_GUARDIAN,
    RISK_NO_READER_REPLICA,
]

FORBIDDEN_SYNC_NAMES = set(core.FORBIDDEN_SYNC_NAMES)
FORBIDDEN_SYNC_PREFIXES = set(core.FORBIDDEN_SYNC_PREFIXES)


def audit_survivability(local_root: Path, sync_root: Path) -> dict[str, Any]:
    """Audit whether a local vault remains reconstructible from its sync tree."""
    local = Path(local_root).expanduser().resolve()
    sync = Path(sync_root).expanduser().resolve()

    event_files = _event_files(sync)
    blob_files = _blob_files(sync)
    snapshot_files = _snapshot_files(sync)
    event_envelopes, warnings = _load_event_envelopes(event_files, sync)
    device_ids = sorted({path.parent.name for path in event_files})

    missing_blobs = _find_missing_blobs(local, sync, event_envelopes, warnings)
    forbidden_entries = _forbidden_sync_entries(sync)
    replicas = _discover_replica_manifests(local, sync, event_envelopes, warnings)
    reader_replicas = [replica for replica in replicas if replica.get("is_reader_replica")]
    recovery_governance = _discover_recovery_governance(sync, event_envelopes, warnings)
    key_compartments = _discover_key_compartments(local, sync, event_envelopes, warnings)
    coowner_archive = _discover_coowner_archive(local, sync, event_envelopes, warnings)
    resilience_events = _resilience_event_counts(event_envelopes)

    counts = {
        "events": len(event_files),
        "event_devices": len(device_ids),
        "blobs": len(blob_files),
        "snapshots": len(snapshot_files),
        "replicas": len(replicas),
        "reader_replicas": len(reader_replicas),
        "missing_blobs": len(missing_blobs),
        "forbidden_entries": len(forbidden_entries),
        "recovery_keys": len(recovery_governance["evidence"]),
        "recovery_shares": len(recovery_governance["shares"]),
        "key_compartments": len(key_compartments),
        "coowner_archives": len(coowner_archive["manifests"]),
    }
    risks = _risks(counts, missing_blobs, forbidden_entries, recovery_governance)

    return {
        "ok": True,
        "command": "vault survivability",
        "status": _status_from_risks(risks),
        "survivable": not risks,
        "local_root": str(local),
        "sync_root": str(sync),
        "events": counts["events"],
        "blobs": counts["blobs"],
        "snapshots": counts["snapshots"],
        "counts": counts,
        "risks": risks,
        "devices": device_ids,
        "missing_blobs": missing_blobs,
        "forbidden_entries": forbidden_entries,
        "replicas": replicas,
        "reader_replicas": reader_replicas,
        "recovery_evidence": recovery_governance["evidence"],
        "recovery_governance": recovery_governance,
        "key_compartments": key_compartments,
        "coowner_archive": coowner_archive,
        "resilience_events": resilience_events,
        "diagnostics": _diagnostics(coowner_archive, key_compartments, recovery_governance),
        "warnings": warnings,
    }


def audit_vault_resilience(local_root: Path, sync_root: Path) -> dict[str, Any]:
    """Compatibility alias for callers that name the feature after this module."""
    return audit_survivability(local_root, sync_root)


def _event_files(sync_root: Path) -> list[Path]:
    event_root = sync_root / "events"
    if not event_root.exists():
        return []
    return sorted(path for path in event_root.glob("*/*.json") if path.is_file())


def _blob_files(sync_root: Path) -> list[Path]:
    blob_root = sync_root / "blobs"
    if not blob_root.exists():
        return []
    return sorted(path for path in blob_root.glob("*/*.blob") if path.is_file())


def _snapshot_files(sync_root: Path) -> list[Path]:
    snapshot_root = sync_root / "snapshots"
    if not snapshot_root.exists():
        return []
    return sorted(path for path in snapshot_root.glob("*.snapshot") if path.is_file())


def _load_event_envelopes(event_files: list[Path], sync_root: Path) -> tuple[list[tuple[Path, dict[str, Any]]], list[dict[str, str]]]:
    warnings: list[dict[str, str]] = []
    envelopes: list[tuple[Path, dict[str, Any]]] = []
    for path in event_files:
        try:
            payload = _read_json(path)
            if not isinstance(payload, dict):
                raise RuntimeError("event JSON payload is not an object")
            envelopes.append((path, payload))
        except Exception as exc:  # noqa: BLE001
            warnings.append({"path": _relative_display(path, sync_root), "warning": f"event unreadable: {exc}"})
    return envelopes, warnings


def _find_missing_blobs(
    local_root: Path,
    sync_root: Path,
    event_envelopes: list[tuple[Path, dict[str, Any]]],
    warnings: list[dict[str, str]],
) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    seen: set[str] = set()
    for path, event in event_envelopes:
        if event.get("event_type") not in DOCUMENT_EVENT_TYPES:
            continue
        try:
            payload = core.vault_export_debug_payload(local_root, sync_root, path)
        except Exception as exc:  # noqa: BLE001
            warnings.append({"path": _relative_display(path, sync_root), "warning": f"document payload unreadable: {exc}"})
            continue
        blob_id = str(payload.get("blob_id", ""))
        if not blob_id or blob_id in seen:
            continue
        seen.add(blob_id)
        try:
            blob_path = _blob_path(sync_root, blob_id)
        except RuntimeError as exc:
            warnings.append({"path": _relative_display(path, sync_root), "warning": f"invalid blob id: {exc}"})
            missing.append(
                {
                    "blob_id": blob_id,
                    "expected_path": "",
                    "event_path": _relative_display(path, sync_root),
                }
            )
            continue
        if not blob_path.exists():
            missing.append(
                {
                    "blob_id": blob_id,
                    "expected_path": _relative_display(blob_path, sync_root),
                    "event_path": _relative_display(path, sync_root),
                }
            )
    return missing


def _blob_path(sync_root: Path, blob_id: str) -> Path:
    return core._blob_path(sync_root, blob_id)


def _forbidden_sync_entries(sync_root: Path) -> list[str]:
    if not sync_root.exists():
        return []
    forbidden: list[str] = []
    if sync_root.name in FORBIDDEN_SYNC_NAMES or any(sync_root.name.startswith(prefix) for prefix in FORBIDDEN_SYNC_PREFIXES):
        forbidden.append(str(sync_root))
    for path in sync_root.rglob("*"):
        name = path.name
        if name in FORBIDDEN_SYNC_NAMES or any(name.startswith(prefix) for prefix in FORBIDDEN_SYNC_PREFIXES):
            forbidden.append(str(path))
    return sorted(forbidden)


def _discover_replica_manifests(
    local_root: Path,
    sync_root: Path,
    event_envelopes: list[tuple[Path, dict[str, Any]]],
    warnings: list[dict[str, str]],
) -> list[dict[str, Any]]:
    replicas: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    for path in _json_files(sync_root):
        try:
            payload = _read_json(path)
        except Exception as exc:  # noqa: BLE001
            if _looks_like_replica_path(path, sync_root):
                warnings.append({"path": _relative_display(path, sync_root), "warning": f"replica manifest unreadable: {exc}"})
            continue
        if isinstance(payload, dict) and (_looks_like_replica_path(path, sync_root) or _looks_like_replica_payload(payload)):
            replica = _replica_record(path, sync_root, payload, source="manifest")
            replicas.append(replica)
            seen_sources.add(str(path))

    for path, event in event_envelopes:
        if event.get("event_type") not in REPLICA_EVENT_TYPES or str(path) in seen_sources:
            continue
        payload: dict[str, Any] = {}
        try:
            payload = core.vault_export_debug_payload(local_root, sync_root, path)
        except Exception as exc:  # noqa: BLE001
            warnings.append({"path": _relative_display(path, sync_root), "warning": f"replica event payload unreadable: {exc}"})
        merged = dict(event)
        merged.update(payload)
        replicas.append(_replica_record(path, sync_root, merged, source="event"))
    return replicas


def _discover_recovery_governance(
    sync_root: Path,
    event_envelopes: list[tuple[Path, dict[str, Any]]],
    warnings: list[dict[str, str]],
) -> dict[str, Any]:
    evidence: list[dict[str, str]] = []
    groups: list[dict[str, Any]] = []
    for path, event in event_envelopes:
        if event.get("event_type") in RECOVERY_EVENT_TYPES:
            evidence.append({"source": "event", "path": _relative_display(path, sync_root), "kind": str(event.get("event_type", ""))})

    for path in _json_files(sync_root):
        try:
            payload = _read_json(path)
        except Exception as exc:  # noqa: BLE001
            if _looks_like_recovery_path(path, sync_root):
                warnings.append({"path": _relative_display(path, sync_root), "warning": f"recovery manifest unreadable: {exc}"})
            continue
        if isinstance(payload, dict) and _looks_like_recovery_payload(payload):
            evidence.append({"source": "manifest", "path": _relative_display(path, sync_root), "kind": _recovery_kind(payload)})
            groups.append(_recovery_group(path, sync_root, payload))

    shares = [share for group in groups for share in group["shares"]]
    has_coowner_guardian = any(share["is_coowner_guardian"] for share in shares)
    single_cs_dependency = bool(shares) and all(share["is_cs"] for share in shares)
    quorum_satisfied = any(group["quorum_satisfied"] for group in groups)
    quorum_required = max([group["quorum_required"] for group in groups], default=0)
    return {
        "evidence": evidence,
        "groups": groups,
        "shares": shares,
        "quorum_required": quorum_required,
        "quorum_satisfied": quorum_satisfied,
        "has_coowner_guardian": has_coowner_guardian,
        "single_cs_dependency": single_cs_dependency,
        "no_single_cs_dependency": quorum_satisfied and has_coowner_guardian and not single_cs_dependency,
    }


def _discover_key_compartments(
    local_root: Path,
    sync_root: Path,
    event_envelopes: list[tuple[Path, dict[str, Any]]],
    warnings: list[dict[str, str]],
) -> list[dict[str, Any]]:
    compartments: list[dict[str, Any]] = []
    for path in _json_files(sync_root):
        try:
            payload = _read_json(path)
        except Exception:  # noqa: BLE001
            continue
        if isinstance(payload, dict) and (_looks_like_compartment_path(path, sync_root) or _looks_like_compartment_payload(payload)):
            compartments.append(_key_compartment_record(path, sync_root, payload, source="manifest"))

    for path, event in event_envelopes:
        if event.get("event_type") not in KEY_COMPARTMENT_EVENT_TYPES:
            continue
        payload: dict[str, Any] = {}
        try:
            payload = core.vault_export_debug_payload(local_root, sync_root, path)
        except Exception as exc:  # noqa: BLE001
            warnings.append({"path": _relative_display(path, sync_root), "warning": f"key compartment event payload unreadable: {exc}"})
        merged = dict(event)
        merged.update(payload)
        compartments.append(_key_compartment_record(path, sync_root, merged, source="event"))
    return compartments


def _discover_coowner_archive(
    local_root: Path,
    sync_root: Path,
    event_envelopes: list[tuple[Path, dict[str, Any]]],
    warnings: list[dict[str, str]],
) -> dict[str, Any]:
    manifests: list[dict[str, Any]] = []
    for path in _json_files(sync_root):
        try:
            payload = _read_json(path)
        except Exception:  # noqa: BLE001
            continue
        if isinstance(payload, dict) and (_looks_like_archive_path(path, sync_root) or _looks_like_archive_payload(payload)):
            manifests.append(_coowner_archive_record(path, sync_root, payload, source="manifest"))

    for path, event in event_envelopes:
        if event.get("event_type") not in COOWNER_ARCHIVE_EVENT_TYPES:
            continue
        payload: dict[str, Any] = {}
        try:
            payload = core.vault_export_debug_payload(local_root, sync_root, path)
        except Exception as exc:  # noqa: BLE001
            warnings.append({"path": _relative_display(path, sync_root), "warning": f"coowner archive event payload unreadable: {exc}"})
        merged = dict(event)
        merged.update(payload)
        manifests.append(_coowner_archive_record(path, sync_root, merged, source="event"))

    available = any(item["complete"] and item["coowner_downloadable"] for item in manifests)
    verifiable = any(item["presence_verifiable"] and item["integrity_verifiable"] for item in manifests)
    reconstructible_open_scope = any(item["reconstructible_open_scope"] for item in manifests)
    return {
        "available": available,
        "verifiable": verifiable,
        "reconstructible_open_scope": reconstructible_open_scope,
        "sensitive_compartments_stay_encrypted": any(item["sensitive_compartments_stay_encrypted"] for item in manifests),
        "manifests": manifests,
    }


def _json_files(sync_root: Path) -> list[Path]:
    if not sync_root.exists():
        return []
    return sorted(path for path in sync_root.rglob("*.json") if path.is_file())


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _looks_like_replica_path(path: Path, sync_root: Path) -> bool:
    rel = _relative_display(path, sync_root).lower().replace("\\", "/")
    return "replica" in rel


def _looks_like_replica_payload(payload: Mapping[str, Any]) -> bool:
    if payload.get("event_type") in REPLICA_EVENT_TYPES:
        return True
    return any(
        key in payload
        for key in (
            "replica_id",
            "replica_role",
            "replica_type",
            "reader_replica",
            "read_only",
            "last_checked_at",
            "replica_owner",
        )
    )


def _replica_record(path: Path, sync_root: Path, payload: Mapping[str, Any], *, source: str) -> dict[str, Any]:
    role = _first_text(payload, "role", "replica_role", "access", "access_level", "mode", "profile")
    return {
        "source": source,
        "manifest_path": _relative_display(path, sync_root),
        "replica_id": _first_text(payload, "replica_id", "id", "device_id") or path.stem,
        "role": role,
        "owner": _first_text(payload, "owner", "owner_id", "replica_owner", "holder", "custodian"),
        "last_checked_at": _first_text(payload, "last_checked_at", "checked_at", "updated_at"),
        "is_reader_replica": _is_reader_replica(payload),
    }


def _is_reader_replica(payload: Mapping[str, Any]) -> bool:
    if payload.get("reader_replica") is True or payload.get("read_only") is True:
        return True
    values: list[str] = []
    for key in ("role", "replica_role", "access", "access_level", "mode", "profile", "kind"):
        value = payload.get(key)
        if value is not None:
            values.append(str(value))
    capabilities = payload.get("capabilities")
    if isinstance(capabilities, list):
        values.extend(str(item) for item in capabilities)
    normalized = " ".join(values).lower().replace("_", "-")
    return any(token in normalized for token in ("reader", "read-only", "readonly", "lecteur", "lecture"))


def _looks_like_recovery_path(path: Path, sync_root: Path) -> bool:
    rel = _relative_display(path, sync_root).lower().replace("\\", "/")
    return "recovery" in rel or "secours" in rel


def _looks_like_recovery_payload(payload: Mapping[str, Any]) -> bool:
    if payload.get("event_type") in RECOVERY_EVENT_TYPES:
        return True
    text = json.dumps(payload, sort_keys=True, ensure_ascii=True).lower()
    return any(token in text for token in ("recovery_key", "recovery-key", "secours", "secret_share", "quorum"))


def _recovery_kind(payload: Mapping[str, Any]) -> str:
    return _first_text(payload, "key_type", "kind", "type", "recovery_type") or "recovery"


def _recovery_group(path: Path, sync_root: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    shares = _recovery_shares(path, sync_root, payload)
    declared_share_count = _first_int(payload, "share_count", "shares_count", "total_shares") or len(shares)
    quorum_required = _first_int(payload, "quorum_required", "quorum", "threshold", "required_shares")
    distinct_holders = len({share["holder_id"] or f"share_{index}" for index, share in enumerate(shares, start=1)})
    effective_holders = distinct_holders if shares else declared_share_count
    quorum_satisfied = bool(quorum_required and quorum_required >= 2 and declared_share_count >= quorum_required and effective_holders >= quorum_required)
    return {
        "path": _relative_display(path, sync_root),
        "kind": _recovery_kind(payload),
        "key_id": _first_text(payload, "recovery_key_id", "key_id", "id"),
        "quorum_required": quorum_required,
        "share_count": declared_share_count,
        "distinct_holders": effective_holders,
        "quorum_satisfied": quorum_satisfied,
        "shares": shares,
    }


def _recovery_shares(path: Path, sync_root: Path, payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_shares: Any = None
    for key in ("shares", "recovery_shares", "secret_shares", "guardians", "holders", "custodians"):
        if key in payload:
            raw_shares = payload[key]
            break
    if isinstance(raw_shares, Mapping):
        raw_items = list(raw_shares.values())
    elif isinstance(raw_shares, list):
        raw_items = raw_shares
    else:
        raw_items = []
    return [_recovery_share_record(path, sync_root, item, index) for index, item in enumerate(raw_items, start=1)]


def _recovery_share_record(path: Path, sync_root: Path, item: Any, index: int) -> dict[str, Any]:
    if isinstance(item, Mapping):
        holder_id = _first_text(item, "holder_id", "guardian_id", "member_id", "owner_id", "id", "name")
        role = _first_text(item, "holder_role", "guardian_role", "role", "college", "kind")
    else:
        holder_id = str(item)
        role = ""
    role_source = f"{role} {holder_id}"
    return {
        "path": _relative_display(path, sync_root),
        "holder_id": holder_id or f"share_{index}",
        "role": role,
        "is_cs": _is_cs_role(role_source),
        "is_coowner_guardian": _is_coowner_role(role_source) and not _is_cs_role(role_source),
    }


def _looks_like_compartment_path(path: Path, sync_root: Path) -> bool:
    rel = _relative_display(path, sync_root).lower().replace("\\", "/")
    return "compartment" in rel or "compartiment" in rel


def _looks_like_compartment_payload(payload: Mapping[str, Any]) -> bool:
    if payload.get("event_type") in KEY_COMPARTMENT_EVENT_TYPES:
        return True
    return any(
        key in payload
        for key in (
            "compartment_id",
            "key_compartment_id",
            "compartment_key_id",
            "compartment_key",
            "sensitivity",
            "sensitive_compartment",
        )
    )


def _key_compartment_record(path: Path, sync_root: Path, payload: Mapping[str, Any], *, source: str) -> dict[str, Any]:
    allowed_roles = _text_list(_first_value(payload, "allowed_roles", "reader_roles", "recipient_roles", "roles"))
    sensitivity = _first_text(payload, "sensitivity", "classification", "access_level", "scope")
    encrypted = _truthy(_first_value(payload, "encrypted", "encrypted_at_rest", "sensitive_compartment")) or bool(
        _first_text(payload, "encrypted_key_id", "wrapped_key_id", "key_envelope_id")
    )
    return {
        "source": source,
        "path": _relative_display(path, sync_root),
        "compartment_id": _first_text(payload, "compartment_id", "key_compartment_id", "id", "name") or path.stem,
        "key_id": _first_text(payload, "key_id", "compartment_key_id", "wrapped_key_id", "encrypted_key_id"),
        "sensitivity": sensitivity,
        "encrypted": encrypted,
        "allowed_roles": allowed_roles,
    }


def _looks_like_archive_path(path: Path, sync_root: Path) -> bool:
    rel = _normalized(_relative_display(path, sync_root).replace("\\", "/"))
    has_archive = any(token in rel for token in ("archive", "reconstruction-pack", "reconstruction pack", "export"))
    has_coowner = any(token in rel for token in ("coowner", "copro", "coproprietaire"))
    return has_archive and has_coowner


def _looks_like_archive_payload(payload: Mapping[str, Any]) -> bool:
    if payload.get("event_type") in COOWNER_ARCHIVE_EVENT_TYPES:
        return True
    text = _payload_text(payload)
    has_archive = any(token in text for token in ("archive", "reconstruction_pack", "reconstruction pack", "export"))
    has_coowner = any(token in text for token in ("coowner", "copro", "coproprietaire"))
    has_complete = "complete" in text or "full" in text or payload.get("complete") is True
    return has_archive and has_coowner and has_complete


def _coowner_archive_record(path: Path, sync_root: Path, payload: Mapping[str, Any], *, source: str) -> dict[str, Any]:
    downloadable_by = _text_list(_first_value(payload, "downloadable_by", "allowed_roles", "reader_roles", "recipient_roles"))
    scope = _text_list(_first_value(payload, "reconstructible_scope", "open_scope", "scope"))
    text = _payload_text(payload)
    complete = _truthy(_first_value(payload, "complete", "complete_archive", "full_archive")) or "complete" in text or "full" in text
    coowner_downloadable = _truthy(_first_value(payload, "coowner_downloadable", "downloadable_by_coowners")) or any(
        _is_coowner_role(role) for role in downloadable_by
    )
    presence_marker = _first_value(payload, "presence_verifiable", "presence_manifest")
    integrity_marker = _first_value(payload, "integrity_verifiable", "integrity_manifest")
    presence_verifiable = _truthy(presence_marker) or _nonempty_marker(presence_marker) or any(
        token in payload for token in ("presence_manifest_hash", "events_manifest_hash", "blob_manifest_hash")
    )
    integrity_verifiable = _truthy(integrity_marker) or _nonempty_marker(integrity_marker) or any(
        token in payload for token in ("archive_sha256", "manifest_hash", "integrity_manifest_hash")
    )
    reconstructible_open_scope = _truthy(_first_value(payload, "reconstructible_open_scope")) or any(
        token in _normalized(" ".join(scope)) for token in ("open", "accessible", "coowner", "copro")
    )
    sensitive_encrypted = _truthy(_first_value(payload, "sensitive_compartments_stay_encrypted", "restricted_compartments_encrypted")) or (
        "sensitive" in text and "encrypted" in text
    )
    return {
        "source": source,
        "path": _relative_display(path, sync_root),
        "archive_id": _first_text(payload, "archive_id", "pack_id", "export_id", "id") or path.stem,
        "complete": complete,
        "coowner_downloadable": coowner_downloadable,
        "presence_verifiable": presence_verifiable,
        "integrity_verifiable": integrity_verifiable,
        "reconstructible_open_scope": reconstructible_open_scope,
        "sensitive_compartments_stay_encrypted": sensitive_encrypted,
        "downloadable_by": downloadable_by,
    }


def _first_text(payload: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        text = str(value)
        if text:
            return text
    return ""


def _first_value(payload: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _first_int(payload: Mapping[str, Any], *keys: str) -> int:
    for key in keys:
        value = payload.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def _text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        return [str(item) for item in value.values()]
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y", "oui", "ok"}


def _nonempty_marker(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (list, Mapping)):
        return bool(value)
    return bool(str(value).strip())


def _payload_text(payload: Mapping[str, Any]) -> str:
    return _normalized(json.dumps(payload, sort_keys=True, ensure_ascii=True))


def _normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(character for character in decomposed if ord(character) < 128)
    return ascii_text.lower().replace("_", " ").replace("-", " ")


def _is_cs_role(value: str) -> bool:
    normalized = _normalized(value)
    if any(token in normalized for token in ("non cs", "hors cs", "outside cs")):
        return False
    return (
        normalized.strip() == "cs"
        or normalized.startswith("cs ")
        or " conseil syndical" in f" {normalized}"
        or "syndic council" in normalized
        or "board member" in normalized
    )


def _is_coowner_role(value: str) -> bool:
    normalized = _normalized(value)
    return any(token in normalized for token in ("coowner", "copro", "coproprietaire", "lot owner", "owner reader"))


def _resilience_event_counts(event_envelopes: list[tuple[Path, dict[str, Any]]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for _, event in event_envelopes:
        event_type = str(event.get("event_type", ""))
        if event_type in RESILIENCE_EVENT_TYPES:
            counts[event_type] = counts.get(event_type, 0) + 1
    return dict(sorted(counts.items()))


def _diagnostics(
    coowner_archive: Mapping[str, Any],
    key_compartments: list[dict[str, Any]],
    recovery_governance: Mapping[str, Any],
) -> list[str]:
    diagnostics: list[str] = []
    if not coowner_archive.get("available"):
        diagnostics.append("no_coowner_complete_archive")
    elif not coowner_archive.get("verifiable"):
        diagnostics.append("coowner_archive_not_verifiable")
    if not coowner_archive.get("reconstructible_open_scope"):
        diagnostics.append("coowner_archive_open_scope_not_reconstructible")
    if not coowner_archive.get("sensitive_compartments_stay_encrypted"):
        diagnostics.append("sensitive_compartments_policy_missing")
    if not key_compartments:
        diagnostics.append("no_key_compartments")
    if recovery_governance.get("single_cs_dependency"):
        diagnostics.append("single_cs_recovery_dependency")
    return diagnostics


def _risks(
    counts: Mapping[str, int],
    missing_blobs: list[dict[str, str]],
    forbidden_entries: list[str],
    recovery_governance: Mapping[str, Any],
) -> list[str]:
    present = {
        RISK_NO_SNAPSHOT: counts["snapshots"] == 0,
        RISK_SINGLE_DEVICE: counts["event_devices"] < 2,
        RISK_MISSING_BLOB: bool(missing_blobs),
        RISK_FORBIDDEN_ENTRIES: bool(forbidden_entries),
        RISK_NO_RECOVERY_KEY: counts["recovery_keys"] == 0,
        RISK_NO_KEY_QUORUM: not bool(recovery_governance.get("quorum_satisfied")),
        RISK_NO_COOWNER_RECOVERY_GUARDIAN: not bool(recovery_governance.get("has_coowner_guardian")),
        RISK_NO_READER_REPLICA: counts["reader_replicas"] == 0,
    }
    return [risk for risk in RISK_ORDER if present[risk]]


def _status_from_risks(risks: list[str]) -> str:
    if RISK_MISSING_BLOB in risks:
        return "incomplete"
    if RISK_FORBIDDEN_ENTRIES in risks or RISK_NO_SNAPSHOT in risks:
        return "at_risk"
    if risks:
        return "capture_possible"
    return "reconstructible"


def _relative_display(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)
