"""Invoice extraction primitives.

The operational rule is provider-first: filename families can help route
documents, but accounting extraction should be delegated to a provider
sub-extractor whenever one exists.
"""

from .base import (
    DocumentExtractionEvidence,
    REQUIRED_ACCOUNTING_FIELDS,
    InvoiceExtraction,
    detect_invoice_family,
    extract_generic_invoice_from_evidence,
    extract_generic_invoice_fields,
    provider_key_from_name,
)
from .generator import (
    ProviderExtractorSeed,
    build_extractor_generation_prompt,
    build_provider_extractor_seed,
    build_provider_extractor_template,
)
from .reconciliation import (
    DEFAULT_INTERNAL_CROSS_CHECKS,
    DECISION_LIFTED,
    DECISION_NOT_LIFTED,
    DECISION_PARTIAL,
    DecisionResolution,
    DecisionRule,
    DefaultInvoiceReconciler,
    InvoiceReconciliationInput,
    InvoiceReconciliationResult,
    LedgerMatch,
    SupplierResolution,
    SupplierRule,
    invoice_keys,
    resolve_decision,
    resolve_supplier,
    supplier_from_ledger,
)
from .visual_review import (
    DEFAULT_VISUAL_REVIEW_PROMPT,
    PARSING_LEVELS_REQUIRING_CONFIRMATION,
    TEXT_EXPLOITATION_PRIORITY,
    UNRESOLVED_SUPPLIER,
    VisualReviewBatch,
    VisualReviewItem,
    build_visual_review_batches,
    needs_visual_supplier_review,
    parsing_level_requires_confirmation,
)

__all__ = [
    "DEFAULT_VISUAL_REVIEW_PROMPT",
    "DEFAULT_INTERNAL_CROSS_CHECKS",
    "DECISION_LIFTED",
    "DECISION_NOT_LIFTED",
    "DECISION_PARTIAL",
    "DecisionResolution",
    "DecisionRule",
    "DocumentExtractionEvidence",
    "DefaultInvoiceReconciler",
    "InvoiceExtraction",
    "InvoiceReconciliationInput",
    "InvoiceReconciliationResult",
    "LedgerMatch",
    "PARSING_LEVELS_REQUIRING_CONFIRMATION",
    "REQUIRED_ACCOUNTING_FIELDS",
    "SupplierResolution",
    "SupplierRule",
    "ProviderExtractorSeed",
    "TEXT_EXPLOITATION_PRIORITY",
    "UNRESOLVED_SUPPLIER",
    "VisualReviewBatch",
    "VisualReviewItem",
    "build_extractor_generation_prompt",
    "build_provider_extractor_seed",
    "build_provider_extractor_template",
    "build_visual_review_batches",
    "detect_invoice_family",
    "extract_generic_invoice_from_evidence",
    "extract_generic_invoice_fields",
    "invoice_keys",
    "needs_visual_supplier_review",
    "parsing_level_requires_confirmation",
    "provider_key_from_name",
    "resolve_decision",
    "resolve_supplier",
    "supplier_from_ledger",
]
