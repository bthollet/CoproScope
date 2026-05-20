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


def _write_accounting_outputs(source: InstanceConfig, instance_dir: Path, year: int, source_summary: dict[str, Any]) -> None:
    source_base = _source_accounting_dir(source, year)
    accounting_dir = instance_dir / "outputs" / "accounting" / str(year)
    invoice_count = _demo_count(source_summary.get("invoice_count"), 6, 96)
    control_count = _demo_count(source_summary.get("control_count"), 4, 36)
    anomaly_count = _demo_count(source_summary.get("invoice_anomaly_count"), 3, 48)
    statement_count = _demo_count(source_summary.get("expense_statement_line_count"), 8, 120)

    invoice_fields = _fields_from(
        source_base / f"invoice_evidence_{year}.csv",
        ["doc_id", "exercice", "fournisseur", "numero_facture", "date_facture", "ttc", "compte_propose", "famille_charge", "statut_controle", "confidence", "evidence_level"],
    )
    invoices = [
        {
            "doc_id": f"DEMO-FAC-{index:03d}",
            "exercice": str(year),
            "fournisseur": ["JARDINS DES TILLEULS SERVICES", "ATELIER TOITURE DEMO", "NETTOYAGE HORIZON"][index % 3],
            "numero_facture": f"DEMO-{year}-{index:03d}",
            "date_facture": f"{year}-{(index % 9) + 1:02d}-15",
            "ttc": f"{850 + index * 37:.2f}",
            "compte_propose": "615000",
            "famille_charge": "entretien_maintenance",
            "statut_controle": "PROBABLE",
            "confidence": "demo_fictive",
            "evidence_level": "L1_SYNTHETIC_TEXT",
            "source_register": "demo_fictive",
        }
        for index in range(1, min(invoice_count, 18) + 1)
    ]
    write_csv(accounting_dir / f"invoice_evidence_{year}.csv", invoice_fields, _project(invoice_fields, invoices))

    control_fields = _fields_from(
        source_base / f"accounting_controls_{year}.csv",
        ["control_id", "exercice", "severity", "control", "status", "doc_id", "evidence", "action"],
    )
    controls = [
        {
            "control_id": f"CTL-DEMO-{index:03d}",
            "exercice": str(year),
            "severity": "P1" if index in {1, 2} else "P2",
            "control": [
                "Rapprocher facture et etat des depenses",
                "Verifier piece administrative fournisseur",
                "Confirmer ventilation de charge",
                "Preparer question AG",
            ][index % 4],
            "status": "A_TRAITER" if index in {1, 2} else "A_CONFIRMER",
            "doc_id": f"DEMO-FAC-{index:03d}",
            "evidence": "Piece fictive et ligne comptable synthetique",
            "action": "Preparer une question au syndic avec piece attendue.",
        }
        for index in range(1, min(control_count, 12) + 1)
    ]
    write_csv(accounting_dir / f"accounting_controls_{year}.csv", control_fields, _project(control_fields, controls))

    non_match_fields = _fields_from(
        source_base / f"non_rapproches_prioritaires_{year}.csv",
        ["doc_id", "fournisseur", "numero_facture", "ttc", "match_status", "match_priority", "status_label", "match_reason", "next_action"],
    )
    non_matches = [
        {
            "doc_id": "DEMO-FAC-001",
            "fournisseur": "ATELIER TOITURE DEMO",
            "numero_facture": f"DEMO-{year}-001",
            "ttc": "14600.00",
            "match_status": "CANDIDAT_REFERENCE_AMBIGUE",
            "match_priority": "P1",
            "status_label": "Question syndic",
            "match_reason": "La reference comptable ne suffit pas pour rattacher la piece au bon poste.",
            "next_action": "Demander le detail de ligne et la piece justificative associee.",
        },
        {
            "doc_id": "DEMO-FAC-002",
            "fournisseur": "NETTOYAGE HORIZON",
            "numero_facture": f"DEMO-{year}-002",
            "ttc": "960.00",
            "match_status": "CANDIDAT_MONTANT_AMBIGU",
            "match_priority": "P2",
            "status_label": "A confirmer",
            "match_reason": "Plusieurs lignes proches existent dans l'etat de depenses fictif.",
            "next_action": "Confirmer le rattachement avant AG.",
        },
    ]
    write_csv(accounting_dir / f"non_rapproches_prioritaires_{year}.csv", non_match_fields, _project(non_match_fields, non_matches))

    match_fields = _fields_from(
        source_base / f"invoice_expense_matches_{year}.csv",
        ["doc_id", "statement_line_id", "match_status", "match_priority", "match_reason", "next_action"],
    )
    matches = [
        {
            "doc_id": f"DEMO-FAC-{index:03d}",
            "statement_line_id": f"DEP-DEMO-{index:03d}",
            "match_status": "MATCH_AMOUNT_SUPPLIER" if index % 3 else "CANDIDAT_MONTANT_AMBIGU",
            "match_priority": "OK" if index % 3 else "P2",
            "match_reason": "Rapprochement fictif coherent avec l'etat de depenses.",
            "next_action": "Conserver comme preuve candidate.",
        }
        for index in range(1, min(invoice_count, 18) + 1)
    ]
    write_csv(accounting_dir / f"invoice_expense_matches_{year}.csv", match_fields, _project(match_fields, matches))

    anomaly_fields = _fields_from(
        source_base / f"invoice_anomalies_{year}.csv",
        ["doc_id", "anomaly", "severity", "message", "next_action"],
    )
    anomalies = [
        {
            "doc_id": f"DEMO-FAC-{(index % 6) + 1:03d}",
            "anomaly": "PIECE_A_CONFIRMER",
            "severity": "P2",
            "message": "Anomalie fictive pour tester la lecture guidee.",
            "next_action": "Verifier la piece avant restitution.",
        }
        for index in range(1, min(anomaly_count, 12) + 1)
    ]
    write_csv(accounting_dir / f"invoice_anomalies_{year}.csv", anomaly_fields, _project(anomaly_fields, anomalies))

    expense_fields = _fields_from(
        source_base / f"expense_statement_lines_{year}.csv",
        ["statement_line_id", "exercice", "account", "label", "amount", "supplier_hint"],
    )
    expenses = [
        {
            "statement_line_id": f"DEP-DEMO-{index:03d}",
            "exercice": str(year),
            "account": "615000",
            "label": f"Ligne de charge fictive {index:03d}",
            "amount": f"{850 + index * 37:.2f}",
            "supplier_hint": ["JARDINS", "TOITURE", "NETTOYAGE"][index % 3],
        }
        for index in range(1, min(statement_count, 24) + 1)
    ]
    write_csv(accounting_dir / f"expense_statement_lines_{year}.csv", expense_fields, _project(expense_fields, expenses))

    ledger_fields = _fields_from(
        source_base / f"ledger_reconstruction_{year}.csv",
        ["entry_id", "doc_id", "exercice", "account", "label", "debit", "credit", "source"],
    )
    ledger = [
        {
            "entry_id": f"LED-DEMO-{index:03d}",
            "doc_id": f"DEMO-FAC-{index:03d}",
            "exercice": str(year),
            "account": "615000",
            "label": f"Ecriture candidate fictive {index:03d}",
            "debit": f"{850 + index * 37:.2f}",
            "credit": "0.00",
            "source": "demo_fictive",
        }
        for index in range(1, min(invoice_count, 18) + 1)
    ]
    write_csv(accounting_dir / f"ledger_reconstruction_{year}.csv", ledger_fields, _project(ledger_fields, ledger))

    alias_fields = _fields_from(
        source_base / f"supplier_alias_suggestions_{year}.csv",
        ["supplier", "suggested_alias", "evidence_count", "suggestion_status", "next_action"],
    )
    write_csv(
        accounting_dir / f"supplier_alias_suggestions_{year}.csv",
        alias_fields,
        _project(
            alias_fields,
            [
                {
                    "supplier": "JARDINS DES TILLEULS SERVICES",
                    "suggested_alias": "JARDINS TILLEULS",
                    "evidence_count": "3",
                    "suggestion_status": "A_CONFIRMER",
                    "next_action": "Ajouter l'alias si le CS valide le rapprochement.",
                }
            ],
        ),
    )

    due_fields = _fields_from(
        source_base / f"supplier_due_diligence_controls_{year}.csv",
        ["fournisseur", "coverage_status", "controls_to_apply", "existing_result_refs", "next_action"],
    )
    write_csv(
        accounting_dir / f"supplier_due_diligence_controls_{year}.csv",
        due_fields,
        _project(
            due_fields,
            [
                {
                    "fournisseur": "ATELIER TOITURE DEMO",
                    "coverage_status": "A_TRAITER_METHODO_EXISTANTE",
                    "controls_to_apply": "Assurance;qualification;identite juridique",
                    "existing_result_refs": "",
                    "next_action": "Demander les pieces avant engagement.",
                }
            ],
        ),
    )

    summary = {
        "status": "ok",
        "mode": "demo_fictive",
        "year": year,
        "invoice_count": invoice_count,
        "entry_count": min(invoice_count, 18),
        "control_count": control_count,
        "invoice_anomaly_count": anomaly_count,
        "expense_statement_line_count": statement_count,
        "expense_match_counts": {
            "MATCH_AMOUNT_SUPPLIER": max(1, invoice_count - 4),
            "CANDIDAT_MONTANT_AMBIGU": 3,
            "CANDIDAT_REFERENCE_AMBIGUE": 1,
        },
        "publication_note": "Jeu fictif derive par generalisation, sans copie de lignes privees.",
    }
    _json(accounting_dir / f"summary_{year}.json", summary)
    write_text(
        accounting_dir / f"rapport_comptascope_{year}.md",
        "\n".join(
            [
                "# Rapport ComptaScope demo",
                "",
                "Ce rapport est entierement fictif. Il sert a tester l'interface cible sans publier de donnees reelles.",
                "",
                "## Lecture rapide",
                "",
                "- Des rapprochements `OK` montrent la chaine preuve -> controle.",
                "- Des candidats `P2` montrent les confirmations attendues.",
                "- Des `P1` montrent les questions a preparer au syndic.",
                "",
                "## Point prioritaire",
                "",
                "Demander le detail de la ligne travaux et la piece justificative associee.",
            ]
        )
        + "\n",
    )


