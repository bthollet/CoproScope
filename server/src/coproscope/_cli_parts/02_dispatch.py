from __future__ import annotations



def _dispatch(args: argparse.Namespace) -> int:
    _normaliser_commandes(args)
    if args.command == "mcp":
        from .mcp.server import serve_stdio

        serve_stdio()
        return 0

    if args.command == "share-audit":
        repo_root = Path(args.repo_root).resolve()
        config_path = Path(args.config).resolve()
        result = audit_repo(repo_root, config_path)
        print(json.dumps(result, indent=2, ensure_ascii=True))
        extractor_audit = result.get("generalizable_extractors") or {}
        private_violations = extractor_audit.get("private_violations") if isinstance(extractor_audit, dict) else []
        content_violations = result.get("content_violations") or []
        return 0 if not private_violations and not content_violations else 1
    if args.command == "share-export":
        repo_root = Path(args.repo_root).resolve()
        config_path = Path(args.config).resolve()
        output_dir = Path(args.output_dir).resolve()
        result = export_shareable(repo_root, config_path, output_dir, clean=args.clean)
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0
    if args.command == "tools" and args.tools_command == "status":
        tools.print_tools_status()
        return 0
    if args.command == "drive":
        if args.drive_command == "status":
            result = gdriveops.oauth_status(client_secrets_path=args.client_secrets, token_path=args.token_path)
        elif args.drive_command == "auth":
            result = gdriveops.run_oauth_flow(
                client_secrets_path=args.client_secrets,
                token_path=args.token_path,
                open_browser=not args.no_browser,
            )
        elif args.drive_command == "smoke":
            if args.upload:
                result = gdriveops.upload_encrypted_drive_smoke(
                    sync_root=args.sync_root,
                    encrypted_path=args.encrypted_path,
                    token_path=args.token_path,
                    folder_name=args.folder_name,
                    cleartext_canary=args.cleartext_canary,
                    generation=args.generation,
                    parent_sha256=args.parent_sha256,
                )
            else:
                result = gdriveops.prepare_encrypted_drive_smoke(
                    sync_root=args.sync_root,
                    encrypted_path=args.encrypted_path,
                    token_path=args.token_path,
                    cleartext_canary=args.cleartext_canary,
                    generation=args.generation,
                    parent_sha256=args.parent_sha256,
                )
        elif args.drive_command == "pull-package":
            service = gdrive_transport.build_drive_service(token_path=args.token_path)
            result = gdrive_transport.download_latest_encrypted_instance_package(
                drive_service=service,
                folder_id=args.folder_id,
                sync_root=args.sync_root,
            )
        elif args.drive_command == "sync-now":
            instance = load_instance(args.instance, args.instance_root)
            service = gdrive_transport.build_drive_service(token_path=args.token_path)
            result = drive_sync_now.sync_now(
                instance=instance,
                drive_service=service,
                folder_id=args.folder_id,
                sync_root=args.sync_root,
                local_state_root=args.local_state_root,
            )
        elif args.drive_command == "watch-once":
            instance = load_instance(args.instance, args.instance_root)
            service = gdrive_transport.build_drive_service(token_path=args.token_path)
            result = drive_watch.watch_once(
                instance=instance,
                drive_service=service,
                folder_id=args.folder_id,
                sync_root=args.sync_root,
                local_state_root=args.local_state_root,
                local_change_marker=args.local_change_marker,
            )
        elif args.drive_command == "watch-loop":
            instance = load_instance(args.instance, args.instance_root)
            service = gdrive_transport.build_drive_service(token_path=args.token_path)
            result = drive_watch_loop.watch_loop(
                instance=instance,
                drive_service=service,
                folder_id=args.folder_id,
                sync_root=args.sync_root,
                local_state_root=args.local_state_root,
                local_change_marker=args.local_change_marker,
                interval_seconds=args.interval_seconds,
                max_cycles=args.max_cycles,
            )
        elif args.drive_command == "folder-rights":
            service = gdrive_transport.build_drive_service(token_path=args.token_path)
            result = gdrive_rights.inspect_drive_folder_rights(drive_service=service, folder_id=args.folder_id)
        else:
            return 1
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0 if result.get("status") in {"ok", "ready", "prepared", "uploaded", "downloaded", "idle", "synced", "inspected", "limited", "completed"} else 1
    if args.command == "vault":
        roots = vault_core.roots_from_args(args)
        if args.vault_command == "init":
            result = vault_core.vault_init(roots.local_root, roots.sync_root)
        elif args.vault_command == "import":
            result = vault_core.vault_import(roots.local_root, roots.sync_root, Path(args.path))
        elif args.vault_command == "import-audit360-rows":
            imported_at = args.imported_at or datetime.now(timezone.utc).isoformat()
            result = audit360.import_audit360_file(
                local_root=roots.local_root,
                sync_root=roots.sync_root,
                path=Path(args.path),
                db_path=Path(args.db_path) if args.db_path else None,
                source_kind=args.source_kind,
                import_run_id=args.import_run_id,
                imported_at=imported_at,
            )
        elif args.vault_command == "status":
            result = vault_core.vault_status(roots.local_root, roots.sync_root)
        elif args.vault_command == "verify":
            result = vault_core.vault_verify(roots.local_root, roots.sync_root)
        elif args.vault_command == "snapshot":
            result = vault_core.vault_snapshot(roots.local_root, roots.sync_root)
        else:
            return 1
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0 if result.get("ok", False) else 1
    if args.command == "demo" and args.demo_command == "build":
        source = load_instance(args.source_instance, args.source_instance_root)
        run = RunContext(source, command=" ".join(part for part in sys.argv[1:] if part))
        try:
            result = demoops.build_demo_instance(
                source,
                run,
                output_instance=Path(args.output_instance),
                mode=args.mode,
                year=args.year,
                run_source_audit=not args.skip_source_audit,
                max_text_chars=args.max_text_chars,
            )
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "demo build complete")
            return 0 if result["status"] == "ok" else 1
        except Exception as exc:  # noqa: BLE001
            run.log_error(str(exc))
            run.finish("ERROR", str(exc))
            raise

    instance = load_instance(args.instance, args.instance_root)
    if args.command == "instance" and args.instance_command == "git-init":
        result = instancegit.ensure_local_git_repo(
            instance,
            update_gitignore=not args.no_gitignore,
            force_nested=args.force_nested,
        )
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0 if result.get("ok") else 1
    if args.command == "instance" and args.instance_command == "git-status":
        result = instancegit.inspect_instance_git(instance)
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0 if result.get("ok") else 1
    if args.command == "instance" and args.instance_command == "layout" and args.instance_layout_command == "plan":
        result = instance_layout.build_instance_layout_plan(instance)
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0 if result.get("status") == "planned" and result.get("dry_run") else 1

    run = RunContext(instance, command=" ".join(part for part in sys.argv[1:] if part))
    try:
        if args.command == "doctor":
            issues = run_doctor(instance, run)
            run.finish("OK" if issues == 0 else "WARN", f"issues={issues}")
            return 0 if issues == 0 else 1
        if args.command == "inventory":
            path = docuscope.inventory(instance, run)
            print(path)
            run.finish("OK", "inventory complete")
            return 0
        if args.command == "extract-text":
            path = docuscope.extract_text(instance, run, doc_id=args.doc_id, docai_mode=args.docai)
            print(path)
            run.finish("OK", "extract-text complete")
            return 0
        if args.command == "classify":
            path = docuscope.classify(instance, run, copy_files=not args.no_copy)
            print(path)
            run.finish("OK", "classify complete")
            return 0
        if args.command == "missing-docs":
            path = docuscope.missing_docs(instance, run)
            print(path)
            run.finish("OK", "missing-docs complete")
            return 0
        if args.command == "kpi":
            path = docuscope.compute_kpis(instance, run)
            print(path)
            run.finish("OK", "kpi complete")
            return 0
        if args.command == "accounting" and args.accounting_command == "reconstruct":
            result = accounting.reconstruct_accounting(instance, run, year=args.year)
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "accounting reconstruct complete")
            return 0
        if args.command == "accounting" and args.accounting_command == "controls":
            result = accounting.accounting_controls(instance, run, year=args.year)
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "accounting controls complete")
            return 0
        if args.command == "invoices" and args.invoices_command == "extract":
            result = factureops.extract_invoices(instance, run, year=args.year)
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "invoices extract complete")
            return 0
        if args.command == "grist" and args.grist_command == "sync":
            result = gristops.sync_grist(instance, run, target=args.target, dataset=args.dataset, year=args.year)
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "grist sync complete")
            return 0
        if args.command == "evidence" and args.evidence_command == "build":
            result = evidenceops.build_evidence_report(instance, run, dataset=args.dataset, year=args.year)
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "evidence build complete")
            return 0
        if args.command == "workers" and args.workers_command == "run":
            result = workers.run_workers(instance, run, scope=args.scope, year=args.year)
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "workers run complete")
            return 0
        if args.command == "privacy" and args.privacy_command == "screen-existing":
            result = privacyops.screen_existing(
                instance,
                run,
                include_generated=not args.skip_generated,
                max_text_chars=args.max_text_chars,
                prune_unseen=args.prune_unseen,
                scan_workspace_prefixes=args.scan_workspace_prefixes,
            )
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "privacy screen-existing complete")
            return 0
        if args.command == "privacy" and args.privacy_command == "redaction-queue":
            result = biffageops.build_redaction_queue(instance, run)
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "privacy redaction-queue complete")
            return 0
        if args.command == "privacy" and args.privacy_command == "redact":
            result = biffageops.redact_document(
                instance,
                run,
                doc_id=args.doc_id,
                mode=args.mode,
                target_college=args.target_college,
            )
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "privacy redact complete")
            return 0
        if args.command == "privacy" and args.privacy_command == "redact-required":
            result = biffageops.redact_required_documents(
                instance,
                run,
                mode=args.mode,
                target_college=args.target_college,
                limit=args.limit,
            )
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "privacy redact-required complete")
            return 0
        if args.command == "ui" and args.ui_command in {"serve", "open-test"}:
            from .web.app import serve

            run.log_action("ui_serve", instance.path, f"host={args.host}; port={args.port}; year={args.year}")
            if args.ui_command == "open-test":
                access_token = args.token or os.environ.get("COPROSCOPE_UI_TOKEN") or secrets.token_urlsafe(24)
                print(_ui_open_test_notice())
            else:
                access_token = os.environ.get("COPROSCOPE_UI_TOKEN") or secrets.token_urlsafe(24)
            serve(
                instance,
                year=args.year,
                host=args.host,
                port=args.port,
                access_token=access_token,
                unsafe_lan=args.unsafe_lan,
            )
            return 0
        if args.command == "decisions" and args.decisions_command == "build":
            result = decisionops.build_decision_register(instance, run, ensure_ag=not args.no_ag_analyze, doc_id=args.doc_id)
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "decisions build complete")
            return 0
        if args.command == "incidents" and args.incidents_command == "build":
            result = incidentops.build_incident_register(instance, run)
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "incidents build complete")
            return 0
        if args.command == "strategy" and args.strategy_command == "export":
            result = strategy.export_strategy(instance, run)
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "strategy export complete")
            return 0
        if args.command == "ag" and args.ag_command == "analyze":
            agscope.analyze(instance, run)
            print(json.dumps({"status": "ok", "command": "ag analyze"}))
            run.finish("OK", "ag analyze complete")
            return 0
        if args.command == "due-diligence" and args.dd_command == "summarize":
            path = summarize_due_diligence(instance, run)
            print(path)
            run.finish("OK", "due-diligence summarize complete")
            return 0
        if args.command == "audit360" and args.audit360_command == "prepare-anonymized":
            result = audit360.prepare_anonymized_audit_sources(
                instance,
                run,
                doc_id=args.doc_id,
                include_all=args.all,
            )
            print(json.dumps(result, indent=2, ensure_ascii=True))
            run.finish("OK", "audit360 prepare-anonymized complete")
            return 0
        if args.command == "docai" and args.docai_command == "ocr":
            path = docai.run_ocr(instance, run, doc_id=args.doc_id, mode=args.mode, engine=args.engine)
            print(path)
            run.finish("OK", "docai ocr complete")
            return 0
        if args.command == "docai" and args.docai_command == "enrich":
            path = docai.enrich(instance, run, backend=args.backend, doc_id=args.doc_id, mode=args.mode)
            print(path)
            run.finish("OK", "docai enrich complete")
            return 0
        if args.command == "docai" and args.docai_command == "status":
            print(json.dumps(docai.docai_status(instance, mode=args.mode), indent=2, ensure_ascii=True))
            run.finish("OK", "docai status complete")
            return 0
        if args.command == "pipeline" and args.pipeline_command == "run":
            run_pipeline(instance, run, copy_classified=not args.no_copy, docai_mode=args.docai)
            print(json.dumps({"status": "ok", "command": "pipeline run"}))
            run.finish("OK", "pipeline run complete")
            return 0
    except Exception as exc:  # noqa: BLE001
        run.log_error(str(exc))
        run.finish("ERROR", str(exc))
        raise
    return 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return _dispatch(args)


if __name__ == "__main__":
    raise SystemExit(main())
