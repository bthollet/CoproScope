from __future__ import annotations

import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

from ..core.common import InstanceConfig, RunContext, read_csv, sha256_file, write_csv
from ..extractors.invoices import DocumentExtractionEvidence, InvoiceExtraction, extract_generic_invoice_from_evidence
from ..extractors.invoices.providers import (
    CogelecInvoiceProviderExtractor,
    InsuranceNoticeProviderExtractor,
    OmegaAscenseurInvoiceProviderExtractor,
    OrangeInvoiceProviderExtractor,
    PhoceaInvoiceProviderExtractor,
)
from ..extractors.invoices.reconciliation import parse_amount


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
    "evidence_level",
]

INVOICE_ANOMALY_FIELDS = [
    "anomaly_id",
    "exercice",
    "severity",
    "status",
    "doc_id",
    "fournisseur",
    "numero_facture",
    "ttc",
    "anomaly",
    "evidence_level",
    "extraction_method",
    "evidence",
    "action",
]

INTENSITY_LEVELS = (
    "L0_STRUCTURED_SOURCE",
    "L1_NATIVE_TEXT",
    "L2_LOCAL_OCR",
    "L3_LOCAL_STRUCTURE_OR_VISUAL",
    "L4_AI_OR_ONLINE_REVIEW",
)

_INTENSITY_RANK = {level: index for index, level in enumerate(INTENSITY_LEVELS)}


def _factureops_settings(instance: InstanceConfig) -> dict[str, Any]:
    settings = instance.settings()
    factureops = settings.get("factureops", {})
    comptascope = settings.get("comptascope", {})
    merged: dict[str, Any] = {}
    if isinstance(comptascope, dict):
        merged.update(comptascope)
    if isinstance(factureops, dict):
        merged.update(factureops)
    return merged


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _configured_paths(instance: InstanceConfig, settings: dict[str, Any], *keys: str, year: int) -> list[Path]:
    paths: list[Path] = []
    for key in keys:
        for raw_value in _as_list(settings.get(key)):
            value = str(raw_value).format(year=year)
            resolved = instance.resolve_path(value)
            if resolved is not None:
                paths.append(resolved)
    return paths


def _decimal(value: str | None) -> Decimal | None:
    return parse_amount(value)


def _money(value: Decimal | None) -> str:
    return f"{value:.2f}" if value is not None else ""


def _status(anomalies: Iterable[str], confidence: str) -> str:
    values = [value for value in anomalies if value]
    if not values and confidence in {"high", "medium", "preloaded"}:
        return "PROBABLE"
    if any(value in values for value in ["MONTANT_TTC_ABSENT", "DATE_FACTURE_ABSENTE", "FOURNISSEUR_ABSENT"]):
        return "A_CONTROLER"
    return "INCERTAIN"


def normalize_intensity_level(value: str | None, default: str = "L1_NATIVE_TEXT") -> str:
    raw = (value or "").upper()
    if "L4_" in raw or "P4_" in raw or "QWEN" in raw or "AI_OR_ONLINE" in raw:
        return "L4_AI_OR_ONLINE_REVIEW"
    if "L3_" in raw or "P3_" in raw or "DOCLING" in raw or "LAYOUT" in raw or "VISUAL" in raw:
        return "L3_LOCAL_STRUCTURE_OR_VISUAL"
    if "L2_" in raw or "P2_" in raw or "OCR" in raw:
        return "L2_LOCAL_OCR"
    if "L0_" in raw or "STRUCTURED" in raw or "PRELOADED" in raw or "FACTUR-X" in raw:
        return "L0_STRUCTURED_SOURCE"
    if "L1_" in raw or "P1_" in raw or "NATIVE" in raw or "TEXT" in raw:
        return "L1_NATIVE_TEXT"
    return default


def highest_intensity_level(*values: str | None, default: str = "L1_NATIVE_TEXT") -> str:
    levels = [normalize_intensity_level(value, default=default) for value in values if value]
    if not levels:
        return default
    return max(levels, key=lambda level: _INTENSITY_RANK.get(level, -1))


