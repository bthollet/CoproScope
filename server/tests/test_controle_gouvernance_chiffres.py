# -*- coding: utf-8 -*-
"""Les nombres que l'ecran de gouvernance affiche, et d'ou ils viennent.

Extrait de `test_controle_gouvernance.py` le 2026-09-10: ce fichier passait a
618 lignes pour une limite de 600, et la doctrine du depot fait de l'extraction
le chantier prioritaire des qu'un fichier la franchit. La coupure suit une
classe entiere - les nombres du titre - et n'invente aucun decoupage.

Le socle, la fixture et l'instance de recette restent dans le module d'origine:
les dupliquer ferait deux corpus qui divergeraient au premier changement.
"""

from __future__ import annotations

import unittest

from coproscope.modules import actes_autorisation as A
from coproscope.web import _controle_gouvernance_constats as C
from tests.test_controle_gouvernance import CORPUS, CORPUS_NON_TYPE, _Socle, _acte


class LeChiffreDuTitreTests(_Socle):
    """Le nombre le plus visible de l'ecran mesure des pieces, jamais un vide.

    Defaut mesure le 2026-09-04, versement de 173 actes, table
    `liens_gouvernance` vide comme dans le produit: `v_constats` rendait SIX
    lignes et l'ecran annonçait « 157 points a instruire sur 173 decisions
    lues ». Les 154 de l'ecart etaient les actes de portee ORDINAIRE, dont la
    cellule d'avis est ABSENT parce qu'aucune ligne n'existe dans
    `liens_gouvernance` - et la pastille qui portait ce chiffre affirmait en
    plus « la consultation prealable est exigible sur ce type », sur des actes
    dont le type n'avait justement pas ete reconnu.

    Un conseil syndical qui ecrit au syndic sur cette base reclame 154 avis pour
    des resolutions dont beaucoup - les designations, l'approbation des comptes
    - n'en exigent aucun.
    """

    def setUp(self) -> None:
        super().setUp()
        self._alimenter(CORPUS_NON_TYPE)

    def test_le_titre_ne_compte_que_ce_que_les_pieces_etablissent(self) -> None:
        vue = self._vue()
        # Ce test exigeait zero constat AU MODELE. Il voulait dire zero
        # reclamation AU SYNDIC, et les deux ont cesse d'etre la meme chose le
        # 2026-09-05: `EXECUTION_NON_CONTROLABLE` nomme desormais les actes
        # adoptes sans montant lu, ou le rapprochement vote/paye ne peut pas
        # etre conduit. Ces lignes DOIVENT exister - sans elles, une file vide
        # se lit `tout a ete execute` - et elles ne doivent surtout pas etre
        # envoyees au syndic, qui n'y peut rien: c'est l'outil qui n'a pas su
        # lire. D'ou la mesure ci-dessous, qui porte sur le partage et non sur
        # le total: aucun de ces constats n'est une demande.
        codes = {c["code"] for c in A.constats(self.instance)}
        self.assertEqual(codes, {"EXECUTION_NON_CONTROLABLE"})
        self.assertEqual(
            vue["a_demander"],
            0,
            "aucun constat au modele: le nombre qui commande le courrier au "
            "syndic doit valoir zero, pas 154",
        )
        self.assertEqual(vue["a_outiller"], 154)
        self.assertIn("0 points à instruire", vue["lead"])

    def test_ce_que_l_outil_ne_sait_pas_est_compte_a_part_et_nomme(self) -> None:
        """**Ce test exigeait `avis_manquant`, et la phrase est citee ici.**

        Il ecrivait `self.assertIn("avis_manquant", cles)`. Depuis le
        2026-09-10 (`RM-2026-0164`), la question de l'avis se pose sous DEUX
        pastilles: `avis_manquant` quand un seuil de consultation est rattache,
        `avis_sans_exigence` quand aucun ne l'est. Sur ce corpus de recette,
        aucun acte ne porte de seuil rattache: **toutes ses lignes tombent donc,
        a juste titre, dans la seconde** - et exiger la premiere reviendrait a
        exiger que l'ecran presente comme exigible une piece qu'aucun texte ne
        reclame ici.

        Ce qui est garde est l'invariant: la question de l'avis est comptee, et
        elle est comptee du cote de l'OUTIL, jamais parmi ce que les pieces
        etablissent.
        """
        vue = self._vue()
        cles = {m["constat"]["cle"] for m in vue["constats_outil"]}
        self.assertTrue(
            cles & {"avis_manquant", "avis_sans_exigence"},
            "la question de l'avis du conseil syndical n'est comptee sous "
            "aucune de ses deux formes",
        )
        self.assertIn("type_non_reconnu", cles)
        self.assertFalse(
            {"avis_manquant", "avis_sans_exigence"}
            & {m["constat"]["cle"] for m in vue["constats"]},
            "un trou de l'outil ne se reclame a personne: il ne peut pas figurer "
            "parmi ce que les pieces etablissent",
        )

    def test_aucune_pastille_n_affirme_une_exigibilite_sur_un_type_non_reconnu(self) -> None:
        avis = C.CONSTAT_PAR_CLE["avis_manquant"]
        texte = avis["titre"] + " " + avis["aide"]
        self.assertNotIn("exigible", texte)
        self.assertEqual(avis["source"], C.SOURCE_OUTIL)

    def test_une_cellule_que_l_outil_ne_remplit_pas_n_est_pas_une_chaine_rompue(self) -> None:
        """`lignes_marquees` peignait ces 154 lignes en chaine rompue dans le
        tableau, pour la seule raison qu'une table du produit est vide."""
        vue = self._vue({"vue": "tableau"})
        self.assertEqual(vue["ruptures_visibles"], 0)
        self.assertEqual(vue["calme"], 154)
