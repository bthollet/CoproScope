from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from coproscope.core.common import InstanceConfig
from coproscope.web.requests_view import build_requests_view


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "server" / "src" / "coproscope" / "web" / "templates" / "requests.html"
DOC = ROOT / "docs" / "ui_demandes_coproprietaires.md"


def _instance(root: Path) -> InstanceConfig:
    return InstanceConfig(
        path=root / "instance.yml",
        payload={
            "instance_id": "demo-requests",
            "display_name": "Copro demo demandes",
            "registers": {
                "requests": "./registers/registre_demandes_coproprietaires.csv",
            },
        },
    )


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class UiRequestsModelTests(unittest.TestCase):
    def test_model_translates_requestops_rows_for_novice_ui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            instance = _instance(root)
            _write_csv(
                root / "registers" / "registre_demandes_coproprietaires.csv",
                [
                    "request_id",
                    "received_at",
                    "author_label",
                    "channel",
                    "subject",
                    "summary",
                    "proof_ref",
                    "source_ref",
                    "status",
                    "next_action",
                    "related_point_id",
                    "visibility",
                ],
                [
                    {
                        "request_id": "REQ-1",
                        "received_at": "2026-05-20",
                        "author_label": "coproprietaire_lot_12",
                        "channel": "email",
                        "subject": "Fuite dans le parking",
                        "summary": "Demande de suivi apres signalement.",
                        "proof_ref": "MSG-2026-05-20",
                        "source_ref": "boite-cs",
                        "status": "en_cours",
                        "next_action": "Demander le bon d'intervention au syndic.",
                        "related_point_id": "CS-2026-05-POINT-3",
                        "visibility": "conseil_syndical",
                    },
                    {
                        "request_id": "REQ-2",
                        "received_at": "2026-05-19",
                        "author_label": "conseil_syndical",
                        "channel": "portail_syndic",
                        "subject": "Ticket ascenseur sans reponse",
                        "summary": "Le portail affiche une demande ouverte.",
                        "proof_ref": "PORTAIL-77",
                        "source_ref": "ticket syndic",
                        "status": "relance",
                        "next_action": "Relancer avec une echeance explicite.",
                        "visibility": "restreint",
                    },
                ],
            )
            _write_csv(
                root / "registers" / "journal_demandes_coproprietaires.csv",
                [
                    "journal_id",
                    "request_id",
                    "occurred_at",
                    "actor_role",
                    "action_type",
                    "summary",
                    "proof_ref",
                    "source_ref",
                    "status_after",
                    "next_action",
                    "visibility",
                    "event_hash",
                ],
                [
                    {
                        "journal_id": "JRN-1",
                        "request_id": "REQ-1",
                        "occurred_at": "2026-05-20T12:00:00Z",
                        "actor_role": "conseil_syndical",
                        "action_type": "rattachement",
                        "summary": "Rattachement au point de reunion confirme.",
                        "proof_ref": "MSG-2026-05-20",
                        "source_ref": "note cs",
                        "status_after": "en_cours",
                        "next_action": "Verifier la reponse du syndic.",
                        "visibility": "conseil_syndical",
                        "event_hash": "",
                    },
                ],
            )

            model = build_requests_view(instance, year=2026)

        self.assertEqual(model["summary"]["total"], 2)
        self.assertEqual(model["summary"]["open"], 2)
        self.assertEqual(model["summary"]["journal_actions"], 1)
        self.assertEqual(model["open_rows"][0]["request_id"], "REQ-2")
        self.assertEqual(model["open_rows"][0]["status_label"], "a relancer")
        self.assertEqual(model["open_rows"][0]["visibility_label"], "restreint")
        self.assertIn("Diffusion restreinte", model["open_rows"][0]["diffusion_warning"])
        self.assertEqual(model["rows"][1]["channel_label"], "email")
        self.assertEqual(model["rows"][1]["related_label"], "point CS-2026-05-POINT-3")
        self.assertEqual(model["rows"][1]["journal"][0]["action_type_label"], "rattachement")
        self.assertEqual(model["rows"][1]["journal"][0]["next_action_label"], "Verifier la reponse du syndic.")

    def test_model_empty_state_is_useful_without_registers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            model = build_requests_view(_instance(Path(tmp)), year=2026)

        self.assertEqual(model["summary"]["total"], 0)
        self.assertEqual(model["summary"]["open"], 0)
        self.assertIn("La boite de demandes est prete", model["empty_state"]["title"])
        self.assertIn("canal", model["empty_state"]["message"])
        self.assertIn("qualification, relance, reponse", model["empty_state"]["journal_step"])
        self.assertFalse(model["source"]["request_register_exists"])


class UiRequestsStaticTests(unittest.TestCase):
    def test_template_contains_multichannel_request_workflow(self) -> None:
        html = TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("Demandes coproprietaires multi-canaux", html)
        self.assertIn("Boite de demandes a suivre", html)
        self.assertIn("Canaux d'arrivee", html)
        self.assertIn("Statuts et diffusion", html)
        self.assertIn("Registre des demandes", html)
        self.assertIn("Journal d'actions concret", html)
        self.assertIn("Demandes a rattacher", html)
        self.assertIn("Canal, sujet, preuve/source, statut, prochaine action, diffusion et rattachement.", html)
        self.assertIn("{{ row.channel_label }}", html)
        self.assertIn("{{ row.proof_label }}", html)
        self.assertIn("{{ row.next_action_label }}", html)
        self.assertIn("{{ row.visibility_label }}", html)
        self.assertIn("{{ row.related_label or \"a rattacher\" }}", html)
        self.assertIn("{{ action.summary }}", html)
        self.assertIn("{{ requests.empty_state.message }}", html)

    def test_documentation_names_integration_boundary(self) -> None:
        doc = DOC.read_text(encoding="utf-8")

        self.assertIn("UI demandes coproprietaires", doc)
        self.assertIn("requestops", doc)
        self.assertIn("app.py", doc)
        self.assertIn("canal", doc)
        self.assertIn("preuve/source", doc)
        self.assertIn("journal d'actions concret", doc)
        self.assertIn("etat vide utile", doc)


if __name__ == "__main__":
    unittest.main()
