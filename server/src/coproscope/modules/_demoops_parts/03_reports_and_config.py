from __future__ import annotations



def build_demo_instance(
    source: InstanceConfig,
    run: RunContext,
    *,
    output_instance: Path,
    mode: str = "fictive",
    year: int = 2025,
    run_source_audit: bool = True,
    max_text_chars: int = 12000,
) -> dict[str, object]:
    if mode != "fictive":
        raise ValueError("Only mode='fictive' is supported for publishable demos.")

    instance_dir = output_instance
    if instance_dir.suffix.lower() in {".yml", ".yaml", ".json"}:
        instance_dir = instance_dir.parent
    instance_dir = instance_dir.resolve()
    instance_dir.mkdir(parents=True, exist_ok=True)

    source_audit = _run_source_audit(source, run, max_text_chars) if run_source_audit else {
        "status": "skipped",
        "publication_note": "Audit source non execute pour cette generation.",
    }
    profile, source_summary = _source_profile(source, year)
    _write_support_files(instance_dir)
    docs = _write_raw_docs(instance_dir)
    _write_registers(instance_dir, docs)
    instance_path = _write_instance_config(instance_dir)
    _write_accounting_outputs(source, instance_dir, year, source_summary)

    validation = _validate_generated_instance(instance_dir)
    _write_reports(instance_dir, year, profile, validation)
    demo_instance_payload = {
        "mode": "fictive",
        "created_at": now_iso(),
        "demo_instance_id": DEMO_ID,
        "source_profile": profile,
        "source_audit": source_audit,
        "publication_validation": validation,
        "private_content_copied": False,
        "pseudonymization_only_publishable": False,
        "cnil_checks": ["individualisation", "correlation", "inference"],
    }
    _json(instance_dir / "demo_manifest.json", demo_instance_payload)
    _json(instance_dir / "outputs" / "demo" / "manifest_publication.json", demo_instance_payload)

    demo_instance = InstanceConfig(path=instance_path, payload=json.loads(instance_path.read_text(encoding="utf-8")))
    demo_run = RunContext(demo_instance, "demo privacy validation")
    privacyops.screen_existing(demo_instance, demo_run, include_generated=True, max_text_chars=max_text_chars)
    biffageops.build_redaction_queue(demo_instance, demo_run)
    demo_run.finish("OK", "demo privacy validation complete")

    run.log_action("demo_build", instance_path, f"mode={mode}; year={year}; decision={validation['decision']}")
    return {
        "status": "ok" if validation["decision"].startswith("APPROVED") else "review_required",
        "instance": str(instance_path),
        "instance_root": str(instance_dir),
        "mode": mode,
        "year": year,
        "source_audit": source_audit,
        "publication_validation": validation,
        "manifest": str(instance_dir / "demo_manifest.json"),
    }
