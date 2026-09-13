# -*- coding: utf-8 -*-
"""La periode qu'une resolution vise est-elle achevee a la date de l'assemblee ?

**Extrait de `_resolutions_qualification` le 2026-09-11**, qui passait a 626
lignes pour une limite de 600. La regle du depot est de decouper AVANT
d'ajouter, et ce bloc forme un sujet a lui seul: lire une periode, la comparer
a une date d'assemblee, et savoir dire *je ne sais pas*.

**Ce que ce module a corrige en sortant, `RM-2026-0116`.** Il n'enumere plus
deux gabarits - `du JJ/MM/AAAA au JJ/MM/AAAA` et `exercice` suivi
immediatement de quatre chiffres - mais lit une DATE DE FIN quand ceux-ci ne
mordent pas. Mesure du 2026-09-11 sur le second cabinet
(`instances/erables_pseudo_test`, 22 documents): sur 53 lignes d'approbation de
comptes, **0 etaient reconnues avant, 8 le sont apres**. Sur le corpus de
travail, le meme correctif change **zero ligne sur 393** - le premier cabinet
ecrit la forme couverte, le second non, et un gabarit calibre sur le premier
passait donc tous les tests.

**Ce qui reste `None`, et c'est le coeur de la prudence.** Sans periode
lisible, ou sans date d'assemblee, on ne sait pas si une resolution portant sur
des *comptes* arrete un exercice clos ou vote un budget a venir. Supposer l'un
des deux fabriquerait un type. L'appelant garde alors tous ses controles.
"""

from __future__ import annotations

import re

__all__ = ["EXERCICE_RE", "PERIODE_RE", "periode_close"]


# Periode d'un exercice, sous les deux formes rencontrees.
PERIODE_RE = re.compile(r"du\s+(\d{2})/(\d{2})/(\d{4})\s+au\s+(\d{2})/(\d{2})/(\d{4})")
EXERCICE_RE = re.compile(r"(?i)exercice\s+(?:\d{4}/)?(\d{4})")


def periode_close(segment: str, date_ag: str) -> bool | None:
    """La periode visee par la resolution est-elle achevee a la date de l'AG.

    Rend `None` quand aucune periode n'est lisible, ou quand la date
    d'assemblee manque. Ce `None` est le coeur de la prudence du module: sans
    les deux dates, on ne sait pas si une resolution portant sur des `comptes`
    arrete un exercice clos ou vote un budget a venir, et supposer l'un des deux
    fabriquerait un type. Une resolution non typee garde tous ses controles.
    """
    if not date_ag:
        return None
    intervalle = PERIODE_RE.search(segment)
    if intervalle:
        fin = f"{intervalle.group(6)}-{intervalle.group(5)}-{intervalle.group(4)}"
        return fin < date_ag[:10]
    exercice = EXERCICE_RE.search(segment)
    if exercice:
        return f"{exercice.group(1)}-12-31" < date_ag[:10]
    fin = _fin_de_periode_datee(segment)
    if fin:
        return fin < date_ag[:10]
    return None


