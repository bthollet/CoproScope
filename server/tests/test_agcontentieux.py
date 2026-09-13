from __future__ import annotations

import unittest
from datetime import date

from coproscope.modules.agcontentieux import (
    DIFFUSION_COPRO,
    DIFFUSION_CS,
    RESTRICTION_CONFIDENTIAL,
    RESTRICTION_RESTRICTED,
    STATUS_READY,
    STATUS_TO_REVIEW,
    ContentieuxCase,
    DossierAG,
    EvidenceRef,
    LegalRiskNote,
    PieceConvocation,
    QuestionAG,
    build_evidence_bundle,
    build_passation_pack,
    build_precontentious_plan,
    contains_private_data,
    event_payload,
    proof_reference_ids,
    source_reference_ids,
    validate_record,
)


class AGContentieuxTests(unittest.TestCase):
    def test_ag_dossier_tracks_sources_proofs_actions_and_signed_event_shape(self) -> None:
        question = QuestionAG(
            "q-budget",
            "ag-2026-06",
            "Budget previsionnel",
            objective="Preparer une question claire et rattachee aux annexes.",
            source_refs=("DOC-CONVOC-1",),
            proof_refs=("EV-BUDGET-1",),
            status=STATUS_TO_REVIEW,
            due_on=date(2026, 6, 10),
            decision_refs=("DAP-AG-2026-R1",),
            action_refs=("ACT-BUDGET-VERIFY",),
        )
        piece = PieceConvocation(
            "piece-budget",
            "ag-2026-06",
            "Annexe budget",
            source_refs=("DOC-BUDGET-1",),
            proof_refs=("EV-BUDGET-1",),
            status=STATUS_READY,
            due_on="2026-06-08",
            action_refs=("ACT-BUDGET-VERIFY",),
        )
        dossier = DossierAG(
            "ag-2026-06",
            "Preparation AG juin 2026",
            ag_date="2026-06-20",
            questions=(question,),
            pieces=(piece,),
            source_refs=("DOC-CONVOC-1",),
            proof_refs=("EV-CONVOC-1",),
            status=STATUS_TO_REVIEW,
            next_action="Finaliser les annexes diffusable CS.",
            due_on="2026-06-12",
        )

        self.assertEqual(source_reference_ids(dossier), ("DOC-CONVOC-1", "DOC-BUDGET-1"))
        self.assertEqual(proof_reference_ids(dossier), ("EV-CONVOC-1", "EV-BUDGET-1"))
        self.assertEqual(validate_record(dossier), ())

        payload = event_payload(dossier)

        self.assertEqual(payload["schema_version"], "agcontentieux.v1")
        self.assertEqual(payload["event_type"], "agcontentieux.dossier_ag.recorded")
        self.assertEqual(payload["aggregate_id"], "ag-2026-06")
        self.assertEqual(payload["source_refs"], ["DOC-CONVOC-1", "DOC-BUDGET-1"])
        self.assertEqual(payload["decision_refs"], ["DAP-AG-2026-R1"])
        self.assertEqual(payload["action_refs"], ["ACT-BUDGET-VERIFY"])

    def test_evidence_bundle_and_passation_pack_roll_up_restrictions_and_refs(self) -> None:
        convocation = EvidenceRef(
            "EV-CONVOC-1",
            "DOC-CONVOC-1",
            "Convocation AG",
            restriction=RESTRICTION_RESTRICTED,
            diffusion=DIFFUSION_COPRO,
            decision_refs=("DAP-AG-2026-R1",),
        )
        mise_en_demeure = EvidenceRef(
            "EV-CTX-1",
            "DOC-CTX-1",
            "Courrier contentieux redige",
            restriction=RESTRICTION_CONFIDENTIAL,
            diffusion=DIFFUSION_CS,
            action_refs=("ACT-CTX-COLLECT",),
        )
        bundle = build_evidence_bundle(
            "bundle-ag-ctx",
            "Preuves AG et contentieux",
            "Passation conseil syndical",
            [convocation, mise_en_demeure],
            due_on="2026-06-15",
        )
        dossier = DossierAG(
            "ag-2026-06",
            "Preparation AG",
            source_refs=("DOC-CONVOC-1",),
            proof_refs=("EV-CONVOC-1",),
        )
        contentieux = ContentieuxCase(
            "ctx-001",
            "Dossier impaye anonymise",
            "recouvrement",
            source_refs=("DOC-CTX-1",),
            proof_refs=("EV-CTX-1",),
            action_refs=("ACT-CTX-COLLECT",),
        )
        note = LegalRiskNote(
            "risk-001",
            "Points de vigilance recouvrement",
            observations=("Piece manquante: decompte actualise.",),
            risk_signals=("Delai de reponse a suivre.",),
            source_refs=("DOC-CTX-1",),
            proof_refs=("EV-CTX-1",),
        )

        pack = build_passation_pack(
            "passation-2026-s1",
            "Passation S1 2026",
            "AG juin et dossiers ouverts",
            dossiers_ag=[dossier],
            contentieux_cases=[contentieux],
            evidence_bundles=[bundle],
            legal_risk_notes=[note],
            open_points=("Verifier pieces manquantes avant diffusion coproprietaires.",),
        )

        self.assertEqual(bundle.restriction, RESTRICTION_CONFIDENTIAL)
        self.assertEqual(bundle.diffusion, DIFFUSION_CS)
        self.assertEqual(bundle.source_refs, ("DOC-CONVOC-1", "DOC-CTX-1"))
        self.assertEqual(pack.dossier_ag_ids, ("ag-2026-06",))
        self.assertEqual(pack.contentieux_case_ids, ("ctx-001",))
        self.assertEqual(pack.evidence_bundle_ids, ("bundle-ag-ctx",))
        self.assertEqual(pack.legal_risk_note_ids, ("risk-001",))
        self.assertEqual(pack.restriction, RESTRICTION_CONFIDENTIAL)
        self.assertEqual(pack.diffusion, DIFFUSION_CS)
        self.assertIn("ACT-CTX-COLLECT", pack.action_refs)
        self.assertEqual(validate_record(pack), ())

    def test_legal_risk_note_rejects_automatic_legal_advice_markers(self) -> None:
        note = LegalRiskNote(
            "risk-danger",
            "Avis juridique automatique",
            observations=("Nous gagnerons si nous poursuivons.",),
            risk_signals=("Chance de gagner elevee.",),
            source_refs=("DOC-CTX-1",),
            proof_refs=("EV-CTX-1",),
        )

        issues = validate_record(note)

        self.assertTrue(any(issue.reason == "automatic legal advice marker detected" for issue in issues))
        with self.assertRaises(ValueError):
            event_payload(note)

    def test_private_data_markers_block_event_payload(self) -> None:
        self.assertTrue(contains_private_data("contact: copro@example.org"))
        case = ContentieuxCase(
            "ctx-private",
            "Relance copro@example.org",
            "recouvrement",
            source_refs=("DOC-CTX-1",),
            proof_refs=("EV-CTX-1",),
        )

        issues = validate_record(case)

        self.assertTrue(any(issue.reason == "private data marker detected" for issue in issues))
        with self.assertRaises(ValueError):
            event_payload(case)

    def test_precontentious_plan_buckets_p1_findings_without_legal_conclusion(self) -> None:
        findings = [
            {
                "source_row_id": "row-piece",
                "proof_ref": "EV-ASSURANCE",
                "priorite": "P1",
                "point_de_controle": "Attestation assurance manquante",
                "preuve_attendue": "Attestation multirisque 2026",
            },
            {
                "source_row_id": "row-pv",
                "proof_ref": "EV-PV",
                "priorite": "P1",
                "point_de_controle": "Resolution travaux sans reponse syndic",
                "action_a_faire": "Preparer une reserve PV factuelle si la reponse manque.",
                "preuve_attendue": "Demande envoyee et reponse syndic",
            },
            {
                "source_row_id": "row-power",
                "proof_ref": "EV-POUVOIR",
                "priorite": "P1",
                "point_de_controle": "Pouvoir et mandat du representant a verifier",
                "preuve_attendue": "Pouvoir signe ou feuille de presence",
            },
            {
                "source_row_id": "row-correction",
                "proof_ref": "EV-CORRECTION",
                "priorite": "P1",
                "point_de_controle": "Contrat, comptes et RGPD a corriger ou justifier",
                "preuve_attendue": "Correction, justificatif ou reponse documentee",
            },
            {
                "source_row_id": "row-p2",
                "proof_ref": "EV-P2",
                "priorite": "P2",
                "point_de_controle": "Information de confort a suivre plus tard",
            },
        ]

        plan = build_precontentious_plan(
            "plan-ag-2026",
            "Plan de reprise avant AG",
            findings,
            due_on=date(2026, 6, 1),
        )
        same_plan = build_precontentious_plan(
            "plan-ag-2026",
            "Plan de reprise avant AG",
            findings,
            due_on=date(2026, 6, 1),
        )

        self.assertEqual(len(plan.actions), 4)
        self.assertEqual(
            plan.lane_counts,
            {"piece_request": 1, "pv_reserve": 1, "power_trace": 1, "correction": 1},
        )
        self.assertEqual(
            {action.lane: action.label for action in plan.actions},
            {
                "piece_request": "A demander avant l'AG",
                "pv_reserve": "A faire constater au PV si non leve",
                "power_trace": "Pouvoirs et votes a tracer",
                "correction": "Corrections a suivre apres AG",
            },
        )
        self.assertTrue(all(action.status == STATUS_TO_REVIEW for action in plan.actions))
        self.assertTrue(all(action.restriction == RESTRICTION_CONFIDENTIAL for action in plan.actions))
        self.assertEqual(validate_record(plan), ())

        payload = event_payload(plan)

        self.assertEqual(payload["event_type"], "agcontentieux.precontentious_plan.recorded")
        self.assertEqual(payload["aggregate_id"], "plan-ag-2026")
        self.assertIn("row-piece", payload["source_refs"])
        self.assertIn("row-pv", payload["source_refs"])
        self.assertNotIn("row-p2", payload["source_refs"])
        self.assertIn("EV-ASSURANCE", payload["proof_refs"])
        self.assertEqual(payload, event_payload(same_plan))
        serialized = repr(payload).lower()
        for forbidden in ("assigner", "chances de gagner", "avis juridique", "nullite"):
            self.assertNotIn(forbidden, serialized)

    def test_precontentious_plan_rejects_private_legal_and_local_markers(self) -> None:
        legal_plan = build_precontentious_plan(
            "plan-danger",
            "Plan de reprise avant AG",
            [
                {
                    "source_row_id": "row-danger",
                    "priorite": "P1",
                    "action_a_faire": "Nous devons assigner le syndic.",
                }
            ],
        )
        private_plan = build_precontentious_plan(
            "plan-private",
            "Plan de reprise avant AG",
            [
                {
                    "source_row_id": "row-private",
                    "priorite": "P1",
                    "constat": "Contact syndic copro@example.org a relancer.",
                }
            ],
        )
        leaky_plan = build_precontentious_plan(
            "plan-leak",
            "Plan de reprise avant AG",
            [
                {
                    "source_row_id": r"C:\Users\ExampleUser\raw\audit.csv",
                    "proof_ref": "EV-LEAK",
                    "priorite": "P1",
                    "point_de_controle": "Attestation manquante",
                }
            ],
        )

        self.assertTrue(
            any(issue.reason == "automatic legal advice marker detected" for issue in validate_record(legal_plan))
        )
        self.assertTrue(any(issue.reason == "private data marker detected" for issue in validate_record(private_plan)))
        self.assertTrue(any(issue.reason == "unsafe local marker detected" for issue in validate_record(leaky_plan)))
        with self.assertRaises(ValueError):
            event_payload(legal_plan)
        with self.assertRaises(ValueError):
            event_payload(private_plan)
        with self.assertRaises(ValueError):
            event_payload(leaky_plan)


if __name__ == "__main__":
    unittest.main()
