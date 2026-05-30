from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .pdftrace_contracts import (
    DOCUMENT_HASH_MATCH,
    DOCUMENT_HASH_MISMATCH,
    DOCUMENT_HASH_NOT_CHECKED,
    NO_SOURCE_WRITE_NOTICE,
    PROOF_STATUS_CANDIDATE,
    PUBLIC_TEXT_EXCERPT_MASK,
    SCHEMA_VERSION,
    SOURCE_ENGINE_MANUAL,
    SOURCE_ENGINE_PYMUPDF,
    TEXT_STATUS_CONFIRMED,
    TEXT_STATUS_RECOGNIZED,
    TEXT_STATUS_REVIEW_REQUIRED,
    TEXT_STATUS_UNCONFIRMED,
    ZOTERO_POSITION_KIND,
    clean_text,
    contains_sensitive_text,
    document_hash_status,
    file_sha256,
    hash_text,
    normalize_hash,
    public_excerpt,
    public_selection_hash,
    search_text,
    text_status_from_map,
    text_status_label,
    user_notice,
    validate_document_identity,
)


@dataclass(frozen=True)
class PdfTextRect:
    page_index: int
    text: str
    x: float
    y: float
    width: float
    height: float
    block: int = 0
    line: int = 0
    word: int = 0


@dataclass(frozen=True)
class PdfPageTextMap:
    page_index: int
    page_label: str
    width: float
    height: float
    rotation: int
    words: tuple[PdfTextRect, ...]


@dataclass(frozen=True)
class PdfTextMap:
    document_ref: str
    document_hash: str
    source_engine: str
    pages: tuple[PdfPageTextMap, ...]
    document_hash_status: str = DOCUMENT_HASH_MATCH


@dataclass(frozen=True)
class PdfTraceCandidate:
    document_ref: str
    document_hash: str
    page_index: int
    page_label: str
    rects: tuple[PdfTextRect, ...]
    selected_text: str
    selected_text_hash: str
    anchor_hash: str
    sort_index: str
    source_engine: str
    confidence: str = "text_coordinates"
    private_excerpt_blocked: bool = False
    text_status: str = TEXT_STATUS_CONFIRMED
    proof_status: str = PROOF_STATUS_CANDIDATE
    document_hash_status: str = DOCUMENT_HASH_MATCH


def extract_pdf_text_map(
    path: Path,
    *,
    document_ref: str,
    document_hash: str,
) -> PdfTextMap:
    """Extract a visual text map from a text PDF without mutating the source."""

    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyMuPDF/fitz indisponible pour la carte visuelle PDF.") from exc

    validate_document_identity(document_ref, document_hash)
    source_hash = file_sha256(path) if path.is_file() else ""
    hash_status = document_hash_status(document_hash, source_hash)
    document = fitz.open(str(path))
    try:
        pages: list[PdfPageTextMap] = []
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            width = max(float(page.rect.width), 1.0)
            height = max(float(page.rect.height), 1.0)
            words = tuple(
                _word_from_pymupdf(page_index, width, height, raw_word)
                for raw_word in page.get_text("words")
                if len(raw_word) >= 5 and clean_text(str(raw_word[4]))
            )
            pages.append(
                PdfPageTextMap(
                    page_index=page_index,
                    page_label=str(page_index + 1),
                    width=width,
                    height=height,
                    rotation=int(getattr(page, "rotation", 0) or 0),
                    words=words,
                )
            )
    finally:
        document.close()
    if source_hash and path.is_file() and file_sha256(path) != source_hash:
        hash_status = DOCUMENT_HASH_MISMATCH
    return PdfTextMap(
        document_ref=document_ref,
        document_hash=normalize_hash(document_hash),
        source_engine=SOURCE_ENGINE_PYMUPDF,
        pages=tuple(pages),
        document_hash_status=hash_status,
    )


