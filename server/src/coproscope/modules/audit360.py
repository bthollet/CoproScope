from __future__ import annotations

import csv
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ..core.common import InstanceConfig, RunContext, read_csv, relative_to, sha256_file, write_csv, write_text
from ..core.privacy import PrivacySignal, redaction_signals
from ..vault import reconstruction


DERIVED_NOTICE = (
    "Import derive local: ces constats preparent une reprise probatoire, "
    "ils ne sont pas une source de verite et doivent etre verifies humainement."
)

ANONYMIZED_AUDIT_SOURCE_FIELDS = [
    "doc_id",
    "file_name",
    "document_type",
    "source_role",
    "audit_status",
    "cloud_allowed",
    "audit_input_path",
    "audit_text_path",
    "source_sha256",
    "redacted_sha256",
    "needs_human_review",
    "notes",
]

_ABSOLUTE_PATH_RE = re.compile(r"(?i)(?:[a-z]:[\\/]|\\\\|/(?:Users|home|var|tmp|private)/)")
_EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_FORBIDDEN_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)file://"), "file_url"),
    (re.compile(r"(?i)(?:\?|&)token=|--token\b|local-secret|[a-z0-9]+[-_]test(?:[-_]local)?"), "token_or_private_instance"),
    (re.compile(r"(?i)(^|[\\/])(?:raw|restricted|logs)([\\/]|$)"), "private_folder"),
    (_ABSOLUTE_PATH_RE, "local_path"),
    (_EMAIL_RE, "email"),
)


def load_audit360_rows(path: Path) -> list[dict[str, str]]:
    source = Path(path).expanduser().resolve()
    suffix = source.suffix.lower()
    if suffix == ".json":
        return _load_json_rows(source)
    if suffix == ".jsonl":
        return _load_jsonl_rows(source)
    return _load_csv_rows(source)


