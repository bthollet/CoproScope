from __future__ import annotations



def _normalize_point_kind(value: str) -> str:
    token = _token(value)
    aliases = {
        "ag": "ag",
        "assemblee_generale": "ag",
        "resolution": "decision",
        "decision": "decision",
        "demande": "demande",
        "request": "demande",
        "facture": "facture",
        "invoice": "facture",
        "incident": "incident",
        "chantier": "chantier",
        "travaux": "chantier",
        "contentieux": "contentieux",
    }
    normalized = aliases.get(token, token)
    return normalized if normalized in POINT_KINDS else "preuve_libre"


def _normalize_action_kind(value: str) -> str:
    token = _token(value)
    aliases = {
        "verification": "verifier",
        "verifier": "verifier",
        "demande": "demander",
        "demander": "demander",
        "relance": "relancer",
        "relancer": "relancer",
        "biffage": "biffer",
        "biffer": "biffer",
        "transmission": "transmettre",
        "transmettre": "transmettre",
        "classement": "classer",
        "classer": "classer",
    }
    normalized = aliases.get(token, token)
    return normalized if normalized in ACTION_KINDS else "verifier"


def _normalize_proof_intent(value: str) -> str:
    token = _token(value)
    aliases = {
        "presence": "presence",
        "decision": "decision",
        "reception": "reception",
        "execution": "execution",
        "paiement": "paiement",
        "payment": "paiement",
        "refus": "refus",
        "cloture": "cloture",
        "closure": "cloture",
    }
    normalized = aliases.get(token, token)
    return normalized if normalized in PROOF_INTENTS else "presence"


def _safe_local_reference(value: str) -> tuple[str, bool]:
    text = _cell(value)
    if not text:
        return "", False
    if re.match(r"^[A-Za-z]:[\\/]", text) or text.startswith(("/", "\\\\")):
        return "", True
    if re.match(r"^https?://", text, flags=re.IGNORECASE):
        return "", True
    return text, False


def _truthy(value: Any) -> bool:
    return _token(value) in {"1", "true", "yes", "oui", "y", "on", "cloud", "raw", "sync"}


def _first_text(row: Mapping[str, Any], fields: tuple[str, ...]) -> str:
    for field_name in fields:
        value = _cell(row.get(field_name))
        if value:
            return value
    return ""


def _token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _cell(value).lower()).strip("_")


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()
