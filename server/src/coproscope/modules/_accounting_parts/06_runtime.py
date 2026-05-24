from __future__ import annotations



def reconstruct_accounting(instance: InstanceConfig, run: RunContext, year: int) -> dict[str, object]:
    accounting_dir = instance.artifact("accounting_dir") / str(year)
    accounting_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, str]] = []
    controls: list[dict[str, str]] = []
    factureops_result = extract_invoices(instance, run, year)
    invoice_path = Path(str(factureops_result["invoice_evidence"]))
    invoice_anomalies_path = Path(str(factureops_result["invoice_anomalies"]))
    _, invoices = read_csv(invoice_path)
    _, invoice_anomalies = read_csv(invoice_anomalies_path)
    for invoice_row in invoices:
        entry = _entry_for_invoice(invoice_row, year, len(entries) + 1)
        if entry is not None:
            entries.append(entry)

    settings = _comptascope_settings(instance)
    configured_aliases = _load_supplier_aliases(instance)
    try:
        min_alias_evidence = int(settings.get("auto_alias_min_evidence", 2))
    except (TypeError, ValueError):
        min_alias_evidence = 2
    expense_lines = _load_expense_statement_lines(instance, accounting_dir, year)
    alias_suggestions = (
        suggest_supplier_aliases(invoices, expense_lines, configured_aliases, max(2, min_alias_evidence))
        if expense_lines
        else []
    )
    inferred_aliases = (
        supplier_aliases_from_suggestions(alias_suggestions)
        if _as_bool(settings.get("auto_infer_supplier_aliases"), True)
        else {}
    )
    effective_aliases = _merge_supplier_aliases(configured_aliases, inferred_aliases)
    expense_matches = reconcile_invoice_expenses(invoices, expense_lines, effective_aliases) if expense_lines else []
    for match in expense_matches:
        controls.extend(_controls_for_expense_match(match, year))
    supplier_due_invoices = invoices + _load_configured_supplier_due_invoice_triggers(
        instance,
        year,
        {row.get("doc_id", "") for row in invoices},
    )
    supplier_due_diligence = build_supplier_due_diligence_controls(instance, supplier_due_invoices, year)
    review_rows = _build_comptascope_review_rows(
        year=year,
        invoices=invoices,
        entries=entries,
        invoice_anomalies=invoice_anomalies,
        matches=expense_matches,
    )
    review_group_rows = _build_comptascope_review_group_rows(year=year, review_rows=review_rows)
    expense_match_doc_ids = {row.get("doc_id", "") for row in expense_matches}
    for row in review_rows:
        if row.get("doc_id", "") in expense_match_doc_ids:
            continue
        control = _control_for_unmatched_review_row(row, year)
        if control is not None:
            controls.append(control)

    if not invoices:
        controls.append(
            {
                "control_id": f"CTRL-{year}-NO-INVOICE",
                "exercice": str(year),
                "severity": "P0",
                "control": "AUCUNE_FACTURE_RECONSTITUEE",
                "status": "A_TRAITER",
                "doc_id": "",
                "evidence": str(instance.root("raw")),
                "action": "Verifier les sources et lancer l'inventaire documentaire.",
            }
        )

    entries_path = accounting_dir / f"ledger_reconstruction_{year}.csv"
    controls_path = accounting_dir / f"accounting_controls_{year}.csv"
    expense_lines_path = accounting_dir / f"expense_statement_lines_{year}.csv"
    expense_matches_path = accounting_dir / f"invoice_expense_matches_{year}.csv"
    non_matches_path = accounting_dir / f"non_rapproches_prioritaires_{year}.csv"
    alias_suggestions_path = accounting_dir / f"supplier_alias_suggestions_{year}.csv"
    supplier_due_diligence_path = accounting_dir / f"supplier_due_diligence_controls_{year}.csv"
    review_path = accounting_dir / f"controle_comptes_guide_{year}.csv"
    review_groups_path = accounting_dir / f"regroupement_controle_comptes_{year}.csv"
    syndic_questions_path = accounting_dir / f"questions_syndic_comptascope_{year}.md"
    report_path = accounting_dir / f"rapport_comptascope_{year}.md"
    write_csv(entries_path, ACCOUNTING_ENTRY_FIELDS, entries)
    write_csv(controls_path, ACCOUNTING_CONTROL_FIELDS, controls)
    write_csv(expense_lines_path, EXPENSE_STATEMENT_FIELDS, expense_lines)
    write_csv(expense_matches_path, INVOICE_EXPENSE_MATCH_FIELDS, expense_matches)
    write_csv(alias_suggestions_path, SUPPLIER_ALIAS_SUGGESTION_FIELDS, alias_suggestions)
    write_csv(supplier_due_diligence_path, SUPPLIER_DUE_DILIGENCE_FIELDS, supplier_due_diligence)
    write_csv(review_path, COMPTASCOPE_REVIEW_FIELDS, review_rows)
    write_csv(review_groups_path, COMPTASCOPE_REVIEW_GROUP_FIELDS, review_group_rows)
    _write_syndic_questions(syndic_questions_path, year=year, review_rows=review_rows)
    non_matches = [
        {
            "doc_id": row.get("doc_id", ""),
            "fournisseur": row.get("fournisseur", ""),
            "numero_facture": row.get("numero_facture", ""),
            "ttc": row.get("ttc", ""),
            "match_status": row.get("statut_rapprochement", ""),
            "match_priority": row.get("priorite", ""),
            "status_label": row.get("libelle_statut", ""),
            "match_reason": row.get("motif", ""),
            "next_action": row.get("prochaine_action", ""),
        }
        for row in review_rows
        if row.get("priorite") != "OK"
    ]
    non_matches.sort(key=lambda row: (_decimal(row.get("ttc")) or Decimal("0")), reverse=True)
    write_csv(non_matches_path, NON_MATCH_PRIORITY_FIELDS, non_matches)
    _write_accounting_report(
        report_path,
        year=year,
        invoices=invoices,
        entries=entries,
        controls=controls,
        invoice_anomalies=invoice_anomalies,
        expense_lines=expense_lines,
        matches=expense_matches,
        alias_suggestions=alias_suggestions,
        supplier_due_diligence=supplier_due_diligence,
        review_rows=review_rows,
        review_group_rows=review_group_rows,
    )

    duckdb_path = accounting_dir / f"coproscope_accounting_{year}.duckdb"
    duckdb_tables = {
            "invoice_evidence": (INVOICE_EVIDENCE_FIELDS, invoices),
            "invoice_anomalies": (INVOICE_ANOMALY_FIELDS, invoice_anomalies),
            "ledger_reconstruction": (ACCOUNTING_ENTRY_FIELDS, entries),
            "accounting_controls": (ACCOUNTING_CONTROL_FIELDS, controls),
    }
    duckdb_tables["expense_statement_lines"] = (EXPENSE_STATEMENT_FIELDS, expense_lines)
    duckdb_tables["invoice_expense_matches"] = (INVOICE_EXPENSE_MATCH_FIELDS, expense_matches)
    duckdb_tables["supplier_alias_suggestions"] = (SUPPLIER_ALIAS_SUGGESTION_FIELDS, alias_suggestions)
    duckdb_tables["supplier_due_diligence_controls"] = (
        SUPPLIER_DUE_DILIGENCE_FIELDS,
        supplier_due_diligence,
    )
    duckdb_tables["controle_comptes_guide"] = (COMPTASCOPE_REVIEW_FIELDS, review_rows)
    duckdb_tables["regroupement_controle_comptes"] = (COMPTASCOPE_REVIEW_GROUP_FIELDS, review_group_rows)
    duckdb_written = _write_duckdb(duckdb_path, duckdb_tables)

    summary = {
        "status": "ok",
        "year": year,
        "invoice_count": len(invoices),
        "entry_count": len(entries),
        "control_count": len(controls),
        "invoice_anomaly_count": len(invoice_anomalies),
        "expense_statement_line_count": len(expense_lines),
        "expense_match_counts": dict(Counter(row.get("match_status", "") for row in expense_matches)),
        "supplier_alias_suggestion_count": len(alias_suggestions),
        "supplier_alias_auto_count": sum(1 for row in alias_suggestions if row.get("suggestion_status") == "AUTO_APPLICABLE"),
        "supplier_due_diligence_count": len(supplier_due_diligence),
        "supplier_due_diligence_status_counts": dict(
            Counter(row.get("coverage_status", "") for row in supplier_due_diligence)
        ),
        "review_item_count": len(review_rows),
        "review_group_count": len(review_group_rows),
        "syndic_question_count": sum(1 for row in review_rows if row.get("question_syndic")),
        "invoice_evidence": str(invoice_path),
        "invoice_anomalies": str(invoice_anomalies_path),
        "ledger_reconstruction": str(entries_path),
        "accounting_controls": str(controls_path),
        "expense_statement_lines": str(expense_lines_path),
        "invoice_expense_matches": str(expense_matches_path),
        "non_rapproches_prioritaires": str(non_matches_path),
        "supplier_alias_suggestions": str(alias_suggestions_path),
        "supplier_due_diligence_controls": str(supplier_due_diligence_path),
        "controle_comptes_guide": str(review_path),
        "regroupement_controle_comptes": str(review_groups_path),
        "questions_syndic_comptascope": str(syndic_questions_path),
        "report": str(report_path),
        "duckdb": str(duckdb_path) if duckdb_written else "",
        "generated_at": now_iso(),
    }
    write_text(accounting_dir / f"summary_{year}.json", json.dumps(summary, indent=2, ensure_ascii=True))
    run.log_action("accounting_reconstruct", accounting_dir, f"year={year}; invoices={len(invoices)}")
    return summary


