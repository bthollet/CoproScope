from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .pdftrace_contracts import contains_sensitive_text, hash_text, text_status_from_map
from .pdftraceops import PdfTextMap, PdfTextRect, PdfTraceCandidate


def build_zone_text_candidate(
    text_map: PdfTextMap,
    *,
    page_index: int,
    page_label: str,
    zone: Mapping[str, Any],
) -> PdfTraceCandidate | None:
    page = next((item for item in text_map.pages if item.page_index == page_index), None)
    if page is None:
        return None
    selected_words = tuple(
        sorted(
            (word for word in page.words if _overlaps(word, zone)),
            key=lambda word: (word.block, word.line, word.word, word.y, word.x),
        )
    )
    if not selected_words:
        return None
    selected_text = " ".join(word.text for word in selected_words if word.text.strip())
    if not selected_text.strip():
        return None
    selected_text_hash = hash_text(selected_text)
    first = min(selected_words, key=lambda rect: (rect.y, rect.x))
    return PdfTraceCandidate(
        document_ref=text_map.document_ref,
        document_hash=text_map.document_hash,
        page_index=page_index,
        page_label=page_label or page.page_label,
        rects=selected_words,
        selected_text=selected_text,
        selected_text_hash=selected_text_hash,
        anchor_hash=_anchor_hash(text_map, page_index, selected_words, selected_text_hash),
        sort_index=f"{page_index:05d}|{first.y:.6f}|{first.x:.6f}",
        source_engine=text_map.source_engine,
        confidence="text_from_selected_zone",
        private_excerpt_blocked=contains_sensitive_text(selected_text),
        text_status=text_status_from_map(text_map),
        document_hash_status=text_map.document_hash_status,
    )


def _overlaps(word: PdfTextRect, zone: Mapping[str, Any]) -> bool:
    x = _float(zone.get("x"), 0.0)
    y = _float(zone.get("y"), 0.0)
    right = x + _float(zone.get("width"), 0.0)
    bottom = y + _float(zone.get("height"), 0.0)
    word_right = word.x + word.width
    word_bottom = word.y + word.height
    return word.x < right and word_right > x and word.y < bottom and word_bottom > y


def _anchor_hash(
    text_map: PdfTextMap,
    page_index: int,
    rects: tuple[PdfTextRect, ...],
    selected_text_hash: str,
) -> str:
    rect_material = ";".join(f"{rect.x},{rect.y},{rect.width},{rect.height}" for rect in rects)
    return hash_text(
        "|".join(
            (
                text_map.document_ref,
                text_map.document_hash,
                str(page_index),
                selected_text_hash,
                rect_material,
            )
        )
    )


def _float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


__all__ = ["build_zone_text_candidate"]