def build_text_map_from_words(
    *,
    document_ref: str,
    document_hash: str,
    pages: Iterable[Mapping[str, Any]],
    source_engine: str = SOURCE_ENGINE_MANUAL,
    document_hash_status: str = DOCUMENT_HASH_MATCH,
) -> PdfTextMap:
    validate_document_identity(document_ref, document_hash)
    mapped_pages: list[PdfPageTextMap] = []
    for page in pages:
        page_index = _positive_int(page.get("page_index"), default=len(mapped_pages))
        width = max(_float(page.get("width"), 1.0), 1.0)
        height = max(_float(page.get("height"), 1.0), 1.0)
        words = tuple(_word_from_mapping(page_index, width, height, word) for word in _as_words(page.get("words")))
        mapped_pages.append(
            PdfPageTextMap(
                page_index=page_index,
                page_label=str(page.get("page_label") or page_index + 1),
                width=width,
                height=height,
                rotation=_positive_int(page.get("rotation"), default=0),
                words=words,
            )
        )
    return PdfTextMap(
        document_ref=document_ref,
        document_hash=normalize_hash(document_hash),
        source_engine=source_engine,
        pages=tuple(mapped_pages),
        document_hash_status=document_hash_status,
    )


def find_text_traces(
    text_map: PdfTextMap,
    query: str,
    *,
    max_candidates: int = 10,
) -> tuple[PdfTraceCandidate, ...]:
    needle = search_text(query)
    if not needle:
        return tuple()
    candidates: list[PdfTraceCandidate] = []
    for page in text_map.pages:
        haystack, spans = _page_search_index(page.words)
        start = 0
        while len(candidates) < max_candidates:
            match_start = haystack.find(needle, start)
            if match_start < 0:
                break
            match_end = match_start + len(needle)
            matched_words = tuple(
                word for word, span_start, span_end in spans if span_start < match_end and span_end > match_start
            )
            if matched_words:
                candidates.append(_candidate_from_words(text_map, page, matched_words))
            start = max(match_end, match_start + 1)
    return tuple(candidates)


def build_zone_trace_candidate(
    *,
    document_ref: str,
    document_hash: str,
    page_index: int,
    zone: Mapping[str, Any],
    page_label: str = "",
    source_engine: str = SOURCE_ENGINE_MANUAL,
    confidence: str = "zone_only",
) -> PdfTraceCandidate:
    validate_document_identity(document_ref, document_hash)
    safe_page_index = _positive_int(page_index, default=0)
    rect = _rect_from_zone(safe_page_index, zone)
    anchor_hash = hash_text(
        f"{document_ref}|{normalize_hash(document_hash)}|{safe_page_index}|"
        f"{rect.x}|{rect.y}|{rect.width}|{rect.height}"
    )
    return PdfTraceCandidate(
        document_ref=document_ref,
        document_hash=normalize_hash(document_hash),
        page_index=safe_page_index,
        page_label=page_label or str(safe_page_index + 1),
        rects=(rect,),
        selected_text="",
        selected_text_hash=hash_text(""),
        anchor_hash=anchor_hash,
        sort_index=f"{safe_page_index:05d}|{rect.y:.6f}|{rect.x:.6f}",
        source_engine=source_engine,
        confidence=confidence,
        text_status=TEXT_STATUS_UNCONFIRMED,
    )


def candidate_to_annotation_row(
    candidate: PdfTraceCandidate,
    *,
    comment: str,
    author_ref: str,
    created_at: str,
    point_ref: str,
    action_ref: str,
    proof_ref: str,
    annotation_id: str = "",
    diffusion: str = "non_diffusable",
    confidentiality: str = "reserve_cs",
) -> dict[str, Any]:
    zone = union_zone(candidate.rects)
    stable_id = annotation_id or _stable_ref(
        "ANN",
        candidate.document_ref,
        str(candidate.page_index),
        candidate.anchor_hash[-12:],
    )
    return {
        "annotation_id": stable_id,
        "document_ref": candidate.document_ref,
        "document_hash": candidate.document_hash,
        "page": candidate.page_index + 1,
        "zone": zone,
        "rects": [rect_to_position(rect) for rect in candidate.rects],
        "target_kind": "pdf",
        "fragment_ref": f"pdf-trace:{candidate.anchor_hash[-16:]}",
        "anchor_hash": candidate.anchor_hash,
        "comment": comment,
        "author_ref": author_ref,
        "created_at": created_at,
        "point_ref": point_ref,
        "action_ref": action_ref,
        "proof_ref": proof_ref,
        "status": "ouverte",
        "diffusion": diffusion,
        "confidentiality": confidentiality,
        "proof_status": candidate.proof_status,
        "text_status": candidate.text_status,
        "document_hash_status": candidate.document_hash_status,
    }


