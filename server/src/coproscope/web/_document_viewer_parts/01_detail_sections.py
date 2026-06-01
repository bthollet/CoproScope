from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path

from ..core.common import InstanceConfig, read_csv
from ..modules import pdftrace_registry


MAX_TEXT_CHARS = 8000
MAX_INLINE_BYTES = 2 * 1024 * 1024
DOC_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json", ".yml", ".yaml", ".html", ".htm"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
PDF_SUFFIXES = {".pdf"}
BLOCKED_PATH_PARTS = {
    "raw",
    "brut",
    "bruts",
    "restricted",
    "restreint",
    "restreints",
    "private",
    "logs",
    "journaux",
    "secret",
    "secrets",
}


class DocumentNotFoundError(Exception):
    pass


def build_document_detail(instance: InstanceConfig, doc_id: str) -> dict[str, object]:
    if not _is_safe_doc_id(doc_id):
        raise DocumentNotFoundError(doc_id)

    row = _find_document_row(instance, doc_id)
    if row is None:
        raise DocumentNotFoundError(doc_id)
    row = _with_invoice_context(instance, row)
    preview = _build_preview(instance, row)
    storage = _storage_summary(instance, row)
    diffusion = _diffusion_status(row)
    signature = _signature_status(row)

    return {
        "doc": _public_document(row),
        "preview": preview,
        "workbench": _workbench(row, diffusion, signature, storage, preview),
        "evidence": _evidence(row),
        "diffusion": diffusion,
        "signature": signature,
        "pdf_trace": _pdf_trace(instance, row, preview),
        "anchors": _anchors(row),
        "annotations": _annotations(row),
        "history": _history(row),
        "metadata": _metadata(row),
        "policy": _policy(row),
        "workflow": _workflow(row),
        "storage": storage,
    }


def _is_safe_doc_id(doc_id: str) -> bool:
    value = (doc_id or "").strip()
    if not value or ".." in value or "/" in value or "\\" in value:
        return False
    return bool(DOC_ID_PATTERN.fullmatch(value))


def _find_document_row(instance: InstanceConfig, doc_id: str) -> dict[str, str] | None:
    try:
        documents_path = instance.register("documents")
    except KeyError:
        return None
    _, rows = read_csv(documents_path)
    for row in rows:
        if row.get("doc_id") == doc_id:
            return row
    return None


def _public_document(row: dict[str, str]) -> dict[str, str]:
    return {
        "doc_id": row.get("doc_id", ""),
        "file_name": _display_file_name(row),
        "extension": (row.get("extension") or "").lower(),
        "lot": row.get("lot", "") or "non renseigne",
        "document_type": row.get("document_type", "") or "Document",
        "suspected_date": row.get("suspected_date", ""),
        "source_zone": row.get("source_zone", "") or "locale",
        "source_kind": row.get("source_kind", ""),
        "size_bytes": row.get("size_bytes", ""),
        "sha256": row.get("sha256", ""),
        "page_count": row.get("page_count", ""),
    }


def _display_file_name(row: dict[str, str]) -> str:
    if _guard_private_inbox(row):
        return row.get("doc_id", "") or f"Document {_short_hash(row.get('sha256', ''))}"
    value = row.get("file_name") or row.get("filename") or row.get("doc_id", "") or "Document"
    normalized = value.strip().replace("\\", "/")
    if not normalized:
        return row.get("doc_id", "") or "Document"
    basename = next((part for part in reversed(normalized.split("/")) if part), "")
    if basename in {"", ".", ".."}:
        return row.get("doc_id", "") or "Document"
    return basename


def _metadata(row: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"label": "Type", "value": row.get("document_type", "") or "Document"},
        {"label": "Lot", "value": row.get("lot", "") or "non renseigne"},
        {"label": "Date detectee", "value": row.get("suspected_date", "") or "non renseignee"},
        {"label": "Extension", "value": (row.get("extension", "") or "n/a").lower()},
        {"label": "Taille", "value": _format_size(row.get("size_bytes", ""))},
        {"label": "Empreinte", "value": row.get("sha256", "") or "absente"},
    ]


