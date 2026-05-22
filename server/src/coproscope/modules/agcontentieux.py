from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime
from typing import Any, Iterable


SCHEMA_VERSION = "agcontentieux.v1"

STATUS_DRAFT = "draft"
STATUS_TO_REVIEW = "to_review"
STATUS_READY = "ready"
STATUS_BLOCKED = "blocked"
STATUS_ARCHIVED = "archived"

RESTRICTION_INTERNAL = "internal"
RESTRICTION_RESTRICTED = "restricted"
RESTRICTION_CONFIDENTIAL = "confidential"

DIFFUSION_CS = "cs"
DIFFUSION_COPRO = "coproprietaires"
DIFFUSION_PUBLIC_AFTER_REDACTION = "public_after_redaction"

LEGAL_SCOPE_NOTICE = (
    "Note non juridique: constats, risques operationnels et pieces a verifier; "
    "validation par un professionnel si besoin."
)

PRECONTENTIOUS_SCOPE_NOTICE = (
    "Plan derive de constats, a verifier humainement. Il prepare des demandes, "
    "traces et corrections; il ne conclut pas juridiquement."
)

ALLOWED_STATUSES = {
    STATUS_DRAFT,
    STATUS_TO_REVIEW,
    STATUS_READY,
    STATUS_BLOCKED,
    STATUS_ARCHIVED,
}

ALLOWED_RESTRICTIONS = {
    RESTRICTION_INTERNAL,
    RESTRICTION_RESTRICTED,
    RESTRICTION_CONFIDENTIAL,
}

ALLOWED_DIFFUSIONS = {
    DIFFUSION_CS,
    DIFFUSION_COPRO,
    DIFFUSION_PUBLIC_AFTER_REDACTION,
}

_PRIVATE_DATA_PATTERNS = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}\b"),
    re.compile(r"\b[12]\s?\d{2}\s?(?:0[1-9]|1[0-2])\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b"),
)

_LEGAL_ADVICE_PATTERNS = (
    re.compile(r"\bavis juridique\b", re.IGNORECASE),
    re.compile(r"\bconseil juridique\b", re.IGNORECASE),
    re.compile(r"\b(?:vous|nous)\s+(?:devez|devons)\s+(?:assigner|poursuivre|attaquer)\b", re.IGNORECASE),
    re.compile(r"\bil faut\s+(?:assigner|poursuivre|attaquer)\b", re.IGNORECASE),
    re.compile(r"\b(?:vous|nous)\s+gagnerez\b", re.IGNORECASE),
    re.compile(r"\bchances?\s+de\s+gagner\b", re.IGNORECASE),
    re.compile(r"\bnullit[eé]\b", re.IGNORECASE),
)

_UNSAFE_LOCAL_PATTERNS = (
    re.compile(r"\b[A-Z]:\\", re.IGNORECASE),
    re.compile(r"\bfile://", re.IGNORECASE),
    re.compile(r"\b(?:api[_-]?key|token|secret)\s*[:=]", re.IGNORECASE),
    re.compile(r"\b(?:raw|restricted|logs)\b", re.IGNORECASE),
)

_ID_FIELDS = {
    "DossierAG": "dossier_id",
    "QuestionAG": "question_id",
    "PieceConvocation": "piece_id",
    "ContentieuxCase": "case_id",
    "LegalRiskNote": "note_id",
    "EvidenceRef": "evidence_id",
    "EvidenceBundle": "bundle_id",
    "PassationPack": "pack_id",
    "PrecontentiousAction": "action_id",
    "PrecontentiousPlan": "plan_id",
}

_EVENT_NAMES = {
    "DossierAG": "dossier_ag",
    "QuestionAG": "question_ag",
}