def _write_reports(instance_dir: Path, year: int, profile: dict[str, str], validation: dict[str, str]) -> None:
    reports = instance_dir / "outputs" / "reports"
    write_text(
        reports / "rapport_completude_documentaire.md",
        "\n".join(
            [
                "# Rapport de completude documentaire demo",
                "",
                "Instance fictive produite pour tester le cockpit CoproScope.",
                "",
                "- Documents presents: facture, annexe comptable, demande syndic, devis, AG, incident.",
                "- Pieces a demander: assurance prestataire, calendrier travaux, preuve de cloture incident.",
            ]
        )
        + "\n",
    )
    write_text(
        reports / "rapport_ag_preparation.md",
        "\n".join(
            [
                "# Rapport AG demo",
                "",
                "- Resolution travaux a relier a une action suivie.",
                "- Annexes a verifier avant diffusion.",
                "- Questions au syndic a preparer depuis ComptaScope.",
            ]
        )
        + "\n",
    )
    demo_dir = instance_dir / "outputs" / "demo"
    write_text(
        demo_dir / "rapport_validation_publication.md",
        "\n".join(
            [
                "# Rapport de validation publication",
                "",
                "## Statut",
                "",
                f"- Decision: {validation['decision']}",
                f"- Individualisation: {validation['individualisation']}",
                f"- Correlation: {validation['correlation']}",
                f"- Inference: {validation['inference']}",
                "",
                "## Source privee",
                "",
                "Les volumes sources ont ete generalises avant generation de la demo.",
                "",
                "| Signal | Niveau generalise |",
                "| --- | --- |",
                *[f"| {key} | {value} |" for key, value in profile.items()],
                "",
                "## Regle",
                "",
                "Une pseudonymisation tracee n'est pas consideree comme une publication suffisante. Cette instance publie une copro fictive.",
            ]
        )
        + "\n",
    )


