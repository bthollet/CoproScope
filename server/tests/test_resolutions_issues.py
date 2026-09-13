"""La lecture de l'issue d'une resolution, et la passerelle qu'une regex tranchait.

Deux replis muets, mesures le 2026-09-04 sur les deux corpus.

**Un mot de cloture hors liste sortait cinq votes de tous les comptages.** Apres
neuf prefixes essayes, la lecture rendait `mot.upper()`. Le second cabinet ecrit
cinq fois "cette resolution est DEVENUE sans objet": la valeur stockee devenait
la chaine "DEVENUE", qui n'est ni un libelle d'ecran, ni un des trois compteurs,
ni une ligne de relecture. L'ecran annoncait 91 resolutions et n'en comptait que
86, sans exception et sans trace.

**Une regex decidait seule de la majorite appliquee.** `il est passe au vote
suivant l'article 25-1` faisait ecrire `24` quelle que soit la majorite
annoncee, alors que la passerelle ne s'ouvre que sur une resolution annoncee
sous l'article 25.

Aucun nom, aucun tantieme individuel, aucun vote nominatif ne figure dans ces
textes de test: ce sont des formules de cloture et des annonces de majorite.
"""

from __future__ import annotations

import unittest

from coproscope.modules._resolutions_extraction import (
    _issue,
    _majorite_appliquee,
    _majorites,
    divergence_passerelle,
    parse_resolutions,
)
from coproscope.modules._resolutions_motifs import (
    ISSUE_NON_RECONNUE,
    REPORTEE,
    SANS_OBJET,
)


class UneClotureSeLitEnEntier(unittest.TestCase):
    """Le mot qui porte l'issue n'est pas toujours le premier."""

    def test_devenue_sans_objet_est_lue_sans_objet(self):
        # Mesure du second cabinet: cinq occurrences, toutes rendues "DEVENUE".
        self.assertEqual(
            _issue("En consequence, cette resolution est devenue sans objet.", False),
            SANS_OBJET,
        )

    def test_la_forme_accentuee_du_second_cabinet_est_lue_de_meme(self):
        self.assertEqual(
            _issue("cette résolution est devenue sans objet", False), SANS_OBJET
        )

    def test_les_formes_du_premier_cabinet_ne_changent_pas(self):
        self.assertEqual(
            _issue("En vertu de quoi cette resolution est adoptee.", True), "ADOPTEE"
        )
        self.assertEqual(
            _issue("En consequence, cette resolution est rejetee.", True), "REJETEE"
        )
        self.assertEqual(
            _issue("cette resolution est ajournee", False), REPORTEE
        )


class UnVocabulaireInconnuEstUnFaitNomme(unittest.TestCase):
    """Aucun mot brut n'est promu au rang d'issue."""

    def test_une_cloture_illisible_ne_rend_pas_le_mot_brut(self):
        issue = _issue("cette resolution est zzzz qqqq", False)
        self.assertEqual(issue, ISSUE_NON_RECONNUE)
        self.assertNotEqual(issue, "ZZZZ")

    def test_la_ligne_est_appelee_a_relecture(self):
        texte = (
            "1° - Designation du president. Article 24. "
            "cette resolution est zzzz qqqq"
        )
        res = parse_resolutions(texte)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].resultat, ISSUE_NON_RECONNUE)
        self.assertEqual(res[0].confiance, "faible")


