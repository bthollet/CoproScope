from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

from ..core.common import RunContext, load_instance
from ..core.doctor import run_doctor
from ..modules import agscope, docuscope


TOOLS = [
    {"name": "doctor", "description": "Validate an instance configuration."},
    {"name": "inventory", "description": "Inventory raw documents for an instance."},
    {"name": "extract-text", "description": "Extract native text for an instance."},
    {"name": "classify", "description": "Classify documents for an instance."},
    {"name": "missing-docs", "description": "Produce the completeness report."},
    {"name": "kpi", "description": "Compute documentary KPIs."},
    {"name": "ag.analyze", "description": "Analyze AG documents."}
]


def _instance_arg(arguments: dict) -> str:
    instance = arguments.get("instance") or arguments.get("instance_root")
    if not instance:
        raise ValueError("Tool call requires 'instance' or 'instance_root'.")
    return str(instance)


def _capture_stdout(func, *args, **kwargs) -> str:
    previous = sys.stdout
    buffer = StringIO()
    try:
        sys.stdout = buffer
        func(*args, **kwargs)
    finally:
        sys.stdout = previous
    return buffer.getvalue().strip()


def _call_tool(name: str, arguments: dict) -> dict:
    instance_value = _instance_arg(arguments)
    if Path(instance_value).is_dir():
        instance = load_instance(None, instance_value)
    else:
        instance = load_instance(instance_value, None)
    run = RunContext(instance, command=f"mcp:{name}")

    if name == "doctor":
        output = _capture_stdout(run_doctor, instance, run)
        run.finish("OK", "mcp doctor")
        return {"content": output}
    if name == "inventory":
        path = docuscope.inventory(instance, run)
        run.finish("OK", "mcp inventory")
        return {"content": str(path)}
    if name == "extract-text":
        path = docuscope.extract_text(instance, run, doc_id=arguments.get("doc_id"))
        run.finish("OK", "mcp extract-text")
        return {"content": str(path)}
    if name == "classify":
        path = docuscope.classify(instance, run, copy_files=not bool(arguments.get("no_copy")))
        run.finish("OK", "mcp classify")
        return {"content": str(path)}
    if name == "missing-docs":
        path = docuscope.missing_docs(instance, run)
        run.finish("OK", "mcp missing-docs")
        return {"content": str(path)}
    if name == "kpi":
        path = docuscope.compute_kpis(instance, run)
        run.finish("OK", "mcp kpi")
        return {"content": str(path)}
    if name == "ag.analyze":
        agscope.analyze(instance, run)
        run.finish("OK", "mcp ag.analyze")
        return {"content": "ok"}
    raise ValueError(f"Unknown tool: {name}")


def serve_stdio() -> None:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        request = json.loads(line)
        method = request.get("method")
        request_id = request.get("id")
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2025-03-26",
                    "serverInfo": {"name": "coproscope", "version": "0.1.0"},
                    "capabilities": {"tools": {}},
                }
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                params = request.get("params", {})
                result = _call_tool(params.get("name", ""), params.get("arguments", {}))
            else:
                raise ValueError(f"Unsupported method: {method}")
            response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as exc:  # noqa: BLE001
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(exc)},
            }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
