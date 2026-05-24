from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict
from typing import Any, Iterable, Mapping

from ..modules import document_intake


STATUS_LABELS = {
    document_intake.RUNTIME_READY: "pret a enregistrer",
    document_intake.RUNTIME_NEEDS_INPUT: "a completer",
    document_intake.RUNTIME_BLOCKED: "bloque",
}

STATUS_TONES = {
    document_intake.RUNTIME_READY: "ok",
    document_intake.RUNTIME_NEEDS_INPUT: "p2",
    document_intake.RUNTIME_BLOCKED: "p1",
}

CHECK_LABELS = {
    document_intake.CHECK_OK: "fait",
    document_intake.CHECK_TODO: "a faire",
    document_intake.CHECK_BLOCKED: "bloque",
    document_intake.CHECK_FUTURE: "futur",
}

PRIVACY_LABELS = {
    document_intake.PRIVACY_RAW: "diffusion brute autorisee",
    document_intake.PRIVACY_REDACT: "version biffee requise",
    document_intake.PRIVACY_CS_ONLY: "reserve conseil syndical",
    document_intake.PRIVACY_BLOCKED: "bloque",
    document_intake.PRIVACY_ARBITRATE: "a arbitrer",
}

CLASSIFICATION_LABELS = {
    document_intake.CLASSIFICATION_PENDING: "a proposer",
    document_intake.CLASSIFICATION_PROPOSED: "propose",
    document_intake.CLASSIFICATION_ACCEPTED: "accepte",
    document_intake.CLASSIFICATION_UNSURE: "a classer",
}

WARNING_LABELS = {
    "raw_cloud_interdit": "Aucun brut ne doit partir vers un cloud.",
    "chemin_local_ou_absolu_masque": "Un chemin prive a ete masque avant affichage.",
    "version_biffee_a_nommer": "Nommer la version biffee attendue avant diffusion.",
}

PRIVATE_HINT_RE = re.compile(
    r"([A-Za-z]:[\\/]|^/|^\\\\|https?://|@|\\|/|users?|utilisateurs?)",
    flags=re.IGNORECASE,
)


def build_document_intake_view(
    rows: Iterable[Mapping[str, Any] | document_intake.DocumentIntakeInput] | None = None,
    *,
    title: str = "Ajout de document",
    intro: str = (
        "Un parcours local pour deposer une piece, verifier sa confidentialite, "
        "puis la rattacher a un point, une action et une preuve."
    ),
) -> dict[str, Any]:
    """Prepare document-intake rows for a route-free Jinja template."""
    cards = [_card(row, index) for index, row in enumerate(rows or (), start=1)]
    status_counts = Counter(card["status"] for card in cards)
    todo_cards = [card for card in cards if card["status"] == document_intake.RUNTIME_NEEDS_INPUT]
    blocked_cards = [card for card in cards if card["status"] == document_intake.RUNTIME_BLOCKED]
    ready_cards = [card for card in cards if card["status"] == document_intake.RUNTIME_READY]
    warning_cards = [card for card in cards if card["warning_labels"]]

    return {
        "title": title,
        "intro": intro,
        "summary": {
            "total": len(cards),
            "ready": len(ready_cards),
            "todo": len(todo_cards),
            "blocked": len(blocked_cards),
            "warnings": len(warning_cards),
        },
        "has_cards": bool(cards),
        "cards": cards,
        "ready_cards": ready_cards,
        "todo_cards": todo_cards,
        "blocked_cards": blocked_cards,
        "status_counts": _status_counts(status_counts),
        "novice_steps": _novice_steps(),
        "privacy_controls": _privacy_controls(),
        "attachment_contract": _attachment_contract(),
        "future_events": list(document_intake.FUTURE_EVENT_TYPES),
        "integration": {
            "route_ready": True,
            "route_name": "document_intake",
            "template": "document_intake.html",
            "view_helper": "build_document_intake_view",
            "app_boundary": "Le depot local recoit les fichiers; cette page guide le rattachement et la confidentialite.",
        },
        "empty_state": {
            "title": "Le parcours d'ajout est pret a brancher",
            "body": (
                "Branchez les lignes issues du depot local ou d'un formulaire. "
                "Chaque ligne doit rester sans chemin prive et sans nom reel."
            ),
            "first_step": "Commencer par une reference opaque, une empreinte locale et un statut de confidentialite.",
            "next_step": "Ajouter ensuite le rattachement piece -> point -> action -> preuve.",
        },
    }


def template_context(
    rows: Iterable[Mapping[str, Any] | document_intake.DocumentIntakeInput] | None = None,
) -> dict[str, Any]:
    return {"document_intake": build_document_intake_view(rows)}


