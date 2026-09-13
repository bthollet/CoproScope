"""Une empreinte identifie un contenu, pas une denomination.

`RM-2026-0088`. Deux fichiers de meme SHA-256 occupent deux lignes du registre
- une par CHEMIN - et `classify` les jugeait l'une apres l'autre sans jamais
les regarder ensemble. Un contenu unique sortait donc du classement avec deux
types et deux dates, dont AU MOINS UN affirme `AUTO_CLASSIFIED` sans qu'aucune
note ne signale l'autre.

**Ce que ces tests discriminent, et contre quoi.** Tous les tests de
`DesaccordDEmpreinteTests` et de `LecturePartielleDEmpreinteTests` ont ete
joues contre le code d'avant ce lot: ils y echouent, sauf
`test_les_valeurs_ne_sont_pas_modifiees` et
`test_la_date_ne_s_herite_pas_d_une_denomination_a_l_autre`, qui passaient deja
et qui sont des garde-fous - ils tiennent que la reconciliation N'ELIT PAS et
N'HERITE PAS, ce qui est precisement ce que `RM-2026-0088` interdit.
`NatureDeChaqueColonneTests` fixe un contrat de code neuf. Cette garde a ete
REECRITE le 2026-09-09: sa premiere version lisait la syntaxe de `classify`
et laissait passer `row.update(...)`, une cle variable et une ecriture par
helper. Elle porte maintenant sur les colonnes du registre.

**Reserve de mesure.** Le defaut n'est reproductible sur AUCUN corpus present
sur ce poste: `examples/synthetic_copro` (9 pieces), `demo_fictive_tilleuls`
(21), `erables_pseudo_test` (22) et `test_identite_ag_20260908` (858) portent
tous zero empreinte partagee. Le corpus ou il avait ete mesure - deux copies
dans `10_assemblees/` et `90_pieges/` - n'existe plus. Ces tests reconstituent
donc le cas a la main, a partir des deux denominations citees dans l'item. Ils
prouvent le comportement du code; ils ne mesurent aucune volumetrie reelle.
"""

from __future__ import annotations

import ast
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
    CHAMPS_DE_LA_DENOMINATION,
    CHAMPS_DE_TENUE_DE_LIGNE,
    CHAMPS_DU_VERDICT_CONNUS,
    CHAMPS_EXEMPTES,
    CLASSIFICATION_DOUBT_STATUS,
    MENTION_DESACCORD,
    MENTION_LECTURE_PARTIELLE,
    champs_du_verdict_sur_le_contenu,
    classify,
    grouper_par_empreinte,
    reconcilier_par_empreinte,
)

EXAMPLE_INSTANCE = Path(__file__).resolve().parents[2] / "examples" / "synthetic_copro"
CLASSIFICATION_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "coproscope"
    / "modules"
    / "_docuscope_parts"
    / "02_classification.py"
)

EMPREINTE = "7139edad85e4" + "0" * 52
DOC_ID = "DOC-7139EDAD85E4"


