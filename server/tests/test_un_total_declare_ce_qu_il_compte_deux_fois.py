# -*- coding: utf-8 -*-
"""Un total qui somme des assemblees dit ce qu'il compte plusieurs fois.

Instruction de `RM-2026-0077`, dans ses mots: *annoter un rang ne corrige pas
un TOTAL. La reponse n'est pas d'elire ni de dedoublonner, c'est la
CONSERVATION: un total declare combien de ses lignes reposent sur un rang
marque concurrent.*

**LE DEFAUT QUE CE FICHIER EXISTE POUR EMPECHER, et il a la pire forme qui
soit.** La garde precedente, `_resolutions_assemblees.copies_concurrentes`, ne
parle que si **au moins une des assemblees n'a pas de date lue**. Cette
condition tenait sur le corpus qui l'a fait naitre. Puis le correctif de
lecture de date du 2026-09-08 a rendu leur date aux copies - une amelioration
reelle - et **la garde s'est tue au moment meme ou le defaut redevenait
invisible**. Aucun test n'a echoue. Une modalite avait ete prise pour un axe.

**La mesure, sur une instance VIDE reabsorbant 858 pieces sources, le
2026-09-10.** Sept paires d'assemblees partagent des objets identiques;
**six sont muettes pour la garde existante**. La plus grosse des six oppose
deux assemblees toutes deux datees et partage 25 objets sur un bloc de rangs
contigu. Au total, **238 actes sur 550** portent un objet qui existe aussi
sous une autre assemblee, et **deux assemblees n'apportent aucun objet qui
leur soit propre**.

**Ce que ces tests NE demandent pas.** Ils ne demandent jamais qu'un
recouvrement soit qualifie de doublon. Le module refuse d'elire, et ce refus
est teste au meme titre que le compte: un corpus ou deux assemblees partagent
une resolution de seance recurrente doit produire un chiffre, pas un reproche.
"""

from __future__ import annotations

import unittest

from coproscope.modules._resolutions_assemblees import copies_concurrentes
from coproscope.modules._resolutions_recouvrement import (
    assemblees_incluses,
    conservation_du_total,
    recouvrements,
)
from coproscope.modules.pont_actes import _motifs_actes


def _acte(ag: str, numero: int, objet: str, sous: str = "") -> dict:
    """Un acte reduit a ce que la conservation lit."""
    return {
        "acte_id": f"{ag}-{numero}{sous}",
        "nature": "RESOLUTION_AG",
        "ag_id": ag,
        "numero": str(numero),
        "sous_numero": sous,
        "objet": objet,
        "doc_id": f"DOC-{ag}",
    }


#: Deux assemblees DATEES qui portent les memes objets. C'est le temoin du
#: defaut: il ne contient aucune assemblee sans date, donc la garde precedente
#: n'a rien a dire, et pourtant le total compte chaque objet deux fois.
TEMOIN_DEUX_DATEES = (
    [_acte("AG-2024-07-03", n, f"objet numero {n}") for n in range(1, 6)]
    + [_acte("AG-2024-10-01", n, f"objet numero {n}") for n in range(1, 6)]
)

#: Deux assemblees qui n'ont rien en commun. C'est le temoin de sante de
#: l'instrument: le critere doit pouvoir dire NON.
TEMOIN_RIEN_EN_COMMUN = (
    [_acte("AG-2024-07-03", n, f"une affaire de juillet {n}") for n in range(1, 6)]
    + [_acte("AG-2024-10-01", n, f"une affaire d'octobre {n}") for n in range(1, 6)]
)


class LA_GARDE_PRECEDENTE_EST_AVEUGLE_ICI(unittest.TestCase):
    """Le fait qui justifie un second module, ecrit comme un test.

    Si ce test venait a echouer parce que `copies_concurrentes` s'est mise a
    voir ce cas, ce fichier n'aurait plus lieu d'etre - et il faudrait le dire
    plutot que de garder deux mesures concurrentes pour la meme notion.
    """

    def test_copies_concurrentes_ne_voit_rien_quand_les_deux_dates_sont_lues(self):
        self.assertEqual({}, copies_concurrentes(TEMOIN_DEUX_DATEES))

    def test_la_conservation_LE_VOIT(self):
        conservation = conservation_du_total(TEMOIN_DEUX_DATEES)
        self.assertEqual(10, conservation["actes"])
        self.assertEqual(
            10, conservation["actes_partages"],
            "les dix lignes portent un objet present sous l'autre assemblee")


