from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.modules import annuaire_absorption as porte
from coproscope.modules.biffageops import (
    STATUT_LISTE_ABSENTE,
    STATUT_LISTE_ILLISIBLE,
    STATUT_LISTE_TROUVEE,
)


"""La porte d'absorption reclame la liste nominative, et sait laquelle.

Mesure du 2026-09-07: une instance de 825 documents, 539 pieces marquees a
masquer, ZERO masquee, zero pseudonyme sur 2 449 fichiers - et aucun ecran ne
disait que l'annuaire etait vide.

Donnees entierement fictives.
"""


ANNEXE = """
ANNEXE DES SOLDES
101234
MARCHAND ETIENNE
1 240,50
101235
VALLIOT CLEMENCE
-320,00
"""

PV_SANS_LISTE = "PROCES-VERBAL DE L'ASSEMBLEE GENERALE\nResolution n 1 - Approbation des comptes.\n"

#: Des comptes et des montants, aucun nom entre les deux.
LISTE_ILLISIBLE = "101234\n1 240,50\n101235\n-320,00\n101236\n0,00\n"


class ConstatDeLaPorte(unittest.TestCase):
    def test_une_liste_trouvee_ne_declenche_aucune_demande(self) -> None:
        constat = porte.constat({"DOC-ANNEXE": ANNEXE, "DOC-PV": PV_SANS_LISTE})
        self.assertEqual(constat["etat"], STATUT_LISTE_TROUVEE)
        self.assertEqual(constat["personnes_lues"], 2)
        self.assertIsNone(porte.demande_utilisateur(constat))

    def test_une_absence_reclame_la_piece_en_la_nommant(self) -> None:
        constat = porte.constat({"DOC-PV": PV_SANS_LISTE})
        self.assertEqual(constat["etat"], STATUT_LISTE_ABSENTE)
        demande = porte.demande_utilisateur(constat)
        self.assertIsNotNone(demande)
        assert demande is not None
        self.assertIn("annexe des soldes", demande["remede"])
        self.assertTrue(demande["question"].endswith("?"))

    def test_une_liste_illisible_pose_une_AUTRE_question(self) -> None:
        """Le coeur du defaut d'origine: les deux situations se confondaient.

        Reclamer une piece que l'utilisateur a deja fournie est une impasse: il
        la cherche, ne la trouve pas, et conclut que l'outil se trompe.
        """

        constat = porte.constat({"DOC-ANNEXE": LISTE_ILLISIBLE})
        self.assertEqual(constat["etat"], STATUT_LISTE_ILLISIBLE)
        demande = porte.demande_utilisateur(constat)
        assert demande is not None
        self.assertIn("n'a pas pu etre lue", demande["titre"])

        absente = porte.demande_utilisateur(porte.constat({"DOC-PV": PV_SANS_LISTE}))
        assert absente is not None
        self.assertNotEqual(demande["titre"], absente["titre"])
        self.assertNotEqual(demande["question"], absente["question"])

    def test_la_demande_dit_la_consequence_et_pas_seulement_le_manque(self) -> None:
        """Un novice doit comprendre ce qu'il perd s'il ne repond pas."""

        demande = porte.demande_utilisateur(porte.constat({"DOC-PV": PV_SANS_LISTE}))
        assert demande is not None
        self.assertIn("masquer", demande["consequence"])
        for cle in ("titre", "constat", "consequence", "remede", "question"):
            self.assertTrue(demande[cle].strip(), f"{cle} vide")

    def test_un_corpus_vide_reclame_la_liste_plutot_que_de_se_taire(self) -> None:
        constat = porte.constat({})
        self.assertEqual(constat["etat"], STATUT_LISTE_ABSENTE)
        self.assertIsNotNone(porte.demande_utilisateur(constat))


class DecisionDeLaPorte(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        chemin = self.instance_root / "instance.yml"
        contenu = json.loads(chemin.read_text(encoding="utf-8"))
        contenu.setdefault("settings", {})["vault"] = {"local_root": "./vault_local"}
        chemin.write_text(json.dumps(contenu, indent=2), encoding="utf-8")
        self.instance = load_instance(str(chemin), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_aucune_reponse_donnee_au_depart(self) -> None:
        self.assertEqual(porte.decision_enregistree(self.instance), "")

    def test_une_reponse_donnee_ne_se_redemande_pas(self) -> None:
        constat = porte.constat({"DOC-PV": PV_SANS_LISTE})
        porte.enregistrer_decision(self.instance, porte.SANS_LISTE, constat)
        self.assertEqual(porte.decision_enregistree(self.instance), porte.SANS_LISTE)

    def test_un_refus_survit_autant_qu_un_accord(self) -> None:
        """Ecrit en CORRIGE_HUMAIN: une nouvelle absorption ne l'efface pas."""

        constat = porte.constat({"DOC-PV": PV_SANS_LISTE})
        porte.enregistrer_decision(self.instance, porte.SANS_LISTE, constat)
        porte.enregistrer_decision(self.instance, porte.ATTENDU, constat)
        self.assertEqual(porte.decision_enregistree(self.instance), porte.ATTENDU)

    def test_une_decision_inconnue_leve(self) -> None:
        with self.assertRaises(ValueError):
            porte.enregistrer_decision(self.instance, "PEUT_ETRE", {})


if __name__ == "__main__":
    unittest.main()
