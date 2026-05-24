from __future__ import annotations

import shutil
import tempfile
import unittest
import re
from csv import DictReader
from html import unescape
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from coproscope.core.common import load_instance
from coproscope.modules import requestops
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app
from coproscope.web.viewmodel import build_dashboard_model


class UiRequestsRouteTests(unittest.TestCase):
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

    def _piece_id(self) -> str:
        pieces = build_dashboard_model(self.instance, 2025)["ux"]["pieces"]
        self.assertTrue(pieces["missing"])
        return str(pieces["missing"][0]["id"])

    def test_requests_route_requires_token_and_renders_novice_view(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/demandes")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Boite de demandes a suivre", forbidden.text)

        response = client.get("/demandes?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn("Boite de demandes a suivre", response.text)
        self.assertIn("Demandes coproprietaires multi-canaux", response.text)
        self.assertIn('href="/demandes?token=local-secret"', response.text)
        self.assertIn("<span>Demandes syndic</span>", response.text)
        self.assertIn('aria-current="page"', response.text)
        self.assertIn("registre:", response.text)

        fresh_client = self._client(access_token="local-secret")
        header_response = fresh_client.get("/demandes", headers={"x-coproscope-token": "local-secret"})
        self.assertEqual(header_response.status_code, 200)
        self.assertIn("Boite de demandes a suivre", header_response.text)

    def test_requests_route_creates_local_demo_request_with_token(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.post("/demandes", data={"subject": "Relance fictive assurance"})
        self.assertEqual(forbidden.status_code, 403)

        response = client.post(
            "/demandes?token=local-secret",
            data={
                "subject": "Relance fictive assurance",
                "channel": "email",
                "source_ref": "DOC-FICTIF-B12-ASSUR",
                "visibility": "conseil_syndical",
                "next_action": "Preparer la relance et rattacher la reponse syndic.",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertIn("/demandes?status=created&", response.headers["location"])
        self.assertIn("token=local-secret", response.headers["location"])

        register = self.instance.register("requests").read_text(encoding="utf-8")
        rows = list(DictReader(StringIO(register)))
        created = [row for row in rows if row["subject"] == "Relance fictive assurance"]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0]["source_ref"], "DOC-FICTIF-B12-ASSUR")
        self.assertEqual(created[0]["status"], "a_qualifier")
        self.assertEqual(created[0]["visibility"], "conseil_syndical")

        page = client.get("/demandes?token=local-secret")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Relance fictive assurance", page.text)

    def test_requests_route_masks_private_paths_submitted_in_form(self) -> None:
        client = self._client(access_token="local-secret")

        response = client.post(
            "/demandes?token=local-secret",
            data={
                "subject": r"Verifier C:\Users\demo\raw\secret.txt",
                "channel": "email",
                "source_ref": r"G:\Mon Drive\copro\restricted\piece.pdf",
                "next_action": r"Ouvrir file://C:/Users/demo/logs/run.log",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        page = client.get("/demandes?token=local-secret")
        self.assertEqual(page.status_code, 200)
        self.assertIn("[reference locale masquee]", page.text)
        self.assertNotIn(r"C:\Users", page.text)
        self.assertNotIn(r"G:\Mon Drive", page.text)
        self.assertNotIn("file://", page.text)
        self.assertNotIn("secret.txt", page.text)

    def test_relance_syndic_route_is_real_tokenized_and_novice_actionable(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/demandes/relance")
        self.assertEqual(forbidden.status_code, 403)

        response = client.get("/demandes/relance?token=local-secret&request_id=REQ-FICTIF-ASSURANCE-B12")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Relancer le syndic", text)
        self.assertIn("Mode local: aucun message n'est envoye par CoproScope", text)
        self.assertIn("Attestation assurance 2026 non recue", text)
        self.assertIn("Brouillon a copier, non envoye", text)
        self.assertIn("Piece concernee", text)
        self.assertIn("A qui demander / qui doit l'avoir", text)
        self.assertIn("Noter l'envoi fait hors CoproScope", text)
        self.assertIn("Valider la relance", text)
        self.assertIn("Noter un envoi fait hors CoproScope", text)
        self.assertIn("Date d'envoi", text)
        self.assertIn("Canal", text)
        self.assertIn("Copier le message", text)
        self.assertIn('href="/demandes?token=local-secret"', response.text)
        self.assertIn('aria-label="Rattacher la reponse du syndic au depot local"', response.text)
        self.assertIn('href="/depot?intent=syndic-answer&amp;request_id=REQ-FICTIF-ASSURANCE-B12&amp;token=local-secret"', response.text)

        sent_without_post = client.get("/demandes/relance?token=local-secret&sent=1")
        self.assertEqual(sent_without_post.status_code, 200)
        self.assertNotIn("Relance enregistree localement", sent_without_post.text)

        validated = client.post(
            "/demandes/relance?token=local-secret",
            data={
                "request_id": "REQ-FICTIF-ASSURANCE-B12",
                "message": "Relance fictive",
                "sent_date": "2026-05-21",
                "sent_channel": "email",
                "sent_recipient": "Syndic de la copropriete (fictif)",
                "sent_note": "copie email fictive",
            },
            follow_redirects=False,
        )
        self.assertEqual(validated.status_code, 303)
        self.assertIn("/demandes/relance?request_id=REQ-FICTIF-ASSURANCE-B12&sent=1", validated.headers["location"])
        self.assertIn("sent_id=JRN-UI-RELANCE-", validated.headers["location"])
        actions = requestops.normalize_actions(
            list(DictReader(StringIO(requestops.request_action_log_path(self.instance).read_text(encoding="utf-8"))))
        )
        self.assertTrue(
            any(action.request_id == "REQ-FICTIF-ASSURANCE-B12" and action.action_type == "relance" for action in actions)
        )
        self.assertTrue(
            any(
                action.request_id == "REQ-FICTIF-ASSURANCE-B12"
                and "date 2026-05-21, canal email" in action.summary
                and "copie email fictive" in action.summary
                for action in actions
            )
        )

        sent = client.get(validated.headers["location"])
        self.assertEqual(sent.status_code, 200)
        self.assertIn("Relance enregistree localement", sent.text)
        self.assertIn("date 2026-05-21, canal email", sent.text)
        self.assertIn("copie email fictive", sent.text)

    def test_relance_syndic_empty_state_keeps_live_action_labels(self) -> None:
        self.instance.register("requests").write_text(",".join(requestops.REQUEST_FIELDS) + "\n", encoding="utf-8")
        requestops.request_action_log_path(self.instance).write_text(
            ",".join(requestops.ACTION_LOG_FIELDS) + "\n",
            encoding="utf-8",
        )
        client = self._client(access_token="local-secret")

        response = client.get("/demandes/relance?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Aucune relance syndic a preparer", text)
        self.assertIn("Noter l'envoi fait hors CoproScope", text)
        self.assertIn("Choisir ou creer une demande", text)
        self.assertIn("Rattacher la reponse du syndic", text)
        self.assertIn('aria-label="Rattacher la reponse du syndic au depot local"', text)
        self.assertIn("Selectionnez ou creez d'abord une demande", text)

    def test_relance_syndic_route_prefills_from_piece_detail_without_fake_send(self) -> None:
        piece_id = self._piece_id()
        client = self._client(access_token="local-secret")

        response = client.get(f"/demandes/relance?piece_detail={piece_id}&token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Relancer le syndic", text)
        self.assertIn("Brouillon a copier, non envoye", text)
        self.assertIn("Brouillon non envoye par CoproScope", text)
        self.assertIn("Justificatif comptable", text)
        self.assertIn("Piece concernee", text)
        self.assertIn("A qui demander / qui doit l'avoir", text)
        self.assertIn("Pourquoi", text)
        self.assertIn("Action suivante", text)
        self.assertIn("Prudence diffusion", text)
        self.assertIn("Piece ou preuve a demander", text)
        self.assertIn("Diffusion : verifier avant de joindre une piece", text)
        self.assertIn("Noter l'envoi hors CoproScope indisponible", text)
        self.assertIn("Indisponible tant qu'une demande syndic n'est pas rattachee.", text)
        self.assertIn("Rattacher la reponse du syndic", text)
        self.assertIn('aria-label="Rattacher la reponse du syndic au depot local"', text)
        self.assertIn(f"piece_detail={piece_id}", text)
        depot_hrefs = re.findall(r'href="([^"]*/depot[^"]*)"', text)
        self.assertTrue(
            any(
                f"piece_detail={piece_id}" in href
                and "status=reponse-recue" in href
                and "return=pieces" in href
                and "token=local-secret" in href
                for href in depot_hrefs
            ),
            depot_hrefs,
        )
        self.assertIn("Retour detail piece/preuve", text)
        self.assertNotIn("Enregistrer la relance fictive", text)
        self.assertNotIn("C:\\Users", text)
        self.assertNotIn("file://", text)
        self.assertNotIn("raw/", text)
        self.assertNotIn("restricted/", text)

    def test_relance_syndic_piece_detail_reuses_dashboard_model_for_context(self) -> None:
        piece_id = self._piece_id()
        client = self._client(access_token="local-secret")

        from coproscope.web import app as web_app

        calls: list[str] = []
        real_build = web_app.build_dashboard_model

        def counted_build(instance, year=2025):  # type: ignore[no-untyped-def]
            calls.append(instance.instance_id)
            return real_build(instance, year)

        with patch("coproscope.web.app.build_dashboard_model", side_effect=counted_build), patch(
            "coproscope.web.piece_detail_view.build_dashboard_model",
            side_effect=AssertionError("relance piece context should reuse the route dashboard model"),
        ):
            response = client.get(f"/demandes/relance?piece_detail={piece_id}&token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(calls), 1)

    def test_relance_syndic_piece_detail_renders_even_without_request_rows(self) -> None:
        piece_id = self._piece_id()
        self.instance.register("requests").write_text(",".join(requestops.REQUEST_FIELDS) + "\n", encoding="utf-8")
        client = self._client(access_token="local-secret")

        response = client.get(f"/demandes/relance?piece_detail={piece_id}&token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Relancer le syndic", text)
        self.assertIn("Justificatif comptable", text)
        self.assertIn("Rattacher la reponse du syndic", text)
        self.assertIn("Noter l'envoi hors CoproScope indisponible", text)
        self.assertIn("Indisponible tant qu'une demande syndic n'est pas rattachee.", text)
        self.assertIn(f"piece_detail={piece_id}", text)
        self.assertNotIn("Aucune relance syndic a preparer", text)

    def test_requests_and_plain_relance_skip_full_dashboard_model(self) -> None:
        from coproscope.web import app as web_app

        client = self._client(access_token="local-secret")

        with patch.object(web_app, "build_dashboard_model", side_effect=AssertionError("plain request pages need only shell model")):
            requests_response = client.get("/demandes?token=local-secret")
            relance_response = client.get("/demandes/relance?token=local-secret")

        self.assertEqual(requests_response.status_code, 200)
        self.assertEqual(relance_response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
