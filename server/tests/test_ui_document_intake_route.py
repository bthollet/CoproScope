from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import DEFAULT_DOCUMENT_FIELDS, load_instance, read_csv, write_csv
from coproscope.web.app import TOKEN_COOKIE_NAME, create_app


class UiDocumentIntakeRouteTests(unittest.TestCase):
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
        return TestClient(create_app(self.instance, 2025, access_token=access_token, rebrancher=frozenset({"ajouter_document"})))

    def test_document_intake_route_renders_preparation_view_without_configured_token(self) -> None:
        response = self._client().get("/documents/ajouter")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Absorber des informations", response.text)
        self.assertIn("Sources d'absorption", response.text)
        self.assertIn("Sources d'information", response.text)
        self.assertIn("Regler plusieurs inbox", response.text)
        self.assertIn("Inbox du coffre", response.text)
        self.assertIn("Glisser-deposer", response.text)
        self.assertIn("Dossier local", response.text)
        self.assertIn("Drive Desktop", response.text)
        self.assertIn("Mailbox", response.text)
        self.assertIn("Aucun IMAP/OAuth actif", response.text)
        self.assertIn("Prequalification locale", response.text)
        self.assertIn("Ajouter des pieces au coffre local", response.text)
        self.assertIn("Documents a ajouter", response.text)
        self.assertIn("Fichier inbox", response.text)
        self.assertNotIn("PV assemblee generale 2025", response.text)
        self.assertNotIn("Devis travaux a biffer", response.text)
        self.assertIn("A quoi va servir la piece", response.text)
        self.assertIn("piece -&gt; point -&gt; action -&gt; preuve", response.text)
        # Ecran debranche (RM-2026-0183): plus d'entree dans la navigation.
        self.assertNotIn(
            'aria-label="Ajouter un document dans le coffre local"',
            response.text,
        )
        self.assertIn("Deposer un document depuis ce poste", response.text)
        self.assertIn("Glissez vos fichiers ici", response.text)
        self.assertIn("Etapes de traitement des pieces", response.text)
        self.assertIn("Sans IA/cloud", response.text)
        self.assertIn("Texte reconnu", response.text)
        self.assertIn("Traitement renforce", response.text)
        self.assertIn("Corriger une file de documents", response.text)
        self.assertIn('action="/depot"', response.text)
        self.assertIn('method="post"', response.text.lower())
        self.assertIn('type="file"', response.text.lower())
        self.assertIn('name="return" value="document_intake"', response.text)
        self.assertIn('name="source" value="drag_drop"', response.text)
        self.assertIn('required aria-describedby="document-intake-upload-help"', response.text)
        # Depot global de la coque retire (RM-2026-0183): le formulaire de la page reste.
        self.assertNotIn('href="/depot?intent=document"', response.text)
        self.assertNotIn('id="cs-global-drop-form"', response.text)

    def test_document_intake_route_uses_existing_token_guard_and_nav_token(self) -> None:
        client = self._client(access_token="local-secret")

        forbidden = client.get("/documents/ajouter")
        self.assertEqual(forbidden.status_code, 403)
        self.assertNotIn("Documents a ajouter", forbidden.text)

        response = client.get("/documents/ajouter?token=local-secret")

        self.assertEqual(response.status_code, 200)
        self.assertIn(TOKEN_COOKIE_NAME, response.cookies)
        self.assertIn("Sources d'absorption", response.text)
        self.assertIn("Ajouter des pieces au coffre local", response.text)
        self.assertIn("Documents a ajouter", response.text)
        self.assertIn('href="/documents/ajouter?token=local-secret"', response.text)
        self.assertIn('action="/depot?token=local-secret"', response.text)
        # Le depot global de la coque et l'entree de menu sont retires (RM-2026-0183).
        self.assertNotIn('id="cs-global-drop-form"', response.text)
        self.assertNotIn('href="/depot?intent=document', response.text)

        fresh_client = self._client(access_token="local-secret")
        header_response = fresh_client.get(
            "/documents/ajouter",
            headers={"x-coproscope-token": "local-secret"},
        )
        self.assertEqual(header_response.status_code, 200)
        self.assertIn("Documents a ajouter", header_response.text)

    def test_document_intake_upload_returns_to_intake_with_uploaded_files(self) -> None:
        client = self._client(access_token="local-secret")

        response = client.post(
            "/depot?token=local-secret",
            data={"intent": "document", "return": "document_intake", "source": "document_intake"},
            files=[("files", ("convocation_test.pdf", b"%PDF-1.4\n% test\n", "application/pdf"))],
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        location = response.headers["location"]
        self.assertIn("/documents/ajouter?", location)
        self.assertIn("depot=DEPOT-", location)
        self.assertIn("status=uploaded", location)
        self.assertIn("token=local-secret", location)

        upload_only_location = f"{location}&source=drag_drop"
        page = client.get(upload_only_location)
        self.assertEqual(page.status_code, 200)
        self.assertIn("Fichier 1", page.text)
        self.assertIn("Toutes les sources", page.text)
        self.assertIn("Glisser-deposer", page.text)
        self.assertIn("Proposition locale", page.text)
        self.assertIn('name="source" value="drag_drop"', page.text)
        self.assertIn("je ne sais pas encore", page.text.lower())
        self.assertIn("a decider avant partage", page.text.lower())
        self.assertIn("OCR / texte local", page.text)
        self.assertIn("Traitement renforce", page.text)
        self.assertIn("Corriger une file de documents", page.text)
        self.assertIn("Ouvrir le tri de lot", page.text)
        self.assertIn('href="/documents/tri-feedback?token=local-secret"', page.text)
        self.assertIn("DocOps propose, vous confirmez.", page.text)
        self.assertIn("A masquer demande des pages ou plages.", page.text)
        self.assertIn('name="document_type"', page.text)
        self.assertIn('value="A_CLASSER"', page.text)
        self.assertIn('name="privacy_status"', page.text)
        self.assertIn('value="A_ARBITRER" selected', page.text)
        self.assertIn("Diffusion bloquee", page.text)
        self.assertIn('action="/documents/ajouter/qualifier?token=local-secret"', page.text)
        self.assertIn('method="post"', page.text.lower())
        # `RM-2026-0056`: cette assertion disait 50 pour cent, et ce chiffre
        # etait le defaut lui-meme. Le PDF depose ici ne porte aucun texte
        # extractible - le registre ecrit `status_ocr = EXTRACTION_ERROR` et
        # `classification_status = TEXTE_INSUFFISANT`. Le classement disait donc
        # "je ne sais pas", tout en proposant `Convocation_AG` d'apres le seul
        # nom du fichier. Ce statut etant inconnu du vocabulaire de la boite de
        # reception, il etait rabattu sur `PENDING`, puis promu en `PROPOSED`
        # parce qu'un type etait present: l'etape de classification ressortait
        # cochee OK, et la piece illisible s'affichait a moitie qualifiee.
        # 25 pour cent est le chiffre juste: seul le depot local est acquis.
        self.assertRegex(page.text, r"Qualification 25 pour cent")
        self.assertIn("rien de lisible dans la piece", page.text)
        self.assertIn("Aucun texte exploitable", page.text)
        self.assertIn("Verifier l&#39;exemplaire ou relancer l&#39;OCR.", page.text)
        self.assertIn("Texte reconnu", page.text)
        self.assertIn("empreinte", page.text.lower())
        # `RM-2026-0126`: la piece qu'on vient de deposer se confirme par son
        # nom dans l'accuse de depot, et seulement la. La table des documents
        # continue d'appeler cette meme piece `Fichier 1`, assertion gardee
        # ligne 126.
        self.assertIn("convocation_test.pdf", page.text, "l'accuse de depot ne confirme pas la piece envoyee")
        self.assertNotRegex(page.text.lower(), r"raw[\\/]|c:\\\\|file://")
        for forbidden in ("docai", "openai", "chatgpt", "dropbox", "sharepoint", "ocr cloud", "classification ia", "analyse ia"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, page.text.lower())
        match = re.search(r"DOC-[A-F0-9]{12}", page.text)
        self.assertIsNotNone(match)

        deposit_id = location.split("depot=", 1)[1].split("&", 1)[0]
        reviewed_response = client.post(
            "/documents/ajouter/qualifier?token=local-secret",
            data={
                "depot": deposit_id,
                "status": "uploaded",
                "source": "drag_drop",
                "doc_id": match.group(0),
                "document_type": "AG",
                "privacy_status": "RESERVE_CS",
            },
            follow_redirects=False,
        )
        self.assertEqual(reviewed_response.status_code, 303)
        reviewed = client.get(reviewed_response.headers["location"])
        self.assertEqual(reviewed.status_code, 200)
        self.assertRegex(reviewed.text, r"Qualification 75 pour cent")
        self.assertIn('value="AG" selected', reviewed.text)
        self.assertIn('value="RESERVE_CS" selected', reviewed.text)
        self.assertIn("Reserve au conseil syndical", reviewed.text)
        self.assertNotIn("convocation_test.pdf", reviewed.text)
        self.assertNotRegex(reviewed.text.lower(), r"raw[\\/]|c:\\\\|file://")

    def test_document_intake_all_sources_combines_upload_and_inbox_without_paths(self) -> None:
        row = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        row.update(
            {
                "doc_id": "DOC-INBOX-ALL",
                "sha256": "c" * 64,
                "original_path": r"200_INBOX\piece_cachee.pdf",
                "file_name": "piece_cachee.pdf",
                "extension": "pdf",
                "size_bytes": "1024",
                "source_zone": "200_INBOX",
                "source_kind": "physical_deposit",
                "document_type": "A_CLASSER",
                "classification_status": "A_CLASSER",
                "privacy_review_status": "A_ARBITRER",
            }
        )
        client = self._client()

        response = client.post(
            "/depot",
            data={"intent": "document", "return": "document_intake", "source": "drag_drop"},
            files=[("files", ("reponse_syndic.pdf", b"%PDF-1.4\n% test\n", "application/pdf"))],
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        write_csv(self.instance.register("documents"), DEFAULT_DOCUMENT_FIELDS, [row])
        page = client.get(response.headers["location"])
        self.assertEqual(page.status_code, 200)
        self.assertIn("Toutes les sources", page.text)
        self.assertIn("Fichier 1", page.text)
        self.assertIn("Fichier inbox 1", page.text)
        self.assertIn("DOC-INBOX-ALL", page.text)
        self.assertIn("Inbox du coffre", page.text)
        self.assertIn("Glisser-deposer", page.text)
        self.assertNotIn("inbox-reconstruction:", page.text)
        self.assertNotIn("piece_cachee.pdf", page.text)
        # `RM-2026-0126`, arbitrage de Brice du 2026-09-08: « Un accuse de
        # depot montre le nom au deposant seul, juste apres le depot et nulle
        # part ailleurs. » `reponse_syndic.pdf` est le fichier que CE test
        # vient de deposer, et l'URL lue porte son `depot=`: son nom doit donc
        # apparaitre, une fois, dans l'accuse.
        #
        # La discrimination que ce test protege reste entiere, et c'est elle
        # qui compte: `piece_cachee.pdf`, deja presente dans l'inbox et non
        # deposee ici, reste invisible juste au-dessus. L'accuse montre ce que
        # vous venez d'envoyer, jamais ce qui etait deja la.
        self.assertIn("reponse_syndic.pdf", page.text, "l'accuse de depot ne confirme pas la piece envoyee")
        self.assertNotIn("200_INBOX", page.text)
        self.assertNotRegex(page.text.lower(), r"raw[\\/]|c:\\\\|file://")

    def test_document_intake_can_surface_inbox_registry_without_private_paths(self) -> None:
        row = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        row.update(
            {
                "doc_id": "DOC-INBOX-001",
                "sha256": "a" * 64,
                "original_path": r"200_INBOX\mandat_secret.pdf",
                "file_name": "mandat_secret.pdf",
                "extension": "pdf",
                "size_bytes": "4096",
                "source_zone": "200_INBOX",
                "source_kind": "copie_primaire",
                "document_type": "A_CLASSER",
                "classification_status": "A_CLASSER",
                "privacy_review_status": "A_ARBITRER",
            }
        )
        write_csv(self.instance.register("documents"), DEFAULT_DOCUMENT_FIELDS, [row])

        page = self._client().get("/documents/ajouter?source=inbox")

        self.assertEqual(page.status_code, 200)
        self.assertIn("Inbox du coffre", page.text)
        self.assertIn("Toutes les sources", page.text)
        self.assertIn('href="/documents/ajouter"', page.text)
        self.assertIn('href="/documents/ajouter?source=drag_drop"', page.text)
        self.assertIn("Progression de qualification", page.text)
        self.assertIn("Etapes de traitement des pieces", page.text)
        self.assertIn("Corriger une file de documents", page.text)
        self.assertIn('href="/documents/tri-feedback"', page.text)
        self.assertIn("Fichier inbox 1", page.text)
        self.assertIn('name="source" value="inbox"', page.text)
        self.assertIn("DOC-INBOX-001", page.text)
        self.assertIn("Reference locale masquee", page.text)
        self.assertNotIn("inbox-reconstruction:DOC-INBOX-001", page.text)
        self.assertIn("je ne sais pas encore", page.text.lower())
        self.assertIn("a decider avant partage", page.text.lower())
        self.assertIn('value="A_CLASSER" selected', page.text)
        self.assertIn('value="A_ARBITRER" selected', page.text)
        self.assertRegex(page.text, r"Qualification 25 pour cent")
        self.assertNotIn("mandat_secret.pdf", page.text)
        self.assertNotIn("200_INBOX", page.text)
        self.assertNotRegex(page.text.lower(), r"raw[\\/]|c:\\\\|file://")

        client = self._client()
        reviewed_response = client.post(
            "/documents/ajouter/qualifier",
            data={
                "source": "inbox",
                "doc_id": "DOC-INBOX-001",
                "document_type": "FACTURE_COMPTE",
                "privacy_status": "A_BIFFER",
            },
            follow_redirects=False,
        )
        self.assertEqual(reviewed_response.status_code, 303)
        reviewed = client.get(reviewed_response.headers["location"])
        self.assertEqual(reviewed.status_code, 200)
        self.assertRegex(reviewed.text, r"Qualification 75 pour cent")
        self.assertIn('value="FACTURE_COMPTE" selected', reviewed.text)
        self.assertIn('value="A_BIFFER" selected', reviewed.text)
        self.assertIn("Nommer une version masquee avant diffusion", reviewed.text)
        self.assertIn("Traitement renforce", reviewed.text)
        self.assertIn('action="/documents/ajouter/rattacher"', reviewed.text)
        self.assertIn('name="point_label"', reviewed.text)
        linked_response = client.post(
            "/documents/ajouter/rattacher",
            data={
                "source": "inbox",
                "doc_id": "DOC-INBOX-001",
                "point_kind": "ag",
                "point_label": "AG 2025 resolution travaux",
                "action_kind": "verifier",
                "action_label": "verifier le montant vote",
                "proof_intent": "decision",
                "proof_label": "decision et facture retrouvees",
            },
            follow_redirects=False,
        )
        self.assertEqual(linked_response.status_code, 303)
        linked = client.get(linked_response.headers["location"])
        self.assertEqual(linked.status_code, 200)
        self.assertRegex(linked.text, r"Qualification 100 pour cent")
        self.assertIn("AG 2025 resolution travaux", linked.text)
        self.assertIn("verifier le montant vote", linked.text)
        self.assertIn("decision et facture retrouvees", linked.text)
        self.assertNotIn("mandat_secret.pdf", linked.text)
        self.assertNotIn("200_INBOX", linked.text)
        self.assertNotRegex(linked.text.lower(), r"raw[\\/]|c:\\\\|file://")
        self.assertNotIn("mandat_secret.pdf", reviewed.text)
        self.assertNotIn("200_INBOX", reviewed.text)
        self.assertNotRegex(reviewed.text.lower(), r"raw[\\/]|c:\\\\|file://")
        _, rows = read_csv(self.instance.register("documents"))
        self.assertEqual(rows[0]["document_type"], "FACTURE_COMPTE")
        self.assertEqual(rows[0]["classification_status"], "PROPOSED")
        self.assertEqual(rows[0]["privacy_review_status"], "A_BIFFER")
        self.assertEqual(rows[0]["point_kind"], "ag")
        self.assertEqual(rows[0]["point_label"], "AG 2025 resolution travaux")
        self.assertEqual(rows[0]["action_kind"], "verifier")
        self.assertEqual(rows[0]["action_label"], "verifier le montant vote")
        self.assertEqual(rows[0]["proof_intent"], "decision")
        self.assertEqual(rows[0]["proof_label"], "decision et facture retrouvees")

    def test_document_intake_surfaces_auto_classified_rows_that_still_need_review(self) -> None:
        rows = []
        review_ocr = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        review_ocr.update(
            {
                "doc_id": "DOC-INBOX-OCR",
                "sha256": "d" * 64,
                "original_path": r"200_INBOX\facture_cachee.pdf",
                "file_name": "facture_cachee.pdf",
                "extension": "pdf",
                "size_bytes": "4096",
                "source_zone": "200_INBOX",
                "source_kind": "copie_primaire",
                "document_type": "Facture",
                "classification_status": "AUTO_CLASSIFIED",
                "status_ocr": "OCR_REQUIRED",
                "privacy_review_status": "AUTO_POLICY",
                "publication_form": "raw",
            }
        )
        review_privacy = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        review_privacy.update(
            {
                "doc_id": "DOC-INBOX-PRIV",
                "sha256": "e" * 64,
                "original_path": r"200_INBOX\contrat_cache.pdf",
                "file_name": "contrat_cache.pdf",
                "extension": "pdf",
                "size_bytes": "2048",
                "source_zone": "200_INBOX",
                "source_kind": "copie_primaire",
                "document_type": "Contrat_Syndic",
                "classification_status": "AUTO_CLASSIFIED",
                "status_ocr": "TEXT_EXTRACTED",
                "text_char_count": "1200",
                "text_path": r"staging\text\DOC-INBOX-PRIV.native.txt",
                "privacy_review_status": "A_REVOIR",
                "publication_form": "redaction_required",
            }
        )
        already_safe = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        already_safe.update(
            {
                "doc_id": "DOC-INBOX-SAFE",
                "sha256": "f" * 64,
                "original_path": r"200_INBOX\piece_deja_ok.pdf",
                "file_name": "piece_deja_ok.pdf",
                "extension": "pdf",
                "size_bytes": "1024",
                "source_zone": "200_INBOX",
                "source_kind": "copie_primaire",
                "document_type": "Facture",
                "classification_status": "AUTO_CLASSIFIED",
                "status_ocr": "TEXT_EXTRACTED",
                "text_char_count": "900",
                "privacy_review_status": "AUTO_POLICY",
                "publication_form": "raw",
            }
        )
        rows.extend([review_ocr, review_privacy, already_safe])
        write_csv(self.instance.register("documents"), DEFAULT_DOCUMENT_FIELDS, rows)

        page = self._client().get("/documents/ajouter?source=inbox")

        self.assertEqual(page.status_code, 200)
        self.assertIn("DOC-INBOX-OCR", page.text)
        self.assertIn("DOC-INBOX-PRIV", page.text)
        self.assertNotIn("DOC-INBOX-SAFE", page.text)
        self.assertIn("OCR local requis", page.text)
        self.assertIn("Texte reconnu", page.text)
        self.assertIn("Facture", page.text)
        self.assertIn("Contrat_Syndic", page.text)
        self.assertNotIn("facture_cachee.pdf", page.text)
        self.assertNotIn("contrat_cache.pdf", page.text)
        self.assertNotIn("piece_deja_ok.pdf", page.text)
        self.assertNotIn("200_INBOX", page.text)
        self.assertNotRegex(page.text.lower(), r"raw[\\/]|c:\\\\|file://")

    def test_document_intake_ignores_private_or_unknown_choice_values(self) -> None:
        row = {field: "" for field in DEFAULT_DOCUMENT_FIELDS}
        row.update(
            {
                "doc_id": "DOC-INBOX-002",
                "sha256": "b" * 64,
                "original_path": r"200_INBOX\piece_privee.pdf",
                "file_name": "piece_privee.pdf",
                "extension": "pdf",
                "size_bytes": "2048",
                "document_type": "A_CLASSER",
                "classification_status": "A_CLASSER",
                "privacy_review_status": "A_ARBITRER",
            }
        )
        write_csv(self.instance.register("documents"), DEFAULT_DOCUMENT_FIELDS, [row])

        client = self._client()
        response = client.post(
            "/documents/ajouter/qualifier",
            data={
                "source": "inbox",
                "doc_id": "DOC-INBOX-002",
                "document_type": r"C:\Users\secret",
                "privacy_status": "file://raw",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        page = client.get(response.headers["location"])

        self.assertEqual(page.status_code, 200)
        self.assertIn('value="A_CLASSER" selected', page.text)
        self.assertIn('value="A_ARBITRER" selected', page.text)
        self.assertNotIn("piece_privee.pdf", page.text)
        self.assertNotIn("200_INBOX", page.text)
        self.assertNotIn("C:\\Users", page.text)
        self.assertNotIn("file://", page.text)

        link_response = client.post(
            "/documents/ajouter/rattacher",
            data={
                "source": "inbox",
                "doc_id": "DOC-INBOX-002",
                "point_kind": "ag",
                "point_label": r"C:\Users\secret\AG.pdf",
                "action_kind": "verifier",
                "action_label": "controler",
                "proof_intent": "decision",
                "proof_label": "preuve locale",
            },
            follow_redirects=False,
        )
        self.assertEqual(link_response.status_code, 422)
        _, rows = read_csv(self.instance.register("documents"))
        self.assertNotIn("point_label", rows[0])

    def test_document_intake_route_does_not_shadow_document_detail_route(self) -> None:
        response = self._client(access_token="local-secret").get("/documents/inconnu?token=local-secret")

        self.assertEqual(response.status_code, 404)
        self.assertIn("Document introuvable", response.text)


if __name__ == "__main__":
    unittest.main()
