from __future__ import annotations

import unittest

from coproscope.modules import factureops


class FactureOpsProviderRoutingTests(unittest.TestCase):
    def test_uses_insurance_notice_extractor(self) -> None:
        extraction = factureops._extract_invoice_from_evidence(
            factureops.DocumentExtractionEvidence(
                file_name="Avis_echeance_assurance.pdf",
                native_text=(
                    "AVIS D'ECHEANCE\nCompagnie : SADA\nMultirisque Immeuble\nPrime HT 19 570,25 EUR\n"
                    "Taxes et accessoires 2 563,15 EUR\nFrais de quittancement 30,00 EUR\n"
                    "Solde du : 22 163,40 EUR\nConformement a l'article 261 C, votre prime est exoneree de TVA.\n"
                    "Marseille, le jeudi 09 janvier 2025\nNo de Police : 1H0357854\nNo de quittance : 2024RDG11664438\n"
                ),
            )
        )

        self.assertEqual(extraction.provider_key, "insurance_notice")
        self.assertEqual(extraction.numero_facture, "2024RDG11664438")
        self.assertEqual(extraction.date_facture, "2025-01-09")
        self.assertEqual(extraction.tva, "0.00")
        self.assertEqual(extraction.ttc, "22163.40")

    def test_uses_omega_extractor(self) -> None:
        evidence = factureops.DocumentExtractionEvidence(
            file_name="Facture_omega.pdf",
            native_text=(
                "OMEGA ASCENSEUR\nSIRET: 815 051 974 00021\nFA.09.01.25.0700\n09/01/2025\n"
                "TTC : 9.873,60\nContrat de maintenance Ascenseurs\n2.407,20\n240,72\n"
                "2.647,92\n2.647,92\nTVA 10%\n09/02/25 : 2.647,92\nDELAIS DE PAIEMENT\n"
            ),
        )
        extraction = factureops._extract_invoice_from_evidence(evidence)

        self.assertEqual(extraction.provider_key, "omega_ascenseur")
        self.assertEqual(extraction.numero_facture, "FA.09.01.25.0700")
        self.assertEqual(extraction.ht, "2407.20")
        self.assertEqual(extraction.tva, "240.72")
        self.assertEqual(extraction.ttc, "2647.92")
        self.assertEqual(
            factureops._account_for_invoice(evidence.combined_text(), extraction.fournisseur),
            ("615000", "ascenseur_maintenance"),
        )

    def test_uses_cogelec_extractor(self) -> None:
        evidence = factureops.DocumentExtractionEvidence(
            file_name="Facture_cogelec.pdf",
            native_text=(
                "COGELEC\nFacture n 1641180 du 27/01/2025\nSIRET:43418922100022\n"
                "NO_CONTRAT:SC04591\nCODE_PORTAIL:\nMTT_TTC:117,32\nNETAPAYER:117,32\n97,77\n"
                "20,00\nT1\n117,32\n19,55\n97,77\nMontant TVA\nBase\nTaux\n"
            ),
        )
        extraction = factureops._extract_invoice_from_evidence(evidence)
        account, family = factureops._account_for_invoice(evidence.combined_text(), extraction.fournisseur)

        self.assertEqual(extraction.provider_key, "cogelec")
        self.assertEqual(extraction.numero_facture, "1641180")
        self.assertEqual(extraction.ht, "97.77")
        self.assertEqual(extraction.tva, "19.55")
        self.assertEqual(extraction.ttc, "117.32")
        self.assertEqual((account, family), ("615000", "entretien_maintenance"))


if __name__ == "__main__":
    unittest.main()
