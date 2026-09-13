# -*- coding: utf-8 -*-
"""Les trois pieces canoniques du couple ajout-documents / feedback DocOps.

`RM-2026-0003`. L'arbitrage de Brice est acte dans la cellule: priorite au
couple *ajout documents + feedback DocOps*, en iterations fonctionnelles, et
**trois pieces y sont declarees CANONIQUES**:

1. la route `/documents/tri-feedback`;
2. le **pont volontaire** `/documents/ajouter` -> `/documents/tri-feedback`;
3. le lien depuis l'inbox physique vers `/documents/ajouter?source=inbox`.

**CE QUE CETTE GARDE FAIT, ET POURQUOI ELLE MANQUAIT.** Dire d'une piece
qu'elle est *canonique* est une decision; rien ne l'empechait de disparaitre au
prochain remaniement d'ecran, et **le mot canonique ne se verifie nulle part**.
Verification du 2026-09-12: les trois existent. La garde les fixe.

**LE PONT EST VOLONTAIRE, ET CE N'EST PAS UN DETAIL.** Un lecteur qui vient
d'ajouter des documents n'est pas redirige vers le tri: il y va **s'il veut**,
par un lien nomme. La garde verifie donc un LIEN dans le gabarit d'ajout, et
non une redirection - une redirection serait un autre produit.

**LE LIEN D'INBOX SE CONSTRUIT, IL N'EST PAS ECRIT.** `_source_href` le
fabrique depuis la constante `SOURCE_INBOX`, ce qui vaut mieux que le litteral
de la cellule: renommer la source change le lien partout au lieu de laisser
une chaine morte. La garde interroge donc **la fonction**, pas le texte.

**CE QU'ELLE NE FAIT PAS.** Elle ne remplace pas la **recette navigateur** que
l'item nomme comme suite: aucune requete n'est jouee, aucune page n'est
rendue, et le protocole du depot exige pour cela un port reserve, un scenario
clique et un GO novice. Elle garantit que les trois pieces sont **la** le jour
ou cette recette se fera.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from coproscope.web.document_intake_sources import SOURCE_INBOX, _source_href

WEB = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web"
GABARIT_AJOUT = WEB / "templates" / "document_intake.html"
ROUTE_FEEDBACK = WEB / "docops_feedback_route.py"

TRI_FEEDBACK = "/documents/tri-feedback"
AJOUT = "/documents/ajouter"


class LES_TROIS_PIECES_CANONIQUES_SONT_LA(unittest.TestCase):
    def test_la_route_du_tri_de_lot_existe_en_lecture_et_en_ecriture(self) -> None:
        """Une page qui se lit sans pouvoir rien enregistrer ne sert a rien:

        le feedback DocOps est un DEPOT d'avis, donc la route POST fait
        partie de la piece canonique.
        """
        source = ROUTE_FEEDBACK.read_text(encoding="utf-8")
        self.assertRegex(source, r'@app\.get\("%s"' % re.escape(TRI_FEEDBACK))
        self.assertRegex(source, r'@app\.post\("%s"' % re.escape(TRI_FEEDBACK))

    def test_le_pont_est_un_LIEN_depuis_l_ecran_d_ajout(self) -> None:
        """Volontaire, donc un lien - pas une redirection."""
        gabarit = GABARIT_AJOUT.read_text(encoding="utf-8")
        self.assertIn(
            TRI_FEEDBACK, gabarit,
            "le pont volontaire vers le tri de lot a disparu de l'ecran "
            "d'ajout: un lecteur qui vient de deposer des documents n'a plus "
            "de chemin nomme vers leur tri")
        self.assertRegex(
            gabarit, r"<a[^>]*%s" % re.escape(TRI_FEEDBACK),
            "le tri de lot n'est plus atteint par un LIEN: une redirection "
            "serait un autre produit que celui que l'arbitrage a retenu")

    def test_le_lien_d_inbox_se_construit_depuis_la_constante(self) -> None:
        """Interroger la fonction, pas le texte: le litteral mourrait seul."""
        self.assertEqual("%s?source=%s" % (AJOUT, SOURCE_INBOX),
                         _source_href(SOURCE_INBOX, ""))

    def test_l_ecran_d_ajout_est_debranche_et_non_perdu(self) -> None:
        """Recette de Brice du 2026-09-13 (`RM-2026-0183`): l'ecran d'ajout est

        DEBRANCHE, garde pour plus tard. La coque ne l'offre donc plus, et le
        mecanisme de rebranchement doit toujours le connaitre: sinon le pont
        canonique mourrait sans que rien ne le dise.
        """
        from coproscope.web.debranchement import CHEMINS_DEBRANCHES
        coque = (WEB / "templates" / "base.html").read_text(encoding="utf-8")
        self.assertNotIn(AJOUT, coque)
        self.assertIn(AJOUT, CHEMINS_DEBRANCHES["ajouter_document"])


class LE_LIEN_D_INBOX_NE_SE_FABRIQUE_PAS_AU_HASARD(unittest.TestCase):
    """Temoins: sans eux, l'egalite ci-dessus passerait sur n'importe quoi."""

    def test_la_source_par_defaut_ne_porte_aucun_parametre(self) -> None:
        from coproscope.web.document_intake_sources import SOURCE_ALL

        self.assertEqual(AJOUT, _source_href(SOURCE_ALL, ""))

    def test_une_autre_source_donne_un_autre_lien(self) -> None:
        from coproscope.web.document_intake_sources import SOURCE_LOCAL_FOLDER

        self.assertNotEqual(
            _source_href(SOURCE_INBOX, ""),
            _source_href(SOURCE_LOCAL_FOLDER, ""))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
