# -*- coding: utf-8 -*-
"""Le pool fictif est BRANCHE: la chaine du produit le lit, et ses pieces se repondent.

`RM-2026-0183`, recette de Brice du 2026-09-13: *la demo devra deja avoir un
concept branche avec le reste de son pool fictif*. Le pool est une copropriete
entierement inventee, en pieces au format scelle (PDF a texte natif) produites
par `tools/pool_fictif/generer.py`. Aucun registre n'est ecrit a la main: la
chaine d'absorption les reconstruit.

**CE QUE LA GARDE MESURE, ET OU.** Une demo *branchee* qui ne l'est pas ne fait
echouer aucun test: les ecrans affichent simplement moins. La garde passe donc
par le point d'entree que le produit appelle - `core.pipeline.run_pipeline` - sur
un pool genere a neuf, puis lit ce que la chaine a ecrit:

- chaque piece est classee dans la famille attendue, avec sa date d'emission;
- les deux assemblees sont reconnues avec toutes leurs resolutions;
- la piece volontairement absente - le PV de reception des travaux - sort bien
  comme piece a demander.

**Deux proprietes du generateur, verifiees parce qu'elles fondent la demo:**
il est deterministe (memes octets a deux passages), et il refuse un dossier non
vide - melanger une sortie precedente a une entree neuve est le defaut que la
regle de l'instance vide existe pour empecher.

**CE QU'ELLE NE PROUVE PAS.** Les pieces ont ete ecrites pour que la chaine les
lise: le pool prouve que la chaine tourne et sert de vitrine. Il ne prouve rien
sur la justesse d'une lecture de pieces reelles.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
GENERATEUR = RACINE / "tools" / "pool_fictif" / "generer.py"

#: nom de piece -> (famille attendue, date d'emission attendue)
ATTENDU = {
    "2024-06-20_proces_verbal_ag_2024.pdf": ("PV_AG", "2024-06-20"),
    "2025-01-01_contrat_entretien_ascenseur.pdf": ("Contrat_Maintenance", "2025-01-01"),
    "2025-01-10_attestation_assurance_multirisque.pdf": ("Attestation_Assurance", "2025-01-10"),
    "2025-02-03_declaration_sinistre_degat_des_eaux.pdf": ("Declaration_Assurance", "2025-02-03"),
    "2025-03-31_annexe_comptable_etat_financier_2024.pdf": ("Annexe_Comptable", "2025-03-31"),
    "2025-04-02_devis_ravalement_facades.pdf": ("Devis", "2025-04-02"),
    "2025-05-15_convocation_ag_2025.pdf": ("Convocation_AG", "2025-05-15"),
    "2025-06-12_proces_verbal_ag_2025.pdf": ("PV_AG", "2025-06-12"),
    "2025-07-10_ordre_de_service_ravalement.pdf": ("Ordre_Service", "2025-07-10"),
    "2025-09-15_facture_acompte_ravalement.pdf": ("Facture", "2025-09-15"),
    "2025-10-01_courrier_demande_pieces_au_syndic.pdf": ("Courrier", "2025-10-01"),
}


def _generateur():
    spec = importlib.util.spec_from_file_location("pool_fictif_generer", GENERATEUR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _empreintes(racine: Path) -> dict[str, str]:
    return {
        chemin.relative_to(racine).as_posix(): hashlib.sha256(chemin.read_bytes()).hexdigest()
        for chemin in sorted(racine.rglob("*")) if chemin.is_file()
    }


class LE_GENERATEUR_EST_UNE_ENTREE_STABLE(unittest.TestCase):
    def test_deux_passages_rendent_les_memes_octets(self) -> None:
        gen = _generateur()
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            gen.generer(Path(a) / "pool")
            gen.generer(Path(b) / "pool")
            premier, second = _empreintes(Path(a) / "pool"), _empreintes(Path(b) / "pool")
        self.assertEqual(len([n for n in premier if n.startswith("raw/")]), len(gen.PIECES))
        self.assertEqual(premier, second)

    def test_un_dossier_non_vide_est_refuse(self) -> None:
        gen = _generateur()
        with tempfile.TemporaryDirectory() as dossier:
            (Path(dossier) / "sortie_precedente.csv").write_text("x", encoding="utf-8")
            with self.assertRaises(SystemExit):
                gen.generer(Path(dossier))

    def test_chaque_piece_se_declare_fictive(self) -> None:
        gen = _generateur()
        for nom, texte in gen.PIECES:
            with self.subTest(piece=nom):
                self.assertIn("Document fictif", texte)
                self.assertRegex(texte, r"\((fictive|fictif)\)")


class LA_CHAINE_DU_PRODUIT_LIT_LE_POOL(unittest.TestCase):
    """Une seule absorption, jouee par le point d'entree du produit."""

    @classmethod
    def setUpClass(cls) -> None:
        from coproscope.core.common import RunContext, load_instance
        from coproscope.core.pipeline import run_pipeline

        cls._dossier = tempfile.TemporaryDirectory()
        racine = Path(cls._dossier.name) / "pool"
        _generateur().generer(racine)
        instance = load_instance(None, str(racine))
        run_pipeline(instance, RunContext(instance, "garde pool fictif"), copy_classified=False)
        cls.racine = racine

    @classmethod
    def tearDownClass(cls) -> None:
        cls._dossier.cleanup()

    def _lignes(self, relatif: str) -> list[dict[str, str]]:
        with (self.racine / relatif).open(encoding="utf-8", newline="") as flux:
            return list(csv.DictReader(flux))

    def test_chaque_piece_est_classee_avec_sa_date(self) -> None:
        lues = {r["file_name"]: (r["document_type"], r["suspected_date"]) for r in self._lignes("registers/registre_documents.csv")}
        for nom, attendu in ATTENDU.items():
            with self.subTest(piece=nom):
                self.assertEqual(lues.get(nom), attendu)

    def test_les_deux_assemblees_portent_leurs_resolutions(self) -> None:
        ag = {r["ag_id"]: r for r in self._lignes("registers/registre_ag.csv") if r["document_type"] == "PV_AG"}
        self.assertEqual(sorted(ag), ["AG-2024-06-20", "AG-2025-06-12"])

    def test_les_anomalies_ecrites_a_dessein_sont_lues(self) -> None:
        """La demo du controle de gouvernance repose sur trois cas voulus:

        une majorite non enoncee (n°5), une issue sans formule (n°6) et un
        rejet (n°7). Lus dans le coffre de gouvernance que la chaine a ecrit.
        """
        import sqlite3

        from coproscope.vault.gouvernance_store import GOUVERNANCE_DB_FILE

        base = sqlite3.connect(str(self.racine / "vault_local" / GOUVERNANCE_DB_FILE))
        try:
            lues = base.execute(
                "select ag_id, numero, majorite_annoncee, resultat from resolutions "
                "order by ag_id, cast(numero as integer)").fetchall()
        finally:
            base.close()
        self.assertEqual(lues, [
            ("AG-2024-06-20", "1", "24", "ADOPTEE"),
            ("AG-2024-06-20", "2", "24", "ADOPTEE"),
            ("AG-2024-06-20", "3", "24", "ADOPTEE"),
            ("AG-2025-06-12", "1", "24", "ADOPTEE"),
            ("AG-2025-06-12", "2", "24", "ADOPTEE"),
            ("AG-2025-06-12", "3", "24", "ADOPTEE"),
            ("AG-2025-06-12", "4", "25", "ADOPTEE"),
            ("AG-2025-06-12", "5", "", "ADOPTEE"),
            ("AG-2025-06-12", "6", "25", "VOTE_SANS_FORMULE"),
            ("AG-2025-06-12", "7", "24", "REJETEE"),
        ])

    def test_le_pv_de_reception_absent_sort_comme_piece_a_demander(self) -> None:
        demandes = self._lignes("outputs/reports/pieces_a_demander.csv")
        reception = [d for d in demandes if "reception" in d["expected_piece"].lower()]
        self.assertTrue(reception, "la piece volontairement absente n'est pas reclamee")
        self.assertEqual({d["status"] for d in reception}, {"ABSENT"})


if __name__ == "__main__":
    unittest.main()
