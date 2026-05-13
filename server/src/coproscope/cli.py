from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core.common import RunContext, load_instance
from .core.doctor import run_doctor
from .core.due_diligence import summarize_due_diligence
from .core.pipeline import run_pipeline
from .core.share import audit_repo
from .modules import agscope, docuscope


def _instance_parent() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--instance", help="Path to an instance.yml file or instance directory.")
    parent.add_argument("--instance-root", help="Path to an instance directory containing instance.yml.")
    return parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="coprocs", description="CoproScope CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    instance_parent = _instance_parent()

    subparsers.add_parser("doctor", parents=[instance_parent], help="Validate instance configuration and dependencies.")
    subparsers.add_parser("inventory", parents=[instance_parent], help="Inventory raw documents.")

    extract = subparsers.add_parser("extract-text", parents=[instance_parent], help="Extract native text.")
    extract.add_argument("--doc-id", help="Limit extraction to one document id.")

    classify = subparsers.add_parser("classify", parents=[instance_parent], help="Classify documents.")
    classify.add_argument("--no-copy", action="store_true", help="Do not copy files into the classified staging area.")

    subparsers.add_parser("missing-docs", parents=[instance_parent], help="Produce completeness report.")
    subparsers.add_parser("kpi", parents=[instance_parent], help="Compute documentary KPIs.")

    ag_parser = subparsers.add_parser("ag", parents=[instance_parent], help="AG module commands.")
    ag_subparsers = ag_parser.add_subparsers(dest="ag_command", required=True)
    ag_subparsers.add_parser(
        "analyze",
        parents=[instance_parent],
        help="Analyze AG documents and create a preparation register.",
    )

    dd_parser = subparsers.add_parser("due-diligence", parents=[instance_parent], help="Due diligence commands.")
    dd_subparsers = dd_parser.add_subparsers(dest="dd_command", required=True)
    dd_subparsers.add_parser(
        "summarize",
        parents=[instance_parent],
        help="Summarize cached public due diligence searches.",
    )

    pipeline = subparsers.add_parser("pipeline", parents=[instance_parent], help="Run the v1 CoproScope pipeline.")
    pipeline_subparsers = pipeline.add_subparsers(dest="pipeline_command", required=True)
    run_parser = pipeline_subparsers.add_parser("run", parents=[instance_parent], help="Run the pipeline on the instance.")
    run_parser.add_argument("--no-copy", action="store_true", help="Do not stage classified file copies.")

    mcp_parser = subparsers.add_parser("mcp", help="Minimal MCP-compatible stdio server.")
    mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command", required=True)
    mcp_subparsers.add_parser("serve", help="Serve stdio JSON-RPC messages.")

    share_parser = subparsers.add_parser("share-audit", help="Audit what is safe to publish to GitHub.")
    share_parser.add_argument("--repo-root", default="..", help="Repository root to audit.")
    share_parser.add_argument(
        "--config",
        default="src/coproscope/configs/github_sharing.default.yml",
        help="Path to the sharing policy file.",
    )

    return parser


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "mcp":
        from .mcp.server import serve_stdio

        serve_stdio()
        return 0

    if args.command == "share-audit":
        repo_root = Path(args.repo_root).resolve()
        config_path = Path(args.config).resolve()
        result = audit_repo(repo_root, config_path)
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0 if not result["blocked"] else 1

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
            path = docuscope.extract_text(instance, run, doc_id=args.doc_id)
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
        if args.command == "pipeline" and args.pipeline_command == "run":
            run_pipeline(instance, run, copy_classified=not args.no_copy)
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
