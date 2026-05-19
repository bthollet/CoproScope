from __future__ import annotations

import csv
import json
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

from ..core.common import InstanceConfig, RunContext, now_iso, read_csv, sha256_file, write_csv, write_text
from ..extractors.invoices import DocumentExtractionEvidence, extract_generic_invoice_from_evidence


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

        amount = _amount(extraction.ttc)
        if amount is not None:
            entries.append(
                {
                    "entry_id": f"REC-{year}-{len(entries) + 1:04d}",
                    "exercice": str(year),
                    "date": extraction.date_facture,
                    "journal": "ACHATS_RECONSTITUES",
                    "compte_debit": account,
                    "compte_credit": "401000",
                    "debit": f"{amount:.2f}",
                    "credit": f"{amount:.2f}",
                    "fournisseur": extraction.fournisseur,
                    "numero_facture": extraction.numero_facture,
                    "piece_doc_id": invoice_row["doc_id"],
                    "source_path": str(path),
                    "statut": invoice_row["statut_controle"],
                    "justification": "Ecriture candidate reconstruite depuis facture; validation humaine requise.",
                }
            )

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
    write_csv(invoice_path, INVOICE_EVIDENCE_FIELDS, invoices)
    write_csv(entries_path, ACCOUNTING_ENTRY_FIELDS, entries)
    write_csv(controls_path, ACCOUNTING_CONTROL_FIELDS, controls)

    duckdb_path = accounting_dir / f"coproscope_accounting_{year}.duckdb"
    duckdb_written = _write_duckdb(
        duckdb_path,
        {
            "invoice_evidence": (INVOICE_EVIDENCE_FIELDS, invoices),
            "ledger_reconstruction": (ACCOUNTING_ENTRY_FIELDS, entries),
            "accounting_controls": (ACCOUNTING_CONTROL_FIELDS, controls),
        },
    )

    summary = {
        "status": "ok",
        "year": year,
        "invoice_count": len(invoices),
        "entry_count": len(entries),
        "control_count": len(controls),
        "invoice_evidence": str(invoice_path),
        "ledger_reconstruction": str(entries_path),
        "accounting_controls": str(controls_path),
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
    for name in ["invoice_evidence", "ledger_reconstruction", "accounting_controls"]:
        source = accounting_dir / f"{name}_{year}.csv"
        if not source.exists() and name == "ledger_reconstruction":
            source = accounting_dir / f"ledger_reconstruction_{year}.csv"
        if source.exists():
            destination = target_dir / source.name
            destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            copied[name] = str(destination)
    return copied