def _policy(row: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"label": "Confidentialite brute", "value": row.get("raw_max_college", "") or "non qualifiee"},
        {"label": "Confidentialite derivee", "value": row.get("derivative_max_college", "") or "non qualifiee"},
        {"label": "Forme publication", "value": row.get("publication_form", "") or "non arbitree"},
        {"label": "Revue", "value": row.get("privacy_review_status", "") or row.get("review_required", "") or "non requise"},
        {"label": "Biffage", "value": row.get("redaction_status", "") or "non lance"},
        {"label": "Traitement IA", "value": row.get("ai_processing_ceiling", "") or "local_only"},
    ]


def _workflow(row: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"label": "OCR", "value": row.get("status_ocr", "") or "non lance"},
        {"label": "Classement", "value": row.get("classification_status", "") or "non classe"},
        {"label": "Pages", "value": row.get("page_count", "") or "n/a"},
        {"label": "Texte extrait", "value": _format_chars(row.get("text_char_count", ""))},
        {"label": "Qualite texte", "value": row.get("text_quality", "") or "non mesuree"},
        {"label": "Moteur OCR", "value": row.get("ocr_engine", "") or "natif / inconnu"},
    ]


def _pdf_trace(instance: InstanceConfig, row: dict[str, str], preview: dict[str, object]) -> dict[str, object]:
    is_pdf = (row.get("extension") or "").lower().lstrip(".") == "pdf" or preview.get("kind") == "pdf"
    has_pdf_viewer = preview.get("kind") == "pdf"
    page_count = _positive_int(row.get("page_count", ""))
    page_count_known = page_count > 0
    effective_page_count = page_count if page_count_known else 1
    page_nav_available = bool(is_pdf and has_pdf_viewer and effective_page_count > 1)
    saved_traces = pdftrace_registry.public_trace_summaries(instance, row.get("doc_id", "")) if is_pdf else []
    return {
        "available": is_pdf,
        "has_pdf_viewer": has_pdf_viewer,
        "page_nav_available": page_nav_available,
        "page_count": str(effective_page_count),
        "page_count_label": f"sur {effective_page_count}" if page_count_known else "nombre total de pages non connu",
        "current_page": "1",
        "workshop_label": "Atelier de trace PDF" if is_pdf else "Atelier de preuve",
        "reader_label": "Lecteur PDF" if has_pdf_viewer else "Apercu PDF textuel" if is_pdf else "Apercu autorise",
        "page_label": f"Page 1 sur {effective_page_count}" if page_nav_available else "Page 1" if has_pdf_viewer else "Texte extrait" if is_pdf else "Document",
        "thumbnail_label": "Miniatures des pages" if page_nav_available else "Miniature page 1" if has_pdf_viewer else "Texte extrait" if is_pdf else "Apercu",
        "title": "Tracer une preuve candidate" if is_pdf else "Preparer une preuve",
        "primary_action": "Enregistrer comme trace a verifier" if is_pdf else "Selection PDF indisponible",
        "status": "Preuve candidate a verifier",
        "limitation_notice": (
            "Dessinez une zone sur la page avant d'enregistrer comme trace candidate."
            if is_pdf
            else "La selection de zone est reservee aux PDF."
        ),
        "intro": (
            "Encadrez le passage utile. CoproScope gardera le lien, sans changer le PDF."
            if is_pdf
            else "Cette fiche garde les memes garde-fous, sans promettre une selection dans un PDF."
        ),
        "source_notice": "Le PDF original n'est pas modifie." if is_pdf else "La source originale n'est pas modifiee.",
        "selection_prompt": "Choisissez la page, puis encadrez la zone" if page_nav_available else "Dessinez une zone sur la page",
        "selection_empty_label": "Zone a selectionner sur la page {page}" if page_nav_available else "Zone a selectionner",
        "selection_ready_label": "Zone ajustable sur la page {page}",
        "selection_adjust_help": "Tirer les poignees pour ajuster.",
        "validation_notice": (
            "CoproScope garde un repere dans le PDF, mais ne valide pas la preuve."
            if is_pdf
            else "CoproScope prepare un repere de preuve, mais ne valide pas la preuve."
        ),
        "text_status": "Texte reconnu automatiquement : relisez avant de vous en servir.",
        "scan_status": "Texte non confirme : seule la zone encadree est gardee.",
        "hash_status": "Le fichier a change depuis la trace. Verifiez avant usage.",
        "diffusion_status": "Non diffusable par defaut",
        "availability_note": (
            "Trace privee a l'instance tant qu'elle n'est pas validee."
            if is_pdf
            else "Atelier prepare pour les PDF; cette fiche rappelle les garde-fous."
        ),
        "candidate_form": {
            "page": "1",
            "zone_x": "",
            "zone_y": "",
            "zone_width": "",
            "zone_height": "",
            "comment": "Trace candidate depuis l'atelier document.",
        },
        "saved_traces": saved_traces,
        "saved_count": str(len(saved_traces)),
        "sample": {
            "page": "page 1",
            "zone": "Zone encadree page 1",
            "proof": "preuve candidate",
        },
    }


