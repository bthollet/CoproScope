from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone

from coproscope.modules.agcontentieux import (
    DIFFUSION_COPRO,
    RESTRICTION_CONFIDENTIAL,
    ContentieuxCase,
    DossierAG,
    EvidenceRef,
    LegalRiskNote,
    PieceConvocation,
    QuestionAG,
    build_evidence_bundle,
    build_passation_pack,
)
from coproscope.modules.passation_exports import (
    WATERMARK,
    build_passation_derived_export,
    render_passation_derived_json,
    render_passation_derived_markdown,
)
from coproscope.modules.requestops import VISIBILITY_RESTRICTED, normalize_request


class PassationExportsTests(unittest.TestCase):
    def test_builds_json_and_markdown_derived_from_abstract_objects_only(self) -> None:
        question = QuestionAG(
            "q-travaux",
            "ag-2026-06",
            "Vote travaux ascenseur",
            objective="Verifier le chiffrage et le rattachement a la resolution.",
            source_refs=("DOC-CONVOC-1",),
            proof_refs=("EV-DEVIS-1",),
            next_action="Relire la resolution avant envoi.",
            due_on="2026-06-05",
        )
        piece = PieceConvocation(
            "piece-devis",
            "ag-2026-06",
            "Annexe devis",
            source_refs=("DOC-DEVIS-1",),
            proof_refs=("EV-DEVIS-1",),
        )
        dossier = DossierAG(
            "ag-2026-06",
            "AG juin 2026",
            questions=(question,),
            pieces=(piece,),
            source_refs=("DOC-CONVOC-1",),
            proof_refs=("EV-CONVOC-1",),
            diffusion=DIFFUSION_COPRO,
            next_action="Finaliser l'ordre du jour.",
        )
        case = ContentieuxCase(
            "ctx-001",
            "Impayes lot anonymise",
            "recouvrement",
            source_refs=("DOC-CTX-1",),
            proof_refs=("EV-CTX-1",),
            next_action="Verifier le decompte actualise.",
        )
        evidence = EvidenceRef(
            "EV-CTX-1",
            "DOC-CTX-1",
            "Courrier relance anonymise",
            restriction=RESTRICTION_CONFIDENTIAL,
        )
        bundle = build_evidence_bundle("bundle-passation", "Preuves passation", "Passation CS", [evidence])
        note = LegalRiskNote(
            "risk-ctx",
            "Vigilance recouvrement",
            observations=("Piece manquante: decompte actualise.",),
            risk_signals=("Delai de reponse a surveiller.",),
            source_refs=("DOC-CTX-1",),
            proof_refs=("EV-CTX-1",),
        )
        pack = build_passation_pack(
            "passation-2026",
            "Passation AG/contentieux",
            "AG juin et contentieux ouverts",
            dossiers_ag=[dossier],
            contentieux_cases=[case],
            evidence_bundles=[bundle],
            legal_risk_notes=[note],
            open_points=("Verifier les preuves avant diffusion coproprietaires.",),
        )
        request = normalize_request(
            {
                "channel": "ag",
                "subject": "Question ordre du jour",
                "summary": "Demande rattachee a la resolution travaux.",
                "proof_ref": "MSG-CS-1",
                "source_ref": "REG-DEMANDES",
                "next_action": "Confirmer le rattachement au point AG.",
                "visibility": "cs",
            }
        )

        document = build_passation_derived_export(
            title="Export passation test",
            passation_pack=pack,
            dossiers_ag=[dossier],
            contentieux_cases=[case],
            evidence_bundles=[bundle],
            legal_risk_notes=[note],
            requests=[request],
            timeline_entries=[
                {
                    "timeline_id": "TL-1",
                    "object_id": "ctx-001",
                    "source": "event_log",
                    "source_id": "EVT-1",
                    "occurred_at": "2026-05-20T10:00:00Z",
                    "event_type": "proof_linked",
                    "proof_ref": "EV-CTX-1",
                    "summary": "Preuve rattachee au dossier.",
                }
            ],
            generated_at=datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc),
        )
        json_text = render_passation_derived_json(document)
        markdown = render_passation_derived_markdown(document)

        self.assertEqual(document["watermark"], WATERMARK)
        self.assertFalse(document["source_of_truth"])
        self.assertIn("DOC-CONVOC-1", document["source_refs"])
        self.assertIn("EV-CTX-1", document["proof_refs"])
        self.assertEqual(document["scope"]["restriction"], "confidentiel")
        self.assertEqual(document["sections"]["demandes"][0]["proof_refs"], ["MSG-CS-1"])
        self.assertTrue(any(action["object_id"] == "ctx-001" for action in document["next_actions"]))
        self.assertIn(WATERMARK, markdown)
        self.assertIn("preuve", markdown.lower())
        self.assertNotIn("metadata", json_text)
        self.assertNotIn("payload", json_text)

    def test_omits_restricted_requests_and_private_paths_from_payloads(self) -> None:
        dossier = DossierAG(
            "ag-private",
            "Dossier avec chemin local",
            source_refs=(r"C:\Users\ExampleUser\CoproScope\restricted\convocation.pdf", "DOC-PUBLIC-1"),
            proof_refs=("EV-PUBLIC-1",),
            next_action="Controler la version diffusable.",
        )
        restricted_request = normalize_request(
            {
                "channel": "email",
                "subject": "Demande restreinte",
                "summary": "Contient un contact copro@example.org deja expurge par requestops.",
                "proof_ref": "MSG-PRIVATE",
                "source_ref": "REG-DEMANDES",
                "visibility": VISIBILITY_RESTRICTED,
                "next_action": "Traiter hors export derive.",
            }
        )

        document = build_passation_derived_export(
            title="Export sans chemin",
            dossiers_ag=[dossier],
            requests=[restricted_request],
            timeline_entries=[
                {
                    "timeline_id": "TL-PATH",
                    "object_id": r"C:\Users\ExampleUser\private.pdf",
                    "source": "action_log",
                    "source_id": "RUN-1",
                    "proof_ref": r"C:\Users\ExampleUser\proof.pdf",
                    "summary": r"Trace issue de C:\Users\ExampleUser\CoproScope\raw\piece.pdf",
                }
            ],
            generated_at="2026-05-20T12:00:00+00:00",
        )
        serialized = json.dumps(document, ensure_ascii=False, sort_keys=True)

        self.assertEqual(document["sections"]["demandes"], [])
        self.assertEqual(document["sections"]["ag"][0]["source_refs"], ["DOC-PUBLIC-1"])
        self.assertIn("[chemin-retire]", document["sections"]["chronologie"][0]["summary"])
        self.assertTrue(any(item["field"] == "demande" for item in document["omissions"]))
        self.assertNotIn("C:\\Users", serialized)
        self.assertNotIn("restricted", serialized.lower())
        self.assertNotIn("raw", serialized.lower())
        self.assertNotIn("copro@example.org", serialized)

    def test_flags_missing_source_or_proof_without_blocking_export(self) -> None:
        dossier = DossierAG("ag-sans-preuve", "AG sans preuve rattachee", source_refs=(), proof_refs=())

        document = build_passation_derived_export(title="Export incomplet", dossiers_ag=[dossier], generated_at="2026-05-20T12:00:00+00:00")

        self.assertTrue(any(item["field"] == "preuve_source" for item in document["omissions"]))
        self.assertEqual(document["sections"]["ag"][0]["object_id"], "ag-sans-preuve")


if __name__ == "__main__":
    unittest.main()
