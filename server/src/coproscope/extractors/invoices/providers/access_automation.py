from __future__ import annotations

import re

from ..base import InvoiceExtraction, normalize_amount


AMOUNT = r"(-?(?:\d{1,3}(?:[ .\u00a0\u202f]\d{3})+|\d+)[,.]\d{2})"
NUMBER_LABEL = r"Num(?:e|\u00e9)ro"


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


def _supplier_from_lines(text: str) -> str:
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip(" :-")
        if not re.fullmatch(r"(?:EURL\s+)?[A-Z][A-Z0-9&.' -]{5,80}", line):
            continue
        if "AUTOMATISME" in line and "SERVICE" in line:
            return line
    return ""


def _totals(text: str) -> tuple[str, str, str]:
    match = re.search(
        rf"Total\s+HT\s+Total\s+TVA\s+Total\s+TTC\s+{AMOUNT}\s+{AMOUNT}\s+{AMOUNT}",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return "", "", ""
    ht, tva, ttc = match.groups()
    return normalize_amount(ht), normalize_amount(tva), normalize_amount(ttc)


class AccessAutomationInvoiceProviderExtractor:
    """Extractor for access automation and door-control invoices."""

    provider_key = "access_automation"
    status = "generalizable"
    supported_inputs = ["pdf_text", "factur-x", "xml", "ubl", "cii"]

    def extract(self, text: str, file_name: str = "") -> InvoiceExtraction:
        supplier = _supplier_from_lines(text)
        invoice_number = _first([rf"\b{NUMBER_LABEL}\s+([A-Z]{{1,4}}\d{{5,}}[A-Z0-9._/-]*)"], text)
        date_raw = _first(
            [
                rf"\bDate\s+(\d{{2}}/\d{{2}}/20\d{{2}})\s+{NUMBER_LABEL}",
                r"\bDate\s+(\d{2}/\d{2}/20\d{2})",
            ],
            text,
        )
        siren_siret = re.sub(r"\D", "", _first([r"Siret\s*:?\s*([0-9 .]{14,22})"], text))
        ht, tva, ttc = _totals(text)

        extraction = InvoiceExtraction(
            provider_key=self.provider_key,
            fournisseur=supplier,
            siren_siret=siren_siret,
            numero_facture=invoice_number,
            date_facture=_date_to_iso(date_raw),
            ht=ht,
            tva=tva,
            ttc=ttc,
            confidence="high" if supplier and invoice_number and ttc else "medium",
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
        return extraction
