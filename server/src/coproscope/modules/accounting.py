from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter
from decimal import Decimal, InvalidOperation
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

from ..core.common import InstanceConfig, RunContext, now_iso, read_csv, sha256_file, write_csv, write_text
from ..extractors.invoices import DocumentExtractionEvidence, extract_generic_invoice_from_evidence
from ..extractors.invoices.reconciliation import invoice_keys, normalized_for_match, parse_amount


INVOICE_EVIDENCE_FIELDS = [
    "doc_id",
    "sha256",
    "source_path",
    "file_name",
    "exercice",
    "fournisseur",
    "siren_siret",
    "numero_facture",
    "date_facture",
    "ht",
    "tva",
    "ttc",
    "compte_propose",
    "famille_charge",
    "statut_controle",
    "confidence",
    "anomalies",
    "extraction_method",
]

ACCOUNTING_ENTRY_FIELDS = [
    "entry_id",
    "exercice",
    "date",
    "journal",
    "compte_debit",
    "compte_credit",
    "debit",
    "credit",
    "fournisseur",
    "numero_facture",
    "piece_doc_id",
    "source_path",
    "statut",
    "justification",
]

ACCOUNTING_CONTROL_FIELDS = [
    "control_id",
    "exercice",
    "severity",
    "control",
    "status",
    "doc_id",
    "evidence",
    "action",
]

EXPENSE_STATEMENT_FIELDS = [
    "statement_line_id",
    "date",
    "account",
    "account_label",
    "reference",
    "supplier_hint",
    "label",
    "amount",
    "source",
]

INVOICE_EXPENSE_MATCH_FIELDS = [
    "doc_id",
    "numero_facture",
    "fournisseur",
    "ttc",
    "match_status",
    "match_confidence",
    "statement_line_id",
    "statement_reference",
    "statement_label",
    "statement_amount",
    "candidate_count",
    "match_method",
    "match_reason",
    "next_action",
]

NON_MATCH_PRIORITY_FIELDS = [
    "doc_id",
    "fournisseur",
    "numero_facture",
    "ttc",
    "match_status",
    "match_reason",
    "next_action",
]

SUPPLIER_ALIAS_SUGGESTION_FIELDS = [
    "supplier",
    "suggested_alias",
    "suggestion_status",
    "evidence_count",
    "total_ttc",
    "example_doc_id",
    "example_statement_line_id",
    "example_statement_label",
    "reason",
    "next_action",
]


def _normal(value: str | None) -> str:
    return normalized_for_match(value or "")


def _compact(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^A-Za-z0-9]", "", text).upper()


def _decimal(value: str | None) -> Decimal | None:
    return parse_amount(value)


def _money(value: Decimal | None) -> str:
    return f"{value:.2f}" if value is not None else ""


def _comptascope_settings(instance: InstanceConfig) -> dict[str, Any]:
    settings = instance.settings().get("comptascope", {})
    return settings if isinstance(settings, dict) else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "oui", "on"}


def _configured_paths(instance: InstanceConfig, settings: dict[str, Any], *keys: str, year: int) -> list[Path]:
    paths: list[Path] = []
    for key in keys:
        for raw_value in _as_list(settings.get(key)):
            value = str(raw_value).format(year=year)
            resolved = instance.resolve_path(value)
            if resolved is not None:
                paths.append(resolved)
    return paths


def _load_supplier_aliases(instance: InstanceConfig) -> dict[str, set[str]]:
    settings = _comptascope_settings(instance)
    aliases: dict[str, set[str]] = {}
    for item in _as_list(settings.get("supplier_aliases")):
        if not isinstance(item, dict):
            continue
        supplier = str(item.get("supplier") or item.get("fournisseur") or "")
        if not supplier:
            continue
        key = _normal(supplier)
        values = aliases.setdefault(key, set())
        for alias in _as_list(item.get("aliases") or item.get("alias")):
            if str(alias).strip():
                values.add(_normal(str(alias)))
    return aliases


