from __future__ import annotations



def _candidate_row(
    invoice: dict[str, str],
    status: str,
    confidence: str,
    line: dict[str, str] | None,
    candidate_count: int,
    method: str,
    reason: str,
    action: str,
) -> dict[str, str]:
    meta = _status_meta(status)
    return {
        "doc_id": invoice.get("doc_id", ""),
        "numero_facture": invoice.get("numero_facture", ""),
        "fournisseur": invoice.get("fournisseur", ""),
        "ttc": invoice.get("ttc", ""),
        "match_status": status,
        "match_confidence": confidence,
        "match_priority": meta.get("priority", "P2"),
        "status_label": meta.get("label", status),
        "statement_line_id": line.get("statement_line_id", "") if line else "",
        "statement_reference": line.get("reference", "") if line else "",
        "statement_label": line.get("label", "") if line else "",
        "statement_amount": line.get("amount", "") if line else "",
        "candidate_count": str(candidate_count),
        "match_method": method,
        "match_reason": reason,
        "next_action": action,
    }


def _find_split_match(
    invoice_amount: Decimal,
    candidates: list[dict[str, str]],
    max_lines: int = 4,
) -> tuple[list[dict[str, str]], int]:
    matches: list[list[dict[str, str]]] = []
    limited = candidates[:30]
    for size in range(2, min(max_lines, len(limited)) + 1):
        for group in combinations(limited, size):
            total = sum((_decimal(line.get("amount")) or Decimal("0")) for line in group)
            if total == invoice_amount:
                matches.append(list(group))
                if len(matches) > 1:
                    return [], len(matches)
    if len(matches) == 1:
        return matches[0], 1
    return [], len(matches)


def _find_equal_division(
    invoice_amount: Decimal,
    candidates: list[dict[str, str]],
    max_lines: int = 24,
) -> tuple[list[dict[str, str]], int]:
    by_amount: dict[Decimal, list[dict[str, str]]] = {}
    for line in candidates:
        amount = _decimal(line.get("amount"))
        if amount is None or amount <= 0 or amount >= invoice_amount:
            continue
        by_amount.setdefault(amount, []).append(line)
    matches: list[list[dict[str, str]]] = []
    for amount, lines in by_amount.items():
        if len(lines) > max_lines:
            continue
        ratio = invoice_amount / amount
        if ratio == ratio.to_integral_value() and ratio >= 2:
            needed = int(ratio)
            if len(lines) == needed:
                matches.append(lines)
            elif len(lines) > needed:
                return [], 2
    if len(matches) == 1:
        return matches[0], 1
    return [], len(matches)


