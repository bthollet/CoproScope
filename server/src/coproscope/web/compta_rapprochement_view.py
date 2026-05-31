from __future__ import annotations

import hashlib
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import quote

from fastapi import Request as FastAPIRequest

from ..core.common import append_csv_row, read_csv
from .compta_rapprochement_fallback import fallback_rows as _fallback_rows
from .compta_rapprochement_fallback import shell_model as _shell_model


READ_MODEL_NAME = "compta_reconciliation_queue_v1"
VALIDATION_FIELDS = [
    "validation_id",
    "created_at",
    "exercice",
    "review_id",
    "decision",
    "decision_label",
    "note",
    "actor_label",
    "source",
    "read_model",
]

DECISION_LABELS = {
    "validated": "Relu par le conseil syndical",
    "validated_with_reserve": "Reserve visible",
    "question_needed": "Question syndic a poser",
    "decision_needed": "Decision ou devis demande",
    "rejected": "Ecarte du rapprochement",
}

DECISION_ACTIONS = [
    {"key": "validated", "label": "Marquer comme relu par le conseil", "tone": "ok"},
    {"key": "validated_with_reserve", "label": "Garder une reserve visible", "tone": "warn"},
    {"key": "question_needed", "label": "Preparer question syndic", "tone": "warn"},
    {"key": "decision_needed", "label": "Demander decision ou devis", "tone": "warn"},
    {"key": "rejected", "label": "Ecarter ce rapprochement", "tone": "danger"},
]

FORBIDDEN_PATTERNS = (
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/][^\s|,;`)]*"),
    re.compile(r"file://\S+", re.IGNORECASE),
    re.compile(r"(?:^|[\s`'\"(])(?:raw|restricted|logs|private|system)[\\/]\S*", re.IGNORECASE),
    re.compile(r"(?:token|secret|password|prompt|oauth)\s*[:=]\s*\S+", re.IGNORECASE),
)


def register_compta_rapprochement_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from fastapi import HTTPException
    from fastapi.responses import RedirectResponse

    @app.get("/comptes/rapprochement", response_class=html_response)
    def comptes_rapprochement(request: FastAPIRequest):
        require_token(request)
        view = build_compta_reconciliation_view(
            instance=getattr(app.state, "instance", None),
            year=year,
            selected=request.query_params.get("selected"),
        )
        return templates.TemplateResponse(
            request=request,
            name="compta_rapprochement.html",
            context=context(request, "accounting", model=view["shell_model"], rapprochement=view),
        )

    @app.post("/comptes/rapprochement/validation")
    async def comptes_rapprochement_validation(request: FastAPIRequest):
        require_token(request)
        form = await request.form()
        review_id = _review_id(form.get("review_id"))
        if not review_id:
            raise HTTPException(status_code=422, detail="Ligne de rapprochement invalide.")
        decision = _decision_key(form.get("decision"))
        if not decision:
            raise HTTPException(status_code=422, detail="Decision de validation invalide.")
        note = _public_text(form.get("note"), limit=180)
        append_human_validation(getattr(app.state, "instance", None), year, review_id, decision, note)
        target = f"/comptes/rapprochement?selected={quote(review_id)}&validation={quote(decision)}"
        return RedirectResponse(url=_url_with_token(request, target), status_code=303)


