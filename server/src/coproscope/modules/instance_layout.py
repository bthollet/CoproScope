from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.common import InstanceConfig


VISIBLE_DIRECTORIES = (
    "01 - Deposez les nouveaux fichiers ici",
    "01 - Deposez les nouveaux fichiers ici/A deposer ici",
    "02 - Documents classes",
    "03 - Rapports et exports",
    "04 - A verifier",
)

TECHNICAL_DIRECTORIES = (
    ".coproscope",
    ".coproscope/config",
    ".coproscope/registers",
    ".coproscope/system",
    ".coproscope/outputs",
    ".coproscope/staging",
    ".coproscope/cache",
    ".coproscope/generated",
    ".coproscope/migrations",
)

README_PATH = "README - utiliser cette instance.md"


def build_instance_layout_plan(instance: InstanceConfig) -> dict[str, Any]:
    """Return a non-destructive novice layout plan for an instance."""
    operations = [
        _operation(instance, "create_directory", path, "Dossier visible novice.")
        for path in VISIBLE_DIRECTORIES
    ]
    operations.extend(
        _operation(instance, "create_directory", path, "Dossier technique sous .coproscope.")
        for path in TECHNICAL_DIRECTORIES
    )
    operations.append(
        _operation(instance, "write_readme", README_PATH, "Guide local court, a relire avant application.")
    )

    return {
        "ok": True,
        "status": "planned",
        "dry_run": True,
        "will_modify_files": False,
        "instance_id": instance.instance_id,
        "layout_version": "instance_layout_novice_v1",
        "current_layout": _current_layout(instance),
        "recommended_settings": _recommended_settings(),
        "operations": operations,
        "destructive_operations": [],
        "migration_safety": {
            "required_before_apply": [
                "sauvegarde verifiee",
                "manifeste doc_id plus sha256",
                "plan de retour arriere",
                "confirmation humaine explicite",
            ],
            "identity_rule": "Suivre les pieces par doc_id et sha256, jamais seulement par chemin.",
            "source_of_truth": False,
        },
        "privacy_gates": [
            "Aucun fichier source n'est lu par cette commande.",
            "Aucun dossier n'est cree, deplace, renomme ou supprime en dry-run.",
            "Les chemins affiches restent relatifs a la racine d'instance.",
            "Toute application future devra produire un manifeste avant/apres et un rollback.",
        ],
        "next_action": (
            "Relire ce plan, sauvegarder l'instance, puis utiliser une future commande appliquee "
            "seulement avec confirmation explicite."
        ),
    }


def _operation(instance: InstanceConfig, kind: str, relative_path: str, reason: str) -> dict[str, str]:
    target = instance.instance_root / relative_path
    return {
        "kind": kind,
        "path": relative_path.replace("\\", "/"),
        "status": "dry_run_exists" if target.exists() else "dry_run_recommended",
        "reason": reason,
    }


def _current_layout(instance: InstanceConfig) -> dict[str, Any]:
    layout = instance.layout_settings()
    technical_root = instance.technical_root()
    physical_deposit = instance.physical_deposit_path()
    return {
        "configured": bool(layout),
        "mode": str(layout.get("mode") or layout.get("version") or "legacy"),
        "technical_root": _relative_or_hidden(instance, technical_root),
        "physical_deposit": _relative_or_hidden(instance, physical_deposit),
        "user_moves_allowed": instance.user_moves_allowed(),
    }


def _recommended_settings() -> dict[str, Any]:
    return {
        "settings": {
            "layout": {
                "mode": "novice_v1",
                "version": "instance_layout_novice_v1",
                "technical_root": "./.coproscope",
                "physical_deposit": "./01 - Deposez les nouveaux fichiers ici/A deposer ici",
                "user_moves_allowed": True,
            }
        },
        "roots": {
            "workspace": ".",
            "system": "./.coproscope/system",
            "outputs": "./.coproscope/outputs",
            "staging": "./.coproscope/staging",
        },
        "registers": {
            "documents": "./.coproscope/registers/registre_documents.csv",
            "duplicates": "./.coproscope/registers/registre_doublons.csv",
            "manifest": "./.coproscope/registers/manifest_sha256.csv",
            "requests": "./.coproscope/registers/registre_demandes.csv",
            "ag": "./.coproscope/registers/registre_ag.csv",
            "findings": "./.coproscope/registers/constats_diligences.csv",
            "kpi": "./.coproscope/registers/kpi.csv",
        },
    }


def _relative_or_hidden(instance: InstanceConfig, path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return path.resolve().relative_to(instance.instance_root.resolve()).as_posix()
    except ValueError:
        return "[hors-instance]"
