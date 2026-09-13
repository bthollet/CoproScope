from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from ..core.common import InstanceConfig, RunContext, detect_date, read_csv, relative_to, write_csv, write_text


INCIDENT_FIELDS = [
    "incident_id",
    "date_signalement",
    "lieu",
    "description",
    "piece_ref",
    "doc_ids",
    "photo_or_piece",
    "syndic_or_provider",
    "status",
    "priority",
    "next_action",
    "action_due_date",
    "expected_closure_proof",
    "closure_proof_ref",
    "contract_or_insurance_ref",
    "source_refs",
    "notes",
]

OPEN_STATUSES = {
    "NOUVEAU",
    "A_QUALIFIER",
    "EN_COURS",
    "EN_RELANCE",
    "EN_ATTENTE_PREUVE",
    "A_CLOTURER",
}
CLOSED_STATUSES = {"CLOTURE", "SANS_SUITE"}
ALL_STATUSES = OPEN_STATUSES | CLOSED_STATUSES
STATUS_ALIASES = {
    "OPEN": "NOUVEAU",
    "OUVERT": "NOUVEAU",
    "A_TRAITER": "A_QUALIFIER",
    "A_QUALIFIER": "A_QUALIFIER",
    "QUALIFICATION": "A_QUALIFIER",
    "IN_PROGRESS": "EN_COURS",
    "EN_COURS": "EN_COURS",
    "RELANCE": "EN_RELANCE",
    "EN_RELANCE": "EN_RELANCE",
    "WAITING_PROOF": "EN_ATTENTE_PREUVE",
    "EN_ATTENTE_PREUVE": "EN_ATTENTE_PREUVE",
    "A_CLOTURER": "A_CLOTURER",
    "CLOSED": "CLOTURE",
    "CLOTURE": "CLOTURE",
    "CLOTUREE": "CLOTURE",
    "SANS_SUITE": "SANS_SUITE",
}

INCIDENT_KEYWORDS = {
    "incident",
    "sinistre",
    "fuite",
    "infiltration",
    "degat",
    "degats",
    "panne",
    "urgence",
    "reparation",
    "declaration",
    "expertise",
}
INSURANCE_KEYWORDS = {"assurance", "assureur", "sinistre", "declaration", "expertise"}
PROVIDER_KEYWORDS = {"intervention", "reparation", "maintenance", "prestataire", "entreprise"}


def incident_register_path(instance: InstanceConfig) -> Path:
    try:
        return instance.register("incidents")
    except KeyError:
        return instance.instance_root / "registers" / "registre_incidents.csv"


def incident_reports_dir(instance: InstanceConfig) -> Path:
    return instance.artifact("reports_dir") / "incidentops"


def normalize_status(value: str | None) -> str:
    raw = re.sub(r"[^A-Z0-9]+", "_", (value or "").strip().upper()).strip("_")
    if not raw:
        return "NOUVEAU"
    return STATUS_ALIASES.get(raw, raw if raw in ALL_STATUSES else "NOUVEAU")


def is_open_incident(row: dict[str, str]) -> bool:
    return normalize_status(row.get("status")) in OPEN_STATUSES


def _ascii_fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii").casefold()


def _search_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _ascii_fold(value)).strip()


def _keyword_matches(text: str, keyword: str) -> bool:
    normalized = _search_text(keyword or "")
    if not normalized:
        return False
    haystack = _search_text(text)
    pattern = re.escape(normalized).replace(r"\ ", r"\s+")
    if " " not in normalized and len(normalized) > 4 and not normalized.endswith("s"):
        pattern = f"{pattern}s?"
    return re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", haystack, flags=re.IGNORECASE) is not None


def _has_keyword(text: str, keywords: Iterable[str]) -> bool:
    return any(_keyword_matches(text, keyword) for keyword in keywords)


