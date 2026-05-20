from __future__ import annotations

import json

from ..core.common import InstanceConfig, RunContext, now_iso, read_csv, write_text
from .accounting import copy_accounting_tables_for_dashboard, ensure_accounting_outputs


def _match_priority(row: dict[str, str]) -> str:
    priority = row.get("match_priority", "")
    if priority:
        return priority
    status = row.get("match_status", "")
    if status == "NON_RAPPROCHE":
        return "P1"
    if status.startswith("MATCH_"):
        return "OK"
    if status:
        return "P2"
    return ""


def build_evidence_report(instance: InstanceConfig, run: RunContext, dataset: str, year: int) -> dict[str, object]:
    evidence_dir = instance.artifact("evidence_dir") / dataset / str(year)
    data_dir = evidence_dir / "sources" / "comptascope"
    pages_dir = evidence_dir / "pages"
    data_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    ensure_accounting_outputs(instance, run, year)
    accounting_dir = instance.artifact("accounting_dir") / str(year)
    copied = copy_accounting_tables_for_dashboard(instance, year, data_dir)

    invoice_path = accounting_dir / f"invoice_evidence_{year}.csv"
    invoice_anomaly_path = accounting_dir / f"invoice_anomalies_{year}.csv"
    control_path = accounting_dir / f"accounting_controls_{year}.csv"
    match_path = accounting_dir / f"invoice_expense_matches_{year}.csv"
    alias_path = accounting_dir / f"supplier_alias_suggestions_{year}.csv"
    supplier_due_path = accounting_dir / f"supplier_due_diligence_controls_{year}.csv"
    report_path = accounting_dir / f"rapport_comptascope_{year}.md"
    _, invoices = read_csv(invoice_path)
    _, invoice_anomalies = read_csv(invoice_anomaly_path)
    _, controls = read_csv(control_path)
    _, matches = read_csv(match_path)
    _, aliases = read_csv(alias_path)
    _, supplier_due = read_csv(supplier_due_path)
    matched_count = sum(1 for row in matches if _match_priority(row) == "OK")
    candidate_p2_count = sum(1 for row in matches if _match_priority(row) == "P2")
    priority_p1_count = sum(1 for row in matches if _match_priority(row) == "P1")
    auto_alias_count = sum(1 for row in aliases if row.get("suggestion_status") == "AUTO_APPLICABLE")

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
                f"- Anomalies facture: {len(invoice_anomalies)}",
                f"- Controles comptables ouverts: {len(controls)}",
                f"- Rapprochements locaux suffisants: {matched_count}",
                f"- Candidats locaux P2 a confirmer: {candidate_p2_count}",
                f"- Points de rapprochement P1: {priority_p1_count}",
                f"- Alias fournisseurs deduits: {len(aliases)}",
                f"- Alias auto-applicables: {auto_alias_count}",
                f"- Diligences fournisseur rattachees: {len(supplier_due)}",
                "",
                "## Lecture comptable",
                "",
                "DocOps produit la preuve documentaire, FactureOps extrait et qualifie les factures, puis ComptaScope reconstruit les ecritures candidates et rapproche l'etat des depenses. `OK` indique une preuve locale suffisante. `P2` indique un candidat local a confirmer: alias, nom similaire, ventilation, division egale ou regroupement. `P1` indique qu'aucun indice local suffisant n'a ete trouve et qu'un controle prioritaire du grand livre, de l'etat des depenses ou de la piece est necessaire.",
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
        "invoice_anomaly_count": len(invoice_anomalies),
        "control_count": len(controls),
        "matched_count": matched_count,
        "candidate_p2_count": candidate_p2_count,
        "priority_p1_count": priority_p1_count,
        "non_matched_count": priority_p1_count,
        "supplier_alias_suggestion_count": len(aliases),
        "supplier_alias_auto_count": auto_alias_count,
        "supplier_due_diligence_count": len(supplier_due),
        "generated_at": now_iso(),
    }
    write_text(evidence_dir / "evidence_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=True))
    run.log_action("evidence_build", evidence_dir, f"dataset={dataset}; year={year}")
    return manifest
