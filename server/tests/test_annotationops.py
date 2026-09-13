from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from coproscope.core.events_v1 import SIGNATURE_STATUS_PENDING, draft_hash
from coproscope.modules.annotationops import (
    ANNOTATION_EVENT_TYPE,
    CONFIDENTIALITY_BLOCKED,
    DIFFUSION_BLOCKED,
    TARGET_IMAGE,
    CollaborativeAnnotation,
    AnnotationAnchor,
    AnnotationZone,
    draft_annotation_event,
    event_payload,
    non_destructive_sidecar_plan,
    normalize_annotation,
    validate_annotation,
)


HASH = "sha256:" + "a" * 64
ANCHOR_HASH = "sha256:" + "b" * 64


class AnnotationOpsTests(unittest.TestCase):
    def test_pdf_annotation_links_anchor_comment_point_action_proof_and_future_event(self) -> None:
        annotation = normalize_annotation(
            {
                "annotation_id": "ANN-PV-2026-R7",
                "doc_id": "DOC-PV-2026",
                "sha256": HASH,
                "page": "7",
                "zone": {"x": 0.12, "y": 0.25, "width": 0.3, "height": 0.08},
                "anchor_hash": ANCHOR_HASH,
                "commentaire": "Verifier la mention de la resolution travaux.",
                "author_ref": "user:cs-1",
                "created_at": "2026-05-20T08:30:00Z",
                "point_id": "AG-2026-R7",
                "action_id": "ACT-TRAVAUX-1",
                "proof_ref": "PROOF-PV-R7",
                "diffusion": "conseil syndical",
                "confidentialite": "reserve_cs",
            }
        )

        self.assertEqual(annotation.anchor.page, 7)
        self.assertEqual(annotation.anchor.zone.width, 0.3)
        self.assertEqual(annotation.point_ref, "AG-2026-R7")
        self.assertEqual(annotation.action_ref, "ACT-TRAVAUX-1")
        self.assertEqual(annotation.proof_ref, "PROOF-PV-R7")
        self.assertEqual(validate_annotation(annotation), ())

        payload = event_payload(annotation)
        self.assertEqual(payload["event_type"], ANNOTATION_EVENT_TYPE)
        self.assertTrue(payload["non_destructive"])
        self.assertEqual(payload["links"]["point_ref"], "AG-2026-R7")

        draft = draft_annotation_event(annotation, actor_ref="user:cs-1", device_ref="device:local")
        self.assertEqual(draft.event_type, ANNOTATION_EVENT_TYPE)
        self.assertEqual(draft.source_module, "annotationops")
        self.assertEqual(draft.future_signature_status, SIGNATURE_STATUS_PENDING)
        self.assertTrue(draft.payload_hash.startswith("sha256:"))
        self.assertTrue(draft_hash(draft).startswith("sha256:"))

    def test_private_paths_are_blocked_and_never_leak_to_event_payload(self) -> None:
        annotation = normalize_annotation(
            {
                "annotation_id": "ANN-PRIVATE",
                "doc_id": "DOC-PV-PRIVATE-HINT",
                "original_path": r"C:\Users\ExampleUser\secret\pv.pdf",
                "sha256": HASH,
                "page": 1,
                "comment": "Trace a qualifier.",
                "author_ref": "user:cs-1",
                "created_at": "2026-05-20T09:00:00Z",
                "point_ref": "POINT-1",
                "action_ref": "ACT-1",
                "proof_ref": "PROOF-1",
            }
        )

        issues = validate_annotation(annotation)
        self.assertTrue(annotation.source_hint_blocked)
        self.assertEqual(annotation.document_ref, "DOC-PV-PRIVATE-HINT")
        self.assertTrue(any(issue.field == "source_hint" for issue in issues))
        serialized = json.dumps(annotation.__dict__, ensure_ascii=True, default=str)
        self.assertNotIn("secret", serialized.lower())
        with self.assertRaises(ValueError):
            event_payload(annotation)

    def test_blocked_confidentiality_requires_non_diffusable_status(self) -> None:
        annotation = normalize_annotation(
            {
                "annotation_id": "ANN-BLOCKED",
                "document_ref": "DOC-CONTENTIEUX",
                "document_hash": HASH,
                "page": 2,
                "zone": [0.1, 0.1, 0.2, 0.2],
                "comment": "Piece sensible a ne pas diffuser.",
                "author_ref": "user:cs-1",
                "created_at": "2026-05-20T10:00:00Z",
                "point_ref": "CTX-1",
                "action_ref": "ACT-BIFFAGE",
                "proof_ref": "PROOF-SENSIBLE",
                "confidentiality": "blocked",
                "diffusion": "copro",
            }
        )

        issues = validate_annotation(annotation)
        self.assertEqual(annotation.confidentiality, CONFIDENTIALITY_BLOCKED)
        self.assertTrue(any(issue.field == "diffusion" for issue in issues))

        fixed = replace(annotation, diffusion=DIFFUSION_BLOCKED)
        self.assertEqual(validate_annotation(fixed), ())

    def test_image_anchor_and_sidecar_plan_are_non_destructive_without_file_io(self) -> None:
        annotation = CollaborativeAnnotation(
            annotation_id="ANN-IMG-1",
            document_ref="IMG-FACADE-1",
            document_hash=HASH,
            anchor=AnnotationAnchor(
                page=1,
                target_kind=TARGET_IMAGE,
                zone=AnnotationZone(x=0.4, y=0.2, width=0.2, height=0.2),
            ),
            comment="Localiser la fissure visible sur la photo.",
            author_ref="user:cs-1",
            created_at="2026-05-20T11:00:00Z",
            point_ref="INC-FACADE",
            action_ref="ACT-EXPERTISE",
            proof_ref="PHOTO-FACADE",
        )

        with patch("builtins.open", side_effect=AssertionError("annotationops must stay pure")):
            plan = non_destructive_sidecar_plan(annotation)
            draft = draft_annotation_event(annotation, actor_ref="user:cs-1", device_ref="device:local")

        self.assertFalse(plan["source_write_allowed"])
        self.assertEqual(plan["source_mutation"], "forbidden")
        self.assertIn(annotation.annotation_id, plan["sidecar_object_ref"])
        self.assertTrue(draft.payload_hash.startswith("sha256:"))

    def test_validation_rejects_bad_zone_private_contact_and_source_mutation_flag(self) -> None:
        annotation = CollaborativeAnnotation(
            annotation_id="ANN-BAD",
            document_ref="DOC-1",
            document_hash=HASH,
            anchor=AnnotationAnchor(page=0, zone=AnnotationZone(x=0.9, y=0.9, width=0.2, height=-0.1)),
            comment="Appeler le 06 12 34 56 78 avant diffusion.",
            author_ref="user:cs-1",
            created_at="2026-05-20T12:00:00Z",
            point_ref="POINT-1",
            action_ref="ACT-1",
            proof_ref="PROOF-1",
            no_source_write=False,
        )

        issues = validate_annotation(annotation)
        reasons = " | ".join(issue.reason for issue in issues)
        self.assertIn("page numbers are one-based", reasons)
        self.assertIn("zone width and height must be positive", reasons)
        self.assertIn("phone-like private data detected", reasons)
        self.assertIn("annotations must not modify source PDF/image", reasons)

    def test_numeric_hash_is_not_rejected_as_phone_like_private_data(self) -> None:
        numeric_hash = "sha256:" + ("1234567890abcdef" * 4)
        annotation = CollaborativeAnnotation(
            annotation_id="ANN-HASH-DIGITS",
            document_ref="DOC-HASH-DIGITS",
            document_hash=numeric_hash,
            anchor=AnnotationAnchor(
                page=1,
                zone=AnnotationZone(x=0.1, y=0.1, width=0.2, height=0.2),
                anchor_hash=numeric_hash,
            ),
            comment="Verifier la zone selectionnee.",
            author_ref="user:cs-1",
            created_at="2026-05-20T12:30:00Z",
            point_ref="POINT-HASH",
            action_ref="ACT-HASH",
            proof_ref="PROOF-HASH",
        )

        self.assertEqual(validate_annotation(annotation), ())

    def test_static_documentation_covers_contract_markers(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        text = (repo_root / "docs" / "annotations_pdf_collaboratives.md").read_text(encoding="utf-8")
        normalized = text.lower()

        for marker in [
            "modele metier pur",
            "pas d'ui",
            "pas de route",
            "page",
            "zone",
            "point -> action -> preuve",
            "source_write_allowed: false",
            "chemin prive interdit",
            "pdf_annotation_created",
            "pending_future_signature",
            "ne contient aucun chemin local",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, normalized)


if __name__ == "__main__":
    unittest.main()
