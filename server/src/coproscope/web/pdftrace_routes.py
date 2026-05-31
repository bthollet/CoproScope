from __future__ import annotations

from collections.abc import Callable
from urllib.parse import quote, urlencode

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from ..core.common import InstanceConfig


def register_pdftrace_routes(
    app,
    instance: InstanceConfig,
    require_token: Callable[[Request], None],
    url_with_token: Callable[[Request, str], str],
    invalidate_dashboard_model_cache: Callable[[], None],
) -> None:
    @app.post("/documents/{doc_id}/traces")
    async def document_trace_save(request: Request, doc_id: str):
        from .document_viewer import DocumentNotFoundError, build_document_detail
        from ..modules import pdftrace_registry

        require_token(request)
        try:
            detail = build_document_detail(instance, doc_id)
        except DocumentNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Document introuvable.") from exc
        form = await request.form()
        try:
            saved = pdftrace_registry.save_zone_trace(instance, detail["doc"], form)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        invalidate_dashboard_model_cache()
        query = urlencode({"trace": "saved", "trace_id": saved.get("trace_id", "")})
        target = f"/documents/{quote(doc_id)}?{query}"
        return RedirectResponse(url=url_with_token(request, target), status_code=303)


__all__ = ["register_pdftrace_routes"]
