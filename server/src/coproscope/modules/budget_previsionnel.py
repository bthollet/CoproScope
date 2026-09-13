"""Controles reglementaires du budget previsionnel d'une copropriete.

Grille `docs/grille_budget_previsionnel_2026-09-04.md`, lot `RM-2026-0082`.
Seize controles, sept sur le contenu du budget (famille B), neuf sur la
procedure du vote (famille P). Chacun cite l'article qui le fonde, dans la
version lue sur Legifrance le 2026-09-03.

Ce module ne lit aucun PDF et n'extrait rien. Il consomme un `Dossier` deja
structure: c'est volontaire, et c'est le contrat d'entree que l'extracteur
d'etat des depenses et d'annexes (`RM-2026-0074`) devra remplir. Tant qu'il
manque, les controles rendent `INAPPLICABLE` en nommant le champ absent, et
c'est ce comptage qui dit ce que l'outil devra reclamer au syndic.
"""

from __future__ import annotations

from ._budget_previsionnel_controles import CONTROLES
from ._budget_previsionnel_modele import (
    A_VERIFIER_HUMAIN,
    CONFORME,
    ECART,
    INAPPLICABLE,
    STATUTS,
    Annexes,
    BudgetPrevisionnel,
    Constat,
    Convocation,
    Copropriete,
    Dossier,
    LigneBudget,
    Vote,
)
from ._budget_previsionnel_nomenclature import COMPTES, COMPTES_SUPPRIMES, normaliser, rattacher
from ._budget_previsionnel_sources import SOURCES, Source, source

__all__ = [
    "A_VERIFIER_HUMAIN",
    "CONFORME",
    "COMPTES",
    "COMPTES_SUPPRIMES",
    "CONTROLES",
    "ECART",
    "INAPPLICABLE",
    "STATUTS",
    "SOURCES",
    "Annexes",
    "BudgetPrevisionnel",
    "Constat",
    "Convocation",
    "Copropriete",
    "Dossier",
    "LigneBudget",
    "Source",
    "Vote",
    "evaluer",
    "entrees_manquantes",
    "normaliser",
    "rattacher",
    "repartition",
    "source",
]


def evaluer(dossier: Dossier) -> tuple[Constat, ...]:
    """Passe les seize controles et rend leurs constats, dans l'ordre de la grille."""
    return tuple(controle(dossier) for controle in CONTROLES)


def repartition(constats: tuple[Constat, ...]) -> dict[str, int]:
    """Combien de constats par statut. Les quatre statuts sont toujours presents.

    Un statut absent du resultat se lirait comme un zero non mesure; ici, zero
    veut dire zero.
    """
    compte = {statut: 0 for statut in STATUTS}
    for constat in constats:
        compte[constat.statut] += 1
    return compte


def entrees_manquantes(constats: tuple[Constat, ...]) -> dict[str, tuple[str, ...]]:
    """Pour chaque entree absente, les controles qu'elle bloque.

    C'est la sortie utile du lot: elle se lit comme une liste de pieces a
    demander, classee par ce qu'elle debloque.
    """
    index: dict[str, list[str]] = {}
    for constat in constats:
        for entree in constat.entrees_manquantes:
            index.setdefault(entree, []).append(constat.controle)
    return {entree: tuple(sorted(set(controles))) for entree, controles in sorted(index.items())}
