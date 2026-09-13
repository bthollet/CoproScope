# -*- coding: utf-8 -*-
"""Deux etats de franchissement differents ne se rendent pas pareil a l'ecran.

`RM-2026-0118`. Brice, devant le mur de controle: *« le code couleur, je ne
comprends pas du tout son sens »*. Le test d'acceptation que le `CLAUDE.md`
pose pour toute valeur affichee: **deux etats differents du dossier
peuvent-ils produire le meme affichage, sans qu'on puisse remonter de
l'affichage aux etats ?**

----------------------------------------------------------------------
La mesure, et elle refute la garde de la veille
----------------------------------------------------------------------

`test_la_couleur_n_encode_qu_une_dimension.py` concluait que le franchissement
etait porte **en forme** - *un bord en tirets pour `non_comparable`, un bord
epaissi pour `franchi`*. Le calcul de la cascade dit autre chose:

    .cs-bulle                                        border-left: 4px solid ...
    .cs-bulle[data-franchissement="franchi"]         border-left-width: 4px
    .cs-bulle[data-franchissement="non_comparable"]  border-style: dashed

La regle qui devait *epaissir* le bord d'une bulle franchie pose **4 px, la
largeur que le socle lui donne deja**. Elle ne change rien. Une bulle FRANCHIE,
une bulle NON FRANCHIE et une bulle SANS comparaison sont rendues identiques:
le lecteur ne peut pas voir si le seuil est depasse. Seul `non_comparable` se
distingue.

**Pourquoi la garde de la veille n'a rien vu - deux trous, tous deux mesures:**

1. elle decouvrait les valeurs de franchissement DANS LA FEUILLE DE STYLE, donc
   `non_franchi`, qui n'a aucune regle, n'etait jamais examine - alors que sa
   propre docstring dit qu'*une valeur sans marqueur est un etat que le lecteur
   ne peut pas distinguer*;
2. elle comptait la PRESENCE d'une declaration de forme, et le `4px` de
   `franchi` comptait comme marqueur. Une declaration presente n'est pas une
   difference visible.

----------------------------------------------------------------------
Ce que cette garde mesure, et d'ou vient sa portee
----------------------------------------------------------------------

- **Les etats viennent du PRODUCTEUR**: les constantes exportees par
  `_controle_gouvernance_franchissement`, mises en minuscules comme le gabarit
  les rend, plus l'etat ou l'attribut est ABSENT - le gabarit ne le pose que
  sous condition.
- **Les statuts viennent du vocabulaire** (`STATUTS_BULLE`): la propriete doit
  tenir quel que soit le statut de la piece.
- **Les largeurs viennent de la feuille**: chaque `@media (max-width: N)` qu'elle
  declare, plus une largeur au-dessus de toutes.
- **L'apparence est CALCULEE**: selecteurs appliques a l'element que le gabarit
  produit, tries par specificite puis par ordre du document, raccourcis `border`
  et `border-left` developpes. On compare des valeurs, pas des presences.

**Hors portee, et declare.** Les selecteurs a combinateur ou pseudo-classe -
`.cs-bulle b`, `.cs-bulle-statut`, un `::before` - ne sont pas evalues: un
marqueur pose sur un DESCENDANT ne serait pas vu, et la garde conclurait alors a
tort a deux etats indistincts. C'est une fausse alerte, pas une fausse
tranquillite, et un temoin compte ces selecteurs ecartes. `!important` n'est
pas traite: aucune regle de la bulle ne l'emploie aujourd'hui.

**Ce qu'elle ne tranche pas.** Comment une bulle franchie DOIT se voir est une
decision d'ecran - visuel, blueprint et GO du novice avant tout code. La garde
ne change aucune feuille: elle borne le defaut en dette nommee, et le jour ou
un marqueur visible est pose, la dette doit etre retiree.
"""
from __future__ import annotations

import importlib.util
import itertools
import re
import unittest
from pathlib import Path

from coproscope.web import _controle_gouvernance_franchissement as FR
from coproscope.web._controle_gouvernance_vocabulaire import STATUTS_BULLE

_SPEC = importlib.util.spec_from_file_location(
    "coproscope_tests_media_css_franchissement",
    Path(__file__).resolve().with_name("_media_css.py"))
_MEDIA = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MEDIA)

ABSENT = "(attribut absent)"
BULLE = "cs-bulle"

