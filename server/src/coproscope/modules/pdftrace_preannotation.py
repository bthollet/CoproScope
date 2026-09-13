from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from ..core.common import InstanceConfig, now_iso, write_csv
from .pdftrace_contracts import (
    NO_SOURCE_WRITE_NOTICE,
    clean_text,
    public_excerpt,
    public_selection_hash,
    search_text,
)
from .pdftrace_registry import MIN_ZONE_SIZE, PDF_TRACE_FIELDS, read_trace_rows, trace_register_path
from .pdftraceops import (
    PdfTextMap,
    PdfTextRect,
    PdfTraceCandidate,
    candidate_to_annotation_row,
    find_text_traces,
)


SOURCE_ENGINE_PREANNOTATION = "moteur_preannotation"

STATUS_ANCHORED = "ancree"
STATUS_ANCHORED_CONTEXT = "ancree_contexte"
STATUS_AMBIGUOUS = "ambigue"
STATUS_ABSENT = "absente"
PREANNOTATION_STATUSES = frozenset(
    {STATUS_ANCHORED, STATUS_ANCHORED_CONTEXT, STATUS_AMBIGUOUS, STATUS_ABSENT}
)

KIND_AMOUNT = "montant"
KIND_DATE = "date"
KIND_REFERENCE = "reference"
KIND_RESOLUTION = "resolution"
KIND_TEXT = "texte"

INVOICE_FIELD_KINDS = {
    "ht": KIND_AMOUNT,
    "tva": KIND_AMOUNT,
    "ttc": KIND_AMOUNT,
    "numero_facture": KIND_REFERENCE,
    "date_facture": KIND_DATE,
    "fournisseur": KIND_TEXT,
}

INVOICE_FIELD_CONTEXT = {
    "ht": ("ht", "hors", "taxes"),
    "tva": ("tva",),
    "ttc": ("ttc", "total"),
    "numero_facture": ("facture", "numero"),
    "date_facture": ("facture", "date"),
}

_CONTEXT_STOPWORDS = frozenset(
    {
        "les", "des", "une", "aux", "sur", "par", "pour", "avec", "dans",
        "est", "sont", "ete", "etre", "cette", "ces", "leur", "leurs",
        "vous", "nous", "dont", "ainsi", "plus", "tout", "tous", "toutes",
    }
)
_CONTEXT_TOKEN_RE = re.compile(r"[^\W\d_]{3,}")

_MONTHS_PLAIN = (
    "janvier", "fevrier", "mars", "avril", "mai", "juin",
    "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
)
_MONTHS_ACCENT = (
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
)

_AMOUNT_RE = re.compile(r"\d{1,3}(?:[  .]\d{3})+,\d{2}|\d+,\d{2}")
_DATE_NUM_RE = re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-](?:\d{4}|\d{2})\b")
_MONTH_ALTERNATION = "|".join(sorted(set(_MONTHS_PLAIN) | {"février", "août", "décembre"}))
_DATE_LONG_RE = re.compile(
    rf"\b\d{{1,2}}(?:er)?\s+(?:{_MONTH_ALTERNATION})\s+\d{{4}}\b",
    re.IGNORECASE,
)
_AMOUNT_NO_CENTS_RE = re.compile(
    r"(?<![\d,.])\d{1,3}(?:[  .]\d{3})+\s*(?:€|euros?\b)"
    r"|(?<![\d,.  ])\b\d{2,7}\s*(?:€|euros?\b)",
    re.IGNORECASE,
)
_RESOLUTION_RE = re.compile(r"r[eé]solution\s*(?:n\s*[°ºo]\s*)?\d+[a-z]?", re.IGNORECASE)
_REFERENCE_RE = re.compile(
    r"(?:facture|fact\.?|devis|avoir|bordereau)\s*(?:n\s*[°ºo]\s*|n\s*[:#]\s*|[:#]\s*)?"
    r"([A-Za-z0-9][A-Za-z0-9./_-]{2,24}\d)",
    re.IGNORECASE,
)
_DATE_PARSE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y")


@dataclass(frozen=True)
class PreannotationTarget:
    field: str
    kind: str
    value: str
    context: tuple[str, ...] = ()


@dataclass(frozen=True)
class PreannotationResult:
    target: PreannotationTarget
    status: str
    matched_variant: str
    occurrences: int
    candidates: tuple[PdfTraceCandidate, ...]


