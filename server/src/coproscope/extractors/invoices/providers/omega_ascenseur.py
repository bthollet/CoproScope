from __future__ import annotations

import re

from ..base import InvoiceExtraction, normalize_amount


AMOUNT = r"(-?\d[\d .]*[,.]\d{2})"


def _first(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return ""


def _amount(patterns: list[str], text: str) -> str:
    value = _first(patterns, text)
    return normalize_amount(value) if value else ""


def _date_to_iso(value: str) -> str:
    match = re.match(r"(\d{2})/(\d{2})/(\d{2}|\d{4})$", value.strip())
    if not match:
        return ""
    day, month, year = match.groups()
    if len(year) == 2:
        year = "20" + year
    return f"{year}-{month}-{day}"


class OmegaAscenseurInvoiceProviderExtractor:
    """Extractor for Omega Ascenseur maintenance invoices."""

    provider_key = "omega_ascenseur"
    status = "generalizable"
    supported_inputs = ["pdf_text", "factur-x", "xml", "ubl", "cii"]

    def extract(self, text: str, file_name: str = "") -> InvoiceExtraction:
        invoice_number = _first([r"\b(FA\.\d{2}\.\d{2}\.\d{2}\.\d{4,})\b"], text)
        date_raw = _first([r"\b(\d{2}/\d{2}/20\d{2})\b", r"\b(\d{2}/\d{2}/\d{2})\b"], text)
        siren_siret = re.sub(
            r"\D",
            "",
            _first([r"SIRET\s*:?\s*([0-9 .]{14,22})", r"\b(815\s*051\s*974\s*00021)\b"], text),
        )
        ttc = _amount(
            [
                rf":\s*{AMOUNT}\s*DELAIS\s+DE\s+PAIEMENT",
                rf"Total\s+TTC[^\d\-]{{0,80}}{AMOUNT}",
                rf"Net\s+a\s+payer[^\d\-]{{0,80}}{AMOUNT}",
            ],
            text,
        )

        extraction = InvoiceExtraction(
            provider_key=self.provider_key,
            fournisseur="OMEGA ASCENSEUR",
            siren_siret=siren_siret,
            numero_facture=invoice_number,
            date_facture=_date_to_iso(date_raw),
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
