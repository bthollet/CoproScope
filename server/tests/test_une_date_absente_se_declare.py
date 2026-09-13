# -*- coding: utf-8 -*-
"""Une date qu'on n'a pas pu lire se dit; une cellule vide ne dit rien.

`RM-2026-0080`. L'item demandait de faire produire `suspected_date` sur les
documents complets. **Ce travail a atterri** - `02_classification.py` appelle
`date_du_document(extracted, file_name)` depuis des commits posterieurs, portes
par des items voisins - et la cellule ne le disait pas. Ce qui restait est le
cas que la colonne preuve de l'item nommait: *un PV isole, sans document
partiel date a cote, restera sans date*.

**LE DEFAUT MESURE LE 2026-09-12, et il n'est pas celui qu'on attendait.** Le
document reste sans date, et **c'est normal**: rien dans son texte ni dans son
nom n'en porte, et le dossier de rangement n'est pas le document. Le defaut
n'est donc pas l'absence de date - c'est que **rien ne la declarait**.
`note_de_date` ne produisait une phrase **que si le dossier de rangement
portait une date DIFFERENTE**. Un document dont ni le texte, ni le nom, ni le
dossier ne portent de date rendait une cellule vide et **aucune phrase**.

**L'AXE, et c'est la regle des trois etats du depot.** Ce qui VARIE: la
presence d'une date dans le texte, dans le nom, dans le dossier. Ce qui reste
INVARIANT: **une absence de mesure et une mesure vide ne se ressemblent pas.**
Etat 0 rien a lire, etat 1 date lue, etat 2 *le controle n'a pas pu etre fait*
- et l'etat 2 ne doit jamais se lire comme un silence.

**LA CONDITION DE SILENCE ETAIT UNE MODALITE.** Elle portait sur *le dossier
porte-t-il une autre date*, qui est un fait du corpus mesure - 270 pieces
datees par leur dossier de collecte. Elle porte desormais sur **la date
trouvee**, qui se suffit a elle-meme: une date lue n'a rien a declarer, une
date absente si.

**Hors des valeurs observees:** un corpus range a plat, sans aucune date dans
les chemins, declarait auparavant **zero** absence; il les declare toutes.
"""
from __future__ import annotations

import unittest

from coproscope.core.date_du_document import (
    SOURCE_ABSENTE,
    SOURCE_TEXTE,
    date_du_document,
    note_de_date,
)

#: Un chemin de rangement date, et un chemin qui ne l'est pas. Les deux cas
#: existent dans le corpus, et c'est leur DIFFERENCE qui creait le silence.
RANGEMENT_DATE = "raw/collecte_2026-09-02/piece.pdf"
RANGEMENT_NU = "raw/AG/piece.pdf"


class UNE_DATE_ABSENTE_SE_DECLARE(unittest.TestCase):
    def test_sans_date_et_sans_dossier_date_la_note_EXISTE(self) -> None:
        """Le cas de l'item: un PV isole, rien autour de lui.

        C'est la seule combinaison qui restait muette, et c'est la plus
        courante des corpus ranges a plat.
        """
        note = note_de_date("", SOURCE_ABSENTE, RANGEMENT_NU)
        self.assertTrue(note, "une cellule vide sans phrase se lit comme une "
                              "date non cherchee")
        self.assertIn("Aucune date lisible", note)

    def test_elle_dit_les_TROIS_endroits_regardes(self) -> None:
        """Sans cela, un lecteur ne sait pas si le dossier a ete consulte."""
        note = note_de_date("", SOURCE_ABSENTE, RANGEMENT_NU)
        for endroit in ("document", "nom", "dossier"):
            with self.subTest(endroit=endroit):
                self.assertIn(endroit, note)

    def test_sans_date_mais_dossier_date_la_note_NOMME_la_date_ecartee(self) -> None:
        """Conservation: le cas deja couvert ne perd pas son message."""
        note = note_de_date("", SOURCE_ABSENTE, RANGEMENT_DATE)
        self.assertIn("2026-09-02", note)
        self.assertIn("classement", note)


class UNE_DATE_LUE_N_A_RIEN_A_DECLARER(unittest.TestCase):
    """Temoin: la correction n'a pas rendu la note bavarde."""

    def test_une_date_lue_sur_un_rangement_nu_reste_muette(self) -> None:
        self.assertEqual("", note_de_date("2024-07-03", SOURCE_TEXTE, RANGEMENT_NU))

    def test_une_date_lue_qui_concorde_avec_le_dossier_reste_muette(self) -> None:
        self.assertEqual(
            "", note_de_date("2026-09-02", SOURCE_TEXTE, RANGEMENT_DATE))

    def test_une_date_lue_contredite_par_le_dossier_se_declare(self) -> None:
        note = note_de_date("2024-07-03", SOURCE_TEXTE, RANGEMENT_DATE)
        self.assertIn("2026-09-02", note)
        self.assertIn("non retenue", note)


class LE_CAS_DE_L_ITEM_BOUT_A_BOUT(unittest.TestCase):
    """Un proces-verbal dont le texte ne porte aucune date d'assemblee."""

    def test_le_document_reste_sans_date_MAIS_le_dit(self) -> None:
        texte = ("Proces-verbal de l'assemblee generale des coproprietaires.\n"
                 "Resolution 1: approbation des comptes. Adoptee.\n")
        date, source = date_du_document(texte, "pv.pdf")
        self.assertEqual("", date)
        note = note_de_date(date, source, RANGEMENT_NU)
        self.assertTrue(
            note,
            "c'est exactement le cas que l'item nomme - un PV isole - et il "
            "sortait sans date et sans phrase")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
