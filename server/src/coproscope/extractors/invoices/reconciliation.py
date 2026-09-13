from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation


DECISION_LIFTED = "LEVEE"
DECISION_PARTIAL = "LEVEE_PARTIELLE"
DECISION_NOT_LIFTED = "NON_LEVEE"
DEFAULT_INTERNAL_CROSS_CHECKS = (
    "source_aliases_and_duplicate_names",
    "native_text_supplier_identity",
    "provider_identity_consensus",
    "ledger_invoice_reference",
    "ledger_amount_payment_reference",
    "ag_budget_contract_decision_rules",
    "amount_arithmetic_ht_tva_ttc",
    "routing_year_and_supplier",
)


@dataclass(frozen=True)
class SupplierRule:
    """Configurable supplier hint used by instances without leaking instance data."""

    supplier: str
    pattern: str
    siren_siret: str = ""
    confidence: str = "TEXT_STRONG"


@dataclass(frozen=True)
class LedgerMatch:
    supplier: str = ""
    evidence: str = ""
    invoice_key: str = ""
    confidence: str = ""


@dataclass(frozen=True)
class SupplierResolution:
    supplier: str = ""
    siren_siret: str = ""
    confidence: str = "UNRESOLVED"
    method: str = "unresolved"
    evidence: str = ""


@dataclass(frozen=True)
class DecisionRule:
    """A generic AG/budget/contract decision rule.

    Instances provide the actual decision references. The matching engine remains
    shareable: it only knows how to apply supplier, year, family, keyword, and
    amount filters.
    """

    rule_id: str
    decision_ref: str
    source: str
    evidence: str
    status: str = DECISION_PARTIAL
    years: tuple[str, ...] = ()
    supplier_patterns: tuple[str, ...] = ()
    family_patterns: tuple[str, ...] = ()
    text_patterns: tuple[str, ...] = ()
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    residual_controls: str = ""


@dataclass
class InvoiceReconciliationInput:
    doc_id: str
    text: str = ""
    file_name: str = ""
    supplier: str = ""
    siren_siret: str = ""
    invoice_number: str = ""
    invoice_date: str = ""
    amount_ttc: str = ""
    control_family: str = ""


@dataclass
class DecisionResolution:
    status: str = DECISION_NOT_LIFTED
    decision_ref: str = ""
    source: str = ""
    evidence: str = ""
    residual_controls: str = ""
    rule_id: str = ""


@dataclass
class InvoiceReconciliationResult:
    doc_id: str
    supplier: SupplierResolution = field(default_factory=SupplierResolution)
    decision: DecisionResolution = field(default_factory=DecisionResolution)
    lifted_anomalies: list[str] = field(default_factory=list)
    residual_anomalies: list[str] = field(default_factory=list)


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value).replace("\u00a0", " ")
    if any(marker in text for marker in ("Ã", "Â", "â")):
        try:
            repaired = text.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
            if repaired:
                text = repaired
        except UnicodeError:
            pass
    return unicodedata.normalize("NFKC", text).strip()


def normalized_for_match(value: str | None) -> str:
    text = normalize_text(value).lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(char for char in text if not unicodedata.combining(char))


def parse_amount(value: str | None) -> Decimal | None:
    text = normalize_text(value)
    if not text:
        return None
    text = text.replace("EUR", "").replace("eur", "").replace("€", "")
    text = re.sub(r"(?<=\d)\s+(?=\d{3}(?:[,.]\d{2})?\b)", "", text)
    text = text.replace(" ", "").replace(",", ".")
    text = re.sub(r"[^0-9.\-]", "", text)
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def invoice_keys(invoice_number: str = "", text: str = "", file_name: str = "") -> set[str]:
    values = [invoice_number]
    values.extend(
        re.findall(
            r"(?:facture|invoice|avoir|devis|reference|ref\.?|n[°o.])\s*(?:n[°o.]|numero|number|ref\.?)?\s*[:#\- ]+\s*([A-Z]{0,5}\s*\d[A-Z0-9 ./_-]{3,20})",
            text,
            flags=re.IGNORECASE,
        )
    )
    if file_name and not re.match(r"facture_?20\d{12,}", file_name, flags=re.IGNORECASE):
        values.append(file_name)
    keys: set[str] = set()
    for value in values:
        cleaned = re.sub(r"[^A-Za-z0-9]", "", normalize_text(value)).upper()
        if len(cleaned) >= 4 and not re.fullmatch(r"(?:19|20)\d{2}", cleaned):
            keys.add(cleaned)
        digits = re.sub(r"\D", "", cleaned)
        if len(digits) >= 4 and not re.fullmatch(r"(?:19|20)\d{2}", digits):
            keys.add(digits)
    return keys


