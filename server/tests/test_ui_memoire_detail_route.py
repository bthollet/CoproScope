from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlparse

from coproscope.core.common import load_instance
from coproscope.web.app import create_app


DEMO_EVENT_ID = "EVT-FICTIF-C31-INFILT-ASSURANCE"


def _html_hrefs(html: str) -> list[str]:
    return re.findall(r"""href=["']([^"']+)["']""", unescape(html))


class UiMemoireDetailRouteTests(unittest.TestCase):
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

    def assertLocalHref(self, href: str) -> None:
        decoded = unquote(href)
        parsed = urlparse(decoded)
        if parsed.scheme or parsed.netloc:
            self.assertIn(parsed.netloc, {"testserver"})
            self.assertEqual(parsed.scheme, "http")
            self.assertTrue(parsed.path.startswith("/static/"))
            return
        self.assertTrue(decoded.startswith("/") or decoded.startswith("#"), href)
        self.assertFalse(decoded.startswith("//"), href)
        self.assertNotIn("://", decoded)
        self.assertNotIn("\\", decoded)

    def test_memory_event_detail_route_200(self) -> None:
        client = self._client(access_token="local-secret")

        response = client.get(f"/chantiers/{DEMO_EVENT_ID}?token=local-secret", follow_redirects=False)
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Detail evenement memoire", text)
        self.assertIn("Infiltration C31 - suivi assurance B12", text)
        self.assertIn('data-testid="memory-event-detail-shell"', response.text)

    def test_memory_event_detail_contains_required_private_fictive_labels(self) -> None:
        response = self._client(access_token="local-secret").get(f"/chantiers/{DEMO_EVENT_ID}?token=local-secret")
        text = unescape(response.text)

        for expected in [
            "infiltration C31",
            "assurance B12",
            "PV AG",
            "note syndic",
            "Relancer le syndic et demander le retour assureur",
            "Preuve finale manquante",
            "CS seulement en version interne",
            "Donnees FICTIVES de test",
        ]:
            self.assertIn(expected, text)

    def test_memory_event_detail_links_are_token_safe(self) -> None:
        client = self._client(access_token="local-secret")
        response = client.get(
            f"/chantiers/{DEMO_EVENT_ID}?token=local-secret&periode=10ans&categorie=sinistres"
        )
        hrefs = [unquote(href) for href in _html_hrefs(response.text)]

        self.assertIn("/chantiers?periode=10ans&categorie=sinistres&token=local-secret", hrefs)
        self.assertIn(
            f"/confidentialite?scope=event&selected={DEMO_EVENT_ID}&token=local-secret",
            hrefs,
        )
        self.assertIn(
            f"/exports/passation?scope=event&selected={DEMO_EVENT_ID}&token=local-secret",
            hrefs,
        )
        self.assertTrue(
            any(
                href.startswith("/demandes/relance?request_id=REQ-FICTIF-ASSURANCE-B12")
                and "action_id=ACTION-FICTIF-C31-ASSURANCE" in href
                and f"event_id={DEMO_EVENT_ID}" in href
                and "token=local-secret" in href
                for href in hrefs
            )
        )
        for href in hrefs:
            with self.subTest(href=href):
                self.assertLocalHref(href)

    def test_memory_event_detail_no_private_path_leak(self) -> None:
        response = self._client(access_token="local-secret").get(f"/chantiers/{DEMO_EVENT_ID}?token=local-secret")
        text = unescape(response.text)

        self.assertNotIn(str(self.instance_root), text)
        self.assertNotIn("C:\\Users", text)
        self.assertNotRegex(text, r"file://|raw[\\/]|restricted[\\/]|logs[\\/]")

    def test_memory_event_detail_export_is_derived_not_source_of_truth(self) -> None:
        response = self._client(access_token="local-secret").get(f"/chantiers/{DEMO_EVENT_ID}?token=local-secret")
        text = unescape(response.text)

        self.assertIn("export derive, non source de verite", text)
        self.assertIn("source_of_truth false", text)
        self.assertIn(
            f'href="/exports/passation?scope=event&amp;selected={DEMO_EVENT_ID}&amp;token=local-secret"',
            response.text,
        )

    def test_memory_event_detail_accessible_buttons(self) -> None:
        response = self._client(access_token="local-secret").get(f"/chantiers/{DEMO_EVENT_ID}?token=local-secret")
        text = unescape(response.text)

        for expected in [
            'aria-label="Retour a la memoire"',
            'aria-label="Preparer version diffusable"',
            'aria-label="Creer action de relance"',
            "Ajouter document",
            "Exporter cet evenement",
            "Demander assurance B12",
            "Verifier note syndic",
        ]:
            self.assertIn(expected, text)

    def test_memoire_timeline_links_to_real_detail_route_that_opens_selected_event(self) -> None:
        client = self._client(access_token="local-secret")

        index_response = client.get("/chantiers?token=local-secret")
        self.assertEqual(index_response.status_code, 200)
        match = re.search(r'href="/chantiers/([^"?]+)\?token=local-secret"', index_response.text)
        self.assertIsNotNone(match)
        event_id = unquote(match.group(1))

        detail_response = client.get(f"/chantiers/{event_id}?token=local-secret", follow_redirects=False)
        self.assertEqual(detail_response.status_code, 303)
        self.assertIn(f"/chantiers?selected={event_id}&token=local-secret", detail_response.headers["location"])

        selected_response = client.get(detail_response.headers["location"])
        text = unescape(selected_response.text)
        self.assertEqual(selected_response.status_code, 200)
        self.assertIn("Memoire de copropriete", text)
        self.assertIn("Pourquoi c'est garde", text)
        self.assertIn("Documents et preuves", text)
        self.assertNotIn("file://", text)
        self.assertNotIn("raw/", text)

    def test_unknown_memoire_detail_redirects_to_safe_missing_state(self) -> None:
        client = self._client(access_token="local-secret")

        detail_response = client.get("/chantiers/MEM-UNKNOWN-404?token=local-secret", follow_redirects=False)

        self.assertEqual(detail_response.status_code, 303)
        self.assertEqual(
            detail_response.headers["location"],
            "/chantiers?event_missing=MEM-UNKNOWN-404&token=local-secret",
        )

        missing_response = client.get(detail_response.headers["location"])
        text = unescape(missing_response.text)
        self.assertEqual(missing_response.status_code, 200)
        self.assertIn("Evenement introuvable", text)
        self.assertIn("La fiche memoire demandee n'est plus disponible avec ce lien.", text)
        self.assertIn('href="/chantiers?token=local-secret"', text)
        self.assertIn('href="/chantiers?statut=ouvert&token=local-secret"', text)

    def test_unknown_private_like_memoire_id_is_not_reflected(self) -> None:
        client = self._client(access_token="local-secret")

        detail_response = client.get(
            "/chantiers/C:%5CUsers%5CExampleUser%5Craw%5Cmemoire-privee.pdf?token=local-secret",
            follow_redirects=False,
        )

        self.assertEqual(detail_response.status_code, 303)
        location = detail_response.headers["location"]
        self.assertEqual(location, "/chantiers?event_missing=reference-locale-masquee&token=local-secret")
        self.assertNotIn("Users", location)
        self.assertNotIn("raw", location)
        self.assertNotIn("memoire-privee", location)


if __name__ == "__main__":
    unittest.main()
