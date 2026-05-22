from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from ..core.common import InstanceConfig, read_csv
from ..modules import decisionops


STATUS_DRAFT = "draft"
STATUS_TO_REVIEW = "to_review"
STATUS_READY = "ready"
STATUS_BLOCKED = "blocked"
STATUS_ARCHIVED = "archived"

RESTRICTION_INTERNAL = "internal"
RESTRICTION_RESTRICTED = "restricted"
RESTRICTION_CONFIDENTIAL = "confidential"

DIFFUSION_CS = "cs"
DIFFUSION_COPRO = "coproprietaires"
DIFFUSION_PUBLIC_AFTER_REDACTION = "public_after_redaction"

LEGAL_SCOPE_NOTICE = (
    "Note non juridique: constats, risques operationnels et pieces a verifier; "
    "validation par un professionnel si besoin."
)


STATUS_LABELS = {
    STATUS_DRAFT: "brouillon",
    STATUS_TO_REVIEW: "a relire",
    STATUS_READY: "pret a transmettre",
    STATUS_BLOCKED: "bloque",
    STATUS_ARCHIVED: "archive",
    "PREUVE_A_DEMANDER": "preuve a demander",
    "A_VERIFIER": "a verifier",
    "A_TRAITER": "a traiter",
    "CLOS": "clos",
}

RESTRICTION_LABELS = {
    RESTRICTION_INTERNAL: "interne au travail du conseil",
    RESTRICTION_RESTRICTED: "diffusion limitee",
    RESTRICTION_CONFIDENTIAL: "confidentiel",
}

DIFFUSION_LABELS = {
    DIFFUSION_CS: "conseil syndical",
    DIFFUSION_COPRO: "coproprietaires",
    DIFFUSION_PUBLIC_AFTER_REDACTION: "public apres masquage",
}

AG_DOCUMENT_TYPES = {"Convocation_AG", "PV_AG", "Annexe_AG"}
CONTENTIEUX_MARKERS = (
    "contentieux",
    "procedure",
    "recouvrement",
    "impaye",
    "avocat",
    "tribunal",
    "mise en demeure",
)


