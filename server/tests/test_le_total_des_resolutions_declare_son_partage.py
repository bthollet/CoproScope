# -*- coding: utf-8 -*-
"""Le total affiche dit combien de ses lignes existent aussi ailleurs.

Point (1) du reste de `RM-2026-0077`, dans ses mots: *aucun ecran ne lit encore
`actes_partages` - les vues qui somment des assemblees affichent toujours un
total nu*.

**Le defaut.** `resolutions_view` rend `total = sum(ag["total"] for ag in
assemblees)`. Quand la meme matiere figure sous deux assemblees affichees, elle
entre deux fois dans cette somme, et un nombre nu ne le laisse pas voir. Mesure
du 2026-09-10 sur instance VIDE reabsorbant 858 pieces: **238 actes sur 550**
portent un objet present sous une autre assemblee, et deux assemblees
n'apportent aucun objet qui leur soit propre.

**Ce que la vue ne fait PAS, et c'est teste.** Elle ne dit jamais *doublons*,
elle n'elit pas, elle ne retranche rien du total. Elle DECLARE. La raison du
partage - proces-verbal relu, recueil, resolution de seance annuelle - reste
ouverte, et trancher demanderait de conclure sur une ressemblance, ce que
`C054` interdit.

**Le calcul n'est pas refait ici.** Il est delegue a
`_resolutions_recouvrement`, qui le porte deja. Deux implantations d'une meme
notion, c'est le defaut numero un du produit: plusieurs comptages concurrents
pour la meme chose.
"""

from __future__ import annotations

import unittest

from coproscope.web.resolutions_view import _conservation


def _assemblee(objets: list[tuple[str, str]]) -> dict:
    """Une assemblee affichable reduite a ce que la conservation lit."""
    return {"resolutions": [{"numero": n, "objet": o} for n, o in objets]}


TOITURE = ("1", "Refection de la toiture du batiment A")
FACADE = ("2", "Ravalement de la facade est")
ASCENSEUR = ("3", "Remplacement de la cabine d'ascenseur")
SEANCE = ("1", "Election du president de seance")


class L_INSTRUMENT_SAIT_SE_TAIRE(unittest.TestCase):
    """Sans ce temoin, tout ce qui suit pourrait passer au vert sans rien lire."""

    def test_aucune_assemblee_ne_declare_rien(self) -> None:
        self.assertEqual(0, _conservation([]))

    def test_une_seule_assemblee_ne_declare_rien(self) -> None:
        """Une assemblee ne se partage pas avec elle-meme."""
        self.assertEqual(0, _conservation([_assemblee([TOITURE, FACADE, ASCENSEUR])]))

    def test_deux_assemblees_sans_objet_commun_ne_declarent_rien(self) -> None:
        self.assertEqual(0, _conservation([
            _assemblee([TOITURE, FACADE]),
            _assemblee([("1", "Contrat d'entretien des espaces verts")]),
        ]))

    def test_un_meme_rang_avec_des_objets_DIFFERENTS_ne_compte_pas(self) -> None:
        """Deux assemblees ont chacune une resolution n° 1, et alors ?"""
        self.assertEqual(0, _conservation([
            _assemblee([("1", "Refection de la toiture")]),
            _assemblee([("1", "Ravalement de la facade")]),
        ]))


class LE_PARTAGE_SE_COMPTE_DES_DEUX_COTES(unittest.TestCase):
    """Le total les compte deux fois: il doit en declarer deux."""

    def test_deux_objets_partages_font_QUATRE_lignes_declarees(self) -> None:
        """C'est la propriete qui compte: le total additionne les DEUX copies.

        N'en declarer que deux laisserait croire qu'il suffit de retrancher
        deux, alors que le total en porte quatre.
        """
        self.assertEqual(4, _conservation([
            _assemblee([TOITURE, FACADE, ASCENSEUR]),
            _assemblee([TOITURE, FACADE]),
        ]))

    def test_seules_les_lignes_partagees_sont_declarees(self) -> None:
        partage = _conservation([
            _assemblee([TOITURE, FACADE, ASCENSEUR]),
            _assemblee([TOITURE]),
        ])
        self.assertEqual(2, partage, "l'ascenseur et la facade restent propres")

    def test_une_assemblee_ETRANGERE_n_est_pas_entrainee(self) -> None:
        self.assertEqual(4, _conservation([
            _assemblee([TOITURE, FACADE, ASCENSEUR]),
            _assemblee([TOITURE, FACADE]),
            _assemblee([("9", "Contrat d'entretien des espaces verts")]),
        ]))

    def test_un_objet_porte_par_TROIS_assemblees_compte_trois_fois(self) -> None:
        """Le cas de la resolution de seance qui revient chaque annee.

        Elle est declaree comme les autres: la vue ne juge pas de la raison du
        partage, elle dit que le total la compte plusieurs fois.
        """
        self.assertEqual(3, _conservation([
            _assemblee([SEANCE]), _assemblee([SEANCE]), _assemblee([SEANCE]),
        ]))


