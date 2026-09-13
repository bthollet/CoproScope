"""Routes de la page « Documents non lus ».

Une lecture, une ecriture. La lecture montre ce qui n'a pas pu etre lu et
demande l'accord; l'ecriture enregistre la reponse et, si c'est un accord,
lance la reconnaissance de texte pour CE document.

**Un document a la fois, et c'est voulu.** Un accord global sur un lot n'est
pas un accord: la personne doit voir ce qu'elle autorise.

**Le travail part en arriere-plan.** Mesure du 2026-09-03: cinq secondes par
page, soit deux minutes pour le dossier de devis de 28 pages du corpus de
recette. Une requete HTTP ne reste pas ouverte aussi longtemps. La reponse
revient donc immediatement, et la page dit ce qui tourne encore.
"""

from __future__ import annotations

import threading
from typing import Any

from fastapi import Request
from fastapi.responses import RedirectResponse

# Le moteur est impose. Sans lui, `run_ocr` prend la branche `rapidocr`, qui
# vient avant tesseract dans la chaine de `elif`: quand rapidocr ne rend rien,
# tesseract n'est jamais essaye. Mesure du 2026-09-03: 94 secondes pour un
# document de 3 pages, zero caractere produit, `ocr_engine = unavailable`. Avec
# tesseract impose, le meme document rend 15 196 caracteres en 15 secondes.
MOTEUR = "tesseract"


def register_lisibilite_routes(
    app: Any,
    templates: Any,
    context: Any,
    instance: Any,
    year: int,
    require_token: Any,
    shell_model: Any,
    html_response: Any,
    url_with_token: Any,
) -> None:
    @app.get("/documents/non-lus", response_class=html_response)
    def documents_non_lus(request: Request):
        from .lisibilite_view import build_lisibilite_view

        require_token(request)
        return templates.TemplateResponse(
            request=request,
            name="documents_non_lus.html",
            context=context(
                request,
                "documents",
                model=shell_model(instance, year),
                lisibilite=build_lisibilite_view(instance),
            ),
        )

    @app.post("/documents/non-lus/repondre")
    async def repondre(request: Request):
        from ..modules.lisibilite import ACCEPTE, REFUSE, enregistrer_decision

        require_token(request)
        form = await request.form()
        doc_id = str(form.get("doc_id") or "").strip()
        reponse = str(form.get("reponse") or "").strip().upper()
        if not doc_id or reponse not in {ACCEPTE, REFUSE}:
            return RedirectResponse(
                url=url_with_token(request, "/documents/non-lus?erreur=reponse_invalide"),
                status_code=303,
            )

        enregistrer_decision(
            instance,
            doc_id,
            reponse,
            nom=str(form.get("nom") or ""),
            pages=int(str(form.get("pages") or "0") or 0),
            caracteres=0,
        )
        suite = ""
        if reponse == ACCEPTE:
            _lancer_ocr_en_fond(instance, doc_id)
            suite = "&lance=1"
        return RedirectResponse(
            url=url_with_token(request, f"/documents/non-lus?doc={doc_id}{suite}"),
            status_code=303,
        )


def executer_ocr(instance: Any, doc_id: str) -> bool:
    """Reconnaissance de texte pour un document. Rend vrai si elle a abouti.

    **Le resultat est verifie, pas suppose.** `run_ocr` ne leve rien quand
    aucun moteur ne produit de texte: il ecrit `ocr_engine = unavailable` et
    passe. Conclure au succes depuis l'absence d'exception a fait annoncer
    « reconnaissance terminee » sur un document reste vide. On relit donc le
    registre.

    Le mode `local_basic` est impose ici plutot que lu dans l'instance: le
    reglage `docai.mode` vaut `off` par defaut, et c'est justement pourquoi
    aucun document marque `OCR_REQUIRED` n'etait jamais traite. L'accord de
    l'utilisateur porte sur ce traitement precis; il ne change pas le reglage
    general de l'instance.
    """
    from ..core.common import RunContext, read_csv
    from ..modules import docai

    try:
        run = RunContext(instance, "docai-ocr")
    except Exception:
        run = None
    try:
        docai.run_ocr(instance, run, doc_id=doc_id, mode="local_basic", engine=MOTEUR)
    except Exception:
        return False
    try:
        _, rows = read_csv(instance.register("documents"))
    except Exception:
        return False
    for row in rows:
        if row.get("doc_id") == doc_id:
            return row.get("status_ocr") == "OCR_DONE"
    return False


def _lancer_ocr_en_fond(instance: Any, doc_id: str) -> None:
    """Demarre la reconnaissance sans faire attendre la requete.

    Le fil est `daemon`: si le serveur s'arrete pendant un traitement, il ne le
    retient pas. Le document reste alors marque `OCR_REQUIRED` avec un accord
    enregistre, et la page le montre comme non abouti - ce qui est exact.
    """
    threading.Thread(
        target=executer_ocr, args=(instance, doc_id), name=f"ocr-{doc_id}", daemon=True
    ).start()
