# -*- coding: utf-8 -*-
"""Des ecrans DEBRANCHES: le code reste, la route n'est pas servie.

`RM-2026-0183`, recette de Brice du 2026-09-13: *debrancher, garder pour plus
tard*. Un ecran retire se supprime; un ecran debranche garde son code et ses
tests, parce qu'il reviendra - mais le produit ne le propose plus, ni dans le
menu ni a son adresse.

**UN SEUL INTERRUPTEUR, et c'est ce qui le rend verifiable.** `create_app`
recoit `rebrancher`, un ensemble de cles de ce dictionnaire; par defaut il est
vide. Les tests fonctionnels d'un ecran debranche le rebranchent explicitement,
si bien que leur code reste eprouve pendant que le produit ne le sert pas.

Chaque cle nomme l'item du gouvernail qui porte l'ecran. Une cle inconnue est
refusee: un nom mal ecrit ne doit pas rebrancher rien en silence.
`server/tests/test_un_ecran_debranche_ne_se_sert_pas.py` verifie, par les
routes REELLEMENT enregistrees, que chaque cle ajoute des routes et qu'aucune
d'elles n'est servie par defaut.
"""
from __future__ import annotations

import re

from typing import Iterable

#: cle -> item du gouvernail qui porte l'ecran
DEBRANCHES: dict[str, str] = {
    # `/documents/ajouter`, l'envoi de fichiers et les ecritures d'accueil
    "ajouter_document": "RM-2026-0003",
    # `/messages/entrants`
    "messages_entrants": "RM-2026-0031",
    # `/courriers/preuves`
    "courriers_preuves": "RM-2026-0028",
    # `/coffre/drive`: synchronisation mise de cote le 2026-09-12; son seul
    # point d'entree etait `Coffre et partage`, retire le 2026-09-13
    "synchro_drive": "RM-2026-0014",
}


def rebranchements(rebrancher: Iterable[str] = ()) -> frozenset[str]:
    demandes = frozenset(rebrancher)
    inconnus = sorted(demandes - set(DEBRANCHES))
    if inconnus:
        raise ValueError("ecrans a rebrancher inconnus: %s" % inconnus)
    return demandes


#: Chemins des ecrans RETIRES le 2026-09-13 (`RM-2026-0183`). Ce n'est pas une
#: liste d'observations, c'est la table de decision de Brice: elle ne se derive
#: de rien d'autre que de la recette.
RETIRES: tuple[str, ...] = (
    "/actions",
    "/suggestions",
    "/pilotage",
    "/depot",
    "/gouvernance",
    "/confidentialite",
    "/coffre/partage",
)

#: Chemins servis par chaque ecran debranche, quand il n'est pas rebranche.
CHEMINS_DEBRANCHES: dict[str, tuple[str, ...]] = {
    "ajouter_document": ("/documents/ajouter",),
    "messages_entrants": ("/messages/entrants",),
    "courriers_preuves": ("/courriers/preuves",),
    "synchro_drive": ("/coffre/drive",),
}


def chemins_non_servis(rebranches: frozenset[str]) -> tuple[str, ...]:
    debranches = [c for cle, chemins in CHEMINS_DEBRANCHES.items() if cle not in rebranches for c in chemins]
    return RETIRES + tuple(debranches)


def sous(chemin: str, prefixes: Iterable[str]) -> str | None:
    """Le prefixe qui couvre `chemin`, a frontiere de segment, ou `None`."""
    for prefixe in prefixes:
        if chemin == prefixe or chemin.startswith(prefixe + "/"):
            return prefixe
    return None


_ANCRE = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.S | re.I)
_HREF = re.compile(r"""\bhref\s*=\s*(["'])(.*?)\1""", re.S | re.I)


def neutraliser_liens(html: str, prefixes: tuple[str, ...]) -> tuple[str, int]:
    """Rend en TEXTE tout lien qui mene a un chemin non servi.

    **Ce que cela repare et ce que cela laisse, dit ensemble.** Un utilisateur ne
    clique plus vers une page 404: c'est le defaut qu'il voit. Mais le gabarit
    qui proposait l'action existe toujours, et son libelle reste affiche comme
    texte. Ce residu est COMPTE et nomme en dette par
    `server/tests/test_aucun_lien_interne_ne_mene_nulle_part.py`, qui parcourt
    l'interface aussi SANS cette neutralisation: une page reprise fait baisser la
    dette, un nouveau lien vers un ecran retire la fait mordre.
    """
    from ._parcours_liens import lien_interne

    compte = 0

    def remplacer(m):
        nonlocal compte
        href = _HREF.search(m.group(1))
        if not href:
            return m.group(0)
        interne = lien_interne(href.group(2))
        if interne is None or sous(interne.split("?", 1)[0], prefixes) is None:
            return m.group(0)
        compte += 1
        return '<span class="cs-lien-retire">%s</span>' % m.group(2)

    return _ANCRE.sub(remplacer, html), compte
