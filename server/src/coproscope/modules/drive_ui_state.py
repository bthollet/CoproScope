from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from coproscope.core.common import env_snapshot

from . import drive_folder_status, drive_sync_now, drive_watch, gdriveops, gdrive_transport


@dataclass(frozen=True)
class DriveUiConfig:
    configured: bool
    folder_id: str
    sync_root: Path
    local_state_root: Path
    token_path: Path | None
    client_secrets_path: Path | None


def inspect_drive_ui_state(instance: Any) -> dict[str, object]:
    config = resolve_drive_ui_config(instance)
    oauth = gdriveops.oauth_status(
        client_secrets_path=config.client_secrets_path,
        token_path=config.token_path,
    )
    folder = drive_folder_status.inspect_drive_sync_folder(config.sync_root)
    watch = _watch_state(config.local_state_root)
    can_sync = bool(config.configured and oauth.get("status") == "ready" and folder.get("status") == "ready")
    status = _overall_status(config, oauth, folder)
    return {
        "configured": config.configured,
        "status": status,
        "bar_state": _bar_state(status),
        "can_sync": can_sync,
        "folder": _public_folder(config, folder),
        "oauth": _public_oauth(oauth),
        "watch": watch,
        "real_sync": {
            "enabled": can_sync,
            "href": "/coffre/drive/synchroniser",
            "label": "Synchroniser maintenant",
            "help": _sync_help(config, oauth, folder),
        },
        "disclosure": {
            "folder_id": "redacted",
            "token_path": "redacted",
            "local_paths": "redacted",
        },
    }


def sync_now_from_instance(
    *,
    instance: Any,
    drive_service_factory: Callable[..., Any] | None = None,
    media_factory: Callable[[Path], object] | None = None,
    media_downloader_factory: Callable[[Any], bytes] | None = None,
) -> dict[str, object]:
    config = resolve_drive_ui_config(instance)
    state = inspect_drive_ui_state(instance)
    if not state.get("can_sync"):
        return _ui_blocked("Synchronisation a configurer", str(state["real_sync"]["help"]))
    factory = drive_service_factory or gdrive_transport.build_drive_service
    service = factory(token_path=config.token_path)
    result = drive_sync_now.sync_now(
        instance=instance,
        drive_service=service,
        folder_id=config.folder_id,
        sync_root=config.sync_root,
        local_state_root=config.local_state_root,
        media_factory=media_factory,
        media_downloader_factory=media_downloader_factory,
    )
    return _ui_sync_result(result)


def resolve_drive_ui_config(instance: Any) -> DriveUiConfig:
    settings = _drive_settings(instance)
    env = env_snapshot(instance)
    folder_id = _first_text(settings, env, "folder_id", "google_folder_id", "drive_folder_id", "COPROSCOPE_DRIVE_FOLDER_ID")
    sync_root = _resolve_path(
        instance,
        _first_text(settings, env, "sync_root", "encrypted_sync_root", "COPROSCOPE_DRIVE_SYNC_ROOT"),
        default_artifact="drive_instance_demo_sync",
    )
    local_state_root = _resolve_path(
        instance,
        _first_text(settings, env, "local_state_root", "state_root", "COPROSCOPE_DRIVE_LOCAL_STATE_ROOT"),
        default_artifact="drive_instance_sync_state",
    )
    token_path = _optional_path(instance, _first_text(settings, env, "token_path", "COPROSCOPE_DRIVE_TOKEN_PATH"))
    client_path = _optional_path(instance, _first_text(settings, env, "client_secrets_path", "COPROSCOPE_DRIVE_CLIENT_SECRETS"))
    return DriveUiConfig(
        configured=bool(folder_id),
        folder_id=folder_id,
        sync_root=sync_root,
        local_state_root=local_state_root,
        token_path=token_path,
        client_secrets_path=client_path,
    )


def _drive_settings(instance: Any) -> Mapping[str, object]:
    settings = instance.settings() if hasattr(instance, "settings") else {}
    if not isinstance(settings, Mapping):
        return {}
    drive = settings.get("drive_sync") or settings.get("drive") or settings.get("google_drive")
    return drive if isinstance(drive, Mapping) else {}


def _first_text(settings: Mapping[str, object], env: Mapping[str, str], *keys: str) -> str:
    for key in keys:
        value = settings.get(key) if key in settings else env.get(key)
        text = " ".join(str(value or "").split())
        if text:
            return text[:300]
    return ""


def _resolve_path(instance: Any, value: str, *, default_artifact: str) -> Path:
    if value:
        resolved = instance.resolve_path(value) if hasattr(instance, "resolve_path") else Path(value)
        if resolved is not None:
            return Path(resolved).expanduser().resolve()
    try:
        return Path(instance.artifact(default_artifact)).expanduser().resolve()
    except Exception:
        return (Path(instance.instance_root) / "staging" / default_artifact).expanduser().resolve()