DateLike = date | datetime | str | None


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    reason: str
    severity: str = "error"


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    source_ref: str
    title: str
    source_kind: str = "document"
    source_hash: str = ""
    captured_on: DateLike = None
    restriction: str = RESTRICTION_RESTRICTED
    diffusion: str = DIFFUSION_CS
    status: str = STATUS_TO_REVIEW
    next_action: str = "Verifier la piece et son origine avant diffusion."
    due_on: DateLike = None
    decision_refs: tuple[str, ...] = field(default_factory=tuple)
    action_refs: tuple[str, ...] = field(default_factory=tuple)
    event_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


@dataclass(frozen=True)
class PieceConvocation:
    piece_id: str
    dossier_ag_id: str
    label: str
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    proof_refs: tuple[str, ...] = field(default_factory=tuple)
    restriction: str = RESTRICTION_RESTRICTED
    diffusion: str = DIFFUSION_CS
    status: str = STATUS_DRAFT
    next_action: str = "Verifier presence, version et perimetre diffusable."
    due_on: DateLike = None
    decision_refs: tuple[str, ...] = field(default_factory=tuple)
    action_refs: tuple[str, ...] = field(default_factory=tuple)
    event_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


@dataclass(frozen=True)
class QuestionAG:
    question_id: str
    dossier_ag_id: str
    title: str
    objective: str = ""
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    proof_refs: tuple[str, ...] = field(default_factory=tuple)
    restriction: str = RESTRICTION_RESTRICTED
    diffusion: str = DIFFUSION_CS
    status: str = STATUS_DRAFT
    next_action: str = "Consolider les pieces et rattacher les decisions/actions attendues."
    due_on: DateLike = None
    decision_refs: tuple[str, ...] = field(default_factory=tuple)
    action_refs: tuple[str, ...] = field(default_factory=tuple)
    event_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


@dataclass(frozen=True)
class DossierAG:
    dossier_id: str
    title: str
    ag_date: DateLike = None
    questions: tuple[QuestionAG, ...] = field(default_factory=tuple)
    pieces: tuple[PieceConvocation, ...] = field(default_factory=tuple)
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    proof_refs: tuple[str, ...] = field(default_factory=tuple)
    restriction: str = RESTRICTION_RESTRICTED
    diffusion: str = DIFFUSION_CS
    status: str = STATUS_DRAFT
    next_action: str = "Preparer ordre du jour, pieces de convocation et preuves rattachees."
    due_on: DateLike = None
    decision_refs: tuple[str, ...] = field(default_factory=tuple)
    action_refs: tuple[str, ...] = field(default_factory=tuple)
    event_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


@dataclass(frozen=True)
class ContentieuxCase:
    case_id: str
    title: str
    matter: str
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    proof_refs: tuple[str, ...] = field(default_factory=tuple)
    risk_note_refs: tuple[str, ...] = field(default_factory=tuple)
    restriction: str = RESTRICTION_CONFIDENTIAL
    diffusion: str = DIFFUSION_CS
    status: str = STATUS_DRAFT
    next_action: str = "Rassembler les faits dates et pieces, sans qualification juridique automatique."
    due_on: DateLike = None
    decision_refs: tuple[str, ...] = field(default_factory=tuple)
    action_refs: tuple[str, ...] = field(default_factory=tuple)
    event_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


@dataclass(frozen=True)
class LegalRiskNote:
    note_id: str
    subject: str
    observations: tuple[str, ...] = field(default_factory=tuple)
    risk_signals: tuple[str, ...] = field(default_factory=tuple)
    scope_notice: str = LEGAL_SCOPE_NOTICE
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    proof_refs: tuple[str, ...] = field(default_factory=tuple)
    restriction: str = RESTRICTION_CONFIDENTIAL
    diffusion: str = DIFFUSION_CS
    status: str = STATUS_TO_REVIEW
    next_action: str = "Faire relire par une personne competente avant toute decision juridique."
    due_on: DateLike = None
    decision_refs: tuple[str, ...] = field(default_factory=tuple)
    action_refs: tuple[str, ...] = field(default_factory=tuple)
    event_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


