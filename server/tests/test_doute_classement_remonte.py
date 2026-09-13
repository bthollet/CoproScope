"""`RM-2026-0056`: le doute produit par le classement doit atteindre un humain.

Ce module mesure la propriete qui remplace une liste de statuts douteux: ce qui
remonte a la boite de reception se definit par le COMPLEMENT des statuts qui
affirment un classement etabli. La difference n'est pas cosmetique - une liste
de modalites laisse tomber le statut suivant en silence, un complement ne le
peut pas.

Ce que ce fichier garde, et pourquoi chaque garde existe:

1. Un statut FABRIQUE ICI, que le depot n'a jamais ecrit, remonte quand meme.
   C'est la seule garde qui distingue un critere inverse d'une liste allongee:
   une liste peut contenir `A_RECLASSER` et `TEXTE_INSUFFISANT` et echouer a
   ce test.
2. Les deux etats de doute reellement produits remontent.
3. Une piece dont le classement EST etabli ne remonte pas. Sans cette garde,
   un critere qui rendrait "remonte" pour tout ferait passer les autres tests
   en ne mesurant rien.
4. Le motif de remontee NOMME le statut inconnu, au lieu de montrer la piece
   sans dire pourquoi.
5. Un statut de doute n'est plus promu en proposition acceptable a l'ecran.
   C'est le second verrou du meme defaut: la piece atteignait parfois la page,
   mais son doute y etait retourne en affirmation.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

from coproscope.core.classement_etabli import (
    CLASSEMENT_ETABLI,
    MOTIF_STATUT_INCONNU,
    MOTIFS_DE_REMONTEE,
    classement_est_etabli,
    doit_remonter_a_l_humain,
    motif_de_remontee,
)
from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, load_instance, read_csv, write_csv
from coproscope.modules import document_intake
from coproscope.web.app import create_app


#: Les deux etats de doute que le classement par signature de forme produit.
#: Ils sont cites en clair parce que ce sont eux que le lot a trouves muets.
DOUTE_TITRE_ABSENT = "A_RECLASSER"
DOUTE_TEXTE_ABSENT = "TEXTE_INSUFFISANT"


def _statut_jamais_vu(graine: str = "") -> str:
    """Fabrique un statut que ce depot n'a jamais ecrit.

    L'aleatoire est le point: un statut ecrit en dur dans le test finirait par
    etre ajoute a une liste quelque part, et la garde cesserait de mesurer la
    propriete qu'elle croit mesurer.
    """
    return f"STATUT_INVENTE_{graine}{uuid.uuid4().hex[:10].upper()}"


class CritereDeRemonteeTests(unittest.TestCase):
    """Le critere lui-meme, sans passer par la couche web."""

    def test_un_statut_jamais_vu_du_code_remonte_a_l_humain(self) -> None:
        for essai in range(20):
            statut = _statut_jamais_vu(f"{essai}_")
            self.assertFalse(
                classement_est_etabli(statut),
                f"{statut} ne devrait affirmer aucun classement etabli",
            )
            self.assertTrue(
                doit_remonter_a_l_humain(statut),
                f"{statut} doit remonter: un statut inconnu se signale, il ne "
                "se range pas en silence dans 'classe'",
            )

    def test_les_deux_etats_de_doute_du_classement_remontent(self) -> None:
        for statut in (DOUTE_TITRE_ABSENT, DOUTE_TEXTE_ABSENT):
            with self.subTest(statut=statut):
                self.assertTrue(doit_remonter_a_l_humain(statut))
                self.assertNotEqual(motif_de_remontee(statut), MOTIF_STATUT_INCONNU)
                self.assertIn(statut, MOTIFS_DE_REMONTEE)

    def test_un_classement_etabli_ne_remonte_pas(self) -> None:
        # Sans cette garde, un critere qui rendrait "remonte" pour tout ferait
        # passer les autres tests en ne mesurant rien.
        self.assertTrue(CLASSEMENT_ETABLI, "la liste des statuts etablis est vide")
        for statut in CLASSEMENT_ETABLI:
            with self.subTest(statut=statut):
                self.assertTrue(classement_est_etabli(statut))
                self.assertFalse(doit_remonter_a_l_humain(statut))
                self.assertEqual(motif_de_remontee(statut), "")

    def test_le_critere_ignore_la_casse_et_les_espaces(self) -> None:
        for variante in (" auto_classified ", "Auto_Classified", "AUTO_CLASSIFIED"):
            with self.subTest(variante=variante):
                self.assertTrue(classement_est_etabli(variante))

    def test_le_motif_nomme_le_statut_inconnu(self) -> None:
        motif = motif_de_remontee(_statut_jamais_vu())
        self.assertEqual(motif, MOTIF_STATUT_INCONNU)
        self.assertIn("non interprete", motif)

    def test_une_valeur_vide_ou_absente_remonte(self) -> None:
        for valeur in ("", "   ", None):
            with self.subTest(valeur=valeur):
                self.assertTrue(doit_remonter_a_l_humain(valeur))


class QualificationDuDouteTests(unittest.TestCase):
    """Le second verrou: le doute ne doit pas se retourner en affirmation."""

    def _etape_classification(self, statut: str, document_type: str = "Convocation_AG"):
        intake = document_intake.normalize_document_intake(
            {
                "doc_id": "DOC-DOUTE",
                "display_name": "Piece 1",
                "sha256": "a" * 64,
                "document_type": document_type,
                "classification_status": statut,
            }
        )
        runtime = document_intake.build_runtime_checklist(intake)
        for item in runtime.checklist:
            if item.step_id == document_intake.STEP_CLASSIFICATION:
                return intake, item
        self.fail("aucune etape de classification dans la checklist")

    def test_un_statut_inconnu_n_est_pas_promu_en_proposition(self) -> None:
        # Le defaut mesure: statut inconnu -> rabattu sur PENDING -> promu en
        # PROPOSED des qu'un type existait -> etape cochee OK. Une piece dont
        # le classement etait explicitement en doute ressortait reglee.
        intake, etape = self._etape_classification(_statut_jamais_vu())
        self.assertNotEqual(intake.classification.status, document_intake.CLASSIFICATION_PROPOSED)
        self.assertNotEqual(intake.classification.status, document_intake.CLASSIFICATION_ACCEPTED)
        self.assertEqual(etape.status, document_intake.CHECK_TODO)

    def test_les_deux_doutes_ne_cochent_pas_l_etape_de_classification(self) -> None:
        for statut in (DOUTE_TITRE_ABSENT, DOUTE_TEXTE_ABSENT):
            with self.subTest(statut=statut):
                intake, etape = self._etape_classification(statut)
                self.assertEqual(intake.classification.status, statut)
                self.assertEqual(etape.status, document_intake.CHECK_TODO)
                self.assertTrue(etape.next_action.strip())

    def test_un_type_accepte_reste_coche(self) -> None:
        # Garde de contraste: si tout devenait "a faire", les tests ci-dessus
        # passeraient sans rien mesurer.
        _, etape = self._etape_classification(document_intake.CLASSIFICATION_ACCEPTED)
        self.assertEqual(etape.status, document_intake.CHECK_OK)


class BoiteDeReceptionTests(unittest.TestCase):
    """La preuve de bout en bout: la piece douteuse apparait sur la page."""

    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(repo_root / "examples" / "synthetic_copro", self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _ligne(self, doc_id: str, statut: str, empreinte: str) -> dict[str, str]:
        """Une ligne dont le SEUL motif de remontee possible est le classement.

        Tout le reste est deliberement propre: OCR fait, confidentialite
        tranchee, forme de publication brute, type decide. Sans cette hygiene,
        le test passerait pour une autre raison que celle qu'il croit mesurer.
        """
        row = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        row.update(
            {
                "doc_id": doc_id,
                "sha256": empreinte * 64,
                "original_path": r"200_INBOX\piece.pdf",
                "file_name": "piece.pdf",
                "extension": "pdf",
                "size_bytes": "2048",
                "source_zone": "200_INBOX",
                "source_kind": "copie_primaire",
                "document_type": "Convocation_AG",
                "classification_status": statut,
                "status_ocr": "TEXT_EXTRACTED",
                "text_char_count": "1200",
                "privacy_review_status": "AUTO_POLICY",
                "publication_form": "raw",
            }
        )
        return row

    def test_L_INDICATEUR_COMPTE_COMME_LA_BOITE_meme_sur_un_statut_invente(self) -> None:
        """La TROISIEME liste du meme fichier, que ce lot avait laissee.

        **Mesure du 2026-09-09, par contre-enquete.** Deux enumerations avaient
        ete inversees; une troisieme vivait 380 lignes plus bas dans
        `04_completeness_and_kpis.py`, dans `compute_kpis`. Consequence:
        **l'indicateur publie comptait comme CLASSES des documents que la boite
        de reception montrait comme douteux** - deux comptages concurrents pour
        la meme notion, dans un seul fichier, ce qui est le defaut numero un du
        produit.

        Et rien ne le gardait: `compute_kpis` et `KPI-002` n'apparaissaient
        **zero fois** dans `server/tests`. Retirer un statut de cette liste ne
        faisait echouer aucun test.

        Ce test mesure la propriete qui compte - **les deux repondent la meme
        chose** - et il la mesure sur un statut INVENTE, jamais vu du code,
        parce qu'une liste allongee passerait un test ecrit sur des valeurs
        connues.
        """
        from coproscope.modules import docuscope  # noqa: PLC0415

        lignes = [
            self._ligne("DOC-ETABLI", "AUTO_CLASSIFIED", "a"),
            self._ligne("DOC-DOUTE", "A_RECLASSER", "b"),
            self._ligne("DOC-INVENTE", "STATUT_JAMAIS_VU_XYZ", "c"),
        ]
        write_csv(self.instance.register("documents"), DEFAULT_DOCUMENT_FIELDS, lignes)

        attendu_boite = sum(
            1 for l in lignes if doit_remonter_a_l_humain(l["classification_status"])
        )
        self.assertEqual(2, attendu_boite, "fixture inutile: elle ne porte pas de doute")

        docuscope.compute_kpis(self.instance, docuscope.RunContext(self.instance, "test"))
        _, kpi = read_csv(self.instance.register("kpi"))
        ligne = next(k for k in kpi if k.get("kpi_id") == "KPI-002")
        part = float(str(ligne["value"]).rstrip("%").replace(",", "."))

        self.assertAlmostEqual(
            100.0 * attendu_boite / len(lignes), part, places=1,
            msg="l'indicateur et la boite de reception ne comptent pas la meme chose: "
                "KPI-002 dit %s pour %d document(s) que la boite montre comme douteux"
                % (ligne["value"], attendu_boite),
        )

    def _page_boite(self, lignes: list[dict[str, str]]) -> str:
        write_csv(self.instance.register("documents"), DEFAULT_DOCUMENT_FIELDS, lignes)
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:  # pragma: no cover - depend de l'environnement
            self.skipTest("FastAPI test client indisponible")
        client = TestClient(create_app(self.instance, 2025, access_token=None, rebrancher=frozenset({"ajouter_document"})))
        page = client.get("/documents/ajouter?source=inbox")
        self.assertEqual(page.status_code, 200)
        return page.text

    def test_le_doute_et_le_statut_inconnu_apparaissent_dans_la_boite(self) -> None:
        texte = self._page_boite(
            [
                self._ligne("DOC-DOUTE-TITRE", DOUTE_TITRE_ABSENT, "a"),
                self._ligne("DOC-DOUTE-TEXTE", DOUTE_TEXTE_ABSENT, "b"),
                self._ligne("DOC-INVENTE", _statut_jamais_vu(), "c"),
            ]
        )
        self.assertIn("DOC-DOUTE-TITRE", texte)
        self.assertIn("DOC-DOUTE-TEXTE", texte)
        self.assertIn(
            "DOC-INVENTE",
            texte,
            "un statut que cette version n'a jamais vu doit remonter par defaut",
        )
        # Remonter ne suffit pas: la page doit DIRE pourquoi, sinon l'humain
        # herite du travail de deviner ce que le code n'a pas su lire.
        self.assertIn("statut non compris, a verifier", texte)
        self.assertIn("Statut de classement non interprete par cette version", texte)
        self.assertIn("rien de lisible dans la piece", texte)
        self.assertIn("Le contenu a ete lu, mais le titre attendu", texte)

    def test_une_piece_au_classement_etabli_n_apparait_pas(self) -> None:
        # La garde de contraste de bout en bout. Si la boite montrait tout,
        # le test ci-dessus passerait sans rien prouver.
        texte = self._page_boite(
            [
                self._ligne("DOC-REGLE", "AUTO_CLASSIFIED", "d"),
                self._ligne("DOC-DOUTEUX", DOUTE_TITRE_ABSENT, "e"),
            ]
        )
        self.assertIn("DOC-DOUTEUX", texte)
        self.assertNotIn("DOC-REGLE", texte)


class ResiduConnuTests(unittest.TestCase):
    """Ce que ce lot laisse expose, nomme ici plutot que dans une phrase.

    Le rapport de completude pose une question VOISINE mais differente de celle
    de la boite de reception: non pas "le classement est-il etabli", mais "le
    CONTENU a-t-il ete lu". `AUTO_CLASSIFIED` est le seul statut qui l'affirme,
    et c'est volontaire: un humain qui accepte un type n'a pas fait lire la
    piece a la machine.

    Consequence non corrigee par ce lot: `ACCEPTED` et `DEMO_CLASSIFIED` sont
    des statuts CONNUS, mais le constat de lecture les range dans
    `STATUT_INCONNU`. La degradation reste du bon cote - ils ressortent "a
    verifier", jamais "couvert" - donc rien n'est affirme a tort. Mais le motif
    affiche est faux: ils ne sont pas incompris, ils ne sont simplement pas le
    fruit d'une lecture automatique.

    Ce test PIN le comportement actuel. S'il casse, c'est que quelqu'un a
    traite le residu: qu'il mette alors a jour cette docstring au lieu de
    supprimer la garde.
    """

    def _constat(self, statut: str) -> str:
        from coproscope.modules import docuscope

        return docuscope._reading_gap(
            {"document_type": "Facture", "classification_status": statut}
        )

    def test_seule_la_lecture_automatique_vaut_contenu_lu(self) -> None:
        self.assertEqual(self._constat("AUTO_CLASSIFIED"), "")

    def test_les_deux_doutes_sont_nommes_distinctement(self) -> None:
        self.assertEqual(self._constat(DOUTE_TITRE_ABSENT), "TYPE_A_REVOIR")
        self.assertEqual(self._constat(DOUTE_TEXTE_ABSENT), "TYPE_SUR_NOM_DE_FICHIER")

    def test_residu_statuts_humains_ranges_en_inconnu(self) -> None:
        # Le residu lui-meme. Non corrige par ce lot, et borne: la sortie reste
        # "a verifier", donc aucune couverture n'est affirmee a tort.
        for statut in ("ACCEPTED", "DEMO_CLASSIFIED"):
            with self.subTest(statut=statut):
                self.assertEqual(self._constat(statut), "STATUT_INCONNU")
                self.assertTrue(
                    doit_remonter_a_l_humain(statut) is False,
                    "ces statuts affirment bien un classement etabli pour la"
                    " boite de reception: c'est le constat de LECTURE qui les"
                    " nomme mal, pas le critere de remontee",
                )

    def test_un_statut_inconnu_reste_signale_par_le_constat_de_lecture(self) -> None:
        self.assertEqual(self._constat(_statut_jamais_vu()), "STATUT_INCONNU")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
