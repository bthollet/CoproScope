from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance, read_csv, write_csv
from coproscope.modules import biffageops


PV = """PROCES-VERBAL DE L'ASSEMBLEE GENERALE ORDINAIRE
Resolution n 3 - Approbation des comptes, votee a la majorite de l'article 24.
Resolution n 4 - Travaux de ravalement, majorite de l'article 25.
Vote: POUR 8 500 tantiemes, CONTRE 1 200, ABSTENTION 300.
Sont presents: M. DUPONT, Mme LEROY-MARCHAND et Monsieur Jean MARTIN.
Le syndic CABINET ALFA presente un devis de 12 450,00 EUR TTC.
Contact du gardien: gardien@residence.example  06 12 34 56 78
"""

ANNEXE = """ETAT DES SOLDES DES COPROPRIETAIRES
ANNEXE N 1
Copropriataire
Solde debiteur
45000001
DUPONT JEAN
2 061,89
2 061,89
45000002
LEROY-MARCHAND SOPHIE
451,17
451,17
45000003
MARTIN
29,44
29,44
45000004
TOTAL GENERAL
480,61
480,61
"""


def _ecris_instance(racine: Path, identifiant: str) -> Path:
    for dossier in ("raw", "registers", "staging", "outputs", "logs", "system", "restricted", "coffre"):
        (racine / dossier).mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "instance_id": identifiant,
        "scope": "copro_simple",
        "roots": {
            "workspace": ".",
            "raw": "./raw",
            "system": "./system",
            "outputs": "./outputs",
            "staging": "./staging",
            "logs": "./logs",
            "restricted": ["./restricted"],
        },
        "registers": {"documents": "./registers/registre_documents.csv"},
        "artifacts": {
            "privacy_dir": "./outputs/privacy",
            "redacted_dir": "./outputs/redacted",
            "text_dir": "./staging/text",
        },
        "settings": {"vault": {"local_root": "./coffre"}, "corpus_caviarde": {"enabled": True}},
    }
    chemin = racine / "instance.yml"
    chemin.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return chemin


class CorpusCaviardeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.racine = Path(self.tempdir.name) / "instance_a"
        self.chemin = _ecris_instance(self.racine, "corpus-test-a")
        (self.racine / "raw" / "pv.txt").write_text(PV, encoding="utf-8")
        (self.racine / "raw" / "annexe.txt").write_text(ANNEXE, encoding="utf-8")
        (self.racine / "raw" / "scan.jpg").write_bytes(b"\x00\x01binaire")
        write_csv(
            self.racine / "registers" / "registre_documents.csv",
            ["doc_id", "file_name", "original_path", "sha256"],
            [
                {"doc_id": "DOC-PV", "file_name": "pv.txt", "original_path": "raw/pv.txt", "sha256": "a" * 8},
                {"doc_id": "DOC-ANX", "file_name": "annexe.txt", "original_path": "raw/annexe.txt", "sha256": "b" * 8},
                {"doc_id": "DOC-IMG", "file_name": "scan.jpg", "original_path": "raw/scan.jpg", "sha256": "c" * 8},
            ],
        )
        self.instance = load_instance(str(self.chemin), None)
        self.run = RunContext(self.instance, "test-corpus-caviarde")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _construit(self) -> dict:
        return biffageops.build_markdown_corpus(self.instance, self.run)

    def _derive(self, doc_id: str) -> str:
        chemin = Path(biffageops._corpus_markdown_dir(self.instance)) / f"{doc_id}.caviarde.md"
        return chemin.read_text(encoding="utf-8")

    # --- le curseur: on ne remplace que des identites --------------------

    def test_article_24_survit_au_caviardage(self) -> None:
        self._construit()
        derive = self._derive("DOC-PV")
        self.assertIn("article 24", derive)
        self.assertIn("article 25", derive)
        self.assertIn("Vote:", derive)
        self.assertIn("Resolution n 3", derive)

    def test_montants_et_tantiemes_survivent(self) -> None:
        self._construit()
        derive = self._derive("DOC-PV")
        self.assertIn("12 450,00 EUR TTC", derive)
        self.assertIn("8 500 tantiemes", derive)
        annexe = self._derive("DOC-ANX")
        for montant in ("2 061,89", "451,17", "29,44", "480,61"):
            self.assertIn(montant, annexe)

    def test_raison_sociale_et_totaux_preserves(self) -> None:
        self._construit()
        self.assertIn("CABINET ALFA", self._derive("DOC-PV"))
        self.assertIn("TOTAL GENERAL", self._derive("DOC-ANX"))

    # --- l'annexe des soldes: des noms nus, sans civilite -----------------

    def test_annexe_sans_civilite_est_caviardee(self) -> None:
        self._construit()
        annexe = self._derive("DOC-ANX")
        for nom in ("DUPONT JEAN", "LEROY-MARCHAND SOPHIE"):
            self.assertNotIn(nom, annexe)
        self.assertIn("PERSONNE_", annexe)

    def test_annuaire_extrait_les_personnes_de_la_liste(self) -> None:
        self._construit()
        _, entrees = read_csv(biffageops.annuaire_path(self.instance))
        noms = {row["nom_normalise"] for row in entrees}
        self.assertIn("DUPONT", noms)
        self.assertIn("LEROYMARCHAND", noms)
        self.assertNotIn("TOTALGENERAL", noms)
        comptes = {row["nom_normalise"]: row["compte"] for row in entrees}
        self.assertEqual(comptes.get("DUPONT"), "45000001")

    def test_variantes_de_l_annuaire_retrouvees_dans_le_pv(self) -> None:
        """Le nom connu de l'annexe est retrouve sous ses autres ecritures."""

        self._construit()
        derive = self._derive("DOC-PV")
        for forme in ("DUPONT", "LEROY-MARCHAND", "MARTIN"):
            self.assertNotIn(forme, derive)

    # --- pseudonymes lisibles --------------------------------------------

    def test_pseudonymes_sont_des_mots_du_lexique_publie(self) -> None:
        self._construit()
        _, entrees = read_csv(biffageops.annuaire_path(self.instance))
        self.assertTrue(entrees)
        for row in entrees:
            corps = row["alias"].removeprefix("PERSONNE_")
            for morceau in corps.split("_"):
                mot = morceau.rstrip("0123456789")
                self.assertIn(
                    mot,
                    biffageops.MOTS_PSEUDONYMES,
                    f"{row['alias']} sort du lexique publie",
                )

    def test_meme_personne_meme_alias_d_un_document_a_l_autre(self) -> None:
        self._construit()
        _, entrees = read_csv(biffageops.annuaire_path(self.instance))
        alias = {row["nom_normalise"]: row["alias"] for row in entrees}
        alias_dupont = alias["DUPONT"]
        self.assertIn(alias_dupont.split("_")[1], self._derive("DOC-ANX"))
        self.assertIn("PERSONNE_" + alias_dupont.split("_")[1], self._derive("DOC-PV"))

    def test_deux_instances_ne_partagent_pas_les_alias(self) -> None:
        self._construit()
        _, entrees_a = read_csv(biffageops.annuaire_path(self.instance))
        autre_racine = Path(self.tempdir.name) / "instance_b"
        chemin_b = _ecris_instance(autre_racine, "corpus-test-b")
        shutil.copy(self.racine / "raw" / "annexe.txt", autre_racine / "raw" / "annexe.txt")
        write_csv(
            autre_racine / "registers" / "registre_documents.csv",
            ["doc_id", "file_name", "original_path", "sha256"],
            [{"doc_id": "DOC-ANX", "file_name": "annexe.txt", "original_path": "raw/annexe.txt", "sha256": "b" * 8}],
        )
        instance_b = load_instance(str(chemin_b), None)
        run_b = RunContext(instance_b, "test-corpus-caviarde-b")
        biffageops.build_markdown_corpus(instance_b, run_b)
        _, entrees_b = read_csv(biffageops.annuaire_path(instance_b))
        alias_a = {row["nom_normalise"]: row["alias"] for row in entrees_a}
        alias_b = {row["nom_normalise"]: row["alias"] for row in entrees_b}
        communs = set(alias_a) & set(alias_b)
        self.assertTrue(communs)
        self.assertTrue(
            any(alias_a[nom] != alias_b[nom] for nom in communs),
            "deux instances produisent les memes alias: les coffres se correlent",
        )

    # --- le sel ----------------------------------------------------------

    def test_le_sel_vit_dans_le_coffre_local_et_est_stable(self) -> None:
        chemin = biffageops.corpus_salt_path(self.instance)
        self.assertEqual(chemin.parent.parent.name, "coffre")
        premier = biffageops.load_corpus_salt(self.instance)
        second = biffageops.load_corpus_salt(self.instance)
        self.assertEqual(premier, second)
        self.assertGreaterEqual(len(premier), 32)
        self.assertNotIn(
            premier.hex(), chemin.read_text(encoding="utf-8"), "le sel ne doit pas fuir en clair hexadecimal"
        )

    # --- couverture universelle -------------------------------------------

    def test_chaque_document_a_un_derive_ou_une_raison_nommee(self) -> None:
        resultat = self._construit()
        self.assertEqual(resultat["documents"], 3)
        _, couverture = read_csv(Path(str(resultat["couverture"])))
        par_doc = {row["doc_id"]: row for row in couverture}
        self.assertEqual(set(par_doc), {"DOC-PV", "DOC-ANX", "DOC-IMG"})
        self.assertEqual(par_doc["DOC-PV"]["statut"], "MARKDOWN_OK")
        self.assertEqual(par_doc["DOC-IMG"]["statut"], "SANS_DERIVE")
        self.assertTrue(par_doc["DOC-IMG"]["raison"], "un document sans derive doit etre nomme")

    def test_le_derive_porte_son_entete_de_lecture(self) -> None:
        self._construit()
        derive = self._derive("DOC-PV")
        self.assertTrue(derive.startswith("---"))
        self.assertIn("coproscope_corpus: caviarde", derive)
        self.assertIn("sel_empreinte:", derive)
        self.assertIn("schema_alias:", derive)

    # --- le branchement pipeline reste desactive par defaut ---------------

    def test_le_pipeline_ne_produit_rien_sans_reglage(self) -> None:
        racine = Path(self.tempdir.name) / "instance_off"
        chemin = _ecris_instance(racine, "corpus-test-off")
        payload = json.loads(chemin.read_text(encoding="utf-8"))
        payload["settings"].pop("corpus_caviarde")
        chemin.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        write_csv(
            racine / "registers" / "registre_documents.csv",
            ["doc_id", "file_name", "original_path", "sha256"],
            [],
        )
        instance = load_instance(str(chemin), None)
        self.assertFalse(biffageops.corpus_markdown_enabled(instance))
        run = RunContext(instance, "test-corpus-off")
        resultat = biffageops.build_markdown_corpus_if_enabled(instance, run)
        self.assertEqual(resultat["status"], "DESACTIVE")


