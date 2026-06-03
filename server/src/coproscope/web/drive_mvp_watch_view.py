from __future__ import annotations

from typing import Any, Mapping

from coproscope.modules import drive_ui_state
from coproscope.modules import drive_watch_service as watch_service_module


def runtime_with_watch_service(app: Any, instance: Any) -> dict[str, object]:
    runtime = dict(drive_ui_state.inspect_drive_ui_state(instance))
    service = getattr(app.state, "drive_watch_service", None)
    if isinstance(service, watch_service_module.DriveWatchService):
        runtime["watch_service"] = service.snapshot()
    else:
        runtime["watch_service"] = watch_service_module.stopped_snapshot()
    return runtime


def ensure_watch_service(app: Any, instance: Any) -> watch_service_module.DriveWatchService:
    service = getattr(app.state, "drive_watch_service", None)
    if isinstance(service, watch_service_module.DriveWatchService):
        return service

    def run_once() -> dict[str, object]:
        return drive_ui_state.watch_once_from_instance(
            instance=instance,
            drive_service_factory=getattr(app.state, "drive_service_factory", None),
        )

    interval = getattr(app.state, "drive_watch_interval_seconds", 30.0)
    service = watch_service_module.DriveWatchService(run_once, interval_seconds=float(interval))
    app.state.drive_watch_service = service
    return service


def stop_watch_service(app: Any) -> dict[str, object]:
    service = getattr(app.state, "drive_watch_service", None)
    if isinstance(service, watch_service_module.DriveWatchService):
        return service.stop()
    return watch_service_module.stopped_snapshot()


def watch_service_config_blocked(runtime: Mapping[str, object]) -> dict[str, object]:
    control = runtime.get("watch_control") if isinstance(runtime.get("watch_control"), Mapping) else {}
    return watch_service_module.blocked_snapshot(_safe(control.get("help"), "Surveillance a configurer."))


def watch_panel(result: Mapping[str, object]) -> dict[str, object]:
    status = str(result.get("status") or "blocked")
    return {
        "tone": "ready" if status in {"idle", "synced"} else "error",
        "source": "watch",
        "state": _watch_state(status),
        "title": "Surveillance de ce poste",
        "summary": _safe(result.get("summary"), "Passage de surveillance termine."),
        "result_label": _safe(result.get("result_label"), "Surveillance terminee"),
        "share_label": _safe(result.get("share_label"), "Affichage limite a ce poste."),
        "publish_href": "/coffre/drive/publier-test",
        "recover_href": "/coffre/drive/recuperer-test",
        "publish_label": "Tester la preparation",
        "recover_label": "Tester la recuperation",
        "steps": _steps(result),
    }


def watch_service_panel(result: Mapping[str, object]) -> dict[str, object]:
    status = str(result.get("status") or "stopped")
    ok = status in {"running", "working", "stopped"}
    return {
        "tone": "ready" if ok else "error",
        "source": "watch-service",
        "state": _watch_service_state(status),
        "title": "Surveillance automatique",
        "summary": _safe(result.get("summary"), "Surveillance automatique mise a jour."),
        "result_label": _safe(result.get("result_label"), "Surveillance automatique"),
        "share_label": _safe(result.get("share_label"), "Affichage limite a ce poste."),
        "publish_href": "/coffre/drive/publier-test",
        "recover_href": "/coffre/drive/recuperer-test",
        "publish_label": "Tester la preparation",
        "recover_label": "Tester la recuperation",
        "steps": [
            _step("Surveiller", _watch_service_state(status), _safe(result.get("last_summary"), "Controle regulier de ce poste.")),
        ],
    }