def build_agcontentieux_passation_view(instance: InstanceConfig, year: int) -> dict[str, Any]:
    """Build the AG/contentieux/passation UI model without registering a route."""
    documents = _read_rows(_safe_register(instance, "documents"))
    ag_rows = _read_rows(_safe_register(instance, "ag"))
    decision_rows = _read_rows(decisionops.decision_register_path(instance))

    ag_docs = [_document_card(row) for row in documents if _is_ag_document(row)]
    contentieux_docs = [_document_card(row) for row in documents if _is_contentieux_document(row)]
    questions = _question_cards(ag_rows, decision_rows, ag_docs, year)
    pieces = _piece_cards(ag_rows, ag_docs, year)
    dossiers = _dossier_cards(ag_rows, questions, pieces, year)
    contentieux_cases = _contentieux_cases(contentieux_docs, year)
    risk_notes = _risk_notes(contentieux_cases, year)
    evidence = _evidence_cards(ag_docs, contentieux_docs)
    pack = _passation_pack(dossiers, contentieux_cases, risk_notes, evidence, year)
    all_items = [*questions, *pieces, *contentieux_cases, *risk_notes, pack]
    status_counts = Counter(str(item.get("status", "")) for item in all_items if item.get("status"))
    restriction_counts = Counter(str(item.get("restriction", "")) for item in all_items if item.get("restriction"))

    return {
        "instance": {
            "id": instance.instance_id,
            "name": instance.display_name,
            "year": str(year),
        },
        "novice": {
            "title": "AG, contentieux, passation",
            "summary": (
                "Cette page aide a preparer une assemblee generale, suivre un dossier sensible et "
                "transmettre le travail sans perdre les preuves ni diffuser trop largement."
            ),
            "legal_notice": LEGAL_SCOPE_NOTICE,
            "empty_title": "Rien a preparer pour le moment",
            "empty_body": (
                "Deposez une convocation, une annexe, une note de suivi ou une piece source. "
                "La page affichera ensuite la question, la preuve, la restriction et la prochaine action."
            ),
        },
        "summary": {
            "questions": len(questions),
            "pieces": len(pieces),
            "contentieux": len(contentieux_cases),
            "risk_notes": len(risk_notes),
            "evidence": len(evidence),
            "packs": 1 if pack else 0,
            "open_due": sum(1 for item in all_items if item.get("due_on")),
            "ready": status_counts.get(STATUS_READY, 0),
            "is_empty": not any([questions, pieces, contentieux_cases, risk_notes, evidence]),
        },
        "labels": {
            "statuses": STATUS_LABELS,
            "restrictions": RESTRICTION_LABELS,
            "diffusions": DIFFUSION_LABELS,
        },
        "ag": {
            "dossiers": dossiers,
            "questions": questions,
            "pieces": pieces,
        },
        "contentieux": {
            "cases": contentieux_cases,
            "risk_notes": risk_notes,
        },
        "evidence": {
            "items": evidence,
            "sources_read": len(documents),
        },
        "passation": {
            "pack": pack,
            "checklist": [
                "Verifier les questions AG et les pieces de convocation.",
                "Limiter le dossier contentieux au factuel et aux sources.",
                "Garder la note de risque en note non juridique.",
                "Nommer le public autorise avant tout export.",
                "Transmettre les actions ouvertes avec echeance et preuve attendue.",
            ],
        },
        "counts": {
            "by_status": [
                {"status": key, "label": _status_label(key), "count": count}
                for key, count in sorted(status_counts.items())
            ],
            "by_restriction": [
                {"restriction": key, "label": _restriction_label(key), "count": count}
                for key, count in sorted(restriction_counts.items())
            ],
        },
    }


def _dossier_cards(
    ag_rows: list[dict[str, str]],
    questions: list[dict[str, Any]],
    pieces: list[dict[str, Any]],
    year: int,
) -> list[dict[str, Any]]:
    if not ag_rows and not (questions or pieces):
        return []
    rows = ag_rows or [{"ag_id": f"AG-{year}", "detected_date": "", "notes": ""}]
    dossiers: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        ag_id = row.get("ag_id") or f"AG-{year}-{index}"
        dossiers.append(
            {
                "id": ag_id,
                "title": f"Preparation {ag_id}",
                "ag_date": row.get("detected_date") or "",
                "questions": [item for item in questions if item.get("dossier_id") == ag_id] or questions[:3],
                "pieces": [item for item in pieces if item.get("dossier_id") == ag_id] or pieces[:5],
                "source_ref": row.get("doc_id") or "",
                "restriction": RESTRICTION_RESTRICTED,
                "restriction_label": _restriction_label(RESTRICTION_RESTRICTED),
                "diffusion": DIFFUSION_CS,
                "diffusion_label": _diffusion_label(DIFFUSION_CS),
                "status": STATUS_TO_REVIEW,
                "status_label": _status_label(STATUS_TO_REVIEW),
                "next_action": "Relire ordre du jour, questions et annexes avant diffusion.",
                "due_on": _default_due(year),
                "notes": row.get("notes") or "Dossier AG pret a enrichir avec les preuves.",
            }
        )
    return dossiers