@dataclass(frozen=True)
class EvidenceBundle:
    bundle_id: str
    title: str
    purpose: str
    evidence_refs: tuple[EvidenceRef, ...] = field(default_factory=tuple)
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    proof_refs: tuple[str, ...] = field(default_factory=tuple)
    restriction: str = RESTRICTION_RESTRICTED
    diffusion: str = DIFFUSION_CS
    status: str = STATUS_DRAFT
    next_action: str = "Completer les sources manquantes et controler la diffusion."
    due_on: DateLike = None
    decision_refs: tuple[str, ...] = field(default_factory=tuple)
    action_refs: tuple[str, ...] = field(default_factory=tuple)
    event_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


@dataclass(frozen=True)
class PassationPack:
    pack_id: str
    title: str
    handover_scope: str
    dossier_ag_ids: tuple[str, ...] = field(default_factory=tuple)
    contentieux_case_ids: tuple[str, ...] = field(default_factory=tuple)
    evidence_bundle_ids: tuple[str, ...] = field(default_factory=tuple)
    legal_risk_note_ids: tuple[str, ...] = field(default_factory=tuple)
    open_points: tuple[str, ...] = field(default_factory=tuple)
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    proof_refs: tuple[str, ...] = field(default_factory=tuple)
    restriction: str = RESTRICTION_RESTRICTED
    diffusion: str = DIFFUSION_CS
    status: str = STATUS_DRAFT
    next_action: str = "Transmettre le paquet avec limites de diffusion et actions ouvertes."
    due_on: DateLike = None
    decision_refs: tuple[str, ...] = field(default_factory=tuple)
    action_refs: tuple[str, ...] = field(default_factory=tuple)
    event_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


@dataclass(frozen=True)
class PrecontentiousAction:
    action_id: str
    lane: str
    label: str
    objective: str
    expected_proof: str = ""
    priority: str = "P1"
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    proof_refs: tuple[str, ...] = field(default_factory=tuple)
    restriction: str = RESTRICTION_CONFIDENTIAL
    diffusion: str = DIFFUSION_CS
    status: str = STATUS_TO_REVIEW
    next_action: str = "Faire verifier humainement avant toute diffusion ou decision."
    due_on: DateLike = None
    decision_refs: tuple[str, ...] = field(default_factory=tuple)
    action_refs: tuple[str, ...] = field(default_factory=tuple)
    event_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""


@dataclass(frozen=True)
class PrecontentiousPlan:
    plan_id: str
    title: str
    actions: tuple[PrecontentiousAction, ...] = field(default_factory=tuple)
    scope_notice: str = PRECONTENTIOUS_SCOPE_NOTICE
    source_refs: tuple[str, ...] = field(default_factory=tuple)
    proof_refs: tuple[str, ...] = field(default_factory=tuple)
    restriction: str = RESTRICTION_CONFIDENTIAL
    diffusion: str = DIFFUSION_CS
    status: str = STATUS_TO_REVIEW
    next_action: str = "Envoyer les demandes P1, preparer les reserves PV et rattacher les reponses comme preuves."
    due_on: DateLike = None
    decision_refs: tuple[str, ...] = field(default_factory=tuple)
    action_refs: tuple[str, ...] = field(default_factory=tuple)
    event_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""

    @property
    def lane_counts(self) -> dict[str, int]:
        counts = {"piece_request": 0, "pv_reserve": 0, "power_trace": 0, "correction": 0}
        for action in self.actions:
            counts[action.lane] = counts.get(action.lane, 0) + 1
        return counts


