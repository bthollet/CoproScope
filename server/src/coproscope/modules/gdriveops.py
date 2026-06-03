from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Iterable


DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file"
DEFAULT_SCOPES = (DRIVE_FILE_SCOPE,)
ALLOWED_SCOPES = frozenset(DEFAULT_SCOPES)
SMOKE_COMMAND = "drive smoke prepare"
SMOKE_UPLOAD_COMMAND = "drive smoke upload"
DEFAULT_SMOKE_FOLDER_NAME = "CoproScope Dev Smoke"
SYNC_PROTOCOL = "coproscope-drive-sync-v1"
DEFAULT_SYNC_GENERATION = 1
SYNC_CONFLICT_POLICY = "block_and_review_on_parent_mismatch"
SYNC_REMOTE_NAME_POLICY = "opaque-hash-derived"

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_BLOB_DIR_RE = re.compile(r"^[0-9a-f]{2}$")
_FORBIDDEN_UPLOAD_SEGMENTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "cache",
    "decrypted",
    "exports",
    "logs",
    "private",
    "raw",
    "restricted",
    "staging",
    "temp",
    "tmp",
}


def default_oauth_dir() -> Path:
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / "CoproScope" / "oauth"
    return Path.home() / ".config" / "CoproScope" / "oauth"


def default_client_secrets_path() -> Path:
    return default_oauth_dir() / "client_secret_dev.json"


def default_token_path() -> Path:
    return default_oauth_dir() / "token_drive_file.json"


def normalize_scopes(scopes: Iterable[str] | None = None) -> tuple[str, ...]:
    normalized: list[str] = []
    for scope in _iter_scope_values(scopes):
        for value in str(scope or "").split():
            if value not in ALLOWED_SCOPES:
                raise ValueError("CoproScope Drive OAuth is limited to the drive.file scope.")
            if value not in normalized:
                normalized.append(value)
    return tuple(normalized or DEFAULT_SCOPES)


def oauth_status(
    *,
    client_secrets_path: str | Path | None = None,
    token_path: str | Path | None = None,
    scopes: Iterable[str] | None = None,
) -> dict[str, object]:
    client_path = Path(client_secrets_path) if client_secrets_path else default_client_secrets_path()
    token = Path(token_path) if token_path else default_token_path()
    requested_scopes = normalize_scopes(scopes)
    token_scopes = _token_scopes(token)
    scope_ok = _token_scope_ok(token_scopes, requested_scopes)
    return {
        "status": "ready" if client_path.exists() and token.exists() and scope_ok else "action_required",
        "client_secrets_present": client_path.exists(),
        "token_present": token.exists(),
        "client_secrets_path": _redacted_path("oauth-client-json"),
        "token_path": _redacted_path("drive-token"),
        "path_disclosure": "redacted",
        "requested_scopes": list(requested_scopes),
        "token_scopes": list(token_scopes),
        "scope_ok": scope_ok,
        "scope_policy": "drive.file-only",
        "next_action": _next_action(client_path, token, scope_ok),
    }


def run_oauth_flow(
    *,
    client_secrets_path: str | Path | None = None,
    token_path: str | Path | None = None,
    scopes: Iterable[str] | None = None,
    open_browser: bool = True,
) -> dict[str, object]:
    client_path = Path(client_secrets_path) if client_secrets_path else default_client_secrets_path()
    token = Path(token_path) if token_path else default_token_path()
    if not client_path.exists():
        raise FileNotFoundError("OAuth client file missing from the CoproScope OAuth folder outside Git.")
    requested_scopes = normalize_scopes(scopes)
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError("Install Drive support with: python -m pip install -e .[drive]") from exc

    flow = InstalledAppFlow.from_client_secrets_file(str(client_path), list(requested_scopes))
    credentials = flow.run_local_server(port=0, open_browser=open_browser)
    token.parent.mkdir(parents=True, exist_ok=True)
    token.write_text(credentials.to_json(), encoding="utf-8")
    return {
        "status": "ok",
        "token_saved": True,
        "token_path": _redacted_path("drive-token"),
        "scopes": list(requested_scopes),
        "scope_policy": "drive.file-only",
        "next_action": "Run `coprocs drive status` then the encrypted Drive smoke test.",
    }


