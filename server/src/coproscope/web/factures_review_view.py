from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import Request as FastAPIRequest

from ..core.common import read_csv


FORBIDDEN_PATTERNS = (
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/][^\s|,;`)]*"),
    re.compile(r"file://\S+", re.IGNORECASE),
    re.compile(r"(?:^|[\s`'\"(])(?:raw|restricted|logs|private|system)[\\/]\S*", re.IGNORECASE),
    re.compile(r"\b[a-f0-9]{24,}\b", re.IGNORECASE),
)

ANOMALY_LABELS = {
    "FOURNISSEUR_ABSENT": "Fournisseur absent",
    "NUMERO_FACTURE_ABSENT": "Numero facture absent",
    "DATE_FACTURE_ABSENTE": "Date facture absente",
    "MONTANT_TTC_ABSENT": "Montant TTC absent",
    "SIREN_SIRET_ABSENT": "SIREN ou SIRET absent",
    "DOUBLON_POTENTIEL": "Doublon potentiel",
    "FACTURE_HORS_EXERCICE": "Facture hors exercice",
    "INCOHERENCE_HT_TVA_TTC": "HT, TVA et TTC incoherents",
    "SECURITE_INCENDIE_A_DEVISER": "Securite incendie a deviser",
}

STATUS_LABELS = {
    "PROBABLE": "Probable",
    "A_CONTROLER": "A controler",
    "INCERTAIN": "Incertain",
}

FILTERS = (
    ("all", "Toutes"),
    ("priorite-haute", "Priorite haute"),
    ("doublons", "Doublons"),
    ("montants-incomplets", "Montants incomplets"),
    ("hors-exercice", "Hors exercice"),
    ("fournisseur-absent", "Fournisseur absent"),
)

HIGH_PRIORITY_ANOMALIES = {
    "INCOHERENCE_HT_TVA_TTC",
    "DOUBLON_POTENTIEL",
    "FACTURE_HORS_EXERCICE",
    "SECURITE_INCENDIE_A_DEVISER",
}
COMPLETION_ANOMALIES = {
    "FOURNISSEUR_ABSENT",
    "NUMERO_FACTURE_ABSENT",
    "DATE_FACTURE_ABSENTE",
    "MONTANT_TTC_ABSENT",
    "SIREN_SIRET_ABSENT",
}


def register_factures_review_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    @app.get("/comptes/factures-a-revoir", response_class=html_response)
    def factures_a_revoir(request: FastAPIRequest):
        require_token(request)
        active_filter = _filter_token(request.query_params.get("filtre"))
        view = build_factures_review_view(getattr(app.state, "instance", None), year, active_filter=active_filter)
        return templates.TemplateResponse(
            request=request,
            name="factures_review.html",
            context=context(request, "accounting", factures_review=view),
        )


def build_factures_review_view(instance: Any | None, year: int = 2025, active_filter: str = "all") -> dict[str, Any]:
    invoices = _read_invoice_rows(instance, year)
    anomalies = _read_anomaly_rows(instance, year)
    anomalies_by_doc: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in anomalies:
        doc_id = _safe_doc_id(row.get("doc_id"))
        if doc_id:
            anomalies_by_doc[doc_id].append(row)
    items = [_invoice_item(row, anomalies_by_doc.get(_safe_doc_id(row.get("doc_id")), [])) for row in invoices]
    review_items = [item for item in items if item["needs_review"]]
    filtered_items = [item for item in review_items if _matches_filter(item, active_filter)]
    filtered_items = sorted(filtered_items, key=_sort_key)
    counts = Counter(item["priority_key"] for item in review_items)
    status_counts = Counter(item["status_key"] for item in items)
    critical = sum(1 for item in review_items if item["priority_key"] == "P1")
    return {
        "title": "Factures a revoir",
        "eyebrow": "ComptaScope / factures",
        "year": str(year),
        "source_label": "Table derivee locale",
        "summary": [
            {"label": "A traiter", "value": str(counts.get("P1", 0)), "detail": "Donnee bloquante ou doublon."},
            {"label": "A controler", "value": str(status_counts.get("A_CONTROLER", 0)), "detail": "Statut machine prioritaire."},
            {"label": "Incertaines", "value": str(status_counts.get("INCERTAIN", 0)), "detail": "Lecture partielle a reprendre."},
            {"label": "Anomalies critiques", "value": str(critical), "detail": "A regarder avant rapprochement."},
            {"label": "Probables", "value": str(status_counts.get("PROBABLE", 0)), "detail": "A garder en controle simple."},
            {"label": "Total candidates", "value": str(len(invoices)), "detail": "Depuis les textes locaux."},
        ],
        "filters": _filter_links(active_filter),
        "active_filter": active_filter,
        "rows": filtered_items,
        "count": len(filtered_items),
        "total_review": len(review_items),
        "has_source": bool(invoices),
        "empty": _empty_message(invoices, filtered_items),
        "privacy_notice": "File locale: chemins, noms bruts et preuves internes ne sont pas affiches.",
    }


