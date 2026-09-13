# -*- coding: utf-8 -*-
"""Le montant de l'acte franchit-il le seuil qui lui est rattache ?

**C'est le trou T9**, laisse ouvert depuis le blueprint et ecrit a l'ecran dans
une phrase ajoutee a chaque cellule de seuil: *le franchissement lui-meme n'est
pas calcule; la comparaison du montant au seuil n'existe pas encore dans le
modele*.

**Cette phrase est devenue fausse le 2026-09-10, et de deux facons.** La
comparaison EXISTE desormais dans le modele - la matrice porte le montant arrete
par la deliberation retenue a cote de celui de l'acte. Et surtout, ce qui
manquait n'etait pas le calcul: **c'etaient les montants**. Mesure sur instance
VIDE reabsorbant 858 pieces sources, 550 liens de seuil: **124 comparables, et
426 dont le montant de l'ACTE n'est pas lisible.** Dire *le modele ne compare
pas* laissait croire a un manque de code la ou il y a un manque de donnee.

**TROIS ETATS, et le troisieme n'est jamais un feu vert.** C'est la forme que ce
depot donne a tout controle: 0 rien trouve, 1 quelque chose trouve, 2 **le
controle n'a pas pu etre fait**. Un montant illisible ne se lit JAMAIS comme
*sous le seuil* - ce serait affirmer qu'aucune obligation ne s'applique, sur
une ligne ou l'on ne sait rien.

**L'axe.** Ce qui varie: l'ecriture du montant, sa presence, son unite, la norme
concernee. Ce qui reste invariant: **comparer demande deux nombres, et il faut
les deux.** La fonction ne rend donc `FRANCHI` ou `NON_FRANCHI` que lorsque les
deux sont lus; tout le reste - absent d'un cote, illisible de l'autre, les deux
- tombe dans le meme etat declare, avec le motif qui dit lequel manque.

**Le cas limite est tranche par le droit, pas par une convention.** L'article 21
alinea 2 soumet les marches *dont le montant EXCEDE* le seuil. Un montant EGAL
au seuil ne l'excede pas: il n'est donc pas franchi. Mesure du 2026-09-10: zero
egalite sur les 124 comparables du corpus, donc **aucune ligne ne depend
aujourd'hui de ce choix** - raison de plus pour l'ecrire maintenant, tant qu'il
ne coute rien, plutot que le jour ou il decidera d'une obligation.
"""

from __future__ import annotations

from decimal import Decimal

from ..modules._montants import MontantIllisible, montant_decimal

__all__ = [
    "FRANCHI",
    "NON_COMPARABLE",
    "NON_FRANCHI",
    "franchissement",
    "phrase_de_franchissement",
]

FRANCHI = "FRANCHI"
NON_FRANCHI = "NON_FRANCHI"
NON_COMPARABLE = "NON_COMPARABLE"

#: Ce qui manque, quand la comparaison n'a pas pu se faire. Le motif est rendu
#: a cote de l'etat: *non comparable* sans raison laisse le lecteur devant un
#: refus muet, et il ne saurait pas quoi reclamer.
MANQUE_ACTE = "montant de la decision"
MANQUE_SEUIL = "montant du seuil"
MANQUE_LES_DEUX = "les deux montants"


def _lu(valeur: object) -> Decimal | None:
    """Le montant, ou `None` - qu'il soit absent OU illisible.

    Les deux causes se confondent volontairement ICI: pour la comparaison, un
    montant qu'on ne peut pas lire et un montant qui n'existe pas ont
    exactement la meme consequence. La distinction entre les deux se fait en
    amont, la ou l'on decide quoi reclamer au syndic.
    """
    try:
        return montant_decimal(valeur)
    except MontantIllisible:
        return None


def franchissement(montant_acte: object, montant_seuil: object) -> tuple[str, str]:
    """L'etat du franchissement, et ce qui manque quand il n'est pas calculable.

    Rend `(etat, motif)`. Le motif est vide quand la comparaison a eu lieu.
    """
    acte, seuil = _lu(montant_acte), _lu(montant_seuil)
    if acte is None and seuil is None:
        return NON_COMPARABLE, MANQUE_LES_DEUX
    if acte is None:
        return NON_COMPARABLE, MANQUE_ACTE
    if seuil is None:
        return NON_COMPARABLE, MANQUE_SEUIL
    # `>` et non `>=`: l'alinea vise les marches dont le montant EXCEDE le seuil.
    return (FRANCHI, "") if acte > seuil else (NON_FRANCHI, "")


def phrase_de_franchissement(etat: str, motif: str) -> str:
    """Ce que la cellule ajoute, dans les mots d'un coproprietaire.

    **Aucune des trois phrases ne conclut a une obligation.** Un seuil franchi
    rend la consultation exigible au sens du texte; savoir si elle a EU LIEU est
    une autre question, portee par la colonne d'avis. Confondre les deux ferait
    reclamer une piece la ou elle existe deja, et l'inverse.
    """
    if etat == FRANCHI:
        return (" Le montant de cette décision **dépasse** ce seuil : "
                "l'obligation s'applique.")
    if etat == NON_FRANCHI:
        return (" Le montant de cette décision **ne dépasse pas** ce seuil : "
                "l'obligation ne s'applique pas de ce fait.")
    return (" Le franchissement **n'a pas pu être calculé** : il manque "
            f"{motif or 'un montant'}. Ce n'est pas un « non » : "
            "sur cette ligne, on ne sait pas.")
