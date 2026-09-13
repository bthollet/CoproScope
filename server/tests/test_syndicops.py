from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import read_csv
from coproscope.modules import syndicops


class SyndicOpsTests(unittest.TestCase):
    def test_normalizes_docops_like_rows(self) -> None:
        rows = syndicops.normalize_requests(
            [
                {
                    "request_id": "REQ-DOC-PRV-SYN",
                    "source_ref": "PRV-SYN",
                    "priority": "P1",
                    "status": "ABSENT",
                    "subject": "Demander au syndic: Contrat syndic signe",
                    "expected_piece": "Contrat syndic signe",
                    "reason": "Aucune piece locale ne correspond au type attendu.",
                    "suggested_diligence": "Demander la piece au syndic.",
                    "response_due_date": "2026-05-27",
                    "canal": "courriel",
                }
            ],
            today="2026-05-20",
        )

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["request_id"], "REQ-DOC-PRV-SYN")
        self.assertEqual(row["origin_kind"], "docops")
        self.assertEqual(row["origin_ref"], "PRV-SYN")
        self.assertEqual(row["channel"], "email")
        self.assertEqual(row["due_at"], "2026-05-27")
        self.assertEqual(row["status"], "todo")
        self.assertEqual(row["expected_proof"], "Contrat syndic signe")
        self.assertIn("Aucune piece locale", row["notes"])

    def test_deduplicates_by_origin_kind_origin_ref_and_expected_piece(self) -> None:
        rows = syndicops.normalize_requests(
            [
                {
                    "request_id": "REQ-1",
                    "origin_kind": "DocOps",
                    "origin_ref": "PRV-ASS",
                    "expected_piece": "Attestation assurance",
                    "priority": "P2",
                    "due_at": "2026-05-30",
                    "notes": "premiere demande",
                },
                {
                    "request_id": "REQ-2",
                    "origin_kind": "docops",
                    "origin_ref": "PRV-ASS",
                    "expected_piece": " attestation   assurance ",
                    "priority": "P1",
                    "due_at": "2026-05-25",
                    "last_follow_up": "2026-05-21",
                    "notes": "relance conseil syndical",
                },
            ],
            today="2026-05-20",
        )

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["request_id"], "REQ-1")
        self.assertEqual(row["priority"], "P1")
        self.assertEqual(row["due_at"], "2026-05-25")
        self.assertEqual(row["last_follow_up_at"], "2026-05-21")
        self.assertIn("premiere demande", row["notes"])
        self.assertIn("relance conseil syndical", row["notes"])

    def test_marks_overdue_without_proof_as_a_relancer(self) -> None:
        row = syndicops.normalize_request(
            {
                "origin_kind": "manual",
                "origin_ref": "MAIL-2026-05-01",
                "expected_piece": "Releve des comptes bancaires",
                "due_at": "2026-05-10",
                "status": "pending",
            },
            today="2026-05-20",
        )

        self.assertEqual(row["status"], "a_relancer")

    def test_answered_and_closed_statuses_require_response_or_proof(self) -> None:
        answered_without_response = syndicops.normalize_request(
            {
                "origin_ref": "REQ-A",
                "expected_piece": "Contrat syndic",
                "due_at": "2026-05-30",
                "status": "answered",
            },
            today="2026-05-20",
        )
        closed_without_proof = syndicops.normalize_request(
            {
                "origin_ref": "REQ-B",
                "expected_piece": "Attestation assurance",
                "due_at": "2026-05-30",
                "status": "closed",
                "response_ref": "MAIL-REP-1",
            },
            today="2026-05-20",
        )
        closed_with_proof = syndicops.normalize_request(
            {
                "origin_ref": "REQ-C",
                "expected_piece": "PV AG signe",
                "due_at": "2026-05-10",
                "status": "closed",
                "proof_ref": "DOC-PV-1",
            },
            today="2026-05-20",
        )

        self.assertEqual(answered_without_response["status"], "todo")
        self.assertEqual(closed_without_proof["status"], "answered")
        self.assertEqual(closed_with_proof["status"], "closed")

    def test_writes_normalized_csv_core(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "registre_syndicops.csv"

            syndicops.write_syndic_requests(
                path,
                [
                    {
                        "source_ref": "PRV-CONV",
                        "expected_piece": "Convocation AG et annexes",
                        "response_due_date": "2026-05-01",
                    }
                ],
                today="2026-05-20",
            )

            fields, rows = read_csv(path)
            self.assertEqual(fields, syndicops.SYNDIC_REQUEST_FIELDS)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["origin_kind"], "docops")
            self.assertEqual(rows[0]["status"], "a_relancer")


if __name__ == "__main__":
    unittest.main()
