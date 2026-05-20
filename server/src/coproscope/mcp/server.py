from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

from ..core.common import RunContext, load_instance
from ..core.doctor import run_doctor
from ..modules import agscope, docai, docuscope


TOOLS = [
    {"name": "doctor", "description": "Diagnostiquer une instance CoproScope."},
    {"name": "diagnostic", "description": "Alias francophone de doctor."},
    {"name": "inventory", "description": "Inventorier les documents bruts d'une instance."},
    {"name": "inventaire", "description": "Alias francophone de inventory."},
    {"name": "extract-text", "description": "Extraire le texte natif d'une instance."},
    {"name": "extraire-texte", "description": "Alias francophone de extract-text."},
    {"name": "classify", "description": "Classer les documents d'une instance."},
    {"name": "classer", "description": "Alias francophone de classify."},
    {"name": "missing-docs", "description": "Produire le rapport de completude."},
    {"name": "pieces-manquantes", "description": "Alias francophone de missing-docs."},
    {"name": "kpi", "description": "Calculer les indicateurs documentaires."},
    {"name": "indicateurs", "description": "Alias francophone de kpi."},
    {"name": "ag.analyze", "description": "Analyser les documents d'AG."},
    {"name": "ag.analyser", "description": "Alias francophone de ag.analyze."},
    {"name": "docai.status", "description": "Lister les backends Document Intelligence disponibles."},
    {"name": "docai.ocr", "description": "Executer l'OCR local Document Intelligence."},
    {"name": "docai.enrich", "description": "Enrichir un document via Docling, Qwen VL ou LayoutLMv3."},
]

TOOL_ALIASES = {
    "diagnostic": "doctor",
    "inventaire": "inventory",
    "extraire-texte": "extract-text",
    "classer": "classify",
    "pieces-manquantes": "missing-docs",
    "indicateurs": "kpi",
    "ag.analyser": "ag.analyze",
}


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
    name = TOOL_ALIASES.get(name, name)
    instance_value = _instance_arg(arguments)
    if Path(instance_value).is_dir():
        instance = load_instance(None, instance_value)
    else:
        instance = load_instance(instance_value, None)
    run = RunContext(instance, command=f"mcp:{name}")

    if name == "doctor":
        output = _capture_stdout(run_doctor, instance, run)
        run.finish("OK", "mcp diagnostic")
        return {"content": output}
    if name == "inventory":
        path = docuscope.inventory(instance, run)
        run.finish("OK", "mcp inventaire")
        return {"content": str(path)}
    if name == "extract-text":
        path = docuscope.extract_text(instance, run, doc_id=arguments.get("doc_id"))
        run.finish("OK", "mcp extraire-texte")
        return {"content": str(path)}
    if name == "classify":
        path = docuscope.classify(instance, run, copy_files=not bool(arguments.get("no_copy")))
        run.finish("OK", "mcp classer")
        return {"content": str(path)}
    if name == "missing-docs":
        path = docuscope.missing_docs(instance, run)
        run.finish("OK", "mcp pieces-manquantes")
        return {"content": str(path)}
    if name == "kpi":
        path = docuscope.compute_kpis(instance, run)
        run.finish("OK", "mcp indicateurs")
        return {"content": str(path)}
    if name == "ag.analyze":
        agscope.analyze(instance, run)
        run.finish("OK", "mcp ag.analyser")
        return {"content": "ok"}
    if name == "docai.status":
        result = docai.docai_status(instance, mode=arguments.get("mode"))
        run.finish("OK", "mcp docai.status")
        return {"content": json.dumps(result, ensure_ascii=True)}
    if name == "docai.ocr":
        path = docai.run_ocr(instance, run, doc_id=arguments.get("doc_id"), mode=arguments.get("mode", "local_basic"), engine=arguments.get("engine"))
        run.finish("OK", "mcp docai.ocr")
        return {"content": str(path)}
    if name == "docai.enrich":
        path = docai.enrich(instance, run, backend=arguments.get("backend", "docling"), doc_id=arguments.get("doc_id"), mode=arguments.get("mode", "local_basic"))
        run.finish("OK", "mcp docai.enrich")
        return {"content": str(path)}
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
