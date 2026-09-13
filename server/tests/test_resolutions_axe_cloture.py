"""L'axe de cloture: le texte enonce-t-il l'issue du vote pour CETTE resolution ?

Ces tests portent sur une seule question et sur son residu. Ils sont ecrits
pour echouer si quelqu'un revient a une enumeration de formules, et pour
echouer si la chaine se remet a rendre zero sans le dire.

**Ce que ces tests NE prouvent PAS.** Aucune matiere reelle n'est reproduite
ici: les corpus prives ne rentrent pas dans le depot. Les textes ci-dessous
sont des reconstructions minimales des structures MESUREES le 2026-09-08 sur
deux cabinets et 360 pieces sources - la mesure est citee dans le rendu du lot
et dans les commentaires du code, pas prouvee par ce fichier.
"""

from __future__ import annotations

import unittest

from coproscope.modules import resolutions as R
from coproscope.modules._resolutions_calibrage import _marqueurs
from coproscope.modules._resolutions_cloture import (
    ANNEAU_LARGE,
    ANNEAU_STRICT,
    ancres,
    issues_muettes,
    locution_de_cloture,
)


def _issues(text: str) -> list[str]:
    return [r.resultat for r in R.parse_resolutions(text)]


def _muet(text: str) -> dict[str, object]:
    return issues_muettes(text, _marqueurs(text), _issues(text))


# Un cabinet qui n'ecrit JAMAIS la formule mesuree sur les deux corpus connus.
# Il designe sa resolution par son numero, et il conjugue au passe compose.
TROISIEME_CABINET = """
Resolution n°1 : Designation du president de seance (Article 24)
L'assemblee designe M. X. La resolution n°1 a ete adoptee a l'unanimite.

Resolution n°2 : Approbation des comptes de l'exercice (Article 24)
Les comptes sont presentes. La resolution n°2 a ete rejetee.

Resolution n°3 : Travaux de ravalement (Article 25)
Le devis est presente. La resolution n°3 a ete adoptee.
"""

# Le meme cabinet, mais l'issue n'est PAS predicee d'une designation: elle est
# posee seule, en fin de bloc, comme une etiquette de colonne. Aucun anneau ne
# la lit - c'est le residu declare de l'invariant.
QUATRIEME_CABINET = """
Resolution n°1 : Designation du president de seance (Article 24)
L'assemblee designe M. X. Ont vote pour : 8000 / 10.000
Resultat du vote : ADOPTEE

Resolution n°2 : Approbation des comptes (Article 24)
Les comptes sont presentes. Ont vote pour : 2000 / 10.000
Resultat du vote : REJETEE

Resolution n°3 : Travaux de ravalement (Article 25)
Le devis est presente. Ont vote pour : 9000 / 10.000
Resultat du vote : ADOPTEE
"""

# `RM-2026-0129`, 2026-09-12. **Le quatrieme cabinet est devenu LISIBLE** -
# l'anneau de position lit `Resultat du vote : ADOPTEE`, pose sous l'intitule
# comme le decret 67-223 art. 17 le decrit. Les tests qui verifiaient qu'un
# proces-verbal illisible ne passe ni pour une convocation ni pour un document
# vide perdaient donc leur sujet.
#
# Ce cinquieme cabinet le leur rend: il enonce ses issues **noyees dans une
# ligne de comptage**, sans designation deictique et sans ligne d'issue seule.
# Aucun des trois anneaux ne le lit, et c'est voulu: **une redaction reste
# toujours hors de portee, et ce qui compte est que le silence soit
# BRUYANT.**
CINQUIEME_CABINET = """
Resolution n\u00b01 : Designation du president de seance (Article 24)
Pour 8000 / 10.000, contre 2000, soit resolution adoptee par la majorite requise.

Resolution n\u00b02 : Approbation des comptes (Article 24)
Pour 2000 / 10.000, contre 8000, soit resolution rejetee faute de majorite.

Resolution n\u00b03 : Travaux de ravalement (Article 25)
Pour 9000 / 10.000, contre 1000, soit resolution adoptee a la majorite de l'article 25.
"""

