from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coproscope.core.share import audit_repo, export_shareable
from coproscope.extractors.invoices import (
    DEFAULT_INTERNAL_CROSS_CHECKS,
    DECISION_PARTIAL,
    DocumentExtractionEvidence,
    REQUIRED_ACCOUNTING_FIELDS,
    TEXT_EXPLOITATION_PRIORITY,
    DecisionRule,
    DefaultInvoiceReconciler,
    InvoiceReconciliationInput,
    SupplierRule,
    VisualReviewItem,
    build_visual_review_batches,
    build_extractor_generation_prompt,
    build_provider_extractor_seed,
    detect_invoice_family,
    extract_generic_invoice_from_evidence,
    extract_generic_invoice_fields,
    needs_visual_supplier_review,
    parsing_level_requires_confirmation,
    provider_key_from_name,
    supplier_from_ledger,
)
from coproscope.extractors.invoices.providers import (
    CogelecInvoiceProviderExtractor,
    EdelenInvoiceProviderExtractor,
    EngieInvoiceProviderExtractor,
    InsuranceNoticeProviderExtractor,
    OmegaAscenseurInvoiceProviderExtractor,
    PhoceaInvoiceProviderExtractor,
)


class InvoiceExtractorTests(unittest.TestCase):
    def test_filename_families_are_routing_only(self) -> None:
        self.assertEqual(detect_invoice_family("Facture_2025010811374755.pdf"), "facture_timestamp")
        self.assertEqual(detect_invoice_family("Facture_nd0000027447.pdf"), "facture_nd")
        self.assertEqual(detect_invoice_family("Facture_Hono0000027048.pdf"), "facture_hono")
        self.assertEqual(detect_invoice_family("Facture_Auto_25TX002721_2025101315005556.pdf"), "facture_auto")
        self.assertEqual(detect_invoice_family("note.pdf"), "autres")

    def test_generic_extractor_returns_required_control_fields(self) -> None:
        text = """ACME MAINTENANCE
Facture n FAC-2026-001
Date: 15/05/2026
SIRET: 123 456 789 00012
Total HT 100,00
TVA 20,00
Total TTC 120,00
"""
        extraction = extract_generic_invoice_fields(text, "Facture_2026051510101010.pdf")
        self.assertEqual(extraction.provider_key, provider_key_from_name("ACME MAINTENANCE"))
        self.assertEqual(extraction.siren_siret, "12345678900012")
        self.assertEqual(extraction.date_facture, "2026-05-15")
        self.assertEqual(extraction.ttc, "120.00")
        self.assertNotIn("INCOHERENCE_HT_TVA_TTC", extraction.anomalies)
        self.assertIn("decision_ref", REQUIRED_ACCOUNTING_FIELDS)

    def test_generic_extractor_ignores_building_numbers_and_supplier_contacts(self) -> None:
        text = """TY SERVICES 53 Avenue de Frais Vallon 13013 MARSEILLE - Telephone : 0600000000 - Courriel : contact@example.test
Designation
Prix Total HT
Abattage d'un pin colle au batiment 22
Total Hors Taxes
1 200,00
TVA non applicable
0
Total TTC en euros
1 200,00
Numero de facture
06/2024/0250-BP-Abt-Pin-BT22-Supp
Date
20/01/2025
"""
        extraction = extract_generic_invoice_fields(text, "Facture_2025012116211809.pdf")

        self.assertEqual(extraction.fournisseur, "TY SERVICES")
        self.assertEqual(extraction.ht, "1200.00")
        self.assertEqual(extraction.tva, "0.00")
        self.assertEqual(extraction.ttc, "1200.00")
        self.assertNotIn("INCOHERENCE_HT_TVA_TTC", extraction.anomalies)

    def test_generic_extractor_distinguishes_vat_rate_from_vat_amount(self) -> None:
        text = """CARRE TRAVAUX
Facture n F202500141
Date 20/01/2025
Total HT
830,00
TVA 10 %
83,00
Total TTC
913,00
"""
        extraction = extract_generic_invoice_fields(text, "Facture_2025012115015485.pdf")

        self.assertEqual(extraction.tva, "83.00")
        self.assertEqual(extraction.ttc, "913.00")
        self.assertNotIn("INCOHERENCE_HT_TVA_TTC", extraction.anomalies)

    def test_generic_extractor_uses_tax_summary_and_named_siret_supplier(self) -> None:
        text = """FACTURE
CLIENT: Syndicat demo
TVA INTRACOMMUNAUTAIRE FR714341892211
SIRET FEU TEST : 341 235 679 00139
Facture n 861954
Date 22/01/2025
Base H.T. Taux TVA Mt TVA
1
378,34
20 %
75,67
Montant : 454,01
"""
        extraction = extract_generic_invoice_fields(text, "Facture_2025012211010101.pdf")

        self.assertEqual(extraction.fournisseur, "FEU TEST")
        self.assertEqual(extraction.siren_siret, "34123567900139")
        self.assertEqual(extraction.ht, "378.34")
        self.assertEqual(extraction.tva, "75.67")
        self.assertEqual(extraction.ttc, "454.01")
        self.assertNotIn("INCOHERENCE_HT_TVA_TTC", extraction.anomalies)

    def test_docai_evidence_feeds_generic_extraction_and_generator_prompt(self) -> None:
        evidence = DocumentExtractionEvidence(
            file_name="Facture_ACME.pdf",
            native_text="",
            ocr_text="ACME MAINTENANCE\nFacture n FAC-42\nDate: 15/05/2026\nSIRET: 123 456 789 00012\nTotal TTC 120,00",
            docling_markdown="| Total TTC | 120,00 |",
            layout_json='{"blocks": [{"text": "ACME MAINTENANCE"}]}',
            visual_review="Header reads ACME MAINTENANCE.",
        )
        extraction = extract_generic_invoice_from_evidence(evidence)
        self.assertEqual(extraction.fournisseur, "ACME MAINTENANCE")
        self.assertEqual(extraction.numero_facture, "FAC-42")
        self.assertEqual(extraction.siren_siret, "12345678900012")

        seed = build_provider_extractor_seed("ACME MAINTENANCE", evidence)
        prompt = build_extractor_generation_prompt(seed)
        self.assertIn("Docling Markdown", prompt)
        self.assertIn("L4 AI or online visual-review notes", prompt)
        self.assertIn("Provider key: acme_maintenance", prompt)

    def test_provider_extractors_parse_significant_supplier_formats(self) -> None:
        engie = EngieInvoiceProviderExtractor().extract(
            """ENGIE
Facture n 640000300998 du 01/09/25
RCS Nanterre 542 107 651
Total electricite / hors TVA 79,80
MONTANT TTC a payer 91,37
"""
        )
        self.assertEqual(engie.fournisseur, "ENGIE")
        self.assertEqual(engie.siren_siret, "542107651")
        self.assertEqual(engie.numero_facture, "640000300998")
        self.assertEqual(engie.date_facture, "2025-09-01")
        self.assertEqual(engie.ht, "79.80")
        self.assertEqual(engie.ttc, "91.37")

        omega = OmegaAscenseurInvoiceProviderExtractor().extract(
            """OMEGA ASCENSEUR
SIRET 815 051 974 00021
FACTURE FA.21.02.25.1083
21/02/2025
Echeance 21/03/25 : 1.185,80DELAIS DE PAIEMENT
"""
        )
        self.assertEqual(omega.siren_siret, "81505197400021")
        self.assertEqual(omega.numero_facture, "FA.21.02.25.1083")
        self.assertEqual(omega.ttc, "1185.80")

        omega_contract = OmegaAscenseurInvoiceProviderExtractor().extract(
            """OMEGA ASCENSEUR
SIRET: 815 051 974 00021
FACTURE
FA.09.01.25.0700
09/01/2025
TTC : 9.873,60
Contrat de maintenance Ascenseurs
2.407,20
240,72
2.647,92
2.647,92
TVA 10%
TOTAL
BASE
T.V.A.
09/02/25 : 2.647,92
DELAIS DE PAIEMENT
"""
        )
        self.assertEqual(omega_contract.numero_facture, "FA.09.01.25.0700")
        self.assertEqual(omega_contract.ht, "2407.20")
        self.assertEqual(omega_contract.tva, "240.72")
        self.assertEqual(omega_contract.ttc, "2647.92")

        edelen = EdelenInvoiceProviderExtractor().extract(
            """EDELEN contact@edelen.fr
SIRET 519 028 641 00016
Facture N FA31236
Date : 19.05.2025
Total HT Total TVA Total TTC Net a payer
2.643,00 264,30 2.907,30 2.907,30
"""
        )
        self.assertEqual(edelen.siren_siret, "51902864100016")
        self.assertEqual(edelen.numero_facture, "FA31236")
        self.assertEqual(edelen.ht, "2643.00")
        self.assertEqual(edelen.tva, "264.30")
        self.assertEqual(edelen.ttc, "2907.30")

        phocea = PhoceaInvoiceProviderExtractor().extract(
            """PHOCEA NETTOYAGE ENTRETIEN
Facture 250140731 31/01/2025
Montant HT Tx TVA TVA TTC
3.077,60 20,00 615,52 3.693,12
"""
        )
        self.assertEqual(phocea.numero_facture, "250140731")
        self.assertEqual(phocea.date_facture, "2025-01-31")
        self.assertEqual(phocea.ttc, "3693.12")

        cogelec = CogelecInvoiceProviderExtractor().extract(
            """COGELEC
SIRET:43418922100022 NUM_FACTURE:FC12345 DATE_FACTURE:15/04/2025
MTT_TTC:117,32NETAPAYER:117,32
"""
        )
        self.assertEqual(cogelec.siren_siret, "43418922100022")
        self.assertEqual(cogelec.numero_facture, "FC12345")
        self.assertEqual(cogelec.ttc, "117.32")

        insurance = InsuranceNoticeProviderExtractor().extract(
            """AVIS D'ECHEANCE
Compagnie : SADA
Multirisque Immeuble
Prime HT
19 570,25 EUR
Taxes et accessoires
2 563,15 EUR
Frais de quittancement
30,00 EUR
Solde du :
22 163,40 EUR
Conformement a l'article 261 C, votre prime est exoneree de TVA.
Marseille, le jeudi 09 janvier 2025
No de Police : 1H0357854
No de quittance : 2024RDG11664438
CABINET RIPERT DE GRISSAC
"""
        )
        self.assertEqual(insurance.fournisseur, "RIPERT DE GRISSAC")
        self.assertEqual(insurance.numero_facture, "2024RDG11664438")
        self.assertEqual(insurance.date_facture, "2025-01-09")
        self.assertEqual(insurance.tva, "0.00")
        self.assertEqual(insurance.ttc, "22163.40")
        self.assertIn("ASSURANCE_RIB_A_CONTROLER", insurance.anomalies)

    def test_default_reconciler_uses_text_and_ledger_supplier_evidence(self) -> None:
        invoice = InvoiceReconciliationInput(
            doc_id="DOC-1",
            text="A.M VINCENTELLI RENOVATION\nS.I.R.E.T. 83076953500014\nFacture FC3595",
            supplier="FOURNISSEUR_A_IDENTIFIER",
            invoice_number="FC3595",
            invoice_date="2025-01-16",
            amount_ttc="1837.00",
            control_family="C_TRAVAUX",
        )
        reconciler = DefaultInvoiceReconciler(
            supplier_rules=[
                SupplierRule(
                    supplier="A.M VINCENTELLI RENOVATION",
                    pattern=r"VINCENTELLI|830\s*769\s*535",
                    siren_siret="83076953500014",
                )
            ],
            ledger_lines=[
                "EXERCICE DU 01/01/2025 AU 31/12/2025",
                "16/01/25 FC3595 A.M VINCENTELLI/ RLPT TRONCON WC 1 837,00",
            ],
        )

        result = reconciler.reconcile(invoice)

        self.assertEqual(result.supplier.supplier, "A.M VINCENTELLI RENOVATION")
        self.assertEqual(result.supplier.siren_siret, "83076953500014")
        self.assertEqual(result.supplier.confidence, "TEXT_AND_LEDGER_MATCH")
        self.assertIn("FOURNISSEUR_A_IDENTIFIER", result.lifted_anomalies)
        self.assertIn("SIREN_SIRET_ABSENT", result.lifted_anomalies)

    def test_ledger_matching_does_not_use_amounts_or_years_as_invoice_keys(self) -> None:
        match = supplier_from_ledger(
            {"2025", "7000"},
            [
                "EXERCICE DU 01/01/2025 AU 31/12/2025",
                "15/02/25 83592502CH ASV/ REMPLT FERME PORTE 770,00 10,00 70,00",
            ],
        )

        self.assertEqual(match.supplier, "")

    def test_default_reconciler_matches_ag_decision_rules_as_partial_lift(self) -> None:
        invoice = InvoiceReconciliationInput(
            doc_id="DOC-2",
            text="Contrat de maintenance",
            supplier="OMEGA ASCENSEUR",
            invoice_number="250001",
            invoice_date="2025-04-01",
            amount_ttc="900.00",
            control_family="A_FOURNISSEUR_RECURRENTE",
        )
        reconciler = DefaultInvoiceReconciler(
            decision_rules=[
                DecisionRule(
                    rule_id="budget_2025",
                    decision_ref="AG2024-07-03_R29_BUDGET_2025",
                    source="PV AGO 2024-07-03 resolution 29",
                    evidence="Budget 2025 vote.",
                    status=DECISION_PARTIAL,
                    years=("2025",),
                    family_patterns=(r"^A_",),
                    residual_controls="Contrat, service fait, paiement et imputation a verifier.",
                )
            ]
        )

        result = reconciler.reconcile(invoice)

        self.assertEqual(result.decision.status, DECISION_PARTIAL)
        self.assertEqual(result.decision.decision_ref, "AG2024-07-03_R29_BUDGET_2025")
        self.assertIn("DECISION_MANQUANTE", result.lifted_anomalies)
        self.assertIn("CONTROLES_RESIDUELS_REQUIS", result.residual_anomalies)

    def test_visual_review_batches_are_frugal_supplier_evidence(self) -> None:
        items = [
            VisualReviewItem(doc_id=f"DOC-{index}", file_name=f"Facture_{index}.pdf", supplier="FOURNISSEUR_A_IDENTIFIER")
            for index in range(7)
        ]

        batches = build_visual_review_batches(items, batch_size=3, contact_sheet_prefix="supplier_review")

        self.assertEqual([len(batch.items) for batch in batches], [3, 3, 1])
        self.assertEqual(batches[0].contact_sheet_name, "supplier_review_01.png")
        self.assertIn("contact sheets", batches[0].prompt_hint)
        self.assertTrue(needs_visual_supplier_review("FOURNISSEUR_A_IDENTIFIER", text_chars=200, confidence=""))
        self.assertTrue(needs_visual_supplier_review("ENGIE", text_chars=12, confidence="TEXT_WEAK"))
        self.assertFalse(needs_visual_supplier_review("ENGIE", text_chars=200, confidence="TEXT_STRONG"))
        self.assertEqual(TEXT_EXPLOITATION_PRIORITY[-1], "L4_AI_OR_ONLINE_REVIEW")
        self.assertFalse(parsing_level_requires_confirmation("L3_LOCAL_STRUCTURE_OR_VISUAL"))
        self.assertTrue(parsing_level_requires_confirmation("L4_AI_OR_ONLINE_REVIEW"))
        self.assertFalse(any(level.startswith(("P1_", "P2_", "P3_", "P4_")) for level in TEXT_EXPLOITATION_PRIORITY))

    def test_default_internal_cross_checks_are_defined_before_parsing_escalation(self) -> None:
        self.assertIn("provider_identity_consensus", DEFAULT_INTERNAL_CROSS_CHECKS)
        self.assertIn("ledger_invoice_reference", DEFAULT_INTERNAL_CROSS_CHECKS)
        self.assertIn("ag_budget_contract_decision_rules", DEFAULT_INTERNAL_CROSS_CHECKS)

    def test_share_manifest_lists_generalizable_extractors_and_blocks_private(self) -> None:
        config_path = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "configs" / "github_sharing.default.yml"
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            manifest_dir = repo_root / "server" / "src" / "coproscope" / "extractors" / "invoices"
            providers_dir = manifest_dir / "providers"
            providers_dir.mkdir(parents=True)
            (providers_dir / "generic.py").write_text("x = 1\n", encoding="utf-8")
            (providers_dir / "private_supplier.py").write_text("secret = 1\n", encoding="utf-8")
            (manifest_dir / "extractors.manifest.json").write_text(
                """{
  "provider_extractors": [
    {
      "provider_key": "generic",
      "module_path": "server/src/coproscope/extractors/invoices/providers/generic.py",
      "status": "generalizable"
    },
    {
      "provider_key": "private_supplier",
      "module_path": "server/src/coproscope/extractors/invoices/providers/private_supplier.py",
      "status": "private"
    }
  ]
,
  "default_reconciliation_modules": [
    {
      "module_key": "default_invoice_reconciler",
      "module_path": "server/src/coproscope/extractors/invoices/reconciliation.py",
      "status": "generalizable"
    }
  ],
  "default_visual_review_modules": [
    {
      "module_key": "frugal_supplier_visual_review",
      "module_path": "server/src/coproscope/extractors/invoices/visual_review.py",
      "status": "generalizable"
    }
  ]
}
""",
                encoding="utf-8",
            )
            (manifest_dir / "reconciliation.py").write_text("x = 1\n", encoding="utf-8")
            (manifest_dir / "visual_review.py").write_text("x = 1\n", encoding="utf-8")

            result = audit_repo(repo_root, config_path)
            extractor_audit = result["generalizable_extractors"]
            self.assertIn("server/src/coproscope/extractors/invoices/providers/generic.py", result["shareable"])
            self.assertIn("server/src/coproscope/extractors/invoices/reconciliation.py", result["shareable"])
            self.assertIn("server/src/coproscope/extractors/invoices/visual_review.py", result["shareable"])
            self.assertNotIn("server/src/coproscope/extractors/invoices/providers/private_supplier.py", result["shareable"])
            self.assertIn("server/src/coproscope/extractors/invoices/providers/private_supplier.py", result["blocked"])
            self.assertEqual(extractor_audit["manifest_path"], "server/src/coproscope/extractors/invoices/extractors.manifest.json")
            self.assertEqual(
                extractor_audit["default_reconciliation_modules"][0]["module_path"],
                "server/src/coproscope/extractors/invoices/reconciliation.py",
            )
            self.assertEqual(
                extractor_audit["default_visual_review_modules"][0]["module_path"],
                "server/src/coproscope/extractors/invoices/visual_review.py",
            )

            export_root = Path(tmpdir) / "export"
            manifest = export_shareable(repo_root, config_path, export_root, clean=True)
            self.assertIn("generalizable_extractors", manifest)


if __name__ == "__main__":
    unittest.main()
