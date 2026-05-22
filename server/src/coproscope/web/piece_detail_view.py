from __future__ import annotations

import re
from typing import Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from ..core.common import InstanceConfig
from .viewmodel import build_dashboard_model


SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
MASKED_REFERENCE = "reference-locale-masquee"
PRIVATE_MARKERS = {
    "raw",
    "restricted",
    "logs",
    "private",
    "system",
    "users",
    "home",
    "tmp",
    "etc",
    "root",
}


def public_piece_id(value: object) -> str:
    text = " ".join(str(value or "").strip().split())[:140]
    normalized = text.replace("\\", "/").lower()
    tokens = [token for token in re.split(r"[^a-z0-9]+", normalized) if token]
    if (
        not text
        or ".." in text
        or "/" in text
        or "\\" in text
        or "://" in normalized
        or (len(normalized) > 2 and normalized[1:3] == ":/")
        or any(token in PRIVATE_MARKERS for token in tokens)
        or not SAFE_ID_PATTERN.fullmatch(text)
    ):
        return MASKED_REFERENCE
    return text


def build_piece_detail(
    instance: InstanceConfig,
    year: int,
    piece_id: str,
    query: Mapping[str, str] | None = None,
    dashboard_model: dict[str, object] | None = None,
) -> dict[str, object]:
    safe_piece_id = public_piece_id(piece_id)
    model = dashboard_model if dashboard_model is not None else build_dashboard_model(instance, year)
    item = _find_piece_item(model, safe_piece_id)
    if not item:
        return _empty_detail(safe_piece_id)

    piece = _piece_block(item, safe_piece_id)
    proof = _proof_block(item, piece)
    linked = _linked_block(item, piece["id"])
    diffusion = _diffusion_block(item)
    actions = _actions_block(item, piece["id"], query or {})
    history = _history_block(item, proof)

    return {
        "state": "found",
        "context": {
            "route": f"/pieces/{piece['id']}",
            "title": "Detail piece/preuve",
            "back_href": "/pieces?proof=missing",
            "notice": "CoproScope prepare ou trace les suites; aucun envoi automatique n'est declenche.",
        },
        "piece": piece,
        "proof": proof,
        "linked": linked,
        "diffusion": diffusion,
        "actions": actions,
        "history": history,
    }


def _find_piece_item(model: dict[str, object], piece_id: str) -> dict[str, object]:
    if piece_id == MASKED_REFERENCE:
        return {}
    ux = model.get("ux") if isinstance(model.get("ux"), dict) else {}
    pieces = ux.get("pieces") if isinstance(ux, dict) and isinstance(ux.get("pieces"), dict) else {}
    priority_views = ux.get("priority_views") if isinstance(ux, dict) and isinstance(ux.get("priority_views"), dict) else {}
    missing_view = (
        priority_views.get("missing_pieces")
        if isinstance(priority_views.get("missing_pieces"), dict)
        else {}
    )

    base_items = _list_of_dicts(pieces.get("items")) + _list_of_dicts(pieces.get("empty_state", {}).get("examples") if isinstance(pieces.get("empty_state"), dict) else [])
    missing_items = _list_of_dicts(missing_view.get("items")) if isinstance(missing_view, dict) else []
    candidates: list[dict[str, object]] = []
    candidates.extend(base_items)
    candidates.extend(missing_items)

    base_by_key: dict[str, dict[str, object]] = {}
    for item in base_items:
        for key in _piece_match_keys(item):
            base_by_key.setdefault(key, item)

    for item in candidates:
        if piece_id not in _piece_match_keys(item):
            continue
        merged = dict(base_by_key.get(piece_id, {}))
        merged.update(item)
        return merged
    return {}


def _piece_match_keys(item: dict[str, object]) -> set[str]:
    keys = {
        public_piece_id(item.get("id")),
        public_piece_id(item.get("related_action_id")),
        public_piece_id(item.get("related_event_id")),
    }
    related = item.get("related") if isinstance(item.get("related"), dict) else {}
    keys.add(public_piece_id(related.get("action_id") if isinstance(related, dict) else ""))
    keys.add(public_piece_id(related.get("event_id") if isinstance(related, dict) else ""))
    return {key for key in keys if key != MASKED_REFERENCE}


