from __future__ import annotations

import base64
import hashlib
import json
import secrets
from pathlib import Path
from typing import Any, Mapping

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import drive_folder_status


PROTOCOL = "coproscope-drive-instance-shared-key-v1"
PACKAGE_DIR = "packages"
DEVICE_DIR = "devices"
PACKAGE_SUFFIX = ".cspkg"
SYNC_KEY_FILE = "instance_sync_key.bin"
DEVICE_ID_FILE = "device_id.txt"
SHARED_STATE_FILE = "shared_state.json"
_MASKED = "[masque]"
_PRIVATE_KEY_PARTS = (
    "absolute_path",
    "client_secret",
    "credential",
    "drive_token",
    "local_path",
    "oauth",
    "password",
    "private_key",
    "secret",
    "sync_key",
    "token",
)
_PRIVATE_KEY_NAMES = {"path", "root", "roots", "secret_path", "token_path"}


def publish_instance_update(
    *,
    instance: Any,
    sync_root: str | Path,
    local_state_root: str | Path,
    shared_state: Mapping[str, object] | None = None,
    minimum_generation: int = 0,
) -> dict[str, object]:
    sync = Path(sync_root).expanduser().resolve()
    state = Path(local_state_root).expanduser().resolve()
    blocked = _preflight(sync, state)
    if blocked:
        return blocked
    sync_key = _sync_key(state)
    device_id = _device_public_id(state)
    _write_json(sync / DEVICE_DIR / f"{device_id}.json", {"device": "ce-poste", "public_id": device_id})

    generation = _next_publish_generation(state, minimum=minimum_generation)
    canary = f"COPROSCOPE-DRIVE-DEMO-CANARY-{secrets.token_hex(8)}"
    safe_shared_state = _safe_mapping(shared_state) if shared_state is not None else _shared_state_snapshot(instance)
    shared_state_hash = _stable_hash(safe_shared_state)
    payload = _payload(instance, generation, canary, shared_state=safe_shared_state)
    package = _encrypt_payload(payload, sync_key, generation, device_id)
    package_hash = _package_hash(package)
    package["package_hash"] = package_hash
    _write_json(sync / PACKAGE_DIR / f"{package_hash}{PACKAGE_SUFFIX}", package)
    _write_json(state / "publish_state.json", {"generation": generation, "package_hash": package_hash})

    scan = _scan_surface(sync, canary)
    if scan["cleartext_found"] or scan["private_key_marker_found"] or scan["unexpected_file_count"]:
        return _blocked("Dossier Drive bloque", "Le dossier contient un fichier non prevu.", scan)
    return {
        "action": "publish",
        "status": "published",
        "summary": "Changements chiffres deposes en demonstration locale",
        "result_label": "Publication test terminee",
        "share_label": "Partage Google non verifie par ce test",
        "steps": [
            _step("Ce poste : version test preparee", "ok", "Les donnees sont chiffrees avant depot."),
            _step("Dossier Drive : fichiers chiffres presents", "ok", "Aucun document lisible detecte."),
            _step("Recuperation : a lancer", "waiting", "Cliquez ensuite sur Recuperer en demonstration locale."),
        ],
        "sync_surface": _surface(sync, scan),
        "local_state": {
            "storage": "local-only",
            "applied": False,
            "generation": generation,
            "package_hash": package_hash,
            "shared_state_hash": shared_state_hash,
        },
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def recover_instance_update(*, instance: Any, sync_root: str | Path, local_state_root: str | Path) -> dict[str, object]:
    sync = Path(sync_root).expanduser().resolve()
    state = Path(local_state_root).expanduser().resolve()
    blocked = _preflight(sync, state)
    if blocked:
        return blocked
    sync_key = _sync_key(state)
    package = _latest_package(sync)
    if package is None:
        return _idle(sync, "Aucune nouvelle version test")
    package_hash = str(package.get("package_hash") or "")
    applied = _read_json(state / "recover_state.json")
    if isinstance(applied, Mapping) and applied.get("package_hash") == package_hash:
        return _idle(sync, "Aucune nouvelle version test")
    try:
        payload = _decrypt_payload(package, sync_key)
    except Exception:
        return _blocked("Recuperation bloquee", "CoproScope refuse cette version test avant import.", _empty_scan())
    parsed = json.loads(payload.decode("utf-8"))
    if str(parsed.get("instance_id") or "") != _instance_id(instance):
        return _blocked("Recuperation bloquee", "Cette version test ne correspond pas au coffre courant.", _empty_scan())
    cache = state / "cache_instance"
    cache.mkdir(parents=True, exist_ok=True)
    _write_json(cache / "last_recovered.json", {"instance_id": _instance_id(instance), "generation": parsed["generation"]})
    shared_state = _safe_mapping(parsed.get("shared_state"))
    shared_state_hash = _stable_hash(shared_state)
    _write_json(
        cache / SHARED_STATE_FILE,
        {
            "instance_id": _instance_id(instance),
            "generation": parsed["generation"],
            "package_hash": package_hash,
            "shared_state_hash": shared_state_hash,
            "shared_state": shared_state,
        },
    )
    _write_json(state / "recover_state.json", {"package_hash": package_hash, "generation": parsed["generation"]})
    return {
        "action": "recover",
        "status": "recovered",
        "summary": "Changements verifies et recuperes sur ce poste",
        "result_label": "Recuperation test terminee",
        "share_label": "Partage Google non verifie par ce test",
        "steps": [
            _step("Ce poste : fichier chiffre lu", "ok", "La version disponible est controlee."),
            _step("Verification : conforme", "ok", "La version est bien destinee a ce coffre."),
            _step("Version locale : mise a jour test", "ok", "La copie lisible reste sur ce poste."),
        ],
        "sync_surface": _surface(sync, _empty_scan()),
        "local_state": {"storage": "local-only", "applied": True, "shared_state_hash": shared_state_hash},
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def preview_instance_update(*, instance: Any, sync_root: str | Path, local_state_root: str | Path) -> dict[str, object]:
    sync = Path(sync_root).expanduser().resolve()
    state = Path(local_state_root).expanduser().resolve()
    blocked = _preflight(sync, state)
    if blocked:
        return {"status": "blocked", "summary": "Controle Drive bloque", "payload_disclosure": "not_returned", "path_disclosure": "none"}
    package = _latest_package(sync)
    if package is None:
        return {"status": "idle", "summary": "Aucune version Drive", "payload_disclosure": "not_returned", "path_disclosure": "none"}
    try:
        parsed = json.loads(_decrypt_payload(package, _sync_key(state)).decode("utf-8"))
    except Exception:
        return {"status": "blocked", "summary": "Version Drive refusee avant fusion", "payload_disclosure": "not_returned", "path_disclosure": "none"}
    if str(parsed.get("instance_id") or "") != _instance_id(instance):
        return {"status": "blocked", "summary": "Version Drive hors coffre courant", "payload_disclosure": "not_returned", "path_disclosure": "none"}
    shared_state = _safe_mapping(parsed.get("shared_state"))
    return {
        "status": "ready",
        "generation": int(parsed.get("generation") or 0),
        "package_hash": str(package.get("package_hash") or ""),
        "shared_state_hash": _stable_hash(shared_state),
        "shared_state": shared_state,
        "payload_disclosure": "internal_only",
        "path_disclosure": "none",
    }


def shared_state_snapshot(instance: Any) -> dict[str, object]:
    return _shared_state_snapshot(instance)


def cached_shared_state(*, local_state_root: str | Path) -> dict[str, object]:
    state = Path(local_state_root).expanduser().resolve()
    cache_path = state / "cache_instance" / SHARED_STATE_FILE
    if not cache_path.exists():
        return {"status": "missing", "shared_state": {}, "payload_disclosure": "not_returned", "path_disclosure": "none"}
    payload = _read_json(cache_path)
    if not isinstance(payload, Mapping):
        return {"status": "missing", "shared_state": {}, "payload_disclosure": "not_returned", "path_disclosure": "none"}
    shared_state = _safe_mapping(payload.get("shared_state"))
    return {
        "status": "ready",
        "generation": int(payload.get("generation") or 0),
        "package_hash": str(payload.get("package_hash") or ""),
        "shared_state_hash": _stable_hash(shared_state),
        "shared_state": shared_state,
        "payload_disclosure": "internal_only",
        "path_disclosure": "none",
    }


def record_cached_shared_state(
    *,
    instance: Any,
    local_state_root: str | Path,
    generation: int,
    package_hash: str,
    shared_state: Mapping[str, object],
) -> None:
    state = Path(local_state_root).expanduser().resolve()
    cache = state / "cache_instance"
    cache.mkdir(parents=True, exist_ok=True)
    safe_shared_state = _safe_mapping(shared_state)
    _write_json(cache / "last_recovered.json", {"instance_id": _instance_id(instance), "generation": generation})
    _write_json(
        cache / SHARED_STATE_FILE,
        {
            "instance_id": _instance_id(instance),
            "generation": generation,
            "package_hash": package_hash,
            "shared_state_hash": _stable_hash(safe_shared_state),
            "shared_state": safe_shared_state,
        },
    )
    _write_json(state / "recover_state.json", {"package_hash": package_hash, "generation": generation})


def _preflight(sync: Path, state: Path) -> dict[str, object] | None:
    if state == sync or _is_relative_to(state, sync):
        return _blocked("Etat local mal place", "L'etat local doit rester hors du dossier Drive.", _empty_scan())
    sync.mkdir(parents=True, exist_ok=True)
    folder = drive_folder_status.inspect_drive_sync_folder(sync)
    if folder.get("status") != "ready":
        return _blocked("Dossier Drive a choisir", "Le dossier de demonstration n'est pas pret.", _empty_scan())
    scan = _scan_surface(sync, "")
    if scan["unexpected_file_count"]:
        return _blocked("Dossier Drive bloque", "Le dossier contient un fichier non prevu.", scan)
    return None


def _payload(instance: Any, generation: int, canary: str, *, shared_state: Mapping[str, object] | None = None) -> bytes:
    snapshot = _safe_mapping(shared_state) if shared_state is not None else _shared_state_snapshot(instance)
    return json.dumps(
        {
            "protocol": PROTOCOL,
            "instance_id": _instance_id(instance),
            "generation": generation,
            "canary": canary,
            "shared_state": snapshot,
            "shared_state_hash": _stable_hash(snapshot),
        },
        sort_keys=True,
        ensure_ascii=True,
    ).encode("utf-8")


def _encrypt_payload(payload: bytes, sync_key: bytes, generation: int, device_id: str) -> dict[str, object]:
    nonce = secrets.token_bytes(12)
    encrypted = AESGCM(sync_key).encrypt(nonce, payload, _package_context(device_id))
    return {
        "protocol": PROTOCOL,
        "generation": generation,
        "author_device": device_id,
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(encrypted).decode("ascii"),
    }


def _decrypt_payload(package: Mapping[str, object], sync_key: bytes) -> bytes:
    if package.get("protocol") != PROTOCOL:
        raise ValueError("wrong protocol")
    device_id = str(package.get("author_device") or "")
    if not device_id:
        raise ValueError("missing author")
    nonce = base64.b64decode(str(package.get("nonce") or ""))
    encrypted = base64.b64decode(str(package.get("ciphertext") or ""))
    return AESGCM(sync_key).decrypt(nonce, encrypted, _package_context(device_id))


def _sync_key(state: Path) -> bytes:
    key_path = state / SYNC_KEY_FILE
    if key_path.exists():
        return key_path.read_bytes()
    state.mkdir(parents=True, exist_ok=True)
    key = AESGCM.generate_key(bit_length=256)
    key_path.write_bytes(key)
    return key


def _device_public_id(state: Path) -> str:
    id_path = state / DEVICE_ID_FILE
    if id_path.exists():
        value = id_path.read_text(encoding="ascii").strip()
        if value:
            return value[:32]
    state.mkdir(parents=True, exist_ok=True)
    value = secrets.token_hex(16)
    id_path.write_text(value, encoding="ascii")
    return value


def _package_context(device_id: str) -> bytes:
    return f"{PROTOCOL}:{device_id}".encode("ascii")


def _next_publish_generation(state: Path, *, minimum: int = 0) -> int:
    generations: list[int] = []
    for name in ("publish_state.json", "recover_state.json"):
        current = _read_json(state / name)
        if isinstance(current, Mapping):
            generations.append(int(current.get("generation") or 0))
    return max([*generations, int(minimum or 0)], default=0) + 1


def _shared_state_snapshot(instance: Any) -> dict[str, object]:
    raw = _explicit_shared_state(instance)
    return _safe_mapping(raw)


def _explicit_shared_state(instance: Any) -> object:
    provider = getattr(instance, "drive_shared_state", None)
    if callable(provider):
        try:
            return provider()
        except Exception:
            return {}
    if isinstance(provider, Mapping):
        return provider
    payload = getattr(instance, "payload", None)
    if isinstance(payload, Mapping):
        direct = payload.get("drive_shared_state") or payload.get("shared_state") or payload.get("sync_state")
        if isinstance(direct, Mapping):
            return direct
        settings = payload.get("parametres") or payload.get("settings")
        if isinstance(settings, Mapping):
            configured = settings.get("drive_shared_state") or settings.get("shared_state")
            if isinstance(configured, Mapping):
                return configured
    return {}


def _safe_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    safe = _safe_value(value, key_name="", depth=0)
    return safe if isinstance(safe, dict) else {}


def _safe_value(value: object, *, key_name: str, depth: int) -> object:
    if _private_key_name(key_name):
        return _MASKED
    if depth > 6:
        return _MASKED
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, str):
        return " ".join(value.split())[:2000]
    if isinstance(value, Mapping):
        return {
            str(key)[:120]: _safe_value(child, key_name=str(key), depth=depth + 1)
            for key, child in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, list | tuple):
        return [_safe_value(child, key_name=key_name, depth=depth + 1) for child in value[:100]]
    return str(value)[:500]


def _private_key_name(key_name: str) -> bool:
    lowered = key_name.strip().lower()
    return lowered in _PRIVATE_KEY_NAMES or any(part in lowered for part in _PRIVATE_KEY_PARTS)


def _latest_package(sync: Path) -> dict[str, object] | None:
    packages = []
    for path in (sync / PACKAGE_DIR).glob(f"**/*{PACKAGE_SUFFIX}"):
        payload = _read_json(path)
        if isinstance(payload, dict):
            packages.append(payload)
    return max(packages, key=lambda item: int(item.get("generation") or 0), default=None)


def _scan_surface(sync: Path, canary: str) -> dict[str, object]:
    files = [path for path in sync.rglob("*") if path.is_file()]
    marker = canary.encode("utf-8") if canary else b""
    return {
        "cleartext_checked": True,
        "cleartext_found": bool(marker) and any(_contains(path, marker) for path in files),
        "private_key_marker_found": any(
            _contains(path, b"PRIVATE KEY")
            or _contains(path, b"device_key")
            or _contains(path, SYNC_KEY_FILE.encode("ascii"))
            for path in files
        ),
        "unexpected_file_count": len([path for path in files if not _allowed(sync, path)]),
    }


def _surface(sync: Path, scan: Mapping[str, object]) -> dict[str, object]:
    return {
        **dict(scan),
        "encrypted_file_count": len(list((sync / PACKAGE_DIR).glob(f"*{PACKAGE_SUFFIX}"))),
        "public_key_count": len(list((sync / DEVICE_DIR).glob("*.json"))),
        "content_policy": "fichiers_chiffres_et_cles_publiques",
    }


def _blocked(title: str, detail: str, scan: Mapping[str, object]) -> dict[str, object]:
    return {
        "status": "blocked",
        "summary": "Action bloquee",
        "result_label": title,
        "blocker_detail": detail,
        "share_label": "Partage Google non verifie par ce test",
        "steps": [
            _step("Controle du dossier", "blocked", detail),
            _step("Publication", "waiting", "Non lancee."),
            _step("Recuperation", "waiting", "Non lancee."),
        ],
        "sync_surface": {
            **dict(scan),
            "encrypted_file_count": 0,
            "public_key_count": 0,
            "content_policy": "controle_bloque",
        },
        "local_state": {"storage": "local-only", "applied": False},
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _idle(sync: Path, summary: str) -> dict[str, object]:
    return {
        "action": "recover",
        "status": "idle",
        "summary": summary,
        "result_label": "Aucune nouveaute a recuperer",
        "share_label": "Partage Google non verifie par ce test",
        "steps": [
            _step("Dossier Drive : controle", "ok", "Pas de nouvelle version pour ce poste."),
            _step("Version locale : conservee", "ok", "Rien n'a ete remplace."),
            _step("Conflit : non detecte", "ok", "Aucune action requise."),
        ],
        "sync_surface": _surface(sync, _empty_scan()),
        "local_state": {"storage": "local-only", "applied": False},
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _step(label: str, state: str, detail: str) -> dict[str, str]:
    return {"label": label, "state": state, "detail": detail}


def _empty_scan() -> dict[str, object]:
    return {"cleartext_checked": True, "cleartext_found": False, "private_key_marker_found": False, "unexpected_file_count": 0}


def _package_hash(package: Mapping[str, object]) -> str:
    body = json.dumps(package, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _stable_hash(payload: Mapping[str, object]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, ensure_ascii=True), encoding="utf-8")


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _contains(path: Path, marker: bytes) -> bool:
    try:
        return marker in path.read_bytes()
    except OSError:
        return True


def _allowed(sync: Path, path: Path) -> bool:
    relative = path.relative_to(sync)
    return (
        (len(relative.parts) == 2 and relative.parts[0] == DEVICE_DIR and path.suffix == ".json")
        or (len(relative.parts) == 2 and relative.parts[0] == PACKAGE_DIR and path.suffix == PACKAGE_SUFFIX)
        or (len(relative.parts) == 3 and relative.parts[0] == PACKAGE_DIR and path.suffix == PACKAGE_SUFFIX)
    )


def _instance_id(instance: Any) -> str:
    text = " ".join(str(getattr(instance, "instance_id", "coproscope-instance")).split())
    return text[:80] if text else "coproscope-instance"


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
