"""Tests de l'extracteur de pieces comptables. Lot `RM-2026-0074`.

**Aucune donnee reelle dans ce fichier.** Les gabarits ci-dessous reproduisent la
STRUCTURE mesuree sur le corpus, avec des montants inventes et des libelles
neutres. C'est la structure qui est l'objet du test; les vrais chiffres sont
mesures hors depot et rapportes dans la note du lot.

Chaque gabarit represente une **modalite d'un axe**, et les tests verifient que
le code depend de l'axe et non de la modalite: deux cabinets qui different sur
le separateur decimal, sur l'ordre des colonnes, sur la place du total et sur la
presence meme d'un etat des depenses doivent tous se lire.
"""

from __future__ import annotations

import unittest
from decimal import Decimal

from coproscope.modules.comptes_extraction import (
    ANNEXE,
    ETAT_DES_DEPENSES,
    INDETERMINEE,
    PieceAssemblee,
    PieceJustificative,
    constats_contre_pieces,
    constats_internes,
    dossier_assemblee,
    dossier_comptable,
    lire_annexe,
    lire_etat_depenses,
    nature_de,
    totaux_de_bloc,
)
from coproscope.modules._comptes_extraction_controles import (
    MONTANT_DISCORDANT_AVEC_PIECE,
    PIECE_SANS_LIGNE,
    TAUX_DISCORDANT_AVEC_PIECE,
    TAXE_SUR_COMPTE_EXONERE,
    TAXE_SUR_PIECE_SANS_TAXE,
)
from coproscope.modules._comptes_extraction_lexique import (
    detecter_separateur_decimal,
    lire_montant,
    normaliser_compte,
    taxe_incluse,
)
from coproscope.modules._comptes_extraction_modele import (
    COURANTES,
    DETAILLE,
    GENERAL,
    SEPARATEUR_INDECIDABLE,
    SYNTHESE,
    TAXE_DISCORDANTE,
    TOTAL_ABSENT,
    TRAVAUX,
    TTC_TAXE_INCLUSE,
)

# Cabinet 1: virgule decimale, quatre colonnes, total general en ligne.
# Les nombres sont choisis pour que la taxe incluse retombe exactement.
ETAT_VIRGULE = """===== PAGE 1 =====
CABINET UN
ETAT DES DEPENSES
Copropriete:
0001
RESIDENCE GABARIT
EXERCICE DU
01/01/2030
AU
31/12/2030
NATURE DES CHARGES
MONTANT A REPARTIR
CHARGES
TAUX
MONTANT
LOCATIVES
TVA
T.V.A.
001
CHARGES GENERALES
601000   POSTE ALPHA
- SOUS POSTE UN
1 200,00
1 200,00
20,00
200,00
- SOUS POSTE DEUX
1 100,00
10,00
100,00
TOTAL POSTE ALPHA. . . . . . . . . . . . . . . . .
2 300,00
1 200,00
300,00
616000   POSTE BETA
- SOUS POSTE TROIS
600,00
20,00
100,00
TOTAL POSTE BETA. . . . . . . . . . . . . . . . . .
600,00
100,00
*** TOTAL CHARGES GENERALES a repartir en 1 000 parts ***
2 900,00
1 200,00
400,00
T O T A L   C H A R G E S   C O U R A N T E S
2 900,00
1 200,00
400,00
E01
ENTREE UN
672000   POSTE GAMMA
- SOUS POSTE QUATRE
440,00
10,00
40,00
TOTAL POSTE GAMMA. . . . . . . . . . . . . . . . .
440,00
40,00
*** TOTAL ENTREE UN a repartir en 100 parts ***
440,00
40,00
TOTAL CHARGES TRAVAUX ET OPERATIONS EXCEPTIONNELLES
440,00
40,00
T O T A L   G E N E R A L
3 340,00
1 200,00
440,00
Edite le
01/01/2031
Page:
1
"""

# Meme structure, mais point decimal, ordre de colonnes different, aucune colonne
# de charges locatives, et total general absent. Aucune de ces differences ne
# doit changer la lecture des lignes.
ETAT_POINT = """===== PAGE 1 =====
CABINET DEUX
ETAT DES DEPENSES
EXERCICE DU
01/01/2030
AU
31/12/2030
001
CHARGES COMMUNES
601   POSTE ALPHA
- SOUS POSTE UN
1 200.00
20.00
200.00
- SOUS POSTE DEUX
1 100.00
10.00
100.00
TOTAL POSTE ALPHA. . . . . . . . . . . . . . . . .
2 300.00
300.00
"""