def supplier_from_text(text: str, supplier_rules: list[SupplierRule]) -> SupplierResolution:
    for rule in supplier_rules:
        if re.search(rule.pattern, text, flags=re.IGNORECASE):
            return SupplierResolution(
                supplier=rule.supplier,
                siren_siret=re.sub(r"\D", "", rule.siren_siret),
                confidence=rule.confidence,
                method="text_rule",
                evidence=rule.pattern,
            )
    return SupplierResolution()


def supplier_from_ledger(keys: set[str], ledger_lines: list[str]) -> LedgerMatch:
    if not keys:
        return LedgerMatch()
    usable_keys = {
        key
        for key in keys
        if not re.fullmatch(r"(?:19|20)\d{2}", key)
        and not (key.isdigit() and len(key) <= 4)
    }
    if not usable_keys:
        return LedgerMatch()
    sorted_keys = sorted(usable_keys, key=len, reverse=True)
    for raw_line in ledger_lines:
        line = normalize_text(raw_line)
        if not re.match(r"^\s*\d{2}/\d{2}/\d{2,4}\s+\S+\s+", line):
            continue
        compact = re.sub(r"[^A-Za-z0-9]", "", line).upper()
        matched_key = next((key for key in sorted_keys if key and key in compact), "")
        if not matched_key:
            continue
        # Typical French copro ledgers: "dd/mm/yy FC123 SUPPLIER/ label amount".
        match = re.search(r"\b(?:\d{2}/\d{2}/\d{2,4}\s+)?[A-Z0-9./-]{3,20}\s+(.+?)/", line)
        if match:
            supplier = normalize_text(match.group(1)).strip(" -")
            if supplier:
                return LedgerMatch(
                    supplier=supplier,
                    evidence=line,
                    invoice_key=matched_key,
                    confidence="LEDGER_MATCH",
                )
        match = re.search(r"\b([A-Z][A-Z0-9 .&'_-]{2,50})/", line)
        if match:
            return LedgerMatch(
                supplier=normalize_text(match.group(1)).strip(" -"),
                evidence=line,
                invoice_key=matched_key,
                confidence="LEDGER_MATCH",
            )
    return LedgerMatch()


def resolve_supplier(
    invoice: InvoiceReconciliationInput,
    supplier_rules: list[SupplierRule] | None = None,
    ledger_lines: list[str] | None = None,
) -> SupplierResolution:
    supplier_rules = supplier_rules or []
    ledger_lines = ledger_lines or []

    text_resolution = supplier_from_text(invoice.text, supplier_rules)
    keys = invoice_keys(invoice.invoice_number, invoice.text, invoice.file_name)
    ledger_resolution = supplier_from_ledger(keys, ledger_lines)

    if text_resolution.supplier and ledger_resolution.supplier:
        left = normalized_for_match(text_resolution.supplier)
        right = normalized_for_match(ledger_resolution.supplier)
        if left in right or right in left:
            return SupplierResolution(
                supplier=text_resolution.supplier,
                siren_siret=text_resolution.siren_siret,
                confidence="TEXT_AND_LEDGER_MATCH",
                method="text_rule+ledger",
                evidence=f"{text_resolution.evidence} / {ledger_resolution.evidence}",
            )
        return SupplierResolution(
            supplier=text_resolution.supplier,
            siren_siret=text_resolution.siren_siret,
            confidence="CONFLICT_TEXT_LEDGER",
            method="text_rule+ledger_conflict",
            evidence=f"text={text_resolution.supplier}; ledger={ledger_resolution.supplier}; {ledger_resolution.evidence}",
        )

    if text_resolution.supplier:
        return text_resolution
    if ledger_resolution.supplier:
        return SupplierResolution(
            supplier=ledger_resolution.supplier,
            confidence=ledger_resolution.confidence,
            method="ledger",
            evidence=ledger_resolution.evidence,
        )
    if invoice.supplier and invoice.supplier != "FOURNISSEUR_A_IDENTIFIER":
        return SupplierResolution(
            supplier=invoice.supplier,
            siren_siret=invoice.siren_siret,
            confidence="EXISTING_VALUE",
            method="existing_invoice_value",
            evidence="invoice input",
        )
    return SupplierResolution()


