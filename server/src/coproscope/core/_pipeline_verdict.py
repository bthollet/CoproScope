# -*- coding: utf-8 -*-
"""Le verdict d'un passage DERIVE de ce que les etapes declarent.

**Le defaut mesure le 2026-09-08, sur une instance vide reconstruite.** Un
passage a construit 400 resolutions, en a **ecrase 84 cles** - en les nommant
une par une dans son compte-rendu - n'en a depose que 206 en base, et a conclu
`"status": "ok"`.

La chaine ne se taisait pas: elle disait tout. **C'est le verdict qui mentait**,
et le verdict est ce qu'un lecteur regarde - un humain presse, et toute
automatisation.

**La cause, et c'est la regle des axes appliquee a un statut.** Le calculateur
de statut testait deux cles precises:

    if resultat.get("coffre_non_declare") or resultat.get("registre_vide"): ...

Deux **modalites** observees le jour ou la ligne a ete ecrite. Toute autre
maniere pour une etape de perdre quelque chose - une collision de cle, un
document ecarte, une issue non lue - n'y figure pas, donc le passage se declare
`ok`. Ajouter `resolutions_ecrasees` a la liste aurait reproduit le defaut d'un
cran plus loin.

**L'axe.** Ce qui varie, c'est la maniere dont une etape echoue ou perd. Ce qui
reste invariant, c'est qu'**une etape qui perd quelque chose le DECLARE**, et
que ce depot lui a deja donne l'endroit pour le faire: `motifs_alerte`, ecrit
par l'etape elle-meme, en ses propres termes. Le verdict du passage est donc une
**fonction** de ces declarations, jamais une liste de cas connus du lecteur.

**Ce qui se degrade proprement, et c'est le point le plus important.** Une etape
qui ne declare rien n'est pas comptee comme reussie: elle est listee dans
`etapes_sans_bilan`. Une etape nouvelle, ajoutee demain sans declarer de bilan,
apparait donc **en creux** au lieu de disparaitre dans un `ok`. C'est la
difference entre une absence de mesure et une mesure conforme - la confusion que
ce depot passe ses journees a defaire.

**La dette nommee, parce qu'elle ne doit pas grandir.** `coffre_non_declare` et
`registre_vide` sont deux booleens antérieurs a ce contrat: ils disent une
impossibilite sans passer par `motifs_alerte`. Ils sont lus ici tels quels, et
ce sont **les deux seuls** noms de cle que ce module connaisse. Toute nouvelle
maniere de declarer une impossibilite passe par le contrat, pas par cette liste.
"""

from __future__ import annotations

from typing import Any, Iterable

__all__ = [
    "EMPECHEMENTS_HERITES",
    "STATUT_INCOMPLET",
    "STATUT_OK",
    "STATUT_PERTES",
    "verdict_du_passage",
]

STATUT_OK = "ok"
#: Une etape n'a pas pu s'executer: il manque une declaration a l'instance.
STATUT_INCOMPLET = "incomplet"
#: Les etapes ont tourne, et l'une d'elles a perdu quelque chose qu'elle nomme.
STATUT_PERTES = "pertes_declarees"

#: Dette antérieure au contrat `motifs_alerte`, nommee pour ne pas grandir.
EMPECHEMENTS_HERITES: tuple[str, ...] = ("coffre_non_declare", "registre_vide")


def _motifs(resultat: dict[str, Any]) -> list[str]:
    valeur = resultat.get("motifs_alerte")
    if isinstance(valeur, str):
        return [valeur]
    if isinstance(valeur, (list, tuple)):
        return [str(v) for v in valeur if str(v).strip()]
    return []


def verdict_du_passage(gouvernance: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Le statut du passage, plus ce qui le fonde, etape par etape.

    Rend toujours les trois listes, meme vides: un lecteur voit ainsi la
    difference entre *rien de declare* et *rien a declarer*.
    """
    empechements: list[str] = []
    pertes: list[str] = []
    sans_bilan: list[str] = []

    for etape in gouvernance:
        nom = str(etape.get("etape") or "?")
        resultat = etape.get("resultat")
        if not isinstance(resultat, dict):
            resultat = {}
        bloquee = [cle for cle in EMPECHEMENTS_HERITES if resultat.get(cle)]
        if bloquee:
            empechements.append("%s: %s" % (nom, ", ".join(bloquee)))
            continue
        motifs = _motifs(resultat)
        if motifs:
            pertes.extend("%s: %s" % (nom, m) for m in motifs)
        elif "motifs_alerte" not in resultat:
            # Ni perte declaree, ni declaration du tout. On ne conclut donc pas
            # au succes: on dit que l'etape n'a rien declare.
            sans_bilan.append(nom)

    if empechements:
        statut = STATUT_INCOMPLET
    elif pertes:
        statut = STATUT_PERTES
    else:
        statut = STATUT_OK
    return {
        "statut": statut,
        "empechements": empechements,
        "pertes_declarees": pertes,
        "etapes_sans_bilan": sans_bilan,
    }
