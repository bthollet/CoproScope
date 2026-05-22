from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
import sys
import types
import xml.etree.ElementTree as StdlibElementTree
from html import unescape
from importlib.util import find_spec
from pathlib import Path
from urllib.parse import unquote, urlparse

from coproscope.core.common import load_instance, write_csv
from coproscope.modules.accounting import (
    ACCOUNTING_CONTROL_FIELDS,
    EXPENSE_STATEMENT_FIELDS,
    INVOICE_EXPENSE_MATCH_FIELDS,
    NON_MATCH_PRIORITY_FIELDS,
)


PRIVATE_COMPTES_PATTERNS = [
    re.compile(r"raw[\\/]", re.IGNORECASE),
    re.compile(r"restricted[\\/]", re.IGNORECASE),
    re.compile(r"logs[\\/]", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
    re.compile(r"\\\\"),
    re.compile(r"(?:^|[\\/\s\"'=])/(?:Users|home)[\\/]", re.IGNORECASE),
]

CURRENT_COMPTES_ROUTE_LABELS = [
    "Controle des comptes",
    "P1 a traiter",
    "P2 a confirmer",
    "OK avec preuve rattachee",
    "Prochain geste humain",
    "Questions syndic",
    "Preuves et blocages",
    "Mode prive local",
]

CYCLE3_COMPTES_ROUTE_LABELS = [
    "Controle des comptes",
    "Exercice",
    "Exporter le rapport",
    "Factures rapprochees",
    "P2 a confirmer",
    "P1 a traiter",
    "Pieces manquantes",
    "Depenses par categorie",
    "Statut",
    "Fournisseur",
    "Afficher aussi les categories sans alerte",
    "A traiter",
    "A confirmer",
    "Questions au syndic",
    "Detail",
    "Pieces",
    "Preuve attendue",
    "Rapport AG",
]

CYCLE3_COMPTES_TOP_KEYS = [
    "context",
    "summary",
    "facets",
    "filters",
    "categories",
    "selected",
    "questions_syndic",
    "ag_report",
    "tabs",
    "empty_states",
    "export",
]

CYCLE3_CONTEXT_FIELDS = [
    "coffre_label",
    "sharing_mode_label",
    "sharing_mode_detail",
    "role_label",
    "exercise_label",
    "period_label",
    "year",
    "source_label",
    "last_updated_label",
]

CYCLE3_SUMMARY_COUNTERS = [
    "analyzed_posts_count",
    "invoice_total_count",
    "invoice_matched_count",
    "p1_count",
    "p2_count",
    "missing_pieces_count",
    "questions_count",
    "ag_included_count",
    "export_blockers_count",
]

CYCLE3_SUMMARY_LABELS = [
    "total_charges_label",
    "invoice_matched_label",
    "p1_ratio_label",
    "p2_ratio_label",
    "missing_pieces_ratio_label",
    "last_control_label",
]

CYCLE3_FACETS = [
    "exercise",
    "category",
    "status",
    "supplier",
    "proof_state",
    "piece_state",
    "alert_type",
    "ag_inclusion",
    "match_state",
]

CYCLE3_FILTER_FIELDS = [
    "selected_exercise",
    "selected_category",
    "selected_status",
    "selected_supplier",
    "selected_proof_state",
    "selected_piece_state",
    "selected_alert_type",
    "show_solded_lines",
    "query",
    "selected_category_id",
    "selected_tab",
]

CYCLE3_CATEGORY_FIELDS = [
    "category_id",
    "label",
    "amount_charges_label",
    "matched_ratio_label",
    "unmatched_invoice_count",
    "missing_pieces_count",
    "ecart_label",
    "status",
    "status_label",
    "status_detail",
    "status_tone",
    "alert_count",
    "p1_count",
    "p2_count",
    "question_count",
    "ag_included",
    "next_action_label",
    "href",
    "is_selected",
]

CYCLE3_SELECTED_FIELDS = [
    "category_id",
    "label",
    "novice_summary",
    "controls_summary",
    "alerts",
    "pieces",
    "questions",
    "ag_section",
    "history",
    "subcategories",
    "source_rows",
    "diffusion",
]

CYCLE3_ALERT_FIELDS = [
    "alert_id",
    "priority",
    "priority_label",
    "type",
    "label",
    "explanation",
    "expected_proof",
    "next_action_label",
    "status",
    "href",
]

CYCLE3_PIECE_FIELDS = [
    "piece_id",
    "doc_id",
    "label",
    "type_label",
    "supplier_label",
    "match_status_label",
    "proof_state",
    "proof_state_label",
    "role_label",
    "href",
    "actions",
]

CYCLE3_QUESTION_FIELDS = [
    "question_id",
    "category_id",
    "priority",
    "priority_label",
    "status",
    "status_label",
    "subject",
    "short_label",
    "question_text",
    "copy_text",
    "context_label",
    "expected_answer",
    "expected_proof",
    "recipient_label",
    "channel_label",
    "include_in_ag_report",
    "diffusion_label",
    "href",
]

CYCLE3_AG_REPORT_FIELDS = [
    "title",
    "scope_label",
    "generated_on_label",
    "included_categories",
    "excluded_categories",
    "p1_points",
    "p2_points",
    "ok_with_proof_points",
    "missing_pieces",
    "open_questions",
    "notes",
    "preview_markdown",
    "diffusion_status",
    "diffusion_label",
    "blocked_by",
    "export_href",
    "edit_href",
]

COMPTES_COUNTER_TARGETS = [
    ("/comptes?match=ok", "Controle des comptes"),
    ("/comptes?status=p2", "A confirmer"),
    ("/comptes?status=p1", "A traiter"),
    ("/pieces?proof=missing", "Atelier pieces"),
    ("/actions?scope=comptes&priority=P1", "Registre des decisions"),
    ("/actions?scope=comptes&priority=P2", "Registre des decisions"),
    ("/actions?scope=syndic", "Registre des decisions"),
]


def _install_defusedxml_fallback() -> None:
    if "defusedxml" in sys.modules:
        return
    if find_spec("defusedxml") is None:
        defusedxml = types.ModuleType("defusedxml")
        defusedxml.ElementTree = StdlibElementTree
        sys.modules["defusedxml"] = defusedxml


def _load_dashboard_model():
    _install_defusedxml_fallback()
    from coproscope.web.viewmodel import build_dashboard_model

    return build_dashboard_model


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


class ComptesGuideUiTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _accounting_dir(self) -> Path:
        accounting_dir = self.instance.artifact("accounting_dir") / "2025"
        accounting_dir.mkdir(parents=True, exist_ok=True)
        return accounting_dir

    def _fresh_accounting_dir(self) -> Path:
        shutil.rmtree(self.instance.artifact("accounting_dir"), ignore_errors=True)
        return self._accounting_dir()

    def _seed_accounting_guide_outputs(self) -> None:
        accounting_dir = self._accounting_dir()
        (accounting_dir / "summary_2025.json").write_text(
            json.dumps({"invoice_count": 3, "control_count": 1}),
            encoding="utf-8",
        )
        write_csv(accounting_dir / "invoice_evidence_2025.csv", ["doc_id", "fournisseur", "numero_facture", "ttc"], [])
        write_csv(accounting_dir / "invoice_anomalies_2025.csv", ["doc_id", "severity", "anomaly"], [])
        write_csv(accounting_dir / "accounting_controls_2025.csv", ACCOUNTING_CONTROL_FIELDS, [])
        write_csv(
            accounting_dir / "controles_p1_2025.csv",
            ACCOUNTING_CONTROL_FIELDS,
            [
                {
                    "control_id": "CTRL-001",
                    "exercice": "2025",
                    "severity": "P1",
                    "control": "DECISION_DEPENSE_A_JUSTIFIER",
                    "status": "A_TRAITER",
                    "doc_id": "DOC-TRAVAUX",
                    "evidence": "Facture travaux sans decision rattachee",
                    "action": "Demander la decision AG ou le bon de commande.",
                }
            ],
        )
        write_csv(
            accounting_dir / "non_rapproches_prioritaires_2025.csv",
            NON_MATCH_PRIORITY_FIELDS,
            [
                {
                    "doc_id": "DOC-EAU",
                    "fournisseur": "EAUX EXEMPLE",
                    "numero_facture": "E-2025-04",
                    "ttc": "420.00",
                    "match_status": "REFERENCE_AMBIGUE",
                    "match_priority": "P2",
                    "status_label": "Rapprochement a confirmer",
                    "match_reason": "Deux lignes de depense candidates.",
                    "next_action": "Confirmer la bonne ligne de depense avec le syndic.",
                }
            ],
        )
        write_csv(
            accounting_dir / "invoice_expense_matches_2025.csv",
            INVOICE_EXPENSE_MATCH_FIELDS,
            [
                {
                    "doc_id": "DOC-JARDIN",
                    "numero_facture": "J-2025-01",
                    "fournisseur": "JARDINS EXEMPLE",
                    "ttc": "960.00",
                    "match_status": "MATCH",
                    "match_confidence": "1.00",
                    "match_priority": "OK",
                    "status_label": "Rapprochement exact",
                    "statement_line_id": "DEP-001",
                    "statement_reference": "GL-512",
                    "statement_label": "Entretien espaces verts",
                    "statement_amount": "960.00",
                    "candidate_count": "1",
                    "match_method": "amount_reference",
                    "match_reason": "Montant et reference concordants.",
                    "next_action": "Aucune demande.",
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
        self.assertNotIn("<script", decoded.lower(), f"{path} must not echo script markup: {href!r}")

    def assertProtectedHrefKeepsToken(self, href: str, path: str, token: str) -> None:
        decoded = unquote(href)
        parsed = urlparse(decoded)
        target_path = parsed.path if parsed.scheme or parsed.netloc else decoded.split("?", 1)[0].split("#", 1)[0]
        if not target_path or target_path == "#" or target_path.startswith("/static/"):
            return
        if parsed.scheme or parsed.netloc:
            return
        self.assertIn(f"token={token}", decoded, f"{path} must keep the local token: {href!r}")

    def assertNoPrivateComptesLeak(self, payload: object) -> None:
        for path, text in _public_strings(payload):
            for pattern in PRIVATE_COMPTES_PATTERNS:
                self.assertIsNone(pattern.search(text), f"{path} leaks {pattern.pattern!r}: {text!r}")

    def assertNoForbiddenUxTokens(self, payload: object) -> None:
        serialized = json.dumps(payload, ensure_ascii=False).replace("\\", "/").lower()
        for marker in ["raw/", "restricted/", "logs/", "file://"]:
            self.assertNotIn(marker, serialized)
        self.assertNotIn(str(self.instance_root).replace("\\", "/").lower(), serialized)

    def assertNoBarePriorityLabels(self, payload: object) -> None:
        for path, text in _public_strings(payload):
            leaf = path.rsplit(".", 1)[-1].lower()
            if not any(part in leaf for part in ("label", "title", "status", "subject")):
                continue
            self.assertNotRegex(text.strip(), r"^(?:P1|P2)$", f"{path} must translate P1/P2 for novice users")

    def _assert_counter_with_href(self, summary: dict[str, object], name: str) -> None:
        self.assertIn(name, summary)
        value = summary[name]
        if isinstance(value, dict):
            self.assertTrue("value" in value or "count" in value, f"{name} must expose a count/value.")
            self.assertIn("help_label", value, f"{name} must explain the counter in human terms.")
            self.assertIn("status_tone", value, f"{name} must expose a non-color-only status tone.")
            self.assertLocalHref(str(value.get("href", "")), f"summary.{name}.href")
            return
        self.assertIn(f"{name}_href", summary, f"{name} must expose a local href.")
        self.assertLocalHref(str(summary[f"{name}_href"]), f"summary.{name}_href")

    def _cycle3_comptes_or_skip(self) -> dict[str, object]:
        _, build_dashboard_model = _load_ui_objects()
        model = build_dashboard_model(self.instance, 2025)
        ux = model["ux"]  # type: ignore[index]
        comptes = ux["comptes"]  # type: ignore[index]
        self.assertIsInstance(comptes, dict)
        if not any(key in comptes for key in CYCLE3_COMPTES_TOP_KEYS):
            self.skipTest("Cycle 3 model.ux.comptes target contract is not delivered yet.")
        missing = [key for key in CYCLE3_COMPTES_TOP_KEYS if key not in comptes]
        self.assertFalse(missing, f"Incomplete Cycle 3 model.ux.comptes contract, missing: {missing}")
        return comptes  # type: ignore[return-value]

    def test_comptes_guide_model_groups_p1_p2_and_ok_with_next_step(self) -> None:
        self._seed_accounting_guide_outputs()

        build_dashboard_model = _load_dashboard_model()
        model = build_dashboard_model(self.instance, 2025)
        self.assertEqual(len(model["accounting"]["guide"]["p1"]), 1)
        self.assertEqual(len(model["accounting"]["guide"]["p2"]), 1)
        self.assertEqual(len(model["accounting"]["guide"]["ok"]), 1)
        self.assertIn("Traiter les P1", model["accounting"]["guide"]["next_human_step"])
        self.assertEqual(model["accounting"]["guide"]["ok"][0]["evidence"], "DOC-JARDIN / GL-512")

    def test_model_ux_comptes_projects_real_accounting_rows_into_non_empty_kpis(self) -> None:
        accounting_dir = self._fresh_accounting_dir()
        (accounting_dir / "summary_2025.json").write_text(
            json.dumps(
                {
                    "invoice_count": 2,
                    "expense_statement_line_count": 2,
                    "expense_match_counts": {"MATCH_AMOUNT_ALIAS": 1},
                    "generated_at": "2026-05-21T08:00:00+00:00",
                }
            ),
            encoding="utf-8",
        )
        write_csv(
            accounting_dir / "expense_statement_lines_2025.csv",
            EXPENSE_STATEMENT_FIELDS,
            [
                {
                    "statement_line_id": "DEP-JARDIN",
                    "date": "2025-01-15",
                    "account": "615000",
                    "account_label": "Entretien",
                    "reference": "GL-JARDIN",
                    "supplier_hint": "JARDINS EXEMPLE",
                    "label": "Entretien espaces verts",
                    "amount": "960.00",
                    "source": "etat_depenses",
                },
                {
                    "statement_line_id": "DEP-EAU",
                    "date": "2025-04-01",
                    "account": "606100",
                    "account_label": "Eau",
                    "reference": "GL-EAU",
                    "supplier_hint": "EAUX EXEMPLE",
                    "label": "Consommation eau",
                    "amount": "420.00",
                    "source": "etat_depenses",
                },
            ],
        )
        write_csv(
            accounting_dir / "invoice_evidence_2025.csv",
            ["doc_id", "fournisseur", "numero_facture", "ttc"],
            [
                {"doc_id": "DOC-JARDIN", "fournisseur": "JARDINS EXEMPLE", "numero_facture": "J-2025-01", "ttc": "960.00"},
                {"doc_id": "DOC-EAU", "fournisseur": "EAUX EXEMPLE", "numero_facture": "E-2025-04", "ttc": "420.00"},
            ],
        )
        write_csv(accounting_dir / "invoice_anomalies_2025.csv", ["doc_id", "severity", "anomaly"], [])
        write_csv(accounting_dir / "accounting_controls_2025.csv", ACCOUNTING_CONTROL_FIELDS, [])
        write_csv(
            accounting_dir / "controles_p1_2025.csv",
            ACCOUNTING_CONTROL_FIELDS,
            [
                {
                    "control_id": "CTRL-DECISION",
                    "exercice": "2025",
                    "severity": "P1",
                    "control": "DECISION_DEPENSE_A_JUSTIFIER",
                    "status": "A_TRAITER",
                    "doc_id": "DOC-CTRL",
                    "evidence": "Decision ou bon de commande attendu",
                    "action": "Demander la decision AG ou le bon de commande.",
                }
            ],
        )
        write_csv(
            accounting_dir / "non_rapproches_prioritaires_2025.csv",
            NON_MATCH_PRIORITY_FIELDS,
            [
                {
                    "doc_id": "DOC-EAU",
                    "fournisseur": "EAUX EXEMPLE",
                    "numero_facture": "E-2025-04",
                    "ttc": "420.00",
                    "match_status": "REFERENCE_AMIGUE",
                    "match_priority": "P2",
                    "status_label": "Rapprochement a confirmer",
                    "match_reason": "Deux lignes de depense candidates.",
                    "next_action": "Confirmer la bonne ligne de depense avec le syndic.",
                }
            ],
        )
        write_csv(
            accounting_dir / "invoice_expense_matches_2025.csv",
            INVOICE_EXPENSE_MATCH_FIELDS,
            [
                {
                    "doc_id": "DOC-JARDIN",
                    "numero_facture": "J-2025-01",
                    "fournisseur": "JARDINS EXEMPLE",
                    "ttc": "960.00",
                    "match_status": "MATCH_AMOUNT_ALIAS",
                    "match_confidence": "PROBABLE_FORT",
                    "match_priority": "OK",
                    "status_label": "Montant exact + alias fournisseur",
                    "statement_line_id": "DEP-JARDIN",
                    "statement_reference": "GL-JARDIN",
                    "statement_label": "Entretien espaces verts",
                    "statement_amount": "960.00",
                    "candidate_count": "1",
                    "match_method": "amount_supplier_alias",
                    "match_reason": "Montant TTC exact et alias reconnu.",
                    "next_action": "Conserver le rattachement.",
                }
            ],
        )

        model = _load_dashboard_model()(self.instance, 2025)
        comptes = model["ux"]["comptes"]  # type: ignore[index]
        summary = comptes["summary"]  # type: ignore[index]

        self.assertEqual(model["accounting"]["before_ag"], {"blocking": 1, "to_confirm": 1, "ok": 1})
        self.assertEqual(model["accounting"]["summary"]["total_charges_label"], "1 380,00 EUR")
        self.assertEqual(summary["total_charges_label"], "1 380,00 EUR")
        self.assertEqual(summary["analyzed_posts_count"], 3)
        self.assertEqual(summary["invoice_total_count"], 2)
        self.assertEqual(summary["invoice_matched_count"], 1)
        self.assertEqual(summary["p1_count"], 1)
        self.assertEqual(summary["p2_count"], 1)
        self.assertEqual(summary["missing_pieces_count"], 1)
        self.assertEqual(summary["questions_count"], 2)

        statuses = {category["category_id"]: category["status"] for category in comptes["categories"]}  # type: ignore[index]
        self.assertEqual(statuses["controles_prioritaires"], "p1")
        self.assertEqual(statuses["energie_fluides"], "p2")
        self.assertEqual(statuses["entretien_maintenance"], "ok")
        self.assertEqual(comptes["selected"]["category_id"], "controles_prioritaires")  # type: ignore[index]
        self.assertTrue(comptes["questions_syndic"])  # type: ignore[index]
        self.assertNoBarePriorityLabels(comptes)
        self.assertNoPrivateComptesLeak(comptes)
        self.assertNoForbiddenUxTokens(comptes)

    def test_model_ux_comptes_turns_invoice_anomalies_into_safe_alerts_and_questions(self) -> None:
        accounting_dir = self._fresh_accounting_dir()
        (accounting_dir / "summary_2025.json").write_text(
            json.dumps({"invoice_count": 1, "invoice_anomaly_count": 1}),
            encoding="utf-8",
        )
        write_csv(
            accounting_dir / "expense_statement_lines_2025.csv",
            EXPENSE_STATEMENT_FIELDS,
            [
                {
                    "statement_line_id": "DEP-ENERGIE",
                    "date": "2025-02-01",
                    "account": "606100",
                    "account_label": "Eau",
                    "reference": "GL-ENERGIE",
                    "supplier_hint": "FOURNISSEUR LOCAL",
                    "label": "Fluides a verifier",
                    "amount": "120.00",
                    "source": "etat_depenses",
                }
            ],
        )
        write_csv(
            accounting_dir / "invoice_evidence_2025.csv",
            ["doc_id", "fournisseur", "numero_facture", "ttc"],
            [{"doc_id": "DOC-ANOM", "fournisseur": "FOURNISSEUR LOCAL", "numero_facture": "A-2025", "ttc": "120.00"}],
        )
        write_csv(
            accounting_dir / "invoice_anomalies_2025.csv",
            ["anomaly_id", "exercice", "severity", "status", "doc_id", "fournisseur", "numero_facture", "ttc", "anomaly", "evidence_level", "extraction_method", "evidence", "action"],
            [
                {
                    "anomaly_id": "ANOM-001",
                    "exercice": "2025",
                    "severity": "P1",
                    "status": "A_TRAITER",
                    "doc_id": "DOC-ANOM",
                    "fournisseur": "FOURNISSEUR LOCAL",
                    "numero_facture": "A-2025",
                    "ttc": "120.00",
                    "anomaly": "raw/secret.pdf mentionne un justificatif incomplet.",
                    "evidence_level": "L1",
                    "extraction_method": "local_text",
                    "evidence": "file:///Users/ExampleUser/CoproScope/restricted/preuve.pdf",
                    "action": "Demander une copie diffusable au syndic.",
                }
            ],
        )
        write_csv(accounting_dir / "accounting_controls_2025.csv", ACCOUNTING_CONTROL_FIELDS, [])
        write_csv(accounting_dir / "controles_p1_2025.csv", ACCOUNTING_CONTROL_FIELDS, [])
        write_csv(accounting_dir / "non_rapproches_prioritaires_2025.csv", NON_MATCH_PRIORITY_FIELDS, [])
        write_csv(accounting_dir / "invoice_expense_matches_2025.csv", INVOICE_EXPENSE_MATCH_FIELDS, [])

        model = _load_dashboard_model()(self.instance, 2025)
        comptes = model["ux"]["comptes"]  # type: ignore[index]
        summary = comptes["summary"]  # type: ignore[index]

        self.assertEqual(model["accounting"]["before_ag"]["blocking"], 1)
        self.assertEqual(model["accounting"]["guide"]["p1"][0]["status"], "A traiter")
        self.assertNoPrivateComptesLeak(model["accounting"]["syndic_questions"])
        self.assertNoPrivateComptesLeak(model["accounting"]["guide"])
        self.assertEqual(summary["p1_count"], 1)
        self.assertEqual(summary["questions_count"], 1)
        self.assertEqual(summary["missing_pieces_count"], 1)
        self.assertTrue(comptes["selected"]["alerts"])  # type: ignore[index]
        self.assertTrue(comptes["selected"]["questions"])  # type: ignore[index]
        self.assertNoBarePriorityLabels(comptes)
        self.assertNoPrivateComptesLeak(comptes)
        self.assertNoForbiddenUxTokens(comptes)

    def test_comptes_page_renders_guided_p1_p2_ok_workflow(self) -> None:
        self._seed_accounting_guide_outputs()

        try:
            create_app, _ = _load_ui_objects()
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI/Jinja UI test dependencies unavailable")

        client = TestClient(create_app(self.instance, 2025))
        response = client.get("/comptes")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("P1 a traiter", text)
        self.assertIn("P2 a confirmer", text)
        self.assertIn("OK avec preuve rattachee", text)
        self.assertIn("Prochain geste humain", text)
        self.assertIn("Questions syndic", text)
        self.assertIn("Preuves et blocages", text)
        self.assertIn("Facture travaux sans decision rattachee", text)
        self.assertIn("EAUX EXEMPLE - E-2025-04", text)
        self.assertIn("JARDINS EXEMPLE - J-2025-01", text)
        self.assertIn("DOC-JARDIN / GL-512", text)
        self.assertIn("Confirmer la bonne ligne de depense avec le syndic.", text)

    def test_comptes_page_stays_readable_without_accounting_outputs(self) -> None:
        shutil.rmtree(self.instance.artifact("accounting_dir"), ignore_errors=True)

        try:
            create_app, _ = _load_ui_objects()
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError:
            self.skipTest("FastAPI/Jinja UI test dependencies unavailable")

        client = TestClient(create_app(self.instance, 2025))
        response = client.get("/comptes")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Generer ou importer les sorties ComptaScope", text)
        self.assertIn("Aucun P1 visible dans les sorties disponibles.", text)
        self.assertIn("Aucun P2 a confirmer dans les sorties disponibles.", text)
        self.assertIn("Aucun rapprochement OK charge pour l'instant.", text)

    def test_comptes_route_is_token_gated_and_keeps_current_novice_labels(self) -> None:
        self._seed_accounting_guide_outputs()
        client = self._client(access_token="local-secret")

        blocked = client.get("/comptes")
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("Jeton local requis.", blocked.text)

        response = client.get("/comptes?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        for label in CURRENT_COMPTES_ROUTE_LABELS:
            with self.subTest(label=label):
                self.assertIn(label, text)
        self.assertIn("A traiter avant AG", text)
        self.assertIn("A confirmer: rapprochement plausible", text)
        self.assertNotIn("P1 Prioritaire", text)
        self.assertNotIn("P2 Prioritaire", text)
        self.assertNotIn("email automatique", text.lower())
        self.assertNoPrivateComptesLeak(text)
        for index, href in enumerate(_html_hrefs(text)):
            with self.subTest(href=href):
                self.assertLocalHref(href, f"html.href[{index}]")
                self.assertProtectedHrefKeepsToken(href, f"html.href[{index}]", "local-secret")

    def test_comptes_counters_keep_token_and_open_useful_screens(self) -> None:
        self._seed_accounting_guide_outputs()
        token = "local-secret"
        response = self._client(access_token=token).get(_with_token("/comptes", token))
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertNoPrivateComptesLeak(text)
        for target_path, useful_label in COMPTES_COUNTER_TARGETS:
            with self.subTest(target=target_path):
                href = _find_href_for_path(text, target_path)
                self.assertIn(f"token={token}", href)

                follow_up = self._client(access_token=token).get(href)
                self.assertEqual(follow_up.status_code, 200, href)
                self.assertIn(useful_label, unescape(follow_up.text))

    def test_cycle3_comptes_route_layout_labels_when_delivered(self) -> None:
        self._seed_accounting_guide_outputs()
        client = self._client(access_token="local-secret")

        response = client.get("/comptes?token=local-secret&tab=questions&status=p1")
        text = unescape(response.text)
        self.assertEqual(response.status_code, 200)

        missing_labels = [label for label in CYCLE3_COMPTES_ROUTE_LABELS if label not in text]
        if missing_labels:
            self.skipTest(
                "Cycle 3 front /comptes layout is not delivered yet; "
                f"missing target labels: {missing_labels}"
            )
        for label in CYCLE3_COMPTES_ROUTE_LABELS:
            with self.subTest(label=label):
                self.assertIn(label, text)
        self.assertNotIn("P1 Prioritaire", text)
        self.assertNotIn("P2 Prioritaire", text)
        self.assertNotIn("Envoyer automatiquement", text)
        self.assertNoPrivateComptesLeak(text)

    def test_cycle3_model_ux_comptes_contract_when_delivered(self) -> None:
        self._seed_accounting_guide_outputs()
        comptes = self._cycle3_comptes_or_skip()

        for field in CYCLE3_CONTEXT_FIELDS:
            with self.subTest(context_field=field):
                self.assertIn(field, comptes["context"])

        summary = comptes["summary"]
        self.assertIsInstance(summary, dict)
        for name in CYCLE3_SUMMARY_COUNTERS:
            with self.subTest(summary_counter=name):
                self._assert_counter_with_href(summary, name)
        for field in CYCLE3_SUMMARY_LABELS:
            with self.subTest(summary_label=field):
                self.assertIn(field, summary)

        for facet in CYCLE3_FACETS:
            with self.subTest(facet=facet):
                self.assertIn(facet, comptes["facets"])
        for field in CYCLE3_FILTER_FIELDS:
            with self.subTest(filter_field=field):
                self.assertIn(field, comptes["filters"])

        categories = comptes["categories"]
        self.assertIsInstance(categories, list)
        for category in categories:
            with self.subTest(category=category.get("category_id")):
                for field in CYCLE3_CATEGORY_FIELDS:
                    self.assertIn(field, category)
                self.assertLocalHref(category["href"], f"categories.{category.get('category_id')}.href")
                self.assertIn(category["status"], {"ok", "p2", "p1", "missing", "unknown"})

        selected = comptes["selected"]
        self.assertIsInstance(selected, dict)
        for field in CYCLE3_SELECTED_FIELDS:
            with self.subTest(selected_field=field):
                self.assertIn(field, selected)
        self.assertIsInstance(selected["alerts"], list)
        self.assertIsInstance(selected["pieces"], list)
        self.assertIsInstance(selected["questions"], list)

        for alert in selected["alerts"]:
            for field in CYCLE3_ALERT_FIELDS:
                self.assertIn(field, alert)
            self.assertNotRegex(str(alert["priority_label"]).strip(), r"^(?:P1|P2)$")
            self.assertTrue(alert["expected_proof"])
            self.assertTrue(alert["next_action_label"])
            self.assertLocalHref(alert["href"], f"alerts.{alert.get('alert_id')}.href")

        for piece in selected["pieces"]:
            for field in CYCLE3_PIECE_FIELDS:
                self.assertIn(field, piece)
            self.assertLocalHref(piece["href"], f"pieces.{piece.get('piece_id')}.href")

        for question in selected["questions"]:
            for field in CYCLE3_QUESTION_FIELDS:
                self.assertIn(field, question)
            self.assertNotRegex(str(question["priority_label"]).strip(), r"^(?:P1|P2)$")
            self.assertTrue(question["copy_text"])
            self.assertTrue(question["expected_proof"])
            self.assertLocalHref(question["href"], f"questions.{question.get('question_id')}.href")

        ag_report = comptes["ag_report"]
        self.assertIsInstance(ag_report, dict)
        for field in CYCLE3_AG_REPORT_FIELDS:
            with self.subTest(ag_report_field=field):
                self.assertIn(field, ag_report)
        self.assertLocalHref(ag_report["export_href"], "ag_report.export_href")
        self.assertLocalHref(ag_report["edit_href"], "ag_report.edit_href")

        self.assertNoBarePriorityLabels(comptes)
        self.assertNoPrivateComptesLeak(comptes)
        self.assertNoForbiddenUxTokens(comptes)
        for path, href in _hrefs(comptes):
            with self.subTest(href_path=path):
                self.assertLocalHref(href, path)

    def test_cycle3_model_ux_comptes_masks_private_paths_when_delivered(self) -> None:
        accounting_dir = self._accounting_dir()
        (accounting_dir / "summary_2025.json").write_text(
            json.dumps({"invoice_count": 2, "control_count": 1}),
            encoding="utf-8",
        )
        write_csv(
            accounting_dir / "invoice_evidence_2025.csv",
            ["doc_id", "fournisseur", "numero_facture", "ttc"],
            [
                {
                    "doc_id": "DOC-PRIVATE",
                    "fournisseur": r"C:\Users\ExampleUser\CoproScope\restricted\fournisseur.txt",
                    "numero_facture": "F-PRIVATE",
                    "ttc": "120.00",
                }
            ],
        )
        write_csv(
            accounting_dir / "invoice_anomalies_2025.csv",
            ["doc_id", "severity", "anomaly"],
            [
                {
                    "doc_id": "DOC-PRIVATE",
                    "severity": "P1",
                    "anomaly": "raw/secret.pdf mentionne dans une anomalie importee.",
                }
            ],
        )
        write_csv(accounting_dir / "accounting_controls_2025.csv", ACCOUNTING_CONTROL_FIELDS, [])
        write_csv(
            accounting_dir / "controles_p1_2025.csv",
            ACCOUNTING_CONTROL_FIELDS,
            [
                {
                    "control_id": "CTRL-PRIVATE",
                    "exercice": "2025",
                    "severity": "P1",
                    "control": "CHEMIN_PRIVE_A_MASQUER",
                    "status": "A_TRAITER",
                    "doc_id": r"C:\Users\ExampleUser\CoproScope\raw\facture.pdf",
                    "evidence": "file:///Users/ExampleUser/CoproScope/restricted/preuve.pdf",
                    "action": "Verifier sans exposer logs/audit.log ni chemin absolu.",
                }
            ],
        )
        write_csv(
            accounting_dir / "non_rapproches_prioritaires_2025.csv",
            NON_MATCH_PRIORITY_FIELDS,
            [
                {
                    "doc_id": "DOC-NONMATCH",
                    "fournisseur": "Fournisseur local",
                    "numero_facture": "NR-2025",
                    "ttc": "220.00",
                    "match_status": "NON_RAPPROCHE",
                    "match_priority": "P2",
                    "status_label": "Rapprochement a confirmer",
                    "match_reason": r"C:\Users\ExampleUser\CoproScope\logs\match.log",
                    "next_action": "Demander une reference diffusable au syndic.",
                }
            ],
        )
        write_csv(accounting_dir / "invoice_expense_matches_2025.csv", INVOICE_EXPENSE_MATCH_FIELDS, [])

        comptes = self._cycle3_comptes_or_skip()

        self.assertNoBarePriorityLabels(comptes)
        self.assertNoPrivateComptesLeak(comptes)
        self.assertNoForbiddenUxTokens(comptes)
        for path, href in _hrefs(comptes):
            with self.subTest(href_path=path):
                self.assertLocalHref(href, path)


if __name__ == "__main__":
    unittest.main()
