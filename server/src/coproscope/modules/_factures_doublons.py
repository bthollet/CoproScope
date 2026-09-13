# -*- coding: utf-8 -*-
"""Deux ecritures de meme numero designent-elles la meme obligation ?

`RM-2026-0135`. L'axe de l'item, dans ses termes: la question n'est pas
*supprimer les repetitions* mais **deux ecritures qui portent le meme numero
designent-elles la meme obligation de paiement**, ce qui se tranche sur
l'emetteur, la date et le sens du montant. *Une deduplication ecrite sur
l'egalite du couple effacerait de vraies pieces.*

**CE QUE LA CLE PORTE, ET POURQUOI ELLE NE PORTE PAS LA DATE.**

La cle est `fournisseur|numero|ttc`. Elle inclut donc bien **l'emetteur**, et
elle inclut **le sens du montant** - ce qui n'etait pas evident et a ete
verifie le 2026-09-12 par le point d'entree de l'extracteur: `ttc` est signe,
un avoir sort a `-600.00` et sa facture a `600.00`, donc **les deux portent
deja deux cles distinctes**. Un avoir n'est jamais signale comme doublon de sa
facture, et la moitie du residu que l'item annoncait etait donc deja couverte.

**Ajouter la date a la cle serait le mauvais correctif, et l'axe de l'item le
dit lui-meme.** Une RELANCE porte legitimement le meme numero, le meme montant
et une autre date - et elle designe **la meme obligation de paiement**. La date
dans la cle les separerait, donc **ferait disparaitre le signal sur le cas meme
que l'item cite**. Une facture rectificative, elle, porte un autre montant:
elle est deja separee.

**CE QUI MANQUAIT: dire CE QUI DISTINGUE les deux ecritures.** Le signalement
ne le disait pas, et un lecteur ne pouvait pas separer une relance d'un second
depot sans relire les deux lignes. La date sert donc de **discriminant
nomme**, jamais de cle - et rien n'est efface: c'est un fait de plus, pas un
verdict. **Un humain tranche** entre relance, second depot et reemission.
"""

from __future__ import annotations

#: Deux ecritures se ressemblent assez pour qu'on le dise.
DOUBLON_POTENTIEL = "DOUBLON_POTENTIEL"

#: Elles se ressemblent ET leurs dates different: relance, second depot, ou
#: reemission. Le fait est pose, le verdict ne l'est pas.
DOUBLON_DATES_DIFFERENTES = "DOUBLON_DATES_DIFFERENTES"


def cle_de_doublon(fournisseur: str, numero: str, ttc: str) -> str:
    """L'emetteur, le numero et le montant SIGNE.

    Le montant porte son signe, ce qui separe un avoir de sa facture sans
    qu'aucune regle ne nomme le mot `avoir`.
    """
    return "%s|%s|%s" % (fournisseur, numero, ttc)


def cle_vide(cle: str) -> bool:
    """Une cle dont tous les champs sont vides ne rapproche rien.

    Sans ce garde-fou, deux extractions muettes seraient signalees comme
    doublons l'une de l'autre - ce qui a deja ete corrige une fois.
    """
    return not cle.strip("|")


def anomalies_de_doublon(
    cle: str,
    date: str,
    vues: int,
    dates_vues: list[str],
) -> list[str]:
    """Ce qu'il faut dire de cette ecriture, au vu de celles qui precedent.

    `vues` est le nombre d'ecritures portant cette cle **y compris
    celle-ci**. `dates_vues` porte les dates des precedentes.

    Rend une liste vide quand il n'y a rien a dire: **le silence est la
    reponse normale**, et une anomalie posee sur la premiere ecriture d'une
    cle serait un faux positif systematique.
    """
    if cle_vide(cle) or vues <= 1:
        return []
    trouve = [DOUBLON_POTENTIEL]
    if date and any(autre and autre != date for autre in dates_vues):
        trouve.append(DOUBLON_DATES_DIFFERENTES)
    return trouve
