from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping

from . import drive_sync_now, gdrive_transport


WATCH_STATE_FILE = "drive_watch_state.json"


def watch_once(
    *,
    instance: Any,
    drive_service: Any,
    folder_id: str,
    sync_root: str | Path,
    local_state_root: str | Path,
    local_change_marker: str | None = None,
    media_factory: Callable[[Path], object] | None = None,
    media_downloader_factory: Callable[[Any], bytes] | None = None,
) -> dict[str, object]:
    sync = Path(sync_root).expanduser().resolve()
    state = Path(local_state_root).expanduser().resolve()
    if state == sync or _is_relative_to(state, sync):
        return _blocked("local_state_inside_drive", "Etat local mal place", folder_id)

    previous = _read_state(state)
    remote = gdrive_transport.list_encrypted_instance_packages(drive_service=drive_service, folder_id=folder_id)
    remote_fingerprint = _remote_fingerprint(remote)
    local_fingerprint = _fingerprint(local_change_marker if local_change_marker is not None else _instance_marker(instance))
    previous_remote = str(previous.get("remote_fingerprint") or "")
    previous_local = str(previous.get("local_fingerprint") or "")
    remote_changed = remote_fingerprint != previous_remote
    local_changed = local_fingerprint != previous_local
    actions: list[dict[str, object]] = []
    inbound: Mapping[str, object] | None = None
    outbound: Mapping[str, object] | None = None

    if remote_changed and int(remote.get("remote_package_count") or 0) == 0 and previous_remote:
        return _blocked("remote_packages_missing", "Paquets Drive manquants", folder_id)

    if remote_changed and int(remote.get("remote_package_count") or 0) > 0:
        inbound = drive_sync_now.apply_remote_now(
            instance=instance,
            drive_service=drive_service,
            folder_id=folder_id,
            sync_root=sync,
            local_state_root=state,
            media_downloader_factory=media_downloader_factory,
        )
        actions.append(_action("remote", inbound))
        if inbound.get("status") != "ok":
            return _result("blocked", folder_id, remote_changed, local_changed, actions, inbound=inbound)

    if local_changed:
        outbound = drive_sync_now.publish_local_now(
            instance=instance,
            drive_service=drive_service,
            folder_id=folder_id,
            sync_root=sync,
            local_state_root=state,
            media_factory=media_factory,
        )
        actions.append(_action("local", outbound))
        if outbound.get("status") != "ok":
            return _result("blocked", folder_id, remote_changed, local_changed, actions, inbound=inbound, outbound=outbound)
        remote = gdrive_transport.list_encrypted_instance_packages(drive_service=drive_service, folder_id=folder_id)
        remote_fingerprint = _remote_fingerprint(remote)

    _write_state(
        state,
        {
            "remote_fingerprint": remote_fingerprint,
            "remote_package_count": int(remote.get("remote_package_count") or 0),
            "local_fingerprint": local_fingerprint,
        },
    )
    status = "synced" if actions else "idle"
    return _result(status, folder_id, remote_changed, local_changed, actions, inbound=inbound, outbound=outbound)


def _result(
    status: str,
    folder_id: str,
    remote_changed: bool,
    local_changed: bool,
    actions: list[dict[str, object]],
    *,
    inbound: Mapping[str, object] | None = None,
    outbound: Mapping[str, object] | None = None,
) -> dict[str, object]:
    return {
        "status": status,
        "action": "watch-once",
        "summary": "Surveillance Drive terminee" if status != "blocked" else "Surveillance Drive bloquee",
        "changes": {"remote": remote_changed, "local": local_changed},
        "actions": actions,
        "inbound": {
            "checked": inbound is not None,
            "applied": bool(_nested_status(inbound, "recovered") == "recovered"),
        },
        "outbound": {
            "checked": outbound is not None,
            "uploaded": bool(_nested_status(outbound, "uploaded") == "uploaded"),
        },
        "drive": {"folder_id_present": bool(folder_id), "id_disclosure": "redacted"},
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _blocked(code: str, message: str, folder_id: str) -> dict[str, object]:
    return {
        "status": "blocked",
        "action": "watch-once",
        "blocker_code": code,
        "summary": message,
        "drive": {"folder_id_present": bool(folder_id), "id_disclosure": "redacted"},
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _action(source: str, payload: Mapping[str, object]) -> dict[str, object]:
    return {"source": source, "status": str(payload.get("status") or "unknown")}


def _nested_status(payload: Mapping[str, object] | None, key: str) -> str:
    if not payload:
        return ""
    nested = payload.get(key)
    return str(nested.get("status") or "") if isinstance(nested, Mapping) else ""


def _remote_fingerprint(remote: Mapping[str, object]) -> str:
    packages = remote.get("packages")
    stable = []
    for item in packages if isinstance(packages, list) else []:
        if isinstance(item, Mapping):
            stable.append(
                {
                    "generation": item.get("generation"),
                    "remote_ref": item.get("remote_ref"),
                    "sha256": item.get("sha256"),
                    "size_bytes": item.get("size_bytes"),
                }
            )
    return _fingerprint(json.dumps(sorted(stable, key=lambda item: str(item)), sort_keys=True, ensure_ascii=True))


def _instance_marker(instance: Any) -> str:
    return json.dumps(
        {
            "instance_id": str(getattr(instance, "instance_id", ""))[:120],
            "name": str(getattr(instance, "name", ""))[:120],
        },
        sort_keys=True,
        ensure_ascii=True,
    )


def _fingerprint(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def _read_state(state: Path) -> dict[str, object]:
    try:
        payload = json.loads((state / WATCH_STATE_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_state(state: Path, payload: Mapping[str, object]) -> None:
    state.mkdir(parents=True, exist_ok=True)
    (state / WATCH_STATE_FILE).write_text(json.dumps(payload, sort_keys=True, ensure_ascii=True), encoding="utf-8")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
