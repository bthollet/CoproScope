from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class CoproCoffre:
    coffre_id: str
    display_name: str
    instance_path: Path
    local_root: Path
    sync_root: Path
    role_hint: str | None = None
    last_opened_at: str | None = None
    keys_root: Path | None = None
    governance_scope: str | None = None


def normalize_coffre(raw: Mapping[str, Any] | str) -> CoproCoffre:
    """Normalize a coffre definition loaded from JSON-compatible data."""
    data = _load_mapping(raw)
    coffre_id = _required_text(data, "coffre_id")
    display_name = _required_text(data, "display_name")

    return CoproCoffre(
        coffre_id=coffre_id,
        display_name=display_name,
        instance_path=_normalize_path(_required_value(data, "instance_path"), "instance_path"),
        local_root=_normalize_path(_required_value(data, "local_root"), "local_root"),
        sync_root=_normalize_path(_required_value(data, "sync_root"), "sync_root"),
        role_hint=_optional_text(data, "role_hint"),
        last_opened_at=_optional_text(data, "last_opened_at"),
        keys_root=_optional_path(data, "keys_root"),
        governance_scope=_optional_text(data, "governance_scope"),
    )


def validate_coffre_isolation(raw_coffres: list[CoproCoffre | Mapping[str, Any] | str]) -> dict[str, Any]:
    """Return isolation risks when two coffres reuse the same protected root."""
    coffres = [_coerce_coffre(raw) for raw in raw_coffres]
    path_owners: dict[str, dict[str, str]] = {}
    seen_ids: dict[str, str] = {}
    seen_names: dict[str, str] = {}
    risks: list[dict[str, str]] = []

    for coffre in coffres:
        _append_identity_risks(coffre, seen_ids, seen_names, risks)
        for field_name, path in _protected_paths(coffre):
            key = _path_key(path)
            owner = path_owners.get(key)
            current = {"coffre_id": coffre.coffre_id, "field": field_name}
            if owner is None:
                path_owners[key] = current
                continue
            if owner["coffre_id"] == coffre.coffre_id and owner["field"] == field_name:
                continue
            risks.append(
                {
                    "risk": "shared_protected_path",
                    "path": str(path),
                    "first_coffre_id": owner["coffre_id"],
                    "first_field": owner["field"],
                    "second_coffre_id": coffre.coffre_id,
                    "second_field": field_name,
                }
            )

    risks.extend(_nested_path_risks(coffres))

    return {"ok": not risks, "coffres": coffres, "risks": risks}


