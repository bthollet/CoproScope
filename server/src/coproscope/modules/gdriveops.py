from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Iterable


DRIVE_FILE_SCOPE = "https://www.googleapis.com/auth/drive.file"
DEFAULT_SCOPES = (DRIVE_FILE_SCOPE,)
ALLOWED_SCOPES = frozenset(DEFAULT_SCOPES)
SMOKE_COMMAND = "drive smoke prepare"

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

    return {
        "ok": True,
        "code": "encrypted_vault_surface",
        "relative_path": relative.as_posix(),
        "size_bytes": candidate.stat().st_size,
        "sha256": _sha256_file(candidate),
        "path_disclosure": "relative-vault-path-only",
    }


def prepare_encrypted_drive_smoke(
    *,
    sync_root: str | Path,
    encrypted_path: str | Path | None = None,
    token_path: str | Path | None = None,
    scopes: Iterable[str] | None = None,
) -> dict[str, object]:
    root = Path(sync_root).expanduser().resolve()
    candidate = _candidate_from_argument(root, encrypted_path) if encrypted_path is not None else _first_encrypted_smoke_candidate(root)
    requested_scopes = normalize_scopes(scopes)
    token = Path(token_path) if token_path else default_token_path()
    token_scopes = _token_scopes(token)
    scope_ok = _token_scope_ok(token_scopes, requested_scopes)

    if candidate is None:
        gate = _blocked_gate("missing_candidate", "Upload blocked before Drive: no encrypted smoke candidate is available.")
    else:
        gate = guard_encrypted_drive_upload_candidate(sync_root=root, encrypted_path=candidate)

    candidate_manifest = _candidate_manifest(gate)
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
        payload = json.loads(token_path.read_text(encoding="utf-8"))
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
    return False


def _first_encrypted_smoke_candidate(sync_root: Path) -> Path | None:
    for pattern in ("blobs/*/*.blob", "snapshots/*.snapshot"):
        for path in sorted(sync_root.glob(pattern)):
            if path.is_file():
                return path
    return None


def _candidate_from_argument(sync_root: Path, encrypted_path: str | Path) -> Path:
    candidate = Path(encrypted_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return sync_root / candidate


def _candidate_manifest(gate: dict[str, object]) -> dict[str, object] | None:
    if not gate.get("ok"):
        return None
    return {
        "relative_path": gate["relative_path"],
        "size_bytes": gate["size_bytes"],
        "sha256": gate["sha256"],
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
