from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..core.common import InstanceConfig, RunContext, read_csv, relative_to, write_csv
from ..core.event_types import REQUEST_ACTION_RECORDED, REQUEST_CREATED


CHANNEL_EMAIL = "email"
CHANNEL_ORAL = "oral"
CHANNEL_COURRIER = "courrier"
CHANNEL_AG = "ag"
CHANNEL_PORTAIL_SYNDIC = "portail_syndic"
CHANNEL_DOCOPS = "document_docops"
CHANNEL_INCIDENT = "incident"
REQUEST_CHANNELS = frozenset(
    {
        CHANNEL_EMAIL,
        CHANNEL_ORAL,
        CHANNEL_COURRIER,
        CHANNEL_AG,
        CHANNEL_PORTAIL_SYNDIC,
        CHANNEL_DOCOPS,
        CHANNEL_INCIDENT,
    }
)

STATUS_NEW = "nouvelle"
STATUS_TO_QUALIFY = "a_qualifier"
STATUS_IN_PROGRESS = "en_cours"
STATUS_WAITING = "en_attente"
STATUS_FOLLOW_UP = "relance"
STATUS_CLOSED = "cloturee"
STATUS_DISMISSED = "sans_suite"
OPEN_STATUSES = frozenset(
    {
        STATUS_NEW,
        STATUS_TO_QUALIFY,
        STATUS_IN_PROGRESS,
        STATUS_WAITING,
        STATUS_FOLLOW_UP,
    }
)
REQUEST_STATUSES = OPEN_STATUSES | frozenset({STATUS_CLOSED, STATUS_DISMISSED})

VISIBILITY_COPRO = "copro"
VISIBILITY_CS = "conseil_syndical"
VISIBILITY_RESTRICTED = "restreint"
VISIBILITIES = frozenset({VISIBILITY_COPRO, VISIBILITY_CS, VISIBILITY_RESTRICTED})

REQUEST_FIELDS = [
    "request_id",
    "received_at",
    "author_label",
    "author_role",
    "channel",
    "subject",
    "summary",
    "proof_ref",
    "source_ref",
    "status",
    "next_action",
    "related_point_id",
    "related_action_id",
    "visibility",
    "origin_kind",
    "origin_id",
    "notes",
]

ACTION_LOG_FIELDS = [
    "journal_id",
    "request_id",
    "occurred_at",
    "actor_role",
    "action_type",
    "summary",
    "proof_ref",
    "source_ref",
    "status_after",
    "next_action",
    "visibility",
    "event_hash",
]

AUTHOR_FIELDS = ("author_label", "auteur", "demandeur", "requester", "from", "emetteur")
AUTHOR_ROLE_FIELDS = ("author_role", "role_auteur", "requester_role", "qualite")
CHANNEL_FIELDS = ("channel", "canal", "source_channel", "origine_canal")
SUBJECT_FIELDS = ("subject", "sujet", "title", "titre", "objet")
SUMMARY_FIELDS = ("summary", "resume", "description", "body_summary", "contenu")
PROOF_FIELDS = ("proof_ref", "proof", "preuve", "piece_ref", "evidence", "justificatif")
SOURCE_FIELDS = ("source_ref", "source", "origine", "document_source", "trace_source")
STATUS_FIELDS = ("status", "statut", "etat")
ACTION_FIELDS = ("next_action", "prochaine_action", "action_attendue", "todo")
VISIBILITY_FIELDS = ("visibility", "diffusion", "public", "visibilite")
POINT_FIELDS = ("related_point_id", "point_id", "rattachement_point", "ag_point_id")
RELATED_ACTION_FIELDS = ("related_action_id", "action_id", "rattachement_action")
ORIGIN_KIND_FIELDS = ("origin_kind", "type_origine", "source_kind", "objet_origine")
ORIGIN_ID_FIELDS = ("origin_id", "id_origine", "source_id", "doc_id", "incident_id")
PRIVATE_FIELD_NAMES = frozenset(
    {
        "email",
        "mail",
        "telephone",
        "tel",
        "phone",
        "mobile",
        "adresse",
        "address",
        "nom",
        "prenom",
        "last_name",
        "first_name",
    }
)


@dataclass(frozen=True)
class CoproRequest:
    request_id: str
    received_at: str
    author_label: str
    author_role: str
    channel: str
    subject: str
    summary: str
    proof_ref: str
    source_ref: str
    status: str = STATUS_NEW
    next_action: str = ""
    related_point_id: str = ""
    related_action_id: str = ""
    visibility: str = VISIBILITY_CS
    origin_kind: str = ""
    origin_id: str = ""
    notes: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RequestAction:
    journal_id: str
    request_id: str
    occurred_at: str
    actor_role: str
    action_type: str
    summary: str
    proof_ref: str = ""
    source_ref: str = ""
    status_after: str = ""
    next_action: str = ""
    visibility: str = VISIBILITY_CS
    event_hash: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


