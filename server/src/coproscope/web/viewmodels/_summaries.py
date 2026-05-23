from __future__ import annotations

from ._runtime import *

def _action_counter(actions: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(Counter(action.get(field, "") or "non renseigne" for action in actions))


def _scope_count(actions: list[dict[str, str]], scope: str) -> int:
    return len(
        [
            action
            for action in actions
            if action.get("domain") == scope
            or action.get("channel") == scope
            or action.get("source", "").lower() == scope
        ]
    )


def _action_summary(actions: list[dict[str, str]], preview_count: int) -> dict[str, object]:
    by_domain = _action_counter(actions, "domain")
    return {
        "total": len(actions),
        "preview_count": preview_count,
        "accounting": by_domain.get("comptes", 0),
        "privacy": by_domain.get("confidentialite", 0),
        "documents": by_domain.get("documents", 0),
        "decisions": by_domain.get("decisions", 0),
        "incidents": by_domain.get("incidents", 0),
        "by_domain": by_domain,
        "by_priority": _action_counter(actions, "priority"),
        "by_status": _action_counter(actions, "status"),
        "scope_counts": {
            "tous": len(actions),
            "comptes": _scope_count(actions, "comptes"),
            "confidentialite": _scope_count(actions, "confidentialite"),
            "documents": _scope_count(actions, "documents"),
            "decisions": _scope_count(actions, "decisions"),
            "incidents": _scope_count(actions, "incidents"),
            "syndic": _scope_count(actions, "syndic"),
            "ag": _scope_count(actions, "ag"),
        },
    }


def _cockpit_alerts(
    priorities: list[dict[str, str]],
    action_summary: dict[str, object],
    privacy: dict[str, object],
    piece_workshop: dict[str, object],
) -> list[dict[str, object]]:
    by_status = action_summary.get("by_status") if isinstance(action_summary.get("by_status"), dict) else {}
    privacy_summary = privacy.get("review_summary") if isinstance(privacy.get("review_summary"), dict) else {}
    workshop_summary = piece_workshop.get("summary") if isinstance(piece_workshop.get("summary"), dict) else {}
    alerts: list[dict[str, object]] = []
    if int(by_status.get("bloque", 0)):
        alerts.append(
            {
                "title": "Blocages a lever",
                "severity": "P0",
                "count": int(by_status.get("bloque", 0)),
                "detail": "Actions bloquees avant diffusion ou decision.",
                "href": "/actions?status=bloque",
            }
        )
    if int(by_status.get("a_demander", 0)):
        alerts.append(
            {
                "title": "Demandes au syndic",
                "severity": "P1",
                "count": int(by_status.get("a_demander", 0)),
                "detail": "Pieces, clarifications ou preuves a obtenir.",
                "href": "/actions?status=a_demander",
            }
        )
    if int(workshop_summary.get("with_local_proof") or 0):
        alerts.append(
            {
                "title": "Preuves locales a verifier",
                "severity": "P2",
                "count": int(workshop_summary.get("with_local_proof") or 0),
                "detail": "Preuves deja presentes mais a rattacher ou confirmer.",
                "href": "/pieces",
            }
        )
    if int(privacy_summary.get("blocked") or 0):
        alerts.append(
            {
                "title": "Diffusion bloquee",
                "severity": "P1",
                "count": int(privacy_summary.get("blocked") or 0),
                "detail": "Sorties a arbitrer avant partage.",
                "href": "/confidentialite",
            }
        )
    for priority in priorities[:3]:
        alerts.append({**priority, "count": ""})
    severity_rank = {"P0": 0, "P1": 1, "P2": 2, "OK": 4}
    return sorted(alerts, key=lambda row: severity_rank.get(str(row.get("severity", "P2")), 2))[:6]


def _evidence_summary(
    actions: list[dict[str, str]],
    piece_workshop: dict[str, object],
    decisions: dict[str, object],
    incidents: dict[str, object],
) -> dict[str, object]:
    workshop_summary = piece_workshop.get("summary") if isinstance(piece_workshop.get("summary"), dict) else {}
    decision_summary = decisions.get("summary") if isinstance(decisions.get("summary"), dict) else {}
    incident_summary = incidents.get("summary") if isinstance(incidents.get("summary"), dict) else {}
    items = piece_workshop.get("items") if isinstance(piece_workshop.get("items"), list) else []
    return {
        "actions_with_evidence": len([action for action in actions if action.get("evidence")]),
        "local_proofs_to_verify": int(workshop_summary.get("with_local_proof") or 0),
        "proofs_to_request": int(workshop_summary.get("without_local_proof") or 0),
        "decision_missing_proofs": int(decision_summary.get("missing_proofs") or 0),
        "incident_closure_proofs": int(incident_summary.get("closure_proofs_expected") or 0),
        "items": [item for item in items if isinstance(item, dict)][:6],
    }


def _trust_summary(instance: InstanceConfig, documents: dict[str, object], privacy: dict[str, object]) -> dict[str, object]:
    document_table = documents.get("documents")
    manifest_path = _safe_register(instance, "manifest")
    manifest = _read_table(manifest_path) if manifest_path else DataTable(Path(""), [], [])
    docai = instance.docai_settings()
    privacy_summary = privacy.get("review_summary") if isinstance(privacy.get("review_summary"), dict) else {}
    hashed_documents = (
        len([row for row in document_table.rows if row.get("sha256")])
        if isinstance(document_table, DataTable)
        else 0
    )
    document_count = document_table.count if isinstance(document_table, DataTable) else 0
    return {
        "cards": [
            {
                "label": "Mode local",
                "value": docai.get("privacy", "local_only"),
                "detail": f"DocAI {docai.get('mode', 'off')}; donnees servies depuis l'instance locale.",
            },
            {
                "label": "Empreintes documents",
                "value": f"{hashed_documents}/{document_count}",
                "detail": "Documents inventaries avec SHA-256 dans le registre.",
            },
            {
                "label": "Manifest hash",
                "value": manifest.count if manifest.exists else "absent",
                "detail": "Registre manifest_sha256 disponible pour controle d'integrite.",
            },
            {
                "label": "Diffusion",
                "value": int(privacy_summary.get("blocked") or 0),
                "detail": "Sorties encore bloquees par PrivacyOps.",
            },
            {
                "label": "Pack local",
                "value": "pret",
                "detail": "Export local prepare sans zones de collecte ni journaux internes.",
                "href": "/exports/local.zip",
            },
            {
                "label": "Coffre chiffre/signe",
                "value": "a raccorder",
                "detail": "Le cockpit n'expose pas encore de statut de coffre signe pour cette instance.",
            },
        ]
    }


def _ux_public_tokens(value: str) -> list[str]:
    normalized = value.replace("\\", "/").lower()
    tokenized = "".join(char if char.isalnum() else " " for char in normalized)
    return tokenized.split()


def _contains_forbidden_ux_reference(value: object, *, allow_route: bool = False) -> bool:
    normalized = str(value or "").replace("\\", "/").strip().lower()
    return _contains_forbidden_ux_reference_cached(normalized, allow_route)


@lru_cache(maxsize=32768)
def _contains_forbidden_ux_reference_cached(normalized: str, allow_route: bool = False) -> bool:
    if not normalized:
        return False
    if not any(marker in normalized for marker in _UX_SUSPICIOUS_SUBSTRINGS):
        return False
    first_match = _UX_PUBLIC_TOKEN_RE.search(normalized)
    first_token = first_match.group(0) if first_match else ""
    has_absolute_marker = (
        "file://" in normalized
        or "://" in normalized
        or (len(normalized) > 2 and normalized[1:3] == ":/")
        or normalized.startswith("//")
        or (normalized.startswith("/") and not allow_route)
        or (allow_route and first_token in FORBIDDEN_UX_PUBLIC_ROOTS)
    )
    return has_absolute_marker or bool(_FORBIDDEN_UX_PUBLIC_TOKEN_RE.search(normalized))


def _public_text(value: object, fallback: str = "") -> str:
    text = _clip(str(value or "").strip(), 140)
    if not text:
        return fallback
    if _contains_forbidden_ux_reference(text):
        return fallback or UX_REDACTED_REFERENCE
    return text


def _public_href(value: object, fallback: str = "/actions") -> str:
    href = str(value or "").strip()
    if not href:
        return fallback
    if _contains_forbidden_ux_reference(href, allow_route=True):
        return fallback
    if href.startswith("/") and not href.startswith("//"):
        return href
    return fallback


def _sanitize_ux_public(
    value: Any,
    key: str = "",
    _text_cache: dict[str, str] | None = None,
    _href_cache: dict[str, str] | None = None,
) -> Any:
    if _text_cache is None:
        _text_cache = {}
    if _href_cache is None:
        _href_cache = {}
    if isinstance(value, dict):
        href_context = key == "hrefs" or key.endswith("_hrefs")
        return {
            item_key: _sanitize_ux_public(
                item_value,
                "href" if href_context else item_key,
                _text_cache,
                _href_cache,
            )
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_ux_public(item, key, _text_cache, _href_cache) for item in value]
    if isinstance(value, str):
        if key == "href" or key.endswith("_href") or key == "route" or key.endswith("_route") or key == "opened_from":
            if value not in _href_cache:
                _href_cache[value] = _public_href(value)
            return _href_cache[value]
        if value not in _text_cache:
            _text_cache[value] = UX_REDACTED_REFERENCE if _contains_forbidden_ux_reference(value) else value
        return _text_cache[value]
    return value


def _ux_tone(priority: str, status: str = "") -> str:
    priority = (priority or "").upper()
    status = (status or "").lower()
    if priority in {"P0", "P1"} or status in {"bloque", "a_demander"}:
        return "danger"
    if priority == "P2" or status in {"a_revoir", "a_confirmer", "a_verifier"}:
        return "warn"
    if priority == "OK" or status == "clos":
        return "ok"
    return "info"


def _ux_status_label(status: str) -> str:
    return {
        "a_demander": "A demander",
        "a_relancer": "A relancer",
        "a_verifier": "Preuve a verifier",
        "a_traiter": "A traiter",
        "a_revoir": "A arbitrer",
        "a_confirmer": "A confirmer",
        "bloque": "Bloque",
        "clos": "Termine",
    }.get(status or "", status or "A traiter")


def _ux_lane(action: dict[str, str]) -> str:
    status = action.get("status", "")
    domain = action.get("domain", "")
    channel = action.get("channel", "")
    if status == "bloque" or domain == "confidentialite":
        return "diffusion_risk"
    if channel == "syndic" or status == "a_demander":
        return "waiting_syndic"
    if status in {"a_verifier", "a_confirmer"}:
        return "proofs_to_verify"
    if domain in {"decisions", "incidents"}:
        return "memory"
    return "this_week"


def _ux_work_item(action: dict[str, str]) -> dict[str, object]:
    evidence = _public_text(action.get("evidence"), "preuve attendue a preciser")
    status = action.get("status", "a_traiter")
    priority = action.get("priority", "P2")
    lane = _ux_lane(action)
    proof_state = "missing" if status == "a_demander" else "blocked" if status == "bloque" else "candidate"
    if status in {"a_verifier", "a_confirmer"}:
        proof_state = "local"
    if status == "clos":
        proof_state = "verified"
    diffusion_status = "blocked" if status == "bloque" else "after_redaction" if action.get("domain") == "confidentialite" else "cs_only"
    if status == "clos":
        diffusion_status = "copro_ok"
    return {
        "id": _public_text(
            action.get("id") or _stable_action_id("UX", 0, action.get("title", ""), action.get("source", "")),
            _stable_action_id("UX", 0, action.get("title", ""), action.get("source", "")),
        ),
        "kind": _public_text(action.get("domain"), "general"),
        "title": _public_text(action.get("title"), "Action a traiter"),
        "priority": priority,
        "status": status,
        "status_label": _ux_status_label(status),
        "tone": _ux_tone(priority, status),
        "lane": lane,
        "why": _public_text(action.get("detail"), "Ce point demande une verification par le conseil syndical."),
        "proof": {
            "state": proof_state,
            "label": evidence,
            "refs": [evidence] if evidence else [],
        },
        "action": {
            "label": _public_text(action.get("next_step"), "Verifier et noter la prochaine etape."),
            "kind": "ask_syndic" if lane == "waiting_syndic" else "arbitrate" if lane == "diffusion_risk" else "verify",
            "due_on": "",
            "owner": _public_text(action.get("owner"), "Conseil syndical"),
        },
        "diffusion": {
            "status": diffusion_status,
            "label": {
                "blocked": "Ne pas diffuser",
                "after_redaction": "Partager apres masquage",
                "cs_only": "Conseil syndical seulement",
                "copro_ok": "Partage possible",
            }.get(diffusion_status, "Conseil syndical seulement"),
            "reason": "Limiter le partage aux informations utiles et deja verifiees.",
        },
        "memory": {
            "timeline_ref": _public_text(action.get("id"), ""),
            "handover_note": "A reprendre en passation tant que l'action n'est pas cloturee.",
            "pack_section": _public_text(action.get("domain_label"), "Actions"),
        },
        "href": _public_href(action.get("href"), "/actions"),
        "source": {
            "module": _public_text(action.get("source"), "Module"),
            "object_id": _public_text(action.get("id"), ""),
        },
    }


def _ux_nav_item(label: str, href: str, page: str, active_page: str, *, icon: str, count: object = "") -> dict[str, object]:
    return {
        "label": label,
        "href": href,
        "page": page,
        "icon": icon,
        "count": count,
        "is_active": page == active_page,
    }


def _route_href(path: str = "/actions", **params: object) -> str:
    clean_path = _public_href(path, "/actions")
    query = [
        f"{quote(str(key), safe='')}={quote(str(value), safe='')}"
        for key, value in params.items()
        if value is not None and str(value) != ""
    ]
    return f"{clean_path}?{'&'.join(query)}" if query else clean_path


def _parse_iso_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _date_label(value: object, fallback: str = "A fixer") -> str:
    parsed = _parse_iso_date(value)
    if not parsed:
        return fallback
    return f"{parsed.day:02d}/{parsed.month:02d}/{parsed.year}"
