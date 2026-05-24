from __future__ import annotations

from ._runtime import *

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