def _piece_block(item: dict[str, object], fallback_id: str) -> dict[str, object]:
    piece_id = public_piece_id(item.get("id")) if item.get("id") else fallback_id
    status = _safe_text(item.get("status"), "a_demander")
    label = _human_label(item.get("expected_piece") or item.get("title") or item.get("piece"), "Piece attendue")
    reason = _human_sentence(
        item.get("reason") or item.get("proof_purpose") or item.get("next_step"),
        "Cette piece manque pour prouver le sujet rattache avant de clore le point.",
    )
    return {
        "id": piece_id if piece_id != MASKED_REFERENCE else fallback_id,
        "label": label,
        "status": status,
        "status_label": _status_label(status, item.get("status_label")),
        "priority_label": _safe_text(item.get("criticality_label") or item.get("priority_label"), "Priorite a confirmer"),
        "rubric_label": _safe_text(item.get("rubric_label"), "Pieces"),
        "holder_label": _safe_text(item.get("owner_label"), "Syndic ou conseil syndical"),
        "why_it_matters": reason,
        "next_step": _human_sentence(item.get("next_step"), "Relancer le syndic ou ajouter la reponse recue comme piece candidate."),
        "is_fictive": bool(item.get("is_fictive")),
    }


def _proof_block(item: dict[str, object], piece: dict[str, object]) -> dict[str, object]:
    status = str(piece.get("status") or "")
    candidate_docs = _candidate_docs(item)
    verified_docs = _verified_docs(item)
    if status == "a_verifier" or candidate_docs:
        state_label = "Piece recue a verifier"
        state_detail = "Une piece candidate existe; elle devient preuve finale seulement apres controle explicite."
    elif status == "rattachee" or verified_docs:
        state_label = "Preuve finale validee"
        state_detail = "La preuve est rattachee, mais sa diffusion reste a verifier avant partage."
    else:
        state_label = "Preuve finale manquante"
        state_detail = "Aucune preuve finale n'est validee pour ce point."
    return {
        "expected_label": _human_label(item.get("proof_expected_label") or piece.get("label"), "Preuve attendue"),
        "state_label": state_label,
        "state_detail": state_detail,
        "candidate_docs": candidate_docs,
        "verified_docs": verified_docs,
        "candidate_count": len(candidate_docs),
        "verified_count": len(verified_docs),
        "states": [
            "Piece manquante",
            "Piece recue a verifier",
            "Preuve finale validee seulement apres controle explicite",
        ],
    }


def _candidate_docs(item: dict[str, object]) -> list[dict[str, str]]:
    docs = _list_of_dicts(item.get("candidate_docs"))
    if not docs and item.get("status") == "a_verifier":
        docs = _list_of_dicts(item.get("linked_documents"))
    return [_doc_block(doc, "Piece candidate a verifier") for doc in docs[:8]]


def _verified_docs(item: dict[str, object]) -> list[dict[str, str]]:
    if item.get("status") != "rattachee":
        return []
    return [_doc_block(doc, "Preuve rattachee") for doc in _list_of_dicts(item.get("linked_documents"))[:8]]


def _doc_block(doc: dict[str, object], fallback_status: str) -> dict[str, str]:
    doc_id = public_piece_id(doc.get("id"))
    return {
        "id": "" if doc_id == MASKED_REFERENCE else doc_id,
        "label": _human_label(doc.get("label"), "Document lie"),
        "status_label": _safe_text(doc.get("status_label"), fallback_status),
        "href": _safe_href(doc.get("href"), "/documents"),
    }


