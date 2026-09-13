# -*- coding: utf-8 -*-
"""Un identifiant Legifrance designe UN article, jamais une plage.

`RM-2026-0141`, reste bloquant du point (4): *la citation Legifrance de la
maquette designe [un article] et non [celui qu'elle annonce]*.

**Mesure du 2026-09-11.** 43 fichiers de `docs/assets/` portaient, 86 fois, la
citation *« Loi 65-557, articles 21-1 a 21-3 - LEGIARTI000039301559 »*. Or le
produit lui-meme declare les trois articles **separement**, dans
`_actes_typologie.FONDEMENT_PORTEE[PORTEE_DELEGATION_CS]`:

    art. 21-1 -> LEGIARTI000039301559
    art. 21-2 -> LEGIARTI000039301561
    art. 21-3 -> LEGIARTI000039301563

**Un identifiant presente comme couvrant trois articles est donc faux**, et
faux d'une maniere qui ne se voit pas: le lecteur qui suit le lien atterrit sur
21-1 et croit avoir lu la regle des trois. C'est la meme famille de defaut que
`un identifiant sans date de version n'est pas une citation, c'est une
reference` - la doctrine du depot sur les fondements juridiques.

**Ce que ce lot corrige, et ce qu'il ne corrige pas.** Il reecrit les 86
occurrences en nommant les trois identifiants. Il ne touche pas au produit:
`server/src` declarait deja les trois separement et avait raison. Le defaut
vivait dans les artefacts de recette, qui sont lus par des humains et cites
comme preuves.

**L'AXE.** Ce qui VARIE: le nombre d'articles qu'une regle mobilise, leur
numerotation, la maniere de les ecrire. Ce qui reste INVARIANT: **un
identifiant Legifrance designe exactement un article**. Une plage annoncee sous
un identifiant unique est donc toujours fausse, quel que soit le texte.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
DOCS = DEPOT / "docs"

#: Une PLAGE d'articles annoncee juste avant un identifiant unique.
#: `articles 21-1 a 21-3 - LEGIARTI...`, `art. 14 a 16 (LEGIARTI...)`.
PLAGE_SOUS_UN_IDENTIFIANT = re.compile(
    r"articles?\s+[\d\-]+\s+(?:a|à)\s+[\d\-]+[^.\n]{0,20}?LEGIARTI\d{12}",
    re.IGNORECASE)


def _fautives() -> list[tuple[str, str]]:
    trouvees: list[tuple[str, str]] = []
    for chemin in sorted(DOCS.rglob("*")):
        if chemin.suffix.lower() not in {".html", ".js", ".md"}:
            continue
        texte = chemin.read_text(encoding="utf-8", errors="ignore")
        for m in PLAGE_SOUS_UN_IDENTIFIANT.finditer(texte):
            trouvees.append((chemin.name, m.group(0)[:70]))
    return trouvees


class AUCUNE_PLAGE_D_ARTICLES_SOUS_UN_IDENTIFIANT_UNIQUE(unittest.TestCase):
    """**Le lecteur qui suit le lien n'atterrit que sur le premier article.**"""

    def test_aucun_document_n_annonce_une_plage_sous_un_identifiant(self) -> None:
        fautives = _fautives()
        self.assertEqual(
            [], fautives,
            "une citation annonce plusieurs articles sous un seul identifiant "
            "Legifrance: nommer chaque article avec le sien, ou ne citer que "
            "celui dont on donne l'identifiant")


class LES_TROIS_ARTICLES_DE_LA_DELEGATION_SONT_DISTINCTS(unittest.TestCase):
    """**La source de verite, et c'est le produit qui la porte.**

    Ce test lit le registre du produit plutot que de recopier les trois
    identifiants: une garde qui recopierait sa reference la ferait diverger au
    premier changement, ce qui est exactement le defaut qu'elle corrige.
    """

    def test_le_produit_declare_bien_TROIS_identifiants(self) -> None:
        from coproscope.modules._actes_typologie import FONDEMENT_PORTEE
        from coproscope.modules._actes_vocabulaire import PORTEE_DELEGATION_CS

        _definition, sources = FONDEMENT_PORTEE[PORTEE_DELEGATION_CS]
        identifiants = {identifiant for _libelle, identifiant in sources}
        self.assertGreaterEqual(
            len(identifiants), 3,
            "la delegation au conseil syndical ne cite plus trois articles "
            "distincts: si c'est voulu, remesurer et corriger les artefacts")

    def test_chaque_article_cite_porte_SON_identifiant(self) -> None:
        """Deux articles differents ne peuvent pas partager un identifiant."""
        from coproscope.modules._actes_typologie import FONDEMENT_PORTEE
        from coproscope.modules._actes_vocabulaire import PORTEE_DELEGATION_CS

        _definition, sources = FONDEMENT_PORTEE[PORTEE_DELEGATION_CS]
        self.assertEqual(
            len(sources), len({identifiant for _l, identifiant in sources}),
            "deux articles partagent un identifiant Legifrance")


class LA_GARDE_LIT_BIEN_QUELQUE_CHOSE(unittest.TestCase):
    """Temoins de sante: une garde qui ne reconnait rien passe toujours."""

    def test_le_motif_reconnait_la_citation_qui_a_ete_corrigee(self) -> None:
        self.assertTrue(PLAGE_SOUS_UN_IDENTIFIANT.search(
            "Loi 65-557, articles 21-1 a 21-3 - LEGIARTI000039301559"))

    def test_il_reconnait_aussi_la_forme_accentuee(self) -> None:
        self.assertTrue(PLAGE_SOUS_UN_IDENTIFIANT.search(
            "articles 14 à 16 (LEGIARTI000006428859)"))

    def test_il_epargne_une_citation_CORRECTE(self) -> None:
        """La forme retenue par la correction ne doit pas etre condamnee."""
        self.assertIsNone(PLAGE_SOUS_UN_IDENTIFIANT.search(
            "Loi 65-557, art. 21-1 (LEGIARTI000039301559), "
            "art. 21-2 (LEGIARTI000039301561)"))

    def test_des_documents_sont_bien_parcourus(self) -> None:
        lus = [c for c in DOCS.rglob("*")
               if c.suffix.lower() in {".html", ".js", ".md"}]
        self.assertGreater(len(lus), 50, "aucun document lu dans docs/")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