def _load_text_artifact(instance: InstanceConfig, value: str) -> str:
    if not value:
        return ""
    path = Path(value)
    if not path.is_absolute():
        path = instance.root("workspace") / value
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_source_text(path: Path) -> tuple[str, str, str]:
    if path.suffix.lower() in {".txt", ".md", ".csv"}:
        return path.read_text(encoding="utf-8-sig", errors="ignore"), "native_text", "L1_NATIVE_TEXT"
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text, "pypdf_native_text", "L1_NATIVE_TEXT"
        except Exception:  # noqa: BLE001
            return "", "pdf_unread", "L1_NATIVE_TEXT"
    if path.suffix.lower() in {".xml", ".ubl", ".cii"}:
        return path.read_text(encoding="utf-8-sig", errors="ignore"), "structured_source", "L0_STRUCTURED_SOURCE"
    return "", "unsupported", ""


def _document_evidence(instance: InstanceConfig, row: dict[str, str], path: Path) -> tuple[DocumentExtractionEvidence, str, str]:
    docops_text = _load_text_artifact(instance, row.get("text_path", ""))
    docling_markdown = _load_text_artifact(instance, row.get("docling_path", ""))
    layout_json = _load_text_artifact(instance, row.get("layout_path", ""))
    if docops_text:
        row_level = normalize_intensity_level(row.get("extraction_level"), default="L1_NATIVE_TEXT")
        ocr_text = docops_text if row_level == "L2_LOCAL_OCR" else ""
        native_text = "" if ocr_text else docops_text
        return (
            DocumentExtractionEvidence(
                file_name=path.name,
                native_text=native_text,
                ocr_text=ocr_text,
                docling_markdown=docling_markdown,
                layout_json=layout_json,
            ),
            "docops_text",
            row_level,
        )
    source_text, method, source_level = _read_source_text(path)
    row_level = normalize_intensity_level(row.get("extraction_level"), default=source_level or "L1_NATIVE_TEXT")
    evidence_level = highest_intensity_level(source_level, row_level, default=source_level or row_level)
    native_text = docops_text or source_text
    ocr_text = native_text if evidence_level == "L2_LOCAL_OCR" else ""
    if ocr_text:
        native_text = source_text
    return (
        DocumentExtractionEvidence(
            file_name=path.name,
            native_text=native_text,
            ocr_text=ocr_text,
            docling_markdown=docling_markdown,
            layout_json=layout_json,
        ),
        method if not docops_text else "docops_text",
        evidence_level,
    )


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
        (
            "615000",
            "securite_incendie",
            [
                r"\b(extincteurs?|incendie|s[ée]curit[ée]\s+incendie|maintenance\s+pr[ée]ventive|"
                r"ria|d[ée]senfumage|sparklet|afff)\b"
            ],
        ),
        ("616000", "assurance", [r"\b(assurance|multirisque|police|quittance|prime\s+h\.?\s*t)\b"]),
        (
            "626000",
            "telecom_ligne_technique",
            [r"\b(orange|ligne\s+fixe|contrat\s+professionnel|facture\s+ligne\s+fixe|telecom)\b"],
        ),
        ("615000", "ascenseur_maintenance", [r"\b(ascenseurs?|porte\s+cabine|contact\s+de\s+porte)\b"]),
        (
            "615000",
            "nettoyage_parties_communes",
            [r"\b(nettoyage|entretien\s+des\s+parties\s+communes|cages?\s+d[ '\u2019]?escaliers?)\b"],
        ),
        (
            "615000",
            "travaux_toiture",
            [r"\b(toiture|tuiles?|chapeau\s+de\s+chemin[Ã©e]e|mistral)\b"],
        ),
        ("615000", "entretien_maintenance", [r"\b(plomberie|chauffage|climatisation|robinet|wc|evacuation|pvc)\b"]),
        ("615000", "assainissement_degorgement", [r"\b(assainissement|degorgement|hydrocureur|eaux\s+usees|eaux\s+vannes)\b"]),
        (
            "615000",
            "entretien_maintenance",
            [
                r"\b(entretien|maintenance|nettoyage|ascenseur|jardin|[ée]lagage|abattage|d[ée]bitage|"
                r"d[ée]chetterie|r[ée]manents?|espaces?\s+verts?|pin|arbre|cogelec|interphone|"
                r"contr[ôo]le\s+d[' ]acc[eè]s|portail|badge|vigik)\b"
            ],
        ),
        ("622000", "honoraires_syndic", [r"\b(syndic|honoraire|gestion)\b"]),
        ("606100", "energie_eau", [r"\b(eau|[ée]lectric(?:it[ée])?|[ée]nergie|engie|gaz)\b"]),
        ("671000", "charges_exceptionnelles", [r"\b(sinistre|contentieux|expertise)\b"]),
    ]
    for account, family, patterns in rules:
        if any(re.search(pattern, haystack, flags=re.IGNORECASE) for pattern in patterns):
            return account, family
    return "615000", "charges_courantes_a_confirmer"


