from __future__ import annotations

from typing import Any, Iterable

from .document_intake_view_options import CANONICAL_DOCUMENT_TYPE_OPTIONS


PRIVACY_CHOICES = (
    {"value": "OUVERT_COPROPRIETAIRES", "label": "Ouvert coproprietaires"},
    {"value": "A_MASQUER", "label": "A masquer avant partage"},
    {"value": "RESERVE_CS", "label": "Reserve conseil syndical"},
    {"value": "BLOQUE", "label": "Bloque"},
    {"value": "A_DECIDER", "label": "A decider plus tard"},
)
DOCUMENT_TYPE_CHOICE_OPTIONS = (
    {"value": "A_CLASSER", "label": "Je ne sais pas encore"},
    *CANONICAL_DOCUMENT_TYPE_OPTIONS,
)
DOCUMENT_TYPE_CHOICES = tuple(option["value"] for option in DOCUMENT_TYPE_CHOICE_OPTIONS)
JUSTIFICATION_REQUIRED = {"RESERVE_CS", "A_MASQUER", "BLOQUE"}

SYNTHETIC_DOCOPS_PROPOSALS: tuple[dict[str, str], ...] = (
    {
        "doc_id": "DOC-FICTIF-TRI-001",
        "sha256": "1" * 64,
        "document_type": "PV_AG",
        "privacy_status": "OUVERT_COPROPRIETAIRES",
        "reason": "Decision collective probable, reference neutralisee.",
        "confidence": "0.86",
        "local_state": "texte local reconnu",
    },
    {
        "doc_id": "DOC-FICTIF-TRI-002",
        "sha256": "2" * 64,
        "document_type": "Facture",
        "privacy_status": "A_MASQUER",
        "reason": "Donnees de tiers possibles avant partage.",
        "confidence": "0.72",
        "local_state": "revue humaine attendue",
    },
    {
        "doc_id": "DOC-FICTIF-TRI-003",
        "sha256": "3" * 64,
        "document_type": "Communication",
        "privacy_status": "A_DECIDER",
        "reason": "Origine neutralisee, decision a confirmer.",
        "confidence": "0.49",
        "local_state": "classement incertain",
    },
)


def template_context(
    proposals: Iterable[dict[str, str]] | None = None,
    *,
    saved: dict[str, str] | None = None,
) -> dict[str, Any]:
    cards = [dict(row) for row in (proposals or SYNTHETIC_DOCOPS_PROPOSALS)]
    summary = {
        "total": len(cards),
        "dirty": 0,
        "open": _count(cards, "OUVERT_COPROPRIETAIRES"),
        "mask": _count(cards, "A_MASQUER"),
        "cs": _count(cards, "RESERVE_CS"),
        "blocked": _count(cards, "BLOQUE"),
        "later": _count(cards, "A_DECIDER"),
    }
    return {
        "docops_feedback": {
            "title": "Corriger les propositions DocOps",
            "notice": "Jeu de test synthetique allowliste. Les noms de fichiers et chemins locaux ne sont pas affiches.",
            "summary": summary,
            "cards": cards,
            "privacy_choices": PRIVACY_CHOICES,
            "document_type_choices": DOCUMENT_TYPE_CHOICES,
            "document_type_choice_options": DOCUMENT_TYPE_CHOICE_OPTIONS,
            "justification_required": sorted(JUSTIFICATION_REQUIRED),
            "saved": saved or {},
        }
    }


def _count(cards: list[dict[str, str]], status: str) -> int:
    return sum(1 for card in cards if card.get("privacy_status") == status)
