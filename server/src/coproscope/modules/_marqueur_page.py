# -*- coding: utf-8 -*-
"""Le marqueur de page ecrit par l'extraction: un seul endroit qui le connait.

**Ce marqueur n'appartient a aucun document.** L'extraction ecrit
`===== PAGE n =====` entre les pages, **meme quand la page est vide**, parce
que c'est la seule frontiere de page que le referentiel connaisse. Il est donc
une commodite de lecture, et **il ne doit jamais compter comme du contenu**.

**Pourquoi ce module existe, et le fait qui l'a impose.** Le 2026-09-10, en
mesurant `RM-2026-0146`, j'ai compte les caracteres alphanumeriques des textes
extraits et conclu que **zero** document etait vide - alors que le registre en
declare **149 sur 858**. Ma mesure etait exacte et mesurait autre chose: elle
comptait le mot `PAGE` et les numeros de la charpente de l'extracteur. J'ai
failli publier *« le registre ment sur 149 documents »*, c'est-a-dire l'inverse
de la verite. Le registre a raison: les 149 sont des PDF `OCR_REQUIRED` dont le
texte ne porte **pas un caractere hors marqueurs** - verifie dans les deux sens,
et aucun des 709 autres n'est vide non plus.

**Le piege n'etait pas nouveau, et c'est bien le probleme.** Trois modules le
connaissaient deja et l'ecrivaient chacun de son cote:

- `lisibilite` avec `(?m)^=+\\s*PAGE\\s+\\d+\\s*=+\\s*$`;
- `_comptes_extraction_mise_en_page` avec `^=+\\s*PAGE\\s+\\d+\\s*=+$`,
  **sans le `\\s*` final** - donc un marqueur suivi d'une espace lui echappait -
  et avec `IGNORECASE`, que l'autre n'avait pas;
- `_pont_actes_source` et `_resolutions_registre` le decrivant en prose.

Un producteur, quatre lectures independantes de son format. Le format est
desormais **derive du producteur**, ici, et la garde du lot verifie l'aller-
retour: ce que l'extraction ECRIT doit etre reconnu par ce que les lecteurs
LISENT, sur plusieurs numeros de page.

**Ce que ce module ne fait pas, et il faut le dire.** Il ne connait que la
charpente de CETTE extraction. Un texte produit ailleurs - un export de syndic,
un copier-coller - peut porter ses propres separateurs de page, dans une forme
qu'aucun de ces motifs ne reconnait. Ce residu est le bon sens de la regle: on
retire ce que l'on a ecrit soi-meme, jamais ce qu'on croit reconnaitre.

**Un choix a declarer: la casse.** Le motif est SENSIBLE A LA CASSE, alors que
`_comptes_extraction_mise_en_page` lisait en `IGNORECASE`. Le producteur
n'ecrit jamais autre chose que `PAGE` en capitales, donc rien de ce qu'il ecrit
n'est perdu. Ce qui change est le cas inverse: une ligne d'un vrai document qui
ressemblerait a un marqueur en minuscules n'est plus retiree. C'est le sens
prudent - **prendre du contenu pour de la charpente est la faute la plus
couteuse**, puisqu'elle efface de la matiere en silence, exactement ce que ce
module existe pour empecher.
"""

from __future__ import annotations

import re


#: Le gabarit, tel que l'extraction l'ecrit. C'est LA definition; tout le reste
#: en decoule.
GABARIT = "===== PAGE {index} ====="


def ecrire(index: int) -> str:
    """Le marqueur de la page `index`, tel qu'il part sur le disque."""
    return GABARIT.format(index=index)


#: Le motif qui reconnait ce que `ecrire` produit. Les blancs internes sont
#: tolerants - un producteur anterieur a pu ecrire autrement - mais la forme
#: reste celle du gabarit: des signes egal, le mot, un numero, des signes egal.
#:
#: `[ \t]` et non `\s`: `\s` mange les fins de ligne, et un marqueur tient sur
#: UNE ligne. Avec `\s`, deux marqueurs separes par une ligne vide pouvaient se
#: lire comme un seul.
MARQUEUR_RE = re.compile(r"(?m)^=+[ \t]*PAGE[ \t]+\d+[ \t]*=+[ \t]*$")


def sans_marqueurs(texte: str) -> str:
    """Le texte prive de la charpente que l'extraction y a mise."""
    return MARQUEUR_RE.sub("", texte or "")


def contenu_utile(texte: str) -> int:
    """Combien de caracteres alphanumeriques ce texte porte VRAIMENT.

    C'est la fonction qui manquait le 2026-09-10. Compter sur le texte brut
    rend un nombre exact et faux: un PDF de neuf pages jamais lu rend `45`,
    parce que chaque marqueur porte `PAGE` et son numero, et qu'il y en a neuf.
    """
    return sum(1 for c in sans_marqueurs(texte) if c.isalnum())


def porte_du_contenu(texte: str) -> bool:
    """Ce texte dit-il quelque chose, ou n'est-il que sa propre charpente ?"""
    return contenu_utile(texte) > 0
