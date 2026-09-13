"""Route de l'ecran de controle de gouvernance.

Une seule route, deux vues. La vue, les filtres, le constat d'origine et la
ligne choisie vivent dans la requete: l'etat est dans l'adresse, comme `?tab=`
ailleurs dans le produit. Consequence directe et voulue: un filtre pose survit a
un aller en synthese et a un retour, parce qu'il n'a jamais quitte l'URL - et la
page se partage, se met en signet et se recharge sans rien perdre.

Aucun `role="tablist"` ni `aria-selected` n'est ecrit ici ni dans le gabarit. Le
depot n'en contient aucune occurrence, et le motif ARIA complet exige une
gestion clavier - fleches, Home/Fin, `tabindex` roulant - qui ne sera pas
ecrite. Un motif a moitie implemente promet au lecteur d'ecran un comportement
qui n'existe pas. Des liens dans un `nav` nomme donnent nativement le clavier,
le parcours au lecteur d'ecran et l'ouverture dans un nouvel onglet;
`aria-current="page"` marque l'actif, comme partout ailleurs dans le depot.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import RedirectResponse


def register_controle_gouvernance_routes(
    app: Any,
    templates: Any,
    context: Any,
    instance: Any,
    year: int,
    require_token: Any,
    shell_model: Any,
    html_response: Any,
) -> None:
    @app.get("/controle-gouvernance", response_class=html_response)
    def controle_gouvernance_page(request: Request):
        from .controle_gouvernance_view import build_controle_gouvernance_view

        require_token(request)
        params = dict(request.query_params)
        return templates.TemplateResponse(
            request=request,
            name="controle_gouvernance.html",
            context=context(
                request,
                "controle_gouvernance",
                model=shell_model(instance, year),
                controle=build_controle_gouvernance_view(
                    instance, year, params, token=str(params.get("token") or "")
                ),
            ),
        )

    @app.post("/controle-gouvernance/conclusion")
    async def controle_gouvernance_conclusion(request: Request):
        """Enregistre la conclusion d'un controle, puis renvoie a la ligne.

        **Le geste que la page promettait sans l'offrir.** Elle affichait sous
        le tableau: *« Le geste n'est pas encore cable »*, et la colonne « Ma
        conclusion » montrait toujours `A instruire`. Arbitrage de Brice le
        2026-09-09: *« bien evidemment on trace le controle »*.

        **Renvoi apres ecriture, et non rendu direct.** Un rechargement de page
        rejouerait l'envoi et ecrirait une seconde conclusion identique. Le
        renvoi ramene l'utilisateur a **sa** ligne, filtres compris, parce que
        l'etat de cet ecran vit dans l'adresse.

        **Une conclusion refusee ne se perd pas en silence:** son motif revient
        dans l'adresse et la page le montre. Un formulaire qui rejette sans le
        dire fait croire a l'utilisateur qu'il a conclu.
        """
        from ._controle_gouvernance_conclusion import ConclusionRefusee, enregistrer

        require_token(request)
        form = await request.form()
        retour = str(form.get("retour") or "/controle-gouvernance")
        params: dict[str, str] = {}
        try:
            ligne = enregistrer(
                instance,
                str(form.get("sujet_kind") or "acte"),
                str(form.get("sujet_id") or ""),
                str(form.get("verdict") or ""),
                str(form.get("texte") or ""),
            )
        except ConclusionRefusee as refus:
            params["conclusion_refus"] = str(refus)
        else:
            params["conclusion_ecrite"] = ligne["sujet_id"]

        separateur = "&" if "?" in retour else "?"
        return RedirectResponse(retour + separateur + urlencode(params), status_code=303)