def guard_encrypted_drive_upload_candidate(
    *,
    sync_root: str | Path,
    encrypted_path: str | Path,
    cleartext_canary: str | bytes | None = None,
) -> dict[str, object]:
    root = Path(sync_root).expanduser().resolve()
    candidate = Path(encrypted_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        return _blocked_gate("missing_sync_root", "Upload blocked before Drive: vault sync surface is not ready.")
    if not candidate.exists() or not candidate.is_file():
        return _blocked_gate("missing_candidate", "Upload blocked before Drive: encrypted candidate is not available.")
    if not _is_relative_to(candidate, root):
        return _blocked_gate("outside_sync_root", "Upload blocked before Drive: candidate is outside the encrypted vault surface.")

    relative = candidate.relative_to(root)
    if _contains_forbidden_segment(relative):
        return _blocked_gate("forbidden_source_location", "Upload blocked before Drive: candidate is not part of the encrypted vault surface.")
    if not _is_allowed_encrypted_smoke_candidate(relative):
        return _blocked_gate("not_encrypted_surface", "Upload blocked before Drive: candidate does not match the encrypted smoke surface.")
    if _cleartext_canary_present(candidate, cleartext_canary):
        return _blocked_gate("cleartext_canary_detected", "Upload blocked before Drive: encrypted candidate contains the cleartext canary.")

    return {
        "ok": True,
        "code": "encrypted_vault_surface",
        "relative_path": relative.as_posix(),
        "size_bytes": candidate.stat().st_size,
        "sha256": _sha256_file(candidate),
        "cleartext_canary_checked": bool(cleartext_canary),
        "path_disclosure": "relative-vault-path-only",
    }


def prepare_encrypted_drive_smoke(
    *,
    sync_root: str | Path,
    encrypted_path: str | Path | None = None,
    token_path: str | Path | None = None,
    scopes: Iterable[str] | None = None,
    cleartext_canary: str | bytes | None = None,
    generation: int = DEFAULT_SYNC_GENERATION,
    parent_sha256: str | None = None,
) -> dict[str, object]:
    root = Path(sync_root).expanduser().resolve()
    candidate = _candidate_from_argument(root, encrypted_path) if encrypted_path is not None else _first_encrypted_smoke_candidate(root)
    requested_scopes = normalize_scopes(scopes)
    sync_generation = _normalize_sync_generation(generation)
    sync_parent = _normalize_parent_sha256(parent_sha256)
    token = Path(token_path) if token_path else default_token_path()
    token_scopes = _token_scopes(token)
    scope_ok = _token_scope_ok(token_scopes, requested_scopes)

    if candidate is None:
        gate = _blocked_gate("missing_candidate", "Upload blocked before Drive: no encrypted smoke candidate is available.")
    else:
        gate = guard_encrypted_drive_upload_candidate(
            sync_root=root,
            encrypted_path=candidate,
            cleartext_canary=cleartext_canary,
        )

    candidate_manifest = _candidate_manifest(
        gate,
        generation=sync_generation,
        parent_sha256=sync_parent,
    )
    ready_for_upload = bool(gate["ok"]) and token.exists() and scope_ok
    return {
        "status": _smoke_status(gate_ok=bool(gate["ok"]), token_present=token.exists(), scope_ok=scope_ok),
        "command": SMOKE_COMMAND,
        "upload_attempted": False,
        "ready_for_upload": ready_for_upload,
        "token_present": token.exists(),
        "scope_ok": scope_ok,
        "requested_scopes": list(requested_scopes),
        "token_scopes": list(token_scopes),
        "gate": gate,
        "encrypted_candidate": candidate_manifest,
        "next_action": _smoke_next_action(gate_ok=bool(gate["ok"]), token_present=token.exists(), scope_ok=scope_ok),
    }


def upload_encrypted_drive_smoke(
    *,
    sync_root: str | Path,
    encrypted_path: str | Path | None = None,
    token_path: str | Path | None = None,
    scopes: Iterable[str] | None = None,
    folder_name: str = DEFAULT_SMOKE_FOLDER_NAME,
    drive_service: Any | None = None,
    media_factory: Callable[[Path], object] | None = None,
    cleartext_canary: str | bytes | None = None,
    generation: int = DEFAULT_SYNC_GENERATION,
    parent_sha256: str | None = None,
) -> dict[str, object]:
    root = Path(sync_root).expanduser().resolve()
    candidate = _candidate_from_argument(root, encrypted_path) if encrypted_path is not None else _first_encrypted_smoke_candidate(root)
    requested_scopes = normalize_scopes(scopes)
    sync_generation = _normalize_sync_generation(generation)
    sync_parent = _normalize_parent_sha256(parent_sha256)
    token = Path(token_path) if token_path else default_token_path()
    token_scopes = _token_scopes(token)
    scope_ok = _token_scope_ok(token_scopes, requested_scopes)

    if candidate is None:
        gate = _blocked_gate("missing_candidate", "Upload blocked before Drive: no encrypted smoke candidate is available.")
    else:
        gate = guard_encrypted_drive_upload_candidate(
            sync_root=root,
            encrypted_path=candidate,
            cleartext_canary=cleartext_canary,
        )

    if not gate.get("ok") or not token.exists() or not scope_ok:
        return {
            "status": _smoke_status(gate_ok=bool(gate["ok"]), token_present=token.exists(), scope_ok=scope_ok),
            "command": SMOKE_UPLOAD_COMMAND,
            "upload_attempted": False,
            "ready_for_upload": False,
            "token_present": token.exists(),
            "scope_ok": scope_ok,
            "requested_scopes": list(requested_scopes),
            "token_scopes": list(token_scopes),
            "gate": gate,
            "encrypted_candidate": _candidate_manifest(
                gate,
                generation=sync_generation,
                parent_sha256=sync_parent,
            ),
            "next_action": _smoke_next_action(gate_ok=bool(gate["ok"]), token_present=token.exists(), scope_ok=scope_ok),
        }

    service = drive_service or _build_drive_service(token_path=token, scopes=requested_scopes)
    folder_id = _ensure_smoke_folder(service, _safe_drive_folder_name(folder_name))
    upload = _upload_encrypted_candidate(
        service=service,
        candidate=candidate,
        gate=gate,
        folder_id=folder_id,
        media_factory=media_factory,
        generation=sync_generation,
        parent_sha256=sync_parent,
    )
    return {
        "status": "uploaded",
        "command": SMOKE_UPLOAD_COMMAND,
        "upload_attempted": True,
        "ready_for_upload": True,
        "token_present": True,
        "scope_ok": True,
        "requested_scopes": list(requested_scopes),
        "token_scopes": list(token_scopes),
        "gate": gate,
        "encrypted_candidate": _candidate_manifest(
            gate,
            generation=sync_generation,
            parent_sha256=sync_parent,
        ),
        "drive": {
            "folder_name": _safe_drive_folder_name(folder_name),
            "folder_id_present": bool(folder_id),
            "file_id_present": bool(upload.get("id")),
            "uploaded_name": upload.get("name", "<redacted:drive-file-name>"),
            "path_disclosure": "redacted",
        },
        "next_action": "Drive smoke upload completed for encrypted vault bytes only.",
    }


def _next_action(client_path: Path, token_path: Path, scope_ok: bool) -> str:
    if not client_path.exists():
        return "Download the Desktop app OAuth JSON from Google Cloud and place it in the CoproScope OAuth folder outside Git."
    if not token_path.exists():
        return "Run `coprocs drive auth` to open Google consent in the browser."
    if not scope_ok:
        return "Reconnect Google Drive with the minimal drive.file authorization."
    return "OAuth bootstrap is ready for the encrypted Drive smoke test."


def _token_scopes(token_path: Path) -> tuple[str, ...]:
    if not token_path.exists():
        return ()
    try:
        payload = json.loads(token_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return ()
    scopes = payload.get("scopes") or payload.get("scope") or []
    if isinstance(scopes, str):
        return tuple(scope for scope in scopes.split() if scope)
    if isinstance(scopes, list):
        return tuple(scope for item in scopes for scope in str(item).split() if scope)
    return ()


def _iter_scope_values(scopes: Iterable[str] | None) -> Iterable[str]:
    if scopes is None:
        return DEFAULT_SCOPES
    if isinstance(scopes, str):
        return (scopes,)
    return scopes


def _token_scope_ok(token_scopes: Iterable[str], requested_scopes: Iterable[str]) -> bool:
    token_scope_set = set(token_scopes)
    requested_scope_set = set(requested_scopes)
    return bool(token_scope_set) and token_scope_set == requested_scope_set == set(DEFAULT_SCOPES)


def _redacted_path(label: str) -> str:
    return f"<redacted:{label}>"


def _blocked_gate(code: str, message: str) -> dict[str, object]:
    return {
        "ok": False,
        "code": code,
        "message": message,
        "path_disclosure": "blocked",
    }


def _contains_forbidden_segment(relative_path: Path) -> bool:
    return any(part.lower() in _FORBIDDEN_UPLOAD_SEGMENTS for part in relative_path.parts)


def _cleartext_canary_present(candidate: Path, cleartext_canary: str | bytes | None) -> bool:
    marker = _canary_bytes(cleartext_canary)
    if not marker:
        return False
    overlap = max(len(marker) - 1, 0)
    previous = b""
    with candidate.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            haystack = previous + chunk
            if marker in haystack:
                return True
            previous = haystack[-overlap:] if overlap else b""
    return False


def _canary_bytes(cleartext_canary: str | bytes | None) -> bytes:
    if cleartext_canary is None:
        return b""
    if isinstance(cleartext_canary, bytes):
        return cleartext_canary
    return cleartext_canary.encode("utf-8")


def _is_allowed_encrypted_smoke_candidate(relative_path: Path) -> bool:
    parts = relative_path.parts
    if len(parts) == 3 and parts[0] == "blobs":
        file_name = Path(parts[2])
        return bool(
            _BLOB_DIR_RE.fullmatch(parts[1])
            and _SHA256_HEX_RE.fullmatch(file_name.stem)
            and file_name.suffix == ".blob"
        )
    if len(parts) == 2 and parts[0] == "snapshots":
        return Path(parts[1]).suffix == ".snapshot"
    if len(parts) == 2 and parts[0] == "packages":
        file_name = Path(parts[1])
        return bool(_SHA256_HEX_RE.fullmatch(file_name.stem) and file_name.suffix == ".cspkg")
    return False


def _first_encrypted_smoke_candidate(sync_root: Path) -> Path | None:
    for pattern in ("packages/*.cspkg", "blobs/*/*.blob", "snapshots/*.snapshot"):
        for path in sorted(sync_root.glob(pattern)):
            if path.is_file():
                return path
    return None


def _candidate_from_argument(sync_root: Path, encrypted_path: str | Path) -> Path:
    candidate = Path(encrypted_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return sync_root / candidate


def _normalize_sync_generation(generation: int) -> int:
    if not isinstance(generation, int) or generation < 1:
        raise ValueError("Drive sync generation must be a positive integer.")
    return generation


def _normalize_parent_sha256(parent_sha256: str | None) -> str:
    if parent_sha256 is None:
        return ""
    normalized = str(parent_sha256).strip().lower()
    if not normalized:
        return ""
    if not _SHA256_HEX_RE.fullmatch(normalized):
        raise ValueError("Drive sync parent hash must be a sha256 hex value.")
    return normalized


def _candidate_manifest(
    gate: dict[str, object],
    *,
    generation: int,
    parent_sha256: str,
) -> dict[str, object] | None:
    if not gate.get("ok"):
        return None
    return {
        "relative_path": gate["relative_path"],
        "size_bytes": gate["size_bytes"],
        "sha256": gate["sha256"],
        "sync_contract": _sync_contract(gate, generation=generation, parent_sha256=parent_sha256),
    }


def _sync_contract(
    gate: dict[str, object],
    *,
    generation: int,
    parent_sha256: str,
) -> dict[str, object]:
    relative_path = str(gate["relative_path"])
    suffix = Path(relative_path).suffix
    packet_hash = str(gate["sha256"])
    packet_kind = _packet_kind(relative_path)
    return {
        "protocol": SYNC_PROTOCOL,
        "packet_kind": packet_kind,
        "generation": generation,
        "parent_sha256": parent_sha256,
        "packet_sha256": packet_hash,
        "remote_name": _uploaded_smoke_name(packet_hash, suffix),
        "remote_name_policy": SYNC_REMOTE_NAME_POLICY,
        "conflict_policy": SYNC_CONFLICT_POLICY,
        "collaboration_mode": "direct-sync-compatible",
        "cleartext_content": "forbidden",
    }


def _smoke_status(*, gate_ok: bool, token_present: bool, scope_ok: bool) -> str:
    if not gate_ok:
        return "blocked"
    if not token_present or not scope_ok:
        return "action_required"
    return "prepared"


def _smoke_next_action(*, gate_ok: bool, token_present: bool, scope_ok: bool) -> str:
    if not gate_ok:
        return "Use only encrypted vault smoke files before enabling any Drive upload."
    if not token_present:
        return "Connect Google Drive first; no Drive upload was attempted."
    if not scope_ok:
        return "Reconnect Google Drive with drive.file only; no Drive upload was attempted."
    return "Ready for a future Drive upload call; preparation only, no Drive upload was attempted."


def _build_drive_service(*, token_path: Path, scopes: Iterable[str]) -> Any:
    try:
        from google.oauth2.credentials import Credentials  # type: ignore
        from googleapiclient.discovery import build  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError("Install Drive support with: python -m pip install -e .[drive]") from exc

    credentials = Credentials.from_authorized_user_file(str(token_path), list(scopes))
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _ensure_smoke_folder(service: Any, folder_name: str) -> str:
    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    created = service.files().create(body=metadata, fields="id,name").execute()
    return str(created.get("id", ""))


def _upload_encrypted_candidate(
    *,
    service: Any,
    candidate: Path,
    gate: dict[str, object],
    folder_id: str,
    media_factory: Callable[[Path], object] | None,
    generation: int,
    parent_sha256: str,
) -> dict[str, object]:
    media = _media_upload(candidate, media_factory)
    relative_path = str(gate["relative_path"])
    uploaded_name = _uploaded_smoke_name(str(gate["sha256"]), Path(relative_path).suffix)
    app_properties = {
        "coproscope_surface": "encrypted-instance-package" if relative_path.startswith("packages/") else "encrypted-vault-smoke",
        "coproscope_sha256": str(gate["sha256"]),
        "coproscope_protocol": SYNC_PROTOCOL,
        "coproscope_generation": str(generation),
        "coproscope_conflict_policy": SYNC_CONFLICT_POLICY,
    }
    if parent_sha256:
        app_properties["coproscope_parent_sha256"] = parent_sha256
    metadata = {
        "name": uploaded_name,
        "parents": [folder_id],
        "mimeType": "application/octet-stream",
        "appProperties": app_properties,
    }
    response = service.files().create(
        body=metadata,
        media_body=media,
        fields="id,name,mimeType,size",
    ).execute()
    return response if isinstance(response, dict) else {}


def _media_upload(candidate: Path, media_factory: Callable[[Path], object] | None) -> object:
    if media_factory is not None:
        return media_factory(candidate)
    try:
        from googleapiclient.http import MediaFileUpload  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError("Install Drive support with: python -m pip install -e .[drive]") from exc
    return MediaFileUpload(str(candidate), mimetype="application/octet-stream", resumable=False)


def _safe_drive_folder_name(folder_name: str) -> str:
    cleaned = str(folder_name or "").strip() or DEFAULT_SMOKE_FOLDER_NAME
    lowered = cleaned.lower()
    forbidden = ("\\", "/", ":", "token=", "client_secret", "refresh_token", "raw", "restricted", "private")
    if any(marker in lowered for marker in forbidden):
        raise ValueError("Drive smoke folder name must be a simple non-sensitive label.")
    return cleaned[:80]


def _uploaded_smoke_name(sha256_hex: str, suffix: str) -> str:
    return f"coproscope-encrypted-smoke-{sha256_hex[:12]}{suffix or '.blob'}"


def _packet_kind(relative_path: str) -> str:
    if relative_path.startswith("snapshots/"):
        return "encrypted_snapshot"
    if relative_path.startswith("packages/"):
        return "encrypted_instance_package"
    return "encrypted_blob"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
