"""Le college de confidentialite divergeait entre deux exemplaires d'un contenu.

`RM-2026-0088`, deuxieme passe. La premiere reparation confrontait TROIS champs
- `lot`, `document_type`, `suspected_date` - c'est-a-dire exactement les trois
que l'enonce de l'item citait. C'etait une enumeration de modalites, et elle a
rendu un chiffre faux sans faire echouer un seul test: le journal de la course
annoncait `desaccords_empreinte=0` pendant que neuf autres champs divergeaient.

MESURE DU 2026-09-09, base `ffac60c` + le lot mesure, instance
`examples/synthetic_copro` jetable. Deux lignes de meme SHA-256, meme texte,
deux denominations. `classify` ecrit 18 colonnes du registre, pas trois:
`apply_access_policy(row, ...)` fait `row.update(build_access_policy(...))` et
en pose 13 de plus, a partir d'un foin construit sur `file_name`,
`original_path` et `document_type` - trois DENOMINATIONS. Resultat mesure:

    raw_max_college        C2_Coproprietaires   /  C8_Restreint_Critique
    publication_form       raw                  /  aggregation_required
    ai_processing_ceiling  local_only           /  no_ai
    review_required        (vide)               /  YES
    personal_data_level    none                 /  nominative

Les deux lignes sortaient `AUTO_CLASSIFIED`, sans une note. Le champ qui decide
QUI a le droit de voir la piece divergeait en silence.

RESERVE DE MESURE, verifiee et non recopiee. Le defaut n'est reproductible sur
aucun corpus present sur ce poste: `examples/synthetic_copro` 9 lignes / 9
empreintes, `demo_fictive_tilleuls` 21/21, `erables_pseudo_test` 22/22,
`test_identite_ag_20260908` 858/858, `tests_ux` vide, et le `MANIFEST_SOURCE.csv`
de l'instance mere 858 empreintes distinctes sur 858 lignes. Ces tests
reconstituent donc le cas a la main. Ils prouvent le comportement du code; ils
ne mesurent aucune volumetrie reelle.

RESIDU NOMME ET NON TRAITE ICI. Nommer la divergence de college ne dit pas
laquelle des deux valeurs gouverne la publication. Retenir la plus restrictive
serait une election, que l'item interdit ("rien n'est elu"); ne rien retenir
laisse un chemin de diffusion libre de lire la ligne permissive. C'est une
DECISION PRODUIT, elle est posee au fil pilote et n'est pas tranchee par ce lot.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import (
    DEFAULT_DOCUMENT_FIELDS,
    RunContext,
    load_instance,
    read_csv,
    write_csv,
)
from coproscope.modules.docuscope import (
    CHAMPS_EXEMPTES,
    CLASSIFICATION_DOUBT_STATUS,
    MENTION_DESACCORD,
    champs_du_verdict_sur_le_contenu,
    classify,
    reconcilier_par_empreinte,
)

EXAMPLE_INSTANCE = Path(__file__).resolve().parents[2] / "examples" / "synthetic_copro"

EMPREINTE = "7139edad85e4" + "0" * 52
DOC_ID = "DOC-7139EDAD85E4"

# Deux denominations d'un meme contenu. La seconde porte dans son nom deux mots
# que le moteur de politique d'acces lit comme des signaux: c'est une
# denomination, pas le contenu, et c'est exactement la ou le defaut se loge.
PV = "10_assemblees/2024-07-03_pv_AGO.pdf"
SIGNALANT = "90_pieges/pv AGO contentieux impayes 03072024.pdf"


def corps(longueur: int) -> str:
    motif = "la residence entretient ses espaces verts et sa cage d escalier "
    return (motif * (longueur // len(motif) + 1))[:longueur]


PV_DATE = (
    "PROCES-VERBAL DE L ASSEMBLEE GENERALE ORDINAIRE des coproprietaires "
    "tenue le 3 juillet 2024. " + corps(3000)
)


class PolitiqueDAccesConcurrenteTests(unittest.TestCase):
    """Deux exemplaires d'un contenu, deux politiques d'acces: ca se nomme."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name) / "instance"
        shutil.copytree(EXAMPLE_INSTANCE, self.root)
        self.instance = load_instance(str(self.root / "instance.yml"), None)

    def _classer(self, denominations):
        dossier = self.root / "staging" / "text"
        dossier.mkdir(parents=True, exist_ok=True)
        (dossier / (DOC_ID + ".txt")).write_text(PV_DATE, encoding="utf-8")
        lignes = []
        for chemin in denominations:
            ligne = {champ: "" for champ in DEFAULT_DOCUMENT_FIELDS}
            ligne.update(
                {
                    "doc_id": DOC_ID,
                    "instance_id": self.instance.instance_id,
                    "sha256": EMPREINTE,
                    "file_name": chemin.rsplit("/", 1)[-1],
                    "original_path": chemin,
                    "text_path": "staging/text/" + DOC_ID + ".txt",
                }
            )
            lignes.append(ligne)
        write_csv(self.instance.register("documents"), list(DEFAULT_DOCUMENT_FIELDS), lignes)
        classify(self.instance, RunContext(self.instance, "test-politique"), copy_files=False)
        _, sorties = read_csv(self.instance.register("documents"))
        return {ligne["original_path"]: ligne for ligne in sorties}

    def test_le_college_de_confidentialite_diverge_bien_entre_les_deux(self) -> None:
        # D'abord prouver que le cas EXISTE. Sans cela, le test suivant serait
        # vert parce qu'il ne mesure rien.
        lignes = self._classer([PV, SIGNALANT])
        self.assertNotEqual(
            lignes[PV]["raw_max_college"], lignes[SIGNALANT]["raw_max_college"]
        )

    def test_la_divergence_de_college_est_nommee_sur_les_deux_lignes(self) -> None:
        # DEFAUT MESURE: aucune note, sur aucune des deux lignes.
        lignes = self._classer([PV, SIGNALANT])
        for chemin in (PV, SIGNALANT):
            self.assertIn(MENTION_DESACCORD, lignes[chemin]["notes"])
            self.assertIn("raw_max_college", lignes[chemin]["notes"])

    def test_la_divergence_de_forme_de_publication_est_nommee(self) -> None:
        # `publication_form` decide de ce qui peut sortir tel quel. Deux
        # exemplaires d'un meme contenu ne peuvent pas repondre differemment.
        lignes = self._classer([PV, SIGNALANT])
        self.assertIn("publication_form", lignes[PV]["notes"])

    def test_aucune_ligne_ne_reste_affirmee_sur_une_politique_divergente(self) -> None:
        # DEFAUT MESURE: les deux lignes sortaient `AUTO_CLASSIFIED`.
        lignes = self._classer([PV, SIGNALANT])
        for chemin in (PV, SIGNALANT):
            self.assertEqual(
                lignes[chemin]["classification_status"], CLASSIFICATION_DOUBT_STATUS
            )

    def test_aucune_valeur_de_politique_n_est_elue_ni_heritee(self) -> None:
        # GARDE-FOU. Nommer n'est pas resorber: les deux valeurs survivent
        # telles quelles, et aucune n'est recopiee dans l'autre ligne.
        lignes = self._classer([PV, SIGNALANT])
        self.assertEqual(lignes[PV]["raw_max_college"], "C2_Coproprietaires")
        self.assertEqual(lignes[SIGNALANT]["raw_max_college"], "C8_Restreint_Critique")