def _fire_safety_anomalies(text: str) -> list[str]:
    haystack = text.lower()
    if re.search(r"\bextincteurs?\b", haystack) and re.search(r"non\s+satisfaisant|[aà]\s+deviser|dlu\s+d[ée]pass", haystack):
        return ["SECURITE_INCENDIE_A_DEVISER"]
    return []


def _extract_invoice_from_evidence(evidence: DocumentExtractionEvidence) -> InvoiceExtraction:
    text = evidence.combined_text()
    if re.search(r"\bavis\s+d.{0,6}echeance\b|\bmultirisque\s+immeuble\b|\bN\S*\s+de\s+quittance\b", text, flags=re.IGNORECASE):
        return InsuranceNoticeProviderExtractor().extract(text, file_name=evidence.file_name)
    if re.search(r"\bomega\s+ascenseur\b", text, flags=re.IGNORECASE):
        return OmegaAscenseurInvoiceProviderExtractor().extract(text, file_name=evidence.file_name)
    if re.search(r"\borange\s+sa\b|\bpro\.orange\.fr\b|\bfacture\s+ligne\s+fixe\b", text, flags=re.IGNORECASE):
        return OrangeInvoiceProviderExtractor().extract(text, file_name=evidence.file_name)
    if re.search(r"\bcogelec\b", text, flags=re.IGNORECASE):
        return CogelecInvoiceProviderExtractor().extract(text, file_name=evidence.file_name)
    if re.search(r"\bprestations\s+du\s+mois\b", text, flags=re.IGNORECASE) and re.search(
        r"\bmontant\s+h\.?\s*t\s+tx\s+tva\s+tva\s+ttc\b",
        text,
        flags=re.IGNORECASE,
    ):
        return PhoceaInvoiceProviderExtractor().extract(text, file_name=evidence.file_name)
    return extract_generic_invoice_from_evidence(evidence)


def _load_configured_invoice_evidence(instance: InstanceConfig, year: int) -> list[dict[str, str]]:
    settings = _factureops_settings(instance)
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
                "evidence_level": normalize_intensity_level(row.get("evidence_level"), default="L0_STRUCTURED_SOURCE"),
            }
            rows.append(normalized)
    return rows


