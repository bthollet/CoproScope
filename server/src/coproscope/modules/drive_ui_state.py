from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from coproscope.core.common import env_snapshot

from . import drive_folder_status, drive_local_setup, drive_sync_now, drive_watch, gdrive_folder_setup, gdriveops, gdrive_transport


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
    local_setup = drive_local_setup.inspect_local_setup(config.sync_root, config.local_state_root)
    watch = _watch_state(config.local_state_root)
    can_sync = bool(config.configured and oauth.get("status") == "ready" and folder.get("status") == "ready")
    status = _overall_status(config, oauth, folder)
    return {
        "configured": config.configured,
        "status": status,
        "bar_state": _bar_state(status),
        "can_sync": can_sync,
        "folder": _public_folder(config, folder),
        "local_setup": local_setup,
        "oauth": _public_oauth(oauth),
        "watch": watch,
        "oauth_connect": {
            "enabled": _can_connect_google(local_setup, oauth),
            "href": "/coffre/drive/connecter-google",
            "label": "Connecter Google" if oauth.get("status") != "ready" else "Google connecte",
            "help": _oauth_connect_help(local_setup, oauth),
        },
        "real_sync": {
            "enabled": can_sync,
            "href": "/coffre/drive/synchroniser",
            "label": "Synchroniser maintenant",
            "help": _sync_help(config, oauth, folder),
        },
        "google_folder": {
            "enabled": _can_create_google_folder(config, oauth, folder),
            "href": "/coffre/drive/dossier-google/creer",
            "label": "Creer le dossier Google chiffre" if not config.configured else "Dossier Google choisi",
            "help": _google_folder_help(config, oauth, folder),
        },
        "watch_control": {
            "enabled": can_sync,
            "href": "/coffre/drive/surveiller",
            "label": "Surveiller maintenant",
            "help": _watch_help(config, oauth, folder),
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
    )
    return _ui_sync_result(result)


def watch_once_from_instance(
    *,
    instance: Any,
    drive_service_factory: Callable[..., Any] | None = None,
) -> dict[str, object]:
    config = resolve_drive_ui_config(instance)
    state = inspect_drive_ui_state(instance)
    if not state.get("can_sync"):
        return _ui_blocked("Surveillance a configurer", str(state["watch_control"]["help"]), action="watch-once")
    factory = drive_service_factory or gdrive_transport.build_drive_service
    service = factory(token_path=config.token_path)
    result = drive_watch.watch_once(
        instance=instance,
        drive_service=service,
        folder_id=config.folder_id,
        sync_root=config.sync_root,
        local_state_root=config.local_state_root,
    )
    return _ui_watch_result(result)


def create_google_folder_from_instance(
    *,
    instance: Any,
    drive_service_factory: Callable[..., Any] | None = None,
) -> dict[str, object]:
    config = resolve_drive_ui_config(instance)
    state = inspect_drive_ui_state(instance)
    google = state.get("google_folder") if isinstance(state.get("google_folder"), Mapping) else {}
    if not google.get("enabled"):
        return _ui_google_folder_result(
            {
                "status": "blocked",
                "summary": str(google.get("help") or "Dossier Google a configurer."),
                "result_label": "Dossier Google non prepare",
                "share_label": "Aucun identifiant Google n'est affiche.",
            }
        )
    factory = drive_service_factory or gdrive_transport.build_drive_service
    service = factory(token_path=config.token_path)
    result = gdrive_folder_setup.create_private_sync_folder(drive_service=service)
    if result.get("status") == "configured":
        drive_local_setup.save_drive_folder_id(instance, str(result.get("folder_id") or ""))
    return _ui_google_folder_result(result)


def resolve_drive_ui_config(instance: Any) -> DriveUiConfig:
    settings = _drive_settings(instance)
    env = env_snapshot(instance)
    profile = drive_local_setup.drive_profile_settings(instance)
    folder_id = _first_text(settings, env, profile, "folder_id", "google_folder_id", "drive_folder_id", "COPROSCOPE_DRIVE_FOLDER_ID")
    sync_root = _resolve_path(
        instance,
        _first_text(settings, env, profile, "sync_root", "encrypted_sync_root", "COPROSCOPE_DRIVE_SYNC_ROOT"),
        default_artifact="drive_instance_demo_sync",
    )
    local_state_root = _resolve_path(
        instance,
        _first_text(settings, env, profile, "local_state_root", "state_root", "COPROSCOPE_DRIVE_LOCAL_STATE_ROOT"),
        default_artifact="drive_instance_sync_state",
    )
    token_path = _optional_path(instance, _first_text(settings, env, profile, "token_path", "COPROSCOPE_DRIVE_TOKEN_PATH"))
    client_path = _optional_path(instance, _first_text(settings, env, profile, "client_secrets_path", "COPROSCOPE_DRIVE_CLIENT_SECRETS"))
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


def _first_text(settings: Mapping[str, object], env: Mapping[str, str], profile: Mapping[str, object], *keys: str) -> str:
    for key in keys:
        for source in (settings, env, profile):
            value = source.get(key)
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
        "label": "Compte Google pret" if oauth.get("status") == "ready" else "Non connecte",
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
        if folder.get("status") == "ready":
            return "Le dossier local chiffre est pret. Choisissez maintenant le dossier Google Drive."
        return "Choisissez d'abord le dossier Google Drive chiffre."
    if oauth.get("status") != "ready":
        return "Connectez Google Drive avec l'autorisation minimale."
    if folder.get("status") != "ready":
        return "Preparez la surface chiffree locale avant la synchronisation."
    return "Lit Drive, applique les paquets chiffres, puis envoie la version chiffree de ce poste."


def _watch_help(config: DriveUiConfig, oauth: Mapping[str, object], folder: Mapping[str, object]) -> str:
    if not config.configured:
        if folder.get("status") == "ready":
            return "Le dossier local chiffre est pret. Choisissez maintenant le dossier Google Drive."
        return "Choisissez d'abord le dossier Google Drive chiffre."
    if oauth.get("status") != "ready":
        return "Connectez Google Drive avec l'autorisation minimale."
    if folder.get("status") != "ready":
        return "Preparez la surface chiffree locale avant la surveillance."
    return "Controle Drive et ce poste une fois; les details visibles restent limites a ce poste."


def _can_connect_google(local_setup: Mapping[str, object], oauth: Mapping[str, object]) -> bool:
    return bool(local_setup.get("status") == "ready" and oauth.get("status") != "ready")


def _oauth_connect_help(local_setup: Mapping[str, object], oauth: Mapping[str, object]) -> str:
    if oauth.get("status") == "ready":
        return "Google est connecte pour ce poste."
    if local_setup.get("status") != "ready":
        return "Preparez ce poste avant de connecter Google."
    return "Ouvre la connexion Google dans le navigateur, puis revient ici."


def _can_create_google_folder(config: DriveUiConfig, oauth: Mapping[str, object], folder: Mapping[str, object]) -> bool:
    return bool(not config.configured and oauth.get("status") == "ready" and folder.get("status") == "ready")


def _google_folder_help(config: DriveUiConfig, oauth: Mapping[str, object], folder: Mapping[str, object]) -> str:
    if config.configured:
        return "Le dossier Google chiffre est deja choisi pour ce poste."
    if folder.get("status") != "ready":
        return "Preparez ce poste avant de creer le dossier Google."
    if oauth.get("status") != "ready":
        return "Connectez Google avant de creer le dossier Google chiffre."
    return "Cree un dossier Drive reserve aux paquets chiffres CoproScope."


def _ui_blocked(title: str, detail: str, *, action: str = "sync-now") -> dict[str, object]:
    return {
        "action": action,
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


def _ui_google_folder_result(result: Mapping[str, object]) -> dict[str, object]:
    status = str(result.get("status") or "blocked")
    ready = status == "configured"
    return {
        "action": "google-folder",
        "status": "configured" if ready else "blocked",
        "summary": _safe_text(result.get("summary"), "Dossier Google non prepare."),
        "result_label": _safe_text(result.get("result_label"), "Dossier Google"),
        "share_label": _safe_text(result.get("share_label"), "Aucun identifiant Google n'est affiche."),
        "steps": [
            {"label": "Verifier ce poste", "state": "OK" if ready else "Bloque", "detail": "Surface chiffree locale controlee."},
            {"label": "Creer dans Google", "state": "OK" if ready else "Bloque", "detail": "Aucun contenu lisible envoye."},
            {"label": "Verifier droits", "state": "OK" if ready else "A lancer", "detail": "Aucun lien public autorise."},
        ],
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _ui_sync_result(result: Mapping[str, object]) -> dict[str, object]:
    status = str(result.get("status") or "blocked")
    blocked = status != "synced"
    rights_blocked = blocked and _phase_status(result, "droits_google") == "blocked"
    return {
        "action": "sync-now",
        "status": "blocked" if blocked else "synced",
        "summary": str(result.get("summary") or ("Synchronisation Drive bloquee" if blocked else "Synchronisation Drive terminee")),
        "result_label": "Droits Google a corriger" if rights_blocked else ("Synchronisation bloquee" if blocked else "Synchronisation terminee"),
        "share_label": _safe_text(result.get("blocker"), "Dossier Google configure; identifiants et chemins restent masques.") if blocked else "Dossier Google configure; identifiants et chemins restent masques.",
        "steps": [
            _phase_step("Verifier droits", result, "droits_google"),
            _phase_step("Lire Drive", result, "lecture_drive"),
            _phase_step("Appliquer ici", result, "application_locale"),
            _phase_step("Envoyer chiffre", result, "envoi_drive"),
        ],
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _ui_watch_result(result: Mapping[str, object]) -> dict[str, object]:
    status = str(result.get("status") or "blocked")
    conflict = result.get("conflict") if isinstance(result.get("conflict"), Mapping) else {}
    merge = result.get("merge") if isinstance(result.get("merge"), Mapping) else {}
    blocked = status == "blocked"
    return {
        "action": "watch-once",
        "status": status,
        "summary": _watch_summary(status, conflict, merge),
        "result_label": _watch_label(status, conflict, merge),
        "share_label": _watch_share_label(result, conflict),
        "steps": _watch_steps(result, blocked),
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _watch_summary(status: str, conflict: Mapping[str, object], merge: Mapping[str, object]) -> str:
    if status == "idle":
        return "Aucun changement detecte pendant ce passage."
    if status == "synced" and merge:
        return "Modifications simultanees fusionnees sans ecrasement."
    if status == "synced":
        return "Surveillance terminee: ce poste est a jour."
    if conflict:
        return "Modifications simultanees a verifier; rien n'a ete ecrase."
    return "Surveillance Drive bloquee avant de modifier ce poste."


def _watch_label(status: str, conflict: Mapping[str, object], merge: Mapping[str, object]) -> str:
    if status == "idle":
        return "Rien a appliquer"
    if status == "synced" and merge:
        return "Fusion terminee"
    if status == "synced":
        return "Surveillance terminee"
    if conflict:
        return "Conflit a verifier"
    return "Surveillance bloquee"


def _watch_share_label(result: Mapping[str, object], conflict: Mapping[str, object]) -> str:
    if conflict:
        return "Controle humain requis; aucune version n'a ete remplacee."
    blocker = _safe_text(result.get("summary"), "")
    if str(result.get("status") or "") == "blocked" and blocker:
        return blocker
    return "Affichage limite a ce poste."


def _watch_steps(result: Mapping[str, object], blocked: bool) -> list[dict[str, str]]:
    changes = result.get("changes") if isinstance(result.get("changes"), Mapping) else {}
    inbound = result.get("inbound") if isinstance(result.get("inbound"), Mapping) else {}
    outbound = result.get("outbound") if isinstance(result.get("outbound"), Mapping) else {}
    merge = result.get("merge") if isinstance(result.get("merge"), Mapping) else {}
    conflict = result.get("conflict") if isinstance(result.get("conflict"), Mapping) else {}
    return [
        {"label": "Verifier droits", "state": "Bloque" if blocked and not changes else "OK", "detail": "Controle termine sans afficher d'identifiant Google."},
        {"label": "Lire Drive", "state": "OK" if changes.get("remote") or inbound.get("checked") else "A lancer", "detail": "Paquets chiffres controles."},
        {"label": "Appliquer ici", "state": _watch_apply_state(inbound, merge, conflict), "detail": "Seulement sur ce poste."},
        {"label": "Envoyer chiffre", "state": "OK" if outbound.get("uploaded") else ("Bloque" if blocked else "A lancer"), "detail": "Aucun contenu lisible envoye."},
    ]


def _watch_apply_state(inbound: Mapping[str, object], merge: Mapping[str, object], conflict: Mapping[str, object]) -> str:
    if conflict:
        return "Bloque"
    if merge or inbound.get("applied"):
        return "OK"
    return "A lancer"


def _phase_step(label: str, result: Mapping[str, object], phase_name: str) -> dict[str, str]:
    status = _phase_status(result, phase_name) or "waiting"
    if status in {"ok", "downloaded", "recovered", "uploaded", "published", "idle"}:
        return {"label": label, "state": "OK", "detail": "Termine sans contenu lisible."}
    if status == "unknown" or status == "waiting":
        return {"label": label, "state": "A lancer", "detail": "Non lance."}
    return {"label": label, "state": "Bloque", "detail": "Controle a reprendre."}


def _phase_status(result: Mapping[str, object], phase_name: str) -> str:
    for phase in result.get("phases", []) if isinstance(result.get("phases"), list) else []:
        if isinstance(phase, Mapping) and phase.get("name") == phase_name:
            return str(phase.get("status") or "")
    return ""


def _safe_text(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").split())
    forbidden = ("token", "secret", "oauth", "drive.file", "c:\\", "\\", "@", "raw", "private")
    return fallback if not text or any(marker in text.lower() for marker in forbidden) else text[:160]