def _write_instance_config(instance_dir: Path) -> Path:
    payload = {
        "version": 1,
        "instance_id": DEMO_ID,
        "display_name": DEMO_NAME,
        "scope": "copro_demo_fictive",
        "entity_id": "main",
        "roots": {
            "workspace": ".",
            "raw": "./raw",
            "system": "./system",
            "outputs": "./outputs",
            "staging": "./staging",
            "logs": "./logs",
            "restricted": ["./restricted/C8_local_only"],
        },
        "registers": {
            "documents": "./registers/registre_documents.csv",
            "duplicates": "./registers/registre_doublons.csv",
            "manifest": "./registers/manifest_sha256.csv",
            "requests": "./registers/registre_demandes.csv",
            "ag": "./registers/registre_ag.csv",
            "findings": "./registers/constats_diligences.csv",
            "kpi": "./registers/kpi.csv",
            "privacy_screening": "./outputs/privacy/registre_screening_confidentialite.csv",
            "redactions": "./outputs/privacy/registre_biffages.csv",
            "redaction_map": "./restricted/C8_local_only/table_correspondance_biffage.csv",
        },
        "matrices": {
            "proofs": "./system/matrices/matrice_preuves_attendues.csv",
            "extranet": "./system/matrices/matrice_conformite_extranet.csv",
            "due_diligence_dir": "./system/due_diligence",
        },
        "artifacts": {
            "text_dir": "./staging/text",
            "classified_dir": "./staging/classified",
            "reports_dir": "./outputs/reports",
            "docai_dir": "./staging/docai",
            "accounting_dir": "./outputs/accounting",
            "grist_dir": "./outputs/grist",
            "evidence_dir": "./outputs/evidence",
            "privacy_dir": "./outputs/privacy",
            "redacted_dir": "./outputs/redacted",
        },
        "env": {"files": ["./.env.local"], "required": [], "optional": []},
        "settings": {
            "never_modify_raw": True,
            "write_outputs_only": True,
            "demo_publication": {
                "mode": "fictive",
                "source_private_content_copied": False,
                "pseudonymization_only_is_publishable": False,
            },
        },
    }
    path = instance_dir / "instance.yml"
    _json(path, payload)
    return path


