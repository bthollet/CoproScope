from __future__ import annotations

import unittest
from pathlib import Path


class AntiConfiscationKeysStrategyDocTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[2]
        cls.doc_path = cls.repo_root / "docs" / "strategie_anti_confiscation_cles.md"
        cls.text = cls.doc_path.read_text(encoding="utf-8")
        cls.normalized = cls.text.lower()

    def test_document_exists_and_stays_generic(self) -> None:
        self.assertTrue(self.doc_path.exists())
        self.assertIn("# Strategie anti-confiscation des cles", self.text)
        self.assertIn("reste generique", self.normalized)
        self.assertIn("aucune donnee privee", self.normalized)

        forbidden_private_markers = [
            "adresse personnelle",
            "numero de lot",
            "iban",
            "telephone personnel",
            "email personnel",
            "mot de passe",
        ]
        for marker in forbidden_private_markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.normalized)

    def test_archive_strategy_covers_complete_encrypted_download_and_restricted_content(self) -> None:
        section = self._section("## Archive complete chiffree", "## Verification sans tout lire")
        compact = self._compact(section)

        required_markers = [
            "telecharger l'archive complete chiffree",
            "contenus restreints sous forme chiffree",
            "blobs chiffres",
            "enveloppes de cles",
            "sans cle en clair",
            "rapport novice",
            "transport n'est jamais presente comme une garantie cloud",
        ]

        for marker in required_markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, compact)

    def test_verification_and_reconstruction_are_possible_without_reading_everything(self) -> None:
        verification = self._section("## Verification sans tout lire", "## Reconstruction autorisee")
        reconstruction = self._section("## Reconstruction autorisee", "## Contenus restreints")

        for marker in [
            "hash canonique du manifeste",
            "preuve d'existence",
            "compteur d'evenements",
            "ce_qui_existe_mais_reste_restreint",
            "ce_qui_est_manquant_ou_suspect",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, verification.lower())

        for marker in [
            "cache vide",
            "verifier le manifeste",
            "preuves de presence",
            "cle est absente, revoquee ou incoherente",
            "memoire lisible partielle mais verifiable",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, reconstruction.lower())

    def test_restricted_content_quorum_revocation_and_reader_copies_have_explicit_limits(self) -> None:
        restricted = self._section("## Contenus restreints", "## Quorum et partage de secours")
        quorum = self._section("## Quorum et partage de secours", "## Revocation honnete")
        revocation = self._section("## Revocation honnete", "## Copies lectrices")
        reader_copies = self._section("## Copies lectrices", "## Alertes de capture et suppression")
        compact_revocation = self._compact(revocation)
        compact_reader_copies = self._compact(reader_copies)

        for marker in [
            "inaccessibles sans cle",
            "aucun payload restreint dans le manifeste clair",
            "preuve d'existence verifiable par hash",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, restricted.lower())

        for marker in [
            "seuil minimal de quorum",
            "parts inutilisables seules",
            "rotation apres depart",
            "key_recovery_performed",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, quorum.lower())

        for marker in [
            "bloquer les nouveaux dechiffrements",
            "conserver les signatures et evenements valides produits avant revocation",
            "effacer une copie locale deja dechiffree",
            "fausse promesse de securite",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, compact_revocation)

        for marker in [
            "copie lectrice",
            "conserver l'archive complete chiffree",
            "sans disposer forcement de toutes les cles",
            "ne peut pas modifier le vault",
            "lire les compartiments restreints sans cle",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, compact_reader_copies)

    def test_alerts_and_acceptance_criteria_cover_capture_and_malicious_deletion(self) -> None:
        alerts = self._section("## Alertes de capture et suppression", "## UX attendue")
        acceptance = self._section("## Criteres d'acceptation testables", "## Non-objectifs")

        for marker in [
            "capture_possible",
            "suppression_suspecte",
            "archive_incomplete",
            "cle_a_risque",
            "copie_lectrice_obsolete",
            "revocation_incomplete",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, alerts)

        for marker in [
            "archive complete chiffree",
            "payloads restreints chiffres",
            "manifest",
            "cache vide",
            "une seule part de secours",
            "quorum valide",
            "revocation bloque les acces futurs",
            "copie lectrice",
            "suppression malveillante",
            "capture possible",
            "aucune donnee privee",
        ]:
            with self.subTest(marker=marker):
                self.assertIn(marker, acceptance.lower())

    def _section(self, start: str, end: str | None = None) -> str:
        start_index = self.text.index(start)
        end_index = self.text.index(end, start_index) if end else len(self.text)
        return self.text[start_index:end_index]

    def _compact(self, value: str) -> str:
        return " ".join(value.lower().split())


if __name__ == "__main__":
    unittest.main()