class ConfrontationParDefautTests(unittest.TestCase):
    """Un champ que le code n'a jamais vu se degrade bruyamment, pas en silence."""

    def _ligne(self, **champs) -> dict:
        ligne = {champ: "" for champ in DEFAULT_DOCUMENT_FIELDS}
        ligne.update(champs)
        return ligne

    def test_un_champ_ecrit_hors_row_crochet_est_quand_meme_confronte(self) -> None:
        # Trois mutations de `classify` jouees le 2026-09-09 echappaient au
        # lecteur d'arbre syntaxique de la premiere garde: `row.update({...})`,
        # une cle variable, une ecriture par helper. La maniere d'ecrire
        # n'entre plus dans la regle: `emitter` est confronte parce qu'il n'est
        # pas exempte, quel que soit le code qui l'a pose.
        lignes = [
            self._ligne(sha256=EMPREINTE, emitter="Cabinet A"),
            self._ligne(sha256=EMPREINTE, emitter="Cabinet B"),
        ]
        comptes = reconcilier_par_empreinte(lignes)
        self.assertEqual(comptes["desaccords"], 1)
        self.assertEqual(comptes["champs_en_desaccord"], "emitter")
        for ligne in lignes:
            self.assertIn(MENTION_DESACCORD, ligne["notes"])

    def test_une_colonne_inconnue_du_registre_est_confrontee(self) -> None:
        # LE TEST D'ACCEPTATION DE LA REGLE DES AXES. Une valeur que le code n'a
        # jamais vue - ici une colonne qui n'existe dans aucune liste - ne doit
        # pas produire une reponse fausse en silence. Elle tombe du cote
        # bruyant: elle est confrontee.
        lignes = [
            self._ligne(sha256=EMPREINTE, **{"champ_invente_demain": "oui"}),
            self._ligne(sha256=EMPREINTE, **{"champ_invente_demain": "non"}),
        ]
        comptes = reconcilier_par_empreinte(lignes)
        self.assertEqual(comptes["champs_en_desaccord"], "champ_invente_demain")

    def test_une_colonne_exemptee_ne_declenche_rien(self) -> None:
        # Le pendant: ce qui decrit l'exemplaire depose differe par
        # construction, et ne doit pas remplir le registre de bruit.
        lignes = [
            self._ligne(sha256=EMPREINTE, original_path="a/x.pdf", file_name="x.pdf"),
            self._ligne(sha256=EMPREINTE, original_path="b/y.pdf", file_name="y.pdf"),
        ]
        comptes = reconcilier_par_empreinte(lignes)
        self.assertEqual(comptes["desaccords"], 0)
        self.assertEqual([ligne["notes"] for ligne in lignes], ["", ""])

    def test_le_journal_nomme_les_champs_et_pas_seulement_leur_nombre(self) -> None:
        # Un compteur seul ne dit pas si le desaccord porte sur le type du
        # document ou sur le college de confidentialite. Les deux n'appellent
        # pas la meme suite.
        lignes = [
            self._ligne(sha256=EMPREINTE, document_type="PV_AG", raw_max_college="C2_Coproprietaires"),
            self._ligne(sha256=EMPREINTE, document_type="Convocation_AG", raw_max_college="C8_Restreint_Critique"),
        ]
        comptes = reconcilier_par_empreinte(lignes)
        self.assertEqual(comptes["champs_en_desaccord"], "document_type;raw_max_college")

    def test_l_instrument_confronte_bien_quelque_chose(self) -> None:
        # Si la liste des champs confrontes etait vide, tous les tests
        # ci-dessus passeraient en ne mesurant rien.
        confrontes = champs_du_verdict_sur_le_contenu(DEFAULT_DOCUMENT_FIELDS)
        self.assertGreaterEqual(len(confrontes), 10)
        self.assertEqual(
            len(confrontes) + len(set(CHAMPS_EXEMPTES) & set(DEFAULT_DOCUMENT_FIELDS)),
            len(DEFAULT_DOCUMENT_FIELDS),
        )


