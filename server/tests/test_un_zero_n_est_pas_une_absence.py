# -*- coding: utf-8 -*-
"""Un compteur qui vaut zero n'est pas un compteur absent.

`RM-2026-0109`, point (2) de l'ordre d'instruction de Brice: *appliquer la
regle - sans coffre, l'ecran ne montre rien et DIT qu'il ne montre rien*.

**Le defaut mesure le 2026-09-11, et il est dans les gabarits.** Jinja offre
deux modes a `default`: `|default(x)` ne mord que sur `undefined`, tandis que
`|default(x, true)` active le mode BOOLEEN et mord sur **toute valeur falsy,
zero compris**. Verifie: `0|default(4, true)` rend **4**.

**Consequence, et elle inverse le sens de l'ecran.** Un compteur a zero est la
BONNE nouvelle - aucune piece manquante, aucun manquement critique. Le mode
booleen le remplacait par son repli: *zero piece critique* affichait le nombre
de points du guide comptable, et **une absence de manquement devenait une
alarme**. C'est le meme motif que le bandeau des courriers qui annoncait *3
brouillons* devant un tableau d'un seul, et que `_courriers_matiere` a corrige
le meme jour: **un seul comptage, et il compte ce qu'il annonce**.

**Mesure sur les gabarits:** **8 compteurs** portaient le mode booleen - cinq
dans `pieces.html`, trois dans `_actions_reprise_actions.html` - contre **58
`|default(0)` inoffensifs**, qui ne couvrent qu'une variable non definie. Les
huit sont corriges; les cinquante-huit sont laisses tels quels, parce qu'un
repli sur `undefined` est exactement ce qu'un repli doit faire.

**L'AXE.** Ce qui VARIE: le nom du compteur, sa source, la valeur de son repli.
Ce qui reste INVARIANT: **zero est une mesure, l'absence est une ignorance, et
les deux ne se remplacent pas.** Un repli couvre ce qu'on ne sait pas; il ne
doit jamais couvrir ce qu'on a mesure.

**Ce que cette garde ne fait pas.** Elle ne juge pas les replis eux-memes - un
compteur absent PEUT legitimement retomber sur un autre. Elle interdit
seulement qu'un repli s'applique a une valeur mesuree.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
GABARITS = DEPOT / "server/src/coproscope/web/templates"

#: `|default(<repli>, true)`, le mode booleen. Le repli est capture pour qu'on
#: puisse distinguer un repli LITTERAL vide - inoffensif, il ne fabrique aucun
#: nombre - d'un repli qui calcule.
MODE_BOOLEEN = re.compile(
    r"\|\s*default\(\s*([^,()]*(?:\([^()]*\)[^,()]*)*)\s*,\s*true\s*\)")

#: Un repli qui ne peut fabriquer aucun nombre trompeur.
REPLIS_INOFFENSIFS = {"0", "''", '""', "[]", "{}", "none", "None"}

#: Ce qui fait d'une variable un COMPTEUR. La garde ne porte que sur eux: un
#: libelle ou un titre a le droit de retomber sur un repli quand il est vide.
MOTS_DE_COMPTEUR = ("total", "count", "length", "nombre")


def _compteurs_a_repli() -> list[tuple[str, int, str]]:
    trouves: list[tuple[str, int, str]] = []
    for chemin in sorted(GABARITS.rglob("*.html")):
        texte = chemin.read_text(encoding="utf-8", errors="ignore")
        for numero, ligne in enumerate(texte.splitlines(), start=1):
            for m in MODE_BOOLEEN.finditer(ligne):
                repli = m.group(1).strip()
                if repli in REPLIS_INOFFENSIFS:
                    continue
                gauche = ligne[:m.start()]
                noms = re.findall(r"([A-Za-z_][\w.]*)\s*$", gauche)
                nom = noms[0] if noms else ""
                if any(mot in (nom + " " + repli).lower()
                       for mot in MOTS_DE_COMPTEUR):
                    trouves.append((chemin.name, numero, nom))
    return trouves


class AUCUN_COMPTEUR_NE_SE_REMPLACE_PAR_UN_REPLI(unittest.TestCase):
    """La garde du lot, et elle porte sur tous les gabarits sans liste."""

    def test_plus_aucun_compteur_ne_porte_le_mode_booleen(self) -> None:
        trouves = _compteurs_a_repli()
        self.assertEqual(
            [], trouves,
            "un compteur peut etre remplace par son repli quand il vaut zero: "
            "une absence de manquement s'afficherait comme une alarme. "
            "Retirer le `, true` - `|default(x)` couvre `undefined`, ce qui "
            "est la seule chose qu'un repli doit couvrir.")


class LA_GARDE_MESURE_BIEN_QUELQUE_CHOSE(unittest.TestCase):
    """**Temoins de sante.** Une garde qui ne lit rien passe toujours.

    C'est le defaut rencontre trois fois dans ce depot le meme jour: une
    fixture refusee en amont, une garde inatteignable, un filtre sensible aux
    accents. Ces temoins verifient que le motif et le corpus existent.
    """

    def test_des_gabarits_sont_lus(self) -> None:
        self.assertGreater(len(list(GABARITS.rglob("*.html"))), 20)

    def test_le_motif_reconnait_bien_le_mode_booleen(self) -> None:
        self.assertTrue(MODE_BOOLEEN.search("{{ a.total|default(b|length, true) }}"))

    def test_il_ne_confond_pas_avec_le_mode_par_defaut(self) -> None:
        """`|default(x)` sans le `true` est legitime et ne doit pas etre vu."""
        self.assertIsNone(MODE_BOOLEEN.search("{{ a.total|default(b|length) }}"))

    def test_les_replis_inoffensifs_restent_nombreux_et_intacts(self) -> None:
        """**Ce test dit ce que le lot n'a PAS touche.** 58 `|default(0, true)`
        subsistent: un repli litteral nul ne fabrique aucun nombre trompeur, et
        les corriger aurait ete du bruit."""
        total = 0
        for chemin in GABARITS.rglob("*.html"):
            texte = chemin.read_text(encoding="utf-8", errors="ignore")
            for m in MODE_BOOLEEN.finditer(texte):
                if m.group(1).strip() in REPLIS_INOFFENSIFS:
                    total += 1
        # Plancher a la mesure. Mesure du 2026-09-13: 16, apres la suppression
        # de 12 ecrans dont les gabarits portaient la plupart de ces replis
        # (`RM-2026-0183`) - un retrait dit, pas un motif qui cesse de lire.
        self.assertGreater(
            total, 15,
            "les replis litteraux nuls ont disparu: soit le motif ne les "
            "reconnait plus, soit un lot les a retires sans le dire")


class LE_MODE_BOOLEEN_DE_JINJA_FAIT_BIEN_CE_QUE_LA_GARDE_DIT(unittest.TestCase):
    """**La mesure qui fonde tout le lot, rejouee.**

    Sans elle, la garde repose sur une lecture de documentation. Le depot a
    deja paye de croire une documentation plutot qu'une mesure.
    """

    def test_zero_est_remplace_en_mode_booleen(self) -> None:
        from jinja2 import Environment

        rendu = Environment().from_string(
            "{{ n|default(4, true) }}").render(n=0)
        self.assertEqual("4", rendu)

    def test_zero_survit_en_mode_par_defaut(self) -> None:
        from jinja2 import Environment

        rendu = Environment().from_string("{{ n|default(4) }}").render(n=0)
        self.assertEqual("0", rendu)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