class LE_TOTAL_N_EST_PAS_CORRIGE_MAIS_DECLARE(unittest.TestCase):
    """Retrancher serait elire; l'item l'interdit explicitement."""

    def test_le_partage_ne_depasse_jamais_le_total(self) -> None:
        assemblees = [_assemblee([TOITURE, FACADE]), _assemblee([TOITURE, FACADE])]
        total = sum(len(a["resolutions"]) for a in assemblees)
        self.assertLessEqual(_conservation(assemblees), total)

    def test_deux_copies_ENTIERES_declarent_la_totalite(self) -> None:
        """Quand tout est partage, le compte declare vaut le total.

        Le lecteur voit alors que la sommation ne lui apprend rien sur le
        nombre de resolutions distinctes.
        """
        assemblees = [_assemblee([TOITURE, FACADE]), _assemblee([TOITURE, FACADE])]
        self.assertEqual(4, _conservation(assemblees))


class LA_VUE_EXPOSE_REELLEMENT_LE_COMPTE(unittest.TestCase):
    """**Ce test existe parce qu'une mutation NE MORDAIT PAS.**

    Tous les tests ci-dessus appellent `_conservation` en direct. Retirer
    `total_partage` du modele rendu par `build_resolutions_view` les laissait
    donc tous au vert: le calcul etait garde, **le cablage ne l'etait pas**.
    C'est la meme faute, en miniature, que celle que ce lot corrige - une
    mesure exacte portant sur autre chose que ce qu'on croit garder.
    """

    def _modele(self, lignes: list[dict]) -> dict:
        from unittest import mock

        from coproscope.web import resolutions_view as V

        with mock.patch.object(V, "store_path", lambda instance: "coffre"), \
             mock.patch.object(V, "lire", lambda instance: lignes):
            return V.build_resolutions_view(object())

    @staticmethod
    def _ligne(doc: str, ag: str, numero: int, objet: str, position: int) -> dict:
        return {"doc_id": doc, "ag_id": ag, "numero": str(numero),
                "sous_numero": "", "objet": objet, "position": str(position),
                "resultat": "ADOPTEE", "confiance": "forte"}

    def test_le_modele_PORTE_la_cle(self) -> None:
        modele = self._modele([
            self._ligne("DOC-A", "AG-2024-07-03", 1, "Refection de la toiture", 1),
        ])
        self.assertIn("total_partage", modele,
                      "la vue calcule le partage mais ne le rend pas")

    def test_deux_assemblees_qui_partagent_le_font_REMONTER_dans_le_modele(self) -> None:
        modele = self._modele([
            self._ligne("DOC-A", "AG-2024-07-03", 1, "Refection de la toiture", 1),
            self._ligne("DOC-A", "AG-2024-07-03", 2, "Ravalement de la facade", 2),
            self._ligne("DOC-B", "AG-2026-06-17", 1, "Refection de la toiture", 1),
            self._ligne("DOC-B", "AG-2026-06-17", 9, "Contrat espaces verts", 2),
        ])
        self.assertEqual(4, modele["total"])
        self.assertEqual(2, modele["total_partage"])

    def test_un_corpus_sans_partage_rend_ZERO_dans_le_modele(self) -> None:
        modele = self._modele([
            self._ligne("DOC-A", "AG-2024-07-03", 1, "Refection de la toiture", 1),
            self._ligne("DOC-B", "AG-2026-06-17", 1, "Contrat espaces verts", 1),
        ])
        self.assertEqual(0, modele["total_partage"])


class L_ABSENCE_DE_DONNEE_NE_LEVE_PAS(unittest.TestCase):
    """Une ligne incomplete ne doit ni lever ni fabriquer un partage."""

    def test_des_objets_vides_ne_se_partagent_pas_entre_eux(self) -> None:
        vide = [{"resolutions": [{"numero": "", "objet": ""}]},
                {"resolutions": [{"numero": "", "objet": ""}]}]
        self.assertEqual(0, _conservation(vide))

    def test_une_assemblee_sans_resolution_ne_leve_pas(self) -> None:
        self.assertEqual(0, _conservation([{"resolutions": []},
                                           _assemblee([TOITURE])]))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
