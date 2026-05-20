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
        "artifacts": [
            _artifact(instance, "Registre documents", documents_path, "csv"),
            _artifact(instance, "Registre demandes", requests_path, "csv"),
            _artifact(instance, "Registre AG", ag_path, "csv"),
            _artifact(instance, "Constats", findings_path, "csv"),
            _artifact(instance, "KPI", kpi_path, "csv"),
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
    return {
        "paths": paths,
        "summary": summary,
        "controls": controls,
        "priority_controls": priority_controls,
        "controls_p1": controls_p1[:30],
        "syndic_questions": _syndic_questions(non_matches, controls_p1),
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
    return {
        "paths": paths,
        "screening": screening,
        "redactions": redactions,
        "queue": queue,
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


def _stable_action_id(prefix: str, index: int, *parts: str) -> str:
    raw = "|".join(part for part in parts if part).strip()
    if raw:
        digest = hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:8].upper()
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
        title = row.get("title") or row.get("document_type") or row.get("doc_id") or "Piece documentaire"
        actions.append(
            _action(
                title,
                "DocOps",
                row.get("severity") or row.get("priority") or "P2",
                row.get("detail") or row.get("finding") or row.get("status") or "Piece documentaire a verifier.",
                "/documents",
                action_id=_stable_action_id("ACT-DOC", index, row.get("finding_id", ""), row.get("doc_id", ""), title),
                status="a_verifier",
                domain="documents",
                domain_label="Documents",
                owner="Conseil syndical",
                next_step=row.get("next_action") or row.get("action") or "Verifier la piece ou preparer une demande au syndic.",
                evidence=row.get("evidence") or row.get("original_path") or row.get("doc_id") or title,
                channel="syndic" if "syndic" in " ".join(row.values()).lower() else "",
            )
        )
    return actions


def _action_rank(action: dict[str, str]) -> tuple[int, int, str]:
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "OK": 4}
    status_rank = {"bloque": 0, "a_demander": 1, "a_traiter": 2, "a_revoir": 3, "a_verifier": 4, "clos": 9}
    return (
        priority_rank.get(action.get("priority", "P2"), 2),
        status_rank.get(action.get("status", "a_traiter"), 4),
        action.get("title", "").lower(),
    )


def _build_action_items(documents: dict[str, object], accounting: dict[str, object], privacy: dict[str, object]) -> list[dict[str, str]]:
    non_matches = accounting.get("non_matches")
    priority_controls = accounting.get("priority_controls")
    review_rows = privacy.get("review_rows")
    stale_or_missing = documents.get("stale_or_missing")
    actions: list[dict[str, str]] = []
    if isinstance(non_matches, DataTable) and isinstance(priority_controls, DataTable):
        actions.extend(_accounting_actions(non_matches, priority_controls))
    if isinstance(review_rows, list):
        actions.extend(_privacy_actions(review_rows))
    if isinstance(stale_or_missing, list):
        actions.extend(_document_actions(stale_or_missing))
    return sorted(actions, key=_action_rank)


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
        "by_domain": by_domain,
        "by_priority": _action_counter(actions, "priority"),
        "by_status": _action_counter(actions, "status"),
        "scope_counts": {
            "tous": len(actions),
            "comptes": _scope_count(actions, "comptes"),
            "confidentialite": _scope_count(actions, "confidentialite"),
            "documents": _scope_count(actions, "documents"),
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


def _workstreams() -> list[dict[str, str]]:
    return [
        {
            "label": "Decision -> action -> preuve",
            "status": STATUS_WORKING,
            "detail": "Transformer les resolutions AG en actions suivies avec preuves, echeances et relances.",
            "next": "Creer le registre cible et le brancher aux PV AG.",
        },
        {
            "label": "WorksOps",
            "status": STATUS_WORKING,
            "detail": "Suivre devis, assurances, reception, garanties et ecarts travaux.",
            "next": "Demarrer par un dossier travaux minimal.",
        },
        {
            "label": "IncidentOps",
            "status": STATUS_WORKING,
            "detail": "Tracer incidents, photos, statuts, syndic, prestataire et preuve de cloture.",
            "next": "Creer un registre incident simple.",
        },
        {
            "label": "ContractOps",
            "status": STATUS_NOT_STARTED,
            "detail": "Mettre les contrats sous surveillance : echeance, obligations, clauses, attestations.",
            "next": "Extraire une fiche contrat depuis DocOps.",
        },
        {
            "label": "CommsOps",
            "status": STATUS_WORKING,
            "detail": "Produire des syntheses diffusables, biffees ou agregees.",
            "next": "Brancher PrivacyOps et les rapports existants.",
        },
        {
            "label": "Passation CS",
            "status": STATUS_NOT_STARTED,
            "detail": "Generer un dossier nouveau conseil syndical : sujets ouverts, risques, calendrier, acces.",
            "next": "Composer le pack depuis les priorites du cockpit.",
        },
    ]


def build_dashboard_model(instance: InstanceConfig, year: int = 2025) -> dict[str, object]:
    documents = _documents_model(instance)
    accounting = _accounting_model(instance, year)
    privacy = _privacy_model(instance)

    summary = accounting["summary"] if isinstance(accounting["summary"], dict) else {}
    non_matches = accounting["non_matches"]
    priority_controls = accounting["priority_controls"]
    controls_p1 = accounting["controls_p1"]
    review_rows = privacy["review_rows"]
    priority_control_total = (
        priority_controls.count
        if isinstance(priority_controls, DataTable) and priority_controls.count
        else len(controls_p1) if isinstance(controls_p1, list) else 0
    )
    action_items = _build_action_items(documents, accounting, privacy)
    preview_actions = action_items[:13]
    action_summary = _action_summary(action_items, len(preview_actions))

    priorities: list[dict[str, str]] = []
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
            "Chantiers produit",
            STATUS_WORKING,
            "WorksOps, IncidentOps, CommsOps, passation.",
            "/chantiers",
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
        "documents": documents,
        "accounting": accounting,
        "privacy": privacy,
        "workstreams": _workstreams(),
        "kpis": {
            "documents": documents["documents"].count,
            "invoices": int(summary.get("invoice_count") or accounting["invoices"].count or 0),
            "controls": int(summary.get("control_count") or accounting["controls"].count or 0),
            "privacy_reviews": len(review_rows) if isinstance(review_rows, list) else 0,
            "actions": len(action_items),
        },
    }
