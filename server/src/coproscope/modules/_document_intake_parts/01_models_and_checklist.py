from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


STEP_LOCAL_DEPOSIT = "depot_local"
STEP_CLASSIFICATION = "classification"
STEP_PRIVACY = "confidentialite"
STEP_LINKING = "rattachement"
STEP_PDF_ANNOTATION = "annotation_pdf_future"
STEP_SIGNED_EVENT = "evenement_signe_futur"

CHECK_OK = "ok"
CHECK_TODO = "a_completer"
CHECK_BLOCKED = "bloque"
CHECK_FUTURE = "futur"

RUNTIME_READY = "pret_a_enregistrer"
RUNTIME_NEEDS_INPUT = "a_completer"
RUNTIME_BLOCKED = "bloque"

CLASSIFICATION_PENDING = "PENDING"
CLASSIFICATION_PROPOSED = "PROPOSED"
CLASSIFICATION_ACCEPTED = "ACCEPTED"
CLASSIFICATION_UNSURE = "A_CLASSER"
CLASSIFICATION_STATUSES = frozenset(
    {
        CLASSIFICATION_PENDING,
        CLASSIFICATION_PROPOSED,
        CLASSIFICATION_ACCEPTED,
        CLASSIFICATION_UNSURE,
    }
)

PRIVACY_RAW = "DIFFUSABLE_BRUT"
PRIVACY_REDACT = "A_BIFFER"
PRIVACY_CS_ONLY = "RESERVE_CS"
PRIVACY_BLOCKED = "BLOQUE"
PRIVACY_ARBITRATE = "A_ARBITRER"
PRIVACY_STATUSES = frozenset(
    {
        PRIVACY_RAW,
        PRIVACY_REDACT,
        PRIVACY_CS_ONLY,
        PRIVACY_BLOCKED,
        PRIVACY_ARBITRATE,
    }
)

POINT_KINDS = frozenset(
    {
        "ag",
        "decision",
        "demande",
        "facture",
        "incident",
        "chantier",
        "contentieux",
        "preuve_libre",
    }
)
ACTION_KINDS = frozenset({"verifier", "demander", "relancer", "biffer", "transmettre", "classer"})
PROOF_INTENTS = frozenset({"presence", "decision", "reception", "execution", "paiement", "refus", "cloture"})

FUTURE_EVENT_TYPES = (
    "document_added",
    "document_classified",
    "document_privacy_reviewed",
    "document_linked_to_point",
    "action_created_from_document",
    "proof_attached",
    "pdf_annotation_created",
    "signed_event_recorded",
)


@dataclass(frozen=True)
class ClassificationDraft:
    document_type: str = ""
    domain: str = ""
    period: str = ""
    actor_hint: str = ""
    lot: str = ""
    confidence: str = ""
    status: str = CLASSIFICATION_PENDING
    reason: str = ""


@dataclass(frozen=True)
class PrivacyDraft:
    status: str = PRIVACY_ARBITRATE
    rationale: str = ""
    required_derivative: str = ""


@dataclass(frozen=True)
class AttachmentDraft:
    piece_label: str = ""
    point_id: str = ""
    point_label: str = ""
    point_kind: str = "preuve_libre"
    action_kind: str = "verifier"
    action_label: str = ""
    proof_intent: str = "presence"
    proof_label: str = ""


@dataclass(frozen=True)
class DocumentIntakeInput:
    doc_id: str = ""
    display_name: str = ""
    local_reference: str = ""
    source_kind: str = "depot_local"
    file_format: str = ""
    size_bytes: str = ""
    content_hash: str = ""
    duplicate_of: str = ""
    classification: ClassificationDraft = field(default_factory=ClassificationDraft)
    privacy: PrivacyDraft = field(default_factory=PrivacyDraft)
    attachments: tuple[AttachmentDraft, ...] = ()
    pdf_annotation_requested: bool = False
    signed_event_requested: bool = False
    raw_cloud_requested: bool = False
    source_hint_blocked: bool = False


@dataclass(frozen=True)
class ChecklistItem:
    step_id: str
    novice_label: str
    status: str
    next_action: str
    required: bool = True
    future: bool = False


