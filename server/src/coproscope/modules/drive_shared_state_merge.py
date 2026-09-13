from __future__ import annotations

from copy import deepcopy
from typing import Mapping


_MISSING = object()


def merge_shared_state(
    *,
    base: Mapping[str, object],
    local: Mapping[str, object],
    remote: Mapping[str, object],
) -> dict[str, object]:
    base_map = dict(base)
    local_map = dict(local)
    remote_map = dict(remote)
    local_changes = _changes(base_map, local_map)
    remote_changes = _changes(base_map, remote_map)
    conflicts = _overlaps(set(local_changes), set(remote_changes))
    if not local_changes or not remote_changes:
        return _conflict("insufficient_visible_delta", [])
    if conflicts:
        return _conflict("overlapping_shared_state_paths", conflicts)

    merged = deepcopy(base_map)
    _apply_changes(merged, remote_changes)
    _apply_changes(merged, local_changes)
    return {
        "status": "merged",
        "policy": "disjoint_shared_state_paths",
        "local_changed_path_count": len(local_changes),
        "remote_changed_path_count": len(remote_changes),
        "merged_state": merged,
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }


def _changes(base: Mapping[str, object], current: Mapping[str, object]) -> dict[tuple[str, ...], object]:
    base_flat = _flatten(base)
    current_flat = _flatten(current)
    changes: dict[tuple[str, ...], object] = {}
    for path in sorted(set(base_flat) | set(current_flat)):
        old = base_flat.get(path, _MISSING)
        new = current_flat.get(path, _MISSING)
        if old != new:
            changes[path] = new
    return changes


def _flatten(value: object, prefix: tuple[str, ...] = ()) -> dict[tuple[str, ...], object]:
    if isinstance(value, Mapping):
        if not value and prefix:
            return {prefix: {}}
        items: dict[tuple[str, ...], object] = {}
        for key, child in sorted(value.items(), key=lambda item: str(item[0])):
            items.update(_flatten(child, (*prefix, str(key))))
        return items
    return {prefix: value}


def _overlaps(local_paths: set[tuple[str, ...]], remote_paths: set[tuple[str, ...]]) -> list[dict[str, object]]:
    conflicts: list[dict[str, object]] = []
    for local in sorted(local_paths):
        for remote in sorted(remote_paths):
            if _same_or_parent(local, remote):
                conflicts.append({"local_depth": len(local), "remote_depth": len(remote)})
    return conflicts


def _same_or_parent(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    limit = min(len(left), len(right))
    return left[:limit] == right[:limit]


def _apply_changes(target: dict[str, object], changes: Mapping[tuple[str, ...], object]) -> None:
    for path, value in sorted(changes.items(), key=lambda item: (len(item[0]), item[0])):
        if not path:
            continue
        if value is _MISSING:
            _delete_path(target, path)
        else:
            _set_path(target, path, deepcopy(value))


def _set_path(target: dict[str, object], path: tuple[str, ...], value: object) -> None:
    cursor: dict[str, object] = target
    for part in path[:-1]:
        child = cursor.get(part)
        if not isinstance(child, dict):
            child = {}
            cursor[part] = child
        cursor = child
    cursor[path[-1]] = value


def _delete_path(target: dict[str, object], path: tuple[str, ...]) -> None:
    cursor: dict[str, object] = target
    for part in path[:-1]:
        child = cursor.get(part)
        if not isinstance(child, dict):
            return
        cursor = child
    cursor.pop(path[-1], None)


def _conflict(reason: str, overlaps: list[dict[str, object]]) -> dict[str, object]:
    return {
        "status": "conflict",
        "reason": reason,
        "overlap_count": len(overlaps),
        "overlaps": overlaps[:20],
        "payload_disclosure": "not_returned",
        "path_disclosure": "none",
    }
