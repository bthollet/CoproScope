# -*- coding: utf-8 -*-
"""Parcourir l'interface en suivant ses propres liens, depuis `/`.

`RM-2026-0183`. La recette du 2026-09-13 a trouve un lien `Detail piece/preuve`
qui menait a `/pieces/` sans identifiant: 404, sur une page que tous les tests
rendaient en 200. Aucune garde ne suivait les liens - chacune verifiait la page
qu'elle nommait.

**L'AXE.** Ce qui varie: l'ensemble des pages, des routes et des liens, qui
bouge a chaque lot - des pages ont ete retirees le meme jour. Ce qui reste
INVARIANT: **un lien affiche a un utilisateur mene quelque part.** La portee
se derive donc de ce que l'application REND, en partant de `/`, et jamais d'une
liste de routes ecrite une fois: une page retiree dont un lien survit est
trouvee le jour du retrait, et une page ajoutee est parcourue le jour ou un
lien y mene.

**HORS PORTEE, DECLARE.** Les cibles de formulaires (`action=`), les liens
poses par script, et les pages qu'aucun lien n'atteint: une route orpheline
n'est pas un lien mort. Un plafond de pages borne le parcours; s'il est atteint,
le rapport le DIT au lieu de conclure sur ce qu'il a vu.

Ce module ne depend d'aucun client HTTP: il recoit une fonction `obtenir(chemin)`
qui rend `(statut, type_de_contenu, texte)`. Le test l'alimente par le client de
test; l'export statique de la demo l'alimente de la meme facon.
"""
from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from html import unescape
from typing import Callable
from urllib.parse import parse_qsl, urlencode, urlsplit

#: Toute valeur `href`, entre guillemets doubles ou simples.
HREF = re.compile(r"""href\s*=\s*(["'])(.*?)\1""", re.IGNORECASE | re.DOTALL)

#: Hotes que le client de test donne aux URL absolues qu'il fabrique.
HOTES_INTERNES = frozenset({"testserver", "127.0.0.1", "localhost"})

Obtenir = Callable[[str], "tuple[int, str, str]"]


@dataclass
class Parcours:
    pages: dict[str, int] = field(default_factory=dict)
    #: (lien, page qui le porte, statut obtenu)
    liens_morts: list[tuple[str, str, int]] = field(default_factory=list)
    plafond_atteint: bool = False
    #: lien normalise -> premiere page qui le porte
    origines: dict[str, str] = field(default_factory=dict)


def lien_interne(href: str) -> str | None:
    """Le chemin interne vise par `href`, normalise, ou `None` s'il sort de l'interface.

    Le jeton local est retire (il n'identifie pas une page), l'ancre aussi; les
    autres parametres restent, parce qu'une page filtree est une autre page.
    """
    valeur = unescape(href).strip()
    if not valeur or valeur.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    morceaux = urlsplit(valeur)
    if morceaux.scheme or morceaux.netloc:
        if morceaux.scheme not in {"http", "https"} or morceaux.hostname not in HOTES_INTERNES:
            return None
    elif not valeur.startswith("/") or valeur.startswith("//"):
        return None
    chemin = morceaux.path or "/"
    if chemin.startswith("/static/"):
        return None
    requete = [(cle, val) for cle, val in parse_qsl(morceaux.query, keep_blank_values=True) if cle != "token"]
    return chemin + ("?" + urlencode(requete) if requete else "")


def liens_de(texte: str) -> list[str]:
    vus: list[str] = []
    for _, href in HREF.findall(texte):
        interne = lien_interne(href)
        if interne is not None and interne not in vus:
            vus.append(interne)
    return vus


def parcourir(obtenir: Obtenir, depart: str = "/", plafond: int = 3000) -> Parcours:
    """Suit chaque lien interne rendu, en largeur, a partir de `depart`."""
    resultat = Parcours()
    file: deque[tuple[str, str]] = deque([(depart, "")])
    while file:
        chemin, origine = file.popleft()
        if chemin in resultat.pages:
            continue
        if len(resultat.pages) >= plafond:
            resultat.plafond_atteint = True
            break
        statut, type_contenu, texte = obtenir(chemin)
        resultat.pages[chemin] = statut
        resultat.origines.setdefault(chemin, origine)
        if statut >= 400:
            resultat.liens_morts.append((chemin, origine, statut))
            continue
        if "html" not in (type_contenu or "").lower():
            continue
        for lien in liens_de(texte):
            if lien not in resultat.pages:
                file.append((lien, chemin))
    return resultat
