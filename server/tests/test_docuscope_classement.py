"""Ce sur quoi un type de document repose.

Les mesures citees viennent des deux cabinets: 3447 lignes de registre pour le
premier, 22 pieces pour le second.

Deux natures de test cohabitent ici, et les confondre serait mentir au
coordinateur qui s'appuie sur ce fichier sans le relire. Une version anterieure
de ce docstring affirmait que TOUS les tests echouaient sur le code d'avant:
c'etait faux pour trois d'entre eux, et la phrase a ete corrigee ici.

Chaque test est probant contre sa propre reference, qui n'est pas la meme pour
tous: les tests du classement initial se mesurent au classifieur d'avant ce
lot; ceux de l'arbitrage de titre se mesurent a la premiere version de cet
arbitrage, celle qui promouvait sans regarder les preuves concurrentes.

Ne sont probants contre AUCUNE reference, et l'annoncent chacun dans leur
propre commentaire:

- `test_le_mot_reste_entier`, `test_le_doute_de_titre_reste_un_doute` et
  `test_la_taxonomie_reste_lisible_en_json`: garde-fous de non-regression, ils
  passaient deja avant le lot (rejeu verifie);
- `test_le_titre_decide_encore_quand_rien_dautre_ne_nomme_la_piece`: garde-fou
  du correctif d'arbitrage, il tient que refuser une promotion en conflit n'a
  pas supprime la promotion elle-meme;
- `ScoreDuTypeRetenuTests` et
  `test_tout_champ_de_regle_est_un_champ_que_le_produit_lit`: ils fixent le
  contrat de code neuf. Un test ne discrimine rien contre un code qui ne
  contient pas encore ce qu'il appelle.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import (
    DEFAULT_DOCUMENT_FIELDS,
    RunContext,
    load_instance,
    load_structured_file,
    read_csv,
    write_csv,
)
from coproscope.modules.docuscope import (
    CHAMPS_REGLE_DOCUMENTAIRES,
    CLASSIFICATION_DOUBT_STATUS,
    CLASSIFICATION_NO_TEXT_STATUS,
    _classify,
    _keyword_matches,
    _type_score,
    classify,
    title_signature_matches,
)

EXAMPLE_INSTANCE = Path(__file__).resolve().parents[2] / "examples" / "synthetic_copro"
TAXONOMY = Path(__file__).resolve().parents[2] / "server" / "src" / "coproscope" / "configs" / "taxonomy.default.yml"
TITRES = {"PV_AG": r"proces verbal de l assemblee"}


def corps(longueur: int) -> str:
    """Matiere de remplissage, sans mot-cle d'aucun type."""
    motif = "la residence entretient ses espaces verts et sa cage d escalier "
    return (motif * (longueur // len(motif) + 1))[:longueur]


class AccentsTests(unittest.TestCase):
    """Deux orthographes du meme mot francais sont le meme mot."""

    def test_la_locution_qui_nomme_le_document_est_reconnue_accentuee(self) -> None:
        # Mesure: 1595 des 2533 textes lisibles du premier cabinet portent au
        # moins un accent. Les locutions les plus discriminantes en portent
        # toutes: ce sont donc elles qui etaient jetees.
        cas = [
            ("assemblee generale", "Assemblée Générale ordinaire"),
            ("reglement de copropriete", "Règlement de copropriété du 12 mai"),
            ("proces-verbal", "Procès-verbal de seance"),
            ("resolution adoptee", "La résolution adoptée porte le numero 12"),
            ("etat des depenses", "État des dépenses de l exercice"),
        ]
        for mot_cle, texte in cas:
            with self.subTest(mot_cle=mot_cle):
                self.assertTrue(_keyword_matches(texte, mot_cle))

    def test_un_mot_cle_accentu_reconnait_un_texte_sans_accent(self) -> None:
        self.assertTrue(_keyword_matches("proces verbal de seance", "procès-verbal"))

    def test_le_mot_reste_entier(self) -> None:
        # GARDE-FOU DE NON-REGRESSION: passe deja avant le lot, verifie par
        # rejeu sur le classifieur d'origine. Il n'atteste d'aucune correction:
        # il existe pour que la neutralisation des accents n'elargisse jamais
        # le mot. `avoir` ne doit pas se declencher sur `pouvoirs`.
        self.assertFalse(_keyword_matches("les pouvoirs du syndic", "avoir"))


class PreuveDeContenuTests(unittest.TestCase):
    """Un mot-cle est une preuve de contenu, pas un segment de chemin."""

    REGLE = {"lot": "L", "type_document": "T", "mots_cles": ["releve bancaire"]}

    def test_un_mot_cle_present_dans_le_nom_ne_vaut_pas_lecture(self) -> None:
        # Mesure: 227 lignes du registre canonique vivent sous les dossiers de
        # travail de l'audit, et 198 portent un type documentaire affirme. Une
        # grille de controle nommee d'apres un type devenait ce type.
        lot, type_doc, score, _ = _classify(
            "", "grille_releve_bancaire.csv", "audit/grilles/grille_releve_bancaire.csv", [self.REGLE]
        )
        self.assertEqual(type_doc, "A_CLASSER")
        self.assertEqual(score, 0)

    def test_un_mot_cle_present_dans_le_contenu_vaut_lecture(self) -> None:
        _, type_doc, score, _ = _classify(
            "releve bancaire du compte separe", "piece.pdf", "recu/piece.pdf", [self.REGLE]
        )
        self.assertEqual(type_doc, "T")
        self.assertEqual(score, 5)

    def test_le_nom_de_fichier_garde_son_propre_motif(self) -> None:
        regle = dict(self.REGLE, motifs_nom_fichier=["releve.*bancaire"])
        _, type_doc, score, _ = _classify("", "releve_bancaire_2024.pdf", "recu/x.pdf", [regle])
        self.assertEqual(type_doc, "T")
        self.assertEqual(score, 50)


class EgaliteTests(unittest.TestCase):
    """Une egalite au sommet est un arbitrage sans preuve: elle se dit."""

    def test_les_types_ex_aequo_sont_rendus(self) -> None:
        # Mesure sur le second cabinet: quatre paquets comptables de meme forme
        # se coupent en deux types selon un mot present ou absent, l'egalite
        # etant tranchee par la position de la regle dans la configuration.
        regles = [
            {"lot": "L1", "type_document": "PREMIER", "mots_cles": ["etat financier"]},
            {"lot": "L2", "type_document": "SECOND", "mots_cles": ["conseil syndical"]},
        ]
        _, type_doc, _, ex_aequo = _classify("etat financier vu par le conseil syndical", "x.pdf", "x.pdf", regles)
        self.assertEqual(type_doc, "PREMIER")
        self.assertEqual(sorted(ex_aequo), ["PREMIER", "SECOND"])

    def test_un_vainqueur_net_na_pas_dex_aequo(self) -> None:
        regles = [
            {"lot": "L1", "type_document": "PREMIER", "mots_cles": ["etat financier"], "poids_mot_cle": 9},
            {"lot": "L2", "type_document": "SECOND", "mots_cles": ["conseil syndical"]},
        ]
        _, type_doc, _, ex_aequo = _classify("etat financier vu par le conseil syndical", "x.pdf", "x.pdf", regles)
        self.assertEqual(ex_aequo, ["PREMIER"])


class ScoreDuTypeRetenuTests(unittest.TestCase):
    """Un score repond du type affiche, ou il ne repond de rien.

    CONTRAT DE CODE NEUF: `_type_score` n'existait pas avant ce correctif, donc
    ces deux tests ne discriminent aucun code anterieur. Ils fixent ce que le
    helper doit rendre, pour que le recalcul de score ne reparte pas a la
    derive.
    """

    REGLES = [
        {"lot": "L1", "type_document": "ECARTE", "motifs_nom_fichier": ["dossier"],
         "poids_nom_fichier": 50},
        {"lot": "L2", "type_document": "RETENU", "mots_cles": ["etat financier"],
         "poids_mot_cle": 7},
    ]

    def test_le_score_dun_type_ne_compte_que_ses_propres_preuves(self) -> None:
        # Lors d'une promotion par titre, le score conservait celui du type
        # ecarte: une ligne devenue PV_AG portait un score bati sur les preuves
        # de Convocation_AG. Le score se recalcule donc pour le type retenu.
        self.assertEqual(
            _type_score(self.REGLES, "RETENU", "etat financier", "dossier.pdf", "x/dossier.pdf"),
            7,
        )
        self.assertEqual(
            _type_score(self.REGLES, "ECARTE", "etat financier", "dossier.pdf", "x/dossier.pdf"),
            50,
        )

    def test_un_type_sans_preuve_propre_ne_marque_rien(self) -> None:
        self.assertEqual(_type_score(self.REGLES, "RETENU", "", "dossier.pdf", ""), 0)


class SignatureDeTitreTests(unittest.TestCase):
    """Le titre lu en tete nomme le document: il decide."""

    def test_les_titres_lus_en_tete_sont_rendus_sans_connaitre_le_type(self) -> None:
        texte = "PROCES-VERBAL DE L ASSEMBLEE GENERALE ORDINAIRE " + corps(3000)
        titres, utile = title_signature_matches(texte, TITRES, 300, 200)
        self.assertEqual(titres, ["PV_AG"])
        self.assertTrue(utile)

    def test_un_texte_utile_vide_se_distingue_dun_texte_court(self) -> None:
        vide, _ = title_signature_matches("===== PAGE 1 =====\npage 1 sur 4", TITRES, 300, 200)
        court, utile_court = title_signature_matches(corps(60), TITRES, 300, 200)
        self.assertEqual(vide, [])
        self.assertEqual(court, [])
        self.assertEqual(title_signature_matches("page 1 page 2", TITRES, 300, 200)[1], "")
        self.assertTrue(utile_court)


class ClassementSurInstanceTests(unittest.TestCase):
    """Les memes faits, vus a travers classify() sur une instance reelle."""

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
            ligne = {champ: "" for champ in DEFAULT_DOCUMENT_FIELDS}
            ligne.update(
                {
                    "doc_id": doc_id,
                    "instance_id": self.instance.instance_id,
                    "file_name": nom,
                    "original_path": "raw/" + nom,
                }
            )
            if texte is not None:
                (text_dir / (doc_id + ".txt")).write_text(texte, encoding="utf-8")
                ligne["text_path"] = "staging/text/" + doc_id + ".txt"
            lignes.append(ligne)
        write_csv(self.instance.register("documents"), list(DEFAULT_DOCUMENT_FIELDS), lignes)

    def _lignes(self) -> dict[str, dict[str, str]]:
        classify(self.instance, RunContext(self.instance, "test-classement"), copy_files=False)
        _, lignes = read_csv(self.instance.register("documents"))
        return {ligne["doc_id"]: ligne for ligne in lignes}

    def test_un_titre_ne_retype_pas_ce_que_le_nom_du_fichier_nomme_autrement(self) -> None:
        # REGRESSION corrigee. Une convocation dont l'ordre du jour porte
        # "approbation du proces-verbal de l assemblee generale precedente"
        # etait retypee en proces-verbal, en silence. Mesure: le titre tombe en
        # position 252 pour une fenetre de tete de 300, calibree pour un role
        # de garde et non d'arbitre. Le nom du fichier nomme, lui aussi: les
        # deux denominations se contredisent, aucune ne tranche seule.
        texte = (
            "CONVOCATION A L ASSEMBLEE GENERALE ORDINAIRE des coproprietaires "
            "de la residence, qui se tiendra le 12 juin a 18 heures dans la "
            "salle commune du batiment A, sur premiere convocation. "
            + corps(40)
            + " ORDRE DU JOUR : 1. approbation du proces-verbal de l assemblee "
            "generale precedente. " + corps(3000)
        )
        ligne = self._lignes_pour("DOC-CONV", "convocation_ag_2025.pdf", texte)
        self.assertEqual(ligne["document_type"], "Convocation_AG")

    def test_un_fragment_de_page_de_convocation_reste_une_convocation(self) -> None:
        # REGRESSION corrigee, forme dominante du corpus: 69,3 % des lignes du
        # registre sont des fragments de pages issus du traitement. Une page
        # qui commence directement a l'ordre du jour n'a pas de preambule, donc
        # le titre du proces-verbal cite y tombe en tete.
        texte = (
            "ORDRE DU JOUR : 1. approbation du proces-verbal de l assemblee "
            "generale precedente. " + corps(3000)
        )
        ligne = self._lignes_pour("DOC-FRAG", "convocation_ag_2025_page2.pdf", texte)
        self.assertEqual(ligne["document_type"], "Convocation_AG")

    def test_le_conflit_de_denomination_est_ecrit_et_devient_un_doute(self) -> None:
        # Le silence est le defaut a ne pas refaire: la version fautive ecrivait
        # une note qui presentait l'erreur comme une correction, avec le statut
        # affirme AUTO_CLASSIFIED. Le desacord se nomme, et il se paie d'un
        # doute au lieu d'une affirmation.
        #
        # CONTREDIT ET CORRIGE le 2026-09-09, RM-2026-0052 defaut (1). La
        # matiere precedente etait `ORDRE DU JOUR : 1. approbation du
        # proces-verbal de l assemblee generale precedente.`, et l'assertion
        # etait `assertEqual(ligne["classification_status"],
        # CLASSIFICATION_DOUBT_STATUS)`. Cette matiere ne porte AUCUN conflit:
        # la locution y est gouvernee par `approbation du`, donc elle designe
        # une autre piece et ne nomme pas celle-ci. Le doute que l'ancienne
        # version relevait etait fabrique par la regle, pas par le document -
        # et il payait un fragment de convocation correctement type. La
        # propriete gardee reste la meme: quand deux DENOMINATIONS se
        # contredisent vraiment, le desaccord s'ecrit et coute un doute. La
        # matiere devient un vrai conflit: un titre qui ouvre son enonce face a
        # un nom de fichier qui dit autre chose.
        texte = (
            "PROCES-VERBAL DE L ASSEMBLEE GENERALE ORDINAIRE\n"
            "Premiere resolution: approbation des comptes. " + corps(3000)
        )
        ligne = self._lignes_pour("DOC-FRAG2", "convocation_ag_2025_page2.pdf", texte)
        self.assertEqual(ligne["classification_status"], CLASSIFICATION_DOUBT_STATUS)
        self.assertIn("denominations en conflit", ligne["notes"])
        self.assertIn("PV_AG", ligne["notes"])
        self.assertIn("Convocation_AG", ligne["notes"])

    def test_un_fragment_qui_cite_le_pv_ne_fabrique_plus_de_conflit(self) -> None:
        # Contrepartie du test ci-dessus, et c'est elle qui prouve que le
        # doute n'est plus fabrique: meme fichier, meme type retenu, mais la
        # locution y est une mention. Aucun conflit, donc aucun doute a payer.
        texte = (
            "ORDRE DU JOUR : 1. approbation du proces-verbal de l assemblee "
            "generale precedente. " + corps(3000)
        )
        ligne = self._lignes_pour("DOC-FRAG3", "convocation_ag_2025_page2.pdf", texte)
        self.assertEqual(ligne["document_type"], "Convocation_AG")
        self.assertNotIn("denominations en conflit", ligne["notes"])

    def test_un_texte_trop_court_pour_juger_ne_vaut_pas_un_type_affirme(self) -> None:
        # C050/C086, seconde moitie. Seul un texte utile STRICTEMENT vide
        # donnait TEXTE_INSUFFISANT. Un texte utile non vide mais sous le
        # plancher de 200 caracteres - trop court pour juger quoi que ce soit -
        # restait affirme en silence, et n'etait rattrape que si le type retenu
        # portait une signature de titre, c'est-a-dire PV_AG seul.
        ligne = self._lignes_pour("DOC-COURT", "facture_2024.pdf", corps(110))
        self.assertEqual(ligne["document_type"], "Facture")
        self.assertEqual(ligne["classification_status"], CLASSIFICATION_NO_TEXT_STATUS)

    def test_le_texte_trop_court_dit_sa_longueur_et_son_plancher(self) -> None:
        # Une valeur inattendue devient un fait nomme: le lecteur doit pouvoir
        # savoir de combien on a manque, sans rouvrir la piece.
        ligne = self._lignes_pour("DOC-COURT2", "facture_2024.pdf", corps(110))
        self.assertIn("110 caracteres", ligne["notes"])
        self.assertIn("plancher 200", ligne["notes"])

    def test_un_texte_court_mais_reellement_lu_reste_un_type_affirme(self) -> None:
        # GARDE-FOU: la longueur seule ne dit pas si une piece a ete lue.
        # Mesure: cette trace de courriel compte 150 caracteres utiles, sous le
        # plancher de 200, et declenche pourtant deux mots-cles de son propre
        # type. Son type repose sur une lecture; la marquer TEXTE_INSUFFISANT
        # serait affirmer une chose fausse. Une premiere version de ce
        # correctif le faisait, et cassait test_docops_completeness.
        texte = (
            "Sujet: pieces de copropriete\n"
            "Email recu du syndic concernant les pieces attendues.\n"
            "Le conseil syndical conserve cette trace locale comme preuve de suivi."
        )
        ligne = self._lignes_pour("DOC-MAIL", "2026-05-13_echange_syndic.txt", texte)
        self.assertEqual(ligne["document_type"], "Communication")
        self.assertEqual(ligne["classification_status"], "AUTO_CLASSIFIED")

    def test_le_titre_decide_encore_quand_rien_dautre_ne_nomme_la_piece(self) -> None:
        # GARDE-FOU DE NON-REGRESSION du correctif ci-dessus: refuser la
        # promotion en cas de conflit ne doit pas supprimer la promotion.
        # Quand le nom du fichier ne designe aucun type, le titre reste seul a
        # nommer la piece, et il decide.
        texte = (
            "PROCES-VERBAL DE L ASSEMBLEE GENERALE de la residence "
            + corps(200) + " " + corps(3000)
        )
        ligne = self._lignes_pour("DOC-SEUL", "divers_document.pdf", texte)
        self.assertEqual(ligne["document_type"], "PV_AG")
        self.assertEqual(ligne["classification_status"], "AUTO_CLASSIFIED")

    def test_le_titre_corrige_le_type_au_lieu_den_douter(self) -> None:
        # Cas mesure: une piece dont le nom ne porte aucun indice de type et
        # dont le texte commence au caractere 0 par le titre du proces-verbal
        # etait etiquetee Convocation_AG, donc jamais examinee par le seul
        # controle de forme du produit.
        texte = (
            "PROCES-VERBAL DE L ASSEMBLEE GENERALE de la residence "
            + corps(200)
            + " convocation ordre du jour "
            + corps(3000)
        )
        ligne = self._lignes_pour("DOC-PV", "divers_document.pdf", texte)
        self.assertEqual(ligne["document_type"], "PV_AG")
        self.assertIn("Titre PV_AG lu en tete", ligne["notes"])

    def _lignes_pour(self, doc_id: str, nom: str, texte) -> dict[str, str]:
        self._ecrire([(doc_id, nom, texte)])
        return self._lignes()[doc_id]

    def test_un_type_affirme_sans_aucun_texte_lu_le_dit(self) -> None:
        # Mesure: 80 lignes du registre canonique portent un type affirme
        # AUTO_CLASSIFIED sans qu'aucun caractere de texte n'ait ete lu, et le
        # statut TEXTE_INSUFFISANT est emis 0 fois sur 3447 lignes.
        ligne = self._lignes_pour("DOC-SCAN", "facture_2024.pdf", "===== PAGE 1 =====\npage 1 sur 3")
        self.assertEqual(ligne["document_type"], "Facture")
        self.assertEqual(ligne["classification_status"], CLASSIFICATION_NO_TEXT_STATUS)
        self.assertIn("aucune lecture du contenu", ligne["notes"])

    def test_un_proces_verbal_illisible_nest_pas_une_ligne_a_classer_de_plus(self) -> None:
        # Cas mesure sur le second cabinet: un proces-verbal d'un exercice sur
        # quatre sort en A_CLASSER, score 0, sans un mot sur l'extraction vide.
        ligne = self._lignes_pour("DOC-PV-VIDE", "2025-06-30_ag_pv.pdf", "===== PAGE 2 =====")
        self.assertEqual(ligne["classification_status"], CLASSIFICATION_NO_TEXT_STATUS)
        self.assertIn("Aucun texte utile", ligne["notes"])

    def test_un_document_sans_texte_extrait_du_tout(self) -> None:
        ligne = self._lignes_pour("DOC-IMG", "convocation_page1.png", None)
        self.assertEqual(ligne["classification_status"], CLASSIFICATION_NO_TEXT_STATUS)

    def test_le_doute_de_titre_reste_un_doute(self) -> None:
        # GARDE-FOU DE NON-REGRESSION: l'ancien classifieur rendait deja
        # PV_AG / A_RECLASSER sur cette piece, verifie par rejeu. Le test ne
        # prouve aucune correction; il tient que le doute de titre n'a pas ete
        # avale par les regles de promotion ajoutees depuis.
        ligne = self._lignes_pour("DOC-TRAVAIL", "pv_ag_journal.md", "# Journal des decisions\n" + corps(2000))
        self.assertEqual(ligne["document_type"], "PV_AG")
        self.assertEqual(ligne["classification_status"], CLASSIFICATION_DOUBT_STATUS)

    def test_legalite_de_score_est_ecrite_dans_le_registre(self) -> None:
        # FIXTURE REFAITE A L'INTEGRATION. L'ancienne reposait sur une egalite
        # que le defaut des priorites fabriquait: la taxonomie ecrit `priorite`
        # trente-neuf fois quand le bareme lisait `priority`, donc les trente-neuf
        # priorites valaient zero et beaucoup de types se retrouvaient a egalite
        # par accident. La cle etant corrigee, ces egalites-la ont disparu -
        # c'est le but - et le test mesurait donc le defaut plutot que le
        # mecanisme.
        # La nouvelle fixture vise la seule egalite qui subsiste par calcul sur
        # la taxonomie livree: Ordre_Service (priorite 50 + deux mots-cles a 5)
        # et Contentieux_Nominatif (priorite 40 + quatre mots-cles a 5) plafonnent
        # tous deux a 60. Un texte qui porte les six mots-cles met donc les deux
        # types a egalite reelle, priorites comprises.
        texte = (
            "ordre de service pour le demarrage des travaux, transmis a l avocat "
            "au titre du contentieux, apres mise en demeure et assignation. "
            + corps(2000)
        )
        ligne = self._lignes_pour("DOC-EGAL", "piece_melangee.pdf", texte)
        self.assertIn("Egalite de score entre", ligne["notes"])
        self.assertIn("pas par une preuve", ligne["notes"])


class MotifsQuiNommentLInstrumentTests(unittest.TestCase):
    """Un motif ne vaut preuve que s'il nomme l'instrument, pas son voisin."""

    def setUp(self) -> None:
        self.taxonomie = load_structured_file(TAXONOMY)
        self.regles = {
            str(regle.get("type_document", regle.get("document_type", ""))): regle
            for regle in self.taxonomie.get("regles", self.taxonomie.get("rules", []))
        }

    def _motifs(self, type_document: str) -> list[str]:
        regle = self.regles[type_document]
        return [str(v) for v in regle.get("motifs_nom_fichier", regle.get("filename_patterns", []))]

    def _mots(self, type_document: str) -> list[str]:
        regle = self.regles[type_document]
        return [str(v) for v in regle.get("mots_cles", regle.get("keywords", []))]

    def test_pouvoirs_ne_nomme_pas_la_feuille_de_presence(self) -> None:
        # Mesure: 51 lignes sur 51 typees Feuille_Presence_AG, declenchees par
        # le seul mot `pouvoirs`, et aucune n'est une feuille de presence. La
        # loi 65-557 emploie ce mot pour les pouvoirs du syndic (art. 18); le
        # mandat de l'art. 22 est un autre instrument.
        self.assertNotIn("pouvoirs", self._motifs("Feuille_Presence_AG"))
        self.assertNotIn("pouvoirs", self._mots("Feuille_Presence_AG"))
        self.assertIn("feuille de presence", self._mots("Feuille_Presence_AG"))

    def test_un_identifiant_de_compte_ne_releve_aucune_operation(self) -> None:
        # Mesure: 5 lignes sur 5 typees Releve_Bancaire sont fausses; la carte
        # professionnelle du syndic y entre par `compte bancaire`.
        for motif in ("rib", "banque"):
            self.assertNotIn(motif, self._motifs("Releve_Bancaire"))
        for mot in ("iban", "compte bancaire"):
            self.assertNotIn(mot, self._mots("Releve_Bancaire"))

    def test_annexe_nu_ne_nomme_ni_lannexe_comptable_ni_celle_de_la_convocation(self) -> None:
        # Mesure: 52 des 58 Annexe_Comptable sont declenchees par le seul motif
        # `annexe`, et Annexe_AG ne compte qu'une ligne, qui est un fichier de
        # travail.
        self.assertNotIn("annexe", self._motifs("Annexe_Comptable"))
        self.assertIn("annexe.*comptable", self._motifs("Annexe_Comptable"))

    def test_le_nom_de_lorgane_ne_nomme_aucun_instrument(self) -> None:
        # `assemblee generale` se declenche aussi bien sur une convocation que
        # sur un proces-verbal: il ne separe rien et vaut le meme poids que la
        # locution qui, elle, nomme la piece.
        self.assertNotIn("assemblee generale", self._mots("Convocation_AG"))
        self.assertNotIn("assemblee generale", self._mots("PV_AG"))

    def test_chaque_motif_retire_laisse_son_fondement(self) -> None:
        for type_document in ("Feuille_Presence_AG", "Releve_Bancaire", "Annexe_Comptable", "Convocation_AG", "PV_AG"):
            with self.subTest(type_document=type_document):
                self.assertTrue(str(self.regles[type_document].get("fondement", "")).strip())

    def test_la_taxonomie_reste_lisible_en_json(self) -> None:
        # GARDE-FOU DE NON-REGRESSION: l'ancien fichier etait deja du JSON
        # valide, verifie. Il tient la forme du fichier au fil des retraits de
        # motifs, pas une correction.
        json.loads(TAXONOMY.read_text(encoding="utf-8"))

    def test_tout_champ_de_regle_est_un_champ_que_le_produit_lit(self) -> None:
        # CONTRAT DE CODE NEUF: ne discrimine aucun code anterieur, puisque
        # `CHAMPS_REGLE_DOCUMENTAIRES` n'existait pas. Il tient la declaration.
        #
        # `fondement` a ete ajoute sur 5 regles pour porter la regle de droit
        # qui justifie un motif retire. Un champ que personne ne declare est un
        # reglage qui n'en est pas un: il se lit comme un reglage, il ne fait
        # rien, et une garde a liste fermee le refuse au chargement. Le champ
        # est donc declare, et ce test tient la declaration a jour.
        connus = CHAMPS_REGLE_DOCUMENTAIRES | {
            "lot", "document_type", "type_document", "priority", "priorite",
            "filename_patterns", "motifs_nom_fichier", "path_patterns",
            "motifs_chemin", "keywords", "mots_cles", "filename_weight",
            "poids_nom_fichier", "path_weight", "poids_chemin",
            "keyword_weight", "poids_mot_cle",
        }
        for type_document, regle in self.regles.items():
            with self.subTest(type_document=type_document):
                self.assertEqual(set(regle) - connus, set())


if __name__ == "__main__":
    unittest.main()
