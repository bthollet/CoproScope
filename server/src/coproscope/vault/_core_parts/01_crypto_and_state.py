from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VAULT_SCHEMA_VERSION = "1.0"
EVENT_SCHEMA_VERSION = "1.0"
SNAPSHOT_SCHEMA_VERSION = "1.0"
CRYPTO_PROFILE = "coproscope-vault-v1-aes256gcm-ed25519"
LOCAL_STATE_FILE = "vault_local.json"
FORBIDDEN_SYNC_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
FORBIDDEN_SYNC_PREFIXES = {
    "coproscope-agent-",
}
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_SYNC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _write_json(path: Path, value: Any, *, canonical: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if canonical:
        path.write_bytes(_canonical_bytes(value))
    else:
        path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_crypto() -> dict[str, Any]:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as exc:  # pragma: no cover - exercised only without dependency
        raise RuntimeError(
            "The vault subsystem requires the 'cryptography' package. "
            "Install CoproScope with the declared project dependencies."
        ) from exc
    return {
        "AESGCM": AESGCM,
        "InvalidSignature": InvalidSignature,
        "ed25519": ed25519,
        "serialization": serialization,
    }


@dataclass(frozen=True)
class VaultRoots:
    local_root: Path
    sync_root: Path


def roots_from_args(args: Any) -> VaultRoots:
    local_root = Path(args.local_root).expanduser().resolve()
    sync_root = Path(args.sync_root).expanduser().resolve()
    return VaultRoots(local_root=local_root, sync_root=sync_root)


def _ensure_sync_tree(sync_root: Path) -> None:
    for name in ["blobs", "events", "snapshots", "keys", "indexes"]:
        (sync_root / name).mkdir(parents=True, exist_ok=True)


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


def _assert_sync_root_clean(sync_root: Path) -> None:
    forbidden = _forbidden_sync_entries(sync_root)
    if forbidden:
        joined = "\n".join(f"- {item}" for item in forbidden[:20])
        raise RuntimeError(f"Forbidden development/runtime entries found in vault sync root:\n{joined}")


def _state_path(local_root: Path) -> Path:
    return local_root / LOCAL_STATE_FILE


def _load_state(local_root: Path) -> dict[str, Any]:
    path = _state_path(local_root)
    if not path.exists():
        raise RuntimeError(f"Vault local state not found: {path}")
    state = _read_json(path)
    if not isinstance(state, dict):
        raise RuntimeError(f"Invalid vault local state: {path}")
    return state


def _save_state(local_root: Path, state: dict[str, Any]) -> None:
    local_root.mkdir(parents=True, exist_ok=True)
    _write_json(_state_path(local_root), state)


def _generate_state(local_root: Path, sync_root: Path, vault_id: str) -> dict[str, Any]:
    crypto = _require_crypto()
    private_key = crypto["ed25519"].Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    serialization = crypto["serialization"]
    private_raw = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    author_key_id = "ak_" + _sha256_bytes(public_raw)[:16]
    return {
        "schema_version": VAULT_SCHEMA_VERSION,
        "vault_id": vault_id,
        "created_at": _now_iso(),
        "local_root": str(local_root),
        "sync_root": str(sync_root),
        "device_id": "dev_" + secrets.token_hex(8),
        "author_key_id": author_key_id,
        "vault_key": _b64(crypto["AESGCM"].generate_key(bit_length=256)),
        "signing_private_key": _b64(private_raw),
        "signing_public_key": _b64(public_raw),
        "crypto_profile": CRYPTO_PROFILE,
    }


def _vault_json(vault_id: str) -> dict[str, Any]:
    return {
        "schema_version": VAULT_SCHEMA_VERSION,
        "vault_id": vault_id,
        "created_at": _now_iso(),
        "crypto_profile": CRYPTO_PROFILE,
        "event_format_version": EVENT_SCHEMA_VERSION,
        "snapshot_format_version": SNAPSHOT_SCHEMA_VERSION,
    }


def _write_public_key(sync_root: Path, state: dict[str, Any]) -> Path:
    key_path = _public_key_path(sync_root, str(state["author_key_id"]))
    payload = {
        "schema_version": VAULT_SCHEMA_VERSION,
        "key_type": "ed25519-public",
        "author_key_id": state["author_key_id"],
        "public_key": state["signing_public_key"],
        "created_at": state["created_at"],
    }
    _write_json(key_path, payload)
    return key_path


def _private_key_from_state(state: dict[str, Any]) -> Any:
    crypto = _require_crypto()
    return crypto["ed25519"].Ed25519PrivateKey.from_private_bytes(_unb64(state["signing_private_key"]))


def _public_key_from_file(sync_root: Path, author_key_id: str) -> Any:
    crypto = _require_crypto()
    key_path = _public_key_path(sync_root, author_key_id)
    if not key_path.exists():
        raise RuntimeError(f"Missing public key: {key_path}")
    payload = _read_json(key_path)
    return crypto["ed25519"].Ed25519PublicKey.from_public_bytes(_unb64(payload["public_key"]))


def _aesgcm_from_state(state: dict[str, Any]) -> Any:
    crypto = _require_crypto()
    return crypto["AESGCM"](_unb64(state["vault_key"]))


def _encrypt_payload(state: dict[str, Any], payload: dict[str, Any]) -> tuple[str, str, str]:
    nonce = secrets.token_bytes(12)
    plaintext = _canonical_bytes(payload)
    ciphertext = _aesgcm_from_state(state).encrypt(nonce, plaintext, None)
    return _b64(nonce), _b64(ciphertext), _sha256_bytes(ciphertext)


def _decrypt_payload(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    plaintext = _aesgcm_from_state(state).decrypt(
        _unb64(str(event["payload_nonce"])),
        _unb64(str(event["encrypted_payload"])),
        None,
    )
    payload = json.loads(plaintext.decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid decrypted payload for event {event.get('event_id')}")
    return payload


def _device_event_dir(sync_root: Path, device_id: str) -> Path:
    return sync_root / "events" / device_id


def _device_event_files(sync_root: Path, device_id: str) -> list[Path]:
    event_dir = _device_event_dir(sync_root, device_id)
    if not event_dir.exists():
        return []
    return sorted(event_dir.glob("*.json"))


def _all_event_files(sync_root: Path) -> list[Path]:
    event_root = sync_root / "events"
    if not event_root.exists():
        return []
    return sorted(path for path in event_root.glob("*/*.json") if path.is_file())


def _all_snapshot_files(sync_root: Path) -> list[Path]:
    snapshot_root = sync_root / "snapshots"
    if not snapshot_root.exists():
        return []
    return sorted(path for path in snapshot_root.glob("*.snapshot") if path.is_file())


def _file_event_hash(path: Path) -> str:
    return _sha256_file(path)


def _last_device_hash(sync_root: Path, device_id: str) -> str:
    files = _device_event_files(sync_root, device_id)
    return _file_event_hash(files[-1]) if files else ""


def _next_sequence(sync_root: Path, device_id: str) -> int:
    files = _device_event_files(sync_root, device_id)
    if not files:
        return 1
    prefix = files[-1].name.split("_", 1)[0]
    try:
        return int(prefix) + 1
    except ValueError:
        return len(files) + 1


def _sign_event(state: dict[str, Any], event_without_signature: dict[str, Any]) -> str:
    signature = _private_key_from_state(state).sign(_canonical_bytes(event_without_signature))
    return _b64(signature)


def _event_file_name(sequence: int, event: dict[str, Any]) -> str:
    event_hash = _sha256_bytes(_canonical_bytes(event))
    return f"{sequence:012d}_{event_hash}.json"


def append_event(
    roots: VaultRoots,
    state: dict[str, Any],
    event_type: str,
    object_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    nonce, encrypted_payload, encrypted_hash = _encrypt_payload(state, payload)
    sequence = _next_sequence(roots.sync_root, state["device_id"])
    event: dict[str, Any] = {
        "event_id": "evt_" + uuid.uuid4().hex,
        "vault_id": state["vault_id"],
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_type": event_type,
        "author_key_id": state["author_key_id"],
        "device_id": state["device_id"],
        "sequence": sequence,
        "created_at": _now_iso(),
        "object_id": object_id,
        "prev_device_event_hash": _last_device_hash(roots.sync_root, state["device_id"]),
        "encrypted_payload_hash": encrypted_hash,
        "payload_nonce": nonce,
        "encrypted_payload": encrypted_payload,
    }
    event["signature"] = _sign_event(state, event)
    event_dir = _device_event_dir(roots.sync_root, state["device_id"])
    event_dir.mkdir(parents=True, exist_ok=True)
    event_path = event_dir / _event_file_name(sequence, event)
    _write_json(event_path, event, canonical=True)
    return {
        "event_id": event["event_id"],
        "event_type": event_type,
        "event_path": str(event_path),
        "event_hash": _file_event_hash(event_path),
    }


def vault_init(local_root: Path, sync_root: Path) -> dict[str, Any]:
    roots = VaultRoots(local_root=local_root.resolve(), sync_root=sync_root.resolve())
    roots.local_root.mkdir(parents=True, exist_ok=True)
    roots.sync_root.mkdir(parents=True, exist_ok=True)
    _assert_sync_root_clean(roots.sync_root)
    _ensure_sync_tree(roots.sync_root)

    vault_file = roots.sync_root / "vault.json"
    created_vault = not vault_file.exists()
    if created_vault:
        vault_id = "vault_" + uuid.uuid4().hex
        _write_json(vault_file, _vault_json(vault_id))
    else:
        vault_payload = _read_json(vault_file)
        vault_id = str(vault_payload["vault_id"])

    state_file = _state_path(roots.local_root)
    created_state = not state_file.exists()
    if created_state:
        state = _generate_state(roots.local_root, roots.sync_root, vault_id)
        _save_state(roots.local_root, state)
    else:
        state = _load_state(roots.local_root)

    key_path = _write_public_key(roots.sync_root, state)
    event_result: dict[str, Any] | None = None
    if not _device_event_files(roots.sync_root, state["device_id"]):
        event_result = append_event(
            roots,
            state,
            "vault_initialized",
            state["vault_id"],
            {
                "vault_id": state["vault_id"],
                "device_id": state["device_id"],
                "author_key_id": state["author_key_id"],
                "created_at": state["created_at"],
            },
        )

    return {
        "ok": True,
        "command": "vault init",
        "vault_id": vault_id,
        "local_root": str(roots.local_root),
        "sync_root": str(roots.sync_root),
        "created_vault": created_vault,
        "created_state": created_state,
        "public_key": str(key_path),
        "event": event_result,
    }


def _blob_path(sync_root: Path, blob_id: str) -> Path:
    if not _is_sha256_hex(blob_id):
        raise RuntimeError(f"Invalid blob id: {blob_id}")
    return _safe_sync_path(sync_root, "blobs", blob_id[:2], f"{blob_id}.blob")


def _public_key_path(sync_root: Path, author_key_id: str) -> Path:
    if not _is_safe_sync_id(author_key_id):
        raise RuntimeError(f"Invalid author_key_id: {author_key_id}")
    return _safe_sync_path(sync_root, "keys", f"{author_key_id}.json")


def _is_sha256_hex(value: str) -> bool:
    return bool(SHA256_HEX_RE.fullmatch(value))


def _is_safe_sync_id(value: str) -> bool:
    return bool(SAFE_SYNC_ID_RE.fullmatch(value))


def _safe_sync_path(sync_root: Path, *parts: str) -> Path:
    root = Path(sync_root).expanduser().resolve()
    path = root.joinpath(*parts).resolve()
    if not _is_relative_to(path, root):
        raise RuntimeError(f"Vault sync path escaped sync_root: {path}")
    return path


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def vault_import(local_root: Path, sync_root: Path, source_path: Path) -> dict[str, Any]:
    roots = VaultRoots(local_root=local_root.resolve(), sync_root=sync_root.resolve())
    state = _load_state(roots.local_root)
    source = source_path.expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise RuntimeError(f"Import source not found or not a file: {source}")

    plaintext = source.read_bytes()
    nonce = secrets.token_bytes(12)
    ciphertext = _aesgcm_from_state(state).encrypt(nonce, plaintext, None)
    blob_id = _sha256_bytes(ciphertext)
    blob_path = _blob_path(roots.sync_root, blob_id)
    blob_path.parent.mkdir(parents=True, exist_ok=True)
    if not blob_path.exists():
        blob_path.write_bytes(ciphertext)

    document_id = "doc_" + uuid.uuid4().hex
    payload = {
        "document_id": document_id,
        "original_name": source.name,
        "source_path": str(source),
        "source_sha256": _sha256_bytes(plaintext),
        "size_bytes": len(plaintext),
        "blob_id": blob_id,
        "blob_sha256": _sha256_file(blob_path),
        "blob_nonce": _b64(nonce),
        "imported_at": _now_iso(),
    }
    event = append_event(roots, state, "document_added", document_id, payload)
    return {
        "ok": True,
        "command": "vault import",
        "document_id": document_id,
        "blob_id": blob_id,
        "blob_path": str(blob_path),
        "event": event,
    }


def vault_status(local_root: Path, sync_root: Path) -> dict[str, Any]:
    roots = VaultRoots(local_root=local_root.resolve(), sync_root=sync_root.resolve())
    vault_file = roots.sync_root / "vault.json"
    state_exists = _state_path(roots.local_root).exists()
    vault_payload = _read_json(vault_file) if vault_file.exists() else {}
    return {
        "ok": True,
        "command": "vault status",
        "local_root": str(roots.local_root),
        "sync_root": str(roots.sync_root),
        "vault_exists": vault_file.exists(),
        "local_state_exists": state_exists,
        "vault_id": vault_payload.get("vault_id", ""),
        "events": len(_all_event_files(roots.sync_root)),
        "blobs": len(list((roots.sync_root / "blobs").glob("*/*.blob"))) if (roots.sync_root / "blobs").exists() else 0,
        "snapshots": len(list((roots.sync_root / "snapshots").glob("*.snapshot"))) if (roots.sync_root / "snapshots").exists() else 0,
        "forbidden_entries": _forbidden_sync_entries(roots.sync_root),
    }


def _verify_signature(sync_root: Path, event: dict[str, Any]) -> None:
    crypto = _require_crypto()
    signature = _unb64(str(event["signature"]))
    signed = dict(event)
    signed.pop("signature", None)
    public_key = _public_key_from_file(sync_root, str(event["author_key_id"]))
    try:
        public_key.verify(signature, _canonical_bytes(signed))
    except crypto["InvalidSignature"] as exc:
        raise RuntimeError("Invalid event signature") from exc


def _expected_hash_from_filename(path: Path) -> str:
    stem = path.stem
    parts = stem.split("_", 1)
    return parts[1] if len(parts) == 2 else ""
