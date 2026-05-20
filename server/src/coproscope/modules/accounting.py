from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

from ..core.common import InstanceConfig, RunContext, now_iso, read_csv, sha256_file, write_csv, write_text
from ..extractors.invoices.reconciliation import invoice_keys, normalized_for_match, parse_amount
from .factureops import INVOICE_ANOMALY_FIELDS, INVOICE_EVIDENCE_FIELDS, extract_invoices


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
    "match_priority",
    "status_label",
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
    "match_priority",
    "status_label",
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

SUPPLIER_DUE_DILIGENCE_FIELDS = [
    "doc_id",
    "exercice",
    "fournisseur",
    "siren_siret",
    "numero_facture",
    "date_facture",
    "ttc",
    "trigger_anomalies",
    "coverage_status",
    "diligence_liee",
    "method_sources",
    "existing_worklist_refs",
    "existing_result_refs",
    "controls_to_apply",
    "next_action",
]

MATCH_STATUS_META: dict[str, dict[str, str]] = {
    "MATCH_REFERENCE": {
        "label": "Reference facture retrouvee",
        "priority": "OK",
        "meaning": "Le numero de facture ou une reference equivalente apparait dans l'etat des depenses.",
        "local_treatment": "Recherche deterministe de reference apres normalisation des espaces et signes.",
        "human_check": "Controle simple du libelle si le montant ou le fournisseur parait incoherent.",
    },
    "MATCH_AMOUNT_SUPPLIER": {
        "label": "Montant exact + fournisseur reconnu",
        "priority": "OK",
        "meaning": "Une seule ligne porte le meme TTC et un nom fournisseur reconnu.",
        "local_treatment": "Comparaison exacte du montant et reconnaissance du fournisseur dans le libelle/tiers.",
        "human_check": "Controle ponctuel des postes sensibles.",
    },
    "MATCH_AMOUNT_ALIAS": {
        "label": "Montant exact + alias fournisseur",
        "priority": "OK",
        "meaning": "Une seule ligne porte le meme TTC et un alias fournisseur configure ou deduit.",
        "local_treatment": "Application des alias locaux confirmes ou auto-applicables.",
        "human_check": "Conserver la trace de l'alias utilise.",
    },
    "CANDIDAT_SOMME_MULTI_LIGNES": {
        "label": "Somme multi-lignes unique",
        "priority": "P2",
        "meaning": "Plusieurs lignes compatibles totalisent exactement le TTC de la facture.",
        "local_treatment": "Recherche locale de combinaison unique de lignes inferieures au montant facture.",
        "human_check": "Confirmer la ventilation par cle, compteur, batiment ou equipement.",
    },
    "CANDIDAT_MONTANT_FAMILLE": {
        "label": "Montant exact + famille comptable",
        "priority": "P2",
        "meaning": "Une seule ligne porte le meme TTC et un compte compatible, mais le fournisseur n'est pas reconnu.",
        "local_treatment": "Comparaison du compte/famille de charge avec le compte propose de la facture.",
        "human_check": "Confirmer le libelle puis creer un alias si le lien est exact.",
    },
    "CANDIDAT_NOM_SIMILAIRE": {
        "label": "Nom fournisseur tres similaire",
        "priority": "P2",
        "meaning": "Le montant et la famille concordent; le nom du tiers ressemble fortement au fournisseur.",
        "local_treatment": "Similarite locale de noms, sans appel IA ni interpretation externe.",
        "human_check": "Confirmer que les deux noms designent le meme tiers avant de valider.",
    },
    "CANDIDAT_DIVISION_EGALE": {
        "label": "Facture divisee en lignes egales",
        "priority": "P2",
        "meaning": "La facture semble ventilee en plusieurs lignes de meme montant.",
        "local_treatment": "Division exacte du TTC par un nombre de lignes compatibles.",
        "human_check": "Verifier la cle de repartition ou le detail de ventilation.",
    },
    "CANDIDAT_REGROUPEMENT_FACTURES": {
        "label": "Plusieurs factures regroupees",
        "priority": "P2",
        "meaning": "Plusieurs factures du meme fournisseur semblent former une seule ligne de depense.",
        "local_treatment": "Somme exacte de plusieurs factures candidates vers une ligne de depense.",
        "human_check": "Confirmer que la ligne comptable regroupe bien ces pieces.",
    },
    "CANDIDAT_REFERENCE_AMBIGUE": {
        "label": "Reference trouvee plusieurs fois",
        "priority": "P2",
        "meaning": "La reference apparait dans plusieurs lignes possibles.",
        "local_treatment": "Recherche deterministe de reference, mais sans departage unique.",
        "human_check": "Departager par date, compte, montant ou piece.",
    },
    "CANDIDAT_MONTANT_AMBIGU": {
        "label": "Montant exact ambigu",
        "priority": "P2",
        "meaning": "Le montant existe, mais plusieurs factures ou lignes peuvent correspondre.",
        "local_treatment": "Comparaison exacte du montant avec detection des doublons/repetitions.",
        "human_check": "Utiliser la date, la reference, le compte ou la ventilation pour departager.",
    },
    "CANDIDAT_VENTILATION_AMBIGUE": {
        "label": "Ventilation possible mais ambigue",
        "priority": "P2",
        "meaning": "Plusieurs combinaisons de lignes peuvent reconstituer la facture.",
        "local_treatment": "Recherche de sommes multi-lignes exactes.",
        "human_check": "Limiter par date, compte, cle ou equipement avant validation.",
    },
    "CANDIDAT_MONTANT_SANS_NOM": {
        "label": "Montant exact sans fournisseur reconnu",
        "priority": "P2",
        "meaning": "Le montant existe, mais le fournisseur ou son alias n'est pas reconnu.",
        "local_treatment": "Comparaison exacte du TTC, sans preuve de tiers suffisante.",
        "human_check": "Verifier le libelle et creer un alias si le lien est confirme.",
    },
    "CANDIDAT_FOURNISSEUR_SANS_MONTANT": {
        "label": "Fournisseur reconnu sans montant exact",
        "priority": "P2",
        "meaning": "Le fournisseur est present, mais aucun montant identique n'a ete trouve.",
        "local_treatment": "Recherche du fournisseur ou alias dans les lignes.",
        "human_check": "Chercher regroupement, division, avoir ou regularisation.",
    },
    "CANDIDAT_FAMILLE_SEULE": {
        "label": "Famille comptable compatible seulement",
        "priority": "P2",
        "meaning": "Le compte semble compatible, mais reference, montant et fournisseur ne suffisent pas.",
        "local_treatment": "Rapprochement faible par compte/famille de charge.",
        "human_check": "Comparer avec le grand livre et les pieces avant tout reclassement.",
    },
    "NON_RAPPROCHE": {
        "label": "Aucun indice local suffisant",
        "priority": "P1",
        "meaning": "Aucune reference, montant, fournisseur, alias ou famille comptable suffisante n'a ete trouvee.",
        "local_treatment": "Tous les traitements locaux disponibles ont echoue.",
        "human_check": "Verifier grand livre, etat des depenses, OCR, piece manquante ou imputation hors perimetre.",
    },
}


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