def _read_invoice_rows(instance: Any | None, year: int) -> list[dict[str, str]]:
    path = _accounting_year_dir(instance, year) / f"invoice_evidence_{year}.csv"
    _, rows = read_csv(path)
    return [dict(row) for row in rows]


def _read_anomaly_rows(instance: Any | None, year: int) -> list[dict[str, str]]:
    path = _accounting_year_dir(instance, year) / f"invoice_anomalies_{year}.csv"
    _, rows = read_csv(path)
    return [dict(row) for row in rows]


def _accounting_year_dir(instance: Any | None, year: int) -> Path:
    if instance is None:
        return Path()
    try:
        base = Path(instance.artifact("accounting_dir"))
    except (AttributeError, KeyError, TypeError, ValueError, OSError):
        return Path()
    year_dir = base / str(year)
    return year_dir if year_dir.exists() else base


def _invoice_item(row: dict[str, str], anomalies: list[dict[str, str]]) -> dict[str, Any]:
    doc_id = _safe_doc_id(row.get("doc_id"))
    anomaly_tokens = _unique([*_row_anomaly_tokens(row), *[_anomaly_token(item.get("anomaly")) for item in anomalies]])
    anomaly_labels = [_anomaly_label(token) for token in anomaly_tokens]
    status_key = _status_key(row.get("statut_controle"))
    status_label = STATUS_LABELS.get(status_key, "A confirmer")
    severities = {str(item.get("severity") or "").upper() for item in anomalies}
    priority_key = _priority_key(status_key, anomaly_tokens, severities)
    priority_label = _priority_label(priority_key, anomaly_tokens)
    needs_review = bool(anomaly_tokens or status_key != "PROBABLE")
    return {
        "id": doc_id or _public_text(row.get("numero_facture"), limit=36) or "facture-a-identifier",
        "doc_id": doc_id,
        "priority_key": priority_key,
        "priority_label": priority_label,
        "tone": "p1" if priority_key == "P1" else "p2",
        "card_tone": "danger" if priority_key == "P1" else "warn",
        "status_key": status_key,
        "status_label": status_label,
        "needs_review": needs_review,
        "supplier": _public_text(row.get("fournisseur"), limit=72) or "Fournisseur a identifier",
        "invoice_number": _public_text(row.get("numero_facture"), limit=48) or "Reference a identifier",
        "date": _public_text(row.get("date_facture"), limit=24) or "Date a verifier",
        "amount": _money(row.get("ttc")),
        "account": _public_text(row.get("compte_propose"), limit=32) or "Compte a confirmer",
        "family": _public_text(row.get("famille_charge"), limit=60) or "Nature a confirmer",
        "anomalies": anomaly_labels or ["A relire"],
        "anomaly_tokens": anomaly_tokens,
        "next_action": _next_action(priority_key, anomaly_tokens),
        "href": f"/documents/{quote(doc_id)}?source=factures" if doc_id else "",
    }


def _priority_key(status_key: str, anomaly_tokens: list[str], severities: set[str]) -> str:
    if "P0" in severities or "P1" in severities or status_key == "A_CONTROLER":
        return "P1"
    if any(token in HIGH_PRIORITY_ANOMALIES or token in COMPLETION_ANOMALIES for token in anomaly_tokens):
        return "P1"
    return "P2"


def _sort_key(item: dict[str, Any]) -> tuple[int, str]:
    return (0 if item["priority_key"] == "P1" else 1, str(item["supplier"]), str(item["date"]), str(item["id"]))


def _priority_label(priority_key: str, anomaly_tokens: list[str]) -> str:
    if priority_key == "P1" and any(token in HIGH_PRIORITY_ANOMALIES for token in anomaly_tokens):
        return "Priorite haute"
    if priority_key == "P1":
        return "A completer"
    return "A verifier"


