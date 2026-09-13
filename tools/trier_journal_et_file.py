# -*- coding: utf-8 -*-
"""Separer le JOURNAL des defauts connus de la FILE de ce qui est engage.

**Le defaut mesure le 2026-09-09, sur une question de Brice.** Le gouvernail
fait deux metiers dans la meme colonne: il enregistre ce qu'on sait de faux, et
il engage ce que quelqu'un doit faire. Les melanger rend le compte d'`ACTIF`
ininterpretable - c'est la distinction la plus ancienne du metier, entre le
rapport d'anomalie et l'element de travail.

Mesure de la periode: **115 items ajoutes, 24 fermes, 4,8 pour 1.** Un suivi qui
recoit cinq fois plus qu'il ne rend n'est plus un outil de pilotage, c'est un
journal - et il vaut mieux l'assumer que le subir.

**Ce que cet outil fait, et ce qu'il ne fait pas.** Il ne deplace rien et ne
ferme rien: il **classe**, et il rend le compte de chaque classe. La decision de
separer appartient a Brice; ce qui lui manquait pour la prendre etait de savoir
a quoi ressemblerait chaque pile.

**Les trois classes, et l'axe qui les separe.** Ce qui varie: le sujet, la
priorite, l'age. Ce qui reste invariant: **ce qu'il faut pour que l'item cesse
d'etre ouvert**.

- **DECISION** - il attend un mot humain. Aucun travail ne le fera avancer.
- **ENGAGE** - un travail est en cours ou une prochaine action est ecrite et
  executable sans decision.
- **CONSTAT GARDE** - le defaut est connu, une garde executable le tient, et
  rien n'attend personne. C'est du journal, pas de la file.

**Degradation.** Un item qu'aucune des trois ne reconnait sort en `A_CLASSER`
avec son identifiant: on ne le range pas au hasard, on le montre.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[1]
GOUVERNAIL = DEPOT / "docs" / "roadmap_backlog_central.md"
ANCRE = "## Registre actif par identifiant"

_NUE = re.compile(r"(?<!\\)\|")
_ITEM = re.compile(r"^\| `(RM-\d{4}-\d{4})` \|")
CHAMPS = ("id", "t", "ty", "st", "p", "o", "src", "a", "ch", "preuve", "maj")

#: Ce qui signale qu'un item attend un MOT et non un travail. Le statut le dit
#: quand il est pose; la description le dit quand il ne l'est pas.
_ATTEND_UN_MOT = ("a arbitrer", "arbitrage", "decision pour brice",
                  "question fermee", "attend un mot", "en_attente_user",
                  "a trancher", "decision produit")

#: Ce qui signale qu'un residu est **tenu par une garde executable**, donc qu'il
#: n'attend plus rien: le defaut ne peut pas revenir sans faire echouer un test.
_GARDE_POSEE = ("residu executable", "garde posee", "garde executable",
                "prouve porteur", "prouvee mordante", "controle negatif")


def _cellules(ligne: str) -> dict:
    brut = _NUE.split(ligne)[1:-1]
    if len(brut) != len(CHAMPS):
        return {}
    return {c: v.strip().strip("`").strip() for c, v in zip(CHAMPS, brut)}


def registre() -> list[dict]:
    lignes = GOUVERNAIL.read_text(encoding="utf-8").splitlines()
    d = next(i for i, l in enumerate(lignes) if l.startswith(ANCRE))
    f = next((i for i, l in enumerate(lignes[d + 1:], d + 1) if l.startswith("## ")), len(lignes))
    return [c for l in lignes[d:f] if _ITEM.match(l) and (c := _cellules(l))]


def classe(item: dict) -> str:
    """DECISION, ENGAGE, CONSTAT_GARDE, ou A_CLASSER."""
    statut = item.get("st", "").upper()
    texte = (item.get("a", "") + " " + item.get("t", "")).lower().replace("'", " ")
    if statut == "A_ARBITRER" or any(m in texte for m in _ATTEND_UN_MOT):
        return "DECISION"
    if any(m in texte for m in _GARDE_POSEE):
        # Une garde posee ET une prochaine action executable: c'est encore de la
        # file. La garde seule, sans suite, est du journal.
        return "CONSTAT_GARDE" if "prochaine action" not in texte else "ENGAGE"
    if item.get("a", "").strip():
        return "ENGAGE"
    return "A_CLASSER"


def main(argv: list[str]) -> int:
    actifs = [i for i in registre() if i.get("st", "").upper() == "ACTIF"]
    piles: dict[str, list[dict]] = {}
    for item in actifs:
        piles.setdefault(classe(item), []).append(item)

    print("%d items ACTIF au registre" % len(actifs))
    print()
    for nom in ("DECISION", "ENGAGE", "CONSTAT_GARDE", "A_CLASSER"):
        pile = piles.get(nom, [])
        p0 = sum(1 for i in pile if i.get("p", "").upper() == "P0")
        print("  %-14s %3d items  dont %2d en P0" % (nom, len(pile), p0))
    print()
    if "--detail" in argv:
        for nom in ("DECISION", "ENGAGE", "CONSTAT_GARDE", "A_CLASSER"):
            print("=== %s ===" % nom)
            for i in sorted(piles.get(nom, []), key=lambda x: x["p"]):
                print("  %-6s %-14s %s" % (i.get("p"), i.get("id"), i.get("t", "")[:76]))
            print()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
