from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import quote

from ..core.common import InstanceConfig, read_csv, relative_to
from ..modules import decisionops, incidentops
from .depot import export_catalog, read_deposit_manifests


STATUS_OPERATIONAL = "operationnel"
STATUS_PARTIAL = "partiel"
STATUS_WORKING = "en chantier"
STATUS_NOT_STARTED = "non demarre"
ACTION_EXPORT_FIELDS = [
    "id",
    "priority",
    "status",
    "domain",
    "source",
    "owner",
    "title",
    "detail",
    "next_step",
    "evidence",
    "href",
]
FORBIDDEN_UX_PUBLIC_TOKENS = {"raw", "restricted", "logs", "private"}
FORBIDDEN_UX_PUBLIC_ROOTS = {"users", "home", "var", "tmp", "etc", "opt", "root", "mnt", "volumes"}
UX_REDACTED_REFERENCE = "reference locale masquee"


class _JinjaItemsProxy:
    def __init__(self, parent: dict[str, Any]) -> None:
        self.parent = parent

    def __iter__(self):
        value = dict.__getitem__(self.parent, "items")
        return iter(value if isinstance(value, list) else [])

    def __call__(self):
        return dict.items(self.parent)


class _JinjaItemsDict(dict[str, Any]):
    def __getattribute__(self, name: str) -> Any:
        if name == "items" and dict.__contains__(self, "items"):
            return _JinjaItemsProxy(self)
        return dict.__getattribute__(self, name)


@dataclass(frozen=True)
class DataTable:
    path: Path
    fields: list[str]
    rows: list[dict[str, str]]

    @property
    def exists(self) -> bool:
        return self.path.exists()

    @property
    def count(self) -> int:
        return len(self.rows)


def _read_table(path: Path) -> DataTable:
    fields, rows = read_csv(path)
    return DataTable(path=path, fields=fields, rows=rows)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _rel(instance: InstanceConfig, path: Path) -> str:
    return relative_to(instance.instance_root, path)


def _safe_register(instance: InstanceConfig, name: str) -> Path | None:
    try:
        return instance.register(name)
    except KeyError:
        return None


def _safe_artifact(instance: InstanceConfig, name: str) -> Path | None:
    try:
        return instance.artifact(name)
    except KeyError:
        return None


def _counter(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(Counter(row.get(field, "") or "non renseigne" for row in rows))


def _clip(value: str, length: int = 120) -> str:
    normalized = " ".join((value or "").split())
    if len(normalized) <= length:
        return normalized
    return normalized[: length - 1].rstrip() + "..."


def _amount_value(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    cleaned = (
        text.replace("\u00a0", " ")
        .replace("EUR", "")
        .replace("eur", "")
        .replace("â‚¬", "")
        .replace(" ", "")
    )
    if "," in cleaned and cleaned.rfind(",") > cleaned.rfind("."):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    if cleaned in {"", "-", ".", "-."}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _amount_label(value: object, fallback: str = "Montant non charge") -> str:
    amount = _amount_value(value)
    if amount is None:
        return fallback
    return f"{amount:,.2f} EUR".replace(",", " ").replace(".", ",")


def _coerce_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value or "").strip().replace("\u00a0", " ").replace(" ", "")
    if not text:
        return 0
    try:
        return int(float(text.replace(",", ".")))
    except ValueError:
        return 0


def _status(has_data: bool, has_file: bool = False) -> str:
    if has_data:
        return STATUS_OPERATIONAL
    if has_file:
        return STATUS_PARTIAL
    return STATUS_WORKING


def _artifact(instance: InstanceConfig, label: str, path: Path | None, kind: str) -> dict[str, object]:
    if path is None:
        return {
            "label": label,
            "kind": kind,
            "exists": False,
            "count": 0,
            "path": "",
            "state": "absent",
        }
    fields, rows = read_csv(path) if path.suffix.lower() == ".csv" else ([], [])
    return {
        "label": label,
        "kind": kind,
        "exists": path.exists(),
        "count": len(rows),
        "path": _rel(instance, path),
        "state": "pret" if path.exists() else "a generer",
        "fields": fields,
    }


def _accounting_base(instance: InstanceConfig, year: int) -> Path:
    primary = instance.artifact("accounting_dir") / str(year)
    try:
        outputs = instance.root("outputs")
    except KeyError:
        return primary
    alternatives = [
        outputs / f"accounting_{year}_factures",
        primary,
    ]
    for candidate in alternatives:
        if (candidate / f"summary_{year}.json").exists() or (candidate / f"summary_{year}_controlled.json").exists():
            return candidate
    return primary


def _accounting_paths(instance: InstanceConfig, year: int) -> dict[str, Path]:
    base = _accounting_base(instance, year)
    controlled = base / f"summary_{year}_controlled.json"
    return {
        "base": base,
        "summary": controlled if controlled.exists() else base / f"summary_{year}.json",
        "invoice_evidence": base / f"invoice_evidence_{year}_controlled.csv"
        if (base / f"invoice_evidence_{year}_controlled.csv").exists()
        else base / f"invoice_evidence_{year}.csv",
        "invoice_anomalies": base / f"invoice_anomalies_{year}.csv",
        "ledger": base / f"ledger_reconstruction_{year}_controlled.csv"
        if (base / f"ledger_reconstruction_{year}_controlled.csv").exists()
        else base / f"ledger_reconstruction_{year}.csv",
        "expense_statement": base / f"expense_statement_lines_{year}_controlled.csv"
        if (base / f"expense_statement_lines_{year}_controlled.csv").exists()
        else base / f"expense_statement_lines_{year}.csv",
        "controls": base / f"accounting_controls_{year}_controlled.csv"
        if (base / f"accounting_controls_{year}_controlled.csv").exists()
        else base / f"accounting_controls_{year}.csv",
        "matches": base / f"invoice_expense_matches_{year}_controlled.csv"
        if (base / f"invoice_expense_matches_{year}_controlled.csv").exists()
        else base / f"invoice_expense_matches_{year}_explained.csv"
        if (base / f"invoice_expense_matches_{year}_explained.csv").exists()
        else base / f"invoice_expense_matches_{year}.csv",
        "non_matches": base / f"non_rapproches_prioritaires_{year}_explained.csv"
        if (base / f"non_rapproches_prioritaires_{year}_explained.csv").exists()
        else base / f"non_rapproches_prioritaires_{year}.csv",
        "priority_controls": base / f"controles_p1_{year}.csv",
        "aliases": base / f"supplier_alias_suggestions_{year}.csv",
        "supplier_due": base / f"supplier_due_diligence_controls_{year}.csv",
        "report": base / f"rapport_comptascope_{year}_explique.md"
        if (base / f"rapport_comptascope_{year}_explique.md").exists()
        else base / f"rapport_comptascope_{year}.md",
    }


def _privacy_paths(instance: InstanceConfig) -> dict[str, Path]:
    privacy_dir = _safe_artifact(instance, "privacy_dir") or instance.root("staging") / "privacy_dir"
    redacted_dir = _safe_artifact(instance, "redacted_dir") or instance.root("staging") / "redacted_dir"
    return {
        "screening": _safe_register(instance, "privacy_screening")
        or privacy_dir / "registre_screening_confidentialite.csv",
        "redactions": _safe_register(instance, "redactions")
        or privacy_dir / "registre_biffages.csv",
        "queue": privacy_dir / "file_biffage.csv",
        "report": instance.artifact("reports_dir") / "rapport_screening_confidentialite.md",
        "redacted_dir": redacted_dir,
    }


def _read_report(path: Path, max_chars: int = 8000) -> dict[str, str]:
    if not path.exists():
        return {"exists": False, "text": "", "html": ""}
    try:
        text = path.read_text(encoding="utf-8-sig")[:max_chars]
    except OSError:
        return {"exists": False, "text": "", "html": ""}
    escaped = html.escape(text)
    return {"exists": True, "text": text, "html": escaped}


def _module(label: str, status: str, detail: str, href: str) -> dict[str, str]:
    return {"label": label, "status": status, "detail": detail, "href": href}


def _priority(title: str, severity: str, detail: str, href: str) -> dict[str, str]:
    return {"title": title, "severity": severity or "info", "detail": detail, "href": href}


def _action(
    title: str,
    source: str,
    priority: str,
    detail: str,
    href: str,
    *,
    action_id: str = "",
    status: str = "a_traiter",
    domain: str = "general",
    domain_label: str = "General",
    owner: str = "Conseil syndical",
    next_step: str = "",
    evidence: str = "",
    channel: str = "",
) -> dict[str, str]:
    return {
        "id": action_id,
        "title": title,
        "source": source,
        "priority": priority or "P2",
        "detail": detail,
        "href": href,
        "status": status,
        "domain": domain,
        "domain_label": domain_label,
        "owner": owner,
        "next_step": next_step or detail,
        "evidence": evidence,
        "channel": channel,
    }


def _priority_for(row: dict[str, str], default: str = "P2") -> str:
    return row.get("match_priority") or row.get("severity") or row.get("priority") or default


def _question_from_non_match(row: dict[str, str]) -> dict[str, str]:
    supplier = row.get("fournisseur") or "fournisseur non renseigne"
    invoice = row.get("numero_facture") or row.get("doc_id") or "piece non renseignee"
    amount = row.get("ttc")
    status = row.get("match_status", "")
    if status == "NON_RAPPROCHE":
        question = (
            f"Pouvez-vous indiquer a quelle ligne de l'etat des depenses rattacher la facture {invoice} "
            f"de {supplier}{f' ({amount} EUR)' if amount else ''}, ou transmettre la piece/ventilation manquante ?"
        )
    elif "MONTANT_AMBIGU" in status or "REFERENCE_AMBIGUE" in status:
        question = (
            f"Pouvez-vous confirmer le rattachement exact de la facture {invoice} de {supplier}"
            f"{f' ({amount} EUR)' if amount else ''}, avec la reference comptable ou la ventilation retenue ?"
        )
    else:
        question = (
            f"Pouvez-vous confirmer le traitement comptable de la facture {invoice} de {supplier}"
            f"{f' ({amount} EUR)' if amount else ''} et fournir l'element de preuve associe ?"
        )
    return {
        "priority": _priority_for(row, "P2"),
        "source": "non_rapproches_prioritaires",
        "title": f"{supplier} - {invoice}",
        "question": question,
        "reason": row.get("match_reason") or row.get("next_action") or status,
    }


def _question_from_control(row: dict[str, str]) -> dict[str, str]:
    evidence = row.get("evidence") or row.get("doc_id") or "piece concernee"
    control = row.get("control") or "controle comptable"
    if "DECISION" in control:
        question = (
            f"Pouvez-vous transmettre la decision, le devis, le service fait ou la reception permettant "
            f"de justifier la depense suivante : {evidence} ?"
        )
    else:
        question = f"Pouvez-vous transmettre les justificatifs attendus pour le controle `{control}` : {evidence} ?"
    return {
        "priority": _priority_for(row, "P1"),
        "source": "controles_p1",
        "title": control,
        "question": question,
        "reason": row.get("action") or row.get("status") or "Piece attendue.",
    }


def _question_from_anomaly(row: dict[str, str]) -> dict[str, str]:
    supplier = row.get("fournisseur") or "fournisseur non renseigne"
    invoice = row.get("numero_facture") or row.get("doc_id") or "piece non renseignee"
    anomaly = row.get("anomaly") or row.get("evidence") or "anomalie facture"
    question = (
        f"Pouvez-vous confirmer le traitement de la facture {invoice} de {supplier} "
        f"et transmettre le justificatif attendu pour le point suivant : {anomaly} ?"
    )
    return {
        "priority": _priority_for(row, "P2"),
        "source": "anomalies_facture",
        "title": f"{supplier} - {invoice}",
        "question": question,
        "reason": row.get("action") or row.get("status") or anomaly,
    }


def _syndic_questions(
    non_matches: DataTable,
    controls_p1: list[dict[str, str]],
    anomalies: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    questions = [_question_from_non_match(row) for row in non_matches.rows[:20]]
    questions.extend(_question_from_control(row) for row in controls_p1[:20])
    questions.extend(_question_from_anomaly(row) for row in (anomalies or [])[:20])
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "OK": 3}
    sorted_questions = sorted(questions, key=lambda row: priority_order.get(row.get("priority", "P2"), 2))[:30]
    return [
        {
            "priority": _priority_for(row, "P2"),
            "source": _public_text(row.get("source"), "controle_comptes"),
            "title": _public_text(row.get("title"), "Question syndic"),
            "question": _public_text(row.get("question"), "Pouvez-vous transmettre la piece ou la confirmation attendue ?"),
            "reason": _public_text(row.get("reason"), "Piece ou confirmation attendue."),
        }
        for row in sorted_questions
    ]


def _accounting_status_label(value: object, priority: str) -> str:
    normalized = str(value or priority or "").strip().upper()
    if normalized in {"P0", "P1", "BLOQUE", "A_TRAITER"}:
        return "A traiter"
    if normalized in {"P2", "A_CONFIRMER"}:
        return "A confirmer"
    if normalized in {"OK", "MATCH", "RAPPROCHE"} or normalized.startswith("MATCH"):
        return "Conforme avec preuve"
    return _public_text(value, "A verifier")


def _accounting_control_item(row: dict[str, str]) -> dict[str, str]:
    question = _question_from_control(row)
    priority = _priority_for(row, "P1")
    return {
        "priority": priority,
        "tone": priority.lower(),
        "source": "Controle comptable",
        "title": _public_text(row.get("control"), "Controle comptable prioritaire"),
        "status": _accounting_status_label(row.get("status") or row.get("severity"), priority),
        "reason": _public_text(row.get("action") or question["reason"], "Piece attendue."),
        "evidence": _public_text(row.get("evidence") or row.get("doc_id"), "Piece attendue"),
        "question": _public_text(question["question"], "Question syndic a preparer."),
        "next_step": "Demander la piece ou la justification au syndic, puis rattacher la reponse au point.",
    }


def _accounting_non_match_item(row: dict[str, str]) -> dict[str, str]:
    question = _question_from_non_match(row)
    priority = _priority_for(row, "P2")
    supplier = row.get("fournisseur") or row.get("supplier") or "Fournisseur non renseigne"
    invoice = row.get("numero_facture") or row.get("doc_id") or "piece non renseignee"
    amount = row.get("ttc")
    title = f"{supplier} - {invoice}"
    if amount:
        title = f"{title} ({amount} EUR)"
    return {
        "priority": priority,
        "tone": priority.lower(),
        "source": "Rapprochement facture",
        "title": _public_text(title, "Facture a rapprocher"),
        "status": _accounting_status_label(row.get("status_label") or row.get("match_status"), priority),
        "reason": _public_text(row.get("match_reason") or row.get("next_action"), "Rapprochement a clarifier."),
        "evidence": _public_text(row.get("chemin_piece") or row.get("doc_id") or invoice, "Piece attendue"),
        "question": _public_text(question["question"], "Question syndic a preparer."),
        "next_step": _public_text(row.get("next_action"), "Confirmer le rattachement comptable et conserver la preuve."),
    }


def _accounting_anomaly_item(row: dict[str, str]) -> dict[str, str]:
    question = _question_from_anomaly(row)
    priority = _priority_for(row, "P2")
    supplier = row.get("fournisseur") or "Fournisseur non renseigne"
    invoice = row.get("numero_facture") or row.get("doc_id") or "piece non renseignee"
    amount = row.get("ttc")
    title = f"{supplier} - {invoice}"
    if amount:
        title = f"{title} ({amount} EUR)"
    return {
        "priority": priority,
        "tone": priority.lower(),
        "source": "Anomalie facture",
        "title": _public_text(title, "Facture a verifier"),
        "status": _accounting_status_label(row.get("status") or row.get("severity"), priority),
        "reason": _public_text(row.get("anomaly") or row.get("evidence"), "Anomalie facture a clarifier."),
        "evidence": _public_text(row.get("evidence") or row.get("doc_id") or invoice, "Justificatif attendu"),
        "question": _public_text(question["question"], "Question syndic a preparer."),
        "next_step": _public_text(row.get("action"), "Demander le justificatif ou la confirmation au syndic."),
    }


def _accounting_ok_item(row: dict[str, str]) -> dict[str, str]:
    supplier = row.get("fournisseur") or row.get("supplier") or "Fournisseur non renseigne"
    invoice = row.get("numero_facture") or row.get("doc_id") or "piece non renseignee"
    statement = row.get("statement_reference") or row.get("statement_line_id") or row.get("statement_label")
    proof_parts = [part for part in [row.get("doc_id", ""), statement] if part]
    return {
        "priority": "OK",
        "tone": "ok",
        "source": "Rapprochement valide",
        "title": _public_text(f"{supplier} - {invoice}", "Facture rapprochee"),
        "status": _public_text(row.get("status_label") or row.get("match_status") or "OK", "OK"),
        "reason": _public_text(row.get("match_reason"), "Preuve locale suffisante."),
        "evidence": _public_text(" / ".join(proof_parts), "Rapprochement documente"),
        "question": "",
        "next_step": "Conserver le rattachement et citer cette preuve si le point revient en AG.",
    }


def _accounting_is_ok_match(row: dict[str, str]) -> bool:
    status = (row.get("match_status") or row.get("status") or "").upper()
    priority = _priority_for(row, "")
    return (
        priority == "OK"
        or status in {"MATCH", "OK", "RAPPROCHE"}
        or status.startswith("MATCH")
        or "RAPPROCH" in status
    )


def _accounting_summary_match_count(summary: dict[str, Any]) -> int:
    counts = summary.get("expense_match_counts")
    if not isinstance(counts, dict):
        return 0
    total = 0
    for status, count in counts.items():
        normalized = str(status or "").upper()
        if normalized in {"MATCH", "OK", "RAPPROCHE"} or normalized.startswith("MATCH") or "RAPPROCH" in normalized:
            total += _coerce_int(count)
    return total


def _accounting_row_amount(row: dict[str, str], *fields: str) -> float | None:
    for field in fields:
        amount = _amount_value(row.get(field))
        if amount is not None:
            return amount
    return None


def _accounting_row_key(row: dict[str, str], index: int, source: str) -> str:
    statement = row.get("statement_line_id")
    if statement:
        return f"statement:{statement}"
    for field in ["piece_doc_id", "doc_id", "source_doc_id"]:
        value = row.get(field)
        if value:
            return f"doc:{value}"
    for field in ["entry_id", "numero_facture", "reference", "statement_reference"]:
        value = row.get(field)
        if value:
            return f"ref:{value}"
    return f"{source}:{index}"


def _accounting_sum_unique(
    rows: list[dict[str, str]],
    *,
    amount_fields: tuple[str, ...],
    source: str,
) -> tuple[float, int]:
    total = 0.0
    count = 0
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        amount = _accounting_row_amount(row, *amount_fields)
        if amount is None:
            continue
        key = _accounting_row_key(row, index, source)
        if key in seen:
            continue
        seen.add(key)
        total += amount
        count += 1
    return total, count


def _accounting_total_charges(
    expense_statement: DataTable,
    ledger: DataTable,
    invoices: DataTable,
    matches: DataTable,
    non_matches: DataTable,
) -> tuple[float, bool]:
    total, count = _accounting_sum_unique(
        expense_statement.rows,
        amount_fields=("amount", "statement_amount", "ttc"),
        source="expense_statement",
    )
    if count:
        return total, True
    total, count = _accounting_sum_unique(
        ledger.rows,
        amount_fields=("debit", "amount", "statement_amount", "ttc"),
        source="ledger",
    )
    if count:
        return total, True
    fallback_rows = matches.rows + non_matches.rows + invoices.rows
    total, count = _accounting_sum_unique(
        fallback_rows,
        amount_fields=("statement_amount", "ttc", "montant_depense", "amount"),
        source="invoice",
    )
    return total, bool(count)


def _docops_actionable_model(matrix: DataTable, requests: DataTable) -> dict[str, object]:
    status_counts = _counter(matrix.rows, "status")
    present = [row for row in matrix.rows if row.get("status") == "PRESENT"]
    missing = [row for row in matrix.rows if row.get("status") in {"ABSENT", "A_DEMANDER", "MISSING"}]
    obsolete = [row for row in matrix.rows if row.get("status") == "OBSOLETE"]
    to_classify = [row for row in matrix.rows if row.get("status") in {"A_CLASSER", "A_VERIFIER_CLASSEMENT"}]
    to_request = requests.rows or [
        {
            "request_id": f"REQ-DOC-{row.get('proof_id', index)}",
            "source_ref": row.get("proof_id", ""),
            "priority": row.get("criticality", "P2"),
            "status": row.get("status", ""),
            "subject": row.get("expected_label", "") or row.get("document_type", ""),
            "expected_piece": row.get("expected_label", "") or row.get("document_type", ""),
            "reason": row.get("reason", ""),
            "related_doc_ids": row.get("matched_doc_ids", ""),
            "evidence_paths": row.get("evidence_paths", ""),
            "suggested_diligence": row.get("action", ""),
        }
        for index, row in enumerate(matrix.rows, start=1)
        if row.get("status") != "PRESENT"
    ]
    return {
        "matrix": matrix,
        "requests": requests,
        "status_counts": status_counts,
        "present": present[:20],
        "missing": missing[:20],
        "obsolete": obsolete[:20],
        "to_classify": to_classify[:20],
        "to_request": to_request[:30],
        "summary": {
            "total": matrix.count,
            "present": len(present),
            "missing": len(missing),
            "obsolete": len(obsolete),
            "to_classify": len(to_classify),
            "to_request": len(to_request),
        },
    }


def _decision_model(instance: InstanceConfig) -> dict[str, object]:
    register_path = decisionops.decision_register_path(instance)
    register = _read_table(register_path)
    report_path = instance.artifact("reports_dir") / "rapport_decisions_actions_preuves.md"
    rows = register.rows
    missing_proofs = [row for row in rows if row.get("statut") == "PREUVE_A_DEMANDER"]
    candidate_before_ag = [row for row in rows if row.get("statut") == "CANDIDAT_AVANT_AG"]
    proofs_to_verify = [row for row in rows if row.get("statut") == "PREUVE_LOCALE_A_VERIFIER"]
    due_rows = [row for row in rows if row.get("echeance")]
    open_rows = [
        row
        for row in rows
        if row.get("statut") not in {"", "OK", "TRAITE", "CLOTURE", "CLOS", "SANS_SUITE"}
    ]
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "OK": 9}
    visible_rows = sorted(
        rows,
        key=lambda row: (
            priority_order.get(row.get("priorite", "P2"), 2),
            row.get("echeance") or "9999-12-31",
            row.get("resolution_ref", ""),
        ),
    )
    return {
        "register": register,
        "rows": rows,
        "items": visible_rows[:40],
        "open_rows": open_rows[:40],
        "missing_proofs": missing_proofs[:40],
        "candidate_before_ag": candidate_before_ag[:40],
        "proofs_to_verify": proofs_to_verify[:40],
        "report": _read_report(report_path),
        "summary": {
            "total": register.count,
            "open": len(open_rows),
            "missing_proofs": len(missing_proofs),
            "candidate_before_ag": len(candidate_before_ag),
            "proofs_to_verify": len(proofs_to_verify),
            "with_due_date": len(due_rows),
            "statuses": _counter(rows, "statut"),
            "priorities": _counter(rows, "priorite"),
        },
        "artifacts": [
            _artifact(instance, "Registre decisions-actions-preuves", register_path, "csv"),
            _artifact(instance, "Rapport decisions-actions-preuves", report_path, "markdown"),
        ],
    }


def _incident_model(instance: InstanceConfig) -> dict[str, object]:
    register_path = incidentops.incident_register_path(instance)
    raw_register = _read_table(register_path)
    rows = [incidentops.normalize_incident(row) for row in raw_register.rows]
    register = DataTable(path=raw_register.path, fields=raw_register.fields, rows=rows)
    open_rows = [row for row in rows if incidentops.is_open_incident(row)]
    incomplete = [
        row
        for row in open_rows
        if not row.get("next_action") or not row.get("expected_closure_proof")
    ]
    report_dir = incidentops.incident_reports_dir(instance)
    open_export = report_dir / "incidents_ouverts.csv"
    report_path = report_dir / "rapport_incidentops.md"
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "OK": 9}
    open_sorted = sorted(
        open_rows,
        key=lambda row: (
            priority_order.get(row.get("priority", "P2"), 2),
            row.get("action_due_date") or "9999-12-31",
            row.get("incident_id", ""),
        ),
    )
    return {
        "register": register,
        "rows": rows,
        "items": rows[:40],
        "open_rows": open_sorted[:40],
        "incomplete": incomplete[:40],
        "report": _read_report(report_path),
        "summary": {
            "total": len(rows),
            "open": len(open_rows),
            "incomplete": len(incomplete),
            "closure_proofs_expected": len([row for row in open_rows if row.get("expected_closure_proof")]),
            "statuses": _counter(rows, "status"),
            "priorities": _counter(rows, "priority"),
        },
        "artifacts": [
            _artifact(instance, "Registre incidents", register_path, "csv"),
            _artifact(instance, "Incidents ouverts", open_export, "csv"),
            _artifact(instance, "Rapport IncidentOps", report_path, "markdown"),
        ],
    }


def _documents_model(instance: InstanceConfig) -> dict[str, object]:
    documents_path = _safe_register(instance, "documents")
    requests_path = _safe_register(instance, "requests")
    ag_path = _safe_register(instance, "ag")
    findings_path = _safe_register(instance, "findings")
    kpi_path = _safe_register(instance, "kpi")
    reports_dir = instance.artifact("reports_dir")

    documents = _read_table(documents_path) if documents_path else DataTable(Path(""), [], [])
    requests = _read_table(requests_path) if requests_path else DataTable(Path(""), [], [])
    ag = _read_table(ag_path) if ag_path else DataTable(Path(""), [], [])
    findings = _read_table(findings_path) if findings_path else DataTable(Path(""), [], [])
    kpi = _read_table(kpi_path) if kpi_path else DataTable(Path(""), [], [])
    missing_report = reports_dir / "rapport_completude_documentaire.md"
    ag_report = reports_dir / "rapport_ag_preparation.md"
    completeness_matrix_path = reports_dir / "matrice_completude_documentaire.csv"
    document_requests_path = reports_dir / "pieces_a_demander.csv"
    completeness_matrix = _read_table(completeness_matrix_path)
    document_requests = _read_table(document_requests_path)

    stale_or_missing = [
        row
        for row in findings.rows
        if row.get("severity") in {"P0", "P1", "P2"} or row.get("status") not in {"", "OK", "TRAITE"}
    ]
    return {
        "documents": documents,
        "requests": requests,
        "ag": ag,
        "findings": findings,
        "kpi": kpi,
        "missing_report": _read_report(missing_report),
        "ag_report": _read_report(ag_report),
        "document_types": _counter(documents.rows, "document_type"),
        "source_zones": _counter(documents.rows, "source_zone"),
        "stale_or_missing": stale_or_missing[:20],
        "actionable": _docops_actionable_model(completeness_matrix, document_requests),
        "artifacts": [
            _artifact(instance, "Registre documents", documents_path, "csv"),
            _artifact(instance, "Registre demandes", requests_path, "csv"),
            _artifact(instance, "Registre AG", ag_path, "csv"),
            _artifact(instance, "Constats", findings_path, "csv"),
            _artifact(instance, "KPI", kpi_path, "csv"),
            _artifact(instance, "Matrice completude", completeness_matrix_path, "csv"),
            _artifact(instance, "Pieces a demander", document_requests_path, "csv"),
            _artifact(instance, "Rapport completude", missing_report, "markdown"),
            _artifact(instance, "Rapport AG", ag_report, "markdown"),
        ],
    }


def _accounting_model(instance: InstanceConfig, year: int) -> dict[str, object]:
    paths = _accounting_paths(instance, year)
    summary = _read_json(paths["summary"])
    controls = _read_table(paths["controls"])
    priority_controls = _read_table(paths["priority_controls"])
    non_matches = _read_table(paths["non_matches"])
    matches = _read_table(paths["matches"])
    invoices = _read_table(paths["invoice_evidence"])
    anomalies = _read_table(paths["invoice_anomalies"])
    ledger = _read_table(paths["ledger"])
    expense_statement = _read_table(paths["expense_statement"])

    controls_p1 = priority_controls.rows or [
        row
        for row in controls.rows
        if row.get("severity") in {"P0", "P1"} or row.get("status") in {"P0", "P1", "BLOQUE", "A_TRAITER"}
    ]
    anomaly_p1 = [
        row
        for row in anomalies.rows
        if _priority_for(row, "P2") in {"P0", "P1"}
        or row.get("status") in {"P0", "P1", "BLOQUE", "A_TRAITER"}
    ]
    anomaly_p2 = [
        row
        for row in anomalies.rows
        if row not in anomaly_p1 and _priority_for(row, "P2") not in {"OK"}
    ]
    non_match_priorities = _counter(non_matches.rows, "match_priority")
    match_status = _counter(matches.rows, "match_status")
    supplier_counts = Counter(row.get("fournisseur") or row.get("supplier") or "non renseigne" for row in non_matches.rows)
    supplier_focus = [
        {"supplier": supplier, "count": count}
        for supplier, count in supplier_counts.most_common(8)
    ]
    blocking_non_matches = [
        row
        for row in non_matches.rows
        if _priority_for(row, "P2") in {"P0", "P1"}
    ]
    to_confirm_non_matches = [
        row
        for row in non_matches.rows
        if _priority_for(row, "P2") not in {"P0", "P1", "OK"}
    ]
    ok_matches = [row for row in matches.rows if _accounting_is_ok_match(row)]
    p1_items = [_accounting_control_item(row) for row in controls_p1[:12]]
    p1_items.extend(_accounting_non_match_item(row) for row in blocking_non_matches[:12])
    p1_items.extend(_accounting_anomaly_item(row) for row in anomaly_p1[:12])
    p2_items = [_accounting_non_match_item(row) for row in to_confirm_non_matches[:12]]
    p2_items.extend(_accounting_anomaly_item(row) for row in anomaly_p2[:12])
    ok_items = [_accounting_ok_item(row) for row in ok_matches[:12]]
    total_charges, has_total_charges = _accounting_total_charges(
        expense_statement,
        ledger,
        invoices,
        matches,
        non_matches,
    )
    if has_total_charges:
        summary["total_charges"] = round(total_charges, 2)
        if summary.get("total_charges_label") in {None, "", "A calculer", "Montant non charge"}:
            summary["total_charges_label"] = _amount_label(total_charges)
    if invoices.count or matches.count or non_matches.count:
        summary.setdefault("invoice_count", max(invoices.count, matches.count + non_matches.count))
    if ledger.count:
        summary.setdefault("entry_count", ledger.count)
    if expense_statement.count:
        summary.setdefault("expense_statement_line_count", expense_statement.count)
    summary_ok_count = _accounting_summary_match_count(summary)
    ok_count = max(len(ok_matches), summary_ok_count)
    if p1_items and p2_items:
        next_human_step = (
            "Traiter les P1 - A traiter avant AG: envoyer les questions P1 au syndic et rattacher chaque reponse comme preuve. "
            "A confirmer: rapprochement plausible pour les P2, a verifier avant validation."
        )
    elif p1_items:
        next_human_step = "Traiter les P1 - A traiter avant AG: envoyer les questions P1 au syndic et rattacher chaque reponse comme preuve."
    elif p2_items:
        next_human_step = "A confirmer: rapprochement plausible a verifier avec le syndic ou une piece avant de passer en OK."
    elif ok_items:
        next_human_step = "Preparer l'AG: garder les preuves OK sous la main pour expliquer les comptes."
    else:
        next_human_step = "Generer ou importer les sorties ComptaScope, puis relancer cette lecture guide."
    return {
        "paths": paths,
        "summary": summary,
        "controls": controls,
        "priority_controls": priority_controls,
        "controls_p1": controls_p1[:30],
        "syndic_questions": _syndic_questions(non_matches, controls_p1, anomaly_p1 + anomaly_p2),
        "supplier_focus": supplier_focus,
        "blocker_types": {
            "matches": match_status,
            "non_matches": _counter(non_matches.rows, "match_status"),
            "controls": _counter(controls.rows, "status"),
        },
        "before_ag": {
            "blocking": len(blocking_non_matches) + len(controls_p1) + len(anomaly_p1),
            "to_confirm": len(to_confirm_non_matches) + len(anomaly_p2),
            "ok": ok_count,
        },
        "guide": {
            "p1": p1_items[:12],
            "p2": p2_items[:12],
            "ok": ok_items[:12],
            "next_human_step": next_human_step,
        },
        "non_matches": non_matches,
        "matches": matches,
        "invoices": invoices,
        "anomalies": anomalies,
        "ledger": ledger,
        "expense_statement": expense_statement,
        "match_status": match_status,
        "non_match_priorities": non_match_priorities,
        "report": _read_report(paths["report"]),
        "artifacts": [
            _artifact(instance, "Synthese", paths["summary"], "json"),
            _artifact(instance, "Factures candidates", paths["invoice_evidence"], "csv"),
            _artifact(instance, "Anomalies facture", paths["invoice_anomalies"], "csv"),
            _artifact(instance, "Etat des depenses", paths["expense_statement"], "csv"),
            _artifact(instance, "Grand livre reconstruit", paths["ledger"], "csv"),
            _artifact(instance, "Controles comptables", paths["controls"], "csv"),
            _artifact(instance, "Controles P1", paths["priority_controls"], "csv"),
            _artifact(instance, "Rapprochements", paths["matches"], "csv"),
            _artifact(instance, "Non rapproches", paths["non_matches"], "csv"),
            _artifact(instance, "Rapport ComptaScope", paths["report"], "markdown"),
        ],
    }


