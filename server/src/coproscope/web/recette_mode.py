from __future__ import annotations

from typing import Any, Callable

from fastapi import Request

from ..core.common import InstanceConfig
from ..modules import recetteops


def register_recette_routes(
    app: Any,
    templates: Any,
    context: Callable[..., dict[str, object]],
    instance: InstanceConfig,
    require_token: Callable[[Any], None],
    html_response_class: Any,
    response_class: type[Any],
    download_headers: Callable[[str], dict[str, str]],
) -> None:
    @app.get("/recette", response_class=html_response_class)
    def recette_page(request: Request):
        require_token(request)
        return templates.TemplateResponse(
            request=request,
            name="recette.html",
            context=context(
                request,
                "recette",
                annotations=recetteops.list_annotations(instance),
                recette_export_json="/exports/recette-annotations.json",
                recette_export_md="/exports/recette-annotations.md",
            ),
        )

    @app.post("/recette/annotations")
    async def save_recette_annotation(request: Request):
        require_token(request)
        payload = await request.json()
        if not isinstance(payload, dict):
            payload = {}
        saved = recetteops.save_annotation(instance, payload)
        return {"ok": True, "annotation_id": saved["annotation_id"]}

    @app.get("/exports/recette-annotations.json")
    def export_recette_json(request: Request):
        require_token(request)
        return response_class(
            content=recetteops.render_json_export(instance),
            media_type="application/json; charset=utf-8",
            headers=download_headers("recette_annotations.json"),
        )

    @app.get("/exports/recette-annotations.md")
    def export_recette_markdown(request: Request):
        require_token(request)
        return response_class(
            content=recetteops.render_markdown_export(instance),
            media_type="text/markdown; charset=utf-8",
            headers=download_headers("recette_annotations.md"),
        )
