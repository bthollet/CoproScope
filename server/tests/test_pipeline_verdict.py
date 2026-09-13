# -*- coding: utf-8 -*-
"""Le verdict d'un passage derive de ce que les etapes declarent.

**Le cas reel que ces tests figent**, mesure le 2026-09-08 sur une instance vide
reconstruite: un passage construit 400 resolutions, **ecrase 84 cles** en les
nommant une par une, en depose 206 en base - et conclut `status: ok`.

Le calculateur de statut testait deux cles precises, `coffre_non_declare` et
`registre_vide`. Deux modalites observees le jour ou la ligne fut ecrite. Toute
autre facon de perdre quelque chose n'y figurait pas.
"""

from __future__ import annotations

import unittest

from coproscope.core._pipeline_verdict import (
    STATUT_INCOMPLET,
    STATUT_OK,
    STATUT_PERTES,
    verdict_du_passage,
)


def etape(nom: str, **resultat: object) -> dict[str, object]:
    return {"etape": nom, "resultat": dict(resultat)}


class VerdictDuPassage(unittest.TestCase):
    def test_une_perte_declaree_interdit_le_statut_ok(self) -> None:
        """Le cas mesure: 84 cles ecrasees, et le passage se disait `ok`."""
        verdict = verdict_du_passage(
            [etape("resolutions", motifs_alerte=["84 cles de resolution ecrasees"])]
        )
        self.assertEqual(STATUT_PERTES, verdict["statut"])
        self.assertEqual(["resolutions: 84 cles de resolution ecrasees"], verdict["pertes_declarees"])

    def test_une_perte_d_un_genre_INCONNU_compte_aussi(self) -> None:
        """La propriete qui remplace l'enumeration de deux cles.

        Le motif est un texte libre que l'etape ecrit en ses propres termes. Le
        verdict n'a donc pas a connaitre les facons de perdre quelque chose - il
        n'en connait aucune, et c'est ce qui le rend juste pour la prochaine.
        """
        verdict = verdict_du_passage(
            [etape("etape_future", motifs_alerte=["un genre de perte que personne n'a prevu"])]
        )
        self.assertEqual(STATUT_PERTES, verdict["statut"])

    def test_un_empechement_l_emporte_sur_une_perte(self) -> None:
        verdict = verdict_du_passage(
            [
                etape("resolutions", motifs_alerte=["deux cles ecrasees"]),
                etape("actes", registre_vide=True),
            ]
        )
        self.assertEqual(STATUT_INCOMPLET, verdict["statut"])
        self.assertEqual(["actes: registre_vide"], verdict["empechements"])

    def test_une_etape_qui_ne_declare_RIEN_n_est_pas_reputee_reussie(self) -> None:
        """La degradation qui compte le plus.

        Une etape ajoutee demain sans bilan apparait en creux, au lieu de
        disparaitre dans un `ok`. C'est la difference entre une absence de
        mesure et une mesure conforme.
        """
        verdict = verdict_du_passage([etape("ag")])
        self.assertEqual(["ag"], verdict["etapes_sans_bilan"])

    def test_rien_a_declarer_se_distingue_de_rien_de_declare(self) -> None:
        verdict = verdict_du_passage([etape("resolutions", motifs_alerte=[])])
        self.assertEqual(STATUT_OK, verdict["statut"])
        self.assertEqual([], verdict["etapes_sans_bilan"])
        self.assertEqual([], verdict["pertes_declarees"])

    def test_un_motif_unique_en_chaine_est_accepte(self) -> None:
        verdict = verdict_du_passage([etape("resolutions", motifs_alerte="une perte")])
        self.assertEqual(STATUT_PERTES, verdict["statut"])

    def test_un_resultat_non_dictionnaire_ne_fait_pas_tomber_le_verdict(self) -> None:
        verdict = verdict_du_passage([{"etape": "ag", "resultat": None}])
        self.assertEqual(["ag"], verdict["etapes_sans_bilan"])

    def test_les_trois_listes_sont_toujours_rendues(self) -> None:
        verdict = verdict_du_passage([])
        for cle in ("empechements", "pertes_declarees", "etapes_sans_bilan"):
            self.assertIn(cle, verdict)
            self.assertEqual([], verdict[cle])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
