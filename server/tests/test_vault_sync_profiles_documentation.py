from __future__ import annotations

import re
import unittest
from pathlib import Path

from coproscope.vault.sync_profiles import CONFLICT_MARKERS, MANDATORY_EXCLUSIONS, known_sync_profiles


class VaultSyncProfilesDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[2]
        cls.doc_path = cls.repo_root / "docs" / "sync_transport_profiles_v1.md"
        cls.text = cls.doc_path.read_text(encoding="utf-8")
        cls.normalized = cls.text.lower()

    def test_document_exists_and_declares_transport_boundary(self) -> None:
        self.assertTrue(self.doc_path.exists())
        self.assertIn("# Sync transport profiles v1", self.text)
        self.assertIn("sync = transport, pas moteur", self.normalized)
        self.assertIn("le moteur du vault reste local", self.normalized)
        self.assertIn("ne scanne ni processus ni ports", self.normalized)
        self.assertIn("ne deduit pas l'etat de", self.normalized)

    def test_document_lists_all_runtime_profiles_once(self) -> None:
        documented_ids = re.findall(r"^\|\s*`([a-z0-9_]+)`\s*\|", self.text, flags=re.MULTILINE)
        runtime_ids = [profile.id for profile in known_sync_profiles()]

        self.assertEqual(documented_ids, runtime_ids)

    def test_document_covers_each_transport_family(self) -> None:
        required_markers = [
            "Google Drive Desktop",
            "OneDrive",
            "Dropbox",
            "Nextcloud",
            "Syncthing P2P",
            "Backup froid chiffre",
            "backup froid",
            "pair-a-pair",
            "offline_backup",
            "folder_transport",
            "peer_to_peer",
        ]

        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), self.normalized)

    def test_document_tracks_runtime_exclusions_and_conflict_markers(self) -> None:
        for exclusion in MANDATORY_EXCLUSIONS:
            with self.subTest(exclusion=exclusion):
                self.assertIn(f"`{exclusion}`", self.text)

        for marker in CONFLICT_MARKERS:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), self.normalized)

    def test_document_forbids_private_runtime_and_temporary_sync_surface(self) -> None:
        required_markers = [
            ".git",
            ".venv",
            "cache",
            "logs",
            "exports temporaires",
            "tmp_exports",
            "exports_tmp",
            "temporary_exports",
            "blobs dechiffres",
        ]

        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), self.normalized)

    def test_conflict_response_is_attention_first_and_integrity_driven(self) -> None:
        reaction_section = self._section("## Marqueurs de conflit", "## Risques par transport")

        required_markers = [
            "signal `attention`",
            "revue humaine",
            "comparer les hashes, signatures et evenements sources",
            "ne jamais choisir une version par horodatage fournisseur seul",
            "ne pas verrouiller tout le vault pour un simple conflit fournisseur",
            "suspendre la publication",
            "passer en lecture seule uniquement si l'integrite vault est en incident",
        ]

        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), reaction_section.lower())

    def test_audit_contract_keeps_detection_static_and_transport_only(self) -> None:
        audit_section = self._section("## Contrat d'audit")

        for marker in [
            "signaux observables dans le dossier",
            "information",
            "attention",
            "protection",
            "incident",
            "ne remplace pas la verification cryptographique",
            "ne doit pas devenir un moteur de sync cache",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker.lower(), audit_section.lower())

    def _section(self, start: str, end: str | None = None) -> str:
        start_index = self.text.index(start)
        end_index = self.text.index(end, start_index) if end else len(self.text)
        return self.text[start_index:end_index]


if __name__ == "__main__":
    unittest.main()
