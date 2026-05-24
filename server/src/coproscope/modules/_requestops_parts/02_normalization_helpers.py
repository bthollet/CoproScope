from __future__ import annotations



def _normalize_channel(value: str) -> str:
    text = _token(value)
    aliases = {
        "courriel": CHANNEL_EMAIL,
        "mail": CHANNEL_EMAIL,
        "email": CHANNEL_EMAIL,
        "e_mail": CHANNEL_EMAIL,
        "oral": CHANNEL_ORAL,
        "telephone": CHANNEL_ORAL,
        "appel": CHANNEL_ORAL,
        "reunion": CHANNEL_ORAL,
        "courrier": CHANNEL_COURRIER,
        "lettre": CHANNEL_COURRIER,
        "papier": CHANNEL_COURRIER,
        "ag": CHANNEL_AG,
        "assemblee_generale": CHANNEL_AG,
        "pv_ag": CHANNEL_AG,
        "portail": CHANNEL_PORTAIL_SYNDIC,
        "portail_syndic": CHANNEL_PORTAIL_SYNDIC,
        "extranet_syndic": CHANNEL_PORTAIL_SYNDIC,
        "document": CHANNEL_DOCOPS,
        "docops": CHANNEL_DOCOPS,
        "document_docops": CHANNEL_DOCOPS,
        "incident": CHANNEL_INCIDENT,
        "incidentops": CHANNEL_INCIDENT,
    }
    return aliases.get(text, text if text in REQUEST_CHANNELS else CHANNEL_ORAL)


def _normalize_status(value: str) -> str:
    text = _token(value)
    aliases = {
        "new": STATUS_NEW,
        "nouveau": STATUS_NEW,
        "nouvelle": STATUS_NEW,
        "open": STATUS_NEW,
        "a_traiter": STATUS_TO_QUALIFY,
        "a_qualifier": STATUS_TO_QUALIFY,
        "qualification": STATUS_TO_QUALIFY,
        "in_progress": STATUS_IN_PROGRESS,
        "en_cours": STATUS_IN_PROGRESS,
        "attente": STATUS_WAITING,
        "en_attente": STATUS_WAITING,
        "waiting": STATUS_WAITING,
        "relance": STATUS_FOLLOW_UP,
        "follow_up": STATUS_FOLLOW_UP,
        "closed": STATUS_CLOSED,
        "cloture": STATUS_CLOSED,
        "cloturee": STATUS_CLOSED,
        "done": STATUS_CLOSED,
        "sans_suite": STATUS_DISMISSED,
        "dismissed": STATUS_DISMISSED,
    }
    return aliases.get(text, text if text in REQUEST_STATUSES else STATUS_NEW)


def _normalize_visibility(value: str) -> str:
    text = _token(value)
    aliases = {
        "copro": VISIBILITY_COPRO,
        "copropriete": VISIBILITY_COPRO,
        "tous_coproprietaires": VISIBILITY_COPRO,
        "public": VISIBILITY_COPRO,
        "cs": VISIBILITY_CS,
        "conseil": VISIBILITY_CS,
        "conseil_syndical": VISIBILITY_CS,
        "board": VISIBILITY_CS,
        "restreint": VISIBILITY_RESTRICTED,
        "restricted": VISIBILITY_RESTRICTED,
        "confidentiel": VISIBILITY_RESTRICTED,
    }
    return aliases.get(text, text if text in VISIBILITIES else VISIBILITY_CS)


def _normalize_action_type(value: str) -> str:
    text = _token(value)
    aliases = {
        "note": "note",
        "qualification": "qualification",
        "relance": "relance",
        "follow_up": "relance",
        "reponse": "reponse",
        "answer": "reponse",
        "rattachement": "rattachement",
        "cloture": "cloture",
        "closure": "cloture",
    }
    return aliases.get(text, text or "note")


def _metadata(row: Mapping[str, Any], reserved: set[str]) -> dict[str, str]:
    normalized_reserved = {_token(field) for field in reserved}
    metadata: dict[str, str] = {}
    for key, value in row.items():
        key_text = _cell(key)
        value_text = _cell(value)
        token = _token(key_text)
        if not key_text or not value_text:
            continue
        if token in normalized_reserved or token in PRIVATE_FIELD_NAMES:
            continue
        metadata[key_text] = _privacy_safe_text(value_text)
    return metadata


def _first_text(row: Mapping[str, Any], fields: Iterable[str]) -> str:
    for field_name in fields:
        value = _cell(row.get(field_name))
        if value:
            return value
    return ""


def _require_fields(item: Any, field_names: Iterable[str]) -> None:
    missing = [field_name for field_name in field_names if not _cell(getattr(item, field_name, ""))]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def _stable_id(prefix: str, *parts: str) -> str:
    material = "|".join(_privacy_safe_text(part) for part in parts if _cell(part)) or prefix
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12].upper()
    readable = re.sub(r"[^A-Za-z0-9]+", "-", material).strip("-").upper()[:36]
    return f"{prefix}-{readable}-{digest}" if readable else f"{prefix}-{digest}"


def _flat_row(data: Mapping[str, Any], fields: Iterable[str]) -> dict[str, str]:
    return {field: _cell(data.get(field)) for field in fields}


def _without_empty(data: Mapping[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, Mapping):
            nested = _without_empty(value)
            if nested:
                cleaned[str(key)] = nested
        elif value not in ("", None, {}, [], ()):
            cleaned[str(key)] = value
    return cleaned


def _privacy_safe_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in data.items():
        token = _token(key)
        if token in PRIVATE_FIELD_NAMES:
            continue
        if isinstance(value, Mapping):
            safe[str(key)] = _privacy_safe_mapping(value)
        elif isinstance(value, (list, tuple)):
            safe[str(key)] = [_privacy_safe_text(item) for item in value]
        else:
            safe[str(key)] = _privacy_safe_text(value)
    return safe


def _privacy_safe_text(value: Any) -> str:
    text = _cell(value)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[redacted-email]", text)
    text = _PHONE_RE.sub(_redact_phone_match, text)
    return text


def _reject_private_data(data: Mapping[str, Any]) -> None:
    serialized = json.dumps(_private_scan_data(data), ensure_ascii=True, sort_keys=True)
    if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", serialized):
        raise ValueError("Private email-like data is not allowed in requestops")
    if any(_looks_like_phone(match.group(0)) for match in _PHONE_RE.finditer(serialized)):
        raise ValueError("Private phone-like data is not allowed in requestops")


_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .-]{7,}\d)(?!\d)")


def _private_scan_data(value: Any) -> Any:
    if isinstance(value, Mapping):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            token = _token(key)
            if token == "event_hash" or token.endswith("_hash") or token in {"hash", "sha256"}:
                continue
            cleaned[str(key)] = _private_scan_data(item)
        return cleaned
    if isinstance(value, (list, tuple, set)):
        return [_private_scan_data(item) for item in value]
    return value


def _redact_phone_match(match: re.Match[str]) -> str:
    return "[redacted-phone]" if _looks_like_phone(match.group(0)) else match.group(0)


def _looks_like_phone(value: str) -> bool:
    digits = re.sub(r"\D+", "", value)
    return len(digits) >= 10


def _token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _cell(value).lower()).strip("_")


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True, ensure_ascii=True)
    return str(value).strip()
