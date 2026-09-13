"""Assemblage des predicats de la grille budget previsionnel.

Un controle = une fonction qui lit un `Dossier` et rend un `Constat`. Trois
regles tenues dans les deux familles:

1. une entree absente rend `INAPPLICABLE` en nommant ce qui manque, jamais
   `CONFORME`;
2. un `ECART` dit ce qui est constate, pas ce qu'il faut en conclure;
3. `ne_prouve_pas` est obligatoire. Un controle qui pretend prouver plus qu'il
   ne peut est la faute la plus couteuse ici.

L'ordre de `CONTROLES` est celui de la grille et fait partie du contrat: les
constats se lisent dans cet ordre.
"""

from __future__ import annotations

from ._budget_previsionnel_controles_b import (
    b1_perimetre_article_44,
    b2_nomenclature,
    b3_compte_supprime,
    b4_egalite_annexes,
    b5_plancher_fonds_travaux,
    b6_avance_reserve,
    b7_suspension_cotisation,
)
from ._budget_previsionnel_controles_p import (
    p1_vote_avant_exercice,
    p2_provisions_transitoires,
    p3_duree_exercice,
    p4_delai_six_mois,
    p5_comparatif_dernier_budget,
    p6_presentation_annexe2,
    p7_majorite,
    p8_concertation,
    p9_archivage,
)

CONTROLES = (
    b1_perimetre_article_44,
    b2_nomenclature,
    b3_compte_supprime,
    b4_egalite_annexes,
    b5_plancher_fonds_travaux,
    b6_avance_reserve,
    b7_suspension_cotisation,
    p1_vote_avant_exercice,
    p2_provisions_transitoires,
    p3_duree_exercice,
    p4_delai_six_mois,
    p5_comparatif_dernier_budget,
    p6_presentation_annexe2,
    p7_majorite,
    p8_concertation,
    p9_archivage,
)

__all__ = ["CONTROLES"] + [controle.__name__ for controle in CONTROLES]
