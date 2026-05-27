from __future__ import annotations

from typing import Any


def register_feature_routes(
    app: Any,
    templates: Any,
    context: Any,
    year: int,
    require_token: Any,
    html_response: Any,
) -> None:
    from .coffre_partage_view import register_coffre_partage_routes
    from .activity_view import register_activity_routes
    from .compta_rapprochement_view import register_compta_rapprochement_routes
    from .contractops_view import register_contractops_routes
    from .courriers_preuves_view import register_courriers_preuves_routes
    from .governance_atelier_ag_view import register_governance_atelier_ag_routes
    from .governance_cr_cs_view import register_governance_cr_cs_routes
    from .incidentops_view import register_incidentops_routes
    from .messages_entrants_view import register_messages_entrants_routes
    from .participants_ag_view import register_participants_ag_routes
    from .roles_commissions_view import register_roles_commissions_routes
    from .suggestions_view import register_suggestions_routes
    from .worksops_travaux_view import register_travaux_routes

    register_travaux_routes(app, templates, context, year, require_token, html_response)
    register_coffre_partage_routes(app, templates, context, year, require_token, html_response)
    register_governance_cr_cs_routes(app, templates, context, year, require_token, html_response)
    register_governance_atelier_ag_routes(app, templates, context, year, require_token, html_response)
    register_participants_ag_routes(app, templates, context, year, require_token, html_response)
    register_roles_commissions_routes(app, templates, context, year, require_token, html_response)
    register_courriers_preuves_routes(app, templates, context, year, require_token, html_response)
    register_messages_entrants_routes(app, templates, context, year, require_token, html_response)
    register_incidentops_routes(app, templates, context, year, require_token, html_response)
    register_contractops_routes(app, templates, context, year, require_token, html_response)
    register_compta_rapprochement_routes(app, templates, context, year, require_token, html_response)
    register_activity_routes(app, templates, context, year, require_token, html_response)
    register_suggestions_routes(app, templates, context, year, require_token, html_response)
