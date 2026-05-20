from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from ..core.common import InstanceConfig
from .viewmodel import actions_to_csv, actions_to_markdown, build_dashboard_model, filter_action_items

try:  # Optional dependency: create_app raises a clearer error when it is absent.
    from fastapi import Request as FastAPIRequest  # type: ignore
except ImportError:  # pragma: no cover - depends on optional extra
    FastAPIRequest = Any  # type: ignore


PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"


def _require_web_stack():
    try:
        from fastapi import FastAPI, Request  # type: ignore
        from fastapi.responses import HTMLResponse, Response  # type: ignore
        from fastapi.staticfiles import StaticFiles  # type: ignore
        from fastapi.templating import Jinja2Templates  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "UI dependencies are missing. Install them with: python -m pip install -e .[ui]"
        ) from exc
    return FastAPI, Request, HTMLResponse, Response, StaticFiles, Jinja2Templates


def create_app(instance: InstanceConfig, year: int = 2025):
    FastAPI, Request, HTMLResponse, Response, StaticFiles, Jinja2Templates = _require_web_stack()

    app = FastAPI(title="CoproScope local", docs_url=None, redoc_url=None)
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    def context(request: FastAPIRequest, page: str, **extra: object) -> dict[str, object]:
        values: dict[str, object] = {
            "request": request,
            "page": page,
            "model": build_dashboard_model(instance, year),
        }
        values.update(extra)
        return values

    def _filtered_actions(scope: str = "", priority: str = "", status: str = "") -> tuple[dict[str, object], list[dict[str, str]]]:
        model = build_dashboard_model(instance, year)
        actions = filter_action_items(
            model["action_items"],  # type: ignore[arg-type]
            scope=scope,
            priority=priority,
            status=status,
        )
        return model, actions

    def _query_suffix(scope: str = "", priority: str = "", status: str = "") -> str:
        query = {
            key: value
            for key, value in {
                "scope": scope,
                "priority": priority,
                "status": status,
            }.items()
            if value
        }
        return f"?{urlencode(query)}" if query else ""

    def _download_headers(filename: str) -> dict[str, str]:
        return {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        }

    @app.get("/", response_class=HTMLResponse)
    def overview(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="overview.html", context=context(request, "overview"))

    @app.get("/actions", response_class=HTMLResponse)
    def actions(request: FastAPIRequest, scope: str = "", priority: str = "", status: str = ""):
        model, rows = _filtered_actions(scope=scope, priority=priority, status=status)
        return templates.TemplateResponse(
            request=request,
            name="actions.html",
            context=context(
                request,
                "actions",
                model=model,
                action_rows=rows,
                action_filters={
                    "scope": scope or "tous",
                    "priority": priority or "tous",
                    "status": status or "tous",
                },
                action_query_suffix=_query_suffix(scope=scope, priority=priority, status=status),
            ),
        )

    @app.get("/comptes", response_class=HTMLResponse)
    def accounting(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="accounting.html", context=context(request, "accounting"))

    @app.get("/documents", response_class=HTMLResponse)
    def documents(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="documents.html", context=context(request, "documents"))

    @app.get("/confidentialite", response_class=HTMLResponse)
    def privacy(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="privacy.html", context=context(request, "privacy"))

    @app.get("/chantiers", response_class=HTMLResponse)
    def workstreams(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="workstreams.html", context=context(request, "workstreams"))

    @app.get("/api/model")
    def api_model():
        return build_dashboard_model(instance, year)

    @app.get("/exports/actions.csv")
    def export_actions_csv(scope: str = "", priority: str = "", status: str = ""):
        _, rows = _filtered_actions(scope=scope, priority=priority, status=status)
        return Response(
            content=actions_to_csv(rows),
            media_type="text/csv; charset=utf-8",
            headers=_download_headers(f"coproscope_actions_{year}.csv"),
        )

    @app.get("/exports/actions.md")
    def export_actions_markdown(scope: str = "", priority: str = "", status: str = ""):
        _, rows = _filtered_actions(scope=scope, priority=priority, status=status)
        return Response(
            content=actions_to_markdown(rows),
            media_type="text/markdown; charset=utf-8",
            headers=_download_headers(f"coproscope_actions_{year}.md"),
        )

    @app.get("/health")
    def health():
        return {"status": "ok", "instance": instance.instance_id, "year": year}

    return app


def serve(instance: InstanceConfig, year: int = 2025, host: str = "127.0.0.1", port: int = 8765) -> None:
    try:
        import uvicorn  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "Uvicorn is missing. Install UI dependencies with: python -m pip install -e .[ui]"
        ) from exc

    uvicorn.run(create_app(instance, year), host=host, port=port, log_level="info")
