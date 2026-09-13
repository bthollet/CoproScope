# -*- coding: utf-8 -*-
"""L'identite de ce qu'on regarde ne se sacrifie pas a la place disponible.

**Le defaut, mesure sur le commit `ffac60c`.** `styles_part_05.css:462` portait,
dans `@media (max-width: 1280px)`, la regle `.cs-topbar .instance-meta {
display: none }`. Ce conteneur portait `Coffre <id>` et `Exercice <annee>`: sous
1281 px de fenetre, l'ecran continuait donc d'afficher des chiffres en cessant
de dire DE QUI ils etaient. C'est le defaut de veracite de `RM-2026-0078` et
`RM-2026-0087` obtenu par disparition au lieu de fabrication, et le seuil n'a
rien d'exotique - une fenetre munie d'une barre laterale d'assistant y passe
sans que l'utilisateur fasse quoi que ce soit.

**L'axe, et non la modalite.** Ce qui varie est la largeur, le gabarit, le
nombre d'elements de la barre. Ce qui reste vrai le long de cet axe:
*l'identite est le DERNIER element qu'on retire, jamais le premier.* Le
correctif dit cela en structure - l'identite quitte le conteneur d'actions et
rejoint le bloc de titre, qu'aucun palier ne masque - et la barre se REPLIE au
lieu de supprimer du contenu.

**Cette garde ne cherche pas une chaine de caracteres.** Elle reconstruit depuis
`base.html` la chaine d'ancetres reelle des elements marques
`data-cs-identite`, puis relit TOUTES les feuilles, a toute profondeur
d'at-rules - `@media`, `@supports`, `@container`, ce qui viendra - et refuse
toute declaration qui supprimerait la boite d'un de ces noeuds. Renommer une
classe, changer le seuil, passer a `@container` ou ecrire la regle dans un autre
fragment ne l'esquive pas: la chaine est relue depuis le gabarit a chaque
passage. Elle lit aussi le manifeste `styles.css`, les attributs `style=` et
`hidden` du gabarit, et juge CHAQUE sous-arbre marque - trois elargissements du
2026-09-09 dont la raison est plus bas.

**Sens de degradation, qui est le point de la regle des axes.** Le controle des
proprietes de suppression est fait par CATEGORIE d'effet, pas par liste de
valeurs vues: une valeur inconnue de `display`, de `visibility` ou de
`content-visibility` est REFUSEE, pas ignoree. Sur les elements d'identite
eux-memes le controle est en plus une liste BLANCHE de proprietes: une propriete
inconnue arrivant demain fait rougir la garde en la nommant, au lieu de passer
en silence. C'est le seul sens de degradation acceptable ici.

**Ce que cette garde NE prouve PAS, et il faut le lire avant de s'y fier.**

1. *Elle ne rend rien.* La suite n'a aucun moteur de rendu - zero `playwright`,
   `selenium`, `puppeteer` - donc aucune requete de media n'est evaluee par
   personne. Cette garde lit le CSS et le gabarit. **Une mesure sur la source
   n'est pas une recette:** que l'identite reste LISIBLE a 420 px, qu'elle ne
   soit pas recouverte, tronquee ou repoussee hors du premier viewport demande
   un oeil devant une fenetre. Ce lot ne l'a pas fait.
2. *Elle ne voit pas toutes les manieres de rendre un texte imperceptible.*
   Elle attrape la suppression de boite, l'invisibilite, le rognage,
   l'effondrement a zero et la couleur totalement transparente. Elle n'attrape
   PAS un ancetre deplace hors ecran (`position: absolute; left: -9999px`), ni
   un texte peint de la couleur du fond, ni un recouvrement par un autre
   element. Ces trois-la demandent une geometrie calculee.
3. *Le rattachement selecteur -> noeud sur-attrape volontairement.* Un selecteur
   dont la partie ancetre est indecidable (combinateurs de fratrie) est retenu
   plutot qu'ecarte. Elle peut donc echouer a tort, jamais reussir a tort.

**Population lue, pour distinguer `rien a signaler` de `la garde ne lit plus
rien`.** Mesure du 2026-09-09 apres refutation, base `177945d`: 38 fichiers -
le manifeste `styles.css`, les 34 fragments qu'il importe et 3 scripts -, 1694
regles de style, 75 declarations retombant sur la chaine d'identite, 0
infraction. Le plancher anti-mutisme porte donc sur l'INSTRUMENT et non sur ses
infractions, qui sont zero: sinon un vert ne distinguerait pas *rien a
signaler* de *la garde ne lit plus rien*. La chaine reconstruite est `html >
body.cs-shell > div.cs-app-shell > div.cs-workspace > header.cs-topbar.topbar >
div.cs-topbar-title > div.cs-topbar-identity > span`.

**CORRECTION DU 2026-09-09, et elle porte sur ce que cet en-tete affirmait.**
La premiere version de ce fichier ecrivait *37 fichiers*, *74 declarations*, et
plus haut *elle peut donc echouer a tort, jamais reussir a tort*. Les trois
etaient faux ensemble, et pour une seule cause. Le lecteur reduisait
`:fonction(...)` en substituant la parenthese la plus INTERNE: sur
`:not(:has(.cs-search))` il obtenait `:not(:has())`, forme qu'il ne sait pas
analyser, et il repondait alors *cette regle ne vise pas la chaine* au lieu de
*je n'ai pas su lire*. La 75e declaration manquante etait exactement celle de
`.cs-topbar:not(:has(.cs-search))`, dans `styles_part_30.css`, sur un ANCETRE de
l'identite. Consequence mesuree: le defaut de `RM-2026-0111` remis a l'identique
sous cette forme de selecteur laissait les DIX tests verts. Le 38e fichier est
le manifeste lui-meme, qui est servi au navigateur et n'etait pas lu.
**Les onze morsures annoncees mordaient reellement** - verifie une par une - et
c'est le point a retenir: une garde peut mordre onze fois et laisser passer la
douzieme, parce que les onze formes essayees avaient toutes ete choisies par
celui qui avait ecrit le lecteur. Les formes qu'il n'a pas imaginees sont
precisement celles que son lecteur ne lit pas. C'est pourquoi les garanties du
LECTEUR sont desormais gardees a part, dans
`test_ui_identite_lecteur_de_style.py`, et par mutation de ce fichier-ci.

**Morsure eprouvee, onze fois, le 2026-09-09.** Chaque forme a ete reintroduite
dans l'arbre puis retiree; les onze rendent ROUGE: (a) l'identite masquee sous
un palier de largeur, (b) un ANCETRE en `visibility: hidden`, (c) un
`@container` avec `max-height: 0`, (d) une regle injectee depuis une chaine de
script, (e) la technique `sr-only` par `clip-path`, (f) une valeur de `display`
INCONNUE, (g) le texte peint en `rgba(0,0,0,0)`, (h) l'identite devenue une
constante, (i) l'identite enveloppee dans un `{% block %}`, (j) la marque
retiree du gabarit, (k) le conteneur RENOMME puis masque sous son nouveau nom -
ce dernier cas prouve que la chaine est relue depuis `base.html` et non codee
ici. Renommer seul reste vert, et c'est correct: un renommage ne cache rien.
"""

