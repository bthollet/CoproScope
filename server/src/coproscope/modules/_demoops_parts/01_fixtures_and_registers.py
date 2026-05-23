from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from ..core.common import (
    AG_FIELDS,
    DEFAULT_DOCUMENT_FIELDS,
    FINDING_FIELDS,
    REQUEST_FIELDS,
    InstanceConfig,
    RunContext,
    now_iso,
    read_csv,
    relative_to,
    sha256_file,
    write_csv,
    write_text,
)
from . import biffageops, privacyops


DEMO_NAME = "Residence Les Tilleuls"
DEMO_ID = "demo-fictive-tilleuls"


RAW_DOCS = {
    "2025-01-18_facture_entretien_jardin.txt": """Facture DEMO-JAR-2025-001
Fournisseur: Jardins des Tilleuls Services
Objet: entretien mensuel des espaces verts
Montant TTC: 1280.00 EUR
Statut: facture fictive produite pour demonstration CoproScope.
""",
    "2025-12-31_annexe_comptable.txt": """Annexe comptable synthetique 2025
Charges entretien: 1280.00 EUR
Charges ascenseur: 1840.00 EUR
Charges nettoyage: 960.00 EUR
Cette piece est fictive et ne correspond a aucune copropriete reelle.
""",
    "2026-02-10_demande_pieces_syndic.txt": """Demande au syndic
Sujet: obtenir les attestations assurance et les devis comparatifs.
Statut: relance a preparer avant la prochaine reunion du conseil syndical.
""",
    "2026-03-12_devis_reprise_etancheite.txt": """Devis fictif de reprise d'etancheite
Entreprise: Atelier Toiture Demo
Montant TTC: 14600.00 EUR
Pieces attendues: assurance, qualification, planning, conditions de reception.
""",
    "2026-04-20_convocation_ag.txt": """Convocation assemblee generale fictive
Points: approbation comptes, budget previsionnel, travaux etancheite, contrat nettoyage.
Annexes attendues: devis, rapport conseil syndical, tableau de suivi des decisions.
""",
    "2026-05-03_incident_portail.txt": """Signalement incident fictif
Objet: portail bloque en position ouverte.
Suite attendue: intervention prestataire, preuve de cloture, verification contrat.
""",
}


def _json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=True) + "\n")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _source_accounting_dir(source: InstanceConfig, year: int) -> Path:
    primary = source.artifact("accounting_dir") / str(year)
    try:
        outputs = source.root("outputs")
    except KeyError:
        return primary
    candidates = [
        primary,
        outputs / f"accounting_{year}_factures",
    ]
    for candidate in candidates:
        if (candidate / f"summary_{year}.json").exists() or (candidate / f"summary_{year}_controlled.json").exists():
            return candidate
    return primary


def _bucket(value: Any) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return "non disponible"
    if number == 0:
        return "0"
    if number <= 10:
        return "1-10"
    if number <= 50:
        return "11-50"
    if number <= 200:
        return "51-200"
    if number <= 500:
        return "201-500"
    return "500+"


