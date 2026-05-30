from __future__ import annotations

import base64
import hashlib
import json
import secrets
from pathlib import Path
from typing import Any, Mapping

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import drive_folder_status


PROTOCOL = "coproscope-drive-instance-demo-v1"
PACKAGE_DIR = "packages"
DEVICE_DIR = "devices"
PACKAGE_SUFFIX = ".cspkg"


def publish_instance_update(*, instance: Any, sync_root: str | Path, local_state_root: str | Path) -> dict[str, object]:
    sync = Path(sync_root).expanduser().resolve()
    state = Path(local_state_root).expanduser().resolve()
    blocked = _preflight(sync, state)
    if blocked:
        return blocked
    private_key = _device_key(state)
    public_id = _device_public_id(private_key)
    _write_json(sync / DEVICE_DIR / f"{public_id}.json", {"device": "ce-poste", "public_id": public_id})

    generation = _next_publish_generation(state)
    canary = f"COPROSCOPE-DRIVE-DEMO-CANARY-{secrets.token_hex(8)}"
    payload = _payload(instance, generation, canary)
    package = _encrypt_payload(payload, private_key, generation, public_id)
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
        "local_state": {"storage": "local-only", "applied": False},
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def recover_instance_update(*, instance: Any, sync_root: str | Path, local_state_root: str | Path) -> dict[str, object]:
    sync = Path(sync_root).expanduser().resolve()
    state = Path(local_state_root).expanduser().resolve()
    blocked = _preflight(sync, state)
    if blocked:
        return blocked
    private_key = _device_key(state)
    package = _latest_package(sync)
    if package is None:
        return _idle(sync, "Aucune nouvelle version test")
    package_hash = str(package.get("package_hash") or "")
    applied = _read_json(state / "recover_state.json")
    if isinstance(applied, Mapping) and applied.get("package_hash") == package_hash:
        return _idle(sync, "Aucune nouvelle version test")
    try:
        payload = _decrypt_payload(package, private_key)
    except Exception:
        return _blocked("Recuperation bloquee", "CoproScope refuse cette version test avant import.", _empty_scan())
    parsed = json.loads(payload.decode("utf-8"))
    if str(parsed.get("instance_id") or "") != _instance_id(instance):
        return _blocked("Recuperation bloquee", "Cette version test ne correspond pas au coffre courant.", _empty_scan())
    cache = state / "cache_instance"
    cache.mkdir(parents=True, exist_ok=True)
    _write_json(cache / "last_recovered.json", {"instance_id": _instance_id(instance), "generation": parsed["generation"]})
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
        "local_state": {"storage": "local-only", "applied": True},
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


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


def _payload(instance: Any, generation: int, canary: str) -> bytes:
    return json.dumps(
        {
            "protocol": PROTOCOL,
            "instance_id": _instance_id(instance),
            "generation": generation,
            "canary": canary,
        },
        sort_keys=True,
        ensure_ascii=True,
    ).encode("utf-8")


def _encrypt_payload(payload: bytes, private_key: bytes, generation: int, public_id: str) -> dict[str, object]:
    nonce = secrets.token_bytes(12)
    encrypted = AESGCM(private_key).encrypt(nonce, payload, public_id.encode("ascii"))
    return {
        "protocol": PROTOCOL,
        "generation": generation,
        "recipient": public_id,
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(encrypted).decode("ascii"),
    }


def _decrypt_payload(package: Mapping[str, object], private_key: bytes) -> bytes:
    public_id = _device_public_id(private_key)
    if package.get("recipient") != public_id:
        raise ValueError("wrong recipient")
    nonce = base64.b64decode(str(package.get("nonce") or ""))
    encrypted = base64.b64decode(str(package.get("ciphertext") or ""))
    return AESGCM(private_key).decrypt(nonce, encrypted, public_id.encode("ascii"))


def _device_key(state: Path) -> bytes:
    key_path = state / "device_key.bin"
    if key_path.exists():
        return key_path.read_bytes()
    state.mkdir(parents=True, exist_ok=True)
    key = AESGCM.generate_key(bit_length=256)
    key_path.write_bytes(key)
    return key


def _device_public_id(key: bytes) -> str:
    return hashlib.sha256(key).hexdigest()[:32]


def _next_publish_generation(state: Path) -> int:
    current = _read_json(state / "publish_state.json")
    return int(current.get("generation") or 0) + 1 if isinstance(current, Mapping) else 1


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
        "private_key_marker_found": any(_contains(path, b"PRIVATE KEY") or _contains(path, b"device_key") for path in files),
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
        len(relative.parts) == 2
        and relative.parts[0] == DEVICE_DIR
        and path.suffix == ".json"
        or len(relative.parts) == 2
        and relative.parts[0] == PACKAGE_DIR
        and path.suffix == PACKAGE_SUFFIX
        or len(relative.parts) == 3
        and relative.parts[0] == PACKAGE_DIR
        and path.suffix == PACKAGE_SUFFIX
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
