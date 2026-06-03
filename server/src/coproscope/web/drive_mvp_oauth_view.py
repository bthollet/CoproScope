from __future__ import annotations

from typing import Any, Mapping

from coproscope.modules import drive_oauth_service, drive_ui_state


def runtime_with_google_connection(
    app: Any,
    instance: Any,
    runtime: Mapping[str, object] | None = None,
) -> dict[str, object]:
    merged = dict(runtime or drive_ui_state.inspect_drive_ui_state(instance))
    service = getattr(app.state, "drive_oauth_service", None)
    config = drive_ui_state.resolve_drive_ui_config(instance)
    if isinstance(service, drive_oauth_service.DriveOAuthService) and service.matches(
        client_secrets_path=config.client_secrets_path,
        token_path=config.token_path,
    ):
        snapshot = service.snapshot()
    else:
        connected = str(merged.get("oauth", {}).get("status") if isinstance(merged.get("oauth"), Mapping) else "") == "ready"
        snapshot = drive_oauth_service.idle_snapshot(connected)
    merged["google_connection"] = snapshot
    merged["oauth_connect"] = _oauth_connect_control(merged, snapshot)
    return merged


def ensure_oauth_service(app: Any, instance: Any) -> drive_oauth_service.DriveOAuthService:
    config = drive_ui_state.resolve_drive_ui_config(instance)
    service = getattr(app.state, "drive_oauth_service", None)
    if isinstance(service, drive_oauth_service.DriveOAuthService) and service.matches(
        client_secrets_path=config.client_secrets_path,
        token_path=config.token_path,
    ):
        return service
    flow_runner = getattr(app.state, "drive_oauth_flow", None)
    service = drive_oauth_service.DriveOAuthService(
        client_secrets_path=config.client_secrets_path,
        token_path=config.token_path,
        flow_runner=flow_runner,
    )
    app.state.drive_oauth_service = service
    return service


def google_connection_config_blocked(runtime: Mapping[str, object]) -> dict[str, object]:
    control = runtime.get("oauth_connect") if isinstance(runtime.get("oauth_connect"), Mapping) else {}
    return drive_oauth_service.blocked_snapshot(_safe(control.get("help"), "Preparez ce poste avant de connecter Google."))


def google_connect_panel(result: Mapping[str, object]) -> dict[str, object]:
    status = str(result.get("status") or "blocked")
    ok = status == "ready"
    working = status == "working"
    return {
        "tone": "ready" if ok else ("review" if working else "error"),
        "source": "google-connect",
        "state": _google_state(status),
        "title": "Connexion Google",
        "summary": _safe(result.get("summary"), "Connexion Google a reprendre."),
        "result_label": _safe(result.get("result_label"), "Action requise"),
        "share_label": _safe(result.get("share_label"), "Aucun envoi Drive lance."),
        "publish_href": "/coffre/drive/publier-test",
        "recover_href": "/coffre/drive/recuperer-test",
        "publish_label": "Tester la preparation",
        "recover_label": "Tester la recuperation",
        "steps": _steps(result),
    }


def _oauth_connect_control(runtime: Mapping[str, object], snapshot: Mapping[str, object]) -> dict[str, object]:
    base = runtime.get("oauth_connect") if isinstance(runtime.get("oauth_connect"), Mapping) else {}
    status = str(snapshot.get("status") or "")
    if status == "working":
        return {
            "enabled": False,
            "href": str(base.get("href") or "/coffre/drive/connecter-google"),
            "label": "Connexion en cours",
            "help": "Suivez la fenetre Google, puis revenez ici.",
        }
    if status == "ready":
        return {
            "enabled": False,
            "href": str(base.get("href") or "/coffre/drive/connecter-google"),
            "label": "Google connecte",
            "help": "Google est connecte pour ce poste.",
        }
    if status == "blocked":
        return {
            "enabled": True,
            "href": str(base.get("href") or "/coffre/drive/connecter-google"),
            "label": "Reessayer Google",
            "help": _safe(snapshot.get("summary"), "Connexion Google a reprendre."),
        }
    return dict(base)


def _google_state(status: str) -> str:
    return {
        "ready": "Connecte",
        "working": "Connexion en cours",
        "idle": "Non connecte",
    }.get(status, "Action requise")


def _steps(result: Mapping[str, object]) -> list[dict[str, str]]:
    steps = result.get("steps")
    if not isinstance(steps, list):
        return []
    return [_step(_safe(item.get("label"), "Etape"), _state_text(item.get("state")), _safe(item.get("detail"), "")) for item in steps if isinstance(item, Mapping)]


def _step(label: str, state: str, detail: str) -> dict[str, str]:
    return {"label": label, "state": state, "detail": detail}


def _state_text(value: object) -> str:
    text = str(value or "").lower()
    if text in {"ok", "connecte"}:
        return "OK"
    if text in {"en cours", "working"}:
        return "En cours"
    if text in {"bloque", "blocked"}:
        return "Bloque"
    return "A lancer"


def _safe(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").split())
    forbidden = ("token", "secret", "oauth", "drive.file", "client_", "c:\\", "\\", "@", "raw", "private", "traceback")
    return fallback if not text or any(marker in text.lower() for marker in forbidden) else text[:160]
