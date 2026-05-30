from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "tools" / "orchestration_watchdog.py"


def _load_watchdog_module():
    spec = importlib.util.spec_from_file_location("orchestration_watchdog", TOOL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load watchdog tool from {TOOL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


watchdog = _load_watchdog_module()


def _row(conv_id: str, status: str) -> object:
    return watchdog.Conversation(
        f"`{conv_id}`",
        "`RM-2026-0006`",
        "`CH-20260525-000000-RM-2026-0006-test`",
        "Role test",
        f"`{status}`",
        "Lecture seule",
        "repo principal",
        "2026-05-25 10:00 +0200",
        "n/a",
        "Prochain geste test",
        "Trace test",
        1,
    )


def _ord(code: str, chunk: str, loop: str, next_task: str, gate: str) -> object:
    return watchdog.OrdItem(
        f"`{code}`",
        f"`{chunk}`",
        loop,
        "`RM-2026-0005`",
        next_task,
        gate,
        1,
    )


class OrchestrationWatchdogQuietTraceTests(unittest.TestCase):
    def test_relaunch_prompt_includes_expert_metier_agile_composition(self) -> None:
        prompt = watchdog.emit_prompt("agile", rows=[], items=[])

        self.assertIn("testeur expert metier", prompt)
        self.assertIn("juridique + compta + process chantier + syndic", prompt)
        self.assertIn("QA et coordinateur reprennent explicitement cette checklist", prompt)

    def test_uxui_prompt_keeps_dedicated_protocol_without_agile_composition(self) -> None:
        prompt = watchdog.emit_prompt("uxui", rows=[], items=[])

        self.assertNotIn("Composition agile canonique", prompt)

    def test_waiting_user_prompt_blocks_auto_dispatch(self) -> None:
        row = _row("CONV-2026-1641", "EN_ATTENTE_USER")
        row.next_step = "Arbitrage avant reprise de `ORD-P0-061`."
        prompt = watchdog.emit_prompt("agile", rows=[row], items=[])

        self.assertIn("sans relance automatique", prompt)
        self.assertIn("Ne lance aucune nouvelle equipe", prompt)
        self.assertIn("sous-agents attendent une mission explicite", prompt)
        self.assertNotIn("Composition agile canonique", prompt)
        self.assertNotIn("CONV-2026-1641 / ORD-P0-061", prompt)

    def test_auto_prompt_routes_backend_domain_without_agile_default(self) -> None:
        prompt = watchdog.emit_prompt(
            "auto",
            rows=[],
            items=[
                _ord(
                    "ORD-P0-901",
                    "INSTALLABLE-DRIVE-COEDITION",
                    "Deux appareils autorises -> publier des changements chiffres.",
                    "Contrat coedition et simulateur local deux appareils.",
                    "Aucun document brut, token ou identite reelle.",
                )
            ],
        )

        self.assertIn("Equipe-type: BACKEND_DOMAINE", prompt)
        self.assertIn("hub-and-spoke", prompt)
        self.assertIn("Tracer ROUTAGE_EQUIPE", prompt)
        self.assertIn("Les sous-agents recoivent directement role", prompt)
        self.assertNotIn("Composition agile canonique", prompt)

    def test_latest_trace_accepts_objectif_point_reprise_without_heartbeat_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "presence_agents.md"
            path.write_text(
                "\n".join(
                    [
                        "| Date | Agent | Evenement | Detail |",
                        "|---|---|---|---|",
                        "| 2026-05-30 13:20 +02:00 | `CONV-1` | `POINT_REPRISE_OBJECTIF` | Reprise par /objectif. |",
                    ]
                ),
                encoding="utf-8",
            )

            when, line = watchdog.latest_watchdog_trace(path)

        self.assertIsNotNone(when)
        self.assertIn("POINT_REPRISE_OBJECTIF", line or "")

    def test_auto_prompt_routes_live_recipe(self) -> None:
        prompt = watchdog.emit_prompt(
            "auto",
            rows=[],
            items=[
                _ord(
                    "ORD-P0-036",
                    "RECETTE-NAVIGATEUR-PARCOURS",
                    "Tester un cycle bout-en-bout.",
                    "Scenario navigateur desktop/mobile/tablette.",
                    "Screenshots, clics et absence de chevauchement texte requis.",
                )
            ],
        )

        self.assertIn("Equipe-type: RECETTE_LIVE_QA", prompt)
        self.assertIn("serie stricte", prompt)

    def test_stationnement_trace_matches_known_current_blockers(self) -> None:
        trace = (
            "| 2026-05-25 10:35 +02:00 | `relance-equipe-agile-gouvernail-autonome` "
            "| `HEARTBEAT_POST_RESPONSIVE_STATIONNEMENT` | A remonter: arbitrage "
            "`CONV-2026-1641`, blocage `CONV-2026-1708`, conversations stale/expirees "
            "`CONV-2026-1525` et `CONV-2026-0120`. Aucun role artificiel ouvert. |"
        )

        self.assertTrue(
            watchdog.quiet_trace_matches_current_state(
                trace,
                decisions=[_row("CONV-2026-1641", "EN_ATTENTE_USER")],
                blocked=[_row("CONV-2026-1708", "BLOQUE")],
                stale=[_row("CONV-2026-1525", "EN_COURS"), _row("CONV-2026-0120", "EN_COURS")],
                expired=[_row("CONV-2026-1525", "EN_COURS"), _row("CONV-2026-0120", "EN_COURS")],
            )
        )

    def test_stationnement_trace_rejects_untracked_new_blocker(self) -> None:
        trace = (
            "| 2026-05-25 10:35 +02:00 | `relance-equipe-agile-gouvernail-autonome` "
            "| `HEARTBEAT_POST_RESPONSIVE_STATIONNEMENT` | A remonter: arbitrage "
            "`CONV-2026-1641`. Aucun role artificiel ouvert. |"
        )

        self.assertFalse(
            watchdog.quiet_trace_matches_current_state(
                trace,
                decisions=[_row("CONV-2026-1641", "EN_ATTENTE_USER")],
                blocked=[_row("CONV-2026-1708", "BLOQUE")],
                stale=[],
                expired=[],
            )
        )


if __name__ == "__main__":
    unittest.main()
