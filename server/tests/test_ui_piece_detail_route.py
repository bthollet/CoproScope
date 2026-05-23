from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance
from coproscope.web.app import create_app
from coproscope.web.piece_detail_view import MASKED_REFERENCE, build_piece_detail, public_piece_id
from coproscope.web.viewmodel import build_dashboard_model


FORBIDDEN_MARKERS = (
    "C:\\Users",
    "G:\\",
    "/Users",
    "/home",
    "file://",
    "raw/",
    "raw\\",
    "restricted/",
    "restricted\\",
    "logs/",
    "logs\\",
    "private/",
    "private\\",
)
TAG_RE = re.compile(r"<[^>]+>")
MAIN_RE = re.compile(r"<main\b[^>]*id=[\"']contenu[\"'][^>]*>(?P<body>[\s\S]*?)</main>", re.IGNORECASE)


def _visible_text(html: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", html)).strip()


def _main_text(html: str) -> str:
    match = MAIN_RE.search(html)
    if not match:
        raise AssertionError("Missing main#contenu")
    return _visible_text(match.group("body"))


class PieceDetailRouteTests(unittest.TestCase):
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

    def _piece_id(self, bucket: str = "missing") -> str:
        pieces = build_dashboard_model(self.instance, 2025)["ux"]["pieces"]
        rows = pieces[bucket]
        self.assertTrue(rows)
        return str(rows[0]["id"])

    def assertNoPrivateLeak(self, body: str) -> None:
        self.assertNotIn(str(self.instance_root), body)
        for marker in FORBIDDEN_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, body)

    def test_piece_detail_route_explains_why_proof_context_and_next_action(self) -> None:
        piece_id = self._piece_id("missing")

        response = self._client(access_token="local-secret").get(f"/pieces/{piece_id}?token=local-secret")
        body = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Detail piece/preuve", body)
        self.assertIn("Pourquoi cette piece compte", body)
        self.assertIn("Preuve attendue", body)
        self.assertIn("Qui doit l'avoir", body)
        self.assertIn("Piece candidate et preuve finale", body)
        self.assertIn("Preuve finale manquante", body)
        self.assertIn("Diffusion", body)
        self.assertIn("Relancer syndic", body)
        self.assertIn("Ajouter reponse recue", body)
        self.assertIn('aria-label="Actions principales piece/preuve"', body)
        first_viewport = _main_text(body)[:1800]
        self.assertIn("Piece concernee", first_viewport)
        self.assertIn("Pourquoi", first_viewport)
        self.assertIn("Action suivante", first_viewport)
        self.assertIn("Prudence diffusion", first_viewport)
        self.assertNotIn("Donnees fictives", first_viewport)
        self.assertIn("Voir le point lie", body)
        self.assertIn("Aucun envoi automatique", body)
        self.assertNoPrivateLeak(body)

    def test_piece_detail_distinguishes_candidate_from_final_proof(self) -> None:
        piece_id = self._piece_id("to_verify")

        detail = build_piece_detail(self.instance, 2025, piece_id)

        self.assertEqual(detail["state"], "found")
        self.assertEqual(detail["proof"]["state_label"], "Piece recue a verifier")
        self.assertGreaterEqual(detail["proof"]["candidate_count"], 1)
        self.assertIn("Preuve finale validee seulement apres controle explicite", detail["proof"]["states"])

    def test_piece_detail_tokenizes_local_ctas_without_double_token(self) -> None:
        piece_id = self._piece_id("missing")

        response = self._client(access_token="local-secret").get(f"/pieces/{piece_id}?token=local-secret")
        body = response.text

        self.assertEqual(response.status_code, 200)
        self.assertIn('href="/pieces?proof=missing&amp;token=local-secret"', body)
        self.assertIn("/demandes/relance?", body)
        relance_hrefs = re.findall(r'href="([^"]*/demandes/relance[^"]*)"', body)
        self.assertTrue(
            any(
                f"piece_detail={piece_id}" in unescape(href)
                and "token=local-secret" in unescape(href)
                for href in relance_hrefs
            ),
            relance_hrefs,
        )
        self.assertIn("/depot?", body)
        self.assertIn("token=local-secret", body)
        self.assertNotIn("token=local-secret&amp;token=local-secret", body)
        self.assertNotIn("token=local-secret&token=local-secret", body)

    def test_piece_detail_route_reuses_dashboard_model_for_detail_and_page(self) -> None:
        piece_id = self._piece_id("missing")
        client = self._client(access_token="local-secret")

        from coproscope.web import app as web_app

        calls: list[str] = []
        real_build = web_app.build_dashboard_model

        def counted_build(instance, year=2025):  # type: ignore[no-untyped-def]
            calls.append(instance.instance_id)
            return real_build(instance, year)

        with patch("coproscope.web.app.build_dashboard_model", side_effect=counted_build), patch(
            "coproscope.web.piece_detail_view.build_dashboard_model",
            side_effect=AssertionError("piece detail should reuse the route dashboard model"),
        ):
            response = client.get(f"/pieces/{piece_id}?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(calls), 1)

    def test_piece_detail_received_ctas_include_piece_detail_context(self) -> None:
        piece_id = self._piece_id("missing")

        response = self._client(access_token="local-secret").get(f"/pieces/{piece_id}?token=local-secret")
        body = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Ajouter reponse recue", body)
        self.assertIn(f"piece_detail={piece_id}", body)
        self.assertIn("status=reponse-recue", body)
        self.assertIn("return=pieces", body)
        self.assertIn("/demandes/relance?", body)

    def test_missing_pieces_list_links_to_piece_detail_route(self) -> None:
        piece_id = self._piece_id("missing")

        response = self._client(access_token="local-secret").get("/pieces?proof=missing&token=local-secret")
        body = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Detail piece/preuve", body)
        self.assertIn(f'href="/pieces/{piece_id}?token=local-secret"', body)

    def test_piece_detail_unknown_or_private_like_id_returns_safe_empty_state(self) -> None:
        client = self._client(access_token="local-secret")

        unknown = client.get("/pieces/PIECE-INCONNUE?token=local-secret")
        unsafe = client.get("/pieces/C:%5CUsers%5CExampleUser%5Craw%5Csecret.txt?token=local-secret")
        unsafe_body = unescape(unsafe.text)

        self.assertEqual(unknown.status_code, 200)
        self.assertIn("Piece introuvable", unescape(unknown.text))
        self.assertEqual(unsafe.status_code, 200)
        self.assertIn("Piece introuvable", unsafe_body)
        self.assertIn(MASKED_REFERENCE, unsafe_body)
        self.assertNotIn("fictif", unsafe_body.lower())
        self.assertNotIn("C:\\Users", unsafe_body)
        self.assertNotIn("secret.txt", unsafe_body)
        self.assertNoPrivateLeak(unsafe_body)

    def test_public_piece_id_masks_path_like_references(self) -> None:
        self.assertEqual(public_piece_id("UX-PIECE-COMP-C2B3F479"), "UX-PIECE-COMP-C2B3F479")
        self.assertEqual(public_piece_id("C:\\Users\\ExampleUser\\raw\\secret.txt"), MASKED_REFERENCE)
        self.assertEqual(public_piece_id("../raw/secret.txt"), MASKED_REFERENCE)


if __name__ == "__main__":
    unittest.main()
