from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.vault import gouvernance_store as G

CHAMPS = ["resolution_id", "ag_id", "doc_id", "numero", "position", "etat", "origine", "objet"]


class _Instance:
    """Instance minimale: seul le coffre local compte pour ce magasin."""

    def __init__(self, racine: Path, coffre: str | None = "./vault_local") -> None:
        self.racine = racine
        self.coffre = coffre

    def settings(self) -> dict:
        return {"vault": {"local_root": self.coffre}} if self.coffre else {}

    def resolve_path(self, valeur: str) -> Path:
        return (self.racine / valeur.lstrip("./")).resolve()


def _ligne(res_id: str, doc: str, position: int, origine: str = "EXTRAIT") -> dict[str, str]:
    return {
        "resolution_id": res_id, "ag_id": "AG-2024-07-03", "doc_id": doc,
        "numero": res_id[-2:], "position": str(position),
        "etat": "CONSTATEE", "origine": origine, "objet": f"Objet {res_id}",
    }


class GouvernanceStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        # C'est ici que se voyait le defaut: une connexion non fermee laisse le
        # fichier verrouille sous Windows, et l'erreur sort au nettoyage plutot
        # qu'a l'endroit qui la cause.
        shutil.rmtree(self.racine, ignore_errors=False)

    def test_ecrit_puis_relit(self) -> None:
        G.remplacer_pour_documents(self.instance, CHAMPS, [_ligne("R001", "DOC-A", 1)], ["DOC-A"])
        lignes = G.lire(self.instance)
        self.assertEqual(len(lignes), 1)
        self.assertEqual(lignes[0]["resolution_id"], "R001")

    def test_le_fichier_nest_pas_verrouille_apres_ecriture(self) -> None:
        """Regression: `with sqlite3.connect(...)` commite mais ne ferme pas."""
        G.remplacer_pour_documents(self.instance, CHAMPS, [_ligne("R001", "DOC-A", 1)], ["DOC-A"])
        chemin = G.store_path(self.instance)
        chemin.unlink()  # leve PermissionError [WinError 32] si le handle traine
        self.assertFalse(chemin.exists())

    def test_le_fichier_nest_pas_verrouille_apres_lecture(self) -> None:
        G.remplacer_pour_documents(self.instance, CHAMPS, [_ligne("R001", "DOC-A", 1)], ["DOC-A"])
        G.lire(self.instance)
        G.store_path(self.instance).unlink()

    def test_reextraction_remplace_ses_lignes(self) -> None:
        G.remplacer_pour_documents(
            self.instance, CHAMPS,
            [_ligne("R001", "DOC-A", 1), _ligne("R002", "DOC-A", 2)], ["DOC-A"],
        )
        G.remplacer_pour_documents(self.instance, CHAMPS, [_ligne("R001", "DOC-A", 1)], ["DOC-A"])
        self.assertEqual([l["resolution_id"] for l in G.lire(self.instance)], ["R001"])

    def test_reextraction_epargne_les_corrections_humaines(self) -> None:
        G.remplacer_pour_documents(
            self.instance, CHAMPS,
            [_ligne("R001", "DOC-A", 1), _ligne("R009", "DOC-A", 9, origine="CORRIGE_HUMAIN")],
            ["DOC-A"],
        )
        G.remplacer_pour_documents(self.instance, CHAMPS, [_ligne("R001", "DOC-A", 1)], ["DOC-A"])
        origines = sorted(l["origine"] for l in G.lire(self.instance))
        self.assertEqual(origines, ["CORRIGE_HUMAIN", "EXTRAIT"])

    def test_reextraction_ne_touche_pas_aux_autres_documents(self) -> None:
        G.remplacer_pour_documents(self.instance, CHAMPS, [_ligne("R001", "DOC-A", 1)], ["DOC-A"])
        G.remplacer_pour_documents(self.instance, CHAMPS, [_ligne("R101", "DOC-B", 1)], ["DOC-B"])
        G.remplacer_pour_documents(self.instance, CHAMPS, [_ligne("R001", "DOC-A", 1)], ["DOC-A"])
        self.assertEqual(len(G.lire(self.instance)), 2)

    def test_base_absente_rend_liste_vide_sans_lever(self) -> None:
        self.assertEqual(G.lire(self.instance), [])

    def test_coffre_non_declare_leve_explicitement(self) -> None:
        sans_coffre = _Instance(self.racine, coffre=None)
        with self.assertRaises(G.GouvernanceStoreIndisponible):
            G.store_path(sans_coffre)
        self.assertEqual(G.lire(sans_coffre), [])


class PrerequisColonnesTests(unittest.TestCase):
    """Signale par la conversation convocations: l'erreur SQL etait illisible."""

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=True)

    def test_table_sans_origine_est_refusee_avec_un_message_clair(self) -> None:
        with self.assertRaises(ValueError) as capture:
            G.remplacer_pour_documents(
                self.instance, ["convocation_id", "doc_id"], [], ["D1"], table="convocations"
            )
        self.assertIn("origine", str(capture.exception))

    def test_table_sans_doc_id_est_refusee(self) -> None:
        with self.assertRaises(ValueError) as capture:
            G.remplacer_pour_documents(
                self.instance, ["convocation_id", "origine"], [], ["D1"], table="convocations"
            )
        self.assertIn("doc_id", str(capture.exception))

    def test_table_conforme_passe(self) -> None:
        G.remplacer_pour_documents(
            self.instance, ["convocation_id", "doc_id", "origine"],
            [{"convocation_id": "C1", "doc_id": "D1", "origine": "EXTRAIT"}], ["D1"],
            table="convocations", cles=("convocation_id", "origine"),
        )
        self.assertEqual(len(G.lire(self.instance, table="convocations", ordre="convocation_id")), 1)


if __name__ == "__main__":
    unittest.main()