def audit_rows_for_private_leaks(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    for row_index, row in enumerate(rows, start=1):
        for field, value in row.items():
            text = "" if value is None else str(value)
            if not text:
                continue
            reason = _forbidden_reason(text)
            if reason:
                violations.append({"row": row_index, "field": str(field), "reason": reason})
    return violations


def import_audit360_file(
    *,
    local_root: Path,
    sync_root: Path,
    path: Path,
    db_path: Path | None = None,
    source_kind: str = "audit360",
    import_run_id: str = "manual-audit360-import",
    imported_at: str = "1970-01-01T00:00:00+00:00",
) -> dict[str, object]:
    rows = load_audit360_rows(path)
    privacy_violations = audit_rows_for_private_leaks(rows)
    if privacy_violations:
        return {
            "ok": False,
            "command": "vault import-audit360-rows",
            "source_file": Path(path).name,
            "rows": len(rows),
            "imported_rows": 0,
            "privacy_violations": privacy_violations,
            "notice": DERIVED_NOTICE,
        }

    resolved_db_path = reconstruction.resolve_reconstruction_db_path(local_root, db_path)
    if not resolved_db_path.exists():
        reconstruction.rebuild_local_cache(local_root, sync_root, resolved_db_path)

    result = reconstruction.import_audit360_rows(
        resolved_db_path,
        rows,
        source_kind=source_kind,
        source_file=Path(path).name,
        import_run_id=import_run_id,
        imported_at=imported_at,
    )
    return {
        "ok": bool(result.get("ok")),
        "command": "vault import-audit360-rows",
        "source_file": Path(path).name,
        "rows": result.get("rows", len(rows)),
        "imported_rows": result.get("imported_rows", 0),
        "skipped_rows": result.get("skipped_rows", 0),
        "points": result.get("points", 0),
        "actions": result.get("actions", 0),
        "expected_pieces": result.get("expected_pieces", 0),
        "object_links": result.get("object_links", 0),
        "source_import_map": result.get("source_import_map", 0),
        "created": result.get("created", {}),
        "notice": DERIVED_NOTICE,
    }


def prepare_anonymized_audit_sources(
    instance: InstanceConfig,
    run: RunContext,
    *,
    doc_id: str | None = None,
    include_all: bool = False,
) -> dict[str, object]:
    """Prepare a cloud-audit manifest that never points to raw source files."""
    _, docs = read_csv(instance.register("documents"))
    rows = [_anonymized_audit_source_row(instance, row) for row in docs if _audit_source_match(row, doc_id, include_all)]
    manifest_path = _anonymized_manifest_path(instance)
    write_csv(manifest_path, ANONYMIZED_AUDIT_SOURCE_FIELDS, rows)
    run.log_action("write", manifest_path, f"anonymized audit sources={len(rows)}")
    ready = sum(1 for row in rows if row.get("cloud_allowed") == "YES")
    blocked = len(rows) - ready
    return {
        "status": "ok",
        "source_count": len(rows),
        "ready_for_cloud_audit": ready,
        "blocked_count": blocked,
        "manifest": str(manifest_path),
        "manifest_relative": relative_to(instance.root("workspace"), manifest_path),
    }


def _audit_source_match(row: dict[str, str], doc_id: str | None, include_all: bool) -> bool:
    if doc_id:
        return row.get("doc_id") == doc_id
    if include_all:
        return True
    return row.get("document_type") in {"Convocation_AG", "PV_AG", "Annexe_AG"}


def _anonymized_manifest_path(instance: InstanceConfig) -> Path:
    path = instance.artifact("reports_dir") / "audit_sources_anonymized.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _anonymized_text_dir(instance: InstanceConfig) -> Path:
    path = instance.root("staging") / "audit_anonymized"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _workspace_path(instance: InstanceConfig, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return instance.root("workspace") / value


def _requires_anonymized_derivative(row: dict[str, str]) -> bool:
    publication_form = row.get("publication_form", "")
    transformations = row.get("required_transformations", "")
    return "redaction" in publication_form or "redaction" in transformations


def _requires_manual_aggregation(row: dict[str, str]) -> bool:
    publication_form = row.get("publication_form", "")
    transformations = row.get("required_transformations", "")
    return "aggregation" in publication_form or "aggregation" in transformations


def _source_role(row: dict[str, str]) -> str:
    if row.get("document_type") == "Convocation_AG":
        return "piece_mere_ag_audit"
    if row.get("document_type") in {"PV_AG", "Annexe_AG"}:
        return "piece_ag_audit"
    return "piece_audit"


def _anonymized_audit_source_row(instance: InstanceConfig, row: dict[str, str]) -> dict[str, str]:
    base = {
        "doc_id": row.get("doc_id", ""),
        "file_name": row.get("file_name", ""),
        "document_type": row.get("document_type", ""),
        "source_role": _source_role(row),
        "audit_status": "",
        "cloud_allowed": "",
        "audit_input_path": "",
        "audit_text_path": "",
        "source_sha256": row.get("sha256", ""),
        "redacted_sha256": row.get("redacted_sha256", ""),
        "needs_human_review": row.get("review_required", ""),
        "notes": "",
    }

    if _requires_manual_aggregation(row):
        base.update(
            {
                "audit_status": "BLOCKED_MANUAL_AGGREGATION_REQUIRED",
                "notes": "Audit cloud bloque: produire une synthese agregee sans donnees personnelles.",
            }
        )
        return base

    if _requires_anonymized_derivative(row):
        redacted_path = row.get("redacted_path", "")
        if row.get("redaction_status") != "REDACTED" or not redacted_path:
            base.update(
                {
                    "audit_status": "BLOCKED_REDACTION_REQUIRED",
                    "notes": "Audit cloud bloque: biffage/anonymisation requis avant traitement.",
                }
            )
            return base
        source = _workspace_path(instance, redacted_path)
        if not source.exists():
            base.update(
                {
                    "audit_status": "BLOCKED_REDACTED_FILE_MISSING",
                    "notes": "Audit cloud bloque: le derive anonymise reference est introuvable.",
                }
            )
            return base
        text_path, residuals = _write_audit_text(instance, row, source, "redacted", sanitize=True)
        if residuals:
            base.update(
                {
                    "audit_status": "BLOCKED_RESIDUAL_IDENTIFIERS",
                    "audit_text_path": relative_to(instance.root("workspace"), text_path),
                    "redacted_sha256": row.get("redacted_sha256") or sha256_file(source),
                    "notes": "Audit cloud bloque: le derive anonymise contient encore des identifiants detectables.",
                }
            )
            return base
        base.update(
            {
                "audit_status": "READY_ANONYMIZED_TEXT",
                "cloud_allowed": "YES",
                "audit_text_path": relative_to(instance.root("workspace"), text_path),
                "redacted_sha256": row.get("redacted_sha256") or sha256_file(source),
                "notes": "Audit cloud autorise uniquement sur le texte derive anonymise; le PDF reste local.",
            }
        )
        return base

    original_path = row.get("original_path", "")
    if not original_path:
        base.update({"audit_status": "BLOCKED_SOURCE_MISSING", "notes": "Aucune source locale referencee."})
        return base
    source = _workspace_path(instance, original_path)
    if not source.exists():
        base.update({"audit_status": "BLOCKED_SOURCE_MISSING", "notes": "Source locale introuvable."})
        return base
    text_path, residuals = _write_audit_text(instance, row, source, "low_risk", sanitize=False)
    if residuals:
        base.update(
            {
                "audit_status": "BLOCKED_RESIDUAL_IDENTIFIERS",
                "audit_text_path": relative_to(instance.root("workspace"), text_path),
                "notes": "Audit cloud bloque: identifiants detectables dans le texte derive.",
            }
        )
        return base
    base.update(
        {
            "audit_status": "READY_NO_REDACTION_REQUIRED",
            "cloud_allowed": "YES",
            "audit_text_path": relative_to(instance.root("workspace"), text_path),
            "notes": "Aucun biffage requis par PrivacyOps; le manifeste ne reference pas le chemin brut.",
        }
    )
    return base


def _write_audit_text(instance: InstanceConfig, row: dict[str, str], source: Path, suffix: str, *, sanitize: bool) -> tuple[Path, list[str]]:
    text = _extract_text_for_audit(source)
    if sanitize and not text.strip():
        text = _fallback_text_for_redacted_audit(instance, row)
    if sanitize:
        text = _sanitize_text_for_cloud_audit(instance, row, text)
    out = _anonymized_text_dir(instance) / f"{row.get('doc_id', 'DOC')}.{suffix}.audit.txt"
    if not text.strip():
        text = f"Document {row.get('doc_id', 'DOC')} pret pour audit, sans texte extractible automatiquement."
    write_text(out, text.rstrip() + "\n")
    return out, _residual_identifier_findings(text)


def _fallback_text_for_redacted_audit(instance: InstanceConfig, row: dict[str, str]) -> str:
    """Use local extracted text when a redacted PDF/image has no text layer."""
    text_path = row.get("text_path", "")
    if not text_path:
        return ""
    path = _workspace_path(instance, text_path)
    if not path.exists():
        return ""
    return _extract_text_for_audit(path)


def _sanitize_text_for_cloud_audit(instance: InstanceConfig, row: dict[str, str], text: str) -> str:
    replacements = _replacement_values_from_text(text)
    original_path = row.get("original_path", "")
    if original_path:
        original = _workspace_path(instance, original_path)
        if original.exists():
            replacements.extend(_replacement_values_from_text(_extract_text_for_audit(original)))
    sanitized = text
    for value, label in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        if value:
            sanitized = sanitized.replace(value, label)
    sanitized = re.sub(
        r"(?im)(je soussign[ée]\s+)([A-Z][A-Z'\-]{2,}\s+[A-Z][A-Za-zÀ-ÿ'\-]+)",
        r"\1[BIFFE_PERSON_NAME]",
        sanitized,
    )
    sanitized = re.sub(
        r"(?im)^(r[ée]f[ée]rence\s*:?\s*)([0-9][0-9 ./-]{2,})$",
        r"\1[BIFFE_REFERENCE]",
        sanitized,
    )
    sanitized = re.sub(
        r"(?im)(nos r[ée]f[ée]rences\s*\n)([0-9][0-9 ./-]{2,})",
        r"\1[BIFFE_REFERENCE]",
        sanitized,
    )
    sanitized = re.sub(
        r"(?im)(r[ée]f[ée]rence\s*:?\s*\[BIFFE_REFERENCE\]\s*\n)([0-9][0-9 ./-]{2,})",
        r"\1[BIFFE_REFERENCE]",
        sanitized,
    )
    sanitized = re.sub(
        r"(?im)^(-\s*De:\s*)[^<\n]+(<\[BIFFE_EMAIL\]>)",
        r"\1[BIFFE_PERSON_NAME] \2",
        sanitized,
    )
    sanitized = re.sub(
        r"(?im)^(De\s*:\s*)(?!CHAVISSIMMO\b|\[BIFFE_)[^\n<]+$",
        r"\1[BIFFE_PERSON_NAME]",
        sanitized,
    )
    sanitized = re.sub(
        r"(?i)https://mail\.google\.com/mail/#\S+",
        "[BIFFE_GMAIL_URL]",
        sanitized,
    )
    sanitized = re.sub(r"(?i)\bappel de fonds\b", "[BIFFE_ACCOUNT_INDIVIDUAL]", sanitized)
    sanitized = re.sub(r"(?m)^\s*\d{7,}\s*$", "[BIFFE_REFERENCE]", sanitized)
    return sanitized


def _replacement_values_from_text(text: str) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for signal in redaction_signals(text):
        values.append((signal.value, _label(signal)))
        if signal.category == "PERSON_NAME":
            bare = re.sub(r"(?i)^(?:m\.|mme|monsieur|madame)\s+", "", signal.value).strip()
            if bare and bare != signal.value:
                values.append((bare, _label(signal)))
                values.append((bare.upper(), _label(signal)))
    return values


def _label(signal: PrivacySignal) -> str:
    return f"[BIFFE_{signal.category}]"


def _residual_identifier_findings(text: str) -> list[str]:
    findings = [
        signal.category
        for signal in redaction_signals(text)
        if not (signal.category == "LOT" and signal.value.strip().lower() in {"lot", "lots"})
    ]
    if re.search(r"(?im)^je soussign[ée]\s+[A-Z][A-Z'\-]{2,}\s+[A-Z][A-Za-zÀ-ÿ'\-]+", text):
        findings.append("PERSON_NAME")
    if re.search(r"(?im)^r[ée]f[ée]rence\s*:?\s*[0-9][0-9 ./-]{2,}$", text):
        findings.append("REFERENCE")
    if re.search(r"(?im)nos r[ée]f[ée]rences\s*\n[0-9][0-9 ./-]{2,}", text):
        findings.append("REFERENCE")
    if re.search(r"(?m)^\s*\d{7,}\s*$", text):
        findings.append("REFERENCE")
    return sorted(set(findings))


def _extract_text_for_audit(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    if ext in {"txt", "md", "csv", "tsv", "json", "yml", "yaml", "html", "htm"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if ext == "pdf":
        try:
            import fitz  # type: ignore

            document = fitz.open(str(path))
            try:
                return "\n\n".join(document.load_page(index).get_text("text") for index in range(document.page_count))
            finally:
                document.close()
        except Exception:  # noqa: BLE001
            return ""
    return ""


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return [{str(key or ""): str(value or "") for key, value in row.items()} for row in csv.DictReader(stream)]


def _load_json_rows(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        payload = payload.get("rows", [])
    if not isinstance(payload, list):
        raise ValueError("Audit360 JSON input must be a list or an object with a rows list")
    return [_string_dict(row) for row in payload if isinstance(row, Mapping)]


def _load_jsonl_rows(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        payload = json.loads(stripped)
        if isinstance(payload, Mapping):
            rows.append(_string_dict(payload))
    return rows


def _string_dict(row: Mapping[str, Any]) -> dict[str, str]:
    return {str(key): "" if value is None else str(value) for key, value in row.items()}


def _forbidden_reason(text: str) -> str:
    for pattern, reason in _FORBIDDEN_PATTERNS:
        if pattern.search(text):
            return reason
    return ""
