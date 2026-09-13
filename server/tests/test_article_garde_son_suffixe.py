# -*- coding: utf-8 -*-
"""Le suffixe d'un article fait partie de son identite, et ne s'efface pas.

Constat `C076` de l'audit, l'un des deux que la verification du 2026-09-08
signalait comme **produisant un chiffre faux en silence** (`RM-2026-0086`), et
qu'elle nommait *un cas d'ecole de la regle du depot sur les axes*.

**Le defaut.** Le motif de majorite s'ecrivait `2[3456](?:-1)?`. Il connaissait
le seul suffixe que quelqu'un avait vu - `25-1` - et **effacait tous les autres
sans rien dire**. Mesure du 2026-09-10 sur le corpus reel, forme par forme:

| reference ecrite | occurrences | ce que le motif rendait |
|------------------|------------:|-------------------------|
| `25`             |         663 | `25`                    |
| `24`             |         393 | `24`                    |
| `25-1`           |         102 | `25-1`                  |
| **`26-4`**       |      **25** | **`26`**                |
| `26`             |           7 | `26`                    |
| `23`             |           5 | `23`                    |
| **`26-5`**       |       **4** | **`26`**                |
| **`26-6`**       |       **4** | **`26`**                |

**33 references** etaient donc attribuees a la majorite des deux tiers de
l'article 26, alors que les articles 26-4 a 26-6 portent l'emprunt collectif et
non le regime des modifications statutaires. Un chiffre faux, et rien pour le
signaler.

**L'axe, et il n'est pas la liste des suffixes rencontres.** Le degre de
liberte est *un numero d'article peut porter un suffixe*; ce qui reste
invariant est que **le suffixe distingue l'article d'un autre article**, donc
qu'il appartient a son identite. Hors des valeurs observees, un suffixe inconnu
est desormais RENDU tel quel: `regime_de_majorite` ne le reconnait pas et rend
`None` - ce qui se declare - au lieu de ranger la resolution sous un regime que
le texte n'enonce pas. **C'est la degradation propre que le test d'acceptation
du depot exige:** un septieme suffixe arrivant demain ne produira pas une
reponse fausse en silence.

**Tolerer a la lecture, normaliser a la sortie, jamais l'inverse.** Un syndic
ecrit `article 26 - 4`; la table des regimes, elle, ne connait qu'une forme. Le
motif accepte les blancs, `article_lu` les retire.
"""

from __future__ import annotations

import unittest

from coproscope.modules._convocation_motifs import MAJORITE_RE as MAJORITE_CONVOCATION
from coproscope.modules._decompte_voix_regimes import regime_de_majorite
from coproscope.modules._resolutions_motifs import MAJORITE_RE, article_lu


#: Les huit formes rencontrees sur le corpus reel, avec leur compte mesure le
#: 2026-09-10. Les comptes sont ici pour la lisibilite du cas; ce qui est
#: EPINGLE est la forme rendue, qui ne depend d'aucun corpus.
FORMES_MESUREES = (
    ("25", 663), ("24", 393), ("25-1", 102),
    ("26-4", 25), ("26", 7), ("23", 5), ("26-5", 4), ("26-6", 4),
)

#: Les seuls regimes de majorite que la loi de 1965 donne a compter, et que
#: `_decompte_voix_regimes` connait. `26-4` n'en fait pas partie: c'est le fait
#: que ce module protege.
REGIMES_CONNUS = ("24", "25", "25-1", "26")


class UnArticleSeLitAvecSonSuffixe(unittest.TestCase):
    """Les deux motifs, resolutions et convocations, rendent la meme chose."""

    def test_TOUTE_FORME_DU_CORPUS_EST_RENDUE_TELLE_QUELLE(self) -> None:
        for forme, _compte in FORMES_MESUREES:
            with self.subTest(article=forme):
                phrase = "vote a la majorite de l article " + forme
                for nom, motif in (("resolutions", MAJORITE_RE),
                                   ("convocations", MAJORITE_CONVOCATION)):
                    lues = [article_lu(x) for x in motif.findall(phrase)]
                    self.assertEqual(
                        [forme], lues,
                        "%s: `article %s` n'est pas rendu tel quel" % (nom, forme),
                    )

    def test_LES_TRENTE_TROIS_REFERENCES_NE_SONT_PLUS_LUES_COMME_26(self) -> None:
        """Le coeur du constat: trois suffixes, 33 occurrences, un faux regime."""
        for forme in ("26-4", "26-5", "26-6"):
            with self.subTest(article=forme):
                lues = [article_lu(x) for x in
                        MAJORITE_RE.findall("majorite de l article " + forme)]
                self.assertNotIn("26", lues, "le suffixe est encore efface")
                self.assertEqual([forme], lues)

    def test_un_suffixe_inconnu_ne_se_range_sous_aucun_regime(self) -> None:
        """La degradation propre, et elle se verifie en aval.

        `regime_de_majorite` rend `None`, ce qui se declare. L'ancien
        comportement rendait le regime des deux tiers, ce qui est une affirmation
        de droit sur un article qui ne la porte pas.
        """
        for forme in ("26-4", "26-5", "26-6"):
            with self.subTest(article=forme):
                self.assertIsNone(regime_de_majorite(forme))
        for forme in REGIMES_CONNUS:
            with self.subTest(regime=forme):
                self.assertIsNotNone(regime_de_majorite(forme))

    def test_les_blancs_autour_du_tiret_sont_toleres_puis_retires(self) -> None:
        """Un syndic ecrit `article 26 - 4`; la table ne connait que `26-4`."""
        lues = [article_lu(x) for x in MAJORITE_RE.findall("article 26 - 4")]
        self.assertEqual(["26-4"], lues)

    def test_UN_SUFFIXE_JAMAIS_VU_EST_RENDU_AU_LIEU_D_ETRE_ROGNE(self) -> None:
        """Le test d'acceptation du depot: et si un septieme arrivait demain ?

        `26-7` n'existe pas dans le corpus mesure. Ce qui est verifie n'est
        donc pas qu'on le connaisse - c'est qu'il **ne soit pas confondu avec
        `26`**, et qu'il descende en aval comme un article inconnu.
        """
        lues = [article_lu(x) for x in MAJORITE_RE.findall("article 26-7")]
        self.assertEqual(["26-7"], lues)
        self.assertIsNone(regime_de_majorite("26-7"))

    def test_le_pluriel_et_le_numero_restent_lus(self) -> None:
        """Ce que le motif savait deja faire ne doit pas avoir ete perdu."""
        self.assertEqual(["24"], MAJORITE_RE.findall("Articles 24 et 25 combines"))
        self.assertEqual(["26"], MAJORITE_RE.findall("article n° 26"))
        self.assertEqual(["25"], MAJORITE_RE.findall("ARTICLE 25"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
