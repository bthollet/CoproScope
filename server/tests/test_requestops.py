from __future__ import annotations

import unittest
from dataclasses import replace

from coproscope.modules.requestops import (
    CHANNEL_DOCOPS,
    CHANNEL_EMAIL,
    CHANNEL_INCIDENT,
    CHANNEL_ORAL,
    STATUS_FOLLOW_UP,
    STATUS_IN_PROGRESS,
    STATUS_NEW,
    VISIBILITY_COPRO,
    VISIBILITY_CS,
    VISIBILITY_RESTRICTED,
    action_event_payload,
    action_with_hash,
    event_hash,
    normalize_action,
    normalize_request,
    request_event_payload,
    request_from_docops,
    request_from_incident,
    requests_from_csv,
    validate_action,
    validate_request,
)


class RequestOpsTests(unittest.TestCase):
    def test_normalizes_multichannel_request_without_private_contact_data(self) -> None:
        request = normalize_request(
            {
                "canal": "courriel",
                "auteur": "Conseil - alice@example.com",
                "role_auteur": "coproprietaire",
                "sujet": "Question sur une fuite en cave",
                "resume": "Demande recue par email, rappel au 06 12 34 56 78 a supprimer.",
                "preuve": "MSG-2026-05-19",
                "source": "Boite CS import manuel",
                "statut": "nouveau",
                "diffusion": "CS",
                "email": "alice@example.com",
            }
        )

        self.assertEqual(request.channel, CHANNEL_EMAIL)
        self.assertEqual(request.status, STATUS_NEW)
        self.assertEqual(request.visibility, VISIBILITY_CS)
        self.assertIn("[redacted-email]", request.author_label)
        self.assertIn("[redacted-phone]", request.summary)
        self.assertNotIn("email", request.metadata)
        self.assertTrue(request.next_action)
        self.assertTrue(validate_request(request))

    def test_request_requires_source_or_proof_and_next_action_when_open(self) -> None:
        missing_proof = normalize_request(
            {
                "channel": "oral",
                "subject": "Question parking",
                "summary": "Echange oral en permanence.",
                "next_action": "Demander une trace ecrite.",
            }
        )
        with self.assertRaises(ValueError):
            validate_request(missing_proof)

        missing_action = normalize_request(
            {
                "channel": "portail syndic",
                "subject": "Demande sans suite precise",
                "proof_ref": "PORTAIL-42",
                "status": "en_cours",
                "next_action": "",
            }
        )
        with self.assertRaises(ValueError):
            validate_request(replace(missing_action, next_action=""))

    def test_docops_and_incident_sources_become_lightweight_requests(self) -> None:
        doc_request = request_from_docops(
            {
                "doc_id": "DOC-AG-2026-05",
                "file_name": "pv_ag_2026.pdf",
                "document_type": "proces_verbal_ag",
                "original_path": "raw/pv_ag_2026.pdf",
            },
            subject="Clarifier le vote sur les travaux",
        )
        incident_request = request_from_incident(
            {
                "incident_id": "INC-FUITE",
                "description": "Fuite parking",
                "piece_ref": "PHOTO-1",
                "next_action": "Demander le bon d'intervention au syndic.",
            }
        )

        self.assertEqual(doc_request.channel, CHANNEL_DOCOPS)
        self.assertEqual(doc_request.origin_id, "DOC-AG-2026-05")
        self.assertEqual(doc_request.proof_ref, "DOC-AG-2026-05")
        self.assertTrue(validate_request(doc_request))

        self.assertEqual(incident_request.channel, CHANNEL_INCIDENT)
        self.assertEqual(incident_request.origin_id, "INC-FUITE")
        self.assertEqual(incident_request.proof_ref, "PHOTO-1")
        self.assertTrue(validate_request(incident_request))

    def test_action_journal_is_concrete_and_hashable_for_future_signed_events(self) -> None:
        request = normalize_request(
            {
                "channel": "AG",
                "subject": "Rattacher la demande au point travaux",
                "proof_ref": "PV-AG-2026#resolution-7",
                "status": "relance",
                "next_action": "Ajouter le point a l'ordre du jour du prochain CS.",
                "related_point_id": "AG-2026-R7",
                "visibility": "copro",
            }
        )
        action = normalize_action(
            {
                "request_id": request.request_id,
                "occurred_at": "2026-05-20T10:00:00Z",
                "actor_role": "conseil_syndical",
                "action_type": "rattachement",
                "summary": "Rattachement au point AG-2026-R7 confirme.",
                "proof_ref": "PV-AG-2026#resolution-7",
                "status_after": "en_cours",
                "next_action": "Verifier la reponse du syndic avant le 2026-05-27.",
                "visibility": "restreint",
            }
        )

        self.assertEqual(request.channel, "ag")
        self.assertEqual(request.visibility, VISIBILITY_COPRO)
        self.assertEqual(request.status, STATUS_FOLLOW_UP)
        self.assertEqual(action.status_after, STATUS_IN_PROGRESS)
        self.assertEqual(action.visibility, VISIBILITY_RESTRICTED)
        self.assertTrue(action.event_hash)
        self.assertTrue(validate_action(action, request))

        payload = request_event_payload(request)
        action_payload = action_event_payload(action)
        self.assertEqual(payload["event_schema"], "coproscope.unsigned_event.v1")
        self.assertEqual(action.event_hash, event_hash(action_payload))
        self.assertEqual(event_hash(payload), event_hash(request_event_payload(request)))

    def test_csv_helper_accepts_novice_french_headers_and_channel_aliases(self) -> None:
        rows = requests_from_csv(
            "canal,sujet,preuve,source,prochaine_action,diffusion\n"
            "oral,Interphone en panne,NOTE-CS-2026-05,Reunion hall,"
            "Verifier si un ticket syndic existe,conseil syndical\n"
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].channel, CHANNEL_ORAL)
        self.assertEqual(rows[0].visibility, VISIBILITY_CS)
        self.assertTrue(validate_request(rows[0]))


if __name__ == "__main__":
    unittest.main()
