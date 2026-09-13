"""Lecture d'une convocation: extraction pure et controles.

Le texte de reference est fictif mais reproduit les formes reellement
rencontrees: sous-numerotation des devis concurrents, formule de style affirmant
l'avis du conseil syndical, prix a l'unite sans total, preambule declarant une
contestation partielle et un rejeu total, et deux conventions decimales dans le
meme document.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.modules import convocation
from coproscope.modules import _convocation_registre as registre
from coproscope.modules._convocation_extraction import _montant

ORDRE_DU_JOUR = """
ORDRE DU JOUR
1- Election du President de seance.
2- Election du secretaire de seance.
3- Approbation des comptes de gestion 2024 ci-annexes.
4- Vote du budget previsionnel 2025.
5- VOTE DES TRAVAUX DE RAVALEMENT DU BLOC 1.
5.1- BLOC 1 : choix du devis de ravalement TOITURA pour 120.500,00 EUR TTC.
5.2- BLOC 1 : choix du devis de ravalement MUREXO pour 118.250,40 EUR TTC.
6- VOTE DU REMPLACEMENT DES VOLETS.
6.1- BLOC 1 : choix du devis de remplacement des volets TOITURA.
"""

PROJETS = """
PREAMBULE : DANS LE CADRE DE LA PROCEDURE ENTAMEE PAR UN COPROPRIETAIRE EN NULITE DES
QUESTIONS N°3, 5-2 et 6-1 DE LA DERNIERE ASSEMBLEE DU 03/12/2025 NOUS VOUS CONVOQUONS
POUR CETTE ASSEMBLEE EXTRAORDINAIRE AFIN DE FAIRE RE-VOTER TOUTES LES QUESTIONS DE
L'ORDRE DU JOUR ET PERMETTRE AINSI AUX COPROPRIETAIRES DE CONFIRMER LEURS CHOIX.
Article 24
L'Assemblee Generale approuve les comptes de charges dont le montant annuel des depenses
s'eleve a 290 117.06 EUR pour les depenses courantes (total de l'annexe 3) et en charges
travaux 55 955.07 EUR pour les depenses hors budget (total de l'annexe 4)
3- Approbation des comptes de gestion 2024 ci-annexes.
Article 24
L'assemblee generale, apres avoir pris connaissance des conditions essentielles des devis
et du rapport d'analyse des offres, pris connaissance de l'avis du conseil syndical et
apres en avoir delibere, decide d'effectuer les travaux suivants :
Retient la proposition presentee : par l'entreprise TOITURA pour 120.500,00 EUR TTC.
Les travaux seront repartis selon la cle B01 du Syndic; soit sur 1135 tantiemes.
5.1- BLOC 1 : choix du devis de ravalement TOITURA pour 120.500,00 EUR TTC.
Article 25
L'assemblee generale, apres avoir pris connaissance des conditions essentielles des devis
et du rapport d'analyse des offres, pris connaissance de l'avis du conseil syndical et
apres en avoir delibere, decide d'effectuer les travaux suivants :
Retient la proposition presentee : par l'entreprise MUREXO pour 118.250,40 EUR TTC.
Les travaux seront repartis selon la cle B01 du Syndic; soit sur 1135 tantiemes.
5.2- BLOC 1 : choix du devis de ravalement MUREXO pour 118.250,40 EUR TTC.
Article 25
L'assemblee generale, apres avoir pris connaissance des conditions essentielles des devis
et du rapport d'analyse des offres, pris connaissance de l'avis du conseil syndical et
apres en avoir delibere, decide d'effectuer les travaux suivants :
volet dimension h 1,40 X l 1,30 : 1.700 EUR TTC l'unite
Retient la proposition presentee : par l'entreprise TOITURA.
Les travaux seront repartis selon la cle B01 du Syndic; soit sur 1135 tantiemes.
6.1- BLOC 1 : choix du devis de remplacement des volets TOITURA.
Article 25
"""

PAGES = ["Lettre de convocation. Ordre du jour ci-apres.", ORDRE_DU_JOUR, PROJETS]


class MontantTests(unittest.TestCase):
    def test_accepte_les_deux_conventions_decimales(self) -> None:
        # Le meme document ecrit les deux; une regle fixe ferait de 290 117.06
        # un montant cent fois trop grand.
        self.assertEqual(_montant("120.500,00"), "120500.00")
        self.assertEqual(_montant("290 117.06"), "290117.06")
        self.assertEqual(_montant("55 955,07"), "55955.07")

    def test_sans_decimale_le_montant_reste_entier(self) -> None:
        self.assertEqual(_montant("1 200"), "1200")


class ExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.convocation = convocation.parse_convocation(PAGES, ag_date="2026-04-29")

    def test_compte_les_points_annonces_et_leurs_sous_points(self) -> None:
        self.assertEqual(self.convocation.points_ordre_du_jour, 6)
        self.assertEqual(self.convocation.sous_points_ordre_du_jour, 3)

    def test_ne_retient_que_les_pages_qui_enumerent(self) -> None:
        # La lettre de convocation cite l'ordre du jour sans l'enumerer.
        self.assertTrue(all(point.page >= 2 for point in self.convocation.points))

    def test_lit_un_devis_avec_son_prix_son_article_et_sa_cle(self) -> None:
        devis = {d.reference: d for d in self.convocation.devis}
        self.assertEqual(devis["5-1"].entreprise, "TOITURA")
        self.assertEqual(devis["5-1"].montant_ttc, "120500.00")
        self.assertEqual(devis["5-1"].etat_prix, convocation.PRIX_QUANTIFIE)
        self.assertEqual(devis["5-1"].majorite_annoncee, "25")
        self.assertEqual(devis["5-1"].cle_repartition, "B01")

    def test_un_devis_sans_prix_global_est_un_constat_pas_un_echec(self) -> None:
        devis = {d.reference: d for d in self.convocation.devis}
        self.assertEqual(devis["6-1"].entreprise, "TOITURA")
        self.assertEqual(devis["6-1"].montant_ttc, "")
        self.assertEqual(devis["6-1"].etat_prix, convocation.PRIX_NON_QUANTIFIE)

    def test_enregistre_les_affirmations_du_syndic_sans_les_prendre_pour_preuve(self) -> None:
        for devis in self.convocation.devis:
            if devis.etat_prix != convocation.PRIX_NON_LU:
                self.assertTrue(devis.avis_cs_affirme)
                self.assertTrue(devis.analyse_offres_affirmee)

    def test_lit_les_totaux_que_la_resolution_attribue_aux_annexes(self) -> None:
        totaux = {t.annexe: t.montant for t in self.convocation.totaux_annonces}
        self.assertEqual(totaux[3], "290117.06")
        self.assertEqual(totaux[4], "55955.07")


class DeclarationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.declarations = convocation.declarations_sur_ag(PAGES)

    def test_contestation_et_rejeu_sont_deux_declarations_de_portees_differentes(self) -> None:
        natures = {d.nature: d for d in self.declarations}
        self.assertIn(convocation.NATURE_CONTESTATION, natures)
        self.assertIn(convocation.NATURE_REJEU, natures)
        self.assertEqual(natures[convocation.NATURE_CONTESTATION].portee, convocation.PORTEE_PARTIELLE)
        self.assertEqual(natures[convocation.NATURE_REJEU].portee, convocation.PORTEE_TOTALE)

    def test_la_contestation_nomme_ses_questions_sous_numeros_compris(self) -> None:
        contestation = next(
            d for d in self.declarations if d.nature == convocation.NATURE_CONTESTATION
        )
        self.assertEqual(set(contestation.questions_visees), {"3", "5-2", "6-1"})
        self.assertEqual(contestation.ag_visee, "2025-12-03")

    def test_le_rejeu_total_ne_nomme_aucune_question(self) -> None:
        # Rejouer tout l'ordre du jour n'est pas rejouer les questions attaquees:
        # confondre les deux ferait perdre la portee de chacune.
        rejeu = next(d for d in self.declarations if d.nature == convocation.NATURE_REJEU)
        self.assertEqual(rejeu.questions_visees, ())


class ControleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controles = convocation.controles(convocation.parse_convocation(PAGES))

    def test_l_enumeration_annoncee_sert_d_etalon_sans_reference_externe(self) -> None:
        enumeration = self.controles["enumeration"]
        self.assertEqual(enumeration["sous_points_annonces"], 3)
        self.assertEqual(enumeration["sous_points_lus"], 3)
        self.assertTrue(enumeration["complete"])

    def test_la_sequence_de_l_ordre_du_jour_est_continue(self) -> None:
        self.assertEqual(self.controles["sequence"]["trous"], [])

    def test_le_taux_de_quantification_distingue_les_trois_etats(self) -> None:
        quantification = self.controles["quantification"]
        self.assertEqual(quantification["devis_cites"], 3)
        self.assertEqual(quantification["quantifies"], 2)
        self.assertEqual(quantification["non_quantifies"], 1)
        self.assertEqual(quantification["non_lus"], 0)

    def test_les_affirmations_sont_comptees_et_aucune_piece_n_est_produite(self) -> None:
        affirmations = self.controles["affirmations"]
        self.assertEqual(affirmations["avis_cs_affirme"], affirmations["projets_lus"])
        self.assertEqual(affirmations["piece_produite"], 0)

    def test_les_references_a_suivre_sont_nommees(self) -> None:
        references = self.controles["references"]
        self.assertEqual(references["ag_visees"], ["2025-12-03"])
        self.assertEqual(set(references["questions_visees"]), {"3", "5-2", "6-1"})

    def test_sans_projets_le_controle_se_declare_ineffectif(self) -> None:
        # On retire la page des projets. L'ordre du jour porte les memes lignes
        # que les projets: sans frontiere, l'enumeration se compare a elle-meme
        # et rendrait "complete" quoi qu'il arrive. Le controle doit le dire.
        partielle = convocation.controles(convocation.parse_convocation(PAGES[:2]))
        self.assertFalse(partielle["enumeration"]["controle_effectif"])
        self.assertFalse(partielle["extraction_complete"])

    def test_le_controle_est_effectif_quand_les_projets_sont_delimites(self) -> None:
        self.assertTrue(self.controles["enumeration"]["controle_effectif"])


class ConfrontationTests(unittest.TestCase):
    """Le contenu est le temoin de l'identite, pas l'identite elle-meme."""

    def _ligne(self, cle: str, entreprise: str, montant: str, origine: str) -> dict[str, str]:
        return {
            "devis_cite_id": cle,
            "entreprise": entreprise,
            "montant_ttc": montant,
            "origine": origine,
        }

    def test_un_temoin_inchange_ne_produit_aucune_divergence(self) -> None:
        ancienne = [self._ligne("D1", "TOITURA", "120500.00", convocation.ORIGINE_EXTRAIT)]
        nouvelle = [self._ligne("D1", "TOITURA", "120500.00", convocation.ORIGINE_EXTRAIT)]
        _, divergences = convocation.confronter(
            ancienne, nouvelle, cle="devis_cite_id", temoin=("entreprise", "montant_ttc")
        )
        self.assertEqual(divergences, [])

    def test_un_temoin_qui_change_est_signale_et_non_repointe_en_silence(self) -> None:
        ancienne = [self._ligne("D1", "TOITURA", "120500.00", convocation.ORIGINE_EXTRAIT)]
        nouvelle = [self._ligne("D1", "MUREXO", "118250.40", convocation.ORIGINE_EXTRAIT)]
        _, divergences = convocation.confronter(
            ancienne, nouvelle, cle="devis_cite_id", temoin=("entreprise", "montant_ttc")
        )
        self.assertEqual(len(divergences), 1)
        self.assertIn("entreprise", divergences[0]["ecarts"])

    def test_une_correction_humaine_survit_a_la_re_extraction(self) -> None:
        # Decision back n.2 de la strategie: la re-extraction ecrit a cote et
        # signale, elle n'ecrase jamais.
        ancienne = [self._ligne("D1", "TOITURA SAS", "120500.00", convocation.ORIGINE_CORRIGE)]
        nouvelle = [self._ligne("D1", "TOITURA", "120500.00", convocation.ORIGINE_EXTRAIT)]
        ecrites, divergences = convocation.confronter(
            ancienne, nouvelle, cle="devis_cite_id", temoin=("entreprise", "montant_ttc")
        )
        self.assertEqual(ecrites[0]["entreprise"], "TOITURA SAS")
        self.assertEqual(ecrites[0]["origine"], convocation.ORIGINE_CORRIGE)
        self.assertEqual(len(divergences), 1)

    def test_un_objet_disparu_est_signale_plutot_que_supprime_en_silence(self) -> None:
        ancienne = [self._ligne("D1", "TOITURA", "120500.00", convocation.ORIGINE_EXTRAIT)]
        _, divergences = convocation.confronter(
            [*ancienne], [], cle="devis_cite_id", temoin=("entreprise", "montant_ttc")
        )
        self.assertEqual(len(divergences), 1)
        self.assertIn("absent", divergences[0]["ecarts"])


if __name__ == "__main__":
    unittest.main()


class NatureTests(unittest.TestCase):
    """Un proces-verbal ou une convocation: le decider en lisant, pas au nom.

    Le contre-exemple est reel: `2023-06-19_AG_PV_Convoc.pdf` porte `PV` dans
    son nom et ne rapporte aucun vote.
    """

    def test_un_document_qui_rapporte_des_votes_est_un_constat(self) -> None:
        pv = ["\n".join(
            f"{n}- Objet numero {n}\nEn consequence, cette resolution est adoptee.\n"
            f"ont vote pour: 8000/10.000"
            for n in range(1, 12)
        )]
        nature = convocation.nature_du_document(pv, convocation.calibrer(pv))
        self.assertEqual(nature.etat, convocation.ETAT_CONSTATEE)
        self.assertTrue(nature.porte_des_votes)

    def test_une_convocation_reste_un_projet(self) -> None:
        nature = convocation.nature_du_document(PAGES, convocation.calibrer(PAGES))
        self.assertNotEqual(nature.etat, convocation.ETAT_CONSTATEE)
        self.assertFalse(nature.porte_des_votes)

    def test_une_mention_isolee_de_vote_ne_fait_pas_un_proces_verbal(self) -> None:
        # Contre-exemple mesure: la convocation Tilleuls du 29/04/2026 porte
        # UNE formule de cloture dans 425 000 caracteres, perdue dans une annexe.
        # La presence seule la classait proces-verbal; la densite corrige.
        pages = [*PAGES, "Piece jointe: le rapport indique que la demande est approuvee."]
        nature = convocation.nature_du_document(pages, convocation.calibrer(pages))
        self.assertNotEqual(nature.etat, convocation.ETAT_CONSTATEE)

    def test_un_document_sans_couche_texte_est_illisible_pas_vide(self) -> None:
        nature = convocation.nature_du_document(["", "  ", "\n"])
        self.assertEqual(nature.etat, convocation.ETAT_ILLISIBLE)


class CalibrageTests(unittest.TestCase):
    """La convention de numerotation se mesure, elle ne se connait pas."""

    def test_trouve_le_separateur_du_document(self) -> None:
        signature = convocation.calibrer(PAGES)
        self.assertIsNotNone(signature)
        self.assertEqual(signature.suffixe, "-")

    def test_trouve_une_convention_a_prefixe_jamais_codee(self) -> None:
        # Aucun separateur n'est ecrit en dur pour cette forme: elle est
        # decouverte parce qu'elle est la plus reguliere du document.
        pages = ["\n".join(
            f"Resolution n°{n} : Objet numero {n} (Article 24)" for n in range(1, 15)
        )]
        signature = convocation.calibrer(pages)
        self.assertIsNotNone(signature)
        self.assertIn("resolution", signature.prefixe)
        self.assertGreaterEqual(signature.portee, 14)

    def test_une_liste_sans_majorite_perd_contre_l_ordre_du_jour(self) -> None:
        # Mesure sur Erables (pseudo) 2024: la liste des pieces jointes est plus
        # longue et plus reguliere que l'ordre du jour - 23 contre 19 - et
        # gagnerait sans l'ancrage metier.
        #
        # L'ecart reproduit ici est celui du corpus. Une liste DEUX FOIS plus
        # longue repasserait devant: c'est la limite connue, documentee dans
        # `_convocation_calibrage`, et la sortie propre est de restreindre la
        # collecte a la region de l'ordre du jour plutot que d'ajouter un poids.
        pages = ["\n".join(
            [f"{n}) Point numero {n}\nArticle 24" for n in range(1, 20)]
            + [f"Piece jointe n°{n} : document {n}" for n in range(1, 24)]
        )]
        signature = convocation.calibrer(pages)
        self.assertIsNotNone(signature)
        self.assertEqual(signature.prefixe, "")

    def test_un_document_sans_enumeration_ne_rend_aucune_signature(self) -> None:
        self.assertIsNone(convocation.calibrer(["Lettre de convocation sans liste."]))


class PagesDuDocumentTests(unittest.TestCase):
    """Le repli lit le referentiel, et le decoupe sur SES bornes."""

    def _instance(self, contenu: str):
        dossier = Path(tempfile.mkdtemp(prefix="conv_repli_"))
        self.addCleanup(shutil.rmtree, dossier, True)
        (dossier / "staging" / "text").mkdir(parents=True)
        (dossier / "staging" / "text" / "DOC-TEST.native.txt").write_text(
            contenu, encoding="utf-8"
        )

        class Instance:
            def root(self, nom: str) -> Path:
                return dossier

        return Instance()

    #: Le format exact que `_write_page_text` produit: un marqueur par page.
    REFERENTIEL = "\n".join(
        ligne
        for numero, corps in enumerate(
            ("Ordre du jour de l'assemblee.", "Resolution 1.", "Resolution 2."), start=1
        )
        for ligne in (f"===== PAGE {numero} =====", corps, "")
    )

    LIGNE = {"doc_id": "DOC-TEST", "text_path": "staging/text/DOC-TEST.native.txt"}

    def test_le_repli_rend_une_page_par_borne(self) -> None:
        """Il rendait UNE page quel que soit le document.

        Mesure du 2026-09-07 sur `tilleuls_20260906`: 57 des 121 documents
        candidats passent par ce repli, et les 57 rendaient une page unique
        alors qu'ils portent de 3 a 124 bornes. Apres correction, les 57
        retrouvent la pagination du registre.
        """
        instance = self._instance(self.REFERENTIEL)
        pages = convocation.pages_du_document(instance, dict(self.LIGNE))
        self.assertEqual(len(pages), 3)
        self.assertIn("Ordre du jour", pages[0])
        self.assertIn("Resolution 2.", pages[2])

    def test_le_repli_ne_laisse_aucun_marqueur_dans_le_texte(self) -> None:
        """Une page unique contenant tous les marqueurs, c'est du texte pollue.

        Mesure du 2026-09-07: 1524 marqueurs traversaient le repli et se
        retrouvaient dans le texte donne a l'extracteur. Apres correction: 0.
        """
        instance = self._instance(self.REFERENTIEL)
        pages = convocation.pages_du_document(instance, dict(self.LIGNE))
        self.assertNotIn("===== PAGE", "".join(pages))

    def test_le_saut_de_page_ne_decoupe_rien(self) -> None:
        r"""Le repli cherchait un `\f` que l'extraction n'ecrit jamais.

        Quand il s'en trouve un, il vient du contenu: quatre fichiers des 825
        du corpus en portent trois chacun, dont un document de 143 pages qu'un
        decoupage sur `\f` aurait reduit a 4.
        """
        avec_saut = (
            "===== PAGE 1 =====\nDebut\f suite de la page 1\n"
            "===== PAGE 2 =====\nPage deux, assez de texte pour passer le seuil.\n"
        )
        instance = self._instance(avec_saut)
        pages = convocation.pages_du_document(instance, dict(self.LIGNE))
        self.assertEqual(len(pages), 2)
        self.assertIn("suite de la page 1", pages[0])

    def test_un_referentiel_de_marqueurs_ne_rend_rien(self) -> None:
        """La densite se mesure sur le contenu, jamais sur les marqueurs.

        Le repli gardait `len(texte.strip()) < SEUIL_COUCHE_TEXTE`, qui compte
        les marqueurs. Mesure du 2026-09-07 sur `tilleuls_20260906`: les 57
        documents du repli rendent de 60 a 2741 caracteres au `strip()` et ZERO
        caractere de document. Ils franchissaient la garde, ressortaient
        `INDETERMINE` - ni ecartes ni signales - et etaient lus comme des
        convocations a zero devis. Le comptage `sans couche texte` passe de 27
        a 84 sur 121, ce qui est la verite mesurable.
        """
        marqueurs_seuls = "\n".join(f"===== PAGE {n} =====\n" for n in range(1, 28))
        self.assertGreater(len(marqueurs_seuls.strip()), registre.SEUIL_COUCHE_TEXTE)
        instance = self._instance(marqueurs_seuls)
        self.assertEqual(convocation.pages_du_document(instance, dict(self.LIGNE)), [])
