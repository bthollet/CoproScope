from __future__ import annotations



def redact_document(
    instance: InstanceConfig,
    run: RunContext,
    *,
    doc_id: str,
    mode: str = "redaction_irreversible",
    target_college: str = "C2_Coproprietaires",
) -> dict[str, object]:
    if mode not in {"redaction_irreversible", "pseudonymisation_tracee"}:
        raise ValueError(f"Unsupported redaction mode: {mode}")

    _, rows = read_csv(instance.register("documents"))
    row = next((item for item in rows if item.get("doc_id") == doc_id), None)
    if row is None:
        raise ValueError(f"Unknown document id: {doc_id}")

    target_college = normalize_college(target_college, default="C2_Coproprietaires")
    derivative_ceiling = normalize_college(row.get("derivative_max_college"), default=target_college)
    if ACCESS_RANK[target_college] < ACCESS_RANK[derivative_ceiling]:
        raise ValueError(
            f"Target college {target_college} is wider than derivative_max_college {derivative_ceiling} for {doc_id}."
        )
    source = _source_path(instance, row)
    if not source.exists():
        raise FileNotFoundError(source)

    text = _source_text(source)
    if not text.strip():
        text = _registered_text(instance, row)
    signals = redaction_signals(text)
    categories = sorted({signal.category for signal in signals})
    redaction_id = f"RED-{doc_id}-{now_iso().replace(':', '').replace('-', '')}"
    if not signals:
        if row.get("personal_data_level") == "none" and text.strip():
            out = _write_text_derivative_redaction(instance, row, text, [], {}, mode)
            digest = sha256_file(out)
            record = {
                "redaction_id": redaction_id,
                "created_at": now_iso(),
                "doc_id": doc_id,
                "source_path": row.get("original_path", ""),
                "source_sha256": row.get("sha256", ""),
                "redacted_path": relative_to(instance.root("workspace"), out),
                "redacted_sha256": digest,
                "mode": mode,
                "target_college": target_college,
                "status": "REDACTED",
                "match_count": "0",
                "categories": "",
                "map_path": "",
                "notes": "No identifiers detected; text derivative registered for anonymized audit boundary.",
            }
            _register_redaction(instance, record)
            _update_document_row(
                instance,
                doc_id,
                {
                    "redaction_status": "REDACTED",
                    "redaction_mode": mode,
                    "redacted_path": record["redacted_path"],
                    "redacted_sha256": digest,
                    "redaction_map_id": "",
                },
            )
            run.log_action("biffage_redact_no_matches", out, f"doc_id={doc_id}; matches=0; mode={mode}")
            return {
                "status": "ok",
                "doc_id": doc_id,
                "mode": mode,
                "target_college": target_college,
                "match_count": 0,
                "categories": [],
                "redacted_path": str(out),
                "redacted_sha256": digest,
                "map_path": "",
            }
        record = {
            "redaction_id": redaction_id,
            "created_at": now_iso(),
            "doc_id": doc_id,
            "source_path": row.get("original_path", ""),
            "source_sha256": row.get("sha256", ""),
            "redacted_path": "",
            "redacted_sha256": "",
            "mode": mode,
            "target_college": target_college,
            "status": "NO_LOCAL_IDENTIFIER_MATCHES",
            "match_count": "0",
            "categories": "",
            "map_path": "",
            "notes": "No direct identifiers detected by local rules.",
        }
        _register_redaction(instance, record)
        run.log_action("biffage_no_matches", source, f"doc_id={doc_id}")
        return {"status": record["status"], "doc_id": doc_id, "match_count": 0}

    if mode == "pseudonymisation_tracee":
        replacements, map_path = _mapping_for(instance, row, signals)
        map_path_value = relative_to(instance.root("workspace"), map_path)
    else:
        replacements = {signal.value: _label_for(signal, mode, None) for signal in signals}
        map_path_value = ""

    fallback_text = text if source.suffix.lower().lstrip(".") == "pdf" else None
    out = _write_redacted(instance, row, source, signals, replacements, mode, fallback_text=fallback_text)
    digest = sha256_file(out)
    record = {
        "redaction_id": redaction_id,
        "created_at": now_iso(),
        "doc_id": doc_id,
        "source_path": row.get("original_path", ""),
        "source_sha256": row.get("sha256", ""),
        "redacted_path": relative_to(instance.root("workspace"), out),
        "redacted_sha256": digest,
        "mode": mode,
        "target_college": target_college,
        "status": "REDACTED",
        "match_count": str(len(signals)),
        "categories": ";".join(categories),
        "map_path": map_path_value,
        "notes": "pseudonymized data remain personal data" if mode == "pseudonymisation_tracee" else "",
    }
    _register_redaction(instance, record)
    _update_document_row(
        instance,
        doc_id,
        {
            "redaction_status": "REDACTED",
            "redaction_mode": mode,
            "redacted_path": record["redacted_path"],
            "redacted_sha256": digest,
            "redaction_map_id": map_path_value,
        },
    )
    run.log_action("biffage_redact", out, f"doc_id={doc_id}; matches={len(signals)}; mode={mode}")
    return {
        "status": "ok",
        "doc_id": doc_id,
        "mode": mode,
        "target_college": target_college,
        "match_count": len(signals),
        "categories": categories,
        "redacted_path": str(out),
        "redacted_sha256": digest,
        "map_path": map_path_value,
    }


