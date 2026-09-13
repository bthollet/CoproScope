# -*- coding: utf-8 -*-
"""Un item declare acheve cite un FAIT, pas seulement qui a fait le travail.

`RM-2026-0171`, prochaine action nommee par l'item: *appliquer le test aux
verdicts existants - statut d'un item du gouvernail contre sa colonne preuve*.

**LE MOTIF DE L'ITEM, EN UNE PHRASE:** l'information exacte est presente, la
conclusion tiree a cote la contredit, et c'est la conclusion qui est lue. Son
test d'acceptation: **si un fait defavorable apparaissait demain dans les
donnees que ce verdict cotoie, le verdict changerait-il TOUT SEUL ?**

**APPLIQUE AU GOUVERNAIL, la reponse est non par construction.** L'etat d'un
item est une donnee **ecrite a la main**, dans une cellule voisine de celle des
faits. Les deux peuvent donc diverger sans que rien ne bouge - c'est la forme
(b) du remede de l'item: quand la derivation est impossible, **rendre le fait
impossible a contourner**.

**MESURE DU 2026-09-12.** Sur **95 items** declares `INTEGRE`, `CLOS`,
`PRET_A_INTEGRER` ou `CLOTURE`:

- **zero** porte une preuve vide ou une preuve qui se declare absente - le
  premier critere essaye, et son zero est un vrai zero, verifie en sondant les
  preuves les plus courtes;
- **cinq** ont pour preuve **UNIQUEMENT un identifiant de chantier**, ce qui
  nomme *qui a fait le travail* et non *ce qui a ete mesure*.

Le second critere est celui qui tient. Un `CH-*` ne change pas quand un fait
contraire apparait: c'est exactement le verdict qui ne se derive pas de ses
faits.

**L'AXE.** Ce qui VARIE: la nature de la preuve - un compte, un verdict de
suite, un commit, une phrase de constat. Ce qui reste INVARIANT: **une preuve
se verifie; une reference se suit.** Les deux sont utiles et ne se remplacent
pas. **Hors des valeurs observees:** un identifiant d'une famille nouvelle -
un `ORD-*`, un futur prefixe - est reconnu comme reference par sa FORME, et ne
devient pas un fait parce que personne ne l'a prevu.

**CE QUE CETTE GARDE NE FAIT PAS.** Elle ne juge pas si le fait cite est
**juste** - cela demanderait de rejouer chaque mesure. Elle interdit qu'une
cellule de preuve se reduise a un renvoi. La dette de cinq est bornee, datee,
et ne doit pas grandir.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REGISTRE = (Path(__file__).resolve().parents[2] / "docs"
            / "roadmap_backlog_central.md")

_SEPARATEUR = re.compile("(?<!" + chr(92) * 2 + ")" + chr(92) + "|")

#: Les etats qui AFFIRMENT un achevement. Lus dans le vocabulaire du
#: gouvernail lui-meme, pas inventes ici.
ETATS_D_ACHEVEMENT = frozenset({"INTEGRE", "CLOS", "PRET_A_INTEGRER", "CLOTURE"})

#: Une reference se reconnait a sa FORME - un prefixe de famille suivi d'un
#: identifiant - et non a une liste de prefixes rencontres.
REFERENCE = re.compile(r"`?(?:CH|CONV|RM|ORD)-[0-9A-Za-z-]+`?")

#: Etat mesure le 2026-09-12. **Dette bornee et datee, jamais une tolerance.**
DETTE_2026_09_12 = frozenset({
    "RM-2026-0058",
    "RM-2026-0074",
    "RM-2026-0075",
    "RM-2026-0110",
    "RM-2026-0117",
})


def _items() -> list[tuple[str, str, str]]:
    """(identifiant, etat, preuve) du registre actif."""
    trouves: list[tuple[str, str, str]] = []
    dans_le_registre = False
    for ligne in REGISTRE.read_text(encoding="utf-8").splitlines():
        if ligne.startswith("## "):
            dans_le_registre = "Registre actif par identifiant" in ligne
            continue
        if not dans_le_registre or not ligne.startswith("| `RM-"):
            continue
        cellules = _SEPARATEUR.split(ligne)
        if len(cellules) < 12:
            continue
        trouves.append((
            cellules[1].strip().strip("`"),
            cellules[4].strip().strip("`"),
            cellules[10].strip(),
        ))
    return trouves


def _preuve_reduite_a_une_reference(preuve: str) -> bool:
    """Vrai quand il ne reste RIEN une fois les references retirees."""
    reste = REFERENCE.sub("", preuve).strip(" ,;.`-")
    return bool(preuve) and not reste


class UN_VERDICT_D_ACHEVEMENT_CITE_UN_FAIT(unittest.TestCase):
    def test_l_instrument_lit_bien_le_registre(self) -> None:
        """Garde de l'instrument: un registre mal lu rendrait tout vert.

        C'est la quatrieme forme de la serie A - celle qui ne laisse meme pas
        un `Ran 0` derriere elle.
        """
        items = _items()
        self.assertGreater(len(items), 100, "le registre n'est presque pas lu")
        acheves = [i for i in items if i[1] in ETATS_D_ACHEVEMENT]
        self.assertGreater(
            len(acheves), 50,
            "aucun etat d'achevement reconnu: le vocabulaire a change")

    def test_le_critere_discrimine(self) -> None:
        """Temoin de l'instrument, dans les deux sens.

        Sans lui, un motif trop large declarerait toutes les preuves fautives,
        et un motif trop etroit n'en declarerait aucune.
        """
        self.assertTrue(_preuve_reduite_a_une_reference(
            "`CH-20260908-1200-RM-2026-0074-voie-factures`"))
        self.assertTrue(_preuve_reduite_a_une_reference(
            "`CH-20260101-0000-RM-2026-0001-x`, `CONV-2026-2101`"))
        self.assertFalse(_preuve_reduite_a_une_reference(
            "`CH-20260908-1200-RM-2026-0074-voie-factures`, 8 tests verts"))
        self.assertFalse(_preuve_reduite_a_une_reference(
            "lanceur corrige, CLI verifie par le chemin du lanceur"))
        self.assertFalse(_preuve_reduite_a_une_reference(""))

    def test_aucune_preuve_NEUVE_ne_se_reduit_a_une_reference(self) -> None:
        """La regle, appliquee: un achevement se justifie par un fait.

        Un `CH-*` nomme QUI a fait le travail, pas CE QUI a ete mesure. Il ne
        changerait pas si un fait contraire apparaissait demain - c'est
        exactement le verdict qui ne se derive pas de ses faits.
        """
        fautifs = sorted(
            ident for ident, etat, preuve in _items()
            if etat in ETATS_D_ACHEVEMENT
            and _preuve_reduite_a_une_reference(preuve)
            and ident not in DETTE_2026_09_12
        )
        self.assertEqual(
            [], fautifs,
            "ces items sont declares acheves et leur colonne preuve ne porte "
            "QU'UN renvoi de chantier: elle nomme qui a fait le travail, pas "
            "ce qui a ete mesure. Y ecrire un fait verifiable - un compte, un "
            "verdict de suite, un commit. Fautifs: %s" % fautifs)

    def test_RESIDU_la_dette_est_bornee_et_ne_grandit_pas(self) -> None:
        """Cinq items au 2026-09-12, et leur compte ne bouge pas en silence."""
        reduits = {
            ident for ident, etat, preuve in _items()
            if etat in ETATS_D_ACHEVEMENT and _preuve_reduite_a_une_reference(preuve)
        }
        self.assertEqual(
            DETTE_2026_09_12, reduits,
            "la dette a change. Si elle a BAISSE, retirer l'item d'ici et dire "
            "au gouvernail quel fait a ete ecrit a la place du renvoi - une "
            "borne qu'on laisse haute laisse la frontiere reculer.")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
