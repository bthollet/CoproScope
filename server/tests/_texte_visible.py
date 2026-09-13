# -*- coding: utf-8 -*-
"""Tout texte d'un gabarit qui parvient a l'utilisateur, en UN seul endroit.

`RM-2026-0106`, 2026-09-12. **Deux gardes surveillaient la meme notion avec
deux instruments qui ne voient pas la meme chose**, et l'union n'appartenait a
personne:

- `test_ui_accessibility_language` lisait les CORPS d'element - `h1` a `h3`,
  `a`, `strong`, certains `span` - sur neuf gabarits, elargis a 46 le meme jour;
- `test_ui_novice_language_static` lisait ces corps ET les ATTRIBUTS visibles -
  `aria-label`, `title`, `alt`, `placeholder` - mais sur neuf gabarits.

**Mesure du 2026-09-12, et elle refute la subsomption dans les deux sens.** Sur
les 46 gabarits: l'instrument novice voit **1 471** fragments, l'instrument
accessibilite **691**, et **12 gabarits portent un fragment que seul
l'accessibilite voit** - ses motifs traversent les elements imbriques la ou les
autres s'arretent. Aucun des deux ne contient l'autre. Une regle gardee par
deux instruments partiels est **le defaut numero un du produit applique a
l'outillage**: plusieurs comptages concurrents pour la meme notion.

**L'AXE.** Ce qui VARIE: le vehicule du texte - corps d'element, attribut
d'accessibilite, infobulle. Ce qui reste INVARIANT: **tout texte qui parvient a
l'utilisateur est du texte visible, quel que soit son vehicule.** Un
`aria-label` est lu a voix haute par un lecteur d'ecran: il est *plus* expose
que le corps d'un `span`, pas moins.

**Ce que le code en fait:** une seule fonction, ici, et les deux gardes
l'appellent. **Hors des valeurs observees:** un vehicule nouveau - un
`data-tooltip`, un attribut d'un composant a venir - s'ajoute a un seul
endroit et les deux gardes en beneficient le jour meme.
"""
from __future__ import annotations

import re
from html import unescape
from pathlib import Path

#: Les attributs dont le contenu est restitue a l'utilisateur, a l'ecran ou a
#: la voix. Ce n'est pas une liste de modalites observees: c'est l'ensemble des
#: attributs HTML dont la specification dit qu'ils sont presentes a l'usager.
ATTRIBUTS_RESTITUES = re.compile(
    r"\b(?:aria-label|title|alt|placeholder)=[\"']([^\"']*)[\"']", re.I)

#: Les elements dont le corps est du texte courant. Les deux motifs coexistent
#: a dessein: le second traverse les elements imbriques, le premier s'arrete a
#: la premiere fermeture, et la mesure montre que chacun rattrape ce que
#: l'autre laisse.
#: **Elargi le 2026-09-12, et la raison n'est pas theorique.** La liste
#: precedente - `h1` a `h3`, `a`, `button`, `strong`, `span`, `small`,
#: `caption` - etait une enumeration de vehicules OBSERVES la ou le module
#: revendique l'axe *tout texte qui parvient a l'utilisateur*. Elle ignorait un
#: paragraphe, une cellule de tableau, une etiquette de formulaire, un element
#: de liste: rien de tout cela n'est moins lu que le corps d'un `span`.
#:
#: **Le cout a ete mesure en essayant de reparer sans l'elargir.** Une premiere
#: passe de reparation des accents a corrige `<h2>Contrôle des comptes</h2>` et
#: laisse, DEUX LIGNES PLUS BAS dans le meme ecran,
#: `<p class="lead">Vue de controle avant AG</p>` - le meme mot, ecrit des deux
#: facons sous les yeux du meme lecteur, ce qui est exactement le defaut que la
#: garde existe pour empecher. Une demi-reparation est pire que l'absence de
#: reparation: elle a l'air d'une negligence au lieu d'une limite.
CORPS_COURTS = re.compile(
    r"<(?:h[1-6]|a|button|strong|em|b|span|small|caption|p|li|td|th|label"
    r"|option|legend|summary|figcaption|dt|dd)\b[^>]*>(.*?)"
    r"</(?:h[1-6]|a|button|strong|em|b|span|small|caption|p|li|td|th|label"
    r"|option|legend|summary|figcaption|dt|dd)>", re.I | re.S)

