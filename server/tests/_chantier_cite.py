# -*- coding: utf-8 -*-
"""Les deux lectures dont la garde `test_un_chantier_cite_se_retrouve` a besoin.

Separees du fichier de test pour une seule raison: la garde et le script qui
regenere sa dette doivent lire le depot EXACTEMENT de la meme facon. Deux
copies de ces fonctions divergeraient, et la dette ecrite ne designerait plus
ce que la garde mesure.
"""
from __future__ import annotations

import re
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
DOCS = DEPOT / "docs"
GOUVERNAIL = DOCS / "roadmap_backlog_central.md"
SECTION = "Registre actif par identifiant"

#: Barre NUE: une barre echappee `\|` appartient au texte d'une cellule.
SEPARATEUR = re.compile("(?<!" + chr(92) * 2 + ")" + chr(92) + "|")

#: Un identifiant de chantier. Les deux formats du depot - l'historique
#: `CH-YYYY-NNNN` et l'horodate `CH-YYYYMMDD-HHMMSS-RM-...-slug` - et les
#: formes libres anciennes (`CH-20260602-CR-CS-RECETTE-...`) y entrent tous:
#: la forme retenue est *CH- suivi de mots separes par des tirets*, pas une
#: enumeration de formats.
CHANTIER = re.compile(r"\bCH-[0-9A-Za-z][0-9A-Za-z-]*[0-9A-Za-z]")

#: Un identifiant qui ne porte AUCUN chiffre est un gabarit ecrit en prose -
#: `CH-YYYY-NNNN` - et non un chantier. Critere de forme, pas liste de gabarits.
_UN_CHIFFRE = re.compile(r"\d")


def cellules(ligne: str) -> list[str]:
    return [c.strip() for c in SEPARATEUR.split(ligne)]


def chantiers_de(texte: str) -> set[str]:
    return {m for m in CHANTIER.findall(texte) if _UN_CHIFFRE.search(m)}


def registres_de_coordination(racine: Path = DOCS,
                              exclu: Path = GOUVERNAIL) -> dict[str, set[str]]:
    """Les registres de coordination, reconnus par leur FORME, et leurs chantiers.

    **Pas par un chemin ecrit une fois.** `test_fondements_juridiques.py`
    designait son registre par son chemin; le depot en portait deux, et la
    garde a compte 24 dettes au lieu de 19 sans jamais signaler qu'elle n'en
    lisait qu'un (`CLAUDE.md`).

    Un registre de coordination est un `.md` dont une ligne d'EN-TETE de
    tableau porte a la fois une cellule `Chantier` et une cellule `Statut`.
    Le seul mot `Chantier` ne suffit pas: trois tables d'archive l'emploient
    pour un nom de travail en prose, sans aucun etat de coordination.
    """
    trouves: dict[str, set[str]] = {}
    for chemin in sorted(racine.rglob("*.md")):
        if chemin.resolve() == exclu.resolve():
            continue
        try:
            texte = chemin.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lignes = [l for l in texte.splitlines() if l.lstrip().startswith("|")]
        if not any({"Chantier", "Statut"} <= set(cellules(l)) for l in lignes):
            continue
        ids: set[str] = set()
        for ligne in lignes:
            ids |= chantiers_de(ligne)
        trouves[chemin.relative_to(racine.parent).as_posix()] = ids
    return trouves


def lignes_d_item(gouvernail: Path = GOUVERNAIL) -> tuple[list[str], list[list[str]]]:
    """L'en-tete et les lignes d'item de la section active du gouvernail."""
    entete: list[str] = []
    items: list[list[str]] = []
    dans = False
    for ligne in gouvernail.read_text(encoding="utf-8").splitlines():
        if ligne.startswith("## "):
            dans = SECTION in ligne
            continue
        if not dans or not ligne.startswith("|"):
            continue
        morceaux = cellules(ligne)
        if ligne.startswith("| `RM-"):
            items.append(morceaux)
        elif not entete and not ligne.startswith("|---"):
            entete = morceaux
    return entete, items


def citations_orphelines(gouvernail: Path = GOUVERNAIL,
                         racine: Path = DOCS) -> dict[str, frozenset[tuple[str, str]]]:
    """Par COLONNE NOMMEE, les couples `(RM, CH)` dont le chantier ne designe rien.

    Une TABLE et non un scalaire: une citation orpheline dans *Chantiers lies*
    et une dans *Preuve/livrable* n'ont pas le meme cout - la seconde fait
    reposer une preuve sur un identifiant qui ne designe rien.

    La colonne est prise par son NOM dans l'en-tete, jamais par son index:
    reordonner les colonnes ne doit pas vider la garde.
    """
    connus = set().union(*registres_de_coordination(racine, gouvernail).values())
    entete, items = lignes_d_item(gouvernail)
    table: dict[str, set[tuple[str, str]]] = {}
    for morceaux in items:
        rm = morceaux[1].strip("`")
        for index, cellule in enumerate(morceaux):
            nom = entete[index] if index < len(entete) else "colonne %d" % index
            for ch in chantiers_de(cellule):
                if ch not in connus:
                    table.setdefault(nom, set()).add((rm, ch))
    return {nom: frozenset(couples) for nom, couples in table.items()}
