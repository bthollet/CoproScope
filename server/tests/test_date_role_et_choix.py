# -*- coding: utf-8 -*-
"""Un jeton n'est une date que si rien ne le designe comme autre chose.

**Les cas de ce fichier ne sont pas inventes.** Ce sont les pieges mesures par
l'etalon du 2026-09-08 sur 80 documents lus a l'aveugle
(`docs/etalon_dates_confrontation_2026-09-08.md`), ou l'ancien lecteur rendait
**9 dates justes sur 75** et **aucune depuis le corps d'un document**.

Chaque test porte le cas reel qui l'a fait ecrire, et le nombre de documents
qu'il touchait dans le corpus.
"""

from __future__ import annotations

import unittest

from coproscope.core._date_candidats import (
    ROLE_ACTE_CITE,
    ROLE_COLLE,
    ROLE_DATE,
    ROLE_NUMERO,
    candidats_du_texte,
    normalise,
    ordre_du_document,
    role_du_candidat,
)
from coproscope.core.date_du_document import SOURCE_AMBIGU, date_du_document, lire_date


def role(texte: str) -> str:
    normal = normalise(texte)
    candidats = candidats_du_texte(normal)
    assert candidats, "aucun candidat: le cas ne teste pas ce qu'il croit"
    return role_du_candidat(normal, candidats[0])


class LeRoleDuJeton(unittest.TestCase):
    def test_une_date_citee_dans_un_texte_de_loi_n_est_pas_la_date_du_document(self) -> None:
        """Huit factures de 2025 et 2026 etaient datees de novembre 2012."""
        self.assertEqual(ROLE_ACTE_CITE, role("en application du decret n 2012-1115 du 2 octobre 2012"))

    def test_un_numero_de_devis_en_forme_de_date_n_est_pas_une_date(self) -> None:
        """Dix factures datees du 20 octobre 2018 ou du 6 janvier 2016."""
        self.assertEqual(ROLE_NUMERO, role("Selon Devis n 2018-10-20 PH"))

    def test_une_heure_n_est_pas_un_mois(self) -> None:
        """Trois documents: `20/03/2025 08:56:39` rendait 2025-08.

        Le remede n'est pas une regle sur l'heure - j'en avais ecrit une, elle
        etait INATTEIGNABLE. La paire `2025 08` n'est simplement plus proposee
        comme candidat, parce que la forme numerique a deux champs n'est pas
        reconnue du tout. On mesure donc le resultat, et l'absence du faux.
        """
        lecture = lire_date("Facture. Le : 20/03/2025 08:56:39")
        self.assertEqual("2025-03-20", lecture["valeur"])
        self.assertEqual([], candidats_du_texte(normalise("08:56:39 puis 12/2025")))

    def test_un_jeton_colle_a_d_autres_chiffres_n_est_pas_une_date(self) -> None:
        """`FACTURE N F2026-04-058` rendait 2026-04-05.

        Le rejet est plus fort que prevu et c'est mieux ainsi: un jeton borde
        de chiffres n'est meme pas PROPOSE comme candidat, donc aucune regle
        de voisinage n'a a le rattraper.
        """
        self.assertEqual([], candidats_du_texte(normalise("FACTURE N F2026-04-058 du mois")))

    def test_une_date_ordinaire_reste_une_date(self) -> None:
        """La garde doit laisser passer: un filtre qui refuse tout est inutile."""
        self.assertEqual(ROLE_DATE, role("Marseille, le 23/06/2026 - facture"))

    def test_les_regles_structurelles_ne_connaissent_aucun_mot(self) -> None:
        """Un cabinet inconnu ne peut pas refuter une regle de forme.

        Les deux vocabulaires - numerotation, actes juridiques - sont des
        listes, donc refutables. Les trois regles structurelles ne le sont pas,
        et ce test le fige: un libelle en langue inconnue est quand meme
        disqualifie s'il colle le jeton a des chiffres.
        """
        self.assertEqual([], candidats_du_texte(normalise("ZZZZ 9992026-04-05")))


