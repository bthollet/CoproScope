# -*- coding: utf-8 -*-
"""Un connecteur qui ne sait pas lire ne declare pas une absence.

`RM-2026-0168`. La structure relevee en direct sur l'extranet d'un TROISIEME
editeur casse trois hypotheses du lecteur: l'arborescence est un ARBRE charge
au clic et non une liste deja presente; les rubriques sont **nommees, pas
codees**, sur au moins trois niveaux, avec **zero correspondance** avec les
huit codes ecrits en dur; et l'editeur publie une date de mise en ligne par
document.

**LA LISTE DE CODES EST UNE MODALITE, et le troisieme editeur la refute
exactement comme la regle des axes le prevoit.** Ce n'est pas ce que ce test
repare - la corriger demande une page reelle du troisieme editeur, que la suite
n'a pas et qu'on ne simule pas.

**CE QUE CE TEST PROTEGE, ET QUI N'ETAIT GARDE NULLE PART.** Sur un editeur
inconnu, aucune des huit rubriques n'est trouvee et le lecteur rend
`presente: false` pour chacune. **La question n'est pas s'il se trompe - il ne
sait pas -, c'est ce qu'il en DIT.** Le journal traduit `presente: false` en
**`NON_EXPLOREE`**, jamais en `ABSENTE`, et l'en-tete du lecteur le pose en
propres termes: *l'absence ne sera pas affirmable*.

**L'AXE, et c'est la regle des trois etats du depot.** Ce qui VARIE: l'editeur,
la maniere dont il nomme et charge ses rubriques, le nombre de niveaux de son
arbre. Ce qui reste INVARIANT: **ne pas avoir lu n'est pas avoir constate un
vide.** Un connecteur qui confondrait les deux ferait reclamer a un syndic des
pieces qu'il a peut-etre deposees - et le ferait avec l'autorite d'un releve.

**Hors des valeurs observees:** un quatrieme editeur, dont aucune rubrique ne
sera trouvee non plus, tombe sous la meme regle sans qu'on ajoute rien.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

CLIENT = (Path(__file__).resolve().parents[2] / "clients"
          / "extension-navigateur")
LECTEUR = CLIENT / "lecteur.js"
JOURNAL = CLIENT / "journal.js"


class UNE_RUBRIQUE_NON_TROUVEE_SE_DIT_NON_EXPLOREE(unittest.TestCase):
    def setUp(self) -> None:
        self.journal = JOURNAL.read_text(encoding="utf-8")
        self.lecteur = LECTEUR.read_text(encoding="utf-8")

    def test_les_deux_fichiers_sont_bien_lus(self) -> None:
        """Garde de l'instrument: un chemin casse rendrait tout vert."""
        self.assertGreater(len(self.journal), 2000)
        self.assertGreater(len(self.lecteur), 2000)

    def test_une_rubrique_absente_du_DOM_se_dit_NON_EXPLOREE(self) -> None:
        """Le coeur: `presente: false` ne devient jamais une absence.

        La garde attache au MOTIF - la ternaire qui traduit l'etat - et non a
        la mention du mot, qui figure aussi dans les commentaires.
        """
        self.assertRegex(
            self.journal,
            r'etat:\s*r\.presente\s*\?\s*"PARCOURUE"\s*:\s*"NON_EXPLOREE"',
            "le journal ne traduit plus `presente: false` en NON_EXPLOREE: "
            "un editeur qu'on ne sait pas lire serait declare VIDE, et un "
            "syndic se verrait reclamer des pieces qu'il a peut-etre deposees")

    def test_le_mot_ABSENTE_n_est_pas_produit_par_le_connecteur(self) -> None:
        """Le pendant: aucun etat d'absence ne sort de ce cote.

        L'absence se constate cote produit, apres rattachement declare par un
        humain - `_extranet_referentiel` le dit - jamais par un lecteur de
        page qui n'a pas trouve un selecteur.
        """
        produits = re.findall(r'"(ABSENTE|ABSENT)"', self.journal)
        self.assertEqual([], produits)

    def test_une_rubrique_non_trouvee_ne_compte_aucune_piece(self) -> None:
        """Sinon `NON_EXPLOREE` porterait un comptage, donc un constat."""
        self.assertRegex(
            self.journal,
            r'nb_pieces:\s*String\(r\.presente\s*\?\s*piecesDe\(r\)\.length\s*:\s*0\)')

    def test_la_cloture_n_est_pas_CONSTATEE_sans_lecture(self) -> None:
        """Une rubrique non exploree ne peut pas etre declaree close."""
        self.assertRegex(
            self.journal,
            r'cloture:\s*r\.presente\s*&&\s*!releve\.pagination\s*\?\s*"CONSTATEE"')


class LA_LISTE_DE_CODES_EST_UNE_MODALITE_DECLAREE(unittest.TestCase):
    """Ce que le lot ne repare pas, borne pour que cela ne grandisse pas."""

    def setUp(self) -> None:
        self.lecteur = LECTEUR.read_text(encoding="utf-8")

    def test_la_liste_existe_et_son_compte_est_arrete(self) -> None:
        """Huit codes au 2026-09-12. **Ce n'est pas une tolerance.**

        Allonger la liste est exactement le geste que la regle des axes
        interdit: le troisieme editeur n'a **aucune** de ces rubriques, et un
        neuvieme code ne le rapprocherait pas d'un cheveu. La reparation est
        de reconnaitre une rubrique a ce qu'elle EST - un bloc qui porte des
        lignes de pieces - et cela demande une page reelle du troisieme
        editeur.
        """
        trouve = re.search(r"const CODES = \[([^\]]*)\]", self.lecteur)
        self.assertIsNotNone(trouve, "la liste de codes a change de forme")
        codes = re.findall(r'"([A-Z]+)"', trouve.group(1))
        self.assertEqual(
            8, len(codes),
            "la liste des codes d'editeur a change de taille. L'allonger ne "
            "repare rien: un editeur qui nomme ses rubriques en francais "
            "ordinaire n'en porte aucune. Voir `RM-2026-0168`.")

    def test_le_lecteur_declare_ce_que_sa_liste_laisse_expose(self) -> None:
        """Une garantie se decrit avec ce qu'elle laisse expose."""
        self.assertIn("NON_EXPLOREE", self.lecteur)
        self.assertIn("absence", self.lecteur.lower())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