def amount_variants(value: str) -> tuple[str, ...]:
    raw = clean_text(str(value or ""))
    if not raw:
        return tuple()
    variants = [raw]
    compact = raw.replace(" ", " ").replace("€", "").replace("EUR", "").strip()
    compact = compact.replace(" ", "")
    if "," in compact and "." in compact:
        if compact.rfind(",") > compact.rfind("."):
            compact = compact.replace(".", "").replace(",", ".")
        else:
            compact = compact.replace(",", "")
    elif "," in compact:
        compact = compact.replace(",", ".")
    try:
        amount = abs(Decimal(compact)).quantize(Decimal("0.01"))
    except InvalidOperation:
        return tuple(dict.fromkeys(variants))
    int_part, dec_part = f"{amount:.2f}".split(".")
    grouped_space = _group_thousands(int_part, " ")
    grouped_dot = _group_thousands(int_part, ".")
    variants += [
        f"{grouped_space},{dec_part}",
        f"{int_part},{dec_part}",
        f"{grouped_dot},{dec_part}",
        f"{int_part}.{dec_part}",
        f"{grouped_space}.{dec_part}",
    ]
    if dec_part == "00":
        variants += [grouped_space, int_part]
    return tuple(dict.fromkeys(variant for variant in variants if variant))


def date_variants(value: str) -> tuple[str, ...]:
    raw = clean_text(str(value or ""))
    if not raw:
        return tuple()
    parsed: datetime | None = None
    for fmt in _DATE_PARSE_FORMATS:
        try:
            parsed = datetime.strptime(raw, fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        return (raw,)
    day, month, year = parsed.day, parsed.month, parsed.year
    variants = [
        raw,
        f"{day:02d}/{month:02d}/{year}",
        f"{day:02d}-{month:02d}-{year}",
        f"{day:02d}.{month:02d}.{year}",
        f"{year}-{month:02d}-{day:02d}",
        f"{day} {_MONTHS_ACCENT[month - 1]} {year}",
        f"{day} {_MONTHS_PLAIN[month - 1]} {year}",
    ]
    if day == 1:
        variants += [f"1er {_MONTHS_ACCENT[month - 1]} {year}", f"1er {_MONTHS_PLAIN[month - 1]} {year}"]
    return tuple(dict.fromkeys(variants))


def reference_variants(value: str) -> tuple[str, ...]:
    raw = clean_text(str(value or ""))
    if not raw:
        return tuple()
    spaced = clean_text(re.sub(r"[-_/.]+", " ", raw))
    collapsed = re.sub(r"[\s\-_/.]+", "", raw)
    return tuple(dict.fromkeys([raw, spaced, collapsed]))


def variants_for(kind: str, value: str) -> tuple[str, ...]:
    if kind == KIND_AMOUNT:
        return amount_variants(value)
    if kind == KIND_DATE:
        return date_variants(value)
    if kind == KIND_REFERENCE:
        return reference_variants(value)
    cleaned = clean_text(str(value or ""))
    return (cleaned,) if cleaned else tuple()


def targets_from_invoice_row(row: Mapping[str, object]) -> tuple[PreannotationTarget, ...]:
    targets: list[PreannotationTarget] = []
    for field, kind in INVOICE_FIELD_KINDS.items():
        value = clean_text(str(row.get(field, "") or ""))
        if value:
            targets.append(
                PreannotationTarget(
                    field=field,
                    kind=kind,
                    value=value,
                    context=INVOICE_FIELD_CONTEXT.get(field, ()),
                )
            )
    return tuple(targets)


def generic_targets_from_text(text: str, *, max_per_kind: int = 8) -> tuple[PreannotationTarget, ...]:
    """Derive value-targets from already-extracted document text (no detection model)."""

    haystack = str(text or "")
    targets: list[PreannotationTarget] = []
    targets += _merge_kind(
        max_per_kind,
        "montant",
        KIND_AMOUNT,
        _collect(_AMOUNT_RE, haystack, KIND_AMOUNT, "montant", max_per_kind),
        _collect(_AMOUNT_NO_CENTS_RE, haystack, KIND_AMOUNT, "montant", max_per_kind),
    )
    targets += _merge_kind(
        max_per_kind,
        "date",
        KIND_DATE,
        _collect(_DATE_NUM_RE, haystack, KIND_DATE, "date", max_per_kind),
        _collect(_DATE_LONG_RE, haystack, KIND_DATE, "date", max_per_kind),
    )
    targets += _collect(_RESOLUTION_RE, haystack, KIND_RESOLUTION, "resolution", max_per_kind)
    targets += _collect(_REFERENCE_RE, haystack, KIND_REFERENCE, "reference", max_per_kind, group=1)
    return tuple(targets)


def preannotate(
    text_map: PdfTextMap,
    targets: Iterable[PreannotationTarget],
    *,
    max_candidates: int = 8,
) -> tuple[PreannotationResult, ...]:
    """Anchor each target value in the page map; never writes, everything stays candidate."""

    results: list[PreannotationResult] = []
    for target in targets:
        matched_variant = ""
        exact: tuple[PdfTraceCandidate, ...] = tuple()
        for variant in variants_for(target.kind, target.value):
            needle = search_text(variant)
            if not needle:
                continue
            found = find_text_traces(text_map, variant, max_candidates=max_candidates)
            exact = tuple(c for c in found if _anchor_text_matches(c.selected_text, needle))
            if exact:
                matched_variant = variant
                break
        occurrences = len(exact)
        candidates = exact
        if not exact:
            status = STATUS_ABSENT
        elif len(exact) == 1:
            status = STATUS_ANCHORED
        else:
            chosen = _disambiguate_by_line(text_map, exact, target.context)
            if chosen is not None:
                status = STATUS_ANCHORED_CONTEXT
                candidates = (chosen,)
            else:
                status = STATUS_AMBIGUOUS
        results.append(
            PreannotationResult(
                target=target,
                status=status,
                matched_variant=matched_variant,
                occurrences=occurrences,
                candidates=candidates,
            )
        )
    return tuple(results)


def preannotation_summary(results: Iterable[PreannotationResult]) -> dict[str, object]:
    totals = {STATUS_ANCHORED: 0, STATUS_ANCHORED_CONTEXT: 0, STATUS_AMBIGUOUS: 0, STATUS_ABSENT: 0}
    by_kind: dict[str, dict[str, int]] = {}
    count = 0
    for result in results:
        count += 1
        totals[result.status] = totals.get(result.status, 0) + 1
        kind_bucket = by_kind.setdefault(
            result.target.kind, {STATUS_ANCHORED: 0, STATUS_ANCHORED_CONTEXT: 0, STATUS_AMBIGUOUS: 0, STATUS_ABSENT: 0}
        )
        kind_bucket[result.status] = kind_bucket.get(result.status, 0) + 1
    return {"total": count, **totals, "par_type": by_kind}


def preannotation_annotation_rows(
    results: Iterable[PreannotationResult],
    *,
    created_at: str,
    author_ref: str = SOURCE_ENGINE_PREANNOTATION,
    point_ref: str = "",
    action_ref: str = "",
    proof_ref: str = "",
    diffusion: str = "non_diffusable",
    confidentiality: str = "reserve_cs",
    include_ambiguous: bool = False,
    comment_prefix: str = "Pre-annotation moteur",
) -> list[dict[str, object]]:
    """Build candidate annotation rows; comments stay value-free by design."""

    rows: list[dict[str, object]] = []
    for result in results:
        if result.status == STATUS_ABSENT:
            continue
        if result.status == STATUS_AMBIGUOUS and not include_ambiguous:
            continue
        suffix = ""
        if result.status == STATUS_AMBIGUOUS:
            suffix = f"; {result.occurrences} occurrences a desambiguiser"
        elif result.status == STATUS_ANCHORED_CONTEXT:
            suffix = f"; desambiguise par contexte de ligne ({result.occurrences} occurrences)"
        comment = f"{comment_prefix}: champ {result.target.field} ({result.target.kind}){suffix}"
        row = candidate_to_annotation_row(
            result.candidates[0],
            comment=comment,
            author_ref=author_ref,
            created_at=created_at,
            point_ref=point_ref,
            action_ref=action_ref,
            proof_ref=proof_ref,
            diffusion=diffusion,
            confidentiality=confidentiality,
        )
        row["preannotation_field"] = result.target.field
        row["preannotation_kind"] = result.target.kind
        row["preannotation_status"] = result.status
        rows.append(row)
    return rows


def save_preannotation_traces(
    instance: InstanceConfig,
    results: Iterable[PreannotationResult],
    *,
    created_at: str = "",
    comment_prefix: str = "Pre-annotation moteur",
) -> dict[str, object]:
    """Append anchored candidates to registre_pdf_traces.csv (idempotent par anchor_hash).

    Seules les cibles `ancree` et `ancree_contexte` sont ecrites; les ambigues
    restent hors registre tant qu'un humain ou un contexte ne les a pas departagees.
    Les PDF sources ne sont jamais touches.
    """

    stamp = created_at or now_iso()
    existing = {row.get("anchor_hash", "") for row in read_trace_rows(instance)}
    new_rows: list[dict[str, str]] = []
    skipped_existing = 0
    skipped_status = 0
    for result in results:
        if result.status not in (STATUS_ANCHORED, STATUS_ANCHORED_CONTEXT):
            skipped_status += 1
            continue
        candidate = result.candidates[0]
        if candidate.anchor_hash in existing:
            skipped_existing += 1
            continue
        suffix = ""
        if result.status == STATUS_ANCHORED_CONTEXT:
            suffix = f"; desambiguise par contexte de ligne ({result.occurrences} occurrences)"
        comment = f"{comment_prefix}: champ {result.target.field} ({result.target.kind}){suffix}"
        annotation_row = candidate_to_annotation_row(
            candidate,
            comment=comment,
            author_ref=SOURCE_ENGINE_PREANNOTATION,
            created_at=stamp,
            point_ref=f"POINT-{candidate.document_ref}",
            action_ref=f"ACTION-{candidate.document_ref}",
            proof_ref=f"PROOF-{candidate.document_ref}",
        )
        zone = _resume_zone(annotation_row["zone"])
        new_rows.append(
            {
                "trace_id": str(annotation_row["annotation_id"]),
                "created_at": stamp,
                "document_ref": candidate.document_ref,
                "document_hash": candidate.document_hash,
                "page": str(annotation_row["page"]),
                "zone_x": f"{zone['x']:.6f}",
                "zone_y": f"{zone['y']:.6f}",
                "zone_width": f"{zone['width']:.6f}",
                "zone_height": f"{zone['height']:.6f}",
                "anchor_hash": candidate.anchor_hash,
                "fragment_ref": str(annotation_row["fragment_ref"]),
                "point_ref": str(annotation_row["point_ref"]),
                "action_ref": str(annotation_row["action_ref"]),
                "proof_ref": str(annotation_row["proof_ref"]),
                "proof_status": candidate.proof_status,
                "text_status": candidate.text_status,
                "selected_text_hash": public_selection_hash(candidate),
                "selected_text_excerpt": public_excerpt(candidate),
                "confidence": candidate.confidence,
                "document_hash_status": candidate.document_hash_status,
                "diffusion": str(annotation_row["diffusion"]),
                "confidentiality": str(annotation_row["confidentiality"]),
                "status": str(annotation_row["status"]),
                "comment": comment,
                "write_policy": NO_SOURCE_WRITE_NOTICE,
                "source_engine": SOURCE_ENGINE_PREANNOTATION,
            }
        )
        existing.add(candidate.anchor_hash)
    if new_rows:
        rows = read_trace_rows(instance)
        write_csv(trace_register_path(instance), PDF_TRACE_FIELDS, [*rows, *new_rows])
    return {
        "ecrites": len(new_rows),
        "deja_presentes": skipped_existing,
        "non_eligibles": skipped_status,
        "registre": trace_register_path(instance).name,
    }


def _resume_zone(zone: Mapping[str, object], *, minimum: float = MIN_ZONE_SIZE * 1.2) -> dict[str, float]:
    """Garantit une zone de reprise cliquable (>= MIN_ZONE_SIZE) sans toucher l'ancre exacte."""

    x = float(zone["x"])
    y = float(zone["y"])
    width = float(zone["width"])
    height = float(zone["height"])
    if width < minimum:
        x = max(0.0, min(x - (minimum - width) / 2, 1.0 - minimum))
        width = minimum
    if height < minimum:
        y = max(0.0, min(y - (minimum - height) / 2, 1.0 - minimum))
        height = minimum
    return {"x": x, "y": y, "width": width, "height": height}


def _context_tokens(before: str, after: str, *, limit: int = 6) -> tuple[str, ...]:
    def tokens(value: str) -> list[str]:
        return [
            token
            for token in _CONTEXT_TOKEN_RE.findall(value.lower())
            if token not in _CONTEXT_STOPWORDS
        ]

    selected = tokens(before)[-4:] + tokens(after)[:2]
    return tuple(dict.fromkeys(selected))[:limit]


def _line_words(text_map: PdfTextMap, candidate: PdfTraceCandidate) -> tuple[PdfTextRect, ...]:
    page = next((p for p in text_map.pages if p.page_index == candidate.page_index), None)
    if page is None or not candidate.rects:
        return tuple()
    first = candidate.rects[0]
    keys = {(word.block, word.line) for word in page.words}
    if len(keys) > 1:
        key = (first.block, first.line)
        same_line = tuple(word for word in page.words if (word.block, word.line) == key)
        if len(same_line) > len(candidate.rects):
            return same_line
    return tuple(
        word
        for word in page.words
        if word.y < first.y + first.height and word.y + word.height > first.y
    )


def _disambiguate_by_line(
    text_map: PdfTextMap,
    candidates: tuple[PdfTraceCandidate, ...],
    context: tuple[str, ...],
) -> PdfTraceCandidate | None:
    if not context:
        return None
    scored: list[tuple[int, PdfTraceCandidate]] = []
    for candidate in candidates:
        words = sorted(_line_words(text_map, candidate), key=lambda word: (word.x, word.word))
        line_text = " " + search_text(" ".join(word.text for word in words)) + " "
        score = sum(1 for token in context if f" {token} " in line_text)
        scored.append((score, candidate))
    best = max(score for score, _ in scored)
    if best <= 0:
        return None
    winners = [candidate for score, candidate in scored if score == best]
    return winners[0] if len(winners) == 1 else None


def _anchor_text_matches(selected_text: str, needle: str) -> bool:
    normalized = search_text(selected_text)
    if normalized == needle:
        return True
    return normalized.strip("€()[]{}*.,;: ").strip() == needle


def _target_key(value: str) -> str:
    key = search_text(value).replace(" ", "").replace(" ", "")
    for token in ("euros", "euro", "eur", "€"):
        key = key.replace(token, "")
    return key


def _merge_kind(
    max_per_kind: int,
    prefix: str,
    kind: str,
    primary: list[PreannotationTarget],
    secondary: list[PreannotationTarget],
) -> list[PreannotationTarget]:
    merged: list[PreannotationTarget] = []
    seen: set[str] = set()
    for target in [*primary, *secondary]:
        key = _target_key(target.value)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(
            PreannotationTarget(
                field=f"{prefix}_{len(merged) + 1}", kind=kind, value=target.value, context=target.context
            )
        )
        if len(merged) >= max_per_kind:
            break
    return merged


def _collect(
    pattern: re.Pattern[str],
    haystack: str,
    kind: str,
    prefix: str,
    max_per_kind: int,
    *,
    group: int = 0,
) -> list[PreannotationTarget]:
    targets: list[PreannotationTarget] = []
    seen: set[str] = set()
    for match in pattern.finditer(haystack):
        value = clean_text(match.group(group))
        key = _target_key(value)
        if not key or key in seen:
            continue
        seen.add(key)
        start, end = match.span(group)
        context = _context_tokens(haystack[max(0, start - 70):start], haystack[end:end + 40])
        targets.append(
            PreannotationTarget(field=f"{prefix}_{len(targets) + 1}", kind=kind, value=value, context=context)
        )
        if len(targets) >= max_per_kind:
            break
    return targets


def _group_thousands(digits: str, separator: str) -> str:
    if len(digits) <= 3:
        return digits
    chunks: list[str] = []
    remaining = digits
    while len(remaining) > 3:
        chunks.insert(0, remaining[-3:])
        remaining = remaining[:-3]
    chunks.insert(0, remaining)
    return separator.join(chunks)


__all__ = [
    "INVOICE_FIELD_KINDS",
    "KIND_AMOUNT",
    "KIND_DATE",
    "KIND_REFERENCE",
    "KIND_RESOLUTION",
    "KIND_TEXT",
    "PREANNOTATION_STATUSES",
    "PreannotationResult",
    "PreannotationTarget",
    "SOURCE_ENGINE_PREANNOTATION",
    "STATUS_ABSENT",
    "STATUS_AMBIGUOUS",
    "STATUS_ANCHORED",
    "STATUS_ANCHORED_CONTEXT",
    "amount_variants",
    "date_variants",
    "generic_targets_from_text",
    "preannotate",
    "preannotation_annotation_rows",
    "preannotation_summary",
    "reference_variants",
    "save_preannotation_traces",
    "targets_from_invoice_row",
    "variants_for",
]
