from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from urllib.parse import unquote

from coproscope.core.common import load_instance
from coproscope.web.app import PASSATION_EXPORT_WATERMARK, TOKEN_COOKIE_NAME, create_app


PRIMARY_UI_ROUTES = [
    ("/", "Ce qui demande attention maintenant"),
    ("/actions", "Boite de travail du conseil syndical"),
    ("/suggestions", "Suggestions utiles"),
    ("/comptes", "Controle des comptes"),
    ("/comptes/rapprochement", "Controle des comptes"),
    ("/documents", "Documents, preuves et demandes"),
    ("/courriers/preuves", "Courriers et preuves"),
    ("/messages/entrants", "Messages entrants"),
    ("/incidents", "Incidents et sinistres"),
    ("/contrats", "Contrats et obligations"),
    ("/pieces", "Atelier pieces"),
    ("/demandes", "Boite de demandes a suivre"),
    ("/ag-contentieux", "AG, contentieux, passation"),
    ("/pilotage", "Pilotage des indicateurs"),
    ("/pilotage/activite", "Activite en cours"),
    ("/gouvernance", "Tableau de controle local"),
    ("/gouvernance/compte-rendu-cs", "Compte rendu du conseil syndical"),
    ("/gouvernance/atelier-ag", "Atelier AG"),
    ("/gouvernance/participants-ag", "Participants et droits AG"),
    ("/gouvernance/roles-commissions", "Roles et commissions"),
    ("/coffre/partage", "Coffre et partage"),
    ("/depot", "Depot guide & exports locaux"),
    ("/confidentialite", "Confidentialite et diffusion"),
    ("/chantiers", "Passation conseil syndical"),
]

CYCLE_N_ROUTES = [
    ("/", ("Ce qui demande attention maintenant", "A traiter")),
    ("/actions", ("Registre decisions - actions - preuves", "Prochaine action")),
    ("/suggestions", ("Suggestions utiles", "Revue humaine")),
    ("/actions?priority=P1", ("Registre des decisions", "Fiches action a traiter maintenant")),
    ("/actions?scope=syndic", ("Registre des decisions", "Syndic")),
    ("/actions?status=a_demander", ("Demander au syndic", "Preuve a demander")),
    ("/comptes", ("Controle des comptes", "Prochain geste humain")),
    ("/comptes/rapprochement", ("Controle des comptes", "Lignes a controler")),
    ("/pieces?proof=missing", ("Atelier pieces", "Pieces a demander")),
    ("/chantiers", ("Passation conseil syndical", "Prochaine passation")),
    ("/courriers/preuves", ("Courriers et preuves", "Verifier avant envoi")),
    ("/messages/entrants", ("Messages entrants", "Qualifier maintenant")),
    ("/incidents", ("Incidents et sinistres", "Preuve de cloture")),
    ("/contrats", ("Contrats et obligations", "Preuve attendue")),
    ("/pilotage/activite", ("Activite en cours", "Dernier passage")),
    ("/gouvernance/compte-rendu-cs", ("Compte rendu du conseil syndical", "Verifier avant partage")),
    ("/gouvernance/atelier-ag", ("Atelier AG", "Projet CS - non officiel")),
    ("/gouvernance/participants-ag", ("Participants et droits AG", "Verifier les pouvoirs")),
    ("/gouvernance/roles-commissions", ("Roles et commissions", "Droits par ressource")),
    ("/coffre/partage", ("Coffre et partage", "Verifier avant partage")),
]

COCKPIT_COUNTER_TARGETS = [
    ("/actions?priority=P1", "Registre des decisions"),
    ("/pieces?proof=missing", "Atelier pieces"),
    ("/actions?scope=syndic", "Registre des decisions"),
    ("/ag-contentieux", "AG, contentieux, passation"),
    ("/comptes", "Controle des comptes"),
]

PRIVATE_ROUTE_LEAK_MARKERS = [
    "UI_ROUTE_RAW_LEAK",
    "UI_ROUTE_RESTRICTED_LEAK",
    "UI_ROUTE_LOG_LEAK",
    "UI_ROUTE_PRIVATE_LEAK",
    "ui_route_raw_leak.txt",
    "ui_route_restricted_leak.txt",
    "ui_route_log_leak.log",
    "ui_route_private_leak.txt",
    "raw/ui_route_raw_leak.txt",
    "raw\\ui_route_raw_leak.txt",
    "restricted/ui_route_restricted_leak.txt",
    "restricted\\ui_route_restricted_leak.txt",
    "logs/ui_route_log_leak.log",
    "logs\\ui_route_log_leak.log",
    "private/ui_route_private_leak.txt",
    "private\\ui_route_private_leak.txt",
]

PRIVATE_PATH_PATTERNS = [
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
    re.compile(r"(?:^|[\\/\s\"'=])/(?:Users|home)[\\/]", re.IGNORECASE),
    re.compile(r"(?:^|[\\/\s\"'=])raw[\\/]_depot_ui[\\/]", re.IGNORECASE),
]


def _with_token(path: str, token: str) -> str:
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}token={token}"


def _html_hrefs(html: str) -> list[str]:
    return re.findall(r"""href=["']([^"']+)["']""", html)


def _find_href_for_path(html: str, target_path: str) -> str:
    for href in _html_hrefs(html):
        decoded = unquote(href)
        if decoded.split("#", 1)[0].startswith(target_path):
            return decoded
    raise AssertionError(f"Missing href to {target_path!r}")


class ExpandedUiSmokeRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

        private_files = [
            (self.instance_root / "raw" / "ui_route_raw_leak.txt", "UI_ROUTE_RAW_LEAK"),
            (self.instance_root / "restricted" / "ui_route_restricted_leak.txt", "UI_ROUTE_RESTRICTED_LEAK"),
            (self.instance_root / "logs" / "ui_route_log_leak.log", "UI_ROUTE_LOG_LEAK"),
            (self.instance_root / "private" / "ui_route_private_leak.txt", "UI_ROUTE_PRIVATE_LEAK"),
        ]
        for path, marker in private_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(marker, encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self, access_token: str | None = None):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional UI dependency
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        return TestClient(create_app(self.instance, 2025, access_token=access_token))

    def _assert_no_private_route_leak(self, text: str, path: str) -> None:
        for marker in PRIVATE_ROUTE_LEAK_MARKERS:
            self.assertNotIn(marker, text, path)
        for pattern in PRIVATE_PATH_PATTERNS:
            self.assertIsNone(pattern.search(text), f"{path} leaks private path pattern {pattern.pattern!r}")

    def test_primary_ui_routes_render_from_synthetic_instance_without_configured_token(self) -> None:
        client = self._client()

        for path, expected_token in PRIMARY_UI_ROUTES:
            with self.subTest(path=path):
                response = client.get(path)
                text = unescape(response.text)

                self.assertEqual(response.status_code, 200)
                self.assertIn(expected_token, text)
                self._assert_no_private_route_leak(text, path)

    def test_primary_ui_routes_are_guarded_and_render_with_local_token(self) -> None:
        client = self._client(access_token="local-secret")

        for path, expected_token in PRIMARY_UI_ROUTES:
            with self.subTest(path=path, mode="without-token"):
                response = client.get(path)
                self.assertEqual(response.status_code, 403)
                self.assertIn("Jeton local requis.", response.text)
                self.assertNotIn(expected_token, response.text)

        for path, expected_token in PRIMARY_UI_ROUTES:
            with self.subTest(path=path, mode="query-token"):
                response = client.get(_with_token(path, "local-secret"))
                text = unescape(response.text)

                self.assertEqual(response.status_code, 200)
                self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
                self.assertIn(expected_token, text)
                self._assert_no_private_route_leak(text, path)

        fresh_client = self._client(access_token="local-secret")
        header_response = fresh_client.get("/pilotage", headers={"x-coproscope-token": "local-secret"})
        self.assertEqual(header_response.status_code, 200)
        self.assertIn("Pilotage des indicateurs", unescape(header_response.text))

        cookie_client = self._client(access_token="local-secret")
        first_response = cookie_client.get("/?token=local-secret")
        self.assertEqual(first_response.status_code, 200)
        follow_up = cookie_client.get("/gouvernance")
        self.assertEqual(follow_up.status_code, 200)
        self.assertIn("Tableau de controle local", unescape(follow_up.text))

    def test_cycle_n_routes_are_real_guarded_and_novice_readable(self) -> None:
        client = self._client(access_token="local-secret")

        for path, expected_tokens in CYCLE_N_ROUTES:
            with self.subTest(path=path, mode="without-token"):
                blocked = self._client(access_token="local-secret").get(path)
                self.assertEqual(blocked.status_code, 403)
                self.assertIn("Jeton local requis.", blocked.text)

            with self.subTest(path=path, mode="with-token"):
                response = client.get(_with_token(path, "local-secret"))
                text = unescape(response.text)

                self.assertEqual(response.status_code, 200)
                for expected in expected_tokens:
                    self.assertIn(expected, text)
                self.assertNotIn("P1 Prioritaire", text)
                self.assertNotIn("P2 Prioritaire", text)
                self.assertNotIn("Envoyer automatiquement", text)
                self._assert_no_private_route_leak(text, path)

    def test_cockpit_counter_links_keep_token_and_open_useful_screens(self) -> None:
        token = "local-secret"
        response = self._client(access_token=token).get(_with_token("/", token))
        self.assertEqual(response.status_code, 200)
        text = unescape(response.text)

        for target_path, useful_label in COCKPIT_COUNTER_TARGETS:
            with self.subTest(target=target_path):
                href = _find_href_for_path(text, target_path)
                self.assertIn(f"token={token}", href)

                follow_client = self._client(access_token=token)
                follow_up = follow_client.get(href)
                self.assertEqual(follow_up.status_code, 200, href)
                self.assertIn(useful_label, unescape(follow_up.text))
                self._assert_no_private_route_leak(unescape(follow_up.text), href)

    def test_passation_exports_are_guarded_derived_and_do_not_leak_private_roots(self) -> None:
        token = "local-secret"
        client = self._client(access_token=token)

        for path in ["/exports/passation.json", "/exports/passation.txt"]:
            with self.subTest(path=path, mode="without-token"):
                self.assertEqual(client.get(path).status_code, 403)

        json_response = client.get(_with_token("/exports/passation.json", token))
        text_response = client.get(_with_token("/exports/passation.txt", token))

        self.assertEqual(json_response.status_code, 200)
        self.assertEqual(text_response.status_code, 200)
        self.assertIn(PASSATION_EXPORT_WATERMARK, text_response.text)
        payload = json_response.json()
        self.assertFalse(payload["source_of_truth"])
        self.assertEqual(payload["watermark"], PASSATION_EXPORT_WATERMARK)

        combined = f"{json_response.text}\n{text_response.text}"
        self._assert_no_private_route_leak(combined, "/exports/passation.*")


if __name__ == "__main__":
    unittest.main()
