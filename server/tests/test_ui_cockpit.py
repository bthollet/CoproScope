from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import types
import unittest
import xml.etree.ElementTree as StdlibElementTree
from html import unescape
from importlib.util import find_spec
from pathlib import Path

from coproscope.core.common import load_instance, write_csv
from coproscope.modules import decisionops, docuscope, incidentops


PRIVATE_COCKPIT_PATTERNS = [
    re.compile(r"raw[\\/]", re.IGNORECASE),
    re.compile(r"restricted[\\/]", re.IGNORECASE),
    re.compile(r"logs[\\/]", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
    re.compile(r"\\\\"),
    re.compile(r"(?:^|[\\/\s\"'=])/(?:Users|home)[\\/]", re.IGNORECASE),
]

CYCLE1_ROUTE_LABELS = [
    "Cockpit Conseil Syndical",
    "Ce qui demande attention maintenant",
    "A traiter",
    "Pieces manquantes",
    "Demandes syndic",
    "Echeances AG",
    "Controle comptes",
    "Alertes et risques",
]


def _install_defusedxml_fallback() -> None:
    if "defusedxml" in sys.modules:
        return
    if find_spec("defusedxml") is None:
        defusedxml = types.ModuleType("defusedxml")
        defusedxml.ElementTree = StdlibElementTree
        sys.modules["defusedxml"] = defusedxml


def _load_ui_objects():
    _install_defusedxml_fallback()
    from coproscope.web.app import create_app
    from coproscope.web.viewmodel import build_dashboard_model

    return create_app, build_dashboard_model


def _public_strings(value: object, path: str = "$"):
    if isinstance(value, str):
        yield path, value
        return
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _public_strings(child, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _public_strings(child, f"{path}[{index}]")


def _hrefs(value: object, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            next_path = f"{path}.{key}"
            if key.endswith("href") and isinstance(child, str) and child:
                yield next_path, child
            yield from _hrefs(child, next_path)
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from _hrefs(child, f"{path}[{index}]")


class CockpitOverviewUiTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _render_overview_template(self, model: dict[str, object]) -> str:
        template_dir = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "templates"
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape  # type: ignore
        except ImportError:
            return "\n".join(
                [
                    (template_dir / "base.html").read_text(encoding="utf-8"),
                    (template_dir / "overview.html").read_text(encoding="utf-8"),
                ]
            )

        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(("html", "xml")),
        )
        env.globals["url_for"] = lambda name, **kwargs: f"/static/{kwargs.get('path', '')}"
        return env.get_template("overview.html").render(
            model=model,
            page="overview",
            ui_token_query="",
            ui_token_param="",
        )

    def _seed_cockpit_outputs(self) -> None:
        reports_dir = self.instance.artifact("reports_dir")
        write_csv(
            reports_dir / "matrice_completude_documentaire.csv",
            docuscope.COMPLETENESS_FIELDS,
            [
                {
                    "proof_id": "PRV-PV",
                    "lot": "ag",
                    "expected_label": "PV AG signe",
                    "document_type": "PV_AG",
                    "status": "PRESENT",
                    "criticality": "P1",
                    "freshness_months": "",
                    "matched_doc_ids": "DOC-AG",
                    "evidence_paths": "DOC-AG:pv_ag_2025.txt",
                    "newest_date": "2025-05-01",
                    "reason": "Piece presente.",
                    "action": "Rattacher au registre de decisions.",
                },
                {
                    "proof_id": "PRV-CONTRAT",
                    "lot": "contrats",
                    "expected_label": "Contrat syndic signe",
                    "document_type": "Contrat_Syndic",
                    "status": "ABSENT",
                    "criticality": "P1",
                    "freshness_months": "",
                    "matched_doc_ids": "",
                    "evidence_paths": "",
                    "newest_date": "",
                    "reason": "Aucune piece locale ne correspond au type attendu.",
                    "action": "Demander la piece au syndic.",
                },
            ],
        )
        write_csv(
            reports_dir / "pieces_a_demander.csv",
            docuscope.DOCUMENT_REQUEST_FIELDS,
            [
                {
                    "request_id": "REQ-DOC-PRV-CONTRAT",
                    "source_ref": "PRV-CONTRAT",
                    "priority": "P1",
                    "status": "ABSENT",
                    "subject": "Demander au syndic: Contrat syndic signe",
                    "expected_piece": "Contrat syndic signe",
                    "reason": "Aucune piece locale ne correspond au type attendu.",
                    "related_doc_ids": "",
                    "evidence_paths": "",
                    "suggested_diligence": "Demander la piece au syndic et rattacher sa reponse au registre.",
                }
            ],
        )
        write_csv(
            decisionops.decision_register_path(self.instance),
            decisionops.DECISION_ACTION_FIELDS,
            [
                {
                    "decision_action_id": "DAP-001",
                    "ag_id": "AG-2025",
                    "source_doc_id": "DOC-AG",
                    "source_file": "pv_ag_2025.txt",
                    "resolution_ref": "R01",
                    "decision_text": "Resolution 1 - travaux toiture votes.",
                    "action_attendue": "Demander le devis signe, le calendrier et la preuve de reception.",
                    "responsable": "Syndic / commission travaux",
                    "echeance": "2025-06-15",
                    "preuve_attendue": "Devis vote et ordre de service.",
                    "proof_doc_ids": "",
                    "proof_document_types": "",
                    "related_request_ids": "",
                    "related_invoice_refs": "",
                    "related_work_refs": "",
                    "statut": "PREUVE_A_DEMANDER",
                    "priorite": "P1",
                    "notes": "Aucune preuve locale rattachee automatiquement.",
                }
            ],
        )
        write_csv(
            incidentops.incident_register_path(self.instance),
            incidentops.INCIDENT_FIELDS,
            [
                {
                    "incident_id": "INC-001",
                    "date_signalement": "2025-05-02",
                    "lieu": "Hall",
                    "description": "Infiltration signalee apres pluie.",
                    "piece_ref": "mail_syndic.txt",
                    "doc_ids": "",
                    "photo_or_piece": "",
                    "syndic_or_provider": "Syndic",
                    "status": "EN_COURS",
                    "priority": "P1",
                    "next_action": "Relancer le syndic sur la date d'intervention.",
                    "action_due_date": "2025-05-09",
                    "expected_closure_proof": "Bon d'intervention ou photo apres resolution.",
                    "closure_proof_ref": "",
                    "contract_or_insurance_ref": "",
                    "source_refs": "mail_syndic.txt",
                    "notes": "",
                }
            ],
        )

    def _client(self, *, access_token: str | None = None):
        create_app, _ = _load_ui_objects()
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError as exc:
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        return TestClient(create_app(self.instance, 2025, access_token=access_token))

    def assertLocalHref(self, href: str, path: str) -> None:
        self.assertTrue(href.startswith("/"), f"{path} must be a local href: {href!r}")
        self.assertFalse(href.startswith("//"), f"{path} must not be protocol-relative: {href!r}")
        self.assertNotIn("://", href, f"{path} must not contain a URL scheme: {href!r}")
        self.assertNotIn("\\", href, f"{path} must not contain backslashes: {href!r}")

    def assertNoPrivateCockpitLeak(self, payload: object) -> None:
        for path, text in _public_strings(payload):
            for pattern in PRIVATE_COCKPIT_PATTERNS:
                self.assertIsNone(pattern.search(text), f"{path} leaks {pattern.pattern!r}: {text!r}")

    def assertNoForbiddenUxTokens(self, payload: object, *, instance_root: Path | None = None) -> None:
        serialized = json.dumps(payload, ensure_ascii=False).replace("\\", "/").lower()
        for marker in ["raw", "restricted", "logs", "private", "file://"]:
            self.assertNotIn(marker, serialized)
        root = instance_root or self.instance_root
        self.assertNotIn(str(root).replace("\\", "/").lower(), serialized)

    def _make_empty_instance(self):
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
        return load_instance(str(empty_root / "instance.yml"), None)

    def test_overview_surfaces_operational_cockpit_sections(self) -> None:
        self._seed_cockpit_outputs()

        create_app, build_dashboard_model = _load_ui_objects()
        model = build_dashboard_model(self.instance, 2025)

        self.assertTrue(model["cockpit_alerts"])
        self.assertGreaterEqual(model["evidence_summary"]["proofs_to_request"], 1)
        self.assertGreaterEqual(model["evidence_summary"]["decision_missing_proofs"], 1)
        self.assertIn("trust_summary", model)
        self.assertTrue(any(card["label"] == "Coffre chiffre/signe" for card in model["trust_summary"]["cards"]))
        self.assertTrue(any(card["label"] == "Pack local" for card in model["trust_summary"]["cards"]))
        self.assertTrue(any(alert["title"] == "Demandes au syndic" for alert in model["cockpit_alerts"]))
        self.assertTrue(
            any(
                "Contrat syndic signe" in (action.get("title", "") + action.get("evidence", ""))
                for action in model["actions"]
            )
        )

        status_code = 200
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            text = unescape(self._render_overview_template(model))
        else:
            client = TestClient(create_app(self.instance, 2025))
            response = client.get("/")
            status_code = response.status_code
            text = unescape(response.text)

        self.assertEqual(status_code, 200)
        self.assertIn("A faire maintenant", text)
        self.assertIn("Pourquoi", text)
        self.assertIn("Preuve ou source", text)
        self.assertIn("Prochaine action", text)
        self.assertIn("Partage autorise", text)
        self.assertIn("Raccourcis de travail", text)
        self.assertIn("Actions concretes", text)
        self.assertIn("Filtrer", text)
        self.assertIn("Ouvrir", text)
        self.assertIn("Demander au syndic: Contrat syndic signe", text)
        self.assertIn("Devis vote et ordre de service.", text)
        self.assertIn("Relancer le syndic sur la date d'intervention.", text)
        html_source = response.text if "response" in locals() else text
        self.assertGreaterEqual(html_source.count('class="cs-now-card'), 3)
        self.assertIn('class="cs-metric-chip', html_source)
        self.assertLess(
            html_source.index('class="cs-compact-metrics'),
            html_source.index('class="cs-now-grid'),
        )
        self.assertIn('class="cs-secondary-group"', html_source)
        self.assertIn('class="cs-risk-group"', html_source)
        self.assertIn("Comptes", text)
        self.assertIn("Statut sync a verifier", text)
        self.assertIn("Partage externe: non lance", text)
        self.assertNotIn("Placeholder synthetique", text)
        self.assertNotIn("Alertes simples pour test 21h15", text)
        self.assertNotIn("Coffre chiffre/signe a controler", text)
        self.assertIn("Alertes en mots simples", text)
        self.assertIn("Decisions, actions, preuves", text)
        self.assertIn("Confiance, signature, coffre", text)
        self.assertIn("Aller au contenu", text)
        self.assertIn('aria-current="page"', text)

    def test_cycle1_route_surfaces_target_cockpit_labels_with_local_token(self) -> None:
        self._seed_cockpit_outputs()
        client = self._client(access_token="local-secret")

        blocked = client.get("/")
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("Jeton local requis.", blocked.text)

        response = client.get("/?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        for label in CYCLE1_ROUTE_LABELS:
            with self.subTest(label=label):
                self.assertTrue(label in text, f"Missing Cycle 1 cockpit label: {label!r}")
        for label in ["Pourquoi", "Preuve", "Prochaine action", "Partage autorise"]:
            with self.subTest(actionable_label=label):
                self.assertTrue(label in text, f"Missing actionable cockpit label: {label!r}")
        self.assertNoPrivateCockpitLeak(text)

    def test_cycle1_route_uses_compact_action_inbox_css(self) -> None:
        static_dir = Path(__file__).resolve().parents[1] / "src" / "coproscope" / "web" / "static"
        manifest = (static_dir / "styles.css").read_text(encoding="utf-8")
        cockpit_css = (static_dir / "styles_part_32.css").read_text(encoding="utf-8")

        self.assertIn("styles_part_32.css", manifest)
        for selector in (".cs-metric-chip", ".cs-now-card", ".cs-secondary-group", ".cs-risk-group"):
            with self.subTest(selector=selector):
                self.assertIn(selector, cockpit_css)

    def test_cycle1_ux_cockpit_contract_has_cards_links_and_actionable_items(self) -> None:
        self._seed_cockpit_outputs()
        _, build_dashboard_model = _load_ui_objects()

        model = build_dashboard_model(self.instance, 2025)
        ux = model["ux"]
        cockpit = ux["cockpit"]

        self.assertEqual(ux["schema_version"], "coproscope.ux.v1")
        self.assertIn("shell", ux)
        self.assertIn("cockpit", ux)
        self.assertEqual(ux["shell"]["page_title"], "Cockpit Conseil Syndical")
        self.assertEqual(cockpit["intro_title"], "Ce qui demande attention maintenant")

        cards = cockpit["summary_cards"]
        self.assertEqual(len(cards), 5)
        card_labels = [card["label"] for card in cards]
        for label in ["Pieces manquantes", "Demandes syndic", "Echeances AG", "Alertes et risques"]:
            with self.subTest(summary_card=label):
                self.assertIn(label, card_labels)

        nav_labels = [
            item["label"]
            for section in ux["shell"]["nav_sections"]
            for item in section["items"]
        ]
        for label in ["A traiter", "Controle comptes"]:
            with self.subTest(nav_label=label):
                self.assertIn(label, nav_labels)

        for path, href in _hrefs(cockpit):
            with self.subTest(href_path=path):
                self.assertLocalHref(href, path)

        now_items = cockpit["now"]
        self.assertTrue(now_items)
        self.assertLessEqual(len(now_items), 5)
        for item in now_items:
            with self.subTest(item=item["id"]):
                for field in [
                    "id",
                    "kind",
                    "title",
                    "priority",
                    "status",
                    "lane",
                    "why",
                    "proof",
                    "action",
                    "diffusion",
                    "memory",
                    "href",
                    "source",
                ]:
                    self.assertIn(field, item)
                self.assertIn("why", item)
                self.assertTrue(item["why"])
                self.assertIsInstance(item["proof"], dict)
                self.assertTrue(item["proof"]["label"])
                self.assertIsInstance(item["action"], dict)
                self.assertTrue(item["action"]["label"])
                self.assertIsInstance(item["diffusion"], dict)
                self.assertTrue(item["diffusion"]["label"])
                self.assertLocalHref(item["href"], f"now.{item['id']}.href")

        self.assertNoPrivateCockpitLeak(cockpit)
        self.assertNoForbiddenUxTokens(ux)

    def test_cycle1_ux_cockpit_masks_private_paths_from_public_fields(self) -> None:
        reports_dir = self.instance.artifact("reports_dir")
        write_csv(
            reports_dir / "matrice_completude_documentaire.csv",
            docuscope.COMPLETENESS_FIELDS,
            [
                {
                    "proof_id": "PRV-PRIVATE",
                    "lot": "contentieux",
                    "expected_label": "Piece sensible a verifier",
                    "document_type": "Note_Contentieux",
                    "status": "A_VERIFIER_CLASSEMENT",
                    "criticality": "P1",
                    "freshness_months": "",
                    "matched_doc_ids": "",
                    "evidence_paths": r"C:\Users\ExampleUser\CoproScope\raw\secret.pdf",
                    "newest_date": "",
                    "reason": "file:///Users/ExampleUser/CoproScope/restricted/source.pdf",
                    "action": "Verifier sans exposer logs/audit.log ni chemin absolu.",
                }
            ],
        )
        write_csv(
            reports_dir / "pieces_a_demander.csv",
            docuscope.DOCUMENT_REQUEST_FIELDS,
            [
                {
                    "request_id": "REQ-DOC-PRIVATE",
                    "source_ref": "PRV-PRIVATE",
                    "priority": "P1",
                    "status": "A_VERIFIER_CLASSEMENT",
                    "subject": r"C:\Users\ExampleUser\CoproScope\restricted\secret.pdf",
                    "expected_piece": "Piece sensible a verifier",
                    "reason": "restricted/secret.pdf",
                    "related_doc_ids": "",
                    "evidence_paths": "raw/source.pdf",
                    "suggested_diligence": "Demander une reference diffusable.",
                }
            ],
        )

        _, build_dashboard_model = _load_ui_objects()
        ux = build_dashboard_model(self.instance, 2025)["ux"]
        cockpit = ux["cockpit"]

        self.assertNoPrivateCockpitLeak(cockpit)
        self.assertNoForbiddenUxTokens(ux)

    def test_cycle1_ux_cockpit_keeps_empty_instance_useful(self) -> None:
        empty = self._make_empty_instance()
        _, build_dashboard_model = _load_ui_objects()

        model = build_dashboard_model(empty, 2025)
        ux = model["ux"]
        cockpit = ux["cockpit"]

        self.assertEqual(ux["schema_version"], "coproscope.ux.v1")
        self.assertEqual(len(cockpit["summary_cards"]), 5)
        self.assertEqual(cockpit["now"], [])
        self.assertTrue(cockpit["empty_state"]["is_visible"])
        self.assertTrue(cockpit["risk_alerts"])
        self.assertNoForbiddenUxTokens(ux, instance_root=empty.instance_root)


if __name__ == "__main__":
    unittest.main()
