from __future__ import annotations

import re
import unicodedata

from ..core.common import AG_FIELDS, FINDING_FIELDS, RunContext, detect_date, load_structured_file, read_csv, write_csv, write_text


def _read_text(instance, row: dict[str, str]) -> str:
    text_path = row.get("text_path")
    if not text_path:
        return ""
    path = instance.root("workspace") / text_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", normalized.lower()).strip()


def _rule_values(rules: dict, *keys: str) -> list[str]:
    for key in keys:
        values = rules.get(key)
        if values:
            return [_normalize(str(value)) for value in values if str(value).strip()]
    return []


def analyze(instance, run: RunContext) -> None:
    _, docs = read_csv(instance.register("documents"))
    ag_rules = load_structured_file(instance.ag_rules_path())
    patterns = _rule_values(ag_rules, "resolution_patterns", "motifs_resolution")
    majority_terms = _rule_values(ag_rules, "majority_terms", "termes_majorite")
    annex_keywords = _rule_values(ag_rules, "annex_keywords", "mots_cles_annexes")
    rows: list[dict[str, str]] = []
    findings: list[dict[str, str]] = []

    for doc in docs:
        doc_type = doc.get("document_type", "")
        text = _read_text(instance, doc)
        haystack = _normalize(f"{doc.get('file_name', '')}\n{text}")
        if doc_type not in {"Convocation_AG", "PV_AG", "Annexe_AG"} and "assemblee generale" not in haystack and "convocation" not in haystack:
            continue
        resolution_count = sum(1 for line in text.splitlines() if any(token in _normalize(line) for token in patterns))
        annex_hits = sum(1 for token in annex_keywords if token in haystack)
        matched_majorities = sorted({term for term in majority_terms if term in haystack})
        detected_date = detect_date(doc.get("file_name", "")) or detect_date(doc.get("original_path", "")) or ""
        ag_id = f"AG-{detected_date or doc.get('doc_id', '')[-6:]}"
        missing_annex = "YES" if doc_type == "Convocation_AG" and annex_hits == 0 else ""
        notes = ""
        if doc_type == "Convocation_AG" and resolution_count == 0:
            notes = "Convocation detectee sans lignes explicites de resolution."
        rows.append(
            {
                "ag_id": ag_id,
                "doc_id": doc.get("doc_id", ""),
                "file_name": doc.get("file_name", ""),
                "document_type": doc_type,
                "detected_date": detected_date,
                "resolution_count": str(resolution_count),
                "annex_hits": str(annex_hits),
                "majority_terms": "; ".join(matched_majorities),
                "missing_annex_signals": missing_annex,
                "notes": notes,
            }
        )
        if missing_annex:
            findings.append(
                {
                    "finding_id": f"FDG-AG-{doc.get('doc_id', '')[-6:]}",
                    "category": "ag",
                    "severity": "P1",
                    "source_ref": doc.get("doc_id", ""),
                    "fact": "Convocation AG detectee sans signal d'annexes jointes.",
                    "diligence": "Verifier les annexes, devis, budgets et resolutions jointes avant preparation AG.",
                    "status": "OPEN",
                }
            )

    ag_path = instance.register("ag")
    write_csv(ag_path, AG_FIELDS, rows)
    run.log_action("write", ag_path, f"ag rows={len(rows)}")

    report_path = instance.artifact("reports_dir") / "rapport_ag_preparation.md"
    report_lines = [
        "# Rapport AG",
        "",
        f"- Documents AG analyses: {len(rows)}",
        "",
        "| AG | Document | Type | Date | Resolutions | Annexes | Majorites |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        report_lines.append(
            f"| {row['ag_id']} | {row['doc_id']} | {row['document_type']} | {row['detected_date']} | "
            f"{row['resolution_count']} | {row['annex_hits']} | {row['majority_terms']} |"
        )
    if not rows:
        report_lines.append("| - | - | - | - | 0 | 0 | - |")
    write_text(report_path, "\n".join(report_lines) + "\n")
    run.log_action("write", report_path, "ag report")

    findings_path = instance.register("findings")
    _, existing_findings = read_csv(findings_path)
    merged = [row for row in existing_findings if row.get("category") != "ag"] + findings
    write_csv(findings_path, FINDING_FIELDS, merged)
    run.log_action("write", findings_path, f"ag findings merged={len(merged)}")
