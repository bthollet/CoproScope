from __future__ import annotations

import unittest

from coproscope.core.colonnes_nominatives import colonnes_nominatives, noms_en_colonne
from coproscope.modules import biffageops


"""`RM-2026-0068` - une liste de coproprietaires nommes avec leur solde.

Ce module garde une propriete et une seule: **la maniere dont un extracteur rend
les cellules d'un tableau est un degre de liberte, pas une modalite a enumerer.**

Le tableau ci-dessous est synthetique et ses noms sont inventes. Les huit
fonctions qui suivent en produisent HUIT RENDUS: meme table, meme information,
memes six personnes, seule change la mise en page du texte extrait. Le test
exige les six dans les huit.

**Ce qu'il refuse, mesure du 2026-09-09 sur la base `913d744`:** avant ce lot,
six de ces huit rendus donnaient **0 nom sur 6, en silence**. Les deux regles
qui existaient - `liste_nominative` et `ligne_montant` - avaient ete ecrites sur
ce qu'un seul cabinet avait rendu. Sur le second cabinet du poste, elles
rendaient **zero sur 487 identites detectees**.
"""


#: Personnes inventees. Aucune ne designe quiconque.
TABLE = (
    ("45000001", "MERCADIER JEROME", "2 061,89"),
    ("45000002", "VANDERSTOCKE SOPHIE", "451,17"),
    ("45000003", "DELAVIGNE-PERRIN CLAIRE", "29,44"),
    ("45000004", "ESCOFFIER MATHIAS", "1 204,00"),
    ("45000005", "BOURRINET ADELINE", "88,10"),
    ("45000006", "GRANDCHAMP OLIVIER", "3 917,45"),
)

ENTETE = "ETAT DES SOLDES DES COPROPRIETAIRES\nANNEXE N 1\nCompte\nCoproprietaire\nSolde\n"

FAMILLES = tuple(nom.split()[0] for _, nom, _ in TABLE)


def _cellule_par_ligne() -> str:
    """Un rang eclate en une ligne par cellule. Le seul rendu observe jusqu'ici."""

    return ENTETE + "".join("%s\n%s\n%s\n" % rang for rang in TABLE)


def _rang_sur_une_ligne_compte_devant() -> str:
    """Un rang par ligne, numero de compte en tete - la lecture naturelle."""

    return ENTETE + "".join("%s   %s   %s\n" % rang for rang in TABLE)


def _rang_sur_une_ligne_nom_devant() -> str:
    """Un rang par ligne, sans colonne de compte."""

    return ENTETE + "".join("%s   %s\n" % (nom, montant) for _, nom, montant in TABLE)


def _cellules_separees_par_barres() -> str:
    """Table docx ou xlsx: le lecteur du depot joint les cellules par ` | `."""

    return ENTETE + "".join("%s | %s | %s\n" % rang for rang in TABLE)


def _compte_alphanumerique() -> str:
    """Meme mise en page que le rendu observe, compte non purement numerique."""

    return ENTETE + "".join(
        "450-%s\n%s\n%s\n" % (compte[-4:], nom, montant) for compte, nom, montant in TABLE
    )


def _ordre_colonne() -> str:
    """Extracteur colonne par colonne: tous les comptes, tous les noms, tous les soldes."""

    return (
        ENTETE
        + "".join("%s\n" % compte for compte, _, _ in TABLE)
        + "".join("%s\n" % nom for _, nom, _ in TABLE)
        + "".join("%s\n" % montant for _, _, montant in TABLE)
    )


def _casse_de_titre() -> str:
    """Le syndic n'ecrit pas ses noms en capitales."""

    return ENTETE + "".join(
        "%s\n%s\n%s\n" % (compte, nom.title(), montant) for compte, nom, montant in TABLE
    )


def _sans_colonne_de_compte() -> str:
    """Pas de numero de compte du tout: nom puis solde, une cellule par ligne."""

    return ENTETE + "".join("%s\n%s\n" % (nom, montant) for _, nom, montant in TABLE)


def _tantiemes_entiers() -> str:
    """Feuille de presence: le nom est aligne sur des tantiemes ENTIERS.

    `RM-2026-0068` nomme ce cas autant que celui des soldes: environ 120
    coproprietaires listes avec leurs tantiemes et le sens de leur vote.
    """

    return ENTETE + "".join(
        "%s\n%s\n%d\n" % (compte, nom, 120 + rang * 37)
        for rang, (compte, nom, _) in enumerate(TABLE)
    )


