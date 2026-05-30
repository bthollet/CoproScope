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
        "title": "Drive n'est pas encore relie",
        "notice": "Ce poste seulement",
        "status": _page_status(),
        "folder_setup": folder,
        "instance_sync": panel,
        "next_steps": [
            _item("1", "Choisir le dossier Drive", "Aucun dossier Google reel n'est relie pour l'instant."),
            _item("2", "Verifier les droits Google", "CoproScope lira les droits Google avant tout envoi reel."),
            _item("3", "Tester la recuperation", "La verification restera locale avant tout branchement Drive reel."),
        ],
        "sync_status_bar": _status_bar(panel),
        "local_vs_drive": [
            {"label": "Reste sur ce poste", "items": ["Cle du coffre", "Documents lisibles", "Etat de cet ordinateur", "Cache temporaire"]},
            {"label": "Peut partir dans Drive", "items": ["Fichiers chiffres", "Liste minimale des versions", "Preuves de controle"]},
        ],
        "visible_limit": "Affichage limite a cet ordinateur.",
        "links": [{"label": "Retour coffre et partage", "href": "/coffre/partage"}],
        "shell_model": _shell_model(instance, year),
    }


def _folder_status() -> dict[str, object]:
    folder = drive_folder_status.inspect_drive_sync_folder(None)
    return {
        "state": "Aucun dossier choisi",
        "tone": "action",
        "title": "Dossier Drive",
        "subtitle": "Le dossier Google sera choisi plus tard.",
        "headline": str(folder["folder_label"]),
        "summary": "Aucun dossier Google reel n'est relie a ce poste.",
        "share_label": "Droits Google non lus",
        "share_detail": "Ils seront verifies par Google avant tout envoi reel.",
    }


def _panel(result: Mapping[str, object] | None) -> dict[str, object]:
    if not result:
        return {
            "tone": "idle",
            "state": "Pret a tester",
            "title": "Test sans envoi lisible",
            "summary": "Ces actions creent et relisent un fichier chiffre dans la zone de test locale.",
            "result_label": "Aucun test lance",
            "share_label": "Aucun dossier Drive reel n'est utilise",
            "publish_href": "/coffre/drive/publier-test",
            "recover_href": "/coffre/drive/recuperer-test",
            "publish_label": "Tester la preparation",
            "recover_label": "Tester la recuperation",
            "steps": [
                _step("Preparer", "A lancer", "Cree une version test chiffree."),
                _step("Stocker en test", "A lancer", "Utilise seulement la zone de test locale."),
                _step("Relire", "A lancer", "Verifie puis applique sur ce poste."),
            ],
        }
    status = str(result.get("status") or "blocked")
    return {
        "tone": "ready" if status in {"published", "recovered", "idle"} else "error",
        "state": _state(status),
        "title": "Test sans envoi lisible",
        "summary": _safe(result.get("summary"), "Action Drive terminee."),
        "result_label": _safe(result.get("result_label"), "Action Drive terminee"),
        "share_label": _safe(result.get("share_label"), "Partage Google non verifie par ce test"),
        "publish_href": "/coffre/drive/publier-test",
        "recover_href": "/coffre/drive/recuperer-test",
        "publish_label": "Tester la preparation",
        "recover_label": "Tester la recuperation",
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
                "Cet ordinateur prepare seulement des fichiers chiffres.",
                "La recuperation est verifiee localement.",
                "Partage Google non verifie par ce test.",
                "L'etat affiche est limite a cet ordinateur.",
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
                "La copie lisible reste sur cet ordinateur.",
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
            "Le test local peut etre lance sans envoi Google reel.",
            "Aucun document lisible ni cle du coffre n'est envoye dans Drive.",
        ],
    }


def _page_status() -> dict[str, str]:
    return {
        "tone": "review",
        "label": "A configurer",
        "summary": "Aucun dossier Google n'est relie. Vous pouvez tester le chiffrement sans envoyer de document lisible.",
        "source": "Controle local",
    }


def _shell_model(instance: Any, year: int) -> dict[str, object]:
    instance_id = str(getattr(instance, "instance_id", "local"))[:40]
    return {
        "instance": {"id": instance_id, "name": getattr(instance, "name", "CoproScope"), "year": year},
        "ux": {"shell": {"page_title": "Drive chiffre", "sharing_mode_label": "Drive a configurer", "sharing_mode_status": "Aucun envoi Google reel"}},
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


def _step(label: str, state: str, detail: str) -> dict[str, str]:
    return {"label": label, "state": state, "detail": detail}


def _steps(result: Mapping[str, object]) -> list[dict[str, str]]:
    steps = result.get("steps")
    if not isinstance(steps, list):
        return []
    return [_step(_safe(item.get("label"), "Etape"), _state_text(item.get("state")), _safe(item.get("detail"), "")) for item in steps if isinstance(item, Mapping)]


def _state(status: str) -> str:
    return {"published": "Preparation test terminee", "recovered": "Recuperation test terminee", "idle": "Aucune nouvelle version"}.get(status, "Bloque")


def _state_text(value: object) -> str:
    return {"ok": "OK", "waiting": "A lancer", "blocked": "Bloque"}.get(str(value or ""), "A lancer")


def _safe(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").split())
    forbidden = ("token", "secret", "oauth", "drive.file", "c:\\", "\\", "@", "raw", "private")
    return fallback if not text or any(marker in text.lower() for marker in forbidden) else text[:160]