def _demo_count(value: Any, floor: int, ceiling: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return floor
    if number <= 0:
        return floor
    derived = int(math.sqrt(number) * 5)
    return max(floor, min(ceiling, derived))


def _source_profile(source: InstanceConfig, year: int) -> tuple[dict[str, str], dict[str, Any]]:
    base = _source_accounting_dir(source, year)
    summary = _read_json(base / f"summary_{year}_controlled.json") or _read_json(base / f"summary_{year}.json")
    profile = {
        "invoice_count_bucket": _bucket(summary.get("invoice_count")),
        "control_count_bucket": _bucket(summary.get("control_count")),
        "invoice_anomaly_count_bucket": _bucket(summary.get("invoice_anomaly_count")),
        "statement_line_count_bucket": _bucket(summary.get("expense_statement_line_count")),
    }
    return profile, summary


def _fields_from(path: Path, fallback: list[str]) -> list[str]:
    fields, _ = read_csv(path)
    return fields or fallback


def _project(fields: list[str], rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{field: row.get(field, "") for field in fields} for row in rows]


def _write_raw_docs(instance_dir: Path) -> list[dict[str, str]]:
    raw_dir = instance_dir / "raw"
    rows: list[dict[str, str]] = []
    now = now_iso()
    for index, (file_name, content) in enumerate(RAW_DOCS.items(), start=1):
        path = raw_dir / file_name
        write_text(path, content)
        digest = sha256_file(path)
        doc_id = f"DEMO-DOC-{index:03d}"
        row = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        row.update(
            {
                "doc_id": doc_id,
                "instance_id": DEMO_ID,
                "entity_id": "main",
                "scope": "copro_demo_fictive",
                "sha256": digest,
                "original_path": relative_to(instance_dir, path),
                "file_name": file_name,
                "extension": path.suffix.lower().lstrip("."),
                "size_bytes": str(path.stat().st_size),
                "last_modified": now,
                "first_seen": now,
                "source_zone": "raw",
                "source_kind": "demo_fictive_generated",
                "document_type": _document_type_for(file_name),
                "suspected_date": file_name[:10],
                "status_ocr": "NATIVE_TEXT",
                "classification_status": "DEMO_CLASSIFIED",
                "text_path": relative_to(instance_dir, path),
                "text_quality": "synthetic",
                "raw_max_college": "C0_Public",
                "derivative_max_college": "C0_Public",
                "publication_form": "raw",
                "personal_data_level": "none",
                "ip_status": "synthetic_public",
                "ai_processing_ceiling": "local_only",
                "privacy_review_status": "DEMO_FICTIVE",
                "notes": "Document fictif genere pour demonstration publique.",
            }
        )
        rows.append(row)
    return rows


def _document_type_for(file_name: str) -> str:
    lower = file_name.lower()
    if "facture" in lower:
        return "Facture"
    if "annexe_comptable" in lower:
        return "Annexe_Comptable"
    if "demande" in lower:
        return "Demande_Syndic"
    if "devis" in lower:
        return "Devis"
    if "convocation" in lower:
        return "Convocation_AG"
    if "incident" in lower:
        return "Incident"
    return "Document"


def _write_registers(instance_dir: Path, docs: list[dict[str, str]]) -> None:
    registers = instance_dir / "registers"
    write_csv(registers / "registre_documents.csv", DEFAULT_DOCUMENT_FIELDS, docs)
    write_csv(
        registers / "registre_doublons.csv",
        ["sha256", "count", "doc_ids", "paths"],
        [],
    )
    write_csv(
        registers / "manifest_sha256.csv",
        ["doc_id", "sha256", "original_path", "file_name", "size_bytes", "source_kind"],
        [
            {
                "doc_id": row["doc_id"],
                "sha256": row["sha256"],
                "original_path": row["original_path"],
                "file_name": row["file_name"],
                "size_bytes": row["size_bytes"],
                "source_kind": row["source_kind"],
            }
            for row in docs
        ],
    )
    write_csv(
        registers / "registre_demandes.csv",
        REQUEST_FIELDS,
        [
            {
                "request_id": "REQ-DEMO-001",
                "date": "2026-02-10",
                "subject": "Pieces assurance et devis comparatifs",
                "expected_piece": "Attestations assurance, devis, planning",
                "status": "A_RELANCER",
                "last_follow_up": "2026-02-24",
                "priority": "P1",
                "response_due_date": "2026-03-05",
                "source_document": "DEMO-DOC-003",
                "related_doc_ids": "DEMO-DOC-004",
                "notes": "Cas fictif representatif d'une relance syndic.",
            }
        ],
    )
    write_csv(
        registers / "registre_ag.csv",
        AG_FIELDS,
        [
            {
                "ag_id": "AG-DEMO-2026-001",
                "doc_id": "DEMO-DOC-005",
                "file_name": "2026-04-20_convocation_ag.txt",
                "document_type": "Convocation_AG",
                "detected_date": "2026-04-20",
                "resolution_count": "4",
                "annex_hits": "devis;budget;rapport_cs",
                "majority_terms": "article 24;article 25",
                "missing_annex_signals": "tableau_suivi_decisions",
                "notes": "AG fictive pour tester le parcours decision-action-preuve.",
            }
        ],
    )
    write_csv(
        registers / "constats_diligences.csv",
        FINDING_FIELDS,
        [
            {
                "finding_id": "FIND-DEMO-001",
                "category": "comptes",
                "severity": "P1",
                "source_ref": "DEMO-DOC-002",
                "fact": "Une ligne de charge demande un rapprochement explicite.",
                "diligence": "Preparer une question au syndic avec piece attendue.",
                "status": "A_TRAITER",
            },
            {
                "finding_id": "FIND-DEMO-002",
                "category": "travaux",
                "severity": "P2",
                "source_ref": "DEMO-DOC-004",
                "fact": "Un devis travaux attend ses pieces administratives.",
                "diligence": "Demander assurance et calendrier.",
                "status": "A_RELANCER",
            },
        ],
    )
    write_csv(
        registers / "kpi.csv",
        ["kpi_id", "theme", "label", "definition", "source", "type", "value", "notes"],
        [
            {
                "kpi_id": "KPI-DEMO-001",
                "theme": "Documents",
                "label": "Documents demo",
                "definition": "Nombre de documents fictifs generes",
                "source": "registre_documents",
                "type": "COUNT",
                "value": str(len(docs)),
                "notes": "Jeu public fictif.",
            }
        ],
    )