# Variante detaillee: chaque ligne porte sa date et sa reference de piece.
ETAT_DETAILLE = """===== PAGE 1 =====
CABINET UN
ETAT DES DEPENSES
EXERCICE DU
01/01/2030
AU
31/12/2030
001
CHARGES GENERALES
     601000     POSTE ALPHA
021
SOUS POSTE UN
02/01/30
FA1001
FOURNISSEUR ALPHA / PRESTATION
1 200,00
1 200,00
20,00
200,00
14/02/30
FA1002
FOURNISSEUR BETA / PRESTATION
770,00 T14
770,00
10,00
70,00
TOTAL SOUS POSTE UN. . . . . . . . . . . . . . . .
1 970,00
1 970,00
270,00
--- TOTAL POSTE ALPHA ---
1 970,00
1 970,00
270,00
*** TOTAL CHARGES GENERALES a repartir en 1 000 parts ***
1 970,00
1 970,00
270,00
T O T A L   G E N E R A L
1 970,00
1 970,00
270,00
"""

# Annexe dont les valeurs de total PRECEDENT l'intitule, cinq colonnes.
ANNEXE_VALEURS_AVANT = """===== PAGE 1 =====
Exercice
precedent
approuve
Exercice clos
budget vote
Exercice clos
realise a
approuver
Budget
previsionnel en
cours vote
Budget
previsionnel a
voter
2028
2029
2029
2030
2031
ANNEXE N° 3
Compte de gestion pour operations courantes de l'exercice clos realise (N) du 01/01/2029 au 31/12/2029
601 POSTE ALPHA
1 000,00
1 100,00
1 050,00
1 200,00
1 300,00
Total charges
1 000,00
1 100,00
1 050,00
1 200,00
1 300,00
TOTAL CHARGES NETTES
Provisions coproprietaires
1 100,00
1 100,00
"""

# Meme annexe, valeurs APRES l'intitule, deux colonnes, point decimal.
ANNEXE_VALEURS_APRES = """===== PAGE 1 =====
ANNEXE N° 3
Compte de gestion pour operations courantes du 01/01/2029 au 31/12/2029
2029
2030
601 POSTE ALPHA
 1 000.00
 1 100.00
sous total :
 1 000.00
 1 100.00
TOTAL CHARGES NETTES
 2 000.00
 2 200.00
Provisions coproprietaires
 2 100.00
 2 200.00
"""

# Deux annexes empilees dans un seul fichier, comme chez le second cabinet.
ANNEXES_EMPILEES = (
    "===== PAGE 1 =====\nANNEXE N° 1\nEtat financier apres repartition au 31/12/2029\n"
    " 4 716.35\n 4 716.35\n" + ANNEXE_VALEURS_APRES.split("=====\n", 1)[1]
)


class TestLexique(unittest.TestCase):
    """L'axe du separateur decimal est mesure, jamais suppose."""

    def test_separateur_detecte_dans_les_deux_notations(self) -> None:
        self.assertEqual(detecter_separateur_decimal(["1 200,00", "3,50"]), ",")
        self.assertEqual(detecter_separateur_decimal(["1 200.00", "3.50"]), ".")

    def test_separateur_indecidable_rend_none(self) -> None:
        self.assertIsNone(detecter_separateur_decimal(["POSTE ALPHA", "TOTAL"]))

    def test_la_notation_opposee_est_refusee(self) -> None:
        """Lire `1.234,00` comme un point decimal vaudrait un facteur mille."""
        self.assertEqual(lire_montant("1 234,00", ","), Decimal("1234.00"))
        self.assertIsNone(lire_montant("1 234,00", "."))

    def test_marqueur_de_cle_accole_au_montant(self) -> None:
        self.assertEqual(lire_montant("1 133,00 T14", ","), Decimal("1133.00"))

    def test_taxe_incluse_et_non_ajoutee(self) -> None:
        """1 200,00 au taux de 20 pour cent porte 200,00 de taxe, pas 240,00."""
        self.assertEqual(taxe_incluse(Decimal("1200.00"), Decimal("20")), Decimal("200.00"))

    def test_normalisation_de_compte_garde_trois_chiffres(self) -> None:
        self.assertEqual(normaliser_compte("601000"), "601")
        self.assertEqual(normaliser_compte("700"), "700")


