from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..core.common import InstanceConfig
from ..modules import requestops


STATUS_LABELS = {
    requestops.STATUS_NEW: "nouvelle",
    requestops.STATUS_TO_QUALIFY: "a qualifier",
    requestops.STATUS_IN_PROGRESS: "en cours",
    requestops.STATUS_WAITING: "en attente",
    requestops.STATUS_FOLLOW_UP: "a relancer",
    requestops.STATUS_CLOSED: "cloturee",
    requestops.STATUS_DISMISSED: "sans suite",
}

STATUS_HELP = {
    requestops.STATUS_NEW: "La demande existe, il faut encore verifier son sens, sa preuve et qui s'en occupe.",
    requestops.STATUS_TO_QUALIFY: "Le conseil syndical doit completer le sujet, la preuve ou le rattachement.",
    requestops.STATUS_IN_PROGRESS: "Une personne suit la demande et une suite concrete est attendue.",
    requestops.STATUS_WAITING: "On attend une piece, une reponse ou une confirmation avant d'avancer.",
    requestops.STATUS_FOLLOW_UP: "La suite est en retard ou doit etre relancee avec une trace.",
    requestops.STATUS_CLOSED: "La demande est terminee avec une preuve ou une decision rattachee.",
    requestops.STATUS_DISMISSED: "Le conseil syndical garde la trace, mais ne poursuit pas la demande.",
}

CHANNEL_LABELS = {
    requestops.CHANNEL_EMAIL: "email",
    requestops.CHANNEL_ORAL: "oral / reunion",
    requestops.CHANNEL_COURRIER: "courrier",
    requestops.CHANNEL_AG: "assemblee generale",
    requestops.CHANNEL_PORTAIL_SYNDIC: "portail syndic",
    requestops.CHANNEL_DOCOPS: "document repere",
    requestops.CHANNEL_INCIDENT: "incident",
}

CHANNEL_HELP = {
    requestops.CHANNEL_EMAIL: "message recu ou resume depuis une boite mail",
    requestops.CHANNEL_ORAL: "echange verbal transforme en trace relisible",
    requestops.CHANNEL_COURRIER: "lettre papier ou courrier numerise",
    requestops.CHANNEL_AG: "question, point ou resolution d'assemblee generale",
    requestops.CHANNEL_PORTAIL_SYNDIC: "ticket ou message depose sur un portail syndic",
    requestops.CHANNEL_DOCOPS: "demande detectee depuis une piece locale",
    requestops.CHANNEL_INCIDENT: "suite a donner depuis un incident",
}

VISIBILITY_LABELS = {
    requestops.VISIBILITY_COPRO: "coproprietaires",
    requestops.VISIBILITY_CS: "conseil syndical",
    requestops.VISIBILITY_RESTRICTED: "restreint",
}

VISIBILITY_HELP = {
    requestops.VISIBILITY_COPRO: "diffusable a tous les coproprietaires si la preuve est partageable",
    requestops.VISIBILITY_CS: "lecture de travail pour le conseil syndical",
    requestops.VISIBILITY_RESTRICTED: "a limiter tant qu'un conflit, une donnee sensible ou un arbitrage existe",
}

ACTION_TYPE_LABELS = {
    "qualification": "qualification",
    "relance": "relance",
    "reponse": "reponse recue",
    "rattachement": "rattachement",
    "cloture": "cloture",
    "note": "note de suivi",
}

OPEN_STATUSES = set(requestops.OPEN_STATUSES)


def build_requests_view(instance: InstanceConfig, year: int = 2025) -> dict[str, Any]:
    """Build the owner-facing request board without requiring a route in app.py."""
    requests = _read_requests(instance)
    actions = _read_actions(instance)
    action_groups = _actions_by_request(actions)
    rows = [_display_request(item, action_groups.get(item.request_id, [])) for item in requests]
    rows.sort(key=_request_sort_key)

    by_status = Counter(row["status"] for row in rows)
    by_channel = Counter(row["channel"] for row in rows)
    by_visibility = Counter(row["visibility"] for row in rows)
    open_rows = [row for row in rows if row["is_open"]]
    unlinked_rows = [row for row in rows if not row["related_label"]]
    needs_source_rows = [row for row in rows if row["proof_state"] != "preuve presente"]

    return {
        "instance": {
            "id": instance.instance_id,
            "name": instance.display_name,
            "year": str(year),
        },
        "summary": {
            "total": len(rows),
            "open": len(open_rows),
            "needs_source": len(needs_source_rows),
            "unlinked": len(unlinked_rows),
            "journal_actions": len(actions),
        },
        "status_counts": _named_counts(by_status, STATUS_LABELS, requestops.REQUEST_STATUSES),
        "channel_counts": _named_counts(by_channel, CHANNEL_LABELS, requestops.REQUEST_CHANNELS),
        "visibility_counts": _named_counts(by_visibility, VISIBILITY_LABELS, requestops.VISIBILITIES),
        "rows": rows,
        "open_rows": open_rows,
        "unlinked_rows": unlinked_rows,
        "needs_source_rows": needs_source_rows,
        "empty_state": _empty_state(instance),
        "source": {
            "request_register": _path_label(_request_register_path(instance)),
            "action_log": _path_label(_action_log_path(instance)),
            "request_register_exists": bool(_request_register_path(instance) and _request_register_path(instance).exists()),
            "action_log_exists": bool(_action_log_path(instance) and _action_log_path(instance).exists()),
        },
        "novice_steps": _novice_steps(),
    }


