from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from . import drive_watch


def watch_loop(
    *,
    instance: Any,
    drive_service: Any,
    folder_id: str,
    sync_root: str | Path,
    local_state_root: str | Path,
    local_change_marker: str | None = None,
    local_change_marker_factory: Callable[[int], str | None] | None = None,
    interval_seconds: float = 15.0,
    max_cycles: int | None = None,
    sleep: Callable[[float], None] = time.sleep,
    media_factory: Callable[[Path], object] | None = None,
    media_downloader_factory: Callable[[Any], bytes] | None = None,
) -> dict[str, object]:
    interval = _safe_interval(interval_seconds)
    cycles_limit = _safe_cycles(max_cycles)
    cycles: list[dict[str, object]] = []
    counts = {"synced": 0, "idle": 0, "blocked": 0}
    index = 0

    while cycles_limit is None or index < cycles_limit:
        marker = local_change_marker_factory(index) if local_change_marker_factory else local_change_marker
        result = drive_watch.watch_once(
            instance=instance,
            drive_service=drive_service,
            folder_id=folder_id,
            sync_root=sync_root,
            local_state_root=local_state_root,
            local_change_marker=marker,
            media_factory=media_factory,
            media_downloader_factory=media_downloader_factory,
        )
        status = str(result.get("status") or "blocked")
        counts[status if status in counts else "blocked"] += 1
        cycles.append(_cycle(index, result))
        index += 1
        if status == "blocked":
            break
        if cycles_limit is not None and index >= cycles_limit:
            break
        if interval:
            sleep(interval)

    final_status = "blocked" if counts["blocked"] else "completed"
    return {
        "status": final_status,
        "action": "watch-loop",
        "summary": "Surveillance Drive arretee sur blocage" if final_status == "blocked" else "Surveillance Drive terminee",
        "cycles_requested": cycles_limit if cycles_limit is not None else "until_stopped",
        "cycles_completed": len(cycles),
        "counts": counts,
        "cycles": cycles,
        "drive": {"folder_id_present": bool(folder_id), "id_disclosure": "redacted"},
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _cycle(index: int, result: dict[str, object]) -> dict[str, object]:
    inbound = result.get("inbound") if isinstance(result.get("inbound"), dict) else {}
    outbound = result.get("outbound") if isinstance(result.get("outbound"), dict) else {}
    changes = result.get("changes") if isinstance(result.get("changes"), dict) else {}
    return {
        "index": index,
        "status": str(result.get("status") or "blocked"),
        "remote_changed": bool(changes.get("remote")),
        "local_changed": bool(changes.get("local")),
        "applied": bool(inbound.get("applied")),
        "uploaded": bool(outbound.get("uploaded")),
    }


def _safe_interval(value: float) -> float:
    try:
        interval = float(value)
    except (TypeError, ValueError):
        raise ValueError("Drive watch interval must be a non-negative number.") from None
    if interval < 0:
        raise ValueError("Drive watch interval must be a non-negative number.")
    return min(interval, 3600.0)


def _safe_cycles(value: int | None) -> int | None:
    if value is None:
        return None
    try:
        cycles = int(value)
    except (TypeError, ValueError):
        raise ValueError("Drive watch cycles must be a positive integer.") from None
    if cycles < 1:
        raise ValueError("Drive watch cycles must be a positive integer.")
    return min(cycles, 10000)
