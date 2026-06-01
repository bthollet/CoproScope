from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation


REQUIRED_ACCOUNTING_FIELDS = [
    "doc_id",
    "sha256",
    "aliases",
    "fournisseur",
    "siren_siret",
    "numero_facture",
    "date_facture",
    "exercice",
    "periode",
    "ht",
    "tva",
    "ttc",
    "compte_propose",
    "decision_ref",
    "paiement_ref",
    "statut_controle",
    "anomalies",
    "chemin_piece",
]

SUPPORTED_EINVOICE_FORMATS = ["factur-x", "xml", "ubl", "cii"]


@dataclass
class InvoiceExtraction:
    provider_key: str = ""
    fournisseur: str = ""
    siren_siret: str = ""
    numero_facture: str = ""
    date_facture: str = ""
    ht: str = ""
    tva: str = ""
    ttc: str = ""
    anomalies: list[str] = field(default_factory=list)
    confidence: str = "low"


@dataclass
class DocumentExtractionEvidence:
    file_name: str = ""
    native_text: str = ""
    ocr_text: str = ""
    docling_markdown: str = ""
    layout_json: str = ""
    visual_review: str = ""

    def combined_text(self) -> str:
        parts = [
            ("NATIVE_TEXT", self.native_text),
            ("OCR_TEXT", self.ocr_text),
            ("DOCLING_MARKDOWN", self.docling_markdown),
            ("LAYOUT_JSON", self.layout_json),
            ("VISUAL_REVIEW", self.visual_review),
            ("FILENAME", self.file_name),
        ]
        return "\n\n".join(f"===== {label} =====\n{value}" for label, value in parts if value.strip())


