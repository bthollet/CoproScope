from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlparse

from coproscope.core.common import load_instance, write_csv
from coproscope.core.privacy import SCREENING_FIELDS
from coproscope.modules import decisionops, docuscope, incidentops

SCREENING_REVIEW_FIELDS = [
    *SCREENING_FIELDS,
    "privacy_review_status",
    "review_status_recommendation",
    "review_next_step",
    "review_justification_required",
    "privacy_review_justification",
    "privacy_review_owner",
    "privacy_reviewed_at",
    "publication_blocker",
]

PRIVATE_MEMOIRE_PATTERNS = [
    re.compile(r"raw[\\/]", re.IGNORECASE),
    re.compile(r"restricted[\\/]", re.IGNORECASE),
    re.compile(r"logs[\\/]", re.IGNORECASE),
    re.compile(r"private[\\/]", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
    re.compile(r"(?:^|[\\/\s\"'=])/(?:Users|home)[\\/]", re.IGNORECASE),
]

CHANTIERS_COUNTER_TARGETS = [
    ("/actions?scope=decisions", "Registre des decisions"),
    ("/actions?scope=documents", "Registre des decisions"),
    ("/actions?scope=incidents", "Registre des decisions"),
    ("/confidentialite", "Confidentialite et diffusion"),
]


def _html_hrefs(html: str) -> list[str]:
    return re.findall(r"""href=["']([^"']+)["']""", html)


def _with_token(path: str, token: str) -> str:
    separator = "&" if "?" in path else "?"
    return f"{path}{separator}token={token}"


def _find_href_for_path(html: str, target_path: str) -> str:
    for href in _html_hrefs(html):
        decoded = unquote(href)
        if decoded.split("#", 1)[0].startswith(target_path):
            return decoded
    raise AssertionError(f"Missing href to {target_path!r}")


class MemoireUiTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        self.source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(self.source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _seed_memoire_outputs(self) -> None:
        reports_dir = self.instance.artifact("reports_dir")
        write_csv(
            decisionops.decision_register_path(self.instance),
            decisionops.DECISION_ACTION_FIELDS,
            [
                {
                    "decision_action_id": "DAP-TOITURE",
                    "ag_id": "AG-2025",
                    "source_doc_id": "DOC-AG",
                    "source_file": "pv_ag_2025.txt",
                    "resolution_ref": "R12",
                    "decision_text": "Resolution toiture: devis accepte et calendrier a confirmer.",
                    "action_attendue": "Obtenir ordre de service, planning et preuve de reception.",
                    "responsable": "Commission travaux",
                    "echeance": "2025-09-30",
                    "preuve_attendue": "Ordre de service et PV de reception.",
                    "proof_doc_ids": "",
                    "proof_document_types": "",
                    "related_request_ids": "",
                    "related_invoice_refs": "",
                    "related_work_refs": "TRX-TOITURE",
                    "statut": "PREUVE_A_DEMANDER",
                    "priorite": "P1",
                    "notes": "",
                }
            ],
        )
        write_csv(
            incidentops.incident_register_path(self.instance),
            incidentops.INCIDENT_FIELDS,
            [
                {
                    "incident_id": "INC-INFILTRATION",
                    "date_signalement": "2025-07-04",
                    "lieu": "Local velo",
                    "description": "Infiltration persistante apres orage.",
                    "piece_ref": "mail_syndic.txt",
                    "doc_ids": "",
                    "photo_or_piece": "",
                    "syndic_or_provider": "Syndic",
                    "status": "EN_COURS",
                    "priority": "P1",
                    "next_action": "Relancer l'entreprise et dater la reprise.",
                    "action_due_date": "2025-07-12",
                    "expected_closure_proof": "Photo apres reprise et bon d'intervention.",
                    "closure_proof_ref": "",
                    "contract_or_insurance_ref": "Contrat entretien toiture",
                    "source_refs": "mail_syndic.txt",
                    "notes": "",
                }
            ],
        )
        write_csv(
            reports_dir / "matrice_completude_documentaire.csv",
            docuscope.COMPLETENESS_FIELDS,
            [
                {
                    "proof_id": "PRV-CONTRAT-SYNDIC",
                    "lot": "contrats",
                    "expected_label": "Contrat syndic signe",
                    "document_type": "Contrat_Syndic",
                    "status": "ABSENT",
                    "criticality": "P1",
                    "freshness_months": "",
                    "matched_doc_ids": "",
                    "evidence_paths": "",
                    "newest_date": "",
                    "reason": "Contrat necessaire pour reprendre les obligations.",
                    "action": "Demander la derniere version signee au syndic.",
                }
            ],
        )
        write_csv(
            reports_dir / "pieces_a_demander.csv",
            docuscope.DOCUMENT_REQUEST_FIELDS,
            [
                {
                    "request_id": "REQ-CONTRAT-SYNDIC",
                    "source_ref": "PRV-CONTRAT-SYNDIC",
                    "priority": "P1",
                    "status": "ABSENT",
                    "subject": "Contrat syndic signe",
                    "expected_piece": "Contrat syndic signe",
                    "reason": "Contrat necessaire pour reprendre les obligations.",
                    "related_doc_ids": "",
                    "evidence_paths": "",
                    "suggested_diligence": "Demander la derniere version signee au syndic.",
                }
            ],
        )
        write_csv(
            self.instance.root("staging") / "privacy_dir" / "registre_screening_confidentialite.csv",
            SCREENING_REVIEW_FIELDS,
            [
                {
                    "doc_id": "DOC-CONTENTIEUX",
                    "sha256": "abc",
                    "original_path": "outputs/reports/note_contentieux.md",
                    "file_name": "note_contentieux.md",
                    "extension": ".md",
                    "source_zone": "outputs",
                    "raw_max_college": "conseil_syndical",
                    "derivative_max_college": "conseil_syndical",
                    "publication_form": "synthese",
                    "required_transformations": "Biffage noms et lots.",
                    "restriction_reasons": "contentieux",
                    "personal_data_level": "direct",
                    "ip_status": "",
                    "ai_processing_ceiling": "local_only",
                    "review_required": "YES",
                    "policy_confidence": "high",
                    "screening_signals": "CONTENTIOUS",
                    "exposure_risk": "high",
                    "remediation_priority": "P1",
                    "recommended_action": "Limiter la diffusion au conseil syndical.",
                    "privacy_review_status": "A_ARBITRER",
                    "review_status_recommendation": "DIFFUSABLE_APRES_BIFFAGE",
                    "review_next_step": "Arbitrer le niveau de diffusion avant passation.",
                    "review_justification_required": "YES",
                    "privacy_review_justification": "",
                    "privacy_review_owner": "",
                    "privacy_reviewed_at": "",
                    "publication_blocker": "",
                }
            ],
        )

    def _create_app(self):
        try:
            from coproscope.web.app import create_app  # type: ignore
        except ImportError as exc:
            self.skipTest(f"UI dependencies unavailable: {exc}")
        return create_app

    def _client(self, *, access_token: str | None = None):
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError as exc:
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        return TestClient(self._create_app()(self.instance, 2025, access_token=access_token))

    def assertLocalHref(self, href: str, path: str) -> None:
        decoded = unquote(href)
        parsed = urlparse(decoded)
        if parsed.scheme or parsed.netloc:
            self.assertIn(parsed.netloc, {"testserver"}, f"{path} must not point outside TestClient: {href!r}")
            self.assertEqual(parsed.scheme, "http", f"{path} must use the TestClient static origin: {href!r}")
            self.assertTrue(parsed.path.startswith("/static/"), f"{path} external-looking href must be static: {href!r}")
            return
        self.assertTrue(decoded.startswith("/") or decoded.startswith("#"), f"{path} must be local: {href!r}")
        self.assertFalse(decoded.startswith("//"), f"{path} must not be protocol-relative: {href!r}")
        self.assertNotIn("://", decoded, f"{path} must not contain a URL scheme: {href!r}")
        self.assertNotIn("\\", decoded, f"{path} must not contain backslashes: {href!r}")

    def assertNoPrivateMemoireLeak(self, payload: str) -> None:
        for pattern in PRIVATE_MEMOIRE_PATTERNS:
            self.assertIsNone(pattern.search(payload), f"memoire route leaks {pattern.pattern!r}")

    def test_template_contains_memoire_passation_surface(self) -> None:
        template = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "coproscope"
            / "web"
            / "templates"
            / "workstreams.html"
        ).read_text(encoding="utf-8")

        for expected in [
            "Passation conseil syndical",
            "Sujets ouverts",
            "Decisions non cloturees",
            "Contrats et travaux",
            "Preuves essentielles",
            "Diffusion et restreint",
            "Prochaine passation",
        ]:
            self.assertIn(expected, template)

    def test_chantiers_renders_memoire_passation_sections(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        self._seed_memoire_outputs()
        create_app = self._create_app()
        client = TestClient(create_app(self.instance, 2025))
        response = client.get("/chantiers")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        for expected in [
            "Passation conseil syndical",
            "Sujets ouverts",
            "Decisions non cloturees",
            "Contrats et travaux",
            "Preuves essentielles",
            "Diffusion et restreint",
            "Prochaine passation",
            "Resolution toiture",
            "Contrat syndic signe",
            "Infiltration persistante",
            "note_contentieux.md",
            "A_ARBITRER",
        ]:
            self.assertIn(expected, text)

    def test_chantiers_is_token_gated_and_counter_links_keep_token(self) -> None:
        self._seed_memoire_outputs()
        token = "local-secret"

        blocked = self._client(access_token=token).get("/chantiers")
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("Jeton local requis.", blocked.text)

        response = self._client(access_token=token).get(_with_token("/chantiers", token))
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Passation conseil syndical", text)
        self.assertIn("Prochaine passation", text)
        self.assertNoPrivateMemoireLeak(text)
        for index, href in enumerate(_html_hrefs(text)):
            with self.subTest(href=href):
                self.assertLocalHref(href, f"html.href[{index}]")

        for target_path, useful_label in CHANTIERS_COUNTER_TARGETS:
            with self.subTest(target=target_path):
                href = _find_href_for_path(text, target_path)
                self.assertIn(f"token={token}", href)

                follow_up = self._client(access_token=token).get(href)
                self.assertEqual(follow_up.status_code, 200, href)
                self.assertIn(useful_label, unescape(follow_up.text))

    def test_chantiers_renders_for_empty_instance(self) -> None:
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI test client unavailable")

        empty_root = Path(self.tempdir.name) / "empty"
        for name in ["raw", "system", "outputs", "staging", "logs", "registers"]:
            (empty_root / name).mkdir(parents=True, exist_ok=True)
        (empty_root / "instance.yml").write_text(
            json.dumps(
                {
                    "version": 1,
                    "instance_id": "empty-copro",
                    "display_name": "Copropriete vide",
                    "roots": {
                        "workspace": ".",
                        "raw": "./raw",
                        "system": "./system",
                        "outputs": "./outputs",
                        "staging": "./staging",
                        "logs": "./logs",
                        "restricted": [],
                    },
                    "registers": {
                        "documents": "./registers/registre_documents.csv",
                        "requests": "./registers/registre_demandes.csv",
                        "ag": "./registers/registre_ag.csv",
                        "findings": "./registers/constats_diligences.csv",
                        "kpi": "./registers/kpi.csv",
                    },
                    "artifacts": {
                        "reports_dir": "./outputs/reports",
                        "accounting_dir": "./outputs/accounting",
                        "evidence_dir": "./outputs/evidence",
                    },
                }
            ),
            encoding="utf-8",
        )
        empty = load_instance(str(empty_root / "instance.yml"), None)
        create_app = self._create_app()
        client = TestClient(create_app(empty, 2025))
        response = client.get("/chantiers")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Passation conseil syndical", text)
        self.assertIn("Aucun sujet ouvert charge pour cette instance.", text)
        self.assertIn("Aucune decision non cloturee chargee.", text)
        self.assertIn("Aucune restriction de diffusion prioritaire chargee.", text)


if __name__ == "__main__":
    unittest.main()
