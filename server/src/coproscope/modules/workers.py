from __future__ import annotations

from ..core.common import InstanceConfig, RunContext
from . import agscope, docuscope, factureops
from .accounting import accounting_controls, reconstruct_accounting
from .evidenceops import build_evidence_report
from .gristops import sync_grist


def run_workers(instance: InstanceConfig, run: RunContext, scope: str, year: int) -> dict[str, object]:
    actions: list[dict[str, object]] = []

    if scope in {"inventory", "all"}:
        actions.append({"worker": "inventory_worker", "path": str(docuscope.inventory(instance, run))})
    if scope in {"documents", "all"}:
        actions.append({"worker": "document_text_worker", "path": str(docuscope.extract_text(instance, run))})
    if scope in {"syndic", "all"}:
        actions.append({"worker": "syndic_tracking_worker", "path": str(docuscope.missing_docs(instance, run))})
    if scope in {"ag", "all"}:
        agscope.analyze(instance, run)
        actions.append({"worker": "ag_worker", "status": "ok"})
    if scope in {"invoices", "all"}:
        actions.append({"worker": "invoice_worker", "result": factureops.extract_invoices(instance, run, year)})
    if scope in {"accounting", "all"}:
        actions.append({"worker": "comptascope_worker", "result": reconstruct_accounting(instance, run, year)})
        actions.append({"worker": "reconciliation_worker", "result": accounting_controls(instance, run, year)})
    if scope in {"dashboards", "all"}:
        actions.append({"worker": "grist_sync_worker", "result": sync_grist(instance, run, "local", "demo", year)})
        actions.append({"worker": "evidence_report_worker", "result": build_evidence_report(instance, run, "demo", year)})

    return {"status": "ok", "scope": scope, "year": year, "actions": actions}
