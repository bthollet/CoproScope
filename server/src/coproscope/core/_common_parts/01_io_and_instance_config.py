from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SERVER_ROOT = PACKAGE_ROOT.parents[2]

ROOT_KEY_ALIASES = {
    "workspace": ("espace_travail", "workspace"),
    "raw": ("bruts", "brut", "raw"),
    "system": ("systeme", "system"),
    "outputs": ("sorties", "outputs"),
    "staging": ("preparation", "staging"),
    "logs": ("journaux", "logs"),
    "restricted": ("restreint", "restreints", "restricted"),
}

REGISTER_KEY_ALIASES = {
    "documents": ("documents",),
    "duplicates": ("doublons", "duplicates"),
    "manifest": ("manifeste", "manifest"),
    "requests": ("demandes", "requests"),
    "ag": ("assemblees_generales", "ag"),
    "findings": ("constats", "findings"),
    "kpi": ("indicateurs", "kpi"),
    "privacy_screening": ("screening_confidentialite", "privacy_screening"),
    "redactions": ("biffages", "redactions"),
    "redaction_map": ("table_correspondance_biffage", "redaction_map"),
}

MATRIX_KEY_ALIASES = {
    "proofs": ("preuves", "proofs"),
    "extranet": ("extranet",),
    "due_diligence_dir": ("dossier_due_diligence", "dossier_diligence", "due_diligence_dir"),
}

ARTIFACT_KEY_ALIASES = {
    "text_dir": ("dossier_textes", "text_dir"),
    "classified_dir": ("dossier_classes", "classified_dir"),
    "reports_dir": ("dossier_rapports", "reports_dir"),
    "docai_dir": ("dossier_docai", "docai_dir"),
    "accounting_dir": ("dossier_comptabilite", "accounting_dir"),
    "grist_dir": ("dossier_grist", "grist_dir"),
    "evidence_dir": ("dossier_evidence", "evidence_dir"),
    "privacy_dir": ("dossier_confidentialite", "privacy_dir"),
    "redacted_dir": ("dossier_biffages", "redacted_dir"),
}

DEFAULT_DOCUMENT_FIELDS = [
    "doc_id",
    "instance_id",
    "entity_id",
    "scope",
    "sha256",
    "original_path",
    "file_name",
    "extension",
    "size_bytes",
    "last_modified",
    "first_seen",
    "source_zone",
    "source_kind",
    "lot",
    "document_type",
    "suspected_date",
    "emitter",
    "status_ocr",
    "classification_status",
    "text_path",
    "page_count",
    "text_char_count",
    "extraction_level",
    "text_quality",
    "ocr_engine",
    "docling_path",
    "layout_path",
    "ai_review_status",
    "sensitivity",
    "raw_max_college",
    "derivative_max_college",
    "publication_form",
    "restriction_reasons",
    "personal_data_level",
    "ip_status",
    "ai_processing_ceiling",
    "review_required",
    "policy_confidence",
    "required_transformations",
    "screening_signals",
    "privacy_review_status",
    "redaction_status",
    "redaction_mode",
    "redacted_path",
    "redacted_sha256",
    "redaction_map_id",
    "notes",
]

REQUEST_FIELDS = [
    "request_id",
    "date",
    "subject",
    "expected_piece",
    "status",
    "last_follow_up",
    "priority",
    "response_due_date",
    "source_document",
    "related_doc_ids",
    "notes",
]

AG_FIELDS = [
    "ag_id",
    "doc_id",
    "file_name",
    "document_type",
    "detected_date",
    "resolution_count",
    "annex_hits",
    "majority_terms",
    "missing_annex_signals",
    "notes",
]

