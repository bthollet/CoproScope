from __future__ import annotations

from ..core.common import FINDING_FIELDS, REQUEST_FIELDS, RunContext, load_template_csv, read_csv, write_csv, write_text


def bootstrap_instance_state(instance, run: RunContext) -> None:
    for directory in [
        instance.root("logs"),
        instance.root("staging"),
        instance.artifact("text_dir"),
        instance.artifact("classified_dir"),
        instance.artifact("reports_dir"),
        instance.register("documents").parent,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    request_path = instance.register("requests")
    if not request_path.exists():
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(load_template_csv("registre_demandes.csv"), encoding="utf-8")
        run.log_action("write", request_path, "bootstrap request register")

    findings_path = instance.register("findings")
    if not findings_path.exists():
        write_csv(findings_path, FINDING_FIELDS, [])
        run.log_action("write", findings_path, "bootstrap findings register")

    decision_log = instance.root("logs") / "decision_log.md"
    if not decision_log.exists():
        write_text(decision_log, "# Decision Log\n\n")
        run.log_action("write", decision_log, "bootstrap decision log")


def request_metrics(instance) -> dict[str, int]:
    _, rows = read_csv(instance.register("requests"))
    total = len(rows)
    traced = 0
    complete = 0
    for row in rows:
        has_trace = bool(row.get("source_document") or row.get("related_doc_ids"))
        if has_trace:
            traced += 1
        if row.get("status", "").strip().lower() in {"complete", "completee", "complète", "completee"}:
            complete += 1
    return {
        "total": total,
        "traced": traced,
        "complete": complete,
    }
