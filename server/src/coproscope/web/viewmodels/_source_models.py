from __future__ import annotations

from ._runtime import *

_PUBLIC_DOC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_PRIVATE_REFERENCE_RE = re.compile(
    r"file://|(?<![A-Za-z])[A-Za-z]:[\\/]|(?:^|[\\/\s\"'=])/(?:Users|home)[\\/]|"
    r"(?:^|[\\/_\s\"'=.-])(?:raw|restricted|logs|private|100_collecte_raw|220_assemblees)(?=$|[\\/_\s\"'=.-])",
    re.IGNORECASE,
)
_PUBLIC_MASKED_REFERENCE = "[reference locale masquee]"


def _document_display_label(row: dict[str, str]) -> str:
    for key in ("file_name", "filename"):
        label = _safe_basename(row.get(key, ""))
        if label:
            return label
    return _public_doc_id(row.get("doc_id", "")) or "Document"


def _safe_basename(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    basename = next((part for part in reversed(text.replace("\\", "/").split("/")) if part), "")
    if basename in {"", ".", ".."} or _looks_private_reference(basename):
        return ""
    return _clip(basename, 100)


def _public_doc_id(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if ".." in text or "/" in text or "\\" in text or not _PUBLIC_DOC_ID_RE.fullmatch(text):
        return _PUBLIC_MASKED_REFERENCE
    return text


def _looks_private_reference(value: object) -> bool:
    return bool(_PRIVATE_REFERENCE_RE.search(str(value or "").replace("\\", "/")))


def _public_cell(value: object, fallback: str = _PUBLIC_MASKED_REFERENCE) -> str:
    text = _clip(str(value or "").strip(), 160)
    if not text:
        return ""
    return fallback if _looks_private_reference(text) else text


def _public_report(report: dict[str, str]) -> dict[str, str]:
    if not report.get("exists"):
        return report
    text = report.get("text", "")
    if not _looks_private_reference(text):
        return report
    masked = "Rapport disponible localement; apercu masque car il contient des references locales privees."
    return {**report, "text": masked, "html": html.escape(masked)}


def _safe_document_rows(table: DataTable) -> DataTable:
    rows = []
    for row in table.rows:
        safe = dict(row)
        safe["display_file_name"] = _document_display_label(row)
        safe["display_doc_id"] = _public_doc_id(row.get("doc_id", ""))
        safe["display_document_type"] = _public_cell(row.get("document_type") or row.get("extension"))
        safe["display_confidentiality"] = _public_cell(
            row.get("derivative_max_college") or row.get("raw_max_college") or row.get("sensitivity")
        )
        doc_id = row.get("doc_id", "").strip()
        safe["detail_href"] = f"/documents/{quote(doc_id)}" if _public_doc_id(doc_id) == doc_id else ""
        rows.append(safe)
    return DataTable(path=table.path, fields=table.fields, rows=rows)


def _safe_document_actionable(actionable: dict[str, object]) -> dict[str, object]:
    copied = dict(actionable)
    for key in ("present", "missing", "obsolete", "to_classify", "to_request"):
        rows = copied.get(key)
        if isinstance(rows, list):
            copied[key] = [_safe_docops_row(row) for row in rows if isinstance(row, dict)]
    return copied


def _safe_docops_row(row: dict[str, str]) -> dict[str, str]:
    safe = dict(row)
    for key, value in row.items():
        safe[key] = _public_cell(value)
    safe["display_evidence_ref"] = _public_cell(row.get("evidence_paths") or row.get("matched_doc_ids"))
    return safe


def _safe_privacy_rows(table: DataTable) -> DataTable:
    rows = []
    for row in table.rows:
        safe = dict(row)
        safe["display_file_name"] = _document_display_label(row)
        safe["display_doc_id"] = _public_doc_id(row.get("doc_id", ""))
        safe["display_review_status"] = _public_cell(row.get("privacy_review_status") or row.get("remediation_priority"))
        safe["display_decision"] = _public_cell(row.get("review_status_recommendation") or row.get("required_transformations"))
        safe["display_next_step"] = _public_cell(
            row.get("publication_blocker") or row.get("review_next_step") or row.get("recommended_action")
        )
        safe["display_queue_status"] = _public_cell(row.get("queue_status"))
        safe["display_transformations"] = _public_cell(row.get("required_transformations"))
        safe["display_mode"] = _public_cell(row.get("recommended_mode"))
        rows.append(safe)
    return DataTable(path=table.path, fields=table.fields, rows=rows)


def _decision_dedupe_key(row: dict[str, str], index: int) -> tuple[str, ...]:
    decision_id = row.get("decision_action_id", "").strip()
    if decision_id:
        return ("id", decision_id)
    business_key = (
        row.get("ag_id", "").strip(),
        row.get("source_doc_id", "").strip(),
        row.get("resolution_ref", "").strip(),
        row.get("decision_text", "").strip(),
        row.get("action_attendue", "").strip(),
        row.get("preuve_attendue", "").strip(),
    )
    if any(business_key):
        return ("business", *business_key)
    return ("row", str(index))


def _decision_row_score(row: dict[str, str]) -> tuple[int, int, int]:
    proof_score = 1 if row.get("proof_doc_ids") else 0
    request_score = 1 if row.get("related_request_ids") else 0
    text_score = sum(1 for value in row.values() if str(value or "").strip())
    return (proof_score, request_score, text_score)


def _dedupe_decision_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected: dict[tuple[str, ...], dict[str, str]] = {}
    order: list[tuple[str, ...]] = []
    for index, row in enumerate(rows):
        key = _decision_dedupe_key(row, index)
        current = selected.get(key)
        if current is None:
            order.append(key)
            selected[key] = row
            continue
        if _decision_row_score(row) > _decision_row_score(current):
            selected[key] = row
    return [selected[key] for key in order]


def _decision_model(instance: InstanceConfig) -> dict[str, object]:
    register_path = decisionops.decision_register_path(instance)
    register = _read_table(register_path)
    report_path = instance.artifact("reports_dir") / "rapport_decisions_actions_preuves.md"
    raw_rows = register.rows
    rows = _dedupe_decision_rows(raw_rows)
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
            "total": len(rows),
            "raw_total": register.count,
            "deduplicated": max(0, register.count - len(rows)),
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
    documents = _safe_document_rows(documents)
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
        "missing_report": _public_report(_read_report(missing_report)),
        "ag_report": _public_report(_read_report(ag_report)),
        "document_types": _counter(documents.rows, "document_type"),
        "source_zones": _counter(documents.rows, "source_zone"),
        "stale_or_missing": [_safe_docops_row(row) for row in stale_or_missing[:20]],
        "actionable": _safe_document_actionable(_docops_actionable_model(completeness_matrix, document_requests)),
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
    screening = _safe_privacy_rows(_read_table(paths["screening"]))
    redactions = _read_table(paths["redactions"])
    queue = _safe_privacy_rows(_read_table(paths["queue"]))
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
        "report": _public_report(_read_report(paths["report"])),
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