def _extract_invoice_rows(instance: InstanceConfig, year: int) -> list[dict[str, str]]:
    preloaded = _load_configured_invoice_evidence(instance, year)
    if preloaded:
        return preloaded

    invoices: list[dict[str, str]] = []
    seen_keys: Counter[str] = Counter()
    for row in _candidate_source_rows(instance):
        path = _resolve_source_path(instance, row)
        if path is None or not path.is_file():
            continue
        if not row.get("text_path") and (row.get("status_ocr") or "").upper() in {
            "PENDING",
            "OCR_REQUIRED",
            "EXTRACTION_ERROR",
            "SOURCE_MISSING",
            "UNSUPPORTED",
        }:
            continue
        evidence, method, evidence_level = _document_evidence(instance, row, path)
        text = evidence.combined_text()
        if not _looks_like_invoice(row, path, text, year):
            continue
        extraction = _extract_invoice_from_evidence(evidence)
        account, family = _account_for_invoice(text, extraction.fournisseur)
        anomalies = list(extraction.anomalies)
        anomalies.extend(_fire_safety_anomalies(text))
        if extraction.date_facture and str(year) not in extraction.date_facture:
            anomalies.append("FACTURE_HORS_EXERCICE")
        key = f"{extraction.fournisseur}|{extraction.numero_facture}|{extraction.ttc}"
        seen_keys[key] += 1
        if key.strip("|") and seen_keys[key] > 1:
            anomalies.append("DOUBLON_POTENTIEL")

        invoices.append(
            {
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
                "evidence_level": evidence_level,
            }
        )
    return invoices


def invoice_anomaly_rows(invoices: list[dict[str, str]], year: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    severities = {
        "FOURNISSEUR_ABSENT": "P0",
        "NUMERO_FACTURE_ABSENT": "P0",
        "DATE_FACTURE_ABSENTE": "P0",
        "MONTANT_TTC_ABSENT": "P0",
        "SIREN_SIRET_ABSENT": "P1",
    }
    for invoice in invoices:
        anomalies = [item for item in invoice.get("anomalies", "").split("|") if item]
        for anomaly in anomalies:
            rows.append(
                {
                    "anomaly_id": f"INV-{year}-{invoice.get('doc_id', '')}-{anomaly}",
                    "exercice": str(year),
                    "severity": severities.get(anomaly, "P1"),
                    "status": "A_TRAITER",
                    "doc_id": invoice.get("doc_id", ""),
                    "fournisseur": invoice.get("fournisseur", ""),
                    "numero_facture": invoice.get("numero_facture", ""),
                    "ttc": invoice.get("ttc", ""),
                    "anomaly": anomaly,
                    "evidence_level": invoice.get("evidence_level", ""),
                    "extraction_method": invoice.get("extraction_method", ""),
                    "evidence": invoice.get("source_path", ""),
                    "action": "Verifier la piece et completer la donnee manquante.",
                }
            )
    return rows


def extract_invoices(instance: InstanceConfig, run: RunContext, year: int) -> dict[str, object]:
    accounting_dir = instance.artifact("accounting_dir") / str(year)
    accounting_dir.mkdir(parents=True, exist_ok=True)
    invoices = _extract_invoice_rows(instance, year)
    anomalies = invoice_anomaly_rows(invoices, year)
    invoice_path = accounting_dir / f"invoice_evidence_{year}.csv"
    anomaly_path = accounting_dir / f"invoice_anomalies_{year}.csv"
    write_csv(invoice_path, INVOICE_EVIDENCE_FIELDS, invoices)
    write_csv(anomaly_path, INVOICE_ANOMALY_FIELDS, anomalies)
    summary = {
        "status": "ok",
        "year": year,
        "invoice_count": len(invoices),
        "invoice_anomaly_count": len(anomalies),
        "invoice_evidence": str(invoice_path),
        "invoice_anomalies": str(anomaly_path),
        "evidence_level_counts": dict(Counter(row.get("evidence_level", "") for row in invoices)),
    }
    run.log_action("factureops_extract", accounting_dir, f"year={year}; invoices={len(invoices)}")
    return summary


def required_invoice_paths(instance: InstanceConfig, year: int) -> list[Path]:
    accounting_dir = instance.artifact("accounting_dir") / str(year)
    return [
        accounting_dir / f"invoice_evidence_{year}.csv",
        accounting_dir / f"invoice_anomalies_{year}.csv",
    ]


def ensure_invoice_outputs(instance: InstanceConfig, run: RunContext, year: int) -> dict[str, object] | None:
    missing = [path for path in required_invoice_paths(instance, year) if not path.exists()]
    if missing:
        return extract_invoices(instance, run, year)
    return None