def _status_meta(status: str) -> dict[str, str]:
    return MATCH_STATUS_META.get(
        status,
        {
            "label": status or "Statut non renseigne",
            "priority": "P2",
            "meaning": "Statut a documenter.",
            "local_treatment": "Traitement local non detaille.",
            "human_check": "Verifier la ligne source.",
        },
    )


def _status_priority(status: str) -> str:
    return _status_meta(status).get("priority", "P2")


def _priority_rank(priority: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "OK": 3}.get(priority or "", 4)


def _is_confirmed_status(status: str) -> bool:
    return _status_priority(status) == "OK"


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


def _configured_paths_no_year(instance: InstanceConfig, settings: dict[str, Any], *keys: str) -> list[Path]:
    paths: list[Path] = []
    for key in keys:
        for raw_value in _as_list(settings.get(key)):
            resolved = instance.resolve_path(str(raw_value))
            if resolved is not None:
                paths.append(resolved)
    return paths


def _supplier_due_diligence_settings(instance: InstanceConfig) -> dict[str, Any]:
    settings = instance.settings()
    combined: dict[str, Any] = {}
    global_settings = settings.get("supplier_due_diligence")
    if isinstance(global_settings, dict):
        combined.update(global_settings)
    comptascope_settings = _comptascope_settings(instance).get("supplier_due_diligence")
    if isinstance(comptascope_settings, dict):
        combined.update(comptascope_settings)
    return combined