def status_bar(panel: Mapping[str, object], runtime: Mapping[str, object]) -> dict[str, object]:
    service = runtime.get("watch_service") if isinstance(runtime.get("watch_service"), Mapping) else {}
    if panel.get("source") == "watch-service":
        return _service_status_bar(panel)
    if service and str(service.get("status") or "") in {"running", "working", "blocked"}:
        return _service_status_bar(service)
    if panel.get("source") == "watch":
        ok = panel.get("tone") == "ready"
        return {
            "state": "ok" if ok else "error",
            "icon": "cloud" if ok else "error",
            "label": str(panel["state"]),
            "summary": str(panel["summary"]),
            "aria_label": "Etat de surveillance Drive sur ce poste, ouvrir les details",
            "details": [
                str(panel["result_label"]),
                str(panel["share_label"]),
                "L'etat affiche ne decrit que cet ordinateur.",
            ],
        }
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


def watch_auto(runtime: Mapping[str, object]) -> dict[str, object]:
    service = runtime.get("watch_service") if isinstance(runtime.get("watch_service"), Mapping) else {}
    status = str(service.get("status") or "stopped")
    running = bool(service.get("running"))
    can_sync = bool(runtime.get("can_sync"))
    return {
        "running": running,
        "enabled_start": can_sync and not running,
        "enabled_stop": running or status == "blocked",
        "start_href": "/coffre/drive/surveillance/activer",
        "stop_href": "/coffre/drive/surveillance/arreter",
        "start_label": "Activer la surveillance",
        "stop_label": "Arreter la surveillance",
        "status_label": _watch_service_state(status),
        "help": _watch_auto_help(can_sync, status, service),
        "cycles_completed": int(service.get("cycles_completed") or 0),
    }


def _service_status_bar(source: Mapping[str, object]) -> dict[str, object]:
    status = str(source.get("status") or "stopped")
    blocked = status == "blocked"
    working = status in {"running", "working"}
    return {
        "state": "error" if blocked else ("working" if working else "ok"),
        "icon": "error" if blocked else ("sync" if working else "cloud"),
        "label": _watch_service_state(status),
        "summary": _safe(source.get("summary"), "Surveillance automatique mise a jour."),
        "aria_label": "Etat de surveillance Drive sur ce poste, ouvrir les details",
        "details": [
            _safe(source.get("result_label"), "Surveillance automatique"),
            _safe(source.get("last_summary"), "Aucun detail supplementaire."),
            "L'etat affiche ne decrit que cet ordinateur.",
        ],
    }


def _watch_auto_help(can_sync: bool, status: str, service: Mapping[str, object]) -> str:
    if not can_sync:
        return "Disponible quand le dossier Drive chiffre et Google sont prets."
    if status in {"running", "working"}:
        return "CoproScope controle Drive regulierement pendant que l'application est ouverte."
    if status == "blocked":
        return _safe(service.get("summary"), "Surveillance arretee: action a verifier.")
    return "Controle Drive regulierement pendant que l'application est ouverte."


def _steps(result: Mapping[str, object]) -> list[dict[str, str]]:
    steps = result.get("steps")
    if not isinstance(steps, list):
        return []
    return [_step(_safe(item.get("label"), "Etape"), _state_text(item.get("state")), _safe(item.get("detail"), "")) for item in steps if isinstance(item, Mapping)]


def _step(label: str, state: str, detail: str) -> dict[str, str]:
    return {"label": label, "state": state, "detail": detail}


def _watch_state(status: str) -> str:
    return {
        "idle": "A jour",
        "synced": "Surveille",
    }.get(status, "A verifier")


def _watch_service_state(status: str) -> str:
    return {
        "running": "Surveille",
        "working": "Controle",
        "blocked": "A verifier",
        "stopped": "Arrete",
    }.get(status, "Arrete")


def _state_text(value: object) -> str:
    return {"ok": "OK", "waiting": "A lancer", "blocked": "Bloque"}.get(str(value or "").lower(), "A lancer")


def _safe(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").split())
    forbidden = ("token", "secret", "oauth", "drive.file", "c:\\", "\\", "@", "raw", "private")
    return fallback if not text or any(marker in text.lower() for marker in forbidden) else text[:160]
