# -*- coding: utf-8 -*-
"""Ne pas savoir ce qu'une decision EST n'empeche pas de savoir ce qu'elle N'EST PAS.

`RM-2026-0116`. Brice, revue du 2026-09-07 a 05:45, a propos du vote des
comptes: *« il ne peut pas etre dans les marches. On ne peut pas dire que c'est
au-dessus du seuil. Il faut le sortir, c'est a part. »*

**Le defaut, mesure le 2026-09-08, n'etait pas ou l'item le cherchait.** La
table des controles donnait deja raison a Brice: elle declare le seuil non
applicable a une approbation de comptes, et ecrit pourquoi. C'est le CLASSEMENT
qui ratait. `portee_resolution` exige, pour typer une approbation de comptes,
que la periode visee soit lisible ET close; `periode_close` rend `None` quand
elle ne sait pas, et le code traitait ce `None` comme un `False`. La resolution
retombait donc sur `ORDINAIRE`, **le seau generique qui porte les controles de
seuil**.

Contre-intuitif et mesure: le libelle *Approbation des comptes de l'exercice
CLOS au 31 decembre 2024* rendait `ORDINAIRE`, tandis que le libelle vague
*Approbation des comptes de l'exercice 2024* rendait `APPROBATION_COMPTES`. Le
libelle qui dit explicitement `exercice clos` etait celui qui echouait.

**L'intention du module etait juste, sa consequence ne l'etait pas.** Sa
docstring dit *une resolution non typee garde tous ses controles*: c'est de la
prudence sur le typage, et elle est bien vue - fabriquer un type serait pire.
Mais garder tous ses controles fait heriter un doute de contraintes qui ne le
concernent pas. La prudence sur le typage etait devenue une imprudence sur les
controles.
"""
from __future__ import annotations

import unittest

from coproscope.modules._resolutions_exclusions import controles_exclus
from coproscope.modules._resolutions_qualification import portee_resolution

AG = "2025-06-01"


def seuil_exclu(texte: str) -> bool:
    return any(e["controle"] == "SEUIL" for e in controles_exclus(texte))


class CeQuUneDecisionNePeutPasEtre(unittest.TestCase):
    def test_le_vote_des_comptes_sort_des_marches_meme_sans_periode_lisible(self):
        """Le cas de Brice, dans les deux redactions qui se comportaient differemment."""
        for texte in (
            "Approbation des comptes de l'exercice clos au 31 decembre 2024",
            "Approbation des comptes de l'exercice 2024",
            "Approbation des comptes annuels",
            "Arrete des comptes du syndicat",
        ):
            with self.subTest(texte=texte):
                self.assertTrue(
                    seuil_exclu(texte),
                    "le seuil doit etre exclu: une approbation de comptes ne passe aucun marche",
                )

    def test_l_exclusion_ne_depend_pas_de_la_portee_obtenue(self):
        """L'axe: la portee dit ce que la decision EST, l'exclusion ce qu'elle n'est PAS.

        Ces deux libelles obtiennent des portees differentes - l'un est encore
        `ORDINAIRE` faute de periode lisible - et pourtant tous deux excluent le
        seuil. C'est exactement l'independance que l'item a etablie: ne pas
        savoir la premiere n'empeche pas de savoir la seconde.
        """
        vague = "Approbation des comptes annuels"
        date = "Approbation des comptes de l'exercice 2024"
        self.assertNotEqual(portee_resolution(vague, AG)[0], portee_resolution(date, AG)[0])
        self.assertTrue(seuil_exclu(vague))
        self.assertTrue(seuil_exclu(date))

    def test_le_quitus_et_l_election_sortent_aussi(self):
        for texte in ("Quitus au syndic pour sa gestion de l'exercice ecoule",
                      "Election des membres du conseil syndical"):
            with self.subTest(texte=texte):
                self.assertTrue(seuil_exclu(texte))

    def test_une_decision_qui_passe_un_marche_garde_son_seuil(self):
        """Le controle negatif: l'exclusion doit savoir NE PAS s'appliquer."""
        for texte in (
            "Travaux de ravalement de la facade sud, devis de l'entreprise retenue",
            "Fixation du montant des marches et contrats a partir duquel la consultation "
            "du conseil syndical est obligatoire",
            "Renouvellement du contrat d'entretien de l'ascenseur",
        ):
            with self.subTest(texte=texte):
                self.assertFalse(seuil_exclu(texte),
                                 "une decision qui passe un marche garde son controle de seuil")

    def test_une_resolution_MIXTE_garde_son_seuil(self):
        """La degradation la plus importante, et elle penche du bon cote.

        Un texte qui approuve les comptes ET vote des travaux avec devis
        n'obtient AUCUNE exclusion: on ne peut pas prouver qu'il ne passe aucun
        marche, donc le controle reste. Se taire laisse un controle inutile, ce
        qui coute une verification humaine; exclure a tort effacerait un controle
        du, ce qui coute une fuite. Le defaut penche du cote le moins cher.
        """
        mixte = "Approbation des comptes et vote des travaux de toiture, devis joint"
        self.assertFalse(seuil_exclu(mixte))

    def test_chaque_exclusion_porte_son_motif_et_son_fondement(self):
        """Conservation: une exclusion sans motif est une suppression silencieuse."""
        for e in controles_exclus("Approbation des comptes annuels"):
            with self.subTest(controle=e["controle"]):
                self.assertTrue(e["motif"].strip(), "une exclusion doit dire pourquoi")
                self.assertTrue(e["fondement"].strip(), "une exclusion doit citer son fondement")
                self.assertIn("21", e["fondement"])


if __name__ == "__main__":
    unittest.main()