class LaLectureDuDocument(unittest.TestCase):
    def test_la_date_ne_vient_plus_de_la_premiere_forme_trouvee(self) -> None:
        texte = "Facture\nen application du decret n 2012-1115\nMarseille, le 13 avril 2026"
        self.assertEqual(("2026-04-13", "texte"), date_du_document(texte, "piece.pdf"))

    def test_le_cas_le_plus_dangereux_de_l_etalon(self) -> None:
        """Un jour d'ecart, invisible a tout controle de vraisemblance.

        `Devis N JR D2025.04.26 / Date : 25/04/2025`: l'ancien lecteur rendait
        le 26 avril quand le document dit le 25. Ni absurde, ni detectable.
        """
        texte = "Devis N : JR D2025.04.26   Date : 25/04/2025"
        self.assertEqual("2025-04-25", lire_date(texte)["valeur"])

    def test_un_mois_en_lettres_se_lit(self) -> None:
        self.assertEqual("2025-09-01", lire_date("Marseille, le 1 septembre 2025")["valeur"])

    def test_un_prefixe_de_mois_inconnu_se_lit_sans_qu_on_l_ait_ajoute(self) -> None:
        """L'invariant: un mot de mois est un PREFIXE d'un des douze noms.

        `sept.` n'est ecrit nulle part dans le code. Un cabinet qui abregerait
        autrement tombe dans la meme regle, sans modification.
        """
        self.assertEqual("2024-09-12", lire_date("fait le 12 sept. 2024")["valeur"])

    def test_un_desaccord_ne_s_elit_pas_il_se_declare(self) -> None:
        """Deux candidats d'en-tete qui se contredisent: on rend AMBIGU.

        Elire l'un des deux serait trancher a la place du lecteur, et rien dans
        la page ne permet de le faire.
        """
        texte = "Etat au 01/01/2025 puis arrete au 31/12/2025, edite ensuite"
        lecture = lire_date(texte)
        self.assertEqual(SOURCE_AMBIGU, lecture["source"])
        self.assertEqual("", lecture["valeur"])
        self.assertGreaterEqual(len(lecture["candidats"]), 2)

    def test_le_nom_du_fichier_corrobore_mais_n_impose_pas(self) -> None:
        """La corroboration departage; elle n'ajoute jamais une valeur absente.

        Mesure du 2026-09-09: sans cette regle, cinq documents dont le nom
        portait la reponse etaient rendus vides parce que leur texte hesitait.
        Avec une regle plus lache - corroborer sur le seul mois - le troc
        devenait defavorable, et une date fausse coute plus cher qu'une absence.
        """
        texte = "Etat au 01/01/2025 puis arrete au 31/12/2025"
        self.assertEqual("2025-12-31", lire_date(texte, "2025-12-31_etat.pdf")["valeur"])
        # Un nom qui ne designe aucun candidat ne gagne pas: le desaccord tient.
        self.assertEqual(SOURCE_AMBIGU, lire_date(texte, "2026-07-04_etat.pdf")["source"])

    def test_une_annee_a_deux_chiffres_est_refusee_et_non_devinee(self) -> None:
        """Tout pivot de siecle est une modalite: `10/07/65` n'est pas 2065."""
        self.assertEqual("", lire_date("la loi du 10/07/65 dispose")["valeur"])

    def test_les_ecartes_sont_comptes_et_rendus(self) -> None:
        """Le comptage tient lieu de garde sur les deux vocabulaires.

        Le jour ou un cabinet numerote autrement, le signal attendu est une
        hausse des documents sans candidat - jamais une date fausse en silence.
        """
        lecture = lire_date("decret n 2012-1115 du 2 octobre 2012\nle 13 avril 2026")
        self.assertIn(ROLE_ACTE_CITE, lecture["role_ecartes"])
        self.assertGreaterEqual(lecture["role_ecartes"][ROLE_ACTE_CITE], 1)

    def test_l_hypothese_d_ordre_est_declaree_quand_rien_ne_tranche(self) -> None:
        """6 269 occurrences prouvent le jour en premier, 0 l'inverse.

        Restent 107 documents ou aucune date ne depasse 12: la convention s'y
        applique, et la lecture doit DIRE que c'en est une.
        """
        lecture = lire_date("facture du 05/04/2026")
        self.assertTrue(any("jour/mois" in h for h in lecture["hypotheses"]))

    def test_un_champ_superieur_a_douze_tranche_l_ordre_par_l_arithmetique(self) -> None:
        candidats = candidats_du_texte(normalise("facture du 23/06/2026"))
        self.assertEqual("jma", ordre_du_document(candidats))

    def test_une_date_impossible_est_refusee_par_le_calendrier(self) -> None:
        self.assertEqual("", lire_date("le 31/02/2025 il ne s'est rien passe")["valeur"])

    def test_la_lecture_rend_toujours_les_memes_cles(self) -> None:
        for texte in ("", "rien du tout", "le 23/06/2026"):
            lecture = lire_date(texte, "x.pdf")
            for cle in ("valeur", "source", "chaine", "granularite", "role_ecartes",
                        "hypotheses", "candidats"):
                self.assertIn(cle, lecture, texte)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