def _workbench(
    row: dict[str, str],
    diffusion: dict[str, str],
    signature: dict[str, str],
    storage: dict[str, str],
    preview: dict[str, object],
) -> dict[str, object]:
    return {
        "title": "Parcours novice: piece -> point -> action -> preuve",
        "notice": "Lire la piece, choisir le point a traiter, lancer la bonne action, puis garder une preuve verifiable.",
        "steps": [
            {
                "label": "1. Piece",
                "title": _display_file_name(row),
                "status": row.get("document_type", "") or "Document a qualifier",
                "text": "Identifier ce que contient la piece sans modifier le fichier source.",
            },
            {
                "label": "2. Point",
                "title": _role_label(row),
                "status": row.get("classification_status", "") or "point a classer",
                "text": "Relier la piece a un lot, une date, un sujet de conseil syndical ou une demande.",
            },
            {
                "label": "3. Action",
                "title": diffusion["action"],
                "status": diffusion["label"],
                "text": diffusion["detail"],
            },
            {
                "label": "4. Preuve",
                "title": _proof_title(row, preview),
                "status": storage["status"],
                "text": "Utiliser l'empreinte et le journal separe; ne pas annoter ni remplacer le PDF source.",
            },
        ],
        "primary_action": diffusion["action"],
        "secondary_action": signature["action"],
    }


def _evidence(row: dict[str, str]) -> dict[str, object]:
    sha256 = row.get("sha256", "")
    redacted_sha256 = row.get("redacted_sha256", "")
    return {
        "status": "piece probatoire",
        "notice": "La source reste intacte. La fiche montre seulement des statuts, des extraits autorises et des evenements separes.",
        "chain": [
            {"label": "Identifiant stable", "value": row.get("doc_id", "") or "absent"},
            {"label": "Role dossier", "value": _role_label(row)},
            {"label": "Empreinte source", "value": _short_hash(sha256) if sha256 else "absente"},
            {
                "label": "Version publiable",
                "value": _short_hash(redacted_sha256) if redacted_sha256 else "non produite",
            },
            {"label": "Mode annotation", "value": "journal separe du fichier"},
        ],
    }