@dataclass(frozen=True)
class DocumentIntakeRuntime:
    status: str
    next_action: str
    checklist: tuple[ChecklistItem, ...]
    warnings: tuple[str, ...] = ()
    future_event_types: tuple[str, ...] = FUTURE_EVENT_TYPES


def normalize_document_intake(row: Mapping[str, Any]) -> DocumentIntakeInput:
    row_data = dict(row)
    content_hash = _first_text(row_data, ("content_hash", "sha256", "hash", "empreinte"))
    local_reference, source_hint_blocked = _safe_local_reference(
        _first_text(row_data, ("local_reference", "local_ref", "storage_ref", "depot_ref", "original_path"))
    )
    doc_id = _first_text(row_data, ("doc_id", "document_id", "id"))
    if not doc_id and content_hash:
        doc_id = f"DOC-{content_hash[:12].upper()}"
    display_name = _first_text(row_data, ("display_name", "file_name", "nom_affiche", "title"))
    source_kind = _normalize_source_kind(_first_text(row_data, ("source_kind", "source", "origin")) or "depot_local")
    raw_cloud_requested = _truthy(_first_text(row_data, ("raw_cloud_requested", "cloud_raw", "sync_raw", "cloud_target")))

    attachments = _normalize_attachments(row_data.get("attachments") or row_data.get("rattachements") or ())
    if not attachments and any(
        _first_text(row_data, fields)
        for fields in [
            ("point_id", "related_point_id"),
            ("action_label", "next_action"),
            ("proof_label", "preuve_attendue"),
        ]
    ):
        attachments = (_normalize_attachment(row_data),)

    return DocumentIntakeInput(
        doc_id=_cell(doc_id),
        display_name=_cell(display_name),
        local_reference=local_reference,
        source_kind=source_kind,
        file_format=_cell(_first_text(row_data, ("file_format", "extension", "format"))).lower().lstrip("."),
        size_bytes=_cell(_first_text(row_data, ("size_bytes", "taille_octets"))),
        content_hash=_cell(content_hash),
        duplicate_of=_cell(_first_text(row_data, ("duplicate_of", "doublon_de"))),
        classification=_normalize_classification(row_data),
        privacy=_normalize_privacy(row_data),
        attachments=attachments,
        pdf_annotation_requested=_truthy(_first_text(row_data, ("pdf_annotation_requested", "annotation_pdf"))),
        signed_event_requested=_truthy(_first_text(row_data, ("signed_event_requested", "evenement_signe"))),
        raw_cloud_requested=raw_cloud_requested or source_kind == "cloud_raw",
        source_hint_blocked=source_hint_blocked,
    )


def build_runtime_checklist(intake: DocumentIntakeInput | Mapping[str, Any]) -> DocumentIntakeRuntime:
    normalized = normalize_document_intake(intake) if isinstance(intake, Mapping) else intake
    items = (
        _deposit_item(normalized),
        _classification_item(normalized),
        _privacy_item(normalized),
        _linking_item(normalized),
        _pdf_annotation_item(normalized),
        _signed_event_item(normalized),
    )
    warnings = _warnings(normalized)
    status = _runtime_status(items)
    next_action = _runtime_next_action(status, items, normalized)
    return DocumentIntakeRuntime(status=status, next_action=next_action, checklist=items, warnings=warnings)


def novice_checklist(runtime: DocumentIntakeRuntime | DocumentIntakeInput | Mapping[str, Any]) -> list[str]:
    built = build_runtime_checklist(runtime) if not isinstance(runtime, DocumentIntakeRuntime) else runtime
    return [f"{item.novice_label} [{item.status}] - {item.next_action}" for item in built.checklist]


def runtime_to_dict(runtime: DocumentIntakeRuntime) -> dict[str, Any]:
    data = asdict(runtime)
    data["checklist"] = [asdict(item) for item in runtime.checklist]
    return data