def _linked_block(item: dict[str, object], piece_id: object) -> dict[str, object]:
    action_href = _safe_href(item.get("action_href") or item.get("href"), "/pieces?proof=missing")
    action_label = _human_label(item.get("action_label") or item.get("point_label"), "Point lie")
    relance_href = _append_query(
        _safe_href(item.get("request_href"), "/demandes/relance"),
        {"piece_detail": str(piece_id or "")},
    )
    deposit_href = _append_query(
        _safe_href(item.get("deposit_href"), "/depot?intent=proof"),
        {
            "status": "reponse-recue",
            "return": "pieces",
            "piece_detail": str(piece_id or ""),
        },
    )
    docs = [_doc_block(doc, "Document lie") for doc in _list_of_dicts(item.get("linked_documents"))[:8]]
    return {
        "action": {
            "label": action_label,
            "href": action_href,
            "type_label": "Controle comptes" if action_href.startswith("/comptes") else "Action liee",
        },
        "request": {
            "label": "Relance syndic preparee",
            "href": relance_href,
        },
        "deposit": {
            "label": "Depot de reponse recue",
            "href": deposit_href,
        },
        "documents": docs,
    }


def _diffusion_block(item: dict[str, object]) -> dict[str, str]:
    label = _safe_text(item.get("diffusion_label"), "Conseil syndical seulement")
    if "blo" in label.lower():
        state = "Bloque pour l'export"
        detail = "Ne pas partager avant arbitrage."
    elif "masqu" in label.lower() or "biff" in label.lower():
        state = "Diffusable apres masquage"
        detail = "Preparer une version diffusable avant toute sortie."
    else:
        state = "CS seulement"
        detail = "Visible pour le conseil syndical; relire avant export ou partage externe."
    return {
        "label": label,
        "state": state,
        "detail": detail,
        "review_href": "/confidentialite",
    }


def _actions_block(item: dict[str, object], piece_id: object, query: Mapping[str, str]) -> list[dict[str, str]]:
    deposit_href = _append_query(
        _safe_href(item.get("deposit_href"), "/depot?intent=proof"),
        {
            "status": "reponse-recue",
            "return": "pieces",
            "piece_detail": str(piece_id or ""),
        },
    )
    relance_href = _append_query(
        _safe_href(item.get("request_href"), "/demandes/relance"),
        {"piece_detail": str(piece_id or "")},
    )
    action_href = _safe_href(item.get("action_href") or item.get("href"), "/pieces?proof=missing")
    back_href = _safe_href(query.get("return_to") if query else "", "/pieces?proof=missing")
    return [
        {"id": "back", "label": "Retour aux pieces manquantes", "href": back_href, "kind": "secondary"},
        {"id": "relance", "label": "Relancer syndic", "href": relance_href, "kind": "primary"},
        {"id": "received", "label": "Ajouter reponse recue", "href": deposit_href, "kind": "secondary"},
        {"id": "open-context", "label": "Voir le point lie", "href": action_href, "kind": "secondary"},
        {"id": "diffusion", "label": "Verifier diffusion", "href": "/confidentialite", "kind": "secondary"},
    ]


def _history_block(item: dict[str, object], proof: dict[str, object]) -> list[dict[str, str]]:
    return [
        {
            "label": "Piece attendue",
            "status": _safe_text(item.get("status_label"), "A demander"),
            "note": _safe_text(item.get("reason"), "Le besoin de preuve est ouvert."),
        },
        {
            "label": "Reponse recue",
            "status": str(proof.get("state_label") or "Preuve finale manquante"),
            "note": "Une reponse ajoutee reste candidate jusqu'au controle du conseil syndical.",
        },
        {
            "label": "Decision de preuve",
            "status": "Controle attendu",
            "note": "La validation finale est une action humaine tracee, pas une deduction automatique.",
        },
    ]