def _matches_any(patterns: tuple[str, ...], value: str) -> bool:
    if not patterns:
        return True
    return any(re.search(pattern, value, flags=re.IGNORECASE) for pattern in patterns)


def _year_from_date(value: str) -> str:
    match = re.search(r"(20\d{2})", value or "")
    return match.group(1) if match else ""


def resolve_decision(
    invoice: InvoiceReconciliationInput,
    supplier: str,
    decision_rules: list[DecisionRule] | None = None,
) -> DecisionResolution:
    decision_rules = decision_rules or []
    year = _year_from_date(invoice.invoice_date)
    amount = parse_amount(invoice.amount_ttc)
    haystack = "\n".join(
        [
            normalize_text(invoice.text),
            normalize_text(invoice.file_name),
            normalize_text(invoice.control_family),
            normalize_text(supplier),
        ]
    )

    for rule in decision_rules:
        if rule.years and year not in rule.years:
            continue
        if not _matches_any(rule.supplier_patterns, supplier):
            continue
        if not _matches_any(rule.family_patterns, invoice.control_family):
            continue
        if not _matches_any(rule.text_patterns, haystack):
            continue
        if rule.min_amount is not None and (amount is None or amount < rule.min_amount):
            continue
        if rule.max_amount is not None and amount is not None and amount > rule.max_amount:
            continue
        return DecisionResolution(
            status=rule.status,
            decision_ref=rule.decision_ref,
            source=rule.source,
            evidence=rule.evidence,
            residual_controls=rule.residual_controls,
            rule_id=rule.rule_id,
        )

    return DecisionResolution()


class DefaultInvoiceReconciler:
    """Default cross-check engine for invoice exploitation workflows."""

    def __init__(
        self,
        supplier_rules: list[SupplierRule] | None = None,
        ledger_lines: list[str] | None = None,
        decision_rules: list[DecisionRule] | None = None,
    ) -> None:
        self.supplier_rules = supplier_rules or []
        self.ledger_lines = ledger_lines or []
        self.decision_rules = decision_rules or []

    def reconcile(self, invoice: InvoiceReconciliationInput) -> InvoiceReconciliationResult:
        supplier = resolve_supplier(invoice, self.supplier_rules, self.ledger_lines)
        decision = resolve_decision(invoice, supplier.supplier or invoice.supplier, self.decision_rules)

        lifted: list[str] = []
        residual: list[str] = []
        if supplier.supplier and supplier.supplier != invoice.supplier:
            lifted.append("FOURNISSEUR_A_IDENTIFIER")
        if supplier.siren_siret and supplier.siren_siret != invoice.siren_siret:
            lifted.append("SIREN_SIRET_ABSENT")
        if decision.status in {DECISION_LIFTED, DECISION_PARTIAL}:
            lifted.append("DECISION_MANQUANTE")
        if decision.status == DECISION_PARTIAL:
            residual.append("CONTROLES_RESIDUELS_REQUIS")
        if supplier.confidence in {"CONFLICT_TEXT_LEDGER", "UNRESOLVED"}:
            residual.append("FOURNISSEUR_A_VERIFIER")

        return InvoiceReconciliationResult(
            doc_id=invoice.doc_id,
            supplier=supplier,
            decision=decision,
            lifted_anomalies=list(dict.fromkeys(lifted)),
            residual_anomalies=list(dict.fromkeys(residual)),
        )
