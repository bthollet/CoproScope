"""Parcours complet sur une instance vide: du depot au controle.

Ce test ne verifie pas une fonction, il verifie un CHEMIN. Il part d'une
instance qui ne contient rien - pas un exemple pre-rempli, pas un fixture
recopie - depose un seul fichier, et suit ce que l'utilisateur suivrait:

    depot -> inventaire -> extraction du texte -> classement -> registres -> controles

Ce que ce parcours attrape et qu'un test unitaire manque: un registre non
declare dans `instance.yml`, un type de document qui ne se reconnait pas, un
enchainement qui rend une liste vide sans dire pourquoi. C'est exactement le
defaut que la strategie decrit - une source absente rend une liste vide et fait
croire qu'il n'y a rien a faire.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import RunContext, load_instance, read_csv
from coproscope.modules import convocation, docuscope
from coproscope.modules import _convocation_store as store

CONVOCATION_DEPOSEE = """CONVOCATION A L'ASSEMBLEE GENERALE EXTRAORDINAIRE
Residence fictive Les Cypres - assemblee du 12 mai 2026

ORDRE DU JOUR
1- Election du President de seance.
2- Approbation des comptes de gestion 2025 ci-annexes.
3- VOTE DES TRAVAUX DE TOITURE.
3.1- choix du devis de toiture COUVRETOUT pour 84.300,00 EUR TTC.
3.2- choix du devis de toiture ZINGUERIA pour 79.115,50 EUR TTC.