def _cell(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _stable_incident_id(row: dict[str, str]) -> str:
    source = "|".join(
        _cell(row.get(field))
        for field in ["date_signalement", "lieu", "description", "piece_ref", "doc_ids", "source_refs"]
    )
    digest = hashlib.sha256((source or "incident").encode("utf-8")).hexdigest()
    return f"INC-{digest[:10].upper()}"


def _parse_date(value: str) -> datetime | None:
    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _default_due_date(row: dict[str, str], days: int) -> str:
    base = _parse_date(row.get("date_signalement", ""))
    if base is None:
        return ""
    return (base + timedelta(days=days)).strftime("%Y-%m-%d")


def _haystack(row: dict[str, str]) -> str:
    return _ascii_fold(
        " ".join(
            [
                row.get("description", ""),
                row.get("piece_ref", ""),
                row.get("photo_or_piece", ""),
                row.get("contract_or_insurance_ref", ""),
                row.get("source_refs", ""),
                row.get("notes", ""),
            ]
        )
    )


def _default_priority(row: dict[str, str]) -> str:
    haystack = _haystack(row)
    if _has_keyword(haystack, ["urgence", "securite", "sinistre", "degat", "fuite"]):
        return "P1"
    return "P2"


def _default_expected_proof(row: dict[str, str]) -> str:
    haystack = _haystack(row)
    if _has_keyword(haystack, INSURANCE_KEYWORDS):
        return "Numero de dossier, courrier assureur ou accord de prise en charge."
    if row.get("syndic_or_provider") or _has_keyword(haystack, PROVIDER_KEYWORDS):
        return "Bon d'intervention, facture ou photo apres intervention."
    return "Photo apres resolution ou confirmation ecrite du syndic."


def _default_next_action(row: dict[str, str]) -> str:
    status = normalize_status(row.get("status"))
    if status == "NOUVEAU":
        return "Qualifier le lieu, la piece source et l'acteur responsable."
    if status == "A_QUALIFIER":
        return "Identifier syndic/prestataire, assurance eventuelle et preuve attendue."
    if status == "EN_COURS":
        target = row.get("syndic_or_provider") or "syndic"
        return f"Relancer {target} sur la date d'intervention et la preuve de resolution."
    if status == "EN_RELANCE":
        return "Relancer avec echeance explicite et demander une trace ecrite."
    if status in {"EN_ATTENTE_PREUVE", "A_CLOTURER"}:
        return "Obtenir la preuve de cloture avant passage en CLOTURE."
    return ""


def normalize_incident(row: dict[str, str]) -> dict[str, str]:
    normalized = {field: _cell(row.get(field, "")) for field in INCIDENT_FIELDS}
    normalized["status"] = normalize_status(normalized.get("status"))
    if not normalized["date_signalement"]:
        normalized["date_signalement"] = detect_date(
            " ".join([normalized.get("piece_ref", ""), normalized.get("source_refs", "")])
        )
    if not normalized["incident_id"]:
        normalized["incident_id"] = _stable_incident_id(normalized)
    if not normalized["priority"]:
        normalized["priority"] = _default_priority(normalized)

    if is_open_incident(normalized):
        if not normalized["expected_closure_proof"]:
            normalized["expected_closure_proof"] = _default_expected_proof(normalized)
        if not normalized["next_action"]:
            normalized["next_action"] = _default_next_action(normalized)
        if not normalized["action_due_date"]:
            delay = 7 if normalized["priority"] in {"P0", "P1"} else 14
            normalized["action_due_date"] = _default_due_date(normalized, delay)
    return normalized


def read_incident_register(instance: InstanceConfig) -> list[dict[str, str]]:
    _, rows = read_csv(incident_register_path(instance))
    return [normalize_incident(row) for row in rows]


def write_incident_register(instance: InstanceConfig, run: RunContext, rows: Iterable[dict[str, str]]) -> Path:
    path = incident_register_path(instance)
    normalized = sorted(
        [normalize_incident(row) for row in rows],
        key=lambda row: (row.get("status", ""), row.get("date_signalement", ""), row.get("incident_id", "")),
    )
    write_csv(path, INCIDENT_FIELDS, normalized)
    run.log_action("write", path, f"incident rows={len(normalized)}")
    return path


def _load_text_artifact(instance: InstanceConfig, row: dict[str, str], max_chars: int = 4000) -> str:
    value = row.get("text_path", "")
    if not value:
        return ""
    path = Path(value)
    if not path.is_absolute():
        path = instance.root("workspace") / value
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]


def _document_haystack(instance: InstanceConfig, row: dict[str, str]) -> str:
    return _ascii_fold(
        "\n".join(
            [
                row.get("file_name", ""),
                row.get("original_path", ""),
                row.get("document_type", ""),
                row.get("lot", ""),
                _load_text_artifact(instance, row),
            ]
        )
    )


def _looks_like_incident(text: str) -> bool:
    return _has_keyword(text, INCIDENT_KEYWORDS)


def _extract_location(text: str) -> str:
    match = re.search(r"\b(?:lieu|localisation|emplacement)\s*[:\-]\s*([^\n\r.;]{2,80})", text, flags=re.IGNORECASE)
    return _cell(match.group(1)) if match else ""


def detect_incidents_from_documents(instance: InstanceConfig) -> list[dict[str, str]]:
    documents_path = instance.register("documents")
    if not documents_path.exists():
        return []

    _, docs = read_csv(documents_path)
    incidents: list[dict[str, str]] = []
    for doc in docs:
        haystack = _document_haystack(instance, doc)
        if not _looks_like_incident(haystack):
            continue
        text_sample = _load_text_artifact(instance, doc, max_chars=1200)
        doc_id = doc.get("doc_id", "")
        original_path = doc.get("original_path", "")
        file_name = doc.get("file_name", "")
        insurance_ref = doc_id if _has_keyword(haystack, INSURANCE_KEYWORDS) else ""
        date_signalement = doc.get("suspected_date") or detect_date(file_name) or detect_date(original_path)
        incidents.append(
            normalize_incident(
                {
                    "date_signalement": date_signalement,
                    "lieu": _extract_location(text_sample),
                    "description": f"Signalement detecte dans {file_name or doc_id}",
                    "piece_ref": doc_id or original_path,
                    "doc_ids": doc_id,
                    "photo_or_piece": original_path,
                    "status": "A_QUALIFIER",
                    "contract_or_insurance_ref": insurance_ref,
                    "source_refs": original_path,
                }
            )
        )
    return incidents