# Une convocation: elle porte des projets numerotes et n'enonce aucune issue.
# Les quelques participes qu'elle contient viennent de ses annexes comptables.
CONVOCATION = """
Resolution n°1 : Designation du president de seance (Article 24)
L'assemblee generale designe en qualite de president de seance.

Resolution n°2 : Approbation des comptes (Article 24)
Etat financier. Exercice precedent approuve. Exercice clos.

Resolution n°3 : Budget previsionnel (Article 24)
L'assemblee generale approuve le budget previsionnel.

Resolution n°4 : Travaux de ravalement (Article 25)
Le devis joint est soumis au vote.
"""


class AxeAncrage(unittest.TestCase):
    """Quel anneau prend la main, et pourquoi."""

    def test_anneau_strict_prefere_quand_il_rend_une_serie(self):
        """La formule mesuree du cabinet garde la main. Non-regression par
        construction: tant qu'elle est presente en serie, l'elargissement ne
        peut pas deplacer une frontiere de segment."""
        text = (
            "1° - Objet un. cette resolution est adoptee. "
            "2° - Objet deux. cette resolution est rejetee. "
            "3° - Objet trois. cette resolution est adoptee."
        )
        self.assertEqual(ancres(text)[1], ANNEAU_STRICT)

    def test_anneau_large_prend_la_main_si_le_strict_est_muet(self):
        """C'est le seul chemin par lequel un troisieme cabinet est lu du tout."""
        marques, anneau = ancres(TROISIEME_CABINET)
        self.assertEqual(anneau, ANNEAU_LARGE)
        self.assertEqual(len(marques), 3)

    def test_l_anneau_de_POSITION_lit_le_quatrieme_cabinet(self):
        """`RM-2026-0129`: ce texte etait le residu declare de l'invariant.

        Il pose l'issue sous l'intitule - `Resultat du vote : ADOPTEE` - ce
        que le decret 67-223 art. 17 decrit et qu'aucune PREDICATION ne
        capture. L'anneau de position le lit depuis le 2026-09-12.
        """
        self.assertEqual(ancres(QUATRIEME_CABINET)[1], "position")

    def test_aucun_anneau_sur_un_texte_sans_predication(self):
        """La meme verification, sur une redaction qui reste hors de portee."""
        self.assertEqual(ancres(CINQUIEME_CABINET)[1], "aucune")


