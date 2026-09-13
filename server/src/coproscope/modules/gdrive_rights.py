from __future__ import annotations

from collections import Counter
from typing import Any, Mapping


FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
FILE_FIELDS = "id,name,mimeType,ownedByMe,shared,capabilities(canAddChildren,canEdit,canShare)"
PERMISSION_FIELDS = "nextPageToken,permissions(type,role,allowFileDiscovery,deleted)"
WRITER_ROLES = {"owner", "organizer", "fileOrganizer", "writer"}
READER_ROLES = WRITER_ROLES | {"reader", "commenter"}
BLOCKING_SHARE_STATUSES = {
    "lien_public": ("public_link", "Dossier Google partage par lien public: synchronisation refusee."),
    "partage_domaine": ("domain_share", "Dossier Google ouvert a un domaine: synchronisation refusee."),
    "droits_non_lisibles": ("permissions_unreadable", "Droits Google non lisibles: synchronisation refusee par securite."),
}


def inspect_drive_folder_rights(*, drive_service: Any, folder_id: str, page_size: int = 100) -> dict[str, object]:
    metadata = _folder_metadata(drive_service.files(), folder_id)
    if not metadata:
        return _blocked("folder_unavailable", "Dossier Google inaccessible", folder_id)

    permissions_payload = _permission_summary(drive_service, folder_id, page_size)
    capabilities = metadata.get("capabilities") if isinstance(metadata.get("capabilities"), Mapping) else {}
    can_write = bool(capabilities.get("canAddChildren") or capabilities.get("canEdit"))
    can_share = bool(capabilities.get("canShare"))
    permissions_readable = permissions_payload.get("permissions_readable") is True
    share_status = _share_status(metadata, permissions_payload)

    return {
        "status": "inspected" if permissions_readable else "limited",
        "folder": {
            "folder_id_present": bool(folder_id),
            "id_disclosure": "redacted",
            "is_folder": metadata.get("mimeType") == FOLDER_MIME_TYPE,
            "owned_by_this_google_account": bool(metadata.get("ownedByMe")),
            "shared_by_google": bool(metadata.get("shared")),
        },
        "current_google_account": {
            "can_read_metadata": True,
            "can_write_files": can_write,
            "can_manage_sharing": can_share,
        },
        "sharing": {
            "status": share_status,
            "permissions_readable": permissions_readable,
            "permission_count": permissions_payload.get("permission_count", 0),
            "role_counts": permissions_payload.get("role_counts", {}),
            "type_counts": permissions_payload.get("type_counts", {}),
            "public_link_present": bool(permissions_payload.get("public_link_present")),
            "domain_share_present": bool(permissions_payload.get("domain_share_present")),
            "writer_present": bool(permissions_payload.get("writer_present") or can_write),
            "reader_present": bool(permissions_payload.get("reader_present")),
        },
        "sync_account_policy": {
            "google_account_required_for_api_sync": True,
            "gmail_address_required": False,
            "summary": "Chaque poste qui synchronise par l'API doit avoir un compte Google autorise; l'adresse n'a pas besoin d'etre Gmail.",
        },
        "payload_disclosure": "counts_only",
        "path_disclosure": "none",
    }


def validate_drive_sync_rights(rights: Mapping[str, object]) -> dict[str, object]:
    folder = rights.get("folder") if isinstance(rights.get("folder"), Mapping) else {}
    account = rights.get("current_google_account") if isinstance(rights.get("current_google_account"), Mapping) else {}
    sharing = rights.get("sharing") if isinstance(rights.get("sharing"), Mapping) else {}
    share_status = str(sharing.get("status") or "")

    if rights.get("status") == "blocked":
        return _sync_blocked(str(rights.get("blocker_code") or "folder_unavailable"), "Dossier Google inaccessible.")
    if folder and folder.get("is_folder") is False:
        return _sync_blocked("not_a_folder", "La cible Google choisie n'est pas un dossier.")
    if account and not account.get("can_write_files"):
        return _sync_blocked("missing_write_access", "Ce compte Google ne peut pas ecrire dans ce dossier.")
    if share_status in BLOCKING_SHARE_STATUSES:
        code, summary = BLOCKING_SHARE_STATUSES[share_status]
        return _sync_blocked(code, summary, share_status=share_status)

    status = "ok" if rights.get("status") == "inspected" else "limited"
    return {
        "status": status,
        "summary": _allowed_summary(share_status, status),
        "sharing": _public_sharing(sharing),
        "current_google_account": {"can_write_files": bool(account.get("can_write_files"))},
        "payload_disclosure": "counts_only",
        "path_disclosure": "none",
    }


