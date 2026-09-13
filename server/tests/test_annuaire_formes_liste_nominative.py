from __future__ import annotations

import unittest

from coproscope.modules import biffageops


"""Ce que `lit_liste_nominative` voit, quelle que soit la mise en page.

**Ce fichier a change de sens le 2026-09-07, et c'est la bonne nouvelle qu'il
annoncait.** Il figeait un defaut connu, `RM-2026-0097`: cinq mises en page sur
sept rendaient zero personne, en silence. Son message d'echec disait qu'un
echec signifierait que le defaut est repare. C'est arrive: les sept rendent
maintenant 4/4, et ce fichier assure desormais la non-regression.

**L'axe**: la maniere dont une liste nominative distribue le numero de compte,
le nom et le montant sur des lignes est un degre de liberte.
**L'invariant**: les trois se suivent dans cet ordre, quel que soit le nombre de
sauts de ligne entre eux.

Donnees entierement fictives: quatre personnes inventees.
"""


ATTENDU = 4

TROIS_LIGNES = """
ANNEXE DES SOLDES

101234
MARCHAND ETIENNE
1 240,50
101235
VALLIOT CLEMENCE
-320,00
101236
NOIRET BASTIEN
0,00
101237
LEGRAND SOPHIE
2 015,75
"""

TROIS_LIGNES_EURO = TROIS_LIGNES.replace(",50", ",50 €").replace(",00", ",00 €").replace(",75", ",75 €")

UNE_LIGNE = """
ANNEXE DES SOLDES

101234  MARCHAND ETIENNE        1 240,50
101235  VALLIOT CLEMENCE         -320,00
101236  NOIRET BASTIEN               0,00
101237  LEGRAND SOPHIE          2 015,75
"""

TABLE_BARRES = """
| Compte | Nom | Solde |
|---|---|---|
| 101234 | MARCHAND ETIENNE | 1 240,50 |
| 101235 | VALLIOT CLEMENCE | -320,00 |
| 101236 | NOIRET BASTIEN | 0,00 |
| 101237 | LEGRAND SOPHIE | 2 015,75 |
"""

DEUX_LIGNES = """
ANNEXE DES SOLDES

101234 MARCHAND ETIENNE
1 240,50
101235 VALLIOT CLEMENCE
-320,00
101236 NOIRET BASTIEN
0,00
101237 LEGRAND SOPHIE
2 015,75
"""

CASSE_MIXTE = """
101234
Marchand Etienne
1 240,50
101235
Valliot Clemence
-320,00
101236
Noiret Bastien
0,00
101237
Legrand Sophie
2 015,75
"""

COMPTE_COURT = """
1234
MARCHAND ETIENNE
1 240,50
1235
VALLIOT CLEMENCE
-320,00
1236
NOIRET BASTIEN
0,00
1237
LEGRAND SOPHIE
2 015,75
"""

TOUTES_LES_FORMES = (
    ("trois lignes: compte / NOM / montant", TROIS_LIGNES),
    ("trois lignes, montant avec symbole euro", TROIS_LIGNES_EURO),
    ("une seule ligne: compte NOM montant", UNE_LIGNE),
    ("table a barres verticales", TABLE_BARRES),
    ("deux lignes: compte NOM puis montant", DEUX_LIGNES),
    ("trois lignes, nom en casse mixte", CASSE_MIXTE),
    ("trois lignes, compte a quatre chiffres", COMPTE_COURT),
)


class FormesDeListeNominative(unittest.TestCase):
    def test_toutes_les_mises_en_page_rendent_les_quatre_personnes(self) -> None:
        for etiquette, texte in TOUTES_LES_FORMES:
            with self.subTest(forme=etiquette):
                resultat = biffageops.lit_liste_nominative(texte)
                self.assertEqual(resultat["statut"], biffageops.STATUT_LISTE_TROUVEE)
                self.assertEqual(
                    len(resultat["entrees"]),
                    ATTENDU,
                    f"La mise en page `{etiquette}` a cesse d'etre lue. Un annuaire vide "
                    "fait retomber tout le caviardage sur les regles generiques, sans que "
                    "rien ne le signale.",
                )

    def test_le_compte_et_le_nom_sont_apparies(self) -> None:
        entrees = dict(biffageops.extrait_entrees_annuaire(UNE_LIGNE))
        self.assertEqual(entrees.get("101234"), "MARCHAND ETIENNE")
        self.assertEqual(entrees.get("101237"), "LEGRAND SOPHIE")

    def test_une_absence_de_liste_se_distingue_d_une_liste_illisible(self) -> None:
        """Le coeur du defaut d'origine: les deux rendaient la meme liste vide.

        La gate d'absorption ne pouvait donc pas reclamer la bonne piece: elle
        ne savait pas laquelle des deux situations elle voyait.
        """

        sans_liste = "PROCES-VERBAL DE L'ASSEMBLEE GENERALE\nResolution n 1 - Approbation des comptes.\n"
        absente = biffageops.lit_liste_nominative(sans_liste)
        self.assertEqual(absente["statut"], biffageops.STATUT_LISTE_ABSENTE)

        illisible = biffageops.lit_liste_nominative(
            "101234\n1 240,50\n101235\n-320,00\n101236\n0,00\n"
        )
        self.assertEqual(illisible["statut"], biffageops.STATUT_LISTE_ILLISIBLE)
        self.assertTrue(str(illisible["motif"]).strip(), "un statut illisible doit dire pourquoi")
        self.assertNotEqual(absente["statut"], illisible["statut"])

    def test_un_poste_de_depense_ne_passe_pas_pour_une_personne(self) -> None:
        """L'ancrage par le compte est ce qui protege de ce faux positif.

        `- EAU ARROSAGE` suivi de son montant ressemble a un nom suivi d'un
        solde. Ce qui l'en distingue est l'absence d'identifiant de compte
        devant lui.
        """

        etat_des_depenses = """
ETAT DES DEPENSES
- EAU ARROSAGE
1 240,50
- ENTRETIEN ESPACES VERTS
2 015,75
"""
        resultat = biffageops.lit_liste_nominative(etat_des_depenses)
        self.assertEqual(resultat["entrees"], [])
        self.assertEqual(resultat["statut"], biffageops.STATUT_LISTE_ABSENTE)


if __name__ == "__main__":
    unittest.main()