def _load_rows_with_source(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_paths: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved in seen_paths or not resolved.exists():
            continue
        seen_paths.add(resolved)
        _, loaded = read_csv(resolved)
        for row in loaded:
            copied = dict(row)
            copied["_source_file"] = path.name
            rows.append(copied)
    return rows


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


def _load_configured_supplier_due_invoice_triggers(
    instance: InstanceConfig,
    year: int,
    existing_doc_ids: set[str],
) -> list[dict[str, str]]:
    settings = _comptascope_settings(instance)
    if not _as_bool(settings.get("include_cross_year_supplier_due_diligence"), True):
        return []
    candidates = _configured_paths(
        instance,
        settings,
        "invoice_evidence_csv",
        "pre_accounting_invoices",
        "pre_compta_invoices",
        year=year,
    )
    rows: list[dict[str, str]] = []
    seen_doc_ids = set(existing_doc_ids)
    for path in candidates:
        if not path.exists():
            continue
        _, loaded = read_csv(path)
        for index, row in enumerate(loaded, start=1):
            doc_id = row.get("doc_id") or f"INV-{year}-DILIGENCE-{len(rows) + index:04d}"
            if doc_id in seen_doc_ids:
                continue
            anomalies = (row.get("anomalies") or "").replace(" | ", "|")
            candidate = {
                "doc_id": doc_id,
                "sha256": row.get("sha256", ""),
                "source_path": row.get("source_path") or row.get("chemin_piece") or row.get("original_path") or "",
                "file_name": row.get("file_name") or row.get("aliases") or "",
                "exercice": row.get("exercice") or row.get("year") or str(year),
                "fournisseur": row.get("fournisseur") or row.get("supplier") or "",
                "siren_siret": row.get("siren_siret") or row.get("siret") or row.get("siren") or "",
                "numero_facture": row.get("numero_facture") or row.get("invoice_number") or "",
                "date_facture": row.get("date_facture") or row.get("invoice_date") or "",
                "ht": row.get("ht") or row.get("amount_ht") or "",
                "tva": row.get("tva") or row.get("vat") or "",
                "ttc": _money(_decimal(row.get("ttc") or row.get("amount_ttc") or row.get("montant_ttc"))),
                "compte_propose": row.get("compte_propose") or row.get("account") or "",
                "famille_charge": row.get("famille_charge") or row.get("control_family") or "",
                "statut_controle": row.get("statut_controle") or "",
                "confidence": row.get("confidence") or row.get("confiance") or "preloaded",
                "anomalies": anomalies,
                "extraction_method": row.get("extraction_method") or row.get("source_register") or "preloaded_csv",
            }
            if _invoice_is_supplier_due_diligence_trigger(candidate):
                seen_doc_ids.add(doc_id)
                rows.append(candidate)
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


def _supplier_match_score(left: str, right: str) -> Decimal:
    left_norm = _normal(left)
    right_norm = _normal(right)
    if not left_norm or not right_norm:
        return Decimal("0")
    if left_norm == right_norm:
        return Decimal("1")
    if left_norm in right_norm or right_norm in left_norm:
        return Decimal("0.95")
    left_tokens = _significant_supplier_tokens(left)
    right_tokens = _significant_supplier_tokens(right)
    if not left_tokens or not right_tokens:
        return Decimal(str(SequenceMatcher(None, left_norm, right_norm).ratio()))
    overlap = Decimal(len(left_tokens & right_tokens))
    token_score = overlap / Decimal(max(len(left_tokens), len(right_tokens)))
    sequence_score = Decimal(str(SequenceMatcher(None, left_norm, right_norm).ratio()))
    return max(token_score, sequence_score)


def _row_actor(row: dict[str, str]) -> str:
    return (
        row.get("acteur")
        or row.get("cible")
        or row.get("producteur_piece")
        or row.get("supplier")
        or row.get("fournisseur")
        or ""
    )


def _row_reference(row: dict[str, str]) -> str:
    identifier = (
        row.get("resultat_id")
        or row.get("controle_id")
        or row.get("acteur")
        or row.get("cible")
        or row.get("producteur_piece")
        or row.get("_source_file")
        or ""
    )
    source = row.get("_source_file", "")
    if source and source not in identifier:
        return f"{identifier} ({source})"
    return identifier


def _matching_rows(supplier: str, rows: list[dict[str, str]], threshold: Decimal = Decimal("0.72")) -> list[dict[str, str]]:
    matches: list[tuple[Decimal, dict[str, str]]] = []
    for row in rows:
        actor = _row_actor(row)
        score = _supplier_match_score(supplier, actor)
        if score >= threshold:
            matches.append((score, row))
    matches.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in matches]


