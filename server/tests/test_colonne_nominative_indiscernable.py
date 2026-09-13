from __future__ import annotations

import re
import unittest

from coproscope.core import colonnes_nominatives as structure
from coproscope.core.colonnes_nominatives import noms_en_colonne
from coproscope.modules import biffageops
from tests.test_colonnes_nominatives import DEPENSES, _sans_colonne_de_compte


"""`RM-2026-0068`, refutation mesuree le 2026-09-09 sur la base `4ec8452`.

Le lot `colonne nominative` affirme deux choses a la fois, et **elles se
contredisent**. Ce module rend la contradiction executable au lieu de la
laisser dans une prose de commit.

**Ce qu'il affirme.** D'un cote, `test_les_huit_rendus_de_la_meme_table_donnent
_les_memes_personnes` exige que le rendu `sans colonne de compte` - un libelle,
puis un nombre, repete - rende SIX personnes. De l'autre,
`test_un_etat_des_depenses_ne_devient_pas_une_liste_de_personnes` affirme qu'un
etat des depenses, de la MEME forme, n'en rende AUCUNE.

**Pourquoi les deux ne peuvent pas tenir.** Les deux textes ont exactement la
meme suite de silhouettes de lignes. Aucune fonction de la STRUCTURE ne peut
donc leur repondre differemment. Le test des depenses ne passe que parce que
`_nom_recevable` refuse a lui seul chacun de ses libelles: ils sont tous batis
sur des mots de `VOCABULAIRE_PROTEGE`. La garde ne mesure pas le module neuf -
elle mesure le lexique, et elle passerait a l'identique avec le module retire.

C'est exactement le defaut que le lot avait su nommer pour sa fixture de
sommaire - sa fixture portait aussi des chiffres et un mot deja refuse par le
lexique, donc la mutation ne prouvait rien - puis qu'il a laisse intact dans la
fixture d'a cote.

**Mesure sur donnees reelles, meme jour, meme instrument.** Sur la convocation
de 143 pages, rendue par l'extracteur de PREMIER CHOIX du depot (PyMuPDF), la
base `913d744` detecte 442 valeurs PERSONNE et `4ec8452` en detecte 459: +17,
zero retiree. Ces 17 n'ont pas le profil d'un coproprietaire - les 442 de la
base apparaissent 1 fois en mediane, 2 au neuvieme decile; les 17 ajoutees
apparaissent 9 fois en mediane, 67 au neuvieme decile, 69 au maximum. Une
annexe enumere des personnes; un intitule de rubrique se repete.
Le lot a annonce l'inverse - zero faux positif ajoute, zero detection perdue -
parce qu'il n'avait mesure que onze pages de ce document.
"""


#: Un etat des depenses dont AUCUN libelle n'est dans `VOCABULAIRE_PROTEGE`.
#: C'est la seule difference avec la fixture du lot, et c'est celle qui compte:
#: ici le lexique laisse passer, donc ce qui repond est la STRUCTURE et elle
#: seule. Libelles inventes, aucun ne designe une prestation reelle.
LIBELLES_HORS_LEXIQUE = (
    "REFECTION HALL",
    "ELAGAGE ARBRES",
    "POSE GARDE CORPS",
    "REMPLACEMENT INTERPHONE",
    "CONTROLE ACCES",
    "REPRISE SEUILS",
)

#: Les montants sont ceux de la fixture du lot: la comparaison ne doit pas
#: dependre d'eux.
MONTANTS = ("4 120,00", "2 310,55", "7 890,12", "5 400,00", "1 233,40", "88,10")


def _etat_des_depenses_hors_lexique() -> str:
    """Meme mise en page que le rendu `sans colonne de compte` du lot."""

    entete = "ETAT DES SOLDES DES COPROPRIETAIRES\nANNEXE N 1\nCompte\nCoproprietaire\nSolde\n"
    return entete + "".join(
        "%s\n%s\n" % couple for couple in zip(LIBELLES_HORS_LEXIQUE, MONTANTS)
    )


def _silhouettes(texte: str) -> list[str]:
    """La suite des silhouettes de lignes, telle que le module la lit."""

    return [
        silhouette
        for silhouette, _ in structure._rangs(texte, biffageops._nom_recevable)
    ]


