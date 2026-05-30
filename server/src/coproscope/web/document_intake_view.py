from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict
from typing import Any, Iterable, Mapping

from ..modules import document_intake
from .document_intake_view_options import (
    ACTION_KIND_OPTIONS,
    DOCUMENT_TYPE_OPTIONS,
    POINT_KIND_OPTIONS,
    PRIVACY_OPTIONS,
    PROOF_INTENT_OPTIONS,
)


STATUS_LABELS = {
    document_intake.RUNTIME_READY: "pret a rattacher",
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
    document_intake.PRIVACY_RAW: "peut etre partage tel quel",
    document_intake.PRIVACY_REDACT: "a masquer avant partage",
    document_intake.PRIVACY_CS_ONLY: "reserve au conseil syndical",
    document_intake.PRIVACY_BLOCKED: "ne pas partager",
    document_intake.PRIVACY_ARBITRATE: "a decider avant partage",
}

CLASSIFICATION_LABELS = {
    document_intake.CLASSIFICATION_PENDING: "a proposer",
    document_intake.CLASSIFICATION_PROPOSED: "propose",
    document_intake.CLASSIFICATION_ACCEPTED: "accepte",
    document_intake.CLASSIFICATION_UNSURE: "je ne sais pas encore",
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
TEXT_OK_STATUSES = {"TEXT_EXTRACTED", "OCR_DONE"}
TEXT_REINFORCED_STATUSES = {"OCR_REQUIRED"}
TEXT_BLOCKED_STATUSES = {"UNSUPPORTED", "EXTRACTION_ERROR", "SOURCE_MISSING"}
TRACK_DONE = "done"
TRACK_CURRENT = "current"
TRACK_BLOCKED = "blocked"
TRACK_IDLE = "idle"


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
    required_checks = [
        item
        for card in cards
        for item in card["checklist"]
        if item["required"] and not item["future"]
    ]
    done_checks = [item for item in required_checks if item["status"] == document_intake.CHECK_OK]
    progress_pct = round((len(done_checks) / len(required_checks)) * 100) if required_checks else 0
    workflow_steps = _workflow_steps(cards)

    return {
        "title": "Absorber des informations",
        "intro": (
            "Deposez ou consultez les arrivees locales. CoproScope garde les bruts dans "
            "l'instance, propose une qualification locale, puis vous aide a confirmer "
            "type, confidentialite et rattachement."
        ),
        "summary": {
            "total": len(cards),
            "ready": len(ready_cards),
            "todo": len(todo_cards),
            "blocked": len(blocked_cards),
            "warnings": len(warning_cards),
            "progress_pct": progress_pct,
            "text_ready": _workflow_count(cards, "texte", TRACK_DONE),
            "reinforced": sum(1 for card in cards if card["docops"]["reinforced_required"]),
            "ready_to_link": sum(1 for card in cards if card["docops"]["ready_to_link"]),
        },
        "has_cards": bool(cards),
        "cards": cards,
        "trust_badges": [
            "Sources multiples",
            "Bruts locaux",
            "Sans IA/cloud externe",
            "Texte reconnu localement",
            "Prequalification locale",
            "Validation humaine",
            "Rien n'est diffuse automatiquement",
        ],
        "docops_workflow": workflow_steps,
        "document_type_options": list(DOCUMENT_TYPE_OPTIONS),
        "privacy_options": list(PRIVACY_OPTIONS),
        "point_kind_options": list(POINT_KIND_OPTIONS),
        "action_kind_options": list(ACTION_KIND_OPTIONS),
        "proof_intent_options": list(PROOF_INTENT_OPTIONS),
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
            "title": "Deposez vos premiers documents",
            "body": (
                "Choisissez un ou plusieurs fichiers. Ils resteront dans le coffre local de cette instance."
            ),
            "first_step": "Le brut reste dans le coffre local de l'instance.",
            "next_step": "Vous choisirez ensuite le type, la confidentialite et le rattachement piece -> point -> action -> preuve.",
            "inbox": "Aucune information a qualifier dans les sources selectionnees.",
        },
    }


def template_context(
    rows: Iterable[Mapping[str, Any] | document_intake.DocumentIntakeInput] | None = None,
) -> dict[str, Any]:
    return {"document_intake": build_document_intake_view(rows)}


