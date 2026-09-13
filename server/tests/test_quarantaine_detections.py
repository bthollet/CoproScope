from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.modules import biffageops


"""Une detection generique ne cree jamais d'entite d'annuaire.

**Le defaut repare.** `RegistrePseudonymes` n'avait aucun chemin de suppression,
et les detections generiques y creaient des entites definitives que
`applique_annuaire` propageait ensuite a tout le corpus. Un faux positif ne
restait donc pas local: il devenait une regle, et se renforcait a chaque
passage. C'est le `SUR-MASQUAGE` de `RM-2026-0069`.

**La regle posee.** Deux gestes seulement creent une entite: la lecture d'une
liste nominative structurelle - qui porte un numero de compte, donc une preuve
de rattachement - et la saisie humaine. Tout le reste recoit un alias ephemere
et entre dans la file d'arbitrage.

Donnees entierement fictives.
"""


class QuarantaineDesDetections(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)
        self.salt = biffageops.load_corpus_salt(self.instance)
        self.registre = biffageops.RegistrePseudonymes(self.instance, self.salt)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_alias_connu_ne_cree_rien(self) -> None:
        avant = len(self.registre.entrees())
        self.assertEqual(self.registre.alias_connu("MARCHAND", "Etienne"), "")
        self.assertEqual(len(self.registre.entrees()), avant)

    def test_une_entite_connue_garde_son_alias_stable(self) -> None:
        attendu = self.registre.alias_pour("MARCHAND", "Etienne", compte="101234")
        self.assertTrue(attendu.startswith("PERSONNE_"))
        self.assertEqual(self.registre.alias_connu("MARCHAND", "Etienne"), attendu)

    def test_un_patronyme_connu_sans_ce_prenom_rend_la_racine_de_famille(self) -> None:
        """Dire `un Marchand` est vrai; choisir lequel serait faux."""

        self.registre.alias_pour("MARCHAND", "Etienne", compte="101234")
        racine = self.registre.alias_connu("MARCHAND", "Clemence")
        self.assertTrue(racine.startswith("PERSONNE_"))
        self.assertEqual(racine.count("_"), 1, "la racine de famille ne porte pas de couleur")

    def test_l_alias_ephemere_change_d_un_document_a_l_autre(self) -> None:
        """C'est la definition d'ephemere, et c'est voulu.

        La stabilite d'un alias est une propriete de l'entite, pas de la chaine.
        Un alias stable sur une chaine que personne n'a reconnue propagerait un
        faux positif a tout le corpus sans validation humaine.
        """

        un = biffageops.alias_ephemere(self.salt, "DOC-AAA", "MARCHAND", "Etienne")
        deux = biffageops.alias_ephemere(self.salt, "DOC-BBB", "MARCHAND", "Etienne")
        self.assertNotEqual(un, deux)
        self.assertTrue(un.startswith("PERSONNE_NON_RECONNUE_"))

    def test_l_alias_ephemere_est_stable_dans_un_meme_document(self) -> None:
        un = biffageops.alias_ephemere(self.salt, "DOC-AAA", "MARCHAND", "Etienne")
        encore = biffageops.alias_ephemere(self.salt, "DOC-AAA", "MARCHAND", "Etienne")
        self.assertEqual(un, encore)

    def test_une_entite_creee_par_erreur_peut_etre_retiree(self) -> None:
        """Le chemin qui n'existait pas, et qui rendait un faux positif definitif."""

        self.registre.alias_pour("TOTAL CHARGES", "", compte="000000")
        self.assertNotEqual(self.registre.alias_connu("TOTAL CHARGES"), "")

        self.assertTrue(self.registre.retire("TOTAL CHARGES"))
        self.assertEqual(self.registre.alias_connu("TOTAL CHARGES"), "")
        self.assertNotIn(
            "TOTALCHARGES",
            {row.get("nom_normalise", "") for row in self.registre.entrees()},
        )

    def test_retirer_une_entite_absente_ne_leve_pas(self) -> None:
        self.assertFalse(self.registre.retire("INEXISTANT"))

    def test_le_retrait_survit_a_une_relecture_du_registre(self) -> None:
        self.registre.alias_pour("TOTAL CHARGES", "", compte="000000")
        self.registre.sauvegarde()
        self.registre.retire("TOTAL CHARGES")
        self.registre.sauvegarde()

        relu = biffageops.RegistrePseudonymes(self.instance, self.salt)
        self.assertEqual(relu.alias_connu("TOTAL CHARGES"), "")


if __name__ == "__main__":
    unittest.main()