def _diffusion_status(row: dict[str, str]) -> dict[str, str]:
    publication_form = (row.get("publication_form") or "").strip()
    review_status = (row.get("privacy_review_status") or row.get("review_required") or "").strip()
    transformations = (row.get("required_transformations") or "").lower()
    review_required = (row.get("review_required") or "").strip().lower() in {"1", "yes", "true", "oui", "a_revoir"}

    if review_status == "BLOQUE":
        return {
            "label": "Diffusion bloquee",
            "state": "blocked",
            "action": "Ne pas partager cette piece",
            "detail": row.get("publication_blocker", "") or "Un arbitrage confidentialite bloque la sortie de cette piece.",
            "next_step": "Passer par la revue confidentialite avant tout export ou envoi.",
        }
    if review_status in {"A_ARBITRER", "A_REVOIR", "REVIEW_PENDING", "YES", "true", "True"} or review_required:
        return {
            "label": "Diffusion a arbitrer",
            "state": "review",
            "action": "Faire valider la diffusion",
            "detail": "Un humain doit confirmer ce qui peut sortir du dossier local.",
            "next_step": row.get("review_next_step", "") or "Verifier le niveau de partage et noter la decision.",
        }
    if publication_form in {"redaction_required", "pseudonymization_or_redaction_required"} or "redaction" in transformations:
        return {
            "label": "Biffage requis",
            "state": "redaction",
            "action": "Preparer une version biffee",
            "detail": "La piece peut servir de preuve locale, mais la diffusion doit passer par une version derivee.",
            "next_step": "Verifier ou produire la version biffee avant partage.",
        }
    if publication_form == "aggregation_required" or "aggregation" in transformations:
        return {
            "label": "Synthese seulement",
            "state": "limited",
            "action": "Partager une synthese",
            "detail": "La piece detaillee reste locale; seule une information agregee doit sortir.",
            "next_step": "Rattacher la piece, puis utiliser une synthese comme preuve diffusable.",
        }
    if publication_form == "metadata_only":
        return {
            "label": "Metadonnees seulement",
            "state": "limited",
            "action": "Partager uniquement la reference",
            "detail": "Le contenu ne doit pas sortir; garder seulement le titre, la date, le type et l'empreinte.",
            "next_step": "Eviter tout extrait de contenu dans les exports larges.",
        }
    if publication_form == "raw" or review_status in {"AUTO_POLICY", "DIFFUSABLE_BRUT", "DEMO_FICTIVE"}:
        return {
            "label": "Diffusion directe possible",
            "state": "open",
            "action": "Rattacher la piece a l'action",
            "detail": "La politique connue ne signale pas de transformation obligatoire.",
            "next_step": "Garder l'empreinte et le lien de contexte avec l'action.",
        }
    return {
        "label": "Diffusion a verifier",
        "state": "unknown",
        "action": "Verifier avant partage",
        "detail": "Le statut de diffusion n'est pas assez clair pour un utilisateur novice.",
        "next_step": "Consulter la confidentialite ou demander un arbitrage.",
    }


def _signature_status(row: dict[str, str]) -> dict[str, str]:
    status = (
        row.get("signature_status")
        or row.get("event_signature_status")
        or row.get("vault_signature_status")
        or ""
    ).strip()
    signer = row.get("signed_by") or row.get("signature_owner") or row.get("privacy_review_owner") or ""
    signed_at = row.get("signed_at") or row.get("signature_time") or row.get("privacy_reviewed_at") or ""

    normalized = status.lower()
    if normalized in {"valid", "valide", "verified", "verifiee", "verifie"}:
        return {
            "label": "Signature verifiee",
            "state": "valid",
            "actor": signer or "signataire connu",
            "when": signed_at or "date non renseignee",
            "action": "Conserver le journal signe",
            "detail": "Un evenement signe est declare pour cette fiche.",
        }
    if normalized in {"invalid", "invalide", "invalid_signature"}:
        return {
            "label": "Signature invalide",
            "state": "invalid",
            "actor": signer or "signataire a verifier",
            "when": signed_at or "date non renseignee",
            "action": "Bloquer la preuve signee",
            "detail": "La signature annoncee doit etre corrigee avant de s'appuyer dessus.",
        }
    if status:
        return {
            "label": "Signature a verifier",
            "state": "review",
            "actor": signer or "signataire non renseigne",
            "when": signed_at or "date non renseignee",
            "action": "Verifier la signature",
            "detail": f"Statut declare: {status}.",
        }
    return {
        "label": "Signature a venir",
        "state": "future",
        "actor": "signataire a designer",
        "when": "aucun evenement signe",
        "action": "Preparer un evenement signe",
        "detail": "V1 affiche le futur journal collaboratif; la fiche actuelle ne signe pas encore l'annotation.",
    }


