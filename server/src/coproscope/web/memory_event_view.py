from __future__ import annotations

from typing import Any
from urllib.parse import urlencode


DEMO_MEMORY_EVENT_ID = "EVT-FICTIF-C31-INFILT-ASSURANCE"
SAFE_MISSING_ID = "reference-locale-masquee"
PRIVATE_TOKENS = {"raw", "restricted", "logs", "private", "system"}
PRIVATE_ROOTS = {"users", "home", "var", "tmp", "etc", "opt", "root", "mnt", "volumes"}
CONTEXT_QUERY_KEYS = ("periode", "categorie", "statut", "diffusion", "q")


def _route_tokens(value: str) -> list[str]:
    normalized = value.replace("\\", "/").lower()
    tokenized = "".join(char if char.isalnum() else " " for char in normalized)
    return tokenized.split()


def _contains_private_reference(value: object) -> bool:
    normalized = str(value or "").replace("\\", "/").strip().lower()
    if not normalized:
        return False
    tokens = _route_tokens(normalized)
    first_token = tokens[0] if tokens else ""
    has_path_marker = (
        "file://" in normalized
        or "://" in normalized
        or (len(normalized) > 2 and normalized[1:3] == ":/")
        or normalized.startswith("//")
        or normalized.startswith("/")
        or first_token in PRIVATE_ROOTS
    )
    return has_path_marker or any(token in PRIVATE_TOKENS for token in tokens)


def public_memory_event_id(value: object) -> str:
    text = " ".join(str(value or "").strip().split())[:140]
    if not text or _contains_private_reference(text):
        return SAFE_MISSING_ID
    return text


def _context_query(query: dict[str, str] | None) -> dict[str, str]:
    values: dict[str, str] = {}
    for key in CONTEXT_QUERY_KEYS:
        value = str((query or {}).get(key) or "").strip()
        if value and not _contains_private_reference(value):
            values[key] = value[:140]
    return values


def href_with_query(path: str, query: dict[str, str] | None = None, **extra: str) -> str:
    values = _context_query(query)
    for key, value in extra.items():
        clean = str(value or "").strip()
        if clean and not _contains_private_reference(clean):
            values[key] = clean[:140]
    return f"{path}?{urlencode(values)}" if values else path


