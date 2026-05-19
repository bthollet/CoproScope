from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..core.common import InstanceConfig, RunContext, append_note, module_available, read_csv, relative_to, write_csv


DOCAI_FIELDS = [
    "extraction_level",
    "text_quality",
    "ocr_engine",
    "docling_path",
    "layout_path",
    "ai_review_status",
]

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "tif", "tiff", "bmp"}
OCR_BACKENDS = {"sidecar_ocr", "rapidocr", "gutenocr"}
ENRICH_BACKENDS = {"docling", "qwen_vl", "qwen-vl", "layoutlmv3", "layoutalm"}


def _read_rows(instance: InstanceConfig) -> tuple[Path, list[str], list[dict[str, str]]]:
    registry_path = instance.register("documents")
    fields, rows = read_csv(registry_path)
    if not rows and not fields:
        raise SystemExit(f"Missing registry: {registry_path}")
    for field in DOCAI_FIELDS + ["status_ocr", "text_path", "page_count", "text_char_count", "notes"]:
        if field not in fields:
            fields.append(field)
    return registry_path, fields, rows


def _write_rows(registry_path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    write_csv(registry_path, fields, rows)


def _source_path(instance: InstanceConfig, row: dict[str, str]) -> Path:
    return instance.root("workspace") / row.get("original_path", "")


def _docai_dir(instance: InstanceConfig) -> Path:
    path = instance.artifact("docai_dir")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _artifact_path(instance: InstanceConfig, row: dict[str, str], suffix: str) -> Path:
    doc_id = row.get("doc_id") or "DOC-UNKNOWN"
    return _docai_dir(instance) / f"{doc_id}.{suffix}"


def _write_text_artifact(instance: InstanceConfig, row: dict[str, str], suffix: str, content: str) -> str:
    path = _artifact_path(instance, row, suffix)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return relative_to(instance.root("workspace"), path)


def _write_json_artifact(instance: InstanceConfig, row: dict[str, str], suffix: str, payload: dict[str, Any]) -> str:
    path = _artifact_path(instance, row, suffix)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return relative_to(instance.root("workspace"), path)


def _matches(row: dict[str, str], doc_id: str | None) -> bool:
    return not doc_id or row.get("doc_id") == doc_id


def _append_level(existing: str, level: str) -> str:
    levels = [item.strip() for item in existing.split(";") if item.strip()]
    if level not in levels:
        levels.append(level)
    return ";".join(levels)


def _text_from_existing_path(instance: InstanceConfig, row: dict[str, str]) -> str:
    text_path = row.get("text_path", "")
    if not text_path:
        return ""
    path = instance.root("workspace") / text_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _sidecar_text(path: Path) -> tuple[str, str]:
    candidates = [
        path.with_name(path.name + ".ocr.txt"),
        path.with_suffix(".ocr.txt"),
        path.with_name(path.stem + ".ocr.txt"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8", errors="ignore"), str(candidate)
    return "", ""


def _parse_rapidocr_result(result: Any) -> str:
    if not result:
        return ""
    values = result[0] if isinstance(result, tuple) else result
    lines: list[str] = []
    for item in values or []:
        if isinstance(item, str):
            lines.append(item)
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            if isinstance(item[1], str):
                lines.append(item[1])
            elif isinstance(item[1], (list, tuple)) and item[1] and isinstance(item[1][0], str):
                lines.append(item[1][0])
    return "\n".join(line for line in lines if line.strip())


def _rapidocr_image(path: Path) -> str:
    try:
        from rapidocr import RapidOCR  # type: ignore
    except ImportError:
        return ""
    try:
        engine = RapidOCR()
        return _parse_rapidocr_result(engine(str(path)))
    except Exception:  # noqa: BLE001
        return ""


def _render_pdf_pages(instance: InstanceConfig, row: dict[str, str], source: Path, max_pages: int) -> list[Path]:
    try:
        import fitz  # type: ignore
    except ImportError:
        return []

    render_dir = _docai_dir(instance) / "rendered_pages"
    render_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    document = fitz.open(str(source))
    try:
        for index in range(min(document.page_count, max_pages)):
            page = document.load_page(index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            out = render_dir / f"{row.get('doc_id')}.p{index + 1:03d}.png"
            pixmap.save(str(out))
            rendered.append(out)
    finally:
        document.close()
    return rendered


def _rapidocr_document(instance: InstanceConfig, row: dict[str, str], source: Path, max_pages: int) -> str:
    ext = row.get("extension", "").lower()
    if ext in IMAGE_EXTENSIONS:
        return _rapidocr_image(source)
    if ext == "pdf":
        parts = [_rapidocr_image(path) for path in _render_pdf_pages(instance, row, source, max_pages)]
        return "\n\n".join(part for part in parts if part.strip())
    return ""


def _gutenocr_document(_instance: InstanceConfig, _row: dict[str, str], _source: Path) -> str:
    # GutenOCR is intentionally adapter-only for v1: wire the interface without
    # assuming a package name or model repository that may change.
    return ""


def run_ocr(
    instance: InstanceConfig,
    run: RunContext,
    *,
    doc_id: str | None = None,
    mode: str | None = "local_basic",
    engine: str | None = None,
) -> Path:
    settings = instance.docai_settings(mode)
    registry_path, fields, rows = _read_rows(instance)
    enabled_backends = set(settings["enabled_backends"])
    selected = (engine or "").strip().lower().replace("-", "_")
    processed = 0
    lifted = 0

    for row in rows:
        if not _matches(row, doc_id):
            continue
        if row.get("status_ocr") != "OCR_REQUIRED" and not doc_id:
            continue

        source = _source_path(instance, row)
        if not source.exists():
            row["notes"] = append_note(row.get("notes", ""), "DocAI OCR: fichier source introuvable.")
            continue

        processed += 1
        text = ""
        used_engine = ""
        sidecar, sidecar_path = _sidecar_text(source)
        if sidecar and (not selected or selected == "sidecar_ocr"):
            text = sidecar
            used_engine = "sidecar_ocr"
            row["notes"] = append_note(row.get("notes", ""), f"DocAI OCR: texte sidecar utilise ({sidecar_path}).")
        elif (not selected or selected == "rapidocr") and "rapidocr" in enabled_backends:
            text = _rapidocr_document(instance, row, source, int(settings["max_pages"]))
            used_engine = "rapidocr" if text else ""
        elif selected == "gutenocr" or "gutenocr" in enabled_backends:
            text = _gutenocr_document(instance, row, source)
            used_engine = "gutenocr" if text else ""

        if text.strip():
            row["text_path"] = _write_text_artifact(instance, row, "ocr.txt", text)
            row["text_char_count"] = str(len(text.strip()))
            row["status_ocr"] = "OCR_DONE"
            row["ocr_engine"] = used_engine
            row["extraction_level"] = _append_level(row.get("extraction_level", ""), f"P2_LOCAL_OCR_{used_engine.upper()}")
            row["text_quality"] = "strong" if len(text.strip()) >= 80 else "weak"
            lifted += 1
        else:
            row["ocr_engine"] = selected or "unavailable"
            row["notes"] = append_note(row.get("notes", ""), "DocAI OCR: aucun backend local n'a produit de texte exploitable.")

    _write_rows(registry_path, fields, rows)
    run.log_action("write", registry_path, f"docai ocr processed={processed} lifted={lifted}")
    return registry_path


def _docling_markdown(source: Path, fallback_text: str) -> tuple[str, str]:
    try:
        from docling.document_converter import DocumentConverter  # type: ignore
    except ImportError:
        return fallback_text, "fallback_text_docling_unavailable"

    try:
        result = DocumentConverter().convert(str(source))
        document = getattr(result, "document", None)
        if document and hasattr(document, "export_to_markdown"):
            return str(document.export_to_markdown()), "docling"
    except Exception:  # noqa: BLE001
        pass
    return fallback_text, "fallback_text_docling_error"


def _write_docling(instance: InstanceConfig, row: dict[str, str], source: Path) -> None:
    fallback_text = _text_from_existing_path(instance, row)
    markdown, engine = _docling_markdown(source, fallback_text)
    if not markdown.strip():
        markdown = f"# {row.get('file_name', row.get('doc_id', 'document'))}\n\n"
        markdown += "DocAI: aucun texte source disponible pour l'enrichissement Docling.\n"

    row["docling_path"] = _write_text_artifact(instance, row, "docling.md", markdown)
    row["extraction_level"] = _append_level(row.get("extraction_level", ""), "P1_DOCLING_STRUCTURE")
    if engine != "docling":
        row["notes"] = append_note(row.get("notes", ""), f"DocAI Docling: {engine}.")


def _write_layout_payload(instance: InstanceConfig, row: dict[str, str], backend: str) -> None:
    text = _text_from_existing_path(instance, row)
    payload = {
        "doc_id": row.get("doc_id", ""),
        "file_name": row.get("file_name", ""),
        "backend": backend,
        "status": "READY_FOR_MODEL" if module_available("transformers") else "BACKEND_UNAVAILABLE",
        "source_text_chars": len(text),
        "note": "Layout backend hook; model-specific extraction remains optional and local-only.",
    }
    row["layout_path"] = _write_json_artifact(instance, row, "layout.json", payload)
    row["extraction_level"] = _append_level(row.get("extraction_level", ""), f"P3_LAYOUT_{backend.upper()}")


def _write_qwen_review_payload(instance: InstanceConfig, row: dict[str, str]) -> None:
    payload = {
        "doc_id": row.get("doc_id", ""),
        "file_name": row.get("file_name", ""),
        "backend": "qwen_vl",
        "status": "BACKEND_UNAVAILABLE" if not module_available("transformers") else "READY_FOR_LOCAL_REVIEW",
        "privacy": "local_only",
        "note": "Qwen VL review is evidence-only and must not be treated as final accounting validation.",
    }
    _write_json_artifact(instance, row, "qwen_vl.review.json", payload)
    row["ai_review_status"] = str(payload["status"])
    row["extraction_level"] = _append_level(row.get("extraction_level", ""), "P4_LOCAL_QWEN_VL_REVIEW")


def enrich(
    instance: InstanceConfig,
    run: RunContext,
    *,
    backend: str = "docling",
    doc_id: str | None = None,
    mode: str | None = "local_basic",
) -> Path:
    settings = instance.docai_settings(mode)
    normalized_backend = backend.strip().lower().replace("-", "_")
    if normalized_backend not in {item.replace("-", "_") for item in ENRICH_BACKENDS}:
        raise ValueError(f"Unsupported DocAI backend: {backend}")

    registry_path, fields, rows = _read_rows(instance)
    processed = 0
    for row in rows:
        if not _matches(row, doc_id):
            continue
        source = _source_path(instance, row)
        if not source.exists():
            row["notes"] = append_note(row.get("notes", ""), "DocAI enrich: fichier source introuvable.")
            continue
        if normalized_backend == "qwen_vl" and settings["mode"] != "local_heavy":
            row["ai_review_status"] = "DISABLED_REQUIRES_LOCAL_HEAVY"
            row["notes"] = append_note(row.get("notes", ""), "DocAI Qwen VL: active uniquement en mode local_heavy.")
            continue

        if normalized_backend == "docling":
            _write_docling(instance, row, source)
        elif normalized_backend == "qwen_vl":
            _write_qwen_review_payload(instance, row)
        elif normalized_backend in {"layoutlmv3", "layoutalm"}:
            _write_layout_payload(instance, row, normalized_backend)
        processed += 1

    _write_rows(registry_path, fields, rows)
    run.log_action("write", registry_path, f"docai enrich backend={normalized_backend} processed={processed}")
    return registry_path


def process_after_native_extract(
    instance: InstanceConfig,
    run: RunContext,
    *,
    doc_id: str | None = None,
    mode: str | None = None,
) -> Path:
    settings = instance.docai_settings(mode)
    if settings["mode"] == "off":
        return instance.register("documents")

    if "docling" in settings["enabled_backends"]:
        enrich(instance, run, backend="docling", doc_id=doc_id, mode=settings["mode"])
    if OCR_BACKENDS.intersection(set(settings["enabled_backends"])):
        run_ocr(instance, run, doc_id=doc_id, mode=settings["mode"])
    if settings["mode"] == "local_heavy":
        if "layoutlmv3" in settings["enabled_backends"]:
            enrich(instance, run, backend="layoutlmv3", doc_id=doc_id, mode=settings["mode"])
        if "qwen_vl" in settings["enabled_backends"]:
            enrich(instance, run, backend="qwen_vl", doc_id=doc_id, mode=settings["mode"])
    return instance.register("documents")


def docai_status(instance: InstanceConfig, mode: str | None = None) -> dict[str, Any]:
    settings = instance.docai_settings(mode)
    return {
        "mode": settings["mode"],
        "privacy": settings["privacy"],
        "device": settings["device"],
        "models_dir": settings["models_dir"],
        "enabled_backends": settings["enabled_backends"],
        "modules": {
            "fitz": module_available("fitz"),
            "docling": module_available("docling"),
            "rapidocr": module_available("rapidocr"),
            "torch": module_available("torch"),
            "transformers": module_available("transformers"),
        },
    }


def normalize_backend_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
