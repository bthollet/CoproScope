from __future__ import annotations



def _write_accounting_report(
    path: Path,
    *,
    year: int,
    invoices: list[dict[str, str]],
    entries: list[dict[str, str]],
    controls: list[dict[str, str]],
    invoice_anomalies: list[dict[str, str]],
    expense_lines: list[dict[str, str]],
    matches: list[dict[str, str]],
    alias_suggestions: list[dict[str, str]] | None = None,
    supplier_due_diligence: list[dict[str, str]] | None = None,
    review_rows: list[dict[str, str]] | None = None,
    review_group_rows: list[dict[str, str]] | None = None,
) -> None:
    alias_suggestions = alias_suggestions or []
    supplier_due_diligence = supplier_due_diligence or []
    review_rows = review_rows or []
    review_group_rows = review_group_rows or []
    matched_doc_ids = {row.get("doc_id", "") for row in matches}
    report_match_rows = list(matches)
    for row in review_rows:
        if row.get("doc_id", "") in matched_doc_ids:
            continue
        report_match_rows.append(
            {
                "doc_id": row.get("doc_id", ""),
                "numero_facture": row.get("numero_facture", ""),
                "fournisseur": row.get("fournisseur", ""),
                "ttc": row.get("ttc", ""),
                "match_status": row.get("statut_rapprochement", ""),
                "match_priority": row.get("priorite", ""),
                "status_label": row.get("libelle_statut", ""),
                "match_reason": row.get("motif", ""),
                "next_action": row.get("prochaine_action", ""),
            }
        )
    total_ttc = sum((_decimal(row.get("ttc")) or Decimal("0")) for row in invoices)
    match_statuses = Counter(row.get("match_status", "") or "SANS_ETAT_DEPENSES" for row in report_match_rows)
    priority_counts = Counter(row.get("match_priority", _status_priority(row.get("match_status", ""))) for row in report_match_rows)
    supplier_open_counts = Counter(row.get("fournisseur", "") or "FOURNISSEUR_A_IDENTIFIER" for row in report_match_rows if row.get("match_priority") != "OK")
    supplier_open_totals: Counter[str] = Counter()
    for row in report_match_rows:
        if row.get("match_priority") != "OK":
            supplier_open_totals[row.get("fournisseur", "") or "FOURNISSEUR_A_IDENTIFIER"] += _decimal(row.get("ttc")) or Decimal("0")
    control_severities = Counter(row.get("severity", "") for row in controls)
    invoice_anomaly_severities = Counter(row.get("severity", "") for row in invoice_anomalies)
    invoice_anomaly_types = Counter(row.get("anomaly", "") for row in invoice_anomalies)
    evidence_levels = Counter(row.get("evidence_level", "") or "NON_RENSEIGNE" for row in invoices)
    alias_statuses = Counter(row.get("suggestion_status", "") for row in alias_suggestions)
    supplier_due_statuses = Counter(row.get("coverage_status", "") for row in supplier_due_diligence)
    priority_items = [
        row for row in report_match_rows if row.get("match_status", "") and row.get("match_priority") != "OK"
    ]
    priority_items.sort(
        key=lambda row: (
            _priority_rank(row.get("match_priority", "")),
            -(_decimal(row.get("ttc")) or Decimal("0")),
        )
    )
    matched_count = priority_counts.get("OK", 0)
    p1_count = priority_counts.get("P1", 0)
    p2_count = priority_counts.get("P2", 0)
    review_question_count = sum(1 for row in review_rows if row.get("question_syndic"))

    lines = [
        f"# Rapport ComptaScope {year}",
        "",
        "Ce rapport explique ce que ComptaScope a rapproche localement, ce qui reste candidat, et ce qui doit etre controle en priorite.",
        "",
        "## Synthese",
        "",
        f"- Factures candidates: {len(invoices)}",
        f"- Anomalies facture: {len(invoice_anomalies)}",
        f"- Ecritures candidates: {len(entries)}",
        f"- Total TTC facture: {_money(total_ttc)} EUR",
        f"- Lignes d'etat des depenses exploitees: {len(expense_lines)}",
        f"- Rapprochements locaux suffisants: {matched_count}",
        f"- Candidats a confirmer P2: {p2_count}",
        f"- Points de rapprochement P1: {p1_count}",
        f"- Controles comptables ouverts: {len(controls)}",
        f"- Controles comptables P0: {control_severities.get('P0', 0)}",
        f"- Controles comptables P1: {control_severities.get('P1', 0)}",
        f"- Controles comptables P2: {control_severities.get('P2', 0)}",
        f"- Diligences fournisseur rattachees: {len(supplier_due_diligence)}",
        f"- Alias fournisseurs proposes: {len(alias_suggestions)}",
        f"- Alias auto-appliques: {alias_statuses.get('AUTO_APPLICABLE', 0)}",
        f"- Lignes du controle comptes guide: {len(review_rows)}",
        f"- Regroupements priorite/fournisseur/anomalie: {len(review_group_rows)}",
        f"- Questions syndic pretes a relire: {review_question_count}",
        "",
        "## Lecture rapide",
        "",
        "- `OK`: ComptaScope a une preuve locale suffisante pour rapprocher automatiquement.",
        "- `P2`: ComptaScope a trouve un candidat local plausible; une confirmation humaine suffit souvent.",
        "- `P1`: ComptaScope n'a pas assez d'indices locaux; il faut controler le grand livre, l'etat des depenses ou la piece.",
        "- Les statuts P2 ne sont pas des erreurs: ce sont des traitements locaux avances qui evitent de demander une interpretation IA.",
        "",
        "## Entrees FactureOps",
        "",
        "FactureOps est la couche amont qui detecte les factures, extrait les champs utiles et signale les anomalies de piece. ComptaScope consomme ensuite ces factures candidates pour produire les ecritures et rapprochements.",
        "",
        "| Niveau d'intensite | Factures | Role |",
        "| --- | ---: | --- |",
    ]
    level_labels = {
        "L0_STRUCTURED_SOURCE": "Source structuree ou registre facture precharge",
        "L1_NATIVE_TEXT": "Texte natif et parseurs deterministes",
        "L2_LOCAL_OCR": "OCR local ou sidecar",
        "L3_LOCAL_STRUCTURE_OR_VISUAL": "Structure/table/layout ou revue visuelle locale",
        "L4_AI_OR_ONLINE_REVIEW": "IA ou vision externe, confirmation explicite requise",
    }
    if evidence_levels:
        for level, count in evidence_levels.most_common():
            lines.append(f"| {_md_cell(level)} | {count} | {_md_cell(level_labels.get(level, 'Niveau a documenter'))} |")
    else:
        lines.append("| - | 0 | Aucune facture source |")
    lines.extend(
        [
        "",
        "## Anomalies facture",
        "",
        "| Priorite | Anomalie | Nombre | Traitement attendu |",
        "| --- | --- | ---: | --- |",
    ])
    if invoice_anomaly_types:
        for anomaly, count in invoice_anomaly_types.most_common():
            severity = next((row.get("severity", "") for row in invoice_anomalies if row.get("anomaly") == anomaly), "")
            lines.append(f"| {_md_cell(severity)} | {_md_cell(anomaly)} | {count} | Verifier la piece et completer le registre FactureOps. |")
    else:
        lines.append("| - | Aucune anomalie facture | 0 | - |")
    lines.extend(
        [
        "",
        "## Controles comptables",
        "",
        f"- Controles comptables ouverts: {len(controls)}",
        f"- Controles comptables P0: {control_severities.get('P0', 0)}",
        f"- Controles comptables P1: {control_severities.get('P1', 0)}",
        f"- Controles comptables P2: {control_severities.get('P2', 0)}",
        f"- Anomalies facture P0: {invoice_anomaly_severities.get('P0', 0)}",
        f"- Anomalies facture P1: {invoice_anomaly_severities.get('P1', 0)}",
        "",
        "## Diligences fournisseur",
        "",
        "ComptaScope ne relance pas une enquete fournisseur lorsqu'une diligence recente existe deja. Il rattache les factures marquees `DILIGENCE_REQUISE` au plan `DIL-DD-*`, aux worklists et aux resultats deja produits, puis limite les suites aux pieces manquantes ou aux recoupements prudents.",
        "",
        f"- Lignes de diligence facture: {len(supplier_due_diligence)}",
        f"- Deja couvertes par un resultat recent a recouper: {supplier_due_statuses.get('COUVERT_RECENT_A_RECOUPER', 0)}",
        f"- Deja dans une worklist existante: {supplier_due_statuses.get('DANS_PLAN_EXISTANT_A_COMPLETER', 0)}",
        f"- A traiter selon la methodologie existante: {supplier_due_statuses.get('A_TRAITER_METHODO_EXISTANTE', 0)}",
        "",
        "| Statut | Fournisseur | Facture | TTC | Diligences | Couverture existante | Action |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ])
    if supplier_due_diligence:
        for row in supplier_due_diligence[:20]:
            coverage_refs = row.get("existing_result_refs") or row.get("existing_worklist_refs") or row.get("method_sources")
            lines.append(
                " | ".join(
                    [
                        "",
                        _md_cell(row.get("coverage_status", "")),
                        _md_cell(row.get("fournisseur", "")),
                        _md_cell(row.get("numero_facture", "")),
                        _md_cell(row.get("ttc", "")),
                        _md_cell(row.get("diligence_liee", "")),
                        _md_cell(coverage_refs),
                        _md_cell(row.get("next_action", "")),
                        "",
                    ]
                )
            )
    else:
        lines.append("| - | - | - | 0.00 | - | Aucune facture marquee diligence | - |")
    lines.extend([
        "",
        "## Etat des rapprochements facture / etat des depenses",
        "",
        "| Statut | Libelle clair | Priorite | Nombre | Ce que cela veut dire | Traitement local applique | Confirmation attendue |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ])
    ordered_statuses = sorted(
        match_statuses.items(),
        key=lambda item: (_priority_rank(_status_priority(item[0])), -item[1], item[0]),
    )
    for status, count in ordered_statuses:
        meta = _status_meta(status)
        lines.append(
            " | ".join(
                [
                    "",
                    _md_cell(status),
                    _md_cell(meta.get("label", status)),
                    _md_cell(meta.get("priority", "")),
                    str(count),
                    _md_cell(meta.get("meaning", "")),
                    _md_cell(meta.get("local_treatment", "")),
                    _md_cell(meta.get("human_check", "")),
                    "",
                ]
            )
        )
    lines.extend(
        [
        "",
        "## Traitements locaux appliques",
        "",
        "ComptaScope applique ces traitements dans l'ordre, sans interpretation externe:",
        "",
        "1. reference de facture dans l'etat des depenses ;",
        "2. montant TTC exact avec fournisseur reconnu ;",
        "3. montant TTC exact avec alias fournisseur configure ou deduit ;",
        "4. montant TTC exact avec nom fournisseur tres similaire ;",
        "5. montant TTC exact avec famille comptable compatible ;",
        "6. division d'une facture en plusieurs lignes egales ;",
        "7. somme de plusieurs lignes vers une facture ;",
        "8. regroupement de plusieurs factures vers une ligne ;",
        "9. qualification des cas restants en candidats P2 ou non-rapproches P1.",
        "",
        "Un `NON_RAPPROCHE` ne veut donc pas dire que la facture est absente de la comptabilite. Cela veut dire qu'aucun traitement local n'a produit de preuve suffisante.",
        "",
        "## Causes a traiter par ordre de priorite",
        "",
        "| Priorite | Cause locale | Nombre | Action type |",
        "| --- | --- | ---: | --- |",
    ])
    open_statuses = [
        (status, count)
        for status, count in ordered_statuses
        if _status_priority(status) != "OK"
    ]
    if open_statuses:
        for status, count in open_statuses:
            meta = _status_meta(status)
            lines.append(
                f"| {_md_cell(meta.get('priority', ''))} | {_md_cell(meta.get('label', status))} | {count} | {_md_cell(meta.get('human_check', ''))} |"
            )
    else:
        lines.append("| - | Aucune cause ouverte | 0 | - |")
    lines.extend([
        "",
        "## Fournisseurs a prioriser",
        "",
        "| Fournisseur | Points ouverts | Total TTC ouvert | Priorite de lecture |",
        "| --- | ---: | ---: | --- |",
    ])
    if supplier_open_counts:
        supplier_rows = sorted(
            supplier_open_counts.items(),
            key=lambda item: (
                0 if any(row.get("fournisseur") == item[0] and row.get("match_priority") == "P1" for row in report_match_rows) else 1,
                -(supplier_open_totals.get(item[0], Decimal("0"))),
                item[0],
            ),
        )
        for supplier, count in supplier_rows[:15]:
            total = supplier_open_totals.get(supplier, Decimal("0"))
            priority = "P1 d'abord" if any(row.get("fournisseur") == supplier and row.get("match_priority") == "P1" for row in report_match_rows) else "P2 a confirmer"
            lines.append(f"| {_md_cell(supplier)} | {count} | {_money(total)} | {priority} |")
    else:
        lines.append("| - | 0 | 0.00 | Aucun point ouvert |")
    lines.extend(
        [
            "",
            "## Regroupement priorite / fournisseur / anomalie",
            "",
            "| Priorite | Fournisseur | Anomalie facture | Statut | Factures | Total TTC | Questions | Action type | Exemples |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    if review_group_rows:
        for row in review_group_rows[:20]:
            lines.append(
                " | ".join(
                    [
                        "",
                        _md_cell(row.get("priorite", "")),
                        _md_cell(row.get("fournisseur", "")),
                        _md_cell(row.get("anomalie_facture", "")),
                        _md_cell(row.get("libelle_statut") or row.get("statut_rapprochement", "")),
                        _md_cell(row.get("factures", "")),
                        _md_cell(row.get("total_ttc", "")),
                        _md_cell(row.get("questions_syndic", "")),
                        _md_cell(row.get("action_type", "")),
                        _md_cell(row.get("exemples_factures", "")),
                        "",
                    ]
                )
            )
    else:
        lines.append("| - | - | - | - | 0 | 0.00 | 0 | - | - |")
    lines.extend(
        [
            "",
            "## Controle comptes guide",
            "",
            "| Priorite | Fournisseur | Facture | TTC | Statut | Ligne candidate | Action suivante |",
            "| --- | --- | --- | ---: | --- | --- | --- |",
        ]
    )
    if review_rows:
        for row in review_rows[:20]:
            lines.append(
                " | ".join(
                    [
                        "",
                        _md_cell(row.get("priorite", "")),
                        _md_cell(row.get("fournisseur", "")),
                        _md_cell(row.get("numero_facture") or row.get("doc_id", "")),
                        _md_cell(row.get("ttc", "")),
                        _md_cell(row.get("libelle_statut") or row.get("statut_rapprochement", "")),
                        _md_cell(row.get("libelle_depense") or row.get("ligne_depense_candidate", "")),
                        _md_cell(row.get("prochaine_action", "")),
                        "",
                    ]
                )
            )
    else:
        lines.append("| - | - | - | 0.00 | Aucune facture guidee | - | - |")
    question_rows = [row for row in review_rows if row.get("question_syndic")]
    lines.extend(
        [
            "",
            "## Questions syndic copiables",
            "",
            "| Priorite | Fournisseur | Facture | Question |",
            "| --- | --- | --- | --- |",
        ]
    )
    if question_rows:
        for row in question_rows[:10]:
            lines.append(
                " | ".join(
                    [
                        "",
                        _md_cell(row.get("priorite", "")),
                        _md_cell(row.get("fournisseur", "")),
                        _md_cell(row.get("numero_facture") or row.get("doc_id", "")),
                        _md_cell(row.get("question_syndic", "")),
                        "",
                    ]
                )
            )
    else:
        lines.append("| - | - | - | Aucune question prioritaire a relire |")
    lines.extend([
        "",
        "## Alias fournisseurs deduits",
        "",
        "| Statut | Fournisseur | Alias propose | Preuves | Total TTC | Exemple |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ])
    if alias_suggestions:
        for row in alias_suggestions[:15]:
            lines.append(
                " | ".join(
                    [
                        "",
                        _md_cell(row.get("suggestion_status", "")),
                        _md_cell(row.get("supplier", "")),
                        _md_cell(row.get("suggested_alias", "")),
                        _md_cell(row.get("evidence_count", "")),
                        _md_cell(row.get("total_ttc", "")),
                        _md_cell(row.get("example_statement_label", "")),
                        "",
                    ]
                )
            )
    else:
        lines.append("| - | - | - | 0 | 0.00 | Aucun alias deduit |")
    lines.extend(
        [
            "",
            "## Exemples prioritaires a expliquer",
            "",
            "| Priorite | Statut | Libelle clair | Fournisseur | Facture | TTC | Cause locale | Action demandee |",
            "| --- | --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    if priority_items:
        for row in priority_items[:15]:
            meta = _status_meta(row.get("match_status", ""))
            lines.append(
                " | ".join(
                    [
                        "",
                        _md_cell(row.get("match_priority", "")),
                        _md_cell(row.get("match_status", "")),
                        _md_cell(row.get("status_label", meta.get("label", ""))),
                        _md_cell(row.get("fournisseur", "")),
                        _md_cell(row.get("numero_facture", "")),
                        _md_cell(row.get("ttc", "")),
                        _md_cell(row.get("match_reason", "")),
                        _md_cell(row.get("next_action", "")),
                        "",
                    ]
                )
            )
    else:
        lines.append("| - | - | - | - | - | - | Aucun point prioritaire | - |")
    lines.extend(
        [
            "",
            "## Prochaines actions automatisees",
            "",
            "- Completer les alias fournisseurs locaux lorsque le montant existe mais le libelle differe.",
            "- Departager les montants ambigus par reference, date, compte ou cle de repartition.",
            "- Controler les ventilations multi-lignes avant de les traiter comme rapprochements forts.",
            "- Comparer les blocages P1 restants avec le grand livre et les pieces manquantes.",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def _write_duckdb(path: Path, tables: dict[str, tuple[list[str], list[dict[str, str]]]]) -> bool:
    try:
        import duckdb
    except ImportError:
        return False

    def identifier(value: str) -> str:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError(f"Unsafe DuckDB identifier: {value}")
        return f'"{value}"'

    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    try:
        for table_name, (fields, rows) in tables.items():
            table = identifier(table_name)
            columns = ", ".join(f"{identifier(field)} VARCHAR" for field in fields)
            con.execute(f"DROP TABLE IF EXISTS {table}")  # nosec B608
            con.execute(f"CREATE TABLE {table} ({columns})")  # nosec B608
            if rows:
                placeholders = ", ".join("?" for _ in fields)
                con.executemany(
                    f"INSERT INTO {table} VALUES ({placeholders})",  # nosec B608
                    [[row.get(field, "") for field in fields] for row in rows],
                )
    finally:
        con.close()
    return True
