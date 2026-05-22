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
from urllib.parse import unquote, urlparse

from coproscope.core.common import load_instance, write_csv
from coproscope.modules import decisionops, incidentops


PRIVATE_REGISTRE_PATTERNS = [
    re.compile(r"raw[\\/]", re.IGNORECASE),
    re.compile(r"restricted[\\/]", re.IGNORECASE),
    re.compile(r"logs[\\/]", re.IGNORECASE),
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
    re.compile(r"\\\\"),
    re.compile(r"(?:^|[\\/\s\"'=])/(?:Users|home)[\\/]", re.IGNORECASE),
]

CURRENT_ACTIONS_ROUTE_LABELS = [
    "Registre decisions - actions - preuves",
    "Suivi des decisions et relances",
    "Files de suivi",
    "Preuves attendues",
    "Relances responsables",
    "Registre de travail",
    "Historique / conflit",
    "Prudence diffusion",
]

CYCLE2_REGISTRE_TOP_KEYS = [
    "context",
    "summary",
    "facets",
    "filters",
    "ag_groups",
    "items",
    "selected",
    "tabs",
    "empty_states",
    "export",
]

CYCLE2_TARGET_ONLY_KEYS = [
    key for key in CYCLE2_REGISTRE_TOP_KEYS if key not in {"items", "selected"}
]

CYCLE2_CONTEXT_FIELDS = [
    "coffre_label",
    "sharing_mode_label",
    "sharing_mode_detail",
    "role_label",
    "as_of_label",
]

CYCLE2_SUMMARY_COUNTERS = [
    "total_resolutions",
    "open_actions",
    "late_actions",
    "missing_proofs",
    "syndic_followups",
    "verified_proofs",
    "share_blockers",
]

CYCLE2_FACETS = [
    "ag",
    "status",
    "owner",
    "priority",
    "proof_state",
    "due_state",
    "scope",
]

CYCLE2_FILTER_FIELDS = [
    "selected_ag",
    "selected_status",
    "selected_owner",
    "selected_priority",
    "selected_proof_state",
    "query",
    "selected_item_id",
]

CYCLE2_ITEM_FIELDS = [
    "id",
    "ag_id",
    "resolution_ref",
    "source_doc_id",
    "source_file_label",
    "title",
    "decision_summary",
    "decision_source_excerpt",
    "majority_label",
    "status",
    "status_label",
    "status_detail",
    "status_tone",
    "priority",
    "priority_label",
    "priority_reason",
    "owner",
    "referent",
    "due_on",
    "due_label",
    "due_state",
    "progress_pct",
    "next_step",
    "action_description",
    "proof_expected",
    "proof_state",
    "proof_state_label",
    "proofs",
    "pieces",
    "followups",
    "history",
    "diffusion",
    "memory",
    "href",
]

CYCLE2_PROOF_FIELDS = [
    "proof_id",
    "label",
    "type_label",
    "source_doc_id",
    "source_label",
    "captured_on",
    "verified_on",
    "status",
    "status_label",
    "confirms",
    "diffusion_label",
    "restriction_reason",
    "href",
]

CYCLE2_PIECE_FIELDS = [
    "doc_id",
    "label",
    "type_label",
    "added_on",
    "role_label",
    "proof_relation",
    "diffusion_label",
    "href",
    "download_href",
    "actions",
]

CYCLE2_FOLLOWUP_FIELDS = [
    "followup_id",
    "label",
    "status",
    "status_label",
    "sent_on",
    "channel_label",
    "recipient_label",
    "message_excerpt",
    "expected_answer",
    "answer_summary",
    "related_request_id",
    "copy_text",
    "href",
]

CYCLE2_HISTORY_FIELDS = [
    "event_id",
    "occurred_on",
    "type",
    "type_label",
    "actor_label",
    "summary",
    "proof_ids",
    "piece_ids",
    "followup_ids",
    "is_evidence",
    "memory_note",
]

