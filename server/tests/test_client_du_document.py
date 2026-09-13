# -*- coding: utf-8 -*-
"""Le client d'une facture n'en est pas le fournisseur, et son nom se LIT.

**Ce que ces tests eprouvent.** Jusqu'au 2026-09-08, la regle *ce nom-la n'est
pas un fournisseur* etait ecrite en dur pour **deux clients rencontres**: le nom
reel d'une copropriete et celui d'un cabinet, en litteraux dans l'extracteur.
Une troisieme copropriete voyait donc **son propre nom accepte comme
fournisseur, sans aucun signal**.

Les tests ci-dessous prennent une copropriete que le code n'a jamais vue et
verifient les deux moities de l'axe:

1. tant que rien n'est declare, l'extracteur **ne connait pas** son client - et
   il se trompe, de la meme facon pour tout le monde;
2. des que l'instance declare sa designation, il ne se trompe plus - **sans
   qu'une ligne de code nomme cette copropriete**.
"""

from __future__ import annotations

import unittest

from coproscope.extractors.invoices._client_du_document import (
    FRAGMENTS_DE_FORME,
    designations_declarees,
    fragments_de_rejet,
)
from coproscope.extractors.invoices.base import (
    DocumentExtractionEvidence,
    extract_generic_invoice_fields,
    extract_generic_invoice_from_evidence,
)

#: Une copropriete que le code n'a jamais rencontree. C'est tout l'interet:
#: si le test passait grace a un litteral, il ne prouverait rien.
COPRO_INCONNUE = "Residence du Clos Mirabeau"

#: Une facture qui porte ses mentions legales pres du fournisseur. L'extracteur
#: la lit par un autre chemin - l'ancrage sur `SIRET`/`RCS` - et le vocabulaire
#: de rejet n'y joue quasiment aucun role.
FACTURE_AVEC_MENTIONS_LEGALES = "\n".join(
    [
        COPRO_INCONNUE,
        "12 rue des Acacias",
        "",
        "TOITURES DELAUNAY SARL",
        "SIRET 98765432100019 - RCS Marseille",
        "",
        "Facture n FA-2026-0042",
        "Le 14 mars 2026",
        "Total HT 2 500,00 EUR",
    ]
)

#: La meme facture SANS mention legale reperable. L'extracteur retombe alors sur
#: son dernier recours - la premiere ligne plausible du haut de page - et c'est
#: **la seule branche ou le vocabulaire de rejet decide**. C'est donc la que le
#: defaut vivait, et c'est la qu'il se reproduit.
#:
#: Cette precision n'est pas un detail de mise en scene: mon premier jet de ces
#: tests annoncait le defaut sur la facture ci-dessus, et la mesure l'a refute -
#: l'extracteur y trouvait deja le bon fournisseur. Une affirmation non
#: reproduite ne vaut rien, meme quand le defaut existe ailleurs.
FACTURE_SANS_MENTIONS_LEGALES = "\n".join(
    [
        COPRO_INCONNUE,
        "12 rue des Acacias",
        "",
        "TOITURES DELAUNAY SARL",
        "",
        "Facture n FA-2026-0042",
        "Le 14 mars 2026",
        "Total HT 2 500,00 EUR",
    ]
)


class _Instance:
    """Le minimum qu'une configuration d'instance expose a la lecture."""

    def __init__(self, nom: str, declarees: list[str] | None = None) -> None:
        self.display_name = nom
        self.payload = {"settings": {"factures": {"designations_du_client": declarees or []}}}


class ClientDuDocument(unittest.TestCase):
    def test_le_vocabulaire_de_forme_ne_nomme_aucun_client(self) -> None:
        """Sans designation lue, la liste est EXACTEMENT le vocabulaire de forme.

        C'est la propriete structurelle qui remplace les deux litteraux: rien
        dans le code ne depend d'une copropriete particuliere.
        """
        self.assertEqual(list(FRAGMENTS_DE_FORME), fragments_de_rejet())

    def test_une_designation_declaree_entre_dans_les_fragments(self) -> None:
        fragments = fragments_de_rejet([COPRO_INCONNUE])
        self.assertIn("residence du clos mirabeau", fragments)
        self.assertEqual(len(FRAGMENTS_DE_FORME) + 1, len(fragments))

    def test_une_designation_trop_courte_est_refusee(self) -> None:
        """Un fragment de trois lettres rejetterait des fournisseurs legitimes.

        La borne porte sur la LONGUEUR, donc elle ne connait aucun nom.
        """
        self.assertEqual(list(FRAGMENTS_DE_FORME), fragments_de_rejet(["SCI"]))

    def test_les_designations_se_lisent_dans_l_instance(self) -> None:
        instance = _Instance(COPRO_INCONNUE, ["Syndicat des coproprietaires du Clos Mirabeau"])
        lues = designations_declarees(instance)
        self.assertIn("residence du clos mirabeau", lues)
        self.assertIn("syndicat des coproprietaires du clos mirabeau", lues)

    def test_une_mention_legale_suffit_sans_aucun_vocabulaire(self) -> None:
        """La branche ou le vocabulaire de rejet ne decide de rien.

        Mesure faite en ecrivant ces tests: sur une facture qui porte `SIRET` ou
        `RCS` pres du fournisseur, l'extracteur trouve le bon nom **sans** que
        le client soit declare. Les deux litteraux retires n'y servaient donc
        a rien - ils ne servaient que sur la branche de dernier recours.
        """
        extraction = extract_generic_invoice_fields(
            FACTURE_AVEC_MENTIONS_LEGALES, file_name="facture.pdf"
        )
        self.assertIn("DELAUNAY", extraction.fournisseur.upper())

    def test_sans_designation_le_client_est_pris_pour_le_fournisseur(self) -> None:
        """Le defaut, reproduit: c'est l'etat de TOUTE copropriete non declaree.

        Il est montre ici au lieu d'etre tu, parce qu'il dit exactement ce que
        la declaration achete. Avant le 2026-09-08, ce meme test passait pour
        deux coproprietes - celles dont le nom etait ecrit dans le code - et
        echouait pour toutes les autres, sans que rien ne distingue les deux cas.
        """
        extraction = extract_generic_invoice_fields(
            FACTURE_SANS_MENTIONS_LEGALES, file_name="facture.pdf"
        )
        self.assertEqual(COPRO_INCONNUE, extraction.fournisseur)

    def test_avec_la_designation_lue_le_fournisseur_est_le_bon(self) -> None:
        extraction = extract_generic_invoice_fields(
            FACTURE_SANS_MENTIONS_LEGALES,
            file_name="facture.pdf",
            designations_du_client=(COPRO_INCONNUE,),
        )
        self.assertNotEqual(COPRO_INCONNUE, extraction.fournisseur)
        self.assertIn("DELAUNAY", extraction.fournisseur.upper())

    def test_le_chemin_de_production_transporte_les_designations(self) -> None:
        """La piece manquante: l'evidence doit porter ce que l'instance declare.

        Sans ce transport, la lecture serait faite et jetee - une correction qui
        n'atteint pas l'appelant reel.
        """
        evidence = DocumentExtractionEvidence(
            file_name="facture.pdf",
            native_text=FACTURE_SANS_MENTIONS_LEGALES,
            designations_du_client=(COPRO_INCONNUE,),
        )
        extraction = extract_generic_invoice_from_evidence(evidence)
        self.assertNotEqual(COPRO_INCONNUE, extraction.fournisseur)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