def _write_support_files(instance_dir: Path) -> None:
    write_text(
        instance_dir / ".gitignore",
        "\n".join(
            [
                ".env.local",
                "logs/",
                "restricted/",
                "**/table_correspondance*",
                "**/*mapping*",
                "",
            ]
        ),
    )
    matrices = instance_dir / "system" / "matrices"
    write_csv(
        matrices / "matrice_preuves_attendues.csv",
        ["proof_id", "theme", "piece_attendue", "raison", "priorite"],
        [
            {
                "proof_id": "PROOF-DEMO-001",
                "theme": "Travaux",
                "piece_attendue": "Attestation assurance",
                "raison": "Verifier la couverture avant reception.",
                "priorite": "P1",
            }
        ],
    )
    write_csv(
        matrices / "matrice_conformite_extranet.csv",
        ["item_id", "piece", "status", "action"],
        [
            {
                "item_id": "EXT-DEMO-001",
                "piece": "Devis travaux",
                "status": "A_COMPLETER",
                "action": "Demander les annexes manquantes.",
            }
        ],
    )


def _validate_generated_instance(instance_dir: Path) -> dict[str, str]:
    forbidden = re.compile(r"\b(beauvallon|pinede|pin[eè]de)\b", flags=re.IGNORECASE)
    direct_identifier = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|\bFR\d{2}(?:[\s-]?[A-Z0-9]){11,30}\b",
        flags=re.IGNORECASE,
    )
    scanned = 0
    blocked = False
    for path in sorted(instance_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part in {"restricted", "logs"} for part in path.parts):
            continue
        if path.suffix.lower() not in {".txt", ".md", ".csv", ".json", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        scanned += 1
        if forbidden.search(text) or direct_identifier.search(text):
            blocked = True
            break
    if blocked:
        return {
            "decision": "BLOCKED_REVIEW_REQUIRED",
            "individualisation": "A_REVOIR",
            "correlation": "A_REVOIR",
            "inference": "A_REVOIR",
            "scanned_files": str(scanned),
        }
    return {
        "decision": "APPROVED_FICTIVE_DEMO",
        "individualisation": "OK_GENERALISE",
        "correlation": "OK_IDENTITES_REMPLACEES",
        "inference": "OK_MONTANTS_DATES_FICTIFS",
        "scanned_files": str(scanned),
    }


def _run_source_audit(source: InstanceConfig, run: RunContext, max_text_chars: int) -> dict[str, object]:
    result: dict[str, object] = {"status": "not_run"}
    try:
        privacy_result = privacyops.screen_existing(
            source,
            run,
            include_generated=False,
            max_text_chars=max_text_chars,
            prune_unseen=True,
        )
        queue_result = biffageops.build_redaction_queue(source, run)
        result = {
            "status": "ok",
            "screened_count": privacy_result.get("screened_count", 0),
            "priority_counts": privacy_result.get("priority_counts", {}),
            "queued_count": queue_result.get("queued_count", 0),
            "queue_status_counts": queue_result.get("status_counts", {}),
            "publication_note": "Audit source execute localement; aucune ligne source n'est copiee dans la demo.",
        }
    except Exception as exc:  # noqa: BLE001
        result = {
            "status": "warning",
            "warning": str(exc),
            "publication_note": "La demo peut etre generee, mais l'audit source doit etre repris avant publication externe.",
        }
    return result


def build_demo_instance(
    source: InstanceConfig,
    run: RunContext,
    *,
    output_instance: Path,
    mode: str = "fictive",
    year: int = 2025,
    run_source_audit: bool = True,
    max_text_chars: int = 12000,
) -> dict[str, object]:
    if mode != "fictive":
        raise ValueError("Only mode='fictive' is supported for publishable demos.")

    instance_dir = output_instance
    if instance_dir.suffix.lower() in {".yml", ".yaml", ".json"}:
        instance_dir = instance_dir.parent
    instance_dir = instance_dir.resolve()
    instance_dir.mkdir(parents=True, exist_ok=True)

    source_audit = _run_source_audit(source, run, max_text_chars) if run_source_audit else {
        "status": "skipped",
        "publication_note": "Audit source non execute pour cette generation.",
    }
    profile, source_summary = _source_profile(source, year)
    _write_support_files(instance_dir)
    docs = _write_raw_docs(instance_dir)
    _write_registers(instance_dir, docs)
    instance_path = _write_instance_config(instance_dir)
    _write_accounting_outputs(source, instance_dir, year, source_summary)

    validation = _validate_generated_instance(instance_dir)
    _write_reports(instance_dir, year, profile, validation)
    demo_instance_payload = {
        "mode": "fictive",
        "created_at": now_iso(),
        "demo_instance_id": DEMO_ID,
        "source_profile": profile,
        "source_audit": source_audit,
        "publication_validation": validation,
        "private_content_copied": False,
        "pseudonymization_only_publishable": False,
        "cnil_checks": ["individualisation", "correlation", "inference"],
    }
    _json(instance_dir / "demo_manifest.json", demo_instance_payload)
    _json(instance_dir / "outputs" / "demo" / "manifest_publication.json", demo_instance_payload)

    demo_instance = InstanceConfig(path=instance_path, payload=json.loads(instance_path.read_text(encoding="utf-8")))
    demo_run = RunContext(demo_instance, "demo privacy validation")
    privacyops.screen_existing(demo_instance, demo_run, include_generated=True, max_text_chars=max_text_chars)
    biffageops.build_redaction_queue(demo_instance, demo_run)
    demo_run.finish("OK", "demo privacy validation complete")

    run.log_action("demo_build", instance_path, f"mode={mode}; year={year}; decision={validation['decision']}")
    return {
        "status": "ok" if validation["decision"].startswith("APPROVED") else "review_required",
        "instance": str(instance_path),
        "instance_root": str(instance_dir),
        "mode": mode,
        "year": year,
        "source_audit": source_audit,
        "publication_validation": validation,
        "manifest": str(instance_dir / "demo_manifest.json"),
    }
