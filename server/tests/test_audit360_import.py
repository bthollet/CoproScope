from __future__ import annotations

import csv
import io
import json
import shutil
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from coproscope.cli import _dispatch, build_parser
from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, RunContext, load_instance, read_csv, write_csv
from coproscope.modules import audit360
from coproscope.vault import reconstruction


class Audit360ImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.local_root = self.root / "local"
        self.sync_root = self.root / "sync"
        self.db_path = self.local_root / "audit360.sqlite3"
        reconstruction.rebuild_cache_from_events([], self.db_path, vault_id="vault_test")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_import_csv_creates_derived_objects_without_path_leak(self) -> None:
        source = self._write_csv(
            "audit360_fictif.csv",
            [
                {
                    "source_kind": "audit360_matrix",
                    "source_file": "matrice_preuves_attendues.csv",
                    "source_row_id": "row-17",
                    "control_id": "CTRL-ASSURANCE",
                    "point_de_controle": "Attestation assurance immeuble",
                    "constat": "La piece n'est pas visible dans le corpus transmis.",
                    "risque_concret": "Le conseil syndical ne peut pas verifier la couverture.",
                    "preuve_attendue": "Attestation assurance multirisque 2026",
                    "action_a_faire": "Demander l'attestation au syndic.",
                    "acteur_ou_entreprise": "Syndic",
                    "priorite": "P1",
                    "statut_action": "open",
                }
            ],
        )

        result = audit360.import_audit360_file(
            local_root=self.local_root,
            sync_root=self.sync_root,
            path=source,
            db_path=self.db_path,
            imported_at="2026-05-22T07:32:00+00:00",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["source_file"], "audit360_fictif.csv")
        self.assertEqual(result["created"]["points"], 1)
        self.assertEqual(result["created"]["actions"], 1)
        self.assertEqual(result["created"]["expected_pieces"], 1)
        payload = json.dumps(result, ensure_ascii=False)
        self.assertNotIn(str(self.local_root), payload)
        self.assertNotIn(str(self.db_path), payload)
        self.assertIn("Import derive local", result["notice"])

    def test_import_is_idempotent(self) -> None:
        source = self._write_csv(
            "audit360_fictif.csv",
            [
                {
                    "source_kind": "audit360_matrix",
                    "source_file": "matrice_preuves_attendues.csv",
                    "source_row_id": "row-17",
                    "point_de_controle": "Attestation assurance immeuble",
                    "preuve_attendue": "Attestation assurance multirisque 2026",
                    "action_a_faire": "Demander l'attestation au syndic.",
                }
            ],
        )

        audit360.import_audit360_file(
            local_root=self.local_root,
            sync_root=self.sync_root,
            path=source,
            db_path=self.db_path,
            imported_at="2026-05-22T07:32:00+00:00",
        )
        second = audit360.import_audit360_file(
            local_root=self.local_root,
            sync_root=self.sync_root,
            path=source,
            db_path=self.db_path,
            imported_at="2026-05-22T07:33:00+00:00",
        )

        self.assertEqual(second["created"]["points"], 0)
        self.assertEqual(second["created"]["actions"], 0)
        self.assertEqual(second["created"]["expected_pieces"], 0)

    def test_rejects_private_hints_without_importing_or_echoing_values(self) -> None:
        source = self._write_csv(
            "audit360_prive.csv",
            [
                {
                    "source_kind": "audit360_matrix",
                    "source_file": r"C:\Users\ExampleUser\raw\secret.csv",
                    "source_row_id": "row-private",
                    "point_de_controle": "Controle prive",
                    "action_a_faire": "Relancer avec ?token=local-secret",
                }
            ],
        )

        result = audit360.import_audit360_file(
            local_root=self.local_root,
            sync_root=self.sync_root,
            path=source,
            db_path=self.db_path,
        )

        self.assertFalse(result["ok"])
        self.assertGreaterEqual(len(result["privacy_violations"]), 2)
        payload = json.dumps(result, ensure_ascii=False)
        self.assertNotIn(r"C:\Users\ExampleUser", payload)
        self.assertNotIn("local-secret", payload)
        self.assertEqual(self._count_rows("points"), 0)
        self.assertEqual(self._count_rows("actions"), 0)
        self.assertEqual(self._count_rows("expected_pieces"), 0)

    def test_cli_import_audit360_rows_prints_sanitized_summary(self) -> None:
        source = self._write_csv(
            "audit360_fictif.csv",
            [
                {
                    "source_kind": "audit360_matrix",
                    "source_file": "matrice_preuves_attendues.csv",
                    "source_row_id": "row-17",
                    "point_de_controle": "Attestation assurance immeuble",
                    "preuve_attendue": "Attestation assurance multirisque 2026",
                    "action_a_faire": "Demander l'attestation au syndic.",
                }
            ],
        )
        parser = build_parser()
        args = parser.parse_args(
            [
                "vault",
                "import-audit360-rows",
                "--local-root",
                str(self.local_root),
                "--sync-root",
                str(self.sync_root),
                "--path",
                str(source),
                "--db-path",
                str(self.db_path),
                "--imported-at",
                "2026-05-22T07:32:00+00:00",
            ]
        )

        output = io.StringIO()
        with redirect_stdout(output):
            code = _dispatch(args)

        self.assertEqual(code, 0)
        stdout = output.getvalue()
        self.assertIn("audit360_fictif.csv", stdout)
        self.assertNotIn(str(self.local_root), stdout)
        self.assertNotIn(str(self.db_path), stdout)

    def test_prepare_anonymized_audit_sources_uses_redacted_derivative_only(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        instance_root = self.root / "synthetic_copro"
        shutil.copytree(source_example, instance_root)
        instance = load_instance(str(instance_root / "instance.yml"), None)
        redacted = instance.root("outputs") / "redacted" / "DOC-TEST.redacted.txt"
        redacted.parent.mkdir(parents=True, exist_ok=True)
        redacted.write_text("Resolution 1 - Vote du contrat [BIFFE_PERSON_NAME]\n", encoding="utf-8")
        write_csv(
            instance.register("documents"),
            list(DEFAULT_DOCUMENT_FIELDS),
            [
                {
                    "doc_id": "DOC-TEST",
                    "file_name": "convocation_ag.pdf",
                    "document_type": "Convocation_AG",
                    "sha256": "source-sha",
                    "original_path": "raw/convocation_ag.pdf",
                    "publication_form": "redaction_required",
                    "required_transformations": "redaction",
                    "redaction_status": "REDACTED",
                    "redacted_path": "outputs/redacted/DOC-TEST.redacted.txt",
                    "redacted_sha256": "redacted-sha",
                    "review_required": "YES",
                }
            ],
        )

        result = audit360.prepare_anonymized_audit_sources(
            instance,
            RunContext(instance, "audit360 prepare"),
            doc_id="DOC-TEST",
        )

        self.assertEqual(result["ready_for_cloud_audit"], 1)
        _, rows = read_csv(instance.artifact("reports_dir") / "audit_sources_anonymized.csv")
        self.assertEqual(rows[0]["audit_status"], "READY_ANONYMIZED_TEXT")
        self.assertEqual(rows[0]["cloud_allowed"], "YES")
        self.assertEqual(rows[0]["audit_input_path"], "")
        self.assertNotIn("raw/convocation_ag.pdf", json.dumps(rows, ensure_ascii=False))
        audit_text = instance.root("workspace") / rows[0]["audit_text_path"]
        self.assertTrue(audit_text.exists())

    def test_prepare_anonymized_audit_sources_falls_back_to_sanitized_extracted_text(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        instance_root = self.root / "synthetic_copro"
        shutil.copytree(source_example, instance_root)
        instance = load_instance(str(instance_root / "instance.yml"), None)
        text_path = instance.root("staging") / "text" / "DOC-TEST.native.txt"
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(
            "Contact: syndic@example.test\nResolution 1 - Vote du contrat de syndic.\n",
            encoding="utf-8",
        )
        redacted = instance.root("outputs") / "redacted" / "DOC-TEST.redacted.pdf"
        redacted.parent.mkdir(parents=True, exist_ok=True)
        redacted.write_bytes(b"%PDF-1.4\n% no extractable text fixture\n")
        write_csv(
            instance.register("documents"),
            list(DEFAULT_DOCUMENT_FIELDS),
            [
                {
                    "doc_id": "DOC-TEST",
                    "file_name": "convocation_ag.pdf",
                    "document_type": "Convocation_AG",
                    "sha256": "source-sha",
                    "original_path": "raw/convocation_ag.pdf",
                    "publication_form": "redaction_required",
                    "required_transformations": "redaction",
                    "redaction_status": "REDACTED",
                    "redacted_path": "outputs/redacted/DOC-TEST.redacted.pdf",
                    "redacted_sha256": "redacted-sha",
                    "text_path": "staging/text/DOC-TEST.native.txt",
                    "review_required": "YES",
                }
            ],
        )

        result = audit360.prepare_anonymized_audit_sources(
            instance,
            RunContext(instance, "audit360 prepare"),
            doc_id="DOC-TEST",
        )

        self.assertEqual(result["ready_for_cloud_audit"], 1)
        _, rows = read_csv(instance.artifact("reports_dir") / "audit_sources_anonymized.csv")
        audit_text = (instance.root("workspace") / rows[0]["audit_text_path"]).read_text(encoding="utf-8")
        self.assertIn("Resolution 1", audit_text)
        self.assertIn("[BIFFE_EMAIL]", audit_text)
        self.assertNotIn("syndic@example.test", audit_text)

    def test_prepare_anonymized_audit_sources_does_not_block_on_generic_lots_word(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        instance_root = self.root / "synthetic_copro"
        shutil.copytree(source_example, instance_root)
        instance = load_instance(str(instance_root / "instance.yml"), None)
        redacted = instance.root("outputs") / "redacted" / "DOC-TEST.redacted.txt"
        redacted.parent.mkdir(parents=True, exist_ok=True)
        redacted.write_text("Resolution 1 - Repartition entre les lots generiques.\n", encoding="utf-8")
        write_csv(
            instance.register("documents"),
            list(DEFAULT_DOCUMENT_FIELDS),
            [
                {
                    "doc_id": "DOC-TEST",
                    "file_name": "convocation_ag.pdf",
                    "document_type": "Convocation_AG",
                    "sha256": "source-sha",
                    "original_path": "raw/convocation_ag.pdf",
                    "publication_form": "redaction_required",
                    "required_transformations": "redaction",
                    "redaction_status": "REDACTED",
                    "redacted_path": "outputs/redacted/DOC-TEST.redacted.txt",
                    "redacted_sha256": "redacted-sha",
                    "review_required": "YES",
                }
            ],
        )

        result = audit360.prepare_anonymized_audit_sources(
            instance,
            RunContext(instance, "audit360 prepare"),
            doc_id="DOC-TEST",
        )

        self.assertEqual(result["ready_for_cloud_audit"], 1)
        _, rows = read_csv(instance.artifact("reports_dir") / "audit_sources_anonymized.csv")
        self.assertEqual(rows[0]["audit_status"], "READY_ANONYMIZED_TEXT")

    def _write_csv(self, name: str, rows: list[dict[str, str]]) -> Path:
        path = self.root / name
        fields = sorted({field for row in rows for field in row})
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _count_rows(self, table: str) -> int:
        connection = sqlite3.connect(self.db_path)
        try:
            row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            return int(row[0])
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
