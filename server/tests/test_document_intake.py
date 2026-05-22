from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from coproscope.modules.document_intake import (
    CHECK_BLOCKED,
    CHECK_FUTURE,
    CHECK_OK,
    CHECK_TODO,
    PRIVACY_BLOCKED,
    RUNTIME_BLOCKED,
    RUNTIME_NEEDS_INPUT,
    RUNTIME_READY,
    STEP_LINKING,
    STEP_LOCAL_DEPOSIT,
    build_runtime_checklist,
    novice_checklist,
    normalize_document_intake,
)


class DocumentIntakeRuntimeTests(unittest.TestCase):
    def test_complete_local_document_returns_novice_checklist_and_ready_status(self) -> None:
        runtime = build_runtime_checklist(
            {
                "sha256": "abcdef1234567890",
                "file_name": "pv_ag_2026.pdf",
                "local_reference": "raw/DOC-PV-2026",
                "document_type": "PV_AG",
                "classification_status": "ACCEPTE",
                "privacy_status": "RESERVE_CS",
                "attachments": [
                    {
                        "piece_label": "PV AG 2026",
                        "point_id": "AG-2026-R7",
                        "point_label": "Resolution travaux toiture",
                        "point_kind": "AG",
                        "action_label": "Verifier le devis retenu et la date de lancement.",
                        "proof_intent": "decision",
                        "proof_label": "Decision votee et rattachee au suivi travaux.",
                    }
                ],
            }
        )

        self.assertEqual(runtime.status, RUNTIME_READY)
        self.assertIn("Enregistrer la piece", runtime.next_action)
        self.assertTrue(any(item.step_id == STEP_LOCAL_DEPOSIT and item.status == CHECK_OK for item in runtime.checklist))
        self.assertTrue(any(item.step_id == STEP_LINKING and item.status == CHECK_OK for item in runtime.checklist))
        self.assertEqual([item.status for item in runtime.checklist[-2:]], [CHECK_FUTURE, CHECK_FUTURE])
        labels = "\n".join(novice_checklist(runtime))
        self.assertIn("Depot local", labels)
        self.assertIn("Classification", labels)
        self.assertIn("Confidentialite", labels)
        self.assertIn("Rattachement", labels)

    def test_model_does_not_read_real_file_paths_and_masks_absolute_source_hints(self) -> None:
        with patch("builtins.open", side_effect=AssertionError("document_intake must stay pure")):
            runtime = build_runtime_checklist(
                {
                    "doc_id": "DOC-ABS",
                    "sha256": "abcdef1234567890",
                    "original_path": r"C:\Users\ExampleUser\secret.pdf",
                    "document_type": "Facture",
                    "classification_status": "PROPOSED",
                    "privacy_status": "A_ARBITRER",
                }
            )

        intake = normalize_document_intake(
            {
                "doc_id": "DOC-ABS",
                "sha256": "abcdef1234567890",
                "original_path": r"C:\Users\ExampleUser\secret.pdf",
            }
        )
        self.assertEqual(intake.local_reference, "")
        self.assertTrue(intake.source_hint_blocked)
        self.assertEqual(runtime.status, RUNTIME_NEEDS_INPUT)
        self.assertIn("chemin_local_ou_absolu_masque", runtime.warnings)

    def test_privacy_blocked_document_blocks_runtime_before_export_or_linking(self) -> None:
        runtime = build_runtime_checklist(
            {
                "doc_id": "DOC-SENSIBLE",
                "sha256": "abcdef1234567890",
                "local_reference": "raw/DOC-SENSIBLE",
                "document_type": "Dossier_Contentieux",
                "classification_status": "ACCEPTED",
                "privacy_status": PRIVACY_BLOCKED,
                "attachments": [
                    {
                        "piece_label": "Dossier contentieux",
                        "point_label": "Litige fournisseur",
                        "action_label": "Verifier les pieces communicables.",
                        "proof_label": "Motif de blocage documente.",
                    }
                ],
            }
        )

        self.assertEqual(runtime.status, RUNTIME_BLOCKED)
        self.assertIn("Ne pas exporter", runtime.next_action)
        self.assertTrue(any(item.status == CHECK_BLOCKED for item in runtime.checklist))

    def test_missing_linking_keeps_next_action_on_piece_point_action_proof_chain(self) -> None:
        runtime = build_runtime_checklist(
            {
                "doc_id": "DOC-DEVIS",
                "sha256": "abcdef1234567890",
                "local_reference": "raw/DOC-DEVIS",
                "document_type": "Devis",
                "classification_status": "ACCEPTED",
                "privacy_status": "DIFFUSABLE_BRUT",
                "attachments": [{"piece_label": "Devis toiture", "point_label": "Travaux toiture"}],
            }
        )

        self.assertEqual(runtime.status, RUNTIME_NEEDS_INPUT)
        linking = next(item for item in runtime.checklist if item.step_id == STEP_LINKING)
        self.assertEqual(linking.status, CHECK_TODO)
        self.assertIn("action", linking.next_action)
        self.assertIn("preuve", linking.next_action)

    def test_static_runtime_checklist_doc_covers_contract_markers(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        text = (repo_root / "docs" / "checklist_ajout_document_runtime.md").read_text(encoding="utf-8")
        normalized = text.lower()

        for marker in [
            "depot local -> classification -> confidentialite",
            "piece -> point -> action -> preuve",
            "checklist novice",
            "statut runtime",
            "prochaine action",
            "pas de lecture fichier reel",
            "pas de route",
            "annotation pdf future",
            "evenement signe futur",
            "aucun raw dans cloud",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, normalized)


if __name__ == "__main__":
    unittest.main()