def _invoice_is_supplier_due_diligence_trigger(row: dict[str, str]) -> bool:
    anomalies = row.get("anomalies", "")
    return any(token in anomalies for token in ("DILIGENCE_REQUISE", "DILIGENCE_A_EVALUER"))


def _invoice_due_diligence_codes(row: dict[str, str]) -> list[str]:
    supplier = row.get("fournisseur", "")
    haystack = _normal(
        " ".join(
            [
                supplier,
                row.get("famille_charge", ""),
                row.get("compte_propose", ""),
                row.get("numero_facture", ""),
                row.get("anomalies", ""),
            ]
        )
    )
    codes = ["DIL-DD-003"]
    if "siren_siret_absent" in haystack:
        codes.append("DIL-DD-003")
    if any(token in haystack for token in ["ripert", "assur", "orias", "courtier"]):
        codes.extend(["DIL-DD-007", "DIL-DD-009", "DIL-DD-011", "DIL-DD-016"])
    if any(
        token in haystack
        for token in [
            "travaux",
            "plomberie",
            "ascenseur",
            "omega",
            "vincentelli",
            "services",
            "elagage",
            "maintenance",
        ]
    ):
        codes.extend(["DIL-DD-005", "DIL-DD-009", "DIL-DD-015", "DIL-DD-017"])
    return list(dict.fromkeys(codes))


def _admin_controls_for_codes(admin_rows: list[dict[str, str]], codes: list[str]) -> list[dict[str, str]]:
    wanted = set(codes)
    selected: list[dict[str, str]] = []
    for row in admin_rows:
        linked = {item.strip() for item in re.split(r"[;|]", row.get("diligence_liee", "")) if item.strip()}
        if wanted & linked:
            selected.append(row)
    selected.sort(key=lambda row: (row.get("priorite", "P9"), row.get("controle_id", "")))
    return selected


def _supplier_dd_action(row: dict[str, str], codes: list[str]) -> str:
    supplier = _normal(row.get("fournisseur", ""))
    if "ripert" in supplier or "assur" in supplier:
        return (
            "Rattacher contrat/police, RIB et paiement; verifier ORIAS/mandat si intermediation, "
            "commissions/remunerations et information CS/AG."
        )
    if any(code in codes for code in ["DIL-DD-005", "DIL-DD-017"]):
        return (
            "Rattacher decision/devis ou urgence, consultation CS/mise en concurrence, service fait, "
            "assurance/qualification, reception si applicable, RIB et paiement."
        )
    return "Verifier identite juridique, SIREN/SIRET, RNE/INPI, RIB, paiement et piece primaire fournisseur."