def _card(row: Mapping[str, Any] | document_intake.DocumentIntakeInput, index: int) -> dict[str, Any]:
    raw_row = dict(row) if isinstance(row, Mapping) else {}
    intake = document_intake.normalize_document_intake(row) if isinstance(row, Mapping) else row
    runtime = document_intake.build_runtime_checklist(intake)
    doc_label = _safe_text(intake.display_name) or _safe_text(intake.doc_id) or f"Document {index}"
    if doc_label == "information masquee":
        doc_label = f"Document {index}"
    doc_id = _safe_identifier(intake.doc_id) or f"DOC-A-NOMMER-{index:03d}"
    classification = intake.classification
    privacy = intake.privacy
    safe_derivative = _safe_reference(privacy.required_derivative)
    text_step = _text_step(raw_row, intake)
    track = _docops_track(intake, runtime, text_step, safe_derivative, raw_row)
    docops = _docops_state(track, text_step)
    return {
        "index": index,
        "doc_id": doc_id,
        "document_label": doc_label,
        "source_id": _safe_identifier(raw_row.get("source_id")) or "inbox",
        "source_label": _safe_text(raw_row.get("source_label")) or ("depot local" if intake.source_kind == "depot_local" else "source a revoir"),
        "prequalification_label": "Proposition locale",
        "local_reference": _safe_reference(intake.local_reference) or "reference opaque a creer",
        "format_label": _safe_text(intake.file_format) or "format a detecter",
        "size_label": _safe_size(intake.size_bytes),
        "hash_label": _short_hash(intake.content_hash),
        "duplicate_label": _safe_identifier(intake.duplicate_of),
        "status": runtime.status,
        "status_label": STATUS_LABELS.get(runtime.status, runtime.status),
        "status_tone": STATUS_TONES.get(runtime.status, "p2"),
        "next_action": _novice_copy(runtime.next_action),
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
            "required_derivative": safe_derivative or "version derivee a nommer si besoin",
        },
        "diffusion_review": _diffusion_review(privacy.status, safe_derivative),
        "docops": docops,
        "docops_track": track,
        "attachments": [_attachment(attachment, doc_id, item_index) for item_index, attachment in enumerate(intake.attachments, start=1)],
        "attachment_form": _attachment_form(intake.attachments),
        "has_attachments": bool(intake.attachments),
        "privacy_guard": _privacy_guard(privacy.status),
        "drop_guidance": _drop_guidance(intake),
    }


