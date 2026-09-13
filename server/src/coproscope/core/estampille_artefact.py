# -*- coding: utf-8 -*-
"""Ce que CoproScope ecrit lui-meme se declare, au moment ou il l'ecrit.

`RM-2026-0061`. Tant que la marque n'existe pas, **tout filtre de provenance
retombe sur une liste de chemins**, c'est-a-dire sur la convention d'une seule
instance.

**POURQUOI LES DEUX MARQUES EXISTANTES NE SUFFISENT PAS, mesure a l'appui.**

- `source_kind` et `source_zone` sont **derives du chemin** par
  `_source_labels()`, qui compare le chemin aux racines declarees de
  l'instance. Ils sont degeneres en pratique: **1090 documents sur 1090** chez
  un cabinet et **22 sur 22** chez l'autre valent `raw`/`RAW`, parce que les
  deux instances declarent `workspace` et `raw` sur la meme racine. Zero
  information exploitable.
- `run.log_action("write", ...)` alimente bien `action_log.csv`, mais **aucun
  des 11 fichiers de travail mal classes n'y figure**: 34 cibles ecrites
  distinctes, et pas une seule des matrices, journaux ou syntheses. Ils ont ete
  produits **hors des runs journalises**.

**L'AXE.** Ce qui VARIE: le format ecrit - CSV, Markdown, JSON -, le module qui
ecrit, l'instance, et le fait qu'une course soit journalisee ou non. Ce qui
reste INVARIANT: **ce que CoproScope ecrit lui-meme n'est pas une piece recue
du syndic.** La marque se pose donc au **point d'ecriture**, qui est le seul
endroit ou cette verite est connue de facon certaine - pas au classement, qui
ne voit qu'un fichier pose quelque part.

**HORS DES VALEURS OBSERVEES:** un module ecrit demain, dans un format qu'on
n'a pas prevu, est marque le jour de sa premiere ecriture **sans que personne
ajoute quoi que ce soit**, parce que la marque vit sous `write_csv` et
`write_text` et non dans une liste d'appelants.

**CE QUE LA MARQUE N'EST PAS.** Elle ne modifie **aucun contenu**: un CSV ne
recoit pas de colonne, un Markdown pas d'en-tete. Une estampille qui change le
fichier qu'elle decrit rendrait les empreintes incomparables entre
coproprietaires - contrainte deja posee par `RM-2026-0092`. Le registre est
donc **a cote**, et le fichier reste bit pour bit celui qui a ete ecrit.

**L'INSTANCE SE TROUVE PAR SA FORME, jamais par un chemin declare.** On remonte
depuis le fichier ecrit jusqu'au dossier portant `instance.yml`. Une ecriture
hors de toute instance - un fichier temporaire, une sortie d'outillage - n'est
pas marquee: elle n'appartient a aucun coffre, donc aucun classement ne la
lira.
"""

from __future__ import annotations

import csv
import datetime
from pathlib import Path

#: Le fichier qui identifie la racine d'une instance. C'est une FORME, pas un
#: chemin: on le cherche en remontant, donc un dossier deplace reste trouve.
MARQUEUR_D_INSTANCE = "instance.yml"

#: Le registre des artefacts produits, a cote des autres registres.
REGISTRE = ("registers", "artefacts_produits.csv")

COLONNES = ("chemin_relatif", "ecrit_le")

#: Profondeur maximale de remontee. Une instance n'est jamais a cinquante
#: niveaux d'un fichier qu'elle contient, et la borne evite de remonter
#: jusqu'a la racine du disque sur une ecriture hors instance.
REMONTEE_MAXIMALE = 12

#: Ce qui est deja connu, par racine d'instance. Sans ce cache, chaque
#: ecriture relirait le registre entier.
_CONNUS: dict[Path, set[str]] = {}


def racine_d_instance(chemin: Path) -> Path | None:
    """La racine de l'instance qui contient ce chemin, ou `None`."""
    courant = Path(chemin).resolve().parent
    for _ in range(REMONTEE_MAXIMALE):
        if (courant / MARQUEUR_D_INSTANCE).is_file():
            return courant
        if courant.parent == courant:
            return None
        courant = courant.parent
    return None


def _chemin_du_registre(racine: Path) -> Path:
    return racine.joinpath(*REGISTRE)


def _deja_connus(racine: Path) -> set[str]:
    if racine in _CONNUS:
        return _CONNUS[racine]
    registre = _chemin_du_registre(racine)
    connus: set[str] = set()
    if registre.is_file():
        with registre.open("r", encoding="utf-8-sig", newline="") as fichier:
            for ligne in csv.DictReader(fichier):
                valeur = (ligne.get("chemin_relatif") or "").strip()
                if valeur:
                    connus.add(valeur)
    _CONNUS[racine] = connus
    return connus


def oublie_le_cache() -> None:
    """Pour les tests et les outils: relire le registre depuis le disque."""
    _CONNUS.clear()


def _relatif(racine: Path, chemin: Path) -> str:
    try:
        return Path(chemin).resolve().relative_to(racine).as_posix()
    except ValueError:
        return ""


def marque_produit(chemin: Path) -> bool:
    """Declare que CoproScope a produit ce fichier. Rend `True` si c'est neuf.

    **Le registre ne se marque pas lui-meme**: il est produit par CoproScope,
    mais l'inscrire declencherait une recursion sans fin et n'apprendrait rien
    a personne.
    """
    racine = racine_d_instance(chemin)
    if racine is None:
        return False
    relatif = _relatif(racine, chemin)
    if not relatif or relatif == _chemin_du_registre(racine).relative_to(racine).as_posix():
        return False
    connus = _deja_connus(racine)
    if relatif in connus:
        return False
    registre = _chemin_du_registre(racine)
    registre.parent.mkdir(parents=True, exist_ok=True)
    neuf = not registre.is_file()
    with registre.open("a", encoding="utf-8", newline="") as fichier:
        ecrivain = csv.DictWriter(fichier, fieldnames=list(COLONNES))
        if neuf:
            ecrivain.writeheader()
        ecrivain.writerow({
            "chemin_relatif": relatif,
            "ecrit_le": datetime.datetime.now().isoformat(timespec="seconds"),
        })
    connus.add(relatif)
    return True


def est_produit_par_coproscope(chemin: Path) -> bool:
    """Ce fichier a-t-il ete ECRIT par le produit, plutot que recu ?

    **Une reponse negative n'est pas une preuve de provenance externe**: un
    artefact produit avant que cette marque n'existe n'y figure pas. C'est le
    residu declare du lot, et un appelant qui conclut *donc c'est une piece du
    syndic* se trompera sur tout le fonds anterieur.
    """
    racine = racine_d_instance(chemin)
    if racine is None:
        return False
    relatif = _relatif(racine, chemin)
    return bool(relatif) and relatif in _deja_connus(racine)


def artefacts_produits(racine: Path) -> tuple[str, ...]:
    """Tout ce que le produit declare avoir ecrit dans cette instance."""
    return tuple(sorted(_deja_connus(Path(racine).resolve())))
