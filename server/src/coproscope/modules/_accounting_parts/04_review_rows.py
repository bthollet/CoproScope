from __future__ import annotations



def _read_text(path: Path) -> tuple[str, str]:
    if path.suffix.lower() in {".txt", ".md", ".csv"}:
        return path.read_text(encoding="utf-8-sig", errors="ignore"), "text"
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text, "pypdf"
        except Exception:  # noqa: BLE001
            return "", "pdf_unread"
    return "", "unsupported"


def _candidate_source_rows(instance: InstanceConfig) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    documents_path = instance.register("documents")
    if documents_path.exists():
        _, rows = read_csv(documents_path)

    raw_root = instance.root("raw")
    known_paths = {
        str(_resolve_source_path(instance, row) or "").lower()
        for row in rows
        if row.get("original_path") or row.get("source_path") or row.get("chemin_piece")
    }
    for index, path in enumerate(sorted(raw_root.rglob("*"))):
        if not path.is_file():
            continue
        if str(path.resolve()).lower() in known_paths:
            continue
        rows.append(
            {
                "doc_id": f"DOC-SCAN-{index + 1:04d}",
                "sha256": sha256_file(path),
                "original_path": str(path),
                "file_name": path.name,
                "document_type": "",
                "suspected_date": "",
            }
        )
    return rows


def _resolve_source_path(instance: InstanceConfig, row: dict[str, str]) -> Path | None:
    value = row.get("original_path") or row.get("source_path") or row.get("chemin_piece")
    if not value:
        return None
    path = Path(value)
    if path.is_absolute() and path.exists():
        return path
    for base in [instance.instance_root, instance.root("raw"), instance.root("workspace")]:
        candidate = (base / value).resolve()
        if candidate.exists():
            return candidate
    return None


def _looks_like_invoice(row: dict[str, str], path: Path | None, text: str, year: int) -> bool:
    haystack = " ".join(
        [
            row.get("file_name", ""),
            row.get("document_type", ""),
            row.get("suspected_date", ""),
            path.name if path else "",
            text[:2000],
        ]
    ).lower()
    if str(year) not in haystack:
        return False
    return any(token in haystack for token in ["facture", "invoice", "avoir", "note d'honoraires", "total ttc"])


def _account_for_invoice(text: str, supplier: str) -> tuple[str, str]:
    haystack = f"{supplier}\n{text}".lower()
    rules = [
        ("622000", "honoraires_syndic", ["syndic", "honoraire", "gestion"]),
        ("615000", "entretien_maintenance", ["entretien", "maintenance", "nettoyage", "ascenseur", "jardin"]),
        ("606100", "energie_eau", ["eau", "electric", "energie", "engie", "gaz"]),
        ("616000", "assurance", ["assurance", "multirisque"]),
        ("671000", "charges_exceptionnelles", ["sinistre", "contentieux", "expertise"]),
    ]
    for account, family, needles in rules:
        if any(needle in haystack for needle in needles):
            return account, family
    return "615000", "charges_courantes_a_confirmer"


def _amount(value: str) -> Decimal | None:
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return None


def _status(anomalies: Iterable[str], confidence: str) -> str:
    values = [value for value in anomalies if value]
    if not values and confidence in {"high", "medium"}:
        return "PROBABLE"
    if any(value in values for value in ["MONTANT_TTC_ABSENT", "DATE_FACTURE_ABSENTE", "FOURNISSEUR_ABSENT"]):
        return "A_CONTROLER"
    return "INCERTAIN"


def _controls_for_invoice(row: dict[str, str], year: int) -> list[dict[str, str]]:
    controls: list[dict[str, str]] = []
    anomalies = [item for item in row.get("anomalies", "").split("|") if item]
    severities = {
        "FOURNISSEUR_ABSENT": "P0",
        "NUMERO_FACTURE_ABSENT": "P0",
        "DATE_FACTURE_ABSENTE": "P0",
        "MONTANT_TTC_ABSENT": "P0",
        "SIREN_SIRET_ABSENT": "P1",
    }
    for anomaly in anomalies:
        controls.append(
            {
                "control_id": f"CTRL-{year}-{row['doc_id']}-{anomaly}",
                "exercice": str(year),
                "severity": severities.get(anomaly, "P1"),
                "control": anomaly,
                "status": "A_TRAITER",
                "doc_id": row["doc_id"],
                "evidence": row.get("source_path", ""),
                "action": "Verifier la piece et completer la donnee manquante.",
            }
        )
    return controls


