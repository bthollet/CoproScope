# -*- coding: utf-8 -*-
"""Sur le mur, une mesure conforme et une absence de mesure ne se ressemblent pas.

`RM-2026-0143`, residu traite le 2026-09-11. **L'item a d'abord perdu son
chiffre, et c'est instructif:** il annoncait *51 resolutions sur 55 sans
montant* comme un constat sur la copropriete; Brice a objecte *je pense que le
nombre est faux*, et il avait raison - **le chiffre venait d'une table de
MAQUETTE a quatre entrees**. Un artefact de demonstration lu comme une mesure
des pieces.

**CE QUI RESTE VRAI SANS AUCUN CHIFFRE**, et que la cellule a garde: au niveau
du mur, *une resolution sans montant et une resolution sous le seuil ne portent
ni l'une ni l'autre de marqueur*.

**ETAT MESURE LE 2026-09-11.** Le modele sait distinguer depuis le matin
meme - `franchissement` rend `FRANCHI`, `NON_FRANCHI` ou `NON_COMPARABLE`, et
`phrase_de_franchissement` arrive bien dans le `detail` de la bulle, que le
gabarit rend. **Ce qui manquait est le MARQUEUR**: la bulle ne portait que
`is-{{ statut }}`, qui decrit la force de la PIECE et non le resultat de la
comparaison. Deux bulles de seuil, l'une `FRANCHI` et l'autre
`NON_COMPARABLE`, sortaient donc avec la meme marque.

**L'AXE.** Ce qui VARIE: la force de la piece, le libelle, la norme concernee.
Ce qui reste INVARIANT: **le resultat d'une comparaison et la force de la piece
qui la fonde sont deux informations differentes**, et une seule classe ne peut
pas porter les deux.

**LA MARQUE N'EST PAS UNE COULEUR SEULE.** La doctrine du depot l'interdit, et
son aide rapide le dit aux lecteurs: *les statuts ne reposent pas seulement sur
la couleur*. `NON_COMPARABLE` recoit donc un bord en **tirets**, visible en
monochrome et a l'impression.

**LIMITE DE VERIFICATION, declaree.** Le rendu de bout en bout n'a pas pu etre
mesure: sur l'instance reabsorbee, `/controle-gouvernance` rend **zero bulle** -
la page est vide de lignes. La garde porte donc sur le GABARIT et sur la
feuille de style, pas sur une page rendue.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
GABARIT = (DEPOT / "server/src/coproscope/web/templates"
           / "controle_gouvernance.html")
STATIQUE = DEPOT / "server/src/coproscope/web/static"


def _feuille() -> str:
    return "\n".join(f.read_text(encoding="utf-8", errors="ignore")
                     for f in sorted(STATIQUE.glob("styles*.css")))


class LE_GABARIT_PORTE_LE_RESULTAT_DE_LA_COMPARAISON(unittest.TestCase):
    """La force de la piece et le franchissement sont deux informations."""

    def setUp(self) -> None:
        self.html = GABARIT.read_text(encoding="utf-8")

    def test_la_bulle_rend_le_franchissement(self) -> None:
        self.assertIn(
            "data-franchissement", self.html,
            "la bulle ne porte que la force de la piece: une mesure conforme "
            "et une absence de mesure sortent avec la meme marque")

    def test_il_est_rendu_depuis_le_CHAMP_et_non_devine(self) -> None:
        """Un marqueur calcule dans le gabarit serait un second endroit qui
        decide du franchissement."""
        self.assertRegex(
            self.html, r"data-franchissement=\"\{\{\s*b\.franchissement")

    def test_il_ne_sort_PAS_quand_le_champ_est_vide(self) -> None:
        """Une bulle sans franchissement - l'avis, le devis - ne doit pas
        recevoir un marqueur vide, qui se lirait comme une valeur."""
        bloc = self.html[self.html.index("{% macro bulle("):][:600]
        self.assertIn("{% if b.franchissement %}", bloc)

    def test_la_phrase_reste_dans_le_detail(self) -> None:
        """Le marqueur ne remplace pas le texte: un lecteur qui ne voit pas la
        marque doit lire la raison."""
        self.assertIn("{{ b.detail }}", self.html)


class LA_MARQUE_NE_REPOSE_PAS_SUR_LA_SEULE_COULEUR(unittest.TestCase):
    """Doctrine du depot, et son aide rapide le promet aux lecteurs."""

    def setUp(self) -> None:
        self.css = _feuille()

    def test_le_non_comparable_a_une_marque_de_FORME(self) -> None:
        bloc = re.search(
            r"\.cs-bulle\[data-franchissement=\"non_comparable\"\][^}]*\}",
            self.css)
        self.assertIsNotNone(
            bloc, "aucun style ne distingue une absence de mesure")
        self.assertIn("border-style", bloc.group(0))

    def test_cette_marque_n_est_pas_seulement_une_couleur(self) -> None:
        bloc = re.search(
            r"\.cs-bulle\[data-franchissement=\"non_comparable\"\][^}]*\}",
            self.css).group(0)
        proprietes = re.findall(r"([a-z-]+)\s*:", bloc)
        self.assertTrue(
            [p for p in proprietes if not p.endswith("color")],
            "la marque ne repose que sur une couleur: invisible en monochrome "
            "et a l'impression, ce que la doctrine du depot interdit")


class LES_TROIS_ETATS_RESTENT_DISTINCTS_DANS_LE_MODELE(unittest.TestCase):
    """Temoin: sans cela, le marqueur n'aurait rien a porter."""

    def test_le_controle_rend_bien_trois_valeurs(self) -> None:
        from coproscope.web._controle_gouvernance_franchissement import (
            FRANCHI,
            NON_COMPARABLE,
            NON_FRANCHI,
        )
        self.assertEqual(3, len({FRANCHI, NON_FRANCHI, NON_COMPARABLE}))

    def test_un_montant_illisible_ne_se_lit_pas_comme_sous_le_seuil(self) -> None:
        """Le coeur du motif: l'absence de mesure n'est pas une conformite."""
        from coproscope.web._controle_gouvernance_franchissement import (
            NON_COMPARABLE,
            franchissement,
        )
        etat, motif = franchissement("", "1000")
        self.assertEqual(NON_COMPARABLE, etat)
        self.assertTrue(motif)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
