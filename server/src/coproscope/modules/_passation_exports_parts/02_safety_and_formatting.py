from __future__ import annotations



def _assert_export_safe(value: object) -> None:
    for path, item in _walk(value):
        if path.rsplit(".", 1)[-1] in _FORBIDDEN_KEYS:
            raise ValueError(f"Forbidden export field: {path}")
        if isinstance(item, str):
            lowered = item.lower()
            if _looks_like_private_path(item) or "file://" in lowered or "c:\\users\\" in lowered:
                raise ValueError(f"Private path leaked in export: {path}")
            if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", item):
                raise ValueError(f"Private email-like data leaked in export: {path}")
            if re.search(r"\brestricted\b", item, re.IGNORECASE):
                raise ValueError(f"Restricted marker leaked in export: {path}")


def _walk(value: object, path: str = "document") -> Iterable[tuple[str, object]]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _cell(key)
            yield f"{path}.{key_text}", item
            yield from _walk(item, f"{path}.{key_text}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            yield f"{path}[{index}]", item
            yield from _walk(item, f"{path}[{index}]")


def _max_restriction(records: Iterable[object]) -> str:
    order = {
        agcontentieux.RESTRICTION_INTERNAL: 0,
        agcontentieux.RESTRICTION_RESTRICTED: 1,
        agcontentieux.RESTRICTION_CONFIDENTIAL: 2,
    }
    values = [_field(record, "restriction", agcontentieux.RESTRICTION_INTERNAL) for record in records]
    if not values:
        return agcontentieux.RESTRICTION_INTERNAL
    return max(values, key=lambda item: order.get(item, 0))


def _min_diffusion(records: Iterable[object]) -> str:
    order = {
        agcontentieux.DIFFUSION_PUBLIC_AFTER_REDACTION: 0,
        agcontentieux.DIFFUSION_COPRO: 1,
        agcontentieux.DIFFUSION_CS: 2,
    }
    values = [_field(record, "diffusion", agcontentieux.DIFFUSION_CS) for record in records]
    if not values:
        return agcontentieux.DIFFUSION_CS
    return max(values, key=lambda item: order.get(item, 2))


def _restriction_label(value: object) -> str:
    labels = {
        agcontentieux.RESTRICTION_INTERNAL: "interne",
        agcontentieux.RESTRICTION_RESTRICTED: "restreint",
        agcontentieux.RESTRICTION_CONFIDENTIAL: "confidentiel",
    }
    return labels.get(_cell(value), _sanitize_text(value))


def _diffusion_label(value: object) -> str:
    labels = {
        agcontentieux.DIFFUSION_CS: "conseil_syndical",
        agcontentieux.DIFFUSION_COPRO: "coproprietaires",
        agcontentieux.DIFFUSION_PUBLIC_AFTER_REDACTION: "public_apres_expurgation",
    }
    return labels.get(_cell(value), _sanitize_text(value))


def _visibility_label(value: object) -> str:
    labels = {
        requestops.VISIBILITY_COPRO: "interne_copropriete",
        requestops.VISIBILITY_CS: "conseil_syndical",
        requestops.VISIBILITY_RESTRICTED: "restreint",
    }
    return labels.get(_cell(value), _sanitize_text(value))


def _visibility_diffusion_label(value: object) -> str:
    labels = {
        requestops.VISIBILITY_COPRO: "coproprietaires",
        requestops.VISIBILITY_CS: "conseil_syndical",
        requestops.VISIBILITY_RESTRICTED: "non_exporte",
    }
    return labels.get(_cell(value), "conseil_syndical")


def _generated_at(value: datetime | str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if isinstance(value, datetime):
        item = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return item.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    return _sanitize_text(value)


def _date_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return _sanitize_text(value)


def _without_empty(data: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value not in ("", None, [], {}, ())}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _as_sequence(value: object) -> list[object]:
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _cell(value: object) -> str:
    if value is None:
        return ""
    if is_dataclass(value):
        return json.dumps(asdict(value), ensure_ascii=True, sort_keys=True)
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    return str(value).strip()


def _md(value: object) -> str:
    return _sanitize_text(value).replace("|", "\\|")


def _inline_refs(value: object) -> str:
    refs = _clean_refs(value)
    return ", ".join(f"`{_md(ref)}`" for ref in refs) if refs else "_aucune_"


def _append_cards(lines: list[str], title: str, cards: object, label_field: str) -> None:
    items = [_mapping(item) for item in _sequence(cards)]
    if not items:
        return
    lines.extend([f"## {title}", ""])
    for item in items:
        label = item.get(label_field) or item.get("object_id") or item.get("object_type")
        lines.append(f"- `{_md(item.get('object_id'))}` {_md(label)}")
        if item.get("status") or item.get("restriction") or item.get("diffusion"):
            lines.append(
                f"  - statut `{_md(item.get('status'))}`, restriction `{_md(item.get('restriction'))}`, diffusion `{_md(item.get('diffusion'))}`"
            )
        if item.get("source_refs") or item.get("proof_refs"):
            lines.append(f"  - sources {_inline_refs(item.get('source_refs'))}; preuves {_inline_refs(item.get('proof_refs'))}")
        if item.get("next_action"):
            lines.append(f"  - prochaine action: {_md(item.get('next_action'))}")
    lines.append("")