def _entry_for_invoice(row: dict[str, str], year: int, entry_index: int) -> dict[str, str] | None:
    amount = _amount(row.get("ttc", ""))
    if amount is None:
        return None
    return {
        "entry_id": f"REC-{year}-{entry_index:04d}",
        "exercice": str(year),
        "date": row.get("date_facture", ""),
        "journal": "ACHATS_RECONSTITUES",
        "compte_debit": row.get("compte_propose", "") or "615000",
        "compte_credit": "401000",
        "debit": f"{amount:.2f}",
        "credit": f"{amount:.2f}",
        "fournisseur": row.get("fournisseur", ""),
        "numero_facture": row.get("numero_facture", ""),
        "piece_doc_id": row.get("doc_id", ""),
        "source_path": row.get("source_path", ""),
        "statut": row.get("statut_controle", ""),
        "justification": "Ecriture candidate reconstruite depuis facture; validation humaine requise.",
    }


def _controls_for_expense_match(row: dict[str, str], year: int) -> list[dict[str, str]]:
    status = row.get("match_status", "")
    priority = row.get("match_priority") or _status_priority(status)
    if priority == "OK":
        return []
    severity = priority if priority in {"P0", "P1", "P2"} else "P2"
    control = "FACTURE_NON_RAPPROCHEE_ETAT_DEPENSES" if status == "NON_RAPPROCHE" else "RAPPROCHEMENT_CANDIDAT_A_CONFIRMER"
    return [
        {
            "control_id": f"CTRL-{year}-{row.get('doc_id', '')}-{control}",
            "exercice": str(year),
            "severity": severity,
            "control": control,
            "status": "A_TRAITER",
            "doc_id": row.get("doc_id", ""),
            "evidence": row.get("match_reason", ""),
            "action": row.get("next_action", ""),
        }
    ]


def _control_for_unmatched_review_row(row: dict[str, str], year: int) -> dict[str, str] | None:
    priority = row.get("priorite", "")
    if priority == "OK":
        return None
    status = row.get("statut_rapprochement", "")
    control = "ETAT_DEPENSES_A_FOURNIR" if status == "SANS_ETAT_DEPENSES" else "RAPPROCHEMENT_COMPTES_A_COMPLETER"
    return {
        "control_id": f"CTRL-{year}-{row.get('doc_id', '')}-{control}",
        "exercice": str(year),
        "severity": priority if priority in {"P0", "P1", "P2"} else "P2",
        "control": control,
        "status": "A_TRAITER",
        "doc_id": row.get("doc_id", ""),
        "evidence": row.get("motif", ""),
        "action": row.get("prochaine_action", ""),
    }


def _invoice_anomalies_by_doc(invoice_anomalies: list[dict[str, str]]) -> dict[str, str]:
    grouped: dict[str, list[str]] = {}
    for row in invoice_anomalies:
        doc_id = row.get("doc_id", "")
        if not doc_id:
            continue
        severity = row.get("severity", "")
        anomaly = row.get("anomaly", "")
        if not anomaly:
            continue
        grouped.setdefault(doc_id, []).append(f"{severity}:{anomaly}" if severity else anomaly)
    return {doc_id: " | ".join(dict.fromkeys(values)) for doc_id, values in grouped.items()}


def _default_review_match(invoice: dict[str, str]) -> dict[str, str]:
    status = "SANS_ETAT_DEPENSES"
    meta = _status_meta(status)
    return {
        "doc_id": invoice.get("doc_id", ""),
        "numero_facture": invoice.get("numero_facture", ""),
        "fournisseur": invoice.get("fournisseur", ""),
        "ttc": invoice.get("ttc", ""),
        "match_status": status,
        "match_confidence": "A_CONTROLER",
        "match_priority": meta.get("priority", "P2"),
        "status_label": meta.get("label", status),
        "statement_line_id": "",
        "statement_reference": "",
        "statement_label": "",
        "statement_amount": "",
        "candidate_count": "0",
        "match_method": "missing_expense_statement",
        "match_reason": meta.get("meaning", ""),
        "next_action": meta.get("human_check", ""),
    }


