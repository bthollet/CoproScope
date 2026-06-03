from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlencode


DEMO_BLOCKER_ID = "BLOCK-FICTIF-RELANCE-ASCENSEUR"
SAFE_MISSING_ID = "reference-locale-masquee"
QUERY_KEYS = ("scope", "selected", "audience")
PRIVATE_TOKENS = {"raw", "restricted", "logs", "private", "system"}
PRIVATE_ROOTS = {"users", "home", "var", "tmp", "etc", "opt", "root", "mnt", "volumes"}


def _list_of_dicts(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _route_tokens(value: str) -> list[str]:
    normalized = value.replace("\\", "/").lower()
    tokenized = "".join(char if char.isalnum() else " " for char in normalized)
    return tokenized.split()


def _contains_private_reference(value: object) -> bool:
    normalized = str(value or "").replace("\\", "/").strip().lower()
    if not normalized:
        return False
    tokens = _route_tokens(normalized)
    first_token = tokens[0] if tokens else ""
    has_path_marker = (
        "file://" in normalized
        or "://" in normalized
        or (len(normalized) > 2 and normalized[1:3] == ":/")
        or normalized.startswith("//")
        or normalized.startswith("/")
        or first_token in PRIVATE_ROOTS
    )
    return has_path_marker or any(token in PRIVATE_TOKENS for token in tokens)


def public_blocker_id(value: object) -> str:
    text = " ".join(str(value or "").strip().split())[:120]
    if not text or _contains_private_reference(text):
        return SAFE_MISSING_ID
    return text


def _public_text(value: object, fallback: str) -> str:
    text = " ".join(str(value or "").strip().split())
    if not text or _contains_private_reference(text):
        return fallback
    return text[:220]


def _context_query(query: dict[str, str] | None) -> dict[str, str]:
    values: dict[str, str] = {}
    for key in QUERY_KEYS:
        value = str((query or {}).get(key) or "").strip()
        if value and not _contains_private_reference(value):
            values[key] = value[:120]
    return values


def href_with_query(path: str, query: dict[str, str] | None = None, **extra: str) -> str:
    values = _context_query(query)
    for key, value in extra.items():
        clean = str(value or "").strip()
        if clean and not _contains_private_reference(clean):
            values[key] = clean[:120]
    return f"{path}?{urlencode(values)}" if values else path


def passation_blocker_href(blocker_id: object, query: dict[str, str] | None = None) -> str:
    return href_with_query(f"/exports/passation/blocages/{public_blocker_id(blocker_id)}", query)


def _demo_blocker(query: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "id": DEMO_BLOCKER_ID,
        "label": "Relance ascenseur non tracee",
        "detail": "Il manque la date et le canal d'envoi hors CoproScope.",
        "reason": "Brouillon pris pour un envoi reel si le pack part sans trace.",
        "type_label": "Relance syndic FICTIF",
        "href": passation_blocker_href(DEMO_BLOCKER_ID, query),
    }


def enrich_passation_preview_blocker_links(
    preview: dict[str, Any],
    query: dict[str, str] | None = None,
) -> dict[str, Any]:
    enriched = dict(preview)
    context_query = _context_query(query)

    omitted = dict(enriched.get("omitted")) if isinstance(enriched.get("omitted"), dict) else {}
    omitted_items = []
    for index, item in enumerate(_list_of_dicts(omitted.get("items")), start=1):
        row = dict(item)
        row_id = public_blocker_id(row.get("id") or f"omission-{index}")
        row["id"] = row_id
        row["review_href"] = passation_blocker_href(row_id, context_query)
        omitted_items.append(row)
    omitted["items"] = omitted_items
    enriched["omitted"] = omitted

    blockers = []
    seen: set[str] = set()
    for index, item in enumerate(_list_of_dicts(enriched.get("blockers")), start=1):
        row = dict(item)
        row_id = public_blocker_id(row.get("id") or f"blocker-{index}")
        row["id"] = row_id
        row["href"] = passation_blocker_href(row_id, context_query)
        blockers.append(row)
        seen.add(row_id)

    if context_query.get("scope") == "event" and context_query.get("selected") and DEMO_BLOCKER_ID not in seen:
        blockers.append(_demo_blocker(context_query))
    enriched["blockers"] = blockers
    return enriched


def _candidate_blockers(preview: dict[str, Any], query: dict[str, str]) -> list[dict[str, Any]]:
    candidates = []
    candidates.extend(_list_of_dicts(preview.get("blockers")))
    omitted = preview.get("omitted") if isinstance(preview.get("omitted"), dict) else {}
    for item in _list_of_dicts(omitted.get("items")):
        row = dict(item)
        row.setdefault("detail", row.get("reason"))
        candidates.append(row)
    candidates.append(_demo_blocker(query))
    return candidates


def _find_blocker(preview: dict[str, Any], blocker_id: str, query: dict[str, str]) -> dict[str, Any] | None:
    wanted = public_blocker_id(blocker_id)
    for item in _candidate_blockers(preview, query):
        if public_blocker_id(item.get("id")) == wanted:
            return item
    return None


def _summary_cards(preview: dict[str, Any]) -> list[dict[str, str]]:
    summary = preview.get("summary") if isinstance(preview.get("summary"), dict) else {}
    formats = _list_of_dicts(preview.get("formats") or preview.get("formats_available"))
    return [
        {"label": "Inclus", "value": str(summary.get("included_events_count") or 0), "detail": "evenements"},
        {"label": "A verifier", "value": str(summary.get("diffusion_limited_count") or 0), "detail": "diffusions"},
        {"label": "Bloques", "value": str(len(_list_of_dicts(preview.get("blockers")))), "detail": "points"},
        {"label": "Formats", "value": str(len(formats) or 2), "detail": "derives"},
        {"label": "Watermark", "value": "visible", "detail": "non source"},
    ]


def _summary_counts(preview: dict[str, Any]) -> dict[str, Any]:
    summary = preview.get("summary") if isinstance(preview.get("summary"), dict) else {}
    formats = _list_of_dicts(preview.get("formats") or preview.get("formats_available"))
    return {
        "included_count": int(summary.get("included_events_count") or 0),
        "review_count": int(summary.get("diffusion_limited_count") or 0),
        "blocked_count": len(_list_of_dicts(preview.get("blockers"))),
        "formats_count": len(formats) or 2,
        "watermark_visible": bool(preview.get("watermark") or preview.get("context")),
    }


def _known_detail(blocker: dict[str, Any], query: dict[str, str]) -> dict[str, Any]:
    blocker_id = public_blocker_id(blocker.get("id"))
    is_demo = blocker_id == DEMO_BLOCKER_ID
    title = _public_text(blocker.get("label"), "Point a verifier avant export")
    reason = _public_text(blocker.get("detail") or blocker.get("reason"), "Une verification manque avant export.")
    back_href = href_with_query("/exports/passation", query)
    request_id = "REQ-FICTIF-ASCENSEUR-SYNDIC" if is_demo else "REQ-FICTIF-ASSURANCE-B12"
    action_id = "ACTION-FICTIF-ASC-2025"
    if not is_demo and blocker_id == "preuves-manquantes":
        request_id = ""
        action_id = ""
    return {
        "state": "found",
        "context": {
            "title": "Detail blocage export",
            "source_of_truth": False,
            "watermark": "export derive, non source de verite",
            "scope": _context_query(query),
            "back_href": back_href,
        },
        "summary_cards": [],
        "blocker": {
            "id": blocker_id,
            "title": title,
            "status_label": "Bloque export",
            "user_reason": "Date et canal d'envoi externe manquent." if is_demo else reason,
            "risk_label": "Brouillon pris pour un envoi reel" if is_demo else "Partage avant preuve ou diffusion relue",
            "safe_action": "Noter l'envoi hors CoproScope" if is_demo else "Relire le point avant export",
            "audience": "Conseil syndical restreint",
            "source_label": "scenario FICTIF" if is_demo else _public_text(blocker.get("type_label"), "Element de passation"),
        },
        "excluded_items": [
            {
                "label": "Brouillon de relance non envoye" if is_demo else title,
                "reason": "Le texte copiable reste local tant qu'aucun envoi externe n'est note." if is_demo else reason,
                "status_label": "Exclu",
            },
            {
                "label": "Reference privee remplacee par un libelle",
                "reason": "La page ne publie ni chemin local, ni piece originale, ni contenu non relu.",
                "status_label": "Masque",
            },
            {
                "label": "Synthese action ascenseur" if is_demo else "Synthese de passation",
                "reason": "Peut sortir seulement avec watermark et preuve manquante visible.",
                "status_label": "A verifier",
            },
        ],
        "required_proofs": [
            {"label": "Date d'envoi", "status": "missing"},
            {"label": "Canal et destinataire", "status": "missing"},
            {"label": "Note de suivi", "status": "to_fill"},
        ],
        "confidentiality_checks": [
            {"status": "OK", "label": "Aucun chemin local affiche"},
            {"status": "OK", "label": "Export derive seulement"},
            {"status": "WARN", "label": "Preuve d'envoi absente"},
            {"status": "BLOCKED", "label": "Piece originale bloquee"},
        ],
        "format_impact": [
            {"id": "txt", "label": "TXT verrouille", "enabled": False},
            {"id": "json", "label": "JSON audit", "enabled": True},
            {"id": "clipboard", "label": "Presse-papier verrouille", "enabled": False},
        ],
        "actions": {
            "download": {
                "label": "Preparer dossier derive - verrouille",
                "enabled": False,
                "disabled_reason": title,
            },
            "record_external_send": {
                "label": "Noter l'envoi hors CoproScope",
                "href": href_with_query("/demandes/relance", query, request_id=request_id),
            },
            "record_external_send_with_action": {
                "label": "Noter l'envoi depuis l'action",
                "href": href_with_query("/demandes/relance", query, request_id="REQ-FICTIF-ASSURANCE-B12", action_id=action_id),
            },
            "exclude_from_pack": {
                "label": "Exclure cette relance du pack" if is_demo else "Exclure cet element du pack",
                "href": href_with_query("/exports/passation", query, exclude=blocker_id),
            },
            "back_preview": {"label": "Retour a l'apercu", "href": back_href},
            "view_action": {"label": "Voir action", "href": href_with_query(f"/actions/{action_id}", query) if action_id else href_with_query("/actions", query)},
        },
    }


def _missing_detail(blocker_id: str, query: dict[str, str]) -> dict[str, Any]:
    safe_id = public_blocker_id(blocker_id)
    return {
        "state": "missing",
        "context": {
            "title": "Detail blocage export",
            "source_of_truth": False,
            "watermark": "export derive, non source de verite",
            "scope": _context_query(query),
            "back_href": href_with_query("/exports/passation", query),
        },
        "summary_cards": [],
        "blocker": {
            "id": safe_id,
            "title": "Blocage introuvable",
            "status_label": "A verifier",
            "user_reason": "Ce point n'est pas dans l'apercu courant.",
            "risk_label": "Reference absente du pack filtre",
            "safe_action": "Revenir a l'apercu avant export",
            "audience": "Conseil syndical",
            "source_label": "reference masquee" if safe_id == SAFE_MISSING_ID else safe_id,
        },
        "excluded_items": [],
        "required_proofs": [],
        "confidentiality_checks": [{"status": "OK", "label": "Aucun identifiant prive affiche"}],
        "format_impact": [],
        "actions": {
            "download": {
                "label": "Preparer dossier derive - verrouille",
                "enabled": False,
                "disabled_reason": "Blocage introuvable dans cet apercu.",
            },
            "back_preview": {"label": "Retour a l'apercu", "href": href_with_query("/exports/passation", query)},
            "view_action": {"label": "Voir actions ouvertes", "href": href_with_query("/actions", query)},
        },
    }


def build_passation_blocker_detail(
    preview: dict[str, Any],
    blocker_id: object,
    query: dict[str, str] | None = None,
) -> dict[str, Any]:
    safe_query = _context_query(query)
    safe_id = public_blocker_id(blocker_id)
    blocker = _find_blocker(preview, safe_id, safe_query)
    detail = _known_detail(blocker, safe_query) if blocker else _missing_detail(safe_id, safe_query)
    detail["summary"] = _summary_counts(preview)
    detail["summary_cards"] = _summary_cards(preview)
    return detail