class L_INSTRUMENT_PEUT_DIRE_NON(unittest.TestCase):
    """Une garde qui ne sait pas se taire ne mesure rien."""

    def test_deux_assemblees_sans_objet_commun_ne_declarent_rien(self):
        conservation = conservation_du_total(TEMOIN_RIEN_EN_COMMUN)
        self.assertEqual(10, conservation["actes"])
        self.assertEqual(0, conservation["actes_partages"])
        self.assertEqual([], conservation["recouvrements"])
        self.assertEqual([], conservation["assemblees_entierement_partagees"])

    def test_et_aucun_motif_n_est_publie(self):
        motifs = _motifs_actes([], {}, [], conservation_du_total(TEMOIN_RIEN_EN_COMMUN))
        self.assertEqual([], motifs)

    def test_un_meme_rang_sans_le_meme_objet_ne_compte_pas(self):
        """Deux assemblees ont chacune une resolution n° 7, et alors ?

        C'est le faux positif que `_resolutions_assemblees` nomme deja. Le rang
        seul ne dit rien; c'est le libelle qui fait la matiere.
        """
        actes = [_acte("AG-2024-07-03", 7, "reprise de la toiture"),
                 _acte("AG-2026-06-17", 7, "ravalement de la facade est")]
        self.assertEqual(0, conservation_du_total(actes)["actes_partages"])


class LE_RECOUVREMENT_PARTIEL_RESTE_PARTIEL(unittest.TestCase):
    """Aucun seuil: un tiers partage se lit comme un tiers."""

    def setUp(self) -> None:
        self.actes = (
            [_acte("AG-2024-07-03", n, f"objet numero {n}") for n in range(1, 10)]
            + [_acte("AG-2024-10-01", n, f"objet numero {n}") for n in range(1, 4)]
            + [_acte("AG-2024-10-01", n, f"affaire propre {n}") for n in range(4, 10)]
        )

    def test_seules_les_lignes_partagees_sont_comptees(self):
        conservation = conservation_du_total(self.actes)
        self.assertEqual(18, conservation["actes"])
        self.assertEqual(6, conservation["actes_partages"], "trois de chaque cote")

    def test_une_assemblee_qui_garde_de_la_matiere_propre_n_est_pas_incluse(self):
        self.assertEqual([], assemblees_incluses(self.actes))

    def test_le_compte_par_assemblee_dit_la_proportion(self):
        par = conservation_du_total(self.actes)["par_assemblee"]
        self.assertEqual({"actes": 9, "partages": 3}, par["AG-2024-07-03"])
        self.assertEqual({"actes": 9, "partages": 3}, par["AG-2024-10-01"])


class DEUX_COPIES_EGALES_SONT_DITES_DES_DEUX_COTES(unittest.TestCase):
    """Le cas central de l'item, et celui qu'une inclusion STRICTE raterait.

    Deux copies d'un meme proces-verbal ont des jeux d'objets EGAUX. Aucune
    n'est un sous-ensemble propre de l'autre, donc une inclusion stricte les
    laisserait toutes les deux passer - en silence, et sur le cas que
    `RM-2026-0077` decrit depuis son ouverture.
    """

    def test_les_deux_sont_signalees(self):
        incluses = assemblees_incluses(TEMOIN_DEUX_DATEES)
        self.assertEqual(
            ["AG-2024-07-03", "AG-2024-10-01"],
            [e["assemblee"] for e in incluses])
        self.assertEqual(["AG-2024-10-01"], incluses[0]["contenue_dans"])
        self.assertEqual(["AG-2024-07-03"], incluses[1]["contenue_dans"])