class AxeLecture(unittest.TestCase):
    """Ce que le code fait de l'issue, une fois le segment delimite."""

    def test_troisieme_cabinet_est_lu_sans_ajouter_une_formule(self):
        """`a ete adoptee` n'a jamais ete ajoute nulle part: c'est la STRUCTURE
        - designation deictique, liaison libre, participe - qui la lit."""
        self.assertEqual(_issues(TROISIEME_CABINET), ["ADOPTEE", "REJETEE", "ADOPTEE"])

    def test_le_futur_est_une_liaison_comme_une_autre(self):
        """Mesure du 2026-09-08, second cabinet: `Cette resolution sera
        reportee` est un constat de vote, et il etait perdu."""
        issue, anneau = locution_de_cloture("Cette resolution sera reportee a la prochaine")
        self.assertEqual(anneau, ANNEAU_LARGE)
        self.assertTrue(issue.lower().startswith("reportee"))

    def test_pas_de_vote_car_LA_resolution_est_rejetee_rend_PAS_DE_VOTE(self):
        """**Ce test disait l'inverse, et la phrase contredite est citee ici.**

        Il affirmait, le 2026-09-08: *« Le gain mesure sur Tilleuls: sept
        resolutions de proces-verbaux reels etaient comptees PAS_DE_VOTE alors
        que la phrase entiere dit qu'elles sont REJETEES. Le membre de phrase
        pas de vote etait lu, sa cause ne l'etait pas. »*

        **La confrontation du 2026-09-09 au corpus dont l'etalon est etabli a la
        main, avant tout traitement outil, dit le contraire.** Sur les 55
        resolutions du proces-verbal de reference, la chaine rendait 39/11/4/1
        la ou l'humain avait lu 39/7/8/1: **quatre absences de vote etaient
        devenues des rejets**, et ces quatre lignes portaient zero voix - ni
        pour, ni contre, ni abstention. Dire *rejetee* y attribue a l'assemblee
        un acte qu'elle n'a pas pose, sur des resolutions de modalites d'appels
        de fonds.

        **Ce qui departage les deux lectures est le DETERMINANT, et il se
        mesure.** Sur les 30 pieces du corpus etalon:

            `cette resolution est <issue>` : 92 occurrences
            `la resolution est <issue>`    :  8 occurrences
               dont precedees de `pas de vote` : 8 sur 8
               hors de ce contexte            : 0

        Le redacteur distingue sans exception: le demonstratif annonce l'issue
        de la resolution COURANTE, l'article defini apres une negation de vote
        en designe une AUTRE - celle dont le rejet explique l'absence de vote.

        **Apres correction, les issues tombent EXACTEMENT sur l'etalon**:
        39 adoptees, 7 rejetees, 8 sans vote, 1 sans formule.
        """
        segment = (
            "12° - Travaux de ravalement. VOTE AUX TANTIEMES ENTREE "
            "Pas de vote car la resolution est rejetee"
        )
        self.assertEqual(R.parse_resolutions(segment)[0].resultat, "PAS_DE_VOTE")

    def test_pas_de_vote_car_CETTE_resolution_est_rejetee_rend_REJETEE(self):
        """Le contraste qui prouve que c'est bien le determinant qui tranche.

        Sans lui, la regle serait *toute phrase contenant `pas de vote` rend
        `PAS_DE_VOTE`* - une modalite, qui perdrait le cas ou le redacteur
        enonce vraiment l'issue de la resolution courante.
        """
        segment = (
            "5° - Objet quelconque. Pas de vote car cette resolution est rejetee"
        )
        self.assertEqual(R.parse_resolutions(segment)[0].resultat, "REJETEE")

    def test_la_formule_stricte_garde_la_main_dans_un_segment(self):
        """Quand les deux anneaux parlent, celui du cabinet tranche."""
        segment = (
            "1° - Objet. La decision est favorable au SDC. "
            "cette resolution est adoptee a la majorite."
        )
        self.assertEqual(R.parse_resolutions(segment)[0].resultat, "ADOPTEE")


class MentionsQuiNeSontPasDesVotes(unittest.TestCase):
    """Les six faux positifs mesures de l'anneau large, et ce qu'il en advient.

    Aucun ne doit devenir un vote compte. Tous doivent rester nommes.
    """

    def test_le_pluriel_n_est_pas_une_designation(self):
        """`ceux ayant vote contre l'une des decisions adoptee par cette
        assemblee` figure dans les deux corpus."""
        self.assertEqual(
            ancres("ceux ayant vote contre l'une des decisions adoptee par cette assemblee")[0],
            [],
        )

    def test_une_condition_generale_n_est_pas_un_constat(self):
        """Lu dans un contrat du second cabinet."""
        self.assertEqual(
            ancres("En cas de decision regulierement adoptee par l'assemblee")[0], []
        )

    def test_un_participe_sans_designation_n_est_pas_une_issue(self):
        self.assertEqual(
            ancres("le plan de financement tel qu'il vient d'etre adopte")[0], []
        )

    def test_une_decision_de_justice_n_est_jamais_comptee(self):
        """`La decision est favorable au SDC` et `Cette decision a ete confirme
        par jugement` matchent la structure et ne portent aucun mot d'issue.
        Elles ressortent appelees a relecture, jamais adoptees ni rejetees."""
        for phrase in (
            "1° - Objet. La decision est favorable au SDC.",
            "1° - Objet. Cette decision a ete confirme par jugement.",
        ):
            with self.subTest(phrase=phrase):
                resultat = R.parse_resolutions(phrase)[0].resultat
                self.assertEqual(resultat, R.ISSUE_ENONCEE_NON_LUE)
                self.assertNotIn(resultat, ("ADOPTEE", "REJETEE"))