def _load_expense_statement_lines(instance: InstanceConfig, accounting_dir: Path, year: int) -> list[dict[str, str]]:
    settings = _comptascope_settings(instance)
    candidates = _configured_paths(
        instance,
        settings,
        "expense_statement_lines",
        "etat_depenses_lines",
        "expense_statement_csv",
        year=year,
    )
    if not candidates:
        candidates.append(accounting_dir / f"expense_statement_lines_{year}.csv")
        try:
            candidates.append(instance.root("system") / "accounting" / f"expense_statement_lines_{year}.csv")
        except KeyError:
            pass

    rows: list[dict[str, str]] = []
    seen_paths: set[Path] = set()
    seen_line_ids: set[str] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen_paths or not resolved.exists():
            continue
        seen_paths.add(resolved)
        _, loaded = read_csv(resolved)
        for index, row in enumerate(loaded, start=1):
            amount = _decimal(row.get("amount") or row.get("montant") or row.get("debit") or row.get("credit"))
            normalized = {
                "statement_line_id": row.get("statement_line_id")
                or row.get("line_id")
                or row.get("id")
                or f"DEP-{year}-{len(rows) + index:04d}",
                "date": row.get("date") or row.get("date_ecriture") or "",
                "account": row.get("account") or row.get("compte") or "",
                "account_label": row.get("account_label") or row.get("libelle_compte") or "",
                "reference": row.get("reference") or row.get("piece") or row.get("numero_piece") or "",
                "supplier_hint": row.get("supplier_hint") or row.get("fournisseur") or row.get("tiers") or "",
                "label": row.get("label") or row.get("libelle") or row.get("description") or "",
                "amount": _money(amount),
                "source": row.get("source") or str(resolved),
            }
            if normalized["statement_line_id"] in seen_line_ids:
                continue
            seen_line_ids.add(normalized["statement_line_id"])
            rows.append(normalized)
    return rows


def _load_configured_invoice_evidence(instance: InstanceConfig, year: int) -> list[dict[str, str]]:
    settings = _comptascope_settings(instance)
    candidates = _configured_paths(
        instance,
        settings,
        "invoice_evidence_csv",
        "pre_accounting_invoices",
        "pre_compta_invoices",
        year=year,
    )
    rows: list[dict[str, str]] = []
    seen_doc_ids: set[str] = set()
    for path in candidates:
        if not path.exists():
            continue
        _, loaded = read_csv(path)
        for index, row in enumerate(loaded, start=1):
            exercice = row.get("exercice") or row.get("year") or ""
            if exercice and exercice != str(year):
                continue
            source_path = row.get("source_path") or row.get("chemin_piece") or row.get("original_path") or ""
            file_name = row.get("file_name") or row.get("aliases") or (Path(source_path).name if source_path else "")
            doc_id = row.get("doc_id") or f"INV-{year}-{len(rows) + index:04d}"
            if doc_id in seen_doc_ids:
                continue
            seen_doc_ids.add(doc_id)
            anomalies = row.get("anomalies", "").replace(" | ", "|")
            confidence = row.get("confidence") or row.get("confiance") or "preloaded"
            normalized = {
                "doc_id": doc_id,
                "sha256": row.get("sha256", ""),
                "source_path": source_path,
                "file_name": file_name,
                "exercice": str(year),
                "fournisseur": row.get("fournisseur") or row.get("supplier") or "",
                "siren_siret": row.get("siren_siret") or row.get("siret") or row.get("siren") or "",
                "numero_facture": row.get("numero_facture") or row.get("invoice_number") or "",
                "date_facture": row.get("date_facture") or row.get("invoice_date") or "",
                "ht": row.get("ht") or row.get("amount_ht") or "",
                "tva": row.get("tva") or row.get("vat") or "",
                "ttc": _money(_decimal(row.get("ttc") or row.get("amount_ttc") or row.get("montant_ttc"))),
                "compte_propose": row.get("compte_propose") or row.get("account") or "",
                "famille_charge": row.get("famille_charge") or row.get("control_family") or "",
                "statut_controle": row.get("statut_controle") or _status(anomalies.split("|"), confidence),
                "confidence": confidence,
                "anomalies": anomalies,
                "extraction_method": row.get("extraction_method") or row.get("source_register") or "preloaded_csv",
            }
            rows.append(normalized)
    return rows


