from __future__ import annotations

import threading
from typing import Callable, Mapping


WatchCallback = Callable[[], Mapping[str, object]]


class DriveWatchService:
    def __init__(self, watch_once: WatchCallback, *, interval_seconds: float = 30.0) -> None:
        self._watch_once = watch_once
        self._interval_seconds = _safe_interval(interval_seconds)
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._status = "stopped"
        self._cycles_completed = 0
        self._last_result: dict[str, object] = {}

    def start(self) -> dict[str, object]:
        with self._lock:
            if self._is_running_locked():
                return self._snapshot_locked(summary="Surveillance automatique deja active.")
            self._stop.clear()
            self._status = "running"
            self._thread = threading.Thread(target=self._run, name="coproscope-drive-watch", daemon=True)
            self._thread.start()
            return self._snapshot_locked(summary="Surveillance automatique active.")

    def stop(self) -> dict[str, object]:
        thread: threading.Thread | None
        with self._lock:
            thread = self._thread
            self._stop.set()
        if thread and thread.is_alive():
            thread.join(timeout=2.0)
        with self._lock:
            if not self._is_running_locked() and self._status != "blocked":
                self._status = "stopped"
            return self._snapshot_locked(summary="Surveillance automatique arretee.")

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return self._snapshot_locked()

    def _run(self) -> None:
        while not self._stop.is_set():
            with self._lock:
                self._status = "working"
            result = self._call_once()
            result_status = str(result.get("status") or "blocked")
            with self._lock:
                self._cycles_completed += 1
                self._last_result = dict(result)
                self._status = "blocked" if result_status == "blocked" else "running"
            if result_status == "blocked":
                break
            if self._stop.wait(self._interval_seconds):
                break
        with self._lock:
            if self._stop.is_set() and self._status != "blocked":
                self._status = "stopped"

    def _call_once(self) -> dict[str, object]:
        try:
            result = self._watch_once()
        except Exception:
            return {
                "status": "blocked",
                "summary": "Surveillance arretee: controle a reprendre.",
                "result_label": "Surveillance bloquee",
                "share_label": "Aucun detail technique n'est affiche.",
            }
        return _safe_result(result)

    def _is_running_locked(self) -> bool:
        return bool(self._thread and self._thread.is_alive() and self._status != "blocked")

    def _snapshot_locked(self, *, summary: str | None = None) -> dict[str, object]:
        running = self._is_running_locked()
        last_status = str(self._last_result.get("status") or "")
        status = "running" if running and self._status != "working" else self._status
        return {
            "action": "watch-service",
            "status": status,
            "running": running,
            "cycles_completed": self._cycles_completed,
            "last_status": last_status,
            "summary": summary or _summary(status, last_status),
            "result_label": _label(status, last_status),
            "share_label": _safe_text(self._last_result.get("share_label"), "Affichage limite a ce poste."),
            "last_summary": _safe_text(self._last_result.get("summary"), ""),
            "payload_disclosure": "not_returned",
            "path_disclosure": "none",
        }


def stopped_snapshot() -> dict[str, object]:
    return {
        "action": "watch-service",
        "status": "stopped",
        "running": False,
        "cycles_completed": 0,
        "last_status": "",
        "summary": "Surveillance automatique arretee.",
        "result_label": "Surveillance arretee",
        "share_label": "Affichage limite a ce poste.",
        "last_summary": "",
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def blocked_snapshot(summary: str) -> dict[str, object]:
    return {
        "action": "watch-service",
        "status": "blocked",
        "running": False,
        "cycles_completed": 0,
        "last_status": "blocked",
        "summary": _safe_text(summary, "Surveillance a configurer."),
        "result_label": "Surveillance a configurer",
        "share_label": "Affichage limite a ce poste.",
        "last_summary": "",
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _safe_interval(value: float) -> float:
    try:
        interval = float(value)
    except (TypeError, ValueError):
        return 30.0
    if interval < 0.1:
        return 0.1
    return min(interval, 3600.0)


def _safe_result(result: Mapping[str, object]) -> dict[str, object]:
    status = str(result.get("status") or "blocked")
    return {
        "status": status if status in {"idle", "synced", "blocked"} else "blocked",
        "summary": _safe_text(result.get("summary"), "Passage termine."),
        "result_label": _safe_text(result.get("result_label"), "Surveillance terminee"),
        "share_label": _safe_text(result.get("share_label"), "Affichage limite a ce poste."),
    }


def _summary(status: str, last_status: str) -> str:
    if status == "working":
        return "Surveillance automatique en cours."
    if status == "running":
        return "Surveillance automatique active."
    if status == "blocked":
        return "Surveillance arretee: action a verifier."
    if last_status:
        return "Surveillance automatique arretee."
    return "Surveillance automatique arretee."


def _label(status: str, last_status: str) -> str:
    if status == "working":
        return "Controle en cours"
    if status == "running":
        return "Surveillance active"
    if status == "blocked":
        return "A verifier"
    if last_status == "blocked":
        return "A verifier"
    return "Surveillance arretee"


def _safe_text(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").split())
    forbidden = ("token", "secret", "oauth", "drive.file", "c:\\", "\\", "@", "raw", "private")
    return fallback if not text or any(marker in text.lower() for marker in forbidden) else text[:180]