def build_supplier_due_diligence_controls(
    instance: InstanceConfig,
    invoices: list[dict[str, str]],
    year: int,
) -> list[dict[str, str]]:
    settings = _supplier_due_diligence_settings(instance)
    method_paths = _configured_paths_no_year(instance, settings, "method_plan", "plan", "methodology")
    worklist_rows = _load_rows_with_source(
        _configured_paths_no_year(instance, settings, "worklist_csv", "worklists", "worklist")
    )
    result_rows = _load_rows_with_source(
        _configured_paths_no_year(instance, settings, "result_csv", "result_csvs", "results")
    )
    admin_rows = _load_rows_with_source(
        _configured_paths_no_year(instance, settings, "admin_controls_csv", "admin_controls", "control_matrix")
    )

    rows: list[dict[str, str]] = []
    for invoice in invoices:
        if not _invoice_is_supplier_due_diligence_trigger(invoice):
            continue
        supplier = invoice.get("fournisseur", "") or "FOURNISSEUR_A_IDENTIFIER"
        codes = _invoice_due_diligence_codes(invoice)
        matching_worklist = _matching_rows(supplier, worklist_rows)
        matching_results = _matching_rows(supplier, result_rows)
        controls = _admin_controls_for_codes(admin_rows, codes)
        if matching_results:
            coverage = "COUVERT_RECENT_A_RECOUPER"
        elif matching_worklist:
            coverage = "DANS_PLAN_EXISTANT_A_COMPLETER"
        else:
            coverage = "A_TRAITER_METHODO_EXISTANTE"

        controls_summary = "; ".join(
            f"{row.get('controle_id', '')}: {row.get('controle_a_produire', '')}".strip(": ")
            for row in controls[:8]
        )
        if not controls_summary and codes:
            controls_summary = "Appliquer les controles du plan existant lies a " + "; ".join(codes)
        method_sources = "; ".join(path.name for path in method_paths if path.exists())
        if admin_rows:
            admin_sources = sorted({row.get("_source_file", "") for row in admin_rows if row.get("_source_file")})
            if admin_sources:
                method_sources = "; ".join([item for item in [method_sources, *admin_sources] if item])

        rows.append(
            {
                "doc_id": invoice.get("doc_id", ""),
                "exercice": str(year),
                "fournisseur": supplier,
                "siren_siret": invoice.get("siren_siret", ""),
                "numero_facture": invoice.get("numero_facture", ""),
                "date_facture": invoice.get("date_facture", ""),
                "ttc": invoice.get("ttc", ""),
                "trigger_anomalies": invoice.get("anomalies", ""),
                "coverage_status": coverage,
                "diligence_liee": "; ".join(codes),
                "method_sources": method_sources,
                "existing_worklist_refs": "; ".join(_row_reference(row) for row in matching_worklist[:5]),
                "existing_result_refs": "; ".join(_row_reference(row) for row in matching_results[:5]),
                "controls_to_apply": controls_summary,
                "next_action": _supplier_dd_action(invoice, codes),
            }
        )
    rows.sort(
        key=lambda row: (
            {"COUVERT_RECENT_A_RECOUPER": 2, "DANS_PLAN_EXISTANT_A_COMPLETER": 1}.get(
                row.get("coverage_status", ""), 0
            ),
            -(_decimal(row.get("ttc")) or Decimal("0")),
            row.get("fournisseur", ""),
        )
    )
    return rows


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


def _supplier_similarity(left: str, right: str) -> Decimal:
    left_norm = _normal(left)
    right_norm = _normal(right)
    if not left_norm or not right_norm:
        return Decimal("0")
    if left_norm in right_norm or right_norm in left_norm:
        return Decimal("1")
    left_tokens = _significant_supplier_tokens(left_norm)
    right_tokens = _significant_supplier_tokens(right_norm)
    token_score = Decimal("0")
    if left_tokens and right_tokens:
        common = left_tokens & right_tokens
        token_score = Decimal(len(common) * 2) / Decimal(len(left_tokens) + len(right_tokens))
    sequence_score = Decimal(str(SequenceMatcher(None, left_norm, right_norm).ratio()))
    return max(token_score, sequence_score)


def _similar_supplier_evidence(invoice: dict[str, str], line: dict[str, str]) -> tuple[str, Decimal]:
    candidates = [
        line.get("supplier_hint", ""),
        _statement_alias_candidate(line),
    ]
    label = line.get("label", "")
    if "/" in label:
        candidates.append(label.split("/", 1)[0])
    best_name = ""
    best_score = Decimal("0")
    for candidate in candidates:
        score = _supplier_similarity(invoice.get("fournisseur", ""), candidate)
        if score > best_score:
            best_score = score
            best_name = candidate
    return best_name, best_score


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
                    "Confirmer que la ligne comptable regroupe bien ces factures avant validation.",
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
                        "Verifier la cle de repartition, le compteur, le batiment ou l'equipement avant validation.",
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
                        "Limiter par date, compte ou cle de repartition avant validation.",
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
            action = "Verifier l'etat des depenses, le grand livre, les libelles OCR et la presence de la piece."
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


