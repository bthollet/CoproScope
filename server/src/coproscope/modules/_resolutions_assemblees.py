"""Les copies concurrentes d'une meme assemblee: les NOMMER, sans en elire une.

**Le fait mesure (C054).** Dans le coffre de l'instance a deux exercices, la
table `resolutions` portait TROIS copies de l'assemblee du 03/07/2024, 55
lignes chacune, numerotees 1 a 55, avec trois comptages d'issues differents.
Deux d'entre elles avaient perdu leur date, donc un `ag_id` derive du document.
Rien ne les opposait: les cles different par le `doc_id`, les trois coexistent,
et l'ecran de controle affichait trois fois la resolution n° 7 - avec deux
issues contradictoires - sans jamais dire qu'il s'agissait peut-etre du meme
proces-verbal relu.

**Ce que ce module refuse de faire, et pourquoi.** Il n'elit pas la copie qui
fait foi. Ce serait poser une regle de preuve, et la mesure dit justement que
le choix par defaut serait le mauvais: la copie datee annonce 38 adoptees la ou
le proces-verbal en porte 39. `acte_id_resolution` pose la meme borne dans sa
propre documentation - deux assemblees de meme cardinalite ne sont pas reputees
identiques, ce serait conclure sur une ressemblance.

**Ce qu'il fait a la place.** Il enonce un fait verifiable et rien de plus:
*ce rang de resolution est occupe par plusieurs actes, et au moins l'un d'eux
vient d'une assemblee dont la date n'a pas ete lue - donc rien ici ne permet de
dire s'il s'agit de la meme assemblee ou d'une autre.* C'est une incertitude
nommee, pas une identite affirmee.

**L'axe de generalisation.** Ce qui varie, c'est la raison pour laquelle un
meme proces-verbal entre deux fois: un second scan, un nouvel OCR, un fichier
renomme. Ce qui reste invariant, c'est qu'une assemblee dont la date n'a pas
ete lue est **indiscernable** de toute autre assemblee qui porte les memes
rangs. La condition retenue porte donc sur cette indiscernabilite, jamais sur
la ressemblance des contenus. Hors des valeurs observees - deux assemblees
toutes deux datees, distinctes, et portant chacune un n° 7 - la regle ne se
declenche pas: leurs dates les distinguent, et c'est vrai.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

__all__ = [
    "NATURE_RESOLUTION",
    "assemblees_sans_date_lue",
    "copies_concurrentes",
    "date_lue",
]

NATURE_RESOLUTION = "RESOLUTION_AG"

#: Un `ag_id` qui porte une date lue s'ecrit `AG-AAAA-MM-JJ`. Toute autre forme
#: est un repli sur l'identifiant du document, c'est-a-dire une assemblee que
#: rien ne situe dans le temps. La comparaison porte sur la FORME de
#: l'identifiant, jamais sur sa longueur: `AG-2024-7-3` doit echouer, et une
#: mesure de longueur l'accepterait.
AG_DATE_RE = re.compile(r"^AG-\d{4}-\d{2}-\d{2}$")


def date_lue(ag_id: str) -> bool:
    """Vrai quand l'identifiant d'assemblee porte une date, pas un document."""
    return bool(AG_DATE_RE.match(str(ag_id or "")))


def assemblees_sans_date_lue(actes: Iterable[dict[str, Any]]) -> list[str]:
    """Les assemblees identifiees par un document faute de date lue.

    C'est le repli que `acte_id_resolution` admet mais marque: l'identifiant
    redevient dependant du fichier, donc le meme proces-verbal relu autrement
    fabrique une assemblee de plus.
    """
    return sorted(
        {
            str(a.get("ag_id") or "")
            for a in actes
            if a.get("ag_id") and not date_lue(str(a["ag_id"]))
        }
    )


def _rang(acte: dict[str, Any]) -> str:
    """Le rang de la resolution DANS son assemblee: son numero et son degre.

    C'est la seule coordonnee qu'un proces-verbal relu deux fois conserve a
    l'identique. Le texte, lui, change au moindre OCR, et l'identifiant d'acte
    change avec le document des que la date manque.
    """
    numero = str(acte.get("numero") or "").strip()
    sous = str(acte.get("sous_numero") or "").strip()
    if not numero:
        return ""
    return f"{numero}.{sous}" if sous else numero


def copies_concurrentes(
    actes: Iterable[dict[str, Any]],
) -> dict[str, list[dict[str, str]]]:
    """Par acte, les autres actes qui occupent le meme rang de resolution.

    Rend une entree SEULEMENT pour les rangs ou la question se pose vraiment,
    c'est-a-dire quand les deux conditions suivantes tiennent ensemble:

    1. plusieurs assemblees distinctes occupent ce rang;
    2. au moins l'une d'elles n'a pas de date lue.

    La seconde condition est ce qui empeche le faux positif evident: une
    copropriete qui tient une assemblee en 2024 et une autre en 2026 a deux
    resolutions n° 7, et elles n'ont rien a voir. Leurs dates les distinguent,
    donc rien n'est signale. Des qu'une date manque, plus rien ne les
    distingue - et c'est cela, et rien d'autre, que l'ecran annonce.

    Une meme assemblee lue depuis deux documents n'est pas signalee ici: elle
    produit une collision de cle, deja comptee et nommee a l'ecriture.
    """
    par_rang: dict[str, list[dict[str, Any]]] = {}
    for acte in actes:
        if str(acte.get("nature") or "") != NATURE_RESOLUTION:
            continue
        rang = _rang(acte)
        if not rang:
            continue
        par_rang.setdefault(rang, []).append(acte)

    concurrents: dict[str, list[dict[str, str]]] = {}
    for membres in par_rang.values():
        assemblees = {str(m.get("ag_id") or "") for m in membres}
        if len(assemblees) < 2:
            continue
        if all(date_lue(ag) for ag in assemblees):
            continue
        for membre in membres:
            autres = [
                {
                    "acte_id": str(m.get("acte_id") or ""),
                    "doc_id": str(m.get("doc_id") or ""),
                    "ag_id": str(m.get("ag_id") or ""),
                    "resultat": str(m.get("resultat") or ""),
                    "date_effet": str(m.get("date_effet") or ""),
                    "date_lue": date_lue(str(m.get("ag_id") or "")),
                }
                for m in membres
                if m.get("acte_id") != membre.get("acte_id")
            ]
            if autres:
                concurrents[str(membre.get("acte_id") or "")] = autres
    return concurrents
