from __future__ import annotations

import os
from pathlib import Path


FORBIDDEN_MARKERS = (
    "token",
    "secret",
    "client_secret",
    "refresh_token",
    "drive.file",
    "oauth",
    "raw",
    "restricted",
    "private",
)


def inspect_drive_sync_folder(folder_path: str | Path | None) -> dict[str, object]:
    if folder_path is None or str(folder_path).strip() == "":
        return _result("not_configured", "Aucun dossier choisi", False, False, False, "folder_not_selected")
    raw_path = str(folder_path)
    if _forbidden(raw_path):
        return _result("blocked", "Dossier Drive masque", False, False, False, "path_rejected")

    path = Path(folder_path).expanduser()
    label = _safe_label(path.name)
    if not path.exists():
        return _result("missing", label, False, False, False, "folder_missing")
    if not path.is_dir():
        return _result("blocked", label, False, False, False, "not_a_folder")
    can_read = _can_list(path)
    can_write = os.access(path, os.W_OK)
    status = "ready" if can_read and can_write else "read_only" if can_read else "blocked"
    return _result(
        status,
        label,
        can_read,
        can_write,
        any((path / name).is_dir() for name in ("packages", "devices")),
        "" if status == "ready" else status,
    )


def _result(
    status: str,
    label: str,
    can_read: bool,
    can_write: bool,
    contains_surface: bool,
    blocker: str,
) -> dict[str, object]:
    return {
        "status": status,
        "cloud_provider": "google_drive",
        "status_source": "test_local",
        "folder_label": label,
        "path_disclosure": "none" if status == "not_configured" else "folder-name-only",
        "current_account_can_read": can_read,
        "current_account_can_write": can_write,
        "contains_sync_surface": contains_surface,
        "subject_disclosure": "redacted",
        "blocker": blocker,
    }


def _safe_label(value: object) -> str:
    text = " ".join(str(value or "").split())
    if not text or _forbidden(text):
        return "Dossier Drive masque"
    return text[:80]


def _forbidden(value: object) -> bool:
    lowered = str(value or "").lower()
    return any(marker in lowered for marker in FORBIDDEN_MARKERS)


def _can_list(path: Path) -> bool:
    try:
        next(path.iterdir(), None)
    except OSError:
        return False
    return True