#: Les paires d'etats INDISTINCTES au 2026-09-12, mesurees par la cascade.
#: Egalite d'ensembles: une paire nouvelle echoue, une paire devenue distincte
#: qui reste ici echoue aussi. Les deux premieres sont le DEFAUT - un seuil
#: depasse ne se voit pas; la troisieme est une question d'ecran ouverte: un
#: seuil non depasse et une bulle sans comparaison peuvent-ils se ressembler ?
DETTE_2026_09_12: frozenset[frozenset[str]] = frozenset({
    frozenset({"franchi", "non_franchi"}),
    frozenset({"franchi", ABSENT}),
    frozenset({"non_franchi", ABSENT}),
})

_STYLES_DE_BORD = {"none", "hidden", "dotted", "dashed", "solid", "double",
                   "groove", "ridge", "inset", "outset"}
_LARGEUR = re.compile(r"^(?:\d*\.?\d+(?:px|em|rem)|0|thin|medium|thick)$")
_COTES = ("top", "right", "bottom", "left")


def etats_du_producteur() -> list[str]:
    """Les etats que le code PRODUIT, pas ceux que la feuille style."""
    valeurs = [getattr(FR, nom) for nom in FR.__all__]
    etats = sorted({v.lower() for v in valeurs if isinstance(v, str) and v.isupper()})
    return etats + [ABSENT]


def largeurs(css: str) -> list[int]:
    """Chaque largeur de media declaree, plus une au-dessus de toutes."""
    bornes = {int(n) for n in re.findall(r"@media\s*\(\s*max-width:\s*(\d+)px", css)}
    return sorted(bornes) + [max(bornes | {1440}) + 1]


def _composee(selecteur: str):
    """(classes, attributs, specificite) d'un selecteur COMPOSE simple, ou None.

    Un combinateur, une pseudo-classe ou un nom de balise sortent de la portee.
    """
    if re.search(r"[\s>+~:]", selecteur):
        return None
    classes = set(re.findall(r"\.([\w-]+)", selecteur))
    attributs = dict(re.findall(r'\[([\w-]+)="([^"]*)"\]', selecteur))
    reste = re.sub(r'\.[\w-]+|\[[\w-]+="[^"]*"\]', "", selecteur)
    if reste.strip():
        return None
    return classes, attributs, len(classes) + len(attributs)


def _developpe(propriete: str, valeur: str) -> dict[str, str]:
    """Les longhands d'une declaration; les raccourcis de bord sont developpes."""
    jetons = valeur.split()
    if propriete in ("border",) or re.fullmatch(r"border-(top|right|bottom|left)", propriete):
        cotes = _COTES if propriete == "border" else (propriete.split("-")[1],)
        largeur = next((j for j in jetons if _LARGEUR.match(j)), "medium")
        style = next((j for j in jetons if j in _STYLES_DE_BORD), "none")
        couleur = " ".join(j for j in jetons if j != largeur and j != style) or "currentcolor"
        sortie = {}
        for cote in cotes:
            sortie.update({"border-%s-width" % cote: largeur,
                           "border-%s-style" % cote: style,
                           "border-%s-color" % cote: couleur})
        return sortie
    m = re.fullmatch(r"border-(width|style|color)", propriete)
    if m and len(jetons) == 1:
        return {"border-%s-%s" % (cote, m.group(1)): valeur for cote in _COTES}
    if propriete == "background" and len(jetons) == 1:
        return {"background-color": valeur}
    return {propriete: valeur}


def apparence(css: str, largeur: int, statut: str, etat: str) -> dict[str, str]:
    """Les valeurs calculees sur la bulle que le gabarit produit pour cet etat."""
    classes = {BULLE, "is-" + statut}
    attributs = {} if etat == ABSENT else {"data-franchissement": etat}
    applicables = []
    for ordre, (selecteur, corps) in enumerate(_MEDIA.regles(css, largeur)):
        forme = _composee(selecteur)
        if forme is None:
            continue
        sel_classes, sel_attributs, specificite = forme
        if sel_classes <= classes and all(attributs.get(k) == v for k, v in sel_attributs.items()):
            applicables.append((specificite, ordre, corps))
    calcule: dict[str, str] = {}
    for _, _, corps in sorted(applicables):
        for declaration in corps.split(";"):
            if ":" not in declaration:
                continue
            nom, valeur = declaration.split(":", 1)
            calcule.update(_developpe(nom.strip().lower(), " ".join(valeur.split())))
    return calcule


