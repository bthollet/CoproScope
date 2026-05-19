from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core.common import RunContext, load_instance
from .core.doctor import run_doctor
from .core.due_diligence import summarize_due_diligence
from .core.pipeline import run_pipeline
from .core.share import audit_repo, export_shareable
from .modules import accounting, agscope, docai, docuscope, evidenceops, gristops, strategy, tools, workers


COMMAND_ALIASES = {
    "diagnostic": "doctor",
    "inventaire": "inventory",
    "extraire-texte": "extract-text",
    "classer": "classify",
    "pieces-manquantes": "missing-docs",
    "indicateurs": "kpi",
    "assemblee-generale": "ag",
    "diligence": "due-diligence",
    "chaine": "pipeline",
    "ia-doc": "docai",
    "outils": "tools",
    "compta": "accounting",
    "strategie": "strategy",
    "audit-partage": "share-audit",
    "export-partage": "share-export",
}

SUBCOMMAND_ALIASES = {
    "ag_command": {"analyser": "analyze"},
    "dd_command": {"synthese": "summarize"},
    "pipeline_command": {"executer": "run"},
    "tools_command": {"statut": "status"},
    "accounting_command": {"reconstituer": "reconstruct", "controles": "controls"},
    "grist_command": {"synchroniser": "sync"},
    "evidence_command": {"construire": "build"},
    "workers_command": {"executer": "run"},
    "strategy_command": {"exporter": "export"},
}


