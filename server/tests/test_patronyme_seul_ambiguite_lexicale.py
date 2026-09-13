"""La forme `patronyme seul` se decide sur l'ambiguite, pas sur la longueur.

`RM-2026-0065`. La branche `patronyme seul` de `applique_annuaire` etait gardee
par `len(cle) < 4 or cle in VOCABULAIRE_PROTEGE`. Les deux clauses codaient des
modalites sur des dimensions sans rapport avec le risque.

**Ce que ces tests gardent, et ce qu'ils ne gardent pas.** Ils portent sur les
personnes DEJA connues de l'annuaire - celles qu'une liste nominative a fait
entrer avec un numero de compte. Les personnes qui n'entrent jamais dans
l'annuaire relevent de `RM-2026-0068`, et la boucle humaine qui tranchera les
formes ambigues une fois pour toutes releve de `RM-2026-0099`: ici la machine ne
tranche pas, elle refuse et le dit.

Les valeurs employees sont fictives. La mesure qui a fonde la regle a ete faite
sur le corpus etalon de `RM-2026-0050`, hors depot.
"""

from __future__ import annotations

import unittest

from coproscope.modules.biffageops import (
    VOCABULAIRE_PROTEGE,
    applique_annuaire,
    forme_ambigue_avec_le_lexique,
    formes_seules_retenues,
    mots_en_bas_de_casse,
    vocabulaire_bas_de_casse_corpus,
)


def entree(nom: str, prenom: str = "", racine: str = "CEDRE") -> dict[str, str]:
    return {
        "alias": f"PERSONNE_{racine}" + (f"_BLEU" if prenom else ""),
        "racine": racine,
        "nom_source": nom,
        "prenom_source": prenom,
        "nom_normalise": nom.upper(),
        "prenom_normalise": prenom.upper(),
    }


class PatronymeCourtMasque(unittest.TestCase):
    """Le rappel: un patronyme court n'est plus saute a cause de sa longueur."""

    def test_un_patronyme_de_trois_lettres_est_masque(self) -> None:
        # `ROY` fait trois caracteres: l'ancienne garde `len(cle) < 4` sautait
        # la forme seule et laissait le nom EN CLAIR partout ou il paraissait
        # sans son prenom.
        texte = "Le lot 12 appartient a ROY.\nROY conteste la repartition.\n"
        sortie, compteurs = applique_annuaire(texte, [entree("ROY", "Camille")])
        self.assertNotIn("ROY", sortie)
        self.assertEqual(sum(compteurs.values()), 2)

    def test_la_longueur_ne_decide_pas(self) -> None:
        """Court et long se comportent pareil quand ni l'un ni l'autre n'est ambigu."""

        for nom in ("ROY", "BEC", "VERNAZOUX"):
            with self.subTest(nom=nom):
                texte = f"Convocation adressee a {nom}.\n"
                sortie, _compteurs = applique_annuaire(texte, [entree(nom)])
                self.assertNotIn(nom, sortie)


class PatronymeAmbiguAvecLeLexique(unittest.TestCase):
    """La precision: un mot courant n'est pas remplace parce qu'il est un nom."""

    def test_un_patronyme_qui_est_aussi_un_mot_courant_n_est_pas_applique(self) -> None:
        # Un coproprietaire nomme PETIT ne doit pas faire disparaitre le mot
        # `petit` de la prose: le derive cesserait d'etre analysable.
        texte = (
            "PETIT demande la parole.\n"
            "Le petit local technique reste en indivision.\n"
        )
        sortie, _compteurs = applique_annuaire(texte, [entree("PETIT")])
        self.assertIn("petit local technique", sortie)
        self.assertIn("PETIT demande", sortie)

    def test_la_casse_de_l_occurrence_est_le_signal(self) -> None:
        bas = mots_en_bas_de_casse("le petit local et le grand hall")
        self.assertTrue(forme_ambigue_avec_le_lexique("PETIT", bas))
        self.assertFalse(forme_ambigue_avec_le_lexique("VERNAZOUX", bas))

    def test_une_forme_a_particule_se_juge_sur_son_porteur(self) -> None:
        # `de` est toujours en bas de casse; c'est `vernazoux` qui decide.
        bas = mots_en_bas_de_casse("le lot de monsieur, et de vernazoux aussi")
        self.assertTrue(forme_ambigue_avec_le_lexique("DE VERNAZOUX", bas))
        bas_sans = mots_en_bas_de_casse("le lot de monsieur")
        self.assertFalse(forme_ambigue_avec_le_lexique("DE VERNAZOUX", bas_sans))


