from __future__ import annotations

import hashlib
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..core.common import InstanceConfig, RunContext, now_iso, read_csv, relative_to, safe_name
from ..modules import accounting, agscope, biffageops, docai, docuscope, factureops, privacyops


MAX_UPLOAD_FILES = 50
MAX_UPLOAD_BYTES = 250 * 1024 * 1024
MAX_DEPOSIT_BYTES = 500 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024
DEPOSIT_ROOT_NAME = "_depot_ui"
DEPOSIT_ID_RE = re.compile(r"^DEPOT-\d{8}T\d{6}Z(?:-\d+)?$")
ALLOWED_UPLOAD_EXTENSIONS = {
    "bmp",
    "csv",
    "docx",
    "htm",
    "html",
    "jpeg",
    "jpg",
    "json",
    "md",
    "pdf",
    "png",
    "tif",
    "tiff",
    "tsv",
    "txt",
    "xlsx",
    "yaml",
    "yml",
}

SAFE_EXPORT_DIRS = {
    "registers",
    "outputs/reports",
    "outputs/privacy",
    "outputs/accounting",
    "outputs/deposits",
}
SAFE_EXPORT_SUFFIXES = {".csv", ".json", ".md", ".txt", ".tsv"}
BLOCKED_EXPORT_PARTS = {"raw", "restricted", "logs", ".git", "__pycache__", "private"}
BLOCKED_EXPORT_MARKERS = (
    ".env",
    "table_correspondance",
    "correspondance_biffage",
    "redaction_map",
    "mapping",
)
BLOCKED_EXPORT_CONTENT_PATTERNS = (
    re.compile(rb"[A-Za-z]:[\\/]", re.IGNORECASE),
    re.compile(rb"file://", re.IGNORECASE),
    re.compile(rb"(?:^|[\\/\s\"'=,:])/(?:Users|home)[\\/]", re.IGNORECASE),
    re.compile(rb"(?:^|[\\/\s\"'=,:])(?:raw|restricted|logs|private|system)[\\/]", re.IGNORECASE),
)
DEPOSIT_CONTEXT_KEYS = {
    "intent",
    "status",
    "return",
    "piece_detail",
    "missing_for",
    "request_id",
    "action",
    "source",
    "piece_id",
    "categorie",
}
BLOCKED_DEPOSIT_CONTEXT_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/]", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"\\\\"),
    re.compile(r"(?:^|[\\/\s\"'=,:])/(?:Users|home)[\\/]", re.IGNORECASE),
    re.compile(r"(?:^|[\\/\s\"'=,:])(?:raw|restricted|logs|private|system)[\\/]", re.IGNORECASE),
)


class DepositError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def deposits_dir(instance: InstanceConfig) -> Path:
    try:
        root = instance.root("outputs")
    except KeyError:
        root = instance.instance_root / "outputs"
    path = root / "deposits"
    path.mkdir(parents=True, exist_ok=True)
    return path


def deposit_target_root(instance: InstanceConfig) -> Path:
    physical_deposit = instance.physical_deposit_path()
    if physical_deposit is not None:
        return physical_deposit
    raw_roots = instance.root_list("raw")
    raw_root = raw_roots[0] if raw_roots else instance.root("raw")
    return raw_root / DEPOSIT_ROOT_NAME


def _validate_deposit_id(deposit_id: str) -> str:
    cleaned = str(deposit_id or "").strip()
    if not DEPOSIT_ID_RE.fullmatch(cleaned):
        raise DepositError("Identifiant de depot invalide.", 400)
    return cleaned


def deposit_manifest_path(instance: InstanceConfig, deposit_id: str) -> Path:
    deposit_id = _validate_deposit_id(deposit_id)
    root = deposits_dir(instance).resolve()
    path = (root / f"{deposit_id}.json").resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise DepositError("Chemin de manifeste invalide.", 400) from exc
    return path


def read_deposit_manifest(instance: InstanceConfig, deposit_id: str) -> dict[str, Any] | None:
    try:
        deposit_id = _validate_deposit_id(deposit_id)
        path = deposit_manifest_path(instance, deposit_id)
    except DepositError:
        return None
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    payload["deposit_id"] = deposit_id
    return payload


def read_deposit_manifests(instance: InstanceConfig, limit: int = 8) -> list[dict[str, Any]]:
    root = deposits_dir(instance)
    manifests: list[dict[str, Any]] = []
    for path in sorted(root.glob("DEPOT-*.json"), reverse=True):
        try:
            deposit_id = _validate_deposit_id(path.stem)
        except DepositError:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            payload["deposit_id"] = deposit_id
            manifests.append(payload)
        if len(manifests) >= limit:
            break
    return manifests