def _instance_parent() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--instance", help="Chemin vers un fichier instance.yml ou un dossier d'instance.")
    parent.add_argument("--instance-root", help="Chemin vers un dossier d'instance contenant instance.yml.")
    return parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="coprocs", description="CLI CoproScope")
    subparsers = parser.add_subparsers(dest="command", required=True)
    instance_parent = _instance_parent()

    subparsers.add_parser("doctor", aliases=["diagnostic"], parents=[instance_parent], help="Diagnostiquer une instance et ses dependances.")
    subparsers.add_parser("inventory", aliases=["inventaire"], parents=[instance_parent], help="Inventorier les documents bruts.")

    extract = subparsers.add_parser("extract-text", aliases=["extraire-texte"], parents=[instance_parent], help="Extraire le texte natif.")
    extract.add_argument("--doc-id", help="Limiter l'extraction a un identifiant documentaire.")
    extract.add_argument(
        "--docai",
        choices=["off", "local-basic", "local-heavy"],
        default="off",
        help="Activer la couche Document Intelligence apres extraction native.",
    )

    classify = subparsers.add_parser("classify", aliases=["classer"], parents=[instance_parent], help="Classer les documents.")
    classify.add_argument("--no-copy", action="store_true", help="Ne pas copier les fichiers dans la zone de classement.")

    subparsers.add_parser("missing-docs", aliases=["pieces-manquantes"], parents=[instance_parent], help="Produire le rapport de completude.")
    subparsers.add_parser("kpi", aliases=["indicateurs"], parents=[instance_parent], help="Calculer les indicateurs documentaires.")

    tools_parser = subparsers.add_parser("tools", aliases=["outils"], help="Verifier les outils systeme et modules Python.")
    tools_subparsers = tools_parser.add_subparsers(dest="tools_command", required=True)
    tools_subparsers.add_parser("status", aliases=["statut"], help="Afficher les outils disponibles.")

    accounting_parser = subparsers.add_parser("accounting", aliases=["compta"], parents=[instance_parent], help="Commandes ComptaScope.")
    accounting_subparsers = accounting_parser.add_subparsers(dest="accounting_command", required=True)
    accounting_reconstruct = accounting_subparsers.add_parser(
        "reconstruct",
        aliases=["reconstituer"],
        parents=[instance_parent],
        help="Reconstituer une comptabilite candidate depuis les factures.",
    )
    accounting_reconstruct.add_argument("--year", "--annee", dest="year", type=int, required=True)
    accounting_controls = accounting_subparsers.add_parser(
        "controls",
        aliases=["controles"],
        parents=[instance_parent],
        help="Synthese des controles comptables.",
    )
    accounting_controls.add_argument("--year", "--annee", dest="year", type=int, required=True)

    grist_parser = subparsers.add_parser("grist", parents=[instance_parent], help="Exports et synchronisation Grist.")
    grist_subparsers = grist_parser.add_subparsers(dest="grist_command", required=True)
    grist_sync = grist_subparsers.add_parser("sync", aliases=["synchroniser"], parents=[instance_parent], help="Exporter les tables Grist.")
    grist_sync.add_argument("--target", choices=["local", "self-hosted"], default="local")
    grist_sync.add_argument("--dataset", choices=["demo", "private"], default="demo")
    grist_sync.add_argument("--year", "--annee", dest="year", type=int, default=2025)

    evidence_parser = subparsers.add_parser("evidence", parents=[instance_parent], help="Rapports Evidence locaux.")
    evidence_subparsers = evidence_parser.add_subparsers(dest="evidence_command", required=True)
    evidence_build = evidence_subparsers.add_parser("build", aliases=["construire"], parents=[instance_parent], help="Construire un rapport Evidence.")
    evidence_build.add_argument("--dataset", choices=["demo", "private"], default="demo")
    evidence_build.add_argument("--year", "--annee", dest="year", type=int, default=2025)

    workers_parser = subparsers.add_parser("workers", parents=[instance_parent], help="Executer des workers CoproScope.")
    workers_subparsers = workers_parser.add_subparsers(dest="workers_command", required=True)
    workers_run = workers_subparsers.add_parser("run", aliases=["executer"], parents=[instance_parent], help="Executer un groupe de workers.")
    workers_run.add_argument("--scope", choices=["inventory", "documents", "syndic", "ag", "invoices", "accounting", "dashboards", "all"], default="all")
    workers_run.add_argument("--year", "--annee", dest="year", type=int, default=2025)

    strategy_parser = subparsers.add_parser("strategy", aliases=["strategie"], parents=[instance_parent], help="Strategie et roadmap produit.")
    strategy_subparsers = strategy_parser.add_subparsers(dest="strategy_command", required=True)
    strategy_subparsers.add_parser("export", aliases=["exporter"], parents=[instance_parent], help="Exporter une strategie locale.")

    ag_parser = subparsers.add_parser("ag", aliases=["assemblee-generale"], parents=[instance_parent], help="Commandes du module AG.")
    ag_subparsers = ag_parser.add_subparsers(dest="ag_command", required=True)
    ag_subparsers.add_parser(
        "analyze",
        aliases=["analyser"],
        parents=[instance_parent],
        help="Analyser les documents AG et creer un registre de preparation.",
    )

    dd_parser = subparsers.add_parser("due-diligence", aliases=["diligence"], parents=[instance_parent], help="Commandes de diligence.")
    dd_subparsers = dd_parser.add_subparsers(dest="dd_command", required=True)
    dd_subparsers.add_parser(
        "summarize",
        aliases=["synthese"],
        parents=[instance_parent],
        help="Resumer les recherches publiques de diligence deja en cache.",
    )

    pipeline = subparsers.add_parser("pipeline", aliases=["chaine"], parents=[instance_parent], help="Executer la chaine CoproScope v1.")
    pipeline_subparsers = pipeline.add_subparsers(dest="pipeline_command", required=True)
    run_parser = pipeline_subparsers.add_parser("run", aliases=["executer"], parents=[instance_parent], help="Executer la chaine sur l'instance.")
    run_parser.add_argument("--no-copy", action="store_true", help="Ne pas preparer de copies classees.")
    run_parser.add_argument(
        "--docai",
        choices=["off", "local-basic", "local-heavy"],
        default="off",
        help="Activer Document Intelligence dans le pipeline.",
    )

    docai_parser = subparsers.add_parser("docai", aliases=["ia-doc"], parents=[instance_parent], help="Commandes Document Intelligence locales.")
    docai_subparsers = docai_parser.add_subparsers(dest="docai_command", required=True)
    docai_ocr = docai_subparsers.add_parser("ocr", parents=[instance_parent], help="Executer l'OCR local sur les documents OCR_REQUIRED.")
    docai_ocr.add_argument("--doc-id", help="Limiter l'OCR a un identifiant documentaire.")
    docai_ocr.add_argument("--engine", choices=["sidecar-ocr", "rapidocr", "gutenocr"], help="Forcer un moteur OCR local.")
    docai_ocr.add_argument("--mode", choices=["local-basic", "local-heavy"], default="local-basic", help="Mode DocAI a utiliser.")

    docai_enrich = docai_subparsers.add_parser("enrich", parents=[instance_parent], help="Enrichir des documents via un backend DocAI.")
    docai_enrich.add_argument("--doc-id", help="Limiter l'enrichissement a un identifiant documentaire.")
    docai_enrich.add_argument("--backend", required=True, choices=["docling", "qwen-vl", "layoutlmv3", "layoutalm"], help="Backend d'enrichissement.")
    docai_enrich.add_argument("--mode", choices=["local-basic", "local-heavy"], default="local-basic", help="Mode DocAI a utiliser.")

    docai_status = docai_subparsers.add_parser("status", parents=[instance_parent], help="Afficher les backends DocAI disponibles.")
    docai_status.add_argument("--mode", choices=["off", "local-basic", "local-heavy"], default=None, help="Mode DocAI a evaluer.")

    mcp_parser = subparsers.add_parser("mcp", help="Serveur stdio minimal compatible MCP.")
    mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command", required=True)
    mcp_subparsers.add_parser("serve", help="Servir les messages JSON-RPC sur stdio.")

    share_parser = subparsers.add_parser("share-audit", aliases=["audit-partage"], help="Auditer ce qui peut etre publie sur GitHub.")
    share_parser.add_argument("--repo-root", default="..", help="Racine du depot a auditer.")
    share_parser.add_argument(
        "--config",
        default="src/coproscope/configs/github_sharing.default.yml",
        help="Chemin vers le fichier de politique de partage.",
    )
    share_export = subparsers.add_parser("share-export", aliases=["export-partage"], help="Copier le sous-ensemble publiable dans un dossier propre.")
    share_export.add_argument("--repo-root", default="..", help="Racine du depot a auditer puis exporter.")
    share_export.add_argument(
        "--config",
        default="src/coproscope/configs/github_sharing.default.yml",
        help="Chemin vers le fichier de politique de partage.",
    )
    share_export.add_argument("--output-dir", required=True, help="Dossier destination pour l'export public.")
    share_export.add_argument("--clean", action="store_true", help="Supprimer le dossier d'export avant la copie.")

    return parser


def _normaliser_commandes(args: argparse.Namespace) -> None:
    args.command = COMMAND_ALIASES.get(args.command, args.command)
    for field_name, aliases in SUBCOMMAND_ALIASES.items():
        current = getattr(args, field_name, None)
        if current is not None:
            setattr(args, field_name, aliases.get(current, current))


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
        return 0 if not private_violations else 1
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

    instance = load_instance(args.instance, args.instance_root)
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