def _optional_path(instance: Any, value: str) -> Path | None:
    if not value:
        return None
    resolved = instance.resolve_path(value) if hasattr(instance, "resolve_path") else Path(value)
    return Path(resolved).expanduser().resolve() if resolved is not None else None


def _overall_status(config: DriveUiConfig, oauth: Mapping[str, object], folder: Mapping[str, object]) -> str:
    if not config.configured:
        return "not_configured"
    if oauth.get("status") != "ready":
        return "action_required"
    if folder.get("status") != "ready":
        return "blocked"
    return "ready"


def _bar_state(status: str) -> str:
    return {"ready": "ok", "blocked": "error"}.get(status, "setup")


def _public_folder(config: DriveUiConfig, folder: Mapping[str, object]) -> dict[str, object]:
    return {
        "state": "Dossier Google choisi" if config.configured else "Aucun dossier choisi",
        "headline": "Surface chiffree prete" if folder.get("status") == "ready" else "A preparer",
        "summary": "Le dossier local chiffre est pret." if folder.get("status") == "ready" else "Le dossier chiffre local n'est pas encore pret.",
        "share_label": "Droits Google a verifier" if config.configured else "Droits Google non lus",
        "share_detail": "CoproScope garde les identifiants Google masques dans l'interface.",
        "status": str(folder.get("status") or "not_configured"),
    }


def _public_oauth(oauth: Mapping[str, object]) -> dict[str, object]:
    return {
        "label": "Compte Google pret" if oauth.get("status") == "ready" else "Compte Google a connecter",
        "scope_policy": "Drive limite aux fichiers crees par CoproScope",
        "status": str(oauth.get("status") or "action_required"),
    }


def _watch_state(local_state_root: Path) -> dict[str, object]:
    path = local_state_root / drive_watch.WATCH_STATE_FILE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"label": "Aucun passage en direct", "remote_package_count": 0}
    count = int(payload.get("remote_package_count") or 0) if isinstance(payload, Mapping) else 0
    return {"label": "Dernier passage connu", "remote_package_count": count}


def _sync_help(config: DriveUiConfig, oauth: Mapping[str, object], folder: Mapping[str, object]) -> str:
    if not config.configured:
        return "Choisissez d'abord le dossier Google Drive chiffre."
    if oauth.get("status") != "ready":
        return "Connectez Google Drive avec l'autorisation minimale."
    if folder.get("status") != "ready":
        return "Preparez la surface chiffree locale avant la synchronisation."
    return "Lit Drive, applique les paquets chiffres, puis envoie la version chiffree de ce poste."


def _ui_blocked(title: str, detail: str) -> dict[str, object]:
    return {
        "action": "sync-now",
        "status": "blocked",
        "summary": detail,
        "result_label": title,
        "share_label": "Aucun identifiant Google ni chemin local n'est affiche.",
        "steps": [
            {"label": "Configuration", "state": "Bloque", "detail": detail},
            {"label": "Lecture Drive", "state": "A lancer", "detail": "Non lancee."},
            {"label": "Envoi chiffre", "state": "A lancer", "detail": "Non lance."},
        ],
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _ui_sync_result(result: Mapping[str, object]) -> dict[str, object]:
    status = str(result.get("status") or "blocked")
    blocked = status != "synced"
    return {
        "action": "sync-now",
        "status": "blocked" if blocked else "synced",
        "summary": str(result.get("summary") or ("Synchronisation Drive bloquee" if blocked else "Synchronisation Drive terminee")),
        "result_label": "Synchronisation bloquee" if blocked else "Synchronisation terminee",
        "share_label": "Dossier Google configure; identifiants et chemins restent masques.",
        "steps": [
            _phase_step("Lire Drive", result, "lecture_drive"),
            _phase_step("Appliquer ici", result, "application_locale"),
            _phase_step("Envoyer chiffre", result, "envoi_drive"),
        ],
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _phase_step(label: str, result: Mapping[str, object], phase_name: str) -> dict[str, str]:
    status = "waiting"
    for phase in result.get("phases", []) if isinstance(result.get("phases"), list) else []:
        if isinstance(phase, Mapping) and phase.get("name") == phase_name:
            status = str(phase.get("status") or "waiting")
    if status in {"downloaded", "recovered", "uploaded", "published", "idle"}:
        return {"label": label, "state": "OK", "detail": "Termine sans contenu lisible."}
    if status == "unknown" or status == "waiting":
        return {"label": label, "state": "A lancer", "detail": "Non lance."}
    return {"label": label, "state": "Bloque", "detail": "Controle a reprendre."}