def _card(row: Mapping[str, Any] | document_intake.DocumentIntakeInput, index: int) -> dict[str, Any]:
    intake = document_intake.normalize_document_intake(row) if isinstance(row, Mapping) else row
    runtime = document_intake.build_runtime_checklist(intake)
    doc_label = _safe_text(intake.display_name) or _safe_text(intake.doc_id) or f"Document {index}"
    if doc_label == "information masquee":
        doc_label = f"Document {index}"
    doc_id = _safe_identifier(intake.doc_id) or f"DOC-A-NOMMER-{index:03d}"
    classification = intake.classification
    privacy = intake.privacy
    return {
        "index": index,
        "doc_id": doc_id,
        "document_label": doc_label,
        "source_label": "depot local" if intake.source_kind == "depot_local" else "source a revoir",
        "local_reference": _safe_reference(intake.local_reference) or "reference opaque a creer",
        "format_label": _safe_text(intake.file_format) or "format a detecter",
        "size_label": _safe_size(intake.size_bytes),
        "hash_label": _short_hash(intake.content_hash),
        "duplicate_label": _safe_identifier(intake.duplicate_of),
        "status": runtime.status,
        "status_label": STATUS_LABELS.get(runtime.status, runtime.status),
        "status_tone": STATUS_TONES.get(runtime.status, "p2"),
        "next_action": runtime.next_action,
        "checklist": [_check_item(item) for item in runtime.checklist],
        "warning_labels": [WARNING_LABELS.get(warning, warning) for warning in runtime.warnings],
        "classification": {
            "status": classification.status,
            "status_label": CLASSIFICATION_LABELS.get(classification.status, classification.status),
            "document_type": _safe_text(classification.document_type) or "type a proposer",
            "domain": _safe_text(classification.domain) or "domaine a choisir",
            "period": _safe_text(classification.period) or "periode a choisir",
            "lot": _safe_text(classification.lot) or "lot a choisir",
            "confidence": _safe_text(classification.confidence) or "confiance a estimer",
            "reason": _safe_text(classification.reason) or "raison courte a noter",
        },
        "privacy": {
            "status": privacy.status,
            "status_label": PRIVACY_LABELS.get(privacy.status, privacy.status),
            "rationale": _safe_text(privacy.rationale) or "arbitrage a documenter",
            "required_derivative": _safe_reference(privacy.required_derivative) or "version derivee a nommer si besoin",
        },
        "attachments": [_attachment(attachment, doc_id, item_index) for item_index, attachment in enumerate(intake.attachments, start=1)],
        "has_attachments": bool(intake.attachments),
        "privacy_guard": _privacy_guard(privacy.status),
        "drop_guidance": _drop_guidance(intake),
    }


def _check_item(item: document_intake.ChecklistItem) -> dict[str, Any]:
    return {
        **asdict(item),
        "status_label": CHECK_LABELS.get(item.status, item.status),
        "tone": "p1" if item.status == document_intake.CHECK_BLOCKED else "p2" if item.status == document_intake.CHECK_TODO else "ok",
    }


def _attachment(attachment: document_intake.AttachmentDraft, doc_id: str, index: int) -> dict[str, str]:
    piece = _safe_text(attachment.piece_label) or doc_id or f"piece {index}"
    point = _safe_text(attachment.point_label) or _safe_identifier(attachment.point_id) or "point a choisir"
    action = _safe_text(attachment.action_label) or "action a formuler"
    proof = _safe_text(attachment.proof_label) or "preuve attendue a nommer"
    return {
        "piece": piece,
        "point": point,
        "point_id": _safe_identifier(attachment.point_id),
        "point_kind": _safe_text(attachment.point_kind) or "preuve_libre",
        "action_kind": _safe_text(attachment.action_kind) or "verifier",
        "action": action,
        "proof_intent": _safe_text(attachment.proof_intent) or "presence",
        "proof": proof,
        "chain_label": f"{piece} -> {point} -> {action} -> {proof}",
    }


def _status_counts(counts: Counter[str]) -> list[dict[str, Any]]:
    order = (
        document_intake.RUNTIME_READY,
        document_intake.RUNTIME_NEEDS_INPUT,
        document_intake.RUNTIME_BLOCKED,
    )
    return [
        {
            "key": status,
            "label": STATUS_LABELS.get(status, status),
            "count": counts.get(status, 0),
            "tone": STATUS_TONES.get(status, "p2"),
        }
        for status in order
        if counts.get(status, 0)
    ]


