# -*- coding: utf-8 -*-
"""Lire le style REEL de la coque, et dire ce qui y supprime un element.

Instrument extrait de `test_ui_identite_barre_haute.py` le 2026-09-09, quand ce
fichier a depasse les 600 lignes. Il est ici parce qu'il est reutilisable: la
question *quelle regle peut faire disparaitre CET element* se pose pour la barre
haute, mais aussi pour la navigation laterale ou pour un bandeau d'alerte.

**Ce qu'il sait faire.** (1) Enumerer toutes les regles de style d'un fichier, a
toute profondeur d'at-rules - `@media`, `@supports`, `@container`, ce qui
viendra: rien n'est enumere, on marche sur les accolades. (2) Retrouver le CSS
qu'un script injecte, qui vit dans ses chaines litterales. (3) Dire si un
selecteur peut designer un noeud d'une chaine d'ancetres donnee. (4) Classer une
declaration comme supprimante ou non.

**Le sens de degradation, qui est la raison d'etre du classificateur.** Il
travaille par CATEGORIE D'EFFET, jamais par liste de valeurs deja vues. Une
valeur de `display`, de `visibility` ou de `content-visibility` inconnue est
REFUSEE et nommee, au lieu d'etre ignoree. Une garde qui ignore l'inconnu rend
vert ce qu'elle n'a pas su lire.

**Ce qu'il ne sait pas faire, et il faut le lire avant de s'y fier.** Il ne rend
rien. Il attrape la suppression de boite, l'invisibilite, le rognage,
l'effondrement a zero et la couleur totalement transparente. Il n'attrape pas un
element deplace hors ecran par un positionnement, un texte peint de la couleur
du fond, ni un recouvrement par un autre element: ces trois-la demandent une
geometrie calculee.

Ce module n'est pas un fichier de test: `unittest discover` ne le ramasse pas,
son nom ne commence pas par `test`. Il est charge par chemin, pour tenir dans
les deux facons dont ce depot joue ses tests - `discover -s tests` a plat, et
`-m unittest tests.X` en paquet.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web"
STATIQUE = RACINE / "static"
GABARIT = RACINE / "templates" / "base.html"
MANIFESTE = STATIQUE / "styles.css"

COMMENTAIRE_CSS = re.compile(r"/\*.*?\*/", re.DOTALL)
LITTERAL_JS = re.compile(r"\"((?:[^\"\\\n]|\\.)*)\"|'((?:[^'\\\n]|\\.)*)'")


# --------------------------------------------------------------------------
# Lecture du CSS: toutes les regles, a toute profondeur d'at-rules.
# --------------------------------------------------------------------------

def _regles(texte: str):
    """(selecteur, corps, ligne, contexte at-rules) pour chaque regle de style."""
    texte = COMMENTAIRE_CSS.sub(lambda m: "\n" * m.group(0).count("\n"), texte)
    sorties = []

    def marche(debut, fin, contexte):
        i = prelude_debut = debut
        while i < fin:
            if texte[i] == "{":
                prelude = texte[prelude_debut:i].strip()
                prof, j = 1, i + 1
                while j < fin and prof:
                    if texte[j] == "{":
                        prof += 1
                    elif texte[j] == "}":
                        prof -= 1
                    j += 1
                if prelude.startswith("@"):
                    marche(i + 1, j - 1, contexte + (prelude.split("{")[0].strip(),))
                else:
                    sorties.append((prelude, texte[i + 1:j - 1],
                                    texte.count("\n", 0, i) + 1, contexte))
                i = prelude_debut = j
                continue
            if texte[i] == ";":
                i += 1
                prelude_debut = i
                continue
            i += 1

    marche(0, len(texte), ())
    return sorties


def _declarations(corps: str):
    for morceau in corps.split(";"):
        prop, sep, val = morceau.partition(":")
        if not sep:
            continue
        prop = prop.strip().lower()
        if not re.fullmatch(r"-{0,2}[a-z][a-z0-9-]*", prop):
            continue
        yield prop, " ".join(val.split())


def _css_d_un_script(texte: str) -> list[str]:
    """Le CSS qu'un script injecte vit dans ses chaines litterales.

    On rend DEUX lectures, parce qu'aucune seule ne suffit. Chaque chaine est
    lue isolement - `instance_switcher.js` injecte un tableau dont chaque
    element est une regle complete - et la concatenation est lue aussi, pour la
    regle qui serait coupee entre deux elements. Sans la lecture isolee, la
    prose des chaines voisines se colle au selecteur et le rattachement echoue:
    mesure du 2026-09-09, une regle `.cs-topbar-identity{opacity:0}` injectee
    passait inapercue.
    """
    morceaux = [(m.group(1) or m.group(2) or "")
                for m in LITTERAL_JS.finditer(texte)]
    return morceaux + ["\n".join(morceaux)]


def _sources():
    """Les fichiers qui peuvent porter du style, et le manifeste qui les liste.

    Les `@import` portent un marqueur de version (`?v=...`): il fait partie de
    l'URL servie, pas du nom de fichier.

    **Le manifeste est lui-meme une feuille de style servie au navigateur**, et
    la version du 2026-09-09 ne le lisait pas: une regle ecrite sous ses
    `@import` etait appliquee par le navigateur et invisible pour la garde.
    C'est le meme motif que le fragment absent du manifeste, pris par l'autre
    bout. Il est rendu en tete, avant ce qu'il importe, comme le navigateur.
    """
    importes = [STATIQUE / nom.split("?", 1)[0] for nom in
                re.findall(r"@import\s+url\(\"([^\"]+)\"\)",
                           MANIFESTE.read_text(encoding="utf-8"))]
    return importes, sorted(STATIQUE.glob("*.js"))


def _feuilles_a_lire():
    """Tout ce qui est SERVI comme style: le manifeste d'abord, puis ses
    fragments. `_sources` reste separe parce que le test de coincidence
    manifeste/disque compare des listes de fragments, pas des feuilles lues."""
    importes, scripts = _sources()
    return [MANIFESTE] + importes, scripts


# --------------------------------------------------------------------------
# Rattachement d'un selecteur a un noeud de la chaine.
# --------------------------------------------------------------------------

COMPOSE = re.compile(
    r"^(?:\*|[A-Za-z][A-Za-z0-9-]*)?"
    r"(?:[.#][A-Za-z_-][A-Za-z0-9_-]*|\[[^\]]*\]|::?[A-Za-z-]+(?:\(\))?)*$")

#: Compteur des composes que le lecteur n'a pas su analyser. Il n'existe pas
#: pour decorer un rapport: `test_le_lecteur_avoue_ce_qu_il_ne_lit_pas` s'en
#: sert pour prouver que la voie de l'aveu est bien atteinte par du CSS reel.
ILLISIBLES: set[str] = set()


def _aplatit_fonctions(selecteur: str) -> str:
    """Reduire tout `:fonction(...)` a `:fonction()`, IMBRICATIONS COMPRISES.

    Mesure du 2026-09-09, et c'est le defaut qui a laisse passer la
    reintroduction de `RM-2026-0111`: l'ancienne version substituait la
    parenthese la plus INTERNE, en boucle. Sur `:not(:has(.cs-search))` elle
    rendait `:not(:has())` - une forme que `COMPOSE` ne sait pas lire - et le
    selecteur etait alors traite comme *ne visant pas la chaine* au lieu de
    *illisible*. Le depot emploie deja cette forme sur un ANCETRE de
    l'identite (`styles_part_30.css`, `.cs-topbar:not(:has(.cs-search))`).

    On compte les profondeurs et on remplace du niveau 1, ce qui ne depend
    d'aucune liste de pseudo-classes: `:has`, `:is`, `:where`, `:not`, et
    celles qui viendront, passent par le meme chemin.
    """
    sortie, profondeur = [], 0
    for caractere in selecteur:
        if caractere == "(":
            profondeur += 1
            if profondeur == 1:
                sortie.append("()")
            continue
        if caractere == ")":
            if profondeur:
                profondeur -= 1
                continue
        if not profondeur:
            sortie.append(caractere)
    return "".join(sortie)
CLASSE = re.compile(r"\.([A-Za-z_-][A-Za-z0-9_-]*)")
IDENT = re.compile(r"#([A-Za-z_-][A-Za-z0-9_-]*)")
BALISE = re.compile(r"^(\*|[A-Za-z][A-Za-z0-9-]*)")
ATTRIBUT = re.compile(r"\[\s*([A-Za-z_-][A-Za-z0-9_-]*)")


def _compose_matche(compose: str, noeud) -> bool:
    """Ce compose peut-il designer ce noeud ?

    **Un compose que le lecteur ne sait pas analyser rend `True`, pas `False`.**
    C'est le sens de degradation de tout l'instrument, et l'ancienne version le
    trahissait ici: elle rendait `False`, c'est-a-dire *cette regle ne vise pas
    la chaine* - une reponse FAUSSE, rendue EN SILENCE, pour une regle qu'elle
    n'avait pas lue. Rendre `True` fait au pire rougir la garde sur une regle
    inoffensive, ce qui se voit et se discute.
    """
    tag, classes, ident, attributs = noeud
    if not compose:
        return False
    if not COMPOSE.match(compose):
        ILLISIBLES.add(compose)
        return True
    if "::" in compose:
        return False  # un pseudo-element est une boite generee, pas l'element
    if ":root" in compose:
        return tag == "html"
    balise = BALISE.match(compose)
    nom = balise.group(1) if balise else None
    if nom and nom != "*" and nom != tag:
        return False
    if not set(CLASSE.findall(compose)) <= set(classes):
        return False
    ids = set(IDENT.findall(compose))
    if ids and (ident is None or ids != {ident}):
        return False
    if not set(ATTRIBUT.findall(compose)) <= set(attributs):
        return False
    return True


def _vise(selecteur: str, chaine) -> int | None:
    """Index du noeud de `chaine` que ce selecteur peut designer, ou None.

    Sur-attrape a dessein, et de DEUX facons: un combinateur de fratrie ne dit
    rien sur les ancetres, on le franchit sans conclure; et un compose que le
    lecteur ne sait pas analyser est retenu au lieu d'etre ecarte. La garde peut
    donc echouer a tort, jamais reussir a tort - propriete que la version du
    2026-09-09 annoncait sans la tenir, et que
    `test_ui_identite_barre_haute.py` eprouve desormais par mutation.
    """
    plat = _aplatit_fonctions(" ".join(selecteur.split()))
    plat = re.sub(r"\s*([>+~])\s*", r" \1 ", plat)
    morceaux = [m for m in plat.split(" ") if m]
    if not morceaux:
        return None
    for cible in range(len(chaine) - 1, -1, -1):
        if not _compose_matche(morceaux[-1], chaine[cible]):
            continue
        courant, i, tient = cible, len(morceaux) - 2, True
        while i >= 0 and tient:
            jeton = morceaux[i]
            if jeton in "+~":
                i -= 2
                continue
            direct = jeton == ">"
            if direct:
                i -= 1
                if i < 0:
                    break
                jeton = morceaux[i]
            candidats = ([courant - 1] if direct
                         else list(range(courant - 1, -1, -1)))
            place = next((b for b in candidats
                          if b >= 0 and _compose_matche(jeton, chaine[b])), None)
            if place is None:
                tient = False
            else:
                courant = place
            i -= 1
        if tient:
            return cible
    return None


# --------------------------------------------------------------------------
# Le classificateur: cette declaration supprime-t-elle la boite ?
# --------------------------------------------------------------------------

#: Valeurs de `display` qui GENERENT une boite. Tout le reste est refuse, y
#: compris une valeur inconnue: c'est le sens de degradation voulu.
DISPLAY_QUI_GENERE = {
    "block", "inline", "inline-block", "flex", "inline-flex", "grid",
    "inline-grid", "flow", "flow-root", "contents", "list-item", "table",
    "inline-table", "table-row", "table-row-group", "table-header-group",
    "table-footer-group", "table-cell", "table-column", "table-column-group",
    "table-caption", "ruby", "ruby-base", "ruby-text", "math",
    "initial", "unset", "revert", "revert-layer",
}
#: Proprietes de taille dont une valeur NULLE fait disparaitre le contenu.
#: `min-*` en est volontairement absent: un plancher a zero ne supprime rien.
TAILLES_QUI_EFFONDRENT = {
    "width", "height", "max-width", "max-height", "font-size",
    "inline-size", "block-size", "max-inline-size", "max-block-size",
}
COULEURS_DE_TEXTE = {"color", "-webkit-text-fill-color"}
ZERO = re.compile(
    r"^[+-]?0*(?:\.0*)?(?:px|rem|em|%|vh|vw|vmin|vmax|svh|svw|lvh|lvw|dvh|dvw"
    r"|ch|ex|cap|ic|lh|rlh|pt|pc|cm|mm|q|in)?$", re.IGNORECASE)
NOMBRE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)$")


def _sans_important(valeur: str) -> str:
    return re.sub(r"!\s*important\s*$", "", valeur.strip(), flags=re.I).strip()


def _est_zero(valeur: str) -> bool:
    valeur = _sans_important(valeur)
    return bool(valeur) and bool(ZERO.match(valeur)) and any(
        c.isdigit() for c in valeur)


def _alpha_nulle(valeur: str) -> bool:
    """Cette couleur est-elle totalement transparente ?"""
    v = _sans_important(valeur).lower()
    if v == "transparent":
        return True
    if re.fullmatch(r"#[0-9a-f]{4}", v) and v[-1] == "0":
        return True
    if re.fullmatch(r"#[0-9a-f]{8}", v) and v[-2:] == "00":
        return True
    fonction = re.match(r"^(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch)\((.*)\)$", v)
    if fonction:
        arguments = re.split(r"[,/]", fonction.group(1))
        if len(arguments) >= 4:
            dernier = arguments[-1].strip().rstrip("%")
            if NOMBRE.match(dernier) and float(dernier) == 0:
                return True
    return False


def _supprime(propriete: str, valeur: str) -> str | None:
    """Le motif de refus, ou None si cette declaration ne supprime rien.

    Le controle se fait par CATEGORIE D'EFFET et refuse l'inconnu. Une valeur de
    `display` jamais vue fait rougir la garde au lieu de passer.
    """
    net = _sans_important(valeur).lower()
    if propriete == "display":
        jetons = [j for j in net.split() if j]
        if not jetons or any(j not in DISPLAY_QUI_GENERE for j in jetons):
            return "`display: %s` ne genere pas de boite (ou est inconnu)" % net
        return None
    if propriete == "visibility" and net not in {"visible", "initial", "unset",
                                                 "revert", "revert-layer"}:
        return "`visibility: %s` retire l'element de l'affichage" % net
    if propriete == "content-visibility" and net not in {"visible", "initial",
                                                         "unset", "revert"}:
        return "`content-visibility: %s` saute le rendu du contenu" % net
    if propriete == "opacity" and NOMBRE.match(net.rstrip("%")) and \
            float(net.rstrip("%")) == 0:
        return "`opacity: %s` rend l'element invisible" % net
    if propriete in {"clip", "clip-path"} and net not in {"none", "initial",
                                                          "unset", "revert"}:
        return "`%s: %s` rogne l'element (technique `sr-only`)" % (propriete, net)
    if propriete in TAILLES_QUI_EFFONDRENT and _est_zero(net):
        return "`%s: %s` effondre la boite a zero" % (propriete, net)
    if propriete == "scale" and any(_est_zero(j) for j in net.split()):
        return "`scale: %s` reduit l'element a rien" % net
    if propriete == "transform" and re.search(
            r"\bscale[xyz3d]*\(\s*0(?:\.0*)?\s*[,)]", net):
        return "`transform: %s` reduit l'element a rien" % net
    if propriete == "text-indent" and net.startswith("-"):
        return "`text-indent: %s` pousse le texte hors de sa boite" % net
    if propriete in COULEURS_DE_TEXTE and _alpha_nulle(net):
        return "`%s: %s` peint le texte en transparent" % (propriete, net)
    return None


#: Liste BLANCHE, appliquee aux elements d'identite eux-memes: rien d'autre
#: qu'une propriete cosmetique, typographique ou d'espacement n'a de raison de
#: les viser. Une propriete inconnue fait rougir la garde et se discute.
COSMETIQUE = {
    "color", "background", "background-color", "border", "border-color",
    "border-radius", "border-width", "border-style", "border-top",
    "border-right", "border-bottom", "border-left", "box-shadow",
    "padding", "padding-top", "padding-right", "padding-bottom",
    "padding-left", "padding-inline", "padding-block",
    "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
    "margin-inline", "margin-block", "gap", "row-gap", "column-gap",
    "display", "flex-wrap", "flex-direction", "align-items", "justify-content",
    "order", "list-style", "white-space", "overflow-wrap", "word-break",
    "font-family", "font-size", "font-weight", "font-style", "font-variant",
    "letter-spacing", "line-height", "text-transform", "text-decoration",
    "text-align", "min-width", "min-height",
    # Reglages globaux inertes, qui atteignent l'identite par le selecteur `*`.
    "box-sizing", "-webkit-font-smoothing", "text-rendering",
}

