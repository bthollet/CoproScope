from __future__ import annotations

from typing import Any


def register_feature_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
    rebranches: frozenset[str] = frozenset(),
) -> None:
    from .compta_rapprochement_view import register_compta_rapprochement_routes
    from .contractops_view import register_contractops_routes
    from .courriers_preuves_view import register_courriers_preuves_routes
    from .factures_review_view import register_factures_review_routes
    from .incidentops_view import register_incidentops_routes
    from .messages_entrants_view import register_messages_entrants_routes
    from .worksops_travaux_view import register_travaux_routes
    from .drive_mvp_view import register_drive_mvp_routes

    register_travaux_routes(app, templates, context, year, require_token, html_response)
    if "courriers_preuves" in rebranches:
        register_courriers_preuves_routes(app, templates, context, year, require_token, html_response)
    if "messages_entrants" in rebranches:
        register_messages_entrants_routes(app, templates, context, year, require_token, html_response)
    register_incidentops_routes(app, templates, context, year, require_token, html_response)
    register_contractops_routes(app, templates, context, year, require_token, html_response)
    register_compta_rapprochement_routes(app, templates, context, year, require_token, html_response)
    register_factures_review_routes(app, templates, context, year, require_token, html_response)
    if "synchro_drive" in rebranches:
        register_drive_mvp_routes(app, templates, context, year, require_token, html_response)