def accounting_controls(instance: InstanceConfig, run: RunContext, year: int) -> dict[str, object]:
    ensure_accounting_outputs(instance, run, year)
    accounting_dir = instance.artifact("accounting_dir") / str(year)
    controls_path = accounting_dir / f"accounting_controls_{year}.csv"
    _, rows = read_csv(controls_path)
    summary = {
        "status": "ok",
        "year": year,
        "control_count": len(rows),
        "p0_count": sum(1 for row in rows if row.get("severity") == "P0"),
        "controls": str(controls_path),
    }
    run.log_action("accounting_controls", controls_path, f"year={year}; controls={len(rows)}")
    return summary


def required_accounting_report_paths(instance: InstanceConfig, year: int) -> list[Path]:
    accounting_dir = instance.artifact("accounting_dir") / str(year)
    names = [
        f"invoice_evidence_{year}.csv",
        f"invoice_anomalies_{year}.csv",
        f"ledger_reconstruction_{year}.csv",
        f"accounting_controls_{year}.csv",
        f"expense_statement_lines_{year}.csv",
        f"invoice_expense_matches_{year}.csv",
        f"non_rapproches_prioritaires_{year}.csv",
        f"supplier_alias_suggestions_{year}.csv",
        f"supplier_due_diligence_controls_{year}.csv",
        f"controle_comptes_guide_{year}.csv",
        f"regroupement_controle_comptes_{year}.csv",
        f"questions_syndic_comptascope_{year}.md",
        f"rapport_comptascope_{year}.md",
        f"summary_{year}.json",
    ]
    return [accounting_dir / name for name in names]