class LeSilenceEstSupprime(unittest.TestCase):
    """Le coeur du lot: un document qui vote et qu'on ne lit pas le DIT."""

    def test_un_pv_illisible_n_est_plus_rendu_a_zero(self):
        """Avant: trois resolutions `SANS_ISSUE_TRACEE`, c'est-a-dire la meme
        valeur qu'un document qui ne dit rien."""
        self.assertEqual(
            _issues(CINQUIEME_CABINET),
            [R.ISSUE_ENONCEE_NON_LUE] * 3,
        )

    def test_un_pv_illisible_n_est_plus_classe_convocation(self):
        """Le pire des deux mondes, ferme: un vote accompli sortait du registre
        sous l'etiquette d'un vote a venir."""
        self.assertEqual(
            R.nature_assemblee(CINQUIEME_CABINET), R.NATURE_PV_ISSUES_NON_LUES
        )

    def test_le_diagnostic_est_une_phrase_et_pas_un_booleen(self):
        diag = _muet(CINQUIEME_CABINET)
        self.assertTrue(diag["muet"])
        self.assertEqual(diag["clotures_reconnues"], 0)
        self.assertEqual(diag["segments"], 3)
        self.assertEqual(diag["segments_issue_non_lue"], 3)
        self.assertEqual(diag["mutisme"], "partiel")
        self.assertIn("n'est comprise qu'en partie", diag["verdict"])

    def test_les_voix_comptees_ne_masquent_plus_l_issue_non_lue(self):
        """Ordre du test dans `_issue`: un proces-verbal reel COMPTE ses voix.
        Place apres `a_des_voix`, le temoin n'aurait jamais ete atteint et le
        cas le plus probable d'un troisieme cabinet serait retombe dans
        `VOTE_SANS_FORMULE`, qui affirme qu'aucune adoption n'est enoncee."""
        self.assertNotIn("VOTE_SANS_FORMULE", _issues(CINQUIEME_CABINET))

    def test_l_extraction_n_est_pas_declaree_complete(self):
        coh = R.coherence(CINQUIEME_CABINET, R.parse_resolutions(CINQUIEME_CABINET))
        self.assertEqual(coh["issues_enoncees_non_lues"], 3)
        self.assertFalse(coh["extraction_complete"])

    def test_le_quatrieme_cabinet_est_desormais_COMPLET(self):
        """Le pendant: une extraction qui lit tout se declare complete."""
        coh = R.coherence(QUATRIEME_CABINET, R.parse_resolutions(QUATRIEME_CABINET))
        self.assertEqual(coh["issues_enoncees_non_lues"], 0)
        self.assertTrue(coh["extraction_complete"])

    def test_le_resume_compte_a_part_ce_qui_est_dit_et_non_lu(self):
        resume = R.summarize(R.parse_resolutions(CINQUIEME_CABINET))
        self.assertEqual(resume["issue_enoncee_non_lue"], 3)
        self.assertEqual(resume["sans_issue"], 0)

    def test_la_confiance_appelle_la_relecture(self):
        for res in R.parse_resolutions(CINQUIEME_CABINET):
            self.assertEqual(res.confiance, "faible")

    def test_une_issue_LUE_ne_demande_plus_la_relecture(self):
        """Temoin: la confiance suit ce qui a ete lu, pas la redaction."""
        for res in R.parse_resolutions(QUATRIEME_CABINET):
            self.assertEqual(res.confiance, "forte")