class TestEtatDepenses(unittest.TestCase):
    """La lecture ne depend d'aucune modalite d'un cabinet."""

    def test_totaux_imprimes_du_gabarit_a_virgule(self) -> None:
        etat = lire_etat_depenses(ETAT_VIRGULE)
        self.assertEqual(etat.exercice_debut, "01/01/2030")
        self.assertEqual(etat.exercice_fin, "31/12/2030")
        self.assertEqual(etat.total_general, Decimal("3340.00"))
        self.assertEqual(etat.total(COURANTES).montant_a_repartir, Decimal("2900.00"))
        self.assertEqual(etat.total(TRAVAUX).montant_a_repartir, Decimal("440.00"))

    def test_la_somme_des_lignes_retombe_sur_le_total_imprime(self) -> None:
        """Le seul controle qui prouve qu'aucune ligne n'a ete perdue."""
        etat = lire_etat_depenses(ETAT_VIRGULE)
        somme = sum(ligne.montant_a_repartir for ligne in etat.lignes)
        self.assertEqual(somme, etat.total_general)

    def test_le_total_travaux_a_deux_nombres_rend_la_taxe_pas_le_locatif(self) -> None:
        """Un total a deux nombres est ambigu; il se tranche par recoupement."""
        etat = lire_etat_depenses(ETAT_VIRGULE)
        travaux = etat.total(TRAVAUX)
        self.assertIsNone(travaux.charges_locatives)
        self.assertEqual(travaux.montant_taxe, Decimal("40.00"))

    def test_liaison_a_trois_nombres_sans_colonne_locative(self) -> None:
        """`1 100,00 / 10,00 / 100,00` se lit montant, taux, taxe."""
        etat = lire_etat_depenses(ETAT_VIRGULE)
        ligne = next(l for l in etat.lignes if l.montant_a_repartir == Decimal("1100.00"))
        self.assertIsNone(ligne.charges_locatives)
        self.assertEqual(ligne.taux_taxe, Decimal("10.00"))
        self.assertEqual(ligne.montant_taxe, Decimal("100.00"))

    def test_liaison_a_quatre_nombres_avec_colonne_locative(self) -> None:
        etat = lire_etat_depenses(ETAT_VIRGULE)
        ligne = next(l for l in etat.lignes if l.montant_a_repartir == Decimal("1200.00"))
        self.assertEqual(ligne.charges_locatives, Decimal("1200.00"))
        self.assertEqual(ligne.taux_taxe, Decimal("20.00"))

    def test_le_point_decimal_se_lit_comme_la_virgule(self) -> None:
        """L'axe du separateur ne change rien a la lecture des lignes."""
        etat = lire_etat_depenses(ETAT_POINT)
        self.assertEqual(etat.profil.separateur_decimal, ".")
        montants = [ligne.montant_a_repartir for ligne in etat.lignes]
        self.assertEqual(montants, [Decimal("1200.00"), Decimal("1100.00")])

    def test_total_general_absent_est_dit(self) -> None:
        """L'absence d'un total est un constat, jamais un zero silencieux."""
        etat = lire_etat_depenses(ETAT_POINT)
        self.assertEqual(etat.profil.emplacement_total_general, TOTAL_ABSENT)
        self.assertIsNone(etat.total_general)

    def test_granularite_mesuree_sur_le_contenu(self) -> None:
        self.assertEqual(lire_etat_depenses(ETAT_VIRGULE).profil.granularite, SYNTHESE)
        self.assertEqual(lire_etat_depenses(ETAT_DETAILLE).profil.granularite, DETAILLE)

    def test_reference_de_piece_lue_quand_elle_existe(self) -> None:
        """C'est la colonne qui porte le rapprochement facture vers ligne."""
        etat = lire_etat_depenses(ETAT_DETAILLE)
        self.assertTrue(etat.profil.reference_piece_presente)
        self.assertEqual(
            sorted(ligne.reference_piece for ligne in etat.lignes),
            ["FA1001", "FA1002"],
        )

    def test_convention_du_montant_etablie_par_preuve(self) -> None:
        etat = lire_etat_depenses(ETAT_VIRGULE)
        self.assertEqual(etat.profil.convention_montant, TTC_TAXE_INCLUSE)

    def test_marqueur_de_cle_conserve(self) -> None:
        etat = lire_etat_depenses(ETAT_DETAILLE)
        self.assertIn("T14", etat.profil.marqueurs_de_cle_observes)

    def test_separateur_indecidable_arrete_la_lecture(self) -> None:
        etat = lire_etat_depenses("ETAT DES DEPENSES\nPOSTE ALPHA\nTOTAL")
        self.assertEqual([c.code for c in etat.constats], [SEPARATEUR_INDECIDABLE])
        self.assertEqual(etat.lignes, ())

    def test_taxe_discordante_conserve_les_deux_valeurs(self) -> None:
        """Un ecart est expose, jamais corrige."""
        texte = ETAT_VIRGULE.replace("- SOUS POSTE TROIS\n600,00\n20,00\n100,00", "- SOUS POSTE TROIS\n600,00\n20,00\n123,00")
        etat = lire_etat_depenses(texte)
        discordances = [c for c in etat.constats if c.code == TAXE_DISCORDANTE]
        self.assertEqual(len(discordances), 1)
        self.assertEqual(discordances[0].valeur_document, "123.00")
        self.assertEqual(discordances[0].valeur_calculee, "100.00")