def suggest_supplier_aliases(
    invoices: list[dict[str, str]],
    expense_lines: list[dict[str, str]],
    supplier_aliases: dict[str, set[str]] | None = None,
    min_auto_evidence: int = 2,
) -> list[dict[str, str]]:
    """Propose supplier aliases from repeated amount/account-family evidence."""

    supplier_aliases = supplier_aliases or {}
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for invoice in invoices:
        amount = _decimal(invoice.get("ttc"))
        if amount is None:
            continue
        supplier = invoice.get("fournisseur", "")
        supplier_key = _normal(supplier)
        if not supplier_key:
            continue
        for line in expense_lines:
            line_amount = _decimal(line.get("amount"))
            if line_amount != amount or not _family_matches(invoice, line):
                continue
            if _supplier_match_kind(invoice, line, supplier_aliases):
                continue
            alias, alias_source = _statement_alias_candidate_with_source(line)
            alias_key = _normal(alias)
            if not alias_key or alias_key == supplier_key or alias_key in supplier_aliases.get(supplier_key, set()):
                continue
            key = (supplier, alias)
            bucket = grouped.setdefault(
                key,
                {
                    "supplier": supplier,
                    "suggested_alias": alias,
                    "count": 0,
                    "total": Decimal("0"),
                    "example_doc_id": invoice.get("doc_id", ""),
                    "example_statement_line_id": line.get("statement_line_id", ""),
                    "example_statement_label": line.get("label", ""),
                    "alias_source": alias_source,
                },
            )
            bucket["count"] += 1
            bucket["total"] += amount

    suggestions: list[dict[str, str]] = []
    for bucket in grouped.values():
        count = int(bucket["count"])
        status = "AUTO_APPLICABLE" if count >= min_auto_evidence and bucket.get("alias_source") == "supplier_hint" else "A_CONTROLER"
        suggestions.append(
            {
                "supplier": bucket["supplier"],
                "suggested_alias": bucket["suggested_alias"],
                "suggestion_status": status,
                "evidence_count": str(count),
                "total_ttc": _money(bucket["total"]),
                "example_doc_id": bucket["example_doc_id"],
                "example_statement_line_id": bucket["example_statement_line_id"],
                "example_statement_label": bucket["example_statement_label"],
                "reason": "Montants exacts et famille comptable compatible avec un libelle fournisseur different.",
                "next_action": "Auto-applicable si le motif est repete; sinon confirmer puis ajouter l'alias dans la configuration locale.",
            }
        )
    suggestions.sort(
        key=lambda row: (
            row.get("suggestion_status") != "AUTO_APPLICABLE",
            -int(row.get("evidence_count") or "0"),
            row.get("supplier", ""),
        )
    )
    return suggestions


def supplier_aliases_from_suggestions(suggestions: list[dict[str, str]]) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {}
    for row in suggestions:
        if row.get("suggestion_status") != "AUTO_APPLICABLE":
            continue
        supplier = row.get("supplier", "")
        alias = row.get("suggested_alias", "")
        if supplier and alias:
            aliases.setdefault(_normal(supplier), set()).add(_normal(alias))
    return aliases


def _merge_supplier_aliases(*sources: dict[str, set[str]]) -> dict[str, set[str]]:
    merged: dict[str, set[str]] = {}
    for source in sources:
        for supplier, aliases in source.items():
            merged.setdefault(supplier, set()).update(aliases)
    return merged


def _grouped_invoice_candidates(
    invoices: list[dict[str, str]],
    expense_lines: list[dict[str, str]],
    supplier_aliases: dict[str, set[str]],
    current_results: list[dict[str, str]],
    max_group_size: int = 6,
) -> dict[str, dict[str, str]]:
    result_by_doc = {row.get("doc_id", ""): row for row in current_results}
    open_invoices = [
        invoice
        for invoice in invoices
        if not _is_confirmed_status(result_by_doc.get(invoice.get("doc_id", ""), {}).get("match_status", ""))
        and _decimal(invoice.get("ttc")) is not None
    ]
    updates: dict[str, dict[str, str]] = {}
    for line in expense_lines:
        line_amount = _decimal(line.get("amount"))
        if line_amount is None or line_amount <= 0:
            continue
        by_supplier: dict[str, list[dict[str, str]]] = {}
        for invoice in open_invoices:
            amount = _decimal(invoice.get("ttc"))
            if amount is None or amount >= line_amount:
                continue
            supplier_match = _supplier_match_kind(invoice, line, supplier_aliases)
            similar_name, similarity_score = _similar_supplier_evidence(invoice, line)
            if not (supplier_match or _family_matches(invoice, line) or similarity_score >= Decimal("0.70")):
                continue
            key = _normal(invoice.get("fournisseur"))
            if key:
                by_supplier.setdefault(key, []).append(invoice)
        for candidates in by_supplier.values():
            if len(candidates) < 2 or len(candidates) > 16:
                continue
            matches: list[tuple[dict[str, str], ...]] = []
            for size in range(2, min(max_group_size, len(candidates)) + 1):
                for group in combinations(candidates, size):
                    total = sum((_decimal(invoice.get("ttc")) or Decimal("0")) for invoice in group)
                    if total == line_amount:
                        matches.append(group)
                        if len(matches) > 1:
                            break
                if len(matches) > 1:
                    break
            if len(matches) != 1:
                continue
            group = matches[0]
            for invoice in group:
                updates[invoice.get("doc_id", "")] = _candidate_row(
                    invoice,
                    "CANDIDAT_REGROUPEMENT_FACTURES",
                    "A_CONFIRMATION_HUMAINE",
                    line,
                    len(group),
                    "invoice_group_sum",
                    "Plusieurs factures du meme fournisseur totalisent exactement une ligne de depense.",
                    "Confirmer que la ligne comptable regroupe bien ces factures avant conclusion.",
                )
    return updates


