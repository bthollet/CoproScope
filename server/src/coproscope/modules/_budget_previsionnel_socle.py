"""Socle commun des predicats du budget previsionnel.

Fabrique du constat et arithmetique de dates. Les deux familles de controles s'y
appuient pour que la forme d'un constat - statut, sources citees, entrees
manquantes, limite declaree - soit la meme partout.
"""

from __future__ import annotations

from ._budget_previsionnel_modele import Constat
from ._budget_previsionnel_sources import citations, legiartis

_TOLERANCE = 0.005


def _constat(
    controle: str,
    enonce: str,
    statut: str,
    message: str,
    cles: tuple[str, ...],
    ne_prouve_pas: str,
    entrees_manquantes: tuple[str, ...] = (),
) -> Constat:
    return Constat(
        controle=controle,
        statut=statut,
        enonce=enonce,
        message=message,
        sources=citations(cles),
        legiartis=legiartis(cles),
        entrees_manquantes=entrees_manquantes,
        ne_prouve_pas=ne_prouve_pas,
    )


def _mois_ecoules(depart, arrivee) -> int:
    return (arrivee.year - depart.year) * 12 + (arrivee.month - depart.month)
