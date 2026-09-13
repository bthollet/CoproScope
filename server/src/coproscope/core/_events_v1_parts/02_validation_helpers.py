from __future__ import annotations



def _safe_text(value: object) -> str:
    text = _cell(value)
    if not text:
        return ""
    if _contains_unsafe_detail(text):
        return ""
    return text


def _safe_ref(value: object) -> str:
    text = _cell(value)
    if not text or _contains_unsafe_detail(text) or not _SAFE_REF_RE.match(text):
        return ""
    return text


def _safe_refs(values: object) -> tuple[str, ...]:
    refs: list[str] = []
    for value in _as_sequence(values):
        ref = _safe_ref(value)
        if ref and ref not in refs:
            refs.append(ref)
    return tuple(refs)


def _split_refs(value: object) -> tuple[str, ...]:
    text = _cell(value)
    if not text:
        return ()
    return tuple(item.strip() for item in re.split(r"[;,|]", text) if item.strip())


def _first_text(data: Mapping[str, object], fields: Iterable[str]) -> str:
    for field_name in fields:
        value = _cell(data.get(field_name))
        if value:
            return value
    return ""


def _hash_suffix(value: object) -> str:
    text = _safe_hash(value)
    return text[7:19] if text else stable_hash(_cell(value))[7:19]


def _without_empty(data: Mapping[str, object]) -> dict[str, object]:
    return {key: value for key, value in data.items() if value not in ("", None, (), [], {})}


def _as_sequence(value: object) -> Sequence[object]:
    if value is None or value == "":
        return ()
    if isinstance(value, (list, tuple, set)):
        return tuple(value)
    return (value,)


def _is_sensitive_key(key: str) -> bool:
    normalized = _token(key)
    return any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS)


def _looks_like_path_key(key: str) -> bool:
    normalized = _token(key)
    return normalized in _PATH_KEY_MARKERS or normalized.endswith("_path") or normalized.endswith("_paths")


def _contains_unsafe_detail(value: str) -> bool:
    text = _cell(value)
    if not text:
        return False
    lowered = text.lower()
    normalized = lowered.replace("/", "\\")
    if _WINDOWS_DRIVE_RE.match(text) or _UNIX_ABSOLUTE_RE.match(text):
        return True
    if text.startswith("\\\\") or "\\" in text:
        return True
    if any(marker in lowered for marker in _UNSAFE_VALUE_MARKERS):
        return True
    if re.search(r"(?<![a-z0-9])raw(?![a-z0-9])", lowered):
        return True
    if re.search(r"(?<![a-z0-9])restricted(?![a-z0-9])", lowered):
        return True
    if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text):
        return True
    if _contains_phone_like_detail(text):
        return True
    if "secret" in normalized or "token=" in normalized or "password=" in normalized:
        return True
    return False


def _token(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _cell(value).lower()).strip("_")


def _contains_phone_like_detail(value: str) -> bool:
    for match in re.finditer(r"(?<!\d)(?:\+?\d[\d .-]{7,}\d)(?!\d)", value):
        text = match.group(0)
        digits = re.sub(r"\D+", "", text)
        if len(digits) < 10:
            continue
        if text.startswith("+") or re.search(r"\d[ .]\d", text):
            return True
        if text.startswith("0") and "-" not in text and len(digits) <= 12:
            return True
    return False


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    if is_dataclass(value):
        return json.dumps(asdict(value), ensure_ascii=True, sort_keys=True)
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(_canonical_value(value), ensure_ascii=True, sort_keys=True)
    return str(value).strip()
