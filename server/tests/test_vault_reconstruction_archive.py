from __future__ import annotations

import json
import unittest
from dataclasses import replace

from coproscope.vault.reconstruction_archive import (
    READABLE,
    RESTRICTED,
    ArchiveManifest,
    CorpusPart,
    DownloadableArchive,
    RecoveryHelper,
    build_downloadable_archive,
    build_novice_reconstruction_report,
    reconstruct_authorized_corpus,
    verify_archive_integrity,
)


class CoproScopeVaultReconstructionArchiveTests(unittest.TestCase):
    def _parts(self) -> list[CorpusPart]:
        recovery_helper = RecoveryHelper(
            helper_id="helper_cs_tresorier",
            label="Tresorier du conseil syndical",
            role="cs",
            reason="Peut lancer une demande auditable de recuperation du compartiment contentieux.",
        )
        return [
            CorpusPart(
                part_id="part_pv_ag_2026",
                kind="document",
                public_label="PV AG 2026",
                compartment_id="copro_open",
                compartment_key="key-open-2026",
                payload={
                    "document_id": "doc_pv_ag_2026",
                    "title": "Proces-verbal AG 2026",
                    "decision": "Budget vote",
                },
                readable_by=("coowner", "cs"),
            ),
            CorpusPart(
                part_id="part_contentieux_1",
                kind="document",
                public_label="Piece contentieux referencee",
                compartment_id="contentieux",
                compartment_key="key-contentieux-2026",
                payload={
                    "document_id": "doc_contentieux_1",
                    "title": "Assignation confidentielle",
                    "secret": "CONTENU STRICTEMENT RESTREINT 9f31",
                },
                readable_by=("cs",),
                recovery_helpers=(recovery_helper,),
                restriction_reason="Reserve au compartiment contentieux.",
            ),
        ]

    def _archive(self) -> DownloadableArchive:
        return build_downloadable_archive(
            vault_id="vlt_test",
            archive_id="archive_copro_2026_05_20",
            recipient_role="coowner",
            parts=self._parts(),
            recipient_compartment_keys={"copro_open": "key-open-2026"},
            created_at="2026-05-20T10:00:00Z",
        )

    def test_archive_complete_keeps_restricted_content_out_of_manifest_and_report(self) -> None:
        archive = self._archive()

        self.assertEqual(archive.download_name, "archive_copro_2026_05_20.coproscope-archive.json")
        self.assertEqual(set(archive.sealed_payloads), {"part_pv_ag_2026", "part_contentieux_1"})
        access_by_part = {entry.part_id: entry.access for entry in archive.manifest.entries}
        self.assertEqual(access_by_part["part_pv_ag_2026"], READABLE)
        self.assertEqual(access_by_part["part_contentieux_1"], RESTRICTED)

        manifest_json = json.dumps(archive.manifest.as_dict(), ensure_ascii=True, sort_keys=True)
        self.assertNotIn("CONTENU STRICTEMENT RESTREINT", manifest_json)
        self.assertNotIn("Assignation confidentielle", manifest_json)

        integrity = verify_archive_integrity(archive)
        self.assertTrue(integrity.ok, integrity.as_dict())

        result = reconstruct_authorized_corpus(archive)
        self.assertTrue(result.ok)
        self.assertEqual([part.part_id for part in result.reconstructed], ["part_pv_ag_2026"])
        self.assertEqual([proof.part_id for proof in result.restricted], ["part_contentieux_1"])
        self.assertEqual(result.reconstructed[0].payload["decision"], "Budget vote")

        report = build_novice_reconstruction_report(result)
        report_payload = report.as_dict()
        report_json = json.dumps(report_payload, ensure_ascii=True, sort_keys=True)
        self.assertEqual(len(report_payload["ce_que_je_peux_reconstruire"]), 1)
        self.assertEqual(len(report_payload["ce_qui_existe_mais_reste_restreint"]), 1)
        self.assertEqual(len(report_payload["qui_peut_aider_a_recuperer"]), 1)
        self.assertIn("1 element(s) reconstructible(s)", report_payload["summary"])
        self.assertNotIn("CONTENU STRICTEMENT RESTREINT", report_json)
        self.assertNotIn("Assignation confidentielle", report_json)

    def test_integrity_manifest_detects_payload_tampering_without_decryption(self) -> None:
        archive = self._archive()
        tampered_payloads = dict(archive.sealed_payloads)
        tampered_payloads["part_contentieux_1"] = tampered_payloads["part_contentieux_1"] + b"x"
        tampered = replace(archive, sealed_payloads=tampered_payloads)

        report = verify_archive_integrity(tampered)

        self.assertFalse(report.ok)
        self.assertIn("sealed_hash_mismatch", {finding.code for finding in report.findings})
        self.assertIn("sealed_size_mismatch", {finding.code for finding in report.findings})

    def test_manifest_hash_covers_entry_access_and_existence_proofs(self) -> None:
        archive = self._archive()
        first_entry = archive.manifest.entries[0]
        changed_entry = replace(first_entry, access=RESTRICTED, restriction_reason="Modifie hors manifeste.")
        changed_entries = (changed_entry,) + archive.manifest.entries[1:]
        changed_manifest = ArchiveManifest(
            archive_id=archive.manifest.archive_id,
            vault_id=archive.manifest.vault_id,
            recipient_role=archive.manifest.recipient_role,
            created_at=archive.manifest.created_at,
            entries=changed_entries,
            manifest_sha256=archive.manifest.manifest_sha256,
        )
        changed_archive = replace(archive, manifest=changed_manifest)

        report = verify_archive_integrity(changed_archive)

        self.assertFalse(report.ok)
        self.assertIn("manifest_hash_mismatch", {finding.code for finding in report.findings})

    def test_wrong_readable_key_does_not_reveal_payload(self) -> None:
        archive = self._archive()

        result = reconstruct_authorized_corpus(
            archive,
            recipient_compartment_keys={"copro_open": "wrong-key"},
        )

        self.assertTrue(result.ok)
        self.assertEqual(result.reconstructed, ())
        self.assertEqual({proof.part_id for proof in result.restricted}, {"part_pv_ag_2026", "part_contentieux_1"})
        reasons = {proof.part_id: proof.reason for proof in result.restricted}
        self.assertEqual(reasons["part_pv_ag_2026"], "Cle presente mais payload illisible.")


if __name__ == "__main__":
    unittest.main()