def merge_incidents(existing: Iterable[dict[str, str]], detected: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    by_source: dict[str, str] = {}

    for row in existing:
        normalized = normalize_incident(row)
        incident_id = normalized["incident_id"]
        merged[incident_id] = normalized
        source_key = normalized.get("source_refs") or normalized.get("piece_ref")
        if source_key:
            by_source[source_key] = incident_id

    for row in detected:
        normalized = normalize_incident(row)
        source_key = normalized.get("source_refs") or normalized.get("piece_ref")
        incident_id = by_source.get(source_key, normalized["incident_id"])
        if incident_id in merged:
            preserved = merged[incident_id]
            for field in INCIDENT_FIELDS:
                if not preserved.get(field) and normalized.get(field):
                    preserved[field] = normalized[field]
            merged[incident_id] = normalize_incident(preserved)
        else:
            merged[incident_id] = normalized
            if source_key:
                by_source[source_key] = incident_id

    return list(merged.values())


def validate_open_incidents(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for row in rows:
        if not is_open_incident(row):
            continue
        missing = []
        if not row.get("next_action"):
            missing.append("next_action")
        if not row.get("expected_closure_proof"):
            missing.append("expected_closure_proof")
        if missing:
            issues.append(
                {
                    "incident_id": row.get("incident_id", ""),
                    "missing": ";".join(missing),
                    "status": normalize_status(row.get("status")),
                }
            )
    return issues


def export_open_incidents(
    instance: InstanceConfig,
    run: RunContext,
    rows: Iterable[dict[str, str]] | None = None,
) -> Path:
    incidents = [normalize_incident(row) for row in (rows if rows is not None else read_incident_register(instance))]
    open_rows = [row for row in incidents if is_open_incident(row)]
    out = incident_reports_dir(instance) / "incidents_ouverts.csv"
    write_csv(out, INCIDENT_FIELDS, open_rows)
    run.log_action("write", out, f"open incidents={len(open_rows)}")
    return out


def write_incident_report(instance: InstanceConfig, run: RunContext, rows: Iterable[dict[str, str]]) -> Path:
    incidents = [normalize_incident(row) for row in rows]
    open_rows = [row for row in incidents if is_open_incident(row)]
    issues = validate_open_incidents(open_rows)
    report_path = incident_reports_dir(instance) / "rapport_incidentops.md"
    lines = [
        "# Rapport IncidentOps",
        "",
        f"- Incidents suivis: {len(incidents)}",
        f"- Incidents ouverts: {len(open_rows)}",
        f"- Incidents ouverts incomplets: {len(issues)}",
        "",
        "## Incidents ouverts",
        "",
        "| Incident | Date | Lieu | Statut | Priorite | Prochaine action | Preuve attendue |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in open_rows:
        lines.append(
            "| {incident_id} | {date_signalement} | {lieu} | {status} | {priority} | {next_action} | {expected_closure_proof} |".format(
                **{field: _cell(row.get(field, "")) for field in INCIDENT_FIELDS}
            )
        )
    if not open_rows:
        lines.append("| - | - | - | - | - | - | - |")
    write_text(report_path, "\n".join(lines) + "\n")
    run.log_action("write", report_path, f"incident report rows={len(incidents)}")
    return report_path


def build_incident_register(instance: InstanceConfig, run: RunContext) -> dict[str, object]:
    existing = read_incident_register(instance)
    detected = detect_incidents_from_documents(instance)
    rows = merge_incidents(existing, detected)
    register_path = write_incident_register(instance, run, rows)
    open_export_path = export_open_incidents(instance, run, rows)
    report_path = write_incident_report(instance, run, rows)
    open_rows = [row for row in rows if is_open_incident(row)]
    issues = validate_open_incidents(open_rows)
    return {
        "status": "ok",
        "incident_count": len(rows),
        "open_incident_count": len(open_rows),
        "open_incident_issue_count": len(issues),
        "incident_register": str(register_path),
        "open_incidents_export": str(open_export_path),
        "incident_report": str(report_path),
    }


def relative_incident_outputs(instance: InstanceConfig, result: dict[str, object]) -> dict[str, object]:
    workspace = instance.root("workspace")
    converted: dict[str, object] = dict(result)
    for key in ["incident_register", "open_incidents_export", "incident_report"]:
        value = converted.get(key)
        if isinstance(value, str):
            converted[key] = relative_to(workspace, Path(value))
    return converted