class FormeIndiscernableTest(unittest.TestCase):
    """Ce qu'aucune regle de structure ne peut separer."""

    def test_le_lexique_accepte_chaque_libelle_de_cet_etat_des_depenses(self) -> None:
        """Sans cela, ce module entier serait creux comme celui qu'il refute."""

        for libelle in LIBELLES_HORS_LEXIQUE:
            with self.subTest(libelle=libelle):
                self.assertTrue(
                    biffageops._nom_recevable(libelle),
                    "le lexique refuse deja ce libelle: la mesure qui suit ne "
                    "dirait plus rien de la structure",
                )

    def test_la_garde_de_depenses_du_lot_ne_mesure_que_le_lexique(self) -> None:
        """La fixture voisine est refusee AVANT que le module soit consulte.

        Ce test ne reclame pas qu'elle change: il empeche qu'on la cite encore
        comme preuve que le module ne sur-masque pas. Il tombera le jour ou
        quelqu'un la rendra non creuse - et ce jour-la, la garde du lot tombera
        avec lui, ce qui est precisement le point.
        """

        libelles = [
            ligne.strip()
            for ligne in DEPENSES.splitlines()
            if ligne.strip() and not any(char.isdigit() for char in ligne)
        ]
        acceptes = [
            libelle for libelle in libelles if biffageops._nom_recevable(libelle)
        ]
        self.assertEqual(
            ["Poste"],
            acceptes,
            "hors l'entete de colonne, le lexique refuse deja tous les libelles "
            "de cette fixture: la garde anti-sur-masquage du lot passerait a "
            "l'identique avec `colonne_nominative` retire",
        )

    def test_une_annexe_des_soldes_et_un_etat_des_depenses_ont_la_meme_silhouette(
        self,
    ) -> None:
        """L'axiome de la refutation, et il ne depend d'aucun seuil."""

        self.assertEqual(
            _silhouettes(_sans_colonne_de_compte()),
            _silhouettes(_etat_des_depenses_hors_lexique()),
            "ces deux textes ont la meme suite de silhouettes de lignes; aucune "
            "regle qui ne lit que la structure ne peut leur repondre "
            "differemment, et le lot exige pourtant 6 personnes pour l'un et 0 "
            "pour l'autre",
        )

    def test_la_structure_seule_repond_donc_la_meme_chose_aux_deux(self) -> None:
        """La consequence, mesuree sur la sortie et non deduite."""

        annexe = noms_en_colonne(_sans_colonne_de_compte(), biffageops._nom_recevable)
        depenses = noms_en_colonne(
            _etat_des_depenses_hors_lexique(), biffageops._nom_recevable
        )
        self.assertEqual(
            len(annexe),
            len(depenses),
            "le module rend %d valeurs pour l'annexe et %d pour l'etat des "
            "depenses de meme forme; s'il en rendait des nombres differents, il "
            "lirait autre chose que la structure" % (len(annexe), len(depenses)),
        )
        self.assertTrue(
            annexe,
            "si les deux rendent zero, la couverture annoncee pour ce rendu "
            "n'existe plus",
        )


class PasDePropagationTest(unittest.TestCase):
    """La correction: une forme repetee n'ouvre pas le masquage generalise."""

    def _motifs(self, texte: str) -> list[str]:
        return [
            candidat.motif
            for candidat in biffageops.detecte_identites(texte)
            if candidat.categorie == "PERSONNE"
        ]

    def test_une_detection_de_forme_seule_ne_se_propage_pas_en_nom_nu(self) -> None:
        """`_noms_nus` se donne pour condition `vu accompagne ailleurs`.

        Une colonne n'a jamais vu le mot accompagne: elle l'a vu se repeter.
        Sans cette borne, une seule colonne mal lue ne produit pas une erreur -
        elle produit le remplacement de ce mot dans TOUT le document, ce qui est
        le mecanisme de l'incident du 2026-09-03.
        Mesure du 2026-09-09: sur la convocation de 143 pages, 12 valeurs de
        colonne en fabriquaient 5 de plus par ce chemin.
        """

        motifs = self._motifs(_etat_des_depenses_hors_lexique())
        self.assertEqual(
            [],
            [motif for motif in motifs if motif == "nom_nu"],
            "un libelle vu par la seule repetition de forme a ouvert le "
            "masquage de chacune de ses occurrences isolees dans le document",
        )

    def test_les_motifs_sans_appui_lexical_sont_declares(self) -> None:
        """La borne se lit dans le code, pas seulement dans son effet."""

        self.assertIn("colonne_nominative", biffageops.MOTIFS_SANS_APPUI_LEXICAL)

    def test_un_nom_vu_avec_civilite_se_propage_toujours(self) -> None:
        """L'autre sens: la borne ne doit pas eteindre `_noms_nus` en general."""

        texte = (
            "Le mandat est donne a Mme VANDERSTOCKE Sophie pour cet exercice.\n"
            "VANDERSTOCKE prendra part au vote de la resolution suivante.\n"
        )
        self.assertIn(
            "nom_nu",
            self._motifs(texte),
            "un patronyme etabli par une civilite doit toujours faire tomber "
            "ses occurrences isolees",
        )