def provider_key_from_name(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    return lowered.strip("_")[:80] or "unknown_provider"


def detect_invoice_family(file_name: str) -> str:
    name = file_name.lower()
    if re.match(r"^facture_\d", name):
        return "facture_timestamp"
    if name.startswith("facture_nd"):
        return "facture_nd"
    if name.startswith("facture_hono"):
        return "facture_hono"
    if name.startswith("facture_auto"):
        return "facture_auto"
    return "autres"


def filename_invoice_reference(file_name: str) -> str:
    stem = re.sub(r"\.[^.]+$", "", file_name)
    stem = re.sub(r"\.\d+$", "", stem)
    return stem


def filename_date(file_name: str) -> str:
    match = re.search(r"(20\d{2})([01]\d)([0-3]\d)", file_name)
    if not match:
        return ""
    year, month, day = match.groups()
    return f"{year}-{month}-{day}"


def normalize_amount(value: str) -> str:
    cleaned = value.replace("\u00a0", " ").strip()
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(" ", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(" ", "")
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    if not cleaned:
        return ""
    try:
        return f"{Decimal(cleaned):.2f}"
    except InvalidOperation:
        return ""


def _normalize_text(value: str) -> str:
    text = value.replace("\u00a0", " ").replace("\u202f", " ")
    if any(marker in text for marker in ("Ã", "Â", "â")):
        try:
            repaired = text.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
            if repaired:
                text = repaired
        except UnicodeError:
            pass
    return unicodedata.normalize("NFKC", text).strip()


def _match_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", _normalize_text(value)).lower()
    return "".join(char for char in text if not unicodedata.combining(char))


def _looks_like_building_reference(context: str) -> bool:
    return bool(re.search(r"\b(b[âa]timent|bat\.?|immeuble|cage)\b", context, flags=re.IGNORECASE))


def _looks_like_identifier_amount(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    return len(digits) >= 9 and not re.search(r"[,.]\d{1,2}", value)


def _amount_candidates(window: str) -> list[str]:
    values: list[str] = []
    for match in re.finditer(r"-?\d[\d \u00a0\u202f.,]*(?:[,.]\d{1,2})?", window):
        raw = match.group(0)
        following = window[match.end() : match.end() + 4]
        if "%" in following:
            continue
        if re.fullmatch(r"(?:19|20)\d{2}", raw.strip()):
            continue
        prefix = window[max(0, match.start() - 45) : match.start()]
        if _looks_like_building_reference(prefix) or _looks_like_identifier_amount(raw):
            continue
        amount = normalize_amount(raw)
        if amount:
            values.append(amount)
    return values


def _amount_after(labels: list[str], text: str) -> str:
    for label in labels:
        for label_match in re.finditer(label, text, flags=re.IGNORECASE):
            window = text[label_match.end() : label_match.end() + 180]
            candidates = _amount_candidates(window)
            if candidates:
                return candidates[0]
    return ""


def _amount_after_percent_total(label: str, text: str) -> str:
    amount = r"(-?\d[\d \u00a0\u202f.,]*(?:[,.]\d{1,2})?)"
    pattern = rf"{label}[^\n\r\d-]{{0,40}}\d{{1,2}}[,.]\d{{2}}\s*%[^\d-]{{0,20}}{amount}"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return ""
    return normalize_amount(match.group(1))


def _amounts_after(label: str, text: str) -> list[str]:
    values: list[str] = []
    for label_match in re.finditer(label, text, flags=re.IGNORECASE):
        window = text[label_match.end() : label_match.end() + 180]
        for amount in _amount_candidates(window):
            if amount not in values:
                values.append(amount)
    return values


def _tax_summary_amounts(text: str) -> tuple[str, str] | None:
    for match in re.finditer(r"base\s+h\.?\s*t", text, flags=re.IGNORECASE):
        window = text[match.end() : match.end() + 260]
        if not re.search(r"taux\s+tva|mt\s+tva|montant\s+tva", window, flags=re.IGNORECASE):
            continue
        candidates = _amount_candidates(window)
        if len(candidates) >= 3 and candidates[0].endswith(".00") and Decimal(candidates[0]) <= Decimal("9.00"):
            candidates = candidates[1:]
        if len(candidates) >= 2:
            return candidates[0], candidates[1]
    return None


def _labeled_totals(text: str) -> tuple[str, str, str] | None:
    ht_values = _amounts_after(r"(?:total\s+hors\s+taxes|total\s+h\.?\s*t)", text)
    tva_values = _amounts_after(r"(?:montant\s+)?tva\s*(?:\(\s*\d+\s*%\s*\))?", text)
    ttc_values = _amounts_after(r"total\s+ttc", text)
    if not ht_values or not tva_values or not ttc_values:
        return None
    coherent: list[tuple[Decimal, str, str, str]] = []
    for ht in ht_values:
        for tva in tva_values:
            for ttc in ttc_values:
                try:
                    ht_decimal = Decimal(ht)
                    if abs((ht_decimal + Decimal(tva)) - Decimal(ttc)) <= Decimal("0.05"):
                        coherent.append((ht_decimal, ht, tva, ttc))
                except InvalidOperation:
                    continue
    if coherent:
        _, ht, tva, ttc = max(coherent, key=lambda item: item[0])
        return ht, tva, ttc
    return None


def _total_amount_hint(text: str) -> str:
    patterns = [
        r"\bmontant\s*:\s*(-?\d[\d \u00a0\u202f.,]*(?:[,.]\d{1,2})?)",
        r"\bnet\s+[aàÃ€]\s+payer[^\d\-]{0,40}(-?\d[\d \u00a0\u202f.,]*(?:[,.]\d{1,2})?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            amount = normalize_amount(match.group(1))
            if amount:
                return amount
    return ""


def _sanitize_supplier_line(line: str) -> str:
    cleaned = re.split(
        r"\s+-\s*(?:t[ée]l[ée]phone|tel\.?|courriel|email|e-mail)\b",
        line,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    cleaned = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", " ", cleaned)
    cleaned = re.sub(r"\b(?:\+?\d[\d .-]{7,}\d)\b", " ", cleaned)
    cleaned = re.split(
        r"\b\d+\s+(?:avenue|av\.?|rue|all[ée]e|allee|all\.?|boulevard|bd|chemin|place|traverse|impasse)\b",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return re.sub(r"\s+", " ", cleaned).strip(" :-\t")[:120]


def _first_match(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return ""


def _company_name_hint(text: str) -> str:
    supplier = _first_match([r"\bsoci\S*t\S*\s+([A-Z][A-Z0-9&.' -]{2,60})"], text)
    if supplier:
        return _sanitize_supplier_line(supplier)
    return ""


def _bad_supplier_fragments() -> list[str]:
    return [
        "designation",
        "quantite",
        "prix uni",
        "montant ht",
        "total ht",
        "total ttc",
        "net ht",
        "net a payer",
        "net à payer",
        "echeance",
        "échéance",
        "reglement",
        "règlement",
        "comptant",
        "date des travaux",
        "bon de commande",
        "logement",
        "payer en ligne",
        "nos references",
        "vos references",
        "numero de contrat",
        "numero de facture",
        "sdc ",
        "syndicat",
        "client",
        "beauvallon",
        "chavissimmo",
        "immobilier",
        "installation de chantier",
        "modes de paiement",
        "conditions de paiement",
        "objet",
        "adresse du chantier",
        "capital",
        "sage",
        "www.",
    ]


def _is_bad_supplier_candidate(line: str) -> bool:
    normalized = _match_text(line)
    if normalized in {"facture", "avoir", "invoice", "note de debit", "note d'honoraires"}:
        return True
    if normalized in {"electricite", "local", "local technique"}:
        return True
    if any(fragment in normalized for fragment in _bad_supplier_fragments()):
        return True
    if normalized.startswith(("facture n", "facture no", "facture numero")):
        return True
    if re.search(r"\d{2}/\d{2}/\d{2,4}", line):
        return True
    if re.search(
        r"\ble\s+[0-3]?\d\s+(janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)\s+20\d{2}\b",
        _match_text(line),
        flags=re.IGNORECASE,
    ):
        return True
    if re.search(r"\d[\d \u00a0\u202f]*[,.]\d{2}\s*(?:%|eur|€)?", line, flags=re.IGNORECASE):
        return True
    if re.search(
        r"^\d+\s+(?:avenue|av\.?|rue|all[ée]e|allee|all\.?|boulevard|bd|chemin|place|traverse|impasse)\b",
        line,
        flags=re.IGNORECASE,
    ):
        return True
    if re.search(r"^\d{5}\s+\S+", line):
        return True
    if re.search(r"^bp\s+\d+\b", line, flags=re.IGNORECASE):
        return True
    if normalized in {"batiment", "batiment & industrie", "batiment industrie"}:
        return True
    if re.match(r"^batiment\s+\d+\b", normalized):
        return True
    return bool(
        re.search(
            r"\d{2}/\d{2}/\d{4}|total|tva|siret|siren|iban|bic|page\s+\d|@|telephone|\btel\.?|devis",
            line,
            flags=re.IGNORECASE,
        )
    )


def _supplier_near_legal_markers(text: str) -> str:
    lines = [re.sub(r"\s+", " ", raw_line).strip(" :-\t") for raw_line in text.splitlines()]
    for index, line in enumerate(lines):
        if not re.search(r"\b(rcs|siret|siren|tva\s*:|capital|rcp|d[ée]cennale)\b", line, flags=re.IGNORECASE):
            continue
        for candidate in reversed(lines[max(0, index - 8) : index]):
            if len(candidate) < 3 or _is_bad_supplier_candidate(candidate):
                continue
            supplier = _sanitize_supplier_line(candidate)
            if supplier and not _is_bad_supplier_candidate(supplier):
                return supplier
    return ""


def _has_multiline_invoice_layout(text: str) -> bool:
    return bool(
        re.search(r"\bfacture\s+n\S*\s*\n\s*[A-Z]{1,6}\d+", text, flags=re.IGNORECASE)
        and re.search(r"s\.?\s*i\.?\s*r\.?\s*e\.?\s*t", text, flags=re.IGNORECASE)
    )


def _guess_supplier(text: str) -> str:
    company_hint = ""
    if _has_multiline_invoice_layout(text):
        company_hint = _company_name_hint(text)
    if company_hint:
        return company_hint

    named_siret = _first_match([r"\bsiret\s+([A-Z][A-Z0-9&.' -]{2,40})\s*:"], text)
    if named_siret:
        supplier = _sanitize_supplier_line(named_siret)
        if supplier:
            return supplier

    legal_hint = _supplier_near_legal_markers(text)
    if legal_hint:
        return legal_hint

    for raw_line in text.splitlines()[:25]:
        line = re.sub(r"\s+", " ", raw_line).strip(" :-\t")
        if len(line) < 3:
            continue
        if line.startswith("====="):
            continue
        supplier = _sanitize_supplier_line(line)
        if supplier and not _is_bad_supplier_candidate(supplier):
            return supplier
    return ""


def _looks_like_invoice_number(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"payable", "date", "client", "code", "devis", "total", "virement", "facture"}:
        return False
    return bool(re.search(r"\d", value))


def _invoice_number(text: str, file_name: str) -> str:
    patterns = [
        r"(?:facture|invoice|avoir|note\s+d'honoraires|note\s+de\s+debit)\s*n[^A-Z0-9]{0,12}([A-Z]{1,6}\d{2,}[A-Z0-9_\-/.]*)",
        r"(?:facture|invoice|avoir|note\s+d'honoraires|note\s+de\s+debit)\s*(?:n[Â°o.]?|numero|number)?\s*[:#\- ]+\s*([A-Z0-9][A-Z0-9_\-/.]+)",
        r"(?:n[Â°o.]?|numero)\s*(?:facture|invoice)?\s*[:#\- ]+\s*([A-Z0-9][A-Z0-9_\-/.]+)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            candidate = re.sub(r"\s+", " ", match.group(1)).strip()
            if _looks_like_invoice_number(candidate):
                return candidate
    return filename_invoice_reference(file_name)


def _normalize_invoice_date(value: str) -> str:
    if re.match(r"\d{2}[/-]\d{2}[/-]20\d{2}", value):
        day, month, year = re.split(r"[/-]", value)
        return f"{year}-{month}-{day}"
    return value


def _french_text_date(text: str) -> str:
    months = {
        "janvier": "01",
        "fevrier": "02",
        "mars": "03",
        "avril": "04",
        "mai": "05",
        "juin": "06",
        "juillet": "07",
        "aout": "08",
        "septembre": "09",
        "octobre": "10",
        "novembre": "11",
        "decembre": "12",
    }
    normalized = _match_text(text)
    bad_context = ("travaux", "echeance", "livraison", "intervention", "devis")
    for match in re.finditer(r"\ble\s+([0-3]?\d)\s+([a-z]+)\s+(20\d{2})\b", normalized, flags=re.IGNORECASE):
        context = normalized[max(0, match.start() - 45) : match.start()]
        if any(marker in context for marker in bad_context):
            continue
        day, month, year = match.groups()
        month_number = months.get(month.lower())
        if month_number:
            return f"{year}-{month_number}-{int(day):02d}"
    return ""


def _invoice_date(text: str, file_name: str) -> str:
    invoice_context_patterns = [
        r"facture[\s\S]{0,100}\bdate\b[^\d]{0,30}(\d{2}/\d{2}/20\d{2})",
        r"\bdate\b[^\d]{0,30}(\d{2}/\d{2}/20\d{2})",
    ]
    for pattern in invoice_context_patterns:
        date = _first_match([pattern], text)
        if date:
            return _normalize_invoice_date(date)

    textual_date = _french_text_date(text)
    if textual_date:
        return textual_date

    for match in re.finditer(r"\d{2}/\d{2}/20\d{2}|\d{2}-\d{2}-20\d{2}|20\d{2}-[01]\d-[0-3]\d", text):
        context = text[max(0, match.start() - 35) : match.start()].lower()
        if "devis" in context:
            continue
        return _normalize_invoice_date(match.group(0))
    return filename_date(file_name)


def extract_generic_invoice_fields(text: str, file_name: str = "") -> InvoiceExtraction:
    supplier = _guess_supplier(text)
    invoice_number = _first_match(
        [
            r"(?:facture|invoice|avoir|note\s+d'honoraires|note\s+de\s+debit)\s*(?:n[°o.]?|numero|number)?\s*[:#\- ]+\s*([A-Z0-9][A-Z0-9_\-/.]+)",
            r"(?:n[°o.]?|numero)\s*(?:facture|invoice)?\s*[:#\- ]+\s*([A-Z0-9][A-Z0-9_\-/.]+)",
        ],
        text,
    )
    if not invoice_number:
        invoice_number = filename_invoice_reference(file_name)

    date = _french_text_date(text) or _first_match(
        [
            r"(\d{2}/\d{2}/20\d{2})",
            r"(\d{2}-\d{2}-20\d{2})",
            r"(20\d{2}-[01]\d-[0-3]\d)",
        ],
        text,
    )
    if re.match(r"\d{2}[/-]\d{2}[/-]20\d{2}", date):
        day, month, year = re.split(r"[/-]", date)
        date = f"{year}-{month}-{day}"
    if not date:
        date = filename_date(file_name)
    if _has_multiline_invoice_layout(text):
        invoice_number = _invoice_number(text, file_name)
        date = _invoice_date(text, file_name)

    siren_siret = _first_match(
        [
            r"(?:s\.?\s*i\.?\s*r\.?\s*e\.?\s*t\.?)\s*[:#.\- ]+\s*([0-9][0-9 .]{8,20})",
            r"(?:siret|siren)\s*[:#\- ]+\s*([0-9][0-9 .]{8,20})",
            r"\b([0-9]{3}\s?[0-9]{3}\s?[0-9]{3}(?:\s?[0-9]{5})?)\b",
        ],
        text,
    )
    siren_siret = re.sub(r"\D", "", siren_siret)

    ht = _amount_after([r"total\s+hors\s+taxes", r"total\s+h\.?\s*t", r"montant\s+h\.?\s*t", r"base\s+h\.?\s*t"], text)
    tva = _amount_after_percent_total(r"total\s+t\.?\s*v\.?\s*a\.?", text) or _amount_after(
        [
            r"total\s+t\.?\s*v\.?\s*a\.?",
            r"total\s+tva",
            r"montant\s+t\.?\s*v\.?\s*a\.?",
            r"montant\s+tva",
            r"\btva\b",
        ],
        text,
    )
    ttc = _amount_after([r"net\s+a\s+payer", r"net\s+Ã \s+payer", r"net\s+à\s+payer", r"total\s+ttc", r"\bttc\b"], text)

    labeled_totals = _labeled_totals(text)
    if labeled_totals:
        ht, tva, ttc = labeled_totals

    tax_summary = _tax_summary_amounts(text)
    if tax_summary:
        summary_ht, summary_tva = tax_summary
        total_hint = _total_amount_hint(text) or ttc
        if total_hint:
            try:
                if abs((Decimal(summary_ht) + Decimal(summary_tva)) - Decimal(total_hint)) <= Decimal("0.05"):
                    ht = summary_ht
                    tva = summary_tva
                    ttc = total_hint
            except InvalidOperation:
                pass

    extraction = InvoiceExtraction(
        provider_key=provider_key_from_name(supplier),
        fournisseur=supplier,
        siren_siret=siren_siret,
        numero_facture=invoice_number,
        date_facture=date,
        ht=ht,
        tva=tva,
        ttc=ttc,
        confidence="medium" if supplier and invoice_number and date else "low",
    )

    if not extraction.fournisseur:
        extraction.anomalies.append("FOURNISSEUR_ABSENT")
    if not extraction.siren_siret:
        extraction.anomalies.append("SIREN_SIRET_ABSENT")
    if not extraction.numero_facture:
        extraction.anomalies.append("NUMERO_FACTURE_ABSENT")
    if not extraction.date_facture:
        extraction.anomalies.append("DATE_FACTURE_ABSENTE")
    if not extraction.ttc:
        extraction.anomalies.append("MONTANT_TTC_ABSENT")

    if extraction.ht and extraction.tva and extraction.ttc:
        try:
            ht = Decimal(extraction.ht)
            tva = Decimal(extraction.tva)
            ttc = Decimal(extraction.ttc)
            if abs((ht + tva) - ttc) > Decimal("0.05"):
                extraction.anomalies.append("INCOHERENCE_HT_TVA_TTC")
        except InvalidOperation:
            extraction.anomalies.append("MONTANTS_NON_NUMERIQUES")

    return extraction


def extract_generic_invoice_from_evidence(evidence: DocumentExtractionEvidence) -> InvoiceExtraction:
    return extract_generic_invoice_fields(evidence.combined_text(), file_name=evidence.file_name)