class TestTotauxDeBloc(unittest.TestCase):
    def test_les_trois_totaux_sont_lus(self) -> None:
        totaux = totaux_de_bloc(lire_etat_depenses(ETAT_VIRGULE))
        self.assertEqual(totaux["general"], Decimal("3340.00"))
        self.assertEqual(totaux["courantes"], Decimal("2900.00"))
        self.assertFalse(totaux["courantes_deduite"])

    def test_le_total_courantes_absent_est_deduit_et_signale_comme_tel(self) -> None:
        """Un cabinet ne l'imprime pas sur tous les exercices. Il se deduit."""
        texte = ETAT_VIRGULE.replace(
            "T O T A L   C H A R G E S   C O U R A N T E S\n2 900,00\n1 200,00\n400,00\n",
            "",
        )
        totaux = totaux_de_bloc(lire_etat_depenses(texte))
        self.assertEqual(totaux["courantes"], Decimal("2900.00"))
        self.assertTrue(totaux["courantes_deduite"])


class TestControles(unittest.TestCase):
    """Les trois ecarts du corpus, et par quelle voie chacun se voit."""

    def test_taxe_sur_compte_exonere_vue_sur_le_seul_etat(self) -> None:
        """Une prime d'assurance ne supporte pas de taxe sur la valeur ajoutee.

        Le compte est reconnu par son NUMERO. Un cabinet qui l'intitulerait
        autrement serait quand meme attrape.
        """
        constats = constats_internes(lire_etat_depenses(ETAT_VIRGULE))
        codes = [c.code for c in constats]
        self.assertIn(TAXE_SUR_COMPTE_EXONERE, codes)
        trouve = next(c for c in constats if c.code == TAXE_SUR_COMPTE_EXONERE)
        self.assertEqual(trouve.compte, "616000")

    def test_taux_discordant_invisible_sans_la_piece(self) -> None:
        """La ligne est coherente avec elle-meme: seule la piece revele l'ecart."""
        etat = lire_etat_depenses(ETAT_DETAILLE)
        self.assertNotIn(
            TAUX_DISCORDANT_AVEC_PIECE, [c.code for c in constats_internes(etat)]
        )
        pieces = {"FA1001": PieceJustificative("FA1001", taux=Decimal("10.00"))}
        constats = constats_contre_pieces(etat, pieces)
        self.assertEqual([c.code for c in constats], [TAUX_DISCORDANT_AVEC_PIECE])
        self.assertEqual(constats[0].valeur_document, "20.00")
        self.assertEqual(constats[0].valeur_calculee, "10.00")

    def test_taxe_sur_piece_qui_declare_ne_pas_en_porter(self) -> None:
        etat = lire_etat_depenses(ETAT_DETAILLE)
        pieces = {"FA1001": PieceJustificative("FA1001", taxe_non_applicable=True)}
        constats = constats_contre_pieces(etat, pieces)
        self.assertEqual([c.code for c in constats], [TAXE_SUR_PIECE_SANS_TAXE])

    def test_montant_discordant_expose_les_deux_valeurs(self) -> None:
        etat = lire_etat_depenses(ETAT_DETAILLE)
        pieces = {"FA1001": PieceJustificative("FA1001", total=Decimal("1000.00"))}
        constats = constats_contre_pieces(etat, pieces)
        self.assertEqual([c.code for c in constats], [MONTANT_DISCORDANT_AVEC_PIECE])
        self.assertEqual(constats[0].valeur_document, "1200.00")

    def test_piece_sans_ligne_correspondante(self) -> None:
        """Une facture d'un autre exercice n'a pas de ligne, et cela se dit."""
        etat = lire_etat_depenses(ETAT_DETAILLE)
        pieces = {"FA9999": PieceJustificative("FA9999", total=Decimal("500.00"))}
        constats = constats_contre_pieces(etat, pieces)
        self.assertEqual([c.code for c in constats], [PIECE_SANS_LIGNE])

    def test_le_silence_n_est_pas_une_conformite(self) -> None:
        """Une reference inconnue ne produit aucun constat sur la ligne."""
        etat = lire_etat_depenses(ETAT_DETAILLE)
        self.assertEqual(constats_contre_pieces(etat, {}), ())


