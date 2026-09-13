# -*- coding: utf-8 -*-
"""Ce que le controle de confidentialite a REELLEMENT lu avant de conclure.

**Le defaut, mesure le 2026-09-11 sur une instance VIDE reabsorbant 858 pieces
sources.** Le classement de diffusabilite d'un document - celui qui decide si
une piece peut sortir, et sous quelle forme - est rendu par
`build_access_policy` a partir d'un ECHANTILLON. Trois plafonds se superposent,
et aucun des trois ne laissait de trace:

1. `_read_pdf_text` s'arrete a `min(page_count, 10)`: **dix pages**, quelle que
   soit la longueur du document;
2. `_read_sample` tronque a `max_text_chars`, **50 000 caracteres** par defaut;
3. `build_access_policy` retronque son propre foin a **50 000 caracteres**,
   meme quand l'appelant lui passe tout.

**Ce que ca coute, et ce n'est pas theorique.** Sur les 64 PDF de plus de dix
pages du corpus, **19 portent au moins une categorie de donnee personnelle que
le scan ne voit pas**, et **12 portent une categorie CRITIQUE ratee**. Deux
documents de 140 et 143 pages sont classes sur **3,6 %** de leur texte: au-dela
de la page dix, ils portent `HEALTH`, `IBAN`, `IMPAID`, `CONTENTIOUS`,
`CONFIDENTIAL`, `LOT` et `NEGOTIATION` - aucune de ces categories n'a compte
dans leur verdict. Quatre documents etaient declares `nominative` **sans
relecture humaine exigee** alors qu'ils relevent de l'article 9 du RGPD.

**L'AXE, et il decide de tout le reste.** Ce qui VARIE: la longueur des pieces,
leur format, la valeur des plafonds, la puissance de la machine qui scanne.
Ce qui reste INVARIANT: **un controle qui n'a pas lu tout son objet ne peut pas
rendre le meme « rien trouve » qu'un controle complet.** L'absence de constat
sur un echantillon n'est pas une absence de constat.

**Ce que ce module NE fait PAS, et c'est deliberé.** Il ne remonte aucun
plafond. Ecrire `min(page_count, 50)` remplacerait dix par cinquante et
laisserait le defaut intact au document de cinquante et une pages - ce serait
coder une modalite observee a la place d'un axe. Les plafonds protegent le
temps de traitement et restent ou ils sont; ce qui change est qu'ils **cessent
d'etre muets**.

**Trois etats, et le troisieme n'est jamais un feu vert.** C'est le meme partage
que partout ailleurs dans ce produit: 0 rien trouve, 1 quelque chose trouve,
2 le controle n'a pas pu etre fait. Ici, `PARTIELLE` est ce 2: elle dit que le
verdict ne porte que sur ce qui a ete lu, et rien sur le reste.

**Hors des valeurs observees.** Un document d'une page, un de 153 pages, un
tableur d'un million de lignes, un fichier illisible: les quatre se rangent dans
les trois etats sans cas particulier, parce que l'etat se deduit d'une
comparaison - ce qui a ete lu contre ce qui existe - et non d'un seuil.
Si un plafond change demain, ou si un lecteur devient capable de tout lire,
`COMPLETE` revient de lui-meme et l'exigence de relecture disparait sans qu'on
retouche une ligne: **cette garde ne demande pas que le defaut survive.**
"""

from __future__ import annotations

__all__ = [
    "CHAMP",
    "COMPLETE",
    "INDETERMINEE",
    "PARTIELLE",
    "conclut",
    "couverture_lue",
    "la_plus_prudente",
    "lisible",
]

#: Tout ce qui existe a ete confronte aux detecteurs. Un « rien trouve » conclut.
COMPLETE = "COMPLETE"

#: Une partie seulement. Le verdict vaut pour cette partie, et **rien** pour le
#: reste. C'est l'etat 2 du partage a trois: le controle n'a pas pu etre fait
#: en entier, ce qui n'est pas la meme chose que ne rien avoir trouve.
PARTIELLE = "PARTIELLE"