def _rangs_coupes_par_des_sections() -> str:
    """Un intitule de batiment casse la suite des rangs tous les deux noms."""

    morceaux = [ENTETE]
    for rang, (compte, nom, montant) in enumerate(TABLE):
        if rang % 2 == 0:
            morceaux.append("BATIMENT %d\n" % (rang // 2 + 1))
        morceaux.append("%s\n%s\n%s\n" % (compte, nom, montant))
    return "".join(morceaux)


RENDUS = (
    ("cellule par ligne", _cellule_par_ligne),
    ("rang sur une ligne, compte devant", _rang_sur_une_ligne_compte_devant),
    ("rang sur une ligne, nom devant", _rang_sur_une_ligne_nom_devant),
    ("cellules separees par barres", _cellules_separees_par_barres),
    ("compte alphanumerique", _compte_alphanumerique),
    ("ordre colonne", _ordre_colonne),
    ("casse de titre", _casse_de_titre),
    ("sans colonne de compte", _sans_colonne_de_compte),
    ("tantiemes entiers", _tantiemes_entiers),
    ("rangs coupes par des sections", _rangs_coupes_par_des_sections),
)


#: Une table des matieres: intitule d'annexe puis numero de page. Elle a la
#: silhouette d'une liste nominative des que la colonne alignee accepte les
#: entiers, et c'est ce qui est arrive le 2026-09-09 sur le corpus etalon -
#: neuf intitules devenus des personnes.
#:
#: **Chaque intitule ci-dessous n'a QU'UNE SEULE raison d'etre refuse: sa barre
#: oblique.** C'est deliberé, et c'est ce qui manquait a la premiere version de
#: cette fixture: ses intitules contenaient aussi des chiffres et le mot
#: `ANNEXE`, tous deux deja refuses par le lexique. Le controle negatif passait
#: donc au vert en autorisant la barre oblique, et ne prouvait rien.
#: Verifie: `_nom_recevable` accepte ces cinq chaines, `_forme_de_nom` les refuse.
SOMMAIRE = """SOMMAIRE
TOITURE/ZINGUERIE
12
CHAUFFERIE/BRULEUR
18
VENTILATION/EXTRACTION
24
MENUISERIE/SERRURERIE
31
PEINTURE/RAVALEMENT
37
"""

#: Meme construction, seule faute: la cellule ne commence pas par une lettre.
SOMMAIRE_A_PUCES = """SOMMAIRE
- TOITURE ZINGUERIE
12
- CHAUFFERIE BRULEUR
18
- VENTILATION EXTRACTION
24
- MENUISERIE SERRURERIE
31
- PEINTURE RAVALEMENT
37
"""

#: Une colonne d'etiquette: la meme valeur repetee en face de montants
#: differents. Ce n'est pas un annuaire.
ETIQUETTE_REPETEE = """RELEVE
REF
2 010,00
REF
480,55
REF
77,20
REF
1 900,00
REF
33,10
"""


#: Un etat des depenses: meme silhouette qu'une liste nominative - un libelle,
#: un montant, repete - mais les libelles sont du vocabulaire comptable. Le
#: masquer detruirait la piece, et c'est exactement l'incident du 2026-09-03,
#: ou 5 400 etiquettes sur 6 099 recouvraient des mots courants.
DEPENSES = """ETAT DES DEPENSES DE L'EXERCICE
Poste
Montant
ENTRETIEN ASCENSEUR
4 120,00
NETTOYAGE ESCALIER
2 310,55
ASSURANCE IMMEUBLE
7 890,12
HONORAIRES SYNDIC
5 400,00
ELECTRICITE PARTIES COMMUNES
1 233,40
TOTAL GENERAL
20 954,07
"""


class ColonnesNominativesTest(unittest.TestCase):
    """La structure: ce que `core.colonnes_nominatives` sait voir."""

    def _noms(self, texte: str) -> list[str]:
        return noms_en_colonne(texte, biffageops._nom_recevable)

    def test_les_huit_rendus_de_la_meme_table_donnent_les_memes_personnes(self) -> None:
        """L'axe. Un rendu inconnu doit degrader, jamais rendre zero en silence."""

        for libelle, fabrique in RENDUS:
            with self.subTest(rendu=libelle):
                trouves = " ".join(self._noms(fabrique())).upper()
                manquants = [famille for famille in FAMILLES if famille not in trouves]
                self.assertEqual(
                    [],
                    manquants,
                    "rendu '%s': %d personnes sur %d invisibles a la detection "
                    "de colonne nominative (%s). La mise en page des cellules est "
                    "un degre de liberte, pas une modalite."
                    % (libelle, len(manquants), len(FAMILLES), ", ".join(manquants)),
                )

    def test_un_etat_des_depenses_ne_devient_pas_une_liste_de_personnes(self) -> None:
        """L'autre sens de la garde: le vocabulaire comptable survit."""

        self.assertEqual(
            [],
            self._noms(DEPENSES),
            "un etat des depenses a la meme silhouette qu'une liste nominative; "
            "ses libelles ne sont pas des personnes et doivent survivre au caviardage",
        )

    def test_les_fixtures_de_sommaire_n_ont_qu_une_seule_faute(self) -> None:
        """Sans cela, les deux controles negatifs qui suivent ne prouvent rien.

        Le lexique doit ACCEPTER ces cellules: seule la forme les refuse. Une
        fixture refusee deux fois passerait au vert sous mutation.
        """

        for cellule in ("TOITURE/ZINGUERIE", "- TOITURE ZINGUERIE"):
            with self.subTest(cellule=cellule):
                self.assertTrue(
                    biffageops._nom_recevable(cellule),
                    "le lexique refuse deja cette cellule: le controle negatif "
                    "de la forme serait creux",
                )

    def test_un_sommaire_ne_devient_pas_une_liste_de_personnes(self) -> None:
        """Le faux positif reellement mesure sur le corpus etalon."""

        self.assertEqual(
            [],
            self._noms(SOMMAIRE),
            "une table des matieres a la silhouette d'une liste nominative; "
            "un intitule portant une barre oblique n'est pas un patronyme",
        )

    def test_une_cellule_a_puce_n_est_pas_un_nom(self) -> None:
        """Un patronyme ne commence pas par un tiret de liste."""

        self.assertEqual([], self._noms(SOMMAIRE_A_PUCES))

    def test_une_etiquette_repetee_n_est_pas_un_annuaire(self) -> None:
        """Un annuaire nomme des gens differents."""

        self.assertEqual([], self._noms(ETIQUETTE_REPETEE))

    def test_une_repetition_trop_courte_n_est_pas_une_colonne(self) -> None:
        """Deux rangs sont une coincidence, pas une colonne."""

        court = ENTETE + "".join("%s\n%s\n%s\n" % rang for rang in TABLE[:2])
        self.assertEqual([], self._noms(court))

    def test_la_colonne_declare_sa_preuve(self) -> None:
        """Une detection sans sa preuve structurelle n'est pas verifiable."""

        colonnes = colonnes_nominatives(_cellule_par_ligne(), biffageops._nom_recevable)
        self.assertTrue(colonnes)
        couvrantes = [
            colonne
            for colonne in colonnes
            if all(
                famille in " ".join(colonne.valeurs).upper() for famille in FAMILLES
            )
        ]
        self.assertTrue(couvrantes, "aucune colonne ne couvre la table entiere")
        colonne = couvrantes[0]
        self.assertIn(colonne.lecture, {"rang", "colonne"})
        self.assertIn(colonne.periode, (1, 2, 3, 4))
        self.assertGreaterEqual(colonne.rangs, 4)
        self.assertTrue(colonne.motif.startswith("colonne_nominative:"))


class DetecteIdentitesTest(unittest.TestCase):
    """Le branchement: ce que la chaine de caviardage recoit vraiment."""

    def _personnes(self, texte: str) -> list[str]:
        return [
            candidat.valeur.upper()
            for candidat in biffageops.detecte_identites(texte)
            if candidat.categorie == "PERSONNE"
        ]

    def test_chaque_rendu_atteint_la_chaine_de_caviardage(self) -> None:
        for libelle, fabrique in RENDUS:
            with self.subTest(rendu=libelle):
                trouves = " ".join(self._personnes(fabrique()))
                manquants = [famille for famille in FAMILLES if famille not in trouves]
                self.assertEqual(
                    [],
                    manquants,
                    "rendu '%s': %s n'arrive pas jusqu'a detecte_identites"
                    % (libelle, ", ".join(manquants)),
                )

    def test_le_vocabulaire_comptable_ne_devient_pas_une_identite(self) -> None:
        personnes = self._personnes(DEPENSES)
        self.assertEqual([], personnes, "le caviardage mangerait l'etat des depenses")


if __name__ == "__main__":
    unittest.main()