def _supplier_aliases_for(invoice: dict[str, str], aliases: dict[str, set[str]]) -> set[str]:
    supplier = _normal(invoice.get("fournisseur"))
    values = set(aliases.get(supplier, set()))
    if supplier:
        values.add(supplier)
    return values


def _significant_supplier_tokens(value: str) -> set[str]:
    stopwords = {
        "a",
        "au",
        "aux",
        "de",
        "des",
        "du",
        "et",
        "la",
        "le",
        "les",
        "l",
        "sa",
        "sas",
        "sarl",
        "services",
        "service",
        "societe",
    }
    return {token for token in re.split(r"[^a-z0-9]+", _normal(value)) if len(token) >= 3 and token not in stopwords}


def _line_text(line: dict[str, str]) -> str:
    return " ".join(
        [
            line.get("supplier_hint", ""),
            line.get("reference", ""),
            line.get("label", ""),
            line.get("account", ""),
            line.get("account_label", ""),
        ]
    )


def _statement_alias_candidate_with_source(line: dict[str, str]) -> tuple[str, str]:
    hint = normalize_statement_alias(line.get("supplier_hint", ""))
    if hint:
        return hint, "supplier_hint"
    label = line.get("label", "")
    if "/" in label:
        left = label.split("/", 1)[0]
        left = re.sub(r"^\s*[A-Z0-9._-]{3,24}\s+", "", left)
        alias = normalize_statement_alias(left)
        if alias:
            return alias, "label_prefix"
    return "", ""


def _statement_alias_candidate(line: dict[str, str]) -> str:
    return _statement_alias_candidate_with_source(line)[0]


def normalize_statement_alias(value: str) -> str:
    text = re.sub(r"\s+", " ", value or "").strip(" -_/")
    normalized = _normal(text)
    if not normalized:
        return ""
    weak = {
        "assur",
        "assurance",
        "avoir",
        "cb",
        "cheque",
        "const",
        "demeure",
        "dos",
        "dossier",
        "facture",
        "honoraires",
        "mise",
        "paiement",
        "prelevement",
        "rar",
        "reglement",
        "suivi",
        "vac",
        "vacation",
        "virement",
    }
    tokens = [token for token in re.split(r"[^a-z0-9]+", normalized) if token]
    if not tokens or all(token in weak or token.isdigit() for token in tokens):
        return ""
    return text


def _supplier_match_kind(invoice: dict[str, str], line: dict[str, str], aliases: dict[str, set[str]]) -> str:
    haystack = _normal(_line_text(line))
    supplier = _normal(invoice.get("fournisseur"))
    if supplier and supplier in haystack:
        return "supplier"
    supplier_tokens = _significant_supplier_tokens(invoice.get("fournisseur", ""))
    if supplier_tokens and len(supplier_tokens) <= 2 and supplier_tokens.issubset(set(re.split(r"[^a-z0-9]+", haystack))):
        return "supplier"
    for alias in _supplier_aliases_for(invoice, aliases):
        if alias and alias != supplier and alias in haystack:
            return "alias"
    return ""


def _family_matches(invoice: dict[str, str], line: dict[str, str]) -> bool:
    account = re.sub(r"\D", "", line.get("account", ""))
    proposed = re.sub(r"\D", "", invoice.get("compte_propose", ""))
    family = invoice.get("famille_charge", "")
    if account and proposed and account[:3] == proposed[:3]:
        return True
    prefixes = {
        "energie_eau": ("601", "602", "606"),
        "entretien_maintenance": ("611", "614", "615"),
        "honoraires_syndic": ("622",),
        "assurance": ("616",),
        "charges_exceptionnelles": ("671",),
    }
    return bool(account and family in prefixes and account.startswith(prefixes[family]))


