from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping

from . import drive_instance_sync, gdriveops


PACKAGE_SURFACE = "encrypted-instance-package"
LIST_FIELDS = "nextPageToken, files(id,name,mimeType,size,modifiedTime,appProperties)"
UPLOAD_FIELDS = "id,name,mimeType,size"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_NAME_MARKERS = ("\\", "/", "..", "token", "secret", "oauth", "raw", "restricted", "private")


def list_encrypted_instance_packages(
    *,
    drive_service: Any,
    folder_id: str,
    page_size: int = 100,
) -> dict[str, object]:
    packages = _remote_package_candidates(drive_service.files(), folder_id, page_size)
    return {
        "status": "ready" if packages else "idle",
        "remote_package_count": len(packages),
        "packages": [_public_package(item) for item in packages],
        "drive": {
            "folder_id_present": bool(folder_id),
            "id_disclosure": "redacted",
        },
        "path_disclosure": "none",
    }


def download_latest_encrypted_instance_package(
    *,
    drive_service: Any,
    folder_id: str,
    sync_root: str | Path,
    page_size: int = 100,
    media_downloader_factory: Callable[[Any], bytes] | None = None,
) -> dict[str, object]:
    sync = Path(sync_root).expanduser().resolve()
    if sync.exists() and not sync.is_dir():
        return _blocked("invalid_sync_root", "Download blocked before Drive import: local sync surface is not a folder.")

    files_api = drive_service.files()
    packages = _remote_package_candidates(files_api, folder_id, page_size)
    if not packages:
        return {
            "status": "idle",
            "downloaded": False,
            "remote_package_count": 0,
            "next_action": "Aucun paquet chiffre CoproScope visible dans le dossier Drive choisi.",
            "drive": {"folder_id_present": bool(folder_id), "file_id_present": False, "id_disclosure": "redacted"},
            "path_disclosure": "none",
        }

    latest = max(packages, key=lambda item: (int(item["generation"]), str(item["modified_time"]), str(item["name"])))
    content = _download_bytes(files_api, str(latest["file_id"]), media_downloader_factory)
    content_sha256 = _sha256_bytes(content)
    if content_sha256 != latest["sha256"]:
        return _blocked("sha256_mismatch", "Download blocked: the Drive package does not match its expected fingerprint.")
    package_check = _validate_package_payload(content)
    if package_check is not None:
        return package_check

    local_name = f"{content_sha256}{drive_instance_sync.PACKAGE_SUFFIX}"
    local_path = sync / drive_instance_sync.PACKAGE_DIR / local_name
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(content)
    return {
        "status": "downloaded",
        "downloaded": True,
        "remote_package_count": len(packages),
        "package": {
            "generation": latest["generation"],
            "remote_name": latest["name"],
            "sha256": content_sha256,
            "local_ready": True,
        },
        "drive": {"folder_id_present": bool(folder_id), "file_id_present": True, "id_disclosure": "redacted"},
        "path_disclosure": "none",
        "next_action": "Paquet chiffre recupere; la recuperation locale peut verifier et appliquer.",
    }


def upload_encrypted_instance_package(
    *,
    drive_service: Any,
    folder_id: str,
    sync_root: str | Path,
    encrypted_path: str | Path,
    media_factory: Callable[[Path], object] | None = None,
) -> dict[str, object]:
    sync = Path(sync_root).expanduser().resolve()
    candidate = Path(encrypted_path).expanduser()
    if not candidate.is_absolute():
        candidate = sync / candidate
    candidate = candidate.resolve()
    gate = gdriveops.guard_encrypted_drive_upload_candidate(sync_root=sync, encrypted_path=candidate)
    if not gate.get("ok"):
        return _blocked("upload_gate_blocked", "Upload blocked: only encrypted CoproScope packages can be sent.")

    package_payload = _read_package_payload(candidate)
    if not isinstance(package_payload, Mapping):
        return _blocked("invalid_package_json", "Upload blocked: the local encrypted package is not valid.")
    if package_payload.get("protocol") != drive_instance_sync.PROTOCOL:
        return _blocked("wrong_package_protocol", "Upload blocked: the local package does not match CoproScope sync.")

    sha256 = str(gate["sha256"])
    generation = _generation(package_payload.get("generation"))
    media = _media_upload(candidate, media_factory)
    try:
        response = drive_service.files().create(
            body={
                "name": _uploaded_name(sha256),
                "parents": [str(folder_id)],
                "mimeType": "application/octet-stream",
                "appProperties": {
                    "coproscope_surface": PACKAGE_SURFACE,
                    "coproscope_sha256": sha256,
                    "coproscope_protocol": gdriveops.SYNC_PROTOCOL,
                    "coproscope_generation": str(generation),
                    "coproscope_conflict_policy": gdriveops.SYNC_CONFLICT_POLICY,
                },
            },
            media_body=media,
            fields=UPLOAD_FIELDS,
        ).execute()
    finally:
        _close_media(media)
    uploaded = response if isinstance(response, Mapping) else {}
    return {
        "status": "uploaded",
        "uploaded": True,
        "package": {
            "generation": generation,
            "remote_name": _uploaded_name(sha256),
            "sha256": sha256,
        },
        "drive": {
            "folder_id_present": bool(folder_id),
            "file_id_present": bool(uploaded.get("id")),
            "id_disclosure": "redacted",
        },
        "path_disclosure": "none",
        "next_action": "Paquet chiffre envoye; les autres postes pourront le verifier avant application.",
    }


