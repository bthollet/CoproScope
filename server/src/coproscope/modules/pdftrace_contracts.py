from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .annotationops import contains_private_path


SCHEMA_VERSION = "coproscope.pdf_trace.v1"
SOURCE_ENGINE_PYMUPDF = "pymupdf_text_map"
SOURCE_ENGINE_MANUAL = "manual_pdf_pointer"
ZOTERO_POSITION_KIND = "zotero_pdf_position_compatible"
NO_SOURCE_WRITE_NOTICE = "source_pdf_is_never_modified"
TEXT_STATUS_RECOGNIZED = "texte_reconnu"
TEXT_STATUS_CONFIRMED = TEXT_STATUS_RECOGNIZED
TEXT_STATUS_UNCONFIRMED = "non_confirme"
TEXT_STATUS_REVIEW_REQUIRED = "a_verifier"
PROOF_STATUS_CANDIDATE = "preuve_candidate"
DOCUMENT_HASH_MATCH = "hash_conforme"
DOCUMENT_HASH_MISMATCH = "hash_a_verifier"
DOCUMENT_HASH_NOT_CHECKED = "hash_non_verifie"
PUBLIC_TEXT_EXCERPT_MASK = "Texte repere: extrait masque par defaut."

_HASH_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$", re.IGNORECASE)
_DOC_REF_RE = re.compile(r"^[A-Za-z0-9_.:#-]+$")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .-]{7,}\d)(?!\d)")
_SENSITIVE_MARKER_RE = re.compile(
    r"(^|[\s&?;.:#/\\_-])(?:token|secret|client_secret|password|passwd|api[_-]?key|oauth|raw|restricted|private)(=|:|[\s/\\._:-]|$)",
    re.IGNORECASE,
)
_SPACE_RE = re.compile(r"\s+")


def validate_document_identity(document_ref: str, document_hash: str) -> None:
    if not document_ref or not _DOC_REF_RE.match(document_ref) or contains_sensitive_text(document_ref):
        raise ValueError("document_ref logique requis, sans chemin local ni marqueur sensible")
    if not _HASH_RE.match(str(document_hash or "")):
        raise ValueError("document_hash sha256 requis")


def normalize_hash(value: str) -> str:
    text = str(value or "").strip().lower()
    if text.startswith("sha256:"):
        text = text[7:]
    return f"sha256:{text}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def document_hash_status(expected_hash: str, source_hash: str) -> str:
    if not source_hash:
        return DOCUMENT_HASH_NOT_CHECKED
    return DOCUMENT_HASH_MATCH if normalize_hash(expected_hash) == source_hash else DOCUMENT_HASH_MISMATCH


def hash_text(value: str) -> str:
    normalized = _SPACE_RE.sub(" ", value.strip()).lower()
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def public_excerpt(candidate: Any) -> str:
    if candidate.document_hash_status == DOCUMENT_HASH_MISMATCH:
        return "Le fichier a change depuis la trace. Verifiez avant usage."
    if candidate.private_excerpt_blocked:
        return "[extrait masque: contenu local ou sensible]"
    if not candidate.selected_text.strip() or candidate.text_status != TEXT_STATUS_CONFIRMED:
        return "Texte non confirme: seule la zone encadree est gardee."
    return PUBLIC_TEXT_EXCERPT_MASK


def public_selection_hash(candidate: Any) -> str:
    return candidate.anchor_hash if candidate.private_excerpt_blocked else candidate.selected_text_hash


def text_status_from_map(text_map: Any) -> str:
    if text_map.document_hash_status == DOCUMENT_HASH_MISMATCH:
        return TEXT_STATUS_REVIEW_REQUIRED
    return TEXT_STATUS_RECOGNIZED


def text_status_label(candidate: Any) -> str:
    if candidate.document_hash_status == DOCUMENT_HASH_MISMATCH:
        return "Le fichier a change depuis la trace. Verifiez avant usage."
    if candidate.text_status == TEXT_STATUS_UNCONFIRMED:
        return "Texte non confirme: seule la zone encadree est gardee."
    return "Texte reconnu automatiquement: relisez avant de vous en servir."


def user_notice(candidate: Any) -> dict[str, str]:
    return {
        "proof": "Preuve candidate a verifier",
        "verification": "CoproScope garde un repere dans le PDF, mais ne valide pas la preuve.",
        "source": "Le PDF original n'est pas modifie.",
        "text": text_status_label(candidate),
    }


def contains_sensitive_text(value: str) -> bool:
    text = _SPACE_RE.sub(" ", str(value or "").strip())
    if not text:
        return False
    if contains_private_path(text) or _EMAIL_RE.search(text):
        return True
    if any(_looks_like_phone(match.group(0)) for match in _PHONE_RE.finditer(text)):
        return True
    return bool(_SENSITIVE_MARKER_RE.search(text))


def search_text(value: str) -> str:
    return _SPACE_RE.sub(" ", str(value or "").strip()).lower()


def clean_text(value: str) -> str:
    return _SPACE_RE.sub(" ", value.strip())


def _looks_like_phone(value: str) -> bool:
    return len(re.sub(r"\D", "", value)) >= 9