class LE_DETAIL_RENDU_PERMET_A_UN_HUMAIN_DE_TRANCHER(unittest.TestCase):
    """Le module ne conclut pas; il rend de quoi conclure.

    Sur le corpus reel, un bloc de rangs contigu partage par exactement deux
    assemblees est presque surement un proces-verbal relu, tandis que deux
    objets portes par trois assemblees sont presque surement des resolutions de
    seance. `presque surement` n'est pas `surement`, donc c'est rendu, pas
    decide.
    """

    def test_un_bloc_contigu_est_annonce_comme_contigu(self):
        actes = (
            [_acte("AG-A", n, f"objet numero {n}") for n in range(1, 11)]
            + [_acte("AG-B", n, f"objet numero {n}") for n in range(6, 11)]
        )
        entree = recouvrements(actes)[0]
        self.assertEqual(5, entree["objets_communs"])
        self.assertEqual((6, 10), (entree["rang_min"], entree["rang_max"]))
        self.assertTrue(entree["bloc_contigu"])

    def test_des_rangs_epars_sont_annonces_epars(self):
        actes = (
            [_acte("AG-A", n, f"objet numero {n}") for n in range(1, 11)]
            + [_acte("AG-B", n, f"objet numero {n}") for n in (2, 5, 9)]
            + [_acte("AG-B", 99, "une affaire qui n'appartient qu'a B")]
        )
        entree = recouvrements(actes)[0]
        self.assertEqual(3, entree["objets_communs"])
        self.assertFalse(entree["bloc_contigu"])

    def test_un_objet_porte_par_plus_de_deux_assemblees_est_compte_a_part(self):
        """La formalite qui revient chaque annee, distinguee du reste."""
        seance = "election du president de seance"
        actes = [
            _acte("AG-A", 2, seance), _acte("AG-B", 2, seance),
            _acte("AG-C", 2, seance),
            _acte("AG-A", 3, "une affaire propre a A"),
            _acte("AG-B", 3, "une affaire propre a B"),
            _acte("AG-C", 3, "une affaire propre a C"),
        ]
        for entree in recouvrements(actes):
            self.assertEqual(1, entree["objets_communs"])
            self.assertEqual(
                1, entree["objets_portes_par_plus_de_deux"],
                "trois assemblees portent cet objet: c'est une formalite")

    def test_la_date_lue_est_RENDUE_mais_ne_conditionne_rien(self):
        """La modalite qui avait eteint la garde precedente est desormais une
        colonne d'information, jamais un filtre."""
        entree = recouvrements(TEMOIN_DEUX_DATEES)[0]
        self.assertEqual([True, True], entree["dates_lues"])
        self.assertEqual(5, entree["objets_communs"])


class LE_MOTIF_ENONCE_UN_FAIT_ET_PAS_UN_VERDICT(unittest.TestCase):
    """La conservation dit ce qu'elle sait; elle n'accuse pas."""

    def setUp(self) -> None:
        self.motifs = _motifs_actes(
            [], {}, [], conservation_du_total(TEMOIN_DEUX_DATEES))

    def test_un_motif_est_publie(self):
        self.assertEqual(1, len(self.motifs))

    def test_il_donne_le_compte_ET_son_total(self):
        self.assertIn("10 actes sur 10", self.motifs[0])

    def test_il_dit_la_CONSEQUENCE_sur_le_total(self):
        self.assertIn("les compte plusieurs fois", self.motifs[0])

    def test_il_ne_prononce_JAMAIS_le_mot_doublon(self):
        """Elire une copie serait poser une regle de preuve, et la mesure dit
        que le choix par defaut serait le mauvais."""
        for interdit in ("doublon", "copie a supprimer", "fait foi"):
            self.assertNotIn(interdit, self.motifs[0].lower())

    def test_il_nomme_les_assemblees_sans_matiere_propre(self):
        self.assertIn("n'apportent aucun objet", self.motifs[0])


class SEULES_LES_RESOLUTIONS_ENTRENT(unittest.TestCase):
    """Un acte d'une autre nature n'est pas une resolution d'assemblee."""

    def test_une_autre_nature_est_ignoree(self):
        actes = [
            _acte("AG-A", 1, "le meme objet"),
            dict(_acte("AG-B", 1, "le meme objet"), nature="AUTRE_CHOSE"),
        ]
        conservation = conservation_du_total(actes)
        self.assertEqual(1, conservation["actes"])
        self.assertEqual(0, conservation["actes_partages"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
