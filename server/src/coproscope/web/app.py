from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from ..core.common import InstanceConfig
from .depot import (
    DepositError,
    build_local_export_zip,
    create_deposit_from_uploads,
    latest_deposit_manifest,
    read_deposit_manifest,
    run_accounting_pipeline,
    run_all_non_heavy_pipeline,
    run_docai_pipeline,
    run_docops_pipeline,
    run_light_pipeline,
)
from .viewmodel import actions_to_csv, actions_to_markdown, build_dashboard_model, filter_action_items

try:  # Optional dependency: create_app raises a clearer error when it is absent.
    from fastapi import Request as FastAPIRequest  # type: ignore
except ImportError:  # pragma: no cover - depends on optional extra
    FastAPIRequest = Any  # type: ignore


PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _require_web_stack():
    try:
        from fastapi import FastAPI, HTTPException, Request  # type: ignore
        from fastapi.responses import HTMLResponse, RedirectResponse, Response  # type: ignore
        from fastapi.staticfiles import StaticFiles  # type: ignore
        from fastapi.templating import Jinja2Templates  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "UI dependencies are missing. Install them with: python -m pip install -e .[ui]"
        ) from exc
    return FastAPI, HTTPException, Request, HTMLResponse, RedirectResponse, Response, StaticFiles, Jinja2Templates


def create_app(instance: InstanceConfig, year: int = 2025, access_token: str | None = None):
    FastAPI, HTTPException, Request, HTMLResponse, RedirectResponse, Response, StaticFiles, Jinja2Templates = _require_web_stack()

    app = FastAPI(title="CoproScope local", docs_url=None, redoc_url=None)
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    def _request_has_token(request: FastAPIRequest) -> bool:
        if not access_token:
            return False
        supplied = request.query_params.get("token") or request.headers.get("x-coproscope-token", "")
        return bool(supplied and secrets.compare_digest(str(supplied), access_token))

    def _require_token(request: FastAPIRequest) -> None:
        if not access_token:
            return
        if not _request_has_token(request):
            raise HTTPException(status_code=403, detail="Jeton local requis.")

    def _token_suffix(request: FastAPIRequest) -> str:
        if not access_token or not _request_has_token(request):
            return ""
        return f"token={quote(access_token)}"

    def _url_with_token(request: FastAPIRequest, path: str) -> str:
        suffix = _token_suffix(request)
        if not suffix:
            return path
        separator = "&" if "?" in path else "?"
        return f"{path}{separator}{suffix}"

    def context(request: FastAPIRequest, page: str, **extra: object) -> dict[str, object]:
        values: dict[str, object] = {
            "request": request,
            "page": page,
            "model": build_dashboard_model(instance, year),
            "ui_token_query": f"?{_token_suffix(request)}" if _token_suffix(request) else "",
            "ui_token_param": _token_suffix(request),
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

    @app.get("/pieces", response_class=HTMLResponse)
    def pieces(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="pieces.html", context=context(request, "pieces"))

    @app.get("/confidentialite", response_class=HTMLResponse)
    def privacy(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="privacy.html", context=context(request, "privacy"))

    @app.get("/chantiers", response_class=HTMLResponse)
    def workstreams(request: FastAPIRequest):
        return templates.TemplateResponse(request=request, name="workstreams.html", context=context(request, "workstreams"))

    @app.get("/depot", response_class=HTMLResponse)
    def depot_page(request: FastAPIRequest, depot: str = "", status: str = ""):
        _require_token(request)
        selected = read_deposit_manifest(instance, depot) if depot else latest_deposit_manifest(instance)
        return templates.TemplateResponse(
            request=request,
            name="depot.html",
            context=context(request, "depot", selected_deposit=selected, pipeline_status=status),
        )

    @app.post("/depot")
    async def depot_upload(request: FastAPIRequest):
        _require_token(request)
        form = await request.form()
        uploads = [value for key, value in form.multi_items() if key in {"files", "file"}]
        try:
            manifest = create_deposit_from_uploads(instance, uploads)
        except DepositError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        run_light_pipeline(instance, manifest)
        return RedirectResponse(
            url=_url_with_token(request, f"/depot?depot={manifest['deposit_id']}&status=uploaded"),
            status_code=303,
        )

    @app.post("/depot/{deposit_id}/pipeline/{pipeline}")
    def depot_pipeline(request: FastAPIRequest, deposit_id: str, pipeline: str):
        _require_token(request)
        manifest = read_deposit_manifest(instance, deposit_id)
        if manifest is None:
            raise HTTPException(status_code=404, detail="Depot introuvable.")
        if pipeline == "docai":
            run_docai_pipeline(instance, manifest)
        elif pipeline == "docops":
            run_docops_pipeline(instance, manifest)
        elif pipeline == "compta":
            run_accounting_pipeline(instance, manifest, year)
        elif pipeline == "all":
            run_all_non_heavy_pipeline(instance, manifest, year)
        else:
            raise HTTPException(status_code=404, detail="Pipeline inconnu.")
        return RedirectResponse(
            url=_url_with_token(request, f"/depot?depot={deposit_id}&status={pipeline}"),
            status_code=303,
        )

    @app.get("/api/model")
    def api_model(request: FastAPIRequest):
        _require_token(request)
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

    @app.get("/exports/local.zip")
    def export_local_zip(request: FastAPIRequest):
        _require_token(request)
        _, rows = _filtered_actions()
        payload = build_local_export_zip(
            instance,
            year=year,
            actions_csv=actions_to_csv(rows),
            actions_markdown=actions_to_markdown(rows),
        )
        return Response(
            content=payload,
            media_type="application/zip",
            headers=_download_headers(f"coproscope_pack_local_{year}.zip"),
        )

    @app.get("/health")
    def health():
        return {"status": "ok", "instance": instance.instance_id, "year": year}

    return app


def _ui_token() -> str:
    return os.environ.get("COPROSCOPE_UI_TOKEN") or secrets.token_urlsafe(24)


def serve(
    instance: InstanceConfig,
    year: int = 2025,
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    access_token: str | None = None,
    unsafe_lan: bool = False,
) -> None:
    if host not in LOOPBACK_HOSTS and not unsafe_lan:
        raise ValueError("Refusing to expose the UI outside loopback without --unsafe-lan.")
    access_token = access_token or _ui_token()
    try:
        import uvicorn  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            "Uvicorn is missing. Install UI dependencies with: python -m pip install -e .[ui]"
        ) from exc

    print(f"CoproScope UI token URL: http://{host}:{port}/?token={quote(access_token)}")
    uvicorn.run(create_app(instance, year, access_token=access_token), host=host, port=port, log_level="info")
