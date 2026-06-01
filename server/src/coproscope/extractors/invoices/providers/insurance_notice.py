from __future__ import annotations

import re
import unicodedata

from ..base import InvoiceExtraction, normalize_amount


AMOUNT = r"(-?\d[\d .]*[,.]\d{2})"
MONTHS = {
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


def _plain(value: str) -> str:
    raw = value.lower()
    replacements = {
        "\u00c3\u00a9": "e",
        "\u00c3\u00a8": "e",
        "\u00c3\u00aa": "e",
        "\u00c3\u00a0": "a",
        "\u00c3\u00a2": "a",
        "\u00c3\u00b9": "u",
        "\u00c3\u00bb": "u",
        "\u00c3\u00ae": "i",
        "\u00c3\u00af": "i",
        "\u00c3\u00b4": "o",
        "\u00c3\u00a7": "c",
    }
    for source, target in replacements.items():
        raw = raw.replace(source, target)
    return unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")


def _first(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    return ""


def _amount(patterns: list[str], text: str) -> str:
    value = _first(patterns, text)
    return normalize_amount(value) if value else ""


def _french_date_to_iso(text: str) -> str:
    plain = _plain(text)
    match = re.search(
        r"\ble\s+(?:lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)?\s*(\d{1,2})\s+"
        r"(janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)\s+(20\d{2})",
        plain,
    )
    if not match:
        return ""
    day, month_name, year = match.groups()
    return f"{year}-{MONTHS[month_name]}-{int(day):02d}"


def _supplier(text: str) -> str:
    if re.search(r"\bcabinet\s+ripert\s+de\s+grissac\b", _plain(text), flags=re.IGNORECASE):
        return "RIPERT DE GRISSAC"
    company = _first([r"\bCompagnie\s*:\s*([A-Z][A-Z0-9&.' -]{2,40})"], text)
    return company or "ASSURANCE IMMEUBLE"


class InsuranceNoticeProviderExtractor:
    """Extractor for building insurance premium notices."""

    provider_key = "insurance_notice"
    status = "generalizable"
    supported_inputs = ["pdf_text"]

    def extract(self, text: str, file_name: str = "") -> InvoiceExtraction:
        quittance = _first([r"N\S*\s+de\s+quittance\s*:\s*([A-Z0-9._/-]+)", r"\b([0-9]{4}RDG[0-9]+)\b"], text)
        police = _first([r"N\S*\s+de\s+Police\s*:\s*([A-Z0-9._/-]+)", r"\bPolice\s*:\s*([A-Z0-9._/-]+)"], text)
        total = _amount(
            [
                rf"Solde\s+d\S*\s*:\s*{AMOUNT}",
                rf"Montant\s+de\s+la\s+quittance\s*:\s*{AMOUNT}",
                rf"Total\s+TTC.{{0,120}}?{AMOUNT}",
            ],
            text,
        )

        extraction = InvoiceExtraction(
            provider_key=self.provider_key,
            fournisseur=_supplier(text),
            numero_facture=quittance or police,
            date_facture=_french_date_to_iso(text),
            tva="0.00" if re.search(r"exoneree?\s+de\s+tva|article\s+261\s+c", _plain(text)) else "",
            ttc=total,
            anomalies=["ASSURANCE_RIB_A_CONTROLER"],
            confidence="high" if total and (quittance or police) else "medium",
        )
        if not extraction.numero_facture:
            extraction.anomalies.append("NUMERO_FACTURE_ABSENT")
        if not extraction.date_facture:
            extraction.anomalies.append("DATE_FACTURE_ABSENTE")
        if not extraction.ttc:
            extraction.anomalies.append("MONTANT_TTC_ABSENT")
        return extraction
