"""Le typage des resolutions, et ce qu'il retire aux controles.

Chaque test porte le nom de la promesse qu'il tient. La promesse centrale de ce
lot tient en une phrase: **un controle ne s'applique pas partout, et la ou il ne
s'applique pas, l'ecran doit dire pourquoi au lieu d'annoncer une piece
manquante.**

Le corpus reel n'est pas lu ici - il est prive. Les libelles ci-dessous
reproduisent les DEUX manieres d'ecrire relevees sur les deux cabinets, sans
aucun nom de personne, de societe ni de copropriete. C'est le point du lot: si
un test passait pour un seul des deux cabinets, le typage serait une modalite et
non un axe.
"""

from __future__ import annotations

import re
import shutil
import tempfile
import unittest

#: **Un identifiant Legifrance, et rien autour.** Les ancres ne sont pas un
#: detail: sans elles, `XXLEGIARTI999999999999YY` passe, et la garde cesse de
#: verifier une FORME pour ne verifier qu'une PRESENCE.
MOTIF_IDENTIFIANT = re.compile(r"^LEGIARTI\d{12}$")
from pathlib import Path

from coproscope.modules import actes_autorisation as A
from coproscope.modules import _actes_typologie as T
from coproscope.modules import _actes_vocabulaire as V
from coproscope.modules import _resolutions_qualification as Q

from tests.test_actes_autorisation import _Instance, _acte, _dossier

AG = "2024-07-03"


class TypologieSourceeTests(unittest.TestCase):
    """Aucun type n'existe sans l'article qui le fonde."""

    def test_chaque_portee_est_declaree_avec_son_fondement(self) -> None:
        self.assertEqual(set(V.PORTEES), set(T.FONDEMENT_PORTEE))

    def test_chaque_portee_cite_un_article_et_son_identifiant_legifrance(self) -> None:
        """Une regle de majorite ne se cite pas de memoire.

        `ORDINAIRE` est la seule exception, et c'est cohérent: elle ne dit pas
        ce qu'est la resolution, elle dit qu'on ne le sait pas.
        """
        for portee, (definition, sources) in T.FONDEMENT_PORTEE.items():
            self.assertTrue(definition.strip(), portee)
            if portee == V.PORTEE_ORDINAIRE:
                self.assertEqual(sources, ())
                continue
            self.assertTrue(sources, portee)
            for article, identifiant in sources:
                self.assertTrue(article.strip(), portee)
                self.assertRegex(identifiant, MOTIF_IDENTIFIANT, portee)

    def test_chaque_retrait_de_controle_porte_son_motif(self) -> None:
        """Retirer un constat sans dire pourquoi vaut l'afficher a tort.

        Dans les deux cas l'utilisateur ne peut pas prendre le controle en
        defaut, et c'est la seule chose que la file de travail doit permettre.
        """
        for portee, retraits in T.HORS_CONTROLE.items():
            self.assertIn(portee, V.PORTEES)
            for controle, motif in retraits.items():
                self.assertIn(controle, T.CONTROLES, f"{portee}/{controle}")
                self.assertGreater(len(motif.strip()), 30, f"{portee}/{controle}")

    def test_une_portee_hors_vocabulaire_garde_tous_ses_controles(self) -> None:
        """Le doute penche du cote du controle, jamais du classement sans suite.

        Les deux valeurs mesurees sont celles qui arrivent vraiment: la chaine
        vide, qu'`_actes_store._valider_vocabulaire` admet a l'ecriture parce
        qu'une colonne non renseignee est un fait et pas une faute, et une
        valeur ecrite de travers par une autre conversation.
        """
        for portee in ("", "PORTEE_INVENTEE"):
            for controle in T.CONTROLES:
                with self.subTest(portee=portee, controle=controle):
                    self.assertTrue(T.controle_applicable(portee, controle))
            self.assertEqual(T.motif_hors_controle(portee, T.CTRL_SEUIL), "")
            self.assertEqual(T.portees_retirees(T.CTRL_SEUIL).count(portee), 0)

    def test_la_portee_ordinaire_perd_le_rapport_du_conseil_syndical(self) -> None:
        """C064: le commentaire, le code et le test se contredisaient.

        Le commentaire de fin de `HORS_CONTROLE` annoncait qu'ORDINAIRE n'a
        aucune exclusion; la boucle placee juste apres lui ajoute
        `CTRL_RAPPORT_CS`, et le test cense garder l'invariant interrogeait
        'PORTEE_INVENTEE' - une valeur que le code n'ecrit jamais - au lieu du
        repli reellement ecrit. Mesure: `HORS_CONTROLE['ORDINAIRE']` vaut
        `{'RAPPORT_CS'}`.

        Le fond est defendable et reste inchange: le compte rendu annuel du
        conseil syndical est rattache a l'assemblee qui approuve les comptes
        et a la delegation qui en rend compte, pas a chaque resolution. Ce
        test dit ce qui est, pour que l'invariant reste verifiable le jour ou
        on voudra s'y fier.
        """
        self.assertEqual(
            set(T.HORS_CONTROLE.get(V.PORTEE_ORDINAIRE, {})), {T.CTRL_RAPPORT_CS}
        )
        self.assertFalse(
            T.controle_applicable(V.PORTEE_ORDINAIRE, T.CTRL_RAPPORT_CS)
        )
        self.assertIn(
            V.PORTEE_ORDINAIRE, T.portees_retirees(T.CTRL_RAPPORT_CS),
            "une portee DANS le vocabulaire peut perdre un controle; c'est la "
            "portee hors vocabulaire qui les garde tous.",
        )
        for controle in T.CONTROLES:
            if controle == T.CTRL_RAPPORT_CS:
                continue
            with self.subTest(controle=controle):
                self.assertTrue(
                    T.controle_applicable(V.PORTEE_ORDINAIRE, controle)
                )

    def test_seul_l_engagement_de_depense_porte_tous_les_controles_de_depense(self) -> None:
        """Le rapport du conseil syndical est mis a part, et c'est voulu.

        Il n'est exigible que de deux portees - les comptes et la delegation -
        donc il n'entre pas dans la question `qui subit tous les controles de
        depense`. Les six autres controles, eux, ne visent au complet que
        l'engagement de depense, et la portee non determinee qui les garde par
        prudence.
        """
        controles_depense = tuple(
            c for c in T.CONTROLES if c != T.CTRL_RAPPORT_CS
        )
        soumis = {
            portee for portee in V.PORTEES
            if all(T.controle_applicable(portee, c) for c in controles_depense)
        }
        self.assertEqual(soumis, {V.PORTEE_ENGAGEMENT_DEPENSE, V.PORTEE_ORDINAIRE})


