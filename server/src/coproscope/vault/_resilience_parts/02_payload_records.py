from __future__ import annotations



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
