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
    match = re.match(r"(\d{2})/(\d{2})/(20\d{2})$", value.strip())
    if not match:
        return ""
    day, month, year = match.groups()
    return f"{year}-{month}-{day}"


def _amount(patterns: list[str], text: str) -> str:
    value = _first(patterns, text)
    return normalize_amount(value) if value else ""


class AsvInvoiceProviderExtractor:
    """Extractor for ASV access and locksmith maintenance invoices."""

    provider_key = "asv"
    status = "generalizable"
    supported_inputs = ["pdf_text", "factur-x", "xml", "ubl", "cii"]

    def extract(self, text: str, file_name: str = "") -> InvoiceExtraction:
        invoice_number = _first([r"Facture\s+n[^\dA-Z]{0,5}([A-Z0-9][A-Z0-9._/-]+)"], text)
        date_raw = _first([r"\bDate\b[^\d]{0,80}(\d{2}/\d{2}/20\d{2})", r"\b(\d{2}/\d{2}/20\d{2})\b"], text)
        siren_siret = re.sub(
            r"\D",
            "",
            _first([r"R\.?\s*C\.?\s*S\.?\s*:?\s*([0-9 .]{9,20})", r"R\.?\s*C\.?\s*S\.?\s*(?::)?\s*([0-9 .]{9,20})"], text),
        )
        ht = _amount([rf"Total\s+H\.?\s*T[^\d-]{{0,40}}{AMOUNT}", rf"Net\s+H\.?\s*T[^\d-]{{0,40}}{AMOUNT}"], text)
        tva = _amount([rf"Total\s+TVA[^\d-]{{0,40}}{AMOUNT}"], text)
        ttc = _amount([rf"Total\s+TTC[^\d-]{{0,40}}{AMOUNT}", rf"NET\s+A\s+PAYER[^\d-]{{0,40}}{AMOUNT}"], text)

        extraction = InvoiceExtraction(
            provider_key=self.provider_key,
            fournisseur="ASV",
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