class QuatreDemandesDeBriceTests(unittest.TestCase):
    """Les quatre pistes du 2026-09-04, chacune tranchee par la source."""

    def test_l_approbation_des_comptes_ne_releve_pas_des_seuils(self) -> None:
        """Piste 1. Les seuils de l'art. 21 al. 2 portent sur des marches et
        des contrats a passer; un exercice clos n'en passe aucun."""
        self.assertFalse(
            T.controle_applicable(V.PORTEE_APPROBATION_COMPTES, T.CTRL_SEUIL))
        self.assertIn("exercice clos", T.motif_hors_controle(
            V.PORTEE_APPROBATION_COMPTES, T.CTRL_SEUIL))

    def test_l_approbation_des_comptes_appelle_le_rapport_du_conseil_syndical(self) -> None:
        """Piste 1, sa seconde moitie: le rattachement qui remplace le seuil.

        Decret 67-223 art. 22 al. 2 - le conseil syndical rend compte chaque
        annee - et art. 11 II 4, qui joint ce compte rendu a l'ordre du jour.
        """
        self.assertTrue(
            T.controle_applicable(V.PORTEE_APPROBATION_COMPTES, T.CTRL_RAPPORT_CS))
        self.assertEqual(
            set(T.portees_soumises(T.CTRL_RAPPORT_CS)),
            {V.PORTEE_APPROBATION_COMPTES, V.PORTEE_DELEGATION_CS},
        )

    def test_le_contrat_de_syndic_est_exclu_du_seuil_de_mise_en_concurrence(self) -> None:
        """Piste 2, tranchee par la source et non par l'intuition.

        Il n'existe AUCUNE exclusion de la passerelle de l'art. 25-1 pour la
        designation du syndic: le texte vise l'art. 25 'ou une autre
        disposition', sans reserve. L'exception que Brice pressentait existe
        bien, mais elle est ailleurs et elle n'est pas une exclusion: l'art. 21
        al. 2 sort le contrat de syndic du seuil de mise en concurrence, et le
        decret art. 19 impose de voter chaque candidature a la majorite du
        premier vote avant d'ouvrir le second.
        """
        # **Mesure deplacee par `RM-2026-0144`, propriete inchangee.**
        # Elle portait sur `CTRL_SEUIL`, qui couvre les TROIS relations de
        # seuil: le retrait emportait donc aussi le seuil de consultation du
        # conseil syndical, que l'alinea n'excepte pas. L'exclusion se declare
        # desormais par RELATION, et c'est la qu'on la verifie.
        from coproscope.modules._actes_seuils_applicabilite import portees_exclues
        from coproscope.modules._actes_seuils_normes import NORME_CONCURRENCE

        self.assertIn(
            V.PORTEE_DESIGNATION_SYNDIC,
            portees_exclues(NORME_CONCURRENCE.relation))
        self.assertIn("autres que celui de syndic", NORME_CONCURRENCE.exclut)

    def test_l_autorisation_a_un_coproprietaire_n_engage_pas_le_syndicat(self) -> None:
        """Piste 4. Art. 25 b: les travaux sont faits a leurs frais."""
        for controle in (T.CTRL_SEUIL, T.CTRL_AVIS_CS, T.CTRL_DEVIS,
                         T.CTRL_EXECUTION):
            self.assertFalse(T.controle_applicable(
                V.PORTEE_AUTORISATION_COPROPRIETAIRE, controle), controle)


