from __future__ import annotations



def contains_unsafe_local_marker(value: str) -> bool:
    return any(pattern.search(value or "") for pattern in _UNSAFE_LOCAL_PATTERNS)


def validate_record(record: object) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for path, item in _walk_records(record):
        issues.extend(_validate_one(path, item))
    return tuple(issues)


def event_payload(record: object) -> dict[str, Any]:
    issues = validate_record(record)
    blocking = [issue for issue in issues if issue.severity == "error"]
    if blocking:
        details = "; ".join(f"{issue.field}: {issue.reason}" for issue in blocking)
        raise ValueError(f"Record is not event-ready: {details}")
    record_type = type(record).__name__
    record_id = _record_id(record)
    event_name = _EVENT_NAMES.get(record_type, _snake_case(record_type))
    return {
        "schema_version": SCHEMA_VERSION,
        "event_type": f"agcontentieux.{event_name}.recorded",
        "aggregate_id": record_id,
        "status": getattr(record, "status", ""),
        "restriction": getattr(record, "restriction", ""),
        "diffusion": getattr(record, "diffusion", ""),
        "source_refs": list(source_reference_ids(record)),
        "proof_refs": list(proof_reference_ids(record)),
        "decision_refs": list(decision_reference_ids(record)),
        "action_refs": list(action_reference_ids(record)),
        "payload": _json_ready(record),
    }


def _validate_one(path: str, record: object) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    record_id = _record_id(record)
    if not record_id:
        issues.append(ValidationIssue(f"{path}.id", "missing identifier"))

    status = getattr(record, "status", "")
    if status and status not in ALLOWED_STATUSES:
        issues.append(ValidationIssue(f"{path}.status", f"unsupported status {status!r}"))

    restriction = getattr(record, "restriction", "")
    if restriction and restriction not in ALLOWED_RESTRICTIONS:
        issues.append(ValidationIssue(f"{path}.restriction", f"unsupported restriction {restriction!r}"))

    diffusion = getattr(record, "diffusion", "")
    if diffusion and diffusion not in ALLOWED_DIFFUSIONS:
        issues.append(ValidationIssue(f"{path}.diffusion", f"unsupported diffusion {diffusion!r}"))

    due_on = getattr(record, "due_on", None)
    if due_on is not None and _as_date(due_on) is None:
        issues.append(ValidationIssue(f"{path}.due_on", "invalid ISO date"))

    if not source_reference_ids(record) and type(record).__name__ != "PassationPack":
        issues.append(ValidationIssue(f"{path}.source_refs", "missing source reference"))

    for field_name, value in _text_fields(record):
        if contains_private_data(value):
            issues.append(ValidationIssue(f"{path}.{field_name}", "private data marker detected"))

    if isinstance(record, (PrecontentiousAction, PrecontentiousPlan)):
        if isinstance(record, PrecontentiousPlan) and not _is_non_legal_scope(record.scope_notice):
            issues.append(ValidationIssue(f"{path}.scope_notice", "precontentious plan must stay non juridique"))
        for field_name, value in _text_fields(record):
            if contains_legal_advice(value):
                issues.append(ValidationIssue(f"{path}.{field_name}", "automatic legal advice marker detected"))
            if field_name not in {"restriction", "diffusion", "status"} and contains_unsafe_local_marker(value):
                issues.append(ValidationIssue(f"{path}.{field_name}", "unsafe local marker detected"))
        for index, reference in enumerate((*source_reference_ids(record), *proof_reference_ids(record))):
            if contains_unsafe_local_marker(reference):
                issues.append(ValidationIssue(f"{path}.refs[{index}]", "unsafe local marker detected"))

    if isinstance(record, LegalRiskNote):
        if not _is_non_legal_scope(record.scope_notice):
            issues.append(ValidationIssue(f"{path}.scope_notice", "legal risk note must stay non juridique"))
        for field_name, value in _text_fields(record):
            if contains_legal_advice(value):
                issues.append(ValidationIssue(f"{path}.{field_name}", "automatic legal advice marker detected"))

    return tuple(issues)


def _walk_records(record: object, path: str = "record") -> tuple[tuple[str, object], ...]:
    if isinstance(record, (str, bytes)) or record is None:
        return ()
    if isinstance(record, Iterable) and not is_dataclass(record):
        walked: list[tuple[str, object]] = []
        for index, item in enumerate(record):
            walked.extend(_walk_records(item, f"{path}[{index}]"))
        return tuple(walked)
    if not is_dataclass(record):
        return ()
    walked = [(path, record)]
    for field_name, value in asdict(record).items():
        if isinstance(value, (list, tuple)):
            original_value = getattr(record, field_name)
            for index, item in enumerate(original_value):
                walked.extend(_walk_records(item, f"{path}.{field_name}[{index}]"))
    return tuple(walked)


def _text_fields(record: object) -> tuple[tuple[str, str], ...]:
    if not is_dataclass(record):
        return ()
    ignored = {
        "source_ref",
        "source_refs",
        "proof_ref",
        "proof_refs",
        "decision_refs",
        "action_refs",
        "event_refs",
        "risk_note_refs",
        "dossier_ag_ids",
        "contentieux_case_ids",
        "evidence_bundle_ids",
        "legal_risk_note_ids",
        "source_hash",
    }
    values: list[tuple[str, str]] = []
    for field_name, value in asdict(record).items():
        if field_name in ignored:
            continue
        if isinstance(value, str):
            values.append((field_name, value))
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                if isinstance(item, str):
                    values.append((f"{field_name}[{index}]", item))
    return tuple(values)


def _collect_refs(record_or_records: object, field_names: tuple[str, ...]) -> tuple[str, ...]:
    values: list[str] = []
    for _, record in _walk_records(record_or_records):
        for field_name in field_names:
            raw = getattr(record, field_name, None)
            if raw is None:
                continue
            if isinstance(raw, str):
                values.append(raw)
            else:
                values.extend(str(item) for item in raw if str(item).strip())
    return _dedupe(values)


def _is_non_legal_scope(value: str) -> bool:
    normalized = _normalize(value)
    return "non juridique" in normalized or "ne conclut pas juridiquement" in normalized


def _max_restriction(records: Iterable[object]) -> str:
    order = {
        RESTRICTION_INTERNAL: 0,
        RESTRICTION_RESTRICTED: 1,
        RESTRICTION_CONFIDENTIAL: 2,
    }
    restrictions = [getattr(record, "restriction", RESTRICTION_INTERNAL) for record in records]
    if not restrictions:
        return RESTRICTION_INTERNAL
    return max(restrictions, key=lambda value: order.get(value, 0))


def _min_diffusion(records: Iterable[object]) -> str:
    order = {
        DIFFUSION_PUBLIC_AFTER_REDACTION: 0,
        DIFFUSION_COPRO: 1,
        DIFFUSION_CS: 2,
    }
    diffusions = [getattr(record, "diffusion", DIFFUSION_CS) for record in records]
    if not diffusions:
        return DIFFUSION_CS
    return max(diffusions, key=lambda value: order.get(value, 2))


def _record_id(record: object) -> str:
    field_name = _ID_FIELDS.get(type(record).__name__, "")
    return str(getattr(record, field_name, "")) if field_name else ""


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return {key: _json_ready(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _as_date(value: DateLike) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return date.fromisoformat(stripped[:10])
        except ValueError:
            return None
    return None


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return tuple(result)


def _normalize(value: str) -> str:
    return " ".join((value or "").lower().split())


def _snake_case(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