def _anchors(row: dict[str, str]) -> dict[str, object]:
    items: list[dict[str, str]] = []
    pages = _positive_int(row.get("page_count", ""))
    if pages:
        for page in range(1, min(pages, 3) + 1):
            items.append(
                {
                    "label": f"Ancre P{page}",
                    "target": f"page {page}",
                    "status": "ancre logique disponible",
                }
            )
    if _positive_int(row.get("text_char_count", "")):
        items.append(
            {
                "label": "Ancre texte",
                "target": "texte extrait",
                "status": "rattachement par extrait possible",
            }
        )
    if not items:
        items.append(
            {
                "label": "Ancre document",
                "target": "piece entiere",
                "status": "placeholder a qualifier",
            }
        )
    return {
        "status": "ancres sans ecriture PDF",
        "notice": "Les ancres servent a rattacher une note ou un visa a la piece; elles ne modifient pas le PDF source.",
        "entries": items,
    }


def _annotations(row: dict[str, str]) -> dict[str, object]:
    privacy_status = row.get("privacy_review_status", "") or row.get("review_required", "") or "a qualifier"
    redaction_status = row.get("redaction_status", "") or "non lance"
    return {
        "mode": "evenements futurs separes",
        "notice": "Les annotations collaboratives sont preparees comme des evenements futurs: elles viseront une ancre; aucune annotation n'est injectee dans le PDF.",
        "events": [
            {
                "label": "Annotation signee",
                "status": "a venir",
                "actor": "signataire a designer",
                "anchor": "ancre a choisir",
                "action": "Ecrire la note, puis signer l'evenement",
                "proof": "journal separe du document source",
                "note": "Evenement probatoire futur, separe du document source.",
            },
            {
                "label": "Point rattache",
                "status": row.get("classification_status", "") or "a classer",
                "actor": "conseil syndical",
                "anchor": "piece ou page",
                "action": "Relier la piece au sujet traite",
                "proof": "doc_id stable",
                "note": "Transforme une lecture en point de travail.",
            },
            {
                "label": "Visa diffusion",
                "status": privacy_status,
                "actor": "revue locale",
                "anchor": "piece entiere",
                "action": "Autoriser, limiter ou bloquer le partage",
                "proof": "decision de confidentialite",
                "note": "Controle avant partage ou publication.",
            },
            {
                "label": "Controle biffage",
                "status": redaction_status,
                "actor": "operateur local",
                "anchor": "version derivee",
                "action": "Verifier que la version diffusable existe",
                "proof": "empreinte derivee si produite",
                "note": "Suit une version biffee sans remplacer la source.",
            },
        ],
    }


def _history(row: dict[str, str]) -> dict[str, object]:
    events = [
        {
            "label": "Document inventorie",
            "when": row.get("first_seen", "") or "date inconnue",
            "status": "source locale masquee" if _guard_private_inbox(row) else row.get("source_zone", "") or "source locale",
        },
        {
            "label": "Extraction texte",
            "when": row.get("suspected_date", "") or "date document inconnue",
            "status": row.get("status_ocr", "") or "non lance",
        },
        {
            "label": "Classement",
            "when": row.get("suspected_date", "") or "date document inconnue",
            "status": row.get("classification_status", "") or "non classe",
        },
        {
            "label": "Revue confidentialite",
            "when": row.get("privacy_reviewed_at", "") or "a planifier",
            "status": row.get("publication_form", "") or "non arbitree",
            "signature": row.get("privacy_review_owner", "") or "signature a venir",
        },
    ]
    for event in events:
        event.setdefault("signature", "registre local")
    if row.get("redaction_status") or row.get("redacted_sha256"):
        events.append(
            {
                "label": "Version biffee",
                "when": row.get("redaction_status", "") or "produite",
                "status": _short_hash(row.get("redacted_sha256", "")) if row.get("redacted_sha256") else "empreinte absente",
                "signature": "journal a verifier",
            }
        )
    return {
        "status": "historique fiche",
        "notice": "Historique visible pour comprendre ce qui est acquis, ce qui reste a signer et ce qui ne modifie jamais la source.",
        "events": events,
    }


