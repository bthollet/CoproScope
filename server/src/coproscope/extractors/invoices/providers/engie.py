from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from ..base import InvoiceExtraction, normalize_amount


AMOUNT = r"(-?\d[\d .]*[,.]\d{2})"
MONTHS = {
    "janvier": "01",
    "fevrier": "02",
    "février": "02",
    "mars": "03",
    "avril": "04",
    "mai": "05",
    "juin": "06",
    "juillet": "07",
    "aout": "08",
    "août": "08",
    "septembre": "09",
    "octobre": "10",
    "novembre": "11",
    "decembre": "12",
    "décembre": "12",
}


def _first(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return ""


def _amount(patterns: list[str], text: str) -> str:
    value = _first(patterns, text)
    return normalize_amount(value) if value else ""


def _last_amount(pattern: str, text: str) -> str:
    values = [normalize_amount(match.group(1)) for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.DOTALL)]
    values = [value for value in values if value]
    return values[-1] if values else ""


def _date_to_iso(value: str) -> str:
    raw = re.sub(r"\s+", " ", value.strip().lower())
    match = re.match(r"(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})$", raw)
    if match:
        day, month, year = match.groups()
        if len(year) == 2:
            year = "20" + year
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    match = re.match(r"(\d{1,2})\s+([a-zéû]+)\s+(\d{4})$", raw)
    if match:
        day, month_name, year = match.groups()
        month = MONTHS.get(month_name)
        if month:
            return f"{year}-{month}-{day.zfill(2)}"
    return ""


def _difference(left: str, right: str) -> str:
    try:
        return f"{(Decimal(left) - Decimal(right)):.2f}"
    except (InvalidOperation, ValueError):
        return ""


class EngieInvoiceProviderExtractor:
    """Extractor for ENGIE utility invoices."""

    provider_key = "engie"
    status = "generalizable"
    supported_inputs = ["pdf_text", "factur-x", "xml", "ubl", "cii"]

    def extract(self, text: str, file_name: str = "") -> InvoiceExtraction:
        invoice_number = _first(
            [
                r"Facture\s+n[^\dA-Z]{0,5}([A-Z0-9][A-Z0-9._/-]+)\s+du\s+\d{2}/\d{2}/\d{2,4}",
                r"Facture\s+monosite.{0,160}?N[°o]\s*([0-9]{8,})\s*-",
                r"n[^\dA-Z]{0,5}facture\s*[:#\- ]+\s*([A-Z0-9][A-Z0-9._/-]+)",
            ],
            text,
        )
        date_raw = _first(
            [
                r"Facture\s+n[^\dA-Z]{0,5}[A-Z0-9][A-Z0-9._/-]+\s+du\s+(\d{2}/\d{2}/\d{2,4})",
                r"Facture\s+monosite.{0,160}?N[°o]\s*[0-9]{8,}\s*-\s*(\d{1,2}\s+[a-zéû]+\s+\d{4})",
                r"\bdu\s+(\d{2}/\d{2}/\d{2,4})\b",
            ],
            text,
        )
        siren_siret = ""
        if re.search(r"542\s*107\s*651|FR\s*13\s*542\s*107\s*651", text, flags=re.IGNORECASE):
            siren_siret = "542107651"

        ht = _last_amount(rf"Total\s+[^\n]{{0,100}}hors\s+TVA\s+{AMOUNT}", text) or _amount(
            [
                rf"Total\s+[^\n]{{0,100}}hors\s+TVA\s+{AMOUNT}",
                rf"Total\s+HT[^\d\-]{{0,80}}{AMOUNT}",
            ],
            text,
        )
        ttc = _amount(
            [
                rf"MONTANT\s+TTC.{{0,60}}?payer[^\d\-]{{0,30}}{AMOUNT}",
                rf"Total\s+TTC[^\d\-]{{0,80}}{AMOUNT}",
            ],
            text,
        )
        tva = _difference(ttc, ht) if ttc and ht else ""

        extraction = InvoiceExtraction(
            provider_key=self.provider_key,
            fournisseur="ENGIE",
            siren_siret=siren_siret,
            numero_facture=invoice_number,
            date_facture=_date_to_iso(date_raw),
            ht=ht,
            tva=tva,
            ttc=ttc,
            confidence="high" if invoice_number and ttc else "medium",
        )
        if not extraction.siren_siret:
            extraction.anomalies.append("SIREN_SIRET_ABSENT")
        if not extraction.numero_facture:
            extraction.anomalies.append("NUMERO_FACTURE_ABSENT")
        if not extraction.date_facture:
            extraction.anomalies.append("DATE_FACTURE_ABSENTE")
        if not extraction.ttc:
            extraction.anomalies.append("MONTANT_TTC_ABSENT")
        return extraction
