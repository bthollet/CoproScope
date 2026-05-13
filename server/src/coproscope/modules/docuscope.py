from __future__ import annotations

import csv
import re
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from ..core.common import (
    DEFAULT_DOCUMENT_FIELDS,
    FINDING_FIELDS,
    RunContext,
    append_note,
    detect_date,
    load_template_csv,
    load_structured_file,
    now_iso,
    read_csv,
    relative_to,
    safe_name,
    sha256_file,
    write_csv,
    write_text,
)
from .coprolink import request_metrics


TEXT_EXTENSIONS = {"txt", "md", "csv", "tsv", "json"}
HTML_EXTENSIONS = {"html", "htm"}
SKIP_DIRS = {".git", "__pycache__", ".secrets"}
SKIP_FILENAMES = {"desktop.ini", "thumbs.db"}
PRESERVE_FIELDS = {
    "lot",
    "document_type",
    "suspected_date",
    "emitter",
    "status_ocr",
    "classification_status",
    "text_path",
    "page_count",
    "text_char_count",
    "sensitivity",
    "notes",
}


def _load_existing_by_digest(registry_path: Path) -> dict[str, dict[str, str]]:
    _, rows = read_csv(registry_path)
    return {row.get("sha256", ""): row for row in rows if row.get("sha256")}


def _doc_id_for(digest: str) -> str:
    return f"DOC-{digest[:12].upper()}"


def _iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name.lower() in SKIP_FILENAMES:
            continue
        yield path


def _load_sensitivity_rules(instance) -> dict:
    return load_structured_file(instance.sensitivity_rules_path())


def _classify_sensitivity(relative_path: str, instance) -> tuple[str, str]:
    rules = _load_sensitivity_rules(instance)
    lower_path = relative_path.lower()
    for rule in rules.get("rules", []):
        keywords = [keyword.lower() for keyword in rule.get("path_keywords", [])]
        if any(keyword in lower_path for keyword in keywords):
            return str(rule.get("sensitivity", "internal")), str(rule.get("scope", "internal"))
    return str(rules.get("default_sensitivity", "internal")), "internal"


def inventory(instance, run: RunContext) -> Path:
    raw_root = instance.root("raw")
    workspace_root = instance.root("workspace")
    registry_path = instance.register("documents")
    duplicates_path = instance.register("duplicates")
    manifest_path = instance.register("manifest")
    existing = _load_existing_by_digest(registry_path)
    seen_at = now_iso()
    rows: list[dict[str, str]] = []
    by_digest: dict[str, list[dict[str, str]]] = defaultdict(list)

    for path in _iter_files(raw_root):
        digest = sha256_file(path)
        previous = existing.get(digest, {})
        stat = path.stat()
        relative_path = relative_to(workspace_root, path)
        sensitivity, scope = _classify_sensitivity(relative_path, instance)
        row = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        row.update(
            {
                "doc_id": previous.get("doc_id") or _doc_id_for(digest),
                "instance_id": instance.instance_id,
                "entity_id": instance.entity_id,
                "scope": previous.get("scope") or scope,
                "sha256": digest,
                "original_path": relative_path,
                "file_name": path.name,
                "extension": path.suffix.lower().lstrip("."),
                "size_bytes": str(stat.st_size),
                "last_modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
                "first_seen": previous.get("first_seen") or seen_at,
                "source_zone": "RAW",
                "source_kind": "raw",
                "status_ocr": previous.get("status_ocr") or "PENDING",
                "classification_status": previous.get("classification_status") or "PENDING",
                "sensitivity": previous.get("sensitivity") or sensitivity,
            }
        )
        for field in PRESERVE_FIELDS:
            if previous.get(field):
                row[field] = previous[field]
        rows.append(row)
        by_digest[digest].append(row)

    rows.sort(key=lambda item: (item["file_name"].lower(), item["doc_id"]))
    write_csv(registry_path, DEFAULT_DOCUMENT_FIELDS, rows)
    run.log_action("write", registry_path, f"inventory rows={len(rows)}")

    duplicates_rows: list[dict[str, str]] = []
    for digest, digest_rows in sorted(by_digest.items()):
        if len(digest_rows) < 2:
            continue
        duplicates_rows.append(
            {
                "sha256": digest,
                "count": str(len(digest_rows)),
                "doc_ids": "; ".join(row["doc_id"] for row in digest_rows),
                "paths": "; ".join(row["original_path"] for row in digest_rows),
            }
        )
    write_csv(duplicates_path, ["sha256", "count", "doc_ids", "paths"], duplicates_rows)
    run.log_action("write", duplicates_path, f"duplicate groups={len(duplicates_rows)}")

    manifest_rows = [
        {
            "doc_id": row["doc_id"],
            "sha256": row["sha256"],
            "original_path": row["original_path"],
            "file_name": row["file_name"],
            "size_bytes": row["size_bytes"],
            "source_kind": row["source_kind"],
        }
        for row in rows
    ]
    write_csv(manifest_path, ["doc_id", "sha256", "original_path", "file_name", "size_bytes", "source_kind"], manifest_rows)
    run.log_action("write", manifest_path, f"manifest rows={len(manifest_rows)}")
    return registry_path