class DeuxCabinetsTests(unittest.TestCase):
    """Le meme type sous deux plumes. C'est le test de l'axe.

    Si l'un des deux couples echouait, le typage aurait appris un cabinet par
    coeur - exactement ce que la regle du 2026-09-04 interdit.
    """

    def _portee(self, texte: str) -> str:
        return Q.portee_resolution(texte, AG)[0]

    def test_election_et_designation_du_syndic_donnent_le_meme_type(self) -> None:
        self.assertEqual(
            self._portee("7 - Election du syndic selon les modalites de son "
                         "contrat joint a la convocation."),
            V.PORTEE_DESIGNATION_SYNDIC)
        self.assertEqual(
            self._portee("Resolution n 9 : Designation du syndic (Article 25 - "
                         "General) L'assemblee generale designe en qualite de "
                         "syndic le cabinet dont le contrat est annexe."),
            V.PORTEE_DESIGNATION_SYNDIC)

    def test_vote_et_fixation_d_un_seuil_donnent_le_meme_type(self) -> None:
        self.assertEqual(
            self._portee("26 - Vote du montant des marches et contrats a partir "
                         "desquels la consultation du Conseil Syndical est "
                         "obligatoire."),
            V.PORTEE_SEUIL)
        self.assertEqual(
            self._portee("Resolution n 22 : Fixation du montant des marches et "
                         "contrats, a partir duquel la consultation du conseil "
                         "syndical est rendue obligatoire."),
            V.PORTEE_SEUIL)

    def test_election_et_designation_au_conseil_syndical_donnent_le_meme_type(self) -> None:
        self.assertEqual(
            self._portee("8 - Election des Membres du Conseil Syndical."),
            V.PORTEE_DESIGNATION_ORGANE)
        self.assertEqual(
            self._portee("Resolution n 13 : Election au conseil syndical "
                         "(Article 25 - General)"),
            V.PORTEE_DESIGNATION_ORGANE)

    def test_les_deux_ecritures_de_l_autorisation_de_l_article_25_b(self) -> None:
        self.assertEqual(
            self._portee("35 - A la demande d'un coproprietaire - Vote de "
                         "l'autorisation a lui donner pour installer un "
                         "equipement sous la partie exterieure de son balcon."),
            V.PORTEE_AUTORISATION_COPROPRIETAIRE)
        self.assertEqual(
            self._portee("Resolution n 28 : Demande d'autorisation de travaux "
                         "privatifs affectant les parties communes, a la charge "
                         "du coproprietaire demandeur."),
            V.PORTEE_AUTORISATION_COPROPRIETAIRE)