class LeRefusEstDit(unittest.TestCase):
    """Un refus muet redevient le defaut que ce lot repare."""

    def test_la_forme_retenue_remonte_avec_ses_occurrences_en_clair(self) -> None:
        texte = (
            "PETIT demande la parole.\n"
            "PETIT quitte la seance.\n"
            "Le petit local technique reste en indivision.\n"
        )
        retenues = formes_seules_retenues(texte, [entree("PETIT")])
        self.assertEqual(retenues, {"PETIT": 2})

    def test_les_occurrences_en_bas_de_casse_ne_sont_pas_comptees(self) -> None:
        # Ce sont justement celles dont on affirme qu'elles ne designent
        # personne: les compter gonflerait la file d'un bruit qu'on a choisi.
        texte = "Le petit local, le petit hall, le petit garage.\n"
        self.assertEqual(formes_seules_retenues(texte, [entree("PETIT")]), {})

    def test_un_patronyme_applique_ne_remonte_pas(self) -> None:
        texte = "ROY conteste la repartition.\n"
        self.assertEqual(formes_seules_retenues(texte, [entree("ROY")]), {})


class DegradationHorsDesValeursObservees(unittest.TestCase):
    """Le test d'acceptation de la doctrine: le silence est le seul echec."""

    def test_une_piece_toute_en_capitales_masque_au_lieu_de_se_taire(self) -> None:
        # Aucune prose, donc aucune contre-preuve. Le sens sur est de masquer.
        texte = "CONVOCATION ASSEMBLEE GENERALE\nLOT 12 - CHARBONNIER\n"
        sortie, compteurs = applique_annuaire(texte, [entree("CHARBONNIER")])
        self.assertNotIn("CHARBONNIER", sortie)
        self.assertEqual(sum(compteurs.values()), 1)

    def test_un_patronyme_vu_en_bas_de_casse_part_en_arbitrage_pas_au_silence(self) -> None:
        # Le cas defavorable: un vrai patronyme ecrit en bas de casse ailleurs -
        # un index, une adresse electronique - est juge ambigu. Il n'est pas
        # masque, MAIS il est nomme: c'est ce qui distingue ce comportement de
        # l'ancien `continue`.
        texte = "CHARBONNIER preside.\ncontact: jean.charbonnier arobase exemple\n"
        sortie, _compteurs = applique_annuaire(texte, [entree("CHARBONNIER")])
        self.assertIn("CHARBONNIER preside", sortie)
        self.assertEqual(
            formes_seules_retenues(texte, [entree("CHARBONNIER")]),
            {"CHARBONNIER": 1},
        )

    def test_un_troisieme_cabinet_avec_un_patronyme_inconnu_ne_repond_pas_faux(self) -> None:
        """La regle ne connait aucune liste de noms: elle lit la piece."""

        for nom in ("NGUYEN", "EL ORFA", "O'DWYER", "VAN DEN BERG", "LI"):
            with self.subTest(nom=nom):
                texte = f"Le lot 3 appartient a {nom}, present.\n"
                sortie, compteurs = applique_annuaire(texte, [entree(nom)])
                self.assertNotIn(nom, sortie, f"{nom} est reste en clair")
                self.assertEqual(sum(compteurs.values()), 1)