def _deposit_item(intake: DocumentIntakeInput) -> ChecklistItem:
    if intake.raw_cloud_requested or intake.source_kind == "cloud_raw":
        return ChecklistItem(
            STEP_LOCAL_DEPOSIT,
            "Depot local: garder le fichier brut dans l'instance locale",
            CHECK_BLOCKED,
            "Retirer la cible cloud du brut, puis reprendre le depot local avec une reference opaque.",
        )
    if intake.source_hint_blocked:
        return ChecklistItem(
            STEP_LOCAL_DEPOSIT,
            "Depot local: garder le fichier brut dans l'instance locale",
            CHECK_TODO,
            "Remplacer le chemin local ou absolu par une reference opaque avant toute sortie.",
        )
    if not intake.doc_id or not intake.content_hash:
        return ChecklistItem(
            STEP_LOCAL_DEPOSIT,
            "Depot local: identifier le document sans lire son contenu ici",
            CHECK_TODO,
            "Fournir un doc_id et une empreinte calculee par le depot local.",
        )
    if intake.duplicate_of:
        return ChecklistItem(
            STEP_LOCAL_DEPOSIT,
            "Depot local: reutiliser le document deja connu",
            CHECK_OK,
            f"Confirmer que {intake.doc_id} reutilise {intake.duplicate_of} sans copie brute supplementaire.",
        )
    return ChecklistItem(
        STEP_LOCAL_DEPOSIT,
        "Depot local: document reference et empreinte locale presente",
        CHECK_OK,
        "Continuer vers la classification assistee.",
    )


def _classification_item(intake: DocumentIntakeInput) -> ChecklistItem:
    classification = intake.classification
    if classification.status == CLASSIFICATION_UNSURE:
        return ChecklistItem(
            STEP_CLASSIFICATION,
            "Classification: dire que le type reste a classer",
            CHECK_TODO,
            "Garder A_CLASSER et demander une verification humaine du type, du lot et de la periode.",
        )
    if not classification.document_type:
        return ChecklistItem(
            STEP_CLASSIFICATION,
            "Classification: proposer un type documentaire",
            CHECK_TODO,
            "Choisir ou corriger le type de document avant tout rattachement probatoire.",
        )
    if classification.status in {CLASSIFICATION_ACCEPTED, CLASSIFICATION_PROPOSED}:
        return ChecklistItem(
            STEP_CLASSIFICATION,
            "Classification: type, domaine et raison courte visibles",
            CHECK_OK,
            "Passer a l'arbitrage de confidentialite.",
        )
    return ChecklistItem(
        STEP_CLASSIFICATION,
        "Classification: proposition a confirmer",
        CHECK_TODO,
        "Accepter la proposition ou marquer A_CLASSER si elle reste ambigue.",
    )


def _privacy_item(intake: DocumentIntakeInput) -> ChecklistItem:
    privacy = intake.privacy
    if privacy.status == PRIVACY_BLOCKED:
        return ChecklistItem(
            STEP_PRIVACY,
            "Confidentialite: document bloque",
            CHECK_BLOCKED,
            "Ne pas exporter, ne pas partager et arbitrer une version derivee autorisee.",
        )
    if privacy.status == PRIVACY_ARBITRATE:
        return ChecklistItem(
            STEP_PRIVACY,
            "Confidentialite: choisir qui peut voir la piece",
            CHECK_TODO,
            "Choisir DIFFUSABLE_BRUT, A_BIFFER, RESERVE_CS ou BLOQUE avant toute sortie.",
        )
    if privacy.status == PRIVACY_REDACT:
        return ChecklistItem(
            STEP_PRIVACY,
            "Confidentialite: version biffee requise avant diffusion",
            CHECK_OK,
            "Preparer une version derivee biffee; le brut reste local.",
        )
    if privacy.status == PRIVACY_CS_ONLY:
        return ChecklistItem(
            STEP_PRIVACY,
            "Confidentialite: reserve conseil syndical",
            CHECK_OK,
            "Limiter les rattachements visibles au contexte conseil syndical.",
        )
    return ChecklistItem(
        STEP_PRIVACY,
        "Confidentialite: diffusion brute autorisee dans le contexte choisi",
        CHECK_OK,
        "Continuer vers le rattachement piece, point, action et preuve.",
    )