class CeQuiNeDoitPasBasculer(unittest.TestCase):
    """Le diagnostic de silence ne doit pas devenir un detecteur de tout."""

    def test_une_convocation_n_est_pas_un_pv_muet(self):
        """Critere STRUCTUREL et non lexical: une convocation porte des projets
        numerotes et n'enonce pas d'issue en serie. Mesure du 2026-09-08 sur le
        second cabinet: 77 resolutions projetees pour 3 participes d'issue."""
        diag = _muet(CONVOCATION)
        self.assertFalse(diag["muet"])
        self.assertEqual(R.nature_assemblee(CONVOCATION), R.NATURE_CONVOCATION)

    def test_un_document_qui_ne_dit_rien_reste_sans_issue_tracee(self):
        """`SANS_ISSUE_TRACEE` et `ISSUE_ENONCEE_NON_LUE` doivent rester deux
        etats distincts: le premier dit que le document se tait."""
        text = (
            "1° - Objet un, sans suite. "
            "2° - Objet deux, sans suite. "
            "3° - Objet trois, sans suite."
        )
        self.assertEqual(_issues(text), ["SANS_ISSUE_TRACEE"] * 3)

    def test_une_lettre_qui_cite_une_resolution_ne_devient_pas_un_pv(self):
        """Une occurrence n'est pas une serie."""
        text = "Monsieur, je conteste la resolution n°4 qui a ete adoptee le 3 juillet."
        self.assertEqual(R.nature_assemblee(text), R.NATURE_AUTRE)


class ResiduDeclare(unittest.TestCase):
    """Ce que l'invariant laisse passer, rendu VISIBLE par un test.

    L'invariant exige une designation deictique. Un cabinet qui poserait
    l'issue seule - `ADOPTEE` en fin de bloc, une colonne `Resultat` - n'est
    lu par aucun anneau, et ce n'est pas un oubli: la deixis est ce qui separe
    le constat de la mention. Ce que ce test verrouille, c'est que la
    degradation reste BRUYANTE.
    """

    def test_l_issue_sans_designation_EST_LUE_depuis_le_2026_09_12(self):
        """**Ce residu est comble**, et le test se retourne au lieu de partir.

        Il disait: *l'issue posee seule n'est lue par aucun anneau, et ce
        n'est pas un oubli*. `RM-2026-0129` a montre que si - le decret decrit
        cette forme - et l'anneau de position la lit. Garder l'ancienne
        assertion aurait fait echouer la suite sur une reparation.
        """
        issues = _issues(QUATRIEME_CABINET)
        self.assertEqual(["ADOPTEE", "REJETEE", "ADOPTEE"], issues)
        self.assertFalse(_muet(QUATRIEME_CABINET)["muet"])

    def test_une_redaction_hors_de_portee_reste_BRUYANTE(self):
        """Ce que le test d'origine verrouillait, et qui reste vrai.

        Une redaction restera toujours hors de portee; ce qui compte est que
        la degradation se voie. Le cinquieme cabinet le montre.
        """
        issues = _issues(CINQUIEME_CABINET)
        self.assertNotIn("ADOPTEE", issues)
        self.assertTrue(_muet(CINQUIEME_CABINET)["muet"])

    def test_sous_le_seuil_de_serie_une_ancre_isolee_ne_segmente_pas(self):
        """Residu connu et non ferme par ce lot: un proces-verbal qui ne
        porterait qu'une ou deux resolutions reste sous `MINIMUM_SERIE` et ne
        produit rien par le repli des clotures. Le test le rend visible au lieu
        de le laisser se decouvrir sur un corpus."""
        text = "Objet unique. cette resolution est adoptee a la majorite."
        self.assertEqual(R.parse_resolutions(text), [])
        self.assertLess(len(ancres(text)[0]), R.MINIMUM_SERIE)


if __name__ == "__main__":
    unittest.main()
