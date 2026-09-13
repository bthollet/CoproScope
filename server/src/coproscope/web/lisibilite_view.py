"""Les documents que CoproScope n'a pas pu lire, et la demande d'accord.

Trois regles d'affichage:

- **on demande, on ne fait pas.** La reconnaissance de texte prend du temps
  machine et travaille sur les documents de l'utilisateur. Elle ne se declenche
  jamais seule;
- **on explique avant de demander.** Un coproprietaire n'a pas a savoir ce
  qu'est l'OCR pour repondre. Le message dit ce qui ne va pas, ou le traitement
  a lieu, et combien de temps il prend;
- **une reponse donnee ne se redemande pas.** Accord comme refus sont gardes,
  et survivent a une nouvelle extraction.

Rien ici ne compte un document comme lu parce que son fichier texte n'est pas
vide: c'est precisement le defaut que `lisibilite` ferme.
"""

from __future__ import annotations

from typing import Any

from ..modules.lisibilite import (
    ACCEPTE,
    ILLISIBLE,
    REFUSE,
    decisions,
    demande_utilisateur,
    texte_utile,
    verdict,
)

RIEN_A_SIGNALER = "rien_a_signaler"
A_DECIDER = "a_decider"


def _nom(row: dict[str, str]) -> str:
    """Le libelle d'une piece a lire, derive de ce qu'elle est.

    **Corrige une fuite mesuree le 2026-09-08** (`RM-2026-0127`). Cette
    fonction rendait le nom de base de `original_path`, et `/documents/non-lus`
    l'affichait. Couper le dossier protege le poste, pas la personne: le nom de
    base est justement la partie ecrite par un tiers, qui peut porter un
    patronyme.

    `/documents/non-lus` n'etait dans la liste d'aucun des six ecrans que
    gardait `test_ui_nom_de_fichier_ne_fuit_pas` avant sa refonte: c'est
    l'enumeration qui l'a laissee passer, pas l'inattention.
    """

    from ..core.libelle_public import libelle_public_document

    return libelle_public_document(row)


def _texte(instance, row: dict[str, str]) -> str:
    chemin = row.get("text_path")
    if not chemin:
        return ""
    fichier = instance.root("workspace") / chemin
    if not fichier.exists():
        return ""
    return fichier.read_text(encoding="utf-8", errors="ignore")


def _duree_totale(pages: int) -> str:
    from ..modules.lisibilite import SECONDES_PAR_PAGE

    minutes = round(max(pages, 1) * SECONDES_PAR_PAGE / 60)
    if minutes < 1:
        return "moins d'une minute"
    return f"environ {minutes} minute{'s' if minutes > 1 else ''}"


def build_lisibilite_view(instance) -> dict[str, Any]:
    """Documents illisibles en attente d'une reponse de l'utilisateur."""
    from ..core.common import read_csv

    try:
        _, rows = read_csv(instance.register("documents"))
    except Exception:
        rows = []

    deja = decisions(instance)
    attente: list[dict[str, Any]] = []
    en_cours: list[dict[str, Any]] = []
    refuses = 0
    reconnus = 0
    pages_totales = 0

    for row in rows:
        doc_id = row.get("doc_id") or ""
        if row.get("status_ocr") == "OCR_DONE":
            reconnus += 1
            continue
        pages = int(row.get("page_count") or 0)
        brut = _texte(instance, row)
        if verdict(brut, pages) != ILLISIBLE:
            continue
        reponse = deja.get(doc_id)
        if reponse == REFUSE:
            refuses += 1
            continue
        if reponse == ACCEPTE:
            # Accord donne mais document toujours illisible: la reconnaissance
            # tourne encore, ou elle a echoue. Les deux se montrent - masquer
            # un echec derriere un accord serait le pire des deux mondes.
            en_cours.append({"doc_id": doc_id, "nom": _nom(row), "pages": pages})
            continue
        message = demande_utilisateur(_nom(row), pages, brut)
        message["doc_id"] = doc_id
        message["type"] = row.get("document_type") or ""
        attente.append(message)
        pages_totales += pages

    attente.sort(key=lambda m: (-int(m["pages"] or 0), str(m["titre"])))
    return {
        "etat": A_DECIDER if (attente or en_cours) else RIEN_A_SIGNALER,
        "documents": attente,
        "nombre": len(attente),
        "pages_totales": pages_totales,
        "duree_totale": _duree_totale(pages_totales),
        "refuses": refuses,
        "deja_reconnus": reconnus,
        "en_cours": en_cours,
        "resume": (
            f"{len(attente)} document n'a pas pu être lu"
            if len(attente) == 1
            else f"{len(attente)} documents n'ont pas pu être lus"
        )
        if attente
        else "Tous les documents déposés ont pu être lus.",
        "pourquoi_ca_compte": (
            "Un document que CoproScope ne peut pas lire n'apparaît dans aucun "
            "contrôle : ni dans les résolutions d'assemblée, ni dans le "
            "rapprochement des dépenses. Il est présent dans le coffre, mais "
            "invisible pour les vérifications."
        ),
    }
