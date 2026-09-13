"""CoproScope n'ouvre pas une instance posee dans un dossier synchronise.

**Ce que ca protege.** Une instance ecrit des registres, des sorties et un
coffre. Dans un dossier tenu par un nuage, ces fichiers partent chez un tiers,
sont modifies par une machine que nous ne pilotons pas, et reviennent dans un
etat que nous n'avons pas ecrit - sans qu'aucune erreur ne soit levee. Sur une
copropriete en procedure, cela suffit a rendre une mesure incontestable.

Le depot en a fait l'experience: son propre code a vecu dans un Drive partage,
et des chemins de ce Drive sont encore dans des fichiers versionnes.

**L'axe, et la modalite qu'il remplace.** La garde precedente
(`drive_local_setup._CLOUD_MARKERS`) etait une liste de noms de produits. Un
Drive monte sur une lettre de lecteur, dont le chemin ne porte aucun de ces
mots, la traversait - et c'est le cas de ce poste. La question generale est
« ce dossier est-il tenu par un logiciel de synchronisation », et Windows y
repond par le type de volume et par l'attribut de fichier fantome. Le nom
reste, en dernier recours, pour le cas ou aucun signal structurel n'existe: un
dossier synchronise sur disque fixe, contenu entierement local.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from coproscope.core.common import load_instance
from coproscope.modules import zone_synchronisee as Z

SEP = chr(92)


def _chemin(*morceaux: str) -> str:
    return SEP.join(morceaux)


class LAxeEstLeVolumePasLeNomTests(unittest.TestCase):
    def test_un_disque_local_ordinaire_est_accepte(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(Z.raison_de_refus(tmp), "")

    def test_un_volume_qui_n_est_pas_un_disque_fixe_est_refuse(self) -> None:
        """Le cas que la liste de noms ne voyait pas: un Drive monte sur G:."""
        with mock.patch.object(Z, "_volume_non_fixe", return_value="G:" + SEP):
            raison = Z.raison_de_refus(_chemin("G:", "Un Dossier", "instance"))
        self.assertIn("G:", raison)
        self.assertIn("disque local", raison)

    def test_un_fichier_a_la_demande_est_refuse(self) -> None:
        """L'attribut que le systeme pose, independant de tout nom."""
        with mock.patch.object(Z, "_attribut_fantome", return_value=True):
            raison = Z.raison_de_refus(_chemin("C:", "ailleurs", "instance"))
        self.assertIn("disponible", raison)

    def test_le_nom_reste_un_dernier_recours_et_le_dit(self) -> None:
        cible = _chemin("C:", "Users", "x", "OneDrive", "copro")
        with mock.patch.object(Z, "_attribut_fantome", return_value=False):
            with mock.patch.object(Z, "_volume_non_fixe", return_value=""):
                raison = Z.raison_de_refus(cible)
        self.assertIn("onedrive", raison)
        self.assertIn("dernier recours", raison)
        self.assertIn("peut se tromper", raison)


class UneInstanceSynchroniseeNeSOuvrePasTests(unittest.TestCase):
    def _instance(self, racine: Path) -> Path:
        (racine / "raw").mkdir(parents=True, exist_ok=True)
        chemin = racine / "instance.yml"
        chemin.write_text(json.dumps({
            "version": 1, "instance_id": "essai", "display_name": "Essai",
            "scope": "copro_simple", "entity_id": "essai",
            "roots": {"workspace": ".", "raw": "./raw", "system": "./system",
                      "outputs": "./outputs", "staging": "./staging",
                      "logs": "./logs", "restricted": []},
        }), encoding="utf-8")
        return chemin

    def test_le_chargement_refuse_et_nomme_le_dossier_et_le_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._instance(Path(tmp))
            with mock.patch.object(Z, "_attribut_fantome", return_value=True):
                with self.assertRaises(SystemExit) as capture:
                    load_instance(None, tmp)
            message = str(capture.exception)
            nom = Path(tmp).name
        self.assertIn("dossier synchronise", message)
        self.assertIn(nom, message, "le message doit nommer le dossier fautif")
        self.assertIn("Deplacez", message, "un refus doit dire quoi faire")

    def test_une_instance_sur_disque_local_s_ouvre_toujours(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self._instance(Path(tmp))
            config = load_instance(None, tmp)
        self.assertEqual(config.instance_id, "essai")

    def test_la_garde_lit_les_racines_pas_seulement_la_racine_d_instance(self) -> None:
        """Un `instance.yml` recopie ailleurs ne doit pas suffire a passer."""
        vus: list[str] = []

        def espion(chemin: object) -> str:
            vus.append(str(chemin))
            return ""

        with tempfile.TemporaryDirectory() as tmp:
            self._instance(Path(tmp))
            with mock.patch.object(Z, "raison_de_refus", side_effect=espion):
                load_instance(None, tmp)
        self.assertGreater(
            len(vus), 1,
            "la garde doit verifier les racines declarees, pas seulement le "
            "dossier de l'instance")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