def _check_item(item: document_intake.ChecklistItem) -> dict[str, Any]:
    return {
        **asdict(item),
        "next_action": _novice_copy(item.next_action),
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


def _attachment_form(attachments: tuple[document_intake.AttachmentDraft, ...]) -> dict[str, str]:
    attachment = attachments[0] if attachments else document_intake.AttachmentDraft()
    return {
        "point_kind": _safe_text(attachment.point_kind) or "preuve_libre",
        "point_id": _safe_identifier(attachment.point_id),
        "point_label": _safe_text(attachment.point_label),
        "action_kind": _safe_text(attachment.action_kind) or "verifier",
        "action_label": _safe_text(attachment.action_label),
        "proof_intent": _safe_text(attachment.proof_intent) or "presence",
        "proof_label": _safe_text(attachment.proof_label),
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


def _workflow_steps(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(cards)
    reinforced = sum(1 for card in cards if card["docops"]["reinforced_required"])
    return [
        _workflow_step("depot", "Deposees localement", _workflow_count(cards, "depot", TRACK_DONE), total),
        _workflow_step("texte", "Texte reconnu", _workflow_count(cards, "texte", TRACK_DONE), total),
        _workflow_step("type", "Type de document", _workflow_count(cards, "type", TRACK_DONE), total),
        _workflow_step("confidentialite", "Confidentialite", _workflow_count(cards, "confidentialite", TRACK_DONE), total),
        {
            "key": "renfort",
            "label": "Traitement renforce",
            "count": reinforced,
            "total": total,
            "counter": f"{reinforced}/{total}" if total else "0/0",
            "detail": "Texte absent, biffage, arbitrage ou blocage local.",
            "tone": "p2" if reinforced else "ok",
        },
        {
            "key": "pret",
            "label": "Pretes a rattacher",
            "count": sum(1 for card in cards if card["docops"]["ready_to_link"]),
            "total": total,
            "counter": f"{sum(1 for card in cards if card['docops']['ready_to_link'])}/{total}" if total else "0/0",
            "detail": "Type et confidentialite traites, sans blocage.",
            "tone": "ok" if total and any(card["docops"]["ready_to_link"] for card in cards) else "p2",
        },
    ]


def _workflow_step(key: str, label: str, count: int, total: int) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "count": count,
        "total": total,
        "counter": f"{count}/{total}" if total else "0/0",
        "detail": "Signal reel local uniquement.",
        "tone": "ok" if total and count == total else "p2",
    }


def _workflow_count(cards: list[dict[str, Any]], key: str, state: str) -> int:
    return sum(1 for card in cards for step in card["docops_track"] if step["key"] == key and step["state"] == state)


def _docops_track(
    intake: document_intake.DocumentIntakeInput,
    runtime: document_intake.DocumentIntakeRuntime,
    text_step: dict[str, str],
    safe_derivative: str,
    raw_row: Mapping[str, Any],
) -> list[dict[str, str]]:
    checks = {item.step_id: item for item in runtime.checklist}
    return [
        _track_from_check("depot", "Depot local", checks[document_intake.STEP_LOCAL_DEPOSIT]),
        text_step,
        _track_from_check("type", "Type reconnu", checks[document_intake.STEP_CLASSIFICATION]),
        _track_from_check("confidentialite", "Confidentialite", checks[document_intake.STEP_PRIVACY]),
        _reinforced_step(intake, text_step, safe_derivative, raw_row),
        _track_from_check("rattachement", "Rattachement", checks[document_intake.STEP_LINKING]),
    ]


def _docops_state(track: list[dict[str, str]], text_step: dict[str, str]) -> dict[str, Any]:
    states = {step["key"]: step["state"] for step in track}
    reinforced = next(step for step in track if step["key"] == "renfort")
    required_ok = all(states.get(key) == TRACK_DONE for key in ("depot", "texte", "type", "confidentialite"))
    no_block = not any(states.get(key) == TRACK_BLOCKED for key in ("depot", "texte", "type", "confidentialite", "renfort"))
    return {
        "text_label": text_step["label"],
        "text_detail": text_step["detail"],
        "reinforced_required": reinforced["state"] in {TRACK_CURRENT, TRACK_BLOCKED},
        "ready_to_link": required_ok and no_block and reinforced["state"] != TRACK_CURRENT,
    }


def _track_from_check(key: str, label: str, item: document_intake.ChecklistItem) -> dict[str, str]:
    state = TRACK_DONE if item.status == document_intake.CHECK_OK else TRACK_BLOCKED if item.status == document_intake.CHECK_BLOCKED else TRACK_CURRENT
    return {
        "key": key,
        "label": label,
        "state": state,
        "tone": "ok" if state == TRACK_DONE else "p1" if state == TRACK_BLOCKED else "p2",
        "detail": _novice_copy(item.next_action),
    }


def _text_step(raw_row: Mapping[str, Any], intake: document_intake.DocumentIntakeInput) -> dict[str, str]:
    local_text_status = _cell(raw_row.get("local_text_status")).lower()
    status_ocr = _cell(raw_row.get("status_ocr")).upper()
    text_chars = _int_cell(raw_row.get("text_char_count"))
    has_text_path = bool(_cell(raw_row.get("text_path")))
    if intake.raw_cloud_requested or intake.source_kind == "cloud_raw":
        return _track_item("texte", "Texte local", TRACK_BLOCKED, "Le brut ne doit pas partir vers un cloud.")
    if local_text_status == "ok" or status_ocr in TEXT_OK_STATUSES or text_chars > 0 or has_text_path:
        detail = f"{text_chars} caracteres reconnus sans IA/cloud." if text_chars > 0 else "Texte reconnu localement sans IA/cloud."
        return _track_item("texte", "Texte reconnu", TRACK_DONE, detail)
    if local_text_status == "error" or status_ocr in TEXT_BLOCKED_STATUSES:
        return _track_item("texte", "Texte a reprendre", TRACK_BLOCKED, "Le traitement local n'a pas produit de texte exploitable.")
    if status_ocr in TEXT_REINFORCED_STATUSES:
        return _track_item("texte", "OCR local requis", TRACK_CURRENT, "Traitement renforce local, sans IA/cloud.")
    if not intake.content_hash:
        return _track_item("texte", "En attente du depot", TRACK_CURRENT, "Le texte sera controle apres l'empreinte locale.")
    return _track_item("texte", "Texte a verifier", TRACK_CURRENT, "Aucun signal de texte local reconnu pour l'instant.")


def _reinforced_step(
    intake: document_intake.DocumentIntakeInput,
    text_step: dict[str, str],
    safe_derivative: str,
    raw_row: Mapping[str, Any],
) -> dict[str, str]:
    required_transformations = _cell(raw_row.get("required_transformations")).lower()
    status_ocr = _cell(raw_row.get("status_ocr")).upper()
    redaction_status = _cell(raw_row.get("redaction_status")).upper()
    if intake.privacy.status == document_intake.PRIVACY_BLOCKED:
        return _track_item("renfort", "Traitement renforce", TRACK_BLOCKED, "Piece bloquee: arbitrage humain requis.")
    if status_ocr in TEXT_REINFORCED_STATUSES or text_step["state"] == TRACK_BLOCKED:
        return _track_item("renfort", "Traitement renforce", TRACK_CURRENT, "Reprise locale du texte ou OCR local requis.")
    if intake.privacy.status == document_intake.PRIVACY_REDACT and not safe_derivative:
        return _track_item("renfort", "Traitement renforce", TRACK_CURRENT, "Version masquee a preparer avant partage.")
    if "redaction" in required_transformations and redaction_status != "REDACTED":
        return _track_item("renfort", "Traitement renforce", TRACK_CURRENT, "Biffage local a verifier.")
    if intake.privacy.status == document_intake.PRIVACY_ARBITRATE:
        return _track_item("renfort", "Traitement renforce", TRACK_CURRENT, "Decision de confidentialite manquante.")
    return _track_item("renfort", "Traitement renforce", TRACK_IDLE, "Aucun renfort requis a ce stade.")


def _track_item(key: str, label: str, state: str, detail: str) -> dict[str, str]:
    return {
        "key": key,
        "label": label,
        "state": state,
        "tone": "ok" if state in {TRACK_DONE, TRACK_IDLE} else "p1" if state == TRACK_BLOCKED else "p2",
        "detail": _novice_copy(detail),
    }


def _novice_copy(text: str) -> str:
    replacements = {
        "DIFFUSABLE_BRUT": "Peut etre partage tel quel",
        "A_BIFFER": "A masquer avant partage",
        "RESERVE_CS": "Reserve au conseil syndical",
        "BLOQUE": "Ne pas partager",
        "A_CLASSER": "Je ne sais pas encore",
        "classification assistee": "type de document",
    }
    result = text
    for technical, novice in replacements.items():
        result = result.replace(technical, novice)
        result = result.replace(technical.lower(), novice.lower())
    return result


def _novice_steps() -> list[dict[str, str]]:
    return [
        {
            "title": "1. Deposer localement",
            "body": "Le fichier brut reste dans l'instance locale; l'ecran affiche seulement une reference opaque et une empreinte.",
        },
        {
            "title": "2. Classer sans certitude forcee",
            "body": "Si le type est flou, gardez Je ne sais pas encore et demandez une verification humaine.",
        },
        {
            "title": "3. Controler la confidentialite",
            "body": "Choisir Peut etre partage tel quel, A masquer avant partage, Reserve au conseil syndical ou Ne pas partager.",
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


def _diffusion_review(status: str, safe_derivative: str) -> dict[str, str]:
    if status == document_intake.PRIVACY_BLOCKED:
        return {"tone": "p1", "label": "Diffusion bloquee", "body": "Aucun partage tant qu'un arbitrage n'est pas fait."}
    if status == document_intake.PRIVACY_ARBITRATE:
        return {"tone": "p2", "label": "Diffusion bloquee", "body": "Choisir une confidentialite avant tout partage."}
    if status == document_intake.PRIVACY_REDACT and not safe_derivative:
        return {"tone": "p2", "label": "Diffusion bloquee", "body": "Nommer une version masquee avant diffusion."}
    if status == document_intake.PRIVACY_REDACT:
        return {"tone": "ok", "label": "Diffusion biffee uniquement", "body": "Le brut reste local; seule la version masquee peut sortir."}
    if status == document_intake.PRIVACY_CS_ONLY:
        return {"tone": "ok", "label": "Reserve conseil syndical", "body": "Limiter la lecture au conseil syndical."}
    return {"tone": "ok", "label": "Diffusion brute possible", "body": "Partager seulement dans le contexte choisi."}


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


def _int_cell(value: Any) -> int:
    try:
        return int(_cell(value) or "0")
    except ValueError:
        return 0


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()