def _accepte_tout(valeur: str) -> bool:
    """Le lexique le plus permissif concevable: toute cellule non numerique.

    C'est le CONTREFACTUEL de la garde. Il ne sert pas a masquer quoi que ce
    soit: il sert a repondre a la seule question que la fixture du lot ne
    posait pas - *cette fixture a-t-elle seulement la silhouette qu'il faut
    pour etre masquee ?*
    """
    nette = (valeur or "").strip()
    return len(nette) >= 3 and not any(char.isdigit() for char in nette)


class CE_QUI_PROTEGE_VRAIMENT_EST_LE_LEXIQUE(unittest.TestCase):
    """**La garde que la refutation ci-dessus laissait manquante.**

    Le module precedent a etabli que la STRUCTURE ne peut pas separer une
    annexe des soldes d'un etat des depenses: meme silhouette, meme reponse.
    Sa conclusion - *la garde du lot mesure le lexique* - etait juste, et elle
    s'arretait la. **Or si le lexique est le seul rempart, c'est LUI qu'il faut
    garder, et rien ne le gardait.**

    **Mesure du 2026-09-11, sur une instance VIDE reabsorbant 858 pieces
    sources, par le point d'entree du module.** Le meme texte confronte a trois
    lexiques differents:

    | lexique injecte | valeurs retenues | documents touches |
    |---|---:|---:|
    | qui refuse tout | **0** | 0 |
    | le lexique reel | 6 780 | **24** |
    | qui accepte tout | 13 886 | **321** |

    Trois faits en decoulent, et aucun n'etait ecrit nulle part:

    1. **avec un lexique qui refuse tout, le module ne rend RIEN** - il ne
       masque donc jamais par sa seule structure, ce qui est la propriete de
       sureté du module et elle se verifie;
    2. **le lexique reel epargne 297 documents sur 321** - la protection
       anti-sur-masquage est massive, un facteur 13, et elle est entierement
       portee par lui;
    3. **51,2 % de ce qu'un lexique permissif retiendrait est refuse par le
       lexique reel.**

    **Ce que cette classe garde, et pourquoi elle n'est pas creuse.** Elle
    n'affirme plus que la structure protege - c'est faux et la refutation l'a
    montre. Elle mesure l'ECART entre le lexique reel et un lexique permissif
    sur une fixture de forme identique. Affaiblir `_nom_recevable` fait tomber
    l'ecart, donc le test. La fixture du lot, elle, passait meme module retire.
    """

    def _noms(self, texte, lexique):
        return noms_en_colonne(texte, lexique)

    def test_la_fixture_du_lot_a_BIEN_la_silhouette_qu_il_faut(self) -> None:
        """**Le chainon manquant, et tout tient a lui.**

        La garde du lot constate zero personne sur l'etat des depenses et en
        conclut que le caviardage epargne le vocabulaire comptable. Mais un
        zero a deux causes possibles: *le lexique a refuse* ou *il n'y avait
        rien a trouver*. Sans ce test, les deux sont indiscernables - et c'est
        exactement pourquoi la garde passait avec le module retire.
        """
        vues = self._noms(DEPENSES, _accepte_tout)
        self.assertTrue(
            vues,
            "avec un lexique permissif, l'etat des depenses ne produit AUCUNE "
            "colonne: sa silhouette ne se prete donc pas au masquage, et le "
            "zero de la garde du lot ne prouve rien du lexique")

    def test_et_le_lexique_reel_la_refuse_pourtant(self) -> None:
        """L'autre moitie: la meme fixture, le lexique du produit, zero."""
        self.assertEqual(
            [], self._noms(DEPENSES, biffageops._nom_recevable),
            "le lexique laisse passer des libelles comptables: un etat des "
            "depenses serait caviarde")

    def test_l_ECART_entre_les_deux_lexiques_est_la_garde_elle_meme(self) -> None:
        """Ce que la structure ne fait pas, le lexique le fait - et seul lui.

        Ce test tombe si `_nom_recevable` cesse de refuser le vocabulaire
        comptable, ce qu'aucun test du lot ne detectait.
        """
        permissif = len(self._noms(DEPENSES, _accepte_tout))
        reel = len(self._noms(DEPENSES, biffageops._nom_recevable))
        self.assertGreater(
            permissif - reel, 0,
            "les deux lexiques rendent la meme chose sur cette fixture: le "
            "lexique n'y protege de rien, et la garde anti-sur-masquage du lot "
            "est redevenue creuse")

    def test_un_module_sans_lexique_ne_masque_JAMAIS_rien(self) -> None:
        """La propriete de sureté du module, mesuree au lieu d'etre affirmee.

        Elle vaut pour les DEUX fixtures - celle qui porte de vrais noms comme
        celle qui porte des libelles comptables: sans lexique, la structure ne
        designe personne.
        """
        for nom, texte in (("etat des depenses", DEPENSES),
                           ("annexe des soldes", _sans_colonne_de_compte())):
            with self.subTest(fixture=nom):
                self.assertEqual(
                    [], self._noms(texte, lambda _valeur: False),
                    "%s: le module a retenu des valeurs sans qu'aucun lexique "
                    "n'en reconnaisse une seule - il masque donc par sa seule "
                    "structure" % nom)

    def test_le_RESIDU_est_nomme_et_il_ne_se_referme_pas(self) -> None:
        """**Ce que cette garde laisse expose, et il faut le dire.**

        La structure ne discriminant pas, un libelle comptable qui
        FRANCHIRAIT le lexique serait masque comme un nom. Ce n'est pas
        hypothetique: `LIBELLES_HORS_LEXIQUE`, six libelles de travaux
        parfaitement plausibles, franchissent le lexique - et le module les
        retient. Le rempart est donc un lexique, c'est-a-dire une liste, et
        une liste se prend toujours en defaut par une valeur qu'elle ignore.
        Ce test EXIGE que le residu reste visible: le jour ou il tombe, c'est
        que quelqu'un aura trouve mieux qu'une liste, et il faudra le dire.
        """
        masques = self._noms(
            _etat_des_depenses_hors_lexique(), biffageops._nom_recevable)
        self.assertTrue(
            masques,
            "des libelles de travaux hors lexique ne sont plus masques: si "
            "c'est une vraie amelioration, remplacer ce test par la mesure qui "
            "la fonde, au lieu de le supprimer")


