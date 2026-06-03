from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Mapping

from . import drive_instance_sync


KEY_CODE_PROTOCOL = "coproscope-drive-key-code-v1"
KEY_CODE_PREFIX = "CSP-DRIVE-KEY-V1"
KEY_BYTES = 32


def create_sync_key_code(*, local_state_root: str | Path) -> dict[str, object]:
    state = Path(local_state_root).expanduser().resolve()
    key = drive_instance_sync._sync_key(state)
    code = _encode_key_code(key)
    return {
        "status": "exported",
        "action": "key-export",
        "secret_code": code,
        "secret_disclosure": "shown_once",
        "key_fingerprint": _fingerprint(key),
        "local_state": {"storage": "local-only"},
        "drive_storage": "forbidden",
        "path_disclosure": "none",
    }


def write_sync_key_code_file(*, local_state_root: str | Path, output_file: str | Path) -> dict[str, object]:
    result = create_sync_key_code(local_state_root=local_state_root)
    output = Path(output_file).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(str(result["secret_code"]), encoding="ascii")
    return _without_secret(
        result,
        {
            "output_written": True,
            "output_file_disclosure": "redacted",
            "next_action": "Transmettre ce code par un canal separe, puis supprimer le fichier temporaire.",
        },
    )


def import_sync_key_code(*, local_state_root: str | Path, secret_code: str) -> dict[str, object]:
    state = Path(local_state_root).expanduser().resolve()
    try:
        key = _decode_key_code(secret_code)
    except ValueError:
        return _blocked("Code d'acces refuse", "Le code du coffre n'est pas valide.")
    key_path = state / drive_instance_sync.SYNC_KEY_FILE
    if key_path.exists() and key_path.read_bytes() != key:
        return _blocked("Code d'acces refuse", "Ce poste a deja une autre cle de coffre.")
    state.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(key)
    return {
        "status": "imported",
        "action": "key-import",
        "result_label": "Code d'acces importe",
        "summary": "Ce poste peut maintenant lire les paquets chiffres du coffre.",
        "key_fingerprint": _fingerprint(key),
        "local_state": {"storage": "local-only", "key_ready": True},
        "drive_storage": "forbidden",
        "secret_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def import_sync_key_code_file(*, local_state_root: str | Path, code_file: str | Path) -> dict[str, object]:
    try:
        code = Path(code_file).expanduser().read_text(encoding="ascii")
    except OSError:
        return _blocked("Code d'acces introuvable", "Le fichier de code n'est pas lisible.")
    return import_sync_key_code(local_state_root=local_state_root, secret_code=code)


def _encode_key_code(key: bytes) -> str:
    if len(key) != KEY_BYTES:
        raise ValueError("wrong key length")
    payload = {"protocol": KEY_CODE_PROTOCOL, "key": base64.b64encode(key).decode("ascii")}
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    token = base64.urlsafe_b64encode(body).decode("ascii").rstrip("=")
    return f"{KEY_CODE_PREFIX}.{token}.{_checksum(token)}"


def _decode_key_code(secret_code: str) -> bytes:
    parts = " ".join(str(secret_code or "").split()).split(".")
    if len(parts) != 3 or parts[0] != KEY_CODE_PREFIX or parts[2] != _checksum(parts[1]):
        raise ValueError("invalid key code")
    body = base64.urlsafe_b64decode(_with_padding(parts[1]))
    payload = json.loads(body.decode("ascii"))
    if not isinstance(payload, Mapping) or payload.get("protocol") != KEY_CODE_PROTOCOL:
        raise ValueError("wrong key protocol")
    key = base64.b64decode(str(payload.get("key") or ""), validate=True)
    if len(key) != KEY_BYTES:
        raise ValueError("wrong key length")
    return key


def _checksum(token: str) -> str:
    return hashlib.sha256(f"{KEY_CODE_PROTOCOL}:{token}".encode("ascii")).hexdigest()[:16]


def _fingerprint(key: bytes) -> str:
    return hashlib.sha256(key).hexdigest()[:16]


def _with_padding(value: str) -> str:
    return value + "=" * (-len(value) % 4)


def _without_secret(result: Mapping[str, object], extra: Mapping[str, object]) -> dict[str, object]:
    clean = {key: value for key, value in result.items() if key != "secret_code"}
    clean["secret_disclosure"] = "written_not_returned"
    clean.update(extra)
    return clean


def _blocked(title: str, detail: str) -> dict[str, object]:
    return {
        "status": "blocked",
        "action": "key-import",
        "result_label": title,
        "summary": detail,
        "local_state": {"storage": "local-only", "key_ready": False},
        "drive_storage": "forbidden",
        "secret_disclosure": "not_returned",
        "path_disclosure": "none",
    }
