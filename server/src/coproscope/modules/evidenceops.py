from __future__ import annotations

import json

from ..core.common import InstanceConfig, RunContext, now_iso, read_csv, write_text
from .accounting import copy_accounting_tables_for_dashboard, reconstruct_accounting


def build_evidence_report(instance: InstanceConfig, run: RunContext, dataset: str, year: int) -> dict[str, object]:
    evidence_dir = instance.artifact("evidence_dir") / dataset / str(year)
    data_dir = evidence_dir / "sources" / "comptascope"
    pages_dir = evidence_dir / "pages"
    data_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    accounting_dir = instance.artifact("accounting_dir") / str(year)
    if not accounting_dir.exists():
        reconstruct_accounting(instance, run, year)
    copied = copy_accounting_tables_for_dashboard(instance, year, data_dir)

    invoice_path = accounting_dir / f"invoice_evidence_{year}.csv"
    control_path = accounting_dir / f"accounting_controls_{year}.csv"
    match_path = accounting_dir / f"invoice_expense_matches_{year}.csv"
    report_path = accounting_dir / f"rapport_comptascope_{year}.md"
    _, invoices = read_csv(invoice_path)
    _, controls = read_csv(control_path)
    _, matches = read_csv(match_path)
    matched_count = sum(1 for row in matches if row.get("match_status", "").startswith("MATCH_"))
    non_matched_count = sum(1 for row in matches if row.get("match_status") == "NON_RAPPROCHE")

    package = {
        "scripts": {"dev": "evidence dev", "build": "evidence build"},
        "dependencies": {"@evidence-dev/evidence": "40.1.8", "@evidence-dev/duckdb": "2.0.1"},
    }
    write_text(evidence_dir / "package.json", json.dumps(package, indent=2, ensure_ascii=True))
    write_text(
        pages_dir / "index.md",
        "\n".join(
            [
                f"# ComptaScope {year}",
                "",
                "Rapport local genere depuis les tables candidates CoproScope.",
                "",
                f"- Factures candidates: {len(invoices)}",
                f"- Controles ouverts: {len(controls)}",
                f"- Rapprochements automatiques: {matched_count}",
                f"- Factures non rapprochees a expliquer/controler: {non_matched_count}",
                "",
                "## Lecture comptable",
                "",
                "`NON_RAPPROCHE` signale une limite de rapprochement automatique, pas une absence comptable certaine. Les causes typiques sont les alias fournisseurs, les references internes, les ventilations multi-lignes, les regroupements et les extractions faibles.",
                "",
                f"- Rapport ComptaScope local: `{report_path.name}`",
                "",
                "Les donnees reelles restent locales. Les exports publics doivent utiliser l'instance synthetique.",
                "",
            ]
        ),
    )
    manifest = {
        "status": "ok",
        "dataset": dataset,
        "year": year,
        "exports": copied,
        "invoice_count": len(invoices),
        "control_count": len(controls),
        "matched_count": matched_count,
        "non_matched_count": non_matched_count,
        "generated_at": now_iso(),
    }
    write_text(evidence_dir / "evidence_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=True))
    run.log_action("evidence_build", evidence_dir, f"dataset={dataset}; year={year}")
    return manifest