class DetectionIdentitesTests(unittest.TestCase):
    """Les regles de detection, isolees de toute instance."""

    def test_vocabulaire_juridique_n_est_pas_une_personne(self) -> None:
        for valeur in ("Article 24", "ARTICLE 25", "TOTAL GENERAL", "Vote Pour", "SARL OMEGA"):
            self.assertEqual(
                [item for item in biffageops.detecte_identites(valeur) if item.categorie == "PERSONNE"],
                [],
                f"{valeur} a ete pris pour une personne",
            )

    def test_civilite_et_nom_nu(self) -> None:
        texte = "M. DUPONT preside. DUPONT signe le proces-verbal."
        valeurs = {item.valeur for item in biffageops.detecte_identites(texte)}
        self.assertIn("DUPONT", valeurs)

    def test_telephone_ne_traverse_pas_une_fin_de_ligne(self) -> None:
        """Une colonne de montants n'est pas un numero de telephone."""

        texte = "291,03\n291,03\n45000020\nSUIVANT\n"
        categories = {item.categorie for item in biffageops.detecte_identites(texte)}
        self.assertNotIn("TELEPHONE", categories)

    def test_un_alias_deja_pose_n_est_pas_redetecte(self) -> None:
        texte = "M.PERSONNE_AUBEPINE_INDIGO est present."
        valeurs = {item.valeur for item in biffageops.detecte_identites(texte)}
        self.assertNotIn("PERSONNE", valeurs)


if __name__ == "__main__":
    unittest.main()