FINDING_FIELDS = [
    "finding_id",
    "category",
    "severity",
    "source_ref",
    "fact",
    "diligence",
    "status",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def safe_name(name: str, max_length: int = 150) -> str:
    cleaned = re.sub(r"[^\w.\- ]+", "_", name, flags=re.UNICODE).strip()
    return re.sub(r"\s+", "_", cleaned)[:max_length] or "document"


def append_note(existing: str, note: str) -> str:
    if not existing:
        return note
    if note in existing:
        return existing
    return f"{existing} | {note}"


def detect_date(value: str) -> str:
    match = re.search(r"(20\d{2})[-_. ]([01]\d)(?:[-_. ]([0-3]\d))?", value)
    if not match:
        return ""
    year, month, day = match.groups()
    if day:
        return f"{year}-{month}-{day}"
    return f"{year}-{month}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def resource_path(section: str, filename: str) -> Path:
    return PACKAGE_ROOT / section / filename


def load_structured_file(path: Path) -> Any:
    raw = path.read_text(encoding="utf-8-sig")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        if importlib.util.find_spec("yaml"):
            import yaml  # type: ignore

            return yaml.safe_load(raw)
        raise RuntimeError(
            f"Structured file {path} is not JSON-compatible YAML and PyYAML is not available."
        )


def load_template_csv(name: str) -> str:
    return resource_path("templates", name).read_text(encoding="utf-8")


def append_csv_row(path: Path, fieldnames: list[str], row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _first_present(mapping: dict[str, Any], names: tuple[str, ...], default: Any = None) -> Any:
    for name in names:
        if name in mapping and mapping[name] is not None:
            return mapping[name]
    return default


@dataclass
class InstanceConfig:
    path: Path
    payload: dict[str, Any]

    @property
    def instance_root(self) -> Path:
        return self.path.parent

    def _section(self, *names: str) -> dict[str, Any]:
        value = _first_present(self.payload, tuple(names), {})
        return dict(value) if isinstance(value, dict) else {}

    def _section_value(self, section_names: tuple[str, ...], key_names: tuple[str, ...]) -> Any:
        section = self._section(*section_names)
        return _first_present(section, key_names)

    @property
    def instance_id(self) -> str:
        value = _first_present(self.payload, ("identifiant_instance", "instance_id"))
        if value is None:
            raise KeyError(f"Missing instance identifier in {self.path}")
        return str(value)

    @property
    def display_name(self) -> str:
        return str(_first_present(self.payload, ("nom_affichage", "display_name"), self.instance_id))

    @property
    def scope(self) -> str:
        return str(_first_present(self.payload, ("perimetre", "scope"), "copro_simple"))

    @property
    def entity_id(self) -> str:
        return str(_first_present(self.payload, ("identifiant_entite", "entite_id", "entity_id"), "main"))

    def resolve_path(self, value: str | None) -> Path | None:
        if not value:
            return None
        candidate = Path(value)
        if candidate.is_absolute():
            return candidate
        return (self.instance_root / candidate).resolve()

    def root(self, name: str) -> Path:
        aliases = ROOT_KEY_ALIASES.get(name, (name,))
        value = self._section_value(("racines", "roots"), aliases)
        if isinstance(value, list):
            value = value[0] if value else None
        if value is None:
            raise KeyError(f"Missing root '{name}' in {self.path}")
        resolved = self.resolve_path(str(value))
        if resolved is None:
            raise KeyError(f"Unable to resolve root '{name}' in {self.path}")
        return resolved

    def root_list(self, name: str) -> list[Path]:
        aliases = ROOT_KEY_ALIASES.get(name, (name,))
        values = self._section_value(("racines", "roots"), aliases) or []
        if isinstance(values, str):
            values = [values]
        return [self.resolve_path(str(item)) for item in values if self.resolve_path(str(item))]  # type: ignore[list-item]

    def register(self, name: str) -> Path:
        aliases = REGISTER_KEY_ALIASES.get(name, (name,))
        value = self._section_value(("registres", "registers"), aliases)
        if value is None:
            raise KeyError(f"Missing register '{name}' in {self.path}")
        resolved = self.resolve_path(str(value))
        if resolved is None:
            raise KeyError(f"Unable to resolve register '{name}' in {self.path}")
        return resolved

    def matrix(self, name: str) -> Path | None:
        aliases = MATRIX_KEY_ALIASES.get(name, (name,))
        value = self._section_value(("matrices",), aliases)
        return self.resolve_path(str(value)) if value else None

    def artifact(self, name: str) -> Path:
        aliases = ARTIFACT_KEY_ALIASES.get(name, (name,))
        value = self._section_value(("artefacts", "artifacts"), aliases)
        if value is None:
            fallback = self.root("staging") / name
            return fallback
        resolved = self.resolve_path(str(value))
        if resolved is None:
            raise KeyError(f"Unable to resolve artifact '{name}' in {self.path}")
        return resolved

    def env_files(self) -> list[Path]:
        env_section = self._section("environnement", "env")
        values = _first_present(env_section, ("fichiers", "files"), [])
        if isinstance(values, str):
            values = [values]
        resolved: list[Path] = []
        for value in values:
            path = self.resolve_path(str(value))
            if path is not None:
                resolved.append(path)
        return resolved

    def required_env(self) -> list[str]:
        env_section = self._section("environnement", "env")
        values = _first_present(env_section, ("obligatoires", "required"), [])
        return [str(item) for item in values]

    def optional_env(self) -> list[str]:
        env_section = self._section("environnement", "env")
        values = _first_present(env_section, ("optionnelles", "optional"), [])
        return [str(item) for item in values]

    def settings(self) -> dict[str, Any]:
        return self._section("parametres", "settings")

    def layout_settings(self) -> dict[str, Any]:
        layout = self.settings().get("layout") or {}
        return dict(layout) if isinstance(layout, dict) else {}

    def technical_root(self) -> Path | None:
        value = self.layout_settings().get("technical_root")
        return self.resolve_path(str(value)) if value else None

    def physical_deposit_path(self) -> Path | None:
        value = self.layout_settings().get("physical_deposit")
        return self.resolve_path(str(value)) if value else None

    def user_moves_allowed(self) -> bool:
        value = self.layout_settings().get("user_moves_allowed")
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "vrai", "yes", "oui", "on"}
        return bool(value)

    def docai_settings(self, mode_override: str | None = None) -> dict[str, Any]:
        settings = self.settings()
        configured = settings.get("docai") or self._section("docai")
        if not isinstance(configured, dict):
            configured = {}

        raw_mode = mode_override or _first_present(configured, ("mode",), "off")
        mode = str(raw_mode).strip().lower().replace("-", "_")
        if mode not in {"off", "local_basic", "local_heavy"}:
            mode = "off"

        enabled_backends = _first_present(configured, ("enabled_backends", "backends"), [])
        if isinstance(enabled_backends, str):
            enabled_backends = [enabled_backends]
        enabled = [str(item).strip().lower().replace("-", "_") for item in enabled_backends if str(item).strip()]
        if not enabled:
            if mode == "local_basic":
                enabled = ["pymupdf", "docling", "rapidocr", "sidecar_ocr"]
            elif mode == "local_heavy":
                enabled = ["pymupdf", "docling", "rapidocr", "sidecar_ocr", "qwen_vl", "layoutlmv3"]
            else:
                enabled = []

        models_dir = _first_present(configured, ("models_dir", "dossier_modeles"), "./models")
        max_pages = _first_present(configured, ("max_pages", "nombre_pages_max"), 30)
        try:
            max_pages = int(max_pages)
        except (TypeError, ValueError):
            max_pages = 30

        return {
            "mode": mode,
            "privacy": str(_first_present(configured, ("privacy", "confidentialite"), "local_only")),
            "device": str(_first_present(configured, ("device", "materiel"), "auto")),
            "models_dir": str(models_dir),
            "models_path": self.resolve_path(str(models_dir)),
            "max_pages": max(1, max_pages),
            "enabled_backends": enabled,
        }

    def politique_linguistique(self) -> dict[str, Any]:
        settings = self.settings()
        policy = settings.get("politique_linguistique") or settings.get("language_policy") or {}
        if not isinstance(policy, dict):
            policy = {}
        return {
            "langue_principale": str(
                _first_present(
                    settings,
                    ("langue_principale", "primary_language"),
                    _first_present(policy, ("langue_principale", "primary_language"), "fr"),
                )
            ),
            "locale_preferree": str(
                _first_present(
                    settings,
                    ("locale_preferree", "preferred_locale"),
                    _first_present(policy, ("locale_preferree", "preferred_locale"), "fr-FR"),
                )
            ),
            "preferer_le_francais": bool(
                _first_present(policy, ("preferer_le_francais", "prefer_french"), True)
            ),
            "autoriser_anglais_technique": bool(
                _first_present(
                    policy,
                    (
                        "autoriser_anglais_uniquement_pour_compatibilite_technique",
                        "allow_english_only_for_technical_compatibility",
                    ),
                    True,
                )
            ),
            "traduire_sorties_diffusables": bool(
                _first_present(
                    policy,
                    ("traduire_les_sorties_diffusables", "translate_diffusible_outputs"),
                    True,
                )
            ),
        }

    def classification_rules_path(self) -> Path:
        overrides = self._section("surcharges_config", "config_overrides")
        override = _first_present(overrides, ("regles_classification", "classification_rules"))
        if override:
            resolved = self.resolve_path(str(override))
            if resolved is not None:
                return resolved
        return resource_path("configs", "taxonomy.default.yml")

    def completeness_rules_path(self) -> Path:
        overrides = self._section("surcharges_config", "config_overrides")
        override = _first_present(overrides, ("completude_documentaire", "document_completeness"))
        if override:
            resolved = self.resolve_path(str(override))
            if resolved is not None:
                return resolved
        return resource_path("configs", "document_completeness.default.yml")

    def ag_rules_path(self) -> Path:
        overrides = self._section("surcharges_config", "config_overrides")
        override = _first_present(overrides, ("regles_ag", "ag_rules"))
        if override:
            resolved = self.resolve_path(str(override))
            if resolved is not None:
                return resolved
        return resource_path("configs", "ag_rules.fr.yml")

    def sensitivity_rules_path(self) -> Path:
        overrides = self._section("surcharges_config", "config_overrides")
        override = _first_present(overrides, ("regles_sensibilite", "sensitivity_rules"))
        if override:
            resolved = self.resolve_path(str(override))
            if resolved is not None:
                return resolved
        return resource_path("configs", "sensitivity_rules.default.yml")

    def privacy_rules_path(self) -> Path:
        overrides = self._section("surcharges_config", "config_overrides")
        override = _first_present(overrides, ("regles_confidentialite", "privacy_rules"))
        if override:
            resolved = self.resolve_path(str(override))
            if resolved is not None:
                return resolved
        return resource_path("configs", "privacy_rules.default.yml")