def _fin_de_periode_datee(segment: str) -> str:
    """La date de fin d'exercice ecrite en clair, ou la chaine vide.

    **Pourquoi cette fonction existe, et c'est la correction de `RM-2026-0116`.**
    Les deux motifs ci-dessus enumerent des GABARITS: `du JJ/MM/AAAA au
    JJ/MM/AAAA`, et `exercice` suivi immediatement de quatre chiffres. Mesure du
    2026-09-11: sur six libelles d'approbation de comptes, **cinq retombaient
    sur `ORDINAIRE`** - dont *« Approbation des comptes de l'exercice CLOS AU 31
    decembre 2024 »*, celui que l'item nomme explicitement, et *« comptes
    arretes au 31 decembre 2024 »*. Le seul qui passait etait *« exercice
    2024 »*. **Le classement dependait donc de la presence d'une annee en
    chiffres accolee au mot `exercice`**, pas du sens de la phrase.

    **L'axe.** Ce qui VARIE: la maniere de designer la periode - par son annee,
    par son intervalle, par sa date de cloture, en chiffres ou en lettres. Ce
    qui reste INVARIANT: **une approbation de comptes porte sur une periode
    achevee, et cette periode a une date de fin.** On lit donc une date, au lieu
    d'ajouter un troisieme gabarit - lequel aurait casse au quatrieme syndic.

    **Aucun lecteur nouveau n'est ecrit.** `core._date_candidats` lit deja les
    trois formes - `31/12/2024`, `31 decembre 2024`, `TRENTE ET UN DECEMBRE
    DEUX MILLE VINGT QUATRE` - et `role_du_candidat` ecarte deja ce qui n'est
    pas une date: un numero de piece, une date d'acte cite, un jeton colle a
    d'autres chiffres. Ce module etait dans le depot et n'etait pas consulte
    ici, exactement comme le champ `exclut` de `RM-2026-0144`.

    **La plus TARDIVE est retenue**, et c'est le sens de la phrase: *comptes de
    l'exercice du 01/01/2024 au 31/12/2024* borne la periode par sa fin. Prendre
    la premiere daterait l'exercice par son ouverture, donc le declarerait clos
    un an trop tot.

    **Residu nomme.** Une date presente dans le libelle pour une autre raison -
    une echeance de paiement, une date de convocation - serait lue comme une fin
    de periode. Le risque est borne par l'appelant: `periode_close` n'est
    consultee qu'en conjonction avec `COMPTES_RE` ou `BUDGET_RE`, donc sur des
    libelles qui parlent deja de comptes ou de budget. Il n'est pas nul.
    """
    from ..core._date_candidats import (
        ROLE_DATE,
        candidats_du_texte,
        normalise,
        role_du_candidat,
    )

    texte = normalise(segment)
    dates: list[str] = []
    for candidat in candidats_du_texte(texte):
        if role_du_candidat(texte, candidat) != ROLE_DATE:
            continue
        # **UNE GARDE A ETE ECRITE ICI PUIS RETIREE, et la mesure l'a exigee.**
        # Elle ecartait les candidats dont `ordre_possible` vaut `ambigu`, au
        # motif que `01/12` et `12/01` designent deux dates. La campagne de
        # mutation du 2026-09-11 ne l'a pas fait mordre, et la mesure a dit
        # pourquoi: **`ambigu` n'est jamais produit**. Il demande deux lectures
        # valides du meme jeton - annee en tete ET en queue - ce qui exige un
        # quantieme a quatre chiffres. Sur 432 formes essayees, 114 candidats:
        # `jma` et `amj` seulement, **zero ambigu**.
        #
        # Le depot a deja tranche ce cas, dans `_date_candidats` lui-meme, a
        # propos d'une regle sur les heures: *une garde qui ne peut pas se
        # declencher donne l'illusion d'une protection: on la retire plutot que
        # de la garder pour la forme.* Le jour ou un producteur de candidats
        # rendra `ambigu`, c'est LUI qui devra le declarer.
        quantieme, mois, millesime = candidat.champs
        if not (mois and millesime):
            continue
        # Un quantieme non dit - `decembre 2024` - se lit comme la fin du mois
        # nommé: c'est la seule lecture qui ne DEVANCE pas la cloture.
        jour = quantieme or _JOURS_DU_MOIS[mois - 1]
        dates.append("%04d-%02d-%02d" % (millesime, mois, jour))
    return max(dates) if dates else ""


#: Le dernier jour de chaque mois, fevrier au plus long. Sert uniquement a lire
#: `decembre 2024` comme la FIN de decembre: un quantieme absent ne doit pas
#: faire croire l'exercice clos le premier du mois.
_JOURS_DU_MOIS = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
