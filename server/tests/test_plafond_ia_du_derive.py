from __future__ import annotations

import unittest

from coproscope.core.privacy import _plafond_ia, apply_access_policy


"""Un derive caviarde porte SON plafond IA, pas celui de sa source.

Mesure du 2026-09-07 sur l'instance servie en 8788: 478 documents sur 825
etaient `no_ai`, parce que leur piece d'origine est en C7 ou C8. Le plafond
etait calcule sur `raw_max_college` seul, alors que `derivative_max_college`
existait deja et n'etait jamais consulte pour cela. Un document restait donc
interdit a l'IA meme apres avoir ete caviarde - ce qui annule la raison d'etre
du caviardage.

Le champ d'origine n'est pas touche: il decrit le brut, et `docai` s'en sert a
bon droit pour refuser de traiter la piece d'origine.
"""


class PlafondIaDuDerive(unittest.TestCase):
    def test_le_plafond_suit_le_college_qu_on_lui_donne(self) -> None:
        self.assertEqual(_plafond_ia("C8_Restreint_Critique"), "no_ai")
        self.assertEqual(_plafond_ia("C7_Contentieux_Secret"), "no_ai")
        self.assertEqual(_plafond_ia("C2_Coproprietaires"), "local_only")
        self.assertEqual(_plafond_ia("C4_Conseil_Syndical"), "local_only")

    def test_un_college_inconnu_ne_devient_pas_permissif_par_accident(self) -> None:
        """Hors des valeurs connues, on ne rend jamais `no_ai` par erreur...

        ...mais on ne rend pas non plus une valeur inventee. `local_only` est le
        defaut du produit, et il reste borne au poste.
        """

        self.assertEqual(_plafond_ia(""), "local_only")
        self.assertEqual(_plafond_ia("C99_Inconnu"), "local_only")

    def test_les_deux_plafonds_coexistent_et_peuvent_differer(self) -> None:
        politique = apply_access_policy(
            {"doc_id": "DOC-TEST", "file_name": "piece.txt"},
            "Assignation devant le tribunal, avocat et huissier.",
        )
        self.assertIn("ai_processing_ceiling", politique)
        self.assertIn("derivative_ai_ceiling", politique)
        self.assertEqual(politique["ai_processing_ceiling"], _plafond_ia(politique["raw_max_college"]))
        self.assertEqual(
            politique["derivative_ai_ceiling"], _plafond_ia(politique["derivative_max_college"])
        )

    def test_une_piece_restreinte_a_un_derive_exploitable(self) -> None:
        """Le cas qui motive tout: brut interdit a l'IA, derive autorise."""

        politique = apply_access_policy(
            {"doc_id": "DOC-TEST", "file_name": "piece.txt"},
            "Assignation devant le tribunal, avocat, huissier, contentieux.",
        )
        if politique["ai_processing_ceiling"] != "no_ai":
            self.skipTest("le classement n'a pas rendu cette piece no_ai; cas non couvert ici")
        self.assertEqual(
            politique["derivative_ai_ceiling"],
            "local_only",
            "Un derive dont le college est plus ouvert que sa source doit redevenir "
            "exploitable localement, sinon le caviardage ne sert a rien.",
        )


if __name__ == "__main__":
    unittest.main()