def build_compta_reconciliation_view(
    instance: Any | None = None,
    year: int = 2025,
    selected: str | None = None,
) -> dict[str, Any]:
    if isinstance(instance, int) and year == 2025:
        year = instance
        instance = None
    review_rows = _review_rows(instance, year)
    source_label = "Synthese derivee" if review_rows else "Controle a preparer"
    if instance is None and not review_rows:
        review_rows = _fallback_rows(year)
        source_label = "FICTIF"

    validations = _latest_validations(instance, year)
    items = [_queue_item(row, index=index, validation=validations.get(_row_id(row, index)), source_label=source_label) for index, row in enumerate(review_rows, start=1)]
    items = sorted(items, key=_queue_sort_key)
    selected_id = _review_id(selected) or (items[0]["id"] if items else "")
    selected_item = next((item for item in items if item["id"] == selected_id), items[0] if items else None)
    counts = Counter(item["priority"] for item in items)
    validated_count = sum(1 for item in items if item["validation"])
    question_count = sum(1 for item in items if item["question_syndic"])
    open_count = sum(1 for item in items if not item["validation"] and item["priority"] != "OK")
    notice = (
        "File de validation issue des controles ComptaScope."
        if items and source_label != "FICTIF"
        else "Scenario FICTIF: file de demonstration, aucun envoi."
        if items
        else "Aucune ligne a controler: lancez ComptaScope ou importez une synthese derivee."
    )
    return {
        "title": "Controle des comptes",
        "work_title": "Ligne selectionnee et preuves",
        "headline": "Controle des comptes avec sources separees",
        "read_model_name": READ_MODEL_NAME,
        "eyebrow": "Factures, lignes comptables et decisions",
        "notice": notice,
        "status": {
            "label": "Controle humain ouvert" if open_count else "Aucun blocage ouvert",
            "summary": "Commencez par l'action proposee, puis verifiez les quatre sources.",
            "cta": "Ouvrir la file",
        },
        "summary": [
            _metric("A traiter avant assemblee", str(counts.get("P1", 0)), "Lignes sans faisceau suffisant."),
            _metric("A confirmer", str(counts.get("P2", 0)), "Candidats ou rapprochements ambigus."),
            _metric("Relues ou reservees", str(validated_count), "Traces locales du conseil."),
            _metric("Questions syndic", str(question_count), "Brouillons sans envoi automatique."),
        ],
        "definitions": [
            _entry("Comptabilite", "Ligne issue de l'etat des depenses ou d'une annexe comptable."),
            _entry("Banque", "Source non fournie dans le corpus actuel: aucun paiement n'est confirme."),
            _entry("Facture", "Piece fournisseur et montant TTC extraits ou confirmes."),
            _entry("Decision / devis", "Vote, devis, bon ou reserve qui justifie la depense."),
        ],
        "items": items,
        "selected": selected_item,
        "selected_id": selected_id,
        "actions": DECISION_ACTIONS,
        "status_counts": _status_counts(items),
        "shell_model": _shell_model(year),
    }


def append_human_validation(
    instance: Any | None,
    year: int,
    review_id: str,
    decision: str,
    note: str = "",
) -> Path | None:
    if instance is None:
        return None
    path = _validation_path(instance, year)
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    seed = f"{created_at}|{review_id}|{decision}|{note}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:10].upper()
    append_csv_row(
        path,
        VALIDATION_FIELDS,
        {
            "validation_id": f"VAL-{digest}",
            "created_at": created_at,
            "exercice": str(year),
            "review_id": review_id,
            "decision": decision,
            "decision_label": DECISION_LABELS[decision],
            "note": _public_text(note, limit=180),
            "actor_label": "Conseil syndical",
            "source": "ui_compta_rapprochement",
            "read_model": READ_MODEL_NAME,
        },
    )
    return path


def _review_rows(instance: Any | None, year: int) -> list[dict[str, str]]:
    accounting_dir = _accounting_dataset_dir(instance, year)
    if accounting_dir is None:
        return []
    _, rows = read_csv(accounting_dir / f"controle_comptes_guide_{year}.csv")
    return [dict(row) for row in rows]


def _latest_validations(instance: Any | None, year: int) -> dict[str, dict[str, str]]:
    path = _validation_path(instance, year)
    if path is None:
        return {}
    _, rows = read_csv(path)
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        review_id = _review_id(row.get("review_id"))
        decision = _decision_key(row.get("decision"))
        if review_id and decision:
            copied = dict(row)
            copied["decision"] = decision
            copied["decision_label"] = DECISION_LABELS[decision]
            copied["note"] = _public_text(row.get("note"), limit=180)
            latest[review_id] = copied
    return latest