class LaPorteeEstLeCorpusPasLaPiece(unittest.TestCase):
    """La piece ou le mot se lit en minuscules n'est pas celle ou l'on tranche.

    Mesure du 2026-09-09: juge piece par piece, le test masquait quand meme 88
    occurrences de trois intitules courants, parce que les pieces ou ils
    paraissent sont des tables tout en capitales.
    """

    def test_une_table_en_capitales_seule_ne_sait_pas(self) -> None:
        table = "TABLEAU\nCOMPTE 004 CHARBONNIER\nCOMPTE 005 PETIT\n"
        sortie, _compteurs = applique_annuaire(table, [entree("PETIT")])
        self.assertNotIn("PETIT", sortie)

    def test_la_prose_d_une_AUTRE_piece_suffit_a_lever_le_doute(self) -> None:
        table = "TABLEAU\nCOMPTE 004 CHARBONNIER\nCOMPTE 005 PETIT\n"
        prose = "Le petit local technique reste en indivision.\n"
        corpus = vocabulaire_bas_de_casse_corpus({"D1": table, "D2": prose})
        sortie, _compteurs = applique_annuaire(
            table, [entree("PETIT")], bas_de_casse_corpus=corpus
        )
        self.assertIn("PETIT", sortie)
        self.assertEqual(
            formes_seules_retenues(table, [entree("PETIT")], bas_de_casse_corpus=corpus),
            {"PETIT": 1},
        )

    def test_un_vrai_patronyme_reste_masque_avec_la_portee_corpus(self) -> None:
        table = "TABLEAU\nCOMPTE 004 CHARBONNIER\n"
        prose = "Le petit local technique reste en indivision.\n"
        corpus = vocabulaire_bas_de_casse_corpus({"D1": table, "D2": prose})
        sortie, _compteurs = applique_annuaire(
            table, [entree("CHARBONNIER")], bas_de_casse_corpus=corpus
        )
        self.assertNotIn("CHARBONNIER", sortie)


class LeReleveEstUnSurEnsemble(unittest.TestCase):
    """Si l'apparieur peut trouver la forme en bas de casse, le releve la porte.

    Une premiere version ne tenait pas cette propriete, et la mesure l'a
    attrapee: `_motif_forme` accepte une apostrophe ou un trait d'union juste
    avant la forme, donc `l'annee` porte pour lui une occurrence de `annee`.
    Une forme jugee non ambigue a tort est masquee a tort.
    """

    def test_une_forme_collee_derriere_une_apostrophe_est_relevee(self) -> None:
        mots = mots_en_bas_de_casse("le solde de l'annee est arrete")
        self.assertIn("annee", mots)

    def test_une_forme_collee_derriere_un_trait_d_union_est_relevee(self) -> None:
        mots = mots_en_bas_de_casse("le lot sud-roy est vendu")
        self.assertIn("roy", mots)

    def test_ce_que_l_apparieur_trouve_le_releve_le_contient(self) -> None:
        # La propriete elle-meme, jouee sur les deux graphies qui l'avaient
        # mise en defaut.
        for texte, forme in (("l'annee ecoulee", "ANNEE"), ("sud-roy", "ROY")):
            with self.subTest(texte=texte):
                sortie, _compteurs = applique_annuaire(texte, [entree(forme)])
                self.assertEqual(sortie, texte, "la forme a ete masquee a tort")

    def test_une_lettre_hors_de_la_plage_ascii_est_jugee_sur_sa_casse(self) -> None:
        # Le texte est replie, pas reduit a l'ASCII. Une plage `a-z` laissait
        # passer les lettres qui n'y sont pas.
        self.assertIn("cœur", mots_en_bas_de_casse("le cœur de l'immeuble"))
        self.assertNotIn("CŒUR", mots_en_bas_de_casse("LE CŒUR DE L'IMMEUBLE"))


class LeVocabulaireProtegeNEstPlusLeMecanisme(unittest.TestCase):
    """Il reste un filet. Allonger la liste ne repare rien."""

    def test_il_reste_un_filet_pour_une_piece_sans_prose(self) -> None:
        # `SOLDE` est dans la liste: meme sans occurrence en bas de casse, la
        # forme seule n'est pas appliquee.
        self.assertIn("SOLDE", VOCABULAIRE_PROTEGE)
        texte = "TABLEAU DES COMPTES\nSOLDE 1 234,56\n"
        sortie, _compteurs = applique_annuaire(texte, [entree("SOLDE")])
        self.assertIn("SOLDE", sortie)

    def test_il_ne_couvrait_aucun_des_patronymes_ambigus_mesures(self) -> None:
        # Mesure du 2026-09-09 sur le corpus etalon: 0 prise sur 49 patronymes.
        # Ces sept-la sont des patronymes francais courants qui sont aussi des
        # mots communs; aucun n'est dans la liste, et c'est pour cela qu'une
        # liste fermee ne pouvait pas etre la garde.
        for nom in ("PETIT", "ROCHE", "MEUNIER", "BOUCHER", "FONTAINE", "LEROY", "MARTIN"):
            with self.subTest(nom=nom):
                self.assertNotIn(nom, VOCABULAIRE_PROTEGE)


if __name__ == "__main__":
    unittest.main()
