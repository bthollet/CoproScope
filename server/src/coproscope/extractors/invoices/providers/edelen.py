from __future__ import annotations

import re

from ..base import InvoiceExtraction, normalize_amount


AMOUNT = r"-?\d[\d .]*[,.]\d{2}"


def _first(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return ""


def _date_to_iso(value: str) -> str:
    match = re.match(r"(\d{2})[./-](\d{2})[./-](20\d{2})$", value.strip())
    if not match:
        return ""
    day, month, year = match.groups()
    return f"{year}-{month}-{day}"


def _money_values(text: str) -> list[str]:
    return [normalize_amount(raw) for raw in re.findall(AMOUNT, text) if normalize_amount(raw)]


class EdelenInvoiceProviderExtractor:
    """Extractor for Edelen invoices."""

    provider_key = "edelen"
    status = "generalizable"
    supported_inputs = ["pdf_text", "factur-x", "xml", "ubl", "cii"]

    def extract(self, text: str, file_name: str = "") -> InvoiceExtraction:
        invoice_number = _first([r"Facture\s+n[^\dA-Z]{0,5}([A-Z]{1,4}\d{3,})", r"\b(FA\d{3,})\b"], text)
        date_raw = _first([r"Date\s*:\s*(\d{2}[./-]\d{2}[./-]20\d{2})"], text)
        siren_siret = re.sub(r"\D", "", _first([r"SIRET\s*:?\s*([0-9 .]{14,22})", r"\b(519\s*028\s*641\s*00016)\b"], text))

        ht = tva = ttc = ""
        totals_block = re.search(
            r"Total\s+HT\s+Total\s+TVA\s+Total\s+TTC\s+Net\s+.{0,20}?payer(.{0,220})",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if totals_block:
            values = _money_values(totals_block.group(1))
            if len(values) >= 3:
                ht, tva, ttc = values[:3]

        extraction = InvoiceExtraction(
            provider_key=self.provider_key,
            fournisseur="EDELEN",
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
