# -*- coding: utf-8 -*-
"""« Ce document a-t-il un type etabli ? » se tranche a UN seul endroit.

`RM-2026-0056`, residu mesure le 2026-09-11. Le lot de reparation avait ete
**refute 4 fois sur 4**, et l'une des refutations portait exactement ceci: *une
TROISIEME liste de modalites vit 380 lignes plus bas DANS LE MEME FICHIER*.
`core/classement_etabli` avait resolu la question pour le STATUT de classement;
elle restait ouverte pour le TYPE.

**Mesure: six endroits tranchaient la meme question, chacun a sa facon.**

    `04_completeness_and_kpis:196`   `document_type in {"", "A_CLASSER"}`
    `04_completeness_and_kpis:228`   `status == "A_CLASSER"`
    `document_intake_route:202`      `document_type == "A_CLASSER"`
    `document_intake_route:282`      `document_type == "A_CLASSER"`
    `document_intake_route:333`      `document_type.upper() == "A_CLASSER"`
    `_document_selection:8`          `document_type not in {"", "Document"}`

**Elles divergent deja par ecrit**: l'une compte le type VIDE, une autre non,
une troisieme normalise la casse, une quatrieme ajoute `Document`.

**ET POURTANT ELLES DONNENT LE MEME NOMBRE SUR LE CORPUS - 83 sur 858 - ce qui
est precisement ce qui rend le defaut dangereux.** Elles coincident par
ACCIDENT: aucun document du corpus ne porte un type vide. Or le modele admet
explicitement le vide a l'ecriture. Le jour ou un document arrive sans type,
`in {"", "A_CLASSER"}` le compte et `== "A_CLASSER"` ne le compte pas - deux
compteurs pour la meme notion, divergeant en silence. C'est le defaut numero un
du produit, a l'etat latent.

**L'AXE.** Ce qui VARIE: l'ecriture du type, sa casse, ses blancs, le fait
qu'il soit absent ou marque `A_CLASSER`. Ce qui reste INVARIANT: **un document
dont le type n'est pas affirme est un document que quelqu'un doit regarder**, et
cela ne depend pas de la maniere dont l'absence est ecrite.

**C'est le meme choix que le cas d'egalite du franchissement et que l'exclusion
du contrat de syndic, tranches le meme jour: ecrire la regle tant qu'elle ne
coute rien, plutot que le jour ou elle decidera d'un chiffre affiche.**
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from coproscope.core.classement_etabli import (
    TYPE_A_CLASSER,
    type_doit_remonter_a_l_humain,
    type_est_etabli,
)

DEPOT = Path(__file__).resolve().parents[2]
SRC = DEPOT / "server/src/coproscope"

#: Les modules qui tranchent cette question et doivent passer par la fonction.
BRANCHES = (
    Path("modules/_docuscope_parts/04_completeness_and_kpis.py"),
    Path("web/document_intake_route.py"),
)


class LES_SIX_ECRITURES_RENDENT_LE_MEME_VERDICT(unittest.TestCase):
    """Ce que les six lectures faisaient differemment."""

    def test_le_type_vide_remonte(self) -> None:
        """`== "A_CLASSER"` ne le comptait pas; `in {"", "A_CLASSER"}` si."""
        self.assertTrue(type_doit_remonter_a_l_humain(""))

    def test_le_type_absent_remonte_aussi(self) -> None:
        """`None` arrive quand la colonne n'existe pas dans la ligne."""
        self.assertTrue(type_doit_remonter_a_l_humain(None))

    def test_la_casse_ne_change_rien(self) -> None:
        """Un seul des six modules appliquait `.upper()`."""
        for ecriture in ("A_CLASSER", "a_classer", "A_Classer"):
            with self.subTest(ecriture=ecriture):
                self.assertTrue(type_doit_remonter_a_l_humain(ecriture))

    def test_les_blancs_non_plus(self) -> None:
        self.assertTrue(type_doit_remonter_a_l_humain("  A_CLASSER  "))

    def test_un_type_reel_ne_remonte_pas(self) -> None:
        for reel in ("Facture", "PV_AG", "Contrat_Fournisseur"):
            with self.subTest(type=reel):
                self.assertTrue(type_est_etabli(reel))

    def test_les_deux_fonctions_sont_bien_complementaires(self) -> None:
        """Si elles divergeaient, on aurait recree le defaut a l'interieur du
        module cense le corriger."""
        for valeur in ("", None, "A_CLASSER", "Facture", "Document", "  "):
            with self.subTest(valeur=valeur):
                self.assertNotEqual(
                    type_est_etabli(valeur),
                    type_doit_remonter_a_l_humain(valeur))


