from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode

from fastapi import Request

from coproscope.modules import drive_key_transfer, drive_local_setup, drive_ui_state
from coproscope.modules.drive_instance_sync import publish_instance_update, recover_instance_update
from coproscope.web import drive_mvp_oauth_view, drive_mvp_watch_view


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
        runtime = drive_mvp_watch_view.runtime_with_watch_service(app, instance)
        view = build_drive_mvp_view(instance, year, result, drive_mvp_oauth_view.runtime_with_google_connection(app, instance, runtime))
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

    @app.post("/coffre/drive/surveiller")
    async def drive_mvp_watch_once(request: Request):
        require_token(request)
        result = drive_ui_state.watch_once_from_instance(
            instance=instance,
            drive_service_factory=getattr(app.state, "drive_service_factory", None),
        )
        return _redirect(app, request, result)

    @app.post("/coffre/drive/preparer-poste")
    async def drive_mvp_prepare_local(request: Request):
        require_token(request)
        result = drive_local_setup.prepare_drive_local_workspace(instance)
        return _redirect(app, request, result)

    @app.post("/coffre/drive/connecter-google")
    async def drive_mvp_connect_google(request: Request):
        require_token(request)
        runtime = drive_mvp_oauth_view.runtime_with_google_connection(
            app,
            instance,
            drive_mvp_watch_view.runtime_with_watch_service(app, instance),
        )
        control = runtime.get("oauth_connect") if isinstance(runtime.get("oauth_connect"), Mapping) else {}
        if not control.get("enabled"):
            result = drive_mvp_oauth_view.google_connection_config_blocked(runtime)
        else:
            result = drive_mvp_oauth_view.ensure_oauth_service(app, instance).start()
        return _redirect(app, request, result)

    @app.post("/coffre/drive/dossier-google/creer")
    async def drive_mvp_create_google_folder(request: Request):
        require_token(request)
        result = drive_ui_state.create_google_folder_from_instance(
            instance=instance,
            drive_service_factory=getattr(app.state, "drive_service_factory", None),
        )
        return _redirect(app, request, result)

    @app.post("/coffre/drive/surveillance/activer")
    async def drive_mvp_watch_service_start(request: Request):
        require_token(request)
        runtime = drive_ui_state.inspect_drive_ui_state(instance)
        if not runtime.get("can_sync"):
            return _redirect(app, request, drive_mvp_watch_view.watch_service_config_blocked(runtime))
        result = drive_mvp_watch_view.ensure_watch_service(app, instance).start()
        return _redirect(app, request, result)

    @app.post("/coffre/drive/surveillance/arreter")
    async def drive_mvp_watch_service_stop(request: Request):
        require_token(request)
        result = drive_mvp_watch_view.stop_watch_service(app)
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

    @app.post("/coffre/drive/code-acces")
    async def drive_mvp_key_export(request: Request):
        require_token(request)
        result = drive_key_transfer.create_sync_key_code(
            local_state_root=_artifact(instance, "drive_instance_sync_state"),
        )
        return _redirect(app, request, result)

    @app.post("/coffre/drive/importer-code")
    async def drive_mvp_key_import(request: Request):
        require_token(request)
        form = await request.form()
        result = drive_key_transfer.import_sync_key_code(
            local_state_root=_artifact(instance, "drive_instance_sync_state"),
            secret_code=str(form.get("secret_code") or ""),
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
        "local_setup": runtime["local_setup"],
        "oauth_connect": runtime["oauth_connect"],
        "google_folder": runtime["google_folder"],
        "watch_control": runtime["watch_control"],
        "watch_auto": drive_mvp_watch_view.watch_auto(runtime),
        "key_transfer": _key_transfer(result),
        "oauth": runtime["oauth"],
        "watch": runtime["watch"],
        "next_steps": _next_steps(runtime),
        "next_steps_label": _next_steps_label(runtime),
        "sync_status_bar": drive_mvp_watch_view.status_bar(panel, runtime),
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
    if not result or str(result.get("action") or "").startswith("key-"):
        return {
            "tone": "idle",
            "source": "manual",
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
    if str(result.get("action") or "") == "watch-once":
        return drive_mvp_watch_view.watch_panel(result)
    if str(result.get("action") or "") == "watch-service":
        return drive_mvp_watch_view.watch_service_panel(result)
    if str(result.get("action") or "") == "prepare-local":
        return _local_setup_panel(result)
    if str(result.get("action") or "") == "google-connect":
        return drive_mvp_oauth_view.google_connect_panel(result)
    if str(result.get("action") or "") == "google-folder":
        return _google_folder_panel(result)
    status = str(result.get("status") or "blocked")
    return {
        "tone": "ready" if status in {"published", "recovered", "idle", "synced"} else "error",
        "source": "sync-now" if str(result.get("action") or "") == "sync-now" else "manual",
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


def _local_setup_panel(result: Mapping[str, object]) -> dict[str, object]:
    return {
        "tone": "ready" if str(result.get("status") or "") == "prepared" else "error",
        "source": "local-setup",
        "state": _state(str(result.get("status") or "blocked")),
        "title": "Preparation locale de ce poste",
        "summary": _safe(result.get("summary"), "Preparation locale terminee."),
        "result_label": _safe(result.get("result_label"), "Poste prepare"),
        "share_label": _safe(result.get("share_label"), "Aucun envoi Drive."),
        "publish_href": "/coffre/drive/publier-test",
        "recover_href": "/coffre/drive/recuperer-test",
        "publish_label": "Tester la preparation",
        "recover_label": "Tester la recuperation",
        "steps": _steps(result),
    }


def _google_folder_panel(result: Mapping[str, object]) -> dict[str, object]:
    ready = str(result.get("status") or "") == "configured"
    return {
        "tone": "ready" if ready else "error",
        "source": "google-folder",
        "state": "Dossier Google pret" if ready else "Dossier Google bloque",
        "title": "Dossier Google chiffre",
        "summary": _safe(result.get("summary"), "Dossier Google non prepare."),
        "result_label": _safe(result.get("result_label"), "Dossier Google"),
        "share_label": _safe(result.get("share_label"), "Aucun identifiant Google n'est affiche."),
        "publish_href": "/coffre/drive/publier-test",
        "recover_href": "/coffre/drive/recuperer-test",
        "publish_label": "Tester la preparation",
        "recover_label": "Tester la recuperation",
        "steps": _steps(result),
    }


def _key_transfer(result: Mapping[str, object] | None) -> dict[str, object]:
    state = str(result.get("status") or "") if result else ""
    action = str(result.get("action") or "") if result else ""
    code = str(result.get("secret_code") or "") if action == "key-export" else ""
    if action == "key-import":
        imported = state == "imported"
        return {
            "title": "Code d'acces coffre",
            "summary": "Ce code sert seulement a autoriser ce coffre sur un nouvel ordinateur.",
            "export_href": "/coffre/drive/code-acces",
            "import_href": "/coffre/drive/importer-code",
            "export_label": "Creer un code",
            "import_label": "Importer le code",
            "status_label": "Code importe" if imported else "Code refuse",
            "status_tone": "ready" if imported else "error",
            "secret_code": "",
            "secret_help": "Le code n'est pas enregistre dans Drive.",
        }
    if code:
        return {
            "title": "Code d'acces coffre",
            "summary": "Copiez ce code seulement vers la personne ou l'ordinateur autorise.",
            "export_href": "/coffre/drive/code-acces",
            "import_href": "/coffre/drive/importer-code",
            "export_label": "Recreer un code",
            "import_label": "Importer le code",
            "status_label": "Code pret",
            "status_tone": "ready",
            "secret_code": code,
            "secret_help": "Ne placez pas ce code dans Drive: il ouvre le coffre chiffre.",
        }
    return {
        "title": "Code d'acces coffre",
        "summary": "Un nouvel ordinateur doit recevoir ce code en dehors de Drive pour lire les paquets chiffres.",
        "export_href": "/coffre/drive/code-acces",
        "import_href": "/coffre/drive/importer-code",
        "export_label": "Creer un code",
        "import_label": "Importer le code",
        "status_label": "Non cree",
        "status_tone": "idle",
        "secret_code": "",
        "secret_help": "Drive ne recoit jamais ce code.",
    }


def _page_status(runtime: Mapping[str, object]) -> dict[str, str]:
    status = str(runtime.get("status") or "not_configured")
    if status == "ready":
        return {
            "tone": "ready",
            "dot_state": "ok",
            "label": "Pret",
            "summary": "Le dossier Drive chiffre et la connexion Google sont prets pour ce poste.",
            "source": "Controle local",
        }
    if status == "blocked":
        return {
            "tone": "risk",
            "dot_state": "error",
            "label": "A verifier",
            "summary": "La configuration existe, mais la surface chiffree locale doit etre preparee.",
            "source": "Controle local",
        }
    if status == "action_required":
        return {
            "tone": "review",
            "dot_state": "setup",
            "label": "Connexion a faire",
            "summary": "Le dossier Drive est choisi, mais Google doit encore etre connecte avec l'autorisation minimale.",
            "source": "Controle local",
        }
    return {
        "tone": "review",
        "dot_state": "setup",
        "label": "A configurer",
        "summary": "Aucun dossier Google n'est relie. Le test prepare seulement des paquets chiffres.",
        "source": "Controle local",
    }


def _next_steps(runtime: Mapping[str, object]) -> list[dict[str, str]]:
    status = str(runtime.get("status") or "not_configured")
    if status == "ready":
        return [
            _item("1", "Synchroniser maintenant", "Lit Drive puis envoie seulement des paquets chiffres."),
            _item("2", "Activer la surveillance", "CoproScope relance le controle pendant que l'application est ouverte."),
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
        "prepared": "Poste prepare",
        "idle": "Aucune nouvelle version",
        "synced": "Synchronisation terminee",
    }.get(status, "Bloque")


def _state_text(value: object) -> str:
    return {"ok": "OK", "waiting": "A lancer", "blocked": "Bloque"}.get(str(value or "").lower(), "A lancer")


def _safe(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").split())
    forbidden = ("token", "secret", "oauth", "drive.file", "c:\\", "\\", "@", "raw", "private")
    return fallback if not text or any(marker in text.lower() for marker in forbidden) else text[:160]
