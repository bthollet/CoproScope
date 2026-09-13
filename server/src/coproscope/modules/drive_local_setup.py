from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Mapping


PROFILE_VERSION = 1
PROFILE_ENV = "COPROSCOPE_DRIVE_PROFILE_ROOT"
LOCAL_ROOT_ENV = "COPROSCOPE_DRIVE_LOCAL_ROOT"

_CLOUD_MARKERS = ("google drive", "mon drive", "my drive", "onedrive", "dropbox", "icloud drive")
_FORBIDDEN_PARTS = {".git", ".venv", "raw", "restricted", "private", "logs", "secrets"}
_INSTANCE_RE = re.compile(r"[^a-zA-Z0-9_.-]+")


def prepare_drive_local_workspace(
    instance: Any,
    *,
    base_root: str | Path | None = None,
    profile_root: str | Path | None = None,
) -> dict[str, object]:
    instance_id = _safe_instance_id(instance)
    profile_base = _profile_root(profile_root)
    local_base = _local_base(instance_id, base_root=base_root)
    _reject_unsafe_data_path(local_base)
    _reject_unsafe_data_path(profile_base)

    sync_root = local_base / "sync_chiffre"
    local_state_root = local_base / "local" / "drive_state"
    oauth_root = profile_base / "oauth" / instance_id
    client_secrets_path = oauth_root / "client_secret.json"
    token_path = oauth_root / "token_drive_file.json"

    for path in (sync_root / "packages", sync_root / "devices", local_state_root, oauth_root):
        path.mkdir(parents=True, exist_ok=True)

    profile = _read_profile(profile_base)
    instances = profile.setdefault("instances", {})
    if not isinstance(instances, dict):
        instances = {}
        profile["instances"] = instances
    instances[instance_id] = {
        "provider": "google_drive",
        "sync_root": str(sync_root),
        "local_state_root": str(local_state_root),
        "client_secrets_path": str(client_secrets_path),
        "token_path": str(token_path),
    }
    _write_profile(profile_base, profile)

    return {
        "action": "prepare-local",
        "status": "prepared",
        "summary": "Ce poste est pret cote local. Google reste a connecter avant toute synchronisation reelle.",
        "result_label": "Poste prepare",
        "share_label": "Aucun document lisible ni identifiant Google n'a ete envoye dans Drive.",
        "steps": [
            {"label": "Dossier local", "state": "OK", "detail": "La copie de travail reste sur ce poste."},
            {"label": "Surface chiffree", "state": "OK", "detail": "Les paquets destines a Drive seront chiffres."},
            {"label": "Profil local", "state": "OK", "detail": "CoproScope memorise seulement des emplacements techniques."},
        ],
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def drive_profile_settings(instance: Any, *, profile_root: str | Path | None = None) -> Mapping[str, object]:
    profile_base = _profile_root(profile_root)
    try:
        _reject_unsafe_data_path(profile_base)
    except ValueError:
        return {}
    profile = _read_profile(profile_base, missing_ok=True)
    instances = profile.get("instances") if isinstance(profile, Mapping) else {}
    row = instances.get(_safe_instance_id(instance)) if isinstance(instances, Mapping) else {}
    if not isinstance(row, Mapping):
        return {}
    sync_root = _text(row.get("sync_root"))
    local_state_root = _text(row.get("local_state_root"))
    if not sync_root or not local_state_root:
        return {}
    try:
        _reject_unsafe_data_path(Path(sync_root))
        _reject_unsafe_data_path(Path(local_state_root))
    except ValueError:
        return {}
    return {
        "folder_id": _text(row.get("folder_id")),
        "sync_root": sync_root,
        "local_state_root": local_state_root,
        "client_secrets_path": _text(row.get("client_secrets_path")),
        "token_path": _text(row.get("token_path")),
    }


def save_drive_folder_id(instance: Any, folder_id: str, *, profile_root: str | Path | None = None) -> None:
    folder = _text(folder_id)
    if not folder:
        raise ValueError("Dossier Google manquant.")
    profile_base = _profile_root(profile_root)
    _reject_unsafe_data_path(profile_base)
    profile = _read_profile(profile_base, missing_ok=True)
    instances = profile.setdefault("instances", {})
    if not isinstance(instances, dict):
        instances = {}
        profile["instances"] = instances
    instance_id = _safe_instance_id(instance)
    current = instances.get(instance_id)
    row = dict(current) if isinstance(current, Mapping) else {"provider": "google_drive"}
    row["folder_id"] = folder
    instances[instance_id] = row
    _write_profile(profile_base, profile)


def inspect_local_setup(sync_root: Path, local_state_root: Path) -> dict[str, object]:
    sync_ready = (sync_root / "packages").is_dir() and (sync_root / "devices").is_dir()
    state_ready = local_state_root.is_dir()
    ready = sync_ready and state_ready
    return {
        "status": "ready" if ready else "missing",
        "enabled": not ready,
        "href": "/coffre/drive/preparer-poste",
        "label": "Preparer ce poste" if not ready else "Poste prepare",
        "help": (
            "Ce poste dispose deja de sa zone locale chiffree."
            if ready
            else "Cree les dossiers locaux necessaires, sans rien envoyer dans Drive."
        ),
        "path_disclosure": "none",
    }


def _local_base(instance_id: str, *, base_root: str | Path | None) -> Path:
    root_value = base_root or os.environ.get(LOCAL_ROOT_ENV)
    if root_value:
        root = Path(root_value)
    else:
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "CoproScope" / "coffres"
    return (root / instance_id).expanduser().resolve()


def _profile_root(profile_root: str | Path | None) -> Path:
    root_value = profile_root or os.environ.get(PROFILE_ENV)
    if root_value:
        root = Path(root_value)
    else:
        root = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "CoproScope"
    return root.expanduser().resolve()


def _read_profile(profile_root: Path, *, missing_ok: bool = False) -> dict[str, object]:
    path = _profile_path(profile_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"version": PROFILE_VERSION, "instances": {}} if missing_ok else {"version": PROFILE_VERSION, "instances": {}}
    except (OSError, json.JSONDecodeError):
        return {"version": PROFILE_VERSION, "instances": {}}
    if not isinstance(payload, dict):
        return {"version": PROFILE_VERSION, "instances": {}}
    payload["version"] = PROFILE_VERSION
    payload.setdefault("instances", {})
    return payload


def _write_profile(profile_root: Path, payload: Mapping[str, object]) -> None:
    path = _profile_path(profile_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _profile_path(profile_root: Path) -> Path:
    return profile_root / "config" / "drive_profile.json"


def _safe_instance_id(instance: Any) -> str:
    raw = str(getattr(instance, "instance_id", "local") or "local").strip()[:80]
    cleaned = _INSTANCE_RE.sub("-", raw).strip("-.")
    return cleaned or "local"


def _reject_unsafe_data_path(path: Path) -> None:
    resolved = path.expanduser().resolve()
    lowered = str(resolved).lower()
    if any(marker in lowered for marker in _CLOUD_MARKERS):
        raise ValueError("Le dossier local CoproScope ne doit pas etre place dans un dossier cloud.")
    if any(part.lower() in _FORBIDDEN_PARTS for part in resolved.parts):
        raise ValueError("Le dossier local CoproScope pointe vers une zone refusee.")
    if _inside_git_worktree(resolved):
        raise ValueError("Le dossier local CoproScope ne doit pas etre place dans le depot de code.")


def _inside_git_worktree(path: Path) -> bool:
    current = path if path.exists() and path.is_dir() else path.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return True
    return False


def _text(value: object) -> str:
    return " ".join(str(value or "").split())[:500]
