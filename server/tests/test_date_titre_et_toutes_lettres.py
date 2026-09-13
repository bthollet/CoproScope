# -*- coding: utf-8 -*-
"""Un document date son objet dans son titre, et parfois en toutes lettres.

**Deux mesures du 2026-09-09, sur les seuls documents d'assemblee.** Le lecteur
livre le matin rendait 56,6 %% sur l'etalon general - et **sept proces-verbaux
sur dix revenaient AMBIGU**. Un taux moyen ne dit rien d'une population
particuliere, et c'est celle-la qui decide de l'identite des assemblees.

Deux causes, toutes deux mesurees:

1. **la date d'un proces-verbal est ecrite EN TOUTES LETTRES** - `Ce jour
   MERCREDI TROIS JUILLET DEUX MILLE VINGT QUATRE`. Elle n'etait pas mal
   choisie: elle n'etait pas candidate du tout;
2. **le titre perdait contre une etiquette.** Une etiquette d'emission - `le`,
   `date :` - se repete partout dans un document; la position du titre ne se
   repete pas. Le proces-verbal de l'assemblee en double portait un seul
   candidat dans sa zone de titre, et c'etait le bon.

Apres correction: **9 proces-verbaux sur 10 portent une date**, chacune
verifiee a la main contre son titre.
"""

from __future__ import annotations

import unittest

from coproscope.core._date_en_lettres import date_en_toutes_lettres, nombre_en_lettres
from coproscope.core.date_du_document import ZONE_TITRE, lire_date

TITRE_REEL = (
    "PROCES-VERBAL DE L'ASSEMBLEE GENERALE de la RESIDENCE LES TILLEULS (pseudo) "
    "- 23 TRAVERSE DES EXEMPLES 13000 VILLE (REF 0000) "
    "Ce jour MERCREDI TROIS JUILLET DEUX MILLE VINGT QUATRE, les Coproprietaires"
)


class NombreEnLettres(unittest.TestCase):
    def test_les_quantiemes_usuels(self) -> None:
        for mots, attendu in (("premier", 1), ("trois", 3), ("quinze", 15),
                              ("vingt", 20), ("vingt et un", 21), ("trente et un", 31)):
            self.assertEqual(attendu, nombre_en_lettres(mots), mots)

    def test_le_millesime_du_siecle_en_cours(self) -> None:
        self.assertEqual(2024, nombre_en_lettres("deux mille vingt quatre"))
        self.assertEqual(2000, nombre_en_lettres("deux mille"))

    def test_un_millesime_du_siecle_precedent_n_est_PAS_devine(self) -> None:
        """Degradation declaree: `mille neuf cent ...` rend 0, donc une absence.

        Aucune date fausse n'en sort. L'exception, quand elle viendra, se verra
        comme un document sans date - pas comme une date de 2000.
        """
        self.assertEqual(0, nombre_en_lettres("mille neuf cent quatre-vingt-cinq"))

    def test_une_suite_de_mots_qui_n_est_pas_un_nombre_rend_zero(self) -> None:
        self.assertEqual(0, nombre_en_lettres("les coproprietaires"))
        self.assertEqual(0, nombre_en_lettres(""))


class DateEnToutesLettres(unittest.TestCase):
    def test_la_forme_des_actes_se_lit(self) -> None:
        trouves = date_en_toutes_lettres(
            "ce jour mercredi trois juillet deux mille vingt quatre, les coproprietaires"
        )
        self.assertEqual(1, len(trouves))
        self.assertEqual((3, 7, 2024), trouves[0][2])

    def test_un_quantieme_compose_se_lit(self) -> None:
        trouves = date_en_toutes_lettres("ce jour mercredi vingt et un fevrier deux mille vingt quatre")
        self.assertEqual((21, 2, 2024), trouves[0][2])

    def test_le_jour_de_la_semaine_n_est_pas_exige(self) -> None:
        """Il varie librement et n'ajoute rien: l'exiger serait une modalite."""
        trouves = date_en_toutes_lettres("l'an deux mille vingt quatre, le trois juillet deux mille vingt quatre")
        self.assertTrue(trouves)

    def test_une_date_impossible_en_lettres_est_refusee(self) -> None:
        self.assertEqual([], date_en_toutes_lettres("le trente et un fevrier deux mille vingt quatre"))


class LeTitreDateLeDocument(unittest.TestCase):
    def test_le_proces_verbal_de_l_assemblee_en_double_retrouve_sa_date(self) -> None:
        """Le cas qui a motive les deux corrections, ecrit tel qu'il se lit."""
        self.assertEqual("2024-07-03", lire_date(TITRE_REEL)["valeur"])

    def test_le_titre_l_emporte_sur_une_etiquette_plus_bas(self) -> None:
        """Une etiquette se repete; la position du titre ne se repete pas.

        Sur le corpus reel, cette priorite fait passer les proces-verbaux
        portant une date de 4 sur 10 a 9 sur 10.
        """
        corps = " ..." + ("x" * ZONE_TITRE) + " echeance le 15/09/2024, precedente le 12/06/2023."
        self.assertEqual("2024-07-03", lire_date(TITRE_REEL + corps)["valeur"])

    def test_LA_LIMITE_DU_PROXY_une_date_concurrente_DANS_le_titre_fait_abandonner(self) -> None:
        """**La zone de titre est un proxy en NOMBRE DE CARACTERES, pas un titre.**

        Ecrit parce que mon propre test l'a pris en defaut avant le corpus: si
        une date concurrente tombe elle aussi dans les premiers caracteres, la
        priorite du titre ne departage plus rien et la lecture s'abstient.

        C'est la bonne degradation - elle ne fabrique pas de date - mais c'est
        une limite reelle, et un document au bandeau charge la rencontrera. Le
        remede n'est pas d'elargir ou de retrecir la borne au jugé: c'est de
        decouper le titre sur la STRUCTURE du texte, ce que l'extraction ne
        rend pas encore.
        """
        texte = TITRE_REEL + " echeance le 15/09/2024, precedente le 12/06/2023."
        self.assertEqual("", lire_date(texte)["valeur"])
        self.assertEqual("ambigu", lire_date(texte)["source"])

    def test_la_zone_du_titre_est_bornee_et_la_borne_est_declaree(self) -> None:
        """Une date qui n'est PAS dans le titre ne beneficie pas de sa priorite."""
        texte = ("x" * (ZONE_TITRE + 50)) + " reunion du 03/07/2024 puis du 15/09/2024"
        lecture = lire_date(texte)
        self.assertIn(lecture["source"], ("ambigu", "texte"))

    def test_sans_titre_utile_la_lecture_ne_fabrique_rien(self) -> None:
        self.assertEqual("", lire_date("tableau sans en-tete ni date")["valeur"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