def _question_cards(
    ag_rows: list[dict[str, str]],
    decision_rows: list[dict[str, str]],
    ag_docs: list[dict[str, Any]],
    year: int,
) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for index, row in enumerate(decision_rows, start=1):
        ag_id = row.get("ag_id") or f"AG-{year}"
        questions.append(
            {
                "id": row.get("decision_action_id") or f"question-{index}",
                "dossier_id": ag_id,
                "title": row.get("decision_text") or row.get("resolution_ref") or "Question AG a clarifier",
                "objective": row.get("action_attendue") or "Transformer le point AG en action suivie.",
                "source_ref": row.get("source_doc_id") or row.get("source_file") or "",
                "proof_ref": row.get("preuve_attendue") or row.get("proof_doc_ids") or "",
                "restriction": RESTRICTION_RESTRICTED,
                "restriction_label": _restriction_label(RESTRICTION_RESTRICTED),
                "diffusion": DIFFUSION_CS,
                "diffusion_label": _diffusion_label(DIFFUSION_CS),
                "status": row.get("statut") or STATUS_TO_REVIEW,
                "status_label": _status_label(row.get("statut") or STATUS_TO_REVIEW),
                "next_action": row.get("action_attendue") or "Rattacher la question a une piece et a une preuve.",
                "due_on": row.get("echeance") or _default_due(year),
            }
        )
    if questions:
        return questions
    for index, row in enumerate(ag_rows, start=1):
        ag_id = row.get("ag_id") or f"AG-{year}-{index}"
        questions.append(_question_from_ag_row(row, ag_id, index, year))
    if questions:
        return questions
    if ag_docs:
        doc = ag_docs[0]
        return [
            {
                "id": "question-convocation",
                "dossier_id": f"AG-{year}",
                "title": "Questions a preparer depuis la convocation",
                "objective": "Identifier les points a demander ou verifier avant l'AG.",
                "source_ref": doc["id"],
                "proof_ref": doc["title"],
                "restriction": RESTRICTION_RESTRICTED,
                "restriction_label": _restriction_label(RESTRICTION_RESTRICTED),
                "diffusion": DIFFUSION_CS,
                "diffusion_label": _diffusion_label(DIFFUSION_CS),
                "status": STATUS_TO_REVIEW,
                "status_label": _status_label(STATUS_TO_REVIEW),
                "next_action": "Lire la convocation et lister les questions du conseil syndical.",
                "due_on": _default_due(year),
            }
        ]
    return []


def _question_from_ag_row(row: dict[str, str], ag_id: str, index: int, year: int) -> dict[str, Any]:
    missing_annex = (row.get("missing_annex_signals") or "").upper() == "YES"
    title = "Pieces de convocation a verifier" if missing_annex else "Question AG a preparer"
    return {
        "id": f"{ag_id}-question-{index}",
        "dossier_id": ag_id,
        "title": title,
        "objective": row.get("notes") or "Transformer la lecture AG en questions simples.",
        "source_ref": row.get("doc_id") or row.get("file_name") or "",
        "proof_ref": row.get("file_name") or "",
        "restriction": RESTRICTION_RESTRICTED,
        "restriction_label": _restriction_label(RESTRICTION_RESTRICTED),
        "diffusion": DIFFUSION_CS,
        "diffusion_label": _diffusion_label(DIFFUSION_CS),
        "status": STATUS_TO_REVIEW,
        "status_label": _status_label(STATUS_TO_REVIEW),
        "next_action": "Verifier les annexes et formuler la question en langage court.",
        "due_on": row.get("detected_date") or _default_due(year),
    }


def _piece_cards(ag_rows: list[dict[str, str]], ag_docs: list[dict[str, Any]], year: int) -> list[dict[str, Any]]:
    ag_id_by_doc = {row.get("doc_id", ""): row.get("ag_id", f"AG-{year}") for row in ag_rows}
    pieces: list[dict[str, Any]] = []
    for index, doc in enumerate(ag_docs, start=1):
        pieces.append(
            {
                "id": f"piece-{doc['id'] or index}",
                "dossier_id": ag_id_by_doc.get(str(doc["id"]), f"AG-{year}"),
                "title": doc["title"],
                "source_ref": doc["id"],
                "proof_ref": doc["sha256_short"],
                "restriction": RESTRICTION_RESTRICTED,
                "restriction_label": _restriction_label(RESTRICTION_RESTRICTED),
                "diffusion": DIFFUSION_COPRO,
                "diffusion_label": _diffusion_label(DIFFUSION_COPRO),
                "status": STATUS_TO_REVIEW,
                "status_label": _status_label(STATUS_TO_REVIEW),
                "next_action": "Controler que la version peut etre jointe ou citee.",
                "due_on": doc.get("date") or _default_due(year),
            }
        )
    return pieces


