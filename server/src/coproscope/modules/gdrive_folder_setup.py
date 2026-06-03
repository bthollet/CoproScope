from __future__ import annotations

from typing import Any, Mapping

from . import gdrive_rights


DEFAULT_FOLDER_NAME = "CoproScope coffre chiffre"
FOLDER_FIELDS = "id,name,mimeType"


def create_private_sync_folder(
    *,
    drive_service: Any,
    folder_name: str = DEFAULT_FOLDER_NAME,
) -> dict[str, object]:
    name = _safe_folder_name(folder_name)
    try:
        created = drive_service.files().create(
            body={
                "name": name,
                "mimeType": gdrive_rights.FOLDER_MIME_TYPE,
                "appProperties": {
                    "coproscope_surface": "encrypted-instance-sync-folder",
                    "coproscope_cleartext": "forbidden",
                },
            },
            fields=FOLDER_FIELDS,
        ).execute()
    except Exception:
        return _blocked("folder_create_failed", "Dossier Google non cree. Verifiez la connexion Google.")

    folder_id = _text(created.get("id") if isinstance(created, Mapping) else "")
    if not folder_id:
        return _blocked("folder_id_missing", "Dossier Google cree sans confirmation exploitable.")

    rights = gdrive_rights.inspect_drive_folder_rights(drive_service=drive_service, folder_id=folder_id)
    validation = gdrive_rights.validate_drive_sync_rights(rights)
    if validation.get("status") == "blocked":
        return {
            "action": "google-folder",
            "status": "blocked",
            "summary": str(validation.get("summary") or "Droits Google a corriger."),
            "result_label": "Dossier Google bloque",
            "share_label": "Aucun identifiant Google n'est affiche.",
            "blocker_code": str(validation.get("blocker_code") or "rights_blocked"),
            "payload_disclosure": "counts_only",
            "path_disclosure": "none",
        }

    return {
        "action": "google-folder",
        "status": "configured",
        "summary": "Dossier Google chiffre pret pour ce coffre.",
        "result_label": "Dossier Google pret",
        "share_label": _share_label(validation),
        "folder_id": folder_id,
        "folder_id_disclosure": "redacted",
        "payload_disclosure": "counts_only",
        "path_disclosure": "none",
    }


def _share_label(validation: Mapping[str, object]) -> str:
    sharing = validation.get("sharing") if isinstance(validation.get("sharing"), Mapping) else {}
    if sharing.get("status") == "partage_nominal":
        return "Partage Google nominatif autorise; aucun lien public detecte."
    if validation.get("status") == "limited":
        return "Droits Google partiellement lus; aucun lien public detecte."
    return "Dossier Google prive; aucun lien public detecte."


def _blocked(code: str, summary: str) -> dict[str, object]:
    return {
        "action": "google-folder",
        "status": "blocked",
        "summary": summary,
        "result_label": "Dossier Google non prepare",
        "share_label": "Aucun identifiant Google n'est affiche.",
        "blocker_code": code,
        "payload_disclosure": "none",
        "path_disclosure": "none",
    }


def _safe_folder_name(value: object) -> str:
    text = " ".join(str(value or "").split()) or DEFAULT_FOLDER_NAME
    lowered = text.lower()
    forbidden = ("\\", "/", ":", "token", "secret", "oauth", "raw", "restricted", "private")
    if any(marker in lowered for marker in forbidden):
        return DEFAULT_FOLDER_NAME
    return text[:80]


def _text(value: object) -> str:
    return " ".join(str(value or "").split())[:300]