CORPS_LARGES = (
    r"<h[1-3][^>]*>(.*?)</h[1-3]>",
    r"<a\b[^>]*>(.*?)</a>",
    r"<strong\b[^>]*>(.*?)</strong>",
    r"<span\b[^>]*class=[\"'][^\"']*(?:novice-label|nav-extra|badge|pill)"
    r"[^\"']*[\"'][^>]*>(.*?)</span>",
)

#: Une entite HTML n'est pas un mot: `&nbsp;` parvient a l'utilisateur comme
#: une ESPACE, jamais comme les quatre lettres `nbsp`. Le texte nettoye ne s'y
#: trompe pas - `unescape` la resout - mais un masque pose sur la source brute
#: y verrait un mot, et la mesure du 2026-09-12 l'a montre: trois faux `nbsp`
#: dans `controle_gouvernance.html`.
_ENTITE = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]{1,31});")

_COMMENTAIRE_JINJA = re.compile(r"\{#.*?#\}", re.S)
_SORTIE_JINJA = re.compile(r"\{\{.*?\}\}", re.S)
_BLOC_JINJA = re.compile(r"\{%.*?%\}", re.S)
_BALISE = re.compile(r"<[^>]+>")


def _en_clair(fragment: str) -> str:
    texte = _SORTIE_JINJA.sub(" ", fragment)
    texte = _BLOC_JINJA.sub(" ", texte)
    texte = _BALISE.sub(" ", texte)
    return unescape(re.sub(r"\s+", " ", texte)).strip()


def fragments_visibles(chemin: Path) -> list[str]:
    """Les fragments de texte qu'un gabarit presente a l'utilisateur.

    Un commentaire Jinja n'en fait pas partie: il ne sort jamais du gabarit.
    """
    source = _COMMENTAIRE_JINJA.sub(" ", chemin.read_text(encoding="utf-8"))
    bruts: list[str] = list(ATTRIBUTS_RESTITUES.findall(source))
    bruts.extend(CORPS_COURTS.findall(source))
    for motif in CORPS_LARGES:
        bruts.extend(re.findall(motif, source, flags=re.S | re.I))
    vus: list[str] = []
    connus: set[str] = set()
    for brut in bruts:
        texte = _en_clair(brut)
        if texte and texte not in connus:
            connus.add(texte)
            vus.append(texte)
    return vus


def texte_visible(chemin: Path) -> str:
    """Le meme, en un seul bloc, pour y chercher un mot."""
    return "\n".join(fragments_visibles(chemin))


# --------------------------------------------------------------------------
# Situer, et non plus seulement compter
# --------------------------------------------------------------------------
# **Ce que cette moitie ajoute, et pourquoi elle manquait.** `RM-2026-0115`
# avait mesure 216 mots affiches sans accents et nommait lui-meme son blocage:
# *l'instrument qui les COMPTE ne sait pas les SITUER. Il rend du texte, pas des
# positions, et un remplacement au motif dans le fichier brut toucherait des
# identifiants - `res_vue.assemblees`, `vue.deja_reconnus`, la classe CSS
# `coffre-model` - et des commentaires Jinja qui ne sortent jamais du gabarit.*
#
# **La methode, et elle evite le piege que l'item decrit.** On ne cherche pas
# dans le texte nettoye, dont les offsets ne correspondent plus a rien: on
# construit un MASQUE sur la source brute - position par position, ce caractere
# parvient-il a l'utilisateur ? - puis on ne retient que les occurrences
# entierement a l'interieur. Un identifiant dans `{{ ... }}`, une classe CSS
# dans une balise et un commentaire Jinja sont donc exclus **par construction**,
# au lieu de l'etre par une liste de cas a ne pas toucher.