def _contentieux_cases(contentieux_docs: list[dict[str, Any]], year: int) -> list[dict[str, Any]]:
    return [
        {
            "id": f"contentieux-{index}",
            "title": doc["title"],
            "matter": "dossier factuel restreint",
            "source_ref": doc["id"],
            "proof_ref": doc["sha256_short"] or doc["title"],
            "restriction": RESTRICTION_CONFIDENTIAL,
            "restriction_label": _restriction_label(RESTRICTION_CONFIDENTIAL),
            "diffusion": DIFFUSION_CS,
            "diffusion_label": _diffusion_label(DIFFUSION_CS),
            "status": STATUS_TO_REVIEW,
            "status_label": _status_label(STATUS_TO_REVIEW),
            "next_action": "Rassembler les faits dates et les pieces sans qualifier juridiquement.",
            "due_on": doc.get("date") or _default_due(year),
        }
        for index, doc in enumerate(contentieux_docs, start=1)
    ]


def _risk_notes(contentieux_cases: list[dict[str, Any]], year: int) -> list[dict[str, Any]]:
    return [
        {
            "id": f"note-risque-{case['id']}",
            "title": f"Note de risque non juridique - {case['title']}",
            "observations": [
                "Pieces et dates a verifier avant toute conclusion.",
                "Diffusion limitee au public autorise.",
            ],
            "risk_signals": [
                "echeance a surveiller",
                "preuve source a rattacher",
            ],
            "scope_notice": LEGAL_SCOPE_NOTICE,
            "source_ref": case["source_ref"],
            "proof_ref": case["proof_ref"],
            "restriction": RESTRICTION_CONFIDENTIAL,
            "restriction_label": _restriction_label(RESTRICTION_CONFIDENTIAL),
            "diffusion": DIFFUSION_CS,
            "diffusion_label": _diffusion_label(DIFFUSION_CS),
            "status": STATUS_TO_REVIEW,
            "status_label": _status_label(STATUS_TO_REVIEW),
            "next_action": "Faire relire la note avant toute decision sensible.",
            "due_on": case.get("due_on") or _default_due(year),
        }
        for case in contentieux_cases
    ]