def template_context(instance: InstanceConfig, year: int = 2025) -> dict[str, Any]:
    """Small helper for the future FastAPI route: context(request, 'requests', requests=...)."""
    return {"requests": build_requests_view(instance, year)}


def _read_requests(instance: InstanceConfig) -> list[requestops.CoproRequest]:
    try:
        return requestops.read_request_register(instance)
    except (KeyError, ValueError):
        return []


def _read_actions(instance: InstanceConfig) -> list[requestops.RequestAction]:
    path = _action_log_path(instance)
    if path is None or not path.exists():
        return []
    try:
        return requestops.normalize_actions(_read_csv_rows(path))
    except ValueError:
        return []


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    from ..core.common import read_csv

    _, rows = read_csv(path)
    return rows


def _request_register_path(instance: InstanceConfig) -> Path | None:
    try:
        return requestops.request_register_path(instance)
    except KeyError:
        return None


def _action_log_path(instance: InstanceConfig) -> Path | None:
    try:
        return requestops.request_action_log_path(instance)
    except KeyError:
        return None


def _actions_by_request(actions: list[requestops.RequestAction]) -> dict[str, list[requestops.RequestAction]]:
    groups: dict[str, list[requestops.RequestAction]] = defaultdict(list)
    for action in actions:
        groups[action.request_id].append(action)
    for request_actions in groups.values():
        request_actions.sort(key=lambda item: (item.occurred_at, item.journal_id))
    return groups


def _display_request(item: requestops.CoproRequest, actions: list[requestops.RequestAction]) -> dict[str, Any]:
    latest_action = actions[-1] if actions else None
    proof_ref = item.proof_ref or (latest_action.proof_ref if latest_action else "")
    source_ref = item.source_ref or (latest_action.source_ref if latest_action else "")
    related_label = _related_label(item)
    status = item.status
    visibility = item.visibility
    channel = item.channel
    next_action = latest_action.next_action if latest_action and latest_action.next_action else item.next_action
    return {
        **asdict(item),
        "channel_label": CHANNEL_LABELS.get(channel, channel or "canal a verifier"),
        "channel_help": CHANNEL_HELP.get(channel, "origine a verifier"),
        "status_label": STATUS_LABELS.get(status, status or "statut a verifier"),
        "status_help": STATUS_HELP.get(status, "statut a relire"),
        "visibility_label": VISIBILITY_LABELS.get(visibility, visibility or "diffusion a choisir"),
        "visibility_help": VISIBILITY_HELP.get(visibility, "public a confirmer avant partage"),
        "visibility_badge": _visibility_badge(visibility),
        "status_tone": _status_tone(status),
        "is_open": status in OPEN_STATUSES,
        "received_label": item.received_at or "date a completer",
        "author_label": item.author_label or "auteur non nominatif",
        "subject": item.subject or "sujet a nommer",
        "summary": item.summary or "resume a completer pour qu'un novice comprenne la demande.",
        "proof_label": _public_reference_label(proof_ref, "preuve a rattacher"),
        "source_label": _public_reference_label(source_ref, "source a noter"),
        "proof_state": "preuve presente" if proof_ref or source_ref else "preuve manquante",
        "next_action_label": next_action or _fallback_next_action(status),
        "related_label": related_label,
        "related_state": "rattachee" if related_label else "a rattacher",
        "journal": [_display_action(action) for action in actions],
        "journal_count": len(actions),
        "latest_action_label": _latest_action_label(latest_action),
        "diffusion_warning": _diffusion_warning(item),
    }


def _display_action(action: requestops.RequestAction) -> dict[str, str]:
    action_type = action.action_type
    status_after = action.status_after
    visibility = action.visibility
    return {
        **asdict(action),
        "action_type_label": ACTION_TYPE_LABELS.get(action_type, action_type or "note de suivi"),
        "status_after_label": STATUS_LABELS.get(status_after, status_after or "statut inchange"),
        "visibility_label": VISIBILITY_LABELS.get(visibility, visibility or "diffusion a choisir"),
        "visibility_badge": _visibility_badge(visibility),
        "tone": "is-done" if status_after == requestops.STATUS_CLOSED else "is-risk" if status_after == requestops.STATUS_FOLLOW_UP else "",
        "proof_label": _public_reference_label(action.proof_ref or action.source_ref, "aucune preuve ajoutee"),
        "next_action_label": action.next_action or "aucune suite inscrite",
    }