def _md_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").replace("|", "/").strip()


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
) -> None:
    alias_suggestions = alias_suggestions or []
    supplier_due_diligence = supplier_due_diligence or []
    total_ttc = sum((_decimal(row.get("ttc")) or Decimal("0")) for row in invoices)
    match_statuses = Counter(row.get("match_status", "") or "SANS_ETAT_DEPENSES" for row in matches)
    priority_counts = Counter(row.get("match_priority", _status_priority(row.get("match_status", ""))) for row in matches)
    supplier_open_counts = Counter(row.get("fournisseur", "") or "FOURNISSEUR_A_IDENTIFIER" for row in matches if row.get("match_priority") != "OK")
    supplier_open_totals: Counter[str] = Counter()
    for row in matches:
        if row.get("match_priority") != "OK":
            supplier_open_totals[row.get("fournisseur", "") or "FOURNISSEUR_A_IDENTIFIER"] += _decimal(row.get("ttc")) or Decimal("0")
    control_severities = Counter(row.get("severity", "") for row in controls)
    invoice_anomaly_severities = Counter(row.get("severity", "") for row in invoice_anomalies)
    invoice_anomaly_types = Counter(row.get("anomaly", "") for row in invoice_anomalies)
    evidence_levels = Counter(row.get("evidence_level", "") or "NON_RENSEIGNE" for row in invoices)
    alias_statuses = Counter(row.get("suggestion_status", "") for row in alias_suggestions)
    supplier_due_statuses = Counter(row.get("coverage_status", "") for row in supplier_due_diligence)
    priority_items = [
        row for row in matches if row.get("match_status", "") and row.get("match_priority") != "OK"
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
                0 if any(row.get("fournisseur") == item[0] and row.get("match_priority") == "P1" for row in matches) else 1,
                -(supplier_open_totals.get(item[0], Decimal("0"))),
                item[0],
            ),
        )
        for supplier, count in supplier_rows[:15]:
            total = supplier_open_totals.get(supplier, Decimal("0"))
            priority = "P1 d'abord" if any(row.get("fournisseur") == supplier and row.get("match_priority") == "P1" for row in matches) else "P2 a confirmer"
            lines.append(f"| {_md_cell(supplier)} | {count} | {_money(total)} | {priority} |")
    else:
        lines.append("| - | 0 | 0.00 | Aucun point ouvert |")
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
    report_path = accounting_dir / f"rapport_comptascope_{year}.md"
    write_csv(entries_path, ACCOUNTING_ENTRY_FIELDS, entries)
    write_csv(controls_path, ACCOUNTING_CONTROL_FIELDS, controls)
    write_csv(expense_lines_path, EXPENSE_STATEMENT_FIELDS, expense_lines)
    write_csv(expense_matches_path, INVOICE_EXPENSE_MATCH_FIELDS, expense_matches)
    write_csv(alias_suggestions_path, SUPPLIER_ALIAS_SUGGESTION_FIELDS, alias_suggestions)
    write_csv(supplier_due_diligence_path, SUPPLIER_DUE_DILIGENCE_FIELDS, supplier_due_diligence)
    non_matches = [
        {
            "doc_id": row.get("doc_id", ""),
            "fournisseur": row.get("fournisseur", ""),
            "numero_facture": row.get("numero_facture", ""),
            "ttc": row.get("ttc", ""),
            "match_status": row.get("match_status", ""),
            "match_priority": row.get("match_priority", ""),
            "status_label": row.get("status_label", ""),
            "match_reason": row.get("match_reason", ""),
            "next_action": row.get("next_action", ""),
        }
        for row in expense_matches
        if row.get("match_priority") != "OK"
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
        "invoice_evidence": str(invoice_path),
        "invoice_anomalies": str(invoice_anomalies_path),
        "ledger_reconstruction": str(entries_path),
        "accounting_controls": str(controls_path),
        "expense_statement_lines": str(expense_lines_path),
        "invoice_expense_matches": str(expense_matches_path),
        "non_rapproches_prioritaires": str(non_matches_path),
        "supplier_alias_suggestions": str(alias_suggestions_path),
        "supplier_due_diligence_controls": str(supplier_due_diligence_path),
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