from __future__ import annotations

import importlib.util
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

# L'instrument de lecture du style vit a cote, dans `_lecture_style_coque.py`.
# Il est charge PAR CHEMIN et non par `import`: ce depot joue ses tests de deux
# facons - `discover -s tests` a plat, et `-m unittest tests.X` en paquet - et
# aucune forme d'import ordinaire ne tient dans les deux. Un module qui passe
# seul pendant que la suite casse est le piege nomme dans `CLAUDE.md`.
_specification = importlib.util.spec_from_file_location(
    "coproscope_tests_lecture_style_coque",
    Path(__file__).resolve().with_name("_lecture_style_coque.py"))
lecture = importlib.util.module_from_spec(_specification)
_specification.loader.exec_module(lecture)

GABARIT = lecture.GABARIT
STATIQUE = lecture.STATIQUE
COSMETIQUE = lecture.COSMETIQUE

#: L'attribut qui declare qu'un element porte l'identite de ce qui est montre.
MARQUE = "data-cs-identite"
#: Les roles qui doivent etre presents. Un ecran qui montre des chiffres dit de
#: quelle copropriete et de quel exercice ils sont.
ROLES_ATTENDUS = {"copropriete", "exercice"}

VIDES = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
         "meta", "param", "source", "track", "wbr"}