def _request_sort_key(row: dict[str, Any]) -> tuple[int, str, str]:
    status_weight = {
        requestops.STATUS_FOLLOW_UP: 0,
        requestops.STATUS_NEW: 1,
        requestops.STATUS_TO_QUALIFY: 2,
        requestops.STATUS_WAITING: 3,
        requestops.STATUS_IN_PROGRESS: 4,
        requestops.STATUS_CLOSED: 8,
        requestops.STATUS_DISMISSED: 9,
    }
    return (status_weight.get(str(row["status"]), 5), str(row["received_at"]), str(row["request_id"]))


def _named_counts(counter: Counter[str], labels: dict[str, str], known_keys: Any) -> list[dict[str, Any]]:
    keys = sorted(set(known_keys) | set(counter.keys()), key=lambda key: labels.get(key, key))
    return [
        {
            "key": key,
            "label": labels.get(key, key),
            "count": counter.get(key, 0),
        }
        for key in keys
        if counter.get(key, 0)
    ]


def _related_label(item: requestops.CoproRequest) -> str:
    if item.related_point_id and item.related_action_id:
        return f"point {item.related_point_id} et action {item.related_action_id}"
    if item.related_point_id:
        return f"point {item.related_point_id}"
    if item.related_action_id:
        return f"action {item.related_action_id}"
    return ""


def _status_tone(status: str) -> str:
    if status in {requestops.STATUS_FOLLOW_UP, requestops.STATUS_NEW}:
        return "p1"
    if status in {requestops.STATUS_TO_QUALIFY, requestops.STATUS_WAITING}:
        return "p2"
    return "ok"


def _visibility_badge(visibility: str) -> str:
    if visibility == requestops.VISIBILITY_COPRO:
        return "is-public"
    if visibility == requestops.VISIBILITY_RESTRICTED:
        return "is-private"
    return "is-review"


def _latest_action_label(action: requestops.RequestAction | None) -> str:
    if action is None:
        return "aucune action journalisee"
    label = ACTION_TYPE_LABELS.get(action.action_type, action.action_type or "note")
    return f"{label} le {action.occurred_at or 'date a completer'}"


def _diffusion_warning(item: requestops.CoproRequest) -> str:
    if item.visibility == requestops.VISIBILITY_RESTRICTED:
        return "Diffusion restreinte: garder en interne tant que le sujet sensible n'est pas arbitre."
    if not item.proof_ref and not item.source_ref:
        return "Ne pas diffuser comme acquis: il manque encore la preuve ou la source."
    if item.visibility == requestops.VISIBILITY_COPRO:
        return "Diffusable aux coproprietaires si la preuve est lisible et non sensible."
    return "Travail CS: partager une synthese claire avant toute diffusion plus large."


def _fallback_next_action(status: str) -> str:
    if status == requestops.STATUS_CLOSED:
        return "Conserver la preuve de cloture et le rattachement."
    if status == requestops.STATUS_DISMISSED:
        return "Garder la trace de la raison et ne rien diffuser sans demande."
    return "Choisir une personne responsable, une echeance et la preuve attendue."


def _public_reference_label(value: str, fallback: str) -> str:
    text = (value or "").strip()
    if not text:
        return fallback
    normalized = text.replace("\\", "/").lower()
    if (
        "file://" in normalized
        or (len(normalized) > 2 and normalized[1:3] == ":/")
        or normalized.startswith("/")
        or any(part in normalized.split("/") for part in {"raw", "restricted", "logs", "private"})
    ):
        return "reference locale masquee"
    return text


def _path_label(path: Path | None) -> str:
    if path is None:
        return "non configure"
    return "pret" if path.exists() else "a creer"


def _empty_state(instance: InstanceConfig) -> dict[str, str]:
    register_path = _request_register_path(instance)
    action_path = _action_log_path(instance)
    return {
        "title": "La boite de demandes est prete",
        "message": (
            "Aucune demande n'est encore lue. Ajoutez une ligne de demande avec un canal, un sujet, "
            "une preuve ou source, un statut et une prochaine action."
        ),
        "first_step": "Commencer par une demande simple: oral, email, courrier, AG, portail syndic, document ou incident.",
        "proof_step": "Noter une reference de preuve courte, par exemple MSG-2026-05-20 ou PV-AG-2026#7.",
        "journal_step": "Ajouter ensuite une action concrete dans le journal: qualification, relance, reponse, rattachement ou cloture.",
        "request_register": _path_label(register_path),
        "action_log": _path_label(action_path),
    }


def _novice_steps() -> list[dict[str, str]]:
    return [
        {
            "title": "1. Comprendre la demande",
            "body": "Le sujet doit dire ce que la personne demande, sans adresse email ni numero de telephone.",
        },
        {
            "title": "2. Garder la preuve",
            "body": "La preuve est une reference locale: message, courrier, photo, PV, ticket syndic ou document.",
        },
        {
            "title": "3. Inscrire la suite",
            "body": "Chaque demande ouverte doit avoir une prochaine action concrete et un niveau de diffusion.",
        },
    ]