def _invoice_duplicate_key(invoice: dict[str, str]) -> str:
    return f"{_normal(invoice.get('fournisseur'))}|{_money(_decimal(invoice.get('ttc')))}"


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
    return {
        "doc_id": invoice.get("doc_id", ""),
        "numero_facture": invoice.get("numero_facture", ""),
        "fournisseur": invoice.get("fournisseur", ""),
        "ttc": invoice.get("ttc", ""),
        "match_status": status,
        "match_confidence": confidence,
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
            line_infos.append(
                {
                    "line": line,
                    "amount": line_amount,
                    "ref_match": ref_match,
                    "supplier_match": supplier_match,
                    "family_match": family_match,
                    "amount_match": amount_match,
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
        if len(exact_family) == 1 and not repeated_invoice:
            results.append(
                _candidate_row(
                    invoice,
                    "MATCH_AMOUNT_ACCOUNT_FAMILY",
                    "PROBABLE",
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
                        "MATCH_SPLIT_SUM",
                        "PROBABLE",
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
                        "Limiter par date, compte ou cle de repartition avant validation.",
                    )
                )
                continue

        amount_only = [info for info in line_infos if info["amount_match"]]
        supplier_only = [info for info in line_infos if info["supplier_match"]]
        family_only = [info for info in line_infos if info["family_match"]]
        if amount_only:
            reason = "Le montant TTC existe dans l'etat des depenses, mais le fournisseur ou l'alias n'est pas reconnu."
            action = "Ajouter un alias fournisseur ou verifier que le libelle comptable vise la meme piece."
            line = amount_only[0]["line"]
            candidate_count = len(amount_only)
        elif supplier_only:
            reason = "Le fournisseur semble present, mais aucun montant identique n'a ete trouve."
            action = "Chercher une ventilation, un regroupement, un avoir ou une regularisation."
            line = supplier_only[0]["line"]
            candidate_count = len(supplier_only)
        elif family_only:
            reason = "La famille comptable est compatible, mais ni reference, ni montant exact, ni fournisseur reconnu ne suffisent."
            action = "Comparer les lignes du compte candidat et completer les alias/factures manquantes."
            line = family_only[0]["line"]
            candidate_count = len(family_only)
        else:
            reason = "Aucune ligne de depense ne porte la reference, le montant exact, le fournisseur ou une famille comptable suffisante."
            action = "Verifier l'etat des depenses, le grand livre, les libelles OCR et la presence de la piece."
            line = None
            candidate_count = 0
        results.append(
            _candidate_row(
                invoice,
                "NON_RAPPROCHE",
                "A_CONTROLER",
                line,
                candidate_count,
                "no_deterministic_match",
                reason,
                action,
            )
        )

    return results


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
    if status.startswith("MATCH_"):
        return []
    severity = "P1" if status == "NON_RAPPROCHE" else "P2"
    control = "FACTURE_NON_RAPPROCHEE_ETAT_DEPENSES" if status == "NON_RAPPROCHE" else "RAPPROCHEMENT_A_CONTROLER"
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


def _counter_lines(counter: Counter[str], empty_label: str = "Aucun") -> list[str]:
    if not counter:
        return [f"- {empty_label}"]
    return [f"- {key}: {value}" for key, value in counter.most_common()]


def _md_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").replace("|", "/").strip()


def _write_accounting_report(
    path: Path,
    *,
    year: int,
    invoices: list[dict[str, str]],
    entries: list[dict[str, str]],
    controls: list[dict[str, str]],
    expense_lines: list[dict[str, str]],
    matches: list[dict[str, str]],
    alias_suggestions: list[dict[str, str]] | None = None,
) -> None:
    alias_suggestions = alias_suggestions or []
    total_ttc = sum((_decimal(row.get("ttc")) or Decimal("0")) for row in invoices)
    match_statuses = Counter(row.get("match_status", "") or "SANS_ETAT_DEPENSES" for row in matches)
    non_match_reasons = Counter(row.get("match_reason", "") for row in matches if not row.get("match_status", "").startswith("MATCH_"))
    supplier_non_matches = Counter(row.get("fournisseur", "") or "FOURNISSEUR_A_IDENTIFIER" for row in matches if row.get("match_status") == "NON_RAPPROCHE")
    control_severities = Counter(row.get("severity", "") for row in controls)
    alias_statuses = Counter(row.get("suggestion_status", "") for row in alias_suggestions)
    priority_items = [
        row for row in matches if row.get("match_status", "") and not row.get("match_status", "").startswith("MATCH_")
    ]
    priority_items.sort(key=lambda row: (_decimal(row.get("ttc")) or Decimal("0")), reverse=True)

    lines = [
        f"# Rapport ComptaScope {year}",
        "",
        "Ce rapport explique la reconstruction comptable candidate et les rapprochements avec l'etat des depenses quand il est disponible.",
        "",
        "## Synthese",
        "",
        f"- Factures candidates: {len(invoices)}",
        f"- Ecritures candidates: {len(entries)}",
        f"- Total TTC facture: {_money(total_ttc)} EUR",
        f"- Lignes d'etat des depenses exploitees: {len(expense_lines)}",
        f"- Controles ouverts: {len(controls)}",
        f"- Controles P0: {control_severities.get('P0', 0)}",
        f"- Controles P1: {control_severities.get('P1', 0)}",
        f"- Alias fournisseurs proposes: {len(alias_suggestions)}",
        f"- Alias auto-appliques: {alias_statuses.get('AUTO_APPLICABLE', 0)}",
        "",
        "## Rapprochements",
        "",
        *_counter_lines(match_statuses, "Aucun rapprochement calcule"),
        "",
        "## Comment lire un non-rapprochement",
        "",
        "`NON_RAPPROCHE` ne veut pas dire que la facture est absente de la comptabilite. Cela veut dire que ComptaScope n'a pas encore trouve de preuve deterministe suffisante dans l'etat des depenses.",
        "",
        "ComptaScope avance automatiquement quand il trouve une reference de facture, un montant exact avec fournisseur reconnu, un alias fournisseur configure, une famille comptable compatible, ou une somme unique de lignes ventilees.",
        "",
        "Une facture peut rester non rapprochee si le syndic utilise un alias, une reference interne, une ventilation par cle/batiment/equipement, un regroupement de factures, ou si l'extraction OCR a affaibli le numero ou le montant.",
        "",
        "## Causes a traiter",
        "",
        *_counter_lines(non_match_reasons, "Aucune cause ouverte"),
        "",
        "## Alias fournisseurs deduits",
        "",
        "| Statut | Fournisseur | Alias propose | Preuves | Total TTC | Exemple |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
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
            "## Fournisseurs a prioriser",
            "",
            *_counter_lines(supplier_non_matches, "Aucun fournisseur non rapproche"),
            "",
            "## Exemples prioritaires a expliquer",
            "",
            "| Statut | Fournisseur | Facture | TTC | Cause | Action |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    if priority_items:
        for row in priority_items[:15]:
            lines.append(
                " | ".join(
                    [
                        "",
                        _md_cell(row.get("match_status", "")),
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
        lines.append("| - | - | - | - | Aucun point prioritaire | - |")
    lines.extend(
        [
            "",
            "## Prochaines actions automatisees",
            "",
            "- Completer les alias fournisseurs locaux lorsque le montant existe mais le libelle differe.",
            "- Departager les montants ambigus par reference, date, compte ou cle de repartition.",
            "- Controler les ventilations multi-lignes avant de les traiter comme rapprochements forts.",
            "- Comparer les non-rapproches restants avec le grand livre et les pieces manquantes.",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def _write_duckdb(path: Path, tables: dict[str, tuple[list[str], list[dict[str, str]]]]) -> bool:
    try:
        import duckdb
    except ImportError:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    try:
        for table_name, (fields, rows) in tables.items():
            con.execute(f"DROP TABLE IF EXISTS {table_name}")
            columns = ", ".join(f"{field} VARCHAR" for field in fields)
            con.execute(f"CREATE TABLE {table_name} ({columns})")
            if rows:
                placeholders = ", ".join("?" for _ in fields)
                con.executemany(
                    f"INSERT INTO {table_name} VALUES ({placeholders})",
                    [[row.get(field, "") for field in fields] for row in rows],
                )
    finally:
        con.close()
    return True


def reconstruct_accounting(instance: InstanceConfig, run: RunContext, year: int) -> dict[str, object]:
    accounting_dir = instance.artifact("accounting_dir") / str(year)
    accounting_dir.mkdir(parents=True, exist_ok=True)

    invoices: list[dict[str, str]] = []
    entries: list[dict[str, str]] = []
    controls: list[dict[str, str]] = []
    seen_keys: Counter[str] = Counter()

    preloaded_invoices = _load_configured_invoice_evidence(instance, year)
    if preloaded_invoices:
        for invoice_row in preloaded_invoices:
            invoices.append(invoice_row)
            controls.extend(_controls_for_invoice(invoice_row, year))
            entry = _entry_for_invoice(invoice_row, year, len(entries) + 1)
            if entry is not None:
                entries.append(entry)
    else:
        for row in _candidate_source_rows(instance):
            path = _resolve_source_path(instance, row)
            if path is None or not path.is_file():
                continue
            text, method = _read_text(path)
            if not _looks_like_invoice(row, path, text, year):
                continue
            extraction = extract_generic_invoice_from_evidence(
                DocumentExtractionEvidence(file_name=path.name, native_text=text)
            )
            account, family = _account_for_invoice(text, extraction.fournisseur)
            anomalies = list(extraction.anomalies)
            if extraction.date_facture and str(year) not in extraction.date_facture:
                anomalies.append("FACTURE_HORS_EXERCICE")
            key = f"{extraction.fournisseur}|{extraction.numero_facture}|{extraction.ttc}"
            seen_keys[key] += 1
            if key.strip("|") and seen_keys[key] > 1:
                anomalies.append("DOUBLON_POTENTIEL")

            invoice_row = {
                "doc_id": row.get("doc_id") or f"DOC-{len(invoices) + 1:04d}",
                "sha256": row.get("sha256") or sha256_file(path),
                "source_path": str(path),
                "file_name": path.name,
                "exercice": str(year),
                "fournisseur": extraction.fournisseur,
                "siren_siret": extraction.siren_siret,
                "numero_facture": extraction.numero_facture,
                "date_facture": extraction.date_facture,
                "ht": extraction.ht,
                "tva": extraction.tva,
                "ttc": extraction.ttc,
                "compte_propose": account,
                "famille_charge": family,
                "statut_controle": _status(anomalies, extraction.confidence),
                "confidence": extraction.confidence,
                "anomalies": "|".join(dict.fromkeys(anomalies)),
                "extraction_method": method,
            }
            invoices.append(invoice_row)
            controls.extend(_controls_for_invoice(invoice_row, year))
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

    invoice_path = accounting_dir / f"invoice_evidence_{year}.csv"
    entries_path = accounting_dir / f"ledger_reconstruction_{year}.csv"
    controls_path = accounting_dir / f"accounting_controls_{year}.csv"
    expense_lines_path = accounting_dir / f"expense_statement_lines_{year}.csv"
    expense_matches_path = accounting_dir / f"invoice_expense_matches_{year}.csv"
    non_matches_path = accounting_dir / f"non_rapproches_prioritaires_{year}.csv"
    alias_suggestions_path = accounting_dir / f"supplier_alias_suggestions_{year}.csv"
    report_path = accounting_dir / f"rapport_comptascope_{year}.md"
    write_csv(invoice_path, INVOICE_EVIDENCE_FIELDS, invoices)
    write_csv(entries_path, ACCOUNTING_ENTRY_FIELDS, entries)
    write_csv(controls_path, ACCOUNTING_CONTROL_FIELDS, controls)
    if expense_lines:
        write_csv(expense_lines_path, EXPENSE_STATEMENT_FIELDS, expense_lines)
        write_csv(expense_matches_path, INVOICE_EXPENSE_MATCH_FIELDS, expense_matches)
        write_csv(alias_suggestions_path, SUPPLIER_ALIAS_SUGGESTION_FIELDS, alias_suggestions)
        non_matches = [
            {
                "doc_id": row.get("doc_id", ""),
                "fournisseur": row.get("fournisseur", ""),
                "numero_facture": row.get("numero_facture", ""),
                "ttc": row.get("ttc", ""),
                "match_status": row.get("match_status", ""),
                "match_reason": row.get("match_reason", ""),
                "next_action": row.get("next_action", ""),
            }
            for row in expense_matches
            if not row.get("match_status", "").startswith("MATCH_")
        ]
        non_matches.sort(key=lambda row: (_decimal(row.get("ttc")) or Decimal("0")), reverse=True)
        write_csv(non_matches_path, NON_MATCH_PRIORITY_FIELDS, non_matches)
    _write_accounting_report(
        report_path,
        year=year,
        invoices=invoices,
        entries=entries,
        controls=controls,
        expense_lines=expense_lines,
        matches=expense_matches,
        alias_suggestions=alias_suggestions,
    )

    duckdb_path = accounting_dir / f"coproscope_accounting_{year}.duckdb"
    duckdb_tables = {
            "invoice_evidence": (INVOICE_EVIDENCE_FIELDS, invoices),
            "ledger_reconstruction": (ACCOUNTING_ENTRY_FIELDS, entries),
            "accounting_controls": (ACCOUNTING_CONTROL_FIELDS, controls),
    }
    if expense_lines:
        duckdb_tables["expense_statement_lines"] = (EXPENSE_STATEMENT_FIELDS, expense_lines)
        duckdb_tables["invoice_expense_matches"] = (INVOICE_EXPENSE_MATCH_FIELDS, expense_matches)
        duckdb_tables["supplier_alias_suggestions"] = (SUPPLIER_ALIAS_SUGGESTION_FIELDS, alias_suggestions)
    duckdb_written = _write_duckdb(duckdb_path, duckdb_tables)

    summary = {
        "status": "ok",
        "year": year,
        "invoice_count": len(invoices),
        "entry_count": len(entries),
        "control_count": len(controls),
        "expense_statement_line_count": len(expense_lines),
        "expense_match_counts": dict(Counter(row.get("match_status", "") for row in expense_matches)),
        "supplier_alias_suggestion_count": len(alias_suggestions),
        "supplier_alias_auto_count": sum(1 for row in alias_suggestions if row.get("suggestion_status") == "AUTO_APPLICABLE"),
        "invoice_evidence": str(invoice_path),
        "ledger_reconstruction": str(entries_path),
        "accounting_controls": str(controls_path),
        "expense_statement_lines": str(expense_lines_path) if expense_lines else "",
        "invoice_expense_matches": str(expense_matches_path) if expense_lines else "",
        "non_rapproches_prioritaires": str(non_matches_path) if expense_lines else "",
        "supplier_alias_suggestions": str(alias_suggestions_path) if expense_lines else "",
        "report": str(report_path),
        "duckdb": str(duckdb_path) if duckdb_written else "",
        "generated_at": now_iso(),
    }
    write_text(accounting_dir / f"summary_{year}.json", json.dumps(summary, indent=2, ensure_ascii=True))
    run.log_action("accounting_reconstruct", accounting_dir, f"year={year}; invoices={len(invoices)}")
    return summary


def accounting_controls(instance: InstanceConfig, run: RunContext, year: int) -> dict[str, object]:
    accounting_dir = instance.artifact("accounting_dir") / str(year)
    controls_path = accounting_dir / f"accounting_controls_{year}.csv"
    if not controls_path.exists():
        reconstruct_accounting(instance, run, year)
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


def copy_accounting_tables_for_dashboard(instance: InstanceConfig, year: int, target_dir: Path) -> dict[str, str]:
    accounting_dir = instance.artifact("accounting_dir") / str(year)
    target_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[str, str] = {}
    for name in [
        "invoice_evidence",
        "ledger_reconstruction",
        "accounting_controls",
        "expense_statement_lines",
        "invoice_expense_matches",
        "non_rapproches_prioritaires",
        "supplier_alias_suggestions",
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
    return copied