#: Des libelles de rubrique INVENTES, du genre qu'un etat des depenses ou une
#: annexe comptable porte. Aucun ne designe une prestation reelle, aucun ne
#: vient du corpus: ils servent a compter des refus, pas a citer quoi que ce
#: soit.
LIBELLES_DE_RUBRIQUE = (
    "ARTICLE DEUX TRAVAUX",
    "PAGE GARDE ANNEXE",
    "COMPTE FOURNISSEURS DIVERS",
    "SCI DU VIEUX MOULIN",
    "SARL RAVALEMENT SUD",
    "ENTRETIEN ASCENSEUR",
    "NETTOYAGE ESCALIER",
    "TOTAL GENERAL",
)


def _regles_qui_refusent(libelle: str) -> list[str]:
    """Les regles du lexique qui refusent ce libelle, nommees une par une."""
    refusent = []
    if biffageops.GARDE_VOCABULAIRE.match(libelle.strip()):
        refusent.append("garde_vocabulaire")
    if biffageops._tokens_proteges(libelle):
        refusent.append("tokens_proteges")
    tokens = [
        biffageops.normalize_identity_key(token)
        for token in re.split(r"[\s\-\'\u2019]+", libelle)
    ]
    porteurs = [
        token for token in tokens
        if token and token not in biffageops.PARTICULES
    ]
    if any(token in biffageops.VOCABULAIRE_PROTEGE for token in porteurs):
        refusent.append("porteur_protege")
    return refusent


