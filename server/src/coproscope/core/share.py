from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from .common import load_structured_file

EXTRACTOR_MANIFEST_REL = "server/src/coproscope/extractors/invoices/extractors.manifest.json"
PUBLIC_EXTRACTOR_STATUSES = {"generalizable", "candidate_generalizable", "candidat_generalisable"}


def _normalized(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def _matches_allowed(rel: str, allowed_paths: list[str]) -> bool:
    return any(rel == allowed_path.rstrip("/") or rel.startswith(allowed_path.rstrip("/") + "/") for allowed_path in allowed_paths)


def _matches_prefix(rel: str, prefixes: list[str]) -> bool:
    return any(rel == prefix.rstrip("/") or rel.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def _matches_pattern(rel: str, patterns: list[str]) -> bool:
    rel_lower = rel.lower()
    return any(pattern.lower() in rel_lower for pattern in patterns)


def _audit_invoice_extractors(repo_root: Path, shareable: list[str], blocked: list[str]) -> dict[str, object]:
    manifest_path = repo_root / EXTRACTOR_MANIFEST_REL
    if not manifest_path.exists():
        return {
            "manifest_path": "",
            "provider_extractors": [],
            "private_violations": [],
        }

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    provider_extractors: list[dict[str, str]] = []
    reconciliation_modules: list[dict[str, str]] = []
    visual_review_modules: list[dict[str, str]] = []
    extractor_generator_modules: list[dict[str, str]] = []
    private_violations: list[str] = []

    def audit_manifest_item(item: dict[str, object], key_field: str) -> dict[str, str]:
        module_path = str(item.get("module_path", "")).replace("\\", "/")
        status = str(item.get("status", "private"))
        share_status = "shareable" if module_path in shareable else "not_shareable"
        if status not in PUBLIC_EXTRACTOR_STATUSES and module_path:
            private_violations.append(module_path)
            if module_path in shareable:
                shareable.remove(module_path)
            if module_path not in blocked:
                blocked.append(module_path)
            share_status = "blocked_private"
        return {
            key_field: str(item.get(key_field, "")),
            "module_path": module_path,
            "status": status,
            "share_status": share_status,
        }

    for item in manifest.get("provider_extractors", []):
        provider_extractors.append(audit_manifest_item(item, "provider_key"))

    for item in manifest.get("default_reconciliation_modules", []):
        reconciliation_modules.append(audit_manifest_item(item, "module_key"))

    for item in manifest.get("default_visual_review_modules", []):
        visual_review_modules.append(audit_manifest_item(item, "module_key"))

    for item in manifest.get("extractor_generator_modules", []):
        extractor_generator_modules.append(audit_manifest_item(item, "module_key"))

    return {
        "manifest_path": EXTRACTOR_MANIFEST_REL,
        "provider_extractors": provider_extractors,
        "default_reconciliation_modules": reconciliation_modules,
        "default_visual_review_modules": visual_review_modules,
        "extractor_generator_modules": extractor_generator_modules,
        "private_violations": private_violations,
    }


def audit_repo(repo_root: Path, config_path: Path) -> dict[str, object]:
    config = load_structured_file(config_path)
    allowed = [str(item) for item in config.get("chemins_autorises_partage", config.get("share_allowed_paths", []))]
    ignored_prefixes = [str(item).rstrip("/") + "/" for item in config.get("prefixes_ignores", config.get("ignore_prefixes", []))]
    denied_prefixes = [str(item).rstrip("/") + "/" for item in config.get("prefixes_jamais_partager", config.get("never_share_prefixes", []))]
    denied_patterns = [str(item) for item in config.get("motifs_jamais_partager", config.get("never_share_patterns", []))]

    shareable: list[str] = []
    blocked: list[str] = []
    ignored: list[str] = []

    for root, dirnames, filenames in os.walk(repo_root):
        root_path = Path(root)
        kept_dirs: list[str] = []

        for dirname in sorted(dirnames):
            dir_path = root_path / dirname
            rel_dir = _normalized(dir_path, repo_root)
            rel_dir_marker = rel_dir + "/"
            if _matches_prefix(rel_dir, ignored_prefixes):
                ignored.append(rel_dir_marker)
                continue
            if _matches_prefix(rel_dir, denied_prefixes) or _matches_pattern(rel_dir_marker, denied_patterns):
                blocked.append(rel_dir_marker)
                continue
            kept_dirs.append(dirname)

        dirnames[:] = kept_dirs

        for filename in sorted(filenames):
            path = root_path / filename
            rel = _normalized(path, repo_root)
            if _matches_prefix(rel, ignored_prefixes):
                ignored.append(rel)
                continue
            if _matches_prefix(rel, denied_prefixes) or _matches_pattern(rel, denied_patterns):
                blocked.append(rel)
                continue
            if _matches_allowed(rel, allowed):
                shareable.append(rel)
            else:
                ignored.append(rel)

    extractor_audit = _audit_invoice_extractors(repo_root, shareable, blocked)

    return {
        "repo_root": str(repo_root),
        "shareable": shareable,
        "blocked": blocked,
        "ignored": ignored,
        "public_repo_url": str(config.get("url_depot_public", config.get("public_repo_url", ""))),
        "generalizable_extractors": extractor_audit,
    }


def export_shareable(repo_root: Path, config_path: Path, output_dir: Path, clean: bool = False) -> dict[str, object]:
    result = audit_repo(repo_root, config_path)
    destination = output_dir.resolve()
    repo_root = repo_root.resolve()

    if clean and destination.exists():
        if destination == repo_root or destination == repo_root.parent:
            raise ValueError(f"Refusing to clean unsafe destination: {destination}")
        shutil.rmtree(destination)

    destination.mkdir(parents=True, exist_ok=True)

    for rel in result["shareable"]:
        source = repo_root / str(rel)
        target = destination / str(rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    manifest = {
        "repo_root": result["repo_root"],
        "public_repo_url": result["public_repo_url"],
        "shareable": result["shareable"],
        "blocked": result["blocked"],
        "ignored": result["ignored"],
        "generalizable_extractors": result["generalizable_extractors"],
        "export_dir": str(destination),
        "exported_count": len(result["shareable"]),
    }
    manifest_path = destination / "share-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    manifest["manifest_path"] = str(manifest_path)
    return manifest
