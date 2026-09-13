from __future__ import annotations

import re

from ..base import InvoiceExtraction, normalize_amount


AMOUNT = r"(-?(?:\d{1,3}(?:[ .\u00a0\u202f]\d{3})+|\d+)[,.]\d{2})"


def _first(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return ""


def _date_to_iso(value: str) -> str:
    match = re.match(r"(\d{2})/(\d{2})/(\d{2}|\d{4})$", value.strip())
    if not match:
        return ""
    day, month, year = match.groups()
    if len(year) == 2:
        year = "20" + year
    return f"{year}-{month}-{day}"


def _amount(patterns: list[str], text: str) -> str:
    value = _first(patterns, text)
    return normalize_amount(value) if value else ""


class OrangeInvoiceProviderExtractor:
    """Extractor for Orange professional telecom invoices."""

    provider_key = "orange"
    status = "generalizable"
    supported_inputs = ["pdf_text", "factur-x", "xml", "ubl", "cii"]

    def extract(self, text: str, file_name: str = "") -> InvoiceExtraction:
        invoice_number = _first(
            [
                r"n[^\n]{0,20}de\s+facture\s*:\s*([0-9]{8,12}\s+[A-Z0-9-]{4,20}\s+[A-Z0-9-]{3,10})",
                r"date\s+de\s+facture\s*:\s*([0-9]{8,12}\s+[A-Z0-9-]{4,20}\s+[A-Z0-9-]{3,10})",
            ],
            text,
        )
        date_raw = _first(
            [
                r"votre\s+facture\s+du\s+(\d{2}[./]\d{2}[./]\d{2,4})",
                r"date\s+de\s+facture\s*:.*?(\d{2}/\d{2}/\d{2})",
            ],
            text,
        ).replace(".", "/")
        ht = _amount([rf"montant\s+h\.?\s*t\s*{AMOUNT}", rf"\b{AMOUNT}\s*HT\b"], text)
        tva = _amount([rf"montant\s+(?:total\s+de\s+la\s+)?TVA[^\d-]{{0,30}}{AMOUNT}"], text)
        ttc = _amount(
            [
                rf"total\s+aupr[eè]s\s+d['’]?Orange.*?{AMOUNT}\s*(?:€|EUR)?\s*TTC",
                rf"\b{AMOUNT}\s*(?:€|EUR)?\s*TTC\b",
            ],
            text,
        )

        extraction = InvoiceExtraction(
            provider_key=self.provider_key,
            fournisseur="ORANGE",
            siren_siret="380129866",
            numero_facture=invoice_number,
            date_facture=_date_to_iso(date_raw),
            ht=ht,
            tva=tva,
            ttc=ttc,
            confidence="high" if invoice_number and ttc else "medium",
        )
        if not extraction.numero_facture:
            extraction.anomalies.append("NUMERO_FACTURE_ABSENT")
        if not extraction.date_facture:
            extraction.anomalies.append("DATE_FACTURE_ABSENTE")
        if not extraction.ttc:
            extraction.anomalies.append("MONTANT_TTC_ABSENT")
        return extraction