def build_evidence_bundle(
    bundle_id: str,
    title: str,
    purpose: str,
    evidence_refs: Iterable[EvidenceRef],
    *,
    status: str = STATUS_DRAFT,
    next_action: str = "Completer les sources manquantes et controler la diffusion.",
    due_on: DateLike = None,
    decision_refs: Iterable[str] = (),
    action_refs: Iterable[str] = (),
) -> EvidenceBundle:
    evidence = tuple(evidence_refs)
    return EvidenceBundle(
        bundle_id=bundle_id,
        title=title,
        purpose=purpose,
        evidence_refs=evidence,
        source_refs=source_reference_ids(evidence),
        proof_refs=proof_reference_ids(evidence),
        restriction=_max_restriction(evidence),
        diffusion=_min_diffusion(evidence),
        status=status,
        next_action=next_action,
        due_on=due_on,
        decision_refs=_dedupe(decision_refs),
        action_refs=_dedupe(action_refs),
    )


def build_precontentious_plan(
    plan_id: str,
    title: str,
    findings: Iterable[dict[str, str]],
    *,
    due_on: DateLike = None,
    max_actions: int = 18,
) -> PrecontentiousPlan:
    actions = tuple(
        _precontentious_action(row, index)
        for index, row in enumerate(_prioritized_findings(findings, max_actions=max_actions), start=1)
    )
    return PrecontentiousPlan(
        plan_id=plan_id,
        title=title or "Plan de reprise avant AG",
        actions=actions,
        source_refs=source_reference_ids(actions),
        proof_refs=proof_reference_ids(actions),
        restriction=_max_restriction(actions),
        diffusion=_min_diffusion(actions),
        due_on=due_on,
        action_refs=action_reference_ids(actions),
    )


def build_passation_pack(
    pack_id: str,
    title: str,
    handover_scope: str,
    *,
    dossiers_ag: Iterable[DossierAG] = (),
    contentieux_cases: Iterable[ContentieuxCase] = (),
    evidence_bundles: Iterable[EvidenceBundle] = (),
    legal_risk_notes: Iterable[LegalRiskNote] = (),
    open_points: Iterable[str] = (),
    status: str = STATUS_DRAFT,
    next_action: str = "Transmettre le paquet avec limites de diffusion et actions ouvertes.",
    due_on: DateLike = None,
) -> PassationPack:
    dossiers = tuple(dossiers_ag)
    cases = tuple(contentieux_cases)
    bundles = tuple(evidence_bundles)
    notes = tuple(legal_risk_notes)
    records: tuple[object, ...] = (*dossiers, *cases, *bundles, *notes)
    return PassationPack(
        pack_id=pack_id,
        title=title,
        handover_scope=handover_scope,
        dossier_ag_ids=_dedupe(dossier.dossier_id for dossier in dossiers),
        contentieux_case_ids=_dedupe(case.case_id for case in cases),
        evidence_bundle_ids=_dedupe(bundle.bundle_id for bundle in bundles),
        legal_risk_note_ids=_dedupe(note.note_id for note in notes),
        open_points=_dedupe(open_points),
        source_refs=source_reference_ids(records),
        proof_refs=proof_reference_ids(records),
        restriction=_max_restriction(records),
        diffusion=_min_diffusion(records),
        status=status,
        next_action=next_action,
        due_on=due_on,
        decision_refs=decision_reference_ids(records),
        action_refs=action_reference_ids(records),
    )


def _prioritized_findings(findings: Iterable[dict[str, str]], *, max_actions: int) -> tuple[dict[str, str], ...]:
    rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "": 4}
    rows = [row for row in findings if str(row.get("priorite") or row.get("priority") or "P1").upper() in {"P0", "P1"}]
    rows.sort(key=lambda row: (rank.get(str(row.get("priorite") or row.get("priority") or "P1").upper(), 9), _row_text(row)))
    return tuple(rows[:max_actions])