def _read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    fields, rows = read_csv(path)
    if not rows and not fields:
        raise SystemExit(f"Missing registry: {path}")
    return fields, rows


def _write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    for field in ["status_ocr", "text_path", "page_count", "text_char_count", "notes"]:
        if field not in fields:
            fields.append(field)
    write_csv(path, fields, rows)


def _extract_pdf(path: Path) -> tuple[list[str], str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Module pypdf indisponible.") from exc

    reader = PdfReader(str(path))
    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001
            text = f"[ERREUR_EXTRACTION_PAGE_{index}: {exc}]"
        pages.append(text.strip())
    return pages, str(len(reader.pages))


def _extract_plain_text(path: Path) -> tuple[list[str], str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")
    return [text], "1"


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        if tag.lower() in {"script", "style", "noscript"}:
            self.skip_depth += 1
        if tag.lower() in {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
        if tag.lower() in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", "".join(self.parts))).strip()


def _extract_html(path: Path) -> tuple[list[str], str]:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = path.read_text(encoding="latin-1")
    parser = _VisibleTextParser()
    parser.feed(raw)
    return [parser.text()], "1"


def _extract_docx(path: Path) -> tuple[list[str], str]:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("Module python-docx indisponible.") from exc

    document = Document(str(path))
    lines = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        for row in table.rows:
            values = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if values:
                lines.append(" | ".join(values))
    return ["\n".join(lines)], "1"


def _extract_xlsx(path: Path) -> tuple[list[str], str]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("Module openpyxl indisponible.") from exc

    workbook = load_workbook(str(path), read_only=True, data_only=True)
    try:
        pages: list[str] = []
        for worksheet in workbook.worksheets:
            lines = [f"===== FEUILLE {worksheet.title} ====="]
            for row in worksheet.iter_rows(values_only=True):
                values = [str(value).strip() if value is not None else "" for value in row]
                if any(values):
                    lines.append(" | ".join(values).rstrip())
            pages.append("\n".join(lines))
    finally:
        workbook.close()
    return pages, str(len(pages))


def _write_page_text(text_dir: Path, doc_id: str, pages: list[str], suffix: str = "native") -> Path:
    text_dir.mkdir(parents=True, exist_ok=True)
    out = text_dir / f"{doc_id}.{suffix}.txt"
    lines: list[str] = []
    for index, text in enumerate(pages, start=1):
        lines.append(f"===== PAGE {index} =====")
        lines.append(text)
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _process_row(instance, row: dict[str, str]) -> dict[str, str]:
    workspace_root = instance.root("workspace")
    text_dir = instance.artifact("text_dir")
    path = workspace_root / row["original_path"]
    ext = row.get("extension", "").lower()
    doc_id = row["doc_id"]
    row.setdefault("notes", "")

    if not path.exists():
        row["status_ocr"] = "SOURCE_MISSING"
        row["notes"] = append_note(row.get("notes", ""), "Fichier source introuvable.")
        return row

    try:
        if ext == "pdf":
            pages, page_count = _extract_pdf(path)
        elif ext in TEXT_EXTENSIONS:
            pages, page_count = _extract_plain_text(path)
        elif ext in HTML_EXTENSIONS:
            pages, page_count = _extract_html(path)
        elif ext == "docx":
            pages, page_count = _extract_docx(path)
        elif ext == "xlsx":
            pages, page_count = _extract_xlsx(path)
        else:
            row["status_ocr"] = "OCR_REQUIRED" if ext in {"png", "jpg", "jpeg", "tif", "tiff", "bmp"} else "UNSUPPORTED"
            return row
    except Exception as exc:  # noqa: BLE001
        row["status_ocr"] = "EXTRACTION_ERROR"
        row["notes"] = append_note(row.get("notes", ""), f"Extraction impossible: {exc}")
        return row

    total_chars = sum(len(page.strip()) for page in pages)
    out = _write_page_text(text_dir, doc_id, pages)
    row["text_path"] = relative_to(workspace_root, out)
    row["page_count"] = page_count
    row["text_char_count"] = str(total_chars)
    if total_chars >= 80 or ext != "pdf":
        row["status_ocr"] = "TEXT_EXTRACTED"
        if total_chars < 80:
            row["notes"] = append_note(row.get("notes", ""), "Texte court extrait; OCR non applicable a ce format.")
    else:
        row["status_ocr"] = "OCR_REQUIRED"
        row["notes"] = append_note(row.get("notes", ""), "Texte natif faible ou absent: OCR scan requis.")
    return row


def extract_text(instance, run: RunContext, doc_id: str | None = None) -> Path:
    registry_path = instance.register("documents")
    fields, rows = _read_rows(registry_path)
    processed = 0
    for row in rows:
        if doc_id and row.get("doc_id") != doc_id:
            continue
        if row.get("status_ocr") == "OCR_DONE":
            continue
        row.update(_process_row(instance, row))
        processed += 1
    _write_rows(registry_path, fields, rows)
    run.log_action("write", registry_path, f"text extraction processed={processed}")
    return registry_path


def _load_taxonomy(instance) -> dict:
    return load_structured_file(instance.classification_rules_path())


def _text_sample(instance, row: dict[str, str]) -> str:
    workspace_root = instance.root("workspace")
    parts = [row.get("file_name", ""), row.get("original_path", "")]
    text_path = row.get("text_path")
    if text_path:
        path = workspace_root / text_path
        if path.exists():
            parts.append(path.read_text(encoding="utf-8", errors="ignore")[:6000])
    return "\n".join(parts).lower()


def _classify(sample: str, file_name: str, original_path: str, rules: list[dict]) -> tuple[str, str, int]:
    best = ("A_CLASSER", "A_CLASSER", 0)
    file_text = file_name.lower()
    path_text = original_path.lower().replace("\\", "/")
    for rule in rules:
        score = 0
        matched = False
        for pattern in rule.get("filename_patterns", []):
            if re.search(pattern, file_text, flags=re.IGNORECASE):
                matched = True
                score += int(rule.get("filename_weight", 50))
        for pattern in rule.get("path_patterns", []):
            if re.search(pattern, path_text, flags=re.IGNORECASE):
                matched = True
                score += int(rule.get("path_weight", 80))
        for keyword in rule.get("keywords", []):
            if keyword.lower() in sample:
                matched = True
                score += int(rule.get("keyword_weight", 5))
        if matched:
            score += int(rule.get("priority", 0))
        if score > best[2]:
            best = (str(rule["lot"]), str(rule["document_type"]), score)
    return best


def classify(instance, run: RunContext, copy_files: bool = True) -> Path:
    registry_path = instance.register("documents")
    fields, rows = _read_rows(registry_path)
    rules = _load_taxonomy(instance).get("rules", [])
    classified_dir = instance.artifact("classified_dir")
    workspace_root = instance.root("workspace")

    processed = 0
    for row in rows:
        sample = _text_sample(instance, row)
        lot, doc_type, score = _classify(sample, row.get("file_name", ""), row.get("original_path", ""), rules)
        row["lot"] = lot
        row["document_type"] = doc_type
        row["suspected_date"] = row.get("suspected_date") or detect_date(sample or row.get("file_name", ""))
        row["classification_status"] = "AUTO_CLASSIFIED" if score else "A_CLASSER"
        if copy_files:
            source = workspace_root / row["original_path"]
            target_dir = classified_dir / lot
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"{row['doc_id']}__{safe_name(row['file_name'])}"
            if source.exists() and not target.exists():
                shutil.copy2(source, target)
                run.log_action("write", target, f"classified copy from {source}")
        processed += 1

    write_csv(registry_path, fields, rows)
    run.log_action("write", registry_path, f"classification processed={processed}")
    return registry_path


def _load_proofs(instance) -> list[dict[str, str]]:
    proofs_path = instance.matrix("proofs")
    if proofs_path and proofs_path.exists():
        _, rows = read_csv(proofs_path)
        return rows
    data = load_structured_file(instance.completeness_rules_path())
    return list(data.get("proofs", []))


def missing_docs(instance, run: RunContext) -> Path:
    _, docs = read_csv(instance.register("documents"))
    proofs = _load_proofs(instance)
    reports_dir = instance.artifact("reports_dir")
    findings_path = instance.register("findings")
    _, existing_findings = read_csv(findings_path)
    report_path = reports_dir / "rapport_completude_documentaire.md"
    by_lot: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_type: dict[str, list[dict[str, str]]] = defaultdict(list)
    for doc in docs:
        by_lot[doc.get("lot", "")].append(doc)
        by_type[doc.get("document_type", "")].append(doc)

    lines = [
        "# Rapport de completude documentaire",
        "",
        f"- Instance: {instance.display_name}",
        f"- Documents inventories: {len(docs)}",
        "",
        "## Pieces attendues",
        "",
        "| Statut | Lot | Piece attendue | Type source | Documents trouves |",
        "|---|---|---|---|---|",
    ]
    finding_rows: list[dict[str, str]] = []
    for proof in proofs:
        lot = proof.get("lot", "")
        doc_type = proof.get("document_type") or proof.get("document_source", "")
        matches = by_type.get(doc_type, []) if doc_type else by_lot.get(lot, [])
        names = "; ".join(match.get("doc_id", "") for match in matches[:5])
        status = "OK" if matches else "MANQUANT"
        lines.append(
            f"| {status} | {lot} | {proof.get('expected_label') or proof.get('preuve_attendue', '')} | "
            f"{doc_type} | {names} |"
        )
        if not matches:
            finding_rows.append(
                {
                    "finding_id": f"FDG-{proof.get('proof_id', 'MISS')}",
                    "category": "completeness",
                    "severity": proof.get("criticality", "P1"),
                    "source_ref": proof.get("proof_id", ""),
                    "fact": f"Piece manquante: {proof.get('expected_label') or proof.get('preuve_attendue', '')}",
                    "diligence": "Verifier le Drive, l'extranet, puis demander la piece au syndic si besoin.",
                    "status": "OPEN",
                }
            )

    extranet_path = instance.matrix("extranet")
    if extranet_path and extranet_path.exists():
        _, extranet_rows = read_csv(extranet_path)
        lines.extend(
            [
                "",
                "## Matrice extranet reference",
                "",
                "| Scope | Document attendu | Present extranet | Qualification |",
                "|---|---|---|---|",
            ]
        )
        for row in extranet_rows[:30]:
            lines.append(
                f"| {row.get('scope', '')} | {row.get('document_attendu', '')} | "
                f"{row.get('present_extranet', '') or 'A_VERIFIER'} | {row.get('qualification', '')} |"
            )

    write_text(report_path, "\n".join(lines) + "\n")
    merged = [row for row in existing_findings if row.get("category") != "completeness"] + finding_rows
    write_csv(findings_path, FINDING_FIELDS, merged)
    run.log_action("write", report_path, f"missing docs report rows={len(proofs)}")
    run.log_action("write", findings_path, f"findings merged={len(merged)}")
    return report_path


def _pct(part: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{(part / total) * 100:.1f}%"


def compute_kpis(instance, run: RunContext) -> Path:
    kpi_path = instance.register("kpi")
    if kpi_path.exists():
        fields, rows = read_csv(kpi_path)
    else:
        template = instance.register("kpi")
        template.parent.mkdir(parents=True, exist_ok=True)
        template.write_text(load_template_csv("kpi.csv"), encoding="utf-8")
        fields, rows = read_csv(template)
        run.log_action("write", template, "bootstrap kpi register")

    _, docs = read_csv(instance.register("documents"))
    total_docs = len(docs)
    ocr_required = sum(1 for doc in docs if doc.get("status_ocr") == "OCR_REQUIRED")
    unclassified = sum(1 for doc in docs if doc.get("classification_status") in {"A_CLASSER", "PENDING", ""})
    request_stats = request_metrics(instance)

    values = {
        "KPI-001": _pct(ocr_required, total_docs),
        "KPI-002": _pct(unclassified, total_docs),
        "KPI-011": _pct(request_stats["traced"], request_stats["total"]),
        "KPI-012": _pct(request_stats["complete"], request_stats["total"]),
    }
    for row in rows:
        kpi_id = row.get("kpi_id", "")
        if kpi_id in values:
            row["value"] = values[kpi_id]
            row["valeur"] = values[kpi_id]
            row["status"] = "CALCULATED"
            row["statut"] = "CALCULE"
    write_csv(kpi_path, list(fields or rows[0].keys() if rows else []), rows)
    run.log_action("write", kpi_path, f"kpi updated ids={','.join(values)}")
    return kpi_path