def candidate_to_public_dict(candidate: PdfTraceCandidate) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "document_ref": candidate.document_ref,
        "document_hash": candidate.document_hash,
        "source_engine": candidate.source_engine,
        "confidence": candidate.confidence,
        "text_status": candidate.text_status,
        "text_status_label": text_status_label(candidate),
        "proof_status": candidate.proof_status,
        "document_hash_status": candidate.document_hash_status,
        "selected_text_hash": public_selection_hash(candidate),
        "anchor_hash": candidate.anchor_hash,
        "selected_text_excerpt": public_excerpt(candidate),
        "private_excerpt_blocked": candidate.private_excerpt_blocked,
        "coproscope_anchor": {
            "page": candidate.page_index + 1,
            "page_label": candidate.page_label,
            "zone": union_zone(candidate.rects),
        },
        "zotero_position": zotero_position(candidate),
        "write_policy": NO_SOURCE_WRITE_NOTICE,
        "user_notice": user_notice(candidate),
    }


def zotero_position(candidate: PdfTraceCandidate) -> dict[str, Any]:
    return {
        "kind": ZOTERO_POSITION_KIND,
        "pageIndex": candidate.page_index,
        "pageLabel": candidate.page_label,
        "rects": [rect_to_position(rect) for rect in candidate.rects],
        "sortIndex": candidate.sort_index,
    }


def rect_to_position(rect: PdfTextRect) -> dict[str, float]:
    return {
        "x": rect.x,
        "y": rect.y,
        "width": rect.width,
        "height": rect.height,
    }


def union_zone(rects: Sequence[PdfTextRect]) -> dict[str, float]:
    if not rects:
        return {"x": 0.0, "y": 0.0, "width": 0.0, "height": 0.0}
    left = min(rect.x for rect in rects)
    top = min(rect.y for rect in rects)
    right = max(rect.x + rect.width for rect in rects)
    bottom = max(rect.y + rect.height for rect in rects)
    return {
        "x": _round(left),
        "y": _round(top),
        "width": _round(max(0.0, right - left)),
        "height": _round(max(0.0, bottom - top)),
    }


def text_map_to_dict(text_map: PdfTextMap) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "document_ref": text_map.document_ref,
        "document_hash": text_map.document_hash,
        "document_hash_status": text_map.document_hash_status,
        "source_engine": text_map.source_engine,
        "pages": [
            {
                "page_index": page.page_index,
                "page_label": page.page_label,
                "width": page.width,
                "height": page.height,
                "rotation": page.rotation,
                "word_count": len(page.words),
            }
            for page in text_map.pages
        ],
        "write_policy": NO_SOURCE_WRITE_NOTICE,
    }


def _candidate_from_words(
    text_map: PdfTextMap,
    page: PdfPageTextMap,
    words: tuple[PdfTextRect, ...],
) -> PdfTraceCandidate:
    selected_text = " ".join(word.text for word in words)
    first = min(words, key=lambda rect: (rect.y, rect.x))
    private_excerpt_blocked = contains_sensitive_text(selected_text)
    selected_text_hash = hash_text(selected_text)
    return PdfTraceCandidate(
        document_ref=text_map.document_ref,
        document_hash=text_map.document_hash,
        page_index=page.page_index,
        page_label=page.page_label,
        rects=words,
        selected_text=selected_text,
        selected_text_hash=selected_text_hash,
        anchor_hash=_anchor_hash(text_map, page, words, selected_text_hash),
        sort_index=f"{page.page_index:05d}|{first.y:.6f}|{first.x:.6f}",
        source_engine=text_map.source_engine,
        private_excerpt_blocked=private_excerpt_blocked,
        text_status=text_status_from_map(text_map),
        document_hash_status=text_map.document_hash_status,
    )


def _anchor_hash(
    text_map: PdfTextMap,
    page: PdfPageTextMap,
    rects: Sequence[PdfTextRect],
    selected_text_hash: str,
) -> str:
    rect_material = ";".join(f"{rect.x},{rect.y},{rect.width},{rect.height}" for rect in rects)
    return hash_text(
        "|".join(
            (
                text_map.document_ref,
                text_map.document_hash,
                str(page.page_index),
                page.page_label,
                selected_text_hash,
                rect_material,
            )
        )
    )


def _word_from_pymupdf(page_index: int, width: float, height: float, raw_word: Sequence[Any]) -> PdfTextRect:
    x0, y0, x1, y1 = (_float(raw_word[index], 0.0) for index in range(4))
    x = _round(_clamp(x0 / width))
    y = _round(_clamp(y0 / height))
    return PdfTextRect(
        page_index=page_index,
        text=clean_text(str(raw_word[4])),
        x=x,
        y=y,
        width=_round(_clamp_extent(x, (x1 - x0) / width)),
        height=_round(_clamp_extent(y, (y1 - y0) / height)),
        block=_positive_int(raw_word[5], default=0) if len(raw_word) > 5 else 0,
        line=_positive_int(raw_word[6], default=0) if len(raw_word) > 6 else 0,
        word=_positive_int(raw_word[7], default=0) if len(raw_word) > 7 else 0,
    )