class DeuxReconciliationsConcurrentesTests(unittest.TestCase):
    """Deux modules reconcilient le meme contenu, avec deux listes differentes.

    TROUVE LE 2026-09-09, et personne ne l'avait dit. `_pont_actes_source.
    registre_documents` fait DEJA, depuis le 2026-09-04, une reconciliation
    entre lignes de meme `doc_id`: il retient la premiere ligne portant un
    `text_path` et nomme les identifiants ambigus. Sa liste decisive est
    `("text_path", "suspected_date")`; celle du classement en est une autre.

    C'est le defaut numero un du produit tel que la doctrine du depot le nomme:
    deux comptages concurrents pour la meme notion. `document_type` est decisif
    au classement et ABSENT de la liste du pont - alors meme que la docstring du
    pont dit avoir mesure "deux types documentaires opposes" sur un meme
    identifiant. Et `text_path` est decisif au pont, exempte au classement
    (l'un des exemplaires a pu etre lu, l'autre non).

    CE TEST NE FUSIONNE RIEN: unifier les deux listes changerait le
    comportement du pont, ce qui n'est ni mon perimetre ni une evidence. Il
    EPINGLE la relation actuelle pour qu'une derive de l'une ou l'autre liste
    se voie, au lieu de s'installer en silence. La fusion est une DECISION
    PRODUIT, posee au fil pilote.
    """

    def test_la_relation_entre_les_deux_listes_est_epinglee(self) -> None:
        from coproscope.modules._pont_actes_source import CHAMPS_DECISIFS

        confrontes = set(champs_du_verdict_sur_le_contenu(DEFAULT_DOCUMENT_FIELDS))
        decisifs = set(CHAMPS_DECISIFS)
        self.assertEqual(
            decisifs - confrontes,
            {"text_path"},
            "le pont juge decisif un champ que le classement ne confronte pas,"
            " et ce n'est plus le seul cas connu: trancher la fusion des deux"
            " listes.",
        )
        self.assertIn(
            "document_type",
            confrontes - decisifs,
            "le classement confrontait `document_type` et le pont ne le jugeait"
            " pas decisif: si cela a change, la note de ce test est perimee.",
        )


if __name__ == "__main__":
    unittest.main()
