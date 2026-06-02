from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import Request as FastAPIRequest

from ..core.common import read_csv
from ..extractors.invoices.reconciliation import parse_amount


FORBIDDEN_PATTERNS = (
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/][^\s|,;`)]*"),
    re.compile(r"file://\S+", re.IGNORECASE),
    re.compile(r"(?:^|[\s`'\"(])(?:raw|restricted|logs|private|system)[\\/]\S*", re.IGNORECASE),
    re.compile(r"\b[a-f0-9]{24,}\b", re.IGNORECASE),
)
CONTACT_PATTERNS = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"(?:\+|00)[\s().-]*33[\s().-]*0?[1-9](?:[\s().-]*\d{2}){4}"),
    re.compile(r"\b(?:\+|00)?33[\s().-]*0?[1-9](?:[\s().-]*\d{2}){4}\b"),
    re.compile(r"\b0[1-9](?:[\s().-]*\d{2}){4}\b"),
    re.compile(r"\b[A-Z]{2}\d{2}(?:[\s-]?[A-Z0-9]){11,30}\b", re.IGNORECASE),
)
ADDRESS_PATTERN = re.compile(
    r"\b(?:\d{1,5}\s+)?(?:avenue|av\.?|rue|boulevard|bd|place|chemin|traverse|impasse|route)\s+[^,;|)]{2,80}",
    re.IGNORECASE,
)
ADMIN_NUMBER_PATTERNS = (
    re.compile(r"\b(?:siren|siret|rna|tva|vat|rcs|ape|naf|nic)\s*[:#-]?\s*[A-Z0-9](?:[\s.-]*[A-Z0-9]){5,}\b", re.IGNORECASE),
    re.compile(r"\b\d(?:[\s.-]*\d){8,}\b"),
)
PUBLIC_PRIVATE_PATTERNS = CONTACT_PATTERNS + (ADDRESS_PATTERN, *ADMIN_NUMBER_PATTERNS)
SUPPLIER_CUT_PATTERN = re.compile(
    r"\s+(?:\d{1,5}\s+)?(?:avenue|av\.?|rue|boulevard|bd|place|chemin|traverse|impasse|route)\b|"
    r"\s+-\s+|\b(?:tel|telephone|courriel|mail|email|iban|bic)\b\s*:?",
    re.IGNORECASE,
)
SUPPLIER_PRIVATE_PATTERNS = PUBLIC_PRIVATE_PATTERNS + (re.compile(r"\d(?:[\s().-]*\d){5,}"),)
INTERNAL_TABLE_FIELDS = {
    "acteur",
    "controle",
    "resultat_id",
    "resultat_premier",
    "sources_utilisees",
}

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
    "ASSURANCE_RIB_A_CONTROLER": "RIB ou mandat assurance a controler",
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
    "ASSURANCE_RIB_A_CONTROLER",
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
        doc_id = _join_doc_key(row.get("doc_id"))
        if doc_id:
            anomalies_by_doc[doc_id].append(row)
    items = [_invoice_item(row, anomalies_by_doc.get(_join_doc_key(row.get("doc_id")), [])) for row in invoices]
    review_items = [item for item in items if item["needs_review"]]
    filtered_items = [item for item in review_items if _matches_filter(item, active_filter)]
    filtered_items = sorted(filtered_items, key=_sort_key)
    counts = Counter(item["priority_key"] for item in review_items)
    status_counts = Counter(item["status_key"] for item in items)
    critical = sum(1 for item in review_items if set(item["anomaly_tokens"]) & HIGH_PRIORITY_ANOMALIES)
    return {
        "title": "Factures a revoir",
        "eyebrow": "ComptaScope / factures",
        "year": str(year),
        "source_label": "Liste de travail locale",
        "summary": [
            {"label": "A traiter", "value": str(counts.get("P1", 0)), "detail": "Donnee bloquante ou doublon."},
            {"label": "A controler", "value": str(status_counts.get("A_CONTROLER", 0)), "detail": "A verifier en premier."},
            {"label": "Incertaines", "value": str(status_counts.get("INCERTAIN", 0)), "detail": "Lecture partielle a reprendre."},
            {"label": "Anomalies critiques", "value": str(critical), "detail": "A regarder avant de relier aux comptes."},
        ],
        "filters": _filter_links(active_filter),
        "active_filter": active_filter,
        "rows": filtered_items,
        "count": len(filtered_items),
        "count_label": _count_label(len(filtered_items), "facture affichee", "factures affichees"),
        "count_rows_label": _count_label(len(filtered_items), "ligne", "lignes"),
        "total_review": len(review_items),
        "total_review_label": _count_label(len(review_items), "facture", "factures"),
        "has_source": bool(invoices),
        "empty": _empty_message(invoices, filtered_items),
        "privacy_notice": "Liste locale: chemins, noms bruts et preuves internes ne sont pas affiches.",
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
    amount = _money(row.get("ttc"))
    invoice_number = _invoice_reference_text(row.get("numero_facture"), limit=48)
    return {
        "id": doc_id or invoice_number or "facture-a-identifier",
        "doc_id": doc_id,
        "priority_key": priority_key,
        "priority_label": priority_label,
        "tone": "p1" if priority_key == "P1" else "p2",
        "card_tone": "danger" if priority_key == "P1" else "warn",
        "status_key": status_key,
        "status_label": status_label,
        "needs_review": needs_review,
        "supplier": _supplier_text(row.get("fournisseur"), limit=72) or "Fournisseur a identifier",
        "invoice_number": invoice_number or "Reference a identifier",
        "date": _public_text(row.get("date_facture"), limit=24) or "Date a verifier",
        "amount": amount,
        "account": _public_text(row.get("compte_propose"), limit=32) or "Compte a confirmer",
        "family": _public_text(row.get("famille_charge"), limit=60) or "Nature a confirmer",
        "anomalies": anomaly_labels or ["A relire"],
        "anomaly_tokens": anomaly_tokens,
        "blocking_alert": _blocking_alert(status_key, anomaly_tokens),
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
        return "Lecture locale insuffisante: retrouver le montant TTC dans la piece ou refaire la lecture automatique du document avant conclusion."
    if "DOUBLON_POTENTIEL" in anomaly_tokens:
        return "Comparer les doublons avant de retenir une seule piece."
    if "FACTURE_HORS_EXERCICE" in anomaly_tokens:
        return "Verifier l'exercice avant de relier la charge aux comptes."
    if "FOURNISSEUR_ABSENT" in anomaly_tokens:
        return "Identifier le fournisseur puis refaire la verification automatique."
    if "SECURITE_INCENDIE_A_DEVISER" in anomaly_tokens:
        return "Demander le devis ou la preuve de remise en conformite incendie."
    if "ASSURANCE_RIB_A_CONTROLER" in anomaly_tokens:
        return "Verifier le RIB connu ou le mandat du courtier avant paiement."
    if priority_key == "P1":
        return "Completer la donnee bloquante avant de relier la facture aux comptes."
    return "Relire la facture puis la rattacher au bon controle comptable."


def _blocking_alert(status_key: str, anomaly_tokens: list[str]) -> str:
    if "MONTANT_TTC_ABSENT" in anomaly_tokens:
        return "Lecture locale insuffisante"
    return ""


def _anomaly_label(value: Any) -> str:
    token = _anomaly_token(value)
    return ANOMALY_LABELS.get(token, _public_text(token.replace("_", " ").title(), limit=70) or "A relire")


def _anomaly_token(value: Any) -> str:
    raw = str(value or "").strip()
    if _contains_sensitive_text(raw):
        return ""
    return re.sub(r"[^A-Z0-9_]+", "_", raw.upper()).strip("_")


def _row_anomaly_tokens(row: dict[str, str]) -> list[str]:
    raw = str(row.get("anomalies") or "")
    return [_anomaly_token(part) for part in re.split(r"[|,;]+", raw) if _anomaly_token(part)]


def _status_key(value: Any) -> str:
    token = re.sub(r"[^A-Z0-9_]+", "_", str(value or "").strip().upper()).strip("_")
    return token if token in STATUS_LABELS else "A_CONFIRMER"


def _money(value: Any) -> str:
    if _contains_sensitive_text(str(value or "")):
        return "Montant a verifier"
    amount = parse_amount(str(value or ""))
    return f"{amount:.2f} EUR" if amount is not None else "Montant a verifier"


def _join_doc_key(value: Any) -> str:
    return str(value or "").strip()


def _safe_doc_id(value: Any) -> str:
    raw = str(value or "").strip()
    if _contains_sensitive_text(raw) or _looks_like_person_initials(raw) or re.search(r"\b[a-f0-9]{24,}\b", raw, re.IGNORECASE):
        return ""
    text = re.sub(r"[^A-Za-z0-9_.:-]+", "-", raw)[:128].strip("-")
    if _contains_sensitive_text(text) or _looks_like_person_initials(text) or re.search(r"\b[a-f0-9]{24,}\b", text, re.IGNORECASE):
        return ""
    return text


def _public_text(value: Any, *, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if _looks_like_raw_file_label(text) or _looks_like_internal_table_text(text):
        return ""
    text = re.sub(r"<\s*script\b.*?<\s*/\s*script\s*>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    for pattern in PUBLIC_PRIVATE_PATTERNS:
        text = pattern.sub("[retire]", text)
    for pattern in FORBIDDEN_PATTERNS:
        text = pattern.sub("[retire]", text)
    text = re.sub(r"(?<!\w)[^\s,;:|()]+\.(?:pdf|docx?|xlsx?)(?!\w)", "piece comptable", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(raw|restricted|logs?|private|system|tokens?|secrets?|oauth)\b", "[retire]", text, flags=re.IGNORECASE)
    text = re.sub(r"(?:\[retire\]\s*)+", "information masquee ", text).strip()
    text = text.strip()
    return text if len(text) <= limit else f"{text[: limit - 1].rstrip()}..."


def _invoice_reference_text(value: Any, *, limit: int) -> str:
    text = _public_text(value, limit=limit)
    if _looks_like_person_initials(text):
        return ""
    return text


def _supplier_text(value: Any, *, limit: int) -> str:
    raw = " ".join(str(value or "").split())
    if not raw:
        return ""
    cut_at = _first_private_text_position(raw)
    if cut_at is not None:
        raw = raw[:cut_at]
    text = _public_text(raw, limit=limit)
    if any(pattern.search(text) for pattern in CONTACT_PATTERNS):
        return ""
    return text


def _first_private_text_position(value: str) -> int | None:
    positions = [match.start() for pattern in (*SUPPLIER_PRIVATE_PATTERNS, SUPPLIER_CUT_PATTERN) if (match := pattern.search(value))]
    return min(positions) if positions else None


def _looks_like_raw_file_label(value: str) -> bool:
    text = value.strip()
    lowered = text.replace("\\", "/").lower()
    if "200_inbox" in lowered or "__bvl." in lowered:
        return True
    if "native_text" in lowered:
        return True
    return bool(re.search(r"(?:^|[_\s-])facture[_\s-]*20\d{10,}(?:\D|$)", lowered))


def _looks_like_internal_table_text(value: str) -> bool:
    lowered = value.strip().strip("\"'").lower()
    if not lowered:
        return False
    field_hits = {field for field in INTERNAL_TABLE_FIELDS if field in lowered}
    return len(field_hits) >= 2 or lowered in INTERNAL_TABLE_FIELDS


def _looks_like_person_initials(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{1,3}", value.strip()))


def _contains_private_marker(value: str) -> bool:
    lowered = value.replace("\\", "/").lower()
    return any(marker in lowered for marker in ("file://", "raw/", "restricted/", "logs/", "private/", "system/")) or bool(
        re.search(r"(?<![a-z])[a-z]:/", lowered)
    )


def _contains_sensitive_text(value: str) -> bool:
    return _contains_private_marker(value) or _looks_like_raw_file_label(value) or any(
        pattern.search(value) for pattern in PUBLIC_PRIVATE_PATTERNS
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
        return bool(tokens & HIGH_PRIORITY_ANOMALIES)
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


def _count_label(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