def _queue_item(row: Mapping[str, Any], *, index: int, validation: Mapping[str, str] | None, source_label: str) -> dict[str, Any]:
    review_id = _row_id(row, index)
    priority = _priority(row)
    status_label = _status_label(row, priority, validation)
    supplier = _business_label(_first(row, "fournisseur", "supplier"), limit=64) or "Piece comptable a qualifier"
    invoice = _invoice_reference(_first(row, "numero_facture", "invoice_number"))
    amount = _money(_first(row, "ttc", "montant_depense", "amount"))
    question = _public_text(row.get("question_syndic"), limit=220)
    next_action = _public_text(row.get("prochaine_action"), limit=180) or _default_next_action(priority)
    return {
        "id": review_id,
        "priority": priority,
        "tone": _tone(priority, validation),
        "status_label": status_label,
        "title": supplier,
        "subtitle": _subtitle(invoice, amount, row),
        "amount": amount,
        "invoice": invoice or "reference facture a confirmer",
        "source_label": source_label,
        "href": f"/comptes/rapprochement?selected={quote(review_id)}",
        "cells": _cells(row, priority),
        "suggestion": {
            "strength": _strength(priority),
            "reason": _public_text(row.get("motif") or row.get("libelle_statut"), limit=220),
            "next_action": next_action,
            "summary_action": _summary_action(next_action),
        },
        "question_syndic": question,
        "copy_text": _public_text(row.get("bloc_copiable") or question, limit=360),
        "validation": dict(validation) if validation else None,
        "diffusion": "Conseil syndical seulement - a relire avant assemblee"
        if priority != "OK"
        else "Interne conseil - diffusable apres controle",
    }

def _cells(row: Mapping[str, Any], priority: str) -> list[dict[str, str]]:
    line_ref = _first(row, "ligne_depense_candidate", "reference_depense", "ecriture_candidate")
    accounting_status = "strong_match" if line_ref and priority == "OK" else "candidate" if line_ref else "missing_source"
    bank_ref = _first(row, "mouvement_bancaire", "bank_reference", "releve_bancaire")
    bank_status = "candidate" if bank_ref else "missing_source"
    doc_id = _review_id(row.get("doc_id"))
    invoice_amount = _money(_first(row, "ttc", "montant_depense", "amount"))
    invoice_status = "strong_match" if _first(row, "doc_id", "numero_facture", "fournisseur") else "missing_source"
    decision_status = _decision_cell_status(row, priority)
    return [
        _cell(
            "Comptabilite",
            accounting_status,
            _accounting_cell_label(row),
            _join_non_empty(
                ("Compte comptable propose", row.get("compte_candidate")),
                ("Reference", row.get("reference_depense")),
                ("Montant", row.get("montant_depense")),
            ),
        ),
        _cell(
            "Banque",
            bank_status,
            _public_text(bank_ref, limit=90) if bank_ref else "Banque non fournie",
            "Aucun extrait bancaire: paiement non confirme.",
        ),
        _cell(
            "Facture",
            invoice_status,
            _invoice_cell_label(row, doc_id),
            _invoice_cell_detail(row, doc_id),
            href=f"/documents/{quote(doc_id)}?source=compta&evidence=montant&value={quote(invoice_amount)}" if doc_id else "",
            action_label="Ouvrir la piece",
            primary_signal=f"Montant a retrouver: {invoice_amount} EUR" if invoice_amount else "",
        ),
        _cell(
            "Decision / devis",
            decision_status,
            _decision_cell_label(row, priority),
            _decision_cell_detail(row, priority),
        ),
    ]


