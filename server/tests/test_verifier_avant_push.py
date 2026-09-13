# -*- coding: utf-8 -*-
"""L'outil qui regarde ce que `git push` enverrait.

**Ce que ce test protege avant tout: la distinction entre *rien trouve* et *pas
regarde*.** Les termes interdits ne peuvent pas vivre dans le depot - ecrire le
nom reel d'une copropriete dans le fichier qui interdit de l'ecrire serait la
premiere fuite. Ils vivent donc dans un fichier local, hors depot. Ce fichier
peut manquer: sur une autre machine, apres un clone, dans la CI.

**Un controle qui se tait faute de matiere est pire qu'aucun controle**, parce
qu'il laisse croire qu'il a regarde. L'outil rend donc trois etats et non deux,
et c'est la propriete que ce module verifie: `0` rien, `1` quelque chose, `2`
**le controle n'a pas pu etre fait**.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DEPOT = Path(__file__).resolve().parents[2]
OUTIL = DEPOT / "tools" / "verifier_avant_push.py"


def _module():
    """Charger l'outil sans l'installer: il vit dans `tools/`, hors du paquet."""
    spec = importlib.util.spec_from_file_location("verifier_avant_push", OUTIL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LOutilExiste(unittest.TestCase):
    def test_le_fichier_est_la(self) -> None:
        self.assertTrue(OUTIL.is_file(), "outil introuvable: %s" % OUTIL)


class TroisEtatsEtNonDeux(unittest.TestCase):
    def test_sans_fichier_de_termes_il_REFUSE_de_certifier(self) -> None:
        """Le coeur du garde: il ne rend jamais 0 quand il n'a pas regarde."""
        with tempfile.TemporaryDirectory() as dossier:
            absent = str(Path(dossier) / "ce_fichier_n_existe_pas.txt")
            r = subprocess.run(
                [sys.executable, str(OUTIL)], cwd=str(DEPOT),
                env={"PATH": "", "SYSTEMROOT": "", "PYTHONIOENCODING": "utf-8",
                     "COPROSCOPE_NOMS_INTERDITS": absent},
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
        self.assertEqual(2, r.returncode, r.stdout + r.stderr)
        self.assertIn("CONTROLE IMPOSSIBLE", r.stderr)

    def test_un_fichier_de_termes_VIDE_refuse_aussi(self) -> None:
        """Un fichier present mais vide n'est pas une absence de fuite."""
        with tempfile.TemporaryDirectory() as dossier:
            vide = Path(dossier) / "termes.txt"
            vide.write_text("# rien que des commentaires\n", encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(OUTIL)], cwd=str(DEPOT),
                env={"PATH": "", "SYSTEMROOT": "", "PYTHONIOENCODING": "utf-8",
                     "COPROSCOPE_NOMS_INTERDITS": str(vide)},
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
        self.assertEqual(2, r.returncode, r.stdout + r.stderr)


class LaLectureDesTermes(unittest.TestCase):
    def test_les_commentaires_et_les_lignes_vides_ne_sont_pas_des_termes(self) -> None:
        module = _module()
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "termes.txt"
            chemin.write_text("# entete\n\nalpha\n  beta  \n", encoding="utf-8")
            self.assertEqual(["alpha", "beta"], module.termes_interdits(chemin))


class LaReconnaissanceDesAdresses(unittest.TestCase):
    """Meme axe que `test_aucune_adresse_reelle`, verifie ici aussi.

    Les deux gardes partagent la regle sans partager le code: l'un vit dans la
    suite de tests, l'autre doit tourner sans elle, avant un `git push`. Une
    divergence entre les deux se verrait donc ici.
    """

    def setUp(self) -> None:
        self.m = _module()

    def _cherche(self, ligne: str):
        for segment in self.m.ECHAPPEMENTS.split(ligne):
            trouve = self.m.ADRESSE.search(segment)
            if trouve:
                return trouve
        return None

    def test_une_adresse_derriere_un_echappement_est_vue(self) -> None:
        self.assertTrue(self._cherche(r"SMA\nBP 242\n13308 MARSEILLE, France"))

    def test_un_identifiant_et_un_montant_ne_sont_pas_des_adresses(self) -> None:
        self.assertIsNone(self._cherche("AG-DOC-729CCCF88863  DOC-729CCCF88863"))
        self.assertIsNone(self._cherche(r"Facture 12345\nDate : 01/01/2025"))
        self.assertIsNone(self._cherche("total 12345 EUR"))

    def test_LES_DEUX_GARDES_RESTENT_D_ACCORD(self) -> None:
        """Deux listes de fichiers exemptes, dans deux fichiers: elles divergent.

        Le garde de la suite exempte les fichiers dont la raison d'etre est de
        porter le motif; l'outil de pre-push doit exempter les MEMES, plus
        lui-meme. Ecrire la relation ici est ce qui empeche qu'un ajout d'un
        cote laisse l'autre crier - et **un garde qui crie toujours finit
        ignore.**
        """
        from tests.test_aucune_adresse_reelle import COMMUNES_FICTIVES, IGNORES

        self.assertEqual(
            IGNORES | {"tools/verifier_avant_push.py"},
            self.m.DECLARENT_LE_MOTIF,
            "les deux listes d'exemption ont divergé",
        )
        self.assertEqual(COMMUNES_FICTIVES, self.m.COMMUNES_FICTIVES,
                         "les deux gardes n'admettent plus les memes communes fictives")

    def test_la_commune_conventionnelle_passe(self) -> None:
        adresse = self.m.ADRESSE.search("10 rue des Exemples, 13000 Ville")
        self.assertTrue(adresse)
        fictives = {c.rstrip("s") for c in self.m.COMMUNES_FICTIVES}
        self.assertIn(adresse.group(1).lower().rstrip("s"), fictives)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