def _linking_item(intake: DocumentIntakeInput) -> ChecklistItem:
    if not intake.attachments:
        return ChecklistItem(
            STEP_LINKING,
            "Rattachement: relier la piece a un point, une action et une preuve",
            CHECK_TODO,
            "Ajouter au moins un lien avec point concret, action attendue et preuve visee.",
        )
    incomplete = [attachment for attachment in intake.attachments if not _attachment_complete(attachment)]
    if incomplete:
        return ChecklistItem(
            STEP_LINKING,
            "Rattachement: completer chaque lien metier",
            CHECK_TODO,
            "Completer le libelle du point, l'action et la preuve attendue pour chaque rattachement.",
        )
    return ChecklistItem(
        STEP_LINKING,
        "Rattachement: piece reliee a un point, une action et une preuve",
        CHECK_OK,
        "Enregistrer le lien sans dupliquer le fichier brut.",
    )


def _pdf_annotation_item(intake: DocumentIntakeInput) -> ChecklistItem:
    action = (
        "Journaliser la demande d'annotation; elle deviendra un evenement separe lie au doc_id, page, zone et hash."
        if intake.pdf_annotation_requested
        else "Ne rien bloquer: l'annotation PDF sera un evenement separe quand le moteur existera."
    )
    return ChecklistItem(
        STEP_PDF_ANNOTATION,
        "Annotation PDF future: ne jamais modifier le PDF source",
        CHECK_FUTURE,
        action,
        required=False,
        future=True,
    )


def _signed_event_item(intake: DocumentIntakeInput) -> ChecklistItem:
    action = (
        "Preparer les champs de hash entree/sortie; la signature sera ajoutee quand le journal signe existera."
        if intake.signed_event_requested
        else "Garder les types d'evenements prevus sans pretendre que la signature est livree."
    )
    return ChecklistItem(
        STEP_SIGNED_EVENT,
        "Evenement signe futur: preparer le journal sans signature active",
        CHECK_FUTURE,
        action,
        required=False,
        future=True,
    )


def _runtime_status(items: tuple[ChecklistItem, ...]) -> str:
    required = [item for item in items if item.required]
    if any(item.status == CHECK_BLOCKED for item in required):
        return RUNTIME_BLOCKED
    if any(item.status == CHECK_TODO for item in required):
        return RUNTIME_NEEDS_INPUT
    return RUNTIME_READY


def _runtime_next_action(status: str, items: tuple[ChecklistItem, ...], intake: DocumentIntakeInput) -> str:
    if status in {RUNTIME_BLOCKED, RUNTIME_NEEDS_INPUT}:
        for item in items:
            if item.required and item.status in {CHECK_BLOCKED, CHECK_TODO}:
                return item.next_action
    if intake.privacy.status == PRIVACY_REDACT:
        return "Enregistrer la piece et preparer une version biffee avant diffusion."
    if intake.duplicate_of:
        return "Enregistrer le rattachement en reutilisant le document deja connu."
    return "Enregistrer la piece, ses rattachements et les evenements futurs non signes."


def _warnings(intake: DocumentIntakeInput) -> tuple[str, ...]:
    warnings: list[str] = []
    if intake.raw_cloud_requested:
        warnings.append("raw_cloud_interdit")
    if intake.source_hint_blocked:
        warnings.append("chemin_local_ou_absolu_masque")
    if intake.privacy.status == PRIVACY_REDACT and not intake.privacy.required_derivative:
        warnings.append("version_biffee_a_nommer")
    return tuple(warnings)


def _normalize_classification(row: Mapping[str, Any]) -> ClassificationDraft:
    status = _normalize_classification_status(_first_text(row, ("classification_status", "statut_classification")))
    document_type = _cell(_first_text(row, ("document_type", "type_documentaire", "type")))
    if document_type and status == CLASSIFICATION_PENDING:
        status = CLASSIFICATION_PROPOSED
    return ClassificationDraft(
        document_type=document_type,
        domain=_cell(_first_text(row, ("domain", "domaine", "theme"))),
        period=_cell(_first_text(row, ("period", "periode", "exercise", "exercice"))),
        actor_hint=_cell(_first_text(row, ("actor_hint", "acteur", "fournisseur"))),
        lot=_cell(_first_text(row, ("lot", "workstream"))),
        confidence=_cell(_first_text(row, ("confidence", "confiance"))),
        status=status,
        reason=_cell(_first_text(row, ("classification_reason", "raison", "motif"))),
    )


