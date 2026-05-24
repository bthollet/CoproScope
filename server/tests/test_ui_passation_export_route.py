from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance
from coproscope.web.app import PASSATION_EXPORT_WATERMARK, TOKEN_COOKIE_NAME, create_app


def _html_hrefs(html: str) -> list[str]:
    return [unescape(href) for href in re.findall(r"""href=["']([^"']+)["']""", html)]


class UiPassationExportRouteTests(unittest.TestCase):
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

    def test_actions_route_reuses_filtered_dashboard_model_in_context(self) -> None:
        from coproscope.web import app as app_module

        calls = 0
        original_build = app_module.build_dashboard_model

        def counted_build(*args, **kwargs):
            nonlocal calls
            calls += 1
            return original_build(*args, **kwargs)

        with patch.object(app_module, "build_dashboard_model", side_effect=counted_build):
            response = self._client(access_token="local-secret").get("/actions?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(calls, 1)

    def test_passation_preview_reuses_dashboard_model_for_document_and_context(self) -> None:
        from coproscope.web import app as app_module

        calls = 0
        original_build = app_module.build_dashboard_model

        def counted_build(*args, **kwargs):
            nonlocal calls
            calls += 1
            return original_build(*args, **kwargs)

        with patch.object(app_module, "build_dashboard_model", side_effect=counted_build):
            response = self._client(access_token="local-secret").get(
                "/exports/passation?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(calls, 1)

    def test_passation_exports_require_token_and_return_derived_json_and_text(self) -> None:
        client = self._client(access_token="local-secret")

        for path in ["/exports/passation.json", "/exports/passation.txt"]:
            self.assertEqual(client.get(path).status_code, 403, path)

        json_response = client.get("/exports/passation.json?token=local-secret")
        text_response = client.get("/exports/passation.txt?token=local-secret")

        self.assertEqual(json_response.status_code, 200)
        self.assertEqual(text_response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, json_response.cookies)
        self.assertIn('filename="coproscope_passation_derivee_2025.json"', json_response.headers["content-disposition"])
        self.assertIn('filename="coproscope_passation_derivee_2025.txt"', text_response.headers["content-disposition"])

        payload = json_response.json()
        self.assertEqual(payload["watermark"], PASSATION_EXPORT_WATERMARK)
        self.assertFalse(payload["source_of_truth"])
        self.assertEqual(payload["scope"]["kind"], "passation_ag_contentieux")
        self.assertIn("sections", payload)
        self.assertIn(PASSATION_EXPORT_WATERMARK, text_response.text)
        self.assertIn("Passation", text_response.text)

    def test_passation_default_route_returns_token_safe_html_preview(self) -> None:
        client = self._client(access_token="local-secret")

        self.assertEqual(client.get("/exports/passation", follow_redirects=False).status_code, 403)

        response = client.get(
            "/exports/passation?token=local-secret&scope=event&selected=MEM-DOC-7D412766",
            follow_redirects=False,
        )
        text = unescape(response.text)
        hrefs = _html_hrefs(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("Apercu de passation", text)
        self.assertIn(PASSATION_EXPORT_WATERMARK, text)
        self.assertIn("source_of_truth", text)
        self.assertIn("false", text)
        self.assertIn("Sections incluses", text)
        self.assertIn("Elements exclus ou bloques", text)
        self.assertIn("Formats disponibles", text)
        self.assertNotIn(str(self.instance_root), text)

        expected_txt = "/exports/passation.txt?scope=event&selected=MEM-DOC-7D412766&token=local-secret"
        expected_json = "/exports/passation.json?scope=event&selected=MEM-DOC-7D412766&token=local-secret"
        expected_blocker = "/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR?scope=event&selected=MEM-DOC-7D412766&token=local-secret"
        self.assertIn(expected_txt, hrefs)
        self.assertIn(expected_json, hrefs)
        self.assertIn(expected_blocker, hrefs)
        self.assertNotIn("/exports/passation.txt?token=local-secret", hrefs)
        self.assertNotIn("/exports/passation.json?token=local-secret", hrefs)
        self.assertIn("Apercu de passation - extrait evenement", text)
        self.assertIn("Perimetre filtre", text)
        self.assertIn("<strong>1</strong><span>evenements inclus</span>", text)
        self.assertNotIn("<strong>12</strong><span>evenements inclus</span>", text)

        followed = client.get(expected_txt)
        self.assertEqual(followed.status_code, 200)
        self.assertIn(PASSATION_EXPORT_WATERMARK, followed.text)

    def test_passation_preview_links_blockers_to_detail_with_scope_and_token(self) -> None:
        response = self._client(access_token="local-secret").get(
            "/exports/passation?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
        )

        self.assertEqual(response.status_code, 200)
        text = unescape(response.text)
        hrefs = _html_hrefs(response.text)
        expected = (
            "/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR"
            "?scope=event&selected=MEM-DOC-7D412766&token=local-secret"
        )
        self.assertIn("Relance ascenseur non tracee", text)
        self.assertIn(expected, hrefs)

    def test_passation_blocker_detail_route_200(self) -> None:
        response = self._client(access_token="local-secret").get(
            "/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR"
            "?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
        )
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Detail blocage export", text)
        self.assertIn("Relance ascenseur non tracee", text)
        self.assertIn("Pourquoi ce n'est pas exporte", text)
        self.assertIn("source_of_truth false", text)
        self.assertIn("<strong>1</strong><span>Inclus</span>", text)
        self.assertIn("<strong>2</strong><span>Formats</span>", text)

    def test_passation_blocker_detail_lists_reason_exclusions_and_required_proofs(self) -> None:
        text = unescape(
            self._client(access_token="local-secret")
            .get(
                "/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR"
                "?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
            )
            .text
        )

        self.assertIn("Date et canal d'envoi externe manquent", text)
        self.assertIn("Brouillon pris pour un envoi reel", text)
        self.assertIn("Exclu", text)
        self.assertIn("Masque", text)
        self.assertIn("A verifier", text)
        self.assertIn("Date d'envoi", text)
        self.assertIn("Canal et destinataire", text)

    def test_passation_blocker_detail_download_is_locked(self) -> None:
        text = unescape(
            self._client(access_token="local-secret")
            .get(
                "/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR"
                "?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
            )
            .text
        )

        self.assertIn("Telecharger export derive", text)
        self.assertIn('aria-disabled="true"', text)
        self.assertIn("TXT verrouille", text)
        self.assertIn("Relance ascenseur non tracee", text)

    def test_passation_blocker_detail_links_are_token_safe_and_preserve_scope(self) -> None:
        response = self._client(access_token="local-secret").get(
            "/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR"
            "?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
        )

        self.assertEqual(response.status_code, 200)
        hrefs = _html_hrefs(response.text)
        self.assertIn("/exports/passation?scope=event&selected=MEM-DOC-7D412766&token=local-secret", hrefs)
        self.assertIn(
            "/demandes/relance?scope=event&selected=MEM-DOC-7D412766"
            "&request_id=REQ-FICTIF-ASCENSEUR-SYNDIC&token=local-secret",
            hrefs,
        )
        self.assertIn(
            "/actions/ACTION-FICTIF-ASC-2025?scope=event&selected=MEM-DOC-7D412766&token=local-secret",
            hrefs,
        )
        self.assertFalse(any("token=local-secret&token=local-secret" in href for href in hrefs))

    def test_passation_blocker_detail_unknown_id_has_safe_empty_state(self) -> None:
        response = self._client(access_token="local-secret").get(
            "/exports/passation/blocages/UNKNOWN-BLOCKER?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
        )
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Blocage introuvable", text)
        self.assertIn("Retour a l'apercu", text)
        self.assertIn("Voir actions ouvertes", text)

    def test_passation_blocker_detail_masks_private_path_like_ids(self) -> None:
        response = self._client(access_token="local-secret").get(
            "/exports/passation/blocages/C:%5CUsers%5CExampleUser%5Craw%5Csecret.pdf"
            "?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
        )
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Blocage introuvable", text)
        self.assertIn("reference-locale-masquee", text)
        self.assertNotIn("Users", text)
        self.assertNotIn("secret.pdf", text)

    def test_passation_blocker_detail_no_private_path_or_raw_leak(self) -> None:
        response = self._client(access_token="local-secret").get(
            "/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR"
            "?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
        )
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(str(self.instance_root), text)
        self.assertNotIn("C:\\Users", text)
        self.assertNotRegex(text, r"\braw\b")
        self.assertNotRegex(text, r"\brestricted\b")
        self.assertNotRegex(text, r"\blogs\b")
        self.assertNotIn("file://", text)

    def test_passation_blocker_detail_source_of_truth_false(self) -> None:
        response = self._client(access_token="local-secret").get(
            "/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR"
            "?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
        )
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("source_of_truth false", text)
        self.assertIn("Non source de verite", text)

    def test_passation_export_links_memory_events_documents_and_open_topics(self) -> None:
        response = self._client(access_token="local-secret").get("/exports/passation.json?token=local-secret")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        passation = payload["sections"]["passation"]
        chronologie = payload["sections"]["chronologie"]
        preuves = payload["sections"]["preuves"]

        self.assertGreater(len(passation.get("open_points", [])), 2)
        self.assertTrue(any(card.get("source") == "memoire_copropriete" for card in chronologie))
        self.assertTrue(any(card.get("proof_refs") for card in chronologie))
        self.assertTrue(any(bundle.get("object_id") == "documents-memoire-passation-2025" for bundle in preuves))

    def test_passation_event_scope_returns_selected_event_extract(self) -> None:
        client = self._client(access_token="local-secret")

        response = client.get(
            "/exports/passation.json?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["scope"]["kind"], "passation_event")
        self.assertEqual(payload["scope"]["selected"], "MEM-DOC-7D412766")
        self.assertEqual(len(payload["sections"]["chronologie"]), 1)
        self.assertEqual(payload["sections"]["chronologie"][0]["object_id"], "MEM-DOC-7D412766")

        text_response = client.get(
            "/exports/passation.txt?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
        )
        self.assertEqual(text_response.status_code, 200)
        self.assertIn("MEM-DOC-7D412766", text_response.text)
        self.assertNotIn("MEM-DOC-816608C5", text_response.text)

    def test_passation_event_scope_with_private_selected_does_not_broaden_to_global_export(self) -> None:
        client = self._client(access_token="local-secret")
        private_selected = "C:%5CUsers%5CExampleUser%5Craw%5Csecret.pdf"

        response = client.get(f"/exports/passation.json?token=local-secret&scope=event&selected={private_selected}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertEqual(payload["scope"]["kind"], "passation_event")
        self.assertEqual(payload["scope"]["selected"], "reference-locale-masquee")
        self.assertEqual(payload["sections"]["chronologie"], [])
        self.assertEqual(payload["source_refs"], [])
        self.assertEqual(payload["proof_refs"], [])
        self.assertNotIn("MEM-DOC-7D412766", serialized)
        self.assertNotIn("C:\\Users", serialized)
        self.assertNotIn("secret.pdf", serialized)
        self.assertNotRegex(serialized, r"\braw\b")

    def test_passation_blocker_detail_route_is_actionable_and_token_safe(self) -> None:
        client = self._client(access_token="local-secret")

        self.assertEqual(client.get("/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR").status_code, 403)
        response = client.get(
            "/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR?token=local-secret&scope=event&selected=MEM-DOC-7D412766"
        )
        text = unescape(response.text)
        hrefs = _html_hrefs(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Detail blocage export", text)
        self.assertIn("Relance ascenseur non tracee", text)
        self.assertIn("Date et canal d'envoi externe manquent", text)
        self.assertIn("Brouillon de relance non envoye", text)
        self.assertIn("Preuves attendues", text)
        self.assertIn("Telecharger export derive - verrouille", text)
        self.assertIn("source_of_truth false", text)
        self.assertIn("Donnees FICTIVES de test", text)
        self.assertIn(
            "/exports/passation?scope=event&selected=MEM-DOC-7D412766&token=local-secret",
            hrefs,
        )
        self.assertIn(
            "/demandes/relance?scope=event&selected=MEM-DOC-7D412766&request_id=REQ-FICTIF-ASCENSEUR-SYNDIC&token=local-secret",
            hrefs,
        )
        self.assertIn(
            "/exports/passation?scope=event&selected=MEM-DOC-7D412766&exclude=BLOCK-FICTIF-RELANCE-ASCENSEUR&token=local-secret",
            hrefs,
        )
        self.assertNotIn(str(self.instance_root), text)
        self.assertNotRegex(text, r"file://|raw[\\/]|restricted[\\/]|logs[\\/]")

    def test_passation_blocker_unknown_or_private_id_uses_safe_empty_state(self) -> None:
        client = self._client(access_token="local-secret")

        response = client.get("/exports/passation/blocages/C:%5CUsers%5Csecret?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Blocage introuvable", text)
        self.assertIn("Retour apercu", text)
        self.assertNotIn("C:\\Users", text)

    def test_passation_export_does_not_serve_raw_restricted_logs_or_private_paths(self) -> None:
        leaks = {
            self.instance_root / "raw" / "secret.txt": "RAW_ROUTE_LEAK",
            self.instance_root / "restricted" / "secret.txt": "RESTRICTED_ROUTE_LEAK",
            self.instance_root / "logs" / "run.log": "LOG_ROUTE_LEAK",
        }
        for path, marker in leaks.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(marker, encoding="utf-8")

        client = self._client(access_token="local-secret")
        combined = "\n".join(
            [
                client.get("/exports/passation?token=local-secret").text,
                client.get("/exports/passation/blocages/BLOCK-FICTIF-RELANCE-ASCENSEUR?token=local-secret").text,
                client.get("/exports/passation.json?token=local-secret").text,
                client.get("/exports/passation.txt?token=local-secret").text,
            ]
        )

        self.assertNotIn("RAW_ROUTE_LEAK", combined)
        self.assertNotIn("RESTRICTED_ROUTE_LEAK", combined)
        self.assertNotIn("LOG_ROUTE_LEAK", combined)
        self.assertNotIn(str(self.instance_root), combined)
        self.assertNotIn("C:\\Users", combined)
        self.assertNotRegex(combined, r"\braw\b")
        self.assertNotRegex(combined, r"\brestricted\b")
        self.assertNotRegex(combined, r"\blogs\b")

        for path in [
            "/exports/passation/raw/secret.txt",
            "/exports/passation/restricted/secret.txt",
            "/exports/passation/logs/run.log",
        ]:
            response = client.get(f"{path}?token=local-secret")
            self.assertEqual(response.status_code, 404, path)

    def test_json_payload_is_serialized_derived_export_not_raw_objects(self) -> None:
        response = self._client(access_token="local-secret").get(
            "/exports/passation.json",
            headers={"x-coproscope-token": "local-secret"},
        )

        self.assertEqual(response.status_code, 200)
        serialized = json.dumps(response.json(), ensure_ascii=False, sort_keys=True)
        self.assertNotIn('"payload"', serialized)
        self.assertNotIn('"metadata"', serialized)
        self.assertNotIn('"absolute_path"', serialized)
        self.assertNotIn('"local_path"', serialized)
        self.assertIn("export_id", response.json())


if __name__ == "__main__":
    unittest.main()