def _invoice_cell_label(row: Mapping[str, Any], doc_id: str) -> str:
    label = _join_title(_business_label(_first(row, "fournisseur"), limit=48), _invoice_reference(_first(row, "numero_facture")))
    if label:
        return label
    if doc_id:
        return "Facture fournie"
    return "Facture a rattacher"


def _invoice_cell_detail(row: Mapping[str, Any], doc_id: str) -> str:
    return "Aucune piece facture directe dans le corpus actuel." if not doc_id else "DocOps: piece a controler."


def _accounting_cell_label(row: Mapping[str, Any]) -> str:
    label = _public_text(_first(row, "libelle_depense", "ecriture_candidate", "ligne_depense_candidate"), limit=90)
    if label and not _is_technical_reference(label):
        return label
    if _first(row, "ligne_depense_candidate", "reference_depense", "ecriture_candidate"):
        return "Ligne comptable possible"
    return "Ligne comptable a identifier"


def _cell(kind: str, status: str, label: str, detail: str, *, href: str = "", action_label: str = "", primary_signal: str = "") -> dict[str, str]:
    return {
        "kind": kind,
        "status": status,
        "status_label": {
            "strong_match": "Source disponible",
            "candidate": "A confirmer",
            "conflict": "Conflit a traiter",
            "missing_source": "Source manquante",
        }.get(status, "A verifier"),
        "label": _public_text(label, limit=90),
        "detail": _public_text(detail, limit=150),
        "href": href,
        "action_label": action_label,
        "primary_signal": _public_text(primary_signal, limit=80),
    }


def _decision_cell_status(row: Mapping[str, Any], priority: str) -> str:
    text = _row_text(row)
    if any(word in text for word in ("manquant", "manquante", "demander", "absence")) and any(
        word in text for word in ("decision", "devis", "commande", "vote")
    ):
        return "missing_source"
    if any(word in text for word in ("decision", "devis", "commande", "vote", "reception")):
        return "candidate"
    return "candidate" if priority == "OK" else "missing_source"


def _decision_cell_label(row: Mapping[str, Any], priority: str) -> str:
    if _decision_cell_status(row, priority) == "missing_source":
        return "Decision, devis ou reserve a rattacher"
    return "Justification a relire"


def _decision_cell_detail(row: Mapping[str, Any], priority: str) -> str:
    if priority == "OK":
        return "Aucun blocage detecte, trace humaine conservee."
    return "Vote, devis ou reserve a fournir." if _decision_cell_status(row, priority) == "missing_source" else "Relire vote, devis ou reserve avant conclusion."


def _status_label(row: Mapping[str, Any], priority: str, validation: Mapping[str, str] | None) -> str:
    if validation:
        return validation.get("decision_label", "") or DECISION_LABELS.get(validation.get("decision", ""), "Trace humaine")
    label = _public_text(row.get("libelle_statut"), limit=70)
    if label:
        return label.replace("avant AG", "avant assemblee").replace("rapport AG", "rapport d'assemblee")
    return {"P1": "A traiter avant assemblee", "P2": "A confirmer", "OK": "OK a relire"}.get(priority, "A verifier")