def ensure_accounting_outputs(instance: InstanceConfig, run: RunContext, year: int) -> dict[str, object] | None:
    missing = [path for path in required_accounting_report_paths(instance, year) if not path.exists()]
    if missing:
        result = reconstruct_accounting(instance, run, year)
        run.log_action(
            "accounting_report_refresh",
            instance.artifact("accounting_dir") / str(year),
            "missing=" + ",".join(path.name for path in missing),
        )
        return result
    return None


def copy_accounting_tables_for_dashboard(instance: InstanceConfig, year: int, target_dir: Path) -> dict[str, str]:
    accounting_dir = instance.artifact("accounting_dir") / str(year)
    target_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[str, str] = {}
    for name in [
        "invoice_evidence",
        "invoice_anomalies",
        "ledger_reconstruction",
        "accounting_controls",
        "expense_statement_lines",
        "invoice_expense_matches",
        "non_rapproches_prioritaires",
        "supplier_alias_suggestions",
        "supplier_due_diligence_controls",
        "controle_comptes_guide",
        "regroupement_controle_comptes",
    ]:
        source = accounting_dir / f"{name}_{year}.csv"
        if not source.exists() and name == "ledger_reconstruction":
            source = accounting_dir / f"ledger_reconstruction_{year}.csv"
        if source.exists():
            destination = target_dir / source.name
            destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            copied[name] = str(destination)
    report = accounting_dir / f"rapport_comptascope_{year}.md"
    if report.exists():
        destination = target_dir / report.name
        destination.write_text(report.read_text(encoding="utf-8"), encoding="utf-8")
        copied["rapport_comptascope"] = str(destination)
    questions = accounting_dir / f"questions_syndic_comptascope_{year}.md"
    if questions.exists():
        destination = target_dir / questions.name
        destination.write_text(questions.read_text(encoding="utf-8"), encoding="utf-8")
        copied["questions_syndic_comptascope"] = str(destination)
    return copied
