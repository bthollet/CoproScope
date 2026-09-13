"""Route de la page AG, contentieux et passation.

Sortie de `_app_fragments/part_003.pyfrag`, qui depassait la limite de 600
lignes du depot. La route y avait ete ajoutee au fil de l'eau; elle a un objet
propre et se relit mieux seule.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request


def register_agcontentieux_routes(
    app: Any,
    templates: Any,
    context: Any,
    instance: Any,
    year: int,
    require_token: Any,
    shell_model: Any,
    html_response: Any,
) -> None:
    @app.get("/ag-contentieux", response_class=html_response)
    def agcontentieux_page(request: Request):
        from .agcontentieux_view import build_agcontentieux_passation_view
        from .resolutions_view import build_resolutions_view

        require_token(request)
        return templates.TemplateResponse(
            request=request,
            name="agcontentieux.html",
            context=context(
                request,
                "agcontentieux",
                model=shell_model(instance, year),
                agcontentieux=build_agcontentieux_passation_view(instance, year),
                resolutions=build_resolutions_view(instance),
            ),
        )