def _status_counts(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter(item.get("priority", "P2") for item in items)
    labels = {"P1": "A traiter", "P2": "A confirmer", "OK": "OK a relire"}
    return [{"key": key, "label": labels.get(key, key), "count": count} for key, count in counts.items() if count]


def _queue_sort_key(item: Mapping[str, Any]) -> tuple[int, int, str]:
    rank = {"P1": 0, "P2": 1, "OK": 2}.get(str(item.get("priority") or ""), 3)
    validated_rank = 1 if item.get("validation") else 0
    return rank, validated_rank, str(item.get("id") or "")


def _priority(row: Mapping[str, Any]) -> str:
    raw = str(row.get("priorite") or row.get("match_priority") or "").strip().upper()
    if raw in {"P0", "P1"}:
        return "P1"
    if raw == "OK":
        return "OK"
    if raw == "P2":
        return "P2"
    status = str(row.get("statut_rapprochement") or row.get("match_status") or "").upper()
    if status.startswith("MATCH_"):
        return "OK"
    if status.startswith("NON_"):
        return "P1"
    return "P2"


def _tone(priority: str, validation: Mapping[str, str] | None) -> str:
    if validation:
        decision = validation.get("decision")
        if decision == "rejected":
            return "danger"
        if decision in {"validated", "validated_with_reserve"}:
            return "ok" if decision == "validated" else "warn"
    return {"P1": "danger", "P2": "warn", "OK": "ok"}.get(priority, "info")


def _strength(priority: str) -> str:
    return {"P1": "Source manquante", "P2": "A confirmer", "OK": "Sources concordantes"}.get(priority, "A confirmer")


def _default_next_action(priority: str) -> str:
    if priority == "P1":
        return "Demander la piece ou le mouvement manquant avant assemblee."
    if priority == "P2":
        return "Confirmer le faisceau puis tracer avec ou sans reserve."
    return "Relire puis tracer si le conseil syndical confirme."


def _summary_action(text: str) -> str:
    lowered = text.lower()
    if "mouvement bancaire" in lowered or "bancaire" in lowered:
        return "Banque + decision."
    if "grand livre" in lowered or "annexe comptable" in lowered or "etat des depenses" in lowered:
        return "Etat depenses."
    if "fournisseur" in lowered:
        return "Fournisseur a confirmer."
    if "sources" in lowered:
        return "Sources a verifier."
    return _public_text(text, limit=34)


def _row_id(row: Mapping[str, Any], index: int) -> str:
    explicit = _review_id(row.get("review_id") or row.get("doc_id"))
    if explicit:
        return explicit
    digest = hashlib.sha256(str(sorted(row.items())).encode("utf-8")).hexdigest()[:8].upper()
    return f"REC-{index:03d}-{digest}"


def _review_id(value: Any) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "").strip())[:80].strip("-")
    return text if text and not _contains_private_marker(text) else ""


def _decision_key(value: Any) -> str:
    key = re.sub(r"[^a-z_]+", "_", str(value or "").strip().lower()).strip("_")
    return key if key in DECISION_LABELS else ""


def _url_with_token(request: Any, path: str) -> str:
    token = str(request.query_params.get("token") or "").strip()
    if not token:
        return path
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}token={quote(token)}"


def _accounting_dir(instance: Any | None) -> Path | None:
    if instance is None:
        return None
    try:
        return Path(instance.artifact("accounting_dir"))
    except (AttributeError, KeyError, TypeError, ValueError, OSError):
        return None


def _validation_path(instance: Any | None, year: int) -> Path | None:
    accounting_dir = _accounting_dataset_dir(instance, year)
    if accounting_dir is None:
        return None
    return accounting_dir / f"compta_human_validations_{year}.csv"


def _accounting_dataset_dir(instance: Any | None, year: int) -> Path | None:
    accounting_dir = _accounting_dir(instance)
    if accounting_dir is None:
        return None
    year_dir = accounting_dir / str(year)
    if (year_dir / f"controle_comptes_guide_{year}.csv").exists():
        return year_dir
    return accounting_dir


def _first(row: Mapping[str, Any], *fields: str) -> str:
    for field in fields:
        value = str(row.get(field) or "").strip()
        if value and not _is_empty_marker(value):
            return value
    return ""


def _is_empty_marker(value: Any) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "", str(value or "").strip().lower())
    return normalized in {"", "vid", "vide", "nan", "none", "null", "na", "nd"}


def _business_label(value: Any, *, limit: int) -> str:
    text = _public_text(value, limit=limit)
    if _is_empty_marker(text):
        return ""
    if text.lower() == "piece comptable":
        return ""
    if re.search(r"\.(?:pdf|docx?|xlsx?)$", text, re.IGNORECASE):
        return ""
    return "" if "_" in text and re.search(r"\b(?:devis|facture|annexe|etat)\b", text, re.IGNORECASE) else text


