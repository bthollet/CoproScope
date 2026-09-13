# -*- coding: utf-8 -*-
"""Lire une date entierement ecrite en toutes lettres.

**Le fait mesure le 2026-09-09.** Sept proces-verbaux sur dix revenaient
`AMBIGU`, et la raison n'etait pas le choix entre candidats: **leur date propre
n'etait pas un candidat du tout**, parce qu'elle est ecrite en mots.

    Ce jour MERCREDI TROIS JUILLET DEUX MILLE VINGT QUATRE, les Coproprietaires
    Ce jour MERCREDI VINGT ET UN FEVRIER DEUX MILLE VINGT QUATRE, les ...

Consequence en aval: `_ag_id` retombait sur l'identifiant du document, et les
assemblees se fragmentaient - `AG-2024-07-03` tombait de 55 resolutions a 7.

**L'axe, et il etait sous mon nez.** Le lecteur supposait qu'une date porte des
CHIFFRES. C'est une modalite: ce qui varie est la maniere d'ECRIRE un nombre,
ce qui reste invariant est **qu'un nombre ecrit en lettres designe le meme
nombre qu'en chiffres**. Ce n'est pas une convention de cabinet, c'est la
langue - et c'est la forme des actes, celle qu'un proces-verbal ou un acte
notarie emploie par tradition.

**Ce qui se degrade proprement.** Le millesime n'est lu que sous la forme
`deux mille ...`, qui couvre 2000-2099. Un `mille neuf cent quatre-vingt-cinq`
n'est pas lu, et c'est declare: aucune date fausse n'en sort, seulement une
absence. Les corpus d'une copropriete portent des actes du siecle en cours;
l'exception, quand elle viendra, se verra comme un document sans date.
"""

from __future__ import annotations

import re

__all__ = ["MOIS_EN_LETTRES", "date_en_toutes_lettres", "nombre_en_lettres"]

_UNITES = {
    "zero": 0, "un": 1, "une": 1, "premier": 1, "premiere": 1, "deux": 2, "trois": 3,
    "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10,
    "onze": 11, "douze": 12, "treize": 13, "quatorze": 14, "quinze": 15, "seize": 16,
}
_DIZAINES = {"vingt": 20, "trente": 30, "quarante": 40, "cinquante": 50,
             "soixante": 60, "quatre-vingt": 80, "quatre-vingts": 80}

_JOURS_PAR_MOIS = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _date_existe(jour: int, mois: int, annee: int) -> bool:
    """Fermeture par le calendrier, ICI et non chez l'appelant.

    Une premiere version laissait ce controle a `_date_candidats`. Un test l'a
    pris en defaut: `le trente et un fevrier deux mille vingt quatre` rendait
    une date. **Une fonction qui rend des dates impossibles invite a s'en
    servir sans verifier** - le prochain appelant ne saura pas qu'il doit.
    """
    if not 1 <= mois <= 12:
        return False
    if mois == 2 and jour == 29:
        return annee % 4 == 0 and (annee % 100 != 0 or annee % 400 == 0)
    return 1 <= jour <= _JOURS_PAR_MOIS[mois - 1]


MOIS_EN_LETTRES = (
    "janvier", "fevrier", "mars", "avril", "mai", "juin",
    "juillet", "aout", "septembre", "octobre", "novembre", "decembre",
)


def nombre_en_lettres(mots: str) -> int:
    """Le nombre que designent ces mots, ou 0 si la suite n'en designe aucun.

    Couvre ce dont une date a besoin: 1 a 31 pour le quantieme, et les annees
    `deux mille ...`. Rend 0 - donc une absence - plutot que de deviner.
    """
    jetons = [j for j in re.split(r"[\s-]+", mots.strip().lower()) if j and j != "et"]
    if not jetons:
        return 0

    # Millesime: `deux mille` puis un reste facultatif de 0 a 99.
    if jetons[:2] == ["deux", "mille"]:
        reste = _petit_nombre(jetons[2:])
        if reste is None:
            return 0
        return 2000 + reste
    petit = _petit_nombre(jetons)
    return petit if petit else 0


def _petit_nombre(jetons: list[str]) -> int | None:
    """Un entier de 0 a 99 ecrit en lettres, ou None si la suite ne l'est pas."""
    if not jetons:
        return 0
    total = 0
    reste = list(jetons)
    if reste[0] in _DIZAINES:
        total = _DIZAINES[reste.pop(0)]
        if reste and reste[0] == "dix" and total in (60, 80):  # soixante-dix, quatre-vingt-dix
            total += 10
            reste.pop(0)
    if reste:
        if reste[0] not in _UNITES:
            return None
        valeur = _UNITES[reste.pop(0)]
        if total in (70, 90) and valeur > 9:
            return None
        total += valeur
    if reste:
        return None
    return total


#: Un quantieme en lettres, un mois, un millesime en lettres. Le jour de la
#: semaine, quand il precede, est ignore: il n'ajoute rien et varie librement.
_MOTIF = re.compile(
    r"\b((?:premier|premiere|une?|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|"
    r"treize|quatorze|quinze|seize|vingt|trente)(?:[\s-]+(?:et[\s-]+)?"
    r"(?:une?|deux|trois|quatre|cinq|six|sept|huit|neuf|dix))?)"
    r"[\s-]+(" + "|".join(MOIS_EN_LETTRES) + r")"
    r"[\s-]+(deux[\s-]+mille(?:[\s-]+[a-z-]+){0,3})\b"
)


def date_en_toutes_lettres(texte_normalise: str):
    """Toutes les dates ecrites en mots, avec leur position et leur chaine.

    Rend des triplets `(debut, fin, (quantieme, mois, millesime))`. Le texte
    doit deja etre normalise - minuscules, sans accents - comme le reste du
    lecteur, pour que les positions restent comparables.
    """
    trouves = []
    for m in _MOTIF.finditer(texte_normalise):
        jour = nombre_en_lettres(m.group(1))
        annee = nombre_en_lettres(m.group(3))
        if not (2000 <= annee <= 2099):
            continue
        mois = MOIS_EN_LETTRES.index(m.group(2)) + 1
        if not _date_existe(jour, mois, annee):
            continue
        trouves.append((m.start(), m.end(), (jour, mois, annee)))
    return trouves