class LaStructureTrancheCeQueLesMotsLaissentAmbiguTests(unittest.TestCase):
    """Deux dates suffisent la ou aucun mot ne suffirait."""

    def test_un_exercice_clos_avant_l_assemblee_est_une_approbation_des_comptes(self) -> None:
        portee, indices = Q.portee_resolution(
            "5 - Approbation des comptes du syndicat pour la periode du "
            "01/01/2023 au 31/12/2023. L'assemblee generale approuve les comptes "
            "de l'exercice.", AG)
        self.assertEqual(portee, V.PORTEE_APPROBATION_COMPTES)
        self.assertTrue(any("clos" in i for i in indices))

    def test_un_exercice_qui_court_apres_l_assemblee_est_un_budget(self) -> None:
        self.assertEqual(
            Q.portee_resolution(
                "28 - Vote du montant du Budget de l'exercice 2024 du "
                "01/01/2024 au 31/12/2024, pour 280.000 EUR.", AG)[0],
            V.PORTEE_BUDGET)

    def test_le_mot_approuve_ne_suffit_pas_a_faire_une_approbation_des_comptes(self) -> None:
        """Faux positif mesure sur le corpus, et corrige par la periode.

        `Modalites de recouvrement des charges` etait rangee en approbation des
        comptes parce que son corps dit `approuve` et `charges`. Rien dans ce
        texte ne porte sur un exercice clos.
        """
        self.assertEqual(
            Q.portee_resolution(
                "30 - Modalites de recouvrement des charges. L'assemblee "
                "generale approuve les modalites de recouvrement.", AG)[0],
            V.PORTEE_MODALITES)

    def test_sans_periode_lisible_le_type_n_est_pas_invente(self) -> None:
        portee, indices = Q.portee_resolution(
            "12 - Question relative aux comptes de la copropriete.", AG)
        self.assertEqual(portee, V.PORTEE_ORDINAIRE)
        self.assertTrue(any("non lisible" in i for i in indices))

    def test_la_fonction_designee_prime_sur_la_personne_designee(self) -> None:
        """Le decret art. 15 fait du syndic le secretaire de plein droit.

        Le proces-verbal ecrit donc, sous l'intitule `election du Secretaire`,
        qu'il nomme le syndic. Lire `syndic` d'abord retirait a cette resolution
        le controle de seuil au nom d'une exception - l'art. 21 al. 2 - qui ne
        la vise pas.
        """
        self.assertEqual(
            Q.portee_resolution(
                "4 - Constitution du bureau de seance, election du Secretaire. "
                "L'assemblee generale procede a la designation d'un Secretaire. "
                "Elle nomme LE SYNDIC.", AG)[0],
            V.PORTEE_DESIGNATION_ORGANE)

    def test_des_travaux_sans_prix_ecrit_restent_non_determines(self) -> None:
        """Les typer en engagement de depense les soumettrait a un controle de
        montant que le document ne permet pas de tenir.

        L'indice le dit, pour que l'utilisateur sache que la question n'est pas
        `quel type` mais `pourquoi ce proces-verbal n'ecrit pas de prix`.
        """
        portee, indices = Q.portee_resolution(
            "33 - Vote des travaux de deplacement d'un ouvrage situe sur "
            "l'ancienne entree de la residence.", AG)
        self.assertEqual(portee, V.PORTEE_ORDINAIRE)
        self.assertTrue(any("aucun montant" in i for i in indices), indices)

    def test_une_decision_sans_objet_reconnaissable_reste_non_determinee(self) -> None:
        """Mesure sur le corpus: deux resolutions sur 55 sont dans ce cas.

        Le proces-verbal enonce une decision d'amenagement sans nommer ni
        travaux, ni marche, ni prix. Aucun type n'est deductible, et le dire est
        la seule reponse honnete: tous les controles restent appliques.
        """
        self.assertEqual(
            Q.portee_resolution(
                "34 - Vote de la decision de reculer la barriere situee avant "
                "le jeu de boules.", AG)[0],
            V.PORTEE_ORDINAIRE)

    def test_un_appel_de_fonds_n_est_pas_la_depense_qu_il_finance(self) -> None:
        """Compter les deux serait compter deux fois le meme euro.

        Loi art. 14-1 I al. 2 et 3 et II, decret art. 35: l'assemblee vote QUAND
        et COMMENT une depense est appelee, ce qui est un objet propre.
        """
        self.assertEqual(
            Q.portee_resolution(
                "37 - Vote des modalites des Appels de Fonds exceptionnels "
                "correspondant aux depenses votees au 01/10/2024.", AG)[0],
            V.PORTEE_MODALITES)

    def test_une_autorisation_de_penetrer_n_est_pas_une_autorisation_de_travaux(self) -> None:
        """Art. 24 II h contre art. 25 b: aucun travaux, donc aucune des deux
        familles de controle de l'article 25 b."""
        self.assertEqual(
            Q.portee_resolution(
                "32 - Vote de l'autorisation permanente accordee a la Police "
                "Municipale de penetrer dans les parties communes.", AG)[0],
            V.PORTEE_MODALITES)

    def test_des_travaux_chiffres_sont_un_engagement_de_depense(self) -> None:
        self.assertEqual(
            Q.portee_resolution(
                "40 - Vote des travaux de remplacement des boites aux lettres. "
                "L'assemblee generale vote le devis a 2.907,30 EUR T.T.C.", AG)[0],
            V.PORTEE_ENGAGEMENT_DEPENSE)


