# -*- coding: utf-8 -*-
"""Evaluer une requete de media sans moteur de rendu.

`RM-2026-0111`. Le constat de l'item nommait le trou: **la suite ne contient
aucun moteur de rendu** - zero occurrence de `playwright`, `selenium`,
`puppeteer` ou `viewport` sous `server/tests/` - donc **aucune requete de media
n'est evaluee par aucun test**. La seule garde responsive LIT le fichier et
verifie qu'une chaine `display: none;` existe *quelque part* dans un bloc:
jamais **ce qui** est cache, jamais **a quelle largeur**. C'est le mode de
defaillance de `RM-2026-0106`, dans une garde.

**CE QUE CE MODULE FAIT.** Il lit les feuilles, isole les blocs
`@media (max-width: N)`, et rend la valeur effective d'une propriete pour un
selecteur **a une largeur donnee**, en appliquant les regles dans l'ordre du
document - ce qui est l'ordre de la cascade a specificite egale.

**CE QU'IL NE FAIT PAS, ET IL FAUT LE DIRE.** Ce n'est pas un navigateur:

- il compare les selecteurs **textuellement**, donc il repond sur le selecteur
  exact qu'on lui donne et n'en deduit aucun autre - `.cs-topbar .instance-meta`
  et `.instance-meta` sont deux questions differentes;
- il n'applique **aucune regle de specificite**: a selecteurs differents, c'est
  l'ordre du document qui tranche, ce qui est faux en general et suffisant ici
  parce que les feuilles sont ecrites dans cet ordre;
- il ne connait **ni heritage, ni cascade d'ancetres**: un parent cache rend
  l'enfant invisible sans que ce module le voie.

Ces trois limites sont la raison pour laquelle il ne remplace pas une recette
sur page reelle. Il repond a une question etroite et verifiable: **cette regle
precise cache-t-elle cet element a cette largeur ?**
"""
from __future__ import annotations

import re
from pathlib import Path

STATIQUE = (Path(__file__).resolve().parents[1]
            / "src" / "coproscope" / "web" / "static")

#: Une requete de media bornee en largeur. Les autres formes - `min-width`,
#: `print`, `prefers-*` - sont ignorees a dessein: elles ne repondent pas a la
#: question *que voit-on en retrecissant la fenetre*.
_MEDIA = re.compile(r"@media\s*\(\s*max-width:\s*(\d+)px\s*\)\s*\{", re.I)

_COMMENTAIRE = re.compile(r"/\*.*?\*/", re.S)


def feuilles() -> str:
    """Les fragments, dans l'ordre ou `styles.css` les importe."""
    return "\n".join(
        chemin.read_text(encoding="utf-8", errors="ignore")
        for chemin in sorted(STATIQUE.glob("styles_part_*.css")))


def _sans_commentaires(css: str) -> str:
    return _COMMENTAIRE.sub(" ", css)


def _bloc(css: str, depart: int) -> tuple[str, int]:
    """Le contenu d'un bloc accolade ouvert juste avant `depart`."""
    profondeur = 1
    i = depart
    while i < len(css) and profondeur:
        if css[i] == "{":
            profondeur += 1
        elif css[i] == "}":
            profondeur -= 1
        i += 1
    return css[depart:i - 1], i


def regles(css: str, largeur: int) -> list[tuple[str, str]]:
    """(selecteur, corps) applicables a cette largeur, dans l'ordre du document.

    Une regle hors media s'applique toujours; une regle sous
    `@media (max-width: N)` s'applique quand `largeur <= N`.
    """
    css = _sans_commentaires(css)
    trouvees: list[tuple[str, str]] = []
    i = 0
    while i < len(css):
        media = _MEDIA.search(css, i)
        debut_media = media.start() if media else len(css)
        trouvees.extend(_regles_simples(css[i:debut_media]))
        if not media:
            break
        contenu, suite = _bloc(css, media.end())
        if largeur <= int(media.group(1)):
            trouvees.extend(_regles_simples(contenu))
        i = suite
    return trouvees


def _regles_simples(css: str) -> list[tuple[str, str]]:
    trouvees: list[tuple[str, str]] = []
    for bloc in re.finditer(r"([^{}@]+)\{([^{}]*)\}", css):
        for selecteur in bloc.group(1).split(","):
            selecteur = " ".join(selecteur.split())
            if selecteur:
                trouvees.append((selecteur, bloc.group(2)))
    return trouvees


def propriete(css: str, selecteur: str, nom: str, largeur: int) -> str:
    """La derniere valeur posee pour `nom` sur ce selecteur, a cette largeur.

    Rend `""` quand aucune regle ne la pose - ce qui **n'est pas** la meme
    chose que la valeur par defaut du navigateur, et l'appelant doit le savoir.
    """
    motif = re.compile(r"(?:^|;)\s*" + re.escape(nom) + r"\s*:\s*([^;]+)")
    valeur = ""
    for cible, corps in regles(css, largeur):
        if cible != selecteur:
            continue
        trouve = motif.findall(corps)
        if trouve:
            valeur = trouve[-1].strip()
    return valeur


def est_cache(css: str, selecteur: str, largeur: int) -> bool:
    """Cette regle precise cache-t-elle cet element a cette largeur ?"""
    return propriete(css, selecteur, "display", largeur).lower() == "none"