def reconcile_invoice_expenses(
    invoices: list[dict[str, str]],
    expense_lines: list[dict[str, str]],
    supplier_aliases: dict[str, set[str]] | None = None,
) -> list[dict[str, str]]:
    """Match invoices with expense-statement lines and explain every miss.

    The engine intentionally separates confirmed-looking deterministic matches
    from candidates. A non-match is an automation limit, not proof that the
    invoice is absent from the official accounts.
    """

    supplier_aliases = supplier_aliases or {}
    duplicate_invoice_counts = Counter(_invoice_duplicate_key(invoice) for invoice in invoices)
    results: list[dict[str, str]] = []

    for invoice in invoices:
        amount = _decimal(invoice.get("ttc"))
        keys = invoice_keys(
            invoice.get("numero_facture", ""),
            "",
            invoice.get("file_name") or invoice.get("aliases") or "",
        )
        line_infos: list[dict[str, Any]] = []
        for line in expense_lines:
            line_amount = _decimal(line.get("amount"))
            line_compact = _compact(_line_text(line))
            ref_match = any(key and key in line_compact for key in keys)
            supplier_match = _supplier_match_kind(invoice, line, supplier_aliases)
            family_match = _family_matches(invoice, line)
            amount_match = amount is not None and line_amount == amount
            similar_name, similarity_score = _similar_supplier_evidence(invoice, line)
            line_infos.append(
                {
                    "line": line,
                    "amount": line_amount,
                    "ref_match": ref_match,
                    "supplier_match": supplier_match,
                    "family_match": family_match,
                    "amount_match": amount_match,
                    "similar_name": similar_name,
                    "similarity_score": similarity_score,
                }
            )

        reference_matches = [
            info
            for info in line_infos
            if info["ref_match"] and (amount is None or info["amount"] is None or info["amount"] == amount)
        ]
        if len(reference_matches) == 1:
            results.append(
                _candidate_row(
                    invoice,
                    "MATCH_REFERENCE",
                    "PROBABLE_FORT",
                    reference_matches[0]["line"],
                    1,
                    "invoice_reference",
                    "Le numero de facture ou une reference equivalente apparait dans l'etat des depenses.",
                    "Verifier seulement si le libelle ou le montant semble incoherent.",
                )
            )
            continue
        if len(reference_matches) > 1:
            results.append(
                _candidate_row(
                    invoice,
                    "CANDIDAT_REFERENCE_AMBIGUE",
                    "A_CONTROLER",
                    reference_matches[0]["line"],
                    len(reference_matches),
                    "invoice_reference",
                    "La reference de facture apparait dans plusieurs lignes de depenses.",
                    "Choisir la ligne correcte ou accepter une ventilation multi-lignes.",
                )
            )
            continue

        exact_supplier = [info for info in line_infos if info["amount_match"] and info["supplier_match"] == "supplier"]
        exact_alias = [info for info in line_infos if info["amount_match"] and info["supplier_match"] == "alias"]
        exact_family = [info for info in line_infos if info["amount_match"] and info["family_match"]]
        duplicate_key = _invoice_duplicate_key(invoice)
        repeated_invoice = duplicate_invoice_counts[duplicate_key] > 1

        if len(exact_supplier) == 1 and not repeated_invoice:
            results.append(
                _candidate_row(
                    invoice,
                    "MATCH_AMOUNT_SUPPLIER",
                    "PROBABLE_FORT",
                    exact_supplier[0]["line"],
                    1,
                    "amount_supplier",
                    "Montant TTC exact et fournisseur reconnu dans la ligne de depense.",
                    "Controler la piece si le rapprochement porte sur un poste sensible.",
                )
            )
            continue
        if len(exact_alias) == 1 and not repeated_invoice:
            results.append(
                _candidate_row(
                    invoice,
                    "MATCH_AMOUNT_ALIAS",
                    "PROBABLE_FORT",
                    exact_alias[0]["line"],
                    1,
                    "amount_supplier_alias",
                    "Montant TTC exact et alias fournisseur reconnu dans l'etat des depenses.",
                    "Conserver l'alias fournisseur dans la configuration locale.",
                )
            )
            continue
        similar_supplier = [
            info
            for info in line_infos
            if info["amount_match"] and info["family_match"] and info["similarity_score"] >= Decimal("0.70")
        ]
        if len(similar_supplier) == 1 and not repeated_invoice:
            similar_name = similar_supplier[0].get("similar_name", "")
            results.append(
                _candidate_row(
                    invoice,
                    "CANDIDAT_NOM_SIMILAIRE",
                    "A_CONFIRMATION_HUMAINE",
                    similar_supplier[0]["line"],
                    1,
                    "amount_family_name_similarity",
                    f"Montant TTC exact, famille comptable compatible, et nom proche detecte localement: {similar_name}.",
                    "Confirmer que les deux noms designent le meme fournisseur, puis ajouter l'alias si besoin.",
                )
            )
            continue
        if len(exact_family) == 1 and not repeated_invoice:
            results.append(
                _candidate_row(
                    invoice,
                    "CANDIDAT_MONTANT_FAMILLE",
                    "A_CONFIRMATION_HUMAINE",
                    exact_family[0]["line"],
                    1,
                    "amount_account_family",
                    "Montant TTC exact et compte/famille de charge compatible, mais fournisseur non reconnu litteralement.",
                    "Verifier le libelle puis ajouter un alias si le rapprochement est confirme.",
                )
            )
            continue

        ambiguous_count = len(exact_supplier) + len(exact_alias) + len(exact_family)
        if ambiguous_count > 1 or (ambiguous_count == 1 and repeated_invoice):
            line = (exact_supplier or exact_alias or exact_family)[0]["line"]
            results.append(
                _candidate_row(
                    invoice,
                    "CANDIDAT_MONTANT_AMBIGU",
                    "A_CONTROLER",
                    line,
                    max(ambiguous_count, duplicate_invoice_counts[duplicate_key]),
                    "amount_candidate",
                    "Le montant existe, mais plusieurs factures ou lignes peuvent correspondre.",
                    "Utiliser une reference de piece, une date ou une ventilation pour departager.",
                )
            )
            continue

        if amount is not None:
            split_candidates = [
                info["line"]
                for info in line_infos
                if info["amount"] is not None
                and info["amount"] < amount
                and (info["supplier_match"] or info["family_match"])
            ]
            division_match, division_count = _find_equal_division(amount, split_candidates)
            if division_count == 1 and division_match and not repeated_invoice:
                first = dict(division_match[0])
                first["statement_line_id"] = " + ".join(line.get("statement_line_id", "") for line in division_match)
                first["reference"] = " + ".join(line.get("reference", "") for line in division_match if line.get("reference"))
                first["label"] = " / ".join(line.get("label", "") for line in division_match if line.get("label"))
                first["amount"] = _money(sum((_decimal(line.get("amount")) or Decimal("0")) for line in division_match))
                results.append(
                    _candidate_row(
                        invoice,
                        "CANDIDAT_DIVISION_EGALE",
                        "A_CONFIRMATION_HUMAINE",
                        first,
                        len(division_match),
                        "equal_division",
                        "Le TTC de la facture se divise exactement en plusieurs lignes compatibles de meme montant.",
                        "Verifier la cle de repartition, le compteur, le batiment ou l'equipement avant conclusion.",
                    )
                )
                continue
            split_match, split_count = _find_split_match(amount, split_candidates)
            if split_count == 1 and split_match and not repeated_invoice:
                first = dict(split_match[0])
                first["statement_line_id"] = " + ".join(line.get("statement_line_id", "") for line in split_match)
                first["reference"] = " + ".join(line.get("reference", "") for line in split_match if line.get("reference"))
                first["label"] = " / ".join(line.get("label", "") for line in split_match if line.get("label"))
                first["amount"] = _money(sum((_decimal(line.get("amount")) or Decimal("0")) for line in split_match))
                results.append(
                    _candidate_row(
                        invoice,
                        "CANDIDAT_SOMME_MULTI_LIGNES",
                        "A_CONFIRMATION_HUMAINE",
                        first,
                        len(split_match),
                        "split_sum",
                        "Plusieurs lignes compatibles totalisent exactement le TTC de la facture.",
                        "Verifier la ventilation par cle, batiment, compteur ou equipement.",
                    )
                )
                continue
            if split_count > 1:
                results.append(
                    _candidate_row(
                        invoice,
                        "CANDIDAT_VENTILATION_AMBIGUE",
                        "A_CONTROLER",
                        split_candidates[0] if split_candidates else None,
                        split_count,
                        "split_sum",
                        "Plusieurs combinaisons de lignes peuvent reconstituer le montant de la facture.",
                        "Limiter par date, compte ou cle de repartition avant conclusion.",
                    )
                )
                continue

        amount_only = [info for info in line_infos if info["amount_match"]]
        supplier_only = [info for info in line_infos if info["supplier_match"]]
        family_only = [info for info in line_infos if info["family_match"]]
        if amount_only:
            status = "CANDIDAT_MONTANT_SANS_NOM"
            reason = "Le montant TTC existe dans l'etat des depenses, mais le fournisseur ou l'alias n'est pas reconnu."
            action = "Ajouter un alias fournisseur ou verifier que le libelle comptable vise la meme piece."
            line = amount_only[0]["line"]
            candidate_count = len(amount_only)
        elif supplier_only:
            status = "CANDIDAT_FOURNISSEUR_SANS_MONTANT"
            reason = "Le fournisseur semble present, mais aucun montant identique n'a ete trouve."
            action = "Chercher une ventilation, un regroupement, un avoir ou une regularisation."
            line = supplier_only[0]["line"]
            candidate_count = len(supplier_only)
        elif family_only:
            status = "CANDIDAT_FAMILLE_SEULE"
            reason = "La famille comptable est compatible, mais ni reference, ni montant exact, ni fournisseur reconnu ne suffisent."
            action = "Comparer les lignes du compte candidat et completer les alias/factures manquantes."
            line = family_only[0]["line"]
            candidate_count = len(family_only)
        else:
            status = "NON_RAPPROCHE"
            reason = "Aucune ligne de depense ne porte la reference, le montant exact, le fournisseur ou une famille comptable suffisante."
            action = "Verifier l'etat des depenses, l'annexe comptable, les libelles OCR et la presence de la piece."
            line = None
            candidate_count = 0
        results.append(
            _candidate_row(
                invoice,
                status,
                "A_CONTROLER",
                line,
                candidate_count,
                "no_deterministic_match",
                reason,
                action,
            )
        )

    grouped_updates = _grouped_invoice_candidates(invoices, expense_lines, supplier_aliases, results)
    if grouped_updates:
        results = [grouped_updates.get(row.get("doc_id", ""), row) for row in results]

    return results