def _empty_detail(piece_id: str) -> dict[str, object]:
    safe_id = piece_id if piece_id != MASKED_REFERENCE else MASKED_REFERENCE
    return {
        "state": "missing",
        "context": {
            "route": f"/pieces/{safe_id}",
            "title": "Detail piece/preuve",
            "back_href": "/pieces?proof=missing",
            "notice": "CoproScope prepare ou trace les suites; aucun envoi automatique n'est declenche.",
        },
        "piece": {
            "id": safe_id,
            "label": "Piece introuvable dans ce coffre local fictif",
            "status_label": "Piece introuvable",
            "priority_label": "A verifier",
            "rubric_label": "Pieces",
            "holder_label": "Syndic ou conseil syndical",
            "why_it_matters": "Cette reference ne correspond pas a une piece suivie dans les donnees chargees.",
            "next_step": "Revenir aux pieces manquantes ou ajouter une reponse recue depuis le depot.",
            "is_fictive": True,
        },
        "proof": {
            "expected_label": "Preuve attendue a preciser",
            "state_label": "Preuve finale manquante",
            "state_detail": "Aucune preuve finale n'est validee pour cette reference.",
            "candidate_docs": [],
            "verified_docs": [],
            "candidate_count": 0,
            "verified_count": 0,
            "states": [
                "Piece manquante",
                "Piece recue a verifier",
                "Preuve finale validee seulement apres controle explicite",
            ],
        },
        "linked": {
            "action": {"label": "Point a rattacher", "href": "/pieces?proof=missing", "type_label": "A completer"},
            "request": {"label": "Relance syndic a preparer", "href": "/demandes/relance"},
            "deposit": {"label": "Depot de reponse recue", "href": "/depot?intent=proof"},
            "documents": [],
        },
        "diffusion": {
            "label": "Diffusion a arbitrer",
            "state": "CS seulement",
            "detail": "Verifier le rattachement avant tout partage.",
            "review_href": "/confidentialite",
        },
        "actions": [
            {"id": "back", "label": "Retour aux pieces manquantes", "href": "/pieces?proof=missing", "kind": "primary"},
            {"id": "received", "label": "Ajouter reponse recue", "href": "/depot?intent=proof&return=pieces", "kind": "secondary"},
            {"id": "relance", "label": "Relancer syndic", "href": "/demandes/relance", "kind": "secondary"},
        ],
        "history": [],
    }


def _list_of_dicts(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _safe_text(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").replace("\x00", " ").split())
    if not text:
        return fallback
    normalized = text.replace("\\", "/").lower()
    tokens = [token for token in re.split(r"[^a-z0-9]+", normalized) if token]
    if (
        "file://" in normalized
        or "://" in normalized
        or (len(normalized) > 2 and normalized[1:3] == ":/")
        or normalized.startswith("/")
        or any(token in PRIVATE_MARKERS for token in tokens)
    ):
        return fallback
    return text[:240]


def _human_label(value: object, fallback: str) -> str:
    text = _safe_text(value, fallback)
    if "_" in text and text.upper() == text:
        text = text.replace("_", " ").lower().capitalize()
    return text


def _human_sentence(value: object, fallback: str) -> str:
    text = _human_label(value, fallback)
    if not text.endswith((".", "?", "!")):
        text = f"{text}."
    return text


def _status_label(status: str, label: object) -> str:
    known = {
        "a_demander": "Piece ou preuve a demander",
        "a_deposer": "Reponse recue a deposer",
        "a_verifier": "Piece recue a verifier",
        "rattachee": "Preuve finale rattachee",
        "exemple": "Exemple fictif",
    }
    return known.get(status, _safe_text(label, "Statut a verifier"))


def _safe_href(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text:
        return fallback
    normalized = text.replace("\\", "/").lower()
    if (
        not text.startswith(("/", "#"))
        or text.startswith("//")
        or "://" in normalized
        or any(f"/{marker}/" in normalized for marker in PRIVATE_MARKERS)
    ):
        return fallback
    return text[:500]


def _append_query(href: str, additions: Mapping[str, str]) -> str:
    split = urlsplit(href)
    query = dict(parse_qsl(split.query, keep_blank_values=False))
    for key, value in additions.items():
        if value and key not in query:
            query[key] = value
    return urlunsplit((split.scheme, split.netloc, split.path, urlencode(query), split.fragment))