def paires_indistinctes(css: str) -> dict[frozenset[str], list[str]]:
    """Chaque paire d'etats rendue identiquement, avec ou elle l'est."""
    trouvees: dict[frozenset[str], list[str]] = {}
    for largeur in largeurs(css):
        for statut in sorted(STATUTS_BULLE):
            rendus = {e: apparence(css, largeur, statut, e) for e in etats_du_producteur()}
            for a, b in itertools.combinations(sorted(rendus), 2):
                if rendus[a] == rendus[b]:
                    trouvees.setdefault(frozenset({a, b}), []).append(
                        "%s a %d px" % (statut, largeur))
    return trouvees


class DEUX_ETATS_NE_SE_RENDENT_PAS_PAREIL(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.css = _MEDIA.feuilles()
        cls.indistinctes = paires_indistinctes(cls.css)

    def test_aucune_paire_NOUVELLE_ne_se_rend_pareil(self) -> None:
        nouvelles = {tuple(sorted(p)): ou[:3] for p, ou in self.indistinctes.items()
                     if p not in DETTE_2026_09_12}
        self.assertEqual(
            {}, nouvelles,
            "deux etats de franchissement sont rendus identiquement: le lecteur "
            "ne peut pas remonter de la bulle a l'etat. %r" % nouvelles)

    def test_la_dette_ne_porte_pas_de_paire_devenue_DISTINCTE(self) -> None:
        devenues = sorted(tuple(sorted(p)) for p in DETTE_2026_09_12
                          if p not in self.indistinctes)
        self.assertEqual(
            [], devenues,
            "ces paires se distinguent desormais a l'ecran: les retirer de la "
            "dette, et le dire au gouvernail: %r" % devenues)


class LES_TEMOINS_QUI_FONT_DE_CECI_UN_CALCUL_ET_NON_UN_COMPTE(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.css = _MEDIA.feuilles()

    def test_les_etats_viennent_du_PRODUCTEUR_et_incluent_celui_sans_regle(self) -> None:
        """`non_franchi` n'a aucune regle: une decouverte par la feuille le rate."""
        etats = etats_du_producteur()
        for attendu in ("franchi", "non_franchi", "non_comparable", ABSENT):
            self.assertIn(attendu, etats)

    def test_CAS_CONNU_non_comparable_se_distingue(self) -> None:
        """Sans cette difference reelle vue, un instrument aveugle passerait."""
        haut = largeurs(self.css)[-1]
        tirets = apparence(self.css, haut, "disponible", "non_comparable")
        socle = apparence(self.css, haut, "disponible", ABSENT)
        self.assertEqual("dashed", tirets.get("border-left-style"))
        self.assertNotEqual(tirets, socle)

    def test_CAS_CONNU_le_bord_de_franchi_vaut_celui_du_socle(self) -> None:
        """Le defaut lui-meme, en valeurs: une regle presente, aucun effet."""
        haut = largeurs(self.css)[-1]
        franchi = apparence(self.css, haut, "disponible", "franchi")
        socle = apparence(self.css, haut, "disponible", ABSENT)
        self.assertEqual(socle.get("border-left-width"), franchi.get("border-left-width"))
        self.assertTrue(socle.get("border-left-width"), "largeur du bord non calculee")

    def test_des_regles_de_la_bulle_sont_bien_lues(self) -> None:
        haut = largeurs(self.css)[-1]
        self.assertGreaterEqual(len(apparence(self.css, haut, "disponible", ABSENT)), 6)

    def test_la_portee_ecartee_est_COMPTEE(self) -> None:
        """Les descendants et pseudo-elements existent: le residu n'est pas vide."""
        ecartes = [s for s, _ in _MEDIA.regles(self.css, largeurs(self.css)[-1])
                   if "cs-bulle" in s and _composee(s) is None]
        self.assertGreater(len(ecartes), 0)

    def test_une_valeur_egale_au_socle_n_est_PAS_une_difference(self) -> None:
        base = ".cs-bulle { border-left: 4px solid #000; }\n"
        muet = base + '.cs-bulle[data-franchissement="franchi"] { border-left-width: 4px; }\n'
        vu = base + '.cs-bulle[data-franchissement="franchi"] { border-left-width: 7px; }\n'
        self.assertEqual(apparence(muet, 2000, "x", "franchi"), apparence(muet, 2000, "x", ABSENT))
        self.assertNotEqual(apparence(vu, 2000, "x", "franchi"), apparence(vu, 2000, "x", ABSENT))

    def test_la_specificite_l_emporte_sur_l_ordre(self) -> None:
        css = ('.cs-bulle[data-franchissement="franchi"] { border-left-width: 7px; }\n'
               ".cs-bulle { border-left: 4px solid #000; }\n")
        self.assertEqual("7px", apparence(css, 2000, "x", "franchi")["border-left-width"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