def normalize_request(row: Mapping[str, Any]) -> CoproRequest:
    row_data = dict(row)
    channel = _normalize_channel(_first_text(row_data, CHANNEL_FIELDS))
    subject = _first_text(row_data, SUBJECT_FIELDS)
    summary = _first_text(row_data, SUMMARY_FIELDS)
    proof_ref = _first_text(row_data, PROOF_FIELDS)
    source_ref = _first_text(row_data, SOURCE_FIELDS)
    received_at = _first_text(row_data, ("received_at", "date", "date_reception", "created_at"))
    author_label = _first_text(row_data, AUTHOR_FIELDS) or "auteur_non_nominalise"
    author_role = _first_text(row_data, AUTHOR_ROLE_FIELDS) or "coproprietaire"
    status = _normalize_status(_first_text(row_data, STATUS_FIELDS))
    visibility = _normalize_visibility(_first_text(row_data, VISIBILITY_FIELDS))
    request_id = _first_text(row_data, ("request_id", "demande_id", "id", "key")) or _stable_id(
        "REQ",
        received_at,
        channel,
        subject,
        proof_ref or source_ref,
    )
    request = CoproRequest(
        request_id=_cell(request_id),
        received_at=_privacy_safe_text(received_at),
        author_label=_privacy_safe_text(author_label),
        author_role=_privacy_safe_text(author_role),
        channel=channel,
        subject=_privacy_safe_text(subject),
        summary=_privacy_safe_text(summary),
        proof_ref=_privacy_safe_text(proof_ref),
        source_ref=_privacy_safe_text(source_ref),
        status=status,
        next_action=_privacy_safe_text(_first_text(row_data, ACTION_FIELDS) or _default_next_action(status, channel)),
        related_point_id=_privacy_safe_text(_first_text(row_data, POINT_FIELDS)),
        related_action_id=_privacy_safe_text(_first_text(row_data, RELATED_ACTION_FIELDS)),
        visibility=visibility,
        origin_kind=_privacy_safe_text(_first_text(row_data, ORIGIN_KIND_FIELDS) or channel),
        origin_id=_privacy_safe_text(_first_text(row_data, ORIGIN_ID_FIELDS)),
        notes=_privacy_safe_text(_first_text(row_data, ("notes", "commentaire", "comment"))),
        metadata=_metadata(
            row_data,
            {
                "request_id",
                "demande_id",
                "id",
                "key",
                "received_at",
                "date",
                "date_reception",
                "created_at",
                "notes",
                "commentaire",
                "comment",
                *AUTHOR_FIELDS,
                *AUTHOR_ROLE_FIELDS,
                *CHANNEL_FIELDS,
                *SUBJECT_FIELDS,
                *SUMMARY_FIELDS,
                *PROOF_FIELDS,
                *SOURCE_FIELDS,
                *STATUS_FIELDS,
                *ACTION_FIELDS,
                *VISIBILITY_FIELDS,
                *POINT_FIELDS,
                *RELATED_ACTION_FIELDS,
                *ORIGIN_KIND_FIELDS,
                *ORIGIN_ID_FIELDS,
            },
        ),
    )
    return request


def normalize_action(row: Mapping[str, Any]) -> RequestAction:
    row_data = dict(row)
    request_id = _first_text(row_data, ("request_id", "demande_id"))
    occurred_at = _first_text(row_data, ("occurred_at", "date", "created_at", "horodatage"))
    actor_role = _first_text(row_data, ("actor_role", "role_acteur", "acteur", "author_role"))
    action_type = _normalize_action_type(_first_text(row_data, ("action_type", "type_action", "type")))
    summary = _first_text(row_data, ("summary", "resume", "description", "action", "fait"))
    journal_id = _first_text(row_data, ("journal_id", "event_id", "id", "key")) or _stable_id(
        "JRN",
        request_id,
        occurred_at,
        actor_role,
        action_type,
        summary,
    )
    raw_status_after = _first_text(row_data, ("status_after", "statut_apres", "status", "statut"))
    action = RequestAction(
        journal_id=_cell(journal_id),
        request_id=_privacy_safe_text(request_id),
        occurred_at=_privacy_safe_text(occurred_at),
        actor_role=_privacy_safe_text(actor_role),
        action_type=action_type,
        summary=_privacy_safe_text(summary),
        proof_ref=_privacy_safe_text(_first_text(row_data, PROOF_FIELDS)),
        source_ref=_privacy_safe_text(_first_text(row_data, SOURCE_FIELDS)),
        status_after=_normalize_status(raw_status_after) if raw_status_after else "",
        next_action=_privacy_safe_text(_first_text(row_data, ACTION_FIELDS)),
        visibility=_normalize_visibility(_first_text(row_data, VISIBILITY_FIELDS)),
        event_hash=_privacy_safe_text(_first_text(row_data, ("event_hash", "hash_evenement"))),
        metadata=_metadata(
            row_data,
            {
                "journal_id",
                "event_id",
                "id",
                "key",
                "request_id",
                "demande_id",
                "occurred_at",
                "date",
                "created_at",
                "horodatage",
                "actor_role",
                "role_acteur",
                "acteur",
                "author_role",
                "action_type",
                "type_action",
                "type",
                "summary",
                "resume",
                "description",
                "action",
                "fait",
                "status_after",
                "statut_apres",
                "status",
                "statut",
                "event_hash",
                "hash_evenement",
                *PROOF_FIELDS,
                *SOURCE_FIELDS,
                *ACTION_FIELDS,
                *VISIBILITY_FIELDS,
            },
        ),
    )
    if not action.event_hash:
        return action_with_hash(action)
    return action


