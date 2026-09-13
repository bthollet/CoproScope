from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
from io import BytesIO
from pathlib import Path

from coproscope.core.common import load_instance
from coproscope.core.share import audit_repo, export_shareable
from coproscope.modules.agcontentieux import DossierAG
from coproscope.modules.passation_exports import build_passation_derived_export, render_passation_derived_json
from coproscope.modules.requestops import VISIBILITY_RESTRICTED, normalize_request
from coproscope.vault.sync_profiles import audit_sync_folder, known_sync_profiles
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app


FORBIDDEN_TEXT_MARKERS = (
    "PRIVATE_ROUTE_LEAK",
    "PRIVATE_ZIP_LEAK",
    "PRIVATE_PASSATION_LEAK",
    "C:\\Users",
    "file://",
    "/Users/",
    "/home/",
)
FORBIDDEN_ROUTE_PARTS = ("raw", "restricted", "logs", "private")
TOKEN_GATED_ROUTES = (
    "/",
    "/actions",
    "/suggestions",
    "/comptes",
    "/comptes/rapprochement",
    "/documents",
    "/documents/ajouter",
    "/courriers/preuves",
    "/messages/entrants",
    "/incidents",
    "/contrats",
    "/pilotage/activite",
    "/pieces",
    "/demandes",
    "/ag-contentieux",
    "/gouvernance",
    "/gouvernance/compte-rendu-cs",
    "/gouvernance/atelier-ag",
    "/gouvernance/participants-ag",
    "/gouvernance/roles-commissions",
    "/coffre/partage",
    "/pilotage",
    "/confidentialite",
    "/chantiers",
    "/depot",
    "/api/model",
    "/exports/actions.csv",
    "/exports/actions.md",
    "/exports/local.zip",
    "/exports/passation",
    "/exports/passation.json",
    "/exports/passation.txt",
)


class SecurityNoPrivateSyncLeaksTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self, access_token: str | None = None):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")
        return TestClient(create_app(self.instance, 2025, access_token=access_token))

    def test_configured_token_guards_main_views_and_exports(self) -> None:
        client = self._client(access_token="qa-local-token")

        for path in TOKEN_GATED_ROUTES:
            self.assertEqual(client.get(path).status_code, 403, path)

        first_response = client.get("/?token=qa-local-token")
        self.assertEqual(first_response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, first_response.cookies)

        for path in TOKEN_GATED_ROUTES:
            response = client.get(f"{path}?token=qa-local-token")
            self.assertNotEqual(response.status_code, 403, path)

        self.assertEqual(client.get("/health").status_code, 200)

    def test_private_roots_are_not_served_even_with_token(self) -> None:
        for relative in (
            "raw/private_note.txt",
            "restricted/secret.txt",
            "logs/run.log",
            "private/source.txt",
        ):
            path = self.instance_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("PRIVATE_ROUTE_LEAK", encoding="utf-8")

        client = self._client(access_token="qa-local-token")
        for root in FORBIDDEN_ROUTE_PARTS:
            for path in (f"/{root}/private_note.txt", f"/exports/{root}/private_note.txt"):
                response = client.get(f"{path}?token=qa-local-token")
                self.assertEqual(response.status_code, 404, path)
                self.assertNotIn("PRIVATE_ROUTE_LEAK", response.text)

    def test_local_zip_export_excludes_raw_restricted_logs_private_and_mappings(self) -> None:
        allowed = self.instance_root / "outputs" / "reports" / "safe_report.txt"
        allowed.parent.mkdir(parents=True, exist_ok=True)
        allowed.write_text("SAFE_REPORT_INCLUDED", encoding="utf-8")

        blocked_files = (
            self.instance_root / "raw" / "raw_secret.txt",
            self.instance_root / "restricted" / "restricted_secret.txt",
            self.instance_root / "logs" / "run.log",
            self.instance_root / "private" / "private_secret.txt",
            self.instance_root / "outputs" / "reports" / "private" / "nested_secret.txt",
            self.instance_root / "outputs" / "privacy" / "table_correspondance_biffage.csv",
            self.instance_root / "outputs" / "deposits" / "redaction_mapping.csv",
        )
        for path in blocked_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("PRIVATE_ZIP_LEAK", encoding="utf-8")

        response = self._client(access_token="qa-local-token").get("/exports/local.zip?token=qa-local-token")
        self.assertEqual(response.status_code, 200)

        with zipfile.ZipFile(BytesIO(response.content)) as archive:
            names = archive.namelist()
            combined = b"".join(archive.read(name) for name in names)

        self.assertIn("outputs/reports/safe_report.txt", names)
        self.assertIn(b"SAFE_REPORT_INCLUDED", combined)
        self.assertNotIn(b"PRIVATE_ZIP_LEAK", combined)
        self.assertFalse(any(name.startswith(tuple(f"{part}/" for part in FORBIDDEN_ROUTE_PARTS)) for name in names))
        self.assertFalse(any("/private/" in name for name in names))
        self.assertFalse(any("table_correspondance" in name or "mapping" in name for name in names))

    def test_passation_exports_strip_restricted_requests_and_private_paths(self) -> None:
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
                "subject": "PRIVATE_PASSATION_LEAK",
                "summary": "Contact copro@example.org et chemin C:\\Users\\ExampleUser\\raw\\note.txt",
                "proof_ref": "MSG-PRIVATE",
                "source_ref": "REG-DEMANDES",
                "visibility": VISIBILITY_RESTRICTED,
                "next_action": "Traiter hors export derive.",
            }
        )

        document = build_passation_derived_export(
            title="Export sans chemin prive",
            dossiers_ag=[dossier],
            requests=[restricted_request],
            timeline_entries=[
                {
                    "timeline_id": "TL-PRIVATE",
                    "object_id": r"C:\Users\ExampleUser\private.pdf",
                    "source": "action_log",
                    "source_id": "RUN-1",
                    "proof_ref": r"file:///Users/ExampleUser/proof.pdf",
                    "summary": r"Trace issue de C:\Users\ExampleUser\CoproScope\raw\piece.pdf",
                }
            ],
            generated_at="2026-05-20T12:00:00+00:00",
        )
        payload = render_passation_derived_json(document)

        self.assertEqual(document["sections"]["demandes"], [])
        self.assertEqual(document["sections"]["ag"][0]["source_refs"], ["DOC-PUBLIC-1"])
        self.assertIn("[chemin-retire]", document["sections"]["chronologie"][0]["summary"])
        for marker in FORBIDDEN_TEXT_MARKERS:
            self.assertNotIn(marker, payload)
        self.assertNotIn("copro@example.org", payload)
        self.assertNotIn("restricted", payload.lower())

    def test_passation_export_routes_do_not_emit_raw_restricted_logs_or_private_paths(self) -> None:
        client = self._client(access_token="qa-local-token")

        for path in ("/exports/passation", "/exports/passation.json", "/exports/passation.txt"):
            response = client.get(f"{path}?token=qa-local-token")
            self.assertEqual(response.status_code, 200, response.text[:200])
            text = response.text
            for marker in FORBIDDEN_TEXT_MARKERS:
                self.assertNotIn(marker, text)
            self.assertNotRegex(text, r"(?:^|[\\/])(raw|restricted|logs|private)(?:[\\/]|$)")
            if path.endswith(".json"):
                self.assertFalse(json.loads(text)["source_of_truth"])

    def test_sync_profiles_exclude_repository_virtualenv_and_cache_folders(self) -> None:
        expected_exclusions = {
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".cache",
            "node_modules",
            "logs",
            "*.log",
        }

        for profile in known_sync_profiles():
            self.assertTrue(expected_exclusions.issubset(set(profile.mandatory_exclusions)), profile.id)

    def test_sync_audit_flags_nested_private_engine_and_cache_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for relative in (
                ".git/config",
                ".venv/pyvenv.cfg",
                "nested/__pycache__/module.pyc",
                "nested/.pytest_cache/nodeids",
                "nested/.ruff_cache/cache.bin",
                "nested/logs/run.log",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("PRIVATE_SYNC_LEAK", encoding="utf-8")

            audit = audit_sync_folder(root, "local_folder")

        self.assertFalse(audit.clean)
        self.assertIn(".git", audit.forbidden_entries)
        self.assertIn(".venv", audit.forbidden_entries)
        self.assertIn("nested/__pycache__", audit.forbidden_entries)
        self.assertIn("nested/.pytest_cache", audit.forbidden_entries)
        self.assertIn("nested/.ruff_cache", audit.forbidden_entries)
        self.assertIn("nested/logs", audit.forbidden_entries)
        self.assertIn("nested/logs/run.log", audit.forbidden_entries)

    def test_share_audit_and_export_block_oauth_and_ai_secrets_in_allowed_content(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        config_path = repo_root / "server" / "src" / "coproscope" / "configs" / "github_sharing.default.yml"
        oauth_secret = "GOCSPX-secretValue1234567890"
        refresh_token = "1//0gRefreshTokenSecretValue123456"
        openai_key = "sk-proj-123456789012345678901234567890"
        bearer_token = "Bearer ya29.a0AfH6SMSecretTokenValue123456"

        with tempfile.TemporaryDirectory() as temp_dir:
            audit_root = Path(temp_dir) / "repo"
            export_root = Path(temp_dir) / "export"
            (audit_root / "docs").mkdir(parents=True)
            (audit_root / "README.md").write_text("# repo\n", encoding="utf-8")
            (audit_root / "docs" / "safe.md").write_text("# safe\n", encoding="utf-8")
            (audit_root / "docs" / "oauth_dump.md").write_text(
                "\n".join(
                    [
                        f'"client_secret": "{oauth_secret}"',
                        f'"refresh_token": "{refresh_token}"',
                        openai_key,
                        f"Authorization: {bearer_token}",
                    ]
                ),
                encoding="utf-8",
            )

            audit = audit_repo(audit_root, config_path)
            exported = export_shareable(audit_root, config_path, export_root, clean=True)
            manifest_text = (export_root / "share-manifest.json").read_text(encoding="utf-8")
            oauth_dump_exported = (export_root / "docs" / "oauth_dump.md").exists()

        violations = {item["path"]: item["rules"] for item in audit["content_violations"]}
        self.assertIn("docs/oauth_dump.md", audit["blocked"])
        self.assertIn("docs/oauth_dump.md", violations)
        for rule in ("oauth_client_secret", "oauth_refresh_token", "openai_secret_key", "bearer_token"):
            self.assertIn(rule, violations["docs/oauth_dump.md"])
        self.assertIn("docs/safe.md", exported["shareable"])
        self.assertFalse(oauth_dump_exported)
        for secret in (oauth_secret, refresh_token, openai_key, bearer_token):
            self.assertNotIn(secret, json.dumps(audit, ensure_ascii=False))
            self.assertNotIn(secret, manifest_text)


if __name__ == "__main__":
    unittest.main()