def _evidence_cards(ag_docs: list[dict[str, Any]], contentieux_docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for doc in ag_docs:
        cards.append(_evidence_card(doc, RESTRICTION_RESTRICTED, DIFFUSION_COPRO))
    for doc in contentieux_docs:
        cards.append(_evidence_card(doc, RESTRICTION_CONFIDENTIAL, DIFFUSION_CS))
    return cards


def _evidence_card(doc: dict[str, Any], restriction: str, diffusion: str) -> dict[str, Any]:
    return {
        "id": f"preuve-{doc['id']}",
        "title": doc["title"],
        "source_ref": doc["id"],
        "source_kind": doc["kind"],
        "source_hash": doc["sha256_short"],
        "captured_on": doc["date"],
        "restriction": restriction,
        "restriction_label": _restriction_label(restriction),
        "diffusion": diffusion,
        "diffusion_label": _diffusion_label(diffusion),
        "status": STATUS_TO_REVIEW,
        "status_label": _status_label(STATUS_TO_REVIEW),
        "next_action": "Verifier la source puis rattacher la preuve au bon dossier.",
        "due_on": doc["date"],
    }


def _passation_pack(
    dossiers: list[dict[str, Any]],
    contentieux_cases: list[dict[str, Any]],
    risk_notes: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    year: int,
) -> dict[str, Any]:
    restriction = (
        RESTRICTION_CONFIDENTIAL
        if contentieux_cases or risk_notes
        else RESTRICTION_RESTRICTED
    )
    return {
        "id": f"passation-ag-contentieux-{year}",
        "title": f"Pack passation AG/contentieux {year}",
        "handover_scope": "questions AG, pieces de convocation, dossiers sensibles et actions ouvertes",
        "dossier_ag_ids": [item["id"] for item in dossiers],
        "contentieux_case_ids": [item["id"] for item in contentieux_cases],
        "legal_risk_note_ids": [item["id"] for item in risk_notes],
        "evidence_refs": [item["id"] for item in evidence],
        "open_points": _open_points(dossiers, contentieux_cases, risk_notes, evidence),
        "restriction": restriction,
        "restriction_label": _restriction_label(restriction),
        "diffusion": DIFFUSION_CS,
        "diffusion_label": _diffusion_label(DIFFUSION_CS),
        "status": STATUS_DRAFT,
        "status_label": _status_label(STATUS_DRAFT),
        "next_action": "Completer les points ouverts puis transmettre avec les limites de diffusion.",
        "due_on": _default_due(year),
    }


def _open_points(
    dossiers: list[dict[str, Any]],
    contentieux_cases: list[dict[str, Any]],
    risk_notes: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> list[str]:
    points = []
    if dossiers:
        points.append("Questions AG et pieces de convocation a relire.")
    if contentieux_cases:
        points.append("Dossier contentieux a garder factuel et restreint.")
    if risk_notes:
        points.append("Note de risque non juridique a faire relire.")
    if evidence:
        points.append("Preuves et sources a rattacher avant export.")
    return points or ["Aucun element charge: pack pret a recevoir les prochaines pieces."]


def _document_card(row: dict[str, str]) -> dict[str, Any]:
    sha = row.get("sha256", "")
    return {
        "id": row.get("doc_id") or row.get("file_name") or "",
        "title": row.get("file_name") or row.get("doc_id") or "Piece sans nom",
        "kind": row.get("document_type") or row.get("source_kind") or "document",
        "date": row.get("suspected_date") or row.get("first_seen", "")[:10],
        "sha256_short": sha[:12],
        "restriction_reasons": row.get("restriction_reasons") or "",
    }


def _is_ag_document(row: dict[str, str]) -> bool:
    document_type = row.get("document_type", "")
    haystack = " ".join(
        [
            document_type,
            row.get("lot", ""),
            row.get("file_name", ""),
            row.get("notes", ""),
        ]
    ).lower()
    return document_type in AG_DOCUMENT_TYPES or "convocation" in haystack or "assemblee" in haystack


def _is_contentieux_document(row: dict[str, str]) -> bool:
    haystack = " ".join(
        [
            row.get("document_type", ""),
            row.get("lot", ""),
            row.get("file_name", ""),
            row.get("restriction_reasons", ""),
            row.get("notes", ""),
        ]
    ).lower()
    return any(marker in haystack for marker in CONTENTIEUX_MARKERS)


def _status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status.lower().replace("_", " ") if status else "a completer")


def _restriction_label(restriction: str) -> str:
    return RESTRICTION_LABELS.get(restriction, restriction)


def _diffusion_label(diffusion: str) -> str:
    return DIFFUSION_LABELS.get(diffusion, diffusion)


def _read_rows(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    _, rows = read_csv(path)
    return rows


def _safe_register(instance: InstanceConfig, name: str) -> Path | None:
    try:
        return instance.register(name)
    except KeyError:
        return None


def _default_due(year: int) -> str:
    return f"{year}-06-30"


def flatten_work_items(view: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all actionable cards for static tests or a future route adapter."""
    return [
        *view["ag"]["questions"],
        *view["ag"]["pieces"],
        *view["contentieux"]["cases"],
        *view["contentieux"]["risk_notes"],
        view["passation"]["pack"],
    ]
