from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode

from fastapi import Request

from coproscope.modules import drive_folder_status
from coproscope.modules.drive_instance_sync import publish_instance_update, recover_instance_update


def register_drive_mvp_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    instance = app.state.instance

    @app.get("/coffre/drive", response_class=html_response)
    def drive_mvp(request: Request):
        require_token(request)
        result = _stored_result(app, request.query_params.get("drive_sync_id"))
        view = build_drive_mvp_view(instance, year, result)
        return templates.TemplateResponse(
            request=request,
            name="drive_mvp.html",
            context=context(request, "drive_mvp", model=view["shell_model"], drive_mvp=view),
        )

    @app.post("/coffre/drive/publier-test")
    async def drive_mvp_publish_test(request: Request):
        require_token(request)
        result = publish_instance_update(
            instance=instance,
            sync_root=_artifact(instance, "drive_instance_demo_sync"),
            local_state_root=_artifact(instance, "drive_instance_sync_state"),
        )
        return _redirect(app, request, result)

    @app.post("/coffre/drive/recuperer-test")
    async def drive_mvp_recover_test(request: Request):
        require_token(request)
        result = recover_instance_update(
            instance=instance,
            sync_root=_artifact(instance, "drive_instance_demo_sync"),
            local_state_root=_artifact(instance, "drive_instance_sync_state"),
        )
        return _redirect(app, request, result)


def build_drive_mvp_view(instance: Any, year: int, result: Mapping[str, object] | None = None) -> dict[str, Any]:
    folder = _folder_status()
    panel = _panel(result)
    return {
        "title": "Synchronisation Drive chiffree",
        "notice": "Test local seulement. Aucun envoi Google reel.",
        "status": _page_status(),
        "folder_setup": folder,
        "instance_sync": panel,
        "primary_actions": _blocked_google_actions(),
        "readiness": [
            _item("Pret", "Chiffrement separe du cloud", "Les donnees sont chiffrees avant le transport."),
            _item("A verifier", "Dossier Google Drive", folder["summary"]),
            _item(str(panel["state"]), "Demonstration locale", str(panel["summary"])),
            _item("A brancher", "Droits Google", "Les droits du dossier seront lus seulement via Google Drive."),
            _item("Local", "Etat visible", "Cet ecran montre seulement ce poste."),
        ],
        "flow": [
            _flow("Ce poste", "Prepare le fichier chiffre", "CoproScope chiffre localement avant depot."),
            _flow("Google Drive", "Transporte les fichiers", "Drive ne voit que des fichiers chiffres."),
            _flow("Ce poste", "Verifie puis recupere", "La copie lisible reste sur ce poste."),
        ],
        "sync_status_bar": _status_bar(panel),
        "local_vs_drive": [
            {"label": "Reste sur ce poste", "items": ["Cle locale", "Copie lisible", "Etat de recuperation", "Cache temporaire"]},
            {"label": "Peut aller dans Drive", "items": ["Fichiers chiffres", "Index minimal", "Preuves de controle", "Cles publiques"]},
        ],
        "google_layer": {
            "account": "Chaque personne utilise son compte Google pour acceder au dossier partage.",
            "read": "Lecture Drive = recevoir les fichiers chiffres.",
            "write": "Ecriture Drive = deposer des fichiers chiffres.",
            "limits": "L'ecran affiche seulement l'etat local de ce poste.",
        },
        "links": [{"label": "Retour coffre et partage", "href": "/coffre/partage"}],
        "shell_model": _shell_model(instance, year),
    }


def _folder_status() -> dict[str, object]:
    folder = drive_folder_status.inspect_drive_sync_folder(None)
    return {
        "state": "Aucun dossier choisi",
        "tone": "action",
        "title": "Dossier Google Drive",
        "subtitle": "Choisissez plus tard le dossier partage qui recevra uniquement les fichiers chiffres.",
        "headline": str(folder["folder_label"]),
        "summary": "Le vrai dossier Google n'est pas encore choisi dans cette tranche.",
        "share_label": "Partage Google inconnu",
        "share_detail": "Aucun controle Google n'est encore lance.",
        "checks": [
            _check("Dossier", "A choisir", "Selection locale a brancher."),
            _check("Lecture locale", "Non teste", "Test local sur ce poste."),
            _check("Ecriture locale", "Non teste", "Necessaire pour publier."),
            _check("Partage Google", "Inconnu", "A verifier par l'API Google Drive."),
        ],
    }


def _panel(result: Mapping[str, object] | None) -> dict[str, object]:
    if not result:
        return {
            "tone": "idle",
            "state": "Pret a tester",
            "title": "Parcours publier / recuperer",
            "summary": "Mode demonstration locale: testez une publication chiffree puis une recuperation sur ce poste.",
            "result_label": "Aucune action lancee",
            "share_label": "Partage Google non verifie par ce test",
            "publish_href": "/coffre/drive/publier-test",
            "recover_href": "/coffre/drive/recuperer-test",
            "publish_label": "Publier en demonstration locale",
            "recover_label": "Recuperer en demonstration locale",
            "steps": [
                _step("Publier", "A lancer", "Cree une version test chiffree."),
                _step("Dossier Drive", "A lancer", "Recoit seulement des fichiers chiffres."),
                _step("Recuperer", "A lancer", "Verifie puis applique sur ce poste."),
            ],
        }
    status = str(result.get("status") or "blocked")
    return {
        "tone": "ready" if status in {"published", "recovered", "idle"} else "error",
        "state": _state(status),
        "title": "Parcours publier / recuperer",
        "summary": _safe(result.get("summary"), "Action Drive terminee."),
        "result_label": _safe(result.get("result_label"), "Action Drive terminee"),
        "share_label": _safe(result.get("share_label"), "Partage Google non verifie par ce test"),
        "publish_href": "/coffre/drive/publier-test",
        "recover_href": "/coffre/drive/recuperer-test",
        "publish_label": "Publier en demonstration locale",
        "recover_label": "Recuperer en demonstration locale",
        "steps": _steps(result),
    }