class LaMatriceCesseDeMettreToutSurLeMemePlanTests(unittest.TestCase):
    """Le typage vu depuis les vues, la ou l'ecran le lit."""

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=True)

    def _matrice(self, *actes: dict) -> dict[str, dict]:
        A.ecrire(self.instance, A.TABLE_ACTES, list(actes), ["DOC-PV"])
        return {l["acte_id"]: l for l in A.matrice(self.instance)}

    def test_une_election_ne_reclame_plus_de_seuil_ni_d_avis(self) -> None:
        """Le defaut vu sur la maquette, et sa mesure.

        Sur les 55 resolutions du proces-verbal du 03/07/2024, vingt-deux sont
        des designations. Avant le typage, chacune portait une cellule seuil et
        une cellule avis marquees `Source manquante`.
        """
        lignes = self._matrice(
            _acte("ELECTION", portee=V.PORTEE_DESIGNATION_ORGANE,
                  objet="Election des membres du conseil syndical"),
            _acte("TRAVAUX", portee=V.PORTEE_ENGAGEMENT_DEPENSE,
                  montant_autorise="2907.30", objet="Remplacement d'equipements"),
        )
        self.assertEqual(lignes["ELECTION"]["cel_seuil"], V.FORCE_NON_APPLICABLE)
        self.assertEqual(lignes["ELECTION"]["cel_avis_cs"], V.FORCE_NON_APPLICABLE)
        self.assertEqual(lignes["TRAVAUX"]["cel_seuil"], V.FORCE_ABSENT)
        self.assertEqual(lignes["TRAVAUX"]["cel_avis_cs"], V.FORCE_ABSENT)

    def test_non_applicable_ne_se_confond_pas_avec_source_manquante(self) -> None:
        """Les deux etats appellent des gestes opposes: l'un une diligence,
        l'autre son retrait. Les ecrire pareil, c'etait mentir poliment."""
        self.assertNotEqual(V.FORCE_NON_APPLICABLE, V.FORCE_ABSENT)
        self.assertIn(V.FORCE_NON_APPLICABLE, V.FORCES)
        self.assertFalse(V.diffusable(V.FORCE_NON_APPLICABLE))

    def test_seule_l_approbation_des_comptes_reclame_le_rapport_du_conseil(self) -> None:
        lignes = self._matrice(
            _acte("COMPTES", portee=V.PORTEE_APPROBATION_COMPTES,
                  objet="Approbation des comptes de l'exercice clos"),
            _acte("ELECTION2", portee=V.PORTEE_DESIGNATION_ORGANE,
                  objet="Election du bureau"),
        )
        self.assertEqual(lignes["COMPTES"]["cel_rapport_cs"], V.FORCE_ABSENT)
        self.assertEqual(lignes["ELECTION2"]["cel_rapport_cs"],
                         V.FORCE_NON_APPLICABLE)

    def test_un_budget_vote_ne_produit_pas_de_constat_d_inexecution(self) -> None:
        """Une enveloppe ne se rapproche pas d'une depense.

        Sans cette borne, tout budget previsionnel adopte produisait un
        `ACTE_SANS_EXECUTION` a chaque exercice - un constat qui n'a jamais rien
        voulu dire.
        """
        A.ecrire(self.instance, A.TABLE_ACTES, [
            _acte("BUDGET", portee=V.PORTEE_BUDGET, montant_autorise="280000.00",
                  objet="Budget previsionnel de l'exercice a venir"),
            _acte("MARCHE", portee=V.PORTEE_ENGAGEMENT_DEPENSE,
                  montant_autorise="2907.30", objet="Travaux votes"),
        ], ["DOC-PV"])
        constats = {l["code"]: l["sujet_id"] for l in A.constats(self.instance)}
        self.assertEqual(constats.get("ACTE_SANS_EXECUTION"), "MARCHE")