def masque_visible(source: str) -> list[bool]:
    """Position par position: ce caractere parvient-il a l'utilisateur ?

    L'ordre compte et il n'est pas interchangeable: on marque d'abord ce qui
    est restitue, puis on RETIRE ce qui ne sort jamais du gabarit - une balise,
    une sortie ou un bloc Jinja, un commentaire - parce que ceux-la se trouvent
    a l'INTERIEUR des corps deja marques. L'inverse laisserait passer le nom
    d'une variable au milieu d'une phrase.
    """
    masque = [False] * len(source)

    def marque(debut: int, fin: int, valeur: bool) -> None:
        for position in range(debut, fin):
            masque[position] = valeur

    #: **L'ordre a ete corrige le 2026-09-12, et l'erreur etait totale.** Les
    #: attributs etaient marques AVANT le retrait des balises - or la valeur
    #: d'un `aria-label` vit a l'interieur de la balise, donc `<[^>]+>` la
    #: reeffacait aussitot. Tout le texte porte par un attribut etait ainsi
    #: invisible a la localisation: `aria-label="Atelier pieces, relier piece,
    #: point, action et preuve"` dans `base.html`, un `title` dans
    #: `governance.html`... c'est-a-dire **exactement le texte qu'un lecteur
    #: d'ecran prononce**, que l'en-tete de ce module declare *plus* expose que
    #: le corps d'un `span`, pas moins.
    #:
    #: Les attributs se marquent donc APRES le retrait des balises, et ce qui
    #: ne sort jamais du gabarit - Jinja, entites - se retire une seconde fois,
    #: parce qu'une valeur d'attribut peut en contenir.
    for trouve in CORPS_COURTS.finditer(source):
        marque(*trouve.span(1), True)
    for motif in CORPS_LARGES:
        for trouve in re.finditer(motif, source, flags=re.S | re.I):
            marque(*trouve.span(1), True)
    # `_ENTITE` n'est pas ici, et son absence est deliberee: la passe finale
    # balaie la source ENTIERE, donc elle retire les entites partout. La citer
    # deux fois etait du poids mort - et la campagne de mutation l'a montre en
    # une ligne: retirer l'une des deux ne changeait rien, ce qui est la
    # definition d'une garde qui ne garde pas.
    for motif in (_COMMENTAIRE_JINJA, _SORTIE_JINJA, _BLOC_JINJA, _BALISE):
        for trouve in motif.finditer(source):
            marque(*trouve.span(), False)
    for trouve in ATTRIBUTS_RESTITUES.finditer(source):
        marque(*trouve.span(1), True)
    for motif in (_COMMENTAIRE_JINJA, _SORTIE_JINJA, _BLOC_JINJA, _ENTITE):
        for trouve in motif.finditer(source):
            marque(*trouve.span(), False)
    return masque


def occurrences_situees(
    chemin: Path, motif: "re.Pattern[str]"
) -> list[tuple[int, int, str]]:
    """Les occurrences de `motif` QUI PARVIENNENT a l'utilisateur, situees.

    Rend `(ligne, colonne, texte)`, la ligne comptee a partir de 1 et la
    colonne a partir de 0, comme un editeur les affiche. Une occurrence a
    cheval sur la frontiere du visible n'est pas rendue: elle serait autant
    dans le texte que hors de lui, et un remplacement aveugle y casserait le
    gabarit.
    """
    source = chemin.read_text(encoding="utf-8")
    masque = masque_visible(source)
    situees: list[tuple[int, int, str]] = []
    for trouve in motif.finditer(source):
        debut, fin = trouve.span()
        if not all(masque[debut:fin]):
            continue
        ligne = source.count("\n", 0, debut) + 1
        colonne = debut - (source.rfind("\n", 0, debut) + 1)
        situees.append((ligne, colonne, trouve.group()))
    return situees