class LE_LITTERAL_NE_SURVIT_PLUS_DANS_LES_BRANCHES(unittest.TestCase):
    """**La garde d'adoption: livrer et adopter sont deux choses.**

    Trois lots ont ete refuses ce mois-ci pour avoir livre un correctif que
    personne n'appelait. La garde verifie donc que les modules qui tranchent
    cette question passent par la fonction, et qu'ils ne portent plus le
    litteral dans une comparaison.
    """

    #: Une COMPARAISON du TYPE au litteral. Trois precisions, chacune payee.
    #:
    #: 1. Pas la simple presence: `TYPE_A_CLASSER = "A_CLASSER"` est la
    #:    DECLARATION, et c'est l'endroit unique ou la valeur est dite.
    #: 2. **Le nom `document_type` doit figurer sur la ligne.** Premiere
    #:    version sans cette condition: elle attrapait
    #:    `_status_action:228`, `if status == "A_CLASSER"` - un statut de
    #:    completude de PREUVE, dont les valeurs sont `PRESENT`, `OBSOLETE`,
    #:    `A_CLASSER`. **Deux domaines emploient la meme chaine pour deux
    #:    notions differentes**, et une garde qui ne lit que la chaine
    #:    condamne le voisin innocent. Residu nomme: cette collision de
    #:    vocabulaire subsiste, elle n'est pas traitee ici.
    #: 3. Les commentaires sont exclus par l'appelant: la docstring de ce
    #:    module cite les six ecritures pour les expliquer.
    COMPARAISON = re.compile(
        r'document_type[^\n]{0,40}?(?:==|!=|\sin\s)\s*\{?\s*(?:""\s*,\s*)?"A_CLASSER"')

    def test_chaque_branche_appelle_la_fonction(self) -> None:
        for relatif in BRANCHES:
            with self.subTest(module=str(relatif)):
                source = (SRC / relatif).read_text(encoding="utf-8")
                self.assertIn(
                    "type_doit_remonter_a_l_humain", source,
                    "ce module tranche le type sans passer par la fonction "
                    "canonique: une septieme ecriture est nee")

    def test_aucune_branche_ne_compare_le_litteral_a_la_main(self) -> None:
        for relatif in BRANCHES:
            with self.subTest(module=str(relatif)):
                source = (SRC / relatif).read_text(encoding="utf-8")
                lignes = [
                    ligne for ligne in source.splitlines()
                    if not ligne.lstrip().startswith("#")
                    and self.COMPARAISON.search(ligne)
                ]
                self.assertEqual(
                    [], lignes,
                    "une comparaison au litteral subsiste: elle divergera du "
                    "jour ou la normalisation changera")

    def test_le_motif_de_la_garde_reconnait_bien_ce_qu_il_vise(self) -> None:
        """**Temoin de sante.** Une garde qui ne reconnait rien passe toujours -
        defaut rencontre trois fois dans ce depot le meme jour."""
        for faute in ('document_type == "A_CLASSER"',
                      'doc.get("document_type", "") in {"", "A_CLASSER"}',
                      'document_type.upper() == "A_CLASSER"'):
            with self.subTest(faute=faute):
                self.assertTrue(self.COMPARAISON.search(faute))

    def test_il_ne_condamne_pas_la_DECLARATION_de_la_constante(self) -> None:
        """`TYPE_A_CLASSER = "A_CLASSER"` doit rester possible: c'est
        l'endroit unique ou la valeur est dite."""
        self.assertIsNone(self.COMPARAISON.search('TYPE_A_CLASSER = "A_CLASSER"'))
        self.assertEqual("A_CLASSER", TYPE_A_CLASSER)

    def test_il_epargne_le_STATUT_de_preuve_qui_porte_la_meme_chaine(self) -> None:
        """**Le temoin qui a fait corriger la garde.** `_status_action` teste
        un statut de completude - `PRESENT`, `OBSOLETE`, `A_CLASSER` - et non
        un type de document. Deux domaines, une meme chaine."""
        self.assertIsNone(
            self.COMPARAISON.search('    if status == "A_CLASSER":'))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
