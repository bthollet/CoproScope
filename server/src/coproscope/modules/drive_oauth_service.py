from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from . import gdriveops


FlowRunner = Callable[..., Mapping[str, object]]


class DriveOAuthService:
    def __init__(
        self,
        *,
        client_secrets_path: str | Path | None,
        token_path: str | Path | None,
        flow_runner: FlowRunner | None = None,
        scopes: Iterable[str] | None = None,
    ) -> None:
        self.client_secrets_path = Path(client_secrets_path) if client_secrets_path else gdriveops.default_client_secrets_path()
        self.token_path = Path(token_path) if token_path else gdriveops.default_token_path()
        self.flow_runner = flow_runner or gdriveops.run_oauth_flow
        self.scopes = tuple(gdriveops.normalize_scopes(scopes))
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._snapshot: dict[str, object] = idle_snapshot(self._connected())

    def matches(self, *, client_secrets_path: str | Path | None, token_path: str | Path | None) -> bool:
        client = Path(client_secrets_path) if client_secrets_path else gdriveops.default_client_secrets_path()
        token = Path(token_path) if token_path else gdriveops.default_token_path()
        return client == self.client_secrets_path and token == self.token_path

    def start(self) -> dict[str, object]:
        with self._lock:
            if self._connected():
                self._snapshot = ready_snapshot()
                return dict(self._snapshot)
            if not self.client_secrets_path.exists():
                self._snapshot = blocked_snapshot("Connexion Google non disponible dans cette version locale.")
                return dict(self._snapshot)
            if self._thread is not None and self._thread.is_alive():
                self._snapshot = working_snapshot()
                return dict(self._snapshot)
            self._snapshot = working_snapshot()
            self._thread = threading.Thread(target=self._run_flow, name="coproscope-drive-google-connect", daemon=True)
            self._thread.start()
            return dict(self._snapshot)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            if self._connected():
                self._snapshot = ready_snapshot()
            elif self._thread is not None and self._thread.is_alive():
                self._snapshot = working_snapshot()
            return dict(self._snapshot)

    def _run_flow(self) -> None:
        try:
            self.flow_runner(
                client_secrets_path=self.client_secrets_path,
                token_path=self.token_path,
                scopes=self.scopes,
                open_browser=True,
            )
            next_snapshot = ready_snapshot() if self._connected() else blocked_snapshot("Connexion Google interrompue. Reessayez depuis ce poste.")
        except Exception:
            next_snapshot = blocked_snapshot("Connexion Google interrompue. Reessayez depuis ce poste.")
        with self._lock:
            self._snapshot = next_snapshot

    def _connected(self) -> bool:
        status = gdriveops.oauth_status(
            client_secrets_path=self.client_secrets_path,
            token_path=self.token_path,
            scopes=self.scopes,
        )
        return status.get("status") == "ready"


def idle_snapshot(connected: bool = False) -> dict[str, object]:
    if connected:
        return ready_snapshot()
    return {
        "action": "google-connect",
        "status": "idle",
        "running": False,
        "summary": "Google n'est pas encore connecte sur ce poste.",
        "result_label": "Non connecte",
        "share_label": "Aucun envoi Drive lance.",
        "steps": _steps("A lancer"),
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def ready_snapshot() -> dict[str, object]:
    return {
        "action": "google-connect",
        "status": "ready",
        "running": False,
        "summary": "Google est connecte pour ce poste.",
        "result_label": "Connecte",
        "share_label": "Aucun document lisible n'a ete envoye.",
        "steps": _steps("OK"),
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def working_snapshot() -> dict[str, object]:
    return {
        "action": "google-connect",
        "status": "working",
        "running": True,
        "summary": "Connexion Google en cours. Suivez la fenetre Google, puis revenez ici.",
        "result_label": "Connexion en cours",
        "share_label": "Aucun envoi Drive lance pendant la connexion.",
        "steps": _steps("En cours"),
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def blocked_snapshot(summary: str) -> dict[str, object]:
    return {
        "action": "google-connect",
        "status": "blocked",
        "running": False,
        "summary": _safe(summary, "Connexion Google interrompue. Reessayez."),
        "result_label": "Action requise",
        "share_label": "Aucun envoi Drive lance.",
        "steps": _steps("Bloque"),
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _steps(state: str) -> list[dict[str, str]]:
    return [
        {"label": "Ouvrir Google", "state": state, "detail": "La connexion se fait dans le navigateur."},
        {"label": "Autoriser ce poste", "state": state, "detail": "CoproScope demandera seulement l'acces minimal."},
        {"label": "Revenir ici", "state": state, "detail": "L'etat sera relu sur cet ordinateur."},
    ]


def _safe(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").split())
    forbidden = ("token", "secret", "oauth", "drive.file", "client_", "c:\\", "\\", "@", "raw", "private", "traceback")
    return fallback if not text or any(marker in text.lower() for marker in forbidden) else text[:160]