def _status_bar(panel: Mapping[str, object]) -> dict[str, object]:
    if panel.get("tone") == "ready":
        return {
            "state": "ok",
            "icon": "cloud",
            "label": str(panel["state"]),
            "summary": str(panel["summary"]),
            "aria_label": "Etat Drive teste sur ce poste, ouvrir les details",
            "details": [
                "Ce poste publie seulement des fichiers chiffres.",
                "Ce poste recupere apres verification locale.",
                "Partage Google non verifie par ce test.",
                "L'etat affiche est limite a ce poste.",
            ],
        }
    if panel.get("tone") == "error":
        return {
            "state": "error",
            "icon": "error",
            "label": "Drive bloque",
            "summary": str(panel["summary"]),
            "aria_label": "Etat Drive bloque, ouvrir les details",
            "details": [
                str(panel["result_label"]),
                str(panel["share_label"]),
                "La copie lisible reste sur ce poste.",
            ],
        }
    return {
        "state": "setup",
        "icon": "gear",
        "label": "A configurer",
        "summary": "Le vrai dossier Drive reste a choisir.",
        "aria_label": "Etat Drive a configurer, ouvrir les details",
        "details": [
            "Aucun dossier Drive reel n'est choisi.",
            "La demonstration locale peut etre lancee sur ce poste.",
            "Aucun document lisible ni cle locale n'est envoye dans Drive.",
        ],
    }


def _blocked_google_actions() -> list[dict[str, str]]:
    return [
        {"label": "Publier vers Drive", "reason": "Publication Google bloquee: dossier et droits a verifier.", "enabled": "false"},
        {"label": "Recuperer depuis Drive", "reason": "Recuperation Google bloquee: dossier et droits a verifier.", "enabled": "false"},
    ]


def _page_status() -> dict[str, str]:
    return {
        "tone": "review",
        "label": "Dossier Drive a choisir",
        "summary": "Testez seulement la production et la recuperation de fichiers chiffres sur ce poste.",
        "source": "Controle local expurge",
    }


def _shell_model(instance: Any, year: int) -> dict[str, object]:
    instance_id = str(getattr(instance, "instance_id", "local"))[:40]
    return {
        "instance": {"id": instance_id, "name": getattr(instance, "name", "CoproScope"), "year": year},
        "ux": {"shell": {"page_title": "Drive chiffre", "sharing_mode_label": "Dossier Drive a choisir", "sharing_mode_status": "Aucun envoi depuis cette page"}},
        "kpis": {},
        "action_summary": {},
    }


def _redirect(app: Any, request: Any, result: dict[str, object]):
    from starlette.responses import RedirectResponse

    query = {"drive_sync_id": _store_result(app, result)}
    token = request.query_params.get("token")
    if token:
        query["token"] = token
    return RedirectResponse(url=f"/coffre/drive?{urlencode(query)}", status_code=303)


def _store_result(app: Any, result: dict[str, object]) -> str:
    key = secrets.token_hex(8)
    results = getattr(app.state, "drive_mvp_results", None)
    if not isinstance(results, dict):
        results = {}
        app.state.drive_mvp_results = results
    results[key] = result
    return key


def _stored_result(app: Any, key: str | None) -> dict[str, object] | None:
    results = getattr(app.state, "drive_mvp_results", {})
    result = results.get(key) if isinstance(results, dict) and key else None
    return result if isinstance(result, dict) else None


def _artifact(instance: Any, name: str) -> Path:
    try:
        return Path(instance.artifact(name)).resolve()
    except Exception:
        return (Path(instance.instance_root) / "staging" / name).resolve()


def _item(state: str, label: str, detail: str) -> dict[str, str]:
    return {"state": state, "label": label, "detail": detail}


def _check(label: str, state: str, detail: str) -> dict[str, str]:
    return {"label": label, "state": state, "detail": detail}


def _flow(actor: str, label: str, detail: str) -> dict[str, str]:
    return {"actor": actor, "label": label, "detail": detail}


def _step(label: str, state: str, detail: str) -> dict[str, str]:
    return {"label": label, "state": state, "detail": detail}


def _steps(result: Mapping[str, object]) -> list[dict[str, str]]:
    steps = result.get("steps")
    if not isinstance(steps, list):
        return []
    return [_step(_safe(item.get("label"), "Etape"), _state_text(item.get("state")), _safe(item.get("detail"), "")) for item in steps if isinstance(item, Mapping)]


def _state(status: str) -> str:
    return {"published": "Publication test terminee", "recovered": "Recuperation test terminee", "idle": "Aucune nouvelle version"}.get(status, "Bloque")


def _state_text(value: object) -> str:
    return {"ok": "OK", "waiting": "A lancer", "blocked": "Bloque"}.get(str(value or ""), "A lancer")


def _safe(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").split())
    forbidden = ("token", "secret", "oauth", "drive.file", "c:\\", "\\", "@", "raw", "private")
    return fallback if not text or any(marker in text.lower() for marker in forbidden) else text[:160]