def _word_from_mapping(page_index: int, width: float, height: float, word: Mapping[str, Any]) -> PdfTextRect:
    if {"x0", "y0", "x1", "y1"}.issubset(word.keys()):
        x = _float(word.get("x0"), 0.0) / width
        y = _float(word.get("y0"), 0.0) / height
        rect_width = (_float(word.get("x1"), 0.0) - _float(word.get("x0"), 0.0)) / width
        rect_height = (_float(word.get("y1"), 0.0) - _float(word.get("y0"), 0.0)) / height
    else:
        x = _float(word.get("x"), 0.0)
        y = _float(word.get("y"), 0.0)
        rect_width = _float(word.get("width"), 0.0)
        rect_height = _float(word.get("height"), 0.0)
    x = _round(_clamp(x))
    y = _round(_clamp(y))
    return PdfTextRect(
        page_index=page_index,
        text=clean_text(str(word.get("text", ""))),
        x=x,
        y=y,
        width=_round(_clamp_extent(x, rect_width)),
        height=_round(_clamp_extent(y, rect_height)),
        block=_positive_int(word.get("block"), default=0),
        line=_positive_int(word.get("line"), default=0),
        word=_positive_int(word.get("word"), default=0),
    )


def _rect_from_zone(page_index: int, zone: Mapping[str, Any]) -> PdfTextRect:
    x = _round(_clamp(_float(zone.get("x"), 0.0)))
    y = _round(_clamp(_float(zone.get("y"), 0.0)))
    rect_width = _round(_clamp_extent(x, _float(zone.get("width", zone.get("w")), 0.0)))
    rect_height = _round(_clamp_extent(y, _float(zone.get("height", zone.get("h")), 0.0)))
    return PdfTextRect(
        page_index=page_index,
        text="",
        x=x,
        y=y,
        width=rect_width,
        height=rect_height,
    )


def _as_words(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes)):
        return tuple()
    return tuple(word for word in value if isinstance(word, Mapping))


def _page_search_index(words: Sequence[PdfTextRect]) -> tuple[str, tuple[tuple[PdfTextRect, int, int], ...]]:
    parts: list[str] = []
    spans: list[tuple[PdfTextRect, int, int]] = []
    cursor = 0
    for word in words:
        normalized = search_text(word.text)
        if not normalized:
            continue
        if parts:
            parts.append(" ")
            cursor += 1
        start = cursor
        parts.append(normalized)
        cursor += len(normalized)
        spans.append((word, start, cursor))
    return "".join(parts), tuple(spans)


def _stable_ref(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return "-".join(part for part in (parts[0], digest) if part)


def _float(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _positive_int(value: object, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def _clamp_extent(start: float, size: float) -> float:
    return max(0.0, min(max(0.0, size), 1.0 - start))


def _round(value: float) -> float:
    return round(value, 6)


__all__ = [
    "NO_SOURCE_WRITE_NOTICE",
    "DOCUMENT_HASH_MATCH",
    "DOCUMENT_HASH_MISMATCH",
    "DOCUMENT_HASH_NOT_CHECKED",
    "PdfPageTextMap",
    "PdfTraceCandidate",
    "PdfTextMap",
    "PdfTextRect",
    "PUBLIC_TEXT_EXCERPT_MASK",
    "PROOF_STATUS_CANDIDATE",
    "SCHEMA_VERSION",
    "SOURCE_ENGINE_MANUAL",
    "SOURCE_ENGINE_PYMUPDF",
    "TEXT_STATUS_CONFIRMED",
    "TEXT_STATUS_RECOGNIZED",
    "TEXT_STATUS_REVIEW_REQUIRED",
    "TEXT_STATUS_UNCONFIRMED",
    "ZOTERO_POSITION_KIND",
    "build_text_map_from_words",
    "build_zone_trace_candidate",
    "candidate_to_annotation_row",
    "candidate_to_public_dict",
    "extract_pdf_text_map",
    "find_text_traces",
    "rect_to_position",
    "text_map_to_dict",
    "union_zone",
    "zotero_position",
]
