from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, RunContext, load_instance, read_csv, relative_to, write_csv
from coproscope.modules.accounting import (
    accounting_controls,
    reconcile_invoice_expenses,
    reconstruct_accounting,
    suggest_supplier_aliases,
    supplier_aliases_from_suggestions,
)
from coproscope.modules.evidenceops import build_evidence_report
from coproscope.modules import factureops
from coproscope.modules.factureops import extract_invoices
from coproscope.modules.gristops import sync_grist
from coproscope.modules.tools import tools_status
from coproscope.modules.workers import run_workers


class ComptaScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.example_root = Path(self.tempdir.name) / "synthetic_copro"
        shutil.copytree(source_example, self.example_root)
        self.instance = load_instance(str(self.example_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_reconstruct_accounting_from_synthetic_invoice(self) -> None:
        run = RunContext(self.instance, "accounting reconstruct")
        result = reconstruct_accounting(self.instance, run, 2025)
        run.finish("OK", "accounting reconstruct complete")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["invoice_count"], 1)
        self.assertEqual(result["entry_count"], 1)
        self.assertTrue(Path(str(result["invoice_evidence"])).exists())
        self.assertTrue(Path(str(result["invoice_anomalies"])).exists())
        self.assertTrue(Path(str(result["ledger_reconstruction"])).exists())
        self.assertTrue(Path(str(result["duckdb"])).exists())
        self.assertTrue(Path(str(result["invoice_expense_matches"])).exists())
        self.assertTrue(Path(str(result["controle_comptes_guide"])).exists())
        self.assertTrue(Path(str(result["regroupement_controle_comptes"])).exists())
        self.assertTrue(Path(str(result["questions_syndic_comptascope"])).exists())
        self.assertTrue(Path(str(result["report"])).exists())
        self.assertEqual(result["expense_match_counts"], {"MATCH_AMOUNT_ALIAS": 1})
        self.assertEqual(result["review_item_count"], 1)
        self.assertEqual(result["review_group_count"], 1)
        self.assertEqual(result["syndic_question_count"], 0)
        self.assertIn("supplier_alias_suggestion_count", result)
        self.assertIn("invoice_anomaly_count", result)

        _, invoices = read_csv(Path(str(result["invoice_evidence"])))
        self.assertEqual(invoices[0]["numero_facture"], "FAC-2025-001")
        self.assertEqual(invoices[0]["ttc"], "1200.00")
        self.assertEqual(invoices[0]["statut_controle"], "PROBABLE")
        self.assertEqual(invoices[0]["evidence_level"], "L1_NATIVE_TEXT")
        _, matches = read_csv(Path(str(result["invoice_expense_matches"])))
        self.assertEqual(matches[0]["match_status"], "MATCH_AMOUNT_ALIAS")
        self.assertIn("alias fournisseur", matches[0]["match_reason"])
        _, guide_rows = read_csv(Path(str(result["controle_comptes_guide"])))
        self.assertEqual(guide_rows[0]["priorite"], "OK")
        self.assertEqual(guide_rows[0]["statut_rapprochement"], "MATCH_AMOUNT_ALIAS")
        self.assertEqual(guide_rows[0]["question_syndic"], "")
        _, group_rows = read_csv(Path(str(result["regroupement_controle_comptes"])))
        self.assertEqual(group_rows[0]["priorite"], "OK")
        self.assertEqual(group_rows[0]["fournisseur"], "JARDINS EXEMPLE SERVICES")
        self.assertEqual(group_rows[0]["anomalie_facture"], "SANS_ANOMALIE_FACTURE")
        report_text = Path(str(result["report"])).read_text(encoding="utf-8")
        self.assertIn("NON_RAPPROCHE", report_text)
        self.assertIn("Regroupement priorite / fournisseur / anomalie", report_text)
        self.assertIn("Questions syndic copiables", report_text)

    def test_controls_grist_and_evidence_exports(self) -> None:
        run = RunContext(self.instance, "workers accounting dashboards")
        reconstruct_accounting(self.instance, run, 2025)
        report_path = self.example_root / "outputs" / "accounting" / "2025" / "rapport_comptascope_2025.md"
        report_path.unlink()
        controls = accounting_controls(self.instance, run, 2025)
        grist = sync_grist(self.instance, run, target="local", dataset="demo", year=2025)
        evidence = build_evidence_report(self.instance, run, dataset="demo", year=2025)
        run.finish("OK", "exports complete")

        self.assertEqual(controls["status"], "ok")
        self.assertEqual(grist["status"], "ok")
        self.assertEqual(evidence["status"], "ok")
        self.assertIn("invoice_evidence", grist["exports"])
        self.assertIn("invoice_anomalies", grist["exports"])
        self.assertIn("invoice_expense_matches", grist["exports"])
        self.assertIn("supplier_alias_suggestions", grist["exports"])
        self.assertIn("controle_comptes_guide", grist["exports"])
        self.assertIn("regroupement_controle_comptes", grist["exports"])
        self.assertIn("questions_syndic_comptascope", grist["exports"])
        self.assertIn("rapport_comptascope", grist["exports"])
        self.assertTrue(report_path.exists())
        self.assertGreaterEqual(evidence["invoice_count"], 1)
        self.assertIn("invoice_anomaly_count", evidence)
        self.assertEqual(evidence["matched_count"], 1)
        self.assertEqual(evidence["candidate_p2_count"], 0)
        self.assertEqual(evidence["priority_p1_count"], 0)
        self.assertIn("supplier_alias_suggestion_count", evidence)

    def test_reconstruct_exports_copyable_syndic_questions_for_open_items(self) -> None:
        preload = self.example_root / "system" / "accounting" / "preloaded_invoice_evidence_2025.csv"
        preload.parent.mkdir(parents=True, exist_ok=True)
        preload.write_text(
            "\n".join(
                [
                    "doc_id,fournisseur,numero_facture,date_facture,ttc,compte_propose,famille_charge,statut_controle,confidence",
                    "Q-1,QUESTION SERVICES,Q-2025-001,2025-02-01,999.00,601000,energie_eau,PROBABLE,preloaded",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.instance.payload.setdefault("settings", {}).setdefault("comptascope", {})["invoice_evidence_csv"] = (
            "./system/accounting/preloaded_invoice_evidence_2025.csv"
        )

        run = RunContext(self.instance, "accounting reconstruct")
        result = reconstruct_accounting(self.instance, run, 2025)
        run.finish("OK", "copyable syndic questions complete")

        self.assertEqual(result["expense_match_counts"], {"NON_RAPPROCHE": 1})
        self.assertEqual(result["syndic_question_count"], 1)
        _, guide_rows = read_csv(Path(str(result["controle_comptes_guide"])))
        self.assertEqual(guide_rows[0]["priorite"], "P1")
        self.assertEqual(guide_rows[0]["statut_rapprochement"], "NON_RAPPROCHE")
        self.assertIn("annexe comptable", guide_rows[0]["question_syndic"])
        self.assertNotIn("grand livre", guide_rows[0]["question_syndic"])
        _, group_rows = read_csv(Path(str(result["regroupement_controle_comptes"])))
        self.assertEqual(group_rows[0]["priorite"], "P1")
        self.assertEqual(group_rows[0]["questions_syndic"], "1")
        self.assertEqual(group_rows[0]["statut_rapprochement"], "NON_RAPPROCHE")
        questions_text = Path(str(result["questions_syndic_comptascope"])).read_text(encoding="utf-8")
        self.assertIn("Objet: Controle comptes 2025 - QUESTION SERVICES - Q-2025-001", questions_text)
        self.assertIn("```text", questions_text)

    def test_reconstruct_guides_when_expense_statement_is_missing(self) -> None:
        expense_statement = self.example_root / "system" / "accounting" / "expense_statement_lines_2025.csv"
        expense_statement.unlink()

        run = RunContext(self.instance, "accounting reconstruct")
        result = reconstruct_accounting(self.instance, run, 2025)
        run.finish("OK", "missing expense statement guided")

        self.assertEqual(result["expense_statement_line_count"], 0)
        self.assertEqual(result["expense_match_counts"], {})
        self.assertEqual(result["review_item_count"], 1)
        self.assertEqual(result["syndic_question_count"], 1)
        self.assertEqual(result["control_count"], 1)
        _, guide_rows = read_csv(Path(str(result["controle_comptes_guide"])))
        self.assertEqual(guide_rows[0]["priorite"], "P2")
        self.assertEqual(guide_rows[0]["statut_rapprochement"], "SANS_ETAT_DEPENSES")
        self.assertIn("etat des depenses", guide_rows[0]["question_syndic"])
        _, non_matches = read_csv(Path(str(result["non_rapproches_prioritaires"])))
        self.assertEqual(non_matches[0]["match_status"], "SANS_ETAT_DEPENSES")
        report_text = Path(str(result["report"])).read_text(encoding="utf-8")
        self.assertIn("Etat des depenses non exploite", report_text)

    def test_tools_status_shape(self) -> None:
        status = tools_status()
        self.assertIn("checks", status)
        self.assertTrue(any(check["name"] == "duckdb" for check in status["checks"]))
        self.assertTrue(any(check["name"] == "grist_api" for check in status["checks"]))

    def test_invoice_accounting_does_not_classify_beauvallon_as_water(self) -> None:
        account, family = factureops._account_for_invoice(
            "Abattage d'un pin colle au batiment 22 - Copropriete Beauvallon Pinede",
            "TY SERVICES",
        )

        self.assertEqual(account, "615000")
        self.assertEqual(family, "entretien_maintenance")

    def test_invoice_accounting_classifies_fire_safety_and_flags_quote_followup(self) -> None:
        account, family = factureops._account_for_invoice(
            "Maintenance preventive extincteurs avec frais de gestion dematerialisee",
            "FEU TEST",
        )

        self.assertEqual(account, "615000")
        self.assertEqual(family, "securite_incendie")
        self.assertEqual(
            factureops._fire_safety_anomalies("Extincteurs CO2 non satisfaisant, DLU depassee, a deviser."),
            ["SECURITE_INCENDIE_A_DEVISER"],
        )

    def test_factureops_extracts_invoice_evidence_and_anomalies(self) -> None:
        run = RunContext(self.instance, "invoices extract")
        result = extract_invoices(self.instance, run, 2025)
        run.finish("OK", "invoices extract complete")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["invoice_count"], 1)
        self.assertTrue(Path(str(result["invoice_evidence"])).exists())
        self.assertTrue(Path(str(result["invoice_anomalies"])).exists())
        _, invoices = read_csv(Path(str(result["invoice_evidence"])))
        self.assertEqual(invoices[0]["evidence_level"], "L1_NATIVE_TEXT")

    def test_factureops_prefers_docops_text_without_reopening_source_pdf(self) -> None:
        doc_id = "DOC-INVOICE-TEXT"
        pdf_path = self.example_root / "200_INBOX" / "facture_2025_source.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(b"%PDF-1.4\n% unread during this test\n")
        ocr_path = self.example_root / "200_INBOX" / "facture_2025_scan.pdf"
        ocr_path.write_bytes(b"%PDF-1.4\n% ocr required during this test\n")
        text_path = self.example_root / "staging" / "text" / f"{doc_id}.native.txt"
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(
            "\n".join(
                [
                    "Facture FAC-2025-777",
                    "Fournisseur Demo",
                    "Date 15/01/2025",
                    "Total TTC 1200,00",
                ]
            ),
            encoding="utf-8",
        )
        row = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        row.update(
            {
                "doc_id": doc_id,
                "sha256": "abc",
                "original_path": relative_to(self.example_root, pdf_path),
                "file_name": "facture_2025_source.pdf",
                "extension": "pdf",
                "document_type": "Facture",
                "status_ocr": "TEXT_EXTRACTED",
                "text_path": relative_to(self.example_root, text_path),
                "text_char_count": "80",
                "extraction_level": "L1_NATIVE_TEXT",
            }
        )
        ocr_row = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        ocr_row.update(
            {
                "doc_id": "DOC-INVOICE-OCR",
                "sha256": "def",
                "original_path": relative_to(self.example_root, ocr_path),
                "file_name": "facture_2025_scan.pdf",
                "extension": "pdf",
                "document_type": "Facture",
                "status_ocr": "OCR_REQUIRED",
                "text_char_count": "0",
            }
        )
        write_csv(self.instance.register("documents"), list(DEFAULT_DOCUMENT_FIELDS), [row, ocr_row])
        original_reader = factureops._read_source_text
        def guarded_reader(path: Path):
            if path in {pdf_path, ocr_path}:
                raise AssertionError("source pdf reopened")
            return original_reader(path)

        factureops._read_source_text = guarded_reader
        try:
            run = RunContext(self.instance, "invoices docops text")
            result = extract_invoices(self.instance, run, 2025)
            run.finish("OK", "invoices docops text complete")
        finally:
            factureops._read_source_text = original_reader

        _, invoices = read_csv(Path(str(result["invoice_evidence"])))
        invoice = next(row for row in invoices if row["doc_id"] == doc_id)
        self.assertFalse(any(row["doc_id"] == "DOC-INVOICE-OCR" for row in invoices))
        self.assertGreaterEqual(result["invoice_count"], 1)
        self.assertEqual(invoice["extraction_method"], "docops_text")
        self.assertEqual(invoice["evidence_level"], "L1_NATIVE_TEXT")

    def test_workers_invoices_scope_does_not_reconstruct_ledger(self) -> None:
        accounting_dir = self.example_root / "outputs" / "accounting"
        if accounting_dir.exists():
            shutil.rmtree(accounting_dir)
        run = RunContext(self.instance, "workers invoices")
        result = run_workers(self.instance, run, scope="invoices", year=2025)
        run.finish("OK", "workers invoices complete")

        self.assertEqual([action["worker"] for action in result["actions"]], ["invoice_worker"])
        self.assertTrue((accounting_dir / "2025" / "invoice_evidence_2025.csv").exists())
        self.assertTrue((accounting_dir / "2025" / "invoice_anomalies_2025.csv").exists())
        self.assertFalse((accounting_dir / "2025" / "ledger_reconstruction_2025.csv").exists())

    def test_reconciliation_explains_ambiguous_repeated_amounts(self) -> None:
        invoices = [
            {"doc_id": "DOC-1", "fournisseur": "ASV", "numero_facture": "F1", "ttc": "198.00", "compte_propose": "615000", "famille_charge": "entretien_maintenance"},
            {"doc_id": "DOC-2", "fournisseur": "ASV", "numero_facture": "F2", "ttc": "198.00", "compte_propose": "615000", "famille_charge": "entretien_maintenance"},
        ]
        expenses = [
            {
                "statement_line_id": "DEP-1",
                "account": "615000",
                "reference": "X1",
                "supplier_hint": "ASV",
                "label": "ASV / intervention",
                "amount": "198.00",
            }
        ]

        matches = reconcile_invoice_expenses(invoices, expenses)

        self.assertEqual(matches[0]["match_status"], "CANDIDAT_MONTANT_AMBIGU")
        self.assertIn("plusieurs factures", matches[0]["match_reason"])

    def test_reconciliation_can_infer_repeated_supplier_aliases(self) -> None:
        invoices = [
            {
                "doc_id": "DOC-1",
                "fournisseur": "EAU EXEMPLE",
                "numero_facture": "EAU-1",
                "ttc": "120.00",
                "compte_propose": "601000",
                "famille_charge": "energie_eau",
            },
            {
                "doc_id": "DOC-2",
                "fournisseur": "EAU EXEMPLE",
                "numero_facture": "EAU-2",
                "ttc": "240.00",
                "compte_propose": "601000",
                "famille_charge": "energie_eau",
            },
        ]
        expenses = [
            {
                "statement_line_id": "DEP-1",
                "account": "601000",
                "reference": "COMPTEUR-1",
                "supplier_hint": "EAUCO",
                "label": "EAUCO / compteur 1",
                "amount": "120.00",
            },
            {
                "statement_line_id": "DEP-2",
                "account": "601000",
                "reference": "COMPTEUR-2",
                "supplier_hint": "EAUCO",
                "label": "EAUCO / compteur 2",
                "amount": "240.00",
            },
        ]

        suggestions = suggest_supplier_aliases(invoices, expenses)
        aliases = supplier_aliases_from_suggestions(suggestions)
        matches = reconcile_invoice_expenses(invoices, expenses, aliases)

        self.assertEqual(suggestions[0]["suggestion_status"], "AUTO_APPLICABLE")
        self.assertEqual(suggestions[0]["suggested_alias"], "EAUCO")
        self.assertEqual(matches[0]["match_status"], "MATCH_AMOUNT_ALIAS")

    def test_reconciliation_uses_local_name_similarity_as_p2_candidate(self) -> None:
        invoices = [
            {
                "doc_id": "DOC-SIM",
                "fournisseur": "A.M VINCENTELLI RENOVATION",
                "numero_facture": "FC3869",
                "ttc": "764.50",
                "compte_propose": "615000",
                "famille_charge": "entretien_maintenance",
            }
        ]
        expenses = [
            {
                "statement_line_id": "DEP-SIM",
                "account": "615000",
                "reference": "INTERVENTION",
                "supplier_hint": "AM VINCENTELLI",
                "label": "AM VINCENTELLI / coffrage placo",
                "amount": "764.50",
            }
        ]

        matches = reconcile_invoice_expenses(invoices, expenses)

        self.assertEqual(matches[0]["match_status"], "CANDIDAT_NOM_SIMILAIRE")
        self.assertEqual(matches[0]["match_priority"], "P2")

    def test_reconciliation_identifies_grouped_invoices_candidate(self) -> None:
        invoices = [
            {"doc_id": "DOC-G1", "fournisseur": "ACME SERVICES", "numero_facture": "G1", "ttc": "100.00", "compte_propose": "615000", "famille_charge": "entretien_maintenance"},
            {"doc_id": "DOC-G2", "fournisseur": "ACME SERVICES", "numero_facture": "G2", "ttc": "150.00", "compte_propose": "615000", "famille_charge": "entretien_maintenance"},
        ]
        expenses = [
            {
                "statement_line_id": "DEP-G",
                "account": "615000",
                "reference": "REGROUP",
                "supplier_hint": "ACME SERVICES",
                "label": "ACME SERVICES / regroupement interventions",
                "amount": "250.00",
            }
        ]

        matches = reconcile_invoice_expenses(invoices, expenses)

        self.assertEqual({row["match_status"] for row in matches}, {"CANDIDAT_REGROUPEMENT_FACTURES"})
        self.assertTrue(all(row["match_priority"] == "P2" for row in matches))

    def test_reconciliation_identifies_equal_division_candidate(self) -> None:
        invoices = [
            {"doc_id": "DOC-DIV", "fournisseur": "EAU EXEMPLE", "numero_facture": "D1", "ttc": "300.00", "compte_propose": "601000", "famille_charge": "energie_eau"}
        ]
        expenses = [
            {"statement_line_id": "DEP-D1", "account": "601000", "reference": "C1", "supplier_hint": "EAU EXEMPLE", "label": "EAU EXEMPLE / compteur 1", "amount": "100.00"},
            {"statement_line_id": "DEP-D2", "account": "601000", "reference": "C2", "supplier_hint": "EAU EXEMPLE", "label": "EAU EXEMPLE / compteur 2", "amount": "100.00"},
            {"statement_line_id": "DEP-D3", "account": "601000", "reference": "C3", "supplier_hint": "EAU EXEMPLE", "label": "EAU EXEMPLE / compteur 3", "amount": "100.00"},
        ]

        matches = reconcile_invoice_expenses(invoices, expenses)

        self.assertEqual(matches[0]["match_status"], "CANDIDAT_DIVISION_EGALE")
        self.assertEqual(matches[0]["match_priority"], "P2")

    def test_equal_division_requires_unique_local_candidate(self) -> None:
        invoices = [
            {"doc_id": "DOC-DIV-AMB", "fournisseur": "EAU EXEMPLE", "numero_facture": "D2", "ttc": "300.00", "compte_propose": "601000", "famille_charge": "energie_eau"}
        ]
        expenses = [
            {"statement_line_id": "DEP-DA1", "account": "601000", "reference": "C1", "supplier_hint": "EAU EXEMPLE", "label": "EAU EXEMPLE / compteur 1", "amount": "100.00"},
            {"statement_line_id": "DEP-DA2", "account": "601000", "reference": "C2", "supplier_hint": "EAU EXEMPLE", "label": "EAU EXEMPLE / compteur 2", "amount": "100.00"},
            {"statement_line_id": "DEP-DA3", "account": "601000", "reference": "C3", "supplier_hint": "EAU EXEMPLE", "label": "EAU EXEMPLE / compteur 3", "amount": "100.00"},
            {"statement_line_id": "DEP-DA4", "account": "601000", "reference": "C4", "supplier_hint": "EAU EXEMPLE", "label": "EAU EXEMPLE / compteur 4", "amount": "100.00"},
        ]

        matches = reconcile_invoice_expenses(invoices, expenses)

        self.assertEqual(matches[0]["match_status"], "CANDIDAT_VENTILATION_AMBIGUE")
        self.assertEqual(matches[0]["match_priority"], "P2")

    def test_reconstruct_can_start_from_preloaded_invoice_csv(self) -> None:
        preload = self.example_root / "system" / "accounting" / "preloaded_invoice_evidence_2025.csv"
        preload.parent.mkdir(parents=True, exist_ok=True)
        preload.write_text(
            "\n".join(
                [
                    "doc_id,fournisseur,numero_facture,date_facture,ttc,compte_propose,famille_charge,statut_controle,confidence",
                    "PRE-1,PRELOADED SERVICES,PRE-2025-001,2025-02-01,42.00,615000,entretien_maintenance,PROBABLE,preloaded",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.instance.payload.setdefault("settings", {}).setdefault("comptascope", {})["invoice_evidence_csv"] = (
            "./system/accounting/preloaded_invoice_evidence_2025.csv"
        )

        run = RunContext(self.instance, "accounting reconstruct")
        result = reconstruct_accounting(self.instance, run, 2025)
        run.finish("OK", "preloaded accounting complete")

        _, invoices = read_csv(Path(str(result["invoice_evidence"])))
        self.assertEqual(result["invoice_count"], 1)
        self.assertEqual(invoices[0]["fournisseur"], "PRELOADED SERVICES")
        self.assertEqual(invoices[0]["ttc"], "42.00")
        self.assertEqual(invoices[0]["evidence_level"], "L0_STRUCTURED_SOURCE")

    def test_supplier_due_diligence_reuses_existing_methodology(self) -> None:
        preload = self.example_root / "system" / "accounting" / "preloaded_invoice_evidence_2025.csv"
        preload.parent.mkdir(parents=True, exist_ok=True)
        preload.write_text(
            "\n".join(
                [
                    "doc_id,exercice,fournisseur,siren_siret,numero_facture,date_facture,ttc,compte_propose,famille_charge,statut_controle,confidence,anomalies",
                    "DD-1,2025,ACME SERVICES,,AC-2025-001,2025-02-01,3000.00,615000,entretien_maintenance,BLOQUE_COMPTA,preloaded,SIREN_SIRET_ABSENT|DILIGENCE_REQUISE",
                    "DD-2,2024,ACME SERVICES,,AC-2024-001,2024-12-15,1200.00,615000,entretien_maintenance,BLOQUE_COMPTA,preloaded,DILIGENCE_REQUISE",
                    "DD-3,2025,OMEGA ASCENSEUR,,OM-2025-001,2025-03-01,1800.00,615000,entretien_maintenance,BLOQUE_COMPTA,preloaded,DILIGENCE_REQUISE",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        matrices_dir = self.example_root / "system" / "matrices"
        admin_controls = matrices_dir / "controles_administratifs.csv"
        admin_controls.write_text(
            "\n".join(
                [
                    "controle_id,producteur_piece,famille_piece,controle_a_produire,preuve_attendue,risque_couvert,priorite,diligence_liee,statut,notes",
                    "ADM-005,Prestataire,Devis contrat facture,Verifier identite juridique exacte,SIREN/SIRET,Risque homonyme,P0,DIL-DD-003,A_PRODUIRE,",
                    "ADM-010,Entreprise travaux,Devis marche,Verifier assurance et qualification,Attestations,Risque travaux non couverts,P0,DIL-DD-005,A_PRODUIRE,",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        results = matrices_dir / "background_results.csv"
        results.write_text(
            "\n".join(
                [
                    "resultat_id,acteur,controle,sources_utilisees,resultat_premiere_passe,qualification,action_suite,diligence_liee,statut",
                    "BGC-RES-TEST,ACME SERVICES,RNE/API,API Recherche Entreprises,Controle recent existant,IDENTITE_ACTIVE_A_RECOUPER,Produire pieces primaires,DIL-DD-003,EN_COURS",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        register_results = matrices_dir / "registre_constats.csv"
        register_results.write_text(
            "\n".join(
                [
                    "constat_id,fact_summary,next_action,diligence_id",
                    "CST-OMEGA,Le contrat OMEGA Ascenseur est deja instruit dans un controle recent,Demander avis CS et mise en concurrence,DIL-DD-014",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.instance.payload.setdefault("settings", {}).setdefault("comptascope", {})["invoice_evidence_csv"] = (
            "./system/accounting/preloaded_invoice_evidence_2025.csv"
        )
        self.instance.payload["settings"]["comptascope"]["supplier_due_diligence"] = {
            "admin_controls_csv": "./system/matrices/controles_administratifs.csv",
            "result_csv": [
                "./system/matrices/background_results.csv",
                "./system/matrices/registre_constats.csv",
            ],
        }

        run = RunContext(self.instance, "accounting reconstruct")
        result = reconstruct_accounting(self.instance, run, 2025)
        run.finish("OK", "supplier due diligence complete")

        self.assertEqual(result["supplier_due_diligence_count"], 3)
        _, rows = read_csv(Path(str(result["supplier_due_diligence_controls"])))
        self.assertEqual(rows[0]["coverage_status"], "COUVERT_RECENT_A_RECOUPER")
        self.assertIn("BGC-RES-TEST", rows[0]["existing_result_refs"])
        self.assertIn("ADM-005", rows[0]["controls_to_apply"])
        self.assertIn("DIL-DD-003", rows[0]["diligence_liee"])
        omega_row = next(row for row in rows if row["fournisseur"] == "OMEGA ASCENSEUR")
        self.assertIn("CST-OMEGA", omega_row["existing_result_refs"])
        self.assertIn("Diligences fournisseur", Path(str(result["report"])).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