class LE_LEXIQUE_EST_REDONDANT_ET_C_EST_MESURE(unittest.TestCase):
    """**Pourquoi une regle du lexique ne se garde pas seule, et il faut le dire.**

    Campagne de mutation du 2026-09-11, chaque regle desarmee a son tour, et
    la question posee a chaque libelle: *quelle regle est NECESSAIRE a ton
    refus ?* Reponse sur huit libelles de rubrique: **un seul** a une regle
    necessaire - `TOTAL GENERAL`, refuse par `porteur_protege` et par elle
    seule. **Les sept autres sont refuses par deux ou trois regles a la fois.**

    **Ce n'est pas un defaut, c'est une defense en profondeur** - et c'est
    precisement ce qui la rend difficile a garder: desarmer `garde_vocabulaire`
    ou `tokens_proteges` ne fait rougir AUCUN test du depot, ni ceux du lot ni
    ceux ecrits ici, parce qu'une autre regle refuse le meme libelle juste
    apres.

    **Ce que cette classe fait, et ce qu'elle ne fait pas.** Elle mesure la
    redondance et la declare. Elle ne fabrique PAS une fixture par regle: il
    faudrait pour cela inventer des libelles calibres pour tomber dans un seul
    trou du lexique, c'est-a-dire coder les modalites d'un lexique a la place
    de ce qu'un syndic ecrit vraiment. Le residu reste donc ouvert, nomme, et
    chiffre.
    """

    def test_chaque_libelle_de_rubrique_est_refuse(self) -> None:
        """Le temoin de sante: sans lui, la mesure qui suit compte du vide."""
        for libelle in LIBELLES_DE_RUBRIQUE:
            with self.subTest(libelle=libelle):
                self.assertFalse(
                    biffageops._nom_recevable(libelle),
                    "ce libelle de rubrique est devenu un nom recevable: il "
                    "serait caviarde dans un etat des depenses")

    def test_la_redondance_du_lexique_est_MESUREE_et_non_supposee(self) -> None:
        """Sept des huit libelles sont refuses par plus d'une regle."""
        redondants = [
            libelle for libelle in LIBELLES_DE_RUBRIQUE
            if len(_regles_qui_refusent(libelle)) > 1
        ]
        self.assertGreaterEqual(
            len(redondants), 5,
            "la redondance du lexique s'est effondree: les regles ne se "
            "recouvrent plus, donc un seul defaut de l'une laisse passer un "
            "libelle comptable")

    def test_au_moins_une_regle_a_un_domaine_PROPRE(self) -> None:
        """**Sans cela, aucune mutation du lexique ne mordrait nulle part.**

        C'est ce seul libelle qui rend la garde principale non creuse: desarmer
        `porteur_protege` le rend recevable, et le test de l'ecart tombe.
        """
        propres = {
            libelle: _regles_qui_refusent(libelle)
            for libelle in LIBELLES_DE_RUBRIQUE
            if len(_regles_qui_refusent(libelle)) == 1
        }
        self.assertTrue(
            propres,
            "aucun libelle n'est refuse par une seule regle: plus aucune "
            "mutation du lexique ne peut faire rougir un test")

    def test_le_residu_se_lit_dans_le_compte_et_non_dans_la_prose(self) -> None:
        """Le nombre de regles SANS aucun domaine propre est le residu.

        Il vaut 2 aujourd'hui - `garde_vocabulaire` et `tokens_proteges`. Ce
        test ne demande pas qu'il diminue: il demande qu'on ne le decouvre pas
        une seconde fois par surprise.
        """
        avec_domaine_propre = {
            regles[0] for libelle in LIBELLES_DE_RUBRIQUE
            if len(regles := _regles_qui_refusent(libelle)) == 1
        }
        toutes = {"garde_vocabulaire", "tokens_proteges", "porteur_protege"}
        sans_domaine_propre = toutes - avec_domaine_propre
        self.assertEqual(
            {"garde_vocabulaire", "tokens_proteges"}, sans_domaine_propre,
            "la liste des regles non gardables a change: la remesurer et "
            "mettre a jour le residu de `RM-2026-0068`")


if __name__ == "__main__":
    unittest.main()
