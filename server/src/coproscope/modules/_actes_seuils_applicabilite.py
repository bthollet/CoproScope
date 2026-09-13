# -*- coding: utf-8 -*-
"""Cette norme s'applique-t-elle a cet acte ? La question posee AVANT de comparer.

**Le refus d'integration de `RM-2026-0144`, et il portait exactement ici.** Le
lot avait separe deux normes que le modele ecrasait en une seule - le seuil de
consultation du conseil syndical et le seuil de mise en concurrence - et il
l'avait fait proprement, jusqu'aux relations. Le sceptique a refuse sur un
motif d'une ligne: **la separation s'arrete aux relations, elle n'atteint pas le
CONTROLE qui decide de leur applicabilite.** Le lot lui-meme l'ecrivait dans sa
propre docstring: *« Ce lot ne s'en sert pas encore pour retirer un controle. »*

**Mesure du 2026-09-11.** Le champ `exclut` de `NormeSeuil` porte le texte de
l'exclusion depuis sa creation. Grep sur tout `server/src` et `server/tests`:
**il n'est lu nulle part.** Declare, documente, transporte, jamais consulte.

**Ce que l'alinea distingue.** L'article 21 alinea 2 de la loi du 10 juillet
1965 arrete deux montants a la meme majorite. Le premier declenche la
consultation prealable du conseil syndical et **ne connait aucune reserve** -
le meme article ajoute au contraire que le conseil peut se prononcer sur tout
projet de contrat de syndic. Le second declenche la mise en concurrence et vise
les marches et contrats **autres que celui de syndic**. Un acte qui porte le
contrat de syndic n'est donc pas *sous le seuil* de mise en concurrence: il est
**hors de son champ**, ce qui n'est pas la meme chose et ne se dit pas pareil.

**POURQUOI CE CONTROLE NE RETIRE AUCUN LIEN AUJOURD'HUI, et pourquoi il faut
l'ecrire quand meme.** Mesure sur une instance VIDE reabsorbant 858 pieces
sources, 550 actes: **12 relevent du contrat de syndic** et ils sont classes
`ORDINAIRE` (7), `DESIGNATION_SYNDIC` (2), `SEUIL` (2), `DESIGNATION_ORGANE`
(1). **Aucun n'est un `ENGAGEMENT_DEPENSE`** - et sur les **282 engagements de
depense** du corpus, **zero** releve du contrat de syndic. Or `liens_seuil` ne
rattache QUE des engagements de depense. L'exclusion ne mord donc sur aucune
des 276 lignes de mise en concurrence.

**Mais elle est respectee par ACCIDENT, et c'est le vrai constat.** Ce qui
protege aujourd'hui n'est pas la regle de l'alinea: c'est qu'une AUTRE
classification - la typologie de portee - range le contrat de syndic ailleurs.
Rien dans le code ne dit que la mise en concurrence l'exclut. Le jour ou un
syndic redige un renouvellement de contrat d'une facon qui le fait classer
`ENGAGEMENT_DEPENSE`, l'exclusion tombe **en silence**, et le produit affirme
une obligation de mise en concurrence que la loi ne prevoit pas. C'est le meme
choix que le cas d'egalite de `franchissement`: l'ecrire tant qu'il ne coute
rien, plutot que le jour ou il decide d'une obligation.

**L'AXE, et il decide de la forme du code.** Ce qui VARIE: la maniere dont une
resolution nomme le contrat de syndic, le cabinet, la langue, la redaction de
l'ordre du jour. Ce qui reste INVARIANT: **une exclusion legale porte sur la
NATURE de l'acte, pas sur les mots qui la disent.** Ce controle ne lit donc
aucun intitule et ne cherche aucun mot: il compare la **portee** - le
vocabulaire que le modele emploie deja pour dire ce qu'un acte est - au champ
d'exclusion de la norme. Un acte dont la portee est inconnue ne tombe ni dans
`APPLICABLE` ni dans `HORS_CHAMP`.

**Hors des valeurs observees.** Une portee que le vocabulaire ne connait pas,
une portee vide, une norme sans exclusion: les trois se rangent sans cas
particulier. Une norme sans exclusion rend `APPLICABLE` pour toute portee, y
compris inconnue - c'est le cas de la consultation du conseil syndical, et c'est
juste: l'alinea ne lui donne aucune reserve, donc rien a verifier.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._actes_vocabulaire import (
    PORTEE_DESIGNATION_SYNDIC,
    PORTEES,
    REL_SEUIL_CONCURRENCE,
)

if TYPE_CHECKING:  # pragma: no cover
    from ._actes_seuils_normes import NormeSeuil

__all__ = [
    "APPLICABLE",
    "HORS_CHAMP",
    "PORTEE_INCONNUE",
    "PORTEES_EXCLUES",
    "portees_exclues",
    "applicabilite",
    "phrase_d_applicabilite",
]

#: La norme s'applique a cet acte: le franchissement peut se calculer.
APPLICABLE = "APPLICABLE"

#: L'acte est hors du champ de la norme. **Ce n'est pas `NON_FRANCHI`.** Un acte
#: hors champ ne franchit rien, y compris quand son montant depasse le seuil:
#: la question ne se pose pas pour lui.
HORS_CHAMP = "HORS_CHAMP"

#: On ne sait pas ce qu'est cet acte, donc on ne sait pas si la norme le vise.
#: **Le troisieme etat, et il n'est jamais un feu vert**: ni une application ni
#: une exclusion, l'aveu qu'on ne peut pas trancher.
PORTEE_INCONNUE = "PORTEE_INCONNUE"

#: Ce que l'alinea sort du champ de la mise en concurrence, dit dans le
#: vocabulaire du modele. `DESIGNATION_SYNDIC` est la portee sous laquelle ce
#: produit range ce qui designe le syndic et arrete son contrat.
#:
#: **Une portee, pas une liste de mots.** Ecrire ici `contrat de syndic`,
#: `mandat du syndic`, `honoraires de gestion` reviendrait a enumerer les
#: tournures d'un cabinet - une modalite - et a casser au troisieme syndic.
PORTEES_EXCLUES: dict[str, frozenset[str]] = {
    REL_SEUIL_CONCURRENCE: frozenset({PORTEE_DESIGNATION_SYNDIC}),
}


def portees_exclues(relation: str) -> frozenset[str]:
    """Les portees que CETTE norme excepte, en plus des retraits de controle.

    **C'est la granularite qui manquait, et le refus portait exactement la.**
    `HORS_CONTROLE` retire un CONTROLE a une portee. Les trois relations de
    seuil partagent `CTRL_SEUIL`, donc son retrait vaut pour les trois d'un
    seul coup - c'est ecrit dans `_actes_vues_matrice.cellule`: *sans ce
    parametre, chaque relation aurait du etre son propre controle*.

    L'exclusion de l'alinea, elle, ne vaut que pour UNE des trois. Elle se
    declare donc ici, par relation, et le gate de vue compose les deux.
    """
    return PORTEES_EXCLUES.get(relation or "", frozenset())


def applicabilite(norme: "NormeSeuil", portee: str) -> tuple[str, str]:
    """L'etat d'applicabilite de cette norme a un acte de cette portee.

    Rend le couple `(etat, motif)`. Le motif est vide quand il n'y a rien a
    dire, et porte le texte de l'exclusion quand elle joue: *hors champ* sans
    raison laisse le lecteur devant un refus muet, et il ne saurait pas quoi
    contester.
    """
    nette = (portee or "").strip()
    exclues = portees_exclues(getattr(norme, "relation", "") or "")
    if not exclues:
        # Aucune reserve dans l'alinea: rien a verifier, meme portee inconnue.
        # C'est le cas de la consultation du conseil syndical.
        return APPLICABLE, ""
    if not nette or nette not in PORTEES:
        return PORTEE_INCONNUE, "la nature de la décision n'est pas établie"
    if nette in exclues:
        return HORS_CHAMP, getattr(norme, "exclut", "") or ""
    return APPLICABLE, ""


def phrase_d_applicabilite(etat: str, motif: str) -> str:
    """Ce que l'ecran dit d'un acte, une fois l'applicabilite tranchee."""
    if etat == HORS_CHAMP:
        return (
            "Cette obligation ne vise pas cette décision : l'alinéa en excepte "
            + (motif or "ce type de décision")
            + "."
        )
    if etat == PORTEE_INCONNUE:
        return (
            "La nature de cette décision n'est pas établie : on ne peut pas "
            "dire si cette obligation la vise."
        )
    return ""