def _join_title(left: str, right: str) -> str:
    parts = [_public_text(left, limit=48), _public_text(right, limit=36)]
    return " - ".join(part for part in parts if part)


def _join_non_empty(*items: tuple[str, Any]) -> str:
    parts = []
    for label, value in items:
        text = _public_text(value, limit=70)
        if text:
            parts.append(f"{label}: {text}")
    return " | ".join(parts)


def _subtitle(invoice: str, amount: str, row: Mapping[str, Any]) -> str:
    parts = []
    if invoice:
        parts.append(f"Facture {invoice}")
    if amount:
        parts.append(f"{amount} EUR")
    if not parts and _review_id(row.get("doc_id")):
        parts.append("Piece disponible dans DocOps")
    return " - ".join(parts) or "Ligne a qualifier"


def _invoice_reference(value: Any) -> str:
    text = _public_text(value, limit=40)
    return "" if _is_technical_reference(text) else text


def _is_technical_reference(value: Any) -> bool:
    text = str(value or "").strip()
    normalized = text.rstrip(".").lower()
    return bool(
        re.match(r"^(?:doc|rec)-[a-z0-9_.-]+$", normalized)
        or normalized.endswith(".native")
        or re.match(r"^[a-f0-9]{10,}$", normalized)
    )


def _money(value: Any) -> str:
    text = str(value or "").strip().replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d{1,2})?", text)
    if not match:
        return _public_text(value, limit=28)
    try:
        return f"{float(match.group(0)):.2f}"
    except ValueError:
        return _public_text(value, limit=28)


def _metric(label: str, value: str, detail: str) -> dict[str, str]:
    return {"label": label, "value": value, "detail": detail}


def _entry(label: str, detail: str) -> dict[str, str]:
    return {"label": label, "detail": detail}


def _public_text(value: Any, *, limit: int) -> str:
    text = " ".join(str(value or "").split())
    for pattern in FORBIDDEN_PATTERNS:
        text = pattern.sub("[retire]", text)
    text = re.sub(
        r"#?\s*\d*[\s_-]*(?:devis|facture|annexe|etat)(?:[\s_.-]+[^\s,;:|()]+)*\.(?:pdf|docx?|xlsx?)",
        "piece comptable",
        text,
        flags=re.IGNORECASE,
    )
    tech_headers = r"\b(?:sha256,count,doc_ids,paths|date,document_type,count,doc_ids,examples)\b"
    text = re.sub(tech_headers, "piece comptable", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<!\w)[^\s,;:|()]+\.(?:pdf|docx?|xlsx?)(?!\w)", "piece comptable", text, flags=re.IGNORECASE)
    text = re.sub(r"\bfacture\s+(?:vid|vide)\b", "facture", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(raw|restricted|logs?|private|system|tokens?|secrets?|prompts?|oauth)\b", "[retire]", text, flags=re.IGNORECASE)
    text = re.sub(r"\bl[e']?\s+grand livre\b", "l'annexe comptable", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:ligne de )?grand livre\b", "annexe comptable", text, flags=re.IGNORECASE)
    text = re.sub(r"\bavant validation\b", "avant conclusion", text, flags=re.IGNORECASE)
    text = re.sub(r"\bavant de valider\b", "avant avis local", text, flags=re.IGNORECASE)
    text = text.strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}..."


def _contains_private_marker(value: str) -> bool:
    lowered = value.replace("\\", "/").lower()
    return any(marker in lowered for marker in ("file://", "raw/", "restricted/", "logs/", "private/", "system/")) or bool(
        re.search(r"(?<![a-z])[a-z]:/", lowered)
    )


def _row_text(row: Mapping[str, Any]) -> str:
    return " ".join(str(value or "") for value in row.values()).lower()
