from __future__ import annotations

import json
import os
from pathlib import Path

from ..core.common import InstanceConfig, RunContext, now_iso, write_text
from .accounting import copy_accounting_tables_for_dashboard, ensure_accounting_outputs


GRIST_TABLES = [
    "Documents",
    "Factures",
    "Anomalies_Factures",
    "Fournisseurs",
    "Contrats",
    "Compta_2025",
    "Anomalies",
    "Diligences_Fournisseurs",
    "Demandes_Syndic",
    "Travaux",
    "AG",
]


def sync_grist(instance: InstanceConfig, run: RunContext, target: str, dataset: str, year: int) -> dict[str, object]:
    grist_dir = instance.artifact("grist_dir") / dataset / str(year)
    grist_dir.mkdir(parents=True, exist_ok=True)
    ensure_accounting_outputs(instance, run, year)

    copied = copy_accounting_tables_for_dashboard(instance, year, grist_dir)
    manifest = {
        "status": "ok",
        "mode": "local_export",
        "target": target,
        "dataset": dataset,
        "year": year,
        "tables": GRIST_TABLES,
        "exports": copied,
        "api_ready": bool(os.environ.get("GRIST_API_KEY") and os.environ.get("GRIST_DOC_ID")),
        "security": "No external Grist sync without explicit private API configuration.",
        "generated_at": now_iso(),
    }
    write_text(grist_dir / "grist_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=True))
    run.log_action("grist_sync", grist_dir, f"dataset={dataset}; target={target}; year={year}")
    return manifest
