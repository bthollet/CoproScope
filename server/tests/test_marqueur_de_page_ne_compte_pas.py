# -*- coding: utf-8 -*-
"""La charpente de l'extraction ne compte jamais comme du contenu.

**Le fait qui a impose cette garde, et je suis celui qui est tombe dedans.**
Le 2026-09-10, en remesurant `RM-2026-0146`, j'ai compte les caracteres
alphanumeriques des 858 textes extraits d'un coffre reel et conclu que **zero**
document etait vide - alors que le registre en declare **149**. La mesure etait
exacte et portait sur autre chose: elle comptait le mot `PAGE` et les numeros
que l'extraction ecrit **entre** les pages, y compris quand la page est vide.
Un PDF de neuf pages jamais lu rend `45` caracteres alphanumeriques et pas un
seul ne vient du document.

J'ai failli publier *« le registre ment sur 149 documents »*, c'est-a-dire
l'inverse de la verite: verifie ensuite dans les deux sens, les 149 sont des PDF
`OCR_REQUIRED` sans **un** caractere hors marqueurs, et aucun des 709 autres
n'est vide. Le registre etait juste; c'est le lecteur qui comptait sa propre
charpente.

**Ce que la garde protege, et pourquoi elle porte sur l'ALLER-RETOUR.**
Le format du marqueur etait ecrit quatre fois: par le producteur, et par trois
lecteurs qui le re-devinaient chacun a sa facon - dont un **sans le `\\s*`
final**, si bien qu'un marqueur suivi d'une espace lui echappait. Verifier que
les lecteurs reconnaissent une chaine ECRITE A LA MAIN dans le test ne
prouverait rien: elle serait un cinquieme exemplaire du meme devinement. La
garde exige donc que ce que le PRODUCTEUR ecrit soit reconnu par ce que les
LECTEURS lisent, sur plusieurs numeros de page - un changement du gabarit ne
peut plus casser les lecteurs en silence.

**L'axe, et ce qu'il laisse dehors.** Ce qui est retire est ce que le produit a
ECRIT lui-meme, jamais ce qu'il croit reconnaitre. Un texte venu d'ailleurs -
export de syndic, copier-coller - peut porter ses propres separateurs de page
dans une forme qu'aucun motif ne connait: ils compteront comme du contenu, et
c'est le bon sens de l'erreur. Prendre du contenu pour de la charpente efface de
la matiere en silence; l'inverse ne fait que gonfler un compte, ce qui se voit.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from coproscope.modules import _marqueur_page as M


class LeProducteurEtLesLecteursParlentDeLaMemeChose(unittest.TestCase):
    """L'aller-retour, sur plusieurs numeros: 1, 9, 10, 999."""

    def test_CE_QUE_L_EXTRACTION_ECRIT_EST_RECONNU_PAR_CE_QU_ON_LIT(self) -> None:
        for index in (1, 2, 9, 10, 99, 100, 999):
            with self.subTest(page=index):
                ecrit = M.ecrire(index)
                self.assertRegex(ecrit, M.MARQUEUR_RE)
                self.assertEqual("", M.sans_marqueurs(ecrit).strip())

    def test_les_trois_sites_partagent_LE_MEME_objet_de_motif(self) -> None:
        """Pas `un motif equivalent`: le meme, sinon ils redivergeront.

        Deux motifs equivalents aujourd'hui ne le restent pas: c'est
        exactement ce qui s'etait produit entre `lisibilite` et le lecteur des
        comptes, l'un ayant gagne un `\\s*` final que l'autre n'a jamais eu.
        """
        from coproscope.modules import _comptes_extraction_mise_en_page as comptes
        from coproscope.modules import lisibilite

        self.assertIs(lisibilite.MARQUEUR_PAGE_RE, M.MARQUEUR_RE)
        self.assertIs(comptes._PAGE, M.MARQUEUR_RE)  # noqa: SLF001


class UnDocumentJamaisLuNePorteAucunContenu(unittest.TestCase):
    """Le compte qui manquait, et la valeur exacte qu'il rendait a tort."""

    def test_UN_PDF_DE_NEUF_PAGES_JAMAIS_LU_COMPTE_ZERO(self) -> None:
        texte = "\n".join(M.ecrire(i) + "\n" for i in range(1, 10))
        brut = sum(1 for c in texte if c.isalnum())
        self.assertEqual(45, brut, "la charpente de neuf pages porte 45 caracteres")
        self.assertEqual(0, M.contenu_utile(texte))
        self.assertFalse(M.porte_du_contenu(texte))

    def test_un_seul_caractere_hors_charpente_suffit_a_le_dire_lu(self) -> None:
        texte = M.ecrire(1) + "\nA\n" + M.ecrire(2) + "\n"
        self.assertEqual(1, M.contenu_utile(texte))
        self.assertTrue(M.porte_du_contenu(texte))

    def test_un_marqueur_suivi_d_une_espace_est_reconnu(self) -> None:
        """Le cas exact que le lecteur des comptes laissait passer."""
        self.assertEqual(0, M.contenu_utile(M.ecrire(3) + "   \n"))

    def test_un_marqueur_ne_mange_pas_la_ligne_suivante(self) -> None:
        """`\\s` engloutit les fins de ligne; `[ \\t]` non.

        Avec `\\s`, deux marqueurs separes par une ligne vide pouvaient se lire
        comme un seul et emporter ce qu'il y avait entre eux.
        """
        texte = M.ecrire(1) + "\n\n" + "Resolution 11 adoptee" + "\n\n" + M.ecrire(2)
        self.assertIn("Resolution 11 adoptee", M.sans_marqueurs(texte))

    def test_un_separateur_venu_d_ailleurs_compte_comme_du_contenu(self) -> None:
        """Residu assume: on retire ce qu'on a ecrit, pas ce qu'on reconnait."""
        self.assertGreater(M.contenu_utile("--- Page 4 sur 12 ---"), 0)


class PLUS_AUCUN_MODULE_NE_REDECLARE_LE_FORMAT(unittest.TestCase):
    """La conservation qui empeche un cinquieme exemplaire d'apparaitre."""

    #: Un motif qui cherche `PAGE` suivi d'un numero, dans une source. C'est la
    #: SILHOUETTE d'une redeclaration, pas une liste de fichiers connus.
    REDECLARATION = re.compile(r"re\.compile\([^)]*PAGE[^)]*\\d")

    def test_le_format_du_marqueur_n_est_ecrit_qu_a_UN_endroit(self) -> None:
        racine = Path(__file__).resolve().parents[1] / "src" / "coproscope"
        proprietaire = racine / "modules" / "_marqueur_page.py"
        coupables = []
        for chemin in sorted(racine.rglob("*.py")) + sorted(racine.rglob("*.pyfrag")):
            if chemin == proprietaire:
                continue
            texte = chemin.read_text(encoding="utf-8", errors="ignore")
            if self.REDECLARATION.search(texte):
                coupables.append(str(chemin.relative_to(racine)))
        self.assertEqual(
            [], coupables,
            "un module redeclare le format du marqueur de page au lieu de le "
            "prendre dans `_marqueur_page`: c'est ainsi que les motifs ont "
            "diverge la premiere fois",
        )

    def test_la_garde_de_redeclaration_sait_reconnaitre_une_redeclaration(self) -> None:
        """Sans ce controle, un motif casse rendrait la garde vide et verte."""
        self.assertTrue(
            self.REDECLARATION.search('_X = re.compile(r"^=+\\s*PAGE\\s+\\d+\\s*=+$")')
        )
        self.assertIsNone(self.REDECLARATION.search('_X = re.compile(r"^Resolution")'))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