#: L'appelant n'a pas dit ce qu'il avait lu, et rien ici ne permet de le
#: deduire. **Ce n'est pas un synonyme de COMPLETE** - c'est l'aveu qu'on
#: l'ignore. Un chemin qui rend cet etat est un chemin a brancher.
INDETERMINEE = "INDETERMINEE"

#: Le nom sous lequel la couverture voyage dans une ligne de registre. Un seul
#: endroit le connait, pour la meme raison que le marqueur de page: un format
#: lu a quatre endroits finit par etre lu de quatre facons.
CHAMP = "text_coverage"

#: Du plus prudent au moins prudent. L'ordre EST la regle de composition:
#: quand deux etages du meme controle disent des choses differentes, c'est le
#: plus prudent qui vaut, parce qu'une lecture complete en aval ne repare pas
#: une troncature en amont.
_ORDRE = (PARTIELLE, INDETERMINEE, COMPLETE)


def couverture_lue(lus: int, disponibles: int | None) -> str:
    """L'etat de couverture d'une lecture, deduit d'une comparaison.

    `lus` est ce que le lecteur a ramene, `disponibles` ce que la source
    portait. `disponibles` vaut `None` quand le lecteur ne peut pas le savoir -
    et c'est un cas reel, pas une commodite: un extracteur qui s'arrete des
    qu'il a sa dose ne sait pas ce qu'il n'a pas ouvert.

    **Un lecteur qui ramene exactement son plafond est traite comme tronque.**
    C'est volontaire et c'est le sens prudent: `[:50000]` sur un texte de
    50 000 caracteres pile rend un texte complet, mais rien dans le resultat ne
    permet de distinguer ce cas de celui d'un texte de 50 001. Se tromper vers
    `PARTIELLE` coute une relecture; se tromper vers `COMPLETE` laisse sortir
    une piece.
    """
    if disponibles is None:
        return INDETERMINEE
    # **Rien a lire n'est pas une lecture tronquee.** Un verdict rendu sans
    # texte - l'inventaire le fait, avant toute extraction - ne subit aucune
    # coupe ICI. Ce qu'il vaut est dit par l'etat que l'amont declare, et
    # l'amont muet dit `INDETERMINEE`; le confondre avec `PARTIELLE` ferait
    # exiger une relecture humaine sur les 858 pieces des le premier passage,
    # et un signal qui se declenche partout finit par etre eteint.
    if disponibles <= 0:
        return COMPLETE
    if lus <= 0:
        return PARTIELLE
    return COMPLETE if lus >= disponibles else PARTIELLE


def la_plus_prudente(*etats: str) -> str:
    """L'etat le plus prudent parmi ceux qu'on lui donne.

    Un verdict traverse plusieurs etages - le lecteur de fichier, puis le
    constructeur de politique qui retronque. Chacun connait SA troncature et
    ignore celle des autres; la couverture reelle est donc la plus mauvaise des
    deux, jamais la derniere vue.
    """
    connus = [e for e in etats if e in _ORDRE]
    if not connus:
        return INDETERMINEE
    return min(connus, key=_ORDRE.index)


def conclut(etat: str) -> bool:
    """Un « rien trouve » sous cet etat vaut-il conclusion ?

    C'est la seule question que le reste du produit a besoin de poser, et elle
    n'a de reponse franche que pour `COMPLETE`. `INDETERMINEE` ne conclut pas
    davantage que `PARTIELLE`: ne pas savoir ce qu'on a lu et savoir qu'on n'a
    pas tout lu laissent le lecteur au meme endroit.
    """
    return etat == COMPLETE


def lisible(etat: str) -> str:
    """La couverture dite a un humain, sans jargon ni pourcentage invente."""
    return {
        COMPLETE: "Le document a été lu en entier.",
        PARTIELLE: "Seule une partie du document a été lue : "
                   "ce constat ne dit rien du reste.",
        INDETERMINEE: "Ce contrôle ne déclare pas quelle part du document "
                      "il a lue.",
    }.get(etat, "Ce contrôle ne déclare pas quelle part du document il a lue.")
