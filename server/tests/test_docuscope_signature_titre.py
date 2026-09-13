from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, RunContext, load_instance, read_csv, write_csv
from coproscope.modules.docuscope import (
    CLASSIFICATION_DOUBT_STATUS,
    CLASSIFICATION_NO_TEXT_STATUS,
    DEFAULT_TITLE_HEAD_CHARS,
    DEFAULT_USEFUL_TEXT_FLOOR,
    _title_head_chars,
    _title_signatures,
    _useful_text,
    _useful_text_floor,
    classify,
    title_signature_verdict,
)

TITRE = "proces verbal de l assemblee"
EXAMPLE_INSTANCE = Path(__file__).resolve().parents[2] / "examples" / "synthetic_copro"


def corps(longueur: int) -> str:
    """Matiere de remplissage, sans aucun mot de la signature."""
    motif = "le syndicat des coproprietaires examine le budget et les charges courantes "
    return (motif * (longueur // len(motif) + 1))[:longueur]


def entete(longueur: int) -> str:
    """Ce qui precede reellement un titre de proces-verbal: un en-tete de
    cabinet, une pagination, un filet - le tout CLOS avant le titre.

    Mesure du 2026-09-09 sur les textes extraits des deux cabinets: la locution
    de titre tombe aux positions 25, 25, 26 et 49, et les quatre fois **rien de
    porteur de mot ne la precede dans son propre enonce**. Une matiere de
    remplissage en prose collee au titre, comme `corps(26) + titre`, decrit
    donc une disposition qu'aucun des quatre documents ne presente: elle
    fabrique une MENTION et l'appelle un titre.
    """
    if longueur <= 0:
        return ""
    plein = ("cabinet gestion immobiliere\nservice copropriete\n" * 10)[: longueur - 1]
    return plein + "\n"


class TitreSignatureUniteTests(unittest.TestCase):
    """Le titre est cherche dans la tete du texte utile, pas n'importe ou."""

    def verdict(self, texte, motif=TITRE, head=DEFAULT_TITLE_HEAD_CHARS, floor=DEFAULT_USEFUL_TEXT_FLOOR):
        return title_signature_verdict(texte, motif, head, floor)

    def test_titre_reconnu_aux_positions_mesurees(self) -> None:
        # Positions relevees sur les proces-verbaux des deux cabinets: 0, 0, 26, 94.
        # CONTREDIT ET CORRIGE le 2026-09-09. La version precedente ecrivait
        # `corps(decalage) + "PROCES-VERBAL ..."`, c'est-a-dire de la prose
        # collee au titre dans le MEME enonce. Aucun des quatre proces-verbaux
        # mesures ne se presente ainsi: aux positions 25, 25, 26 et 49, la
        # locution ouvre son enonce. Le decalage vient d'un en-tete clos, pas
        # d'une phrase en cours. La propriete gardee - le titre est reconnu
        # meme s'il n'est pas au caractere zero - est conservee; c'est la
        # matiere qui occupe le decalage qui devient conforme a la mesure.
        for decalage in (0, 26, 94):
            with self.subTest(position=decalage):
                texte = entete(decalage) + "PROCES-VERBAL DE L ASSEMBLEE GENERALE ORDINAIRE " + corps(3000)
                self.assertEqual(self.verdict(texte), "")

    def test_une_prose_collee_au_titre_en_fait_une_mention(self) -> None:
        # Le defaut (1) de RM-2026-0052, reduit a son noyau. Meme locution,
        # meme fenetre de tete: seule change la presence d'un enonce en cours.
        texte = (
            "cette note reprend le proces-verbal de l assemblee generale du 3 juillet "
            "2024 et confronte ses resolutions aux factures du coffre. " + corps(3000)
        )
        self.assertEqual(self.verdict(texte), CLASSIFICATION_DOUBT_STATUS)

    def test_les_trois_formes_de_fichier_de_travail_de_coproscope(self) -> None:
        # Mesure du 2026-09-09: ces trois formes sortaient PV_AG en
        # AUTO_CLASSIFIED, sans note. Le gouvernail en comptait 11 rangees
        # comme proces-verbaux. Chacune CITE la locution dans ses 300 premiers
        # caracteres, aucune ne la pose en titre.
        formes = {
            "synthese d audit": "resume: le proces-verbal de l assemblee generale a ete depose. ",
            "matrice de risques": "risque_id,lot,risque\nRSK-001,AG,proces-verbal de l assemblee non depose\n",
            "journal de course": "run=RUN-2026 action=read source=proces-verbal de l assemblee generale\n",
        }
        for nom, tete in formes.items():
            with self.subTest(forme=nom):
                self.assertEqual(self.verdict(tete + corps(3000)), CLASSIFICATION_DOUBT_STATUS)

    def test_titre_accentue_et_ponctue_reconnu(self) -> None:
        texte = "PROCÈS-VERBAL DE L’ASSEMBLÉE GÉNÉRALE ORDINAIRE du 29/06/2026 " + corps(3000)
        self.assertEqual(self.verdict(texte), "")

    def test_titre_precede_de_marqueurs_de_pagination(self) -> None:
        # L extraction prefixe "page 1 page 1 sur 26": ce bruit ne doit pas
        # repousser le titre hors de la fenetre de tete.
        texte = "===== PAGE 1 =====\npage 1 sur 26\nProces-verbal de l assemblee generale " + corps(3000)
        self.assertEqual(self.verdict(texte), "")

    def test_convocation_portant_approbation_du_pv_a_l_ordre_du_jour(self) -> None:
        # Le faux positif a eviter: une convocation dont l ordre du jour porte
        # "approbation du proces-verbal de l assemblee precedente". Mesure: le
        # premier marqueur d ordre du jour d une convocation reelle apparait au
        # plus tot a 389 caracteres, le titre d un vrai PV au plus tard a 94.
        texte = (
            "CONVOCATION A L ASSEMBLEE GENERALE ORDINAIRE des coproprietaires "
            + corps(1000)
            + " ordre du jour premiere resolution approbation du proces-verbal de "
            "l assemblee precedente deuxieme resolution "
            + corps(2000)
        )
        self.assertEqual(self.verdict(texte), CLASSIFICATION_DOUBT_STATUS)

    def test_convocation_ordinaire_sans_aucun_titre(self) -> None:
        texte = "CONVOCATION A L ASSEMBLEE GENERALE " + corps(3000)
        self.assertEqual(self.verdict(texte), CLASSIFICATION_DOUBT_STATUS)

    def test_document_de_travail_sans_titre_est_un_doute(self) -> None:
        texte = "risque_id,lot,risque,signaux,impact\nRSK-001,Syndic,mandat expire," + corps(2000)
        self.assertEqual(self.verdict(texte), CLASSIFICATION_DOUBT_STATUS)


class PlancherExtractionTests(unittest.TestCase):
    """Sous le plancher, le controle dit je ne sais pas, jamais ce n est pas un PV."""

    def verdict(self, texte):
        return title_signature_verdict(texte, TITRE, DEFAULT_TITLE_HEAD_CHARS, DEFAULT_USEFUL_TEXT_FLOOR)

    def test_bourrage_de_marqueurs_de_pagination(self) -> None:
        # Cas mesure: des scans dont le texte extrait n est qu une suite de
        # "page N". Ils valaient 126 a 258 caracteres bruts, assez pour tromper
        # un seuil pose sur le texte brut, et 0 caractere utile.
        texte = "===== PAGE 1 =====\n" + " ".join("page %d" % n for n in range(1, 40))
        self.assertGreater(len(texte), DEFAULT_USEFUL_TEXT_FLOOR)
        self.assertEqual(_useful_text(texte), "")
        self.assertEqual(self.verdict(texte), CLASSIFICATION_NO_TEXT_STATUS)

    def test_extractions_quasi_vides_des_deux_cabinets(self) -> None:
        # Longueurs brutes relevees: 13, 78 et 86 caracteres, dont un PV.
        for brut in (13, 78, 86):
            with self.subTest(caracteres=brut):
                self.assertEqual(self.verdict("page 1 " * (brut // 7)), CLASSIFICATION_NO_TEXT_STATUS)

    def test_un_pv_illisible_nest_jamais_declare_non_pv(self) -> None:
        # Le PV 2025 du second cabinet: 86 caracteres bruts, 0 utile.
        self.assertNotEqual(self.verdict("page 1 page 2 page 3"), CLASSIFICATION_DOUBT_STATUS)

    def test_le_plus_petit_document_reel_reste_juge(self) -> None:
        # Le plus petit document reellement porteur de texte des deux corpus
        # compte 251 caracteres utiles: il est au-dessus du plancher, donc juge.
        self.assertEqual(self.verdict(corps(251)), CLASSIFICATION_DOUBT_STATUS)

    def test_les_deux_etats_ne_se_confondent_pas(self) -> None:
        self.assertNotEqual(CLASSIFICATION_DOUBT_STATUS, CLASSIFICATION_NO_TEXT_STATUS)


class ConfigurationSignatureTests(unittest.TestCase):
    """Les deux nombres varieront au troisieme syndic: ils sont configurables."""

    def test_valeurs_par_defaut_quand_la_cle_est_absente(self) -> None:
        self.assertEqual(_title_signatures({}), {"PV_AG": TITRE})
        self.assertEqual(_title_head_chars({}), DEFAULT_TITLE_HEAD_CHARS)
        self.assertEqual(_useful_text_floor({}), DEFAULT_USEFUL_TEXT_FLOOR)

    def test_fenetre_et_plancher_surchargeables(self) -> None:
        taxonomie = {"signature_titre": {"fenetre_tete": 40, "plancher_texte_utile": 900}}
        self.assertEqual(_title_head_chars(taxonomie), 40)
        self.assertEqual(_useful_text_floor(taxonomie), 900)

    def test_alias_anglais(self) -> None:
        taxonomie = {"title_signature": {"head_window": 55, "useful_text_floor": 77}}
        self.assertEqual(_title_head_chars(taxonomie), 55)
        self.assertEqual(_useful_text_floor(taxonomie), 77)

    def test_fenetre_trop_courte_fait_manquer_un_titre_tardif(self) -> None:
        # `entete` et non `corps`: ce test mesure l'effet de la FENETRE, donc
        # ce qui precede le titre doit etre clos, sans quoi il mesurerait en
        # meme temps l'effet de la borne d'enonce et ne prouverait ni l'un ni
        # l'autre.
        texte = entete(94) + "Proces-verbal de l assemblee generale " + corps(2000)
        self.assertEqual(
            title_signature_verdict(texte, TITRE, 40, DEFAULT_USEFUL_TEXT_FLOOR),
            CLASSIFICATION_DOUBT_STATUS,
        )
        self.assertEqual(title_signature_verdict(texte, TITRE, 300, DEFAULT_USEFUL_TEXT_FLOOR), "")

    def test_controle_desactivable(self) -> None:
        self.assertEqual(_title_signatures({"signature_titre": {"motifs": {}}}), {})

    def test_valeur_invalide_retombe_sur_le_defaut(self) -> None:
        for mauvaise in ("", "abc", 0, -5, None):
            with self.subTest(valeur=mauvaise):
                taxonomie = {"signature_titre": {"fenetre_tete": mauvaise}}
                self.assertEqual(_title_head_chars(taxonomie), DEFAULT_TITLE_HEAD_CHARS)


class ClassifySignatureIntegrationTests(unittest.TestCase):
    """Le controle s applique pendant classify(), sans changer le type."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "instance"
        shutil.copytree(EXAMPLE_INSTANCE, self.root)
        self.instance = load_instance(str(self.root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _ecrire(self, cas) -> None:
        text_dir = self.root / "staging" / "text"
        text_dir.mkdir(parents=True, exist_ok=True)
        lignes = []
        for doc_id, nom, texte in cas:
            (text_dir / (doc_id + ".txt")).write_text(texte, encoding="utf-8")
            ligne = {champ: "" for champ in DEFAULT_DOCUMENT_FIELDS}
            ligne.update(
                {
                    "doc_id": doc_id,
                    "instance_id": self.instance.instance_id,
                    "file_name": nom,
                    "original_path": "raw/" + nom,
                    "text_path": "staging/text/" + doc_id + ".txt",
                }
            )
            lignes.append(ligne)
        write_csv(self.instance.register("documents"), list(DEFAULT_DOCUMENT_FIELDS), lignes)

    def _statuts(self):
        _, lignes = read_csv(self.instance.register("documents"))
        return {l["doc_id"]: (l["document_type"], l["classification_status"]) for l in lignes}

    def test_les_trois_issues_sur_un_meme_lot(self) -> None:
        self._ecrire(
            [
                ("DOC-VRAI", "2024-07-03_pv_ago.pdf",
                 "PROCES-VERBAL DE L ASSEMBLEE GENERALE ORDINAIRE du 03/07/2024 " + corps(3000)),
                ("DOC-TRAVAIL", "pv_ag_matrice_risques.csv",
                 "risque_id,lot,risque\nRSK-001,Syndic,mandat expire\n" + corps(2000)),
                ("DOC-SCAN", "pv_ag_scanne.pdf",
                 " ".join("page %d" % n for n in range(1, 40))),
            ]
        )
        classify(self.instance, RunContext(self.instance, "test-signature"), copy_files=False)
        statuts = self._statuts()
        self.assertEqual(statuts["DOC-VRAI"], ("PV_AG", "AUTO_CLASSIFIED"))
        self.assertEqual(statuts["DOC-TRAVAIL"], ("PV_AG", CLASSIFICATION_DOUBT_STATUS))
        self.assertEqual(statuts["DOC-SCAN"], ("PV_AG", CLASSIFICATION_NO_TEXT_STATUS))

    def test_le_type_nest_jamais_change_par_le_controle(self) -> None:
        self._ecrire([("DOC-TRAVAIL", "pv_ag_journal.md", "# Journal des decisions\n" + corps(2000))])
        classify(self.instance, RunContext(self.instance, "test-signature"), copy_files=False)
        type_doc, statut = self._statuts()["DOC-TRAVAIL"]
        self.assertEqual(type_doc, "PV_AG")
        self.assertEqual(statut, CLASSIFICATION_DOUBT_STATUS)

    def test_une_note_explique_le_doute(self) -> None:
        self._ecrire([("DOC-TRAVAIL", "pv_ag_journal.md", "# Journal des decisions\n" + corps(2000))])
        classify(self.instance, RunContext(self.instance, "test-signature"), copy_files=False)
        _, lignes = read_csv(self.instance.register("documents"))
        self.assertIn("Titre PV_AG absent", lignes[0]["notes"])

    def test_un_type_sans_signature_nest_pas_touche(self) -> None:
        self._ecrire([("DOC-FACTURE", "facture_2024.pdf", "FACTURE numero 42 " + corps(2000))])
        classify(self.instance, RunContext(self.instance, "test-signature"), copy_files=False)
        type_doc, statut = self._statuts()["DOC-FACTURE"]
        self.assertNotEqual(type_doc, "PV_AG")
        self.assertNotIn(statut, {CLASSIFICATION_DOUBT_STATUS, CLASSIFICATION_NO_TEXT_STATUS})


if __name__ == "__main__":
    unittest.main()