def _folder_metadata(files_api: Any, folder_id: str) -> Mapping[str, object] | None:
    try:
        payload = files_api.get(
            fileId=str(folder_id),
            fields=FILE_FIELDS,
            supportsAllDrives=True,
        ).execute()
    except Exception:
        return None
    return payload if isinstance(payload, Mapping) else None


def _permission_summary(drive_service: Any, folder_id: str, page_size: int) -> dict[str, object]:
    permissions_api = getattr(drive_service, "permissions", lambda: None)()
    if permissions_api is None:
        return _limited_permissions()

    page_token = None
    rows: list[Mapping[str, object]] = []
    try:
        while True:
            payload = permissions_api.list(
                fileId=str(folder_id),
                fields=PERMISSION_FIELDS,
                pageSize=max(1, min(int(page_size or 100), 1000)),
                pageToken=page_token,
                supportsAllDrives=True,
            ).execute()
            if not isinstance(payload, Mapping):
                break
            for item in payload.get("permissions", []):
                if isinstance(item, Mapping) and not item.get("deleted"):
                    rows.append(item)
            page_token = payload.get("nextPageToken")
            if not page_token:
                break
    except Exception:
        return _limited_permissions()

    role_counts = Counter(_safe_value(item.get("role")) for item in rows)
    type_counts = Counter(_safe_value(item.get("type")) for item in rows)
    roles = set(role_counts)
    return {
        "permissions_readable": True,
        "permission_count": len(rows),
        "role_counts": dict(sorted((key, value) for key, value in role_counts.items() if key)),
        "type_counts": dict(sorted((key, value) for key, value in type_counts.items() if key)),
        "public_link_present": bool(type_counts.get("anyone")),
        "domain_share_present": bool(type_counts.get("domain")),
        "writer_present": bool(roles & WRITER_ROLES),
        "reader_present": bool(roles & READER_ROLES),
    }


def _share_status(metadata: Mapping[str, object], permissions_payload: Mapping[str, object]) -> str:
    if not permissions_payload.get("permissions_readable"):
        return "droits_non_lisibles"
    if permissions_payload.get("public_link_present"):
        return "lien_public"
    if permissions_payload.get("domain_share_present"):
        return "partage_domaine"
    if int(permissions_payload.get("permission_count") or 0) > 1 or metadata.get("shared"):
        return "partage_nominal"
    return "prive"


def _limited_permissions() -> dict[str, object]:
    return {
        "permissions_readable": False,
        "permission_count": 0,
        "role_counts": {},
        "type_counts": {},
        "public_link_present": False,
        "domain_share_present": False,
        "writer_present": False,
        "reader_present": False,
    }


def _blocked(code: str, message: str, folder_id: str) -> dict[str, object]:
    return {
        "status": "blocked",
        "blocker_code": code,
        "summary": message,
        "folder": {"folder_id_present": bool(folder_id), "id_disclosure": "redacted"},
        "payload_disclosure": "none",
        "path_disclosure": "none",
    }


def _sync_blocked(code: str, message: str, *, share_status: str = "") -> dict[str, object]:
    return {
        "status": "blocked",
        "blocker_code": code,
        "summary": message,
        "sharing": {
            "status": share_status,
            "public_link_present": share_status == "lien_public",
            "domain_share_present": share_status == "partage_domaine",
            "permissions_readable": share_status != "droits_non_lisibles",
        },
        "payload_disclosure": "counts_only",
        "path_disclosure": "none",
    }


def _allowed_summary(share_status: str, status: str) -> str:
    if status == "limited":
        return "Droits Google partiellement lus; aucune ouverture publique detectee."
    if share_status == "partage_nominal":
        return "Dossier Google partage nominativement: synchronisation autorisee."
    return "Dossier Google prive: synchronisation autorisee."


def _public_sharing(sharing: Mapping[str, object]) -> dict[str, object]:
    return {
        "status": str(sharing.get("status") or ""),
        "permissions_readable": bool(sharing.get("permissions_readable")),
        "permission_count": int(sharing.get("permission_count") or 0),
        "public_link_present": bool(sharing.get("public_link_present")),
        "domain_share_present": bool(sharing.get("domain_share_present")),
    }


def _safe_value(value: object) -> str:
    text = str(value or "").strip()
    if text in {"user", "group", "domain", "anyone", "owner", "organizer", "fileOrganizer", "writer", "commenter", "reader"}:
        return text
    return ""
