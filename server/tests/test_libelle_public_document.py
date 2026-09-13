from __future__ import annotations

import unittest

from coproscope.core.libelle_public import (
    libelle_public_document,
    reference_courte,
)


"""Le libelle d'un document ne vient jamais de son nom de fichier.

Constat du 2026-09-07: la page qui decide de la diffusion affichait un nom de
fichier portant un patronyme reel. Le nom de fichier est ecrit par un tiers -
syndic, fournisseur, scanner - et n'est donc pas une donnee de l'application.

Donnees entierement fictives.
"""


class LibellePublicDocument(unittest.TestCase):
    def test_le_nom_de_fichier_n_apparait_jamais(self) -> None:
        """La garde centrale. Si ce test tombe, la fuite est revenue."""

        pieges = (
            {"file_name": "assignation MARCHAND.pdf"},
            {"filename": "assignation MARCHAND.pdf"},
            {"original_path": r"raw\assignation MARCHAND.pdf"},
            {"file_name": "SCI VALLIOT-NOIRET releve.pdf", "document_type": "Facture"},
        )
        for row in pieges:
            with self.subTest(row=sorted(row)):
                libelle = libelle_public_document(dict(row))
                self.assertNotIn("MARCHAND", libelle)
                self.assertNotIn("VALLIOT", libelle)
                self.assertNotIn(".pdf", libelle)

    def test_libelle_derive_du_type_et_de_la_date(self) -> None:
        libelle = libelle_public_document(
            {
                "doc_id": "DOC-7139EDAD85E4",
                "file_name": "DIVERS_pv  03072024.pdf",
                "document_type": "PV_AG",
                "suspected_date": "2024-07-03",
            }
        )
        self.assertEqual(libelle, "PV ag du 03/07/2024 (AD85E4)")

    def test_type_inconnu_reste_lisible(self) -> None:
        """Un type jamais vu se degrade proprement, il ne casse pas."""

        libelle = libelle_public_document(
            {"doc_id": "DOC-ABCDEF012345", "document_type": "Attestation_Sinistre_Multirisque"}
        )
        self.assertEqual(libelle, "Attestation sinistre multirisque (012345)")

    def test_sans_type_ni_date_le_document_reste_identifiable(self) -> None:
        """Le repli porte le doc_id ENTIER, pas une troncature.

        `Document TIEUX` pour `DOC-CONTENTIEUX` n'identifiait rien et ne se
        recherchait pas. Le doc_id est publiable: l'interface l'affiche deja.

        CONTREDIT ET CORRIGE le 2026-09-09, `RM-2026-0052` defaut (2). Les deux
        assertions precedentes etaient `assertEqual(..., "DOC-7139EDAD85E4")`
        et `assertEqual(..., "DOC-CONTENTIEUX")`: un identifiant NU tenant lieu
        de titre de carte, ce que le gouvernail reproche mot pour mot - *un
        identifiant technique en face de l'utilisateur*. L'argument contre la
        troncature est conserve entier, et l'identifiant reste complet; ce qui
        change est que le libelle commence par un mot.
        """

        self.assertEqual(
            libelle_public_document({"doc_id": "DOC-7139EDAD85E4"}),
            "Document (DOC-7139EDAD85E4)",
        )
        self.assertEqual(
            libelle_public_document({"doc_id": "DOC-CONTENTIEUX"}),
            "Document (DOC-CONTENTIEUX)",
        )

    def test_ligne_vide_ne_produit_jamais_un_libelle_vide(self) -> None:
        self.assertEqual(libelle_public_document({}), "Document")

    def test_date_non_iso_est_ignoree_plutot_que_rendue_telle_quelle(self) -> None:
        """Une date que le code ne sait pas lire disparait; elle n'est pas recopiee."""

        libelle = libelle_public_document(
            {"doc_id": "DOC-ABCDEF012345", "document_type": "Facture", "suspected_date": "03072024"}
        )
        self.assertEqual(libelle, "Facture (012345)")

    def test_reference_courte_refuse_ce_qui_n_est_pas_une_empreinte(self) -> None:
        self.assertEqual(reference_courte("DOC-7139EDAD85E4"), "AD85E4")
        self.assertEqual(reference_courte(""), "")
        self.assertEqual(reference_courte("DOC-mon fichier.pdf"), "")


if __name__ == "__main__":
    unittest.main()