def corps(longueur: int) -> str:
    """Matiere de remplissage, sans mot-cle d'aucun type."""
    motif = "la residence entretient ses espaces verts et sa cage d escalier "
    return (motif * (longueur // len(motif) + 1))[:longueur]


PV_DATE = (
    "PROCES-VERBAL DE L ASSEMBLEE GENERALE ORDINAIRE des coproprietaires "
    "tenue le 3 juillet 2024. " + corps(3000)
)
PV_SANS_DATE = (
    "PROCES-VERBAL DE L ASSEMBLEE GENERALE ORDINAIRE des coproprietaires "
    "reunis en seance ordinaire. " + corps(3000)
)


class _SurInstance(unittest.TestCase):
    """Socle: une instance jetable, et des lignes qui partagent une empreinte."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "instance"
        shutil.copytree(EXAMPLE_INSTANCE, self.root)
        self.instance = load_instance(str(self.root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _classer(self, denominations, texte, empreinte: str = EMPREINTE):
        """Classe N denominations d'un MEME contenu, rendues par chemin."""
        text_dir = self.root / "staging" / "text"
        text_dir.mkdir(parents=True, exist_ok=True)
        (text_dir / (DOC_ID + ".txt")).write_text(texte, encoding="utf-8")
        lignes = []
        for chemin in denominations:
            ligne = {champ: "" for champ in DEFAULT_DOCUMENT_FIELDS}
            ligne.update(
                {
                    "doc_id": DOC_ID,
                    "instance_id": self.instance.instance_id,
                    "sha256": empreinte,
                    "file_name": chemin.rsplit("/", 1)[-1],
                    "original_path": chemin,
                    "text_path": "staging/text/" + DOC_ID + ".txt",
                }
            )
            lignes.append(ligne)
        write_csv(self.instance.register("documents"), list(DEFAULT_DOCUMENT_FIELDS), lignes)
        classify(self.instance, RunContext(self.instance, "test-empreintes"), copy_files=False)
        _, sorties = read_csv(self.instance.register("documents"))
        return {ligne["original_path"]: ligne for ligne in sorties}


class DesaccordDEmpreinteTests(_SurInstance):
    """Deux verdicts CONCURRENTS sur un meme contenu: ca se garde et s'affiche."""

    PV = "10_assemblees/2024-07-03_pv_AGO.pdf"
    CONVOC = "90_pieges/convocation_ag_2024.pdf"

    def _deux_denominations(self):
        return self._classer([self.PV, self.CONVOC], PV_DATE)

    def test_le_desaccord_de_type_est_nomme_sur_les_deux_lignes(self) -> None:
        # DEFAUT MESURE: la ligne `10_assemblees/...` sortait AUTO_CLASSIFIED en
        # PV_AG, sans une note, pendant que la ligne de meme empreinte sortait
        # Convocation_AG. Le desaccord n'existait nulle part.
        lignes = self._deux_denominations()
        for chemin in (self.PV, self.CONVOC):
            self.assertIn(MENTION_DESACCORD, lignes[chemin]["notes"])
            self.assertIn("PV_AG", lignes[chemin]["notes"])
            self.assertIn("Convocation_AG", lignes[chemin]["notes"])

    def test_aucune_ligne_ne_reste_affirmee(self) -> None:
        # Un type affirme AUTO_CLASSIFIED ne doit pas survivre a la decouverte
        # qu'un autre type porte le meme contenu.
        lignes = self._deux_denominations()
        for chemin in (self.PV, self.CONVOC):
            self.assertNotEqual(lignes[chemin]["classification_status"], "AUTO_CLASSIFIED")
        self.assertEqual(lignes[self.PV]["classification_status"], CLASSIFICATION_DOUBT_STATUS)

    def test_les_valeurs_ne_sont_pas_modifiees(self) -> None:
        # GARDE-FOU, il passait deja. Reconcilier veut dire NOMMER l'ecart, pas
        # le resorber: elire une copie serait trancher sans preuve, ce que
        # `RM-2026-0088` refuse explicitement apres correction du cadrage par
        # Brice ("laquelle des deux copies gagne" etait la mauvaise question).
        lignes = self._deux_denominations()
        self.assertEqual(lignes[self.PV]["document_type"], "PV_AG")
        self.assertEqual(lignes[self.CONVOC]["document_type"], "Convocation_AG")

    def test_un_statut_qui_doute_deja_n_est_pas_ecrase(self) -> None:
        # La ligne `90_pieges/...` porte deja un conflit de denomination INTERNE
        # (titre contre nom de fichier) qui l'a mise a A_RECLASSER. Le desaccord
        # d'empreinte s'y ajoute sans effacer ce que la ligne disait d'elle-meme.
        lignes = self._deux_denominations()
        self.assertIn("denominations en conflit", lignes[self.CONVOC]["notes"])
        self.assertIn(MENTION_DESACCORD, lignes[self.CONVOC]["notes"])

    def test_trois_denominations_se_confrontent_comme_deux(self) -> None:
        # L'AXE est le NOMBRE de denominations, pas la paire observee. Une
        # troisieme copie ne doit rien casser ni rien faire disparaitre.
        troisieme = "20_divers/pv assemblee 03 07 2024.pdf"
        lignes = self._classer([self.PV, self.CONVOC, troisieme], PV_DATE)
        self.assertEqual(len(lignes), 3)
        for chemin in lignes:
            self.assertIn(MENTION_DESACCORD, lignes[chemin]["notes"])
            self.assertIn("3 lignes", lignes[chemin]["notes"])


class LecturePartielleDEmpreinteTests(_SurInstance):
    """Une valeur en face d'une absence n'est PAS un desaccord."""

    PV = "10_assemblees/2024-07-03_pv_AGO.pdf"
    OPAQUE = "90_pieges/DIVERS_pv  03072024.pdf"

    def _une_date_lisible_sur_deux(self):
        # Le contenu ne porte pas de date: l'une des denominations en donne une,
        # l'autre non. C'est le cas exact mesure dans `RM-2026-0088`.
        return self._classer([self.PV, self.OPAQUE], PV_SANS_DATE)

    def test_la_date_ne_s_herite_pas_d_une_denomination_a_l_autre(self) -> None:
        # GARDE-FOU, il passait deja, et c'est l'interdit central de l'item:
        # "Ne PAS heriter une date d'un document a l'autre: la demander".
        lignes = self._une_date_lisible_sur_deux()
        self.assertEqual(lignes[self.PV]["suspected_date"], "2024-07-03")
        self.assertEqual(lignes[self.OPAQUE]["suspected_date"], "")

    def test_l_absence_de_date_est_nommee_la_ou_elle_manque(self) -> None:
        # DEFAUT MESURE: les deux lignes sortaient AUTO_CLASSIFIED sans note. En
        # aval, `_ag_id` fabrique alors DEUX assemblees d'un meme contenu -
        # `AG-2024-07-03` et `AG-DOC-...` - ce qui est `RM-2026-0077`.
        lignes = self._une_date_lisible_sur_deux()
        self.assertIn(MENTION_LECTURE_PARTIELLE, lignes[self.OPAQUE]["notes"])
        self.assertIn("2024-07-03", lignes[self.OPAQUE]["notes"])
        self.assertIn("se demande", lignes[self.OPAQUE]["notes"])

    def test_une_absence_ne_compte_pas_comme_un_desaccord(self) -> None:
        # La distinction est le coeur du lot: l'item dit "deux dates", la mesure
        # montre une date et une ABSENCE. Une absence n'est pas une seconde
        # valeur - c'est la lecon de `RM-2026-0077`, ou un repli sur l'absence
        # fabriquait une identite d'assemblee.
        lignes = self._une_date_lisible_sur_deux()
        self.assertNotIn(MENTION_DESACCORD, lignes[self.OPAQUE]["notes"])
        self.assertNotIn(MENTION_DESACCORD, lignes[self.PV]["notes"])

    def test_une_absence_ne_retire_pas_l_affirmation(self) -> None:
        # Une lecture incomplete ne contredit rien: elle ne doit donc pas
        # degrader le statut de la ligne qui, elle, a lu.
        lignes = self._une_date_lisible_sur_deux()
        self.assertEqual(lignes[self.PV]["classification_status"], "AUTO_CLASSIFIED")


class ComptesEtResiduTests(unittest.TestCase):
    """Ce que la reconciliation compte, et ce qu'elle avoue ne pas voir."""

    def _ligne(self, **champs) -> dict:
        ligne = {champ: "" for champ in DEFAULT_DOCUMENT_FIELDS}
        ligne.update(champs)
        return ligne

    def test_une_ligne_sans_empreinte_est_comptee_et_non_ignoree(self) -> None:
        # RESIDU NOMME. Sans SHA-256, aucune confrontation n'est possible. Le
        # taire ferait passer ces lignes pour reconciliees; `classify` en fait
        # une ligne du journal d'erreurs de la course.
        comptes = reconcilier_par_empreinte(
            [self._ligne(doc_id="A"), self._ligne(doc_id="B", sha256=EMPREINTE)]
        )
        self.assertEqual(comptes["lignes_sans_empreinte"], 1)
        self.assertEqual(comptes["groupes"], 0)

    def test_une_empreinte_seule_ne_produit_aucun_groupe(self) -> None:
        # Le cas dominant: un contenu, une denomination. Rien ne doit s'ecrire.
        lignes = [self._ligne(doc_id="A", sha256=EMPREINTE, document_type="PV_AG")]
        comptes = reconcilier_par_empreinte(lignes)
        self.assertEqual(comptes, {
            "groupes": 0,
            "desaccords": 0,
            "lectures_partielles": 0,
            "lignes_sans_empreinte": 0,
            "champs_en_desaccord": "",
        })
        self.assertEqual(lignes[0]["notes"], "")

    def test_l_accord_entre_denominations_n_ecrit_rien(self) -> None:
        # Deux denominations qui disent la meme chose sont un doublon franc.
        # `registre_doublons.csv` l'enregistre deja: rien a ajouter ici.
        lignes = [
            self._ligne(doc_id="A", sha256=EMPREINTE, document_type="PV_AG",
                        suspected_date="2024-07-03", lot="Assemblees"),
            self._ligne(doc_id="A", sha256=EMPREINTE, document_type="PV_AG",
                        suspected_date="2024-07-03", lot="Assemblees"),
        ]
        comptes = reconcilier_par_empreinte(lignes)
        self.assertEqual(comptes["groupes"], 1)
        self.assertEqual(comptes["desaccords"], 0)
        self.assertEqual(comptes["lectures_partielles"], 0)
        self.assertEqual([ligne["notes"] for ligne in lignes], ["", ""])

    def test_l_empreinte_est_comparee_sans_egard_a_la_casse(self) -> None:
        # Une empreinte hexadecimale s'ecrit en majuscules ou en minuscules
        # selon l'outil qui l'a produite. C'est le MEME contenu.
        lignes = [
            self._ligne(doc_id="A", sha256=EMPREINTE, document_type="PV_AG"),
            self._ligne(doc_id="A", sha256=EMPREINTE.upper(), document_type="Convocation_AG"),
        ]
        self.assertEqual(len(grouper_par_empreinte(lignes)), 1)


class NatureDeChaqueColonneTests(unittest.TestCase):
    """Aucune colonne du registre ne doit echapper a la confrontation.

    PREMIERE ECRITURE DE CETTE GARDE, ET SON DEFAUT MESURE. Elle lisait
    l'arbre syntaxique de `classify` et exigeait que chaque champ ecrit par
    `row["X"] = ...` soit declare. Elle se presentait comme un axe - "pas une
    orthographe, pas un grep" - et ne reconnaissait en fait qu'UNE SEULE
    maniere d'ecrire. Trois mutations jouees le 2026-09-09 la laissent verte:

        row.update({"emitter": doc_type})   # ecriture groupee
        _champ = "emitter"; row[_champ] = x # cle variable
        _poser_verdict(row, doc_type)       # ecriture par un helper

    Et ce n'etait pas theorique: `classify` appelle deja
    `apply_access_policy(row, ...)`, qui fait `row.update(...)` et pose 13
    champs - dont `raw_max_college` et `publication_form`. Mesure du
    2026-09-09: la garde voyait 5 champs, `classify` en ecrivait 18.

    LA GARDE PORTE MAINTENANT SUR LE MODELE DE DONNEES, PAS SUR LA SYNTAXE.
    Chaque colonne du registre a une nature declaree; ce qui n'est pas exempte
    est confronte. Une colonne ajoutee demain n'a aucune nature: elle fait
    tomber ce test en se nommant, et en attendant elle est confrontee - donc
    bruyante, jamais silencieuse.
    """

    def test_toute_colonne_du_registre_a_une_nature_declaree(self) -> None:
        # PREMIERE ECRITURE DE CE TEST: TAUTOLOGIE, mesuree le 2026-09-09. Elle
        # comparait `DEFAULT_DOCUMENT_FIELDS` a `exemptes | (tout sauf
        # exemptes)`, donc a lui-meme, et rendait `OK` sur une colonne neuve
        # ajoutee au registre sans nature. Elle etait exactement le defaut
        # qu'elle pretendait interdire.
        #
        # La comparaison porte maintenant sur un TEMOIN fige: l'etat du
        # registre au jour ou chaque colonne a ete rangee. Une colonne ajoutee
        # demain n'y figure pas et fait tomber ce test en se nommant.
        confrontees = set(champs_du_verdict_sur_le_contenu(DEFAULT_DOCUMENT_FIELDS))
        neuves = confrontees - set(CHAMPS_DU_VERDICT_CONNUS)
        disparues = set(CHAMPS_DU_VERDICT_CONNUS) - confrontees
        self.assertEqual(
            (neuves, disparues),
            (set(), set()),
            "colonne(s) du registre sans nature rangee: "
            + ", ".join(sorted(neuves))
            + " | temoin(s) devenu(s) sans colonne: "
            + ", ".join(sorted(disparues))
            + ". Ranger chaque colonne neuve dans CHAMPS_DE_LA_DENOMINATION,"
            " CHAMPS_DE_TENUE_DE_LIGNE ou CHAMPS_DU_VERDICT_CONNUS. En"
            " attendant, elle EST confrontee - bruyante, jamais silencieuse."
        )

    def test_les_deux_exemptions_ne_se_recouvrent_pas(self) -> None:
        self.assertEqual(
            set(CHAMPS_DE_LA_DENOMINATION) & set(CHAMPS_DE_TENUE_DE_LIGNE),
            set(),
        )

    def test_une_exemption_nomme_une_colonne_qui_existe(self) -> None:
        # Une exemption qui ne correspond a aucune colonne protege du vide et
        # laisse croire que le champ reel, lui, est exempte.
        fantomes = set(CHAMPS_EXEMPTES) - set(DEFAULT_DOCUMENT_FIELDS)
        self.assertEqual(
            fantomes, set(), "exemption(s) sans colonne correspondante: " + ", ".join(sorted(fantomes))
        )

    def test_les_champs_du_verdict_ne_sont_pas_vides(self) -> None:
        # Si l'instrument ne confrontait rien, tout paraitrait conforme.
        confrontes = champs_du_verdict_sur_le_contenu(DEFAULT_DOCUMENT_FIELDS)
        self.assertIn("document_type", confrontes)
        self.assertIn("suspected_date", confrontes)
        self.assertIn("raw_max_college", confrontes)
        self.assertNotIn("original_path", confrontes)
        self.assertNotIn("notes", confrontes)

    def test_ce_que_classify_ecrit_vraiment_a_une_nature(self) -> None:
        # MESURE A L'EXECUTION, et non lecture de syntaxe: on compare la ligne
        # avant et apres une course. Cela attrape ce qu'aucun lecteur d'arbre
        # syntaxique ne voit - une ecriture par helper, par `update`, ou par une
        # cle calculee.
        #
        # PORTEE EXACTE, mesuree et non supposee. Ce test lit le registre ECRIT.
        # Un controle negatif du 2026-09-09 - `classify` posant, par un helper,
        # une cle absente des colonnes du registre - l'a laisse VERT: `write_csv`
        # ne retient que les colonnes declarees, donc cette cle ne survit pas
        # jusqu'ici. Ce n'est pas un trou de comportement - la confrontation,
        # elle, tourne en memoire avant l'ecriture et voit bien cette cle - mais
        # c'est un trou de MESURE, et il se nomme au lieu d'etre suppose couvert.
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        racine = Path(tempdir.name) / "instance"
        shutil.copytree(EXAMPLE_INSTANCE, racine)
        instance = load_instance(str(racine / "instance.yml"), None)
        dossier = racine / "staging" / "text"
        dossier.mkdir(parents=True, exist_ok=True)
        (dossier / (DOC_ID + ".txt")).write_text(PV_DATE, encoding="utf-8")
        avant = {champ: "" for champ in DEFAULT_DOCUMENT_FIELDS}
        avant.update(
            {
                "doc_id": DOC_ID,
                "instance_id": instance.instance_id,
                "sha256": EMPREINTE,
                "file_name": "2024-07-03_pv_AGO.pdf",
                "original_path": "10_assemblees/2024-07-03_pv_AGO.pdf",
                "text_path": "staging/text/" + DOC_ID + ".txt",
            }
        )
        write_csv(instance.register("documents"), list(DEFAULT_DOCUMENT_FIELDS), [dict(avant)])
        classify(instance, RunContext(instance, "test-nature"), copy_files=False)
        _, sorties = read_csv(instance.register("documents"))
        apres = sorties[0]
        ecrits = {
            champ
            for champ in set(avant) | set(apres)
            if (avant.get(champ) or "") != (apres.get(champ) or "")
        }
        self.assertTrue(ecrits, "aucune ecriture mesuree: l'instrument ne mesure rien")
        declarees = set(CHAMPS_EXEMPTES) | set(
            champs_du_verdict_sur_le_contenu(DEFAULT_DOCUMENT_FIELDS)
        )
        self.assertEqual(
            ecrits - declarees,
            set(),
            "champ(s) ecrits par classify sans nature declaree: "
            + ", ".join(sorted(ecrits - declarees)),
        )

    def test_la_garde_de_syntaxe_reste_en_second_temoin(self) -> None:
        # Le lecteur d'arbre syntaxique n'est pas jete: il attrape un champ
        # ecrit sur une branche qu'aucune course d'essai ne parcourt. Il est
        # garde comme SECOND temoin, avec sa portee dite: il ne voit que
        # `row["litteral"] = ...`, il ne voit ni `update`, ni cle variable, ni
        # helper. RESIDU NOMME: un champ ecrit a la fois par un helper ET sur
        # une branche non parcourue echappe encore aux deux temoins.
        arbre = ast.parse(CLASSIFICATION_SOURCE.read_text(encoding="utf-8"))
        fonctions = [
            noeud
            for noeud in ast.walk(arbre)
            if isinstance(noeud, ast.FunctionDef) and noeud.name == "classify"
        ]
        self.assertEqual(len(fonctions), 1, "classify introuvable ou defini deux fois")
        champs: set[str] = set()
        for noeud in ast.walk(fonctions[0]):
            cibles = []
            if isinstance(noeud, ast.Assign):
                cibles = list(noeud.targets)
            elif isinstance(noeud, (ast.AugAssign, ast.AnnAssign)):
                cibles = [noeud.target]
            for cible in cibles:
                if (
                    isinstance(cible, ast.Subscript)
                    and isinstance(cible.value, ast.Name)
                    and cible.value.id == "row"
                    and isinstance(cible.slice, ast.Constant)
                    and isinstance(cible.slice.value, str)
                ):
                    champs.add(cible.slice.value)
        self.assertTrue(champs, "aucune ecriture row[...] lue: le second temoin est casse")
        declarees = set(CHAMPS_EXEMPTES) | set(
            champs_du_verdict_sur_le_contenu(DEFAULT_DOCUMENT_FIELDS)
        )
        self.assertEqual(
            champs - declarees,
            set(),
            "champ(s) sans nature declaree: " + ", ".join(sorted(champs - declarees)),
        )


if __name__ == "__main__":
    unittest.main()
