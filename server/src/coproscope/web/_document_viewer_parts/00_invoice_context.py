from __future__ import annotations


def _with_invoice_context(instance: InstanceConfig, row: dict[str, str]) -> dict[str, str]:
    doc_id = row.get("doc_id", "")
    invoice_date = _invoice_date_from_exports(instance, doc_id)
    if not invoice_date:
        return row
    enriched = dict(row)
    enriched["suspected_date"] = invoice_date
    return enriched


def _invoice_date_from_exports(instance: InstanceConfig, doc_id: str) -> str:
    if not doc_id:
        return ""
    try:
        accounting_dir = Path(instance.artifact("accounting_dir"))
    except (AttributeError, KeyError, TypeError, ValueError, OSError):
        return ""
    for path in sorted(accounting_dir.glob("*/invoice_evidence_*.csv")):
        _header, rows = read_csv(path)
        for item in rows:
            if item.get("doc_id") == doc_id and item.get("date_facture"):
                return str(item.get("date_facture") or "").strip()
    return ""