def latest_deposit_manifest(instance: InstanceConfig) -> dict[str, Any] | None:
    manifests = read_deposit_manifests(instance, limit=1)
    return manifests[0] if manifests else None


def write_deposit_manifest(instance: InstanceConfig, manifest: dict[str, Any]) -> Path:
    deposit_id = _validate_deposit_id(str(manifest["deposit_id"]))
    manifest["deposit_id"] = deposit_id
    path = deposit_manifest_path(instance, deposit_id)
    manifest["updated_at"] = now_iso()
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def _new_deposit_id(instance: InstanceConfig) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = f"DEPOT-{stamp}"
    candidate = base
    index = 2
    while deposit_manifest_path(instance, candidate).exists():
        candidate = f"{base}-{index}"
        index += 1
    return candidate


def _relative(instance: InstanceConfig, path: Path) -> str:
    return relative_to(instance.root("workspace"), path).replace("\\", "/")


def _unique_target(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem or "document"
    suffix = path.suffix
    index = 2
    while True:
        candidate = path.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def _upload_filename(upload: Any) -> str:
    filename = str(getattr(upload, "filename", "") or "").strip()
    if not filename:
        return ""
    return Path(filename.replace("\\", "/")).name


def _validate_upload_name(filename: str) -> str:
    extension = Path(filename).suffix.lower().lstrip(".")
    if not extension or extension not in ALLOWED_UPLOAD_EXTENSIONS:
        raise DepositError("Type de fichier non accepte pour le depot UI.", 415)
    return extension


def _write_upload_file(upload: Any, target: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    file_obj = getattr(upload, "file", None)
    if file_obj is None or not hasattr(file_obj, "read"):
        raise DepositError("Upload invalide.", 400)
    try:
        file_obj.seek(0)
    except (AttributeError, OSError):
        pass
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as handle:
        while True:
            chunk = file_obj.read(UPLOAD_CHUNK_BYTES)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                handle.close()
                target.unlink(missing_ok=True)
                raise DepositError("Fichier trop volumineux pour le depot UI.", 413)
            digest.update(chunk)
            handle.write(chunk)
    if size == 0:
        target.unlink(missing_ok=True)
        raise DepositError("Fichier vide refuse.", 400)
    return size, digest.hexdigest()


def _public_deposit_context(context: Mapping[str, object] | None) -> dict[str, str]:
    if not context:
        return {}
    safe: dict[str, str] = {}
    for key in DEPOSIT_CONTEXT_KEYS:
        text = " ".join(str(context.get(key) or "").replace("\x00", " ").split())
        if not text or any(pattern.search(text) for pattern in BLOCKED_DEPOSIT_CONTEXT_PATTERNS):
            continue
        safe[key] = text[:180]
    return safe


def create_deposit_from_uploads(
    instance: InstanceConfig,
    uploads: Iterable[Any],
    *,
    context: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    upload_list = [upload for upload in uploads if _upload_filename(upload)]
    if not upload_list:
        raise DepositError("Aucun fichier recu.", 400)
    if len(upload_list) > MAX_UPLOAD_FILES:
        raise DepositError("Trop de fichiers dans un seul depot.", 413)

    deposit_id = _new_deposit_id(instance)
    target_dir = deposit_target_root(instance) / deposit_id
    manifest: dict[str, Any] = {
        "deposit_id": deposit_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "target_dir": _relative(instance, target_dir),
        "files": [],
        "doc_ids": [],
        "steps": [],
        "status": "uploaded",
    }
    safe_context = _public_deposit_context(context)
    if safe_context:
        manifest["context"] = safe_context

    total_size = 0
    try:
        for upload in upload_list:
            original = _upload_filename(upload)
            _validate_upload_name(original)
            stored_name = safe_name(original)
            target = _unique_target(target_dir / stored_name)
            size, digest = _write_upload_file(upload, target)
            total_size += size
            if total_size > MAX_DEPOSIT_BYTES:
                target.unlink(missing_ok=True)
                raise DepositError("Depot UI trop volumineux.", 413)
            try:
                upload.file.close()
            except (AttributeError, OSError):
                pass
            manifest["files"].append(
                {
                    "original_name": original,
                    "stored_name": target.name,
                    "path": _relative(instance, target),
                    "size_bytes": size,
                    "sha256": digest,
                }
            )
    except Exception:
        shutil.rmtree(target_dir, ignore_errors=True)
        try:
            if target_dir.parent.name == DEPOSIT_ROOT_NAME and not any(target_dir.parent.iterdir()):
                target_dir.parent.rmdir()
        except OSError:
            pass
        raise

    write_deposit_manifest(instance, manifest)
    return manifest


def _count_rows(path: Path | None) -> int:
    if path is None:
        return 0
    _, rows = read_csv(path)
    return len(rows)


def _document_rows(instance: InstanceConfig) -> list[dict[str, str]]:
    try:
        _, rows = read_csv(instance.register("documents"))
    except KeyError:
        return []
    return rows


def _doc_ids_for_deposit(instance: InstanceConfig, manifest: dict[str, Any]) -> list[str]:
    prefix = str(manifest.get("target_dir", "")).replace("\\", "/").rstrip("/") + "/"
    doc_ids: list[str] = []
    for row in _document_rows(instance):
        original_path = row.get("original_path", "").replace("\\", "/")
        if original_path.startswith(prefix) and row.get("doc_id"):
            doc_ids.append(row["doc_id"])
    return sorted(set(doc_ids))


def _manifest_summary(instance: InstanceConfig, manifest: dict[str, Any]) -> dict[str, Any]:
    privacy_dir = instance.artifact("privacy_dir")
    return {
        "documents": _count_rows(instance.register("documents")),
        "privacy_reviews": _count_rows(privacyops.privacy_screening_path(instance)),
        "redaction_queue": _count_rows(privacy_dir / "file_biffage.csv"),
        "doc_ids": _doc_ids_for_deposit(instance, manifest),
    }


def _run_step(
    instance: InstanceConfig,
    manifest: dict[str, Any],
    name: str,
    runner: Any,
) -> dict[str, Any]:
    step: dict[str, Any] = {
        "name": name,
        "status": "running",
        "started_at": now_iso(),
        "finished_at": "",
        "before": _manifest_summary(instance, manifest),
        "after": {},
        "result": {},
        "error": "",
    }
    manifest.setdefault("steps", []).append(step)
    write_deposit_manifest(instance, manifest)
    try:
        result = runner()
        step["status"] = "ok"
        step["result"] = result if isinstance(result, dict) else {"path": str(result)}
    except Exception as exc:  # noqa: BLE001 - UI pipeline records failures instead of hiding them.
        step["status"] = "error"
        step["error"] = str(exc)
    step["finished_at"] = now_iso()
    step["after"] = _manifest_summary(instance, manifest)
    manifest["doc_ids"] = step["after"]["doc_ids"]
    manifest["status"] = "error" if step["status"] == "error" else "processed"
    write_deposit_manifest(instance, manifest)
    return step


def run_light_pipeline(instance: InstanceConfig, manifest: dict[str, Any]) -> dict[str, Any]:
    run = RunContext(instance, f"ui depot light {manifest['deposit_id']}")
    _run_step(instance, manifest, "inventory", lambda: docuscope.inventory(instance, run))
    doc_ids = _doc_ids_for_deposit(instance, manifest)
    for doc_id in doc_ids:
        _run_step(instance, manifest, f"extract_text:{doc_id}", lambda doc_id=doc_id: docuscope.extract_text(instance, run, doc_id=doc_id))
    _run_step(instance, manifest, "classify", lambda: docuscope.classify(instance, run, copy_files=False))
    _run_step(instance, manifest, "privacy_screening", lambda: privacyops.screen_existing(instance, run, include_generated=False))
    _run_step(instance, manifest, "redaction_queue", lambda: biffageops.build_redaction_queue(instance, run))
    run.finish("OK" if manifest.get("status") != "error" else "WARN", f"deposit={manifest['deposit_id']}")
    return manifest


def run_docai_pipeline(instance: InstanceConfig, manifest: dict[str, Any]) -> dict[str, Any]:
    run = RunContext(instance, f"ui depot docai {manifest['deposit_id']}")
    doc_ids = _doc_ids_for_deposit(instance, manifest) or list(manifest.get("doc_ids", []))
    for doc_id in doc_ids:
        _run_step(
            instance,
            manifest,
            f"docai_local_heavy:{doc_id}",
            lambda doc_id=doc_id: docai.process_after_native_extract(instance, run, doc_id=doc_id, mode="local-heavy"),
        )
    _run_step(instance, manifest, "classify_after_docai", lambda: docuscope.classify(instance, run, copy_files=False))
    _run_step(instance, manifest, "privacy_after_docai", lambda: privacyops.screen_existing(instance, run, include_generated=False))
    _run_step(instance, manifest, "redaction_queue_after_docai", lambda: biffageops.build_redaction_queue(instance, run))
    run.finish("OK" if manifest.get("status") != "error" else "WARN", f"deposit={manifest['deposit_id']}")
    return manifest


def run_docops_pipeline(instance: InstanceConfig, manifest: dict[str, Any]) -> dict[str, Any]:
    run = RunContext(instance, f"ui depot docops {manifest['deposit_id']}")
    _run_step(instance, manifest, "missing_docs", lambda: docuscope.missing_docs(instance, run))
    _run_step(instance, manifest, "kpi", lambda: docuscope.compute_kpis(instance, run))
    _run_step(instance, manifest, "ag", lambda: agscope.analyze(instance, run))
    run.finish("OK" if manifest.get("status") != "error" else "WARN", f"deposit={manifest['deposit_id']}")
    return manifest


def run_accounting_pipeline(instance: InstanceConfig, manifest: dict[str, Any], year: int) -> dict[str, Any]:
    run = RunContext(instance, f"ui depot compta {manifest['deposit_id']}")
    _run_step(instance, manifest, "invoices", lambda: factureops.extract_invoices(instance, run, year))
    _run_step(instance, manifest, "accounting_reconstruct", lambda: accounting.reconstruct_accounting(instance, run, year))
    _run_step(instance, manifest, "accounting_controls", lambda: accounting.accounting_controls(instance, run, year))
    run.finish("OK" if manifest.get("status") != "error" else "WARN", f"deposit={manifest['deposit_id']}")
    return manifest


def run_all_non_heavy_pipeline(instance: InstanceConfig, manifest: dict[str, Any], year: int) -> dict[str, Any]:
    run_light_pipeline(instance, manifest)
    run_docops_pipeline(instance, manifest)
    run_accounting_pipeline(instance, manifest, year)
    return manifest


def export_catalog() -> list[dict[str, str]]:
    return [
        {"label": "Actions CSV", "href": "/exports/actions.csv", "kind": "csv"},
        {"label": "Actions Markdown", "href": "/exports/actions.md", "kind": "markdown"},
        {"label": "Pack local prive", "href": "/exports/local.zip", "kind": "zip"},
    ]


def _is_safe_export_path(instance: InstanceConfig, path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() not in SAFE_EXPORT_SUFFIXES:
        return False
    try:
        relative = path.resolve().relative_to(instance.instance_root.resolve())
    except ValueError:
        return False
    parts = [part.replace("\\", "/").lower() for part in relative.parts]
    normalized = "/".join(parts)
    if any(part in BLOCKED_EXPORT_PARTS for part in parts):
        return False
    if any(marker in normalized for marker in BLOCKED_EXPORT_MARKERS):
        return False
    return any(normalized == safe_dir or normalized.startswith(f"{safe_dir}/") for safe_dir in SAFE_EXPORT_DIRS)


def _export_content_is_safe(content: bytes) -> bool:
    return not any(pattern.search(content) for pattern in BLOCKED_EXPORT_CONTENT_PATTERNS)


def _sanitize_generated_export(content: str) -> str:
    data = content.encode("utf-8", errors="ignore")
    for pattern in BLOCKED_EXPORT_CONTENT_PATTERNS:
        data = pattern.sub(b"[reference locale masquee]", data)
    return data.decode("utf-8", errors="ignore")


def _iter_safe_export_files(instance: InstanceConfig) -> list[Path]:
    paths: list[Path] = []
    for safe_dir in SAFE_EXPORT_DIRS:
        root = instance.instance_root / safe_dir
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if _is_safe_export_path(instance, path):
                paths.append(path)
    return paths


def build_local_export_zip(
    instance: InstanceConfig,
    *,
    year: int,
    actions_csv: str,
    actions_markdown: str,
) -> bytes:
    buffer = BytesIO()
    manifest = {
        "created_at": now_iso(),
        "instance_id": instance.instance_id,
        "year": year,
        "policy": "local_no_sensitive_roots_or_secret_mappings",
        "files": [],
        "skipped": [],
    }
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        generated = {
            f"exports/coproscope_actions_{year}.csv": actions_csv,
            f"exports/coproscope_actions_{year}.md": actions_markdown,
        }
        for name, content in generated.items():
            sanitized = _sanitize_generated_export(content)
            if not _export_content_is_safe(sanitized.encode("utf-8", errors="ignore")):
                manifest["skipped"].append({"path": name, "reason": "unsafe_content"})
                continue
            archive.writestr(name, sanitized)
            manifest["files"].append(name)
        for path in _iter_safe_export_files(instance):
            arcname = relative_to(instance.instance_root, path).replace("\\", "/")
            try:
                content = path.read_bytes()
            except OSError:
                manifest["skipped"].append({"path": arcname, "reason": "read_error"})
                continue
            if not _export_content_is_safe(content):
                if arcname.startswith("outputs/deposits/"):
                    content = _sanitize_generated_export(content.decode("utf-8", errors="ignore")).encode("utf-8")
                if not _export_content_is_safe(content):
                    manifest["skipped"].append({"path": arcname, "reason": "unsafe_content"})
                    continue
            archive.writestr(arcname, content)
            manifest["files"].append(arcname)
        archive.writestr("export_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=True) + "\n")
    return buffer.getvalue()