class LaDepenseSansActeCesseDAccuserLeBudgetTests(unittest.TestCase):
    """Piste 3: ce qui releve du budget deja vote n'est pas non autorise."""

    def setUp(self) -> None:
        self.racine = Path(tempfile.mkdtemp())
        self.instance = _Instance(self.racine)

    def tearDown(self) -> None:
        shutil.rmtree(self.racine, ignore_errors=True)

    def _codes(self, imputation: str) -> set[str]:
        A.ecrire(self.instance, A.TABLE_DOSSIERS,
                 [_dossier("DEP", imputation=imputation)], ["DOC-FAC"])
        return {l["code"] for l in A.constats(self.instance)}

    def test_une_depense_courante_du_budget_vote_n_est_pas_un_manquement(self) -> None:
        """Loi art. 14-1 I: le vote du budget vaut autorisation des depenses
        courantes. Aucune resolution ligne a ligne n'est due."""
        self.assertNotIn("EURO_SANS_ACTE", self._codes("BUDGET_PREVISIONNEL"))

    def test_une_depense_hors_budget_sans_acte_reste_un_manquement(self) -> None:
        self.assertIn("EURO_SANS_ACTE", self._codes("VOTE_SEPARE"))

    def test_une_imputation_non_tranchee_est_rendue_a_l_utilisateur(self) -> None:
        """Le partage tient a l'article 45, et il ne s'automatise pas ici.

        Plutot que de trancher a la place de l'utilisateur - dans un sens qui
        accuserait a tort, dans l'autre qui blanchirait a tort - le constat
        nomme les deux reponses possibles et l'article qui les separe.
        """
        codes = self._codes("INDETERMINE")
        self.assertIn("IMPUTATION_A_TRANCHER", codes)
        self.assertNotIn("EURO_SANS_ACTE", codes)
        motif = [l["motif"] for l in A.constats(self.instance)
                 if l["code"] == "IMPUTATION_A_TRANCHER"][0]
        self.assertIn("article 45", motif)
        self.assertIn("decret art. 44", motif)


class NatureEtPorteeSontDeuxAxesTests(unittest.TestCase):
    """Le type dit sur quoi l'acte porte; la nature dit d'ou il vient.

    Les confondre reviendrait a perdre l'un des deux, et le modele a besoin des
    deux: une decision du conseil syndical qui engage une depense se controle
    par sa nature (elle doit etre fondee par une delegation en vigueur) ET par
    sa portee (elle doit respecter le seuil de mise en concurrence).
    """

    def test_les_deux_vocabulaires_ne_se_recouvrent_pas(self) -> None:
        self.assertEqual(set(V.NATURES) & set(V.PORTEES), set())

    def test_un_acte_delegue_qui_engage_une_depense_porte_les_deux_controles(self) -> None:
        racine = Path(tempfile.mkdtemp())
        try:
            instance = _Instance(racine)
            A.ecrire(instance, A.TABLE_ACTES, [
                _acte("CS-DEP", nature=V.NATURE_DECISION_CS,
                      portee=V.PORTEE_ENGAGEMENT_DEPENSE,
                      montant_autorise="4200.00", objet="Depense engagee"),
            ], ["DOC-PV"])
            codes = {l["code"] for l in A.constats(instance)}
            # Par la nature: aucune delegation ne la fonde.
            self.assertIn("ACTE_SANS_FONDEMENT", codes)
            # Par la portee: le seuil reste a produire.
            ligne = A.matrice(instance)[0]
            self.assertEqual(ligne["cel_seuil"], V.FORCE_ABSENT)
        finally:
            shutil.rmtree(racine, ignore_errors=True)


