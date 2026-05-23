from __future__ import annotations



def _write_report(instance: InstanceConfig, screening_rows: list[dict[str, str]]) -> Path:
    report_path = instance.artifact("reports_dir") / "rapport_screening_confidentialite.md"
    by_raw = Counter(row.get("raw_max_college", "") for row in screening_rows)
    by_priority = Counter(row.get("remediation_priority", "") for row in screening_rows)
    by_review_status = Counter(row.get("privacy_review_status", "") for row in screening_rows)
    to_redact = sum(1 for row in screening_rows if "redaction" in row.get("required_transformations", ""))
    review = sum(1 for row in screening_rows if row.get("review_required"))
    blocked = sum(1 for row in screening_rows if row.get("privacy_review_status") == "BLOQUE")
    justification_required = sum(1 for row in screening_rows if row.get("review_justification_required"))

    lines = [
        "# Rapport de screening confidentialite",
        "",
        f"- Instance: {instance.display_name}",
        f"- Documents screenes: {len(screening_rows)}",
        f"- Documents a biffer: {to_redact}",
        f"- Documents a revoir: {review}",
        f"- Documents bloques: {blocked}",
        f"- Decisions avec justification requise: {justification_required}",
        "",
        "## Repartition par college brut",
        "",
        "| College | Nombre |",
        "| --- | ---: |",
    ]
    for college, count in sorted(by_raw.items()):
        lines.append(f"| {college or '-'} | {count} |")
    lines.extend(
        [
            "",
            "## Priorites de remediation",
            "",
            "| Priorite | Nombre |",
            "| --- | ---: |",
        ]
    )
    for priority, count in sorted(by_priority.items()):
        lines.append(f"| {priority or '-'} | {count} |")
    lines.extend(
        [
            "",
            "## File de decision humaine",
            "",
            "| Statut | Nombre |",
            "| --- | ---: |",
        ]
    )
    for status, count in sorted(by_review_status.items()):
        lines.append(f"| {status or '-'} | {count} |")
    lines.extend(
        [
            "",
            "## Points a traiter",
            "",
            "| Priorite | Statut | Document | College brut | Recommandation | Prochaine etape |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    priority_rows = [
        row
        for row in screening_rows
        if row.get("remediation_priority") in {"P0", "P1", "P2"}
        or row.get("privacy_review_status") in {"BLOQUE", "A_ARBITRER"}
    ]
    for row in priority_rows[:50]:
        lines.append(
            " | ".join(
                [
                    "",
                    row.get("remediation_priority", ""),
                    row.get("privacy_review_status", ""),
                    row.get("doc_id", ""),
                    row.get("raw_max_college", ""),
                    row.get("review_status_recommendation", ""),
                    row.get("publication_blocker") or row.get("review_next_step") or row.get("recommended_action", ""),
                    "",
                ]
            )
        )
    if not priority_rows:
        lines.append("| OK | NO_OBVIOUS_EXPOSURE | - | - | - | Aucun point prioritaire |")
    write_text(report_path, "\n".join(lines) + "\n")
    return report_path


def screen_existing(
    instance: InstanceConfig,
    run: RunContext,
    *,
    include_generated: bool = True,
    max_text_chars: int = 50000,
    prune_unseen: bool = False,
    scan_workspace_prefixes: bool | None = None,
) -> dict[str, object]:
    workspace_root = instance.root("workspace")
    documents_path = instance.register("documents")
    fields, document_rows = read_csv(documents_path)
    if not fields:
        fields = list(DEFAULT_DOCUMENT_FIELDS)
    for field in DEFAULT_DOCUMENT_FIELDS:
        if field not in fields:
            fields.append(field)
    ensure_policy_fields(fields)
    _ensure_review_fields(fields)
    by_path, by_digest = _existing_indexes(document_rows)
    seen_at = now_iso()
    updated_by_path: dict[str, dict[str, str]] = (
        {}
        if prune_unseen
        else {
            row.get("original_path", "").replace("\\", "/").lower(): row
            for row in document_rows
            if row.get("original_path")
        }
    )
    screening_rows: list[dict[str, str]] = []

    for path in _iter_files(
        _scan_roots(
            instance,
            include_generated,
            scan_workspace_prefixes=scan_workspace_prefixes,
        )
    ):
        try:
            digest = sha256_file(path)
            relative_path = relative_to(workspace_root, path)
            key = relative_path.replace("\\", "/").lower()
            previous = by_path.get(key) or by_digest.get(digest, {})
            row = _base_document_row(instance, workspace_root, path, digest, previous, seen_at)
        except OSError as exc:
            run.log_error(f"privacy screen skipped unreadable file {path}: {exc}")
            continue
        text = _read_sample(path, max_text_chars)
        if not text.strip():
            text = _read_existing_text_artifact(instance, row, max_text_chars)
        apply_access_policy(row, text=text, instance=instance)
        _apply_review_defaults(row, previous, digest)
        updated_by_path[key] = row
        screening_rows.append(_screening_row(row))

    document_rows = sorted(updated_by_path.values(), key=lambda item: (item.get("original_path", "").lower(), item.get("doc_id", "")))
    write_csv(documents_path, fields, document_rows)
    screening_path = privacy_screening_path(instance)
    write_csv(screening_path, SCREENING_REVIEW_FIELDS, screening_rows)
    report_path = _write_report(instance, screening_rows)
    run.log_action("privacy_screen_existing", screening_path, f"rows={len(screening_rows)}")
    run.log_action("write", documents_path, f"privacy enriched documents={len(document_rows)}")
    run.log_action("write", report_path, "privacy screening report")
    return {
        "status": "ok",
        "screened_count": len(screening_rows),
        "document_count": len(document_rows),
        "screening_register": str(screening_path),
        "report": str(report_path),
        "by_raw_college": dict(Counter(row.get("raw_max_college", "") for row in screening_rows)),
        "priority_counts": dict(Counter(row.get("remediation_priority", "") for row in screening_rows)),
        "review_status_counts": dict(Counter(row.get("privacy_review_status", "") for row in screening_rows)),
    }


def record_human_review_decision(
    instance: InstanceConfig,
    run: RunContext,
    *,
    doc_id: str,
    status: str,
    justification: str = "",
    reviewer: str = "",
) -> dict[str, object]:
    status = status.strip().upper()
    if status not in REVIEW_STATUSES:
        raise ValueError(f"Unsupported privacy review status: {status}")

    documents_path = instance.register("documents")
    fields, rows = read_csv(documents_path)
    fields = fields or list(DEFAULT_DOCUMENT_FIELDS)
    ensure_policy_fields(fields)
    _ensure_review_fields(fields)
    row = next((item for item in rows if item.get("doc_id") == doc_id), None)
    if row is None:
        raise ValueError(f"Unknown document id: {doc_id}")

    if not row.get("review_status_recommendation"):
        recommendation, next_step, blocker = _recommended_review_decision(row)
        row["review_status_recommendation"] = recommendation
        row["review_next_step"] = next_step
        row["publication_blocker"] = blocker
        row["review_justification_required"] = "YES" if _wide_diffusion_target(row) else ""

    _validate_review_decision(row, status, justification)
    updates = {
        "privacy_review_status": status,
        "privacy_review_justification": justification.strip(),
        "privacy_review_owner": reviewer.strip(),
        "privacy_reviewed_at": now_iso(),
    }
    row.update(updates)
    write_csv(documents_path, fields, rows)
    _sync_screening_review_decision(instance, doc_id, updates)
    run.log_action("privacy_review_decision", documents_path, f"doc_id={doc_id}; status={status}")
    return {
        "status": "ok",
        "doc_id": doc_id,
        "privacy_review_status": status,
        "justification_required": bool(row.get("review_justification_required")),
    }


def screening_summary(instance: InstanceConfig) -> dict[str, object]:
    path = privacy_screening_path(instance)
    _, rows = read_csv(path)
    return {
        "path": str(path),
        "count": len(rows),
        "by_raw_college": dict(Counter(row.get("raw_max_college", "") for row in rows)),
        "priority_counts": dict(Counter(row.get("remediation_priority", "") for row in rows)),
    }
