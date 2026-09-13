# -*- coding: utf-8 -*-
"""Le gouvernail garde ses onze colonnes, et un pipe nu les casse en silence.

**Le defaut s'est produit six fois, dont trois fois de ma main.** Une cellule du
registre qui contient une barre verticale litterale - `35 | 29 | -6`, un chemin
`events|blobs|snapshots` - **fabrique des colonnes fantomes**. Le tableau reste
parfaitement lisible pour un humain: c'est ce qui rend le defaut couteux. Mais
toute lecture par colonne se decale d'un cran, si bien que **le statut d'un item
se lit dans sa priorite, et sa preuve dans ses chantiers**.

**L'axe.** Ce qui varie: quelle cellule, quel item, quel caractere a ete recopie
depuis un chemin, un tableau ou une commande. Ce qui reste invariant: **une
ligne du registre a exactement onze cellules**, parce que l'en-tete en declare
onze. Le controle ne connait aucune liste de cellules interdites; il compte.

**Deux precautions apprises en ecrivant ce garde.**

1. Le fichier porte **huit tableaux**, pas un. `Temps humain explicite`,
   `Synthese UX/UI`, `File canonique` ont deux, trois ou quatre colonnes par
   construction. Une premiere version balayait tout le document et signalait
   vingt lignes fausses qui ne l'etaient pas. **Un controle qui suppose un seul
   tableau la ou il y en a huit fabrique ses propres defauts.**
2. Le decoupage doit ignorer les barres **echappees**, seule facon d'ecrire une
   barre dans une cellule.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
GOUVERNAIL = DEPOT / "docs" / "roadmap_backlog_central.md"

TITRE_REGISTRE = "## Registre actif par identifiant"
COLONNES = 11

#: Une barre NUE. Une barre precedee d'une controblique est du texte de cellule.
_BARRE_NUE = re.compile(r"(?<!\\)\|")

_ITEM = re.compile(r"^\| `(RM-\d{4}-\d{4})` \|")


def _lignes_du_registre() -> list[tuple[int, str]]:
    """Les lignes d'item du seul tableau a onze colonnes du document."""
    lignes = GOUVERNAIL.read_text(encoding="utf-8").splitlines()
    debut = next(i for i, l in enumerate(lignes) if l.startswith(TITRE_REGISTRE))
    fin = next((i for i, l in enumerate(lignes[debut + 1:], debut + 1)
                if l.startswith("## ")), len(lignes))
    return [(i + 1, l) for i, l in enumerate(lignes[debut:fin], debut) if _ITEM.match(l)]


class LeGouvernailGardeSesColonnes(unittest.TestCase):
    def test_le_registre_est_trouve_et_peuple(self) -> None:
        """Sans cela, un garde qui ne lit rien passerait pour vert."""
        lignes = _lignes_du_registre()
        self.assertGreater(len(lignes), 100, "registre suspect: %d lignes" % len(lignes))

    def test_chaque_item_a_onze_cellules(self) -> None:
        fautes = []
        for numero, ligne in _lignes_du_registre():
            cellules = _BARRE_NUE.split(ligne)[1:-1]
            if len(cellules) != COLONNES:
                fautes.append(
                    "ligne %d, `%s`: %d cellules au lieu de %d. Une barre verticale "
                    "litterale dans une cellule fabrique une colonne fantome et decale "
                    "toute lecture par colonne. L'echapper."
                    % (numero, _ITEM.match(ligne).group(1), len(cellules), COLONNES)
                )
        self.maxDiff = None
        self.assertEqual([], fautes, "\n".join(fautes))

    def test_aucun_identifiant_en_double(self) -> None:
        """Deux lignes pour un meme item: la seconde lecture ecrase la premiere."""
        vus = [_ITEM.match(l).group(1) for _, l in _lignes_du_registre()]
        doubles = sorted({r for r in vus if vus.count(r) > 1})
        self.assertEqual([], doubles, "identifiants en double: %s" % ", ".join(doubles))

class UnItemNeDitPasDeuxChosesOpposeesSurLuiMeme(unittest.TestCase):
    """Range HORS FILE et declare `ACTIF`: le document se contredit sur un item.

    **`RM-2026-0171` applique au gouvernail lui-meme.** La section *Hors file
    d'execution* range un item parmi les *acquis ou socles a maintenir, a
    rouvrir seulement sur regression*; sa ligne de registre le declare `ACTIF`.
    Les deux vivent dans le meme fichier, a deux cents lignes d'ecart, et **c'est
    le statut qui est lu**: un item `ACTIF` occupe une place dans la file meme
    quand une autre section dit qu'il n'y est plus.

    **Ce garde ne tranche pas la contradiction, il l'empeche d'etre muette.**
    Aligner l'un sur l'autre est un arbitrage; le declarer ne l'est pas. Deux
    contradictions existaient au 2026-09-09, toutes deux desormais nommees dans
    leur ligne. Une troisieme, ajoutee sans un mot, fera echouer ce test.
    """

    #: Les tournures par lesquelles une ligne reconnait sa propre contradiction.
    #: Radicaux, sans casse ni apostrophe - lecon des deux gardes precedents,
    #: dont les listes de tournures exactes rataient une declaration parfaite.
    _AVEUX = ("contradiction", "hors file", "socle a maintenir")

    def _hors_file(self) -> set[str]:
        lignes = GOUVERNAIL.read_text(encoding="utf-8").splitlines()
        debut = next(i for i, l in enumerate(lignes)
                     if l.startswith("### ") and "Hors file" in l)
        fin = next(i for i, l in enumerate(lignes[debut + 1:], debut + 1)
                   if l.startswith(("## ", "### ")))
        ranges: set[str] = set()
        for ligne in lignes[debut:fin]:
            ranges.update(re.findall(r"RM-\d{4}-\d{4}", ligne))
        return ranges

    def test_la_section_hors_file_est_trouvee_et_peuplee(self) -> None:
        """Sans cela, un garde qui ne lit rien passerait pour vert."""
        self.assertGreater(len(self._hors_file()), 10)

    def test_un_item_hors_file_declare_actif_le_DIT(self) -> None:
        ranges = self._hors_file()
        fautes = []
        for numero, ligne in _lignes_du_registre():
            rm = _ITEM.match(ligne).group(1)
            if rm not in ranges:
                continue
            statut = _BARRE_NUE.split(ligne)[1:-1][3].strip().strip("`")
            if statut != "ACTIF":
                continue
            normal = ligne.lower().replace("'", " ")
            if any(a in normal for a in self._AVEUX):
                continue
            fautes.append(
                "ligne %d, `%s`: range *Hors file d'execution* ET declare `ACTIF`, "
                "sans que la ligne le dise. Trancher, ou nommer la contradiction: "
                "le document dit deux choses opposees et c'est le statut qui est lu."
                % (numero, rm)
            )
        self.maxDiff = None
        self.assertEqual([], fautes, "\n".join(fautes))


class LeGouvernailGardeSesColonnesSuite(unittest.TestCase):
    def test_le_decoupage_distingue_la_barre_nue_de_la_barre_echappee(self) -> None:
        """La propriete qui porte tout le garde, prouvee sur les deux cas."""
        nue = r"| `RM-2026-0001` | a | b | c |"
        self.assertEqual(4, len(_BARRE_NUE.split(nue)[1:-1]))
        echappee = "| `RM-2026-0001` | a " + chr(92) + "| b | c |"
        self.assertEqual(3, len(_BARRE_NUE.split(echappee)[1:-1]))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
