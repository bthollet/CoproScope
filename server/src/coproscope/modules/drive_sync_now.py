from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping

from . import drive_instance_sync, gdrive_rights, gdrive_transport


OK_DOWNLOAD_STATUSES = {"downloaded", "idle"}
OK_RECOVER_STATUSES = {"recovered", "idle"}


def sync_now(
    *,
    instance: Any,
    drive_service: Any,
    folder_id: str,
    sync_root: str | Path,
    local_state_root: str | Path,
    media_factory: Callable[[Path], object] | None = None,
    media_downloader_factory: Callable[[Any], bytes] | None = None,
) -> dict[str, object]:
    sync = Path(sync_root).expanduser().resolve()
    state = Path(local_state_root).expanduser().resolve()
    rights = inspect_drive_sync_rights(drive_service=drive_service, folder_id=folder_id)
    if not drive_rights_allow_sync(rights):
        return _result("blocked", folder_id, rights=rights, blocker=_rights_blocker(rights))

    inbound = apply_remote_now(
        instance=instance,
        drive_service=drive_service,
        folder_id=folder_id,
        sync_root=sync,
        local_state_root=state,
        rights=rights,
        media_downloader_factory=media_downloader_factory,
    )
    downloaded = inbound["downloaded"]
    recovered = inbound["recovered"]
    if inbound["status"] != "ok":
        return _result("blocked", folder_id, rights=rights, downloaded=downloaded, recovered=recovered, blocker=str(inbound["blocker"]))

    outbound = publish_local_now(
        instance=instance,
        drive_service=drive_service,
        folder_id=folder_id,
        sync_root=sync,
        local_state_root=state,
        rights=rights,
        media_factory=media_factory,
    )
    published = outbound["published"]
    uploaded = outbound["uploaded"]
    if outbound["status"] != "ok":
        return _result(
            "blocked",
            folder_id,
            downloaded=downloaded,
            recovered=recovered,
            published=published,
            uploaded=uploaded,
            rights=rights,
            blocker=str(outbound["blocker"]),
        )

    return _result(
        "synced",
        folder_id,
        downloaded=downloaded,
        recovered=recovered,
        published=published,
        uploaded=uploaded,
        rights=rights,
    )


def apply_remote_now(
    *,
    instance: Any,
    drive_service: Any,
    folder_id: str,
    sync_root: str | Path,
    local_state_root: str | Path,
    rights: Mapping[str, object] | None = None,
    media_downloader_factory: Callable[[Any], bytes] | None = None,
) -> dict[str, object]:
    sync = Path(sync_root).expanduser().resolve()
    state = Path(local_state_root).expanduser().resolve()
    rights = rights or inspect_drive_sync_rights(drive_service=drive_service, folder_id=folder_id)
    if not drive_rights_allow_sync(rights):
        return {"status": "blocked", "blocker": _rights_blocker(rights), "rights": rights, "downloaded": None, "recovered": None}

    downloaded = gdrive_transport.download_latest_encrypted_instance_package(
        drive_service=drive_service,
        folder_id=folder_id,
        sync_root=sync,
        media_downloader_factory=media_downloader_factory,
    )
    if str(downloaded.get("status")) not in OK_DOWNLOAD_STATUSES:
        return {"status": "blocked", "blocker": "Lecture Drive bloquee", "downloaded": downloaded, "recovered": None}

    recovered = drive_instance_sync.recover_instance_update(instance=instance, sync_root=sync, local_state_root=state)
    if str(recovered.get("status")) not in OK_RECOVER_STATUSES:
        return {"status": "blocked", "blocker": "Recuperation locale bloquee", "downloaded": downloaded, "recovered": recovered}
    return {"status": "ok", "blocker": "", "downloaded": downloaded, "recovered": recovered}