class TestAnnexe(unittest.TestCase):
    """Les valeurs du total tombent des deux cotes de l'intitule, selon le cabinet."""

    def test_valeurs_avant_l_intitule(self) -> None:
        annexe = lire_annexe(ANNEXE_VALEURS_AVANT)
        self.assertEqual(annexe.numero, "3")
        self.assertEqual(annexe.exercice_fin, "31/12/2029")
        self.assertEqual(len(annexe.colonnes), 5)
        self.assertEqual(
            annexe.total_charges_par_colonne,
            (
                Decimal("1000.00"),
                Decimal("1100.00"),
                Decimal("1050.00"),
                Decimal("1200.00"),
                Decimal("1300.00"),
            ),
        )

    def test_valeurs_apres_l_intitule_et_point_decimal(self) -> None:
        annexe = lire_annexe(ANNEXE_VALEURS_APRES)
        self.assertEqual(annexe.profil.separateur_decimal, ".")
        self.assertEqual(
            annexe.total_charges_par_colonne,
            (Decimal("2000.00"), Decimal("2200.00")),
        )

    def test_les_millesimes_repetes_ne_sont_pas_dedupliques(self) -> None:
        """Deux colonnes portent 2029: le budget vote et le realise."""
        annexe = lire_annexe(ANNEXE_VALEURS_AVANT)
        self.assertEqual([c.exercice for c in annexe.colonnes][:3], ["2028", "2029", "2029"])


class TestDossierParAssemblee(unittest.TestCase):
    """Le contrat d'entree est par assemblee, pas par document."""

    def test_pieces_eclatees_en_plusieurs_fichiers(self) -> None:
        pieces = [
            PieceAssemblee("P-01", ETAT_VIRGULE),
            PieceAssemblee("P-02", ANNEXE_VALEURS_AVANT),
        ]
        lu = dossier_comptable(pieces)
        self.assertEqual(len(lu.etats), 1)
        self.assertEqual(len(lu.annexes), 1)

    def test_plusieurs_annexes_dans_un_seul_fichier(self) -> None:
        """Le second cabinet mesure les empile toutes dans un unique fichier."""
        lu = dossier_comptable([PieceAssemblee("Q-01", ANNEXES_EMPILEES)])
        self.assertEqual([a.numero for a in lu.annexes], ["1", "3"])

    def test_nature_lue_sur_le_contenu_jamais_sur_le_nom(self) -> None:
        self.assertEqual(nature_de(ETAT_VIRGULE), ETAT_DES_DEPENSES)
        self.assertEqual(nature_de(ANNEXE_VALEURS_AVANT), ANNEXE)
        self.assertEqual(nature_de("Registre d'avancement interne"), INDETERMINEE)

    def test_piece_non_reconnue_sort_au_lieu_de_disparaitre(self) -> None:
        lu = dossier_comptable([PieceAssemblee("P-99", "Note de travail interne")])
        self.assertEqual(lu.sans_nature, ("P-99",))

    def test_dossier_remplit_le_contrat_du_module_budget(self) -> None:
        dossier, lu = dossier_assemblee(
            [
                PieceAssemblee("P-01", ETAT_VIRGULE),
                PieceAssemblee("P-02", ANNEXE_VALEURS_AVANT),
            ],
            exercice_du_vote="31/12/2029",
        )
        self.assertEqual(
            dossier.annexes.total_charges_annexe3_courantes, Decimal("1300.00")
        )
        self.assertEqual(dossier.reference, "31/12/2029")

    def test_ce_qui_manque_reste_a_none_et_ne_devient_pas_zero(self) -> None:
        """Un controle prive de son entree doit rendre INAPPLICABLE, pas CONFORME."""
        dossier, _ = dossier_assemblee([PieceAssemblee("P-01", ETAT_VIRGULE)])
        self.assertIsNone(dossier.annexes.total_charges_annexe2_courantes)
        self.assertIsNone(dossier.annexes.total_charges_annexe3_courantes)
        self.assertIsNone(dossier.budget.total_charges)

    def test_constats_rattaches_a_la_piece(self) -> None:
        lu = dossier_comptable([PieceAssemblee("P-01", ETAT_VIRGULE)])
        self.assertTrue(all(c.reference_piece for c in lu.constats))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