def _next_action(priority_key: str, anomaly_tokens: list[str]) -> str:
    if "MONTANT_TTC_ABSENT" in anomaly_tokens:
        return "Retrouver le montant TTC dans la piece ou lancer OCR si besoin."
    if "DOUBLON_POTENTIEL" in anomaly_tokens:
        return "Comparer les doublons avant de retenir une seule piece."
    if "FACTURE_HORS_EXERCICE" in anomaly_tokens:
        return "Verifier l'exercice avant de rapprocher la charge."
    if "FOURNISSEUR_ABSENT" in anomaly_tokens:
        return "Identifier le fournisseur puis relancer le controle machine."
    if "SECURITE_INCENDIE_A_DEVISER" in anomaly_tokens:
        return "Demander le devis ou la preuve de remise en conformite incendie."
    if priority_key == "P1":
        return "Completer la donnee bloquante avant rapprochement."
    return "Relire la facture puis rattacher au bon controle comptable."


def _anomaly_label(value: Any) -> str:
    token = _anomaly_token(value)
    return ANOMALY_LABELS.get(token, _public_text(token.replace("_", " ").title(), limit=70) or "A relire")


def _anomaly_token(value: Any) -> str:
    return re.sub(r"[^A-Z0-9_]+", "_", str(value or "").strip().upper()).strip("_")


def _row_anomaly_tokens(row: dict[str, str]) -> list[str]:
    raw = str(row.get("anomalies") or "")
    return [_anomaly_token(part) for part in re.split(r"[|,;]+", raw) if _anomaly_token(part)]


def _status_key(value: Any) -> str:
    token = re.sub(r"[^A-Z0-9_]+", "_", str(value or "").strip().upper()).strip("_")
    return token if token in STATUS_LABELS else "A_CONFIRMER"


def _money(value: Any) -> str:
    if _contains_private_marker(str(value or "")):
        return "Montant a verifier"
    text = str(value or "").strip().replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d{1,2})?", text)
    return f"{float(match.group(0)):.2f} EUR" if match else "Montant a verifier"


def _safe_doc_id(value: Any) -> str:
    raw = str(value or "").strip()
    if _contains_private_marker(raw) or re.search(r"\b[a-f0-9]{24,}\b", raw, re.IGNORECASE):
        return ""
    text = re.sub(r"[^A-Za-z0-9_.:-]+", "-", raw)[:128].strip("-")
    if _contains_private_marker(text) or re.search(r"\b[a-f0-9]{24,}\b", text, re.IGNORECASE):
        return ""
    return text


def _public_text(value: Any, *, limit: int) -> str:
    text = " ".join(str(value or "").split())
    text = re.sub(r"<\s*script\b.*?<\s*/\s*script\s*>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    for pattern in FORBIDDEN_PATTERNS:
        text = pattern.sub("[retire]", text)
    text = re.sub(r"(?<!\w)[^\s,;:|()]+\.(?:pdf|docx?|xlsx?)(?!\w)", "piece comptable", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(raw|restricted|logs?|private|system|tokens?|secrets?|oauth)\b", "[retire]", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:\[retire\]\s*)+", "information masquee ", text).strip()
    text = text.strip()
    return text if len(text) <= limit else f"{text[: limit - 1].rstrip()}..."


def _contains_private_marker(value: str) -> bool:
    lowered = value.replace("\\", "/").lower()
    return any(marker in lowered for marker in ("file://", "raw/", "restricted/", "logs/", "private/", "system/")) or bool(
        re.search(r"(?<![a-z])[a-z]:/", lowered)
    )


def _filter_token(value: Any) -> str:
    token = re.sub(r"[^a-z0-9-]+", "", str(value or "all").strip().lower())
    return token if token in {key for key, _ in FILTERS} else "all"


def _filter_links(active_filter: str) -> list[dict[str, str]]:
    links = []
    for key, label in FILTERS:
        href = "/comptes/factures-a-revoir" if key == "all" else f"/comptes/factures-a-revoir?filtre={key}"
        links.append({"key": key, "label": label, "href": href, "active": "true" if key == active_filter else "false"})
    return links


def _matches_filter(item: dict[str, Any], active_filter: str) -> bool:
    tokens = set(item["anomaly_tokens"])
    if active_filter == "priorite-haute":
        return item["priority_key"] == "P1"
    if active_filter == "doublons":
        return "DOUBLON_POTENTIEL" in tokens
    if active_filter == "montants-incomplets":
        return "MONTANT_TTC_ABSENT" in tokens
    if active_filter == "hors-exercice":
        return "FACTURE_HORS_EXERCICE" in tokens
    if active_filter == "fournisseur-absent":
        return "FOURNISSEUR_ABSENT" in tokens
    return True


def _empty_message(invoices: list[dict[str, str]], filtered_items: list[dict[str, Any]]) -> str:
    if not invoices:
        return "Aucune table facture locale n'est disponible pour cet exercice."
    if not filtered_items:
        return "Aucune facture ne correspond a ce filtre."
    return ""


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