def _syndic_question_for_review(row: dict[str, str], year: int) -> str:
    if row.get("priorite") == "OK":
        return ""
    invoice_ref = row.get("numero_facture") or row.get("doc_id") or "sans reference"
    supplier = row.get("fournisseur") or "fournisseur a identifier"
    amount = row.get("ttc") or "montant non renseigne"
    status = row.get("statut_rapprochement", "")
    statement = row.get("libelle_depense") or row.get("ligne_depense_candidate")
    if status == "SANS_ETAT_DEPENSES":
        return (
            f"Pouvez-vous transmettre l'etat des depenses ou la ligne de grand livre {year} "
            f"permettant de rapprocher la facture {invoice_ref} de {supplier} ({amount} EUR) ?"
        )
    if row.get("priorite") == "P1":
        return (
            f"Pouvez-vous nous indiquer la ligne de grand livre, d'etat des depenses ou la piece "
            f"qui permet de rapprocher la facture {invoice_ref} de {supplier} ({amount} EUR) ? "
            f"Constat local: {row.get('motif', '')}"
        )
    if statement:
        return (
            f"Pouvez-vous confirmer que la facture {invoice_ref} de {supplier} ({amount} EUR) "
            f"correspond bien a la ligne candidate `{statement}` ? "
            f"Constat local: {row.get('motif', '')}"
        )
    return (
        f"Pouvez-vous confirmer le traitement comptable attendu pour la facture {invoice_ref} "
        f"de {supplier} ({amount} EUR) ? Constat local: {row.get('motif', '')}"
    )


def _copyable_question_block(row: dict[str, str], year: int) -> str:
    question = row.get("question_syndic", "")
    if not question:
        return ""
    invoice_ref = row.get("numero_facture") or row.get("doc_id") or "sans reference"
    supplier = row.get("fournisseur") or "fournisseur a identifier"
    return "\n".join(
        [
            f"Objet: Controle comptes {year} - {supplier} - {invoice_ref}",
            "",
            "Bonjour,",
            "",
            question,
            "",
            f"Priorite CoproScope: {row.get('priorite', '')}. Action attendue: {row.get('prochaine_action', '')}",
            "",
            "Cordialement,",
        ]
    )


def _build_comptascope_review_rows(
    *,
    year: int,
    invoices: list[dict[str, str]],
    entries: list[dict[str, str]],
    invoice_anomalies: list[dict[str, str]],
    matches: list[dict[str, str]],
) -> list[dict[str, str]]:
    entries_by_doc = {row.get("piece_doc_id", ""): row for row in entries}
    matches_by_doc = {row.get("doc_id", ""): row for row in matches}
    anomalies_by_doc = _invoice_anomalies_by_doc(invoice_anomalies)
    rows: list[dict[str, str]] = []
    for index, invoice in enumerate(invoices, start=1):
        doc_id = invoice.get("doc_id", "")
        match = matches_by_doc.get(doc_id) or _default_review_match(invoice)
        status = match.get("match_status", "")
        meta = _status_meta(status)
        priority = match.get("match_priority") or meta.get("priority", "P2")
        entry = entries_by_doc.get(doc_id, {})
        row = {
            "review_id": f"REV-{year}-{index:04d}",
            "exercice": str(year),
            "priorite": priority,
            "fournisseur": invoice.get("fournisseur", ""),
            "numero_facture": invoice.get("numero_facture", ""),
            "doc_id": doc_id,
            "date_facture": invoice.get("date_facture", ""),
            "ttc": invoice.get("ttc", ""),
            "niveau_preuve": invoice.get("evidence_level", ""),
            "anomalies_facture": anomalies_by_doc.get(doc_id, invoice.get("anomalies", "")),
            "statut_rapprochement": status,
            "libelle_statut": match.get("status_label", meta.get("label", status)),
            "confiance": match.get("match_confidence", ""),
            "ligne_depense_candidate": match.get("statement_line_id", ""),
            "reference_depense": match.get("statement_reference", ""),
            "libelle_depense": match.get("statement_label", ""),
            "montant_depense": match.get("statement_amount", ""),
            "candidate_count": match.get("candidate_count", ""),
            "ecriture_candidate": entry.get("entry_id", ""),
            "compte_candidate": entry.get("compte_debit", ""),
            "motif": match.get("match_reason", ""),
            "prochaine_action": match.get("next_action", ""),
            "question_syndic": "",
            "bloc_copiable": "",
        }
        row["question_syndic"] = _syndic_question_for_review(row, year)
        row["bloc_copiable"] = _copyable_question_block(row, year)
        rows.append(row)
    rows.sort(
        key=lambda row: (
            _priority_rank(row.get("priorite", "")),
            row.get("fournisseur", ""),
            -(_decimal(row.get("ttc")) or Decimal("0")),
            row.get("numero_facture", ""),
        )
    )
    return rows