def switch_context_summary(
    current: CoproCoffre | Mapping[str, Any] | str | None,
    target: CoproCoffre | Mapping[str, Any] | str,
    current_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe a coffre switch without carrying document, token, or role state."""
    target_coffre = _coerce_coffre(target)
    current_coffre = _coerce_coffre(current) if current is not None else None
    context_keys = set(current_context or {})
    sensitive_context = ["document_id", "access_token", "token", "role"]

    return {
        "from_coffre_id": current_coffre.coffre_id if current_coffre else None,
        "to_coffre_id": target_coffre.coffre_id,
        "display_name": target_coffre.display_name,
        "instance_path": str(target_coffre.instance_path),
        "local_root": str(target_coffre.local_root),
        "sync_root": str(target_coffre.sync_root),
        "keys_root": str(target_coffre.keys_root) if target_coffre.keys_root else None,
        "role_hint": target_coffre.role_hint,
        "governance_scope": target_coffre.governance_scope,
        "effective_document_id": None,
        "effective_access_token": None,
        "effective_role": None,
        "requires_document_selection": "document_id" in context_keys,
        "requires_reauthentication": bool({"access_token", "token"} & context_keys),
        "requires_role_confirmation": "role" in context_keys or target_coffre.role_hint is not None,
        "carried_context": {},
        "cleared_context": sensitive_context,
        "dropped_context_keys": [key for key in sensitive_context if key in context_keys],
    }


def _coerce_coffre(raw: CoproCoffre | Mapping[str, Any] | str) -> CoproCoffre:
    if isinstance(raw, CoproCoffre):
        return raw
    return normalize_coffre(raw)


def _load_mapping(raw: Mapping[str, Any] | str) -> Mapping[str, Any]:
    if isinstance(raw, str):
        loaded = json.loads(raw)
        if not isinstance(loaded, Mapping):
            raise ValueError("coffre JSON must decode to an object")
        return loaded
    if not isinstance(raw, Mapping):
        raise TypeError("coffre must be a mapping or JSON object string")
    return raw


def _required_value(data: Mapping[str, Any], field_name: str) -> Any:
    value = data.get(field_name)
    if value is None:
        raise ValueError(f"{field_name} is required")
    return value


def _required_text(data: Mapping[str, Any], field_name: str) -> str:
    value = _required_value(data, field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _optional_text(data: Mapping[str, Any], field_name: str) -> str | None:
    value = data.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided")
    stripped = value.strip()
    return stripped or None


def _optional_path(data: Mapping[str, Any], field_name: str) -> Path | None:
    value = data.get(field_name)
    if value is None:
        return None
    return _normalize_path(value, field_name)


def _normalize_path(value: Any, field_name: str) -> Path:
    if not isinstance(value, (str, os.PathLike)):
        raise ValueError(f"{field_name} must be a filesystem path")
    raw_path = Path(value).expanduser()
    if str(raw_path).strip() in {"", "."}:
        raise ValueError(f"{field_name} must not be empty or current directory")
    return raw_path.resolve(strict=False)


def _protected_paths(coffre: CoproCoffre) -> list[tuple[str, Path]]:
    paths = [
        ("instance_path", coffre.instance_path),
        ("local_root", coffre.local_root),
        ("sync_root", coffre.sync_root),
    ]
    if coffre.keys_root is not None:
        paths.append(("keys_root", coffre.keys_root))
    return paths


def _path_key(path: Path) -> str:
    return os.path.normcase(str(path.resolve(strict=False)))


def _append_identity_risks(
    coffre: CoproCoffre,
    seen_ids: dict[str, str],
    seen_names: dict[str, str],
    risks: list[dict[str, str]],
) -> None:
    coffre_key = coffre.coffre_id.casefold()
    first_id = seen_ids.get(coffre_key)
    if first_id is None:
        seen_ids[coffre_key] = coffre.coffre_id
    else:
        risks.append(
            {
                "risk": "duplicate_coffre_id",
                "coffre_id": coffre.coffre_id,
                "first_coffre_id": first_id,
                "second_coffre_id": coffre.coffre_id,
            }
        )

    name_key = " ".join(coffre.display_name.casefold().split())
    first_name_owner = seen_names.get(name_key)
    if first_name_owner is None:
        seen_names[name_key] = coffre.coffre_id
    else:
        risks.append(
            {
                "risk": "ambiguous_display_name",
                "display_name": coffre.display_name,
                "first_coffre_id": first_name_owner,
                "second_coffre_id": coffre.coffre_id,
            }
        )


def _nested_path_risks(coffres: list[CoproCoffre]) -> list[dict[str, str]]:
    entries: list[tuple[CoproCoffre, str, Path]] = []
    for coffre in coffres:
        entries.extend((coffre, field_name, path) for field_name, path in _protected_paths(coffre))

    risks: list[dict[str, str]] = []
    for index, (first_coffre, first_field, first_path) in enumerate(entries):
        for second_coffre, second_field, second_path in entries[index + 1 :]:
            if _path_key(first_path) == _path_key(second_path):
                continue
            if first_field == "instance_path" and second_field == "instance_path":
                continue
            first_entry = (first_coffre, first_field, first_path)
            second_entry = (second_coffre, second_field, second_path)
            if _is_relative_to(second_path, first_path):
                parent = first_entry
                child = second_entry
            elif _is_relative_to(first_path, second_path):
                parent = second_entry
                child = first_entry
            else:
                continue
            risks.append(
                {
                    "risk": "nested_protected_path",
                    "parent_path": str(parent[2]),
                    "parent_coffre_id": parent[0].coffre_id,
                    "parent_field": parent[1],
                    "child_path": str(child[2]),
                    "child_coffre_id": child[0].coffre_id,
                    "child_field": child[1],
                }
            )
    return risks


def _is_relative_to(path: Path, possible_parent: Path) -> bool:
    try:
        path.relative_to(possible_parent)
        return True
    except ValueError:
        return False