CYCLE2_TAB_LABELS = ["Action", "Preuves", "Pieces liees", "Relance syndic", "Historique"]
CYCLE2_PROOF_STATUSES = {"missing", "candidate", "verified", "rejected", "blocked"}
CYCLE2_FOLLOWUP_STATUSES = {"draft", "to_send", "sent_waiting", "answered_to_check", "closed"}

ACTION_FILTER_ROUTE_EXPECTATIONS = [
    ("/actions?priority=P1", ["Registre des decisions", "Fiches action a traiter maintenant", "Prochaine action"]),
    ("/actions?scope=syndic", ["Registre des decisions", "Syndic", "Relance syndic"]),
    ("/actions?status=a_demander", ["Demander au syndic", "Preuve a demander", "Preparer une relance"]),
]

ACTION_COUNTER_TARGETS = [
    ("/actions?status=a_demander", "Demander au syndic"),
    ("/actions?status=a_verifier", "Verifier la preuve"),
    ("/pieces", "Atelier pieces"),
    ("/actions?status=a_revoir", "Arbitrer en CS"),
    ("/actions?status=clos", "Cloturer avec preuve"),
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


class UiRegistreActionsProductQaTests(unittest.TestCase):
    def setUp(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        source_example = repo_root / "examples" / "synthetic_copro"
        self.tempdir = tempfile.TemporaryDirectory()
        self.instance_root = Path(self.tempdir.name) / "instance"
        shutil.copytree(source_example, self.instance_root)
        self.instance = load_instance(str(self.instance_root / "instance.yml"), None)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _client(self, *, access_token: str | None = None, raise_server_exceptions: bool = True):
        create_app, _ = _load_ui_objects()
        try:
            from fastapi.testclient import TestClient  # type: ignore
        except ImportError as exc:
            self.skipTest(f"FastAPI test client unavailable: {exc}")
        return TestClient(
            create_app(self.instance, 2025, access_token=access_token),
            raise_server_exceptions=raise_server_exceptions,
        )

    def _seed_registre_actions(self) -> None:
        reports_dir = self.instance.artifact("reports_dir")
        reports_dir.mkdir(parents=True, exist_ok=True)
        write_csv(
            decisionops.decision_register_path(self.instance),
            decisionops.DECISION_ACTION_FIELDS,
            [
                {
                    "decision_action_id": "DAP-MISSING",
                    "ag_id": "AG-2024-06-15",
                    "source_doc_id": "DOC-PV-2024",
                    "source_file": "pv_ag_2024.txt",
                    "resolution_ref": "R03",
                    "decision_text": "Travaux etancheite toiture votes.",
                    "action_attendue": "Demander le devis signe, le calendrier et la preuve de reception.",
                    "responsable": "Syndic / commission travaux",
                    "echeance": "2024-07-15",
                    "preuve_attendue": "Devis vote et ordre de service.",
                    "proof_doc_ids": "",
                    "proof_document_types": "",
                    "related_request_ids": "REQ-TOITURE",
                    "related_invoice_refs": "",
                    "related_work_refs": "",
                    "statut": "PREUVE_A_DEMANDER",
                    "priorite": "P1",
                    "notes": "Aucune preuve locale rattachee automatiquement.",
                },
                {
                    "decision_action_id": "DAP-CANDIDATE",
                    "ag_id": "AG-2024-06-15",
                    "source_doc_id": "DOC-PV-2024",
                    "source_file": "pv_ag_2024.txt",
                    "resolution_ref": "R04",
                    "decision_text": "Contrat syndic a verifier.",
                    "action_attendue": "Verifier la version signee et la date d'effet.",
                    "responsable": "Conseil syndical",
                    "echeance": "2024-07-01",
                    "preuve_attendue": "Contrat de syndic signe.",
                    "proof_doc_ids": "DOC-CONTRAT",
                    "proof_document_types": "Contrat_Syndic",
                    "related_request_ids": "",
                    "related_invoice_refs": "",
                    "related_work_refs": "",
                    "statut": "PREUVE_LOCALE_A_VERIFIER",
                    "priorite": "P2",
                    "notes": "Preuve candidate a confirmer avant cloture.",
                },
            ],
        )
        write_csv(
            incidentops.incident_register_path(self.instance),
            incidentops.INCIDENT_FIELDS,
            [
                {
                    "incident_id": "INC-RELANCE",
                    "date_signalement": "2024-06-20",
                    "lieu": "Toiture",
                    "description": "Trace d'infiltration apres pluie.",
                    "piece_ref": "mail_syndic.txt",
                    "doc_ids": "",
                    "photo_or_piece": "",
                    "syndic_or_provider": "Syndic",
                    "status": "EN_RELANCE",
                    "priority": "P1",
                    "next_action": "Preparer une relance syndic avec la preuve attendue.",
                    "action_due_date": "2024-06-28",
                    "expected_closure_proof": "Bon d'intervention ou photo apres resolution.",
                    "closure_proof_ref": "",
                    "contract_or_insurance_ref": "",
                    "source_refs": "mail_syndic.txt",
                    "notes": "",
                }
            ],
        )

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

    def assertNoPrivateRegistreLeak(self, payload: object) -> None:
        for path, text in _public_strings(payload):
            for pattern in PRIVATE_REGISTRE_PATTERNS:
                self.assertIsNone(pattern.search(text), f"{path} leaks {pattern.pattern!r}: {text!r}")

    def assertNoForbiddenUxTokens(self, payload: object) -> None:
        serialized = json.dumps(payload, ensure_ascii=False).replace("\\", "/").lower()
        for marker in ["raw/", "restricted/", "logs/", "file://"]:
            self.assertNotIn(marker, serialized)
        self.assertNotIn(str(self.instance_root).replace("\\", "/").lower(), serialized)

    def _cycle2_registre_or_skip(self) -> dict[str, object]:
        _, build_dashboard_model = _load_ui_objects()
        model = build_dashboard_model(self.instance, 2025)
        registre = model["ux"]["registre"]  # type: ignore[index]
        self.assertIsInstance(registre, dict)
        if not any(key in registre for key in CYCLE2_TARGET_ONLY_KEYS):
            self.skipTest("Cycle 2 model.ux.registre target contract is not delivered yet.")
        missing = [key for key in CYCLE2_REGISTRE_TOP_KEYS if key not in registre]
        self.assertFalse(missing, f"Incomplete Cycle 2 model.ux.registre contract, missing: {missing}")
        return registre  # type: ignore[return-value]

    def _assert_counter_with_href(self, summary: dict[str, object], name: str) -> None:
        self.assertIn(name, summary)
        value = summary[name]
        if isinstance(value, dict):
            self.assertTrue("value" in value or "count" in value, f"{name} must expose a count/value.")
            self.assertLocalHref(str(value.get("href", "")), f"summary.{name}.href")
            return
        self.assertIn(f"{name}_href", summary, f"{name} must expose a local href.")
        self.assertLocalHref(str(summary[f"{name}_href"]), f"summary.{name}_href")

    def test_actions_route_is_token_gated_and_surfaces_current_register_labels(self) -> None:
        self._seed_registre_actions()
        client = self._client(access_token="local-secret")

        blocked = client.get("/actions")
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("Jeton local requis.", blocked.text)

        response = client.get("/actions?token=local-secret&scope=decisions&status=a_demander&priority=P1")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        for label in CURRENT_ACTIONS_ROUTE_LABELS:
            with self.subTest(label=label):
                self.assertIn(label, text)
        self.assertIn("Travaux etancheite toiture votes", text)
        self.assertIn("Devis vote et ordre de service", text)
        self.assertNoPrivateRegistreLeak(text)
        for index, href in enumerate(_html_hrefs(text)):
            with self.subTest(href=href):
                self.assertLocalHref(href, f"html.href[{index}]")

    def test_actions_route_renders_default_synthetic_instance_with_token(self) -> None:
        client = self._client(access_token="local-secret", raise_server_exceptions=False)

        blocked = client.get("/actions")
        self.assertEqual(blocked.status_code, 403)
        self.assertIn("Jeton local requis.", blocked.text)

        response = client.get("/actions?token=local-secret")
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Registre decisions - actions - preuves", text)
        self.assertIn("Registre de travail", text)
        self.assertNoPrivateRegistreLeak(text)
        for index, href in enumerate(_html_hrefs(text)):
            with self.subTest(href=href):
                self.assertLocalHref(href, f"html.href[{index}]")

    def test_actions_route_ignores_harmless_extra_query_params_without_script_echo(self) -> None:
        self._seed_registre_actions()
        client = self._client(access_token="local-secret")

        response = client.get(
            "/actions"
            "?token=local-secret"
            "&scope=decisions"
            "&status=a_demander"
            "&priority=P1"
            "&selected_item_id=..%2F..%2Fraw%2Fsecret.pdf"
            "&tab=javascript%3Aalert(1)"
            "&q=%3Cscript%3Ealert(1)%3C%2Fscript%3E"
        )
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("<script>alert(1)</script>", text)
        self.assertNotIn("javascript:alert(1)", text)
        self.assertNoPrivateRegistreLeak(text)
        for index, href in enumerate(_html_hrefs(text)):
            with self.subTest(href=href):
                self.assertLocalHref(href, f"html.href[{index}]")

    def test_actions_priority_scope_and_status_routes_keep_token_and_stay_useful(self) -> None:
        self._seed_registre_actions()
        token = "local-secret"

        for path, expected_labels in ACTION_FILTER_ROUTE_EXPECTATIONS:
            with self.subTest(path=path, mode="without-token"):
                blocked = self._client(access_token=token).get(path)
                self.assertEqual(blocked.status_code, 403)
                self.assertIn("Jeton local requis.", blocked.text)

            with self.subTest(path=path, mode="with-token"):
                response = self._client(access_token=token).get(_with_token(path, token))
                text = unescape(response.text)

                self.assertEqual(response.status_code, 200)
                for label in expected_labels:
                    self.assertIn(label, text)
                self.assertNotIn("P1 Prioritaire", text)
                self.assertNotIn("P2 Prioritaire", text)
                self.assertNotIn("Envoyer automatiquement", text)
                self.assertNoPrivateRegistreLeak(text)
                for index, href in enumerate(_html_hrefs(text)):
                    with self.subTest(route=path, href=href):
                        self.assertLocalHref(href, f"{path}.html.href[{index}]")
                        self.assertProtectedHrefKeepsToken(href, f"{path}.html.href[{index}]", token)

    def test_actions_summary_counters_open_tokenized_useful_screens(self) -> None:
        self._seed_registre_actions()
        token = "local-secret"
        response = self._client(access_token=token).get(_with_token("/actions", token))
        self.assertEqual(response.status_code, 200)
        text = unescape(response.text)

        for target_path, useful_label in ACTION_COUNTER_TARGETS:
            with self.subTest(target=target_path):
                href = _find_href_for_path(text, target_path)
                self.assertIn(f"token={token}", href)

                follow_up = self._client(access_token=token).get(href)
                self.assertEqual(follow_up.status_code, 200, href)
                self.assertIn(useful_label, unescape(follow_up.text))

    def test_actions_api_exposes_minimal_registre_namespace_without_private_leaks(self) -> None:
        self._seed_registre_actions()
        client = self._client(access_token="local-secret")

        blocked = client.get("/api/model")
        self.assertEqual(blocked.status_code, 403)

        response = client.get("/api/model?token=local-secret")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        registre = payload["ux"]["registre"]

        self.assertIsInstance(registre, dict)
        self.assertIsInstance(registre.get("items"), list)
        self.assertIsInstance(registre.get("selected"), dict)
        if registre["items"]:
            first = registre["items"][0]
            for field in ["id", "title", "status", "proof", "action", "diffusion", "memory", "href"]:
                with self.subTest(field=field):
                    self.assertIn(field, first)
            self.assertLocalHref(first["href"], "registre.items[0].href")

        self.assertNoPrivateRegistreLeak(registre)
        self.assertNoForbiddenUxTokens(registre)
        for path, href in _hrefs(registre):
            with self.subTest(href_path=path):
                self.assertLocalHref(href, path)

    def test_cycle2_model_ux_registre_contract_when_delivered(self) -> None:
        self._seed_registre_actions()
        registre = self._cycle2_registre_or_skip()

        for field in CYCLE2_CONTEXT_FIELDS:
            with self.subTest(context_field=field):
                self.assertIn(field, registre["context"])
                self.assertTrue(registre["context"][field])

        summary = registre["summary"]
        self.assertIsInstance(summary, dict)
        for name in CYCLE2_SUMMARY_COUNTERS:
            with self.subTest(summary_counter=name):
                self._assert_counter_with_href(summary, name)
        self.assertIn("last_updated_label", summary)

        for facet in CYCLE2_FACETS:
            with self.subTest(facet=facet):
                self.assertIn(facet, registre["facets"])
        for field in CYCLE2_FILTER_FIELDS:
            with self.subTest(filter_field=field):
                self.assertIn(field, registre["filters"])

        tab_labels = [str(tab.get("label", "")) for tab in registre["tabs"]]
        for label in CYCLE2_TAB_LABELS:
            with self.subTest(tab_label=label):
                self.assertIn(label, tab_labels)

        self.assertIsInstance(registre["ag_groups"], list)
        for group in registre["ag_groups"]:
            with self.subTest(ag_group=group.get("ag_id")):
                for field in ["ag_id", "label", "date", "open_count", "late_count", "is_expanded", "href", "items"]:
                    self.assertIn(field, group)
                self.assertLocalHref(group["href"], f"ag_groups.{group.get('ag_id')}.href")
                self.assertIsInstance(group["items"], list)
                for card in group["items"]:
                    for field in [
                        "id",
                        "resolution_ref",
                        "title",
                        "subtitle",
                        "status_label",
                        "status_tone",
                        "priority_label",
                        "proof_state_label",
                        "owner_label",
                        "due_label",
                        "is_selected",
                        "href",
                    ]:
                        self.assertIn(field, card)
                    self.assertLocalHref(card["href"], f"ag_groups.{group.get('ag_id')}.items.href")

        items = registre["items"]
        self.assertIsInstance(items, list)
        self.assertTrue(items)
        selected = registre["selected"]
        self.assertIsInstance(selected, dict)
        self.assertTrue(selected)
        self.assertIn(selected["id"], {item["id"] for item in items})

        for field in CYCLE2_ITEM_FIELDS:
            with self.subTest(selected_field=field):
                self.assertIn(field, selected)
        self.assertLocalHref(selected["href"], "selected.href")
        self.assertIsInstance(selected["proofs"], list)
        self.assertIsInstance(selected["pieces"], list)
        self.assertIsInstance(selected["followups"], list)
        self.assertIsInstance(selected["history"], list)

        for proof in selected["proofs"]:
            for field in CYCLE2_PROOF_FIELDS:
                self.assertIn(field, proof)
            self.assertIn(proof["status"], CYCLE2_PROOF_STATUSES)
            self.assertLocalHref(proof["href"], f"proofs.{proof.get('proof_id')}.href")

        for piece in selected["pieces"]:
            for field in CYCLE2_PIECE_FIELDS:
                self.assertIn(field, piece)
            self.assertLocalHref(piece["href"], f"pieces.{piece.get('doc_id')}.href")
            self.assertLocalHref(piece["download_href"], f"pieces.{piece.get('doc_id')}.download_href")

        for followup in selected["followups"]:
            for field in CYCLE2_FOLLOWUP_FIELDS:
                self.assertIn(field, followup)
            self.assertIn(followup["status"], CYCLE2_FOLLOWUP_STATUSES)
            self.assertLocalHref(followup["href"], f"followups.{followup.get('followup_id')}.href")

        for event in selected["history"]:
            for field in CYCLE2_HISTORY_FIELDS:
                self.assertIn(field, event)

        for field in ["status", "label", "reason", "allowed_audience", "blocked_by"]:
            self.assertIn(field, selected["diffusion"])
        for field in ["handover_note", "timeline_ref", "open_risk", "pack_section", "next_review_label"]:
            self.assertIn(field, selected["memory"])

        self.assertNoPrivateRegistreLeak(registre)
        self.assertNoForbiddenUxTokens(registre)
        for path, href in _hrefs(registre):
            with self.subTest(href_path=path):
                self.assertLocalHref(href, path)

    def test_cycle2_actions_route_layout_labels_when_delivered(self) -> None:
        self._seed_registre_actions()
        self._cycle2_registre_or_skip()
        expected_front_labels = [
            "Registre des decisions",
            "Fiche decision",
            "Action",
            "Preuves",
            "Pieces liees",
            "Relance syndic",
            "Historique",
            "Mode prive local",
            "Exporter le registre",
            "Nouvelle action",
            "Preparer une relance",
        ]
        template_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "coproscope"
            / "web"
            / "templates"
            / "actions.html"
        )
        template_html = template_path.read_text(encoding="utf-8")
        missing_template_labels = [label for label in expected_front_labels if label not in template_html]
        if missing_template_labels:
            self.skipTest(
                "Cycle 2 front /actions layout is outside this back-owned delivery; "
                f"template labels still missing: {missing_template_labels}"
            )
        client = self._client(access_token="local-secret")

        response = client.get(
            "/actions?token=local-secret"
            "&scope=decisions"
            "&selected_item_id=DAP-MISSING"
            "&tab=relance"
        )
        text = unescape(response.text)

        self.assertEqual(response.status_code, 200)
        for label in expected_front_labels:
            with self.subTest(label=label):
                self.assertIn(label, text)
        self.assertNotIn("Envoyer automatiquement", text)
        self.assertNotIn("email automatique", text.lower())
        self.assertNoPrivateRegistreLeak(text)


class UiRegistreActionsTemplateCompatibilityTests(unittest.TestCase):
    def test_actions_template_contains_decision_action_proof_register(self) -> None:
        template_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "coproscope"
            / "web"
            / "templates"
            / "actions.html"
        )
        html = template_path.read_text(encoding="utf-8")

        self.assertIn("Registre decisions - actions - preuves", html)
        self.assertIn("Suivi des decisions et relances", html)
        self.assertIn("Files de suivi", html)
        self.assertIn("Relances preuves", html)
        self.assertIn("Preuves attendues", html)
        self.assertIn("Relances responsables", html)
        self.assertIn("Registre de travail", html)
        self.assertIn("Historique / conflit", html)
        self.assertIn("Conflit / arbitrage", html)
        self.assertIn("{{ action.title }}", html)
        self.assertIn("{{ action.next_step }}", html)
        self.assertIn("{{ action.evidence }}", html)
        self.assertIn("{{ action.owner }}", html)
        self.assertIn("{{ action.detail }}", html)
        self.assertIn("/exports/actions.csv{{ action_query_suffix }}", html)
        self.assertIn("/exports/actions.md{{ action_query_suffix }}", html)


if __name__ == "__main__":
    unittest.main()