def _novice_steps() -> list[dict[str, str]]:
    return [
        {
            "title": "1. Deposer localement",
            "body": "Le fichier brut reste dans l'instance locale; l'ecran affiche seulement une reference opaque et une empreinte.",
        },
        {
            "title": "2. Classer sans certitude forcee",
            "body": "Si le type est flou, garder A_CLASSER et demander une verification humaine.",
        },
        {
            "title": "3. Controler la confidentialite",
            "body": "Choisir diffusion brute, version biffee, reserve conseil syndical, blocage ou arbitrage.",
        },
        {
            "title": "4. Relier la preuve",
            "body": "Chaque piece doit suivre la chaine piece -> point -> action -> preuve.",
        },
    ]


def _privacy_controls() -> list[dict[str, str]]:
    return [
        {
            "status": document_intake.PRIVACY_RAW,
            "label": PRIVACY_LABELS[document_intake.PRIVACY_RAW],
            "help": "La piece peut sortir dans le contexte choisi, avec son doc_id et son empreinte.",
        },
        {
            "status": document_intake.PRIVACY_REDACT,
            "label": PRIVACY_LABELS[document_intake.PRIVACY_REDACT],
            "help": "Le brut reste local; une version derivee biffee doit porter la diffusion.",
        },
        {
            "status": document_intake.PRIVACY_CS_ONLY,
            "label": PRIVACY_LABELS[document_intake.PRIVACY_CS_ONLY],
            "help": "Lecture limitee au conseil syndical tant que le partage n'est pas elargi.",
        },
        {
            "status": document_intake.PRIVACY_BLOCKED,
            "label": PRIVACY_LABELS[document_intake.PRIVACY_BLOCKED],
            "help": "Aucun export ni partage; l'arbitrage doit passer avant le rattachement diffusable.",
        },
        {
            "status": document_intake.PRIVACY_ARBITRATE,
            "label": PRIVACY_LABELS[document_intake.PRIVACY_ARBITRATE],
            "help": "Statut volontairement visible: il manque une decision de confidentialite.",
        },
    ]


def _attachment_contract() -> list[dict[str, str]]:
    return [
        {"label": "Piece", "value": "document reference sans chemin prive"},
        {"label": "Point", "value": "AG, decision, demande, facture, incident, chantier ou preuve libre"},
        {"label": "Action", "value": "verifier, demander, relancer, biffer, transmettre ou classer"},
        {"label": "Preuve", "value": "presence, decision, reception, execution, paiement, refus ou cloture"},
    ]


def _privacy_guard(status: str) -> str:
    if status == document_intake.PRIVACY_BLOCKED:
        return "Bloquer l'export et demander un arbitrage."
    if status == document_intake.PRIVACY_REDACT:
        return "Preparer la version biffee avant toute diffusion."
    if status == document_intake.PRIVACY_CS_ONLY:
        return "Limiter la lecture au conseil syndical."
    if status == document_intake.PRIVACY_RAW:
        return "Diffusion possible seulement dans le contexte choisi."
    return "Choisir un niveau de confidentialite avant partage."


def _drop_guidance(intake: document_intake.DocumentIntakeInput) -> str:
    if intake.raw_cloud_requested or intake.source_kind == "cloud_raw":
        return "Retirer la cible cloud du brut et reprendre le depot local."
    if intake.source_hint_blocked:
        return "Remplacer le chemin masque par une reference opaque."
    if not intake.content_hash:
        return "Calculer l'empreinte locale avant classement."
    return "Continuer sans exposer de chemin local."


def _safe_reference(value: Any) -> str:
    text = _safe_text(value)
    if not text or text == "information masquee":
        return ""
    return text


def _safe_identifier(value: Any) -> str:
    text = _safe_text(value)
    if not text or text == "information masquee":
        return ""
    return re.sub(r"[^A-Za-z0-9_.:-]+", "-", text).strip("-")[:96]


def _safe_text(value: Any) -> str:
    text = _cell(value)
    if not text:
        return ""
    if PRIVATE_HINT_RE.search(text):
        return "information masquee"
    return text[:180]


def _short_hash(value: Any) -> str:
    text = _cell(value)
    if not text:
        return "empreinte a calculer"
    safe = re.sub(r"[^A-Fa-f0-9]", "", text)
    if not safe:
        return "empreinte a verifier"
    return safe[:12] if len(safe) <= 16 else f"{safe[:12]}...{safe[-8:]}"


def _safe_size(value: Any) -> str:
    text = _cell(value)
    if not text:
        return "taille a detecter"
    try:
        size = int(text)
    except ValueError:
        return "taille a verifier"
    if size < 1024:
        return f"{size} o"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} Ko"
    return f"{size / (1024 * 1024):.1f} Mo"


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()
