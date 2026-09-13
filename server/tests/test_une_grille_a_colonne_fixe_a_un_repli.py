# -*- coding: utf-8 -*-
"""Une grille dont une colonne ne cede jamais doit avoir un repli etroit.

`RM-2026-0067`, repare le 2026-09-11. Le constat - *`.cs-rappro-action` sans
repli etroit repousse la matrice a 2 201 px* - a survecu a un triage
adversarial: un agent a tente de le refuter et **la refutation a echoue**.

**Verification du 2026-09-11:** la regle porte
`grid-template-columns: minmax(0, 1fr) auto` et **n'apparaissait dans AUCUN
`@media`** de la feuille - controle sur toutes les parts. La seconde colonne
porte les boutons d'action, et `auto` la laisse imposer sa largeur: elle ne
cede donc jamais, quelle que soit la place disponible.

**L'AXE.** Ce qui VARIE: la largeur de l'ecran, la longueur des libelles de
boutons, le nombre d'actions. Ce qui reste INVARIANT: **une piste `auto` ne
cede jamais**, donc toute grille qui en porte une a cote d'une piste flexible
doit declarer ce qu'elle fait quand la place manque. Sans cela, ce n'est pas la
grille qui se comprime: c'est la page qui s'allonge.

**Le seuil est celui du depot, pas un seuil neuf.** `760px` est le plus employe
de la feuille - 14 occurrences, contre 7 pour `980px` et 7 pour `720px`. **Un
repli qui invente son propre seuil fabrique une troisieme mise en page a
maintenir**, et c'est le genre de divergence que ce depot paie ailleurs.

**Ce que cette garde ne fait pas.** Elle ne mesure aucune hauteur rendue - il
faudrait un moteur de rendu, que la suite n'a pas, et c'est la limite deja
declaree par `RM-2026-0111`. Elle verifie la propriete qui, elle, se lit dans
la feuille: une grille a colonne fixe declare son repli.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
FEUILLES = sorted((DEPOT / "server/src/coproscope/web/static").glob("styles*.css"))

#: La classe que l'item nomme, et le seuil conventionnel du depot.
CLASSE = ".cs-rappro-action"
SEUIL_CONVENTIONNEL = "max-width: 760px"


def _feuille_complete() -> str:
    return "\n".join(f.read_text(encoding="utf-8", errors="ignore")
                     for f in FEUILLES)


class LA_GRILLE_NOMMEE_PAR_L_ITEM_A_SON_REPLI(unittest.TestCase):
    """**Le defaut repare, et il etait mesure a 2 201 px.**"""

    def setUp(self) -> None:
        self.css = _feuille_complete()

    def test_la_classe_existe_toujours(self) -> None:
        """Temoin: si elle disparaissait, tout ce qui suit garderait le vide."""
        self.assertIn(CLASSE, self.css)

    def test_elle_porte_bien_une_colonne_qui_ne_cede_pas(self) -> None:
        """C'est cette colonne `auto` qui fait le defaut: sans elle, il n'y
        aurait rien a replier."""
        bloc = self.css[self.css.index(CLASSE):][:400]
        self.assertRegex(bloc, r"grid-template-columns:[^;]*\bauto\b")

    def test_elle_est_declaree_dans_un_media_etroit(self) -> None:
        """**Le coeur du lot.** Sans `@media`, la page s'allonge au lieu de se
        comprimer."""
        medias = re.findall(r"@media[^{]*\{(?:[^{}]|\{[^{}]*\})*\}", self.css)
        concernes = [m for m in medias if CLASSE in m]
        self.assertTrue(
            concernes,
            "cette grille porte une colonne `auto` et ne declare nulle part ce "
            "qu'elle fait quand la place manque")

    def test_le_repli_passe_bien_a_UNE_colonne(self) -> None:
        medias = re.findall(r"@media[^{]*\{(?:[^{}]|\{[^{}]*\})*\}", self.css)
        concernes = [m for m in medias if CLASSE in m]
        self.assertTrue(
            any("grid-template-columns: minmax(0, 1fr)" in m
                and "auto" not in m.split(CLASSE, 1)[1][:200]
                for m in concernes),
            "le repli ne retire pas la colonne `auto`: elle continue donc "
            "d'imposer sa largeur, et le repli ne replie rien")

    def test_il_emploie_le_seuil_CONVENTIONNEL_du_depot(self) -> None:
        """Un repli qui invente son seuil fabrique une troisieme mise en page."""
        medias = re.findall(r"@media[^{]*\{(?:[^{}]|\{[^{}]*\})*\}", self.css)
        concernes = [m for m in medias if CLASSE in m]
        self.assertTrue(
            any(SEUIL_CONVENTIONNEL in m for m in concernes),
            "le repli emploie un seuil qui n'est pas celui du depot: "
            "verifier qu'il est justifie, ou l'aligner sur 760px")


class LE_SEUIL_RETENU_EST_BIEN_LE_PLUS_EMPLOYE(unittest.TestCase):
    """La justification du seuil se remesure au lieu d'etre affirmee."""

    def test_760px_reste_le_seuil_dominant(self) -> None:
        css = _feuille_complete()
        seuils = re.findall(r"max-width: *(\d+)px", css)
        assert seuils, "aucun seuil lu dans la feuille"
        from collections import Counter

        compte = Counter(seuils)
        dominant, _n = compte.most_common(1)[0]
        self.assertEqual(
            "760", dominant,
            "le seuil dominant du depot a change: le repli de "
            "`.cs-rappro-action` doit etre remesure et realigne")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
