# -*- coding: utf-8 -*-
"""Une piece absente n'est un manquement que la ou un texte l'exige.

Instruction de `RM-2026-0164`, dans les mots de l'item: *une absence de devis
N'EST PAS un manquement et ne doit pas etre presentee en rouge parmi les pieces
a reclamer* - et son axe: **ce qui VARIE d'une ligne a l'autre, c'est ce que le
franchissement du montant rend obligatoire; ce qui reste INVARIANT, c'est qu'une
exigence a toujours un fondement, et qu'en son absence il n'y a pas manquement
mais simple absence.**

**Pourquoi ce partage n'existait pas avant le 2026-09-10.** Le predicat *un
texte exige cette piece* n'avait aucune donnee: les relations
`SEUIL_CONSULTATION_CS_APPLICABLE` et `SEUIL_CONCURRENCE_APPLICABLE` etaient
**absentes de la base**, parce que les assemblees qui arretent ces montants
n'avaient pas de date lue, donc pas de fenetre de validite, donc aucun lien. La
reabsorption complete sur instance VIDE - 858 pieces sources - les a fait
apparaitre: **274 et 276 liens**.

**La mesure qui a decide de la forme.** Sur cette base, 293 lignes portent une
cellule d'avis `manquante`. Elles se partagent en **219 dont un seuil de
consultation est rattache** et **74 qui n'en portent aucun**. Les melanger
faisait lire soixante-quatorze absences qu'aucun texte n'exige comme des pieces
a reclamer.

**Et c'est une RECIDIVE, l'item le dit lui-meme:** le meme defaut avait ete
corrige le 2026-09-04 sur cette meme colonne - mais **en paroles seulement**.
La prose disait deja *sans en deduire un manquement*; le NOMBRE, lui, restait le
comptage brut des cellules vides. Une correction qui traite un cas et pas une
propriete revient par la porte.

**Ce que ce module NE dit pas, et c'est le residu central.** `SEUIL_RATTACHE`
ne signifie pas *la consultation est obligatoire ici*. Il signifie qu'un montant
declencheur existe. Savoir si le montant de l'acte le FRANCHIT demande une
comparaison que le modele ne fait pas - c'est le trou T9, declare ouvert. Les
219 ne sont donc pas des manquements: ce sont des lignes dont l'exigence reste a
etablir. Les 74, elles, sont tranchees.
"""

from __future__ import annotations

import unittest

from coproscope.web import _controle_gouvernance_constats as C
from coproscope.web._controle_gouvernance_source import (
    EXIGENCE_AUCUN_SEUIL,
    EXIGENCE_SANS_OBJET,
    EXIGENCE_SEUIL_RATTACHE,
    _exigence_avis,
    appliquer_filtres,
)


def _ligne(statut_avis: str, exigence: str, identifiant: str = "L") -> dict:
    """Une ligne reduite a ce que le predicat lit."""
    return {"id": identifiant, "statut_avis": statut_avis,
            "exigence_avis": exigence, "conclusion": "a_instruire"}


class L_EXIGENCE_SE_LIT_ELLE_NE_SE_DEDUIT_PAS(unittest.TestCase):
    """Trois valeurs, et la troisieme est celle qu'on oublie."""

    def test_un_seuil_rattache_donne_SEUIL_RATTACHE(self) -> None:
        self.assertEqual(
            EXIGENCE_SEUIL_RATTACHE,
            _exigence_avis({"cel_avis_cs": "ABSENT", "nb_seuil_consultation_cs": 1}),
        )

    def test_AUCUN_seuil_rattache_donne_AUCUN_SEUIL(self) -> None:
        """La valeur qui tranche: aucun texte n'exige la piece sur cette ligne."""
        for valeur in (0, "", None, "0"):
            with self.subTest(valeur=valeur):
                self.assertEqual(
                    EXIGENCE_AUCUN_SEUIL,
                    _exigence_avis({"cel_avis_cs": "ABSENT",
                                    "nb_seuil_consultation_cs": valeur}),
                )

    def test_un_controle_retire_donne_SANS_OBJET(self) -> None:
        """La question ne se pose pas: ce n'est ni une exigence ni son absence."""
        self.assertEqual(
            EXIGENCE_SANS_OBJET,
            _exigence_avis({"cel_avis_cs": "NON_APPLICABLE",
                            "nb_seuil_consultation_cs": 0}),
        )

    def test_une_valeur_illisible_ne_fabrique_pas_une_exigence(self) -> None:
        """Hors des valeurs observees, on degrade vers *aucun texte ne l'exige*.

        C'est le sens prudent: inventer une exigence ferait reclamer une piece
        au syndic sans fondement, ce qui est la faute que cet item combat.
        """
        self.assertEqual(
            EXIGENCE_AUCUN_SEUIL,
            _exigence_avis({"cel_avis_cs": "ABSENT",
                            "nb_seuil_consultation_cs": "deux"}),
        )


class LES_DEUX_PASTILLES_PARTAGENT_SANS_PERTE(unittest.TestCase):
    """Aucune ligne perdue, aucune comptee deux fois."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.avis_exigible = next(
            c for c in C.CONSTATS if c["cle"] == "avis_manquant")
        cls.avis_sans_exigence = next(
            c for c in C.CONSTATS if c["cle"] == "avis_sans_exigence")
        cls.lignes = (
            [_ligne("manquante", EXIGENCE_SEUIL_RATTACHE, f"S{i}") for i in range(7)]
            + [_ligne("manquante", EXIGENCE_AUCUN_SEUIL, f"A{i}") for i in range(3)]
            + [_ligne("non_applicable", EXIGENCE_SANS_OBJET, "N0")]
            + [_ligne("confirmer", EXIGENCE_SEUIL_RATTACHE, "C0")]
        )

    def test_LE_PARTAGE_EST_EXACT(self) -> None:
        exigibles = appliquer_filtres(self.lignes, self.avis_exigible["filtre"])
        sans = appliquer_filtres(self.lignes, self.avis_sans_exigence["filtre"])
        self.assertEqual(7, len(exigibles))
        self.assertEqual(3, len(sans))
        manquantes = appliquer_filtres(self.lignes, {"avis": "manquante"})
        self.assertEqual(len(manquantes), len(exigibles) + len(sans),
                         "des lignes sans avis n'entrent dans aucune des deux")
        self.assertEqual(set(), {l["id"] for l in exigibles} & {l["id"] for l in sans},
                         "une ligne est comptee dans les deux pastilles")

    def test_CELLE_QUI_NE_RECLAME_RIEN_LE_DIT_DANS_SON_INTENTION(self) -> None:
        """Un nombre sans intention se lit comme une pile de reproches."""
        intention = self.avis_sans_exigence["intention"].lower()
        self.assertIn("ne rien réclamer", intention)
        self.assertNotEqual("warn", self.avis_sans_exigence["ton"],
                            "une piece que rien n'exige n'est pas a surveiller")

    def test_CELLE_QUI_RESTE_NE_CONCLUT_PAS_AU_MANQUEMENT(self) -> None:
        """Un seuil qui EXISTE n'est pas un seuil FRANCHI: trou T9, ouvert."""
        self.assertIn("sans en déduire", self.avis_exigible["intention"].lower())

    def test_les_deux_pastilles_sont_des_constats_de_L_OUTIL(self) -> None:
        """Un trou de l'outil ne se reclame a personne, donc il n'entre pas
        dans l'arithmetique du courrier au syndic."""
        self.assertEqual(C.SOURCE_OUTIL, self.avis_exigible["source"])
        self.assertEqual(C.SOURCE_OUTIL, self.avis_sans_exigence["source"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
