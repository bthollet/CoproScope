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


def _date_to_iso(value: str) -> str:
    match = re.match(r"(\d{2})/(\d{2})/(20\d{2})$", value.strip())
    if not match:
        return ""
    day, month, year = match.groups()
    return f"{year}-{month}-{day}"


def _amounts_from_summary(text: str) -> tuple[str, str]:
    match = re.search(
        rf"{AMOUNT}\s+{AMOUNT}\s+20[,.]00\s+T1\s+{AMOUNT}\s+{AMOUNT}\s+{AMOUNT}\s+Montant\s+TVA\s+Base\s+Taux",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return "", ""
    _line_tva, _line_base, _ttc, total_tva, total_ht = match.groups()
    return normalize_amount(total_ht), normalize_amount(total_tva)


class CogelecInvoiceProviderExtractor:
    """Extractor for Cogelec access-control invoices."""

    provider_key = "cogelec"
    status = "generalizable"
    supported_inputs = ["pdf_text", "factur-x", "xml", "ubl", "cii"]

    def extract(self, text: str, file_name: str = "") -> InvoiceExtraction:
        invoice_number = _first([r"Facture\s+n[^\dA-Z]{0,5}([A-Z0-9][A-Z0-9._/-]+)", r"NUM_FACTURE\s*:?\s*([A-Z0-9._/-]+)"], text)
        date_raw = _first([r"DATE_FACTURE\s*:?\s*(\d{2}/\d{2}/20\d{2})", r"\b(\d{2}/\d{2}/20\d{2})\b"], text)
        siren_siret = re.sub(r"\D", "", _first([r"SIRET\s*:?\s*([0-9 .]{14,22})", r"\b(434\s*189\s*221\s*00022)\b"], text))
        ttc_raw = _first([rf"(?:MTT_TTC|NETAPAYER|Net\s+a\s+payer)\s*:?\s*{AMOUNT}", rf"Total\s+TTC[^\d\-]{{0,80}}{AMOUNT}"], text)
        ttc = normalize_amount(ttc_raw) if ttc_raw else ""
        ht, tva = _amounts_from_summary(text)

        extraction = InvoiceExtraction(
            provider_key=self.provider_key,
            fournisseur="COGELEC",
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
