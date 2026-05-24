from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlparse

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, load_instance, write_csv
from coproscope.modules import decisionops, docuscope, incidentops
from coproscope.web.viewmodel import build_dashboard_model


FORBIDDEN_UX_MARKERS = ("raw", "restricted", "logs", "private", "file://", "payload")


def _hrefs(value: object, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            next_path = f"{path}.{key}"
            if (key == "href" or key.endswith("_href")) and isinstance(child, str) and child:
                yield next_path, child
            yield from _hrefs(child, next_path)
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _hrefs(child, f"{path}[{index}]")


class PiecesViewmodelContractTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def assertLocalHref(self, href: str, path: str) -> None:
        decoded = unquote(href)
        parsed = urlparse(decoded)
        self.assertFalse(parsed.scheme or parsed.netloc, f"{path} must be local: {href!r}")
        self.assertTrue(decoded.startswith("/") or decoded.startswith("#"), f"{path} must be a local path: {href!r}")
        self.assertNotIn("\\", decoded, f"{path} must not contain backslashes: {href!r}")
        self.assertNotIn("://", decoded, f"{path} must not contain a URL scheme: {href!r}")

    def assertNoForbiddenUxMarkers(self, payload: object) -> None:
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).replace("\\", "/").lower()
        self.assertNotIn(str(self.instance_root).replace("\\", "/").lower(), serialized)
        for marker in FORBIDDEN_UX_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotRegex(serialized, rf"(^|[^a-z]){marker}([^a-z]|$)")

    def _seed_piece_contract_outputs(self) -> None:
        reports_dir = self.instance.artifact("reports_dir")
        reports_dir.mkdir(parents=True, exist_ok=True)
        write_csv(decisionops.decision_register_path(self.instance), decisionops.DECISION_ACTION_FIELDS, [])
        write_csv(incidentops.incident_register_path(self.instance), incidentops.INCIDENT_FIELDS, [])
        write_csv(
            self.instance.register("documents"),
            DEFAULT_DOCUMENT_FIELDS,
            [
                {
                    "doc_id": "DOC-OLD",
                    "filename": "assurance_2024.txt",
                    "relative_path": "docs/assurance_2024.txt",
                    "lot": "assurance",
                    "document_type": "Attestation_Assurance",
                    "classification_status": "A_CLASSER",
                    "policy_confidence": "medium",
                    "privacy_review_status": "A_ARBITRER",
                }
            ],
        )
        write_csv(
            reports_dir / "matrice_completude_documentaire.csv",
            docuscope.COMPLETENESS_FIELDS,
            [
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
                    "reason": "Contrat necessaire pour reprendre les obligations.",
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
                    "evidence_paths": "DOC-OLD:assurance_2024.txt",
                    "newest_date": "2024-01-01",
                    "reason": "Version trop ancienne.",
                    "action": "Verifier si une version plus recente existe.",
                },
            ],
        )
        write_csv(
            reports_dir / "pieces_a_demander.csv",
            docuscope.DOCUMENT_REQUEST_FIELDS,
            [
                {
                    "request_id": "REQ-CONTRAT",
                    "source_ref": "PRV-CONTRAT",
                    "priority": "P1",
                    "status": "ABSENT",
                    "subject": "Contrat syndic signe",
                    "expected_piece": "Contrat syndic signe",
                    "reason": "Contrat necessaire pour reprendre les obligations.",
                    "related_doc_ids": "",
                    "evidence_paths": "",
                    "suggested_diligence": "Demander la derniere version signee au syndic.",
                }
            ],
        )

    def _clear_piece_sources(self) -> None:
        for path in [
            self.instance.register("documents"),
            self.instance.artifact("reports_dir") / "matrice_completude_documentaire.csv",
            self.instance.artifact("reports_dir") / "pieces_a_demander.csv",
            decisionops.decision_register_path(self.instance),
            incidentops.incident_register_path(self.instance),
        ]:
            path.unlink(missing_ok=True)

    def _clear_accounting_sources(self) -> None:
        shutil.rmtree(self.instance.artifact("accounting_dir"), ignore_errors=True)
        try:
            shutil.rmtree(self.instance.root("outputs") / "accounting_2025_factures", ignore_errors=True)
        except KeyError:
            pass

    def _seed_accounting_missing_pieces(self) -> None:
        self._clear_piece_sources()
        self._clear_accounting_sources()
        accounting_dir = self.instance.artifact("accounting_dir") / "2025"
        accounting_dir.mkdir(parents=True, exist_ok=True)
        (accounting_dir / "summary_2025.json").write_text(json.dumps({"invoice_count": 2}), encoding="utf-8")
        write_csv(
            accounting_dir / "non_rapproches_prioritaires_2025.csv",
            [
                "doc_id",
                "fournisseur",
                "numero_facture",
                "ttc",
                "match_status",
                "match_priority",
                "match_reason",
                "next_action",
                "categorie",
            ],
            [
                {
                    "doc_id": "DOC-EAU-MISSING",
                    "fournisseur": "EAUX EXEMPLE",
                    "numero_facture": "E-2025-04",
                    "ttc": "120.00",
                    "match_status": "NON_RAPPROCHE",
                    "match_priority": "P1",
                    "match_reason": "Facture sans ligne de depense rattachee.",
                    "next_action": "Demander le justificatif et la ligne comptable au syndic.",
                    "categorie": "energie",
                },
                {
                    "doc_id": "DOC-JARDIN-MISSING",
                    "fournisseur": "JARDINS EXEMPLE",
                    "numero_facture": "J-2025-01",
                    "ttc": "300.00",
                    "match_status": "MISSING_ATTACHMENT",
                    "match_priority": "P1",
                    "match_reason": "Bon de commande ou decision manquante.",
                    "next_action": "Demander la piece de validation au syndic.",
                    "categorie": "entretien",
                },
            ],
        )
        write_csv(accounting_dir / "invoice_evidence_2025.csv", ["doc_id", "fournisseur", "numero_facture", "ttc"], [])
        write_csv(accounting_dir / "invoice_expense_matches_2025.csv", ["doc_id", "match_status"], [])
        write_csv(accounting_dir / "invoice_anomalies_2025.csv", ["anomaly_id", "doc_id"], [])
        write_csv(accounting_dir / "accounting_controls_2025.csv", ["control_id", "control"], [])
        write_csv(accounting_dir / "controles_p1_2025.csv", ["control_id", "control"], [])

    def test_ux_pieces_contract_links_missing_items_to_relance_depot_and_documents(self) -> None:
        self._seed_piece_contract_outputs()

        pieces = build_dashboard_model(self.instance, 2025)["ux"]["pieces"]

        self.assertEqual(pieces["context"]["route"], "/pieces?proof=missing")
        self.assertEqual(pieces["context"]["title"], "Pieces manquantes")
        self.assertGreaterEqual(pieces["summary"]["missing_count"], 1)
        self.assertGreaterEqual(pieces["summary"]["to_verify_count"], 1)
        self.assertGreaterEqual(pieces["summary"]["linked_documents_count"], 1)
        self.assertFalse(pieces["empty_state"]["is_visible"])

        by_piece = {item["expected_piece"]: item for item in pieces["items"]}
        missing = by_piece["Contrat syndic signe"]
        candidate = by_piece["Attestation assurance recente"]

        self.assertEqual(missing["status"], "a_demander")
        self.assertEqual(missing["novice_status"]["label"], "Il faut demander ce document")
        self.assertTrue(missing["request_href"].startswith("/demandes/relance"))
        self.assertTrue(missing["deposit_href"].startswith("/depot"))
        self.assertEqual(missing["primary_action"]["id"], "prepare-relance")
        self.assertIn("REQ-CONTRAT", missing["request_href"])

        self.assertEqual(candidate["status"], "a_verifier")
        self.assertEqual(candidate["novice_status"]["label"], "Un document local existe")
        self.assertEqual(candidate["linked_documents"][0]["id"], "DOC-OLD")
        self.assertEqual(candidate["linked_documents"][0]["href"], "/documents?doc_id=DOC-OLD")
        self.assertEqual(candidate["primary_action"]["id"], "verify-document")

        action_hrefs = {action["id"]: action["href"] for action in missing["actions"]}
        self.assertTrue(action_hrefs["prepare-relance"].startswith("/demandes/relance"))
        self.assertTrue(action_hrefs["add-from-depot"].startswith("/depot"))

        self.assertNoForbiddenUxMarkers(pieces)
        for path, href in _hrefs(pieces):
            with self.subTest(href_path=path):
                self.assertLocalHref(href, path)

    def test_ux_pieces_and_nav_use_missing_accounting_pieces_when_docops_is_empty(self) -> None:
        self._seed_accounting_missing_pieces()

        ux = build_dashboard_model(self.instance, 2025)["ux"]
        pieces = ux["pieces"]
        missing_view = ux["priority_views"]["missing_pieces"]
        comptes_summary = ux["comptes"]["summary"]
        nav_items = [
            item
            for section in ux["shell"]["nav_sections"]
            for item in section["items"]
            if item["label"] == "Pieces manquantes"
        ]
        summary_cards = {
            card["id"]: card
            for card in ux["cockpit"]["summary_cards"]
        }

        self.assertEqual(comptes_summary["missing_pieces_count"], 2)
        self.assertEqual(pieces["summary"]["missing_count"], 2)
        self.assertEqual(missing_view["summary"]["total"], 2)
        self.assertEqual(nav_items[0]["count"], 2)
        self.assertEqual(summary_cards["missing-pieces"]["count"], 2)
        self.assertFalse(pieces["empty_state"]["is_visible"])
        self.assertEqual({item["source_label"] for item in pieces["missing"]}, {"ComptaScope"})

        for item in missing_view["items"]:
            self.assertEqual(item["rubric_label"], "Comptes et factures")
            self.assertTrue(item["request_href"].startswith("/demandes/relance"))
            self.assertTrue(item["deposit_href"].startswith("/depot"))
            self.assertTrue(item["action_href"].startswith("/comptes"))
            self.assertIn("Justificatif comptable", item["proof_expected_label"])
            self.assertTrue(item["owner_label"])

        self.assertNoForbiddenUxMarkers({"pieces": pieces, "missing_view": missing_view})
        for path, href in _hrefs({"pieces": pieces, "missing_view": missing_view}):
            with self.subTest(href_path=path):
                self.assertLocalHref(href, path)

    def test_ux_pieces_empty_state_exposes_fictive_examples_without_counting_them_as_real_items(self) -> None:
        self._clear_piece_sources()
        self._clear_accounting_sources()

        pieces = build_dashboard_model(self.instance, 2025)["ux"]["pieces"]

        self.assertTrue(pieces["empty_state"]["is_visible"])
        self.assertEqual(pieces["summary"]["total_actionable"], 0)
        self.assertEqual(pieces["summary"]["fictive_count"], len(pieces["empty_state"]["examples"]))
        self.assertTrue(pieces["empty_state"]["examples"])
        for example in pieces["empty_state"]["examples"]:
            self.assertTrue(example["is_fictive"])
            self.assertEqual(example["status"], "exemple")
            self.assertEqual(example["novice_status"]["label"], "Exemple fictif")
            self.assertTrue(example["request_href"].startswith("/demandes/relance"))
            self.assertTrue(example["deposit_href"].startswith("/depot"))

        self.assertNoForbiddenUxMarkers(pieces)
        for path, href in _hrefs(pieces):
            with self.subTest(href_path=path):
                self.assertLocalHref(href, path)


if __name__ == "__main__":
    unittest.main()
