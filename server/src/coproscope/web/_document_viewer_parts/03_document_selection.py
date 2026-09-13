from __future__ import annotations


def _document_row_score(row: dict[str, str]) -> tuple[int, int, int, int]:
    return (
        1 if row.get("suspected_date") else 0,
        1 if row.get("status_ocr") or row.get("text_path") else 0,
        1 if row.get("document_type") not in {"", "Document"} else 0,
        sum(1 for value in row.values() if str(value or "").strip()),
    )