JINJA = re.compile(r"\{%.*?%\}|\{#.*?#\}", re.DOTALL)
COMMENTAIRE_JINJA = re.compile(r"\{#.*?#\}", re.DOTALL)
JINJA_BLOC = re.compile(r"\{%-?\s*(end)?block\b", re.DOTALL)


# --------------------------------------------------------------------------
# Lecture du gabarit: la chaine d'ancetres, reconstruite et non supposee.
# --------------------------------------------------------------------------

class _Arbre(HTMLParser):
    """Empile les balises ouvertes et retient la pile aux elements marques."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pile: list[tuple[str, frozenset[str], str | None, frozenset[str]]] = []
        #: Les VALEURS d'attributs, parallelement a la pile: un `style=` ou un
        #: `hidden` pose dans le gabarit cache l'identite sans qu'aucune feuille
        #: ne bouge, et la version du 2026-09-09 ne les regardait pas.
        self.valeurs: list[dict] = []
        self.trouves: list[tuple[list, list, str, int]] = []

    def _noeud(self, tag, attrs):
        att = {nom.lower(): (val or "") for nom, val in attrs}
        classes = frozenset(
            c for c in att.get("class", "").split()
            if re.fullmatch(r"[A-Za-z_-][A-Za-z0-9_-]*", c))
        return (tag.lower(), classes, att.get("id") or None,
                frozenset(att), att)

    def handle_starttag(self, tag, attrs):
        tag, classes, ident, noms, att = self._noeud(tag, attrs)
        noeud = (tag, classes, ident, noms)
        if tag in VIDES:
            self._peut_etre_marque(noeud, att)
            return
        self.pile.append(noeud)
        self.valeurs.append(att)
        self._peut_etre_marque(noeud, att)

    def handle_startendtag(self, tag, attrs):
        tag, classes, ident, noms, att = self._noeud(tag, attrs)
        self._peut_etre_marque((tag, classes, ident, noms), att)

    def handle_endtag(self, tag):
        tag = tag.lower()
        for i in range(len(self.pile) - 1, -1, -1):
            if self.pile[i][0] == tag:
                del self.pile[i:]
                del self.valeurs[i:]
                return

    def _peut_etre_marque(self, noeud, att):
        if MARQUE in att:
            chaine, valeurs = list(self.pile), list(self.valeurs)
            if chaine and chaine[-1] is not noeud:
                chaine.append(noeud)
                valeurs.append(att)
            elif not chaine:
                chaine, valeurs = [noeud], [att]
            self.trouves.append(
                (chaine, valeurs, att[MARQUE].strip(), self.getpos()[0]))


def _sans_jinja(texte: str) -> str:
    """Retire les instructions Jinja; garde les `{{ ... }}` comme du texte."""
    return JINJA.sub("", texte)


def _identites():
    """(chaines d'ancetres, roles, lignes) des elements marques dans base.html."""
    arbre = _Arbre()
    arbre.feed(_sans_jinja(GABARIT.read_text(encoding="utf-8")))
    return arbre.trouves


def _chaine_unique(trouves):
    """La chaine la plus longue: elle sert aux messages et aux plausibilites.

    **Elle ne sert plus a choisir ce qui est protege.** La version du
    2026-09-09 ne gardait qu'elle, en supposant que *tous les marques sont
    freres ici*. C'est une modalite: le jour ou un role d'identite est pose
    dans un autre sous-arbre - ce que le gabarit n'interdit pas - sa chaine
    n'etait plus regardee, et une regle qui l'aurait masquee passait en
    silence. `_chaines()` rend desormais TOUTES les chaines distinctes.
    """
    if not trouves:
        return []
    return max((c for c, _, _, _ in trouves), key=len)


def _chaines(trouves):
    """Toutes les chaines d'ancetres distinctes, sans doublon, avec valeurs."""
    vues, sorties = set(), []
    for chaine, valeurs, _, _ in trouves:
        cle = tuple((n[0], n[1], n[2]) for n in chaine)
        if cle in vues:
            continue
        vues.add(cle)
        sorties.append((chaine, valeurs))
    return sorties



def _fautes_du_gabarit(chaine, valeurs):
    """Ce que le GABARIT cache lui-meme, sans qu'aucune feuille ne bouge.

    Deux formes, toutes deux passees sous la garde du 2026-09-09 qui ne lisait
    que du CSS: `style="display: none"` pose sur un noeud de la chaine, et
    l'attribut HTML `hidden`, dont la feuille par defaut du navigateur fait un
    `display: none`. Une garde qui protege l'identite contre les feuilles mais
    pas contre le gabarit ne protege pas l'identite.
    """
    fautes = []
    for noeud, att in zip(chaine, valeurs):
        nom = "%s%s" % (noeud[0], "".join("." + c for c in sorted(noeud[1])))
        if "hidden" in att:
            fautes.append("base.html  %s  ->  l'attribut HTML `hidden` retire "
                          "l'element de l'affichage" % nom)
        for propriete, valeur in lecture._declarations(att.get("style", "")):
            motif = lecture._supprime(propriete, valeur)
            if motif:
                fautes.append("base.html  %s  style=  ->  %s" % (nom, motif))
    return fautes


def _depart_identite(chaine):
    """Index a partir duquel la liste BLANCHE de proprietes s'applique."""
    depart = len(chaine) - 1
    for i, noeud in enumerate(chaine):
        if MARQUE in noeud[3] or "cs-topbar-identity" in noeud[1]:
            depart = min(depart, i)
    return depart


def _juge(fichier, un, corps, ligne, contexte, cible, depart, fautes):
    """Range dans `fautes` ce que cette regle fait de mal a ce noeud."""
    for propriete, valeur in lecture._declarations(corps):
        if propriete.startswith("--"):
            continue
        motif = lecture._supprime(propriete, valeur)
        if motif is None and cible >= depart and propriete not in COSMETIQUE:
            motif = ("`%s` n'est pas une propriete cosmetique; sur un element "
                     "d'identite elle se discute" % propriete)
        if not motif:
            continue
        # Le numero de ligne n'a de sens que pour une feuille lue entiere:
        # dans un script, la regle est relue chaine par chaine.
        repere = ("%s:%d" % (fichier.name, ligne) if fichier.suffix == ".css"
                  else "%s (chaine injectee)" % fichier.name)
        fautes.add("%s  %s%s  ->  %s"
                   % (repere, (" ".join(contexte) + "  ") if contexte else "",
                      un[:80], motif))


def _infractions():
    """Toutes les declarations refusees, sur TOUTES les chaines d'identite.

    Trois elargissements du 2026-09-09, chacun ferme un trou par lequel le
    defaut de `RM-2026-0111` rentrait sans faire rougir la garde: on lit le
    manifeste `styles.css` lui-meme et pas seulement ce qu'il importe; on juge
    CHAQUE chaine marquee et pas seulement la plus longue; et on regarde les
    attributs du gabarit en plus des feuilles.
    """
    trouves = _identites()
    chaines = _chaines(trouves)
    departs = [_depart_identite(une) for une, _ in chaines]

    fautes, lues, retenues = set(), 0, 0
    for une, valeurs in chaines:
        fautes.update(_fautes_du_gabarit(une, valeurs))
    feuilles, scripts = lecture._feuilles_a_lire()
    for fichier in feuilles + scripts:
        brut = fichier.read_text(encoding="utf-8")
        lectures = (lecture._css_d_un_script(brut)
                    if fichier.suffix == ".js" else [brut])
        for texte in lectures:
            for selecteur, corps, ligne, contexte in lecture._regles(texte):
                lues += 1
                for un in selecteur.split(","):
                    un = " ".join(un.split())
                    if not un or un.startswith("@"):
                        continue
                    for (une, _), depart in zip(chaines, departs):
                        cible = lecture._vise(un, une)
                        if cible is None:
                            continue
                        retenues += sum(
                            1 for propriete, _ in lecture._declarations(corps)
                            if not propriete.startswith("--"))
                        _juge(fichier, un, corps, ligne, contexte, cible,
                              depart, fautes)
    return (sorted(fautes), _chaine_unique(trouves), lues, retenues,
            len(feuilles) + len(scripts))



class LIdentiteEstDeclareeDansLeGabaritTests(unittest.TestCase):
    """Sans marque, la garde suivante n'aurait rien a proteger."""

    def test_les_deux_roles_d_identite_sont_presents(self) -> None:
        roles = {role for _, _, role, _ in _identites()}
        manquants = ROLES_ATTENDUS - roles
        self.assertFalse(
            manquants,
            "\n\n  `base.html` ne declare plus l'identite de ce qu'il affiche.\n"
            "  roles manquants: %s\n"
            "  Un ecran qui montre des chiffres dit de quelle copropriete et de\n"
            "  quel exercice ils sont (`RM-2026-0111`, `RM-2026-0078`).\n"
            "  Marque attendue sur l'element porteur: %s=\"<role>\".\n"
            % (sorted(manquants), MARQUE))

    def test_l_identite_vient_de_l_instance_et_non_d_une_constante(self) -> None:
        texte = GABARIT.read_text(encoding="utf-8")
        for role in sorted(ROLES_ATTENDUS):
            motif = re.search(
                r"%s=\"%s\"[^>]*>(?P<contenu>.*?)</" % (MARQUE, role),
                texte, re.DOTALL)
            self.assertIsNotNone(motif, "role %s introuvable" % role)
            contenu = motif.group("contenu")
            self.assertRegex(
                contenu, r"\{\{[^}]*\binstance\b",
                "\n\n  Le role `%s` n'interpole plus `instance`: son libelle est\n"
                "  devenu une constante. Un nom fixe au-dessus de chiffres reels\n"
                "  est le defaut de `RM-2026-0087`, pas une identite.\n"
                "  trouve: %r\n" % (role, contenu.strip()))

    def test_l_identite_n_est_dans_aucun_bloc_surchargeable(self) -> None:
        """Une page ne doit pas pouvoir remplacer l'identite par autre chose."""
        # Les commentaires Jinja partent d'abord: l'un d'eux cite `{% block %}`
        # en prose, et le compter serait mesurer sa propre documentation.
        texte = COMMENTAIRE_JINJA.sub(
            lambda m: "\n" * m.group(0).count("\n"),
            GABARIT.read_text(encoding="utf-8"))
        position = texte.index(MARQUE)
        ouverts = 0
        for marque in JINJA_BLOC.finditer(texte, 0, position):
            ouverts += -1 if marque.group(1) else 1
        self.assertEqual(
            ouverts, 0,
            "\n\n  L'identite est ecrite a l'interieur d'un `{%% block %%}`.\n"
            "  Une page enfant peut alors la remplacer ou la faire disparaitre\n"
            "  sans qu'aucun test ne le voie. Sortez-la du bloc.\n")

    def test_la_chaine_reconstruite_est_plausible(self) -> None:
        chaine = _chaine_unique(_identites())
        balises = [n[0] for n in chaine]
        classes = set().union(*[set(n[1]) for n in chaine]) if chaine else set()
        self.assertGreaterEqual(
            len(chaine), 5,
            "chaine d'ancetres trop courte, le gabarit n'a pas ete lu: %s"
            % balises)
        self.assertEqual(balises[:2], ["html", "body"], balises)
        self.assertIn(
            "cs-topbar", classes,
            "\n\n  L'identite n'est plus dans la barre haute. Ce n'est pas\n"
            "  forcement une faute, mais la garde a ete ecrite pour elle:\n"
            "  relisez-la avant de la faire passer.\n  chaine lue: %s\n"
            % (balises,))


class AucuneRegleNeSupprimeLIdentiteTests(unittest.TestCase):
    def test_aucune_feuille_ne_masque_l_identite_a_aucune_largeur(self) -> None:
        fautes, chaine, _, _, _ = _infractions()
        self.assertEqual(
            fautes, [],
            "\n\n  Une regle de style supprime l'identite de la copropriete, ou\n"
            "  l'un de ses ancetres, a une largeur donnee. C'est le defaut de\n"
            "  `RM-2026-0111`: l'ecran montre des chiffres sans dire de qui.\n"
            "  L'identite est le DERNIER element qu'on retire, pas le premier:\n"
            "  repliez la barre au lieu d'en supprimer un morceau.\n\n    "
            + "\n    ".join(fautes)
            + "\n\n  chaine protegee: "
            + " > ".join("%s%s" % (n[0], "".join("." + c for c in sorted(n[1])))
                         for n in chaine) + "\n")


class LInstrumentLitVraimentQuelqueChoseTests(unittest.TestCase):
    """Un compteur faux produit un chiffre qui a l'air d'une preuve."""

    def test_toutes_les_feuilles_du_manifeste_sont_lues(self) -> None:
        importes, scripts = lecture._sources()
        sur_disque = set(STATIQUE.glob("styles_part_*.css"))
        self.assertEqual(
            set(importes), sur_disque,
            "\n\n  Le manifeste `styles.css` et les fragments sur disque ne\n"
            "  coincident plus. Un fragment non importe n'est pas servi; un\n"
            "  fragment servi mais non liste ici echapperait a la garde.\n"
            "  seulement dans le manifeste: %s\n"
            "  seulement sur disque: %s\n"
            % (sorted(p.name for p in set(importes) - sur_disque),
               sorted(p.name for p in sur_disque - set(importes))))
        self.assertGreaterEqual(len(scripts), 1)

    def test_l_instrument_a_lu_des_regles_et_touche_la_chaine(self) -> None:
        _, chaine, lues, retenues, fichiers = _infractions()
        self.assertGreaterEqual(fichiers, 30, "trop peu de fichiers lus")
        self.assertGreaterEqual(lues, 800, "trop peu de regles lues: %d" % lues)
        self.assertGreaterEqual(
            retenues, 40,
            "\n\n  L'instrument ne retombe presque plus sur la chaine\n"
            "  d'identite (%d declarations). Soit le gabarit a change, soit le\n"
            "  rattachement selecteur -> noeud est casse. Un vert obtenu ainsi\n"
            "  ne veut rien dire.\n" % retenues)
        self.assertGreaterEqual(len(chaine), 5)


class LeClassificateurMordTests(unittest.TestCase):
    """Chaque categorie de refus est eprouvee sur une valeur fabriquee.

    Sans ce test, un classificateur qui rendrait `None` pour tout laisserait la
    garde precedente verte pour toujours.
    """

    REFUSES = [
        ("display", "none"),
        ("display", "inherit"),
        ("display", "quelque-chose-de-neuf"),
        ("visibility", "hidden"),
        ("visibility", "collapse"),
        ("content-visibility", "hidden"),
        ("opacity", "0"),
        ("opacity", "0.0"),
        ("clip-path", "inset(50%)"),
        ("clip", "rect(0, 0, 0, 0)"),
        ("width", "0"),
        ("max-height", "0px"),
        ("font-size", "0"),
        ("max-inline-size", "0%"),
        ("transform", "scale(0)"),
        ("scale", "0"),
        ("text-indent", "-9999px"),
        ("color", "transparent"),
        ("color", "rgba(0, 0, 0, 0)"),
        ("color", "#00000000"),
        ("display", "none !important"),
    ]

    ACCEPTES = [
        ("display", "grid"),
        ("display", "flex"),
        ("display", "contents"),
        ("visibility", "visible"),
        ("opacity", "0.85"),
        ("width", "100%"),
        ("min-height", "0"),
        ("min-width", "0"),
        ("max-width", "100vw"),
        ("font-size", "11px"),
        ("transform", "scale(1.02)"),
        ("text-indent", "4px"),
        ("color", "#475467"),
        ("color", "rgba(16, 24, 40, .8)"),
        ("clip-path", "none"),
    ]

    def test_chaque_categorie_de_suppression_est_refusee(self) -> None:
        muets = [(p, v) for p, v in self.REFUSES if lecture._supprime(p, v) is None]
        self.assertEqual(
            muets, [],
            "\n\n  Le classificateur ne reconnait plus ces suppressions. La\n"
            "  garde d'identite serait alors verte sans rien mesurer.\n    %s\n"
            % muets)

    def test_le_style_legitime_n_est_pas_refuse(self) -> None:
        faux = [(p, v, lecture._supprime(p, v)) for p, v in self.ACCEPTES
                if lecture._supprime(p, v) is not None]
        self.assertEqual(faux, [], "refus a tort: %s" % (faux,))

    def test_le_rattachement_distingue_la_chaine_du_reste(self) -> None:
        chaine = _chaine_unique(_identites())
        self.assertIsNotNone(
            lecture._vise(".cs-topbar", chaine), "la barre haute est un ancetre")
        self.assertIsNotNone(
            lecture._vise("body", chaine), "le corps est un ancetre")
        self.assertIsNone(
            lecture._vise(".cs-sidebar .nav a", chaine),
            "un selecteur etranger a la chaine ne doit pas etre retenu")
        self.assertIsNone(
            lecture._vise(".cs-topbar::before", chaine),
            "un pseudo-element est une boite generee, pas l'element")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