def _privacy_model(instance: InstanceConfig) -> dict[str, object]:
    paths = _privacy_paths(instance)
    screening = _read_table(paths["screening"])
    redactions = _read_table(paths["redactions"])
    queue = _read_table(paths["queue"])
    review_rows = [
        row
        for row in screening.rows
        if row.get("remediation_priority") in {"P0", "P1", "P2"}
        or row.get("review_required")
        or row.get("privacy_review_status") in {"A_ARBITRER", "BLOQUE"}
    ]
    review_counts = _counter(screening.rows, "privacy_review_status")
    justification_required = [row for row in screening.rows if row.get("review_justification_required")]
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "": 4}
    queue_rows = sorted(
        queue.rows,
        key=lambda row: (
            priority_order.get(row.get("remediation_priority", ""), 4),
            row.get("queue_status", ""),
            row.get("file_name", "") or row.get("doc_id", ""),
        ),
    )
    return {
        "paths": paths,
        "screening": screening,
        "redactions": redactions,
        "queue": queue,
        "queue_rows": queue_rows,
        "review_rows": review_rows,
        "review_counts": review_counts,
        "review_summary": {
            "to_arbitrate": review_counts.get("A_ARBITRER", 0),
            "blocked": review_counts.get("BLOQUE", 0),
            "raw": review_counts.get("DIFFUSABLE_BRUT", 0),
            "redaction": review_counts.get("DIFFUSABLE_APRES_BIFFAGE", 0),
            "aggregation": review_counts.get("DIFFUSABLE_APRES_AGREGATION", 0),
            "justification_required": len(justification_required),
        },
        "priority_counts": _counter(screening.rows, "remediation_priority"),
        "queue_counts": _counter(queue.rows, "queue_status"),
        "report": _read_report(paths["report"]),
        "artifacts": [
            _artifact(instance, "Screening confidentialite", paths["screening"], "csv"),
            _artifact(instance, "File de biffage", paths["queue"], "csv"),
            _artifact(instance, "Registre biffages", paths["redactions"], "csv"),
            _artifact(instance, "Rapport screening", paths["report"], "markdown"),
            _artifact(instance, "Dossier biffe", paths["redacted_dir"], "directory"),
        ],
    }


def _deposits_model(instance: InstanceConfig) -> dict[str, object]:
    manifests = read_deposit_manifests(instance, limit=8)
    latest = manifests[0] if manifests else None
    return {
        "items": manifests,
        "latest": latest,
        "count": len(manifests),
        "exports": export_catalog(),
    }


def _stable_action_id(prefix: str, index: int, *parts: str) -> str:
    raw = "|".join(part for part in parts if part).strip()
    if raw:
        digest = hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:8].upper()
        return f"{prefix}-{digest}"
    return f"{prefix}-{index + 1:04d}"