def request_from_docops(document_row: Mapping[str, Any], *, subject: str = "", next_action: str = "") -> CoproRequest:
    file_name = _first_text(document_row, ("file_name", "original_path", "doc_id"))
    doc_id = _first_text(document_row, ("doc_id", "id"))
    return normalize_request(
        {
            "channel": CHANNEL_DOCOPS,
            "subject": subject or f"Demande detectee dans {file_name or doc_id}",
            "summary": _first_text(document_row, ("document_type", "notes")),
            "proof_ref": doc_id or file_name,
            "source_ref": _first_text(document_row, ("original_path", "file_name")),
            "next_action": next_action,
            "origin_kind": CHANNEL_DOCOPS,
            "origin_id": doc_id,
            "visibility": VISIBILITY_CS,
        }
    )


def request_from_incident(incident_row: Mapping[str, Any], *, next_action: str = "") -> CoproRequest:
    incident_id = _first_text(incident_row, ("incident_id", "id"))
    description = _first_text(incident_row, ("description", "subject", "sujet"))
    return normalize_request(
        {
            "channel": CHANNEL_INCIDENT,
            "subject": description or f"Suite a donner incident {incident_id}",
            "summary": _first_text(incident_row, ("lieu", "notes", "expected_closure_proof")),
            "proof_ref": _first_text(incident_row, ("piece_ref", "closure_proof_ref", "source_refs")),
            "source_ref": incident_id or _first_text(incident_row, ("source_refs",)),
            "status": STATUS_TO_QUALIFY,
            "next_action": next_action or _first_text(incident_row, ("next_action",)),
            "origin_kind": CHANNEL_INCIDENT,
            "origin_id": incident_id,
            "visibility": VISIBILITY_CS,
        }
    )


def validate_request(request: CoproRequest) -> bool:
    _require_fields(request, ("request_id", "channel", "subject", "status", "visibility"))
    if request.channel not in REQUEST_CHANNELS:
        raise ValueError(f"Unsupported request channel: {request.channel}")
    if request.status not in REQUEST_STATUSES:
        raise ValueError(f"Unsupported request status: {request.status}")
    if request.visibility not in VISIBILITIES:
        raise ValueError(f"Unsupported request visibility: {request.visibility}")
    if not request.proof_ref and not request.source_ref:
        raise ValueError("A request needs a proof_ref or source_ref")
    if is_open_request(request) and not request.next_action:
        raise ValueError("An open request needs a next_action")
    _reject_private_data(asdict(request))
    return True


def validate_action(action: RequestAction, request: CoproRequest | None = None) -> bool:
    _require_fields(action, ("journal_id", "request_id", "occurred_at", "actor_role", "action_type", "summary"))
    if request and action.request_id != request.request_id:
        raise ValueError("action and request ids must match")
    if action.visibility not in VISIBILITIES:
        raise ValueError(f"Unsupported action visibility: {action.visibility}")
    if action.status_after and action.status_after not in REQUEST_STATUSES:
        raise ValueError(f"Unsupported action status_after: {action.status_after}")
    _reject_private_data(asdict(action))
    return True


def is_open_request(request: CoproRequest | Mapping[str, Any]) -> bool:
    status = request.status if isinstance(request, CoproRequest) else _first_text(request, STATUS_FIELDS)
    return _normalize_status(status) in OPEN_STATUSES


def action_with_hash(action: RequestAction) -> RequestAction:
    payload = unsigned_event_payload(REQUEST_ACTION_RECORDED, action.journal_id, action_to_dict(action, include_event_hash=False))
    data = action_to_dict(action, include_event_hash=False)
    data["event_hash"] = event_hash(payload)
    return RequestAction(**data)