def _precontentious_action(row: dict[str, str], index: int) -> PrecontentiousAction:
    lane = _precontentious_lane(row)
    priority = str(row.get("priorite") or row.get("priority") or "P1").upper()
    source_ref = _finding_source_ref(row, index)
    proof = _first_value(row, "preuve_attendue", "expected_piece", "piece_attendue", "preuve")
    proof_ref = _first_value(row, "proof_ref", "proof_refs", "evidence_id", "piece_id", "piece_ref")
    point = _first_value(row, "point_de_controle", "control_id", "constat", "titre")
    action = _first_value(row, "action_a_faire", "next_action", "action", "suite")
    return PrecontentiousAction(
        action_id=f"precontentieux-{index:02d}",
        lane=lane,
        label=_lane_label(lane),
        objective=_objective_for(lane, point, action),
        expected_proof=proof,
        priority=priority,
        source_refs=(source_ref,),
        proof_refs=(proof_ref,) if proof_ref else (),
        next_action=_next_action_for(lane),
        notes=_first_value(row, "risque_concret", "constat", "limite", "notes"),
    )


def _precontentious_lane(row: dict[str, str]) -> str:
    text = _row_text(row)
    if re.search(r"\b(pouvoir|mandat|delegation|signature|representant)\b", text):
        return "power_trace"
    if re.search(r"\b(pv|proces[- ]verbal|reserve|resolution|vote|majorite)\b", text):
        return "pv_reserve"
    if re.search(r"\b(contrat|compte|budget|facture|rgpd|donnee|annexe|correction|rectification)\b", text):
        return "correction"
    return "piece_request"


def _lane_label(lane: str) -> str:
    return {
        "piece_request": "A demander avant l'AG",
        "pv_reserve": "A faire constater au PV si non leve",
        "power_trace": "Pouvoirs et votes a tracer",
        "correction": "Corrections a suivre apres AG",
    }.get(lane, "Action precontentieuse")


def _objective_for(lane: str, point: str, action: str) -> str:
    base = point or action or "Constat a reprendre avant AG"
    if lane == "pv_reserve":
        return f"Preparer une formulation factuelle de reserve si la reponse manque: {base}"
    if lane == "power_trace":
        return f"Tracer qui detient le pouvoir, la preuve et la limite de vote: {base}"
    if lane == "correction":
        return f"Demander la correction ou la justification documentee: {base}"
    return f"Demander la piece ou la preuve attendue: {base}"


def _next_action_for(lane: str) -> str:
    return {
        "piece_request": "Envoyer une demande de piece P1 et rattacher la reponse comme preuve.",
        "pv_reserve": "Preparer une reserve factuelle pour le PV si la preuve n'arrive pas avant l'AG.",
        "power_trace": "Verifier pouvoirs, mandats et signataires; conserver la trace de controle.",
        "correction": "Demander correction ou justification avant AG; garder le suivi dans les actions ouvertes.",
    }.get(lane, "Faire verifier humainement avant toute diffusion ou decision.")


def _finding_source_ref(row: dict[str, str], index: int) -> str:
    for key in ("control_id", "source_row_id", "finding_id", "constat_id", "action_id"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return f"finding-{index:02d}"


def _first_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def _row_text(row: dict[str, str]) -> str:
    return " ".join(str(value or "").lower() for value in row.values())


def source_reference_ids(record_or_records: object) -> tuple[str, ...]:
    return _collect_refs(record_or_records, ("source_ref", "source_refs"))


def proof_reference_ids(record_or_records: object) -> tuple[str, ...]:
    return _collect_refs(record_or_records, ("evidence_id", "proof_ref", "proof_refs"))


def decision_reference_ids(record_or_records: object) -> tuple[str, ...]:
    return _collect_refs(record_or_records, ("decision_refs",))


def action_reference_ids(record_or_records: object) -> tuple[str, ...]:
    return _collect_refs(record_or_records, ("action_refs",))


def contains_private_data(value: str) -> bool:
    return any(pattern.search(value or "") for pattern in _PRIVATE_DATA_PATTERNS)


def contains_legal_advice(value: str) -> bool:
    return any(pattern.search(value or "") for pattern in _LEGAL_ADVICE_PATTERNS)


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