def _accounting_actions(
    non_matches: DataTable,
    controls_p1: list[dict[str, str]],
    anomalies: DataTable | None = None,
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for index, row in enumerate(non_matches.rows):
        question = _question_from_non_match(row)
        supplier = row.get("fournisseur") or "Fournisseur non renseigne"
        invoice = row.get("numero_facture") or row.get("doc_id") or row.get("aliases") or "piece non renseignee"
        amount = row.get("ttc")
        title = f"{supplier} - {amount} EUR" if amount else supplier
        actions.append(
            _action(
                title,
                "ComptaScope",
                _priority_for(row, "P1"),
                row.get("match_reason") or row.get("next_action") or "Rapprochement a clarifier.",
                "/comptes",
                action_id=_stable_action_id("ACT-COMP-RAPP", index, row.get("doc_id", ""), invoice, supplier),
                status="a_demander",
                domain="comptes",
                domain_label="Comptes",
                owner="Syndic a solliciter",
                next_step=question["question"],
                evidence=row.get("chemin_piece") or row.get("doc_id") or invoice,
                channel="syndic",
            )
        )
    for index, row in enumerate(controls_p1):
        question = _question_from_control(row)
        control = row.get("control") or row.get("status") or "Controle comptable"
        evidence = row.get("evidence") or row.get("doc_id") or "piece concernee"
        actions.append(
            _action(
                control,
                "ComptaScope",
                _priority_for(row, "P1"),
                row.get("action") or row.get("status") or "Piece attendue.",
                "/comptes",
                action_id=_stable_action_id("ACT-COMP-CTRL", index, row.get("control_id", ""), row.get("doc_id", ""), evidence),
                status="a_demander",
                domain="comptes",
                domain_label="Comptes",
                owner="Syndic a solliciter",
                next_step=question["question"],
                evidence=evidence,
                channel="syndic",
            )
        )
    for index, row in enumerate((anomalies.rows if isinstance(anomalies, DataTable) else [])):
        priority = _priority_for(row, "P2")
        if priority == "OK":
            continue
        question = _question_from_anomaly(row)
        title = question["title"]
        evidence = row.get("evidence") or row.get("doc_id") or row.get("numero_facture") or "justificatif attendu"
        status = "a_demander" if priority in {"P0", "P1"} else "a_confirmer"
        actions.append(
            _action(
                title,
                "ComptaScope",
                priority,
                row.get("anomaly") or question["reason"] or "Justificatif comptable a clarifier.",
                "/comptes",
                action_id=_stable_action_id("ACT-COMP-ANOM", index, row.get("anomaly_id", ""), title, evidence),
                status=status,
                domain="comptes",
                domain_label="Comptes",
                owner="Syndic a solliciter",
                next_step=question["question"],
                evidence=evidence,
                channel="syndic",
            )
        )
    return actions


def _privacy_actions(review_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for index, row in enumerate(review_rows):
        title = row.get("file_name") or row.get("doc_id") or "Document"
        transformation = row.get("required_transformations") or row.get("publication_form") or "revue diffusion"
        review_status = row.get("privacy_review_status", "")
        action_status = "bloque" if review_status == "BLOQUE" else "a_revoir"
        actions.append(
            _action(
                title,
                "PrivacyOps",
                row.get("remediation_priority", "P2"),
                row.get("publication_blocker") or row.get("recommended_action") or "Revoir la politique de diffusion.",
                "/confidentialite",
                action_id=_stable_action_id("ACT-PRIV", index, row.get("doc_id", ""), row.get("original_path", ""), title),
                status=action_status,
                domain="confidentialite",
                domain_label="Confidentialite",
                owner="Conseil syndical",
                next_step=row.get("review_next_step") or row.get("recommended_action") or f"Verifier le niveau de diffusion : {transformation}.",
                evidence=row.get("original_path") or row.get("doc_id") or title,
            )
        )
    return actions


def _document_actions(stale_or_missing: list[dict[str, str]]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for index, row in enumerate(stale_or_missing):
        title = (
            row.get("title")
            or row.get("subject")
            or row.get("expected_piece")
            or row.get("expected_label")
            or row.get("document_type")
            or row.get("doc_id")
            or "Piece documentaire"
        )
        status = row.get("status") or "a_verifier"
        action_status = "a_demander" if status in {"ABSENT", "A_DEMANDER", "OBSOLETE"} else "a_verifier"
        actions.append(
            _action(
                title,
                "DocOps",
                row.get("severity") or row.get("priority") or row.get("criticality") or "P2",
                row.get("detail") or row.get("finding") or row.get("reason") or status or "Piece documentaire a verifier.",
                "/documents",
                action_id=_stable_action_id(
                    "ACT-DOC",
                    index,
                    row.get("request_id", ""),
                    row.get("finding_id", ""),
                    row.get("source_ref", ""),
                    row.get("doc_id", ""),
                    title,
                ),
                status=action_status,
                domain="documents",
                domain_label="Documents",
                owner="Conseil syndical",
                next_step=row.get("suggested_diligence")
                or row.get("next_action")
                or row.get("action")
                or row.get("diligence")
                or "Verifier la piece ou preparer une demande au syndic.",
                evidence=row.get("evidence")
                or row.get("evidence_paths")
                or row.get("related_doc_ids")
                or row.get("original_path")
                or row.get("doc_id")
                or title,
                channel="syndic" if "syndic" in " ".join(row.values()).lower() else "",
            )
        )
    return actions


def _decision_actions(decisions: dict[str, object]) -> list[dict[str, str]]:
    rows = decisions.get("open_rows")
    if not isinstance(rows, list):
        return []
    actions: list[dict[str, str]] = []
    status_map = {
        "PREUVE_A_DEMANDER": "a_demander",
        "CANDIDAT_AVANT_AG": "a_confirmer",
        "PREUVE_LOCALE_A_VERIFIER": "a_verifier",
    }
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        statut = row.get("statut", "")
        title = " - ".join(part for part in [row.get("resolution_ref", ""), _clip(row.get("decision_text", ""), 90)] if part)
        actions.append(
            _action(
                title or row.get("decision_action_id", "") or "Decision AG",
                "DecisionOps",
                row.get("priorite") or "P2",
                row.get("notes") or statut or "Decision a suivre.",
                "/chantiers",
                action_id=_stable_action_id(
                    "ACT-DEC",
                    index,
                    row.get("decision_action_id", ""),
                    row.get("ag_id", ""),
                    row.get("resolution_ref", ""),
                ),
                status=status_map.get(statut, "a_traiter"),
                domain="decisions",
                domain_label="Decisions",
                owner=row.get("responsable") or "Conseil syndical / syndic",
                next_step=row.get("action_attendue") or "Suivre la resolution jusqu'a sa preuve.",
                evidence=row.get("preuve_attendue") or row.get("proof_doc_ids") or row.get("source_file", ""),
                channel="syndic"
                if "syndic" in " ".join([row.get("responsable", ""), row.get("action_attendue", "")]).lower()
                else "",
            )
        )
    return actions


def _incident_actions(incidents: dict[str, object]) -> list[dict[str, str]]:
    rows = incidents.get("open_rows")
    if not isinstance(rows, list):
        return []
    actions: list[dict[str, str]] = []
    status_map = {
        "EN_ATTENTE_PREUVE": "a_demander",
        "A_CLOTURER": "a_demander",
        "EN_RELANCE": "a_demander",
        "A_QUALIFIER": "a_revoir",
        "NOUVEAU": "a_traiter",
        "EN_COURS": "a_traiter",
    }
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        status = incidentops.normalize_status(row.get("status"))
        title_parts = [row.get("lieu", ""), row.get("date_signalement", ""), _clip(row.get("description", ""), 80)]
        title = " - ".join(part for part in title_parts if part)
        actions.append(
            _action(
                title or row.get("incident_id", "") or "Incident ouvert",
                "IncidentOps",
                row.get("priority") or "P2",
                row.get("notes") or row.get("description") or status,
                "/chantiers",
                action_id=_stable_action_id(
                    "ACT-INC",
                    index,
                    row.get("incident_id", ""),
                    row.get("source_refs", ""),
                    row.get("description", ""),
                ),
                status=status_map.get(status, "a_traiter"),
                domain="incidents",
                domain_label="Incidents",
                owner=row.get("syndic_or_provider") or "Conseil syndical / syndic",
                next_step=row.get("next_action") or "Qualifier l'incident et demander une trace ecrite.",
                evidence=row.get("expected_closure_proof") or row.get("closure_proof_ref") or row.get("piece_ref", ""),
                channel="syndic"
                if "syndic" in " ".join([row.get("syndic_or_provider", ""), row.get("next_action", "")]).lower()
                else "",
            )
        )
    return actions


def _action_rank(action: dict[str, str]) -> tuple[int, int, str]:
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "OK": 4}
    status_rank = {
        "bloque": 0,
        "a_demander": 1,
        "a_traiter": 2,
        "a_revoir": 3,
        "a_confirmer": 4,
        "a_verifier": 5,
        "clos": 9,
    }
    return (
        priority_rank.get(action.get("priority", "P2"), 2),
        status_rank.get(action.get("status", "a_traiter"), 4),
        action.get("title", "").lower(),
    )


def _build_action_items(
    documents: dict[str, object],
    accounting: dict[str, object],
    privacy: dict[str, object],
    decisions: dict[str, object],
    incidents: dict[str, object],
) -> list[dict[str, str]]:
    non_matches = accounting.get("non_matches")
    controls_p1 = accounting.get("controls_p1")
    anomalies = accounting.get("anomalies")
    review_rows = privacy.get("review_rows")
    stale_or_missing = documents.get("stale_or_missing")
    actionable = documents.get("actionable")
    actions: list[dict[str, str]] = []
    if isinstance(non_matches, DataTable):
        actions.extend(_accounting_actions(non_matches, controls_p1 if isinstance(controls_p1, list) else [], anomalies if isinstance(anomalies, DataTable) else None))
    if isinstance(review_rows, list):
        actions.extend(_privacy_actions(review_rows))
    doc_rows: list[dict[str, str]] = []
    if isinstance(actionable, dict) and isinstance(actionable.get("to_request"), list):
        doc_rows.extend(row for row in actionable["to_request"] if isinstance(row, dict))
    if isinstance(stale_or_missing, list):
        doc_rows.extend(row for row in stale_or_missing if isinstance(row, dict))
    if doc_rows:
        actions.extend(_document_actions(doc_rows))
    actions.extend(_decision_actions(decisions))
    actions.extend(_incident_actions(incidents))
    return sorted(actions, key=_action_rank)


def _first_value(row: dict[str, str], *fields: str) -> str:
    for field in fields:
        value = row.get(field, "")
        if value:
            return value
    return ""


def _split_piece_refs(value: str) -> list[str]:
    refs: list[str] = []
    for chunk in (value or "").replace(";", ",").replace("|", ",").split(","):
        ref = chunk.strip()
        if not ref:
            continue
        refs.append(ref.split(":", 1)[0].strip())
    return [ref for ref in refs if ref]


def _first_document_for_piece(
    documents_by_id: dict[str, dict[str, str]],
    proof_ref: str,
) -> dict[str, str]:
    for ref in _split_piece_refs(proof_ref):
        if ref in documents_by_id:
            return documents_by_id[ref]
    return {}


def _piece_signature_badge(piece: str, row: dict[str, str] | None = None) -> str:
    haystack = " ".join(
        [
            piece or "",
            (row or {}).get("document_type", ""),
            (row or {}).get("expected_label", ""),
            (row or {}).get("notes", ""),
        ]
    ).lower()
    signature_markers = (" signe", " signee", "signature", "ordre de service", "devis vote")
    return "signature attendue" if any(marker in haystack for marker in signature_markers) else ""


def _workshop_tone(status: str, priority: str, has_local_proof: bool) -> str:
    normalized = (status or "").upper()
    if normalized in {"PRESENT", "OK", "TRAITE", "CLOTURE", "CLOS"}:
        return "ok"
    if has_local_proof and normalized in {"PREUVE_LOCALE_A_VERIFIER", "A_CLASSER", "A_VERIFIER_CLASSEMENT"}:
        return "p2"
    return (priority or "P2").lower()


def _workshop_requires_action(status: str) -> bool:
    normalized = (status or "").upper()
    return normalized not in {"", "PRESENT", "OK", "TRAITE", "CLOTURE", "CLOS", "SANS_SUITE"}


def _piece_workshop_item(
    *,
    source: str,
    point_type: str,
    point: str,
    piece: str,
    status: str,
    priority: str,
    action: str,
    next_step: str,
    proof_ref: str = "",
    point_id: str = "",
    request_id: str = "",
    href: str = "/pieces",
    privacy_badge: str = "",
    confidence_badge: str = "",
    signature_badge: str = "",
) -> dict[str, object]:
    has_local_proof = bool(proof_ref)
    requires_action = _workshop_requires_action(status)
    primary_action = next_step or action or "Qualifier le point puis rattacher la preuve."
    return {
        "source": source,
        "point_type": point_type,
        "point": point or "Point a qualifier",
        "point_id": point_id,
        "piece": piece or "Piece attendue",
        "status": status or "a_verifier",
        "priority": priority or "P2",
        "tone": _workshop_tone(status, priority, has_local_proof),
        "action": action or "Verifier la piece et son rattachement.",
        "next_step": primary_action,
        "primary_action": primary_action,
        "proof_ref": proof_ref,
        "proof_badge": "preuve locale" if has_local_proof else "preuve manquante",
        "privacy_badge": privacy_badge,
        "confidence_badge": confidence_badge,
        "signature_badge": signature_badge,
        "request_id": request_id,
        "href": href,
        "has_local_proof": has_local_proof,
        "requires_action": requires_action,
    }


def _piece_workshop_rank(item: dict[str, object]) -> tuple[int, int, str]:
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "OK": 9}
    status_rank = {
        "ABSENT": 0,
        "MISSING": 0,
        "A_DEMANDER": 0,
        "PREUVE_A_DEMANDER": 0,
        "EN_ATTENTE_PREUVE": 0,
        "OBSOLETE": 1,
        "A_CLASSER": 2,
        "A_VERIFIER_CLASSEMENT": 2,
        "PREUVE_LOCALE_A_VERIFIER": 2,
        "EN_COURS": 3,
        "PRESENT": 8,
        "OK": 9,
    }
    priority = str(item.get("priority", "P2")).upper()
    status = str(item.get("status", "")).upper()
    piece = str(item.get("piece", "")).lower()
    return (priority_rank.get(priority, 2), status_rank.get(status, 4), piece)


def _piece_workshop_model(
    documents: dict[str, object],
    decisions: dict[str, object],
    incidents: dict[str, object],
) -> dict[str, object]:
    items: list[dict[str, object]] = []
    documents_table = documents.get("documents")
    documents_by_id = (
        {
            row.get("doc_id", ""): row
            for row in documents_table.rows
            if isinstance(row, dict) and row.get("doc_id")
        }
        if isinstance(documents_table, DataTable)
        else {}
    )
    actionable = documents.get("actionable") if isinstance(documents.get("actionable"), dict) else {}
    matrix = actionable.get("matrix") if isinstance(actionable, dict) else None
    requests = actionable.get("to_request") if isinstance(actionable, dict) else []
    request_by_ref = {
        row.get("source_ref", ""): row
        for row in requests
        if isinstance(row, dict) and row.get("source_ref")
    }
    if isinstance(matrix, DataTable):
        for row in matrix.rows:
            proof_id = row.get("proof_id", "")
            request = request_by_ref.get(proof_id, {})
            status = request.get("status") or row.get("status", "")
            action = request.get("suggested_diligence") or row.get("action", "")
            proof_ref = _first_value(row, "evidence_paths", "matched_doc_ids")
            next_step = action
            if status == "PRESENT":
                next_step = "Rattacher cette preuve aux points ou actions qui la citent."
            elif proof_ref:
                next_step = "Verifier la piece locale puis confirmer son rattachement."
            document_row = _first_document_for_piece(documents_by_id, proof_ref)
            piece = row.get("expected_label") or row.get("document_type") or proof_id
            items.append(
                _piece_workshop_item(
                    source="DocOps",
                    point_type="Lot documentaire",
                    point=row.get("lot", ""),
                    point_id=proof_id,
                    piece=piece,
                    status=status,
                    priority=request.get("priority") or row.get("criticality", "P2"),
                    action=action,
                    next_step=next_step,
                    proof_ref=proof_ref,
                    request_id=request.get("request_id", ""),
                    href="/documents",
                    privacy_badge=document_row.get("privacy_review_status", ""),
                    confidence_badge=document_row.get("policy_confidence")
                    or document_row.get("classification_status", ""),
                    signature_badge=_piece_signature_badge(piece, document_row),
                )
            )

    decision_rows = decisions.get("open_rows")
    if isinstance(decision_rows, list):
        for row in decision_rows:
            if not isinstance(row, dict):
                continue
            point = " - ".join(
                part for part in [row.get("resolution_ref", ""), _clip(row.get("decision_text", ""), 120)] if part
            )
            status = row.get("statut", "")
            proof_ref = row.get("proof_doc_ids", "")
            next_step = row.get("action_attendue", "")
            if row.get("proof_doc_ids"):
                next_step = "Verifier la preuve locale et valider le suivi de decision."
            document_row = _first_document_for_piece(documents_by_id, proof_ref)
            piece = row.get("preuve_attendue") or row.get("proof_document_types") or "Preuve de decision"
            items.append(
                _piece_workshop_item(
                    source="DecisionOps",
                    point_type="Decision AG",
                    point=point,
                    point_id=row.get("decision_action_id", ""),
                    piece=piece,
                    status=status,
                    priority=row.get("priorite", "P2"),
                    action=row.get("action_attendue", ""),
                    next_step=next_step,
                    proof_ref=proof_ref,
                    href="/chantiers",
                    privacy_badge=document_row.get("privacy_review_status", ""),
                    confidence_badge=document_row.get("policy_confidence")
                    or document_row.get("classification_status", ""),
                    signature_badge=_piece_signature_badge(piece, document_row),
                )
            )

    incident_rows = incidents.get("open_rows")
    if isinstance(incident_rows, list):
        for row in incident_rows:
            if not isinstance(row, dict):
                continue
            status = incidentops.normalize_status(row.get("status"))
            point_parts = [row.get("incident_id", ""), row.get("lieu", ""), _clip(row.get("description", ""), 110)]
            proof_ref = row.get("closure_proof_ref", "")
            document_row = _first_document_for_piece(documents_by_id, proof_ref)
            piece = row.get("expected_closure_proof") or "Preuve de cloture"
            items.append(
                _piece_workshop_item(
                    source="IncidentOps",
                    point_type="Incident",
                    point=" - ".join(part for part in point_parts if part),
                    point_id=row.get("incident_id", ""),
                    piece=piece,
                    status=status,
                    priority=row.get("priority", "P2"),
                    action=row.get("next_action", ""),
                    next_step=row.get("next_action", ""),
                    proof_ref=proof_ref,
                    href="/chantiers",
                    privacy_badge=document_row.get("privacy_review_status", ""),
                    confidence_badge=document_row.get("policy_confidence")
                    or document_row.get("classification_status", ""),
                    signature_badge=_piece_signature_badge(piece, document_row),
                )
            )

    sorted_items = sorted(items, key=_piece_workshop_rank)
    by_source = _action_counter(
        [{"source": str(item.get("source", ""))} for item in sorted_items],
        "source",
    )
    by_status = _action_counter(
        [{"status": str(item.get("status", ""))} for item in sorted_items],
        "status",
    )
    return {
        "items": sorted_items[:80],
        "to_request": [item for item in sorted_items if item.get("requires_action") and not item.get("has_local_proof")][:30],
        "to_verify": [item for item in sorted_items if item.get("requires_action") and item.get("has_local_proof")][:30],
        "summary": {
            "total": len(sorted_items),
            "needs_action": len([item for item in sorted_items if item.get("requires_action")]),
            "with_local_proof": len([item for item in sorted_items if item.get("has_local_proof")]),
            "without_local_proof": len([item for item in sorted_items if not item.get("has_local_proof")]),
            "docops": by_source.get("DocOps", 0),
            "decisions": by_source.get("DecisionOps", 0),
            "incidents": by_source.get("IncidentOps", 0),
            "by_source": by_source,
            "by_status": by_status,
        },
    }


def _action_counter(actions: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(Counter(action.get(field, "") or "non renseigne" for action in actions))


def _scope_count(actions: list[dict[str, str]], scope: str) -> int:
    return len(
        [
            action
            for action in actions
            if action.get("domain") == scope
            or action.get("channel") == scope
            or action.get("source", "").lower() == scope
        ]
    )


def _action_summary(actions: list[dict[str, str]], preview_count: int) -> dict[str, object]:
    by_domain = _action_counter(actions, "domain")
    return {
        "total": len(actions),
        "preview_count": preview_count,
        "accounting": by_domain.get("comptes", 0),
        "privacy": by_domain.get("confidentialite", 0),
        "documents": by_domain.get("documents", 0),
        "decisions": by_domain.get("decisions", 0),
        "incidents": by_domain.get("incidents", 0),
        "by_domain": by_domain,
        "by_priority": _action_counter(actions, "priority"),
        "by_status": _action_counter(actions, "status"),
        "scope_counts": {
            "tous": len(actions),
            "comptes": _scope_count(actions, "comptes"),
            "confidentialite": _scope_count(actions, "confidentialite"),
            "documents": _scope_count(actions, "documents"),
            "decisions": _scope_count(actions, "decisions"),
            "incidents": _scope_count(actions, "incidents"),
            "syndic": _scope_count(actions, "syndic"),
            "ag": _scope_count(actions, "ag"),
        },
    }


def _cockpit_alerts(
    priorities: list[dict[str, str]],
    action_summary: dict[str, object],
    privacy: dict[str, object],
    piece_workshop: dict[str, object],
) -> list[dict[str, object]]:
    by_status = action_summary.get("by_status") if isinstance(action_summary.get("by_status"), dict) else {}
    privacy_summary = privacy.get("review_summary") if isinstance(privacy.get("review_summary"), dict) else {}
    workshop_summary = piece_workshop.get("summary") if isinstance(piece_workshop.get("summary"), dict) else {}
    alerts: list[dict[str, object]] = []
    if int(by_status.get("bloque", 0)):
        alerts.append(
            {
                "title": "Blocages a lever",
                "severity": "P0",
                "count": int(by_status.get("bloque", 0)),
                "detail": "Actions bloquees avant diffusion ou decision.",
                "href": "/actions?status=bloque",
            }
        )
    if int(by_status.get("a_demander", 0)):
        alerts.append(
            {
                "title": "Demandes au syndic",
                "severity": "P1",
                "count": int(by_status.get("a_demander", 0)),
                "detail": "Pieces, clarifications ou preuves a obtenir.",
                "href": "/actions?status=a_demander",
            }
        )
    if int(workshop_summary.get("with_local_proof") or 0):
        alerts.append(
            {
                "title": "Preuves locales a verifier",
                "severity": "P2",
                "count": int(workshop_summary.get("with_local_proof") or 0),
                "detail": "Preuves deja presentes mais a rattacher ou confirmer.",
                "href": "/pieces",
            }
        )
    if int(privacy_summary.get("blocked") or 0):
        alerts.append(
            {
                "title": "Diffusion bloquee",
                "severity": "P1",
                "count": int(privacy_summary.get("blocked") or 0),
                "detail": "Sorties a arbitrer avant partage.",
                "href": "/confidentialite",
            }
        )
    for priority in priorities[:3]:
        alerts.append({**priority, "count": ""})
    severity_rank = {"P0": 0, "P1": 1, "P2": 2, "OK": 4}
    return sorted(alerts, key=lambda row: severity_rank.get(str(row.get("severity", "P2")), 2))[:6]


def _evidence_summary(
    actions: list[dict[str, str]],
    piece_workshop: dict[str, object],
    decisions: dict[str, object],
    incidents: dict[str, object],
) -> dict[str, object]:
    workshop_summary = piece_workshop.get("summary") if isinstance(piece_workshop.get("summary"), dict) else {}
    decision_summary = decisions.get("summary") if isinstance(decisions.get("summary"), dict) else {}
    incident_summary = incidents.get("summary") if isinstance(incidents.get("summary"), dict) else {}
    items = piece_workshop.get("items") if isinstance(piece_workshop.get("items"), list) else []
    return {
        "actions_with_evidence": len([action for action in actions if action.get("evidence")]),
        "local_proofs_to_verify": int(workshop_summary.get("with_local_proof") or 0),
        "proofs_to_request": int(workshop_summary.get("without_local_proof") or 0),
        "decision_missing_proofs": int(decision_summary.get("missing_proofs") or 0),
        "incident_closure_proofs": int(incident_summary.get("closure_proofs_expected") or 0),
        "items": [item for item in items if isinstance(item, dict)][:6],
    }


def _trust_summary(instance: InstanceConfig, documents: dict[str, object], privacy: dict[str, object]) -> dict[str, object]:
    document_table = documents.get("documents")
    manifest_path = _safe_register(instance, "manifest")
    manifest = _read_table(manifest_path) if manifest_path else DataTable(Path(""), [], [])
    docai = instance.docai_settings()
    privacy_summary = privacy.get("review_summary") if isinstance(privacy.get("review_summary"), dict) else {}
    hashed_documents = (
        len([row for row in document_table.rows if row.get("sha256")])
        if isinstance(document_table, DataTable)
        else 0
    )
    document_count = document_table.count if isinstance(document_table, DataTable) else 0
    return {
        "cards": [
            {
                "label": "Mode local",
                "value": docai.get("privacy", "local_only"),
                "detail": f"DocAI {docai.get('mode', 'off')}; donnees servies depuis l'instance locale.",
            },
            {
                "label": "Empreintes documents",
                "value": f"{hashed_documents}/{document_count}",
                "detail": "Documents inventaries avec SHA-256 dans le registre.",
            },
            {
                "label": "Manifest hash",
                "value": manifest.count if manifest.exists else "absent",
                "detail": "Registre manifest_sha256 disponible pour controle d'integrite.",
            },
            {
                "label": "Diffusion",
                "value": int(privacy_summary.get("blocked") or 0),
                "detail": "Sorties encore bloquees par PrivacyOps.",
            },
            {
                "label": "Pack local",
                "value": "pret",
                "detail": "Export local prepare sans zones de collecte ni journaux internes.",
                "href": "/exports/local.zip",
            },
            {
                "label": "Coffre chiffre/signe",
                "value": "a raccorder",
                "detail": "Le cockpit n'expose pas encore de statut de coffre signe pour cette instance.",
            },
        ]
    }


def _ux_public_tokens(value: str) -> list[str]:
    normalized = value.replace("\\", "/").lower()
    tokenized = "".join(char if char.isalnum() else " " for char in normalized)
    return tokenized.split()


def _contains_forbidden_ux_reference(value: object, *, allow_route: bool = False) -> bool:
    normalized = str(value or "").replace("\\", "/").strip().lower()
    if not normalized:
        return False
    tokens = _ux_public_tokens(normalized)
    first_token = tokens[0] if tokens else ""
    has_absolute_marker = (
        "file://" in normalized
        or "://" in normalized
        or (len(normalized) > 2 and normalized[1:3] == ":/")
        or normalized.startswith("//")
        or (normalized.startswith("/") and not allow_route)
        or (allow_route and first_token in FORBIDDEN_UX_PUBLIC_ROOTS)
    )
    return has_absolute_marker or any(token in FORBIDDEN_UX_PUBLIC_TOKENS for token in tokens)


def _public_text(value: object, fallback: str = "") -> str:
    text = _clip(str(value or "").strip(), 140)
    if not text:
        return fallback
    if _contains_forbidden_ux_reference(text):
        return fallback or UX_REDACTED_REFERENCE
    return text


def _public_href(value: object, fallback: str = "/actions") -> str:
    href = str(value or "").strip()
    if not href:
        return fallback
    if _contains_forbidden_ux_reference(href, allow_route=True):
        return fallback
    if href.startswith("/") and not href.startswith("//"):
        return href
    return fallback


def _sanitize_ux_public(value: Any, key: str = "") -> Any:
    if isinstance(value, dict):
        href_context = key == "hrefs" or key.endswith("_hrefs")
        return {
            item_key: _sanitize_ux_public(item_value, "href" if href_context else item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_ux_public(item, key) for item in value]
    if isinstance(value, str):
        if key == "href" or key.endswith("_href") or key == "route" or key.endswith("_route") or key == "opened_from":
            return _public_href(value)
        if _contains_forbidden_ux_reference(value):
            return UX_REDACTED_REFERENCE
    return value


def _ux_tone(priority: str, status: str = "") -> str:
    priority = (priority or "").upper()
    status = (status or "").lower()
    if priority in {"P0", "P1"} or status in {"bloque", "a_demander"}:
        return "danger"
    if priority == "P2" or status in {"a_revoir", "a_confirmer", "a_verifier"}:
        return "warn"
    if priority == "OK" or status == "clos":
        return "ok"
    return "info"


def _ux_status_label(status: str) -> str:
    return {
        "a_demander": "A demander",
        "a_relancer": "A relancer",
        "a_verifier": "Preuve a verifier",
        "a_traiter": "A traiter",
        "a_revoir": "A arbitrer",
        "a_confirmer": "A confirmer",
        "bloque": "Bloque",
        "clos": "Termine",
    }.get(status or "", status or "A traiter")


def _ux_lane(action: dict[str, str]) -> str:
    status = action.get("status", "")
    domain = action.get("domain", "")
    channel = action.get("channel", "")
    if status == "bloque" or domain == "confidentialite":
        return "diffusion_risk"
    if channel == "syndic" or status == "a_demander":
        return "waiting_syndic"
    if status in {"a_verifier", "a_confirmer"}:
        return "proofs_to_verify"
    if domain in {"decisions", "incidents"}:
        return "memory"
    return "this_week"


def _ux_work_item(action: dict[str, str]) -> dict[str, object]:
    evidence = _public_text(action.get("evidence"), "preuve attendue a preciser")
    status = action.get("status", "a_traiter")
    priority = action.get("priority", "P2")
    lane = _ux_lane(action)
    proof_state = "missing" if status == "a_demander" else "blocked" if status == "bloque" else "candidate"
    if status in {"a_verifier", "a_confirmer"}:
        proof_state = "local"
    if status == "clos":
        proof_state = "verified"
    diffusion_status = "blocked" if status == "bloque" else "after_redaction" if action.get("domain") == "confidentialite" else "cs_only"
    if status == "clos":
        diffusion_status = "copro_ok"
    return {
        "id": _public_text(
            action.get("id") or _stable_action_id("UX", 0, action.get("title", ""), action.get("source", "")),
            _stable_action_id("UX", 0, action.get("title", ""), action.get("source", "")),
        ),
        "kind": _public_text(action.get("domain"), "general"),
        "title": _public_text(action.get("title"), "Action a traiter"),
        "priority": priority,
        "status": status,
        "status_label": _ux_status_label(status),
        "tone": _ux_tone(priority, status),
        "lane": lane,
        "why": _public_text(action.get("detail"), "Ce point demande une verification par le conseil syndical."),
        "proof": {
            "state": proof_state,
            "label": evidence,
            "refs": [evidence] if evidence else [],
        },
        "action": {
            "label": _public_text(action.get("next_step"), "Verifier et noter la prochaine etape."),
            "kind": "ask_syndic" if lane == "waiting_syndic" else "arbitrate" if lane == "diffusion_risk" else "verify",
            "due_on": "",
            "owner": _public_text(action.get("owner"), "Conseil syndical"),
        },
        "diffusion": {
            "status": diffusion_status,
            "label": {
                "blocked": "Ne pas diffuser",
                "after_redaction": "Partager apres masquage",
                "cs_only": "Conseil syndical seulement",
                "copro_ok": "Partage possible",
            }.get(diffusion_status, "Conseil syndical seulement"),
            "reason": "Limiter le partage aux informations utiles et deja verifiees.",
        },
        "memory": {
            "timeline_ref": _public_text(action.get("id"), ""),
            "handover_note": "A reprendre en passation tant que l'action n'est pas cloturee.",
            "pack_section": _public_text(action.get("domain_label"), "Actions"),
        },
        "href": _public_href(action.get("href"), "/actions"),
        "source": {
            "module": _public_text(action.get("source"), "Module"),
            "object_id": _public_text(action.get("id"), ""),
        },
    }


def _ux_nav_item(label: str, href: str, page: str, active_page: str, *, icon: str, count: object = "") -> dict[str, object]:
    return {
        "label": label,
        "href": href,
        "page": page,
        "icon": icon,
        "count": count,
        "is_active": page == active_page,
    }


def _route_href(path: str = "/actions", **params: object) -> str:
    clean_path = _public_href(path, "/actions")
    query = [
        f"{quote(str(key), safe='')}={quote(str(value), safe='')}"
        for key, value in params.items()
        if value is not None and str(value) != ""
    ]
    return f"{clean_path}?{'&'.join(query)}" if query else clean_path


def _parse_iso_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _date_label(value: object, fallback: str = "A fixer") -> str:
    parsed = _parse_iso_date(value)
    if not parsed:
        return fallback
    return f"{parsed.day:02d}/{parsed.month:02d}/{parsed.year}"


COMPTES_CATEGORY_INFO: dict[str, dict[str, str]] = {
    "entretien_maintenance": {
        "label": "Entretien & maintenance",
        "icon": "tool",
        "account_family_label": "Entretien, maintenance et espaces communs",
    },
    "energie_fluides": {
        "label": "Energie & fluides",
        "icon": "drop",
        "account_family_label": "Eau, energie et fluides",
    },
    "prestations_service": {
        "label": "Prestations de service",
        "icon": "service",
        "account_family_label": "Prestataires et services courants",
    },
    "assurances": {
        "label": "Assurances",
        "icon": "shield",
        "account_family_label": "Assurances",
    },
    "taxes_impots": {
        "label": "Taxes & impots",
        "icon": "tax",
        "account_family_label": "Taxes et impots",
    },
    "honoraires": {
        "label": "Honoraires & honoraires tiers",
        "icon": "scale",
        "account_family_label": "Syndic, avocat, expert et comptable",
    },
    "controles_prioritaires": {
        "label": "Controles prioritaires",
        "icon": "alert",
        "account_family_label": "Controles comptables a justifier",
    },
    "autres_charges": {
        "label": "Autres charges",
        "icon": "box",
        "account_family_label": "Autres charges a qualifier",
    },
}

COMPTES_STATUS_LABELS = {
    "p1": "A traiter",
    "p2": "A confirmer",
    "ok": "Conforme avec preuve",
    "missing": "Piece a demander",
    "unknown": "A qualifier",
    "empty": "Aucun controle charge",
}

COMPTES_STATUS_TONES = {
    "p1": "danger",
    "p2": "warn",
    "ok": "ok",
    "missing": "warn",
    "unknown": "info",
    "empty": "info",
}


def _comptes_amount(value: object) -> float | None:
    return _amount_value(value)


def _comptes_amount_label(value: object, fallback: str = "Montant non charge") -> str:
    return _amount_label(value, fallback)


def _comptes_ratio_label(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "A calculer"
    return f"{round(100 * numerator / denominator)}%"


def _comptes_ratio_value(numerator: int, denominator: int) -> int:
    return round(100 * numerator / denominator) if denominator > 0 else 0


def _comptes_slug(value: object) -> str:
    normalized = str(value or "").strip().lower().replace("&", " et ")
    normalized = normalized.replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a")
    normalized = normalized.replace("ç", "c").replace("î", "i").replace("ï", "i").replace("ô", "o")
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")


def _comptes_category_info(category_id: str) -> dict[str, str]:
    return COMPTES_CATEGORY_INFO.get(category_id, COMPTES_CATEGORY_INFO["autres_charges"])


def _comptes_category_id(row: dict[str, str]) -> str:
    explicit = _comptes_slug(
        _first_value(
            row,
            "famille_charge",
            "account_family",
            "account_family_label",
            "categorie",
            "category",
        )
    )
    aliases = {
        "entretien": "entretien_maintenance",
        "entretien_maintenance": "entretien_maintenance",
        "maintenance": "entretien_maintenance",
        "energie": "energie_fluides",
        "energie_fluides": "energie_fluides",
        "fluides": "energie_fluides",
        "prestations": "prestations_service",
        "prestations_service": "prestations_service",
        "services": "prestations_service",
        "assurance": "assurances",
        "assurances": "assurances",
        "taxes": "taxes_impots",
        "taxes_impots": "taxes_impots",
        "impots": "taxes_impots",
        "honoraires": "honoraires",
        "honoraire": "honoraires",
    }
    if explicit in aliases:
        return aliases[explicit]
    if explicit in COMPTES_CATEGORY_INFO:
        return explicit

    account = _first_value(row, "compte_propose", "compte_candidate", "account", "compte_debit")
    if account.startswith("615"):
        return "entretien_maintenance"
    if account.startswith("606"):
        return "energie_fluides"
    if account.startswith("616"):
        return "assurances"
    if account.startswith(("621", "622", "623")):
        return "honoraires"
    if account.startswith(("63", "635")):
        return "taxes_impots"

    haystack = " ".join(
        _first_value(row, field)
        for field in [
            "fournisseur",
            "supplier",
            "supplier_hint",
            "statement_label",
            "account_label",
            "label",
            "libelle_depense",
            "control",
            "evidence",
            "anomaly",
            "anomalies",
            "anomalies_facture",
            "justification",
            "match_reason",
            "motif",
            "next_action",
            "action",
        ]
    ).lower()
    if any(word in haystack for word in ["entretien", "maintenance", "jardin", "espaces verts", "travaux"]):
        return "entretien_maintenance"
    if any(word in haystack for word in ["eau", "electricite", "energie", "gaz", "fluide", "chauffage"]):
        return "energie_fluides"
    if any(word in haystack for word in ["assurance", "multirisque"]):
        return "assurances"
    if any(word in haystack for word in ["taxe", "impot", "foncier"]):
        return "taxes_impots"
    if any(word in haystack for word in ["honoraire", "syndic", "avocat", "expert", "comptable"]):
        return "honoraires"
    if any(word in haystack for word in ["service", "nettoyage", "gardien", "prestation"]):
        return "prestations_service"
    if _first_value(row, "control", "severity", "status"):
        return "controles_prioritaires"
    return "autres_charges"


def _comptes_priority(value: object, default: str = "P2") -> str:
    priority = str(value or default).strip().upper()
    if priority in {"P0", "P1"}:
        return "P1"
    if priority == "OK":
        return "OK"
    if priority == "INFO":
        return "info"
    return "P2"


def _comptes_priority_label(priority: object) -> str:
    normalized = _comptes_priority(priority, "P2")
    return {
        "P1": "A traiter",
        "P2": "A confirmer",
        "OK": "Conforme avec preuve",
        "info": "Information",
    }.get(normalized, "A confirmer")


def _comptes_tone_from_priority(priority: object) -> str:
    return {
        "P1": "danger",
        "P2": "warn",
        "OK": "ok",
        "info": "info",
    }.get(_comptes_priority(priority, "P2"), "warn")


def _comptes_match_state(row: dict[str, str]) -> str:
    status = _first_value(row, "match_status", "statut_rapprochement", "status").upper()
    priority = _comptes_priority(_first_value(row, "match_priority", "priorite"), "")
    if priority == "OK" or status in {"OK", "MATCH", "RAPPROCHE"} or status.startswith("MATCH"):
        return "matched"
    if "AMBIG" in status or "CANDIDAT" in status:
        return "ambiguous"
    if "SANS_ETAT" in status or "ETAT_DEPENSES" in status:
        return "missing_statement"
    if "MONTANT" in status or "ECART" in status:
        return "amount_to_check"
    if "FOURNISSEUR" in status or "ALIAS" in status:
        return "supplier_to_check"
    if "NON" in status or "ABSENT" in status or "MISSING" in status:
        return "not_matched"
    return "to_check"


def _comptes_match_state_label(match_state: str) -> str:
    return {
        "matched": "Facture rapprochee",
        "ambiguous": "Rapprochement candidat a confirmer",
        "missing_statement": "Etat des depenses a demander",
        "amount_to_check": "Montant a verifier",
        "supplier_to_check": "Fournisseur a confirmer",
        "not_matched": "Rapprochement manquant",
        "to_check": "A verifier",
    }.get(match_state, "A verifier")


def _comptes_proof_state(row: dict[str, str], priority: str) -> str:
    match_state = _comptes_match_state(row)
    if priority == "OK" or match_state == "matched":
        return "verified"
    if priority == "P1" or match_state in {"not_matched", "missing_statement"}:
        return "missing"
    if match_state in {"ambiguous", "amount_to_check", "supplier_to_check", "to_check"}:
        return "candidate"
    return "candidate"


def _comptes_proof_state_label(proof_state: str) -> str:
    return {
        "missing": "Piece ou preuve a demander",
        "candidate": "Preuve candidate a confirmer",
        "verified": "Preuve rattachee",
        "rejected": "Preuve refusee",
        "not_needed": "Aucune preuve supplementaire",
    }.get(proof_state, "Preuve a verifier")


def _comptes_alert_type(row: dict[str, str]) -> str:
    text = " ".join(str(value or "") for value in row.values()).lower()
    if "bon de commande" in text or "decision" in text:
        return "missing_order"
    if "piece jointe" in text or "justificatif" in text or "piece attendue" in text:
        return "missing_attachment"
    if "period" in text or "periodicite" in text:
        return "period_gap"
    if "montant" in text or "ecart" in text:
        return "amount_gap"
    if "fournisseur" in text or "alias" in text:
        return "supplier_gap"
    if "ambigu" in text or "candidate" in text:
        return "ambiguous_match"
    if "non" in text or "rapproch" in text or "etat des depenses" in text:
        return "non_match"
    return "unknown"


def _comptes_alert_type_label(alert_type: str) -> str:
    return {
        "missing_order": "Decision ou bon de commande a justifier",
        "missing_attachment": "Justificatif manquant",
        "period_gap": "Periodicite a verifier",
        "non_match": "Facture non rapprochee",
        "ambiguous_match": "Rapprochement ambigu",
        "amount_gap": "Ecart de montant",
        "supplier_gap": "Fournisseur a confirmer",
        "unknown": "Controle a qualifier",
    }.get(alert_type, "Controle a qualifier")


def _comptes_expected_proof(row: dict[str, str], priority: str) -> str:
    explicit = _first_value(row, "expected_proof", "evidence", "preuve_attendue")
    if explicit:
        return _public_text(explicit, "Piece ou justification attendue.")
    match_state = _comptes_match_state(row)
    if match_state == "missing_statement":
        return "Etat des depenses ou grand livre de l'exercice."
    if priority == "P1":
        return "Piece, decision ou ligne de grand livre permettant de justifier le point."
    if priority == "P2":
        return "Confirmation du rattachement comptable ou justificatif complementaire."
    return "Facture et ligne de depense rapprochees."


def _comptes_next_action(row: dict[str, str], priority: str) -> str:
    explicit = _first_value(row, "next_action", "prochaine_action", "action")
    if explicit:
        return _public_text(explicit, "Verifier le point avec le syndic.")
    if priority == "P1":
        return "Demander la piece ou la justification au syndic."
    if priority == "P2":
        return "Confirmer le rattachement avec le syndic ou une piece."
    return "Conserver la preuve rattachee."


def _comptes_merge_invoice(row: dict[str, str], invoices_by_doc: dict[str, dict[str, str]]) -> dict[str, str]:
    doc_id = _first_value(row, "doc_id", "source_doc_id")
    merged = dict(invoices_by_doc.get(doc_id, {}))
    for key, value in row.items():
        if value:
            merged[key] = value
    return merged


def _comptes_piece_actions(piece_id: str, doc_id: str, category_id: str) -> list[dict[str, str]]:
    return [
        {"id": "ouvrir", "label": "Ouvrir", "href": _route_href("/comptes", categorie=category_id, piece=piece_id)},
        {
            "id": "fiche_document",
            "label": "Fiche document",
            "href": _route_href("/documents", doc_id=doc_id) if doc_id else _route_href("/documents"),
        },
        {
            "id": "rattacher_preuve",
            "label": "Rattacher comme preuve",
            "href": _route_href("/comptes", categorie=category_id, piece=piece_id, action="rattacher-preuve"),
        },
        {
            "id": "demander_syndic",
            "label": "Demander au syndic",
            "href": _route_href("/comptes", categorie=category_id, piece=piece_id, tab="questions"),
        },
        {
            "id": "ajouter_rapport_ag",
            "label": "Ajouter au rapport AG",
            "href": _route_href("/comptes", categorie=category_id, piece=piece_id, tab="rapport-ag"),
        },
    ]


def _comptes_piece_from_row(
    row: dict[str, str],
    *,
    category_id: str,
    index: int,
    source: str,
    priority: str,
) -> dict[str, object]:
    doc_id = _public_text(_first_value(row, "doc_id", "piece_doc_id", "source_doc_id"), "")
    supplier = _public_text(_first_value(row, "fournisseur", "supplier", "supplier_hint"), "Fournisseur non renseigne")
    invoice_ref_raw = _public_text(_first_value(row, "numero_facture", "invoice_ref", "reference", "statement_reference"), "")
    invoice_ref = invoice_ref_raw or "Facture sans reference"
    match_state = _comptes_match_state(row)
    proof_state = _comptes_proof_state(row, priority)
    piece_id = _stable_action_id("PCE-COMP", index, doc_id, invoice_ref, supplier, source)
    label = (
        f"Facture {invoice_ref} - {supplier}"
        if invoice_ref_raw
        else _first_value(row, "statement_label", "label", "account_label", "control")
        or f"Piece {doc_id or index}"
    )
    return {
        "piece_id": piece_id,
        "doc_id": doc_id,
        "category_id": category_id,
        "label": _public_text(label, "Piece comptable"),
        "type_label": "facture" if invoice_ref_raw else "ligne depense",
        "supplier_label": supplier,
        "invoice_ref": invoice_ref,
        "invoice_date_label": _date_label(_first_value(row, "date_facture", "invoice_date", "date"), "Date non lue"),
        "amount_label": _comptes_amount_label(_first_value(row, "ttc", "statement_amount", "montant_depense", "amount", "debit")),
        "period_label": _public_text(_first_value(row, "periode", "period_label"), "Exercice"),
        "match_status": match_state,
        "match_status_label": _comptes_match_state_label(match_state),
        "proof_state": proof_state,
        "proof_state_label": _comptes_proof_state_label(proof_state),
        "role_label": "preuve locale" if proof_state == "verified" else "piece a verifier",
        "related_alert_ids": [],
        "question_ids": [],
        "diffusion_label": "Conseil syndical",
        "restriction_reason": "Relecture requise avant diffusion AG" if proof_state != "verified" else "",
        "href": _route_href("/comptes", categorie=category_id, piece=piece_id),
        "actions": _comptes_piece_actions(piece_id, doc_id, category_id),
    }


def _comptes_question_from_row(
    row: dict[str, str],
    *,
    category_id: str,
    alert_id: str,
    piece_id: str,
    index: int,
    year: int,
    source: str,
) -> dict[str, object]:
    if source == "control":
        question = _question_from_control(row)
        subject = row.get("control") or "Controle comptable a justifier"
    elif source == "anomaly":
        question = _question_from_anomaly(row)
        subject = question.get("title") or row.get("anomaly") or "Anomalie facture a clarifier"
    else:
        question = _question_from_non_match(row)
        subject = question.get("title") or row.get("fournisseur") or "Rapprochement a confirmer"
    priority = _comptes_priority(question.get("priority") or _priority_for(row, "P2"), "P2")
    question_text = _public_text(question.get("question"), "Pouvez-vous transmettre la piece ou la confirmation attendue ?")
    question_id = _stable_action_id("Q-COMP", index, category_id, alert_id, piece_id, question_text)
    expected_proof = _comptes_expected_proof(row, priority)
    context_label = _public_text(
        " - ".join(
            part
            for part in [
                _comptes_category_info(category_id)["label"],
                _first_value(row, "fournisseur", "supplier", "supplier_hint"),
                _first_value(row, "numero_facture", "doc_id"),
            ]
            if part
        ),
        _comptes_category_info(category_id)["label"],
    )
    copy_text = "\n".join(
        [
            f"Controle comptes {year} - {context_label}",
            "",
            question_text,
            "",
            f"Preuve attendue: {expected_proof}",
        ]
    )
    return {
        "question_id": question_id,
        "category_id": category_id,
        "alert_ids": [alert_id] if alert_id else [],
        "piece_ids": [piece_id] if piece_id else [],
        "priority": priority,
        "priority_label": _comptes_priority_label(priority),
        "status": "draft",
        "status_label": "Brouillon a relire",
        "subject": _public_text(subject, "Question syndic"),
        "short_label": _clip(question_text, 90),
        "question_text": question_text,
        "copy_text": _public_text(copy_text, question_text),
        "context_label": context_label,
        "expected_answer": "Confirmation ecrite ou piece rattachee au point de controle.",
        "expected_proof": expected_proof,
        "recipient_label": "Syndic",
        "channel_label": "Copie manuelle, aucun envoi automatique",
        "last_sent_label": "Non envoyee depuis CoproScope",
        "answer_summary": "",
        "related_request_id": "",
        "include_in_ag_report": priority in {"P1", "P2"},
        "diffusion_label": "Conseil syndical, a relire avant AG",
        "href": _route_href("/comptes", categorie=category_id, tab="questions", question=question_id),
    }


def _comptes_alert_from_row(
    row: dict[str, str],
    *,
    category_id: str,
    piece_id: str,
    question_id: str,
    index: int,
    priority: str,
    source: str,
) -> dict[str, object]:
    alert_type = _comptes_alert_type(row)
    invoice_ref = _public_text(_first_value(row, "numero_facture", "doc_id"), "Piece concernee")
    alert_id = _stable_action_id("AL-COMP", index, category_id, piece_id, alert_type, source)
    explanation = _public_text(
        _first_value(row, "match_reason", "motif", "reason", "status_label", "libelle_statut", "anomaly", "evidence", "action"),
        "Ce point demande une verification humaine avant validation.",
    )
    return {
        "alert_id": alert_id,
        "category_id": category_id,
        "priority": priority,
        "priority_label": _comptes_priority_label(priority),
        "tone": _comptes_tone_from_priority(priority),
        "type": alert_type,
        "label": _comptes_alert_type_label(alert_type),
        "count": 1,
        "explanation": explanation,
        "affected_piece_ids": [piece_id] if piece_id else [],
        "affected_invoice_refs": [invoice_ref] if invoice_ref else [],
        "expected_proof": _comptes_expected_proof(row, priority),
        "suggested_question_id": question_id,
        "next_action_label": _comptes_next_action(row, priority),
        "status": "question_ready" if question_id else "open",
        "href": _route_href("/comptes", categorie=category_id, alert=alert_id),
    }


def _comptes_empty_selected(year: int) -> dict[str, object]:
    return {
        "category_id": "",
        "label": "Aucune categorie selectionnee",
        "icon": "box",
        "account_family_label": "",
        "amount_charges": None,
        "amount_charges_label": "Montant non charge",
        "amount_state": "missing",
        "invoice_count": 0,
        "matched_invoice_count": 0,
        "matched_ratio": 0,
        "matched_ratio_label": "A calculer",
        "unmatched_invoice_count": 0,
        "missing_pieces_count": 0,
        "ecart_amount": None,
        "ecart_label": "Aucun ecart calcule",
        "ecart_state": "unknown",
        "last_invoice_label": "Date non lue",
        "last_invoice_href": _route_href("/comptes", tab="pieces"),
        "status": "empty",
        "status_label": COMPTES_STATUS_LABELS["empty"],
        "status_detail": "Generer ou importer les sorties ComptaScope pour commencer le controle.",
        "status_tone": "info",
        "alert_count": 0,
        "p1_count": 0,
        "p2_count": 0,
        "ok_count": 0,
        "question_count": 0,
        "ag_included": False,
        "next_action_label": "Generer ou importer les sorties ComptaScope pour cet exercice.",
        "href": _route_href("/comptes"),
        "is_selected": True,
        "novice_summary": "Aucun controle comptes charge pour cet exercice.",
        "controls_summary": {
            "conforme": "Aucun point conforme charge.",
            "a_confirmer": "Aucun point a confirmer charge.",
            "bloquant": "Aucun point prioritaire charge.",
        },
        "alerts": [],
        "pieces": [],
        "questions": [],
        "ag_section": {
            "title": f"Rapport AG comptes {year}",
            "include_in_ag_report": False,
            "scope_label": "Aucun point inclus",
            "notes": [],
            "href": _route_href("/comptes", tab="rapport-ag"),
        },
        "history": [],
        "subcategories": [],
        "source_rows": [],
        "diffusion": {
            "status": "local_only",
            "label": "Prive local",
            "reason": "Aucune donnee comptable exploitable n'est chargee.",
            "allowed_audience": "Conseil syndical",
            "blocked_by": [],
        },
        "memory_note": "Relancer le controle apres import des sorties ComptaScope.",
    }


def _comptes_status_from_counts(p1_count: int, p2_count: int, missing_count: int, ok_count: int, total: int) -> str:
    if p1_count:
        return "p1"
    if p2_count:
        return "p2"
    if missing_count and not ok_count:
        return "missing"
    if total:
        return "ok"
    return "unknown"


def _comptes_status_detail(status: str, matched: int, total: int, missing: int) -> str:
    if status == "p1":
        return "Au moins un point doit etre traite avant AG avec une preuve attendue."
    if status == "p2":
        return "Rapprochement plausible ou piece candidate a confirmer avec le syndic."
    if status == "missing":
        return "Piece ou justificatif manquant pour conclure le controle."
    if status == "ok":
        return f"{matched}/{total} pieces disposent d'une preuve rattachee."
    return "Categorie a qualifier a partir des sorties disponibles."


def _comptes_tabs(selected: dict[str, object]) -> list[dict[str, object]]:
    category_id = str(selected.get("category_id") or "")
    counts = {
        "detail": int(selected.get("alert_count") or 0),
        "pieces": len(selected.get("pieces", [])) if isinstance(selected.get("pieces"), list) else 0,
        "questions": len(selected.get("questions", [])) if isinstance(selected.get("questions"), list) else 0,
        "rapport-ag": 1 if selected.get("ag_included") else 0,
    }
    labels = {
        "detail": "Detail",
        "pieces": "Pieces",
        "questions": "Questions au syndic",
        "rapport-ag": "Rapport AG",
    }
    return [
        {
            "id": tab_id,
            "label": labels[tab_id],
            "count": counts[tab_id],
            "is_active": tab_id == "detail",
            "href": _route_href("/comptes", categorie=category_id, tab=tab_id) if category_id else _route_href("/comptes", tab=tab_id),
        }
        for tab_id in ["detail", "pieces", "questions", "rapport-ag"]
    ]


def _comptes_facet_options(
    field: str,
    rows: list[dict[str, object]],
    *,
    route_field: str | None = None,
    labels: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    counts = Counter(str(row.get(field, "") or "non renseigne") for row in rows)
    options: list[dict[str, object]] = []
    for value, count in sorted(counts.items(), key=lambda item: (item[0] == "non renseigne", item[0])):
        option_label = (labels or {}).get(value, value)
        options.append(
            {
                "value": value,
                "label": _public_text(option_label, "non renseigne"),
                "count": count,
                "href": _route_href("/comptes", **{route_field or field: value}),
                "is_active": False,
            }
        )
    return options


def _comptes_ag_note(category: dict[str, object]) -> dict[str, object]:
    category_id = str(category.get("category_id") or "")
    return {
        "note_id": _stable_action_id("NOTE-COMP", 0, category_id, str(category.get("status", ""))),
        "category_id": category_id,
        "author_label": "Conseil syndical",
        "created_on_label": "A completer",
        "text": _public_text(
            category.get("next_action_label"),
            "Point a relire avant diffusion aux coproprietaires.",
        ),
        "diffusion_level": "to_review" if category.get("status") in {"p1", "p2", "missing"} else "ag_public",
        "related_alert_ids": [],
        "related_question_ids": [],
        "href": _route_href("/comptes", categorie=category_id, tab="rapport-ag"),
    }


def _comptes_ag_report(
    year: int,
    categories: list[dict[str, object]],
    alerts: list[dict[str, object]],
    pieces: list[dict[str, object]],
    questions: list[dict[str, object]],
) -> dict[str, object]:
    included = [category for category in categories if category.get("ag_included")]
    excluded = [category for category in categories if not category.get("ag_included")]
    p1_points = [alert for alert in alerts if alert.get("priority") == "P1"]
    p2_points = [alert for alert in alerts if alert.get("priority") == "P2"]
    ok_points = [piece for piece in pieces if piece.get("proof_state") == "verified"][:12]
    missing_pieces = [piece for piece in pieces if piece.get("proof_state") == "missing"]
    open_questions = [question for question in questions if question.get("status") != "closed"]
    notes = [_comptes_ag_note(category) for category in included[:12]]
    preview_lines = [
        f"# Controle des comptes - AG {year}",
        "",
        f"- Points a traiter: {len(p1_points)}",
        f"- Points a confirmer: {len(p2_points)}",
        f"- Pieces manquantes: {len(missing_pieces)}",
        f"- Questions syndic ouvertes: {len(open_questions)}",
    ]
    if included:
        preview_lines.append("")
        preview_lines.append("## Categories a citer")
        for category in included[:8]:
            preview_lines.append(f"- {category.get('label')}: {category.get('status_label')} - {category.get('next_action_label')}")
    diffusion_status = "warning" if p1_points or p2_points or open_questions else "ok"
    return {
        "title": f"Rapport AG controle des comptes {year}",
        "scope_label": "Points ouverts et preuves utiles",
        "generated_on_label": f"Situation {year}",
        "included_categories": included,
        "excluded_categories": [
            {
                "category_id": category.get("category_id"),
                "label": category.get("label"),
                "reason": "Non prioritaire pour le rapport AG",
                "href": category.get("href"),
            }
            for category in excluded
        ],
        "p1_points": p1_points,
        "p2_points": p2_points,
        "ok_with_proof_points": ok_points,
        "missing_pieces": missing_pieces,
        "open_questions": open_questions,
        "notes": notes,
        "preview_markdown": "\n".join(preview_lines),
        "diffusion_status": diffusion_status,
        "diffusion_label": "A relire avant export" if diffusion_status == "warning" else "Export possible",
        "blocked_by": [],
        "export_href": _route_href("/comptes", export="rapport-ag"),
        "edit_href": _route_href("/comptes", tab="rapport-ag"),
    }


def _build_comptes_ux_model(instance: InstanceConfig, year: int, accounting: dict[str, object]) -> dict[str, object]:
    invoices_table = accounting.get("invoices")
    matches_table = accounting.get("matches")
    non_matches_table = accounting.get("non_matches")
    anomalies_table = accounting.get("anomalies")
    ledger_table = accounting.get("ledger")
    expense_statement_table = accounting.get("expense_statement")
    invoices = invoices_table.rows if isinstance(invoices_table, DataTable) else []
    matches = matches_table.rows if isinstance(matches_table, DataTable) else []
    non_matches = non_matches_table.rows if isinstance(non_matches_table, DataTable) else []
    anomalies = anomalies_table.rows if isinstance(anomalies_table, DataTable) else []
    ledger_rows = ledger_table.rows if isinstance(ledger_table, DataTable) else []
    expense_rows = expense_statement_table.rows if isinstance(expense_statement_table, DataTable) else []
    controls_p1 = accounting.get("controls_p1") if isinstance(accounting.get("controls_p1"), list) else []
    before_ag = accounting.get("before_ag") if isinstance(accounting.get("before_ag"), dict) else {}
    summary_source = accounting.get("summary") if isinstance(accounting.get("summary"), dict) else {}
    invoices_by_doc = {row.get("doc_id", ""): row for row in invoices if isinstance(row, dict) and row.get("doc_id")}
    buckets: dict[str, dict[str, object]] = {}
    all_pieces: list[dict[str, object]] = []
    all_alerts: list[dict[str, object]] = []
    all_questions: list[dict[str, object]] = []
    seen_piece_ids: set[str] = set()
    seen_docs: set[str] = set()

    def bucket_for(category_id: str) -> dict[str, object]:
        if category_id not in buckets:
            info = _comptes_category_info(category_id)
            buckets[category_id] = {
                "category_id": category_id,
                "label": info["label"],
                "icon": info["icon"],
                "account_family_label": info["account_family_label"],
                "pieces": [],
                "alerts": [],
                "questions": [],
                "amount_total": 0.0,
                "has_amount": False,
                "amount_keys": set(),
                "post_keys": set(),
                "post_count": 0,
                "source_rows": [],
                "suppliers": Counter(),
                "dates": [],
            }
        return buckets[category_id]

    def add_amount(bucket: dict[str, object], row: dict[str, str], *, index: int, source: str) -> None:
        amount = _accounting_row_amount(row, "amount", "statement_amount", "ttc", "montant_depense", "debit")
        if amount is None:
            return
        key = _accounting_row_key(row, index, source)
        amount_keys = bucket.get("amount_keys")
        if isinstance(amount_keys, set):
            if key in amount_keys:
                return
            amount_keys.add(key)
        bucket["amount_total"] = float(bucket.get("amount_total") or 0.0) + amount
        bucket["has_amount"] = True

    def add_expense_post(category_id: str, row: dict[str, str], *, index: int, source: str) -> None:
        bucket = bucket_for(category_id)
        key = _accounting_row_key(row, index, source)
        post_keys = bucket.get("post_keys")
        if isinstance(post_keys, set):
            if key not in post_keys:
                post_keys.add(key)
                bucket["post_count"] = int(bucket.get("post_count") or 0) + 1
        else:
            bucket["post_count"] = int(bucket.get("post_count") or 0) + 1
        add_amount(bucket, row, index=index, source=source)
        supplier = _public_text(_first_value(row, "fournisseur", "supplier", "supplier_hint"), "")
        if supplier:
            suppliers = bucket.get("suppliers")
            if isinstance(suppliers, Counter):
                suppliers[supplier] += 1
        invoice_date = _first_value(row, "date_facture", "invoice_date", "date")
        if invoice_date:
            dates = bucket.get("dates")
            if isinstance(dates, list):
                dates.append(invoice_date)
        source_rows = bucket.get("source_rows")
        if isinstance(source_rows, list):
            source_rows.append(
                {
                    "source_id": _stable_action_id("SRC-COMP", index, key, source),
                    "type": source,
                    "label": _public_text(
                        _first_value(row, "label", "statement_label", "account_label", "justification"),
                        "Ligne de depense",
                    ),
                    "href": _route_href("/comptes", categorie=category_id, source=source, ligne=index),
                }
            )

    def add_piece(category_id: str, piece: dict[str, object], row: dict[str, str]) -> None:
        piece_id = str(piece.get("piece_id") or "")
        if piece_id in seen_piece_ids:
            return
        seen_piece_ids.add(piece_id)
        doc_id = str(piece.get("doc_id") or "")
        if doc_id:
            seen_docs.add(doc_id)
        bucket = bucket_for(category_id)
        bucket["pieces"].append(piece)
        all_pieces.append(piece)
        supplier = str(piece.get("supplier_label") or "")
        if supplier:
            suppliers = bucket.get("suppliers")
            if isinstance(suppliers, Counter):
                suppliers[supplier] += 1
        if not expense_source_rows:
            add_amount(bucket, row, index=len(all_pieces), source="piece")
        invoice_date = _first_value(row, "date_facture", "invoice_date", "date")
        if invoice_date:
            dates = bucket.get("dates")
            if isinstance(dates, list):
                dates.append(invoice_date)

    def add_alert_and_question(
        category_id: str,
        row: dict[str, str],
        piece: dict[str, object],
        *,
        index: int,
        priority: str,
        source: str,
    ) -> None:
        alert_seed = _stable_action_id("AL-COMP", index, category_id, str(piece.get("piece_id", "")), source)
        question = _comptes_question_from_row(
            row,
            category_id=category_id,
            alert_id=alert_seed,
            piece_id=str(piece.get("piece_id") or ""),
            index=index,
            year=year,
            source=source,
        )
        alert = _comptes_alert_from_row(
            row,
            category_id=category_id,
            piece_id=str(piece.get("piece_id") or ""),
            question_id=str(question.get("question_id") or ""),
            index=index,
            priority=priority,
            source=source,
        )
        question["alert_ids"] = [alert["alert_id"]]
        piece_alerts = piece.get("related_alert_ids")
        if isinstance(piece_alerts, list):
            piece_alerts.append(alert["alert_id"])
        piece_questions = piece.get("question_ids")
        if isinstance(piece_questions, list):
            piece_questions.append(question["question_id"])
        bucket = bucket_for(category_id)
        bucket["alerts"].append(alert)
        bucket["questions"].append(question)
        all_alerts.append(alert)
        all_questions.append(question)

    expense_source_rows = expense_rows if expense_rows else ledger_rows
    expense_source_name = "expense_statement" if expense_rows else "ledger"
    for index, row in enumerate(expense_source_rows, start=1):
        if not isinstance(row, dict):
            continue
        category_id = _comptes_category_id(row)
        add_expense_post(category_id, row, index=index, source=expense_source_name)

    for index, row in enumerate(matches, start=1):
        if not isinstance(row, dict):
            continue
        merged = _comptes_merge_invoice(row, invoices_by_doc)
        category_id = _comptes_category_id(merged)
        priority = _comptes_priority(_first_value(merged, "match_priority", "priorite"), "OK")
        piece = _comptes_piece_from_row(merged, category_id=category_id, index=index, source="match", priority=priority)
        add_piece(category_id, piece, merged)
        if priority != "OK":
            add_alert_and_question(category_id, merged, piece, index=index, priority=priority, source="match")

    for index, row in enumerate(non_matches, start=1):
        if not isinstance(row, dict):
            continue
        merged = _comptes_merge_invoice(row, invoices_by_doc)
        category_id = _comptes_category_id(merged)
        priority = _comptes_priority(_priority_for(merged, "P2"), "P2")
        piece = _comptes_piece_from_row(merged, category_id=category_id, index=1000 + index, source="non_match", priority=priority)
        add_piece(category_id, piece, merged)
        add_alert_and_question(category_id, merged, piece, index=1000 + index, priority=priority, source="non_match")

    for index, row in enumerate(anomalies, start=1):
        if not isinstance(row, dict):
            continue
        merged = _comptes_merge_invoice(row, invoices_by_doc)
        category_id = _comptes_category_id(merged)
        priority = _comptes_priority(_priority_for(merged, "P2"), "P2")
        piece = _comptes_piece_from_row(merged, category_id=category_id, index=1500 + index, source="anomaly", priority=priority)
        add_piece(category_id, piece, merged)
        if priority != "OK":
            add_alert_and_question(category_id, merged, piece, index=1500 + index, priority=priority, source="anomaly")

    for index, raw_row in enumerate(controls_p1, start=1):
        if not isinstance(raw_row, dict):
            continue
        row = _comptes_merge_invoice(raw_row, invoices_by_doc)
        category_id = _comptes_category_id(row)
        priority = _comptes_priority(_priority_for(row, "P1"), "P1")
        piece = _comptes_piece_from_row(row, category_id=category_id, index=2000 + index, source="control", priority=priority)
        piece["type_label"] = "justificatif"
        piece["proof_state"] = "missing"
        piece["proof_state_label"] = _comptes_proof_state_label("missing")
        piece["role_label"] = "preuve attendue"
        add_piece(category_id, piece, row)
        add_alert_and_question(category_id, row, piece, index=2000 + index, priority=priority, source="control")

    for index, row in enumerate(invoices, start=1):
        if not isinstance(row, dict):
            continue
        doc_id = row.get("doc_id", "")
        if doc_id and doc_id in seen_docs:
            continue
        category_id = _comptes_category_id(row)
        has_anomaly = bool(_first_value(row, "anomalies", "anomalies_facture"))
        priority = "P2" if has_anomaly else "OK"
        piece = _comptes_piece_from_row(row, category_id=category_id, index=3000 + index, source="invoice", priority=priority)
        add_piece(category_id, piece, row)
        if has_anomaly:
            add_alert_and_question(category_id, row, piece, index=3000 + index, priority=priority, source="invoice")

    categories: list[dict[str, object]] = []
    for category_id, bucket in buckets.items():
        pieces = [piece for piece in bucket.get("pieces", []) if isinstance(piece, dict)]
        invoice_pieces = [piece for piece in pieces if piece.get("type_label") == "facture"]
        alerts = [alert for alert in bucket.get("alerts", []) if isinstance(alert, dict)]
        questions = [question for question in bucket.get("questions", []) if isinstance(question, dict)]
        def piece_counter_key(piece: dict[str, object], index: int) -> str:
            invoice_ref = str(piece.get("invoice_ref") or "")
            if invoice_ref == "Facture sans reference":
                invoice_ref = ""
            return str(piece.get("doc_id") or invoice_ref or piece.get("piece_id") or index)

        piece_keys = {piece_counter_key(piece, index) for index, piece in enumerate(invoice_pieces, start=1)}
        matched_keys = {
            piece_counter_key(piece, index)
            for index, piece in enumerate(invoice_pieces, start=1)
            if piece.get("proof_state") == "verified"
        }
        invoice_count = len(piece_keys)
        matched_count = len(matched_keys)
        missing_count = len([piece for piece in pieces if piece.get("proof_state") == "missing"])
        p1_count = len([alert for alert in alerts if alert.get("priority") == "P1"])
        p2_count = len([alert for alert in alerts if alert.get("priority") == "P2"])
        ok_count = matched_count
        post_count = int(bucket.get("post_count") or 0)
        status = (
            _comptes_status_from_counts(p1_count, p2_count, missing_count, ok_count, invoice_count)
            if invoice_count
            else "unknown"
            if post_count
            else _comptes_status_from_counts(p1_count, p2_count, missing_count, ok_count, invoice_count)
        )
        has_amount = bool(bucket.get("has_amount"))
        amount_total = float(bucket.get("amount_total") or 0.0)
        dates = [str(value) for value in bucket.get("dates", []) if value]
        last_date = sorted(dates)[-1] if dates else ""
        category = {
            "category_id": category_id,
            "label": bucket.get("label"),
            "icon": bucket.get("icon"),
            "account_family_label": bucket.get("account_family_label"),
            "amount_charges": round(amount_total, 2) if has_amount else None,
            "amount_charges_label": _comptes_amount_label(amount_total) if has_amount else "Montant non charge",
            "amount_state": "loaded" if has_amount else "missing",
            "analyzed_posts_count": max(post_count, invoice_count, len(alerts) if not post_count and not invoice_count else 0),
            "invoice_count": invoice_count,
            "matched_invoice_count": matched_count,
            "matched_ratio": _comptes_ratio_value(matched_count, invoice_count),
            "matched_ratio_label": _comptes_ratio_label(matched_count, invoice_count),
            "unmatched_invoice_count": max(invoice_count - matched_count, 0),
            "missing_pieces_count": missing_count,
            "ecart_amount": None,
            "ecart_label": "A verifier" if status in {"p1", "p2", "missing"} else "Aucun ecart detecte",
            "ecart_state": "detected" if status in {"p1", "p2", "missing"} else "none",
            "last_invoice_label": _date_label(last_date, "Date non lue"),
            "last_invoice_href": _route_href("/comptes", categorie=category_id, tab="pieces"),
            "status": status,
            "status_label": COMPTES_STATUS_LABELS[status],
            "status_detail": _comptes_status_detail(status, matched_count, invoice_count, missing_count),
            "status_tone": COMPTES_STATUS_TONES[status],
            "alert_count": len(alerts),
            "p1_count": p1_count,
            "p2_count": p2_count,
            "ok_count": ok_count,
            "question_count": len(questions),
            "ag_included": status in {"p1", "p2", "missing"},
            "next_action_label": (
                "Traiter les questions et preuves attendues avant AG"
                if status == "p1"
                else "Confirmer avec le syndic ou une piece"
                if status == "p2"
                else "Demander la piece manquante"
                if status == "missing"
                else "Conserver la preuve rattachee"
                if status == "ok"
                else "Qualifier la categorie"
            ),
            "href": _route_href("/comptes", categorie=category_id),
            "is_selected": False,
        }
        categories.append(category)

    status_rank = {"p1": 0, "missing": 1, "p2": 2, "unknown": 3, "ok": 4}
    categories.sort(key=lambda category: (status_rank.get(str(category.get("status")), 9), str(category.get("label", ""))))
    selected_category_id = str(categories[0].get("category_id") or "") if categories else ""
    for category in categories:
        category["is_selected"] = category.get("category_id") == selected_category_id

    selected: dict[str, object]
    if selected_category_id:
        base_category = next(category for category in categories if category.get("category_id") == selected_category_id)
        bucket = buckets[selected_category_id]
        pieces = [piece for piece in bucket.get("pieces", []) if isinstance(piece, dict)]
        alerts = [alert for alert in bucket.get("alerts", []) if isinstance(alert, dict)]
        questions = [question for question in bucket.get("questions", []) if isinstance(question, dict)]
        suppliers = bucket.get("suppliers")
        source_rows = [row for row in bucket.get("source_rows", []) if isinstance(row, dict)]
        selected = dict(base_category)
        selected.update(
            {
                "novice_summary": (
                    f"{base_category.get('label')} : {base_category.get('status_label')}. "
                    f"{base_category.get('next_action_label')}."
                ),
                "controls_summary": {
                    "conforme": f"{base_category.get('matched_invoice_count')} piece(s) avec preuve rattachee.",
                    "a_confirmer": f"{base_category.get('p2_count')} point(s) a confirmer.",
                    "bloquant": f"{base_category.get('p1_count')} point(s) a traiter.",
                },
                "alerts": alerts,
                "pieces": pieces,
                "questions": questions,
                "ag_section": {
                    "title": f"{base_category.get('label')} dans le rapport AG",
                    "include_in_ag_report": bool(base_category.get("ag_included")),
                    "scope_label": "Inclure les points ouverts de cette categorie dans le rapport AG",
                    "notes": [_comptes_ag_note(base_category)] if base_category.get("ag_included") else [],
                    "href": _route_href("/comptes", categorie=selected_category_id, tab="rapport-ag"),
                },
                "history": [
                    {
                        "event_id": _stable_action_id("HIST-COMP", 0, selected_category_id, "control_loaded"),
                        "occurred_on": str(year),
                        "type": "control_loaded",
                        "type_label": "Controle charge",
                        "actor_label": "ComptaScope",
                        "summary": "Sorties comptables chargees dans le guide CS.",
                        "category_id": selected_category_id,
                        "piece_ids": [piece.get("piece_id") for piece in pieces[:3]],
                        "question_ids": [question.get("question_id") for question in questions[:3]],
                        "is_evidence": False,
                        "memory_note": "A conserver pour la passation CS.",
                    }
                ],
                "subcategories": [
                    {
                        "subcategory_id": _stable_action_id("SUB-COMP", index, supplier),
                        "label": supplier,
                        "count": count,
                        "href": _route_href("/comptes", categorie=selected_category_id, fournisseur=supplier),
                    }
                    for index, (supplier, count) in enumerate((suppliers.most_common(5) if isinstance(suppliers, Counter) else []), start=1)
                ],
                "source_rows": source_rows[:8]
                + [
                    {
                        "source_id": _stable_action_id("SRC-COMP", index, str(piece.get("piece_id", ""))),
                        "type": "comptascope",
                        "label": piece.get("label"),
                        "href": piece.get("href"),
                    }
                    for index, piece in enumerate(pieces[:8], start=1)
                ][:8],
                "diffusion": {
                    "status": "after_review" if base_category.get("status") in {"p1", "p2", "missing"} else "ag_ok",
                    "label": "A relire avant diffusion" if base_category.get("status") in {"p1", "p2", "missing"} else "AG diffusable",
                    "reason": "Les questions ouvertes ne doivent pas etre presentees comme des conclusions definitives.",
                    "allowed_audience": "Conseil syndical",
                    "blocked_by": [],
                },
                "memory_note": "Reprendre ce point avant AG avec les preuves et reponses rattachees.",
            }
        )
    else:
        selected = _comptes_empty_selected(year)

    tabs = _comptes_tabs(selected)
    ag_report = _comptes_ag_report(year, categories, all_alerts, all_pieces, all_questions)
    total_charges = sum(float(category.get("amount_charges") or 0.0) for category in categories)
    has_total = any(category.get("amount_state") == "loaded" for category in categories)
    summary_total = _amount_value(summary_source.get("total_charges"))
    if not has_total and summary_total is not None:
        total_charges = summary_total
        has_total = True
    invoice_summary_pieces = [piece for piece in all_pieces if isinstance(piece, dict) and piece.get("type_label") == "facture"]
    piece_summary_keys = {
        str(piece.get("doc_id") or (piece.get("invoice_ref") if piece.get("invoice_ref") != "Facture sans reference" else "") or piece.get("piece_id"))
        for piece in invoice_summary_pieces
    }
    invoice_total = max(
        len(piece_summary_keys),
        _coerce_int(summary_source.get("invoice_count")),
        len(matches) + len(non_matches),
    )
    invoice_matched = max(
        len(
            {
                str(piece.get("doc_id") or (piece.get("invoice_ref") if piece.get("invoice_ref") != "Facture sans reference" else "") or piece.get("piece_id"))
                for piece in invoice_summary_pieces
                if piece.get("proof_state") == "verified"
            }
        ),
        _accounting_summary_match_count(summary_source),
    )
    p1_count = len([alert for alert in all_alerts if alert.get("priority") == "P1"])
    p2_count = len([alert for alert in all_alerts if alert.get("priority") == "P2"])
    missing_count = len([piece for piece in all_pieces if piece.get("proof_state") == "missing"])
    analyzed_posts_count = max(
        sum(int(category.get("analyzed_posts_count") or 0) for category in categories),
        _coerce_int(summary_source.get("expense_statement_line_count")),
        _coerce_int(summary_source.get("entry_count")),
        invoice_total,
        len(categories),
    )
    blocker_count = len(ag_report.get("blocked_by", [])) if isinstance(ag_report.get("blocked_by"), list) else 0

    def counter(value: object, href: str, filter_key: str, help_label: str, status_tone: str) -> dict[str, object]:
        return {
            "value": value,
            "count": value if isinstance(value, int) else None,
            "href": href,
            "filter_key": filter_key,
            "help_label": help_label,
            "status_tone": status_tone,
        }

    summary = {
        "total_charges_amount": round(total_charges, 2) if has_total else None,
        "total_charges_label": _comptes_amount_label(total_charges) if has_total else "Montant non charge",
        "analyzed_posts_count": analyzed_posts_count,
        "invoice_total_count": invoice_total,
        "invoice_matched_count": invoice_matched,
        "invoice_matched_ratio": _comptes_ratio_value(invoice_matched, invoice_total),
        "invoice_matched_label": f"{_comptes_ratio_label(invoice_matched, invoice_total)} ({invoice_matched} / {invoice_total})",
        "p1_count": p1_count,
        "p1_ratio_label": _comptes_ratio_label(p1_count, max(invoice_total, 1)),
        "p2_count": p2_count,
        "p2_ratio_label": _comptes_ratio_label(p2_count, max(invoice_total, 1)),
        "missing_pieces_count": missing_count,
        "missing_pieces_ratio_label": _comptes_ratio_label(missing_count, max(invoice_total, 1)),
        "questions_count": len(all_questions),
        "ag_included_count": len(ag_report.get("included_categories", [])) if isinstance(ag_report.get("included_categories"), list) else 0,
        "export_blockers_count": blocker_count,
        "last_control_label": _date_label(str(summary_source.get("generated_at", ""))[:10], f"Situation {year}"),
        "counters": {
            "total_charges": counter(
                _comptes_amount_label(total_charges) if has_total else "Montant non charge",
                _route_href("/comptes"),
                "all",
                "Total lu dans les sorties disponibles.",
                "info",
            ),
            "invoice_matched": counter(
                invoice_matched,
                _route_href("/comptes", match_state="matched"),
                "matched",
                "Factures reliees a une ligne de depense ou preuve suffisante.",
                "ok" if invoice_matched else "warn",
            ),
            "p1": counter(
                p1_count,
                _route_href("/comptes", statut="p1"),
                "p1",
                "A traiter avant AG avec question ou preuve attendue.",
                "danger" if p1_count else "ok",
            ),
            "p2": counter(
                p2_count,
                _route_href("/comptes", statut="p2"),
                "p2",
                "A confirmer avec le syndic ou une piece.",
                "warn" if p2_count else "ok",
            ),
            "missing_pieces": counter(
                missing_count,
                _route_href("/comptes", proof_state="missing"),
                "missing",
                "Justificatifs a demander ou rattacher.",
                "warn" if missing_count else "ok",
            ),
        },
    }
    summary_counter_meta = {
        "analyzed_posts_count": counter(
            summary["analyzed_posts_count"],
            _route_href("/comptes"),
            "all",
            "Postes ou factures disponibles dans le controle courant.",
            "info",
        ),
        "invoice_total_count": counter(
            invoice_total,
            _route_href("/comptes", tab="pieces"),
            "pieces",
            "Factures et pieces comptables chargees pour cet exercice.",
            "info",
        ),
        "invoice_matched_count": counter(
            invoice_matched,
            _route_href("/comptes", match_state="matched"),
            "matched",
            "Factures reliees a une ligne de depense ou preuve suffisante.",
            "ok" if invoice_matched else "warn",
        ),
        "p1_count": counter(
            p1_count,
            _route_href("/comptes", statut="p1"),
            "p1",
            "A traiter avant AG avec question ou preuve attendue.",
            "danger" if p1_count else "ok",
        ),
        "p2_count": counter(
            p2_count,
            _route_href("/comptes", statut="p2"),
            "p2",
            "A confirmer avec le syndic ou une piece.",
            "warn" if p2_count else "ok",
        ),
        "missing_pieces_count": counter(
            missing_count,
            _route_href("/comptes", proof_state="missing"),
            "missing",
            "Justificatifs a demander ou rattacher.",
            "warn" if missing_count else "ok",
        ),
        "questions_count": counter(
            len(all_questions),
            _route_href("/comptes", tab="questions"),
            "questions",
            "Questions au syndic preparees comme brouillons a relire.",
            "warn" if all_questions else "ok",
        ),
        "ag_included_count": counter(
            summary["ag_included_count"],
            _route_href("/comptes", tab="rapport-ag"),
            "rapport-ag",
            "Categories et points ouverts inclus dans la synthese AG.",
            "warn" if summary["ag_included_count"] else "info",
        ),
        "export_blockers_count": counter(
            blocker_count,
            _route_href("/comptes", tab="rapport-ag"),
            "export",
            "Elements qui bloquent ou limitent un export diffusable.",
            "danger" if blocker_count else "ok",
        ),
    }
    for name, meta in summary_counter_meta.items():
        summary[f"{name}_href"] = meta["href"]
        summary[f"{name}_filter_key"] = meta["filter_key"]
        summary[f"{name}_help_label"] = meta["help_label"]
        summary[f"{name}_status_tone"] = meta["status_tone"]
    summary["counter_meta"] = summary_counter_meta
    summary["cards"] = [
        {"id": key, "label": label, **value}
        for key, label, value in [
            ("total_charges", "Total depenses (charges)", summary["counters"]["total_charges"]),
            ("invoice_matched", "Factures rapprochees", summary["counters"]["invoice_matched"]),
            ("p2", "P2 a confirmer", summary["counters"]["p2"]),
            ("p1", "P1 a traiter", summary["counters"]["p1"]),
            ("missing_pieces", "Pieces manquantes", summary["counters"]["missing_pieces"]),
        ]
    ]
    kpis = {
        "cards": summary["cards"],
        "total_charges": summary["counters"]["total_charges"],
        "invoice_matched": summary["counters"]["invoice_matched"],
        "p2": summary["counters"]["p2"],
        "p1": summary["counters"]["p1"],
        "missing_pieces": summary["counters"]["missing_pieces"],
    }

    facets = {
        "exercise": [
            {
                "value": str(year),
                "label": f"Exercice {year}",
                "count": len(categories),
                "href": _route_href("/comptes", exercice=year),
                "is_active": True,
            }
        ],
        "category": _comptes_facet_options("category_id", categories, route_field="categorie"),
        "status": _comptes_facet_options("status", categories, route_field="statut", labels=COMPTES_STATUS_LABELS),
        "supplier": _comptes_facet_options("supplier_label", all_pieces, route_field="fournisseur"),
        "proof_state": _comptes_facet_options("proof_state", all_pieces, labels={
            "missing": "Piece ou preuve a demander",
            "candidate": "Preuve candidate",
            "verified": "Preuve rattachee",
        }),
        "piece_state": _comptes_facet_options("proof_state", all_pieces, route_field="piece_state", labels={
            "missing": "Piece manquante",
            "candidate": "Piece candidate",
            "verified": "Piece verifiee",
        }),
        "alert_type": _comptes_facet_options("type", all_alerts, route_field="alert_type"),
        "ag_inclusion": _comptes_facet_options("ag_included", categories, route_field="ag", labels={
            "True": "Incluse AG",
            "False": "Non incluse AG",
        }),
        "match_state": _comptes_facet_options("match_status", all_pieces, route_field="match_state"),
    }
    filters = {
        "selected_exercise": str(year),
        "selected_category": selected_category_id,
        "selected_status": "",
        "selected_supplier": "",
        "selected_proof_state": "",
        "selected_piece_state": "",
        "selected_alert_type": "",
        "show_solded_lines": True,
        "query": "",
        "selected_category_id": selected_category_id,
        "selected_tab": "detail",
    }
    has_accounting_data = bool(invoices or matches or non_matches or controls_p1 or before_ag)
    empty_states = {
        "no_accounting": {
            "is_visible": not has_accounting_data,
            "label": "Aucun controle comptes charge. Generer ou importer les sorties ComptaScope pour cet exercice.",
            "href": _route_href("/depot", pipeline="compta"),
        },
        "no_exercise": {
            "is_visible": False,
            "label": "Aucun exercice comptable disponible. Selectionner ou importer un exercice.",
            "href": _route_href("/depot"),
        },
        "no_category": {
            "is_visible": not bool(categories),
            "label": "Aucune categorie de charges exploitable pour cet exercice.",
            "href": _route_href("/depot", pipeline="compta"),
        },
        "no_result": {
            "is_visible": False,
            "label": "Aucune categorie ne correspond a ces filtres. Retirer un filtre ou afficher toutes les categories.",
            "href": _route_href("/comptes"),
        },
        "no_amount": {
            "is_visible": not has_total,
            "label": "Montant non charge pour ce poste. Le controle reste possible a partir des factures et pieces.",
            "href": _route_href("/comptes", tab="pieces"),
        },
        "no_alert": {
            "is_visible": not bool(selected.get("alerts")),
            "label": "Aucune alerte ouverte pour cette categorie. Verifier les preuves OK avant de l'indiquer en AG.",
            "href": _route_href("/comptes", categorie=selected_category_id),
        },
        "no_piece": {
            "is_visible": not bool(selected.get("pieces")),
            "label": "Aucune piece rattachee a cette categorie. Importer une facture, une ligne de depense ou demander le justificatif au syndic.",
            "href": _route_href("/depot", pipeline="compta"),
        },
        "no_question": {
            "is_visible": not bool(selected.get("questions")),
            "label": "Aucune question preparee. Creer une question depuis une alerte ou une piece manquante.",
            "href": _route_href("/comptes", categorie=selected_category_id, tab="questions"),
        },
        "no_ag_note": {
            "is_visible": not bool(selected.get("ag_section", {}).get("notes")) if isinstance(selected.get("ag_section"), dict) else True,
            "label": "Aucune note AG pour cette categorie. Ajouter une note si ce point doit etre explique aux coproprietaires.",
            "href": _route_href("/comptes", categorie=selected_category_id, tab="rapport-ag"),
        },
        "ag_report_empty": {
            "is_visible": not bool(ag_report.get("included_categories")),
            "label": "Aucun point inclus dans le rapport AG. Inclure une categorie ou une question ouverte.",
            "href": _route_href("/comptes", tab="rapport-ag"),
        },
        "export_blocked": {
            "is_visible": blocker_count > 0,
            "label": "Export non prepare car au moins un element demande une revue de diffusion.",
            "href": _route_href("/comptes", tab="rapport-ag"),
        },
    }
    export_status = "blocked" if blocker_count else "warning" if all_questions else "ready"
    detail_view = {
        "category": selected,
        "summary": selected.get("controls_summary", {}) if isinstance(selected, dict) else {},
        "alerts": selected.get("alerts", []) if isinstance(selected, dict) else [],
        "metrics": {
            "amount_charges_label": selected.get("amount_charges_label", "Montant non charge"),
            "invoice_matched_label": selected.get("matched_ratio_label", "A calculer"),
            "unmatched_invoice_count": selected.get("unmatched_invoice_count", 0),
            "missing_pieces_count": selected.get("missing_pieces_count", 0),
            "ecart_label": selected.get("ecart_label", "Aucun ecart calcule"),
            "last_invoice_label": selected.get("last_invoice_label", "Date non lue"),
        },
        "href": _route_href("/comptes", categorie=selected_category_id, tab="detail"),
    }
    pieces_view = {
        "items": selected.get("pieces", []) if isinstance(selected, dict) else [],
        "all_items": all_pieces,
        "missing": [piece for piece in all_pieces if piece.get("proof_state") == "missing"],
        "candidate": [piece for piece in all_pieces if piece.get("proof_state") == "candidate"],
        "verified": [piece for piece in all_pieces if piece.get("proof_state") == "verified"],
        "href": _route_href("/comptes", categorie=selected_category_id, tab="pieces"),
    }
    questions_view = {
        "items": selected.get("questions", []) if isinstance(selected, dict) else [],
        "all_items": all_questions,
        "draft_count": len([question for question in all_questions if question.get("status") == "draft"]),
        "include_in_ag_count": len([question for question in all_questions if question.get("include_in_ag_report")]),
        "href": _route_href("/comptes", categorie=selected_category_id, tab="questions"),
    }
    return {
        "context": {
            "coffre_label": _public_text(instance.display_name, "Copropriete"),
            "sharing_mode_label": "Prive local",
            "sharing_mode_detail": "Aucune synchronisation externe lancee depuis cette page.",
            "role_label": "Conseil syndical",
            "exercise_label": f"Exercice {year}",
            "period_label": f"01/01/{year} - 31/12/{year}",
            "year": year,
            "source_label": "Sorties ComptaScope",
            "last_updated_label": summary["last_control_label"],
            "token_query": "",
        },
        "summary": summary,
        "kpis": kpis,
        "facets": facets,
        "filters": filters,
        "categories": categories,
        "selected": selected,
        "detail": detail_view,
        "pieces": pieces_view,
        "questions": questions_view,
        "rapport_ag": ag_report,
        "questions_syndic": all_questions,
        "ag_report": ag_report,
        "tabs": tabs,
        "empty_states": empty_states,
        "export": {
            "status": export_status,
            "label": "Exporter le rapport",
            "href": _route_href("/comptes", export="rapport-ag"),
            "markdown_href": _route_href("/comptes", export="rapport-ag-md"),
            "notice": "Relire le perimetre, les questions ouvertes et les niveaux de diffusion avant partage.",
            "scopes": [
                {"id": "interne-cs", "label": "Interne CS", "href": _route_href("/comptes", export="interne-cs")},
                {"id": "rapport-ag", "label": "Rapport AG", "href": _route_href("/comptes", export="rapport-ag")},
                {"id": "questions-syndic", "label": "Questions syndic", "href": _route_href("/comptes", export="questions-syndic")},
                {"id": "pieces-a-demander", "label": "Pieces a demander", "href": _route_href("/comptes", export="pieces-a-demander")},
            ],
        },
        "before_ag": before_ag,
        "guide": accounting.get("guide") if isinstance(accounting.get("guide"), dict) else {},
    }


def _date_from_text(value: object) -> str:
    text = str(value or "")
    match = re.search(r"\b(20\d{2})[-_/]?([01]\d)[-_/]?([0-3]\d)\b", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    match = re.search(r"\b([0-3]\d)[-/]([01]\d)[-/](20\d{2})\b", text)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    return ""


def _ag_date(row: dict[str, str]) -> str:
    return _date_from_text(" ".join([row.get("ag_id", ""), row.get("source_file", ""), row.get("decision_text", "")]))


def _ag_label(ag_id: str, ag_date: str) -> str:
    if ag_date:
        return f"AG du {_date_label(ag_date)}"
    cleaned = _public_text((ag_id or "").replace("-", " "), "AG a renseigner")
    return cleaned if cleaned.upper().startswith("AG") else f"AG {cleaned}"


def _decision_status(statut: str, has_proof: bool) -> dict[str, str]:
    normalized = (statut or "").upper()
    if normalized in {"OK", "TRAITE", "CLOTURE", "CLOS", "TERMINE"}:
        return {
            "status": "clos",
            "label": "Terminee",
            "detail": "La decision dispose d'une trace de cloture.",
            "tone": "ok",
        }
    if normalized == "PREUVE_LOCALE_A_VERIFIER" or has_proof:
        return {
            "status": "a_verifier",
            "label": "Preuve a verifier",
            "detail": "Une piece locale existe, mais le conseil syndical doit confirmer ce qu'elle prouve.",
            "tone": "warn",
        }
    if normalized == "CANDIDAT_AVANT_AG":
        return {
            "status": "a_confirmer",
            "label": "Vote a confirmer",
            "detail": "La resolution vient d'une preparation ou convocation; le PV doit confirmer le vote.",
            "tone": "warn",
        }
    if normalized == "PREUVE_A_DEMANDER":
        return {
            "status": "a_demander",
            "label": "Preuve a demander",
            "detail": "La decision est suivie, mais la preuve d'execution manque encore.",
            "tone": "danger",
        }
    return {
        "status": "a_traiter",
        "label": _public_text(statut, "Action en cours"),
        "detail": "Le point demande une mise a jour lisible par le conseil syndical.",
        "tone": "info",
    }


def _proof_state(statut: str, proof_refs: list[str]) -> str:
    normalized = (statut or "").upper()
    if normalized in {"OK", "TRAITE", "CLOTURE", "CLOS", "TERMINE"}:
        return "verified"
    if normalized in {"BLOQUE", "A_REVOIR"}:
        return "blocked"
    if proof_refs:
        return "candidate"
    return "missing"


def _proof_state_label(state: str) -> str:
    return {
        "missing": "Preuve manquante",
        "candidate": "Preuve candidate",
        "verified": "Preuve validee",
        "rejected": "Preuve refusee",
        "blocked": "Verification bloquee",
    }.get(state, "Preuve a qualifier")


def _priority_label(priority: str) -> str:
    return {
        "P0": "Urgent",
        "P1": "A traiter maintenant",
        "P2": "A confirmer",
        "P3": "Suivi courant",
        "OK": "Cloturee",
    }.get((priority or "").upper(), _public_text(priority, "A confirmer"))


def _priority_reason(row: dict[str, str], proof_state: str) -> str:
    if proof_state == "missing":
        return "preuve manquante"
    if row.get("related_work_refs"):
        return "travaux"
    if row.get("related_invoice_refs"):
        return "budget"
    if (row.get("priorite") or "").upper() in {"P0", "P1"}:
        return "delai ou impact important"
    return "suivi courant"


def _due_state(due_on: str, status: str) -> str:
    if status == "clos":
        return "done"
    parsed = _parse_iso_date(due_on)
    if not parsed:
        return "missing"
    return "late" if parsed < date.today() else "planned"


def _due_label(due_on: str, due_state: str) -> str:
    parsed = _parse_iso_date(due_on)
    if due_state == "done":
        return "Cloturee"
    if due_state == "missing" or not parsed:
        return "Echeance a fixer"
    if due_state == "late":
        days = max(1, (date.today() - parsed).days)
        return f"En retard depuis {days} jours"
    return f"Echeance {_date_label(due_on)}"


def _documents_by_id(documents: dict[str, object]) -> dict[str, dict[str, str]]:
    documents_table = documents.get("documents")
    if not isinstance(documents_table, DataTable):
        return {}
    return {
        row.get("doc_id", ""): row
        for row in documents_table.rows
        if isinstance(row, dict) and row.get("doc_id")
    }


def _document_label(doc_id: str, row: dict[str, str] | None = None, fallback: str = "Piece locale") -> str:
    source = row or {}
    return _public_text(
        source.get("display_name") or source.get("file_name") or source.get("title") or doc_id,
        fallback,
    )


def _document_type_label(row: dict[str, str] | None, fallback: str = "Document") -> str:
    raw = (row or {}).get("document_type", "") or fallback
    return _public_text(raw.replace("_", " "), fallback)


def _diffusion_for_item(status: str, proof_state: str, pieces: list[dict[str, object]]) -> dict[str, object]:
    privacy_values = " ".join(str(piece.get("diffusion_label", "")) for piece in pieces).upper()
    if "BLOQUE" in privacy_values or "NE PAS DIFFUSER" in privacy_values:
        diffusion_status = "blocked"
    elif "BIFFER" in privacy_values or "ARBITRER" in privacy_values or proof_state in {"candidate", "blocked"}:
        diffusion_status = "after_redaction"
    elif status == "clos" and proof_state == "verified":
        diffusion_status = "copro_ok"
    else:
        diffusion_status = "cs_only"
    return {
        "status": diffusion_status,
        "label": {
            "local_only": "Prive local",
            "cs_only": "Conseil syndical seulement",
            "copro_ok": "Diffusion copro possible",
            "after_redaction": "A verifier avant partage",
            "blocked": "Export bloque",
        }.get(diffusion_status, "Conseil syndical seulement"),
        "reason": "Verifier les pieces et ne partager que la preuve utile.",
        "allowed_audience": "Conseil syndical" if diffusion_status != "copro_ok" else "Coproprietaires",
        "blocked_by": "verification diffusion" if diffusion_status in {"after_redaction", "blocked"} else "",
    }


def _piece_actions(doc_id: str, item_id: str) -> list[dict[str, str]]:
    return [
        {"id": "open", "label": "Ouvrir", "href": _route_href("/documents", doc_id=doc_id)},
        {"id": "attach-proof", "label": "Rattacher comme preuve", "href": _route_href("/actions", selected_item_id=item_id, tab="preuves")},
        {"id": "detach", "label": "Detacher", "href": _route_href("/actions", selected_item_id=item_id, tab="pieces")},
        {"id": "document-card", "label": "Voir la fiche document", "href": _route_href("/documents", doc_id=doc_id)},
        {"id": "redacted-copy", "label": "Preparer une version diffusable", "href": _route_href("/confidentialite", doc_id=doc_id)},
    ]


def _proof_card(
    *,
    item_id: str,
    proof_ref: str,
    label: str,
    type_label: str,
    status: str,
    source_doc_id: str = "",
    source_label: str = "",
    confirms: str = "execution",
) -> dict[str, object]:
    return {
        "proof_id": _public_text(proof_ref or _stable_action_id("PRV", 0, item_id, label), _stable_action_id("PRV", 0, item_id, label)),
        "label": _public_text(label, "Preuve attendue"),
        "type_label": _public_text(type_label, "Preuve"),
        "source_doc_id": _public_text(source_doc_id, ""),
        "source_label": _public_text(source_label or label, "A demander"),
        "captured_on": "",
        "verified_on": "",
        "status": status,
        "status_label": _proof_state_label(status),
        "confirms": confirms,
        "diffusion_label": "A verifier avant partage" if status != "verified" else "Diffusion possible apres controle",
        "restriction_reason": "" if status == "verified" else "Preuve non encore validee.",
        "href": _route_href("/actions", selected_item_id=item_id, tab="preuves"),
    }


def _piece_card(
    *,
    item_id: str,
    doc_id: str,
    label: str,
    type_label: str,
    role_label: str,
    proof_relation: str,
    doc_row: dict[str, str] | None = None,
) -> dict[str, object]:
    privacy = (doc_row or {}).get("privacy_status") or (doc_row or {}).get("privacy_review_status") or ""
    diffusion_label = {
        "DIFFUSABLE_BRUT": "Diffusion possible apres controle",
        "DIFFUSABLE_APRES_BIFFAGE": "A biffer avant partage",
        "A_BIFFER": "A biffer avant partage",
        "A_ARBITRER": "Diffusion a arbitrer",
        "BLOQUE": "Ne pas diffuser",
        "RESERVE_CS": "Conseil syndical seulement",
    }.get(privacy, "Diffusion a verifier")
    safe_doc_id = _public_text(doc_id, "")
    return {
        "doc_id": safe_doc_id,
        "label": _public_text(label, "Piece locale"),
        "type_label": _public_text(type_label, "Document"),
        "added_on": "",
        "role_label": _public_text(role_label, "annexe utile"),
        "proof_relation": proof_relation,
        "diffusion_label": diffusion_label,
        "href": _route_href("/documents", doc_id=safe_doc_id) if safe_doc_id else _route_href("/documents"),
        "download_href": _route_href("/documents", doc_id=safe_doc_id) if safe_doc_id else _route_href("/documents"),
        "actions": _piece_actions(safe_doc_id, item_id) if safe_doc_id else [],
    }


def _followup_card(
    *,
    item_id: str,
    row: dict[str, str],
    proof_expected: str,
    status: str,
    followup_id: str = "",
) -> dict[str, object]:
    resolution = _public_text(row.get("resolution_ref"), "cette decision")
    title = _public_text(row.get("decision_text"), "decision AG")
    expected = _public_text(proof_expected, "preuve attendue")
    copy_text = (
        f"Bonjour, pouvez-vous nous transmettre ou confirmer la preuve attendue pour {resolution} "
        f"({title}) : {expected} ? Merci d'indiquer la piece, la date et le contexte de la reponse."
    )
    return {
        "followup_id": _public_text(followup_id or _stable_action_id("REL", 0, item_id, expected), _stable_action_id("REL", 0, item_id, expected)),
        "label": "Preparer une relance syndic" if status in {"draft", "to_send"} else "Relance syndic a suivre",
        "status": status,
        "status_label": {
            "draft": "Brouillon a copier",
            "to_send": "A envoyer hors CoproScope",
            "sent_waiting": "Envoyee hors CoproScope, reponse attendue",
            "answered_to_check": "Reponse a verifier",
            "closed": "Relance close",
        }.get(status, "Relance a qualifier"),
        "sent_on": "",
        "channel_label": "Hors CoproScope, canal a noter",
        "recipient_label": _public_text(row.get("responsable"), "Syndic"),
        "message_excerpt": _clip(copy_text, 130),
        "expected_answer": expected,
        "answer_summary": "",
        "related_request_id": _public_text(row.get("related_request_ids"), ""),
        "copy_text": _public_text(copy_text, "Message de relance a preparer."),
        "href": _route_href("/actions", selected_item_id=item_id, tab="relance"),
    }


def _history_event(
    *,
    item_id: str,
    occurred_on: str,
    event_type: str,
    type_label: str,
    summary: str,
    actor_label: str = "CoproScope local",
    proof_ids: list[str] | None = None,
    piece_ids: list[str] | None = None,
    followup_ids: list[str] | None = None,
    is_evidence: bool = False,
    memory_note: str = "",
) -> dict[str, object]:
    event_id = _stable_action_id("EVT", 0, item_id, occurred_on, event_type, summary)
    return {
        "event_id": event_id,
        "occurred_on": occurred_on,
        "type": event_type,
        "type_label": type_label,
        "actor_label": actor_label,
        "summary": _public_text(summary, "Trace de suivi"),
        "proof_ids": proof_ids or [],
        "piece_ids": piece_ids or [],
        "followup_ids": followup_ids or [],
        "is_evidence": is_evidence,
        "memory_note": _public_text(memory_note, "A conserver pour la passation."),
    }


def _decision_register_item(
    row: dict[str, str],
    index: int,
    documents_by_id: dict[str, dict[str, str]],
) -> dict[str, object]:
    raw_id = row.get("decision_action_id") or _stable_action_id("DAP", index, row.get("ag_id", ""), row.get("resolution_ref", ""))
    item_id = _public_text(raw_id, _stable_action_id("DAP", index, row.get("ag_id", ""), row.get("resolution_ref", "")))
    proof_refs = _split_piece_refs(row.get("proof_doc_ids", ""))
    status_info = _decision_status(row.get("statut", ""), bool(proof_refs))
    status = status_info["status"]
    proof_state = _proof_state(row.get("statut", ""), proof_refs)
    due_state = _due_state(row.get("echeance", ""), status)
    ag_id = _public_text(row.get("ag_id"), "AG-SANS-DATE")
    ag_date = _ag_date(row)
    source_doc_id = _public_text(row.get("source_doc_id"), "")
    source_row = documents_by_id.get(row.get("source_doc_id", ""))

    proofs: list[dict[str, object]] = []
    if proof_refs:
        proof_status = "verified" if proof_state == "verified" else "candidate"
        for proof_ref in proof_refs:
            doc_row = documents_by_id.get(proof_ref)
            proofs.append(
                _proof_card(
                    item_id=item_id,
                    proof_ref=proof_ref,
                    label=_document_label(proof_ref, doc_row, row.get("preuve_attendue") or "Preuve candidate"),
                    type_label=_document_type_label(doc_row, row.get("proof_document_types") or "Preuve"),
                    status=proof_status,
                    source_doc_id=proof_ref,
                    source_label=_document_label(proof_ref, doc_row, "Piece locale"),
                )
            )
    else:
        proofs.append(
            _proof_card(
                item_id=item_id,
                proof_ref=f"{item_id}-missing-proof",
                label=row.get("preuve_attendue") or "Preuve a demander",
                type_label=row.get("proof_document_types") or "Preuve attendue",
                status="missing",
            )
        )

    pieces: list[dict[str, object]] = []
    if source_doc_id:
        pieces.append(
            _piece_card(
                item_id=item_id,
                doc_id=source_doc_id,
                label=_document_label(source_doc_id, source_row, row.get("source_file") or "Source du vote"),
                type_label=_document_type_label(source_row, "PV AG"),
                role_label="source du vote",
                proof_relation="none",
                doc_row=source_row,
            )
        )
    for proof_ref in proof_refs:
        doc_row = documents_by_id.get(proof_ref)
        pieces.append(
            _piece_card(
                item_id=item_id,
                doc_id=proof_ref,
                label=_document_label(proof_ref, doc_row, "Piece candidate"),
                type_label=_document_type_label(doc_row, row.get("proof_document_types") or "Preuve"),
                role_label="preuve validee" if proof_state == "verified" else "preuve candidate",
                proof_relation="verified" if proof_state == "verified" else "candidate",
                doc_row=doc_row,
            )
        )
    for ref in _split_piece_refs(row.get("related_invoice_refs", "")):
        doc_row = documents_by_id.get(ref)
        pieces.append(
            _piece_card(
                item_id=item_id,
                doc_id=ref,
                label=_document_label(ref, doc_row, "Facture liee"),
                type_label=_document_type_label(doc_row, "Facture"),
                role_label="facture",
                proof_relation="candidate",
                doc_row=doc_row,
            )
        )
    for ref in _split_piece_refs(row.get("related_work_refs", "")):
        doc_row = documents_by_id.get(ref)
        pieces.append(
            _piece_card(
                item_id=item_id,
                doc_id=ref,
                label=_document_label(ref, doc_row, "Devis ou travaux lies"),
                type_label=_document_type_label(doc_row, "Devis"),
                role_label="devis",
                proof_relation="candidate",
                doc_row=doc_row,
            )
        )

    followups: list[dict[str, object]] = []
    related_requests = _split_piece_refs(row.get("related_request_ids", ""))
    if related_requests:
        followup_status = "answered_to_check" if proof_refs else "sent_waiting"
        for request_id in related_requests:
            followups.append(
                _followup_card(
                    item_id=item_id,
                    row=row,
                    proof_expected=row.get("preuve_attendue", ""),
                    status=followup_status,
                    followup_id=request_id,
                )
            )
    elif proof_state == "missing":
        followups.append(_followup_card(item_id=item_id, row=row, proof_expected=row.get("preuve_attendue", ""), status="draft"))
    elif proof_state == "candidate":
        followups.append(
            _followup_card(item_id=item_id, row=row, proof_expected=row.get("preuve_attendue", ""), status="answered_to_check")
        )

    history = [
        _history_event(
            item_id=item_id,
            occurred_on=ag_date or row.get("echeance", ""),
            event_type="creation",
            type_label="Decision inscrite",
            summary=f"{row.get('resolution_ref') or 'Resolution'} ajoutee au registre.",
            piece_ids=[source_doc_id] if source_doc_id else [],
            memory_note="Conserver la decision et son action attendue pour la passation.",
        )
    ]
    if pieces:
        history.append(
            _history_event(
                item_id=item_id,
                occurred_on=row.get("echeance", ""),
                event_type="piece_linked",
                type_label="Piece liee",
                summary=f"{len(pieces)} piece(s) liee(s) a la decision.",
                piece_ids=[str(piece.get("doc_id", "")) for piece in pieces if piece.get("doc_id")],
                memory_note="Une piece liee n'est pas toujours une preuve validee.",
            )
        )
    if proofs:
        history.append(
            _history_event(
                item_id=item_id,
                occurred_on=row.get("echeance", ""),
                event_type="proof_added" if proof_state != "missing" else "update",
                type_label="Preuve suivie",
                summary=_proof_state_label(proof_state),
                proof_ids=[str(proof.get("proof_id", "")) for proof in proofs],
                is_evidence=proof_state == "verified",
                memory_note="Preuve validee seulement apres controle explicite.",
            )
        )
    if followups:
        history.append(
            _history_event(
                item_id=item_id,
                occurred_on=row.get("echeance", ""),
                event_type="followup_sent" if related_requests else "update",
                type_label="Relance syndic",
                summary=str(followups[0].get("status_label", "Relance a suivre")),
                followup_ids=[str(followup.get("followup_id", "")) for followup in followups],
                memory_note="Noter le canal d'envoi reel hors CoproScope.",
            )
        )
    history = sorted(history, key=lambda event: str(event.get("occurred_on") or "9999-12-31"))

    priority = (row.get("priorite") or "P2").upper()
    title = _public_text(row.get("decision_text"), row.get("resolution_ref") or "Decision AG")
    action_description = _public_text(row.get("action_attendue"), "Suivre la resolution jusqu'a sa preuve.")
    next_step = action_description
    if proof_state == "missing":
        next_step = "Ajouter une preuve ou preparer une relance syndic."
    elif proof_state == "candidate":
        next_step = "Verifier la piece candidate avant de cloturer."
    elif status == "clos":
        next_step = "Conserver la trace pour la memoire de copropriete."

    item = {
        "id": item_id,
        "ag_id": ag_id,
        "ag_label": _ag_label(ag_id, ag_date),
        "ag_date": ag_date,
        "resolution_ref": _public_text(row.get("resolution_ref"), "Resolution AG"),
        "source_doc_id": source_doc_id,
        "source_file_label": _document_label(source_doc_id, source_row, row.get("source_file") or "Source locale"),
        "title": title,
        "decision_summary": title,
        "decision_source_excerpt": _public_text(row.get("decision_text"), "Texte source a verifier dans le PV."),
        "majority_label": _public_text(row.get("majority") or row.get("majorite"), "Majorite a verifier"),
        "status": status,
        "status_label": status_info["label"],
        "status_detail": status_info["detail"],
        "status_tone": status_info["tone"],
        "priority": priority,
        "priority_label": _priority_label(priority),
        "priority_reason": _priority_reason(row, proof_state),
        "owner": _public_text(row.get("responsable"), "Conseil syndical / syndic"),
        "referent": "Conseil syndical",
        "due_on": _public_text(row.get("echeance"), ""),
        "due_label": _due_label(row.get("echeance", ""), due_state),
        "due_state": due_state,
        "progress_pct": 100 if status == "clos" else 60 if proof_state == "candidate" else 20,
        "next_step": next_step,
        "action_description": action_description,
        "proof_expected": _public_text(row.get("preuve_attendue"), "Preuve attendue a preciser"),
        "proof_state": proof_state,
        "proof_state_label": _proof_state_label(proof_state),
        "proofs": proofs,
        "pieces": pieces,
        "linked_documents": pieces,
        "followups": followups,
        "syndic_followups": followups,
        "history": history,
        "history_events": history,
        "diffusion": _diffusion_for_item(status, proof_state, pieces),
        "memory": {
            "handover_note": "Action a reprendre en passation tant qu'une preuve validee manque.",
            "timeline_ref": item_id,
            "open_risk": "preuve manquante" if proof_state == "missing" else "",
            "pack_section": "Decisions AG",
            "next_review_label": "Prochaine revue CS",
        },
        "href": _route_href("/actions", selected_item_id=item_id),
        "action_followup": {
            "label": "Suivi de l'action",
            "progress_pct": 100 if status == "clos" else 60 if proof_state == "candidate" else 20,
            "next_step": next_step,
            "href": _route_href("/actions", selected_item_id=item_id, tab="action"),
        },
        # Legacy work-item fields kept for templates that still consume the older UX shape.
        "kind": "decisions",
        "tone": status_info["tone"],
        "why": _public_text(row.get("notes"), status_info["detail"]),
        "proof": {"state": proof_state, "label": _public_text(row.get("preuve_attendue"), "Preuve attendue")},
        "action": {"label": next_step, "owner": _public_text(row.get("responsable"), "Conseil syndical / syndic")},
        "source": {"module": "DecisionOps", "object_id": item_id},
    }
    return item


def _facet_options(field: str, rows: list[dict[str, object]], labels: dict[str, str] | None = None) -> list[dict[str, object]]:
    counts = Counter(str(row.get(field, "") or "non renseigne") for row in rows)
    options = []
    for value, count in sorted(counts.items(), key=lambda item: (item[0] == "non renseigne", item[0])):
        options.append(
            {
                "value": value,
                "label": (labels or {}).get(value, value),
                "count": count,
                "href": _route_href("/actions", **{field: value}),
                "is_active": False,
            }
        )
    return options


def _register_tabs(selected: dict[str, object]) -> list[dict[str, object]]:
    item_id = selected.get("id", "")
    counts = {
        "action": 1 if selected else 0,
        "preuves": len(selected.get("proofs", [])) if isinstance(selected.get("proofs"), list) else 0,
        "pieces": len(selected.get("pieces", [])) if isinstance(selected.get("pieces"), list) else 0,
        "relance": len(selected.get("followups", [])) if isinstance(selected.get("followups"), list) else 0,
        "historique": len(selected.get("history", [])) if isinstance(selected.get("history"), list) else 0,
    }
    labels = {
        "action": "Action",
        "preuves": "Preuves",
        "pieces": "Pieces liees",
        "relance": "Relance syndic",
        "historique": "Historique",
    }
    return [
        {
            "id": tab_id,
            "label": labels[tab_id],
            "count": counts[tab_id],
            "is_active": tab_id == "action",
            "href": _route_href("/actions", selected_item_id=item_id, tab=tab_id) if item_id else _route_href("/actions", tab=tab_id),
        }
        for tab_id in ["action", "preuves", "pieces", "relance", "historique"]
    ]


def _empty_registre_selected() -> dict[str, object]:
    return {
        "id": "",
        "ag_id": "",
        "resolution_ref": "",
        "source_doc_id": "",
        "source_file_label": "",
        "title": "Aucune decision selectionnee",
        "decision_summary": "",
        "decision_source_excerpt": "",
        "majority_label": "",
        "status": "empty",
        "status_label": "Aucune decision",
        "status_detail": "Importer ou ajouter un PV pour commencer le registre.",
        "status_tone": "info",
        "priority": "",
        "priority_label": "",
        "priority_reason": "",
        "owner": "",
        "referent": "",
        "due_on": "",
        "due_label": "",
        "due_state": "missing",
        "progress_pct": 0,
        "next_step": "Ajouter ou importer un PV / registre AG pour commencer.",
        "action_description": "",
        "proof_expected": "",
        "proof_state": "missing",
        "proof_state_label": "Preuve manquante",
        "proofs": [],
        "pieces": [],
        "linked_documents": [],
        "followups": [],
        "syndic_followups": [],
        "history": [],
        "history_events": [],
        "diffusion": {
            "status": "local_only",
            "label": "Prive local",
            "reason": "Aucun export prepare.",
            "allowed_audience": "Conseil syndical",
            "blocked_by": "",
        },
        "memory": {
            "handover_note": "",
            "timeline_ref": "",
            "open_risk": "",
            "pack_section": "Decisions AG",
            "next_review_label": "",
        },
        "href": _route_href("/actions"),
        "action_followup": {"label": "Suivi de l'action", "progress_pct": 0, "next_step": "", "href": _route_href("/actions")},
    }


def _build_registre_model(
    instance: InstanceConfig,
    year: int,
    *,
    ux_items: list[dict[str, object]],
    decisions: dict[str, object],
    documents: dict[str, object],
) -> dict[str, object]:
    rows = decisions.get("rows") if isinstance(decisions.get("rows"), list) else []
    documents_index = _documents_by_id(documents)
    items = [
        _decision_register_item(row, index, documents_index)
        for index, row in enumerate(rows)
        if isinstance(row, dict)
    ]
    items = sorted(
        items,
        key=lambda item: (
            {"late": 0, "missing": 1, "planned": 2, "done": 9}.get(str(item.get("due_state")), 5),
            {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "OK": 9}.get(str(item.get("priority")), 5),
            str(item.get("due_on") or "9999-12-31"),
            str(item.get("resolution_ref", "")),
        ),
    )
    selected = next((item for item in items if item.get("status") != "clos"), items[0] if items else _empty_registre_selected())
    selected["is_selected"] = bool(selected.get("id"))
    selected["tabs"] = _register_tabs(selected)

    groups: list[dict[str, object]] = []
    grouped: dict[str, list[dict[str, object]]] = {}
    for item in items:
        grouped.setdefault(str(item.get("ag_id") or "AG-SANS-DATE"), []).append(item)
    for ag_id, group_items in sorted(grouped.items(), key=lambda pair: (pair[0],)):
        ag_date = str(group_items[0].get("ag_date") or "")
        groups.append(
            {
                "ag_id": ag_id,
                "label": _ag_label(ag_id, ag_date),
                "date": ag_date,
                "open_count": len([item for item in group_items if item.get("status") != "clos"]),
                "late_count": len([item for item in group_items if item.get("due_state") == "late"]),
                "is_expanded": any(item.get("id") == selected.get("id") for item in group_items),
                "href": _route_href("/actions", ag=ag_id),
                "items": [
                    {
                        "id": item.get("id", ""),
                        "resolution_ref": item.get("resolution_ref", ""),
                        "title": item.get("title", ""),
                        "subtitle": item.get("next_step", ""),
                        "status_label": item.get("status_label", ""),
                        "status_tone": item.get("status_tone", ""),
                        "priority_label": item.get("priority_label", ""),
                        "proof_state_label": item.get("proof_state_label", ""),
                        "owner_label": item.get("owner", ""),
                        "due_label": item.get("due_label", ""),
                        "is_selected": item.get("id") == selected.get("id"),
                        "href": item.get("href", _route_href("/actions")),
                    }
                    for item in group_items
                ],
            }
        )

    total_proofs = [
        proof
        for item in items
        for proof in (item.get("proofs", []) if isinstance(item.get("proofs"), list) else [])
        if isinstance(proof, dict)
    ]
    all_followups = [
        followup
        for item in items
        for followup in (item.get("followups", []) if isinstance(item.get("followups"), list) else [])
        if isinstance(followup, dict)
    ]
    share_blockers = len(
        [
            item
            for item in items
            if isinstance(item.get("diffusion"), dict)
            and item["diffusion"].get("status") in {"blocked", "after_redaction"}
        ]
    )
    summary_counts = {
        "total_resolutions": len(items),
        "open_actions": len([item for item in items if item.get("status") != "clos"]),
        "late_actions": len([item for item in items if item.get("due_state") == "late"]),
        "missing_proofs": len([item for item in items if item.get("proof_state") == "missing"]),
        "syndic_followups": len([followup for followup in all_followups if followup.get("status") != "closed"]),
        "verified_proofs": len([proof for proof in total_proofs if proof.get("status") == "verified"]),
        "share_blockers": share_blockers,
    }
    summary_hrefs = {
        "total_resolutions": _route_href("/actions"),
        "open_actions": _route_href("/actions", status="a_traiter"),
        "late_actions": _route_href("/actions", due_state="late"),
        "missing_proofs": _route_href("/actions", proof_state="missing"),
        "syndic_followups": _route_href("/actions", tab="relance"),
        "verified_proofs": _route_href("/actions", proof_state="verified"),
        "share_blockers": _route_href("/actions", diffusion="blocked"),
    }
    summary: dict[str, object] = {
        **summary_counts,
        **{f"{key}_href": href for key, href in summary_hrefs.items()},
        "last_updated_label": f"Situation {year}",
        "cards": [
            {"id": key, "label": label, "count": summary_counts[key], "href": summary_hrefs[key]}
            for key, label in [
                ("total_resolutions", "Resolutions"),
                ("open_actions", "Actions ouvertes"),
                ("late_actions", "En retard"),
                ("missing_proofs", "Preuves manquantes"),
                ("syndic_followups", "Relances syndic"),
                ("verified_proofs", "Preuves validees"),
                ("share_blockers", "A verifier avant partage"),
            ]
        ],
    }

    facets = {
        "ag": _facet_options("ag_id", items),
        "status": _facet_options("status", items),
        "owner": _facet_options("owner", items),
        "priority": _facet_options("priority", items, {"P0": "Critique", "P1": "Haute", "P2": "Moyenne", "P3": "Basse", "OK": "Cloturee"}),
        "proof_state": _facet_options("proof_state", items),
        "due_state": _facet_options("due_state", items),
        "scope": [{"value": "decisions", "label": "Decisions AG", "count": len(items), "href": _route_href("/actions", scope="decisions"), "is_active": True}],
    }
    filters = {
        "selected_ag": "",
        "selected_status": "",
        "selected_owner": "",
        "selected_priority": "",
        "selected_proof_state": "",
        "query": "",
        "selected_item_id": selected.get("id", ""),
    }
    empty_states = {
        "no_resolution": {
            "is_visible": not bool(items),
            "label": "Aucune decision AG chargee. Ajouter ou importer un PV / registre AG pour commencer.",
            "href": _route_href("/depot"),
        },
        "no_result": {
            "is_visible": False,
            "label": "Aucune resolution ne correspond a ce filtre. Retirer un filtre ou afficher toutes les AG.",
            "href": _route_href("/actions"),
        },
        "no_proof": {
            "is_visible": not bool(selected.get("proofs")),
            "label": "Aucune preuve validee pour cette action. Ajouter une piece, choisir une preuve existante ou preparer une demande au syndic.",
            "href": _route_href("/actions", selected_item_id=selected.get("id", ""), tab="preuves"),
        },
        "no_piece": {
            "is_visible": not bool(selected.get("pieces")),
            "label": "Aucune piece rattachee. Ajouter le PV, un devis, une facture, une reponse syndic ou une note de verification.",
            "href": _route_href("/pieces"),
        },
        "no_followup": {
            "is_visible": not bool(selected.get("followups")),
            "label": "Aucune relance tracee. Preparer un message copiable et noter le canal d'envoi.",
            "href": _route_href("/actions", selected_item_id=selected.get("id", ""), tab="relance"),
        },
        "no_history": {
            "is_visible": not bool(selected.get("history")),
            "label": "Aucune trace encore inscrite. La prochaine mise a jour creera le premier evenement.",
            "href": _route_href("/actions", selected_item_id=selected.get("id", ""), tab="historique"),
        },
        "export_blocked": {
            "is_visible": bool(share_blockers),
            "label": "Export non prepare car au moins un element demande une verification de diffusion.",
            "href": _route_href("/actions", diffusion="blocked"),
        },
    }
    export_status = "blocked" if share_blockers else "ready"
    return {
        "context": {
            "coffre_label": _public_text(instance.display_name, "Copropriete"),
            "sharing_mode_label": "Prive local",
            "sharing_mode_detail": "Aucune synchronisation externe lancee depuis cette page.",
            "role_label": "Conseil syndical",
            "as_of_label": f"Situation {year}",
        },
        "summary": summary,
        "facets": facets,
        "filters": filters,
        "ag_groups": groups,
        "items": items,
        "selected": selected,
        "tabs": selected.get("tabs", _register_tabs(selected)),
        "empty_states": empty_states,
        "export": {
            "status": export_status,
            "label": "Export a verifier avant diffusion" if share_blockers else "Export registre",
            "href": _route_href("/exports/actions.csv", scope="decisions"),
            "markdown_href": _route_href("/exports/actions.md", scope="decisions"),
            "notice": "Exporter le perimetre courant et verifier les pieces sensibles avant partage.",
        },
        "action_followup": selected.get("action_followup", {}),
        "linked_documents": selected.get("linked_documents", []),
        "proofs": selected.get("proofs", []),
        "syndic_followups": selected.get("syndic_followups", []),
        "history_events": selected.get("history_events", []),
        "work_items": ux_items,
    }


def _list_of_dicts(value: object) -> list[dict[str, object]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _action_selected_href(item_id: object, **params: object) -> str:
    return _route_href("/actions", selected=_public_text(item_id, ""), **params)


def _action_detail_model(registre: dict[str, object]) -> dict[str, object]:
    selected = registre.get("selected") if isinstance(registre.get("selected"), dict) else {}
    selected_id = _public_text(selected.get("id"), "")
    proofs = _list_of_dicts(selected.get("proofs"))
    pieces = _list_of_dicts(selected.get("pieces"))
    followups = _list_of_dicts(selected.get("followups"))
    history = _list_of_dicts(selected.get("history"))
    diffusion = selected.get("diffusion") if isinstance(selected.get("diffusion"), dict) else {}
    memory = selected.get("memory") if isinstance(selected.get("memory"), dict) else {}
    proof_state = _public_text(selected.get("proof_state"), "missing")
    expected_proof = _public_text(selected.get("proof_expected"), "Preuve attendue a preciser")
    verified_proofs = [proof for proof in proofs if proof.get("status") == "verified"]
    candidate_proofs = [proof for proof in proofs if proof.get("status") == "candidate"]
    linked_pieces = [piece for piece in pieces if piece.get("proof_relation") not in {"verified", "candidate"}]
    can_close = proof_state == "verified" and bool(verified_proofs)
    share_status = str(diffusion.get("status") or "")
    can_share = share_status == "copro_ok"
    memory_ref = _public_text(memory.get("timeline_ref") or selected_id, "")
    selected_title = _public_text(selected.get("title"), "Action a reprendre")
    selected_status = _public_text(selected.get("status"), "a_traiter")
    primary_label = "Rattacher une preuve"
    if followups or proof_state == "missing":
        primary_label = "Preparer la relance"
    if proof_state == "candidate":
        primary_label = "Verifier la piece candidate"
    if can_close:
        primary_label = "Conserver la preuve validee"

    missing_items: list[dict[str, object]] = []
    if proof_state in {"missing", "blocked"} or not verified_proofs:
        missing_items.append(
            {
                "id": _stable_action_id("MISSING", 0, selected_id, expected_proof),
                "label": expected_proof,
                "why_needed": "Prouver l'execution ou la decision avant cloture.",
                "request_href": _route_href("/demandes/relance", action_id=selected_id),
                "deposit_href": _route_href("/depot", intent="proof", action=selected_id),
            }
        )

    return {
        "context": {
            "route": "/actions",
            "selected_id": selected_id,
            "title": "Detail action",
            "visual_name": "Fiche action",
            "role_label": "Conseil syndical",
            "sharing_mode_label": "Prive local",
            "as_of_label": "Situation courante",
        },
        "navigation": {
            "back_href": _route_href("/actions"),
            "back_label": "Retour aux actions",
            "memory_href": _route_href("/chantiers", selected=memory_ref) if memory_ref else _route_href("/chantiers"),
            "memory_label": "Voir dans la memoire",
            "preserve_filters": True,
        },
        "selected": {
            "id": selected_id,
            "title": selected_title,
            "summary": _public_text(selected.get("decision_summary") or selected.get("status_detail"), "Action suivie par le conseil syndical."),
            "status": selected_status,
            "status_label": _public_text(selected.get("status_label"), _ux_status_label(selected_status)),
            "priority": _public_text(selected.get("priority"), "P2"),
            "priority_label": _public_text(selected.get("priority_label"), _priority_label(str(selected.get("priority") or "P2"))),
            "owner_label": _public_text(selected.get("owner"), "Conseil syndical"),
            "referent_label": _public_text(selected.get("referent"), "Conseil syndical"),
            "due_label": _public_text(selected.get("due_label"), "Echeance a fixer"),
            "next_step": _public_text(selected.get("next_step"), "Noter la prochaine action et la preuve attendue."),
        },
        "source": {
            "kind_label": "Decision ou demande source",
            "label": _public_text(selected.get("resolution_ref") or selected.get("source_file_label"), "Source a confirmer"),
            "summary": _public_text(selected.get("decision_source_excerpt"), "Source a relire avant cloture."),
            "source_href": _action_selected_href(selected_id, tab="historique") if selected_id else _route_href("/actions"),
            "certainty_label": "Preuve validee" if can_close else "A confirmer par piece ou justification.",
        },
        "status": {
            "delay_label": _public_text(selected.get("due_label"), "En attente"),
            "blocked_reason": "" if can_close else "Preuve ou justification attendue.",
            "can_close": can_close,
            "close_disabled_reason": "" if can_close else "La preuve attendue n'est pas encore validee.",
        },
        "proofs": {
            "expected_label": expected_proof,
            "state": proof_state,
            "state_label": _proof_state_label(proof_state),
            "verified": verified_proofs,
            "candidates": candidate_proofs,
            "linked_pieces": linked_pieces,
        },
        "missing": {
            "items": missing_items,
            "summary_label": "Aucun manque bloquant." if not missing_items else f"{len(missing_items)} piece ou preuve attendue.",
        },
        "linked": {
            "documents": [
                {
                    "id": piece.get("doc_id", ""),
                    "label": piece.get("label", "Document lie"),
                    "href": piece.get("href", _route_href("/documents")),
                    "why_linked": piece.get("role_label", "Piece utile au suivi."),
                }
                for piece in pieces[:8]
            ],
            "events": [
                {
                    "id": memory_ref or selected_id,
                    "label": _public_text(memory.get("pack_section"), "Memoire de copropriete"),
                    "href": _route_href("/chantiers", selected=memory_ref or selected_id),
                }
            ]
            if (memory_ref or selected_id)
            else [],
            "requests": [
                {
                    "id": followup.get("related_request_id", ""),
                    "label": followup.get("label", "Relance liee"),
                    "href": followup.get("href", _action_selected_href(selected_id, tab="relance")),
                }
                for followup in followups
                if followup.get("related_request_id")
            ],
            "decisions": [
                {
                    "id": selected_id,
                    "label": _public_text(selected.get("resolution_ref"), "Decision suivie"),
                    "href": _action_selected_href(selected_id),
                }
            ]
            if selected_id
            else [],
        },
        "followups": {
            "status_label": _public_text((followups[0].get("status_label") if followups else ""), "Brouillon a preparer"),
        "primary_href": _route_href("/demandes/relance", action_id=selected_id) if selected_id else _route_href("/demandes/relance"),
            "last_followup_label": _public_text((followups[0].get("label") if followups else ""), "Aucune relance tracee"),
            "items": followups,
        },
        "history": [
            {
                "date_label": _date_label(event.get("occurred_on"), "Date a noter"),
                "label": _public_text(event.get("type_label"), "Mise a jour"),
                "detail": _public_text(event.get("summary"), "Trace courte a completer."),
            }
            for event in history[:8]
        ],
        "share": {
            "level": _public_text(diffusion.get("status"), "conseil_syndical"),
            "label": _public_text(diffusion.get("label"), "Conseil syndical"),
            "can_share": can_share,
            "can_share_label": "Partage possible apres controle" if can_share else "Diffusion a verifier",
            "reason": _public_text(diffusion.get("reason"), "La preuve ou la piece peut contenir des informations a limiter."),
            "review_href": _route_href("/confidentialite", scope="action", selected=selected_id),
        },
        "handover": {
            "note": _public_text(memory.get("handover_note"), "Ne pas clore sans preuve ou justification ecrite."),
            "is_ready": can_close and can_share,
            "missing_for_handover": []
            if can_close and can_share
            else [
                label
                for label in ["preuve validee" if not can_close else "", "statut diffusion" if not can_share else ""]
                if label
            ],
        },
        "actions": {
            "primary": {"label": primary_label, "href": _route_href("/demandes/relance", action_id=selected_id) if primary_label == "Preparer la relance" else _action_selected_href(selected_id, tab="preuves")},
            "secondary": [
                {"label": "Rattacher une piece", "href": _route_href("/depot", intent="proof", action=selected_id)},
                {"label": "Voir dans la memoire", "href": _route_href("/chantiers", selected=memory_ref or selected_id)},
            ],
            "export": {
                "label": "Preparer un extrait",
                "href": _route_href("/exports/passation", scope="action", selected=selected_id),
                "requires_preview": True,
                "disabled": False,
            },
        },
        "empty_states": {
            "not_found": "Action introuvable. Revenir a la liste des actions.",
            "none_selected": "Selectionnez une action pour voir la preuve attendue, le suivi et la prochaine etape.",
            "no_proof": "Aucune preuve validee. Ajouter une piece, choisir un document candidat ou preparer une demande.",
            "no_followup": "Aucune relance tracee. Preparer un message copiable et noter le canal d'envoi.",
        },
    }


def _priority_late_action_item(action: dict[str, str], index: int) -> dict[str, object]:
    item_id = _public_text(action.get("id"), _stable_action_id("ACT", index, action.get("title", ""), action.get("source", "")))
    priority = _public_text(action.get("priority"), "P2")
    status = _public_text(action.get("status"), "a_traiter")
    expected_proof = _public_text(action.get("evidence"), "Preuve attendue a preciser")
    next_step = _public_text(action.get("next_step"), "Verifier le point et noter la prochaine action.")
    domain_label = _public_text(action.get("domain_label"), "Suivi CS")
    return {
        "id": item_id,
        "title": _public_text(action.get("title"), "Action a traiter"),
        "domain_label": domain_label,
        "priority": priority,
        "priority_label": _priority_label(priority),
        "status": status,
        "status_label": _ux_status_label(status),
        "due_date": "",
        "delay_label": "En retard ou prioritaire" if priority in {"P0", "P1"} else "A reprendre",
        "owner": _public_text(action.get("owner"), "Conseil syndical"),
        "expected_proof": expected_proof,
        "next_step": next_step,
        "href": _action_selected_href(item_id),
        "followup_href": _route_href("/demandes/relance", action_id=item_id),
        "piece_href": _route_href("/pieces", missing_for=item_id),
        "memory_href": _public_href(action.get("href"), _route_href("/chantiers")),
        "diffusion_label": "Conseil syndical",
        "can_close": status == "clos",
    }


def _missing_piece_view_item(item: dict[str, object], index: int) -> dict[str, object]:
    piece = _public_text(item.get("piece"), "Piece attendue")
    point_id = _public_text(item.get("point_id"), _stable_action_id("POINT", index, piece))
    proof_ref = _public_text(item.get("proof_ref"), "")
    status = "candidate" if proof_ref else "a_demander"
    return {
        "id": _stable_action_id("MISSING-PIECE", index, point_id, piece),
        "expected_piece": piece,
        "rubric_label": _public_text(item.get("point_type"), "Piece"),
        "reason": _public_text(item.get("action") or item.get("next_step"), "Necessaire pour avancer sans conclure sans preuve."),
        "proof_purpose": "Prouver ou confirmer le point rattache avant passation.",
        "criticality": _public_text(item.get("priority"), "P2"),
        "criticality_label": _priority_label(str(item.get("priority") or "P2")),
        "status": status,
        "status_label": "Piece candidate a verifier" if proof_ref else "A demander",
        "source_label": _public_text(item.get("source"), "Source a confirmer"),
        "related_action_id": point_id,
        "related_event_id": point_id,
        "request_href": _route_href("/demandes/relance", action_id=point_id),
        "deposit_href": _route_href("/depot", intent="proof", missing_for=point_id),
        "candidate_docs": [
            {
                "id": proof_ref,
                "label": proof_ref,
                "status_label": "Piece candidate a verifier",
                "href": _route_href("/documents", doc_id=proof_ref),
            }
        ]
        if proof_ref
        else [],
        "diffusion_label": "Conseil syndical",
        "next_step": _public_text(item.get("next_step"), "Demander ou rattacher la piece attendue."),
    }


def _ux_piece_status(item: dict[str, object]) -> str:
    status = str(item.get("status") or "").upper()
    has_local_proof = bool(item.get("has_local_proof"))
    requires_action = bool(item.get("requires_action", True))
    if has_local_proof and requires_action:
        return "a_verifier"
    if has_local_proof:
        return "rattachee"
    if status in {"ABSENT", "MISSING", "A_DEMANDER", "PREUVE_A_DEMANDER", "EN_ATTENTE_PREUVE"}:
        return "a_demander"
    return "a_deposer" if requires_action else "rattachee"


def _ux_piece_novice_status(status: str) -> dict[str, object]:
    labels = {
        "a_demander": (
            "Il faut demander ce document",
            "Aucune preuve locale n'est rattachee: preparez une relance, puis ajoutez la reponse au depot.",
            "danger",
        ),
        "a_deposer": (
            "A ajouter au depot",
            "Le point attend un fichier: ajoutez-le localement puis rattachez-le comme preuve.",
            "warn",
        ),
        "a_verifier": (
            "Un document local existe",
            "Relisez le document lie avant de dire que la preuve est validee.",
            "info",
        ),
        "rattachee": (
            "Document rattache",
            "La piece existe dans le coffre local; gardez le lien pour la passation.",
            "ok",
        ),
        "exemple": (
            "Exemple fictif",
            "Exemple de piece manquante pour guider l'ecran quand aucun registre n'est encore charge.",
            "muted",
        ),
    }
    label, detail, tone = labels.get(status, labels["a_demander"])
    return {"label": label, "detail": detail, "tone": tone}


def _ux_piece_linked_documents(
    proof_ref: object,
    documents_by_id: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    linked: list[dict[str, object]] = []
    seen: set[str] = set()
    for doc_id in _split_piece_refs(str(proof_ref or "")):
        safe_doc_id = _public_text(doc_id, "")
        if not safe_doc_id or safe_doc_id in seen:
            continue
        seen.add(safe_doc_id)
        doc_row = documents_by_id.get(doc_id, {})
        linked.append(
            {
                "id": safe_doc_id,
                "label": _document_label(safe_doc_id, doc_row, "Document lie"),
                "type_label": _document_type_label(doc_row, "Document"),
                "status_label": "Document local a verifier",
                "href": _route_href("/documents", doc_id=safe_doc_id),
            }
        )
    return linked


def _ux_piece_contract_item(
    item: dict[str, object],
    index: int,
    documents_by_id: dict[str, dict[str, str]],
) -> dict[str, object]:
    expected_piece = _public_text(item.get("piece"), "Piece attendue")
    point_id = _public_text(item.get("point_id"), _stable_action_id("POINT", index, expected_piece))
    request_id = _public_text(item.get("request_id"), "")
    status = _ux_piece_status(item)
    novice_status = _ux_piece_novice_status(status)
    linked_documents = _ux_piece_linked_documents(item.get("proof_ref"), documents_by_id)
    relance_href = _route_href("/demandes/relance", action_id=point_id, request_id=request_id)
    deposit_href = _route_href("/depot", intent="proof", missing_for=point_id, request_id=request_id)
    documents_href = linked_documents[0]["href"] if linked_documents else _route_href("/documents", missing_for=point_id)
    if status == "a_verifier":
        primary_action = {"id": "verify-document", "label": "Verifier le document lie", "href": documents_href}
    elif status == "a_deposer":
        primary_action = {"id": "add-from-depot", "label": "Ajouter depuis le depot", "href": deposit_href}
    elif status == "rattachee":
        primary_action = {"id": "keep-link", "label": "Conserver le lien", "href": _route_href("/pieces", piece=point_id)}
    else:
        primary_action = {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href}
    return {
        "id": _stable_action_id("UX-PIECE", index, point_id, expected_piece),
        "expected_piece": expected_piece,
        "rubric_label": _public_text(item.get("point_type"), "Piece"),
        "point_label": _public_text(item.get("point"), "Point a rattacher"),
        "source_label": _public_text(item.get("source"), "Source a confirmer"),
        "status": status,
        "status_label": novice_status["label"],
        "novice_status": novice_status,
        "priority": _public_text(item.get("priority"), "P2"),
        "priority_label": _priority_label(str(item.get("priority") or "P2")),
        "reason": _public_text(item.get("action") or item.get("next_step"), "Piece necessaire pour avancer."),
        "next_step": _public_text(item.get("next_step"), "Demander, deposer ou verifier la piece attendue."),
        "proof_badge": _public_text(item.get("proof_badge"), "preuve manquante"),
        "signature_badge": _public_text(item.get("signature_badge"), ""),
        "privacy_badge": _public_text(item.get("privacy_badge"), ""),
        "confidence_badge": _public_text(item.get("confidence_badge"), ""),
        "is_fictive": False,
        "requires_real_validation": True,
        "related": {
            "action_id": point_id,
            "request_id": request_id,
            "event_id": point_id,
        },
        "linked_documents": linked_documents,
        "linked_documents_count": len(linked_documents),
        "request_href": relance_href,
        "deposit_href": deposit_href,
        "documents_href": documents_href,
        "href": _route_href("/pieces", piece=point_id),
        "primary_action": primary_action,
        "actions": [
            {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href},
            {"id": "add-from-depot", "label": "Ajouter depuis le depot", "href": deposit_href},
            {"id": "see-documents", "label": "Voir documents lies", "href": documents_href},
        ],
    }


def _ux_piece_from_comptes_piece(piece: dict[str, object], index: int) -> dict[str, object]:
    proof_state = str(piece.get("proof_state") or "")
    if proof_state == "verified":
        status = "rattachee"
    elif proof_state == "candidate":
        status = "a_verifier"
    else:
        status = "a_demander"
    piece_id = _public_text(piece.get("piece_id"), _stable_action_id("PCE-COMP", index, str(piece.get("label", ""))))
    label = _public_text(piece.get("label"), "Piece comptable attendue")
    category_id = _public_text(piece.get("category_id"), "")
    doc_id = _public_text(piece.get("doc_id"), "")
    relance_href = _route_href("/demandes/relance", source="comptes", piece_id=piece_id, categorie=category_id)
    deposit_href = _route_href("/depot", intent="proof", source="comptes", piece_id=piece_id, categorie=category_id)
    action_href = _public_href(piece.get("href"), _route_href("/comptes", proof_state="missing"))
    documents_href = _route_href("/documents", doc_id=doc_id) if doc_id else action_href
    novice_status = _ux_piece_novice_status(status)
    linked_documents = (
        [
            {
                "id": doc_id,
                "label": label,
                "type_label": _public_text(piece.get("type_label"), "Document comptable"),
                "status_label": "Document local a verifier",
                "href": documents_href,
            }
        ]
        if doc_id
        else []
    )
    primary_action = (
        {"id": "verify-document", "label": "Verifier le document lie", "href": documents_href}
        if status == "a_verifier"
        else {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href}
    )
    expected_piece = label if label.lower().startswith("justificatif") else f"Justificatif comptable - {label}"
    return {
        "id": _stable_action_id("UX-PIECE-COMP", index, piece_id, label),
        "expected_piece": expected_piece,
        "rubric_label": "Comptes et factures",
        "point_label": _public_text(piece.get("match_status_label"), "Controle comptable a justifier"),
        "source_label": "ComptaScope",
        "status": status,
        "status_label": novice_status["label"],
        "novice_status": novice_status,
        "priority": "P1" if status == "a_demander" else "P2",
        "priority_label": _priority_label("P1" if status == "a_demander" else "P2"),
        "reason": _public_text(piece.get("proof_state_label") or piece.get("match_status_label"), "Justificatif a demander ou rattacher."),
        "next_step": "Preparer une relance au syndic ou ajouter le justificatif depuis le depot.",
        "proof_badge": "preuve manquante" if status == "a_demander" else "preuve locale",
        "signature_badge": "",
        "privacy_badge": "",
        "confidence_badge": "",
        "is_fictive": False,
        "requires_real_validation": True,
        "related": {
            "action_id": piece_id,
            "request_id": "",
            "event_id": piece_id,
        },
        "linked_documents": linked_documents,
        "linked_documents_count": len(linked_documents),
        "request_href": relance_href,
        "deposit_href": deposit_href,
        "documents_href": documents_href,
        "href": action_href,
        "action_href": action_href,
        "action_label": "Controle comptes",
        "owner_label": "Syndic ou conseil syndical",
        "proof_expected_label": expected_piece,
        "primary_action": primary_action,
        "actions": [
            {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href},
            {"id": "add-from-depot", "label": "Ajouter depuis le depot", "href": deposit_href},
            {"id": "see-documents", "label": "Voir documents lies", "href": documents_href},
            {"id": "open-comptes", "label": "Voir dans les comptes", "href": action_href},
        ],
    }


def _ux_piece_from_action(action: dict[str, str], index: int) -> dict[str, object]:
    action_id = _public_text(action.get("id"), _stable_action_id("ACT", index, action.get("title", "")))
    expected_piece = _public_text(action.get("evidence"), "Preuve attendue a preciser")
    title = _public_text(action.get("title"), "Action a traiter")
    relance_href = _route_href("/demandes/relance", action_id=action_id)
    deposit_href = _route_href("/depot", intent="proof", action=action_id)
    action_href = _action_selected_href(action_id)
    novice_status = _ux_piece_novice_status("a_demander")
    return {
        "id": _stable_action_id("UX-PIECE-ACT", index, action_id, expected_piece),
        "expected_piece": expected_piece,
        "rubric_label": _public_text(action.get("domain_label"), "Action"),
        "point_label": title,
        "source_label": _public_text(action.get("source"), "Registre actions"),
        "status": "a_demander",
        "status_label": novice_status["label"],
        "novice_status": novice_status,
        "priority": _public_text(action.get("priority"), "P2"),
        "priority_label": _priority_label(str(action.get("priority") or "P2")),
        "reason": _public_text(action.get("detail") or action.get("next_step"), "Preuve attendue pour cloturer l'action."),
        "next_step": _public_text(action.get("next_step"), "Preparer une relance ou ajouter la preuve depuis le depot."),
        "proof_badge": "preuve manquante",
        "signature_badge": "",
        "privacy_badge": "",
        "confidence_badge": "",
        "is_fictive": False,
        "requires_real_validation": True,
        "related": {
            "action_id": action_id,
            "request_id": "",
            "event_id": action_id,
        },
        "linked_documents": [],
        "linked_documents_count": 0,
        "request_href": relance_href,
        "deposit_href": deposit_href,
        "documents_href": _route_href("/documents", action=action_id),
        "href": action_href,
        "action_href": action_href,
        "action_label": title,
        "owner_label": _public_text(action.get("owner"), "Syndic ou conseil syndical"),
        "proof_expected_label": expected_piece,
        "primary_action": {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href},
        "actions": [
            {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href},
            {"id": "add-from-depot", "label": "Ajouter depuis le depot", "href": deposit_href},
            {"id": "open-action", "label": "Voir action", "href": action_href},
        ],
    }


def _ux_piece_fictive_examples() -> list[dict[str, object]]:
    examples = [
        (
            "EXEMPLE-ASSURANCE",
            "Attestation assurance immeuble recente",
            "Assurance",
            "Demander l'attestation en cours de validite au syndic.",
        ),
        (
            "EXEMPLE-TRAVAUX",
            "Ordre de service signe",
            "Travaux",
            "Obtenir la version signee avant de clore la decision.",
        ),
    ]
    items: list[dict[str, object]] = []
    for index, (point_id, expected_piece, rubric, reason) in enumerate(examples, start=1):
        relance_href = _route_href("/demandes/relance", action_id=point_id)
        deposit_href = _route_href("/depot", intent="proof", missing_for=point_id)
        novice_status = _ux_piece_novice_status("exemple")
        items.append(
            {
                "id": _stable_action_id("UX-PIECE-EXEMPLE", index, point_id, expected_piece),
                "expected_piece": expected_piece,
                "rubric_label": rubric,
                "point_label": "Exemple de point a rattacher",
                "source_label": "Exemple local",
                "status": "exemple",
                "status_label": novice_status["label"],
                "novice_status": novice_status,
                "priority": "P2",
                "priority_label": _priority_label("P2"),
                "reason": reason,
                "next_step": "Remplacer cet exemple par une vraie piece issue du depot ou d'une relance.",
                "is_fictive": True,
                "requires_real_validation": True,
                "linked_documents": [],
                "linked_documents_count": 0,
                "request_href": relance_href,
                "deposit_href": deposit_href,
                "documents_href": _route_href("/documents"),
                "href": _route_href("/pieces", piece=point_id),
                "primary_action": {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href},
                "actions": [
                    {"id": "prepare-relance", "label": "Preparer une relance", "href": relance_href},
                    {"id": "add-from-depot", "label": "Ajouter depuis le depot", "href": deposit_href},
                ],
            }
        )
    return items


def _build_pieces_ux_model(
    *,
    piece_workshop: dict[str, object],
    documents: dict[str, object],
    action_items: list[dict[str, str]],
    comptes: dict[str, object],
) -> dict[str, object]:
    documents_by_id = _documents_by_id(documents)
    source_items = _list_of_dicts(piece_workshop.get("items"))
    actionable_source = [
        item
        for item in source_items
        if bool(item.get("requires_action", True))
    ]
    items = [
        _ux_piece_contract_item(item, index, documents_by_id)
        for index, item in enumerate(actionable_source[:80], start=1)
    ]
    comptes_pieces = comptes.get("pieces") if isinstance(comptes.get("pieces"), dict) else {}
    comptes_missing = _list_of_dicts(comptes_pieces.get("missing") if isinstance(comptes_pieces, dict) else [])
    comptes_candidate = _list_of_dicts(comptes_pieces.get("candidate") if isinstance(comptes_pieces, dict) else [])
    for index, piece in enumerate((comptes_missing + comptes_candidate)[:80], start=len(items) + 1):
        items.append(_ux_piece_from_comptes_piece(piece, index))
    represented_action_ids = {
        str((item.get("related") or {}).get("action_id") or "")
        for item in items
        if isinstance(item.get("related"), dict)
    }
    represented_piece_keys = {
        str(item.get("expected_piece") or "").strip().lower()
        for item in items
        if str(item.get("expected_piece") or "").strip()
    }
    for index, action in enumerate(action_items, start=len(items) + 1):
        if action.get("status") != "a_demander":
            continue
        if action.get("domain") == "comptes":
            continue
        action_id = _public_text(action.get("id"), "")
        if action_id and action_id in represented_action_ids:
            continue
        expected_piece_key = _public_text(action.get("evidence"), "").strip().lower()
        if expected_piece_key and expected_piece_key in represented_piece_keys:
            continue
        items.append(_ux_piece_from_action(action, index))
        if action_id:
            represented_action_ids.add(action_id)
        if expected_piece_key:
            represented_piece_keys.add(expected_piece_key)
    missing_items = [item for item in items if item.get("status") in {"a_demander", "a_deposer"}]
    verify_items = [item for item in items if item.get("status") == "a_verifier"]
    linked_documents_count = sum(int(item.get("linked_documents_count") or 0) for item in items)
    examples = _ux_piece_fictive_examples() if not items else []
    by_status = Counter(str(item.get("status", "")) for item in items)
    by_rubric = Counter(str(item.get("rubric_label", "Piece")) for item in items)
    piece_summary = piece_workshop.get("summary") if isinstance(piece_workshop.get("summary"), dict) else {}
    total_slots = max(int(piece_summary.get("total") or len(items) or len(examples) or 1), 1)
    completed = int(piece_summary.get("with_local_proof") or linked_documents_count or 0)
    completion_pct = max(0, min(100, round(100 * completed / total_slots)))
    return {
        "context": {
            "route": "/pieces?proof=missing",
            "title": "Pieces manquantes",
            "subtitle": "Demander, deposer ou verifier les pieces attendues avant de clore un point.",
            "role_label": "Conseil syndical",
        },
        "summary": {
            "total_actionable": len(items),
            "missing_count": len([item for item in items if item.get("status") == "a_demander"]),
            "to_deposit_count": len([item for item in items if item.get("status") == "a_deposer"]),
            "to_verify_count": len(verify_items),
            "linked_documents_count": linked_documents_count,
            "fictive_count": len(examples),
            "completion_pct": completion_pct,
        },
        "primary_actions": [
            {"id": "prepare-relance", "label": "Preparer une relance", "href": _route_href("/demandes/relance")},
            {"id": "add-from-depot", "label": "Ajouter depuis le depot", "href": _route_href("/depot", intent="proof")},
            {"id": "see-documents", "label": "Voir documents lies", "href": _route_href("/documents")},
        ],
        "status_legend": [
            {"status": key, **_ux_piece_novice_status(key)}
            for key in ["a_demander", "a_deposer", "a_verifier", "rattachee", "exemple"]
        ],
        "filters": {
            "status": [
                {
                    "value": status,
                    "label": _ux_piece_novice_status(status)["label"],
                    "count": count,
                    "href": _route_href("/pieces", proof=status),
                    "is_active": status in {"a_demander", "a_deposer"},
                }
                for status, count in sorted(by_status.items())
            ],
            "rubrics": [
                {
                    "value": rubric,
                    "label": rubric,
                    "count": count,
                    "href": _route_href("/pieces", rubrique=rubric),
                }
                for rubric, count in sorted(by_rubric.items())
            ],
        },
        "items": items,
        "missing": missing_items,
        "to_verify": verify_items,
        "linked_documents": [
            document
            for item in items
            for document in _list_of_dicts(item.get("linked_documents"))
        ][:20],
        "selected": items[0] if items else {},
        "empty_state": {
            "is_visible": not bool(items),
            "label": "Aucune piece manquante exploitable dans les registres charges.",
            "next_step": "Ajouter une piece au depot ou generer les rapports de completude documentaire.",
            "deposit_href": _route_href("/depot", intent="proof"),
            "relance_href": _route_href("/demandes/relance"),
            "examples": examples,
        },
    }


def _syndic_followup_view_item(action: dict[str, str], index: int) -> dict[str, object]:
    item_id = _public_text(action.get("id"), _stable_action_id("FOLLOWUP", index, action.get("title", "")))
    expected_proof = _public_text(action.get("evidence"), "Preuve attendue a preciser")
    title = _public_text(action.get("title"), "Demande au syndic")
    status = "ready_to_copy" if action.get("status") == "a_demander" else "draft"
    body = (
        f"Bonjour, pouvez-vous nous transmettre ou confirmer la piece suivante: {expected_proof} ? "
        "Merci de preciser la date, la source et le contexte de la reponse."
    )
    return {
        "id": _stable_action_id("RELANCE", index, item_id, expected_proof),
        "title": title,
        "related_action_id": item_id,
        "related_piece_id": _stable_action_id("MISSING-PIECE", index, item_id, expected_proof),
        "status": status,
        "status_label": "Pret a copier" if status == "ready_to_copy" else "Brouillon a relire",
        "priority": _public_text(action.get("priority"), "P2"),
        "priority_label": _priority_label(str(action.get("priority") or "P2")),
        "channel_label": "Email syndic ou canal a noter",
        "last_request_label": "Aucune demande tracee",
        "proposed_followup_label": "A envoyer hors CoproScope apres relecture",
        "expected_proof": expected_proof,
        "draft": {
            "subject": f"Demande de piece - {title}",
            "body": _public_text(body, "Message de relance a preparer."),
            "copy_warning": "CoproScope prepare le texte; l'envoi reste externe et doit etre confirme.",
        },
        "copy_action": {"label": "Copier le message", "disabled": False, "disabled_reason": ""},
        "mark_sent_action": {
            "label": "Noter l'envoi hors CoproScope apres copie",
            "requires_confirmation": True,
            "disabled": False,
            "disabled_reason": "",
        },
        "answer_href": _route_href("/depot", intent="syndic-answer", action=item_id),
        "memory_href": _public_href(action.get("href"), _route_href("/chantiers")),
        "href": _route_href("/demandes/relance", action_id=item_id),
    }


def _missing_piece_view_from_ux_piece(item: dict[str, object], index: int) -> dict[str, object]:
    expected_piece = _public_text(item.get("expected_piece"), "Piece attendue")
    related = item.get("related") if isinstance(item.get("related"), dict) else {}
    related_action_id = _public_text(related.get("action_id"), _stable_action_id("MISSING-PIECE", index, expected_piece))
    candidate_docs = _list_of_dicts(item.get("linked_documents")) if item.get("status") == "a_verifier" else []
    priority = _public_text(item.get("priority"), "P2")
    return {
        "id": _public_text(item.get("id"), _stable_action_id("MISSING-PIECE", index, related_action_id, expected_piece)),
        "expected_piece": expected_piece,
        "proof_expected_label": _public_text(item.get("proof_expected_label") or expected_piece, expected_piece),
        "rubric_label": _public_text(item.get("rubric_label"), "Piece"),
        "reason": _public_text(item.get("reason") or item.get("next_step"), "Necessaire pour avancer sans conclure sans preuve."),
        "proof_purpose": "Prouver ou confirmer le point rattache avant passation.",
        "criticality": priority,
        "criticality_label": _priority_label(priority),
        "status": _public_text(item.get("status"), "a_demander"),
        "status_label": _public_text(item.get("status_label"), "A demander"),
        "source_label": _public_text(item.get("source_label"), "Source a confirmer"),
        "owner_label": _public_text(item.get("owner_label"), "Syndic ou source a confirmer"),
        "related_action_id": related_action_id,
        "related_event_id": _public_text(related.get("event_id"), related_action_id),
        "request_href": _public_href(item.get("request_href"), _route_href("/demandes/relance", action_id=related_action_id)),
        "deposit_href": _public_href(item.get("deposit_href"), _route_href("/depot", intent="proof", missing_for=related_action_id)),
        "action_href": _public_href(item.get("action_href") or item.get("href"), _action_selected_href(related_action_id)),
        "action_label": _public_text(item.get("action_label") or item.get("point_label"), "Action a ouvrir"),
        "candidate_docs": [
            {
                "id": _public_text(document.get("id"), ""),
                "label": _public_text(document.get("label"), "Document lie"),
                "status_label": _public_text(document.get("status_label"), "Piece candidate a verifier"),
                "href": _public_href(document.get("href"), "/documents"),
            }
            for document in candidate_docs
        ],
        "diffusion_label": "Conseil syndical",
        "next_step": _public_text(item.get("next_step"), "Demander ou rattacher la piece attendue."),
    }


def _build_priority_views(
    *,
    action_items: list[dict[str, str]],
    piece_workshop: dict[str, object],
    pieces_model: dict[str, object] | None = None,
) -> dict[str, object]:
    late_source = [
        action
        for action in action_items
        if action.get("priority", "").upper() in {"P0", "P1"} or action.get("status") in {"bloque", "a_demander"}
    ]
    late_items = [_priority_late_action_item(action, index) for index, action in enumerate(late_source[:30], start=1)]
    pieces_model = pieces_model if isinstance(pieces_model, dict) else {}
    merged_missing_source = _list_of_dicts(pieces_model.get("missing"))
    if merged_missing_source:
        missing_items = [
            _missing_piece_view_from_ux_piece(item, index)
            for index, item in enumerate(merged_missing_source[:30], start=1)
        ]
    else:
        missing_source = _list_of_dicts(piece_workshop.get("to_request"))
        missing_items = [_missing_piece_view_item(item, index) for index, item in enumerate(missing_source[:30], start=1)]
    syndic_source = [
        action
        for action in action_items
        if action.get("channel") == "syndic"
        or action.get("status") == "a_demander"
        or "syndic" in " ".join([action.get("owner", ""), action.get("title", ""), action.get("next_step", "")]).lower()
    ]
    followup_items = [_syndic_followup_view_item(action, index) for index, action in enumerate(syndic_source[:30], start=1)]
    missing_by_rubric = Counter(str(item.get("rubric_label", "Piece")) for item in missing_items)
    pieces_summary = pieces_model.get("summary") if isinstance(pieces_model.get("summary"), dict) else {}
    followup_tabs = [
        {"id": "a_preparer", "label": "A preparer", "count": len([item for item in followup_items if item.get("status") == "draft"]), "is_active": True},
        {"id": "pretes", "label": "Pretes a copier", "count": len([item for item in followup_items if item.get("status") == "ready_to_copy"]), "is_active": False},
        {"id": "reponses", "label": "Reponses a verifier", "count": 0, "is_active": False},
        {"id": "cloturees", "label": "Cloturees", "count": 0, "is_active": False},
    ]
    return {
        "late_actions": {
            "context": {
                "route": "/actions?view=retards",
                "title": "Toutes les actions en retard",
                "subtitle": "Ce qui depasse son echeance ou bloque une preuve attendue.",
            },
            "summary": {
                "total": len(late_items),
                "critical_count": len([item for item in late_items if item.get("priority") in {"P0", "P1"}]),
                "missing_proof_count": len([item for item in late_items if item.get("status") == "a_demander"]),
                "syndic_ready_count": len([item for item in followup_items if item.get("status") == "ready_to_copy"]),
                "oldest_delay_label": late_items[0]["delay_label"] if late_items else "Aucun retard",
            },
            "filters": {
                "priority_href": _route_href("/actions", priority="P1"),
                "syndic_href": _route_href("/actions", scope="syndic"),
                "to_request_href": _route_href("/actions", status="a_demander"),
            },
            "items": late_items,
            "selected": late_items[0] if late_items else {},
            "empty_state": {
                "is_visible": not bool(late_items),
                "label": "Aucune action en retard. Les prochaines echeances restent visibles dans la memoire.",
                "href": _route_href("/chantiers"),
            },
        },
        "missing_pieces": {
            "context": {
                "route": "/pieces?proof=missing",
                "title": "Pieces manquantes",
                "subtitle": "Les pieces a obtenir, verifier ou rattacher comme preuve.",
            },
            "summary": {
                "total": len(missing_items),
                "critical_count": len([item for item in missing_items if item.get("criticality") in {"P0", "P1"}]),
                "candidate_count": int(pieces_summary.get("to_verify_count") or len([item for item in missing_items if item.get("candidate_docs")])),
                "to_request_count": len([item for item in missing_items if item.get("status") == "a_demander"]),
                "completion_pct": int(pieces_summary.get("completion_pct") or 0)
                if pieces_summary
                else int(piece_workshop.get("summary", {}).get("with_local_proof", 0) or 0)
                if isinstance(piece_workshop.get("summary"), dict)
                else 0,
            },
            "groups": [
                {"id": _stable_action_id("RUBRIC", index, rubric), "label": rubric, "count": count}
                for index, (rubric, count) in enumerate(sorted(missing_by_rubric.items()), start=1)
            ],
            "items": missing_items,
            "selected": missing_items[0] if missing_items else {},
            "empty_state": {
                "is_visible": not bool(missing_items),
                "label": "Aucune piece manquante prioritaire n'est remontee.",
                "href": _route_href("/pieces"),
            },
        },
        "syndic_followups": {
            "context": {
                "route": "/demandes/relance",
                "title": "Relance syndic",
                "subtitle": "Brouillons, relances a envoyer et reponses a verifier.",
            },
            "summary": {
                "total_open": len(followup_items),
                "draft_count": len([item for item in followup_items if item.get("status") == "draft"]),
                "ready_count": len([item for item in followup_items if item.get("status") == "ready_to_copy"]),
                "sent_external_count": 0,
                "answers_to_verify_count": 0,
                "blocked_count": 0,
            },
            "tabs": followup_tabs,
            "items": followup_items,
            "selected": followup_items[0] if followup_items else {},
            "empty_state": {
                "is_visible": not bool(followup_items),
                "label": "Aucune relance syndic n'est en attente.",
                "href": _route_href("/actions"),
            },
        },
    }


MEMOIRE_CATEGORY_INFO: dict[str, dict[str, str]] = {
    "ag": {"label": "AG", "tone": "green", "icon": "users"},
    "travaux": {"label": "Travaux", "tone": "blue", "icon": "tools"},
    "sinistres": {"label": "Sinistres", "tone": "orange", "icon": "alert"},
    "contrats": {"label": "Contrats", "tone": "green", "icon": "file-check"},
    "syndic": {"label": "Syndic", "tone": "blue", "icon": "building"},
    "documents": {"label": "Documents", "tone": "gray", "icon": "folder"},
    "comptes": {"label": "Comptes", "tone": "blue", "icon": "chart"},
    "demandes": {"label": "Demandes", "tone": "blue", "icon": "message"},
    "contentieux": {"label": "Contentieux", "tone": "red", "icon": "scale"},
}


def _memoire_category_from_document(row: dict[str, str]) -> str:
    text = " ".join(
        [
            row.get("lot", ""),
            row.get("document_type", ""),
            row.get("file_name", ""),
            row.get("notes", ""),
        ]
    ).lower()
    if any(word in text for word in ["contrat", "syndic", "fournisseur"]):
        return "contrats"
    if any(word in text for word in ["travaux", "devis", "chantier", "toiture"]):
        return "travaux"
    if any(word in text for word in ["ag", "pv", "convocation", "assemblee"]):
        return "ag"
    if any(word in text for word in ["compte", "budget", "facture", "comptable"]):
        return "comptes"
    if any(word in text for word in ["contentieux", "litige"]):
        return "contentieux"
    return "documents"


def _memoire_category_option(category_id: str) -> dict[str, str]:
    return MEMOIRE_CATEGORY_INFO.get(category_id, MEMOIRE_CATEGORY_INFO["documents"])


def _memoire_event_status(status: str, *, has_missing_proof: bool = False) -> dict[str, str]:
    normalized = (status or "").upper()
    if normalized in {"OK", "TRAITE", "CLOTURE", "CLOS", "TERMINE", "MATCH"}:
        return {"status": "clos", "label": "Clos", "risk": "low"}
    if has_missing_proof or normalized in {"PREUVE_A_DEMANDER", "ABSENT", "A_DEMANDER"}:
        return {"status": "ouvert", "label": "Ouvert", "risk": "high"}
    if normalized in {"A_ARBITRER", "A_REVOIR", "PREUVE_LOCALE_A_VERIFIER", "CANDIDAT_AVANT_AG"}:
        return {"status": "a_confirmer", "label": "A confirmer", "risk": "medium"}
    return {"status": "ouvert" if normalized else "a_confirmer", "label": "A confirmer", "risk": "medium"}


def _memoire_safe_refs(*values: object) -> list[str]:
    refs: list[str] = []
    for value in values:
        if isinstance(value, list):
            candidates = [str(item or "") for item in value]
        else:
            candidates = _split_piece_refs(str(value or ""))
        for candidate in candidates:
            safe = _public_text(candidate, "")
            if safe and safe not in refs:
                refs.append(safe)
    return refs


def _memoire_filter_options(
    rows: list[dict[str, object]],
    field: str,
    *,
    labels: dict[str, str] | None = None,
    route_field: str | None = None,
) -> list[dict[str, object]]:
    counts = Counter(str(row.get(field, "") or "non renseigne") for row in rows)
    options: list[dict[str, object]] = []
    for value, count in sorted(counts.items(), key=lambda item: (item[0] == "non renseigne", item[0])):
        options.append(
            {
                "id": value,
                "label": (labels or {}).get(value, value),
                "count": count,
                "is_active": False,
                "href": _route_href("/chantiers", **{route_field or field: value}),
            }
        )
    return options


def _memoire_event_detail(event: dict[str, object]) -> dict[str, object]:
    if not event:
        return {}
    event_id = str(event.get("id") or "")
    document_refs = [str(ref) for ref in event.get("document_refs", []) if ref]
    action_refs = [str(ref) for ref in event.get("action_refs", []) if ref]
    decision_refs = [str(ref) for ref in event.get("decision_refs", []) if ref]
    can_export = bool(event.get("can_export"))
    event_status = _public_text(event.get("status"), "a_confirmer")
    proof_state = "verified" if event_status == "clos" and document_refs else "candidate" if document_refs else "missing"
    if event_status == "ouvert" and not document_refs:
        proof_state = "missing"
    documents = [
        {
            "id": ref,
            "label": ref,
            "type_label": "Document",
            "status_label": "Piece candidate a verifier" if proof_state != "verified" else "Preuve validee",
            "why_linked": "Explique ou documente cet evenement.",
            "href": _route_href("/documents", doc_id=ref),
            "diffusion_label": "Conseil syndical",
            "can_download": False,
            "blocked_reason": "Verifier la diffusion avant telechargement.",
        }
        for ref in document_refs[:6]
    ]
    missing_proofs = []
    if proof_state == "missing":
        missing_proofs.append(
            {
                "id": _stable_action_id("MISSING-EVT", 0, event_id, str(event.get("title", ""))),
                "label": "Preuve de cloture ou document explicatif",
                "why_needed": "Prouver ce qui s'est passe et ce qui reste a reprendre.",
                "request_href": _route_href("/actions", selected=action_refs[0] if action_refs else event_id, tab="relance"),
            }
        )
    return {
        "id": event_id,
        "title": _public_text(event.get("title"), "Evenement memoire"),
        "date_iso": _public_text(event.get("date_iso"), ""),
        "date_label": _public_text(event.get("date_label"), "Date a confirmer"),
        "category": _public_text(event.get("kind"), "memoire"),
        "category_label": _public_text(event.get("category_label"), "Memoire"),
        "status": event_status,
        "status_label": _public_text(event.get("status_label"), "A confirmer"),
        "summary": _public_text(event.get("subtitle"), "Evenement a relire."),
        "why_in_memory": "Sujet a reprendre tant qu'une action, une preuve ou une restriction reste ouverte.",
        "next_action": _public_text(event.get("next_action"), "Verifier le point et rattacher les preuves utiles."),
        "owner_label": "Conseil syndical",
        "proof_state": proof_state,
        "proof_state_label": _proof_state_label(proof_state),
        "documents": documents,
        "proofs": {
            "verified": documents if proof_state == "verified" else [],
            "candidates": documents if proof_state == "candidate" else [],
            "missing": missing_proofs,
        },
        "linked_actions": [
            {
                "id": ref,
                "label": "Action liee",
                "next_step": _public_text(event.get("next_action"), "Verifier la prochaine action."),
                "href": _route_href("/actions", selected=ref),
            }
            for ref in action_refs[:6]
        ],
        "linked_documents": [
            {"id": ref, "label": ref, "href": _route_href("/documents", doc_id=ref), "why_linked": "Piece rattachee a l'evenement."}
            for ref in document_refs[:6]
        ],
        "linked_decisions": [
            {"id": ref, "label": ref, "href": _route_href("/actions", selected=ref)}
            for ref in decision_refs[:6]
        ],
        "linked_requests": [],
        "passation_note": _public_text(event.get("passation_note"), "A conserver dans la memoire de passation."),
        "passation": {
            "include_in_handover": event_status != "clos" or proof_state != "missing",
            "note": _public_text(event.get("passation_note"), "A transmettre avec les limites de preuve et de diffusion."),
            "missing_for_handover": [item.get("label", "preuve attendue") for item in missing_proofs],
            "export_href": _route_href("/exports/passation", scope="event", selected=event_id),
        },
        "restriction": {
            "level": event.get("restriction_level", "conseil_syndical"),
            "label": event.get("restriction_label", "Diffusion a verifier"),
            "reason": "Verifier les pieces et ne partager que la preuve utile.",
            "review_href": _route_href("/confidentialite"),
        },
        "history": [
            {
                "date_label": event.get("date_label", "Date a confirmer"),
                "label": "Evenement projete depuis les donnees locales.",
                "detail": "Projection derivee des actions, documents ou incidents disponibles.",
            }
        ],
        "actions": {
            "primary": {"label": "Ouvrir les documents", "href": _route_href("/documents")},
            "secondary": [
                {"label": "Voir l'action liee", "href": _route_href("/actions", selected=action_refs[0])}
                if action_refs
                else {"label": "Voir les actions", "href": _route_href("/actions")}
            ],
            "export": {
                "label": "Exporter cette fiche",
                "href": _route_href("/exports/passation.txt", scope="event", selected=event_id),
                "requires_preview": True,
                "disabled": not can_export,
                "disabled_reason": "" if can_export else "Diffusion a verifier avant export.",
            },
        },
    }


def _build_memoire_ux_model(
    instance: InstanceConfig,
    year: int,
    *,
    ux_items: list[dict[str, object]],
    accounting: dict[str, object],
    decisions: dict[str, object],
    incidents: dict[str, object],
    privacy: dict[str, object],
    documents: dict[str, object],
    piece_workshop: dict[str, object],
) -> dict[str, object]:
    decision_rows = decisions.get("rows") if isinstance(decisions.get("rows"), list) else []
    incident_rows = incidents.get("rows") if isinstance(incidents.get("rows"), list) else []
    document_table = documents.get("documents")
    document_rows = document_table.rows if isinstance(document_table, DataTable) else []
    document_actionable = documents.get("actionable") if isinstance(documents.get("actionable"), dict) else {}
    document_summary = document_actionable.get("summary") if isinstance(document_actionable.get("summary"), dict) else {}
    privacy_rows = privacy.get("review_rows") if isinstance(privacy.get("review_rows"), list) else []
    privacy_summary = privacy.get("review_summary") if isinstance(privacy.get("review_summary"), dict) else {}
    decision_summary = decisions.get("summary") if isinstance(decisions.get("summary"), dict) else {}
    incident_summary = incidents.get("summary") if isinstance(incidents.get("summary"), dict) else {}
    piece_summary = piece_workshop.get("summary") if isinstance(piece_workshop.get("summary"), dict) else {}
    accounting_before_ag = accounting.get("before_ag") if isinstance(accounting.get("before_ag"), dict) else {}

    timeline: list[dict[str, object]] = []

    for index, row in enumerate(decision_rows, start=1):
        if not isinstance(row, dict):
            continue
        category_id = "travaux" if row.get("related_work_refs") else "comptes" if row.get("related_invoice_refs") else "ag"
        category = _memoire_category_option(category_id)
        has_missing_proof = (row.get("statut") or "").upper() == "PREUVE_A_DEMANDER" or not row.get("proof_doc_ids")
        status = _memoire_event_status(row.get("statut", ""), has_missing_proof=has_missing_proof)
        date_iso = _ag_date(row) or _date_from_text(row.get("echeance", "")) or ""
        event_id = _stable_action_id(
            "MEM-DEC",
            index,
            row.get("decision_action_id", ""),
            row.get("ag_id", ""),
            row.get("resolution_ref", ""),
        )
        title = _public_text(row.get("decision_text"), row.get("resolution_ref") or "Decision AG")
        timeline.append(
            {
                "id": event_id,
                "date_iso": date_iso,
                "date_label": _date_label(date_iso, "Date a confirmer"),
                "year": int(date_iso[:4]) if date_iso[:4].isdigit() else year,
                "dot_tone": category["tone"],
                "icon": category["icon"],
                "title": title,
                "subtitle": _public_text(row.get("action_attendue") or row.get("preuve_attendue"), "Action ou preuve a reprendre."),
                "kind": category_id,
                "category_label": category["label"],
                "category_tone": category["tone"],
                "status": status["status"],
                "status_label": status["label"],
                "is_open_topic": status["status"] != "clos",
                "risk_level": status["risk"],
                "restriction_level": "conseil_syndical",
                "restriction_label": "Conseil syndical",
                "href": _route_href("/chantiers", selected=event_id),
                "detail_href": _route_href("/chantiers", selected=event_id),
                "document_refs": _memoire_safe_refs(row.get("source_doc_id"), row.get("proof_doc_ids")),
                "action_refs": _memoire_safe_refs(row.get("decision_action_id")),
                "decision_refs": _memoire_safe_refs(row.get("decision_action_id")),
                "next_action": _public_text(row.get("action_attendue"), "Rattacher la preuve attendue ou relancer le syndic."),
                "passation_note": "Decision a reprendre en passation tant que la preuve ou l'action reste ouverte.",
                "can_export": status["status"] == "clos",
            }
        )

    for index, row in enumerate(incident_rows, start=1):
        if not isinstance(row, dict):
            continue
        category = _memoire_category_option("sinistres")
        is_open = incidentops.is_open_incident(row)
        priority = (row.get("priority") or "P2").upper()
        date_iso = _date_from_text(row.get("date_signalement", "")) or _date_from_text(row.get("action_due_date", "")) or ""
        event_id = _stable_action_id("MEM-INC", index, row.get("incident_id", ""), row.get("date_signalement", ""))
        title_parts = [row.get("lieu", ""), row.get("incident_id", "")]
        title = _public_text(" - ".join(part for part in title_parts if part), "Incident a suivre")
        timeline.append(
            {
                "id": event_id,
                "date_iso": date_iso,
                "date_label": _date_label(date_iso, "Date a confirmer"),
                "year": int(date_iso[:4]) if date_iso[:4].isdigit() else year,
                "dot_tone": "red" if priority in {"P0", "P1"} else category["tone"],
                "icon": category["icon"],
                "title": title,
                "subtitle": _public_text(row.get("description") or row.get("next_action"), "Incident a documenter."),
                "kind": "sinistres",
                "category_label": category["label"],
                "category_tone": category["tone"],
                "status": "ouvert" if is_open else "clos",
                "status_label": "Ouvert" if is_open else "Clos",
                "is_open_topic": is_open,
                "risk_level": "high" if priority in {"P0", "P1"} else "medium" if is_open else "low",
                "restriction_level": "conseil_syndical",
                "restriction_label": "Diffusion limitee",
                "href": _route_href("/chantiers", selected=event_id),
                "detail_href": _route_href("/chantiers", selected=event_id),
                "document_refs": _memoire_safe_refs(row.get("doc_ids"), row.get("closure_proof_ref")),
                "action_refs": _memoire_safe_refs(row.get("incident_id")),
                "decision_refs": [],
                "next_action": _public_text(row.get("next_action"), "Obtenir la preuve de cloture."),
                "passation_note": "Ne pas clore la passation sans preuve de resolution ou prochaine action claire.",
                "can_export": not is_open,
            }
        )

    for index, row in enumerate(document_rows[:30], start=1):
        if not isinstance(row, dict):
            continue
        category_id = _memoire_category_from_document(row)
        category = _memoire_category_option(category_id)
        review_status = row.get("privacy_review_status") or row.get("review_required") or row.get("publication_form") or ""
        needs_review = str(review_status).upper() in {"YES", "A_ARBITRER", "BLOQUE"} or bool(row.get("required_transformations"))
        date_iso = _date_from_text(row.get("suspected_date", "")) or _date_from_text(row.get("last_modified", "")) or ""
        event_id = _stable_action_id("MEM-DOC", index, row.get("doc_id", ""), row.get("file_name", ""))
        timeline.append(
            {
                "id": event_id,
                "date_iso": date_iso,
                "date_label": _date_label(date_iso, "Date a confirmer"),
                "year": int(date_iso[:4]) if date_iso[:4].isdigit() else year,
                "dot_tone": "orange" if needs_review else category["tone"],
                "icon": category["icon"],
                "title": _document_label(row.get("doc_id", ""), row, "Document cle"),
                "subtitle": _document_type_label(row, "Document a transmettre"),
                "kind": category_id,
                "category_label": category["label"],
                "category_tone": category["tone"],
                "status": "a_confirmer" if needs_review else "clos",
                "status_label": "A verifier" if needs_review else "Clos",
                "is_open_topic": needs_review,
                "risk_level": "medium" if needs_review else "low",
                "restriction_level": "a_verifier" if needs_review else "coproprietaires",
                "restriction_label": "A verifier avant partage" if needs_review else "Transmissible apres controle",
                "href": _route_href("/chantiers", selected=event_id),
                "detail_href": _route_href("/chantiers", selected=event_id),
                "document_refs": _memoire_safe_refs(row.get("doc_id")),
                "action_refs": [],
                "decision_refs": [],
                "next_action": "Verifier la diffusion avant de transmettre." if needs_review else "Conserver dans les documents de passation.",
                "passation_note": "Document utile pour comprendre l'historique de la copropriete.",
                "can_export": not needs_review,
            }
        )

    accounting_open = int(accounting_before_ag.get("blocking") or 0) + int(accounting_before_ag.get("to_confirm") or 0)
    if accounting_open or int(accounting_before_ag.get("ok") or 0):
        category = _memoire_category_option("comptes")
        event_id = _stable_action_id("MEM-COMP", 0, str(year), str(accounting_open))
        timeline.append(
            {
                "id": event_id,
                "date_iso": f"{year}-12-31",
                "date_label": f"Exercice {year}",
                "year": year,
                "dot_tone": "orange" if accounting_open else category["tone"],
                "icon": category["icon"],
                "title": f"Controle des comptes {year}",
                "subtitle": "Points comptables a traiter avant AG." if accounting_open else "Rapprochements comptables disponibles.",
                "kind": "comptes",
                "category_label": category["label"],
                "category_tone": category["tone"],
                "status": "ouvert" if accounting_open else "clos",
                "status_label": "Ouvert" if accounting_open else "Clos",
                "is_open_topic": bool(accounting_open),
                "risk_level": "high" if int(accounting_before_ag.get("blocking") or 0) else "medium" if accounting_open else "low",
                "restriction_level": "conseil_syndical",
                "restriction_label": "Conseil syndical",
                "href": _route_href("/comptes"),
                "detail_href": _route_href("/comptes"),
                "document_refs": [],
                "action_refs": [],
                "decision_refs": [],
                "next_action": "Traiter les questions comptes et conserver les preuves utiles.",
                "passation_note": "Reprendre le statut des comptes dans le pack de passation.",
                "can_export": not accounting_open,
            }
        )

    timeline.sort(key=lambda event: str(event.get("date_iso") or "0000-00-00"), reverse=True)
    visible_timeline = timeline[:12]
    selected_event = _memoire_event_detail(visible_timeline[0]) if visible_timeline else {}
    selected_event_id = selected_event.get("id") if isinstance(selected_event, dict) else ""
    for event in visible_timeline:
        event["is_selected"] = bool(selected_event_id and event.get("id") == selected_event_id)
        event["aria_label"] = "Evenement selectionne" if event["is_selected"] else "Ouvrir le detail de cet evenement"
    open_topics = [event for event in timeline if event.get("is_open_topic")]
    restricted_count = len([event for event in timeline if event.get("restriction_level") in {"a_verifier", "conseil_syndical"} and not event.get("can_export")])
    missing_proof_count = int(decision_summary.get("missing_proofs") or 0) + int(piece_summary.get("without_local_proof") or 0)
    syndic_waiting = len([item for item in ux_items if item.get("lane") == "waiting_syndic"])
    document_missing = int(document_summary.get("to_request") or 0)
    privacy_attention = int(privacy_summary.get("to_arbitrate") or 0) + int(privacy_summary.get("blocked") or 0)
    open_incidents = int(incident_summary.get("open") or 0)
    open_works = len(
        [
            row
            for row in decision_rows
            if isinstance(row, dict)
            and row.get("related_work_refs")
            and row.get("statut") not in {"OK", "TRAITE", "CLOTURE", "CLOS", "TERMINE"}
        ]
    )
    contract_missing = len(
        [
            row
            for row in (document_actionable.get("to_request") if isinstance(document_actionable.get("to_request"), list) else [])
            if isinstance(row, dict)
            and "contrat" in " ".join([row.get("lot", ""), row.get("expected_piece", ""), row.get("expected_label", ""), row.get("subject", "")]).lower()
        ]
    )
    checklist_specs = [
        ("contrats", "Contrats en cours a suivre", contract_missing),
        ("travaux", "Travaux en cours ou a venir", open_works),
        ("sinistres", "Litiges et sinistres en cours", open_incidents),
        ("comptes", "Points de vigilance financiere", accounting_open),
        ("demandes", "Demandes en attente au syndic", syndic_waiting),
        ("documents", "Documents cles a transmettre", document_missing + privacy_attention),
    ]
    checklist = [
        {
            "id": item_id,
            "label": label,
            "is_done": count == 0,
            "needs_attention": count > 0,
            "alert_label": "A traiter" if count else "Pret",
            "count": count,
            "href": _route_href("/chantiers", categorie=item_id, statut="ouvert") if count else _route_href("/chantiers", categorie=item_id),
        }
        for item_id, label, count in checklist_specs
    ]
    completed_count = len([item for item in checklist if item["is_done"]])
    total_count = len(checklist)
    progress_pct = round(100 * completed_count / total_count) if total_count else 0

    transmit_items: list[dict[str, object]] = []
    for row in document_rows[:12]:
        if not isinstance(row, dict):
            continue
        doc_id = _public_text(row.get("doc_id"), "")
        review_status = str(row.get("privacy_review_status") or row.get("review_required") or "").upper()
        needs_review = review_status in {"YES", "A_ARBITRER", "BLOQUE"} or bool(row.get("required_transformations"))
        updated_on = _date_from_text(row.get("suspected_date", "")) or _date_from_text(row.get("last_modified", ""))
        transmit_items.append(
            {
                "id": doc_id or _stable_action_id("DOC-MEM", 0, row.get("file_name", "")),
                "title": _document_label(doc_id, row, "Document de passation"),
                "file_type": _public_text((row.get("extension") or "doc").upper(), "DOC"),
                "updated_label": f"Mis a jour le {_date_label(updated_on, 'date a confirmer')}",
                "icon": "file",
                "href": _route_href("/documents", doc_id=doc_id) if doc_id else _route_href("/documents"),
                "download_href": _route_href("/documents", doc_id=doc_id, download=1) if doc_id and not needs_review else "",
                "diffusion_label": "A verifier avant partage" if needs_review else "Transmissible apres controle",
                "restriction_label": "Diffusion a verifier" if needs_review else "",
                "can_download": bool(doc_id and not needs_review),
            }
        )

    last_event_label = str(visible_timeline[0].get("date_label", "Aucune date")) if visible_timeline else "Aucun evenement"
    summary = {
        "event_count": len(timeline),
        "visible_event_count": len(visible_timeline),
        "open_topics_count": len(open_topics),
        "handover_completed_count": completed_count,
        "handover_total_count": total_count,
        "handover_progress_pct": progress_pct,
        "transmit_count": len(transmit_items),
        "diffusion_limited_count": restricted_count,
        "missing_proof_count": missing_proof_count,
        "last_event_label": last_event_label,
    }
    category_labels = {key: value["label"] for key, value in MEMOIRE_CATEGORY_INFO.items()}
    export_status = "blocked" if privacy_attention else "warning" if restricted_count or open_topics else "ready"
    omissions = [
        {
            "id": _stable_action_id("OMIT-MEM", index, str(event.get("id", ""))),
            "label": event.get("title", "Element omis"),
            "reason": "Diffusion a verifier",
            "href": event.get("href", _route_href("/chantiers")),
        }
        for index, event in enumerate([event for event in timeline if not event.get("can_export")][:8], start=1)
    ]
    handover_checklist = [
        {"label": item["label"], "done": item["is_done"], "href": item["href"]}
        for item in checklist
    ]
    return {
        "context": {
            "route": "/chantiers",
            "visual_name": "Memoire de copropriete",
            "title": "Memoire de copropriete",
            "subtitle": "L'historique utile de l'immeuble, les sujets ouverts et les preuves a transmettre.",
            "active_nav_label": "Memoire copropriete",
            "coffre": _public_text(instance.display_name, "Copropriete"),
            "role": "Conseil syndical",
            "exercise": year,
            "as_of_label": f"Situation {year}",
            "default_period": "10ans",
        },
        "summary": summary,
        "toolbar": {
            "search_placeholder": "Rechercher un evenement, un contrat, un document...",
            "query": "",
            "active_period": "10ans",
            "period_options": [
                {"id": "5ans", "label": "5 ans", "href": _route_href("/chantiers", periode="5ans"), "is_active": False},
                {"id": "10ans", "label": "10 ans", "href": _route_href("/chantiers", periode="10ans"), "is_active": True},
                {"id": "tout", "label": "Tout", "href": _route_href("/chantiers", periode="tout"), "is_active": False},
            ],
            "active_filters_count": 0,
            "result_count": len(visible_timeline),
        },
        "filters": {
            "categories": _memoire_filter_options(timeline, "kind", labels=category_labels, route_field="categorie"),
            "statuses": _memoire_filter_options(timeline, "status", labels={"ouvert": "Ouvert", "clos": "Clos", "a_confirmer": "A confirmer"}, route_field="statut"),
            "diffusion": _memoire_filter_options(
                timeline,
                "restriction_level",
                labels={
                    "coproprietaires": "Transmissible",
                    "a_verifier": "A verifier",
                    "conseil_syndical": "Conseil syndical",
                },
                route_field="diffusion",
            ),
            "reset_href": _route_href("/chantiers"),
        },
        "timeline": visible_timeline,
        "selected_event": selected_event,
        "event_detail": selected_event,
        "passation": {
            "title": "Passation CS",
            "description": "Preparez la transmission des informations aux nouveaux membres du conseil syndical.",
            "completed_count": completed_count,
            "total_count": total_count,
            "progress_pct": progress_pct,
            "open_topics_count": len(open_topics),
            "detail_href": _route_href("/chantiers", panel="passation"),
            "checklist": checklist,
            "open_topics": [
                {
                    "id": event.get("id", ""),
                    "label": event.get("category_label", "Memoire"),
                    "title": event.get("title", "Sujet ouvert"),
                    "next_step": event.get("next_action", "Verifier la prochaine action."),
                    "severity": "P1" if event.get("risk_level") == "high" else "P2",
                    "href": event.get("href", _route_href("/chantiers")),
                }
                for event in open_topics[:8]
            ],
        },
        "transmit": {
            "title": "A transmettre",
            "count": len(transmit_items),
            "all_href": _route_href("/chantiers", panel="documents"),
            "items": transmit_items[:5],
        },
        "pack": {
            "id": f"passation-{year}",
            "title": "Pack passation",
            "scope": "Memoire de copropriete, sujets ouverts, preuves essentielles et restrictions de diffusion",
            "status": "partiel" if omissions else "pret",
            "status_label": "Pret avec omissions" if omissions else "Pret a relire",
            "generated_at_label": "Genere depuis les donnees locales",
            "source_of_truth": False,
            "watermark": "export derive, non source collaborative",
            "included_sections": ["Sujets ouverts", "Timeline", "Documents cles", "Restrictions", "Prochaines actions"],
            "omissions": omissions,
            "latest_export": {
                "json_href": _route_href("/exports/passation.json"),
                "text_href": _route_href("/exports/passation.txt"),
                "preview_href": _route_href("/chantiers", panel="export"),
            },
            "safety": {
                "has_local_path": False,
                "has_unreviewed_content": False,
                "blocked_reason": "Diffusion a arbitrer" if export_status == "blocked" else "",
            },
        },
        "export": {
            "title": "Exporter la passation",
            "watermark": "export derive, non source collaborative",
            "source_of_truth": False,
            "json_href": _route_href("/exports/passation.json"),
            "text_href": _route_href("/exports/passation.txt"),
            "preview_href": _route_href("/chantiers", panel="export"),
            "status": export_status,
            "disabled": export_status == "blocked",
            "disabled_reason": "Arbitrer la diffusion avant export." if export_status == "blocked" else "",
            "formats": [
                {"id": "json", "label": "Passation JSON", "href": _route_href("/exports/passation.json")},
                {"id": "text", "label": "Passation texte", "href": _route_href("/exports/passation.txt")},
                {"id": "preview", "label": "Apercu de passation", "href": _route_href("/chantiers", panel="export")},
            ],
            "omissions": omissions,
        },
        "empty_states": {
            "no_event": {
                "is_visible": not bool(timeline),
                "label": "Aucun evenement dans la memoire. Importer les registres ou rattacher des preuves pour commencer.",
                "href": _route_href("/depot"),
            },
            "event_not_found": {
                "is_visible": False,
                "label": "Evenement introuvable dans la projection courante.",
                "href": _route_href("/chantiers"),
            },
            "passation_empty": {
                "is_visible": not bool(open_topics) and completed_count == total_count,
                "label": "Passation a preparer: verifier les documents cles et les sujets ouverts.",
                "href": _route_href("/chantiers", panel="passation"),
            },
            "transmit_empty": {
                "is_visible": not bool(transmit_items),
                "label": "Aucun document transmissible charge pour la passation.",
                "href": _route_href("/documents"),
            },
            "export_blocked": {
                "is_visible": export_status == "blocked",
                "label": "Export bloque tant que la diffusion n'est pas arbitree.",
                "href": _route_href("/confidentialite"),
            },
        },
        "open_topics": open_topics[:12],
        "handover_checklist": handover_checklist,
    }


def _build_passation_export_model(
    *,
    year: int,
    memoire: dict[str, object],
    priority_views: dict[str, object],
    action_detail: dict[str, object],
) -> dict[str, object]:
    memoire_summary = memoire.get("summary") if isinstance(memoire.get("summary"), dict) else {}
    memoire_export = memoire.get("export") if isinstance(memoire.get("export"), dict) else {}
    memoire_pack = memoire.get("pack") if isinstance(memoire.get("pack"), dict) else {}
    late_view = priority_views.get("late_actions") if isinstance(priority_views.get("late_actions"), dict) else {}
    missing_view = priority_views.get("missing_pieces") if isinstance(priority_views.get("missing_pieces"), dict) else {}
    followup_view = priority_views.get("syndic_followups") if isinstance(priority_views.get("syndic_followups"), dict) else {}
    late_actions = _list_of_dicts(late_view.get("items"))
    missing_pieces = _list_of_dicts(missing_view.get("items"))
    followups = _list_of_dicts(followup_view.get("items"))
    timeline = _list_of_dicts(memoire.get("timeline"))
    transmit = memoire.get("transmit") if isinstance(memoire.get("transmit"), dict) else {}
    transmit_items = _list_of_dicts(transmit.get("items"))
    raw_omissions = _list_of_dicts(memoire_export.get("omissions") or memoire_pack.get("omissions"))
    omitted_items = [
        {
            "id": _public_text(item.get("id"), _stable_action_id("OMIT", index, str(item.get("label", "")))),
            "label": _public_text(item.get("label"), "Element exclu ou masque"),
            "reason": _public_text(item.get("reason"), "Diffusion a verifier."),
            "type_label": _public_text(item.get("type_label"), "Element de passation"),
            "review_href": _public_href(item.get("href"), _route_href("/confidentialite")),
        }
        for index, item in enumerate(raw_omissions, start=1)
    ]
    if not omitted_items and missing_pieces:
        omitted_items.append(
            {
                "id": "omission-preuves-manquantes",
                "label": "Preuves manquantes",
                "reason": "Les preuves absentes sont listees comme points a obtenir.",
                "type_label": "Preuve",
                "review_href": _route_href("/pieces", proof="missing"),
            }
        )
    diffusion_limited_count = int(memoire_summary.get("diffusion_limited_count") or 0)
    missing_count = len(missing_pieces)
    blocker_rows: list[dict[str, object]] = []
    if diffusion_limited_count:
        blocker_rows.append(
            {
                "id": "diffusion-a-verifier",
                "label": "Diffusion a verifier",
                "detail": f"{diffusion_limited_count} element(s) demandent une relecture avant export complet.",
                "href": _route_href("/confidentialite", scope="export", export="passation"),
            }
        )
    if missing_count:
        blocker_rows.append(
            {
                "id": "preuves-manquantes",
                "label": "Preuves manquantes",
                "detail": f"{missing_count} preuve(s) ou piece(s) seront listees comme points a obtenir.",
                "href": _route_href("/pieces", proof="missing"),
            }
        )
    can_export = not blocker_rows
    downloads = {
        "requires_preview": True,
        "previewed": True,
        "can_download": can_export,
        "download_disabled_reason": "" if can_export else "Verifier la diffusion et les preuves manquantes.",
    }
    format_specs = [
        ("txt", "TXT", "Synthese lisible et copiable.", "/exports/passation.txt"),
        ("json", "JSON", "Export structure pour audit ou reprise.", "/exports/passation.json"),
    ]
    formats = [
        {
            "id": format_id,
            "label": label,
            "description": description,
            "href": _route_href(path, audience="conseil_syndical"),
            "enabled": can_export,
            "disabled_reason": "" if can_export else "Verifier la diffusion avant export.",
        }
        for format_id, label, description, path in format_specs
    ]
    checklist = [
        {
            "id": "audience",
            "label": "Public vise choisi",
            "status": "done",
            "status_label": "Pret",
            "detail": "Version conseil syndical.",
        },
        {
            "id": "restrictions",
            "label": "Diffusion relue",
            "status": "blocked" if diffusion_limited_count else "done",
            "status_label": "A verifier" if diffusion_limited_count else "Pret",
            "detail": "Relire les elements limites avant partage." if diffusion_limited_count else "Aucun blocage de diffusion signale.",
            "href": _route_href("/confidentialite", scope="export", export="passation"),
        },
        {
            "id": "missing-proofs",
            "label": "Preuves manquantes visibles",
            "status": "blocked" if missing_count else "done",
            "status_label": "A obtenir" if missing_count else "Pret",
            "detail": f"{missing_count} piece(s) ou preuve(s) a obtenir." if missing_count else "Aucune preuve manquante prioritaire.",
            "href": _route_href("/pieces", proof="missing"),
        },
        {
            "id": "watermark",
            "label": "Mention export derive presente",
            "status": "done",
            "status_label": "Pret",
            "detail": "Export derive, non source collaborative.",
        },
    ]
    selected_action_id = ""
    selected = action_detail.get("selected") if isinstance(action_detail.get("selected"), dict) else {}
    if isinstance(selected, dict):
        selected_action_id = _public_text(selected.get("id"), "")
    sections_included = [
        {"id": "synthese", "label": "Synthese", "count": 1, "included": True},
        {"id": "events", "label": "Evenements memoire", "count": len(timeline), "included": True},
        {"id": "actions", "label": "Actions ouvertes", "count": len(late_actions), "included": True},
        {"id": "documents", "label": "Documents de passation", "count": len(transmit_items), "included": True},
        {"id": "proofs", "label": "Preuves a obtenir", "count": missing_count, "included": True},
        {"id": "restrictions", "label": "Restrictions et omissions", "count": diffusion_limited_count + len(omitted_items), "included": True},
    ]
    excluded_or_blocked = [
        {
            "id": _public_text(item.get("id"), _stable_action_id("BLOCK", index, str(item.get("label", "")))),
            "label": _public_text(item.get("label"), "Element a verifier"),
            "reason": _public_text(item.get("reason") or item.get("detail"), "Diffusion ou preuve a verifier."),
            "href": _public_href(item.get("review_href") or item.get("href"), _route_href("/confidentialite", scope="export", export="passation")),
        }
        for index, item in enumerate([*omitted_items, *blocker_rows], start=1)
    ]
    return {
        "watermark": "Export derive, non source collaborative",
        "source_of_truth": False,
        "context": {
            "route": "/exports/passation",
            "title": "Apercu de passation",
            "subtitle": "Verifiez le contenu, les diffusions limitees et les omissions avant export.",
            "source_of_truth": False,
            "watermark": "Export derive, non source collaborative",
            "role_label": "Conseil syndical",
            "as_of_label": f"Situation {year}",
        },
        "sections_included": sections_included,
        "scope": {
            "period_label": "10 ans",
            "selected_scope": "handover",
            "selected_event_id": None,
            "selected_action_id": selected_action_id or None,
            "include_open_actions": True,
            "include_memory_events": True,
            "include_key_documents": True,
            "include_limited_documents": False,
            "hrefs": {
                "all": _route_href("/exports/passation", scope="handover"),
                "open_actions": _route_href("/exports/passation", scope="open-actions"),
                "event": _route_href("/exports/passation", scope="event"),
                "action": _route_href("/exports/passation", scope="action", selected=selected_action_id),
            },
        },
        "audience": {
            "selected": "conseil_syndical",
            "selected_label": "Conseil syndical",
            "options": [
                {
                    "id": "conseil_syndical",
                    "label": "Conseil syndical",
                    "description": "Version de travail interne avec limites visibles.",
                    "href": _route_href("/exports/passation", audience="conseil_syndical"),
                },
                {
                    "id": "diffusable",
                    "label": "Synthese diffusable",
                    "description": "Version plus courte, avec elements sensibles exclus ou masques.",
                    "href": _route_href("/exports/passation", audience="diffusable"),
                },
            ],
        },
        "summary": {
            "included_events_count": len(timeline),
            "open_topics_count": int(memoire_summary.get("open_topics_count") or 0),
            "included_actions_count": len(late_actions),
            "included_documents_count": len(transmit_items),
            "missing_proofs_count": missing_count,
            "diffusion_limited_count": diffusion_limited_count,
            "omitted_items_count": len(omitted_items),
            "can_export": can_export,
            "can_export_label": "Pret a exporter apres apercu" if can_export else "A verifier avant export",
            "last_updated_label": f"Situation {year}",
        },
        "checklist": checklist,
        "preview": {
            "title": "Passation conseil syndical",
            "intro": "Synthese derivee des actions, evenements memoire et documents utiles.",
            "sections": [
                {
                    "id": "synthese",
                    "title": "Synthese",
                    "items": [
                        f"{int(memoire_summary.get('open_topics_count') or 0)} sujets ouverts",
                        f"{missing_count} preuves manquantes",
                        f"{diffusion_limited_count} diffusions a verifier",
                    ],
                },
                {
                    "id": "actions",
                    "title": "Actions ouvertes",
                    "items": [str(item.get("title", "Action ouverte")) for item in late_actions[:8]],
                    "empty_label": "Aucune action ouverte dans ce perimetre.",
                },
                {
                    "id": "relances",
                    "title": "Relances syndic",
                    "items": [str(item.get("title", "Relance syndic")) for item in followups[:8]],
                    "empty_label": "Aucune relance syndic dans ce perimetre.",
                },
            ],
        },
        "included": {
            "events": timeline[:8],
            "actions": late_actions[:8],
            "documents": transmit_items[:8],
            "proofs": [item for item in missing_pieces[:8] if item.get("candidate_docs")],
        },
        "omitted": {
            "items": omitted_items,
            "summary_label": f"{len(omitted_items)} element(s) exclus, masques ou signales.",
        },
        "restrictions": {
            "highest_level": "conseil_syndical" if diffusion_limited_count else "diffusable",
            "label": "Diffusion limitee" if diffusion_limited_count else "Diffusion a relire",
            "reason": "Le pack contient des sujets ouverts ou des pieces a arbitrer." if diffusion_limited_count else "Relire avant partage externe.",
            "review_href": _route_href("/confidentialite", scope="export", export="passation"),
        },
        "blockers": blocker_rows,
        "excluded_or_blocked": excluded_or_blocked,
        "formats_available": formats,
        "formats": formats,
        "downloads": downloads,
        "audit": {
            "generated_at_label": f"Situation {year}",
            "generated_from": "Memoire, actions, preuves et decisions de diffusion",
            "source_of_truth": False,
            "omissions_included": True,
        },
        "empty_states": {
            "no_content": {
                "is_visible": not bool(timeline or late_actions or transmit_items),
                "label": "Aucun contenu de passation disponible. Ajoutez des evenements memoire ou des actions ouvertes.",
                "href": _route_href("/chantiers"),
            },
            "blocked": {
                "is_visible": bool(blocker_rows),
                "label": "Export bloque: relisez la diffusion ou choisissez une synthese diffusable.",
                "href": _route_href("/confidentialite", scope="export", export="passation"),
            },
        },
    }


def _build_ux_model(
    instance: InstanceConfig,
    year: int,
    *,
    action_items: list[dict[str, str]],
    action_summary: dict[str, object],
    evidence_summary: dict[str, object],
    cockpit_alerts: list[dict[str, object]],
    accounting: dict[str, object],
    decisions: dict[str, object],
    incidents: dict[str, object],
    privacy: dict[str, object],
    documents: dict[str, object],
    piece_workshop: dict[str, object],
    trust_summary: dict[str, object],
) -> dict[str, object]:
    ux_items = [_ux_work_item(action) for action in action_items]
    by_status = action_summary.get("by_status") if isinstance(action_summary.get("by_status"), dict) else {}
    by_priority = action_summary.get("by_priority") if isinstance(action_summary.get("by_priority"), dict) else {}
    scope_counts = action_summary.get("scope_counts") if isinstance(action_summary.get("scope_counts"), dict) else {}
    decision_summary = decisions.get("summary") if isinstance(decisions.get("summary"), dict) else {}
    incident_summary = incidents.get("summary") if isinstance(incidents.get("summary"), dict) else {}
    privacy_summary = privacy.get("review_summary") if isinstance(privacy.get("review_summary"), dict) else {}
    document_actionable = documents.get("actionable") if isinstance(documents.get("actionable"), dict) else {}
    document_summary = document_actionable.get("summary") if isinstance(document_actionable.get("summary"), dict) else {}
    piece_summary = piece_workshop.get("summary") if isinstance(piece_workshop.get("summary"), dict) else {}
    comptes_model = _build_comptes_ux_model(instance, year, accounting)
    pieces_model = _build_pieces_ux_model(
        piece_workshop=piece_workshop,
        documents=documents,
        action_items=action_items,
        comptes=comptes_model,
    )
    pieces_model_summary = pieces_model.get("summary") if isinstance(pieces_model.get("summary"), dict) else {}
    p1_count = int(by_priority.get("P0", 0) or 0) + int(by_priority.get("P1", 0) or 0)
    missing_pieces = int(pieces_model_summary.get("missing_count") or 0) + int(pieces_model_summary.get("to_deposit_count") or 0)
    syndic_count = int(scope_counts.get("syndic", 0) or by_status.get("a_demander", 0) or 0)
    ag_count = int(decision_summary.get("open") or decision_summary.get("missing_proofs") or 0)
    risk_count = len(cockpit_alerts) + int(privacy_summary.get("blocked") or 0)

    todo_cards = [
        {
            "id": "late-actions",
            "label": "Actions en retard",
            "count": p1_count,
            "subtitle": "Prioritaires ou bloquees",
            "tone": "danger" if p1_count else "ok",
            "icon": "!",
            "href": "/actions?priority=P1",
        },
        {
            "id": "missing-pieces",
            "label": "Pieces manquantes",
            "count": missing_pieces,
            "subtitle": "A demander ou rattacher",
            "tone": "warn" if missing_pieces else "ok",
            "icon": "doc",
            "href": "/pieces?proof=missing",
        },
        {
            "id": "syndic-followups",
            "label": "Demandes syndic",
            "count": syndic_count,
            "subtitle": "Relances et reponses attendues",
            "tone": "danger" if syndic_count else "ok",
            "icon": "msg",
            "href": "/actions?scope=syndic",
        },
        {
            "id": "ag-deadlines",
            "label": "Echeances AG",
            "count": ag_count,
            "subtitle": "Decisions et preuves avant AG",
            "tone": "info" if ag_count else "ok",
            "icon": "cal",
            "href": "/chantiers?section=ag",
        },
        {
            "id": "risk-alerts",
            "label": "Alertes et risques",
            "count": risk_count,
            "subtitle": "Diffusion, incident ou blocage",
            "tone": "danger" if risk_count else "ok",
            "icon": "risk",
            "href": "/actions?status=a_revoir",
        },
    ]

    total_doc_slots = max(
        int(document_summary.get("total") or 0),
        int(document_summary.get("present") or 0) + missing_pieces,
        1,
    )
    completion_pct = max(0, min(100, round(100 * (total_doc_slots - missing_pieces) / total_doc_slots)))
    missing_items = [
        item
        for item in pieces_model.get("missing", [])
        if isinstance(item, dict)
    ][:4]
    syndic_items = [item for item in ux_items if item.get("lane") == "waiting_syndic"][:4]
    risk_rows = []
    for alert in cockpit_alerts[:6]:
        risk_rows.append(
            {
                "level": alert.get("severity", "P2"),
                "label": alert.get("title", "A surveiller"),
                "tone": _ux_tone(str(alert.get("severity", "P2"))),
                "subject": _public_text(alert.get("title"), "Point a surveiller"),
                "detail": _public_text(alert.get("detail"), "Verifier le point avec les preuves disponibles."),
                "impact": "Action CS requise",
                "due_or_detected": "A traiter maintenant",
                "status_label": "Ouvert",
                "status_tone": "warn",
                "href": alert.get("href") or "/actions",
            }
        )
    if not risk_rows:
        risk_rows.append(
            {
                "level": "OK",
                "label": "Aucune alerte critique",
                "tone": "ok",
                "subject": "Surveillance courante",
                "detail": "Aucun blocage prioritaire detecte dans les registres charges.",
                "impact": "Continuer le suivi",
                "due_or_detected": "Aujourd'hui",
                "status_label": "OK",
                "status_tone": "ok",
                "href": "/actions",
            }
        )

    accounting_before_ag = accounting.get("before_ag") if isinstance(accounting.get("before_ag"), dict) else {}
    accounting_score = max(
        0,
        min(
            100,
            int(accounting_before_ag.get("ok") or 0) * 10
            + int(accounting_before_ag.get("to_confirm") or 0) * 3
            - int(accounting_before_ag.get("blocking") or 0) * 5,
        ),
    )
    decision_rows = decisions.get("open_rows") if isinstance(decisions.get("open_rows"), list) else []
    ag_deadlines = [
        {
            "day": (row.get("echeance") or "A fixer")[-2:] if isinstance(row, dict) else "A fixer",
            "month": (row.get("echeance") or "AG")[:7] if isinstance(row, dict) else "AG",
            "title": _public_text(row.get("resolution_ref") or row.get("decision_action_id"), "Decision AG a suivre") if isinstance(row, dict) else "Decision AG",
            "subtitle": _public_text(row.get("action_attendue") or row.get("preuve_attendue"), "Preuve ou action attendue") if isinstance(row, dict) else "Preuve attendue",
            "relative_label": "Avant prochaine AG",
            "href": "/chantiers?section=ag",
        }
        for row in decision_rows[:3]
        if isinstance(row, dict)
    ]
    if not ag_deadlines:
        ag_deadlines = [
            {
                "day": "AG",
                "month": str(year),
                "title": "Preparation AG",
                "subtitle": "Verifier les decisions ouvertes et les pieces attendues.",
                "relative_label": "A planifier",
                "href": "/chantiers?section=ag",
            }
        ]

    shell = {
        "app_title": "CoproScope",
        "page_title": "Cockpit Conseil Syndical",
        "active_page": "overview",
        "search_placeholder": "Rechercher document, action, decision, fournisseur...",
        "notification_count": len(cockpit_alerts),
        "sharing_mode_label": "Mode prive local",
        "sharing_mode_status": "Aucune synchronisation externe lancee",
        "top_actions": [{"label": "Nouvelle demande", "href": "/demandes", "kind": "primary", "icon": "+"}],
        "nav_sections": [
            {
                "label": "Travail du CS",
                "items": [
                    _ux_nav_item("Tableau de bord", "/", "overview", "overview", icon="home"),
                    _ux_nav_item("A traiter", "/actions", "actions", "overview", icon="check", count=action_summary.get("total", 0)),
                    _ux_nav_item("Pieces manquantes", "/pieces?proof=missing", "pieces", "overview", icon="doc", count=missing_pieces),
                    _ux_nav_item("Demandes syndic", "/actions?scope=syndic", "actions", "overview", icon="msg", count=syndic_count),
                    _ux_nav_item("AG", "/chantiers?section=ag", "workstreams", "overview", icon="cal", count=ag_count),
                ],
            },
            {
                "label": "Dossiers",
                "items": [
                    _ux_nav_item("Controle comptes", "/comptes", "accounting", "overview", icon="chart", count=scope_counts.get("comptes", 0)),
                    _ux_nav_item("Documents", "/documents", "documents", "overview", icon="folder"),
                    _ux_nav_item("Memoire copropriete", "/chantiers", "workstreams", "overview", icon="timeline"),
                    _ux_nav_item("Diffusion et masquage", "/confidentialite", "privacy", "overview", icon="lock", count=privacy_summary.get("blocked", 0)),
                ],
            },
            {
                "label": "Coffre",
                "items": [
                    _ux_nav_item("Droits et roles", "/gouvernance", "governance", "overview", icon="users"),
                    _ux_nav_item("Depot local", "/depot", "depot", "overview", icon="inbox"),
                ],
            },
        ],
    }
    registre_model = _build_registre_model(
        instance,
        year,
        ux_items=ux_items,
        decisions=decisions,
        documents=documents,
    )
    action_detail = _action_detail_model(registre_model)
    priority_views = _build_priority_views(action_items=action_items, piece_workshop=piece_workshop, pieces_model=pieces_model)
    memoire_model = _build_memoire_ux_model(
        instance,
        year,
        ux_items=ux_items,
        accounting=accounting,
        decisions=decisions,
        incidents=incidents,
        privacy=privacy,
        documents=documents,
        piece_workshop=piece_workshop,
    )
    passation_export = _build_passation_export_model(
        year=year,
        memoire=memoire_model,
        priority_views=priority_views,
        action_detail=action_detail,
    )
    # Mark active page in templates that pass a different `page` value by keeping the
    # page ids stable; the template recomputes `aria-current` from `page`.
    ux_model = {
        "schema_version": "coproscope.ux.v1",
        "context": {
            "coffre": _public_text(instance.display_name, "Copropriete"),
            "exercise": year,
            "role": "Conseil syndical",
            "sharing_mode": "local",
        },
        "facets": {
            "lanes": dict(Counter(str(item.get("lane", "")) for item in ux_items)),
            "statuses": dict(Counter(str(item.get("status", "")) for item in ux_items)),
            "priorities": dict(Counter(str(item.get("priority", "")) for item in ux_items)),
        },
        "shell": shell,
        "work_items": ux_items,
        "cockpit": {
            "as_of_label": f"Situation {year}",
            "intro_title": "Ce qui demande attention maintenant",
            "summary_cards": todo_cards,
            "now": ux_items[:5],
            "lanes": {
                "this_week": [item for item in ux_items if item.get("lane") == "this_week"][:4],
                "waiting_syndic": syndic_items,
                "proofs_to_verify": [item for item in ux_items if item.get("lane") == "proofs_to_verify"][:4],
                "diffusion_risk": [item for item in ux_items if item.get("lane") == "diffusion_risk"][:4],
                "before_ag": ag_deadlines,
            },
            "missing_documents": {
                "completion_pct": completion_pct,
                "top_missing": [
                    {
                        "label": _public_text(item.get("expected_piece") or item.get("piece"), "Piece attendue"),
                        "count": 1,
                        "href": item.get("href") or "/pieces",
                        "reason": _public_text(item.get("next_step"), "Demander ou rattacher la piece."),
                    }
                    for item in missing_items
                ],
                "detail_href": "/pieces?proof=missing",
            },
            "syndic_requests": {
                "tabs": [
                    {"id": "waiting", "label": "En attente", "count": syndic_count, "is_active": True},
                    {"id": "running", "label": "En cours", "count": int(by_status.get("a_traiter", 0) or 0), "is_active": False},
                    {"id": "done", "label": "Resolues", "count": int(by_status.get("clos", 0) or 0), "is_active": False},
                ],
                "items": syndic_items,
                "all_href": "/actions?scope=syndic",
            },
            "ag": {
                "deadlines": ag_deadlines,
                "calendar_href": "/chantiers?section=ag",
            },
            "accounting": {
                "score": accounting_score,
                "conformes_count": int(accounting_before_ag.get("ok") or 0),
                "watch_count": int(accounting_before_ag.get("to_confirm") or 0),
                "anomaly_count": int(accounting_before_ag.get("blocking") or 0),
                "watch_items": [item for item in ux_items if item.get("kind") == "comptes"][:3],
                "detail_href": "/comptes",
            },
            "risk_alerts": risk_rows,
            "trust": {
                "cards": trust_summary.get("cards", []),
                "label": "Coffre local",
                "sync_label": "Statut sync a verifier",
                "sync_detail": "Cette page reste locale: aucune synchronisation externe n'est lancee depuis le cockpit.",
            },
            "empty_state": {
                "is_visible": not bool(ux_items),
                "title": "Coffre pret a alimenter",
                "detail": "Ajoutez des pieces ou importez des registres pour faire apparaitre les premieres actions.",
                "primary_action": {"label": "Ajouter une piece", "href": "/depot", "kind": "deposit"},
                "secondary_action": {"label": "Voir les chantiers", "href": "/chantiers", "kind": "memory"},
            },
        },
        "registre": registre_model,
        "priority_views": priority_views,
        "pieces": pieces_model,
        "action_detail": action_detail,
        "comptes": comptes_model,
        "memoire": memoire_model,
        "event_detail": memoire_model.get("event_detail", {}),
        "passation_export": passation_export,
        "passation_export_preview": passation_export,
    }
    sanitized = _sanitize_ux_public(ux_model)
    if isinstance(sanitized, dict):
        cockpit = sanitized.get("cockpit")
        if isinstance(cockpit, dict) and isinstance(cockpit.get("syndic_requests"), dict):
            cockpit["syndic_requests"] = _JinjaItemsDict(cockpit["syndic_requests"])
    return sanitized


def filter_action_items(
    actions: list[dict[str, str]],
    *,
    scope: str = "",
    priority: str = "",
    status: str = "",
) -> list[dict[str, str]]:
    scope = (scope or "").strip().lower()
    priority = (priority or "").strip().upper()
    status = (status or "").strip().lower()
    filtered = actions
    if scope and scope != "tous":
        filtered = [
            action
            for action in filtered
            if action.get("domain") == scope
            or action.get("channel") == scope
            or action.get("source", "").lower() == scope
        ]
    if priority and priority != "TOUS":
        filtered = [action for action in filtered if action.get("priority", "").upper() == priority]
    if status and status != "tous":
        filtered = [action for action in filtered if action.get("status") == status]
    if not filtered and (scope or priority or status):
        label = "Aucune fiche ne correspond a ces filtres."
        if status == "a_demander":
            label = "Aucune preuve a demander dans ce filtre."
        elif scope == "syndic":
            label = "Aucune relance syndic n'est en attente dans ce filtre."
        elif priority == "P1":
            label = "Aucune action prioritaire dans ce filtre."
        return [
            _action(
                label,
                "Registre Actions",
                priority or "P2",
                "Changer de filtre ou revenir au cockpit pour choisir une autre priorite.",
                "/actions",
                action_id=_stable_action_id("EMPTY-ACTION", 0, scope, priority, status),
                status=status or "a_traiter",
                domain=scope or "general",
                domain_label="Etat vide",
                owner="Conseil syndical",
                next_step="Changer de filtre ou ajouter une action avec une preuve attendue.",
                evidence="Aucune preuve attendue pour cet etat vide.",
            )
        ]
    return filtered


def actions_to_csv(actions: list[dict[str, str]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=ACTION_EXPORT_FIELDS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for action in actions:
        writer.writerow(action)
    return output.getvalue()


def _md_cell(value: str) -> str:
    return (value or "").replace("|", "\\|").replace("\n", " ").strip()


def actions_to_markdown(actions: list[dict[str, str]], title: str = "Actions CoproScope") -> str:
    lines = [
        f"# {title}",
        "",
        f"- Actions exportees: {len(actions)}",
        "",
        "| Priorite | Statut | Domaine | Titre | Prochaine etape | Preuve |",
        "|---|---|---|---|---|---|",
    ]
    for action in actions:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(action.get("priority", "")),
                    _md_cell(action.get("status", "")),
                    _md_cell(action.get("domain_label", "")),
                    _md_cell(action.get("title", "")),
                    _md_cell(action.get("next_step", "")),
                    _md_cell(action.get("evidence", "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _workstreams(decisions: dict[str, object], incidents: dict[str, object]) -> list[dict[str, object]]:
    decision_summary = decisions.get("summary") if isinstance(decisions.get("summary"), dict) else {}
    incident_summary = incidents.get("summary") if isinstance(incidents.get("summary"), dict) else {}
    decision_register = decisions.get("register")
    incident_register = incidents.get("register")
    decisions_total = int(decision_summary.get("total") or 0)
    missing_proofs = int(decision_summary.get("missing_proofs") or 0)
    open_incidents = int(incident_summary.get("open") or 0)
    incident_incomplete = int(incident_summary.get("incomplete") or 0)
    return [
        {
            "label": "Decisions AG",
            "status": _status(
                bool(decisions_total),
                bool(isinstance(decision_register, DataTable) and decision_register.exists),
            ),
            "detail": f"{decisions_total} decisions suivies, {missing_proofs} preuves manquantes.",
            "next": "Demander les preuves manquantes et confirmer les resolutions issues de convocations.",
            "items": decisions.get("items", [])[:5] if isinstance(decisions.get("items"), list) else [],
        },
        {
            "label": "WorksOps",
            "status": STATUS_NOT_STARTED,
            "detail": "Suivre devis, assurances, reception, garanties et ecarts travaux.",
            "next": "A lancer depuis les decisions AG et les pieces travaux deja reperees.",
            "items": [],
        },
        {
            "label": "IncidentOps",
            "status": _status(
                bool(open_incidents),
                bool(isinstance(incident_register, DataTable) and incident_register.exists),
            ),
            "detail": f"{open_incidents} incidents ouverts, {incident_incomplete} fiches incompletes.",
            "next": "Relancer les responsables et obtenir une preuve de cloture.",
            "items": incidents.get("open_rows", [])[:5] if isinstance(incidents.get("open_rows"), list) else [],
        },
        {
            "label": "ContractOps",
            "status": STATUS_NOT_STARTED,
            "detail": "Mettre les contrats sous surveillance : echeance, obligations, clauses, attestations.",
            "next": "Extraire une fiche contrat depuis DocOps.",
            "items": [],
        },
        {
            "label": "CommsOps",
            "status": STATUS_PARTIAL,
            "detail": "Produire des syntheses diffusables, biffees ou agregees.",
            "next": "Brancher PrivacyOps et les rapports existants.",
            "items": [],
        },
        {
            "label": "Passation CS",
            "status": STATUS_NOT_STARTED,
            "detail": "Generer un dossier nouveau conseil syndical : sujets ouverts, risques, calendrier, acces.",
            "next": "Composer le pack depuis les priorites du cockpit.",
            "items": [],
        },
    ]


def build_dashboard_model(instance: InstanceConfig, year: int = 2025) -> dict[str, object]:
    documents = _documents_model(instance)
    accounting = _accounting_model(instance, year)
    privacy = _privacy_model(instance)
    decisions = _decision_model(instance)
    incidents = _incident_model(instance)
    deposits = _deposits_model(instance)

    summary = accounting["summary"] if isinstance(accounting["summary"], dict) else {}
    non_matches = accounting["non_matches"]
    priority_controls = accounting["priority_controls"]
    controls_p1 = accounting["controls_p1"]
    review_rows = privacy["review_rows"]
    docops_actionable = documents.get("actionable") if isinstance(documents.get("actionable"), dict) else {}
    docops_summary = docops_actionable.get("summary") if isinstance(docops_actionable, dict) else {}
    decision_summary = decisions.get("summary") if isinstance(decisions.get("summary"), dict) else {}
    incident_summary = incidents.get("summary") if isinstance(incidents.get("summary"), dict) else {}
    priority_control_total = (
        priority_controls.count
        if isinstance(priority_controls, DataTable) and priority_controls.count
        else len(controls_p1) if isinstance(controls_p1, list) else 0
    )
    action_items = _build_action_items(documents, accounting, privacy, decisions, incidents)
    preview_actions = action_items[:13]
    action_summary = _action_summary(action_items, len(preview_actions))
    piece_workshop = _piece_workshop_model(documents, decisions, incidents)
    piece_workshop_summary = (
        piece_workshop["summary"] if isinstance(piece_workshop.get("summary"), dict) else {}
    )

    priorities: list[dict[str, str]] = []
    if isinstance(docops_summary, dict) and int(docops_summary.get("to_request") or 0):
        priorities.append(
            _priority(
                "Pieces documentaires a demander",
                "P2",
                f"{docops_summary.get('to_request')} pieces manquantes, obsoletes ou a classer sont transformees en actions.",
                "/actions?scope=documents",
            )
        )
    if isinstance(non_matches, DataTable) and non_matches.rows:
        priorities.append(
            _priority(
                "Factures a rapprocher",
                "P1",
                f"{len(non_matches.rows)} lignes demandent une clarification. Elles sont traitees comme actions de demande au syndic.",
                "/actions?scope=comptes",
            )
        )
    if isinstance(controls_p1, list) and controls_p1:
        priorities.append(
            _priority(
                "Controles comptables prioritaires",
                "P1",
                f"{priority_control_total} controles comptables prioritaires detectes ; {len(controls_p1)} sont affiches en apercu.",
                "/actions?scope=comptes",
            )
        )
    if isinstance(review_rows, list) and review_rows:
        priorities.append(
            _priority(
                "Confidentialite a revoir",
                "P2",
                f"{len(review_rows)} documents ou sorties demandent une revue.",
                "/actions?scope=confidentialite",
            )
        )
    if isinstance(decision_summary, dict) and int(decision_summary.get("missing_proofs") or 0):
        priorities.append(
            _priority(
                "Preuves de decisions a obtenir",
                "P1",
                f"{decision_summary.get('missing_proofs')} decisions AG n'ont pas encore de preuve rattachee.",
                "/actions?scope=decisions",
            )
        )
    if isinstance(incident_summary, dict) and int(incident_summary.get("open") or 0):
        priorities.append(
            _priority(
                "Incidents ouverts a suivre",
                "P1" if "P1" in incident_summary.get("priorities", {}) else "P2",
                f"{incident_summary.get('open')} incidents ouverts, {incident_summary.get('incomplete')} incomplets.",
                "/actions?scope=incidents",
            )
        )
    if not priorities:
        priorities.append(
            _priority(
                "Aucun blocage prioritaire detecte",
                "OK",
                "Les artefacts disponibles ne signalent pas de blocage immediat.",
                "/",
            )
        )

    cockpit_alerts = _cockpit_alerts(priorities, action_summary, privacy, piece_workshop)
    evidence_summary = _evidence_summary(action_items, piece_workshop, decisions, incidents)
    trust_summary = _trust_summary(instance, documents, privacy)
    ux_model = _build_ux_model(
        instance,
        year,
        action_items=action_items,
        action_summary=action_summary,
        evidence_summary=evidence_summary,
        cockpit_alerts=cockpit_alerts,
        accounting=accounting,
        decisions=decisions,
        incidents=incidents,
        privacy=privacy,
        documents=documents,
        piece_workshop=piece_workshop,
        trust_summary=trust_summary,
    )

    modules = [
        _module(
            "DocOps",
            _status(bool(documents["documents"].count), bool(documents["documents"].exists)),
            "Inventaire, hash, classement, completude.",
            "/documents",
        ),
        _module(
            "Atelier pieces",
            _status(
                bool(piece_workshop_summary.get("total")),
                bool(piece_workshop_summary.get("total")),
            ),
            "Pieces, points, actions attendues et preuves rattachees.",
            "/pieces",
        ),
        _module(
            "ComptaScope",
            _status(bool(summary), bool(accounting["paths"]["summary"].exists())),
            "Controle comptes guide et rapprochements.",
            "/comptes",
        ),
        _module(
            "PrivacyOps / BiffageOps",
            _status(bool(privacy["screening"].count), bool(privacy["screening"].exists)),
            "Screening, file de biffage, restrictions.",
            "/confidentialite",
        ),
        _module(
            "DecisionOps",
            _status(
                bool(decision_summary.get("total") if isinstance(decision_summary, dict) else 0),
                bool(decisions["register"].exists if isinstance(decisions.get("register"), DataTable) else False),
            ),
            "Decisions AG, echeances, preuves attendues.",
            "/chantiers",
        ),
        _module(
            "IncidentOps",
            _status(
                bool(incident_summary.get("total") if isinstance(incident_summary, dict) else 0),
                bool(incidents["register"].exists if isinstance(incidents.get("register"), DataTable) else False),
            ),
            "Incidents ouverts, prochaine action, preuve de cloture.",
            "/chantiers",
        ),
        _module(
            "Chantiers produit",
            STATUS_WORKING,
            "WorksOps, IncidentOps, CommsOps, passation.",
            "/chantiers",
        ),
        _module(
            "Depot & exports",
            _status(bool(deposits["count"]), bool(deposits["count"])),
            "Depot local, pipeline et pack local sur.",
            "/depot",
        ),
    ]
    ux_pieces_summary = (
        ux_model.get("pieces", {}).get("summary", {})
        if isinstance(ux_model.get("pieces"), dict)
        else {}
    )
    nav_missing_pieces = (
        int(ux_pieces_summary.get("missing_count") or 0)
        + int(ux_pieces_summary.get("to_deposit_count") or 0)
    )
    if not nav_missing_pieces and isinstance(docops_summary, dict):
        nav_missing_pieces = int(docops_summary.get("to_request") or 0)

    return {
        "instance": {
            "id": instance.instance_id,
            "name": instance.display_name,
            "root": str(instance.instance_root),
            "year": year,
        },
        "modules": modules,
        "priorities": priorities,
        "cockpit_alerts": cockpit_alerts,
        "evidence_summary": evidence_summary,
        "trust_summary": trust_summary,
        "actions": preview_actions,
        "action_items": action_items,
        "action_summary": action_summary,
        "piece_workshop": piece_workshop,
        "documents": documents,
        "accounting": accounting,
        "privacy": privacy,
        "decisions": decisions,
        "incidents": incidents,
        "deposits": deposits,
        "workstreams": _workstreams(decisions, incidents),
        "ux": ux_model,
        "kpis": {
            "documents": documents["documents"].count,
            "invoices": int(summary.get("invoice_count") or accounting["invoices"].count or 0),
            "controls": int(summary.get("control_count") or accounting["controls"].count or 0),
            "privacy_reviews": len(review_rows) if isinstance(review_rows, list) else 0,
            "decisions": int(decision_summary.get("total") or 0) if isinstance(decision_summary, dict) else 0,
            "open_incidents": int(incident_summary.get("open") or 0) if isinstance(incident_summary, dict) else 0,
            "doc_requests": nav_missing_pieces,
            "piece_workshop": int(piece_workshop_summary.get("total") or 0),
            "actions": len(action_items),
        },
    }
