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

COMPTASCOPE_REVIEW_FIELDS = [
    "review_id",
    "exercice",
    "priorite",
    "fournisseur",
    "numero_facture",
    "doc_id",
    "date_facture",
    "ttc",
    "niveau_preuve",
    "anomalies_facture",
    "statut_rapprochement",
    "libelle_statut",
    "confiance",
    "ligne_depense_candidate",
    "reference_depense",
    "libelle_depense",
    "montant_depense",
    "candidate_count",
    "ecriture_candidate",
    "compte_candidate",
    "motif",
    "prochaine_action",
    "question_syndic",
    "bloc_copiable",
]

COMPTASCOPE_REVIEW_GROUP_FIELDS = [
    "group_id",
    "exercice",
    "priorite",
    "fournisseur",
    "anomalie_facture",
    "statut_rapprochement",
    "libelle_statut",
    "factures",
    "total_ttc",
    "questions_syndic",
    "action_type",
    "exemples_factures",
]

MATCH_STATUS_META: dict[str, dict[str, str]] = {
    "SANS_ETAT_DEPENSES": {
        "label": "Etat des depenses non exploite",
        "priority": "P2",
        "meaning": "Les factures sont reconstituees, mais aucune ligne d'etat des depenses n'est disponible pour rapprocher.",
        "local_treatment": "Production du guide facture sans comparaison comptable.",
        "human_check": "Fournir l'etat des depenses ou l'annexe comptable avant conclusion.",
    },
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
        "human_check": "Confirmer que les deux noms designent le meme tiers avant avis local.",
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
        "human_check": "Limiter par date, compte, cle ou equipement avant conclusion.",
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
        "human_check": "Comparer avec l'etat des depenses et les pieces avant tout reclassement.",
    },
    "NON_RAPPROCHE": {
        "label": "Aucun indice local suffisant",
        "priority": "P1",
        "meaning": "Aucune reference, montant, fournisseur, alias ou famille comptable suffisante n'a ete trouvee.",
        "local_treatment": "Tous les traitements locaux disponibles ont echoue.",
        "human_check": "Verifier etat des depenses, annexe comptable, OCR, piece manquante ou imputation hors perimetre.",
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