PROJETS DE RESOLUTIONS
PREAMBULE : DANS LE CADRE DE LA PROCEDURE ENTAMEE PAR UN COPROPRIETAIRE EN NULITE DES
QUESTIONS N°2 et 3-1 DE LA DERNIERE ASSEMBLEE DU 14/11/2025 NOUS VOUS CONVOQUONS POUR
CETTE ASSEMBLEE EXTRAORDINAIRE AFIN DE FAIRE RE-VOTER TOUTES LES QUESTIONS DE L'ORDRE
DU JOUR.
Article 24
L'Assemblee Generale approuve les comptes dont le montant s'eleve a 141 250.75 EUR pour
les depenses courantes (total de l'annexe 3)
2- Approbation des comptes de gestion 2025 ci-annexes.
Article 24
L'assemblee generale, apres avoir pris connaissance des conditions essentielles des devis
et du rapport d'analyse des offres, pris connaissance de l'avis du conseil syndical et
apres en avoir delibere, decide d'effectuer les travaux suivants :
Retient la proposition presentee : par l'entreprise COUVRETOUT pour 84.300,00 EUR TTC.
Les travaux seront repartis selon la cle T01 du Syndic; soit sur 1000 tantiemes.
3.1- choix du devis de toiture COUVRETOUT pour 84.300,00 EUR TTC.
Article 25
L'assemblee generale, apres avoir pris connaissance des conditions essentielles des devis
et du rapport d'analyse des offres, pris connaissance de l'avis du conseil syndical et
apres en avoir delibere, decide d'effectuer les travaux suivants :
Retient la proposition presentee : par l'entreprise ZINGUERIA pour 79.115,50 EUR TTC.
Les travaux seront repartis selon la cle T01 du Syndic; soit sur 1000 tantiemes.
3.2- choix du devis de toiture ZINGUERIA pour 79.115,50 EUR TTC.
Article 25
"""


def instance_vide(racine: Path, *, avec_coffre: bool = True) -> Path:
    """Une instance qui ne contient rien: des dossiers et un fichier de config."""
    registres = {
        "documents": "./registers/registre_documents.csv",
        "duplicates": "./registers/registre_doublons.csv",
        "manifest": "./registers/manifest_sha256.csv",
        "requests": "./registers/registre_demandes.csv",
        "ag": "./registers/registre_ag.csv",
        "findings": "./registers/constats_diligences.csv",
        "kpi": "./registers/kpi.csv",
    }
    config = {
        "version": 1,
        "instance_id": "instance-vide-test",
        "display_name": "Instance vide de test",
        "scope": "copro_simple",
        "entity_id": "main",
        "roots": {
            "workspace": ".",
            "raw": "./raw",
            "system": "./system",
            "outputs": "./outputs",
            "staging": "./staging",
            "logs": "./logs",
            "restricted": [],
        },
        "registers": registres,
        "artifacts": {
            "text_dir": "./staging/text",
            "classified_dir": "./staging/classified",
            "reports_dir": "./outputs/reports",
            "docai_dir": "./staging/docai",
            "accounting_dir": "./outputs/accounting",
            "grist_dir": "./outputs/grist",
            "evidence_dir": "./outputs/evidence",
        },
        "settings": {"never_modify_raw": True, "write_outputs_only": True},
    }
    if avec_coffre:
        # Arbitrage Brice du 2026-09-03: les donnees de gouvernance vont dans le
        # coffre SQLite, jamais dans un nouveau registre CSV.
        config["settings"]["vault"] = {"local_root": "./coffre"}
    for dossier in ("raw", "system", "outputs", "staging", "logs", "registers", "coffre"):
        (racine / dossier).mkdir(parents=True, exist_ok=True)
    chemin = racine / "instance.yml"
    chemin.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return chemin


class ParcoursDepotVersControleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.racine = Path(self.tempdir.name) / "copro_vide"
        self.racine.mkdir(parents=True)
        self.config = instance_vide(self.racine)
        self.instance = load_instance(str(self.config), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _deposer(self, nom: str, contenu: str) -> None:
        (self.racine / "raw" / nom).write_text(contenu, encoding="utf-8")

    def _jusqu_au_classement(self) -> RunContext:
        run = RunContext(self.instance, "convocation")
        docuscope.inventory(self.instance, run)
        docuscope.extract_text(self.instance, run)
        docuscope.classify(self.instance, run, copy_files=False)
        return run

    def test_instance_vide_ne_produit_aucune_convocation_et_le_dit(self) -> None:
        # Aucun depot: le registre existe, il est vide, et rien ne pretend le contraire.
        run = self._jusqu_au_classement()
        resume = convocation.build_register(self.instance, run)
        self.assertEqual(resume["convocations_lues"], 0)
        self.assertEqual(resume["devis_cites"], 0)
        self.assertEqual(resume["convocations_sans_couche_texte"], [])

    def test_depot_d_une_convocation_va_du_fichier_aux_controles(self) -> None:
        self._deposer("2026-05-12_convocation_ag.txt", CONVOCATION_DEPOSEE)
        run = self._jusqu_au_classement()

        # Le classement a reconnu le type, sinon rien de la suite n'a lieu.
        _, documents = read_csv(self.instance.register("documents"))
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["document_type"], convocation.TYPE_CONVOCATION)

        resume = convocation.build_register(self.instance, run)
        self.assertEqual(resume["convocations_lues"], 1)

        devis = store.lire(self.instance, "devis_cites")
        self.assertEqual(len(devis), 2)
        par_reference = {(d["numero"], d["sous_numero"]): d for d in devis}
        self.assertEqual(par_reference[("3", "1")]["entreprise"], "COUVRETOUT")
        self.assertEqual(par_reference[("3", "1")]["montant_ttc"], "84300.00")
        self.assertEqual(par_reference[("3", "1")]["majorite_annoncee"], "25")
        self.assertEqual(par_reference[("3", "2")]["entreprise"], "ZINGUERIA")

        declarations = store.lire(self.instance, "declarations_ag")
        natures = {d["nature"]: d for d in declarations}
        self.assertEqual(natures[convocation.NATURE_CONTESTATION]["ag_visee"], "2025-11-14")
        self.assertEqual(natures[convocation.NATURE_CONTESTATION]["portee"], convocation.PORTEE_PARTIELLE)
        self.assertEqual(natures[convocation.NATURE_CONTESTATION]["questions_visees"], "2;3-1")
        self.assertEqual(natures[convocation.NATURE_REJEU]["portee"], convocation.PORTEE_TOTALE)

        controles = resume["controles"]["CONV-2026-05-12"]
        self.assertEqual(controles["quantification"]["quantifies"], 2)
        self.assertEqual(controles["affirmations"]["piece_produite"], 0)
        self.assertEqual(
            [t["annexe"] for t in controles["references"]["totaux_a_verifier"]], [3]
        )

    def test_l_ancrage_est_signale_degrade_quand_la_source_n_a_pas_de_pages(self) -> None:
        # Un .txt n'a pas de pagination: les renvois cliquables ne peuvent pas
        # pointer une page. C'est un fait a remonter, pas un echec silencieux.
        self._deposer("2026-05-12_convocation_ag.txt", CONVOCATION_DEPOSEE)
        run = self._jusqu_au_classement()
        resume = convocation.build_register(self.instance, run)
        self.assertEqual(len(resume["ancrage_degrade_page_unique"]), 1)

    def test_un_document_sans_couche_texte_est_compte_a_part(self) -> None:
        # Le piege: un scan de vingt-sept pages rend une liste de vingt-sept
        # chaines vides, donc un objet NON VIDE. Sans mesure de la densite, la
        # convocation serait comptee "lue, zero devis" - et son absence de
        # resultat passerait pour un fait sur la convocation plutot que sur
        # notre lecture. Meme defaut que les 111 documents du corpus classes
        # `L1_NATIVE_TEXT_PYMUPDF` qui rendent zero caractere.
        self._deposer("2026-05-12_convocation_ag.txt", "   \n \n  ")
        run = self._jusqu_au_classement()
        resume = convocation.build_register(self.instance, run)
        self.assertEqual(resume["convocations_lues"], 0)
        self.assertEqual(len(resume["convocations_sans_couche_texte"]), 1)

    def test_coffre_non_declare_le_dit_au_lieu_d_echouer_en_silence(self) -> None:
        # Une instance anterieure a la bascule SQLite n'a pas de coffre. On le
        # nomme, on ne l'invente pas, et on ne plante pas.
        racine = Path(self.tempdir.name) / "copro_ancienne"
        racine.mkdir(parents=True)
        config = instance_vide(racine, avec_coffre=False)
        ancienne = load_instance(str(config), None)
        resume = convocation.build_register(ancienne, None)
        self.assertTrue(resume["coffre_non_declare"])
        self.assertEqual(resume["convocations_lues"], 0)

    def test_une_re_extraction_ne_perd_pas_une_correction_humaine(self) -> None:
        self._deposer("2026-05-12_convocation_ag.txt", CONVOCATION_DEPOSEE)
        run = self._jusqu_au_classement()
        convocation.build_register(self.instance, run)

        # Un humain corrige la raison sociale, puis on relance l'extraction.
        lignes = store.lire(self.instance, "devis_cites")
        lignes[0]["entreprise"] = "COUVRETOUT SAS"
        lignes[0]["origine"] = convocation.ORIGINE_CORRIGE
        store.remplacer_pour_documents(
            self.instance, "devis_cites", convocation.DEVIS_CITE_FIELDS, lignes, []
        )

        resume = convocation.build_register(self.instance, run)

        apres = store.lire(self.instance, "devis_cites")
        corrigee = next(d for d in apres if d["devis_cite_id"] == lignes[0]["devis_cite_id"])
        self.assertEqual(corrigee["entreprise"], "COUVRETOUT SAS")
        self.assertEqual(corrigee["origine"], convocation.ORIGINE_CORRIGE)
        self.assertEqual(len(resume["divergences"]), 1)


if __name__ == "__main__":
    unittest.main()