def _demo_detail(query: dict[str, str]) -> dict[str, Any]:
    event_id = DEMO_MEMORY_EVENT_ID
    review_href = href_with_query("/confidentialite", None, scope="event", selected=event_id)
    relance_href = href_with_query(
        "/demandes/relance",
        None,
        request_id="REQ-FICTIF-ASSURANCE-B12",
        action_id="ACTION-FICTIF-C31-ASSURANCE",
        event_id=event_id,
    )
    return {
        "state": "found",
        "context": {
            "route": f"/chantiers/{event_id}",
            "title": "Detail evenement memoire",
            "source_of_truth": False,
            "watermark": "export derive, non source de verite",
            "active_nav_label": "Memoire copropriete",
            "badge": "Donnees FICTIVES de test",
            "back_href": href_with_query("/chantiers", query),
        },
        "event": {
            "id": event_id,
            "title": "Infiltration C31 - suivi assurance B12",
            "category": "Sinistre",
            "status_label": "Sinistre ouvert",
            "date_label": "03 mars 2025",
            "owner_label": "Nadia L. fictive",
            "next_action": "Relancer le syndic et demander le retour assureur avant le 24 mai 2026.",
            "proof_status": "Preuve finale manquante",
            "diffusion_label": "CS seulement en version interne. Coproprietaires: version masquee et derivee.",
            "summary": "L'infiltration C31 reste ouverte car l'assurance B12 est a relancer et la preuve finale manque.",
            "handover_note": (
                "Transmettre le resume, le PV AG et l'etat assurance B12. Dire clairement que la preuve finale manque."
            ),
            "restriction_note": (
                "Masquer noms, photos de cave C31 et commentaire non verifie du syndic. Export derive seulement."
            ),
        },
        "status_strip": [
            {"label": "Statut", "value": "Sinistre ouvert"},
            {"label": "Preuve", "value": "Preuve finale manquante"},
            {"label": "Diffusion", "value": "CS interne / version masquee"},
            {"label": "Action", "value": "Relancer assurance B12"},
        ],
        "timeline": [
            {
                "date_label": "03 mars 2025",
                "title": "Infiltration C31 signalee",
                "body": "Photo et constat DOC-FICTIF-C31-INFILT ajoutes au coffre local.",
                "restriction": "Photos privees de cave C31",
                "document_id": "DOC-FICTIF-C31-INFILT",
                "href": href_with_query("/documents/DOC-FICTIF-C31-INFILT", None, event_id=event_id),
            },
            {
                "date_label": "08 mars 2025",
                "title": "Assurance B12 demandee",
                "body": "REQ-FICTIF-ASSURANCE-B12 creee pour obtenir attestation, declaration et retour assureur.",
                "action_id": "REQ-FICTIF-ASSURANCE-B12",
                "href": relance_href,
            },
            {
                "date_label": "10 avril 2025",
                "title": "PV AG rattache au sinistre",
                "body": "PV AG 2024: mandat pour suivi assurance et devis de reprise.",
                "document_id": "DOC-FICTIF-PV-AG-2024-C31",
                "href": href_with_query("/documents/DOC-FICTIF-PV-AG-2024-C31", None, event_id=event_id),
            },
            {
                "date_label": "21 mai 2026",
                "title": "Note syndic recue hors outil",
                "body": "Note syndic: visite technique annoncee, mais aucun justificatif final.",
                "document_id": "DOC-FICTIF-NOTE-SYNDIC-C31",
                "href": href_with_query("/documents/DOC-FICTIF-NOTE-SYNDIC-C31", None, check="external-note", event_id=event_id),
            },
        ],
        "linked_documents": [
            {
                "label": "Signalement infiltration C31",
                "type": "IMG",
                "diffusion": "bloque en version non masquee",
                "reason": "photos privees de cave C31",
                "href": href_with_query("/documents/DOC-FICTIF-C31-INFILT", None, event_id=event_id),
            },
            {
                "label": "Assurance B12 attendue",
                "type": "REQ",
                "diffusion": "a relancer",
                "reason": "preuve finale manquante",
                "href": relance_href,
            },
            {
                "label": "PV AG du 10/04/2025",
                "type": "PDF",
                "diffusion": "diffusable apres masquage",
                "reason": "source de mandat",
                "href": href_with_query("/documents/DOC-FICTIF-PV-AG-2024-C31", None, event_id=event_id),
            },
            {
                "label": "Note syndic 21/05/2026",
                "type": "TXT",
                "diffusion": "a verifier",
                "reason": "reponse hors outil non prouvee",
                "href": href_with_query("/documents/DOC-FICTIF-NOTE-SYNDIC-C31", None, check="external-note", event_id=event_id),
            },
        ],
        "passation": {
            "title": "Passation CS",
            "note": "Reprendre l'histoire, les limites de preuve et la relance assurance B12.",
            "items": [
                "Resume transmissible sans piece originale",
                "PV AG comme source diffusable apres masquage",
                "Assurance B12 a relancer avant cloture",
            ],
        },
        "transmission": {
            "title": "Version transmissible",
            "included": ["Resume du sinistre", "PV AG", "etat assurance B12"],
            "masked": ["noms", "photos cave C31", "commentaire syndic non verifie"],
            "blocked_reason": "Export final bloque tant que la preuve assureur manque.",
            "review_href": review_href,
        },
        "actions": {
            "back_memory": {"label": "Retour a la memoire", "href": href_with_query("/chantiers", query)},
            "prepare_shareable": {"label": "Preparer version diffusable", "href": review_href},
            "create_relance": {"label": "Creer action de relance", "href": relance_href},
            "add_document": {
                "label": "Ajouter document",
                "href": href_with_query("/documents/ajouter", None, intent="memory", event_id=event_id),
            },
            "export_event": {
                "label": "Exporter cet evenement",
                "href": href_with_query("/exports/passation", None, scope="event", selected=event_id),
            },
            "ask_insurance": {"label": "Demander assurance B12", "href": relance_href},
            "verify_note": {
                "label": "Verifier note syndic",
                "href": href_with_query("/documents/DOC-FICTIF-NOTE-SYNDIC-C31", None, check="external-note", event_id=event_id),
            },
        },
    }


def build_memory_event_detail(event_id: object, query: dict[str, str] | None = None) -> dict[str, Any]:
    safe_query = _context_query(query)
    safe_id = public_memory_event_id(event_id)
    if safe_id == DEMO_MEMORY_EVENT_ID:
        return _demo_detail(safe_query)
    return {
        "state": "missing",
        "context": {
            "route": f"/chantiers/{safe_id}",
            "title": "Detail evenement memoire",
            "source_of_truth": False,
            "watermark": "export derive, non source de verite",
            "active_nav_label": "Memoire copropriete",
            "badge": "Donnees FICTIVES de test",
            "back_href": href_with_query("/chantiers", safe_query),
        },
        "event": {
            "id": safe_id,
            "title": "Evenement introuvable",
            "status_label": "A verifier",
            "summary": "La fiche memoire demandee n'est pas disponible dans la projection courante.",
            "next_action": "Revenir a la memoire ou filtrer les sujets ouverts.",
        },
        "status_strip": [],
        "timeline": [],
        "linked_documents": [],
        "passation": {"title": "Passation CS", "note": "Rien n'a ete modifie.", "items": []},
        "transmission": {
            "title": "Version transmissible",
            "included": [],
            "masked": [],
            "blocked_reason": "Evenement absent de la projection courante.",
            "review_href": href_with_query("/chantiers", safe_query),
        },
        "actions": {
            "back_memory": {"label": "Retour a la memoire", "href": href_with_query("/chantiers", safe_query)},
            "open_topics": {"label": "Voir les sujets ouverts", "href": href_with_query("/chantiers", safe_query, statut="ouvert")},
        },
    }