def publish_local_now(
    *,
    instance: Any,
    drive_service: Any,
    folder_id: str,
    sync_root: str | Path,
    local_state_root: str | Path,
    rights: Mapping[str, object] | None = None,
    shared_state: Mapping[str, object] | None = None,
    minimum_generation: int = 0,
    media_factory: Callable[[Path], object] | None = None,
) -> dict[str, object]:
    sync = Path(sync_root).expanduser().resolve()
    state = Path(local_state_root).expanduser().resolve()
    rights = rights or inspect_drive_sync_rights(drive_service=drive_service, folder_id=folder_id)
    if not drive_rights_allow_sync(rights):
        return {"status": "blocked", "blocker": _rights_blocker(rights), "rights": rights, "published": None, "uploaded": None}

    published = drive_instance_sync.publish_instance_update(
        instance=instance,
        sync_root=sync,
        local_state_root=state,
        shared_state=shared_state,
        minimum_generation=minimum_generation,
    )
    if published.get("status") != "published":
        return {"status": "blocked", "blocker": "Publication locale bloquee", "published": published, "uploaded": None}

    package_path = _published_package_path(sync, state)
    if package_path is None:
        return {"status": "blocked", "blocker": "Paquet chiffre introuvable", "published": published, "uploaded": None}

    uploaded = gdrive_transport.upload_encrypted_instance_package(
        drive_service=drive_service,
        folder_id=folder_id,
        sync_root=sync,
        encrypted_path=package_path,
        media_factory=media_factory,
    )
    if uploaded.get("status") != "uploaded":
        return {"status": "blocked", "blocker": "Envoi Drive bloque", "published": published, "uploaded": uploaded}
    return {"status": "ok", "blocker": "", "published": published, "uploaded": uploaded}


def inspect_drive_sync_rights(*, drive_service: Any, folder_id: str) -> dict[str, object]:
    rights = gdrive_rights.inspect_drive_folder_rights(drive_service=drive_service, folder_id=folder_id)
    validation = gdrive_rights.validate_drive_sync_rights(rights)
    return {
        "status": str(validation.get("status") or "blocked"),
        "summary": str(validation.get("summary") or "Droits Google a verifier."),
        "blocker_code": str(validation.get("blocker_code") or ""),
        "sharing": validation.get("sharing") if isinstance(validation.get("sharing"), Mapping) else {},
        "current_google_account": validation.get("current_google_account") if isinstance(validation.get("current_google_account"), Mapping) else {},
        "payload_disclosure": "counts_only",
        "path_disclosure": "none",
    }


def drive_rights_allow_sync(rights: Mapping[str, object]) -> bool:
    return str(rights.get("status") or "") == "ok"


def _published_package_path(sync: Path, state: Path) -> Path | None:
    publish_state = _read_json(state / "publish_state.json")
    if isinstance(publish_state, Mapping):
        package_hash = str(publish_state.get("package_hash") or "")
        if package_hash:
            candidate = sync / drive_instance_sync.PACKAGE_DIR / f"{package_hash}{drive_instance_sync.PACKAGE_SUFFIX}"
            if candidate.exists() and candidate.is_file():
                return candidate
    packages = sorted((sync / drive_instance_sync.PACKAGE_DIR).glob(f"*{drive_instance_sync.PACKAGE_SUFFIX}"))
    return packages[-1] if packages else None


def _result(
    status: str,
    folder_id: str,
    *,
    downloaded: Mapping[str, object] | None = None,
    recovered: Mapping[str, object] | None = None,
    published: Mapping[str, object] | None = None,
    uploaded: Mapping[str, object] | None = None,
    rights: Mapping[str, object] | None = None,
    blocker: str = "",
) -> dict[str, object]:
    phases = [
        _phase("droits_google", rights),
        _phase("lecture_drive", downloaded),
        _phase("application_locale", recovered),
        _phase("publication_chiffree", published),
        _phase("envoi_drive", uploaded),
    ]
    return {
        "status": status,
        "action": "sync-now",
        "summary": "Synchronisation Drive terminee" if status == "synced" else "Synchronisation Drive bloquee",
        "blocker": blocker,
        "phases": [phase for phase in phases if phase is not None],
        "inbound": {
            "downloaded": bool(downloaded and downloaded.get("downloaded")),
            "applied": bool(recovered and recovered.get("status") == "recovered"),
        },
        "outbound": {
            "published": bool(published and published.get("status") == "published"),
            "uploaded": bool(uploaded and uploaded.get("status") == "uploaded"),
        },
        "drive": {"folder_id_present": bool(folder_id), "id_disclosure": "redacted"},
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _phase(name: str, payload: Mapping[str, object] | None) -> dict[str, object] | None:
    if payload is None:
        return None
    return {"name": name, "status": str(payload.get("status") or "unknown")}


def _rights_blocker(rights: Mapping[str, object]) -> str:
    return str(rights.get("summary") or "Droits Google bloquants.")


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
