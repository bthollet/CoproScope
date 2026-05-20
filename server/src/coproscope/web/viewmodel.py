from __future__ import annotations

import csv
import hashlib
import html
import json
from collections import Counter
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any

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


def _syndic_questions(non_matches: DataTable, controls_p1: list[dict[str, str]]) -> list[dict[str, str]]:
    questions = [_question_from_non_match(row) for row in non_matches.rows[:20]]
    questions.extend(_question_from_control(row) for row in controls_p1[:20])
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "OK": 3}
    return sorted(questions, key=lambda row: priority_order.get(row.get("priority", "P2"), 2))[:30]


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

    controls_p1 = priority_controls.rows or [
        row
        for row in controls.rows
        if row.get("severity") in {"P0", "P1"} or row.get("status") in {"P0", "P1", "BLOQUE", "A_TRAITER"}
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
    return {
        "paths": paths,
        "summary": summary,
        "controls": controls,
        "priority_controls": priority_controls,
        "controls_p1": controls_p1[:30],
        "syndic_questions": _syndic_questions(non_matches, controls_p1),
        "supplier_focus": supplier_focus,
        "blocker_types": {
            "matches": match_status,
            "non_matches": _counter(non_matches.rows, "match_status"),
            "controls": _counter(controls.rows, "status"),
        },
        "before_ag": {
            "blocking": len(blocking_non_matches) + len(controls_p1),
            "to_confirm": len(to_confirm_non_matches),
            "ok": match_status.get("MATCH", 0) + match_status.get("OK", 0) + match_status.get("RAPPROCHE", 0),
        },
        "non_matches": non_matches,
        "matches": matches,
        "invoices": invoices,
        "anomalies": anomalies,
        "match_status": match_status,
        "non_match_priorities": non_match_priorities,
        "report": _read_report(paths["report"]),
        "artifacts": [
            _artifact(instance, "Synthese", paths["summary"], "json"),
            _artifact(instance, "Factures candidates", paths["invoice_evidence"], "csv"),
            _artifact(instance, "Anomalies facture", paths["invoice_anomalies"], "csv"),
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


def _accounting_actions(non_matches: DataTable, priority_controls: DataTable) -> list[dict[str, str]]:
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
    for index, row in enumerate(priority_controls.rows):
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
    priority_controls = accounting.get("priority_controls")
    review_rows = privacy.get("review_rows")
    stale_or_missing = documents.get("stale_or_missing")
    actionable = documents.get("actionable")
    actions: list[dict[str, str]] = []
    if isinstance(non_matches, DataTable) and isinstance(priority_controls, DataTable):
        actions.extend(_accounting_actions(non_matches, priority_controls))
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
) -> dict[str, object]:
    has_local_proof = bool(proof_ref)
    requires_action = _workshop_requires_action(status)
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
        "next_step": next_step or action or "Qualifier le point puis rattacher la preuve.",
        "proof_ref": proof_ref,
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
            items.append(
                _piece_workshop_item(
                    source="DocOps",
                    point_type="Lot documentaire",
                    point=row.get("lot", ""),
                    point_id=proof_id,
                    piece=row.get("expected_label") or row.get("document_type") or proof_id,
                    status=status,
                    priority=request.get("priority") or row.get("criticality", "P2"),
                    action=action,
                    next_step=next_step,
                    proof_ref=proof_ref,
                    request_id=request.get("request_id", ""),
                    href="/documents",
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
            items.append(
                _piece_workshop_item(
                    source="DecisionOps",
                    point_type="Decision AG",
                    point=point,
                    point_id=row.get("decision_action_id", ""),
                    piece=row.get("preuve_attendue") or row.get("proof_document_types") or "Preuve de decision",
                    status=status,
                    priority=row.get("priorite", "P2"),
                    action=row.get("action_attendue", ""),
                    next_step=next_step,
                    proof_ref=proof_ref,
                    href="/chantiers",
                )
            )

    incident_rows = incidents.get("open_rows")
    if isinstance(incident_rows, list):
        for row in incident_rows:
            if not isinstance(row, dict):
                continue
            status = incidentops.normalize_status(row.get("status"))
            point_parts = [row.get("incident_id", ""), row.get("lieu", ""), _clip(row.get("description", ""), 110)]
            items.append(
                _piece_workshop_item(
                    source="IncidentOps",
                    point_type="Incident",
                    point=" - ".join(part for part in point_parts if part),
                    point_id=row.get("incident_id", ""),
                    piece=row.get("expected_closure_proof") or "Preuve de cloture",
                    status=status,
                    priority=row.get("priority", "P2"),
                    action=row.get("next_action", ""),
                    next_step=row.get("next_action", ""),
                    proof_ref=row.get("closure_proof_ref", ""),
                    href="/chantiers",
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

    return {
        "instance": {
            "id": instance.instance_id,
            "name": instance.display_name,
            "root": str(instance.instance_root),
            "year": year,
        },
        "modules": modules,
        "priorities": priorities,
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
        "kpis": {
            "documents": documents["documents"].count,
            "invoices": int(summary.get("invoice_count") or accounting["invoices"].count or 0),
            "controls": int(summary.get("control_count") or accounting["controls"].count or 0),
            "privacy_reviews": len(review_rows) if isinstance(review_rows, list) else 0,
            "decisions": int(decision_summary.get("total") or 0) if isinstance(decision_summary, dict) else 0,
            "open_incidents": int(incident_summary.get("open") or 0) if isinstance(incident_summary, dict) else 0,
            "doc_requests": int(docops_summary.get("to_request") or 0) if isinstance(docops_summary, dict) else 0,
            "piece_workshop": int(piece_workshop_summary.get("total") or 0),
            "actions": len(action_items),
        },
    }