class SansNEstUneIssueQuAccompagneDObjet(unittest.TestCase):
    """Regression du 2026-09-05: "sans" seul tranchait la locution.

    En elargissant la fenetre de capture a trois mots, la lecture a commence a
    essayer chaque mot de la locution. Le prefixe generique `("sans",
    "SANS_OBJET")` etait alors atteint par toutes les formules ou "sans"
    n'introduit qu'une reserve. Mesure avant correction, sur le code livre:

        "cette resolution est votee sans opposition"   -> SANS_OBJET
        "cette resolution est acceptee sans reserve"   -> SANS_OBJET
        "cette resolution est prise sans debat"        -> SANS_OBJET

    Une resolution votee entrait ainsi dans le compteur "sans vote", avec la
    confiance "moyenne" et hors de la liste de relecture: fausse, comptee, et
    d'apparence normale. C'est plus grave que l'invisibilite d'avant.
    """

    def test_une_reserve_introduite_par_sans_n_est_pas_une_absence_d_objet(self):
        for formule in (
            "cette resolution est votee sans opposition",
            "cette resolution est acceptee sans reserve",
            "cette resolution est prise sans debat",
        ):
            with self.subTest(formule=formule):
                self.assertNotEqual(_issue(formule, True), SANS_OBJET)

    def test_ces_formules_sont_appelees_a_relecture_plutot_que_comptees(self):
        # Le vocabulaire de ces trois formules n'est pas celui du corpus de
        # calibrage. Le dire est un fait nomme; les compter "sans vote" est un
        # defaut silencieux.
        for formule in (
            "cette resolution est votee sans opposition",
            "cette resolution est acceptee sans reserve",
            "cette resolution est prise sans debat",
        ):
            with self.subTest(formule=formule):
                self.assertEqual(_issue(formule, True), ISSUE_NON_RECONNUE)

    def test_la_locution_sans_objet_reste_lue_sous_ses_deux_formes(self):
        self.assertEqual(_issue("cette resolution est sans objet", False), SANS_OBJET)
        self.assertEqual(
            _issue("cette resolution est devenue sans objet", False), SANS_OBJET
        )

    def test_une_resolution_votee_n_entre_pas_dans_le_compteur_sans_vote(self):
        texte = (
            "1° - Approbation des comptes. Article 24. "
            "cette resolution est votee sans opposition"
        )
        ligne = parse_resolutions(texte)[0]
        self.assertNotEqual(ligne.resultat, SANS_OBJET)
        self.assertEqual(ligne.confiance, "faible")


class LaPasserelleNEstPlusTrancheeParUneRegexSeule(unittest.TestCase):
    """Elle ne s'ouvre que sur une resolution annoncee sous l'article 25."""

    def test_sous_l_article_25_la_passerelle_bascule_bien_vers_l_article_24(self):
        self.assertEqual(_majorite_appliquee("", "25", True), "24")
        self.assertEqual(divergence_passerelle("25", True), "")

    def test_sous_l_article_26_la_majorite_annoncee_est_conservee(self):
        self.assertEqual(_majorite_appliquee("", "26", True), "26")
        self.assertIn("ne s'ouvre que", divergence_passerelle("26", True))

    def test_annoncee_25_1_seul_la_majorite_annoncee_est_conservee(self):
        # Troisieme et derniere combinaison changee par la correction C012,
        # jusqu'ici non couverte: le PV qui annonce "Article 25-1" seul.
        self.assertEqual(_majorite_appliquee("", "25-1", True), "25-1")

    def test_la_formule_courante_du_corpus_reste_lue_sous_l_article_25(self):
        # L'etalon ecrit "articles 25 et 25-1": la majorite annoncee lue est
        # "25", donc la combinaison inchangee. C'est ce qui garantit que la
        # correction ne deplace pas le comptage de la piece de reference.
        self.assertEqual(_majorites("aux articles 25 et 25-1"), ["25"])
        self.assertEqual(_majorite_appliquee("", "25", True), "24")

    def test_sans_majorite_annoncee_rien_n_est_invente(self):
        self.assertEqual(_majorite_appliquee("", "", True), "")
        self.assertIn("aucune majorite", divergence_passerelle("", True))

    def test_l_ecart_est_porte_dans_les_divergences_de_la_ligne(self):
        texte = (
            "1° - Travaux de facade. Article 26. "
            "Il est passe au vote suivant l'article 25-1. "
            "cette resolution est adoptee."
        )
        res = parse_resolutions(texte)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].majorite_annoncee, "26")
        self.assertEqual(res[0].majorite_appliquee, "26")
        self.assertTrue(res[0].passerelle_utilisee)
        self.assertTrue(
            any("25-1" in d for d in res[0].divergences), res[0].divergences
        )

    def test_le_cas_courant_du_corpus_ne_produit_aucune_divergence(self):
        texte = (
            "1° - Travaux de facade. Article 25. "
            "Il est passe au vote suivant l'article 25-1. "
            "cette resolution est adoptee."
        )
        res = parse_resolutions(texte)
        self.assertEqual(res[0].majorite_appliquee, "24")
        self.assertEqual(res[0].divergences, [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