def unsigned_event_payload(event_type: str, object_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    cleaned_payload = _without_empty(_privacy_safe_mapping(payload))
    return {
        "event_schema": "coproscope.unsigned_event.v1",
        "event_type": _cell(event_type),
        "object_id": _cell(object_id),
        "payload": cleaned_payload,
        "signature": "",
    }


def request_event_payload(request: CoproRequest) -> dict[str, Any]:
    validate_request(request)
    return unsigned_event_payload(REQUEST_CREATED, request.request_id, request_to_dict(request))


def action_event_payload(action: RequestAction) -> dict[str, Any]:
    validate_action(action)
    return unsigned_event_payload(REQUEST_ACTION_RECORDED, action.journal_id, action_to_dict(action, include_event_hash=False))


def event_hash(event_payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(event_payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_requests(rows: Iterable[Mapping[str, Any]]) -> list[CoproRequest]:
    return [normalize_request(row) for row in rows]


def normalize_actions(rows: Iterable[Mapping[str, Any]]) -> list[RequestAction]:
    return [normalize_action(row) for row in rows]


def rows_from_csv(text: str) -> list[dict[str, str]]:
    if not text.strip():
        return []
    return [dict(row) for row in csv.DictReader(io.StringIO(text))]


def requests_from_csv(text: str) -> list[CoproRequest]:
    return normalize_requests(rows_from_csv(text))


def actions_from_csv(text: str) -> list[RequestAction]:
    return normalize_actions(rows_from_csv(text))


def request_to_dict(request: CoproRequest) -> dict[str, Any]:
    return asdict(request)


def action_to_dict(action: RequestAction, *, include_event_hash: bool = True) -> dict[str, Any]:
    data = asdict(action)
    if not include_event_hash:
        data["event_hash"] = ""
    return data


def request_register_path(instance: InstanceConfig) -> Path:
    try:
        return instance.register("requests")
    except KeyError:
        return instance.instance_root / "registers" / "registre_demandes_coproprietaires.csv"


def request_action_log_path(instance: InstanceConfig) -> Path:
    return instance.instance_root / "registers" / "journal_demandes_coproprietaires.csv"


def read_request_register(instance: InstanceConfig) -> list[CoproRequest]:
    _, rows = read_csv(request_register_path(instance))
    return normalize_requests(rows)


def write_request_register(instance: InstanceConfig, run: RunContext, rows: Iterable[Mapping[str, Any] | CoproRequest]) -> Path:
    requests = [row if isinstance(row, CoproRequest) else normalize_request(row) for row in rows]
    for request in requests:
        validate_request(request)
    path = request_register_path(instance)
    serialized = sorted(
        [_flat_row(request_to_dict(request), REQUEST_FIELDS) for request in requests],
        key=lambda row: (row.get("status", ""), row.get("received_at", ""), row.get("request_id", "")),
    )
    write_csv(path, REQUEST_FIELDS, serialized)
    run.log_action("write", path, f"request rows={len(serialized)}")
    return path


def write_request_action_log(
    instance: InstanceConfig,
    run: RunContext,
    rows: Iterable[Mapping[str, Any] | RequestAction],
) -> Path:
    actions = [row if isinstance(row, RequestAction) else normalize_action(row) for row in rows]
    for action in actions:
        validate_action(action)
    path = request_action_log_path(instance)
    serialized = sorted(
        [_flat_row(action_to_dict(action), ACTION_LOG_FIELDS) for action in actions],
        key=lambda row: (row.get("request_id", ""), row.get("occurred_at", ""), row.get("journal_id", "")),
    )
    write_csv(path, ACTION_LOG_FIELDS, serialized)
    run.log_action("write", path, f"request action rows={len(serialized)}")
    return path


def relative_request_outputs(instance: InstanceConfig, result: dict[str, object]) -> dict[str, object]:
    workspace = instance.root("workspace")
    converted: dict[str, object] = dict(result)
    for key in ["request_register", "request_action_log"]:
        value = converted.get(key)
        if isinstance(value, str):
            converted[key] = relative_to(workspace, Path(value))
    return converted


def _default_next_action(status: str, channel: str) -> str:
    if status == STATUS_NEW:
        return "Qualifier la demande, la preuve source et la personne chargee de la suite."
    if status == STATUS_TO_QUALIFY:
        return "Completer le rattachement point/action et choisir le niveau de diffusion."
    if status == STATUS_IN_PROGRESS:
        return "Suivre la reponse attendue et journaliser la prochaine trace concrete."
    if status == STATUS_WAITING:
        return "Attendre la piece ou la reponse annoncee, puis verifier la preuve."
    if status == STATUS_FOLLOW_UP:
        return "Relancer avec une echeance explicite et conserver la trace."
    if channel == CHANNEL_ORAL:
        return "Transformer l'echange oral en trace ecrite relue avant diffusion."
    return ""
