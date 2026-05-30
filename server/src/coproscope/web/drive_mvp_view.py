from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode

from fastapi import Request

from coproscope.modules import drive_ui_state
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
        view = build_drive_mvp_view(instance, year, result, drive_ui_state.inspect_drive_ui_state(instance))
        return templates.TemplateResponse(
            request=request,
            name="drive_mvp.html",
            context=context(request, "drive_mvp", model=view["shell_model"], drive_mvp=view),
        )

    @app.post("/coffre/drive/synchroniser")
    async def drive_mvp_sync_now(request: Request):
        require_token(request)
        result = drive_ui_state.sync_now_from_instance(
            instance=instance,
            drive_service_factory=getattr(app.state, "drive_service_factory", None),
        )
        return _redirect(app, request, result)

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


def build_drive_mvp_view(
    instance: Any,
    year: int,
    result: Mapping[str, object] | None = None,
    runtime: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    runtime = dict(runtime or drive_ui_state.inspect_drive_ui_state(instance))
    folder = _folder_status(runtime)
    panel = _panel(result)
    return {
        "title": "Drive chiffre",
        "notice": "Ce poste seulement",
        "status": _page_status(runtime),
        "folder_setup": folder,
        "instance_sync": panel,
        "real_sync": runtime["real_sync"],
        "oauth": runtime["oauth"],
        "watch": runtime["watch"],
        "next_steps": _next_steps(runtime),
        "next_steps_label": _next_steps_label(runtime),
        "sync_status_bar": _status_bar(panel, runtime),
        "local_vs_drive": [
            {"label": "Reste ici", "items": ["Cle du coffre", "Documents lisibles", "Etat de cet ordinateur", "Cache temporaire"]},
            {"label": "Va dans Drive", "items": ["Paquets chiffres", "Empreintes de version", "Preuves de controle"]},
        ],
        "visible_limit": "Affichage limite a cet ordinateur.",
        "links": [{"label": "Retour coffre et partage", "href": "/coffre/partage"}],
        "shell_model": _shell_model(instance, year, runtime),
    }


def _folder_status(runtime: Mapping[str, object]) -> dict[str, object]:
    folder = runtime.get("folder") if isinstance(runtime.get("folder"), Mapping) else {}
    return {
        "state": str(folder.get("state") or "Aucun dossier choisi"),
        "tone": "action",
        "title": "Dossier Drive",
        "subtitle": "Le dossier Google sera choisi plus tard.",
        "headline": str(folder.get("headline") or "A preparer"),
        "summary": str(folder.get("summary") or "Aucun dossier Google reel n'est relie a ce poste."),
        "share_label": str(folder.get("share_label") or "Droits Google non lus"),
        "share_detail": str(folder.get("share_detail") or "Ils seront verifies avant tout envoi reel."),
    }


def _panel(result: Mapping[str, object] | None) -> dict[str, object]:
    if not result:
        return {
            "tone": "idle",
            "state": "Pret",
            "title": "Synchronisation de ce poste",
            "summary": "La synchronisation lit les paquets chiffres dans Drive, applique ce qui manque ici, puis envoie la version chiffree de ce poste.",
            "result_label": "Aucune action lancee",
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
        "tone": "ready" if status in {"published", "recovered", "idle", "synced"} else "error",
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


def _status_bar(panel: Mapping[str, object], runtime: Mapping[str, object]) -> dict[str, object]:
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
    runtime_state = str(runtime.get("bar_state") or "setup")
    real_sync = runtime.get("real_sync") if isinstance(runtime.get("real_sync"), Mapping) else {}
    icon = {"ok": "cloud", "error": "error", "working": "sync"}.get(runtime_state, "gear")
    label = {"ok": "Pret", "error": "Bloque", "working": "Synchronise"}.get(runtime_state, "A configurer")
    aria_label = {
        "ok": "Etat Drive pret sur ce poste, ouvrir les details",
        "error": "Etat Drive bloque sur ce poste, ouvrir les details",
        "working": "Synchronisation Drive en cours sur ce poste, ouvrir les details",
    }.get(runtime_state, "Etat Drive a configurer sur ce poste, ouvrir les details")
    return {
        "state": runtime_state,
        "icon": icon,
        "label": label,
        "summary": str(real_sync.get("help") or "Le vrai dossier Drive reste a choisir."),
        "aria_label": aria_label,
        "details": [
            str(real_sync.get("help") or "Aucun dossier Drive reel n'est choisi."),
            "La synchronisation reelle reste limitee a cet ordinateur dans cet affichage.",
            "Aucun document lisible ni cle du coffre n'est envoye dans Drive.",
        ],
    }


def _page_status(runtime: Mapping[str, object]) -> dict[str, str]:
    status = str(runtime.get("status") or "not_configured")
    if status == "ready":
        return {
            "tone": "ready",
            "label": "Pret",
            "summary": "Le dossier Drive chiffre et la connexion Google sont prets pour ce poste.",
            "source": "Controle local",
        }
    if status == "blocked":
        return {
            "tone": "risk",
            "label": "A verifier",
            "summary": "La configuration existe, mais la surface chiffree locale doit etre preparee.",
            "source": "Controle local",
        }
    if status == "action_required":
        return {
            "tone": "review",
            "label": "Connexion a faire",
            "summary": "Le dossier Drive est choisi, mais Google doit encore etre connecte avec l'autorisation minimale.",
            "source": "Controle local",
        }
    return {
        "tone": "review",
        "label": "A configurer",
        "summary": "Aucun dossier Google n'est relie. Le test prepare seulement des paquets chiffres.",
        "source": "Controle local",
    }


def _next_steps(runtime: Mapping[str, object]) -> list[dict[str, str]]:
    status = str(runtime.get("status") or "not_configured")
    if status == "ready":
        return [
            _item("1", "Synchroniser maintenant", "Lit Drive puis envoie seulement des paquets chiffres."),
            _item("2", "Laisser surveiller", "Le futur service relancera ce controle quand ce poste change."),
            _item("3", "Verifier les droits", "Google garde la gestion des personnes autorisees au dossier."),
        ]
    if status == "action_required":
        return [
            _item("1", "Connecter Google", "Autorisation limitee aux fichiers crees par CoproScope."),
            _item("2", "Relancer le controle", "Le bouton de synchronisation apparaitra quand ce poste sera pret."),
            _item("3", "Tester en local", "Les boutons de test restent disponibles sans envoi lisible."),
        ]
    if status == "blocked":
        return [
            _item("1", "Preparer le dossier local", "CoproScope a besoin d'une surface chiffree prete sur ce poste."),
            _item("2", "Verifier Google", "Le dossier Drive choisi reste masque dans l'interface."),
            _item("3", "Relancer la page", "Le bouton de synchronisation sera active apres controle."),
        ]
    return [
        _item("1", "Choisir le dossier Drive", "Aucun dossier Google reel n'est relie pour l'instant."),
        _item("2", "Connecter Google", "CoproScope demandera seulement l'autorisation minimale."),
        _item("3", "Tester en local", "La verification locale reste possible avant tout branchement Drive reel."),
    ]


def _next_steps_label(runtime: Mapping[str, object]) -> str:
    status = str(runtime.get("status") or "not_configured")
    return {
        "ready": "Drive pret",
        "action_required": "Connexion requise",
        "blocked": "A preparer ici",
    }.get(status, "Pas encore de Drive reel")


def _shell_model(instance: Any, year: int, runtime: Mapping[str, object]) -> dict[str, object]:
    instance_id = str(getattr(instance, "instance_id", "local"))[:40]
    status = _page_status(runtime)
    return {
        "instance": {"id": instance_id, "name": getattr(instance, "name", "CoproScope"), "year": year},
        "ux": {
            "shell": {
                "page_title": "Drive chiffre",
                "sharing_mode_label": f"Drive {status['label'].lower()}",
                "sharing_mode_status": str(status["summary"]),
            }
        },
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
    return {
        "published": "Preparation test terminee",
        "recovered": "Recuperation test terminee",
        "idle": "Aucune nouvelle version",
        "synced": "Synchronisation terminee",
    }.get(status, "Bloque")


def _state_text(value: object) -> str:
    return {"ok": "OK", "waiting": "A lancer", "blocked": "Bloque"}.get(str(value or ""), "A lancer")


def _safe(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").split())
    forbidden = ("token", "secret", "oauth", "drive.file", "c:\\", "\\", "@", "raw", "private")
    return fallback if not text or any(marker in text.lower() for marker in forbidden) else text[:160]