def build_redaction_queue(instance: InstanceConfig, run: RunContext) -> dict[str, object]:
    _, docs = read_csv(instance.register("documents"))
    rows: list[dict[str, str]] = []
    for doc in docs:
        transformations = doc.get("required_transformations", "")
        if "redaction" not in transformations and "aggregation" not in transformations and "metadata_only" not in transformations:
            continue
        publication_form = doc.get("publication_form", "")
        if doc.get("redaction_status") == "REDACTED":
            recommended_mode = doc.get("redaction_mode", "") or "redaction_irreversible"
            status = "REDACTED"
        elif "redaction" in transformations and not _supports_local_redaction(doc):
            recommended_mode = "manual_redaction_or_aggregation"
            status = "NEEDS_MANUAL_REDACTION"
        elif "redaction" in transformations:
            recommended_mode = "redaction_irreversible"
            status = "READY_FOR_LOCAL_REDACTION"
        elif "aggregation" in transformations:
            recommended_mode = "manual_aggregation"
            status = "NEEDS_AGGREGATION_MANUAL"
        else:
            recommended_mode = "metadata_only"
            status = "METADATA_ONLY"
        rows.append(
            {
                "doc_id": doc.get("doc_id", ""),
                "file_name": doc.get("file_name", ""),
                "original_path": doc.get("original_path", ""),
                "raw_max_college": doc.get("raw_max_college", ""),
                "derivative_max_college": doc.get("derivative_max_college", ""),
                "publication_form": publication_form,
                "required_transformations": transformations,
                "review_required": doc.get("review_required", ""),
                "recommended_mode": recommended_mode,
                "queue_status": status,
            }
        )
    path = _queue_path(instance)
    write_csv(path, REDACTION_QUEUE_FIELDS, rows)
    run.log_action("biffage_queue", path, f"rows={len(rows)}")
    return {
        "status": "ok",
        "queue": str(path),
        "queued_count": len(rows),
        "status_counts": dict(Counter(row.get("queue_status", "") for row in rows)),
    }


def redact_required_documents(
    instance: InstanceConfig,
    run: RunContext,
    *,
    mode: str = "redaction_irreversible",
    target_college: str = "C2_Coproprietaires",
    limit: int | None = None,
) -> dict[str, object]:
    queue = build_redaction_queue(instance, run)
    queue_path = Path(str(queue["queue"]))
    _, rows = read_csv(queue_path)
    applied: list[dict[str, object]] = []
    for row in rows:
        if row.get("queue_status") != "READY_FOR_LOCAL_REDACTION":
            continue
        if limit is not None and len(applied) >= limit:
            break
        try:
            applied.append(
                redact_document(
                    instance,
                    run,
                    doc_id=row.get("doc_id", ""),
                    mode=mode,
                    target_college=target_college,
                )
            )
        except RuntimeError as exc:
            if "Unsupported redaction format" not in str(exc):
                raise
            record = {
                "redaction_id": f"redact-{row.get('doc_id', '')}-unsupported",
                "created_at": now_iso(),
                "doc_id": row.get("doc_id", ""),
                "source_path": row.get("original_path", ""),
                "source_sha256": "",
                "redacted_path": "",
                "redacted_sha256": "",
                "mode": mode,
                "target_college": target_college,
                "status": "NEEDS_MANUAL_REDACTION",
                "match_count": "0",
                "categories": "",
                "map_path": "",
                "notes": f"Local redaction unsupported for .{_redaction_extension(row) or 'no_extension'}; produce an anonymized export or aggregate summary before cloud audit.",
            }
            _register_redaction(instance, record)
            _update_document_row(
                instance,
                row.get("doc_id", ""),
                {
                    "redaction_status": "NEEDS_MANUAL_REDACTION",
                    "redaction_mode": mode,
                    "redacted_path": "",
                    "redacted_sha256": "",
                    "review_required": "YES",
                },
            )
            run.log_action("biffage_manual_redaction_required", row.get("original_path", ""), f"doc_id={row.get('doc_id', '')}; reason=unsupported_format")
            applied.append({"status": "NEEDS_MANUAL_REDACTION", "doc_id": row.get("doc_id", ""), "reason": str(exc)})
    return {
        "status": "ok",
        "queued_count": queue["queued_count"],
        "applied_count": len(applied),
        "results": applied,
    }
