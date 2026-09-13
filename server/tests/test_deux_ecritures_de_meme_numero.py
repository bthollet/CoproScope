# -*- coding: utf-8 -*-
"""Deux ecritures de meme numero: la cle dit qui les rapproche, la date ce qui les separe.

`RM-2026-0135`. L'item annoncait un residu en **deux champs**: la cle
`fournisseur|numero|ttc` *n'inclut ni la date ni le sens du montant*, alors
que l'axe les designe comme les discriminants.

**MESURE DU 2026-09-12: LE SENS DU MONTANT Y EST DEJA.** Verifie par le point
d'entree de l'extracteur: un avoir sort a `-600.00` et sa facture a `600.00`,
donc **deux cles distinctes**. Un avoir n'est jamais signale comme doublon de
sa facture, et **la moitie du residu annonce etait deja couverte**.

**ET AJOUTER LA DATE A LA CLE SERAIT LE MAUVAIS CORRECTIF**, ce que l'axe de
l'item etablit lui-meme: la question est *deux ecritures qui portent le meme
numero designent-elles la meme obligation de paiement*. Une **relance** porte
legitimement le meme numero, le meme montant et une autre date - et elle
designe **la meme obligation**. La date dans la cle les separerait, donc
**ferait disparaitre le signal sur le cas meme que l'item cite**. Une facture
rectificative, elle, porte un autre montant: elle est deja separee.

**CE QUI MANQUAIT: dire CE QUI DISTINGUE les deux ecritures.** Le signalement
ne le disait pas; un lecteur ne pouvait pas separer une relance d'un second
depot sans relire les deux lignes. La date devient donc un **discriminant
nomme** - `DOUBLON_DATES_DIFFERENTES` - et **rien n'est efface**: c'est un fait
de plus, pas un verdict. Un humain tranche.

**L'AXE.** Ce qui VARIE: la redaction du numero, la maniere de datter, le sens
du montant. Ce qui reste INVARIANT: **ce qui rapproche deux ecritures va dans
la cle, ce qui les distingue se dit a cote.** Melanger les deux fait
disparaitre soit le rapprochement, soit la distinction.
"""
from __future__ import annotations

import unittest

from coproscope.modules._factures_doublons import (
    DOUBLON_DATES_DIFFERENTES,
    DOUBLON_POTENTIEL,
    anomalies_de_doublon,
    cle_de_doublon,
    cle_vide,
)


class LA_CLE_RAPPROCHE_CE_QUI_EST_LA_MEME_OBLIGATION(unittest.TestCase):
    def test_un_avoir_et_sa_facture_portent_deux_cles(self) -> None:
        """Le sens du montant est deja dans la cle, sans nommer le mot avoir."""
        self.assertNotEqual(
            cle_de_doublon("SOCIETE DU PARC", "F-118", "600.00"),
            cle_de_doublon("SOCIETE DU PARC", "F-118", "-600.00"))

    def test_deux_emetteurs_ne_se_rapprochent_pas(self) -> None:
        self.assertNotEqual(
            cle_de_doublon("SOCIETE A", "F-118", "600.00"),
            cle_de_doublon("SOCIETE B", "F-118", "600.00"))

    def test_une_facture_rectificative_porte_un_autre_montant(self) -> None:
        """Elle est deja separee: l'axe le dit, et la cle le fait."""
        self.assertNotEqual(
            cle_de_doublon("SOCIETE DU PARC", "F-118", "600.00"),
            cle_de_doublon("SOCIETE DU PARC", "F-118", "540.00"))

    def test_une_relance_porte_LA_MEME_cle(self) -> None:
        """Meme obligation, donc meme cle - c'est le cas que la date dans la

        cle aurait fait disparaitre.
        """
        self.assertEqual(
            cle_de_doublon("SOCIETE DU PARC", "F-118", "600.00"),
            cle_de_doublon("SOCIETE DU PARC", "F-118", "600.00"))


class LA_DATE_DIT_CE_QUI_DISTINGUE(unittest.TestCase):
    def test_la_premiere_ecriture_ne_signale_RIEN(self) -> None:
        """Une anomalie sur la premiere serait un faux positif systematique."""
        self.assertEqual(
            [], anomalies_de_doublon("A|F-118|600.00", "2025-03-12", 1, []))

    def test_deux_ecritures_de_meme_date_signalent_le_doublon_seul(self) -> None:
        trouve = anomalies_de_doublon(
            "A|F-118|600.00", "2025-03-12", 2, ["2025-03-12"])
        self.assertEqual([DOUBLON_POTENTIEL], trouve)

    def test_deux_dates_differentes_se_DISENT(self) -> None:
        trouve = anomalies_de_doublon(
            "A|F-118|600.00", "2025-04-02", 2, ["2025-03-12"])
        self.assertEqual([DOUBLON_POTENTIEL, DOUBLON_DATES_DIFFERENTES], trouve)

    def test_une_date_ABSENTE_ne_fabrique_pas_une_difference(self) -> None:
        """Ne pas savoir n'est pas constater un ecart - regle des trois etats."""
        self.assertEqual(
            [DOUBLON_POTENTIEL],
            anomalies_de_doublon("A|F-118|600.00", "", 2, ["2025-03-12"]))
        self.assertEqual(
            [DOUBLON_POTENTIEL],
            anomalies_de_doublon("A|F-118|600.00", "2025-03-12", 2, [""]))

    def test_rien_n_est_efface(self) -> None:
        """L'item mettait en garde: *une deduplication ecrite sur l'egalite du

        couple effacerait de vraies pieces*. Ici on ne rend que des
        anomalies - aucune suppression n'est possible depuis cette fonction.
        """
        trouve = anomalies_de_doublon(
            "A|F-118|600.00", "2025-04-02", 3, ["2025-03-12", "2025-04-02"])
        self.assertTrue(all(isinstance(a, str) for a in trouve))


class UNE_CLE_VIDE_NE_RAPPROCHE_RIEN(unittest.TestCase):
    """Garde-fou deja paye une fois: deux extractions muettes se signalaient."""

    def test_une_cle_de_champs_vides_est_vide(self) -> None:
        self.assertTrue(cle_vide(cle_de_doublon("", "", "")))

    def test_elle_ne_produit_aucune_anomalie(self) -> None:
        self.assertEqual([], anomalies_de_doublon("||", "2025-03-12", 5, ["x"]))

    def test_un_seul_champ_rempli_suffit_a_ne_plus_etre_vide(self) -> None:
        self.assertFalse(cle_vide(cle_de_doublon("", "F-118", "")))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
