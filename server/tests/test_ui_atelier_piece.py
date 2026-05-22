from __future__ import annotations

import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from urllib.parse import unquote

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, load_instance, write_csv
from coproscope.modules.accounting import ACCOUNTING_CONTROL_FIELDS
from coproscope.modules import decisionops, docuscope, incidentops
from coproscope.web.viewmodel import build_dashboard_model


def _html_hrefs(html: str) -> list[str]:
    import re

    return re.findall(r"""href=["']([^"']+)["']""", html)


class AtelierPieceUiTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _seed_workshop_outputs(self) -> None:
        reports_dir = self.instance.artifact("reports_dir")
        write_csv(
            self.instance.register("documents"),
            DEFAULT_DOCUMENT_FIELDS,
            [
                {
                    "doc_id": "DOC-AG",
                    "filename": "pv_ag_2025.txt",
                    "relative_path": "docs/pv_ag_2025.txt",
                    "lot": "ag",
                    "document_type": "PV_AG",
                    "classification_status": "AUTO_CLASSIFIED",
                    "policy_confidence": "high",
                    "privacy_review_status": "DIFFUSABLE_BRUT",
                },
                {
                    "doc_id": "DOC-OLD",
                    "filename": "assurance_2023.txt",
                    "relative_path": "docs/assurance_2023.txt",
                    "lot": "assurance",
                    "document_type": "Attestation_Assurance",
                    "classification_status": "A_CLASSER",
                    "policy_confidence": "medium",
                    "privacy_review_status": "A_ARBITRER",
                },
            ],
        )
        write_csv(
            reports_dir / "matrice_completude_documentaire.csv",
            docuscope.COMPLETENESS_FIELDS,
            [
                {
                    "proof_id": "PRV-PV",
                    "lot": "ag",
                    "expected_label": "PV AG signe",
                    "document_type": "PV_AG",
                    "status": "PRESENT",
                    "criticality": "P1",
                    "freshness_months": "",
                    "matched_doc_ids": "DOC-AG",
                    "evidence_paths": "DOC-AG:pv_ag_2025.txt",
                    "newest_date": "2025-05-01",
                    "reason": "Piece presente.",
                    "action": "Aucune demande.",
                },
                {
                    "proof_id": "PRV-CONTRAT",
                    "lot": "contrats",
                    "expected_label": "Contrat syndic signe",
                    "document_type": "Contrat_Syndic",
                    "status": "ABSENT",
                    "criticality": "P1",
                    "freshness_months": "",
                    "matched_doc_ids": "",
                    "evidence_paths": "",
                    "newest_date": "",
                    "reason": "Aucune piece locale ne correspond au type attendu.",
                    "action": "Demander la piece au syndic.",
                },
                {
                    "proof_id": "PRV-ASSURANCE",
                    "lot": "assurance",
                    "expected_label": "Attestation assurance recente",
                    "document_type": "Attestation_Assurance",
                    "status": "OBSOLETE",
                    "criticality": "P2",
                    "freshness_months": "12",
                    "matched_doc_ids": "DOC-OLD",
                    "evidence_paths": "DOC-OLD:assurance_2023.txt",
                    "newest_date": "2023-01-01",
                    "reason": "Version trop ancienne.",
                    "action": "Demander une version recente.",
                },
            ],
        )
        write_csv(
            reports_dir / "pieces_a_demander.csv",
            docuscope.DOCUMENT_REQUEST_FIELDS,
            [
                {
                    "request_id": "REQ-DOC-PRV-CONTRAT",
                    "source_ref": "PRV-CONTRAT",
                    "priority": "P1",
                    "status": "ABSENT",
                    "subject": "Demander au syndic: Contrat syndic signe",
                    "expected_piece": "Contrat syndic signe",
                    "reason": "Aucune piece locale ne correspond au type attendu.",
                    "related_doc_ids": "",
                    "evidence_paths": "",
                    "suggested_diligence": "Demander la piece au syndic et rattacher sa reponse au registre.",
                }
            ],
        )
        write_csv(
            decisionops.decision_register_path(self.instance),
            decisionops.DECISION_ACTION_FIELDS,
            [
                {
                    "decision_action_id": "DAP-001",
                    "ag_id": "AG-2025",
                    "source_doc_id": "DOC-AG",
                    "source_file": "pv_ag_2025.txt",
                    "resolution_ref": "R01",
                    "decision_text": "Resolution 1 - travaux toiture votes.",
                    "action_attendue": "Demander le devis signe, le calendrier et la preuve de reception.",
                    "responsable": "Syndic / commission travaux",
                    "echeance": "2025-06-15",
                    "preuve_attendue": "Devis vote et ordre de service.",
                    "proof_doc_ids": "",
                    "proof_document_types": "",
                    "related_request_ids": "",
                    "related_invoice_refs": "",
                    "related_work_refs": "",
                    "statut": "PREUVE_A_DEMANDER",
                    "priorite": "P1",
                    "notes": "Aucune preuve locale rattachee automatiquement.",
                }
            ],
        )
        write_csv(
            incidentops.incident_register_path(self.instance),
            incidentops.INCIDENT_FIELDS,
            [
                {
                    "incident_id": "INC-001",
                    "date_signalement": "2025-05-02",
                    "lieu": "Hall",
                    "description": "Infiltration signalee apres pluie.",
                    "piece_ref": "mail_syndic.txt",
                    "doc_ids": "",
                    "photo_or_piece": "",
                    "syndic_or_provider": "Syndic",
                    "status": "EN_COURS",
                    "priority": "P1",
                    "next_action": "Relancer le syndic sur la date d'intervention.",
                    "action_due_date": "2025-05-09",
                    "expected_closure_proof": "Bon d'intervention ou photo apres resolution.",
                    "closure_proof_ref": "",
                    "contract_or_insurance_ref": "",
                    "source_refs": "mail_syndic.txt",
                    "notes": "",
                }
            ],
        )

    def test_piece_workshop_links_pieces_points_actions_and_proofs(self) -> None:
        self._seed_workshop_outputs()

        model = build_dashboard_model(self.instance, 2025)
        workshop = model["piece_workshop"]

        self.assertEqual(workshop["summary"]["total"], 5)
        self.assertEqual(workshop["summary"]["docops"], 3)
        self.assertEqual(workshop["summary"]["decisions"], 1)
        self.assertEqual(workshop["summary"]["incidents"], 1)
        self.assertGreaterEqual(workshop["summary"]["needs_action"], 4)
        self.assertGreaterEqual(workshop["summary"]["with_local_proof"], 2)

        items = workshop["items"]
        self.assertTrue(
            any(
                item["piece"] == "Contrat syndic signe"
                and item["point"] == "contrats"
                and item["next_step"] == "Demander la piece au syndic et rattacher sa reponse au registre."
                for item in items
            )
        )
        self.assertTrue(
            any(item["point_type"] == "Decision AG" and "R01" in item["point"] for item in items)
        )
        self.assertTrue(
            any(
                item["point_type"] == "Incident"
                and item["piece"] == "Bon d'intervention ou photo apres resolution."
                for item in items
            )
        )

        try:
            from fastapi.testclient import TestClient  # type: ignore
            from coproscope.web.app import create_app
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        client = TestClient(create_app(self.instance, 2025))
        response = client.get("/pieces")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Atelier pieces", text)
        self.assertIn("Contrat syndic signe", text)
        self.assertIn("Point de rattachement", text)
        self.assertIn("R01", text)
        self.assertIn("Bon d'intervention ou photo apres resolution.", text)
        self.assertIn('data-href="/documents"', text)
        self.assertIn('data-href="/chantiers"', text)
        self.assertIn("Action primaire", text)
        self.assertIn("preuve manquante", text)
        self.assertIn("preuve locale", text)
        self.assertIn("signature attendue", text)
        self.assertIn("confidentialite A_ARBITRER", text)
        self.assertIn("confiance medium", text)
        self.assertIn("Ouvrir", text)

    def test_missing_pieces_view_renders_actionable_novice_cards(self) -> None:
        self._seed_workshop_outputs()

        try:
            from fastapi.testclient import TestClient  # type: ignore
            from coproscope.web.app import create_app
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        client = TestClient(create_app(self.instance, 2025))
        response = client.get("/pieces?proof=missing")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Pieces manquantes", text)
        self.assertIn("Pieces attendues", text)
        self.assertIn("Contrat syndic signe", text)
        self.assertIn("Creer demandes syndic", text)
        self.assertIn("Voir pieces privees", text)
        self.assertIn("Pourquoi", text)
        self.assertIn("Detenteur", text)
        self.assertIn("Lien", text)
        self.assertIn("Preuve attendue", text)
        self.assertIn("Syndic ou detenteur a confirmer", text)
        self.assertIn("Relancer syndic", text)
        self.assertIn("Ajouter reponse recue", text)
        self.assertIn("Question", text)
        self.assertIn("Ouvrir action", text)
        self.assertIn("Voir action", text)
        self.assertIn('href="/demandes/relance?action_id=PRV-CONTRAT', text)
        self.assertIn('href="/depot?intent=proof&amp;missing_for=PRV-CONTRAT', response.text)
        self.assertIn("status=reponse-recue", response.text)
        self.assertIn("return=pieces", response.text)
        self.assertIn('href="/actions?selected=', text)
        self.assertNotIn("Completude passation", text)
        self.assertNotIn("Envoyer automatiquement", text)

    def test_missing_pieces_view_falls_back_to_accounting_p1_when_piece_contract_is_empty(self) -> None:
        for path in [
            self.instance.register("documents"),
            self.instance.artifact("reports_dir") / "matrice_completude_documentaire.csv",
            self.instance.artifact("reports_dir") / "pieces_a_demander.csv",
            decisionops.decision_register_path(self.instance),
            incidentops.incident_register_path(self.instance),
        ]:
            path.unlink(missing_ok=True)

        shutil.rmtree(self.instance.artifact("accounting_dir"), ignore_errors=True)
        accounting_dir = self.instance.artifact("accounting_dir") / "2025"
        accounting_dir.mkdir(parents=True, exist_ok=True)
        write_csv(accounting_dir / "accounting_controls_2025.csv", ACCOUNTING_CONTROL_FIELDS, [])
        write_csv(
            accounting_dir / "controles_p1_2025.csv",
            ACCOUNTING_CONTROL_FIELDS,
            [
                {
                    "control_id": "CTRL-ASC",
                    "exercice": "2025",
                    "severity": "P1",
                    "control": "Facture ascenseur sans justificatif",
                    "status": "A_TRAITER",
                    "doc_id": "DOC-ASC",
                    "evidence": "Facture ascenseur T1 2025",
                    "action": "Demander la facture et la ligne de charge au syndic.",
                },
                {
                    "control_id": "CTRL-ENT",
                    "exercice": "2025",
                    "severity": "P1",
                    "control": "Contrat entretien ascenseur a fournir",
                    "status": "A_TRAITER",
                    "doc_id": "DOC-CONTRAT-ASC",
                    "evidence": "Contrat entretien ascenseur",
                    "action": "Demander le contrat signe au syndic.",
                },
            ],
        )

        try:
            from fastapi.testclient import TestClient  # type: ignore
            from coproscope.web.app import create_app
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        client = TestClient(create_app(self.instance, 2025))
        comptes_text = unescape(client.get("/comptes").text)
        pieces_text = unescape(client.get("/pieces?proof=missing").text)

        self.assertIn("Pieces manquantes", comptes_text)
        self.assertIn("<strong>2</strong>", client.get("/comptes").text)
        self.assertIn("2 pieces concretes a traiter", pieces_text)
        self.assertIn("Facture ascenseur sans justificatif", pieces_text)
        self.assertIn("Contrat entretien ascenseur a fournir", pieces_text)
        self.assertIn('href="/demandes/relance?', pieces_text)
        self.assertIn('href="/depot?intent=proof', pieces_text)
        self.assertIn('href="/comptes?', pieces_text)
        self.assertIn("Ouvrir compte", pieces_text)
        self.assertIn("Voir action", pieces_text)
        self.assertNotIn("Aucune piece manquante detectee.", pieces_text)

    def test_missing_pieces_view_tokenizes_all_local_ctas_without_private_leaks(self) -> None:
        self._seed_workshop_outputs()

        try:
            from fastapi.testclient import TestClient  # type: ignore
            from coproscope.web.app import create_app
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        client = TestClient(create_app(self.instance, 2025, access_token="local-secret"))
        response = client.get("/pieces?proof=missing&token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Ajouter reponse recue", text)
        self.assertNotRegex(text, r"file://|raw[\\/]|restricted[\\/]|logs[\\/]|private[\\/]|C:\\Users")
        for href in _html_hrefs(response.text):
            decoded = unquote(unescape(href))
            if decoded.startswith("http://testserver/static/") or decoded.startswith("#"):
                continue
            self.assertTrue(decoded.startswith("/"), decoded)
            self.assertNotIn("\\", decoded)
            self.assertIn("token=local-secret", decoded, decoded)

    def test_piece_workshop_page_handles_empty_outputs(self) -> None:
        for path in [
            self.instance.register("documents"),
            self.instance.artifact("reports_dir") / "matrice_completude_documentaire.csv",
            self.instance.artifact("reports_dir") / "pieces_a_demander.csv",
            decisionops.decision_register_path(self.instance),
            incidentops.incident_register_path(self.instance),
        ]:
            path.unlink(missing_ok=True)
        shutil.rmtree(self.instance.artifact("accounting_dir"), ignore_errors=True)

        try:
            from fastapi.testclient import TestClient  # type: ignore
            from coproscope.web.app import create_app
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        client = TestClient(create_app(self.instance, 2025))
        response = client.get("/pieces")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Atelier pieces", text)
        self.assertIn("Aucune piece exploitable dans les artefacts charges.", text)

        missing_response = client.get("/pieces?proof=missing")
        missing_text = unescape(missing_response.text)

        self.assertEqual(missing_response.status_code, 200)
        self.assertIn("Aucune piece a demander pour le moment", missing_text)
        self.assertIn("Voir toutes les pieces", missing_text)
        self.assertIn("Retour au cockpit", missing_text)
        self.assertNotIn("Relancer le syndic", missing_text)


if __name__ == "__main__":
    unittest.main()
