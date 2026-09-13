# -*- coding: utf-8 -*-
"""Un dossier decrit un rangement, jamais le contenu d'une piece.

**Le cas reel que ces tests figent**, mesure le 2026-09-08 sur une instance vide
reconstruite depuis les pieces sources: 270 documents portaient la meme date.
Aucun ne la portait dans son nom, et **aucun de leurs textes ne la contenait
nulle part**. Elle venait du dossier de collecte qui les range.

Le mecanisme etait pire qu'un repli: l'echantillon de classement commence par le
CHEMIN, et la date etait cherchee dans cet echantillon, premiere correspondance
gagnante. Le classement battait donc le document **systematiquement**.
"""

from __future__ import annotations

import unittest

from coproscope.core.date_du_document import (
    SOURCE_ABSENTE,
    SOURCE_NOM_DE_FICHIER,
    SOURCE_TEXTE,
    date_du_document,
    date_lisible_dans,
    note_de_date,
)

CHEMIN_DE_COLLECTE = "raw/100_Collecte/105_Captation_coprodirecte_2026-09-02/piece.pdf"


class DateDuDocument(unittest.TestCase):
    def test_le_texte_du_document_l_emporte(self) -> None:
        date, source = date_du_document("Assemblee du 2024-07-03", "scan.pdf")
        self.assertEqual(("2024-07-03", SOURCE_TEXTE), (date, source))

    def test_le_nom_de_fichier_sert_quand_le_texte_ne_dit_rien(self) -> None:
        date, source = date_du_document("aucune date ici", "2024-07-03_PV.pdf")
        self.assertEqual(("2024-07-03", SOURCE_NOM_DE_FICHIER), (date, source))

    def test_sans_date_lisible_la_date_est_VIDE_et_non_empruntee(self) -> None:
        """Le coeur du defaut: une absence nommee vaut mieux qu'une date de classement."""
        date, source = date_du_document("aucune date", "scan.pdf")
        self.assertEqual(("", SOURCE_ABSENTE), (date, source))

    def test_le_chemin_n_est_pas_un_argument_de_cette_fonction(self) -> None:
        """La garantie est structurelle, pas comportementale.

        `date_du_document` ne recoit pas de chemin. Il ne s'agit donc pas de
        faire confiance a l'appelant pour ne pas le passer: il n'y a aucun
        parametre par lequel le passer.
        """
        from inspect import signature

        self.assertEqual(["texte", "nom_de_fichier"], list(signature(date_du_document).parameters))

    def test_un_mois_inexistant_est_refuse(self) -> None:
        """Le registre reel portait `2009-13` et `2016 00`.

        La borne porte sur la VALEUR du champ - un mois va de 01 a 12 - et non
        sur une liste de valeurs rencontrees.
        """
        self.assertEqual("", date_lisible_dans("dossier 2009-13 archive"))
        self.assertEqual("", date_lisible_dans("reference 2016 00"))
        self.assertEqual("2016-01", date_lisible_dans("reference 2016 01"))

    def test_un_jour_inexistant_est_refuse_mais_le_mois_survit(self) -> None:
        self.assertEqual("2024-07", date_lisible_dans("2024-07-32"))

    def test_la_note_dit_quelle_date_du_rangement_a_ete_ECARTEE(self) -> None:
        note = note_de_date("", SOURCE_ABSENTE, CHEMIN_DE_COLLECTE)
        self.assertIn("2026-09-02", note)
        self.assertIn("classement", note)

    def test_la_note_est_muette_quand_le_rangement_dit_la_meme_chose(self) -> None:
        self.assertEqual("", note_de_date("2026-09-02", SOURCE_TEXTE, CHEMIN_DE_COLLECTE))

    def test_la_note_est_muette_quand_le_rangement_ne_porte_pas_de_date(self) -> None:
        self.assertEqual("", note_de_date("2024-07-03", SOURCE_TEXTE, "raw/AG/piece.pdf"))

    def test_le_cas_mesure_bout_a_bout(self) -> None:
        """270 pieces: rien dans le texte, rien dans le nom, une date au dossier."""
        date, source = date_du_document(
            "Proces-verbal. Aucune date exploitable dans ce texte.", "extranet_export.pdf"
        )
        self.assertEqual("", date)
        note = note_de_date(date, source, CHEMIN_DE_COLLECTE)
        self.assertIn("non retenue", note)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