class PasDeCitationDeMemoireTests(unittest.TestCase):
    """Le garde-fou de la consigne: un identifiant Legifrance, ou rien.

    **Constat `C085`, volet 1, corrige le 2026-09-10.** Ce motif s'ecrivait
    `re.compile(r"LEGIARTI\d{12}")`, **sans ancres**, si bien que
    `XXLEGIARTI999999999999YY` le satisfaisait: la garde ne verifiait pas la
    forme d'un identifiant, elle verifiait qu'un identifiant se cachait
    quelque part dans la chaine. Le meme fichier portait deja la version
    ancree, `r"^LEGIARTI\d{12}$"`, sur un autre jeu de valeurs - deux
    ecritures de la meme regle dans un seul fichier, dont une seule mordait.
    Le motif vient desormais d'un seul endroit.
    """

    MOTIF = MOTIF_IDENTIFIANT

    def test_tous_les_identifiants_ont_la_forme_attendue(self) -> None:
        identifiants = [
            ident for _, sources in T.FONDEMENT_PORTEE.values()
            for _, ident in sources
        ]
        self.assertTrue(identifiants)
        for ident in identifiants:
            self.assertRegex(ident, self.MOTIF)

    def test_aucune_portee_typee_ne_reste_sans_source(self) -> None:
        sans_source = [
            portee for portee, (_, sources) in T.FONDEMENT_PORTEE.items()
            if not sources and portee != V.PORTEE_ORDINAIRE
        ]
        self.assertEqual(sans_source, [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


class LA_GARDE_DES_IDENTIFIANTS_MORD_VRAIMENT(unittest.TestCase):
    """Constat `C085`, volet 1: la garde ne gardait pas.

    Le motif etait employe sans ancres. `assertRegex` cherche une
    correspondance N'IMPORTE OU dans la chaine, donc un identifiant noye dans
    du bruit passait - et une garde qui accepte le bruit ne verifie plus la
    forme, elle verifie la presence.

    **Ce module verifie l'INSTRUMENT, pas les donnees.** Les donnees sont
    verifiees par les deux tests voisins; ce qui manquait etait la preuve que
    leur verificateur sait dire non.
    """

    def test_un_identifiant_NOYE_DANS_DU_BRUIT_est_refuse(self) -> None:
        for faux in ("XXLEGIARTI999999999999YY", " LEGIARTI000000000001",
                     "LEGIARTI000000000001 ", "voir LEGIARTI000000000001"):
            with self.subTest(valeur=faux):
                self.assertIsNone(MOTIF_IDENTIFIANT.fullmatch(faux))
                self.assertNotRegex(faux, MOTIF_IDENTIFIANT)

    def test_un_identifiant_trop_court_ou_trop_long_est_refuse(self) -> None:
        self.assertNotRegex("LEGIARTI00000000001", MOTIF_IDENTIFIANT)
        self.assertNotRegex("LEGIARTI0000000000012", MOTIF_IDENTIFIANT)

    def test_un_identifiant_bien_forme_reste_accepte(self) -> None:
        """Anti-vacuite: une garde qui refuse tout ne garde rien non plus."""
        self.assertRegex("LEGIARTI000006428859", MOTIF_IDENTIFIANT)

    def test_les_deux_controles_du_fichier_partagent_LE_MEME_motif(self) -> None:
        """Deux ecritures de la meme regle divergent; une seule mordait."""
        self.assertIs(PasDeCitationDeMemoireTests.MOTIF, MOTIF_IDENTIFIANT)