def _review_anomaly_groups(row: dict[str, str]) -> list[str]:
    raw = row.get("anomalies_facture", "")
    values: list[str] = []
    for item in raw.split("|"):
        item = item.strip()
        if not item:
            continue
        values.append(item.split(":", 1)[-1].strip() or item)
    return list(dict.fromkeys(values)) or ["SANS_ANOMALIE_FACTURE"]


def _build_comptascope_review_group_rows(
    *,
    year: int,
    review_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    groups: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in review_rows:
        priority = row.get("priorite", "") or "P2"
        supplier = row.get("fournisseur", "") or "FOURNISSEUR_A_IDENTIFIER"
        status = row.get("statut_rapprochement", "") or "STATUT_NON_RENSEIGNE"
        for anomaly in _review_anomaly_groups(row):
            key = (priority, supplier, anomaly, status)
            group = groups.setdefault(
                key,
                {
                    "total": Decimal("0"),
                    "factures": 0,
                    "questions": 0,
                    "actions": Counter(),
                    "examples": [],
                    "status_label": row.get("libelle_statut", ""),
                },
            )
            group["factures"] += 1
            group["total"] += _decimal(row.get("ttc")) or Decimal("0")
            if row.get("question_syndic"):
                group["questions"] += 1
            action = row.get("prochaine_action", "")
            if action:
                group["actions"][action] += 1
            example = row.get("numero_facture") or row.get("doc_id", "")
            if example and example not in group["examples"]:
                group["examples"].append(example)
            if row.get("libelle_statut"):
                group["status_label"] = row.get("libelle_statut", "")

    rows: list[dict[str, str]] = []
    sorted_groups = sorted(
        groups.items(),
        key=lambda item: (
            _priority_rank(item[0][0]),
            item[0][1],
            -(item[1]["total"]),
            item[0][2],
            item[0][3],
        ),
    )
    for index, ((priority, supplier, anomaly, status), group) in enumerate(sorted_groups, start=1):
        actions = group["actions"].most_common(1)
        rows.append(
            {
                "group_id": f"GRP-{year}-{index:04d}",
                "exercice": str(year),
                "priorite": priority,
                "fournisseur": supplier,
                "anomalie_facture": anomaly,
                "statut_rapprochement": status,
                "libelle_statut": group["status_label"],
                "factures": str(group["factures"]),
                "total_ttc": _money(group["total"]),
                "questions_syndic": str(group["questions"]),
                "action_type": actions[0][0] if actions else "",
                "exemples_factures": "; ".join(group["examples"][:3]),
            }
        )
    return rows


def _write_syndic_questions(path: Path, *, year: int, review_rows: list[dict[str, str]]) -> None:
    open_rows = [row for row in review_rows if row.get("question_syndic")]
    lines = [
        f"# Questions syndic ComptaScope {year}",
        "",
        "Questions generiques issues du controle guide ComptaScope. Elles doivent etre relues avant envoi et ne valent pas validation comptable.",
        "",
    ]
    if not open_rows:
        lines.extend(["Aucune question syndic prioritaire: les factures analysees sont rapprochees localement.", ""])
        write_text(path, "\n".join(lines))
        return

    current_priority = ""
    for row in open_rows:
        priority = row.get("priorite", "")
        if priority != current_priority:
            current_priority = priority
            lines.extend([f"## Priorite {priority}", ""])
        lines.extend(
            [
                f"### {row.get('fournisseur') or 'Fournisseur a identifier'} - {row.get('numero_facture') or row.get('doc_id')}",
                "",
                f"- Montant TTC: {row.get('ttc') or '-'} EUR",
                f"- Statut local: {row.get('statut_rapprochement')} - {row.get('libelle_statut')}",
                f"- Motif: {row.get('motif') or '-'}",
                "",
                "```text",
                row.get("bloc_copiable", ""),
                "```",
                "",
            ]
        )
    write_text(path, "\n".join(lines))


def _md_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").replace("|", "/").strip()