def build_drive_service(*, token_path: str | Path | None = None) -> Any:
    token = Path(token_path) if token_path else gdriveops.default_token_path()
    scopes = gdriveops.normalize_scopes()
    try:
        from google.oauth2.credentials import Credentials  # type: ignore
        from googleapiclient.discovery import build  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional Drive dependency
        raise RuntimeError("Install Drive support with: python -m pip install -e .[drive]") from exc
    credentials = Credentials.from_authorized_user_file(str(token), list(scopes))
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _remote_package_candidates(files_api: Any, folder_id: str, page_size: int) -> list[dict[str, object]]:
    page_token = None
    candidates: list[dict[str, object]] = []
    while True:
        request = files_api.list(
            q=_list_query(folder_id),
            spaces="drive",
            fields=LIST_FIELDS,
            pageSize=max(1, min(int(page_size or 100), 1000)),
            pageToken=page_token,
        )
        payload = request.execute()
        for item in payload.get("files", []) if isinstance(payload, Mapping) else []:
            candidate = _remote_package(item)
            if candidate:
                candidates.append(candidate)
        page_token = payload.get("nextPageToken") if isinstance(payload, Mapping) else None
        if not page_token:
            return candidates


def _remote_package(item: object) -> dict[str, object] | None:
    if not isinstance(item, Mapping):
        return None
    props = item.get("appProperties")
    if not isinstance(props, Mapping):
        return None
    sha256 = str(props.get("coproscope_sha256") or "").lower()
    if (
        props.get("coproscope_surface") != PACKAGE_SURFACE
        or props.get("coproscope_protocol") != gdriveops.SYNC_PROTOCOL
        or not _SHA256_RE.fullmatch(sha256)
    ):
        return None
    name = _safe_remote_name(item.get("name"))
    file_id = str(item.get("id") or "")
    if not name or not file_id:
        return None
    return {
        "file_id": file_id,
        "name": name,
        "sha256": sha256,
        "generation": _generation(props.get("coproscope_generation")),
        "size_bytes": _size_bytes(item.get("size")),
        "modified_time": str(item.get("modifiedTime") or ""),
    }


def _public_package(item: Mapping[str, object]) -> dict[str, object]:
    return {
        "name": item["name"],
        "generation": item["generation"],
        "size_bytes": item["size_bytes"],
        "sha256": item["sha256"],
        "remote_ref": _remote_ref(str(item["file_id"])),
    }


def _safe_remote_name(value: object) -> str:
    name = " ".join(str(value or "").split())
    lowered = name.lower()
    if not name.endswith(drive_instance_sync.PACKAGE_SUFFIX):
        return ""
    if any(marker in lowered for marker in _FORBIDDEN_NAME_MARKERS):
        return ""
    return name[:120]


def _generation(value: object) -> int:
    try:
        return max(0, int(str(value or "0")))
    except ValueError:
        return 0


def _size_bytes(value: object) -> int:
    try:
        return max(0, int(str(value or "0")))
    except ValueError:
        return 0


def _download_bytes(files_api: Any, file_id: str, media_downloader_factory: Callable[[Any], bytes] | None) -> bytes:
    request = files_api.get_media(fileId=file_id)
    if media_downloader_factory is not None:
        return bytes(media_downloader_factory(request))
    try:
        from googleapiclient.http import MediaIoBaseDownload  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional Drive dependency
        raise RuntimeError("Install Drive support with: python -m pip install -e .[drive]") from exc
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buffer.getvalue()


def _media_upload(candidate: Path, media_factory: Callable[[Path], object] | None) -> object:
    if media_factory is not None:
        return media_factory(candidate)
    try:
        from googleapiclient.http import MediaFileUpload  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional Drive dependency
        raise RuntimeError("Install Drive support with: python -m pip install -e .[drive]") from exc
    return MediaFileUpload(str(candidate), mimetype="application/octet-stream", resumable=False)


def _close_media(media: object) -> None:
    stream = getattr(media, "_fd", None)
    close = getattr(stream, "close", None)
    if callable(close):
        close()


def _read_package_payload(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _validate_package_payload(content: bytes) -> dict[str, object] | None:
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _blocked("invalid_package_json", "Download blocked: the Drive package is not a valid encrypted package.")
    if not isinstance(payload, Mapping):
        return _blocked("invalid_package_payload", "Download blocked: the Drive package format is not valid.")
    if payload.get("protocol") != drive_instance_sync.PROTOCOL:
        return _blocked("wrong_package_protocol", "Download blocked: the Drive package does not match CoproScope sync.")
    if not str(payload.get("package_hash") or ""):
        return _blocked("missing_package_hash", "Download blocked: the Drive package fingerprint is missing.")
    return None


def _blocked(code: str, message: str) -> dict[str, object]:
    return {
        "status": "blocked",
        "downloaded": False,
        "blocker_code": code,
        "next_action": message,
        "drive": {"folder_id_present": False, "file_id_present": False, "id_disclosure": "redacted"},
        "path_disclosure": "none",
    }


def _list_query(folder_id: str) -> str:
    folder = str(folder_id or "").replace("\\", "\\\\").replace("'", "\\'")
    return (
        f"'{folder}' in parents and trashed = false and mimeType = 'application/octet-stream' "
        f"and appProperties has {{ key='coproscope_surface' and value='{PACKAGE_SURFACE}' }}"
    )


def _remote_ref(file_id: str) -> str:
    return hashlib.sha256(file_id.encode("utf-8")).hexdigest()[:16]


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _uploaded_name(sha256_hex: str) -> str:
    return f"coproscope-encrypted-smoke-{sha256_hex[:12]}{drive_instance_sync.PACKAGE_SUFFIX}"
