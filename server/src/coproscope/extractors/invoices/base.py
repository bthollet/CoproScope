from __future__ import annotations

import re
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


def _looks_like_building_reference(context: str) -> bool:
    return bool(re.search(r"\b(b[âa]timent|bat\.?|immeuble|cage)\b", context, flags=re.IGNORECASE))


def _amount_after(labels: list[str], text: str) -> str:
    for label in labels:
        for label_match in re.finditer(label, text, flags=re.IGNORECASE):
            window = text[label_match.end() : label_match.end() + 180]
            for match in re.finditer(r"-?\d[\d\s.,]*(?:[,.]\d{1,2})?", window):
                following = window[match.end() : match.end() + 3]
                if "%" in following:
                    continue
                prefix = window[max(0, match.start() - 45) : match.start()]
                if _looks_like_building_reference(prefix):
                    continue
                amount = normalize_amount(match.group(0))
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
        r"\b\d+\s+(?:avenue|av\.?|rue|all[ée]e|allee|boulevard|bd|chemin|place|traverse|impasse)\b",
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


def _guess_supplier(text: str) -> str:
    skip = {"facture", "avoir", "invoice", "note de debit", "note d'honoraires"}
    bad_fragments = [
        "designation",
        "quantite",
        "prix uni",
        "montant ht",
        "total ht",
        "total ttc",
        "net ht",
        "payer en ligne",
        "nos references",
        "vos references",
        "numero de contrat",
        "numero de facture",
        "sdc ",
        "beauvallon",
        "chavissimmo",
        "installation de chantier",
    ]
    for raw_line in text.splitlines()[:25]:
        line = re.sub(r"\s+", " ", raw_line).strip(" :-\t")
        if len(line) < 3:
            continue
        if line.startswith("====="):
            continue
        if line.lower() in skip:
            continue
        normalized = line.lower()
        if any(fragment in normalized for fragment in bad_fragments):
            continue
        if re.search(r"\d{2}/\d{2}/\d{4}|total|tva|siret|siren|iban|bic|page\s+\d", line, flags=re.IGNORECASE):
            continue
        supplier = _sanitize_supplier_line(line)
        if supplier:
            return supplier
    return ""


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

    date = _first_match(
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

    siren_siret = _first_match(
        [
            r"(?:siret|siren)\s*[:#\- ]+\s*([0-9][0-9 .]{8,20})",
            r"\b([0-9]{3}\s?[0-9]{3}\s?[0-9]{3}(?:\s?[0-9]{5})?)\b",
        ],
        text,
    )
    siren_siret = re.sub(r"\D", "", siren_siret)

    extraction = InvoiceExtraction(
        provider_key=provider_key_from_name(supplier),
        fournisseur=supplier,
        siren_siret=siren_siret,
        numero_facture=invoice_number,
        date_facture=date,
        ht=_amount_after([r"total\s+hors\s+taxes", r"total\s+ht", r"montant\s+ht", r"base\s+ht"], text),
        tva=_amount_after([r"total\s+tva", r"montant\s+tva", r"\btva\b"], text),
        ttc=_amount_after([r"net\s+a\s+payer", r"net\s+à\s+payer", r"total\s+ttc", r"\bttc\b"], text),
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
