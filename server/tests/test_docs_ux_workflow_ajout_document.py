from __future__ import annotations

import unittest
from pathlib import Path


class AjoutDocumentUxWorkflowDocTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[2]
        cls.doc_path = cls.repo_root / "docs" / "ux_workflow_ajout_document.md"
        cls.text = cls.doc_path.read_text(encoding="utf-8")
        cls.normalized = cls.text.lower()

    def test_document_exists_and_declares_non_applicative_scope(self) -> None:
        self.assertTrue(self.doc_path.exists())
        self.assertIn("# UX workflow ajout de document", self.text)
        self.assertIn("sans code applicatif", self.normalized)
        self.assertIn("exploration UX", self.text)

    def test_workflow_covers_local_deposit_classification_privacy_and_linking(self) -> None:
        required_markers = [
            "depot local",
            "classification",
            "confidentialite",
            "piece -> point -> action -> preuve",
            "empreinte locale",
            "doc_id",
            "A_CLASSER",
            "A_ARBITRER",
        ]

        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), self.normalized)

    def test_privacy_contract_forbids_raw_cloud_leaks(self) -> None:
        required_markers = [
            "Aucun raw dans cloud",
            "aucun chemin local",
            "aucun document sensible dans un export diffusable",
            "versions biffees",
            "cartes de pseudonymisation",
            "fichier raw",
            "cache dechiffre",
        ]

        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), self.normalized)

    def test_future_pdf_annotations_are_separate_from_the_source_pdf(self) -> None:
        annotation_section = self._section("## Annotation PDF future", "## Evenement signe futur")

        self.assertIn("future", annotation_section.lower())
        self.assertIn("ne modifie pas le fichier PDF source".lower(), annotation_section.lower())
        self.assertIn("evenement separe", annotation_section.lower())
        self.assertIn("doc_id", annotation_section)
        self.assertIn("page", annotation_section.lower())
        self.assertIn("zone", annotation_section.lower())
        self.assertIn("hash du document cible", annotation_section.lower())

    def test_future_signed_events_are_named_and_not_claimed_as_delivered(self) -> None:
        signed_event_section = self._section("## Evenement signe futur", "## Donnees derivees autorisees")

        required_events = [
            "document_added",
            "document_classified",
            "document_privacy_reviewed",
            "document_linked_to_point",
            "action_created_from_document",
            "proof_attached",
            "pdf_annotation_created",
            "signed_event_recorded",
        ]

        self.assertIn("future", signed_event_section.lower())
        for event_name in required_events:
            with self.subTest(event_name=event_name):
                self.assertIn(event_name, signed_event_section)

        for marker in ["acteur", "date UTC", "hash des entrees", "hash des sorties", "statut de verification"]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), signed_event_section.lower())

    def test_acceptance_criteria_keep_the_static_doc_testable(self) -> None:
        acceptance_section = self._section("## Criteres d'acceptation UX")

        for marker in [
            "document, piece, point, action et",
            "depose localement",
            "A_CLASSER",
            "A_ARBITRER",
            "annotation PDF future",
            "evenement signe futur",
            "aucun raw dans cloud",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), acceptance_section.lower())

    def _section(self, start: str, end: str | None = None) -> str:
        start_index = self.text.index(start)
        end_index = self.text.index(end, start_index) if end else len(self.text)
        return self.text[start_index:end_index]


if __name__ == "__main__":
    unittest.main()