def _normalize_privacy(row: Mapping[str, Any]) -> PrivacyDraft:
    status = _normalize_privacy_status(_first_text(row, ("privacy_status", "confidentialite", "privacy_review_status")))
    return PrivacyDraft(
        status=status,
        rationale=_cell(_first_text(row, ("privacy_rationale", "privacy_review_justification", "justification"))),
        required_derivative=_cell(_first_text(row, ("required_derivative", "version_biffee", "derive_attendu"))),
    )


def _normalize_attachments(value: Any) -> tuple[AttachmentDraft, ...]:
    if isinstance(value, Mapping):
        return (_normalize_attachment(value),)
    if isinstance(value, (list, tuple)):
        return tuple(_normalize_attachment(item) for item in value if isinstance(item, Mapping))
    return ()


def _normalize_attachment(row: Mapping[str, Any]) -> AttachmentDraft:
    point_kind = _normalize_point_kind(_first_text(row, ("point_kind", "type_point", "scope")))
    action_kind = _normalize_action_kind(_first_text(row, ("action_kind", "type_action")))
    proof_intent = _normalize_proof_intent(_first_text(row, ("proof_intent", "intention_preuve")))
    return AttachmentDraft(
        piece_label=_cell(_first_text(row, ("piece_label", "libelle_piece", "doc_id", "document_id"))),
        point_id=_cell(_first_text(row, ("point_id", "related_point_id", "rattachement_point"))),
        point_label=_cell(_first_text(row, ("point_label", "libelle_point", "sujet"))),
        point_kind=point_kind,
        action_kind=action_kind,
        action_label=_cell(_first_text(row, ("action_label", "next_action", "action_attendue"))),
        proof_intent=proof_intent,
        proof_label=_cell(_first_text(row, ("proof_label", "preuve_attendue", "proof_ref"))),
    )


def _attachment_complete(attachment: AttachmentDraft) -> bool:
    return bool(attachment.piece_label and attachment.point_label and attachment.action_label and attachment.proof_label)


def _normalize_source_kind(value: str) -> str:
    token = _token(value)
    aliases = {
        "depot": "depot_local",
        "depot_local": "depot_local",
        "local": "depot_local",
        "docops": "depot_local",
        "cloud": "cloud_raw",
        "drive": "cloud_raw",
        "dropbox": "cloud_raw",
        "sharepoint": "cloud_raw",
        "cloud_raw": "cloud_raw",
    }
    return aliases.get(token, token or "depot_local")


def _normalize_classification_status(value: str) -> str:
    token = _token(value).upper()
    aliases = {
        "": CLASSIFICATION_PENDING,
        "A_CLASSER": CLASSIFICATION_UNSURE,
        "A_VERIFIER": CLASSIFICATION_UNSURE,
        "PENDING": CLASSIFICATION_PENDING,
        "PROPOSED": CLASSIFICATION_PROPOSED,
        "PROPOSE": CLASSIFICATION_PROPOSED,
        "ACCEPTED": CLASSIFICATION_ACCEPTED,
        "ACCEPTE": CLASSIFICATION_ACCEPTED,
    }
    return aliases.get(token, token if token in CLASSIFICATION_STATUSES else CLASSIFICATION_PENDING)


def _normalize_privacy_status(value: str) -> str:
    token = _token(value).upper()
    aliases = {
        "": PRIVACY_ARBITRATE,
        "A_BIFFER": PRIVACY_REDACT,
        "BIFFAGE": PRIVACY_REDACT,
        "DIFFUSABLE_APRES_BIFFAGE": PRIVACY_REDACT,
        "RESERVE_CS": PRIVACY_CS_ONLY,
        "CONSEIL_SYNDICAL": PRIVACY_CS_ONLY,
        "CS": PRIVACY_CS_ONLY,
        "BLOQUE": PRIVACY_BLOCKED,
        "BLOCKED": PRIVACY_BLOCKED,
        "A_ARBITRER": PRIVACY_ARBITRATE,
        "ARBITRAGE": PRIVACY_ARBITRATE,
        "DIFFUSABLE_BRUT": PRIVACY_RAW,
        "RAW": PRIVACY_RAW,
    }
    return aliases.get(token, token if token in PRIVACY_STATUSES else PRIVACY_ARBITRATE)
