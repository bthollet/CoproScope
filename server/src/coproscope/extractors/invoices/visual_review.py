from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

UNRESOLVED_SUPPLIER = "FOURNISSEUR_A_IDENTIFIER"
TEXT_EXPLOITATION_PRIORITY = (
    "P1_NATIVE_TEXT",
    "P2_LOCAL_OCR",
    "P3_LOCAL_VISUAL_TOOL",
    "P4_AI_OR_ONLINE_VISUAL",
)
PARSING_LEVELS_REQUIRING_CONFIRMATION = frozenset({"P4_AI_OR_ONLINE_VISUAL"})
DEFAULT_VISUAL_REVIEW_PROMPT = (
    "Use P3 local visual review first, then propose P4 AI or online vision only for "
    "residual cases after P1 native text and P2 local OCR. P4 requires explicit user "
    "confirmation before any external or AI-vision processing. Review compact first-page "
    "contact sheets only. Identify supplier headers, logos, legal names, and obvious "
    "non-invoice receipts. Return evidence-backed overrides; do not mark accounting "
    "validation as final."
)


@dataclass(frozen=True)
class VisualReviewItem:
    doc_id: str
    file_name: str = ""
    supplier: str = ""
    confidence: str = ""
    text_chars: int = 0
    reason: str = "supplier_unresolved"
    source_path: str = ""


@dataclass(frozen=True)
class VisualReviewBatch:
    batch_id: str
    contact_sheet_name: str
    items: tuple[VisualReviewItem, ...]
    prompt_hint: str = DEFAULT_VISUAL_REVIEW_PROMPT


def parsing_level_requires_confirmation(level: str) -> bool:
    return level.strip().upper() in PARSING_LEVELS_REQUIRING_CONFIRMATION


def needs_visual_supplier_review(
    supplier: str,
    *,
    text_chars: int = 0,
    confidence: str = "",
    min_text_chars: int = 80,
) -> bool:
    """Return True when a frugal visual pass can add supplier evidence."""

    normalized_supplier = supplier.strip().upper()
    normalized_confidence = confidence.strip().upper()
    unresolved_supplier = (
        not normalized_supplier
        or normalized_supplier == UNRESOLVED_SUPPLIER
        or normalized_supplier.endswith("_A_IDENTIFIER")
    )
    weak_text_evidence = text_chars < min_text_chars and normalized_confidence not in {
        "TEXT_STRONG",
        "TEXT_AND_LEDGER_MATCH",
        "IA_VISUELLE_CONFIRME",
    }
    weak_confidence = normalized_confidence in {"", "UNRESOLVED", "NO_MATCH", "OCR_REQUIRED", "TEXT_WEAK"}
    return unresolved_supplier or (weak_text_evidence and weak_confidence)


def build_visual_review_batches(
    items: Iterable[VisualReviewItem],
    *,
    batch_size: int = 6,
    contact_sheet_prefix: str = "contact_sheet",
    prompt_hint: str = DEFAULT_VISUAL_REVIEW_PROMPT,
) -> tuple[VisualReviewBatch, ...]:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    planned_items = tuple(items)
    batches: list[VisualReviewBatch] = []
    for offset in range(0, len(planned_items), batch_size):
        number = (offset // batch_size) + 1
        batch_id = f"{contact_sheet_prefix}_{number:02d}"
        batches.append(
            VisualReviewBatch(
                batch_id=batch_id,
                contact_sheet_name=f"{batch_id}.png",
                items=planned_items[offset : offset + batch_size],
                prompt_hint=prompt_hint,
            )
        )
    return tuple(batches)