def _role_label(row: dict[str, str]) -> str:
    document_type = row.get("document_type", "") or "Document"
    lot = row.get("lot", "") or "lot non renseigne"
    suspected_date = row.get("suspected_date", "")
    if suspected_date:
        return f"{document_type} / {lot} / {suspected_date}"
    return f"{document_type} / {lot}"


def _short_hash(value: str) -> str:
    cleaned = (value or "").strip()
    if len(cleaned) <= 16:
        return cleaned or "absente"
    return f"{cleaned[:12]}...{cleaned[-8:]}"


def _proof_title(row: dict[str, str], preview: dict[str, object]) -> str:
    if row.get("sha256"):
        return f"Empreinte {_short_hash(row.get('sha256', ''))}"
    if preview.get("kind") in {"text", "image", "pdf"}:
        return "Apercu derive disponible"
    return "Preuve a consolider"


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def _build_preview(instance: InstanceConfig, row: dict[str, str]) -> dict[str, object]:
    original_ext = "." + (row.get("extension") or "").lower().lstrip(".")

    redacted = _safe_existing_path(instance, row.get("redacted_path", ""))
    if redacted is not None:
        preview = _preview_from_path(redacted, "version biffee", fallback=False)
        if preview is not None:
            return preview
    if _guard_private_inbox(row):
        return _unavailable_preview()

    extracted_text = _safe_existing_path(instance, row.get("text_path", ""))
    if extracted_text is not None:
        preview = _text_preview(
            extracted_text,
            "texte extrait",
            fallback=original_ext in PDF_SUFFIXES or original_ext in IMAGE_SUFFIXES,
        )
        if preview is not None:
            return preview

    original = _safe_existing_path(instance, row.get("original_path", ""))
    if original is not None:
        preview = _preview_from_path(original, "document local hors zone brute", fallback=False)
        if preview is not None:
            return preview

    return _unavailable_preview()
def _guard_private_inbox(row: dict[str, str]) -> bool:
    source_zone = str(row.get("source_zone") or "").upper()
    privacy = row.get("privacy_review_status") or row.get("review_required")
    publication = row.get("publication_form") or ""
    ocr_review = (row.get("status_ocr") or "").upper() in {"PENDING", "OCR_REQUIRED", "EXTRACTION_ERROR", "SOURCE_MISSING", "UNSUPPORTED"}
    local_review = ocr_review or "A_CLASSER" in {(row.get("document_type") or "").upper(), (row.get("classification_status") or "").upper()}
    if source_zone == "200_INBOX":
        return local_review or privacy not in {"AUTO_POLICY", "DIFFUSABLE_BRUT", "DEMO_FICTIVE"} or publication != "raw"
    return source_zone == "RAW" and (local_review or privacy not in {"", "AUTO_POLICY", "DIFFUSABLE_BRUT", "DEMO_FICTIVE"} or publication not in {"", "raw"})
def _unavailable_preview() -> dict[str, object]:
    return {
        "kind": "unavailable",
        "kind_label": "apercu indisponible",
        "source_label": "",
        "message": "Aucun apercu exploitable hors zones brutes ou restreintes n'est disponible pour cette fiche.",
        "text": "",
        "truncated": False,
        "fallback": False,
    }
def _preview_from_path(path: Path, source_label: str, *, fallback: bool) -> dict[str, object] | None:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return _text_preview(path, source_label, fallback=fallback)
    if suffix in IMAGE_SUFFIXES:
        return _binary_preview(path, "image", source_label)
    if suffix in PDF_SUFFIXES:
        return _binary_preview(path, "pdf", source_label)
    return None
